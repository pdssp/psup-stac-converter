import ast
import json
import tempfile
import time
from io import StringIO
from pathlib import Path
from typing import Literal

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import pystac
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from shapely import Polygon, bounds, to_geojson

from psup_stac_converter.extensions import apply_eo, apply_sci, apply_ssys
from psup_stac_converter.informations import (
    OmegaMineralMapDesc,
    data_providers,
    geojson_features,
    omega_bands,
    omega_c_channel,
    omega_data_cubes,
    omega_map_publications,
    omega_mineral_maps,
)
from psup_stac_converter.processors.selection import ProcessorName, select_processor
from psup_stac_converter.settings import Settings, create_logger
from psup_stac_converter.utils.io import IoHandler, PsupIoHandler

settings = Settings()
log = create_logger(__name__)


class BaseProcessor:
    @staticmethod
    def _open_metadata_as_gpd(metadata_file: Path) -> gpd.GeoDataFrame:
        gdf = gpd.read_file(metadata_file)
        # Place transformations here
        gdf["footprint"] = gdf["footprint"].apply(
            lambda x: Polygon(ast.literal_eval(x))
        )
        gdf = gdf.set_geometry("footprint")
        gdf["keywords"] = (
            gdf["keywords"]
            .astype(str)
            .apply(lambda s: "[" + s.strip("{}") + "]" if s != "nan" else "[]")
            .apply(ast.literal_eval)
        )
        return gdf

    def __init__(
        self,
        raw_data_folder: Path,
        output_folder: Path | None = None,
    ):
        # Metadata is now handled by respective variables

        if not raw_data_folder.exists():
            raise FileNotFoundError(
                f"Couldn't find {raw_data_folder}. Make sure it exists."
            )
        self.io_handler = IoHandler(
            input_folder=raw_data_folder, output_folder=output_folder
        )
        self.possible_names = list(geojson_features.keys())

    def __str__(self) -> str:
        fmt_str = []

        for v in geojson_features.values():
            fmt_str.append(
                f"- {v.description} ({self.io_handler.input_folder / v.name})"
            )

        return "\n".join(fmt_str)

    def _open_as_geodf(
        self, names: list[ProcessorName] | None
    ) -> dict[str, gpd.GeoDataFrame]:
        dfs = {}
        files_with_errors = {}

        if names is not None:
            md_iter = {k: v for k, v in geojson_features.items() if k in names}
        else:
            md_iter = geojson_features

        for obj in md_iter.values():
            try:
                df = gpd.read_file(self.io_handler.input_folder / obj.name)
                dfs[obj.name] = df
                log.info(f"Parsed {obj.name} with success")
            except Exception as e:
                log.error(f"[{e.__class__.__name__}] {e}")
                log.error(f"Couldn't parse {obj.name} as a GeoPandas dataframe!")
                files_with_errors[obj.name] = e

        log.warning(
            f"""Encountered issues with the following files: {files_with_errors}"""
        )
        return dfs

    def preview_geodf(self, names: list[ProcessorName] | None = None):
        console = Console()
        for k, v in self._open_as_geodf(names=names).items():
            buffer = StringIO()
            v.info(buf=buffer)
            panel = Panel(buffer.getvalue(), title=k)
            console.print(panel)
            console.print(v.columns)

    def concat_geodf(self) -> gpd.GeoDataFrame:
        return pd.concat(self._open_as_geodf().values())


class RawDataAnalysis(BaseProcessor):
    """
    Primarily serves as a concatenator for sparse JSON data files.

    Can serve as a good middleman for those who can handle GeoDataframes.
    """

    def __init__(
        self,
        raw_data_folder: Path,
        psup_data_inventory_file: Path | None = None,
        output_folder: Path | None = None,
    ):
        super().__init__(raw_data_folder, output_folder)
        if psup_data_inventory_file is not None and psup_data_inventory_file.exists():
            self.psup_archive = PsupIoHandler(
                psup_data_inventory_file, output_folder=self.io_handler.input_folder
            )
        else:
            log.warning("No data archive found. Consider linking this one.")
            self.psup_archive = None

    @staticmethod
    def show_writable_formats():
        table = Table(title="Available formats")

        table.add_column("Format", style="bold")
        table.add_column("Permission")

        for driver_name, driver_permissions in pyogrio.list_drivers().items():
            if driver_permissions == "r":
                permission = "[yellow]READ ONLY"
            elif driver_permissions == "rw":
                permission = "[bold green]READ/WRITE"

            table.add_row(driver_name, permission)

        console = Console()
        console.print(table)

    def save_to_format(
        self,
        filename: str,
        fmt_name: Literal["shp", "geosjon", "gpkg", "other"] = "other",
    ) -> gpd.GeoDataFrame:
        output_file = self.io_handler.output_folder / filename
        gdf = self.concat_geodf()

        if fmt_name in ["shp", "other"]:
            gdf.to_file(output_file)
        elif fmt_name == "geojson":
            gdf.to_file(output_file, driver="GeoJSON")
        elif fmt_name == "geopackage":
            gdf.to_file(output_file, layer="data", driver="GPKG")

        return gdf


class CatalogCreator(BaseProcessor):
    """PSUP's STAC generator

    Args:
        BaseProcessor (_type_): _description_
    """

    def __init__(
        self,
        raw_data_folder: Path,
        output_folder: Path,
        psup_data_inventory_file: Path | None = None,
    ):
        super().__init__(raw_data_folder, output_folder)
        if psup_data_inventory_file is not None and psup_data_inventory_file.exists():
            self.psup_archive = PsupIoHandler(
                psup_data_inventory_file, output_folder=self.io_handler.input_folder
            )
        else:
            log.warning(
                "No data archive found. Consider linking this one to your converter to extract relevant metadata."
            )
            log.warning("You can use `psup-scraper` to generate one if needed.")
            self.psup_archive = None

    def create_catalog(
        self, self_contained: bool = True, clean_previous_output: bool = False
    ) -> pystac.Catalog:
        """Creates a catalog over the entire feature selection"""
        start_time = time.time()

        if self.io_handler.is_input_folder_empty():
            raise FileNotFoundError("Your folder is empty! Download the data first.")

        if not self.io_handler.is_output_folder_empty() and not clean_previous_output:
            raise ValueError(
                "The output folder is not empty. Please clean it first or set clean_previous_output` to True"
            )
        elif not self.io_handler.is_output_folder_empty() and clean_previous_output:
            self.io_handler.clean_output_folder()

        # Create root catalog for Mars items
        catalog = pystac.Catalog(
            id="urn:pdssp:ias:body:mars",
            description="""This test STAC catalog contains Mars data collections and sub-catalogs currently hosted and distributed by\n[PSUP](http://psup.ias.u-psud.fr/sitools/client-user/index.html?project=PLISonMars) (Planetary SUrface Portal).\n\n![Mars](https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Mars_%28white_background%29.jpg/120px-Mars_%28white_background%29.jpg)\n""",
        )

        catalog = apply_ssys(catalog)

        feature_collection = self.create_feature_collection()
        catalog.add_child(feature_collection)

        omega_mmaps_collection = self.create_omega_mineral_maps_collection()
        catalog.add_child(omega_mmaps_collection)

        omega_c_channel_collection = self.create_omega_c_channel_collection()
        catalog.add_child(omega_c_channel_collection)

        omega_data_cubes_collection = self.create_omega_data_cubes_collection()
        catalog.add_child(omega_data_cubes_collection)

        # Save catalog (ie. in the STAC folder)
        log.info(f"Normalizing hrefs to {self.io_handler.output_folder}")
        catalog.normalize_hrefs(self.io_handler.output_folder.as_posix())

        log.info(
            f"""Saving catalog as {"self-contained" if self_contained else "absolute published"}"""
        )
        if self_contained:
            catalog.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)
        else:
            catalog.save(catalog_type=pystac.CatalogType.ABSOLUTE_PUBLISHED)

        exec_time = time.time() - start_time
        log.info(
            f"Catalog created in {exec_time // 60} minutes and {round(exec_time % 60, 2)} seconds!"
        )

    def create_feature_collection(self) -> pystac.Collection:
        fp_bounds = np.array(
            [bounds(desc.footprint) for desc in geojson_features.values()]
        )
        total_bounds = np.array(
            (
                np.nanmin(fp_bounds[:, 0]),  # minx
                np.nanmin(fp_bounds[:, 1]),  # miny
                np.nanmax(fp_bounds[:, 2]),  # maxx
                np.nanmax(fp_bounds[:, 3]),  # maxy
            )
        ).tolist()

        spatial_extent = pystac.SpatialExtent(bboxes=[total_bounds])
        temporal_extent = pystac.TemporalExtent(
            intervals=[
                [
                    pd.Timestamp.min.to_pydatetime(),
                    pd.Timestamp.max.to_pydatetime(),
                ]
            ]
        )
        collection_extent = pystac.Extent(
            spatial=spatial_extent, temporal=temporal_extent
        )

        master_collection = pystac.Collection(
            id="urn:pdssp:ias:collection:features_datasets",
            extent=collection_extent,
            description="This collection holds locations data for hydrated mineral terrains, Central peaks hydrated phases between Isidis\nand Hellas, Central peaks mineralogy south Valles Marineris, Valles Marineris low Calcium-Pyroxene, Seasonal South\npolar cap limits, Scalloped depressions and Lobate impact craters. This dataset contains vector catalogs\nand their associated metadatas. All catalogs are provided in GeoJSON file format.\n",
            keywords=[
                "polar cap",
                "seasonal",
                "south",
                "CO2",
                "crocus line",
                "inner crocus line",
                "outer crocus line",
                "snowdrop distance",
                "northern plains",
                "periglacial",
                "thermokarst",
                "ground ice",
                "global",
                "craters",
                "ejecta",
                "lithosphere",
                "mineralogy",
            ],
            license="CC-BY-4.0",
            providers=data_providers,
        )

        # Apply extensions here
        master_collection = apply_ssys(master_collection)

        for feature_name in self.possible_names:
            if self.psup_archive is not None:
                file_location = self.psup_archive.find_or_download(feature_name)
            else:
                file_location = self.io_handler.input_folder / feature_name
            log.info(f"Found {feature_name} at {file_location}")

            log.info(f"Processing {feature_name}.")
            processor = select_processor(
                feature_name,
                catalog_folder=file_location.parent,
            )
            subcollection = processor.create_collection()
            # Apply extensions here
            subcollection = apply_sci(
                subcollection, publications=geojson_features[feature_name].publications
            )
            master_collection.add_child(subcollection)

        return master_collection

    def create_omega_mineral_maps_collection(self) -> pystac.Collection:
        spatial_extent = pystac.SpatialExtent(bboxes=[[-180.0, -90.0, 180.0, 90.0]])

        temporal_extent = pystac.TemporalExtent(
            intervals=[
                [
                    min([v.created_at for v in omega_mineral_maps.values()]),
                    max([v.created_at for v in omega_mineral_maps.values()]),
                ]
            ]
        )
        collection_extent = pystac.Extent(
            spatial=spatial_extent, temporal=temporal_extent
        )

        master_collection = pystac.Collection(
            id="urn:pdssp:ias:collection:omega_mineral_maps",
            extent=collection_extent,
            license="CC-BY-4.0",
            description="""PSUP OMEGA mineral maps are OMEGA-based NIR albedo, Ferric BD530, Ferric Nanophase, Olivine SP1, SP2, SP3, Pyroxene and Emissivity at 5.03µm. OMEGA is the VISNIR imaging spectrometer onboard ESA/Mars-Express spacecraft operating around Mars from January 2004. All maps are provided in FITS file format via the "download" column.

This Dataset is also available as a VO TAP service (ivo://idoc/psup/omega_maps/q/epn_core).""",
            providers=data_providers,
            keywords=list(
                set(
                    [
                        kw
                        for omega_map_item in omega_mineral_maps.values()
                        for kw in omega_map_item.raster_keywords
                    ]
                )
            ),
        )

        # Apply extensions here
        master_collection = apply_ssys(master_collection)
        master_collection = apply_sci(
            master_collection, publications=omega_map_publications
        )

        for omega_map_item in omega_mineral_maps.values():
            omega_item = self.create_omega_map_item(omega_map_item)
            master_collection.add_item(omega_item)

        return master_collection

    def create_omega_map_item(self, item: OmegaMineralMapDesc) -> pystac.Item:
        map_geometry = Polygon(((-180, -90), (180, 90), (180, 90), (180, -90)))

        footprint = json.loads(to_geojson(map_geometry))
        bbox = bounds(map_geometry).tolist()

        timestamp = item.created_at

        stac_item_properties = {
            "description": item.raster_description,
            "long_description": item.raster_lng_description,
            "keywords": item.raster_keywords,
        }
        pystac_item = pystac.Item(
            id=Path(item.raster_name).stem.replace("_", "-"),
            properties=stac_item_properties,
            geometry=footprint,
            bbox=bbox,
            datetime=timestamp,
        )

        # assets
        thumbn_asset = pystac.Asset(
            href=str(item.thumbnail),
            media_type=pystac.MediaType.PNG,
            roles=["thumbnail"],
            description="PNG thumbnail preview for visualizations",
        )
        pystac_item.add_asset("thumbnail", thumbn_asset)

        if self.psup_archive:
            remote_fits = self.psup_archive.find_file_remote_path(item.raster_name)
        else:
            remote_fits = item.raster_name
        # Source: https://www.iana.org/assignments/media-types/media-types.xhtml
        fits_asset = pystac.Asset(
            href=str(remote_fits),
            media_type="application/fits",
            roles=["visual", "data"],
            description="FITS data",
        )
        pystac_item.add_asset("fits", fits_asset)

        # extensions
        pystac_item = apply_sci(pystac_item, publications=item.publication)
        pystac_item = apply_ssys(pystac_item)
        pystac_item = apply_eo(pystac_item, bands=omega_bands)

        # common metadata
        pystac_item.common_metadata.platform = "mex"
        pystac_item.common_metadata.instruments = ["omega"]
        pystac_item.common_metadata.gsd = 5000

        return pystac_item

    def create_omega_c_channel_collection(self) -> pystac.Collection:
        spatial_extent = pystac.SpatialExtent(bboxes=[[-180.0, -90.0, 180.0, 90.0]])
        temporal_extent = pystac.TemporalExtent(
            intervals=[
                [
                    pd.Timestamp.min.to_pydatetime(),
                    pd.Timestamp.max.to_pydatetime(),
                ]
            ]
        )
        collection_extent = pystac.Extent(
            spatial=spatial_extent, temporal=temporal_extent
        )

        master_collection = pystac.Collection(
            id="urn:pdssp:ias:collection:omega_c_channel_proj",
            extent=collection_extent,
            license="CC-BY-4.0",
            description="""These data cubes have been specifically selected and filtered for studies of the surface mineralogy between 1 and 2.5 µm.

They contain all the OMEGA observations acquired with the C channel after filtering. Filtering processes have been implemented to remove some instrumental artefacts and observational conditions. Each OMEGA record is available as a `netCDF4.nc` file and an `idl.sav`.

Both files contain the cubes of reflectance of the surface at a given longitude, latitude and wavelength λ. The reflectance is defined by the “reflectance factor” $\frac{I(\lambda)}{F \cos(i)}$ where i is the solar incidence angle with $\lambda$ from 0.97 to 2.55 µm (second dimension of the cube with 120 wavelengths). The spectra are corrected for atmospheric and aerosol contributions according to the method described in Vincendon et al. (Icarus, 251, 2015). It therefore corresponds to albedo for a lambertian surface. The first dimension of the cube refers to the length of scan. It can be 32, 64, or 128 pixels. It gives the first spatial dimension. The third dimension refers to the rank of the scan. It is the second spatial dimension.""",
            providers=data_providers,
        )

        # Apply extensions here
        master_collection = apply_ssys(master_collection)
        master_collection = apply_sci(master_collection, publications=omega_c_channel)

        # TODO: add items here
        if self.psup_archive is not None:
            pass
        else:
            log.warning(
                "psup_data_inventory_file` needed to register items in this collection! Skipping..."
            )

        return master_collection

    def create_omega_data_cubes_collection(self) -> pystac.Collection:
        spatial_extent = pystac.SpatialExtent(bboxes=[[-180.0, -90.0, 180.0, 90.0]])
        temporal_extent = pystac.TemporalExtent(
            intervals=[
                [
                    pd.Timestamp.min.to_pydatetime(),
                    pd.Timestamp.max.to_pydatetime(),
                ]
            ]
        )
        collection_extent = pystac.Extent(
            spatial=spatial_extent, temporal=temporal_extent
        )

        master_collection = pystac.Collection(
            id="urn:pdssp:ias:collection:omega_data_cubes",
            extent=collection_extent,
            license="CC-BY-4.0",
            description="""
This dataset contains all the OMEGA observations acquired with the C, L and VIS channels until April 2016, 11, after filtering. Filtering processes have been implemented to remove some instrumental artefacts and observational conditions. Each OMEGA record is available as a `netCDF4.nc` file and an `idl.sav`

Both files contain the cubes of reflectance of the surface at a given longitude, latitude and wavelength $\lambda$. The surface reflectance is defined as $\frac{I(\lambda)}{F \cos(i)}$  where:

- channel $C=[0.93-2.73 \mu m]$; $L=[2.55-5.10 \mu m]$; $\text{Visible}=[0.38-1.05 \mu m]$;
- atmospheric attenuation is corrected (1-5 µm);
- airborne dust scattering is corrected (0.4-2.5 µm and for 5 µm emissivity estimations);
- thermal contribution is removed (> 3 µm); L channel data and VIS channel are co-registered with C channel when available.

Please note that longitudes range from -180 to 180 degrees east.
""",
            providers=data_providers,
        )

        # Apply extensions here
        master_collection = apply_ssys(master_collection)
        master_collection = apply_sci(master_collection, publications=omega_data_cubes)

        # TODO: add items here
        if self.psup_archive is not None:
            omega_data = self.psup_archive.get_omega_data("data_cubes_slice")
            for cube_idx in omega_data.index.unique():
                cube_item = self.create_omega_data_cube_item(
                    cube_idx, omega_data.loc[cube_idx, :]
                )
                master_collection.add_item(cube_item)
        else:
            log.warning(
                "psup_data_inventory_file` needed to register items in this collection! Skipping..."
            )

        return master_collection

    def create_omega_data_cube_item(
        self, cube_idx: str, cube_info: pd.DataFrame
    ) -> pystac.Item:
        # urls
        nc_href = cube_info.loc[
            cube_info["extension"].str.contains("nc"), "href"
        ].item()
        sav_href = cube_info.loc[
            cube_info["extension"].str.contains("sav"), "href"
        ].item()

        # TODO: open files here
        with tempfile.NamedTemporaryFile(delete_on_close=False) as fp:
            fp.write()
            fp.close()
            with open(fp.name, mode="rb") as f:
                f.read()

        orbit_number, cube_number = cube_idx.split("_")
        item_properties = {"orbit_number": orbit_number, "cube_number": cube_number}

        omega_data_cube = pystac.Item(id=cube_idx, properties=item_properties)

        # assets
        nc_asset = pystac.Asset(
            href=nc_href,
            media_type=pystac.MediaType.NETCDF,
            roles=["data"],
            description="NetCDF data",
        )
        omega_data_cube.add_asset("nc", nc_asset)

        sav_asset = pystac.Asset(
            href=sav_href,
            media_type=pystac.MediaType.TEXT,
            roles=["data"],
            description=".sav data",
        )
        omega_data_cube.add_asset("sav", sav_asset)

        # extensions
        omega_data_cube = apply_ssys(omega_data_cube)
        # EO only if data allows it

        # common metadata
        omega_data_cube.common_metadata.mission = "mex"
        omega_data_cube.common_metadata.instruments = ["omega"]

        return omega_data_cube

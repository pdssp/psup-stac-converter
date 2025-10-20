import ast
import logging
import time
from io import StringIO
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pystac
from rich.console import Console
from rich.panel import Panel
from shapely import Polygon, bounds

from psup_stac_converter.exceptions import FileExtensionError, FolderNotEmptyError
from psup_stac_converter.extensions import apply_sci, apply_ssys
from psup_stac_converter.informations.data_providers import providers as data_providers
from psup_stac_converter.informations.geojson_features import geojson_features
from psup_stac_converter.omega.c_channel_proj import OmegaCChannelProj
from psup_stac_converter.omega.data_cubes import OmegaDataCubes
from psup_stac_converter.omega.mineral_maps import omega_maps_collection_generator
from psup_stac_converter.processors.selection import ProcessorName, select_processor
from psup_stac_converter.settings import Settings, create_logger
from psup_stac_converter.utils.io import IoHandler, PsupIoHandler


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
        log: logging.Logger | None = None,
    ):
        # Metadata is now handled by respective variables

        if not raw_data_folder.exists():
            raise FileNotFoundError(
                f"Couldn't find {raw_data_folder}. Make sure it exists."
            )

        if log is None:
            self.log = create_logger(
                __name__,
                log_level=Settings().log_level,
                log_format=Settings().log_format,
            )
        else:
            self.log = log

        self.io_handler = IoHandler(
            input_folder=raw_data_folder, output_folder=output_folder, log=self.log
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
                self.log.info(f"Parsed {obj.name} with success")
            except Exception as e:
                self.log.error(f"[{e.__class__.__name__}] {e}")
                self.log.error(f"Couldn't parse {obj.name} as a GeoPandas dataframe!")
                files_with_errors[obj.name] = e

        self.log.warning(
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
        log: logging.Logger | None = None,
    ):
        super().__init__(raw_data_folder, output_folder, log=log)
        if psup_data_inventory_file is None:
            psup_data_inventory_file = Settings().psup_inventory_file
        if not psup_data_inventory_file.exists():
            raise FileNotFoundError(
                f"""{psup_data_inventory_file} does not exist.
                You can generate one with
                `psup-scraper get-data-ref -O {psup_data_inventory_file.as_posix()} -f csv --clean` if needed"""
            )

        if not psup_data_inventory_file.suffix.endswith("csv"):
            raise FileExtensionError(["csv"], psup_data_inventory_file.suffix)

        self.psup_archive = PsupIoHandler(
            psup_data_inventory_file, output_folder=raw_data_folder
        )
        self.log.debug(self.psup_archive)

    def _add_collections_to_catalog(self, catalog: pystac.Catalog) -> pystac.Catalog:
        try:
            feature_collection = self.create_feature_collection()
            catalog.add_child(feature_collection)

            self.log.info("Creating OMEGA mineral maps collection")
            omega_mmaps_collection = self.create_omega_mineral_maps_collection()
            catalog.add_child(omega_mmaps_collection)

            self.log.info("Creating OMEGA Data cubes collection")
            omega_data_cubes_builder = OmegaDataCubes(self.psup_archive, log=self.log)
            omega_data_cubes_collection = omega_data_cubes_builder.create_collection()
            catalog.add_child(omega_data_cubes_collection)

            self.log.info("Creating OMEGA C Channel Proj collection")
            self.log.debug(self.psup_archive)
            omega_c_channel_builder = OmegaCChannelProj(self.psup_archive, log=self.log)
            omega_c_channel_collection = omega_c_channel_builder.create_collection()
            catalog.add_child(omega_c_channel_collection)

        except Exception as e:
            self.log.error("There was a problem during collection generation!")
            self.log.error(f"[{e.__class__.__name__}] {e}")
        finally:
            return catalog

    def create_catalog(
        self, self_contained: bool = True, clean_previous_output: bool = False
    ) -> pystac.Catalog:
        """Creates a catalog over the entire feature selection"""
        start_time = time.time()

        if not self.io_handler.is_output_folder_empty() and not clean_previous_output:
            raise FolderNotEmptyError(
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

        catalog = self._add_collections_to_catalog(catalog)

        # Save catalog (ie. in the STAC folder)
        self.log.info(f"Normalizing hrefs to {self.io_handler.output_folder}")
        catalog.normalize_hrefs(self.io_handler.output_folder.as_posix())

        self.log.info(
            f"""Saving catalog as {"self-contained" if self_contained else "absolute published"}"""
        )
        if self_contained:
            catalog.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)
        else:
            catalog.save(catalog_type=pystac.CatalogType.ABSOLUTE_PUBLISHED)

        exec_time = time.time() - start_time
        self.log.info(
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
            file_location = self.psup_archive.find_or_download(feature_name)

            self.log.info(f"Found {feature_name} at {file_location}")

            self.log.info(f"Processing {feature_name}.")
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
        return omega_maps_collection_generator(self.psup_archive)

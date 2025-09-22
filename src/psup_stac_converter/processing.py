import ast
import time
from io import StringIO
from pathlib import Path
from typing import Literal

import geopandas as gpd
import pandas as pd
import pyogrio
import pystac
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from shapely import Polygon

from psup_stac_converter.extensions import apply_ssys
from psup_stac_converter.processors.selection import ProcessorName, select_processor
from psup_stac_converter.settings import Settings, create_logger
from psup_stac_converter.utils.io import IoHandler

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
        return gdf

    def __init__(
        self,
        metadata_file: Path,
        catalog_folder: Path,
        output_folder: Path | None = None,
    ):
        if not metadata_file.exists():
            raise FileNotFoundError(f"Couldn't find {metadata_file}")

        if not metadata_file.suffix.endswith("csv"):
            raise ValueError("File must be a CSV!")

        self.metadata = self._open_metadata_as_gpd(metadata_file)

        if not catalog_folder.exists():
            raise FileNotFoundError(
                f"Couldn't find {catalog_folder}. Make sure it exists."
            )
        self.io_handler = IoHandler(
            input_folder=catalog_folder, output_folder=output_folder
        )
        self.possible_names = self.metadata["name"].tolist()

    def __str__(self) -> str:
        fmt_str = []

        for obj in self.metadata.itertuples():
            fmt_str.append(
                f"- {obj.description} ({self.io_handler.input_folder / obj.name})"
            )

        return "\n".join(fmt_str)

    def _open_as_geodf(
        self, names: list[ProcessorName] | None
    ) -> dict[str, gpd.GeoDataFrame]:
        dfs = {}
        files_with_errors = {}

        if names is not None:
            md_iter = self.metadata[self.metadata["name"].isin(names)]
        else:
            md_iter = self.metadata

        for obj in md_iter.itertuples():
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
        metadata_file: Path,
        catalog_folder: Path,
        output_folder: Path | None = None,
    ):
        super().__init__(metadata_file, catalog_folder, output_folder)

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
    def __init__(self, metadata_file: Path, catalog_folder: Path, output_folder: Path):
        super().__init__(metadata_file, catalog_folder, output_folder)

    def create_catalog(
        self,
        name: str,
        self_contained: bool = True,
        clean_previous_output: bool = False,
    ) -> pystac.Catalog:
        """Creates one catalog per name"""
        start_time = time.time()

        if name not in self.possible_names:
            raise ValueError(
                f"""You entered "{name}". The only possible values are {", ".join(["'" + v + "'" for v in self.possible_names])}"""
            )

        if self.io_handler.is_input_folder_empty():
            raise FileNotFoundError("Your folder is empty! Download the data first.")

        if not self.io_handler.is_output_folder_empty() and not clean_previous_output:
            raise ValueError(
                "The output folder is not empty. Please clean it first or set clean_previous_output` to True"
            )
        elif not self.io_handler.is_output_folder_empty() and clean_previous_output:
            self.io_handler.clean_output_folder()

        processor = select_processor(
            name, metadata=self.metadata, catalog_folder=self.io_handler.input_folder
        )
        catalog = processor.create_catalog()

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
            f"Catalog created in {exec_time // 60} minutes and {exec_time % 60} seconds!"
        )

        return catalog

    def condense_all_in_catalog(
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

        catalog = pystac.Catalog(
            id="urn:pdssp:ias:body:mars",
            description="""This test STAC catalog contains Mars data collections and sub-catalogs currently hosted and distributed by\n[PSUP](http://psup.ias.u-psud.fr/sitools/client-user/index.html?project=PLISonMars) (Planetary SUrface Portal).\n\n![Mars](https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Mars_%28white_background%29.jpg/120px-Mars_%28white_background%29.jpg)\n""",
        )

        catalog = apply_ssys(catalog)

        spatial_extent = pystac.SpatialExtent(
            bboxes=[self.metadata.geometry.total_bounds.tolist()]
        )
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
            description="This collections holds locations data for hydrated mineral terrains, Central peaks hydrated phases between Isidis\nand Hellas, Central peaks mineralogy south Valles Marineris, Valles Marineris low Calcium-Pyroxene, Seasonal South\npolar cap limits, Scalloped depressions and Lobate impact craters. This dataset contains vector catalogs\nand their associated metadatas. All catalogs are provided in GeoJSON file format.\n",
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
            providers=[
                pystac.Provider(
                    name="Institut d'Astrophysique Spatiale (IAS) - IDOC",
                    description="The Integrated Data and Operation Center (IDOC) is responsible for processing, archiving\nand distributing data from space science missions in which the IAS institute is involved.\n",
                    roles=[
                        pystac.ProviderRole.PROCESSOR,
                        pystac.ProviderRole.PRODUCER,
                        pystac.ProviderRole.HOST,
                    ],
                    url="https://idoc.ias.universite-paris-saclay.fr",
                ),
                pystac.Provider(
                    name="Géosciences Paris-Saclay (GEOPS)",
                    description='GEOPS is a joint laboratory of the \u201cUniversit\u00e9 de Paris-Sud\u201d (UPSUD) and the "Centre National\nde la Recherche Scientifique" (CNRS).\n',
                    roles=[
                        pystac.ProviderRole.PROCESSOR,
                        pystac.ProviderRole.PRODUCER,
                    ],
                    url="http://geops.geol.u-psud.fr",
                ),
                pystac.Provider(
                    name="Planetary SUrface Portal (PSUP)",
                    description="PSUP is a french research service, by Observatoire Paris-Sud and Observatoire de Lyon, to help\nthe distribution of high added-value datasets of planetary surfaces.\n",
                    roles=[
                        pystac.ProviderRole.LICENSOR,
                    ],
                    url="https://psup.cnrs.fr",
                ),
            ],
        )

        master_collection = apply_ssys(master_collection)

        for feature_name in self.possible_names:
            log.info(f"Processing {feature_name}.")
            processor = select_processor(
                feature_name,
                metadata=self.metadata,
                catalog_folder=self.io_handler.input_folder,
            )
            subcollection = processor.create_collection()
            master_collection.add_child(subcollection)

        catalog.add_child(master_collection)

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
            f"Catalog created in {exec_time // 60} minutes and {exec_time % 60} seconds!"
        )

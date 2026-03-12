import logging
import os
import time
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
import psutil
import pystac
import pystac.errors
from httpx import ReadTimeout
from shapely import bounds

from psup_stac_converter.exceptions import (
    FileExtensionError,
    FolderEmptyError,
    FolderNotEmptyError,
    OutOfMemoryError,
)
from psup_stac_converter.extensions import apply_proj, apply_sci, apply_ssys
from psup_stac_converter.informations.data_providers import providers
from psup_stac_converter.informations.geojson_features import geojson_features
from psup_stac_converter.omega.c_channel_proj import OmegaCChannelProj
from psup_stac_converter.omega.data_cubes import OmegaDataCubes
from psup_stac_converter.omega.mineral_maps import omega_maps_collection_generator
from psup_stac_converter.processors.selection import ProcessorName, select_processor
from psup_stac_converter.settings import Settings, create_logger
from psup_stac_converter.utils.io import IoHandler, PsupIoHandler, WktIoHandler

process = psutil.Process(os.getpid())


class BaseProcessor:
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


class CatalogCreator(BaseProcessor):
    """The entrypoint class that translates PSUP data information into
    a STAC catalog, using the appropriate collections and items.
    """

    def __init__(
        self,
        raw_data_folder: Path,
        output_folder: Path,
        psup_data_inventory_file: Path | None = None,
        wkt_file: Path | None = None,
        log: logging.Logger | None = None,
        n_omega_files: int | None = None,
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

        if wkt_file is not None:
            self.wkt_io = WktIoHandler(wkt_file)
        else:
            self.wkt_io = None

        self.n_omega_files = n_omega_files
        self.log.debug(self.psup_archive)

    def _add_collections_to_catalog(
        self, catalog: pystac.Catalog, collections_to_add: list[str] | None = None
    ) -> pystac.Catalog:
        """Add PSUP collections to the catalog, all on a unique thread.

        Args:
            catalog (pystac.Catalog): _description_
            collections_to_add (list[str], optional): If the value is None, takes all the collections by default.
                Can only be the following values so far:
                    - "features_datasets"
                    - "omega_mineral_maps"
                    - "omega_data_cubes"
                    - "omega_c_channel_proj"

        Returns:
            pystac.Catalog: _description_
        """
        if collections_to_add is None:
            collections_to_add = [
                "features_datasets",
                "omega_mineral_maps",
                "omega_data_cubes",
                "omega_c_channel_proj",
            ]

        try:
            # Feature collection
            if "features_datasets" in collections_to_add:
                feature_collection = self.create_feature_collection()
                if self.wkt_io is not None:
                    feature_collection = apply_proj(
                        feature_collection,
                        self.wkt_io.pick_sphere_projection_by_body_and_kind(
                            "Mars", "sphere"
                        ),
                    )
                catalog.add_child(feature_collection)
                self.log.debug(
                    f"Collection {feature_collection.id} successfully created!"
                )
                self.log.debug(feature_collection.to_dict())
                memory_snapshot = self.psup_archive.check_memory()
                self.log.debug(str(memory_snapshot))
            else:
                self.log.info("Skipping feature dataset")

            # OMEGA mineral maps
            if "omega_mineral_maps" in collections_to_add:
                self.log.info("Creating OMEGA mineral maps collection")
                omega_mmaps_collection = self.create_omega_mineral_maps_collection()
                if self.wkt_io is not None:
                    omega_mmaps_collection = apply_proj(
                        omega_mmaps_collection,
                        self.wkt_io.pick_sphere_projection_by_body_and_kind(
                            "Mars", "sphere"
                        ),
                    )
                catalog.add_child(omega_mmaps_collection)
                self.log.debug(
                    f"Collection {omega_mmaps_collection.id} successfully created!"
                )
                self.log.debug(omega_mmaps_collection.to_dict())
                memory_snapshot = self.psup_archive.check_memory()
                self.log.debug(str(memory_snapshot))
            else:
                self.log.info("Skipping OMEGA mineral maps")

            # OMEGA data cubes
            if "omega_data_cubes" in collections_to_add:
                self.log.info("Creating OMEGA Data cubes collection")
                omega_data_cubes_builder = OmegaDataCubes(
                    self.psup_archive, log=self.log
                )
                omega_data_cubes_collection = (
                    omega_data_cubes_builder.create_collection(
                        n_limit=self.n_omega_files
                    )
                )

                if self.wkt_io is not None:
                    omega_data_cubes_collection = apply_proj(
                        omega_data_cubes_collection,
                        self.wkt_io.pick_sphere_projection_by_body_and_kind(
                            "Mars", "sphere"
                        ),
                    )

                catalog.add_child(omega_data_cubes_collection)
                self.log.debug(
                    f"Collection {omega_data_cubes_collection.id} successfully created!"
                )
                self.log.debug(omega_data_cubes_collection.to_dict())
                memory_snapshot = self.psup_archive.check_memory()
                self.log.debug(str(memory_snapshot))
            else:
                self.log.info("Skipping OMEGA L2 cubes")

            if "omega_c_channel_proj" in collections_to_add:
                # OMEGA C channel proj
                self.log.info("Creating OMEGA C Channel Proj collection")
                self.log.debug(self.psup_archive)
                omega_c_channel_builder = OmegaCChannelProj(
                    self.psup_archive, log=self.log
                )
                omega_c_channel_collection = omega_c_channel_builder.create_collection(
                    n_limit=self.n_omega_files
                )
                if self.wkt_io is not None:
                    omega_c_channel_collection = apply_proj(
                        omega_c_channel_collection,
                        self.wkt_io.pick_sphere_projection_by_body_and_kind(
                            "Mars", "sphere"
                        ),
                    )
                catalog.add_child(omega_c_channel_collection)
                self.log.debug(
                    f"Collection {omega_c_channel_collection.id} successfully created!"
                )
                self.log.debug(omega_c_channel_collection.to_dict())
                memory_snapshot = self.psup_archive.check_memory()
                self.log.debug(str(memory_snapshot))
            else:
                self.log.info("Skipping OMEGA L3 cubes")

        except KeyboardInterrupt:
            self.log.warning(
                "Stopped collection generation. Use the same command (ie. Ctrl+C) to shut down the process."
            )
        except ReadTimeout as read_err:
            self.log.error(f"[{read_err.__class__.__name__}] {read_err}")
            self.log.error(
                "No response from server. Either retry at a later time or contact support."
            )

        except OutOfMemoryError as oom_err:
            self.log.error(f"[{oom_err.__class__.__name__}] {oom_err}")
            self.log.error(
                "The process' memory consumption ran over the expected threshold!"
            )

        except Exception as e:
            self.log.error("There was a problem during collection generation!")
            self.log.error(f"[{e.__class__.__name__}] {e}")

        finally:
            return catalog

    def create_catalog(
        self, self_contained: bool = True, clean_previous_output: bool = False
    ) -> pystac.Catalog:
        """Creates a catalog over the entire feature selection. The function's goal is to create a brand new
        catalog in a target folder, preferably over the existing one if `clean_previous_output` is set to

        Args:
            self_contained (bool, optional): _description_. Defaults to True.
            clean_previous_output (bool, optional): _description_. Defaults to False.

        Raises:
            FolderNotEmptyError: _description_

        Returns:
            pystac.Catalog: _description_
        """

        # The output folder is expected to ahve a catalog.json instance + the user doesn't want to clean the catalog up
        if not self.io_handler.is_output_folder_empty() and not clean_previous_output:
            raise FolderNotEmptyError(
                "The output folder is not empty. Please clean it first or set `clean_previous_output` to False"
            )
        elif not self.io_handler.is_output_folder_empty() and clean_previous_output:
            self.io_handler.clean_output_folder()

        # Create root catalog for Mars items
        catalog = pystac.Catalog(
            id="mars",
            description="""This test STAC catalog contains Mars data collections and sub-catalogs currently hosted and distributed by\n[PSUP](http://psup.ias.u-psud.fr/sitools/client-user/index.html?project=PLISonMars) (Planetary SUrface Portal).\n\n![Mars](https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Mars_%28white_background%29.jpg/120px-Mars_%28white_background%29.jpg)\n""",
        )

        catalog = cast(pystac.Catalog, apply_ssys(catalog))

        return self._add_collections_wrapper(
            catalog=catalog, self_contained=self_contained
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
            id="features_datasets",
            title="Mars vectorial features",
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
            providers=providers,
        )

        # Apply extensions here
        master_collection = cast(pystac.Collection, apply_ssys(master_collection))

        for feature_name in self.possible_names:
            file_location = self.psup_archive.find_or_download(feature_name)

            self.log.info(f"Found {feature_name} at {file_location}")

            self.log.info(f"Processing {feature_name}.")
            processor = select_processor(
                cast(ProcessorName, feature_name),
                catalog_folder=file_location.parent,
            )
            subcollection = processor.create_collection()
            # Apply extensions here
            subcollection = cast(
                pystac.Collection,
                apply_sci(
                    subcollection,
                    publications=geojson_features[feature_name].publications,
                ),
            )
            master_collection.add_child(subcollection)

        return master_collection

    def create_omega_mineral_maps_collection(self) -> pystac.Collection:
        return omega_maps_collection_generator(self.psup_archive)

    def edit_catalog(self, action: str, self_contained: bool = True) -> pystac.Catalog:
        if self.io_handler.is_output_folder_empty():
            raise FolderEmptyError("The output folder is empty.")
        if (
            not self.io_handler.is_output_folder_empty()
            and not (self.io_handler.output_folder / "catalog.json").exists()
        ):
            raise FileNotFoundError(
                "Output folder isn't empty but `catalog.json` is nowhere to be found."
            )

        catalog = pystac.Catalog.from_file(
            self.io_handler.output_folder / "catalog.json"
        )
        self.log.info(f'Successfully loaded catalog {catalog.id}: "{catalog.title}"')
        collections = catalog.get_collections()
        collection_ids = [collection.id for collection in collections]
        self.log.info(f"Found {len(list(collections))} collections in this catalog.")
        self.log.info(f"Collections: {', '.join(collection_ids)}")

        if action == "add_missing":
            missing_collections = [
                collection_id
                for collection_id in [
                    "features_datasets",
                    "omega_mineral_maps",
                    "omega_data_cubes",
                    "omega_c_channel_proj",
                ]
                if collection_id not in collection_ids
            ]
            return self._add_collections_wrapper(
                catalog=catalog,
                self_contained=self_contained,
                collections_to_add=missing_collections,
            )

        return catalog

    def _add_collections_wrapper(
        self,
        catalog: pystac.Catalog,
        collections_to_add: list[str] | None = None,
        self_contained: bool = True,
    ) -> pystac.Catalog:
        """Wrapper for collection adder that handles the different behaviors from create and edit, as well as
        the execution time and possible exceptions."""
        start_time = time.time()
        try:
            catalog = self._add_collections_to_catalog(
                catalog, collections_to_add=collections_to_add
            )
        except KeyboardInterrupt:
            self.log.warning("Process interrupted by user! Catalog is incomplete.")
        except Exception as e:
            self.log.error(f"A problem occured when generating the catalog: {e}")
        finally:
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

        self.log.info("Checking if catalog is STAC-compliant:")
        try:
            catalog.validate_all()
        except pystac.errors.STACValidationError as e:
            self.log.warning(
                "Validation failed. Some errors were detected during validation."
            )
            self.log.warning(f"See stacktrace for more details: {e}")
        else:
            self.log.info("Your catalog is STAC-compliant!")
        finally:
            return catalog

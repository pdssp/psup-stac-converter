import datetime as dt
import json
import logging
import re
from typing import Any

import numpy as np
from shapely import bounds, box, to_geojson

from psup_stac_converter.extensions import apply_eo
from psup_stac_converter.informations.instruments import omega_bands
from psup_stac_converter.informations.publications import omega_data_cubes
from psup_stac_converter.omega._base import OmegaDataReader
from psup_stac_converter.utils.io import PsupIoHandler


class OmegaDataCubes(OmegaDataReader):
    def __init__(
        self, psup_io_handler: PsupIoHandler, log: logging.Logger | None = None
    ):
        super().__init__(
            psup_io_handler,
            data_type="data_cubes_slice",
            collection_id="urn:pdssp:ias:collection:omega_data_cubes",
            collection_description="""
This dataset contains all the OMEGA observations acquired with the C, L and VIS channels until April 2016, 11, after filtering. Filtering processes have been implemented to remove some instrumental artefacts and observational conditions. Each OMEGA record is available as a `netCDF4.nc` file and an `idl.sav`

Both files contain the cubes of reflectance of the surface at a given longitude, latitude and wavelength $\lambda$. The surface reflectance is defined as $\frac{I(\lambda)}{F \cos(i)}$  where:

- channel $C=[0.93-2.73 \mu m]$; $L=[2.55-5.10 \mu m]$; $\text{Visible}=[0.38-1.05 \mu m]$;
- atmospheric attenuation is corrected (1-5 µm);
- airborne dust scattering is corrected (0.4-2.5 µm and for 5 µm emissivity estimations);
- thermal contribution is removed (> 3 µm); L channel data and VIS channel are co-registered with C channel when available.

Please note that longitudes range from -180 to 180 degrees east.
""",
            publications=omega_data_cubes,
            log=log,
        )
        self.sav_metadata_folder = psup_io_handler.output_folder / "l2_sav"
        self.nc_metadata_folder = psup_io_handler.output_folder / "l2_nc"
        self.log.debug(f".sav metadata folder: {self.sav_metadata_folder}")
        self.log.debug(f".nc metadata folder: {self.nc_metadata_folder}")
        if not self.sav_metadata_folder.exists():
            self.sav_metadata_folder.mkdir()

        if not self.nc_metadata_folder.exists():
            self.nc_metadata_folder.mkdir()

    def create_collection(self):
        """Creates a collection based on the OMEGA datacubes' dataset

                This dataset contains all the OMEGA observations acquired with the C, L and VIS channels until April 2016, 11, after filtering. Filtering processes have been implemented to remove some instrumental artefacts and observational conditions. Each OMEGA record is available as a netCDF4.nc file and an idl.sav

        Both files contain the cubes of reflectance of the surface at a given longitude, latitude and wavelength λ. The surface reflectance is defined as I/F/cos(i) where:

        * channel C=[0.93-2.73 µm]; L=[2.55-5.10 µm]; Visible=[0.38-1.05 µm];
        * atmospheric attenuation is corrected (1-5 µm);
        * airborne dust scattering is corrected (0.4-2.5 µm and for 5 µm emissivity estimations);
        * thermal contribution is removed (> 3 µm); L channel data and VIS channel are co-registered with C channel when available.

        Please note that longitudes range from -180 to 180 degrees east.

                Returns:
                    _type_: _description_
        """
        collection = super().create_collection()

        # Only the C band is needed
        collection = apply_eo(collection, bands=omega_bands)

        return collection

    def extract_sav_info(self, orbit_cube_idx: str) -> dict[str, Any]:
        try:
            orbit_number, cube_number = orbit_cube_idx.split("_")
            sav_info = {"orbit_number": orbit_number, "cube_number": int(cube_number)}
            self.log.debug(f"Opening the sav file for {orbit_cube_idx}")

            # .sav files range from several GB to some KB
            # It is generally not recommended to keep them on local disk
            sav_data = self.open_file(
                orbit_cube_idx, file_extension="sav", on_disk=False
            )
            cube_dims = sav_data["lat"].shape
            em_wl_range = sav_data["wvl"].size

            bbox = box(
                xmin=sav_data["lon"][0, :].min(),
                xmax=sav_data["lon"][0, :].max(),
                ymin=sav_data["lat"][:, 0].min(),
                ymax=sav_data["lat"][:, 0].max(),
            )

            sav_info["dims"] = cube_dims
            sav_info["wavelength_n_values"] = em_wl_range
            sav_info["wavelength_range"] = [
                np.nanmin(sav_data["wvl"]).item(),
                np.nanmax(sav_data["wvl"]).item(),
            ]
            sav_info["footprint"] = json.loads(to_geojson(bbox))
            sav_info["bbox"] = bounds(bbox).tolist()

            # retrieve scalar data
            sav_info["solar_longitude"] = sav_data["solarlong"].item()
            sav_info["data_quality"] = sav_data["data_quality"].item()
            sav_info["pointing_mode"] = sav_data["pointing_mode"].decode().strip('"')
            sav_info["martian_year"] = sav_data["year"].item()
            sav_info["prop_working_channels"] = [
                int(pres_idx) for pres_idx in sav_data["pres"]
            ]
            sav_info["is_target_mars"] = bool(sav_data["tag_ok"] != 0)
            sav_info["is_l_channel_working"] = bool(sav_data["tag_l"] != 0)
            sav_info["is_c_channel_working"] = bool(sav_data["tag_c"] != 0)

            sav_info["martian_time"] = (
                f"""{sav_data["year"]}:{sav_data["solarlong"]}:{np.nanmin(sav_data["heure"])}"""
            )

            # With martian time, is it possible to deduce Earth time?

            # Image dims
            return sav_info

        except OSError as ose:
            self.log.error(f"[{ose.__class__.__name__}] {ose}")
            self.log.error(
                f"""Cube {orbit_cube_idx}'s sav file is too big for the disk."""
            )
        except ValueError as verr:
            self.log.error(f"[{verr.__class__.__name__}] {verr}")
        except Exception as e:
            self.log.error(f"A problem with {orbit_cube_idx} occured")
            self.log.error(f"[{e.__class__.__name__}] {e}")

    def extract_nc_info(self, orbit_cube_idx: str) -> dict[str, Any]:
        try:
            nc_info = {}
            self.log.debug(f"Opening the nc file for {orbit_cube_idx}")

            nc_data = self.open_file(orbit_cube_idx, file_extension="nc", on_disk=False)

            nc_info["creation_date"] = dt.datetime.strptime(
                re.match(
                    r"Created (\d{2}/\d{2}/\d{2})", nc_data.attrs["history"]
                ).group(1),
                "%d/%m/%y",
            ).isoformat()

            nc_data.close()
            return nc_info
        except OSError as ose:
            self.log.error(f"[{ose.__class__.__name__}] {ose}")
            self.log.error(
                f"""Cube {orbit_cube_idx}'s sav file is too big for the disk."""
            )
        except ValueError as verr:
            self.log.error(f"[{verr.__class__.__name__}] {verr}")
        except Exception as e:
            self.log.error(f"A problem with {orbit_cube_idx} occured")
            self.log.error(f"[{e.__class__.__name__}] {e}")

    def create_stac_item(self, orbit_cube_idx: str):
        """
        Information is contained within the IDL.sav files and NetCDF files
        """

        sav_md_state = self.sav_metadata_folder / f"sav_{orbit_cube_idx}.json"
        self.log.debug(f"Opening {sav_md_state}")
        if sav_md_state.exists():
            with open(sav_md_state, "r", encoding="utf-8") as sav_md:
                sav_info = json.load(sav_md)
        else:
            self.log.debug(
                f"{sav_md_state} not found. Creating it from # {orbit_cube_idx}"
            )
            sav_info = self.extract_sav_info(orbit_cube_idx)
            with open(sav_md_state, "w", encoding="utf-8") as sav_md:
                json.dump(sav_info, sav_md)

        # Open NC metadata to complete
        nc_md_state = self.nc_metadata_folder / f"nc_{orbit_cube_idx}.json"
        self.log.debug(f"Opening {nc_md_state}")
        if nc_md_state.exists():
            with open(nc_md_state, "r") as nc_md:
                nc_info = json.load(nc_md)
        else:
            self.log.debug(
                f"{nc_md_state} not found. Creating it from # {orbit_cube_idx}"
            )
            nc_info = self.extract_nc_info(orbit_cube_idx)
            with open(nc_md_state, "w", encoding="utf-8") as nc_md:
                json.dump(nc_info, nc_md)

        # This one is given by the data description
        default_end_datetime = dt.datetime(2016, 4, 11, 0, 0)

        pystac_item = super().create_stac_item(
            orbit_cube_idx,
            timestamp=default_end_datetime,
            footprint=sav_info["footprint"],
            bbox=sav_info["bbox"],
            item_properties={
                k: v
                for k, v in sav_info.items()
                if k
                not in [
                    "footprint",
                    "bbox",
                    "dims",
                    "wavelength_n_values",
                    "wavelength_range",
                ]
            },
        )

        pystac_item.extra_fields["ssys:local_time"] = sav_info["martian_time"]

        pystac_item.assets["sav"].extra_fields["dims"] = sav_info["dims"]
        pystac_item.assets["sav"].extra_fields["wavelength_n_values"] = sav_info[
            "wavelength_n_values"
        ]
        pystac_item.assets["sav"].extra_fields["wavelength_range"] = sav_info[
            "wavelength_range"
        ]

        # NC properties
        pystac_item.assets["nc"].extra_fields["creation_date"] = nc_info[
            "creation_date"
        ]

        # Apply EO extension
        working_bands = [omega_bands[0]]
        if sav_info["is_c_channel_working"]:
            working_bands.append(omega_bands(1))

        if sav_info["is_l_channel_working"]:
            working_bands.append(omega_bands[2])

        pystac_item = apply_eo(pystac_item, bands=working_bands)

        self.log.debug(f"Creating OMEGA data cube item {pystac_item}")
        return pystac_item

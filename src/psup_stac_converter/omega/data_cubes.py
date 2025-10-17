import datetime as dt
import json
import logging
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
            sav_info = {}
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
                np.nanmin(sav_data["wvl"]),
                np.nanmax(sav_data["wvl"]),
            ]
            sav_info["footprint"] = json.loads(to_geojson(bbox))
            sav_info["bbox"] = bounds(bbox).tolist()

            # retrieve scalar data
            sav_info["solar_longitude"] = sav_data["solarlong"]
            sav_info["data_quality"] = sav_data["data_quality"]
            sav_info["pointing_mode"] = sav_data["pointing_mode"]
            sav_info["martian_year"] = sav_data["year"]
            sav_info["prop_working_channels"] = sav_data["pres"]
            sav_info["is_target_mars"] = sav_data["tag_ok"] != 0
            sav_info["is_l_channel_working"] = sav_data["tag_l"] != 0
            sav_info["is_c_channel_working"] = sav_data["tag_c"] != 0

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
            self.log.error(f"""Shape of datacube was {sav_data["ldat_j"].shape}""")
        except Exception as e:
            self.log.error(f"A problem with {orbit_cube_idx} occured")
            self.log.error(f"[{e.__class__.__name__}] {e}")

    def create_stac_item(self, orbit_cube_idx: str):
        """
        Information is contained within the IDL.sav files and NetCDF files
        """
        sav_info = self.extract_sav_info(orbit_cube_idx)
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

        return pystac_item

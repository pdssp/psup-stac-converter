import json
import logging

from shapely import bounds, to_geojson

from psup_stac_converter.extensions import apply_eo
from psup_stac_converter.informations.instruments import omega_bands
from psup_stac_converter.informations.publications import omega_c_channel
from psup_stac_converter.omega._base import OmegaDataReader, OmegaDataTextItem
from psup_stac_converter.utils.io import PsupIoHandler


class OmegaCChannelProj(OmegaDataReader):
    def __init__(
        self, psup_io_handler: PsupIoHandler, log: logging.Logger | None = None
    ):
        super().__init__(
            psup_io_handler,
            data_type="c_channel_slice",
            collection_id="urn:pdssp:ias:collection:omega_c_channel_proj",
            collection_description="""These data cubes have been specifically selected and filtered for studies of the surface mineralogy between 1 and 2.5 µm.

They contain all the OMEGA observations acquired with the C channel after filtering. Filtering processes have been implemented to remove some instrumental artefacts and observational conditions. Each OMEGA record is available as a `netCDF4.nc` file and an `idl.sav`.

Both files contain the cubes of reflectance of the surface at a given longitude, latitude and wavelength λ. The reflectance is defined by the “reflectance factor” $\frac{I(\lambda)}{F \cos(i)}$ where i is the solar incidence angle with $\lambda$ from 0.97 to 2.55 µm (second dimension of the cube with 120 wavelengths). The spectra are corrected for atmospheric and aerosol contributions according to the method described in Vincendon et al. (Icarus, 251, 2015). It therefore corresponds to albedo for a lambertian surface. The first dimension of the cube refers to the length of scan. It can be 32, 64, or 128 pixels. It gives the first spatial dimension. The third dimension refers to the rank of the scan. It is the second spatial dimension.""",
            publications=omega_c_channel,
            log=log,
        )

    def create_collection(self):
        collection = super().create_collection()

        # Only the C band is needed
        collection = apply_eo(collection, bands=[omega_bands[1]])

        return collection

    def create_stac_item(self, orbit_cube_idx):
        text_data: OmegaDataTextItem = self.open_file(
            orbit_cube_idx, "txt", on_disk=True
        )

        footprint = json.loads(to_geojson(text_data.bbox))
        bbox = bounds(text_data.bbox).tolist()

        pystac_item = super().create_stac_item(
            orbit_cube_idx,
            timestamp=text_data.start_time,
            start_datetime=text_data.start_time,
            end_datetime=text_data.stop_time,
            footprint=footprint,
            bbox=bbox,
            item_properties={
                "solar_longitude": text_data.solar_longitude,
                "orbit_number": text_data.orbit_number,
                "cube_number": text_data.cube_number,
                # Would fit more in processing extension
                "data_quality_id": text_data.data_quality_id,
            },
        )

        try:
            self.log.debug(f"Opening the sav file for {orbit_cube_idx}")

            # .sav files range from several GB to some KB
            # It is generally not recommended to keep them on local disk
            sav_data = self.open_file(
                orbit_cube_idx, file_extension="sav", on_disk=False
            )
            x_dim, y_dim = sav_data["longi"].shape

            pystac_item.assets["sav"].extra_fields["map_dimensions"] = (x_dim, y_dim)
        except OSError as ose:
            self.log.error(f"[{ose.__class__.__name__}] {ose}")
            self.log.error(
                f"""Cube {orbit_cube_idx}'s sav file is too big for the disk ({pystac_item.assets["sav"].extra_fields["size"]})."""
            )
        except Exception as e:
            self.log.error(f"A problem with {orbit_cube_idx} occured")
            self.log.error(f"[{e.__class__.__name__}] {e}")

        return pystac_item

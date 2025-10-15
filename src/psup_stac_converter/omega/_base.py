import datetime as dt
import json
import logging
from typing import Any, Literal
from zoneinfo import ZoneInfo

import pandas as pd
import pystac
import scipy.io as sio
import xarray as xr
from pydantic import BaseModel, ConfigDict, computed_field
from pydantic.alias_generators import to_snake
from pystac.extensions.scientific import Publication
from shapely import Polygon, bounds, box, to_geojson
from tqdm.rich import tqdm

from psup_stac_converter.extensions import apply_sci, apply_ssys
from psup_stac_converter.informations.data_providers import providers as data_providers
from psup_stac_converter.settings import create_logger
from psup_stac_converter.utils.io import PsupIoHandler


class OmegaDataTextItem(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    filename: str
    orbit_number: int
    cube_number: int
    start_time: dt.datetime
    stop_time: dt.datetime
    solar_longitude: float
    easternmost_longitude: float
    westernmost_longitude: float
    maximum_latitude: float
    minimum_latitude: float
    data_quality_id: int

    @computed_field
    @property
    def bbox(self) -> Polygon:
        return box(
            xmax=self.easternmost_longitude,
            ymax=self.maximum_latitude,
            xmin=self.westernmost_longitude,
            ymin=self.minimum_latitude,
        )


class OmegaDataReader:
    def __init__(
        self,
        psup_io_handler: PsupIoHandler,
        data_type: Literal["data_cubes_slice", "c_channel_slice"],
        collection_id: str = "",
        license_name: str = "CC-BY-4.0",
        collection_description: str = "",
        publications: list[Publication] = [],
        log: logging.Logger = None,
    ):
        self.io_handler = psup_io_handler
        self.data_type = data_type
        self._omega_data = self._get_omega_data(data_type)
        self.collection_id = collection_id
        self.license_name = license_name
        self.collection_description = collection_description
        self.publications = publications
        if log is None:
            self.log = create_logger(__name__)
        else:
            self.log = log

    @property
    def omega_data(self) -> pd.DataFrame:
        return self._omega_data

    @omega_data.setter
    def omega_data(self, _v: pd.DataFrame):
        raise ValueError(
            "You can't modify `omega_data` without modifying `io_handler` first."
        )

    def _get_omega_data(
        self, data_type: Literal["data_cubes_slice", "c_channel_slice"]
    ) -> pd.DataFrame:
        """Wrapper method retrieving OMEGA cube data

        Args:
            data_type (Literal[&quot;data_cubes_slice&quot;, &quot;c_channel_slice&quot;]): _description_

        Returns:
            pd.DataFrame: _description_
        """
        return self.io_handler.get_omega_data(data_type=data_type)

    @property
    def omega_data_ids(self) -> pd.Index:
        return self.omega_data.sort_values("name").index.unique()

    @property
    def n_elements(self) -> int:
        return self.omega_data_ids.size

    def find_info_by_orbit_cube(
        self,
        orbit_cube_idx: str,
        file_extension: Literal["sav", "nc", "txt"] | None = None,
    ) -> pd.DataFrame:
        if orbit_cube_idx not in self.omega_data.index:
            raise ValueError(
                f'There is no such orbit/cube combination with "{orbit_cube_idx}" in the data.'
            )

        if file_extension is not None:
            omega_info = self.omega_data.loc[
                self.omega_data.index.str.contains(orbit_cube_idx)
                & self.omega_data["extension"].str.contains(file_extension),
                :,
            ]
            if omega_info.empty:
                raise ProcessLookupError(
                    f"{orbit_cube_idx} exists but the info requested with extension .{file_extension} couldn't be found"
                )
            return omega_info

        omega_info = self.omega_data.loc[orbit_cube_idx, :]
        if omega_info.empty:
            raise ProcessLookupError(
                f"{orbit_cube_idx} exists but the info required couldn't be found"
            )

        return omega_info

    def open_file(
        self,
        orbit_cube_idx: str,
        file_extension: Literal["sav", "nc", "txt"],
        on_disk: bool = True,
        text_raw: bool = False,
    ):
        """Opens an asset of a particular OMEGA cube. Allows IDL .sav, NetCDF and text.

        Args:
            orbit_cube_idx (str): _description_
            file_extension (Literal[&quot;sav&quot;, &quot;nc&quot;, &quot;txt&quot;]): _description_
            on_disk (bool, optional): _description_. Defaults to True.
            text_raw (bool, optional): _description_. Defaults to False.

        Raises:
            ValueError: _description_

        Returns:
            _type_: _description_
        """
        if file_extension == "sav":
            return self.open_sav_dataset(orbit_cube_idx, on_disk=on_disk)
        elif file_extension == "nc":
            return self.open_nc_dataset(orbit_cube_idx, on_disk=on_disk)
        elif file_extension == "txt":
            return self.open_txt_metadata(orbit_cube_idx, on_disk=on_disk, raw=text_raw)
        else:
            raise ValueError("The extension can only be 'sav', 'nc' or 'txt'.")

    def open_sav_dataset(
        self, orbit_cube_idx: str, on_disk: bool = True
    ) -> dict[str, Any]:
        """Opens an IDL .sav file

        Args:
            file_href (str): _description_

        Returns:
            dict[str, Any]: _description_
        """
        sav_ds = None
        oc_info = self.find_info_by_orbit_cube(orbit_cube_idx, file_extension="sav")

        if on_disk:
            fp = self.io_handler.find_or_download(oc_info["file_name"].item())
            sav_ds = sio.readsav(fp)
        else:
            with self.io_handler.psup_archive.open_resource(
                oc_info["href"].item()
            ) as sav_file:
                sav_ds = sio.readsav(sav_file.name)

        return sav_ds

    def open_nc_dataset(self, orbit_cube_idx: str, on_disk: bool = True) -> Any:
        """Opens NetCDF4 dataset

        Args:
            file_href (str): _description_

        Returns:
            Any: _description_
        """
        nc_dataset = None
        oc_info = self.find_info_by_orbit_cube(orbit_cube_idx, file_extension="nc")

        if on_disk:
            fp = self.io_handler.find_or_download(oc_info["file_name"].item())
            nc_dataset = xr.open_dataset(fp)
        else:
            with self.io_handler.psup_archive.open_resource(
                oc_info["href"].item()
            ) as nc_file:
                nc_dataset = xr.open_dataset(nc_file.name)

        return nc_dataset

    def open_txt_metadata(
        self, orbit_cube_idx: str, on_disk: bool = True, raw: bool = False
    ) -> str | OmegaDataTextItem:
        """Opens the text metadata for a given OMEGA cube when available

        **Note:** for OMEGA C Channel projections only, as text metadata isn't
        available for Data Cubes.

        Args:
            orbit_cube_idx (str): _description_
            on_disk (bool, optional): _description_. Defaults to True.
            raw (bool, optional): _description_. Defaults to False.

        Returns:
            str | OmegaDataTextItem: The result. Either the raw text if `raw=True` or
            OmegaDataTextItem
        """
        oc_info = self.find_info_by_orbit_cube(orbit_cube_idx, file_extension="txt")
        textinfo = ""

        if on_disk:
            fp = self.io_handler.find_or_download(oc_info["file_name"].item())
            textinfo = fp.read_text()
        else:
            with self.io_handler.psup_archive.open_resource(
                oc_info["href"].item()
            ) as txt_file:
                textinfo = txt_file.read()

        if raw:
            return textinfo

        text_obj = {}
        for line in textinfo.strip().split("\n"):
            k, v = line.split("=")
            k = "_".join(k.split())
            k = to_snake(k.strip())
            v = v.strip()

            text_obj[to_snake(k.strip())] = v.strip()

        return OmegaDataTextItem.model_validate_json(json.dumps(text_obj))

    def find_spatial_extent(self) -> pystac.SpatialExtent:
        return pystac.SpatialExtent(bboxes=[[-180.0, -90.0, 180.0, 90.0]])

    def find_temporal_extent(self) -> pystac.TemporalExtent:
        pystac.TemporalExtent(
            intervals=[
                [
                    pd.Timestamp.min.to_pydatetime(),
                    pd.Timestamp.max.to_pydatetime(),
                ]
            ]
        )

    def create_collection(self) -> pystac.Collection:
        spatial_extent = self.find_spatial_extent()
        temporal_extent = self.find_temporal_extent()
        collection_extent = pystac.Extent(
            spatial=spatial_extent, temporal=temporal_extent
        )

        collection = pystac.Collection(
            id=self.collection_id,
            extent=collection_extent,
            license=self.license_name,
            description=self.collection_description,
            providers=data_providers,
        )

        collection = apply_ssys(collection)
        collection = apply_sci(collection, publications=self.publications)

        for omega_data_idx in tqdm(self.omega_data_ids, total=self.n_elements):
            omega_data_item = self.create_stac_item(omega_data_idx)
            collection.add_item(omega_data_item)

        return collection

    def create_stac_item(self, orbit_cube_idx: str, **kwargs) -> pystac.Item:
        """Creates a STAC item based on the common properties of OMEGA cubes

        Args:
            orbit_cube_idx (str): _description_

        Returns:
            pystac.Item: _description_
        """
        sav_info = self.find_info_by_orbit_cube(orbit_cube_idx, file_extension="sav")
        nc_info = self.find_info_by_orbit_cube(orbit_cube_idx, file_extension="nc")

        footprint = kwargs.get(
            "footprint", json.loads(to_geojson(box(-180.0, -90.0, 180.0, 90.0)))
        )
        bbox = kwargs.get("bbox", bounds(box(-180.0, -90.0, 180.0, 90.0)).tolist())
        timestamp = kwargs.get("timestamp", dt.datetime.now(tz=ZoneInfo("UTC")))
        item_properties = kwargs.get("item_properties", {})

        pystac_item = pystac.Item(
            id=orbit_cube_idx,
            properties=item_properties,
            geometry=footprint,
            bbox=bbox,
            datetime=timestamp,
            start_datetime=kwargs.get("start_datetime", None),
            end_datetime=kwargs.get("end_datetime", None),
        )

        # assets
        nc_asset = pystac.Asset(
            href=nc_info["href"].item(),
            media_type=pystac.MediaType.NETCDF,
            roles=["data"],
            description="NetCDF data",
            extra_fields={"size": nc_info["h_total_size"].item()},
        )
        pystac_item.add_asset("nc", nc_asset)

        sav_asset = pystac.Asset(
            href=sav_info["href"].item(),
            media_type=pystac.MediaType.TEXT,
            roles=["data"],
            description="IDL .sav data",
            extra_fields={"size": sav_info["h_total_size"].item()},
        )
        pystac_item.add_asset("sav", sav_asset)

        # extensions
        pystac_item = apply_ssys(pystac_item)
        # EO only if data allows it

        # common metadata
        pystac_item.common_metadata.mission = "mex"
        pystac_item.common_metadata.instruments = ["omega"]

        return pystac_item

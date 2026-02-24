import datetime as dt
import json
import logging
from typing import Any, Literal, cast
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pystac
import scipy.io as sio
import xarray as xr
from pydantic import BaseModel, ConfigDict, computed_field
from pydantic.alias_generators import to_snake
from pystac.extensions.datacube import DatacubeExtension, Dimension, Variable
from pystac.extensions.scientific import Publication
from shapely import Polygon, bounds, box, to_geojson
from tqdm.rich import tqdm

from psup_stac_converter.exceptions import (
    FileExtensionError,
    OmegaCubeDataMissingError,
    OmegaOrbitCubeIndexNotFoundError,
    PropertySetterError,
)
from psup_stac_converter.extensions import apply_sci, apply_ssys
from psup_stac_converter.informations.data_providers import providers as data_providers
from psup_stac_converter.settings import create_logger
from psup_stac_converter.utils.file_utils import convert_arr_to_thumbnail
from psup_stac_converter.utils.io import PsupIoHandler
from psup_stac_converter.utils.models import (
    CubedataVariable,
    HorizontalSpatialRasterDimension,
    VerticalSpatialRasterDimension,
)


class SpecialObjectEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Dimension) or isinstance(o, Variable):
            return o.to_dict()
        return super().default(o)


def reformat_nc_info(nc_info: dict[str, Any]) -> dict[str, Any]:
    """Opens previously extracted NetCDF4 datacube info for
    catalog input

    Args:
        nc_info (dict[str, Any]): _description_

    Returns:
        dict[str, Any]: _description_
    """
    for k, v in nc_info["variables"].items():
        nc_info["variables"][k] = Variable(properties={**v})
    for k, v in nc_info["dimensions"].items():
        nc_info["dimensions"][k] = Dimension(properties={**v})

    return nc_info


def find_step_from_values(vals: np.ndarray) -> float | None:
    """Identifies the step from the array's values by evaluating
    the difference between the current and previous step. If the function
    finds an unique value, it means the step is regular and taken into
    account.
    """
    steps = vals[1:] - vals[:-1]
    unique_steps = np.unique(steps)
    if unique_steps.size > 1 or unique_steps.size == 0:
        return None
    return unique_steps.item()


def select_rgb_from_xarr(ds: xr.Dataset, attrib: str = "Reflectance") -> np.ndarray:
    channels = [
        ds.wavelength.size // 2 - ds.wavelength.size // 3,
        ds.wavelength.size // 2,
        ds.wavelength.size // 2 + ds.wavelength.size // 3,
    ]
    return getattr(ds.isel(wavelength=channels), attrib).values


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
        processing_level: Literal["L2", "L3"],
        dim_names: tuple[str, str, str],
        metadata_folder_prefix: str,
        collection_id: str = "",
        license_name: str = "CC-BY-4.0",
        collection_description: str = "",
        publications: list[Publication] = [],
        log: logging.Logger | None = None,
    ):
        self.io_handler = psup_io_handler
        self.data_type = data_type
        self.processing_level = processing_level
        self.dim_names = dim_names
        self.metadata_folder_prefix = metadata_folder_prefix
        self._omega_data = self._get_omega_data(data_type)
        self.collection_id = collection_id
        self.license_name = license_name
        self.collection_description = collection_description
        self.publications = publications
        if log is None:
            self.log = create_logger(__name__)
        else:
            self.log = log

        self.sav_metadata_folder = (
            psup_io_handler.output_folder / f"{self.metadata_folder_prefix}sav"
        )
        self.nc_metadata_folder = (
            psup_io_handler.output_folder / f"{self.metadata_folder_prefix}nc"
        )
        self.thumbnail_folder = (
            psup_io_handler.output_folder / f"{self.metadata_folder_prefix}thumbnail"
        )
        self.thumbnail_dims = (256, 256)
        self.log.debug(f".sav metadata folder: {self.sav_metadata_folder}")
        self.log.debug(f".nc metadata folder: {self.nc_metadata_folder}")
        self.log.debug(f"Folder for thumbnails: {self.thumbnail_folder}")
        if not self.sav_metadata_folder.exists():
            self.sav_metadata_folder.mkdir()

        if not self.nc_metadata_folder.exists():
            self.nc_metadata_folder.mkdir()

        if not self.thumbnail_folder.exists():
            self.thumbnail_folder.mkdir()

    @property
    def omega_data(self) -> pd.DataFrame:
        return self._omega_data

    @omega_data.setter
    def omega_data(self, _v: pd.DataFrame):
        raise PropertySetterError(
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

    def get_omega_data_ids(self, n_limit: int | None = None) -> pd.Index:
        if n_limit is None:
            return self.omega_data_ids
        return self.omega_data_ids[:n_limit]

    def __str__(self) -> str:
        return (
            f"[{self.__class__.__name__}] {self.n_elements} elements\n{self.io_handler}"
        )

    def find_info_by_orbit_cube(
        self,
        orbit_cube_idx: str,
        file_extension: Literal["sav", "nc", "txt"] | None = None,
    ) -> pd.DataFrame:
        if orbit_cube_idx not in self.omega_data.index:
            raise OmegaOrbitCubeIndexNotFoundError(
                f'There is no such orbit/cube combination with "{orbit_cube_idx}" in the data.'
            )

        if file_extension is not None:
            omega_info = self.omega_data.loc[
                self.omega_data.index.str.contains(orbit_cube_idx)
                & self.omega_data["extension"].str.contains(file_extension),
                :,
            ]
            if omega_info.empty:
                raise OmegaCubeDataMissingError(
                    f"{orbit_cube_idx} exists but the info requested with extension .{file_extension} couldn't be found"
                )
            return omega_info

        omega_info = self.omega_data.loc[[orbit_cube_idx], :]
        if omega_info.empty:
            raise OmegaCubeDataMissingError(
                f"{orbit_cube_idx} exists but the info required couldn't be found"
            )

        return omega_info

    def open_file(
        self,
        orbit_cube_idx: str,
        file_extension: Literal["sav", "nc", "txt"],
        on_disk: bool = True,
        text_raw: bool = False,
    ) -> Any:
        """Opens an asset of a particular OMEGA cube. Allows IDL .sav, NetCDF and text.

        Args:
            orbit_cube_idx (str): OMEGA data ID of the item
            file_extension (Literal[&quot;sav&quot;, &quot;nc&quot;, &quot;txt&quot;]): The extension of the file.
            Can be a `.txt` text (only available with OMEGA C Channel data), an IDL `.sav` file or a NetCDF `.nc`file.
            on_disk (bool, optional): _description_. Defaults to True.
            text_raw (bool, optional): Either returns the text `.txt`file as it is (str) if left to True, or as an
            interpreted object of left to False. Defaults to False.

        Raises:
            FileExtensionError: If the extension isn't recognized

        Returns:
            OmegaDataTextItem | dict[str, Any] | str | xr.Dataset: The opened file. The type depends of the extension.
        """
        if file_extension == "sav":
            return self.open_sav_dataset(orbit_cube_idx, on_disk=on_disk)
        elif file_extension == "nc":
            return self.open_nc_dataset(orbit_cube_idx, on_disk=on_disk)
        elif file_extension == "txt":
            return self.open_txt_metadata(orbit_cube_idx, on_disk=on_disk, raw=text_raw)
        else:
            raise FileExtensionError(["sav", "nc", "txt"], file_extension)

    def open_sav_dataset(
        self, orbit_cube_idx: str, on_disk: bool = True
    ) -> dict[str, Any]:
        """Opens an IDL .sav file as a dict of attributes

        Args:
            orbit_cube_idx (str): OMEGA data ID of the item
            on_disk (bool, optional): Whether the file should be downloaded on the local
            disk or not. Defaults to True.

        Returns:
            dict[str, Any]: An IDL AttrDict of the.sav file
        """
        sav_ds = None
        oc_info = self.find_info_by_orbit_cube(orbit_cube_idx, file_extension="sav")

        self.log.debug(f"finding info related to {orbit_cube_idx}. On disk? {on_disk}")
        if on_disk:
            fp = self.io_handler.find_or_download(oc_info["file_name"].item())
            sav_ds = sio.readsav(fp)
        else:
            with self.io_handler.psup_archive.open_resource(
                oc_info["href"].item()
            ) as sav_file:
                sav_ds = sio.readsav(sav_file.name)

        return sav_ds

    def open_nc_dataset(self, orbit_cube_idx: str, on_disk: bool = True) -> xr.Dataset:
        """Opens NetCDF4 dataset using the XArray package

        Args:
            orbit_cube_idx (str): OMEGA data ID of the item
            on_disk (bool, optional): Whether the file should be downloaded on the local
            disk or not. Defaults to True.

        Returns:
            xr.Dataset: The NetCDF dataset under an xarray dataset.
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
            orbit_cube_idx (str): the ID of the OMEGA data cube
            on_disk (bool, optional): Whether the file should be saved locally or not. Useful for
            saved states. Defaults to True.
            raw (bool, optional): Whether the file should be returned as str or directly intepreted
            as an object if left to `False`. Defaults to False.

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
                with self.io_handler.psup_archive.open_resource(
                    oc_info["href"].item()
                ) as txt_file:
                    raw_txt = txt_file.read()
                    if isinstance(raw_txt, (bytes, bytearray)):
                        textinfo = raw_txt.decode("utf-8", errors="replace")
                    else:
                        textinfo = str(raw_txt)

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
        """Assesses the spatial extent of the collection (the whole planet by default)

        Returns:
            pystac.SpatialExtent: A SpatialExtent object for the collection
        """
        return pystac.SpatialExtent(bboxes=[[-180.0, -90.0, 180.0, 90.0]])

    def find_temporal_extent(self) -> pystac.TemporalExtent:
        """Assesses the spatial extent of the collection (the extrema defined
        by `pandas.Timestamp`by default)

        Returns:
            pystac.TemporalExtent: A TemporalExtent object for the collection
        """
        return pystac.TemporalExtent(
            intervals=[
                [
                    pd.Timestamp.min.to_pydatetime(),
                    pd.Timestamp.max.to_pydatetime(),
                ]
            ]
        )

    def create_collection(self, n_limit: int | None = None) -> pystac.Collection:
        """Creates a STAC collection based over the OMEGA data series.

        Returns:
            pystac.Collection: The corresponding STAC collection
        """
        spatial_extent = self.find_spatial_extent()
        temporal_extent = self.find_temporal_extent()
        collection_extent = pystac.Extent(
            spatial=spatial_extent, temporal=temporal_extent
        )

        collection = pystac.Collection(
            title=f"OMEGA data cubes ({self.processing_level})",
            id=self.collection_id,
            extent=collection_extent,
            license=self.license_name,
            description=self.collection_description,
            providers=data_providers,
        )

        collection = cast(pystac.Collection, apply_ssys(collection))
        collection = cast(
            pystac.Collection, apply_sci(collection, publications=self.publications)
        )
        # TODO: make a pystac extension for processing
        # collection.extra_fields["processing:level"] = self.processing_level

        for omega_data_idx in tqdm(
            self.get_omega_data_ids(n_limit=n_limit),
            total=n_limit if n_limit else self.n_elements,
        ):
            try:
                omega_data_item = self.create_stac_item(omega_data_idx)
                collection.add_item(omega_data_item)
                self.log.debug(f"Created item for cube # {omega_data_item}")
            except Exception as e:
                self.log.error(
                    f"An unexpected error occured: [{e.__class__.__name__}] {e}"
                )
                self.log.error(f"{omega_data_idx} skipped!")

        return collection

    def create_stac_item(self, orbit_cube_idx: str, **kwargs) -> pystac.Item:
        """Creates a STAC item based on the common properties of OMEGA cubes.

        Args:
            orbit_cube_idx (str): The ID of the data cube

        Returns:
            pystac.Item: The corresponding item of the orbit-cube ID
        """

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
        # NetCDF4 data
        try:
            self.log.debug(f"Creating NetCDF asset for # {orbit_cube_idx}")
            nc_info = self.find_info_by_orbit_cube(orbit_cube_idx, file_extension="nc")
            nc_asset = pystac.Asset(
                href=nc_info["href"].item(),
                media_type=pystac.MediaType.NETCDF,
                roles=["data"],
                description="NetCDF data",
                extra_fields={"size": nc_info["h_total_size"].item()},
            )
            pystac_item.add_asset("nc", nc_asset)
            self.log.debug(f"{nc_asset} successfully added: {nc_asset.to_dict()}")
        except OmegaCubeDataMissingError:
            self.log.warning(f"NetCDF file not found for {orbit_cube_idx}. Skipping.")

        # IDL.sav data
        try:
            self.log.debug(f"Creating IDL.sav asset for # {orbit_cube_idx}")
            sav_info = self.find_info_by_orbit_cube(
                orbit_cube_idx, file_extension="sav"
            )
            sav_asset = pystac.Asset(
                href=sav_info["href"].item(),
                media_type=pystac.MediaType.GEOTIFF,
                roles=["data"],
                description="IDL .sav data",
                extra_fields={"size": sav_info["h_total_size"].item()},
            )
            pystac_item.add_asset("sav", sav_asset)
            self.log.debug(f"{sav_asset} successfully added: {sav_asset.to_dict()}")
        except OmegaCubeDataMissingError:
            self.log.warning(f"IDL.sav not found for {orbit_cube_idx}. Skipping.")

        # Add created thumbnail as an asset
        thumbnail_location = (
            self.thumbnail_folder
            / f"{orbit_cube_idx}_{self.thumbnail_dims[0]}x{self.thumbnail_dims[1]}.png"
        )

        # Normally the thumbnail should be generated
        # but if not, the file is open
        if not thumbnail_location.exists():
            try:
                thumbnail_strategy = "mean"
                self.log.debug(
                    f"{thumbnail_location} doesn't exist. Creating thumbnail based on {thumbnail_strategy} strategy."
                )
                nc_data = self.open_file(orbit_cube_idx, "nc", on_disk=False)

                # define thumbnail strategy
                # By default, takes the reflectance cube
                self.make_thumbnail(
                    orbit_cube_idx=orbit_cube_idx,
                    data=select_rgb_from_xarr(nc_data),
                    dims=self.thumbnail_dims,
                )

                # Thumbnail
                thumbn_asset = pystac.Asset(
                    href=thumbnail_location.as_posix(),
                    media_type=pystac.MediaType.PNG,
                    roles=["thumbnail"],
                    description="PNG thumbnail preview for visualizations",
                )
                pystac_item.add_asset("thumbnail", thumbn_asset)
                self.log.debug(f"Added {thumbn_asset} to item.")
            except OSError as ose:
                self.log.error(f"[{ose.__class__.__name__}] {ose}")
                self.log.error(
                    f"""Either cube {orbit_cube_idx}'s sav file is too big for the disk or
                    the file is corrupted. Check exception for details."""
                )
            except ValueError as verr:
                self.log.error(f"[{verr.__class__.__name__}] {verr}")
            except Exception as e:
                self.log.error(f"A problem with {orbit_cube_idx} occured")
                self.log.error(f"[{e.__class__.__name__}] {e}")
            finally:
                nc_data.close()
        else:
            # Thumbnail
            thumbn_asset = pystac.Asset(
                href=thumbnail_location.as_posix(),
                media_type=pystac.MediaType.PNG,
                roles=["thumbnail"],
                description="PNG thumbnail preview for visualizations",
            )
            pystac_item.add_asset("thumbnail", thumbn_asset)
            self.log.debug(f"Added {thumbn_asset} to item.")

        # extensions
        pystac_item = cast(pystac.Item, apply_ssys(pystac_item))

        # apply cubedata
        self.log.debug("Applying DatacubeExtension")
        cubedata = self.retrieve_nc_info_from_saved_state(orbit_cube_idx=orbit_cube_idx)
        self.log.debug(f"Loading: {cubedata}")
        if cubedata:
            dc_ext = DatacubeExtension.ext(pystac_item, add_if_missing=True)

            # This operation prevents the key from finding itself attached to "Variables" and "Dimensions"
            dc_dimensions: dict[str, Dimension] = {
                k: Dimension.from_dict(v.to_dict()[k])
                for k, v in cubedata["dimensions"].items()
            }
            dc_variables: dict[str, Variable] = {
                k: Variable.from_dict(v.to_dict()[k])
                for k, v in cubedata["variables"].items()
            }

            dc_ext.apply(dimensions=dc_dimensions, variables=dc_variables)

            for extra_name, extra_value in cubedata["extras"].items():
                pystac_item.assets["nc"].extra_fields[extra_name] = extra_value
        else:
            self.log.warning(f"Cubedata for {orbit_cube_idx} appears to be empty.")

        # common metadata
        pystac_item.common_metadata.mission = "mex"
        pystac_item.common_metadata.instruments = ["omega"]
        self.log.debug(f"Created item from base method {pystac_item}")

        return pystac_item

    def find_cubedata_from_ncfile(
        self, orbit_cube_idx: str, thumbnail_strategy: str = "mean"
    ) -> dict[str, dict[str, Dimension | Variable]]:
        """From the NetCDF file, extracts the cubedata information needed for the
        generated STAC item.

        Args:
            orbit_cube_idx (str): the ID of the orbit cube

        Returns:
            dict[str, dict[str, Dimension | Variable]]: A dict containing
            "dimensions", "variables" and "extras" as main keys
        """
        dimensions = {}
        variables = {}
        extras = {}

        try:
            self.log.debug(f"Opening the nc file for {orbit_cube_idx}")

            nc_data = cast(
                xr.Dataset,
                self.open_file(orbit_cube_idx, file_extension="nc", on_disk=False),
            )

            # Start with the variables
            for data_var_name in nc_data.data_vars.keys():
                data_attrs = nc_data.data_vars[data_var_name].attrs
                if "valid_min" in data_attrs and "valid_max" in data_attrs:
                    # The data is an array
                    # Don't pass any values (too many) and pass the range given
                    extent = [
                        data_attrs["valid_min"].item(),
                        data_attrs["valid_max"].item(),
                    ]
                    attr_values = None
                else:
                    # A scalar, no range but values
                    extent = None
                    attr_values = [nc_data.data_vars[data_var_name].values.item()]
                var_model = CubedataVariable(
                    description=data_attrs["long_name"],
                    type="data",
                    dimensions=list(self.dim_names),
                    unit=data_attrs["units"],
                    extent=extent,
                    values=attr_values,
                )
                self.log.debug(f"{var_model} created!")
                variables[data_var_name] = Variable(
                    properties={data_var_name: var_model.model_dump(exclude_none=True)}
                )

            # ... Then move on with the dimensions
            for data_dim_name in nc_data.coords:
                dim_attrs = nc_data.coords[data_dim_name].attrs
                dim_x, dim_y, dim_z = self.dim_names
                if data_dim_name in [dim_x, dim_y]:
                    dim_obj = HorizontalSpatialRasterDimension(
                        axis=dim_attrs["axis"].lower(),
                        extent=[
                            dim_attrs["valid_min"].item(),
                            dim_attrs["valid_max"].item(),
                        ],
                        unit=dim_attrs["units"],
                        step=find_step_from_values(
                            nc_data.coords[data_dim_name].values
                        ),
                        description=dim_attrs["long_name"],
                    )
                elif data_dim_name == dim_z:
                    dim_obj = VerticalSpatialRasterDimension(
                        extent=[
                            dim_attrs["valid_min"].item(),
                            dim_attrs["valid_max"].item(),
                        ],
                        unit=dim_attrs["units"],
                        step=find_step_from_values(
                            nc_data.coords[data_dim_name].values
                        ),
                        description=dim_attrs["long_name"],
                    )
                dim_var = CubedataVariable(
                    dimensions=[dim_attrs["axis"].lower()],
                    type="auxiliary",
                    extent=[
                        dim_attrs["valid_min"].item(),
                        dim_attrs["valid_max"].item(),
                    ],
                    unit=dim_attrs["units"],
                    description=dim_attrs["long_name"],
                )

                variables[data_dim_name] = Variable(
                    properties={data_dim_name: dim_var.model_dump(exclude_none=True)}
                )
                dimensions[data_dim_name] = Dimension(
                    properties={data_dim_name: dim_obj.model_dump(exclude_none=True)}
                )

            # Add some extras if you want
            extras = self.find_extra_nc_data(nc_data)

            # define thumbnail strategy
            # By default, takes the reflectance cube
            self.make_thumbnail(
                orbit_cube_idx=orbit_cube_idx,
                data=select_rgb_from_xarr(nc_data),
                dims=self.thumbnail_dims,
            )

            nc_data.close()
        except OSError as ose:
            self.log.error(f"[{ose.__class__.__name__}] {ose}")
            self.log.error(
                f"""Either cube {orbit_cube_idx}'s sav file is too big for the disk or
                the file is corrupted. Check exception for details."""
            )
        except ValueError as verr:
            self.log.error(f"[{verr.__class__.__name__}] {verr}")
        except Exception as e:
            self.log.error(f"A problem with {orbit_cube_idx} occured")
            self.log.error(f"[{e.__class__.__name__}] {e}")
        finally:
            nc_data.close()

        self.log.debug(f"Obtained dimensions {dimensions}")
        self.log.debug(f"Obtained variables {variables}")
        return {"dimensions": dimensions, "variables": variables, "extras": extras}

    def find_extra_nc_data(self, nc_data: xr.Dataset) -> dict[str, Any]:
        return {}

    def retrieve_nc_info_from_saved_state(self, orbit_cube_idx: str) -> dict[str, Any]:
        nc_md_state = self.nc_metadata_folder / f"nc_{orbit_cube_idx}.json"
        self.log.debug(f"Opening {nc_md_state}")
        if nc_md_state.exists():
            with open(nc_md_state, "r", encoding="utf-8") as nc_md:
                nc_info = json.load(nc_md)
                nc_info = reformat_nc_info(nc_info)
                self.log.debug(f"nc_info loaded with {nc_info}")
            if not nc_info:
                nc_md_state.unlink()
                return self.retrieve_nc_info_from_saved_state(
                    orbit_cube_idx=orbit_cube_idx
                )

        else:
            self.log.debug(
                f"{nc_md_state} not found. Creating it from # {orbit_cube_idx}"
            )
            try:
                nc_info = self.find_cubedata_from_ncfile(orbit_cube_idx=orbit_cube_idx)
                with open(nc_md_state, "w", encoding="utf-8") as nc_md:
                    json.dump(nc_info, nc_md, cls=SpecialObjectEncoder)
                self.log.debug(f"{nc_md_state} with {nc_info} created!")
            except Exception as e:
                self.log.warning(
                    f"Couldn't save .nc information for # {orbit_cube_idx} because of the following: {e}"
                )
                nc_info = {}

        return nc_info

    def make_thumbnail(
        self,
        orbit_cube_idx: str,
        data: np.ndarray,
        dims: tuple[int, int],
        mode: Literal["L", "RGB", "RGBA"] = "RGB",
        cmap: str | None = None,  # left at none for composite
        fmt: str = "png",
    ):
        """Creates a thumbnail for a datacube out of one of its 2D data arrays.

        Args:
            orbit_cube_idx (str): _description_
            data (np.ndarray): _description_
            dims (tuple[int, int]): _description_
            mode (str, optional): _description_. Defaults to "RGB".
            cmap (str, optional): _description_. Defaults to None.
            fmt (str, optional): _description_. Defaults to "png".
        """
        self.log.debug(f"Converting cube {orbit_cube_idx} to thumbnail.")
        thumbnail = convert_arr_to_thumbnail(
            data=data, resize_dims=dims, mode=mode, cmap=cmap
        )
        self.log.debug(f"""Saving as {orbit_cube_idx}_{dims[0]}x{dims[1]}.{fmt}""")
        thumbnail.save(
            self.thumbnail_folder / f"{orbit_cube_idx}_{dims[0]}x{dims[1]}.{fmt}"
        )

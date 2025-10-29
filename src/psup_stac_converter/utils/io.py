import datetime as dt
import logging
import re
from pathlib import Path
from typing import Any, Iterator, Literal

import pandas as pd
import scipy.io as sio
import xarray as xr
from pydantic import BaseModel, HttpUrl
from rich.console import Console
from rich.tree import Tree

from psup_stac_converter.exceptions import FolderNotEmptyError, ValueNotAcceptedError
from psup_stac_converter.settings import Settings, create_logger
from psup_stac_converter.utils.downloader import Downloader, PsupArchive
from psup_stac_converter.utils.formatting import walk_directory

console = Console()


class WktProjectionItem(BaseModel):
    created_at: dt.datetime
    id: str
    solar_body: str
    datum_name: str
    ellipsoid_name: str
    projection_name: str
    wkt: str


class IoHandler:
    def __init__(
        self,
        input_folder: Path | None = None,
        output_folder: Path | None = None,
        log: logging.Logger | None = None,
    ):
        if log is None:
            self.log = create_logger(__name__)
        else:
            self.log = log
        if input_folder is None:
            input_folder = Settings().raw_data_path
        else:
            self.log.warning(
                f"Make sure you don't commit {input_folder} to version control"
            )
        if output_folder is None:
            output_folder = Settings().output_data_path
        else:
            self.log.warning(
                f"Make sure you don't commit {output_folder} to version control"
            )

        self._input_folder = input_folder
        self._output_folder = output_folder

    @property
    def input_folder(self) -> Path:
        return self._input_folder

    @property
    def output_folder(self) -> Path:
        return self._output_folder

    @input_folder.setter
    def input_folder(self, _v: Path):
        if _v is None:
            raise ValueError("input_folder must not be None")
        self.log.warning(f"Make sure you don't commit {_v} to version control")
        self._input_folder = _v

    @output_folder.setter
    def output_folder(self, _v: Path):
        if _v is None:
            raise ValueError("output_folder must not be None")
        self.log.warning(f"Make sure you don't commit {_v} to version control")
        self._output_folder = _v

    def count_input_elements(self) -> int:
        count = 0
        for _, dirs, files in self.input_folder.walk(on_error=print):
            count += len(dirs)
            count += len(files)
        return count

    def count_output_elements(self) -> int:
        count = 0
        for _, dirs, files in self.output_folder.walk(on_error=print):
            count += len(dirs)
            count += len(files)
        return count

    def is_input_folder_empty(self) -> bool:
        return self.count_input_elements() == 0

    def is_output_folder_empty(self) -> bool:
        return self.count_output_elements() == 0

    def show_input_folder(self):
        tree = Tree(self.input_folder.as_posix())
        walk_directory(self.input_folder, tree)
        console.print(tree)

    def show_output_folder(self):
        tree = Tree(self.output_folder.as_posix())
        walk_directory(self.output_folder, tree)
        console.print(tree)

    def download_data(self, file_path: str):
        if not self.is_input_folder_empty():
            raise FolderNotEmptyError("The input folder is not empty!")
        downloader = Downloader(file_path)
        downloader.local_download(output_folder=self.input_folder)

    def all_input_files_from_ext(self, extension: str) -> Iterator[Path]:
        return self.input_folder.rglob(f"*.{extension}")

    def all_output_files_from_ext(self, extension: str) -> Iterator[Path]:
        return self.output_folder.rglob(f"*.{extension}")

    def clean_output_folder(self):
        self.log.warning(
            f"This action will remove the contents of {self.output_folder}"
        )
        for root, dirs, files in self.output_folder.walk(top_down=False):
            for name in files:
                (root / name).unlink()
            for name in dirs:
                (root / name).rmdir()

    def __str__(self):
        return f"""Entry: {self.input_folder}
        Target: {self.output_folder}
        """


class PsupIoHandler(IoHandler):
    def __init__(self, archive_file: Path, input_folder=None, output_folder=None):
        super().__init__(input_folder, output_folder)
        self.psup_archive = PsupArchive(archive_file)

    def save_all(self, auto_valid: bool = False, raise_on_exists: bool = False):
        self.psup_archive.save_all_on_disk(
            self.output_folder, auto_valid=auto_valid, raise_on_exists=raise_on_exists
        )

    def save_files(
        self,
        file_names: list[str],
        auto_valid: bool = False,
        raise_on_exists: bool = False,
    ):
        self.psup_archive.save_slice_on_disk(
            self.output_folder,
            filters=[("file_name", file_names)],
            auto_valid=auto_valid,
            raise_on_exists=raise_on_exists,
        )

    def save_file(
        self,
        file_name: str,
    ):
        self.psup_archive.save_resource_on_disk(
            file_name=file_name, dest_folder=self.output_folder
        )

    def find_by_file(self, file_name: str) -> tuple[Path, bool]:
        """Finds a file by its name.

        Returns:
            tuple[Path, bool]: The path of the file and whether it exists or not
        """
        archive_slice = self.psup_archive.slice_by_one(
            by="file_name", criteria="^" + re.escape(file_name) + "$", set_regex=True
        )
        if archive_slice is None:
            raise ValueError(f"The archive has no file named {file_name} in it.")

        rel_path = archive_slice.iloc[0]["rel_path"]
        full_path = self.output_folder / Path(rel_path)
        return full_path, full_path.exists()

    def find_or_download(self, file_name: str) -> Path:
        fp_on_disk, exists = self.find_by_file(file_name=file_name)
        if not exists:
            self.save_file(file_name)
        return fp_on_disk

    def find_file_remote_path(self, file_name: str) -> HttpUrl:
        slice = self.psup_archive.slice_by_one("file_name", file_name)
        if slice is None:
            raise ValueError(f"Couldn't find any data with file name {file_name}")

        slice = slice.drop_duplicates(subset=["file_name"]).squeeze()
        server_ref = slice["href"]
        return HttpUrl(url=server_ref)

    def get_omega_data(
        self, data_type: Literal["data_cubes_slice", "c_channel_slice"]
    ) -> pd.DataFrame:
        """Wrapper method retrieving OMEGA cube data

        Args:
            data_type (Literal[&quot;data_cubes_slice&quot;, &quot;c_channel_slice&quot;]): _description_

        Returns:
            pd.DataFrame: _description_
        """
        return self.psup_archive.get_omega_data(data_type=data_type)

    def open_sav_dataset(self, file_href: str) -> dict[str, Any]:
        """Opens an IDL .sav file

        Args:
            file_href (str): _description_

        Returns:
            dict[str, Any]: _description_
        """
        sav_ds = None

        with self.psup_archive.open_resource(file_href) as sav_file:
            sav_ds = sio.readsav(sav_file.name)

        return sav_ds

    def open_nc_dataset(self, file_href: str) -> Any:
        """Opens NetCDF4 dataset

        Args:
            file_href (str): _description_

        Returns:
            Any: _description_
        """
        nc_dataset = None

        with self.psup_archive.open_resource(file_href) as nc_file:
            nc_dataset = xr.open_dataset(nc_file.name)

        return nc_dataset


class WktIoHandler:
    crs_no_projection_type = ["ocentric", "ographic", "sphere"]

    @staticmethod
    def open_file(wkt_file: Path) -> pd.DataFrame:
        df = pd.read_csv(wkt_file)
        df["created_at"] = pd.to_datetime(df["created_at"])
        return df

    def __init__(self, wkt_file: Path) -> None:
        if not wkt_file.exists():
            raise FileNotFoundError(
                f"Couldn't open {wkt_file} because it does not exist."
            )
        self.wkt_data = self.open_file(wkt_file)
        self.ss_bodies = self.wkt_data["solar_body"].unique()

    def pick_sphere_projection_by_body_and_kind(
        self, ss_body: str, proj_kind: Literal["ocentric", "ographic", "sphere"]
    ) -> WktProjectionItem:
        if ss_body not in self.ss_bodies:
            raise ValueNotAcceptedError(self.ss_bodies.tolist(), ss_body)

        result = self.wkt_data[
            self.wkt_data["solar_body"].str.contains(ss_body.capitalize())
            & self.wkt_data["projection_name"].str.contains("No projection")
            & self.wkt_data["wkt"].str.contains(proj_kind.capitalize())
        ]
        if result.empty:
            raise ValueError("No such result was found with the criteria you passed in")
        return WktProjectionItem.model_validate(result.to_dict(orient="records")[0])

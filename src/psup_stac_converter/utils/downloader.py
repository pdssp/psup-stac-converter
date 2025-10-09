import re
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Iterable, Literal
from urllib.parse import urlparse

import httpx
import pandas as pd
from tqdm.rich import tqdm

from psup_stac_converter.settings import create_logger

log = create_logger(__name__)


def sizeof_fmt(num: int, suffix: str = "B") -> str:
    for unit in ["", "Ki", "Mi", "Gi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Ei{suffix}"


class Downloader:
    def _analyze_file_path(self):
        parsed_url = urlparse(self.file_name)
        if not parsed_url.netloc:
            self.url_type = "local"
            true_path = Path(self.file_name)
            if not true_path.exists():
                raise FileNotFoundError(f"Couldn't find {true_path}")
        else:
            self.url_type = "url"
            true_path = Path(parsed_url.path)
        self.extension = true_path.suffix

    def __init__(self, file_name: str):
        self.file_name = file_name
        self.url_type: Literal["local", "url", "unknown"] = "unknown"
        self.extension: str = ""
        self._analyze_file_path()
        self.local_path: Path | None = (
            self.file_name if self.url_type == "local" else None
        )

    def _unzip_archive(self, output_folder: Path):
        with zipfile.ZipFile(self.local_path, mode="r") as archive:
            for _file in archive.namelist():
                archive.extract(_file, output_folder)

    def _download_remote_file(self, output_directory: Path, filename: str):
        """Bulk downloads the file if on remote, with progress bar"""
        self.local_path = output_directory / filename
        with httpx.stream("GET", self.file_name) as response:
            response.raise_for_status()
            total = int(response.headers.get("Content-Length", 0))
            with (
                open(self.local_path, "wb") as f,
                tqdm(total=total, unit="B", unit_scale=True, desc=filename) as pbar,
            ):
                for chunk in response.iter_bytes():
                    f.write(chunk)
                    pbar.update(len(chunk))

    def local_download(self, output_folder: Path):
        if self.url_type != "local":
            tmp_dir = tempfile.TemporaryDirectory()
            self._download_remote_file(Path(tmp_dir))

        if self.extension.endswith("zip"):
            self._unzip_archive(output_folder)

        if self.url_type != "local":
            tmp_dir.close()


class PsupArchive:
    @staticmethod
    def open_archive(archive_path: Path) -> pd.DataFrame:
        df = pd.read_csv(archive_path)
        df = df.sort_values(by=["total_size", "rel_path"], ascending=False)
        df["h_total_size"] = df["total_size"].apply(sizeof_fmt)
        df["extension"] = df["rel_path"].apply(lambda p: Path(p).suffix.lstrip("."))
        df["root"] = df["rel_path"].apply(lambda p: p.split("/")[0])
        return df

    def __init__(self, psup_archive_file: Path):
        self.psup_archive = self.open_archive(psup_archive_file)
        self.fields = self.psup_archive.columns

    def __str__(self):
        return f"""Archive of {self.n_elements} elements.
        Total estimated size: {self.htotal_size}.
        """

    def slice_by_one(
        self, by: str, criteria: Any, slice_copy: pd.DataFrame | None = None
    ) -> pd.DataFrame | None:
        """_summary_

        Args:
            by (str): _description_
            criteria (Any): _description_
            slice_copy (pd.DataFrame | None, optional): _description_. Defaults to None.

        Raises:
            ValueError: _description_

        Returns:
            pd.DataFrame | None: _description_
        """
        if slice_copy is None:
            slice_copy = self.psup_archive

        if by not in self.fields:
            raise ValueError(f""""{by}" not found among {self.fields}""")

        if by != "total_size" and type(criteria) is str:
            filtered_df = slice_copy[slice_copy[by].str.contains(criteria)]
        elif by != "total_size" and isinstance(criteria, list):
            filtered_df = slice_copy[slice_copy[by].isin(criteria)]
        elif by == "total_size" and isinstance(criteria, Iterable):
            _min, _max = criteria
            filtered_df = slice_copy[(slice_copy[by] > _min) & (slice_copy[by] < _max)]
        else:
            filtered_df = slice_copy[slice_copy[by] == criteria]
        if filtered_df.empty:
            return None

        return filtered_df

    def slice(self, filters: list[tuple[str, Any]]) -> pd.DataFrame | None:
        """Slices the archive from a list of filters.

        The filters are always interpreted as an END condition. If you want to be
        specific with a single filter, you can always pass a single filter in.

        Args:
            filters (list[tuple[str, Any]]): list of couples composed of a "by"
                and a "criteria". The "by" must be in the column reference, while
                the "criteria" can be any type.

        Returns:
            pd.DataFrame | None: The sliced archive as a dataframe
        """
        filtered_df = self.psup_archive.copy()
        for _by, _criteria in filters:
            filtered_df = self.slice_by_one(filtered_df, _by, _criteria)
        return filtered_df

    @property
    def n_elements(self) -> int:
        return self.psup_archive.shape[0]

    @property
    def total_size(self) -> int:
        return self.psup_archive["total_size"].sum()

    @property
    def htotal_size(self) -> str:
        return sizeof_fmt(self.total_size)

    def save_resource_on_disk(self, file_name: str, dest_folder: Path):
        """Saves a single resource on the disk

        Args:
            file_name (str): _description_
            dest_folder (Path): _description_

        Raises:
            ValueError: _description_
            FileExistsError: _description_
        """
        fn_pattern = r"^" + re.escape(file_name) + r"$"
        row = self.psup_archive[
            self.psup_archive["file_name"].str.contains(fn_pattern, regex=True)
        ]
        if row.empty:
            raise ValueError(f'Couldn\'t find item with the name "{file_name}"')

        # In theory, only one item is left
        row = row.drop_duplicates(subset=["file_name"]).squeeze()
        server_ref = row["href"]

        local_path = dest_folder / Path(row["rel_path"])

        if local_path.exists():
            raise FileExistsError(f"{local_path} already exists!")
        else:
            local_path.parent.mkdir(exist_ok=True, parents=True)
            self._save_on_disk(server_ref, local_path)

    def _save_on_disk(
        self,
        remote_url: str,
        dst: Path,
        dl_desc: str | None = None,
    ):
        with httpx.stream("GET", remote_url) as response:
            response.raise_for_status()
            total = int(response.headers.get("Content-Length", 0))
            with (
                open(dst, "wb") as f,
                tqdm(
                    total=total,
                    unit="B",
                    unit_scale=True,
                    desc=dl_desc if dl_desc is not None else dst.as_posix(),
                ) as pbar,
            ):
                for chunk in response.iter_bytes():
                    f.write(chunk)
                    pbar.update(len(chunk))

    def save_slice_on_disk(
        self,
        dest_folder: Path,
        filters: list[tuple[str, Any]] | None = None,
        auto_valid: bool = False,
        raise_on_exists: bool = False,
    ):
        if filters is None:
            slice = self.psup_archive
        else:
            slice = self.slice(filters=filters)
            if slice is None:
                log.error("There is nothing to download!")
                return

        total_size = slice["total_size"].sum()
        log.warning(f"{total_size} of data will be saved at {dest_folder}")
        if not auto_valid:
            user_yes = input("Do you want to continue? [Y/n]")
            if user_yes.lower() not in ("y", "yes"):
                log.warning("Download cancelled by user.")
                return
        for row in tqdm(
            slice.itertuples(),
            total=slice.shape[0],
            unit="file",
            desc="Downloading archive",
        ):
            server_ref = row["href"]
            local_path = dest_folder / Path(row.rel_path)
            if local_path.exists():
                if raise_on_exists:
                    raise FileExistsError(f"{local_path} already exists!")
                else:
                    log.warning(f"{local_path} already exists. Skipping.")
            else:
                local_path.parent.mkdir(exist_ok=True, parents=True)
                self.save_on_disk(server_ref, local_path)

    def save_all_on_disk(
        self, dest_folder: Path, auto_valid: bool = False, raise_on_exists: bool = False
    ):
        self.save_slice_on_disk(
            dest_folder=dest_folder,
            filters=None,
            auto_valid=auto_valid,
            raise_on_exists=raise_on_exists,
        )

import re
from pathlib import Path
from typing import Literal

import pandas as pd
import pyproj
from rich.console import Console
from rich.panel import Panel

from psup_stac_converter.processing import CatalogCreator, RawDataAnalysis
from psup_stac_converter.utils.downloader import WktDownloader
from psup_stac_converter.utils.io import IoHandler

console = Console()


def describe_target_folders():
    io_handler = IoHandler()

    console.print("Input folder:")
    io_handler.show_input_folder()

    console.print("Output folder:")
    io_handler.show_output_folder()


def download_wkt_files(output_file: Path):
    wkt_dl = WktDownloader()
    wkt_dl.local_download(output_file)


def show_wkt_projections(
    summary_file: Path,
    solar_body: str | None = None,
    proj_keywords: list[str] | None = None,
):
    df = pd.read_csv(summary_file)

    if solar_body:
        df = df[df["solar_body"].str.contains(solar_body, flags=re.IGNORECASE)]

    if proj_keywords:
        df = df[
            df["projection_name"].str.contains(
                "".join([f"(?=.*{kw})" for kw in proj_keywords]),
                regex=True,
                flags=re.IGNORECASE,
            )
        ]

    console = Console()
    for row in df.itertuples():
        crs = pyproj.CRS(row.wkt)

        panel = Panel(
            crs.to_wkt(pretty=True),
            title=f"""[bold]{row.id}""",
            subtitle=f"[bold]{row.solar_body} - {row.projection_name}",
        )
        console.print(panel)


def format_data_for_analysis(
    file_name: Path,
    fmt: Literal["shp", "geosjon", "gpkg", "other"],
    metadata_file: Path,
    catalog_folder: Path,
    output_folder: Path,
):
    """
    ie. "lno_10_days.shp", "shp"
    """
    rda = RawDataAnalysis(metadata_file, catalog_folder, output_folder)
    rda.save_to_format(file_name, fmt)


def preview_data(
    metadata_file: Path,
    catalog_folder: Path,
):
    """
    ie. "lno_10_days.shp", "shp"
    """
    rda = RawDataAnalysis(metadata_file, catalog_folder)
    rda.preview_geodf()


def show_possible_formats():
    RawDataAnalysis.show_writable_formats()


def create_catalog(
    name: str,
    metadata_file: Path,
    catalog_folder: Path,
    output_folder: Path,
    clean_prev_output: bool = False,
):
    catalog_creator = CatalogCreator(
        metadata_file=metadata_file,
        catalog_folder=catalog_folder,
        output_folder=output_folder,
    )
    return catalog_creator.create_catalog(
        name=name, clean_previous_output=clean_prev_output
    )

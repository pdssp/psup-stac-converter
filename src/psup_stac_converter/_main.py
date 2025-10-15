import re
from pathlib import Path
from typing import Literal

import pandas as pd
import pyproj
from rich.console import Console
from rich.panel import Panel

from psup_stac_converter.processing import CatalogCreator, RawDataAnalysis
from psup_stac_converter.utils.io import IoHandler

console = Console()


def describe_target_folders():
    io_handler = IoHandler()

    console.print("Input folder:")
    io_handler.show_input_folder()

    console.print("Output folder:")
    io_handler.show_output_folder()


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
    catalog_folder: Path,
    output_folder: Path,
):
    """
    ie. "lno_10_days.shp", "shp"
    """
    rda = RawDataAnalysis(catalog_folder, output_folder)
    rda.save_to_format(file_name, fmt)


def preview_data(
    catalog_folder: Path,
):
    """
    ie. "lno_10_days.shp", "shp"
    """
    rda = RawDataAnalysis(catalog_folder)
    rda.preview_geodf()


def show_possible_formats():
    RawDataAnalysis.show_writable_formats()


def create_catalog(
    raw_data_folder: Path,
    output_folder: Path,
    psup_data_inventory_file: Path = None,
    clean_prev_output: bool = False,
    **kwargs,
):
    catalog_creator = CatalogCreator(
        raw_data_folder=raw_data_folder,
        output_folder=output_folder,
        psup_data_inventory_file=psup_data_inventory_file,
        log=kwargs.get("logger"),
    )
    return catalog_creator.create_catalog(clean_previous_output=clean_prev_output)

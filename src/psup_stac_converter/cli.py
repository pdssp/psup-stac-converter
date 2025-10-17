from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import typer

from psup_stac_converter import _main as F
from psup_stac_converter.exceptions import FileExtensionError
from psup_stac_converter.settings import (
    create_logger_from_settings,
    init_settings_from_file,
)
from psup_stac_converter.utils.file_utils import infos_from_tif

app = typer.Typer(name="psup-stac")


class FileFormat(str, Enum):
    SHP = "shp"
    GEOJSON = "geosjon"
    GPKG = "gpkg"
    OTHER = "other"


class CatalogName(str, Enum):
    HYD_GLOBAL = ("hyd_global_290615.json",)
    DETECTIONS_CRATERS = ("detections_crateres_benjamin_bultel_icarus.json",)
    LCP_FLAHAUT = ("lcp_flahaut_et_al.json",)
    LCP_VMWALLS = ("lcp_vmwalls.json",)
    CROCUS_LS = ("crocus_ls150-310.json",)
    SCALLOPED_DEPRESSION = ("scalloped_depression.json",)
    COSTARD_CRATERS = ("costard_craters.json",)


@app.callback()
def callback(
    ctx: typer.Context,
    from_config: Annotated[
        Optional[Path],
        typer.Option(
            "--from-config",
            "-c",
            help="Path to a config file (YAML) to load defaults from",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
):
    """Utility package to convert PSUP data to STAC format"""
    ctx.obj = {}
    if from_config is not None:
        typer.echo(f"Using config from {from_config}")
        ctx.obj["settings"] = init_settings_from_file(from_config)
        ctx.obj["logger"] = create_logger_from_settings(ctx.obj["settings"])


@app.command()
def create_stac_catalog(
    ctx: typer.Context,
    raw_data_folder: Annotated[
        Path,
        typer.Option(
            "--input",
            "-I",
            help="Where the raw data lies",
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    output_folder: Annotated[
        Path,
        typer.Option(
            "--output",
            "-O",
            help="Where the processed catalog is",
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    psup_inventory_file: Annotated[
        Path,
        typer.Option(
            "--inventory",
            "-l",
            help="File containing information on the hosted PSUP data",
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    clean_previous_output: Annotated[
        bool,
        typer.Option("--clean/--no-clean", "-c/-nc", help="Cleans the output folder"),
    ] = False,
):
    """Converts raw input into a STAC catalog. The user must have a scraped CSV file as
    a feed to rely on, an input folder to store downloaded raw products, and an output
    folder to put the catalog in."""
    settings = ctx.obj.get("settings")

    F.create_catalog(
        raw_data_folder=raw_data_folder or settings.catalog_folder_path,
        output_folder=output_folder or settings.output_data_path,
        psup_data_inventory_file=psup_inventory_file or settings.psup_inventory_file,
        clean_prev_output=clean_previous_output,
        **{k: v for k, v in ctx.obj.items() if k not in ["settings"]},
    )


@app.command()
def describe_folders():
    """Shows the target folders from config"""
    F.describe_target_folders()


@app.command()
def download_wkt_files(
    ctx: typer.Context,
    file_name: Annotated[
        Path,
        typer.Argument(
            exists=False,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            help="The target file. Must be a CSV.",
        ),
    ] = None,
    output_folder: Annotated[
        Optional[Path],
        typer.Option(
            "--in-folder",
            "-f",
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=False,
            readable=True,
            resolve_path=True,
            help="The folder to put your downloaded data in",
        ),
    ] = None,
):
    """Downloads WKT files from the solar system in FILE_NAME

    You can pass an OUTPUT_FOLDER option for simplicity. Do not use
    OUTPUT_FOLDER if the resolved path is in FILE_NAME.
    """
    settings = ctx.obj.get("settings")
    if file_name is None and settings.wkt_file_name is None:
        raise typer.BadParameter("Must provide a mfile name of CSV type!")

    file_name = file_name or settings.wkt_file_name
    output_folder = output_folder or settings.extra_data_path

    if not file_name.suffix.endswith("csv"):
        raise FileExtensionError(["csv"], file_name.suffix)

    if output_folder is not None:
        file_name = output_folder / file_name

    F.download_wkt_files(
        file_name,
        **{k: v for k, v in ctx.obj.items() if k not in ["settings"]},
    )


@app.command()
def show_wkt_projections(
    ctx: typer.Context,
    file_name: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            help="The target file. Must be a CSV.",
        ),
    ] = None,
    solar_body: Annotated[str, typer.Option("--solar-body", "-sb")] = None,
    proj_keywords: Annotated[list[str], typer.Option("--keywords", "-k")] = None,
):
    settings = ctx.obj.get("settings")
    if file_name is None and settings is None:
        raise typer.BadParameter("Must provide a valid WKT file of CSV type!")

    file_name = file_name or (settings.extra_data_path / settings.wkt_file_name)

    F.show_wkt_projections(
        file_name,
        solar_body=solar_body,
        proj_keywords=proj_keywords,
        **{k: v for k, v in ctx.obj.items() if k not in ["settings"]},
    )


@app.command()
def format_data_for_analysis(
    ctx: typer.Context,
    file_name: Annotated[
        Path,
        typer.Argument(
            help="The name of the intermediate file",
            exists=False,
            file_okay=True,
            dir_okay=False,
            writable=True,
            readable=True,
        ),
    ] = None,
    fmt: Annotated[
        FileFormat,
        typer.Option("--format", "-f", help="The format of the intermediate file"),
    ] = None,
    catalog_folder: Annotated[
        Path,
        typer.Option(
            "--catalog",
            help="The folder in where the catalogs lie",
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=True,
            readable=True,
        ),
    ] = None,
    output_folder: Annotated[
        Path,
        typer.Option(
            "--output-folder",
            "-O",
            help="The intermediate folder to export in",
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=True,
            readable=True,
        ),
    ] = None,
):
    F.format_data_for_analysis(file_name, fmt, catalog_folder, output_folder, **ctx.obj)


@app.command()
def preview_data(
    ctx: typer.Context,
    catalog_folder: Annotated[
        Path,
        typer.Option(
            "--catalog",
            help="The folder in where the catalogs lie",
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=True,
            readable=True,
        ),
    ] = None,
):
    settings = ctx.obj.get("settings")

    F.preview_data(
        catalog_folder or settings.catalog_folder_path,
        **{k: v for k, v in ctx.obj.items() if k not in ["settings"]},
    )


@app.command()
def show_possible_formats():
    """Shows the available formats for saving"""
    F.show_possible_formats()


@app.command()
def describe_tif(
    tif_file: Annotated[
        Path,
        typer.Argument(
            help="""A rasterized image (.ptif, .tif, .geotif)""",
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
        ),
    ],
):
    """Displays the metadata from a rasterized image"""
    infos_from_tif(tif_file)


if __name__ == "__main__":
    app()

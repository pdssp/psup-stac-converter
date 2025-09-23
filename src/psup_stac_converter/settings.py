import ast
import logging
from pathlib import Path

import geopandas as gpd
import yaml
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.logging import RichHandler
from shapely import Polygon

BASE_DIR = Path(__file__).parents[2]


class Settings(BaseSettings):
    """Application settings."""

    log_level: str = "INFO"
    log_format: str = "%(message)s"
    data_path: Path = BASE_DIR / "data"
    raw_data_path: Path = BASE_DIR / "data" / "raw"
    catalog_folder_path: Path = BASE_DIR / "data" / "raw" / "catalogs"
    output_data_path: Path = BASE_DIR / "data" / "processed"
    intermediate_data_path: Path = BASE_DIR / "data" / "intermediate"
    extra_data_path: Path = BASE_DIR / "data" / "extra"
    metadata_file_path: Path = BASE_DIR / "data" / "raw" / "vector.csv"

    wkt_file_name: Path = "wkt_solar_system.csv"

    model_config = SettingsConfigDict()

    @field_validator("metadata_file_path", mode="after")
    @classmethod
    def open_metadata(cls, value: Path) -> Path:
        if not value.suffix.endswith("csv"):
            raise ValueError(f"{value} must end with the .csv extension")

        expected_columns = ["description", "name", "footprint", "keywords"]
        gdf = gpd.read_file(value)
        if not all(
            [
                ex_col == col
                for ex_col, col in zip(sorted(expected_columns), sorted(gdf.columns))
            ]
        ):
            raise ValueError(
                f"""Columns in metadata must only have the following columns: {", ".join(expected_columns)}"""
            )
        # Place transformations here
        gdf["footprint"] = gdf["footprint"].apply(
            lambda x: Polygon(ast.literal_eval(x))
        )
        gdf = gdf.set_geometry("footprint")
        return value


def init_settings_from_file(config_file: Path) -> Settings:
    if not config_file.exists():
        raise ValueError(f"{config_file} not found.")

    if not config_file.suffix.endswith("yml") or config_file.suffix.endswith("yaml"):
        raise ValueError(f"{config_file} must end with .yml or .yaml!")

    cfg = yaml.safe_load(Path("converter-params.yml").read_text())
    return Settings.model_validate(cfg["settings"])


def create_logger(
    logger_name: str, log_level: str | None = None, log_format: str | None = None
) -> logging.Logger:
    if log_level is None:
        log_level = Settings().log_level

    if log_format is None:
        log_format = Settings().log_format

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt="[%X]",
        handlers=[RichHandler()],
    )
    return logging.getLogger(logger_name)

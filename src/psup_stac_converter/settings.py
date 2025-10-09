import logging
from pathlib import Path

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.logging import RichHandler

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
    psup_inventory_file: Path = BASE_DIR / "data" / "raw" / "psup_refs.csv"

    wkt_file_name: Path = "wkt_solar_system.csv"

    model_config = SettingsConfigDict()


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

import inspect
import logging
from pathlib import Path

import yaml
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.logging import RichHandler

from psup_stac_converter.exceptions import FileExtensionError

BASE_DIR = Path(__file__).parents[2]


class Settings(BaseSettings):
    """Application settings."""

    log_level: str = "DEBUG"
    log_format: str = "%(asctime)s [%(levelname)s] %(message)s"
    data_path: Path = BASE_DIR / "data"
    raw_data_path: Path = BASE_DIR / "data" / "raw"
    output_data_path: Path = BASE_DIR / "data" / "processed"
    # This folder holds complementary information for the output
    extra_data_path: Path = BASE_DIR / "data" / "extra"
    psup_inventory_file: Path = BASE_DIR / "data" / "raw" / "psup_refs.csv"

    wkt_file_name: Path = "wkt_solar_system.csv"

    model_config = SettingsConfigDict()

    @field_validator(
        "data_path",
        "raw_data_path",
        "output_data_path",
        "extra_data_path",
        "psup_inventory_file",
        mode="after",
    )
    @classmethod
    def resolve_path(cls, value: Path) -> Path:
        value = value.expanduser()
        return value


def init_settings_from_file(config_file: Path) -> Settings:
    if not config_file.exists():
        raise FileNotFoundError(f"{config_file} not found.")

    if not config_file.suffix.endswith("yml") or config_file.suffix.endswith("yaml"):
        raise FileExtensionError(["yml", "yaml"], config_file.suffix)

    cfg = yaml.safe_load(Path(config_file).read_text())
    return Settings.model_validate(cfg["settings"])


def create_logger(
    logger_name: str, log_level: str | None = None, log_format: str | None = None
) -> logging.Logger:
    """Instanciates the logger based on options

    Args:
        logger_name (str): _description_
        log_level (str | None, optional): _description_. Defaults to None.
        log_format (str | None, optional): _description_. Defaults to None.

    Returns:
        logging.Logger: _description_
    """
    if log_level is None:
        log_level = "DEBUG"

    if log_format is None:
        log_format = "%(asctime)s [%(levelname)s] %(message)s"

    log = logging.getLogger(logger_name)
    log.setLevel(log_level)

    rich_handler = RichHandler()
    file_log_path = BASE_DIR / "logs" / "psup-stac-generator.log"
    file_log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(file_log_path)

    rich_formatter = logging.Formatter("%(message)s", datefmt="[%X]")
    file_formatter = logging.Formatter(log_format, datefmt="[%X]")

    rich_handler.setFormatter(rich_formatter)
    file_handler.setFormatter(file_formatter)

    log.addHandler(rich_handler)
    log.addHandler(file_handler)

    return log


def create_logger_from_settings(
    settings: Settings, logger_name: str | None = None
) -> logging.Logger:
    if logger_name is None:
        callers_stack = inspect.stack()[1]
        module_name = inspect.getmodule(callers_stack[0])
        logger_name = module_name.__name__
    return create_logger(
        logger_name=logger_name,
        log_level=settings.log_level,
        log_format=settings.log_format,
    )

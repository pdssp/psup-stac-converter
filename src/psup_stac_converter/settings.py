import logging
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.logging import RichHandler

BASE_DIR = Path(__file__).parents[2]


class Settings(BaseSettings):
    """Application settings."""

    log_level: str = "INFO"
    log_format: str = "%(message)s"
    data_path: Path = BASE_DIR / "data"
    raw_data_path: Path = BASE_DIR / "data" / "raw"
    output_data_path: Path = BASE_DIR / "data" / "processed"
    intermediate_data_path: Path = BASE_DIR / "data" / "intermediate"
    extra_data_path: Path = BASE_DIR / "data" / "extra"

    model_config = SettingsConfigDict()


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

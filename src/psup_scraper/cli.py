import logging
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import pandas as pd
import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from psup_scraper.items import WktLineItem
from psup_scraper.spiders.psup_files import PsupFilesSpider
from psup_scraper.spiders.wkt_spider import WktSpiderSpider
from psup_stac_converter.utils.downloader import sizeof_fmt

app = typer.Typer(name="psup-scraper")
scrapy_settings = get_project_settings()
console = Console()

logging.basicConfig(
    level=scrapy_settings.get("LOG_LEVEL", "INFO"),
    format=scrapy_settings.get("LOG_FORMAT"),
    datefmt=scrapy_settings.get("LOG_DATEFORMAT"),
    handlers=[RichHandler()],
)
log = logging.getLogger(__name__)


class FeedFormatEnum(StrEnum):
    JSON = "json"
    JSONLINES = "jsonlines"
    CSV = "csv"
    XML = "xml"


@app.callback()
def callback():
    """Retrieves metadata available on PSUP (psup.ias.u-psud.fr/sitools/datastorage/user/storage)"""
    pass


@app.command()
def scraper_settings():
    """Show the current scrapy settings (editable in ./src/psup_scraper/settings.py)"""
    console.print(scrapy_settings.copy_to_dict())


@app.command()
def get_data_ref(
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-O",
            help="Where the download feed should be saved",
            exists=False,
            file_okay=True,
            dir_okay=False,
            writable=True,
            readable=True,
            resolve_path=True,
        ),
    ],
    fmt: Annotated[
        FeedFormatEnum,
        typer.Option("--format", "-f", help="The format of the downloaded result"),
    ],
    clean_feed: Annotated[
        bool,
        typer.Option(
            "--clean/--no-clean", help="Overwrites the feed file passed as an argument"
        ),
    ] = False,
):
    """Crawls the data tree to obtain the references, from files, to links, to their actual size in B"""
    # Get initial parameters
    process = CrawlerProcess(scrapy_settings)
    # Change settings based on CLI options
    process.settings.set(
        "FEEDS",
        {
            output_path.as_posix(): {
                "format": fmt,
                "encoding": "utf8",
                "store_empty": False,
                "overwrite": clean_feed,
            }
        },
    )
    process.settings.set(
        "LOG_FILE",
        (Path(__file__).parent.parent.parent / "logs" / "psup_info.log").as_posix(),
    )
    process.crawl(PsupFilesSpider)
    log.info("Starting the scraper")
    process.start()
    log.info("Process finished!")


@app.command()
def check_data(
    feed_csv: Annotated[
        Path,
        typer.Argument(
            help="The field previously acquired with the scraper. Must be a CSV.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=True,
            readable=True,
            resolve_path=True,
        ),
    ],
    n_lines: Annotated[
        int, typer.Option("--lines", "-n", help="Number of lines to show")
    ] = 10,
):
    """Shows a representation of the scraped result in the std console."""
    psup_refs = pd.read_csv(feed_csv)
    psup_refs = psup_refs.sort_values(by=["total_size", "rel_path"], ascending=False)
    psup_refs["h_total_size"] = psup_refs["total_size"].apply(sizeof_fmt)
    psup_refs["extension"] = psup_refs["rel_path"].apply(
        lambda p: Path(p).suffix.lstrip(".")
    )
    psup_refs["category"] = psup_refs["rel_path"].apply(lambda p: p.split("/")[0])
    psup_refs["root"] = psup_refs["rel_path"].apply(lambda p: p.split("/")[1])

    table = Table("PSUP data feed")

    for column in psup_refs.columns:
        table.add_column(column)

    for row in psup_refs.head(n_lines).itertuples():
        table.add_row(*[str(el) for el in row])

    console.print(table)


@app.command()
def get_wkt_proj(
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-O",
            help="Where the download feed should be saved",
            exists=False,
            file_okay=True,
            dir_okay=False,
            writable=True,
            readable=True,
            resolve_path=True,
        ),
    ],
    fmt: Annotated[
        FeedFormatEnum,
        typer.Option("--format", "-f", help="The format of the downloaded result"),
    ],
    clean_feed: Annotated[
        bool,
        typer.Option(
            "--clean/--no-clean", help="Overwrites the feed file passed as an argument"
        ),
    ] = False,
):
    """Retrieves VESPA's projections under a CSV file"""
    process = CrawlerProcess(scrapy_settings)
    process.settings.set(
        "FEEDS",
        {
            output_path.as_posix(): {
                "format": fmt,
                "item_classes": [WktLineItem],
                "overwrite": clean_feed,
            }
        },
    )
    process.crawl(WktSpiderSpider)
    log.info("Starting the scraper")
    process.start()
    log.info("Process finished!")


if __name__ == "__main__":
    app()

from pathlib import Path
from urllib.parse import urlparse

import scrapy
import scrapy.http

from psup_scraper.items import PsupScraperItem


class PsupFilesSpider(scrapy.Spider):
    name = "psup_files"
    allowed_domains = ["psup.ias.u-psud.fr"]
    base_url = "http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/"
    start_urls = [
        "http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/",
        "http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/omegacubes/",
    ]

    def _find_href(self, url: str) -> str:
        return (
            Path(urlparse(url).path)
            .relative_to(urlparse(self.base_url).path)
            .as_posix()
        )

    def parse(self, response: scrapy.http.Response):
        links = response.css("a")
        for link in links:
            href = link.css("::attr(href)").get()
            txt = link.css("::text").get()

            if txt == "..":
                # Do not come back a level earlier
                continue

            abs_url = response.urljoin(href)

            if href.endswith("/"):
                # In the case where the link is a directory
                # go to next page
                self.logger.info(f"Continuing to {link}")
                yield scrapy.Request(abs_url, callback=self.parse)
                continue

            item = PsupScraperItem()
            item["file_name"] = txt
            item["rel_path"] = self._find_href(href)
            item["href"] = abs_url
            # Request HEAD to get Content-Length without downloading the whole file
            yield scrapy.Request(
                abs_url,
                callback=self._get_size_head,
                meta={"item": item},
                method="HEAD",
                dont_filter=True,
            )

    def _get_size_head(self, response: scrapy.http.Response):
        item = response.meta["item"]
        cl = response.headers.get(b"Content-Length")
        if cl:
            try:
                item["total_size"] = int(cl)
            except Exception as e:
                self.logger.warning("Couldn't obtain the size from the header")
                self.logger.warning(f"Reason: [{e.__class__.__name__}] {e}")
                item["total_size"] = None
            yield item
            return

        # If Content-Length missing, request a single byte to get Content-Range
        headers = {"Range": "bytes=0-0"}
        yield scrapy.Request(
            response.url,
            callback=self._get_size_range,
            headers=headers,
            meta={"item": item},
            method="GET",
            dont_filter=True,
        )

    def _get_size_range(self, response: scrapy.http.Response):
        item = response.meta["item"]
        cr = response.headers.get(b"Content-Range")
        if cr:
            try:
                # Content-Range: bytes 0-0/12345
                total = int(cr.decode().split("/")[-1])
                item["total_size"] = total
            except Exception as e:
                self.logger.warning("Couldn't obtain the size from size_range")
                self.logger.warning(f"Reason: [{e.__class__.__name__}] {e}")
                item["total_size"] = None
            yield item
            return

        # Last resort: fall back to the body length (may have downloaded the whole file)
        item["total_size"] = len(response.body)
        yield item

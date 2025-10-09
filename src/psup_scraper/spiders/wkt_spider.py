import scrapy

from psup_scraper.items import WktLineItem

PLANETS = [
    "mercury",
    "venus",
    "earth",
    "mars",
    "jupiter",
    "saturn",
    "uranus",
    "neptune",
]


class WktSpiderSpider(scrapy.Spider):
    name = "wkt_spider"
    allowed_domains = ["voparis-vespa-crs.obspm.fr"]
    start_urls = ["https://voparis-vespa-crs.obspm.fr/web/"]
    # custom_settings = {
    #     "FEEDS": {
    #         "./downloads/wkt_data.csv": {"format": "csv", "item_classes": [WktLineItem]}
    #     }
    # }
    start_urls = [
        f"https://voparis-vespa-crs.obspm.fr/web/{planet}.html" for planet in PLANETS
    ]

    def parse(self, response):
        table_caption = response.css("table").css("caption::text").get().strip()
        self.logger.info(table_caption)

        columns = tuple(
            element.strip()
            for element in response.css("table").css("thead tr th::text").getall()
        )
        for line in response.css("table").css("tbody tr"):
            wkt_line_item = WktLineItem()
            for col_name, col_value in zip(columns, line.css("td")):
                if col_name == "wkt":
                    extracted_value = col_value.css("pre::text").get()
                else:
                    extracted_value = col_value.css("::text").get().strip()

                wkt_line_item[col_name] = extracted_value

            yield wkt_line_item

import scrapy


class WktSpiderSpider(scrapy.Spider):
    name = "wkt_spider"
    allowed_domains = ["voparis-vespa-crs.obspm.fr"]
    start_urls = ["https://voparis-vespa-crs.obspm.fr/web/"]

    def parse(self, response):
        pass

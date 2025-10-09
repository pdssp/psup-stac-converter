# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PsupScraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    file_name = scrapy.Field()
    rel_path = scrapy.Field()
    href = scrapy.Field()
    total_size = scrapy.Field()


class WktLineItem(scrapy.Item):
    id = scrapy.Field()
    created_at = scrapy.Field()
    solar_body = scrapy.Field()
    datum_name = scrapy.Field()
    ellipsoid_name = scrapy.Field()
    projection_name = scrapy.Field()
    wkt = scrapy.Field()

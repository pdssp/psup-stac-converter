import datetime as dt
import json
from typing import NamedTuple

import geopandas as gpd
import pystac
from shapely import bounds, to_geojson

from psup_stac_converter.processors.base import BaseProcessorModule


class HydratedMineralProcessor(BaseProcessorModule):
    COLUMN_NAMES = [
        "OBJECTID",
        "Id",
        "grid_code",
        "Shape_Leng",
        "Shape_Area",
        "geometry",
    ]

    def __init__(self, name, data: gpd.GeoDataFrame, footprint, description):
        super().__init__(name, data, footprint, description)

    @staticmethod
    def gpd_line_to_item(df_line: NamedTuple) -> pystac.Item:
        item_id = str(df_line.OBJECTID)
        footprint = json.loads(to_geojson(df_line.geometry))
        bbox = bounds(df_line.geometry).tolist()

        properties = {}
        properties["grid_code"] = df_line.grid_code
        properties["Shape_Leng"] = df_line.Shape_Leng
        properties["Shape_Area"] = df_line.Shape_Area

        item = pystac.Item(
            id=item_id,
            geometry=footprint,
            bbox=bbox,
            datetime=dt.datetime(2013, 4, 24, 0, 0),
            properties=properties,
        )

        return item

    def create_catalog(self) -> pystac.Catalog:
        catalog = super().create_catalog()

        for row in self.data.itertuples():
            item = self.gpd_line_to_item(row)
            catalog.add_item(item)

        return catalog

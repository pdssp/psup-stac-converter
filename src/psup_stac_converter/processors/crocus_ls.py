import datetime as dt
import json
from typing import NamedTuple

import geopandas as gpd
import pystac
from altair import Geometry
from shapely import bounds, to_geojson

from psup_stac_converter.processors.base import BaseProcessorModule


class CrocusLs(BaseProcessorModule):
    """
    Important note: this file can't be open with GeoPandas

    Reason: [GEOSException] IllegalArgumentException: Points of LinearRing do not form a closed linestring
    """

    COLUMN_NAMES = ["Crocus typ", "LS", "title"]

    def __init__(
        self, name: str, data: gpd.GeoDataFrame, footprint: Geometry, description: str
    ):
        super().__init__(name, data, footprint, description)

    def transform_data(self):
        transform_data = super().transform_data()
        transform_data.columns = ["crocus_type", "ls", "title", "geometry"]

        return transform_data

    def create_catalog(self) -> pystac.Catalog:
        catalog = super().create_catalog()

        transformed_data = self.transform_data()

        for row in transformed_data.itertuples():
            item = self.gpd_line_to_item(row)
            catalog.add_item(item)

        return catalog

    def create_collection(self) -> pystac.Collection:
        collection = super().create_collection()

        transformed_data = self.transform_data()

        for row in transformed_data.itertuples():
            item = self.gpd_line_to_item(row)
            collection.add_item(item)

        return collection

    @staticmethod
    def gpd_line_to_item(row: NamedTuple) -> pystac.Item:
        id_col = "Index"

        item_id = str(getattr(row, id_col))
        footprint = json.loads(to_geojson(row.geometry))
        bbox = bounds(row.geometry).tolist()
        timestamp = dt.datetime(2009, 7, 10, 0, 0)

        properties = {
            k: v
            for k, v in row._asdict().items()
            if k
            not in [
                id_col,
                "geometry",
            ]
        }

        item = pystac.Item(
            id=item_id,
            geometry=footprint,
            bbox=bbox,
            datetime=timestamp,
            properties=properties,
        )
        return item

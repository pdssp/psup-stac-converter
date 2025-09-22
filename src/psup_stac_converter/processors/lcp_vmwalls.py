import datetime as dt
import json
from typing import NamedTuple

import pystac
from shapely import bounds, to_geojson

from psup_stac_converter.processors.base import BaseProcessorModule


class LcpVmwalls(BaseProcessorModule):
    COLUMN_NAMES = ["N1", "N2", "N3", "type", "geometry"]

    def __init__(self, name, data, footprint, description):
        super().__init__(name, data, footprint, description)

    def create_catalog(self) -> pystac.Catalog:
        catalog = super().create_catalog()

        for row in self.data.itertuples():
            item = self.gpd_line_to_item(row)
            catalog.add_item(item)

        return catalog

    def create_collection(self) -> pystac.Collection:
        collection = super().create_collection()

        for row in self.data.itertuples():
            item = self.gpd_line_to_item(row)
            collection.add_item(item)

        return collection

    @staticmethod
    def gpd_line_to_item(row: NamedTuple) -> pystac.Item:
        id_col = "Index"

        item_id = str(getattr(row, id_col))
        footprint = json.loads(to_geojson(row.geometry))
        bbox = bounds(row.geometry).tolist()
        timestamp = dt.datetime(2012, 1, 11, 0, 0)

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

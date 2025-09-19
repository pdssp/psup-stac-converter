import datetime as dt
import json
from typing import NamedTuple

import pystac
from shapely import bounds, to_geojson

from psup_stac_converter.processors.base import BaseProcessorModule


class ScallopedDepression(BaseProcessorModule):
    COLUMN_NAMES = [
        "Name",
        "description",
        "timestamp",
        "begin",
        "end",
        "altitudeMode",
        "tessellate",
        "extrude",
        "visibility",
        "geometry",
    ]

    def __init__(self, name, data, footprint, description):
        super().__init__(name, data, footprint, description)

    @staticmethod
    def gpd_line_to_item(row: NamedTuple) -> pystac.Item:
        id_col = "Index"

        item_id = str(getattr(row, id_col))
        footprint = json.loads(to_geojson(row.geometry))
        bbox = bounds(row.geometry).tolist()
        timestamp = row.timestamp or dt.datetime(2011, 5, 11, 0, 0)

        properties = {
            k: v
            for k, v in row._asdict().items()
            if k not in [id_col, "geometry", "timestamp"]
        }

        item = pystac.Item(
            id=item_id,
            geometry=footprint,
            bbox=bbox,
            datetime=timestamp,
            properties=properties,
        )
        return item

    def create_catalog(self):
        catalog = super().create_catalog()

        transformed_data = self.transform_data()

        for row in transformed_data.itertuples():
            item = self.gpd_line_to_item(row)
            catalog.add_item(item)

        return catalog

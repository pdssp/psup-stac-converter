import datetime as dt
import json
from typing import NamedTuple

import pystac
from shapely import Point, bounds, to_geojson

from psup_stac_converter.extensions import apply_ssys
from psup_stac_converter.processors.base import BaseProcessorModule


class LcpVmwalls(BaseProcessorModule):
    """For Valles Marineris low Calcium-Pyroxene

    N represents the space in which the point is located:

    * N1 is the latitude
    * N2 is the longitude
    * N3 is the elevation

    type is unique = 1



    """

    COLUMN_NAMES = ["N1", "N2", "N3", "type", "geometry"]

    def __init__(self, name, data, footprint, description, keywords: list[str]):
        super().__init__(name, data, footprint, description, keywords)

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

    def transform_data(self):
        transform_data = super().transform_data()

        transform_data["geometry"] = transform_data.apply(
            lambda row: Point(row["N2"], row["N1"], row["N3"]), axis=1
        )
        transform_data = transform_data.drop(["N1", "N2", "N3", "type"], axis=1)

        return transform_data

    @staticmethod
    def gpd_line_to_item(row: NamedTuple) -> pystac.Item:
        id_col = "Index"

        item_id = str(getattr(row, id_col))
        footprint = json.loads(to_geojson(row.geometry))
        bbox = bounds(row.geometry).tolist()
        timestamp = dt.datetime(2012, 1, 11, 0, 0)

        properties = {}

        item = pystac.Item(
            id=item_id,
            geometry=footprint,
            bbox=bbox,
            datetime=timestamp,
            properties=properties,
        )
        item = apply_ssys(item)
        return item

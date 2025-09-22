import datetime as dt
import json
from io import StringIO
from typing import NamedTuple

import geopandas as gpd
import pandas as pd
import pystac
from bs4 import BeautifulSoup
from shapely import Geometry, bounds, to_geojson

from psup_stac_converter.processors.base import BaseProcessorModule


class CostardCraters(BaseProcessorModule):
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

    EXTRA_FIELDS = ["fid", "lat", "lon", "diam", "type", "lon_earth"]

    def __init__(
        self, name: str, data: gpd.GeoDataFrame, footprint: Geometry, description: str
    ):
        super().__init__(name, data, footprint, description)

    @staticmethod
    def gpd_line_to_item(row: NamedTuple) -> pystac.Item:
        id_col = "fid"

        item_id = str(getattr(row, id_col))
        footprint = json.loads(to_geojson(row.geometry))
        bbox = bounds(row.geometry).tolist()
        timestamp = row.timestamp or dt.datetime(1989, 6, 1, 0, 0)

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
    def extract_infos_from_description(description: str):
        """
        extracts information in the following order:
        fid, lat, lon, diam, type, lon_earth
        """
        soup = BeautifulSoup(description, "html.parser")
        buffer = StringIO(str(soup.find_all("table")[-1]))
        desc_df = pd.read_html(buffer)[0]
        desc_df.columns = ["name", "value"]
        return tuple(desc_df["value"].tolist())

    def transform_data(self) -> gpd.GeoDataFrame:
        transformed_df = super().transform_data()
        (
            transformed_df["fid"],
            transformed_df["lat"],
            transformed_df["lon"],
            transformed_df["diam"],
            transformed_df["type"],
            transformed_df["lon_earth"],
        ) = zip(*transformed_df["description"].map(self.extract_infos_from_description))
        transformed_df = transformed_df.drop("description", axis=1)
        return transformed_df

import datetime as dt
import json
from typing import NamedTuple

import geopandas as gpd
import pystac
from bs4 import BeautifulSoup
from shapely import Geometry, bounds, to_geojson

from psup_stac_converter.extensions import apply_ssys
from psup_stac_converter.processors.base import BaseProcessorModule

# Type 1, referred to as flower type, revealed a single continuous and multilobate ejecta deposit with peripheral ridges close to the margin (Figure 3).
# Type 2, classified as a rampart crater, includes a double continuous ejecta deposit with a more circular perimeter. The first inner annulus, has a convex distal edge. Outside this annulus a thin lobate flow sheet describes a more or less sinuous perimeter (Figure 4).
# Type 3, called pedestal crater or ‘pancake’ crater (Mouginis-Mark, 1979), is defined as morphologically similar to type 2, with an inner annulus but the outer ejecta missing.
crater_type = {1: "flower type", 2: "rampart crater", 3: "pedestal crater"}


class CostardCraters(BaseProcessorModule):
    """
    Based on Lobate impact craters, from François Costard's study.

    * type: flower type, rampart crater, pedestal crater
    * altitudeMode: always `clampToGround`
    * timestmap, being and end are always empty
    * tesseltate: is always -1
    * extrude: is always -1
    * visibility: is always -1

    """

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

    # Empty fields, or fields with a single value
    # Need to be put to the collection
    FIELDS_TO_EXCLUDE = [
        "timestamp",
        "begin",
        "end",
        "altitudeMode",
        "tesselate",
        "extrude",
        "visibility",
    ]

    EXTRA_FIELDS = ["fid", "lat", "lon", "diam", "type", "lon_earth"]

    def __init__(
        self,
        name: str,
        data: gpd.GeoDataFrame,
        footprint: Geometry,
        description: str,
        keywords: list[str],
    ):
        super().__init__(name, data, footprint, description, keywords)

    def gpd_line_to_item(self, row: NamedTuple) -> pystac.Item:
        id_col = "fid"

        item_id = str(getattr(row, id_col))
        footprint = json.loads(to_geojson(row.geometry))
        bbox = bounds(row.geometry).tolist()
        timestamp = row.timestamp or dt.datetime(1989, 6, 1, 0, 0)

        properties = {
            k: v
            for k, v in row._asdict().items()
            if k not in [id_col, "geometry", "timestamp"] + self.FIELDS_TO_EXCLUDE
        }

        item = pystac.Item(
            id=item_id,
            geometry=footprint,
            bbox=bbox,
            datetime=timestamp,
            properties=properties,
        )
        item = apply_ssys(item)

        # Insert common metadata here
        item.common_metadata.instruments = ["viking1", "viking2"]
        item.common_metadata.platform = "viking"

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
        nested_table = soup.find_all("table")[-1]
        attributes = []

        for tr in nested_table.find_all("tr"):
            td_name, td_value = tr.find_all("td")
            name = td_name.get_text().lower()
            value = td_value.get_text()
            if name in ["lat", "lon", "diam", "lon_earth"]:
                value = float(value.replace(",", "."))
            else:
                value = int(value)
            attributes.append(value)
        return tuple(attributes)

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

        transformed_df["type"] = transformed_df["type"].apply(
            lambda t: crater_type.get(t, "unknown")
        )

        return transformed_df

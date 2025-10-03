import datetime as dt
import json
from typing import NamedTuple

import pystac
from pydantic.alias_generators import to_snake
from shapely import bounds, to_geojson

from psup_stac_converter.extensions import apply_ssys
from psup_stac_converter.processors.base import BaseProcessorModule


class LcpFlahaut(BaseProcessorModule):
    """Based on "Central peaks mineralogy south Valles Marineris" """

    COLUMN_NAMES = [
        "CRISM_ID",
        "latitude",
        "longitude",
        "canyon",
        "location_w",
        "associated",
        "LCP_rich_b",
        "other_dete",
        "geometry",
    ]

    def __init__(self, name, data, footprint, description, keywords: list[str]):
        super().__init__(name, data, footprint, description, keywords)

    @staticmethod
    def gpd_line_to_item(row: NamedTuple) -> pystac.Item:
        id_col = "Index"

        item_id = str(getattr(row, id_col))
        footprint = json.loads(to_geojson(row.geometry))
        bbox = bounds(row.geometry).tolist()
        timestamp = dt.datetime(2012, 8, 6)

        chemical_details = (
            row.other_dete.split(",") if row.other_dete is not None else []
        )

        properties = {
            k: v
            for k, v in row._asdict().items()
            if k not in [id_col, "geometry", "other_dete", "crism_id", "associated"]
        }
        properties["chemical_composition"] = chemical_details

        item = pystac.Item(
            id=item_id,
            geometry=footprint,
            bbox=bbox,
            datetime=timestamp,
            properties=properties,
        )
        item = apply_ssys(item)

        crism_asset = pystac.Asset(
            href=f"https://viewer.mars.asu.edu/viewer/crism/{row.crism_id}",
            media_type=pystac.MediaType.HTML,
        )
        item.add_asset("crism_url", crism_asset)

        if row.associated is not None:
            hirise_asset = pystac.Asset(
                href=f"https://www.uahirise.org/{row.associated}",
                media_type=pystac.MediaType.HTML,
            )
            item.add_asset("hirise_url", hirise_asset)

        item.common_metadata.instruments = ["crism", "hirise"]
        item.common_metadata.mission = "mro"

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

    def transform_data(self):
        transformed_data = super().transform_data()
        transformed_data.columns = transformed_data.columns.map(to_snake)

        return transformed_data

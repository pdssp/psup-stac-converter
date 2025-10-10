import datetime as dt
import json
from typing import NamedTuple

import pystac
from shapely import bounds, to_geojson

from psup_stac_converter.extensions import apply_ssys
from psup_stac_converter.processors.base import BaseProcessorModule

crater_type = {"Non visible": "non-visible", "1": "visible", "0": "unknown"}


class CraterDetection(BaseProcessorModule):
    """For "Central peaks hydrated phases between Isidis and Hellas" study"""

    COLUMN_NAMES = [
        "Longitude",
        "Latitude",
        "Name",
        "Diameter__",
        "Name_CRISM",
        "F6",
        "Ejecta",
        "Wall",
        "Floor",
        "Central_Pe",
        "geometry",
    ]

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

    @staticmethod
    def gpd_line_to_item(row: NamedTuple) -> pystac.Item:
        item_id = str(row.name + "_" + row.name_crism)
        footprint = json.loads(to_geojson(row.geometry))
        bbox = bounds(row.geometry).tolist()
        timestamp = dt.datetime(2014, 7, 31, 0, 0)

        properties = {
            k: v
            for k, v in row._asdict().items()
            if k not in ["name_crism", "geometry", "f6"]
        }
        properties["f6"] = sorted([chemical.strip() for chemical in row.f6.split(",")])

        item = pystac.Item(
            id=item_id,
            geometry=footprint,
            bbox=bbox,
            datetime=timestamp,
            properties=properties,
        )
        item = apply_ssys(item)

        # add an asset
        asset = pystac.Asset(
            href=f"https://viewer.mars.asu.edu/viewer/crism/{row.name_crism}",
            media_type=pystac.MediaType.HTML,
            roles=["visual", "data"],
            description="The CRISM image used for observations",
        )
        item.add_asset("crism_url", asset)

        # Item metadata
        item.common_metadata.instruments = ["crism"]
        item.common_metadata.mission = "mro"

        return item

    @staticmethod
    def clean_crater_qual(crater_qual_name: str | None):
        if crater_qual_name is None:
            return "unknown"

        return crater_type[crater_qual_name]

    def transform_data(self):
        transformed_data = super().transform_data()
        transformed_data.columns = [col.lower() for col in transformed_data.columns]
        transformed_data = transformed_data.rename(columns={"diameter__": "diameter"})

        transformed_data["ejecta"] = transformed_data["ejecta"].apply(
            self.clean_crater_qual
        )
        transformed_data["wall"] = transformed_data["wall"].apply(
            self.clean_crater_qual
        )
        transformed_data["floor"] = (
            transformed_data["floor"]
            .astype(int)
            .astype(str)
            .apply(self.clean_crater_qual)
        )
        transformed_data["central_pe"] = transformed_data["central_pe"].apply(
            self.clean_crater_qual
        )

        return transformed_data

import datetime as dt
import json
from typing import NamedTuple

import pystac
from shapely import bounds, to_geojson

from psup_stac_converter.processors.base import BaseProcessorModule

crater_type = {"Non visible": "non-visible", "1": "visible", "0": "unknown"}


class CraterDetection(BaseProcessorModule):
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

    def __init__(self, name, data, footprint, description):
        super().__init__(name, data, footprint, description)

    def create_catalog(self) -> pystac.Catalog:
        catalog = super().create_catalog()

        transformed_data = self.transform_data()

        for row in transformed_data.itertuples():
            item = self.gpd_line_to_item(row)
            catalog.add_item(item)

        return catalog

    @staticmethod
    def gpd_line_to_item(row: NamedTuple) -> pystac.Item:
        id_col = "name_crism"

        item_id = str(getattr(row, id_col))
        footprint = json.loads(to_geojson(row.geometry))
        bbox = bounds(row.geometry).tolist()
        timestamp = dt.datetime(2014, 7, 31, 0, 0)

        properties = {
            k: v
            for k, v in row._asdict().items()
            if k not in [id_col, "geometry", "f6"]
        }
        properties["f6"] = sorted([chemical.strip() for chemical in row.f6.split(",")])

        item = pystac.Item(
            id=item_id,
            geometry=footprint,
            bbox=bbox,
            datetime=timestamp,
            properties=properties,
        )
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

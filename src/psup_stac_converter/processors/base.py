import geopandas as gpd
import pystac
from shapely import Geometry


class BaseProcessorModule:
    COLUMN_NAMES = []

    def __init__(
        self,
        name: str,
        data: gpd.GeoDataFrame,
        footprint: Geometry,
        description: str,
    ):
        self.name = name
        self.data = data
        self.footprint = footprint
        self.description = description

    def create_catalog(self) -> pystac.Catalog:
        """Creates catalog using parameters"""
        return pystac.Catalog(id=self.name, description=self.description)

    def transform_data(self) -> gpd.GeoDataFrame:
        transformed_df = self.data.copy()
        return transformed_df

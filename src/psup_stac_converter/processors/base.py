import geopandas as gpd
import pandas as pd
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
        keywords: list[str],
    ):
        self.name = name
        self.data = data
        self.footprint = footprint
        self.description = description
        self.keywords = keywords

    def create_catalog(self) -> pystac.Catalog:
        """Creates catalog using parameters"""
        return pystac.Catalog(id=self.name, description=self.description)

    def create_collection(self) -> pystac.Collection:
        # Create collection
        spatial_extent = pystac.SpatialExtent(
            bboxes=[self.data.geometry.total_bounds.tolist()]
        )
        temporal_extent = pystac.TemporalExtent(
            intervals=[
                [pd.Timestamp.min.to_pydatetime(), pd.Timestamp.max.to_pydatetime()]
            ]
        )
        collection_extent = pystac.Extent(
            spatial=spatial_extent, temporal=temporal_extent
        )

        collection_title = self.name.split(".")[0]
        return pystac.Collection(
            id="ias_" + collection_title,
            title=collection_title,
            description=self.description,
            extent=collection_extent,
            license="CC-BY-4.0",
            keywords=self.keywords,
            assets={
                "feature-catalog": pystac.Asset(
                    href=f"http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/geojson/{collection_title}",
                    title="feature-catalog",
                    roles=["data"],
                    media_type="application/geo+json",
                )
            },
        )

    def transform_data(self) -> gpd.GeoDataFrame:
        transformed_df = self.data.copy()
        return transformed_df

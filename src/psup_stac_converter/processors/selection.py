import json
from pathlib import Path
from typing import Literal

import geopandas as gpd
from shapely.geometry import shape

from psup_stac_converter.processors.base import BaseProcessorModule
from psup_stac_converter.processors.costard_craters import CostardCraters
from psup_stac_converter.processors.crater_detection import CraterDetection
from psup_stac_converter.processors.crocus_ls import CrocusLs
from psup_stac_converter.processors.hydrated_mineral_sites import (
    HydratedMineralProcessor,
)
from psup_stac_converter.processors.lcp_flahaut import LcpFlahaut
from psup_stac_converter.processors.lcp_vmwalls import LcpVmwalls
from psup_stac_converter.processors.scalloped_depression import ScallopedDepression

type ProcessorName = Literal[
    "hyd_global_290615.json",
    "detections_crateres_benjamin_bultel_icarus.json",
    "lcp_flahaut_et_al.json",
    "lcp_vmwalls.json",
    "crocus_ls150-310.json",
    "scalloped_depression.json",
    "costard_craters.json",
]


def open_problematic_df(filename: Path) -> gpd.GeoDataFrame:
    """
    Emergency function to use whenever `geopandas.read_file` doesn't work.
    """
    with open(filename, "r") as f:
        geojson_data = json.load(f)

    records = []
    for _feature in geojson_data["features"]:
        record = _feature["properties"]
        record["geometry"] = shape(_feature["geometry"])
        records.append(record)

    gdf = gpd.GeoDataFrame.from_records(records)
    gdf.set_geometry("geometry", inplace=True)
    return gdf


def select_processor(
    name: ProcessorName,
    metadata: gpd.GeoDataFrame,
    catalog_folder: Path,
) -> BaseProcessorModule:
    row_md = metadata[metadata["name"] == name]
    description = row_md["description"].item()
    footprint = row_md["footprint"].item()
    keywords = row_md["keywords"].item()

    if name != "crocus_ls150-310.json":
        data = gpd.read_file(catalog_folder / name)
    else:
        data = open_problematic_df(catalog_folder / name)

    if name == "hyd_global_290615.json":
        processor = HydratedMineralProcessor(
            name=name,
            data=data,
            description=description,
            footprint=footprint,
            keywords=keywords,
        )
    elif name == "costard_craters.json":
        processor = CostardCraters(
            name=name,
            data=data,
            description=description,
            footprint=footprint,
            keywords=keywords,
        )
    elif name == "crocus_ls150-310.json":
        processor = CrocusLs(
            name=name,
            data=data,
            description=description,
            footprint=footprint,
            keywords=keywords,
        )
    elif name == "detections_crateres_benjamin_bultel_icarus.json":
        processor = CraterDetection(
            name=name,
            data=data,
            description=description,
            footprint=footprint,
            keywords=keywords,
        )
    elif name == "lcp_flahaut_et_al.json":
        processor = LcpFlahaut(
            name=name,
            data=data,
            description=description,
            footprint=footprint,
            keywords=keywords,
        )
    elif name == "lcp_vmwalls.json":
        processor = LcpVmwalls(
            name=name,
            data=data,
            description=description,
            footprint=footprint,
            keywords=keywords,
        )
    elif name == "scalloped_depression.json":
        processor = ScallopedDepression(
            name=name,
            data=data,
            description=description,
            footprint=footprint,
            keywords=keywords,
        )
    else:
        raise ValueError(f"No processor is affiliated with the name {name}!")

    return processor

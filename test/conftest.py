# TODO move all test case code to this file

import shutil
import uuid
from pathlib import Path

import pytest
from pystac import Asset, Catalog, Item, ItemCollection

HERE = Path(__file__).resolve().parent


def get_data_file(rel_path: str) -> str:
    return str(HERE / "data-files" / rel_path)


@pytest.fixture
def sample_items(sample_item_collection: ItemCollection) -> list[Item]:
    return list(sample_item_collection)


@pytest.fixture(scope="function")
def tmp_asset(tmp_path: Path) -> Asset:
    """Copy the entirety of test-case-2 to tmp and"""
    src = get_data_file("catalogs/test-case-2")
    dst = str(tmp_path / str(uuid.uuid4()))
    shutil.copytree(src, dst)

    catalog = Catalog.from_file(f"{dst}/catalog.json")
    item = next(catalog.get_items(recursive=True))
    return next(v for v in item.assets.values())

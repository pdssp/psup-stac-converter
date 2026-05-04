import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import pystac
import pytest
from dateutil.parser import parse
from pystac import ExtensionTypeError, Item
from pystac.errors import ExtensionNotImplemented, RequiredPropertyMissing
from pystac.extensions.projection import ProjectionExtension
from pystac.summaries import RangeSummary
from pystac.utils import get_opt

from psup_stac_converter.stac_extra.eo_v2 import (
    PREFIX,
    SNOW_COVER_PROP,
    Band,
    EOExtension,
)
from psup_stac_converter.stac_extra.ssys_extension import (
    CatalogSolSysExtension,
    ItemSolSysExtension,
    SolSysExtension,
    SolSysTargetClass,
)

DATA_FILES = Path(__file__).resolve().parent / "data-files"

EXAMPLE_ITEM = DATA_FILES / "ssys_item.json"
EXAMPLE_COLLECTION = DATA_FILES / "ssys_collection.json"
EXAMPLE_CATALOG = DATA_FILES / "ssys_catalog.json"


LANDSAT_EXAMPLE_URI = str(DATA_FILES / "eo-landsat-example.json")
BANDS_IN_ITEM_URI = str(DATA_FILES / "sample-bands-in-item-properties.json")
EO_COLLECTION_URI = str(DATA_FILES / "eo-collection.json")
S2_ITEM_URI = str(DATA_FILES / "eo-sentinel2-item.json")
PLAIN_ITEM = str(DATA_FILES / "item/sample-item.json")


def assert_to_from_dict(
    stac_object_class: type[Item | pystac.Catalog | pystac.Collection],
    d: dict[str, Any],
) -> None:
    def _parse_times(a_dict: dict[str, Any]) -> None:
        for k, v in a_dict.items():
            if isinstance(v, dict):
                _parse_times(v)
            elif isinstance(v, (tuple, list, set)):
                for vv in v:
                    if isinstance(vv, dict):
                        _parse_times(vv)
            else:
                if k == "datetime":
                    if not isinstance(v, datetime):
                        a_dict[k] = parse(v)
                        a_dict[k] = a_dict[k].replace(microsecond=0)

    d1 = deepcopy(d)
    d2 = stac_object_class.from_dict(d, migrate=False).to_dict()
    _parse_times(d1)
    _parse_times(d2)
    assert d1 == d2


@pytest.fixture
def item_as_url() -> str:
    return str(EXAMPLE_ITEM)


@pytest.fixture
def item_as_dict(item_as_url: str) -> dict[str, Any]:
    with open(item_as_url) as f:
        d = json.load(f)
    return cast(dict[str, Any], d)


@pytest.fixture
def example_item(item_as_url: str) -> pystac.Item:
    return pystac.Item.from_file(item_as_url)


@pytest.fixture
def example_collection() -> pystac.Collection:
    return pystac.Collection.from_file(str(EXAMPLE_COLLECTION))


@pytest.fixture
def example_catalog() -> pystac.Catalog:
    return pystac.Catalog.from_file(str(EXAMPLE_CATALOG))


@pytest.mark.vcr()
def test_item_validate_schema(example_item: pystac.Item) -> None:
    assert example_item.validate()


def test_item_with_ssys_ext(example_item: pystac.Item) -> None:
    assert SolSysExtension.has_extension(example_item)
    assert SolSysExtension.get_schema_uri() in example_item.stac_extensions

    item_ssys = SolSysExtension.ext(example_item)
    assert isinstance(item_ssys, ItemSolSysExtension)

    targets = item_ssys.targets
    target_class = item_ssys.target_class

    assert targets is not None
    assert len(targets) == 1
    assert targets[0] == "Europa"

    assert target_class is not None
    assert target_class == SolSysTargetClass.PLANET


def test_item_conversion_dict(
    example_item: pystac.Item, item_as_dict: dict[str, Any]
) -> None:
    example_as_dict = example_item.to_dict(
        include_self_link=False, transform_hrefs=False
    )
    example_properties = example_as_dict.get("properties")
    item_properties = item_as_dict.get("properties")

    assert example_properties is not None
    assert item_properties is not None

    ssys_elements = {
        k: v for k, v in example_properties.items() if k.startswith("ssys:")
    }
    assert len(ssys_elements) == 2
    assert "ssys:local_time" not in ssys_elements

    targets = ssys_elements.get("ssys:targets")
    target_class = ssys_elements.get("ssys:target_class")

    assert targets is not None
    assert len(targets) == 1
    assert targets[0] == "Europa"
    assert targets == item_properties["ssys:targets"]

    assert target_class is not None
    assert target_class == SolSysTargetClass.PLANET
    assert target_class == item_properties["ssys:target_class"]


def test_add_ext_to_catalog(example_catalog: pystac.Catalog) -> None:
    assert SolSysExtension.has_extension(example_catalog)
    SolSysExtension.ext(example_catalog)

    assert SolSysExtension.get_schema_uri() in example_catalog.stac_extensions

    uris = [
        uri
        for uri in example_catalog.stac_extensions
        if uri == SolSysExtension.get_schema_uri()
    ]
    assert len(uris) == 1

    catalog_ssys = SolSysExtension.ext(example_catalog)

    assert isinstance(
        catalog_ssys,
        CatalogSolSysExtension,
    )

    targets = catalog_ssys.targets
    assert targets is not None
    assert len(targets) == 1
    assert targets[0] == "Europa"


DATA_FILES = Path(__file__).resolve().parent / "data-files"


def test_band_create() -> None:
    band = Band.create(
        name="B01",
        common_name="red",
        description=Band.band_description("red"),
        center_wavelength=0.65,
        full_width_half_max=0.1,
        solar_illumination=42.0,
    )

    assert band.name == "B01"
    assert band.common_name == "red"
    assert band.description, "Common name: red == Range: 0.6 to 0.7"
    assert band.center_wavelength == 0.65
    assert band.full_width_half_max == 0.1
    assert band.solar_illumination == 42.0
    assert band.__repr__() == "<BandV2 name=B01>"


def test_band_description_unknown_band() -> None:
    desc = Band.band_description("rainbow")
    assert desc is None


def test_to_from_dict() -> None:
    with open(LANDSAT_EXAMPLE_URI) as f:
        item_dict = json.load(f)
    assert_to_from_dict(Item, item_dict)


def test_from_file_to_dict(ext_item_uri: str, ext_item: pystac.Item) -> None:
    with open(ext_item_uri) as f:
        d = json.load(f)
    actual = ext_item.to_dict(include_self_link=False)
    assert actual == d


def test_add_to() -> None:
    item = Item.from_file(PLAIN_ITEM)
    assert EOExtension.get_schema_uri() not in item.stac_extensions

    # Check that the URI gets added to stac_extensions
    EOExtension.add_to(item)
    assert EOExtension.get_schema_uri() in item.stac_extensions

    # Check that the URI only gets added once, regardless of how many times add_to
    # is called.
    EOExtension.add_to(item)
    EOExtension.add_to(item)

    eo_uris = [
        uri for uri in item.stac_extensions if uri == EOExtension.get_schema_uri()
    ]
    assert len(eo_uris) == 1


@pytest.mark.vcr()
def test_validate_eo() -> None:
    item = pystac.Item.from_file(LANDSAT_EXAMPLE_URI)
    item2 = pystac.Item.from_file(BANDS_IN_ITEM_URI)
    item.validate()
    item2.validate()


@pytest.mark.vcr()
def test_bands() -> None:
    item = pystac.Item.from_file(BANDS_IN_ITEM_URI)

    # Get
    assert "bands" in item.properties
    bands = EOExtension.ext(item).bands
    assert bands is not None
    assert list(map(lambda x: x.name, bands)) == ["band1", "band2", "band3", "band4"]

    # Set
    new_bands = [
        Band.create(name="red", description=Band.band_description("red")),
        Band.create(name="green", description=Band.band_description("green")),
        Band.create(name="blue", description=Band.band_description("blue")),
    ]

    EOExtension.ext(item).bands = new_bands
    assert (
        "Common name: red, Range: 0.62 to 0.69"
        == item.properties["bands"][0]["description"]
    )
    assert len(EOExtension.ext(item).bands or []) == 3
    item.validate()


def test_asset_bands_s2() -> None:
    item = pystac.Item.from_file(S2_ITEM_URI)
    mtd_asset = item.get_assets()["mtd"]
    assert EOExtension.ext(mtd_asset).bands is None


@pytest.mark.vcr()
def test_asset_bands() -> None:
    item = pystac.Item.from_file(LANDSAT_EXAMPLE_URI)

    # Get

    b1_asset = item.assets["B1"]
    asset_bands = EOExtension.ext(b1_asset).bands
    assert asset_bands is not None
    assert len(asset_bands) == 1
    assert asset_bands[0].name == "B1"
    assert asset_bands[0].solar_illumination == 2000

    index_asset = item.assets["index"]
    asset_bands = EOExtension.ext(index_asset).bands
    assert asset_bands is None

    # No asset specified
    item_bands = EOExtension.ext(item).bands
    assert item_bands is not None

    # Set
    b2_asset = item.assets["B2"]
    assert get_opt(EOExtension.ext(b2_asset).bands)[0].name == "B2"
    EOExtension.ext(b2_asset).bands = EOExtension.ext(b1_asset).bands

    new_b2_asset_bands = EOExtension.ext(item.assets["B2"]).bands

    assert get_opt(new_b2_asset_bands)[0].name == "B1"

    item.validate()

    # Check adding a new asset
    new_bands = [
        Band.create(
            name="red",
            description=Band.band_description("red"),
            solar_illumination=1900,
        ),
        Band.create(
            name="green",
            description=Band.band_description("green"),
            solar_illumination=1950,
        ),
        Band.create(
            name="blue",
            description=Band.band_description("blue"),
            solar_illumination=2000,
        ),
    ]
    asset = pystac.Asset(href="some/path.tif", media_type=pystac.MediaType.GEOTIFF)
    EOExtension.ext(asset).bands = new_bands
    item.add_asset("test", asset)

    assert len(item.assets["test"].extra_fields["bands"]) == 3


@pytest.mark.vcr()
def test_cloud_cover() -> None:
    item = pystac.Item.from_file(LANDSAT_EXAMPLE_URI)

    # Get
    assert "eo:cloud_cover" in item.properties
    cloud_cover = EOExtension.ext(item).cloud_cover
    assert cloud_cover == 78

    # Set
    EOExtension.ext(item).cloud_cover = 50
    assert item.properties["eo:cloud_cover"] == 50

    # Get from Asset
    b2_asset = item.assets["B2"]
    assert EOExtension.ext(b2_asset).cloud_cover == EOExtension.ext(item).cloud_cover

    b3_asset = item.assets["B3"]
    assert EOExtension.ext(b3_asset).cloud_cover == 20

    # Set on Asset
    EOExtension.ext(b2_asset).cloud_cover = 10
    assert EOExtension.ext(b2_asset).cloud_cover == 10

    item.validate()


def test_summaries() -> None:
    col = pystac.Collection.from_file(EO_COLLECTION_URI)
    eo_summaries = EOExtension.summaries(col)

    # Get

    cloud_cover_summaries = eo_summaries.cloud_cover
    assert cloud_cover_summaries is not None
    assert cloud_cover_summaries.minimum == 0.0
    assert cloud_cover_summaries.maximum == 80.0

    snow_cover_summaries = eo_summaries.snow_cover
    assert snow_cover_summaries is not None
    assert snow_cover_summaries.minimum == 0.0
    assert snow_cover_summaries.maximum == 80.0

    bands = eo_summaries.bands
    assert bands is not None
    assert len(bands) == 11

    # Set

    eo_summaries.cloud_cover = RangeSummary(1.0, 2.0)
    eo_summaries.snow_cover = RangeSummary(4.0, 23)
    eo_summaries.bands = [Band.create(name="test")]

    col_dict = col.to_dict()
    assert len(col_dict["summaries"]["bands"]) == 1
    assert col_dict["summaries"]["eo:cloud_cover"]["minimum"] == 1.0
    assert col_dict["summaries"]["eo:snow_cover"]["minimum"] == 4.0


def test_summaries_adds_uri() -> None:
    col = pystac.Collection.from_file(EO_COLLECTION_URI)
    col.stac_extensions = []
    with pytest.raises(
        pystac.ExtensionNotImplemented, match="Extension 'eo' is not implemented"
    ):
        EOExtension.summaries(col, add_if_missing=False)

    EOExtension.summaries(col, add_if_missing=True)

    assert EOExtension.get_schema_uri() in col.stac_extensions

    EOExtension.remove_from(col)
    assert EOExtension.get_schema_uri() not in col.stac_extensions


def test_read_pre_09_fields_into_common_metadata() -> None:
    eo_item = pystac.Item.from_file(
        str(DATA_FILES / "examples/0.8.1/item-spec/examples/landsat8-sample.json")
    )

    assert eo_item.common_metadata.platform == "landsat-8"
    assert eo_item.common_metadata.instruments == ["oli_tirs"]


def test_reads_asset_bands_in_pre_1_0_version() -> None:
    item = pystac.Item.from_file(
        str(DATA_FILES / "examples/0.9.0/item-spec/examples/landsat8-sample.json")
    )

    bands = EOExtension.ext(item.assets["B9"]).bands

    assert len(bands or []) == 1
    assert get_opt(bands)[0].common_name == "cirrus"


def test_reads_gsd_in_pre_1_0_version() -> None:
    eo_item = pystac.Item.from_file(
        str(DATA_FILES / "examples/0.9.0/item-spec/examples/landsat8-sample.json")
    )

    assert eo_item.common_metadata.gsd == 30.0


def test_item_apply() -> None:
    item = pystac.Item.from_file(LANDSAT_EXAMPLE_URI)
    eo_ext = EOExtension.ext(item)
    test_band = Band.create(name="test")

    assert eo_ext.cloud_cover == 78
    assert test_band not in (eo_ext.bands or [])

    eo_ext.apply(bands=[test_band], cloud_cover=15)
    assert eo_ext.bands is not None

    assert test_band.to_dict() == eo_ext.bands[0].to_dict()
    assert eo_ext.cloud_cover == 15


def test_extend_invalid_object() -> None:
    link = pystac.Link("child", "https://some-domain.com/some/path/to.json")

    with pytest.raises(pystac.ExtensionTypeError):
        EOExtension.ext(link)  # type: ignore


def test_extension_not_implemented() -> None:
    # Should raise exception if Item does not include extension URI
    item = pystac.Item.from_file(PLAIN_ITEM)

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = EOExtension.ext(item)

    # Should raise exception if owning Item does not include extension URI
    asset = item.assets["thumbnail"]

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = EOExtension.ext(asset)

    # Should succeed if Asset has no owner
    ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
    _ = EOExtension.ext(ownerless_asset)


def test_item_ext_add_to() -> None:
    item = pystac.Item.from_file(PLAIN_ITEM)
    assert EOExtension.get_schema_uri() not in item.stac_extensions

    _ = EOExtension.ext(item, add_if_missing=True)

    assert EOExtension.get_schema_uri() in item.stac_extensions


def test_asset_ext_add_to() -> None:
    item = pystac.Item.from_file(PLAIN_ITEM)
    assert EOExtension.get_schema_uri() not in item.stac_extensions
    asset = item.assets["thumbnail"]

    _ = EOExtension.ext(asset, add_if_missing=True)

    assert EOExtension.get_schema_uri() in item.stac_extensions


def test_asset_ext_add_to_ownerless_asset() -> None:
    item = pystac.Item.from_file(PLAIN_ITEM)
    asset_dict = item.assets["thumbnail"].to_dict()
    asset = pystac.Asset.from_dict(asset_dict)

    with pytest.raises(pystac.STACError):
        _ = EOExtension.ext(asset, add_if_missing=True)


def test_should_raise_exception_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError, match=r"^EOExtension does not apply to type 'object'$"
    ):
        # calling it wrong purposely -------v
        EOExtension.ext(object())  # type: ignore


def test_migration() -> None:
    item_0_8_path = str(
        DATA_FILES / "examples/0.8.1/item-spec/examples/sentinel2-sample.json"
    )
    with open(item_0_8_path) as src:
        item_dict = json.load(src)

    assert "eo:epsg" in item_dict["properties"]

    item = Item.from_file(item_0_8_path)

    assert "eo:epsg" not in item.properties
    assert "proj:code" in item.properties
    assert ProjectionExtension.get_schema_uri() in item.stac_extensions
    assert item.ext.proj.epsg == item_dict["properties"]["eo:epsg"]


@pytest.fixture
def ext_item_uri() -> str:
    return str(DATA_FILES / "eo-landsat-example.json")


@pytest.fixture
def ext_item(ext_item_uri: str) -> pystac.Item:
    return pystac.Item.from_file(ext_item_uri)


@pytest.mark.parametrize("field", ["cloud_cover", "snow_cover"])
def test_get_field(ext_item: pystac.Item, field: str) -> None:
    prop = ext_item.properties[f"{PREFIX}{field}"]
    attr = getattr(EOExtension.ext(ext_item), field)

    assert attr is not None
    assert attr == prop


@pytest.mark.vcr()
@pytest.mark.parametrize(
    "field,value",
    [
        ("cloud_cover", 7.8),
        ("snow_cover", 99),
    ],
)
def test_set_field(ext_item: pystac.Item, field: str, value) -> None:  # type: ignore
    original = ext_item.properties[f"{PREFIX}{field}"]
    setattr(EOExtension.ext(ext_item), field, value)
    new = ext_item.properties[f"{PREFIX}{field}"]

    assert new != original
    assert new == value
    assert ext_item.validate()


def test_snow_cover_set_to_none_pops_from_dict(ext_item: pystac.Item) -> None:
    assert SNOW_COVER_PROP in ext_item.properties

    EOExtension.ext(ext_item).snow_cover = None
    assert SNOW_COVER_PROP not in ext_item.properties


def test_snow_cover_raises_informative_error(ext_item: pystac.Item) -> None:
    with pytest.raises(ValueError, match="must be number"):
        EOExtension.ext(ext_item).snow_cover = True

    with pytest.raises(ValueError, match="must be between 0 and 100"):
        EOExtension.ext(ext_item).snow_cover = 100.5


def test_older_extension_version(ext_item: Item) -> None:
    old = "https://stac-extensions.github.io/eo/v1.1.0/schema.json"
    new = "https://stac-extensions.github.io/eo/v2.0.0/schema.json"

    stac_extensions = set(ext_item.stac_extensions)
    stac_extensions.remove(new)
    stac_extensions.add(old)
    item_as_dict = ext_item.to_dict(include_self_link=False, transform_hrefs=False)
    item_as_dict["stac_extensions"] = list(stac_extensions)
    item = Item.from_dict(item_as_dict, migrate=False)
    assert EOExtension.has_extension(item)
    assert old in item.stac_extensions

    migrated_item = pystac.Item.from_dict(item_as_dict, migrate=True)
    assert EOExtension.has_extension(migrated_item)
    assert new in migrated_item.stac_extensions


@pytest.mark.parametrize(
    "filter,count",
    [
        (dict(), 11),
        ({"name": "B4"}, 1),
        ({"common_name": "blue"}, 1),
        ({"name": "B4", "common_name": "red"}, 1),
        ({"name": "B4", "common_name": "green"}, 0),
    ],
)
def test_get_assets(ext_item: pystac.Item, filter: dict[str, str], count: int) -> None:
    assets = EOExtension.ext(ext_item).get_assets(**filter)  # type:ignore
    assert len(assets) == count


def test_get_assets_works_even_if_band_info_is_incomplete(
    ext_item: pystac.Item,
) -> None:
    name = ext_item.assets["B4"].extra_fields["bands"][0].pop("name")
    common_name = ext_item.assets["B2"].extra_fields["bands"][0].pop("eo:common_name")

    eo_ext = EOExtension.ext(ext_item)

    assets = eo_ext.get_assets(name=name)  # type:ignore
    assert len(assets) == 0

    assets = eo_ext.get_assets(common_name=common_name)  # type:ignore
    assert len(assets) == 0


def test_exception_should_include_hint_if_obj_is_collection(
    example_collection: pystac.Collection,
) -> None:
    with pytest.raises(
        ExtensionTypeError,
        match="Hint: Did you mean to use `EOExtension.summaries` instead?",
    ):
        EOExtension.ext(example_collection)  # type:ignore


def test_ext_syntax(ext_item: pystac.Item) -> None:
    assert ext_item.ext.eo.cloud_cover == 78
    assert (bands := ext_item.assets["B1"].ext.eo.bands)
    assert bands[0].name == "B1"


def test_ext_syntax_remove(ext_item: pystac.Item) -> None:
    ext_item.ext.remove("eo")
    assert ext_item.ext.has("eo") is False
    with pytest.raises(ExtensionNotImplemented):
        ext_item.ext.eo


def test_ext_syntax_add(example_item: pystac.Item) -> None:
    example_item.ext.add("eo")
    assert example_item.ext.has("eo") is True
    assert isinstance(example_item.ext.eo, EOExtension)


def test_required_property_missing(ext_item: pystac.Item) -> None:
    # https://github.com/stac-utils/pystac/issues/1402
    d = ext_item.to_dict(include_self_link=False, transform_hrefs=False)
    del d["assets"]["B1"]["bands"][0]["name"]
    item = pystac.Item.from_dict(d)
    bands = item.assets["B1"].ext.eo.bands
    assert bands is not None
    with pytest.raises(RequiredPropertyMissing):
        bands[0].name


def test_unnecessary_migrations_not_performed(ext_item: Item) -> None:
    item_as_dict = ext_item.to_dict(include_self_link=False, transform_hrefs=False)
    item_as_dict["stac_version"] = "1.0.0"
    item_as_dict["properties"]["bands"] = [{"name": "B1", "common_name": "coastal"}]

    item = Item.from_dict(item_as_dict)

    migrated_item = pystac.Item.from_dict(item_as_dict, migrate=True)

    assert item.properties == migrated_item.properties
    assert len(item.assets) == len(migrated_item.assets)
    for key, value in item.assets.items():
        assert value.to_dict() == migrated_item.assets[key].to_dict()

import json
from collections import Counter
from typing import Any, cast

import pystac
from pystac.extensions import eo, projection, view
from pystac.extensions.hooks import ExtensionHooks
from pystac.serialization.identify import STACJSONDescription, STACVersionID
from pystac.utils import StringEnum, map_opt

SCHEMA_URI: str = "https://stac-extensions.github.io/eo/v2.0.0/schema.json"
SCHEMA_URIS: list[str] = [
    "https://stac-extensions.github.io/eo/v1.1.0/schema.json",
    "https://stac-extensions.github.io/eo/v1.0.0/schema.json",
    SCHEMA_URI,
]
PREFIX: str = "eo:"

# Field names
BANDS_PROP: str = "bands"
CLOUD_COVER_PROP: str = PREFIX + "cloud_cover"
SNOW_COVER_PROP: str = PREFIX + "snow_cover"
COMMON_NAME_PROP: str = PREFIX + "common_name"
CENTER_WAVELENGTH_PROP: str = PREFIX + "center_wavelength"
FULL_WIDTH_HALF_MAX_PROP: str = PREFIX + "full_width_half_max"
SOLAR_ILLUMINATION_PROP: str = PREFIX + "solar_illumination"


class EOCommonName(StringEnum):
    PAN = "pan"
    COASTAL = "coastal"
    BLUE = "blue"
    GREEN = "green"
    GREEN05 = "green05"
    YELLOW = "yellow"
    RED = "red"
    REDEDGE = "rededge"
    REDEDGE071 = "rededge071"
    REDEDGE075 = "rededge075"
    REDEDGE078 = "rededge078"
    NIR = "nir"
    NIR08 = "nir08"
    NIR09 = "nir09"
    CIRRUS = "cirrus"
    SWIR16 = "swir16"
    SWIR22 = "swir22"
    LWIR = "lwir"
    LWIR11 = "lwir11"
    LWIR12 = "lwir12"


class Band(eo.Band):
    @property
    def common_name(self) -> str | None:
        """Get or sets the name commonly used to refer to the band to make it easier
            to search for bands across instruments. See the :stac-ext:`list of accepted
            common names <eo#common-band-names>`.

        Returns:
            Optional[str]
        """
        return self.properties.get("eo:common_name")

    @common_name.setter
    def common_name(self, v: str | None) -> None:
        if v is not None:
            self.properties["eo:common_name"] = v
        else:
            self.properties.pop("eo:common_name", None)

    @property
    def center_wavelength(self) -> float | None:
        """Get or sets the center wavelength of the band, in micrometers (μm).

        Returns:
            float
        """
        return self.properties.get("eo:center_wavelength")

    @center_wavelength.setter
    def center_wavelength(self, v: float | None) -> None:
        if v is not None:
            self.properties["eo:center_wavelength"] = v
        else:
            self.properties.pop("eo:center_wavelength", None)

    @property
    def full_width_half_max(self) -> float | None:
        """Get or sets the full width at half maximum (FWHM). The width of the band,
            as measured at half the maximum transmission, in micrometers (μm).

        Returns:
            [float]
        """
        return self.properties.get("eo:full_width_half_max")

    @full_width_half_max.setter
    def full_width_half_max(self, v: float | None) -> None:
        if v is not None:
            self.properties["eo:full_width_half_max"] = v
        else:
            self.properties.pop("eo:full_width_half_max", None)

    @property
    def solar_illumination(self) -> float | None:
        """Get or sets the solar illumination of the band,
            as measured at half the maximum transmission, in W/m2/micrometers.

        Returns:
            [float]
        """
        return self.properties.get("eo:solar_illumination")

    @solar_illumination.setter
    def solar_illumination(self, v: float | None) -> None:
        if v is not None:
            self.properties["eo:solar_illumination"] = v
        else:
            self.properties.pop("eo:solar_illumination", None)

    @staticmethod
    def band_range(common_name: str) -> tuple[float, float] | None:
        """Gets the band range for a common band name.

        Args:
            common_name : The common band name. Must be one of the :stac-ext:`list of
                accepted common names <eo#common-band-names>`.

        Returns:
            Tuple[float, float] or None: The band range for this name as (min, max), or
            None if this is not a recognized common name.
        """
        name_to_range = {
            "pan": (0.40, 1.00),
            "coastal": (0.40, 0.45),
            "blue": (0.45, 0.53),
            "green": (0.51, 0.60),
            "green05": (0.51, 0.55),
            "yellow": (0.58, 0.62),
            "red": (0.62, 0.69),
            "rededge": (0.69, 0.79),
            "rededge071": (0.69, 0.73),
            "rededge075": (0.73, 0.76),
            "rededge078": (0.76, 0.79),
            "nir": (0.76, 1.00),
            "nir08": (0.80, 0.90),
            "nir09": (0.90, 1.00),
            "cirrus": (1.35, 1.40),
            "swir16": (1.55, 1.75),
            "swir22": (2.08, 2.35),
            "lwir": (10.4, 12.5),
            "lwir11": (10.5, 11.5),
            "lwir12": (11.5, 12.5),
        }

        return name_to_range.get(common_name)

    @staticmethod
    def band_description(common_name: str) -> str | None:
        """Returns a description of the band for one with a common name.

        Args:
            common_name : The common band name. Must be one of the :stac-ext:`list of
                accepted common names <eo#common-band-names>`.

        Returns:
            str or None: If a recognized common name, returns a description including
            the band range. Otherwise, returns None.
        """
        r = Band.band_range(common_name)
        if r is not None:
            return f"Common name: {common_name}, Range: {r[0]} to {r[1]}"
        return None

    def __repr__(self) -> str:
        return f"<BandV2 name={self.properties.get('name')}>"


class EOExtension(eo.EOExtension[eo.T]):
    def apply(
        self,
        bands: list[Band] | None = None,
        cloud_cover: float | None = None,
        snow_cover: float | None = None,
        common_name: EOCommonName | None = None,
        center_wavelength: float | None = None,
        full_width_half_max: float | None = None,
        solar_illumination: float | None = None,
    ) -> None:
        """Applies Electro-Optical Extension properties to the extended
        :class:`~pystac.Item` or :class:`~pystac.Asset`.

        Args:
            bands : A list of available bands where each item is a :class:`~Band`
                object. If given, requires at least one band.
            cloud_cover : The estimate of cloud cover as a percentage
                (0-100) of the entire scene. If not available the field should not
                be provided.
            snow_cover : The estimate of snow cover as a percentage
                (0-100) of the entire scene. If not available the field should not
                be provided.
        """
        self.bands = bands
        self.cloud_cover = eo.validated_percentage(cloud_cover)
        self.snow_cover = eo.validated_percentage(snow_cover)
        self.common_name = common_name
        self.center_wavelength = center_wavelength
        self.full_width_half_max = full_width_half_max
        self.solar_illumination = solar_illumination

    @property
    def bands(self) -> list[Band] | None:
        """Gets or sets a list of available bands where each item is a :class:`~Band`
        object (or ``None`` if no bands have been set). If not available the field
        should not be provided.
        """
        return self._get_bands()

    @bands.setter
    def bands(self, v: list[Band] | None) -> None:
        self._set_property(
            BANDS_PROP, map_opt(lambda bands: [b.to_dict() for b in bands], v)
        )

    def _get_bands(self) -> list[Band] | None:
        return map_opt(
            lambda bands: [Band(b) for b in bands],
            self._get_property(BANDS_PROP, list[dict[str, Any]]),
        )

    # common_name
    @property
    def common_name(self) -> EOCommonName | None:
        """Gets or sets the name commonly used to refer to the band to make it
        easier to search for bands across instruments. Must be an accepted
        common name from `EOCommonName`:

        - pan
        - coastal
        - blue
        - green
        - green05
        - yellow
        - red
        - rededge
        - rededge071
        - rededge075
        - rededge078
        - nir
        - nir08
        - nir09
        - cirrus
        - swir16
        - swir22
        - lwir
        - lwir11
        - lwir12

        Raises:
            pystac.ExtensionTypeError

        Returns:
            EOCommonName or None
        """
        return self._get_property(COMMON_NAME_PROP, EOCommonName)

    @common_name.setter
    def common_name(self, v: EOCommonName | None) -> None:
        self._set_property(COMMON_NAME_PROP, v, pop_if_none=True)

    # center_wavelength
    @property
    def center_wavelength(self) -> float | None:
        """Gets or sets The center wavelength of the band, in micrometers (μm).

        Returns:
            float | None
        """
        return self._get_property(CENTER_WAVELENGTH_PROP, float)

    @center_wavelength.setter
    def center_wavelength(self, v: float | None) -> None:
        self._set_property(CENTER_WAVELENGTH_PROP, v, pop_if_none=True)

    # full_width_half_max
    @property
    def full_width_half_max(self) -> float | None:
        """Gets or sets Full width at half maximum (FWHM). The width of the
        band, as measured at half the maximum transmission, in micrometers (μm).

        Returns:
            float | None
        """
        return self._get_property(FULL_WIDTH_HALF_MAX_PROP, float)

    @full_width_half_max.setter
    def full_width_half_max(self, v: float | None) -> None:
        self._set_property(FULL_WIDTH_HALF_MAX_PROP, v, pop_if_none=True)

    # solar_illumination
    @property
    def solar_illumination(self) -> float | None:
        """Gets or sets the solar illumination of the band, as measured at
        half the maximum transmission, in W/m2/micrometers.

        Returns:
            float | None
        """
        return self._get_property(SOLAR_ILLUMINATION_PROP, float)

    @solar_illumination.setter
    def solar_illumination(self, v: float | None) -> None:
        self._set_property(SOLAR_ILLUMINATION_PROP, v, pop_if_none=True)

    @classmethod
    def ext(cls, obj: eo.T, add_if_missing: bool = False) -> "EOExtension[eo.T]":
        """Extends the given STAC Object with properties from the
        :stac-ext:`Electro-Optical Extension <eo>`.

        This extension can be applied to instances of :class:`~pystac.Item` or
        :class:`~pystac.Asset`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(EOExtension[eo.T], ItemEOExtension(obj))
        elif isinstance(obj, pystac.Asset):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(EOExtension[eo.T], AssetEOExtension(obj))
        elif isinstance(obj, pystac.ItemAssetDefinition):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(EOExtension[eo.T], ItemAssetsEOExtension(obj))
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> "SummariesEOExtension":
        """Returns the extended summaries object for the given collection."""
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesEOExtension(obj)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI


class ItemEOExtension(EOExtension, eo.ItemEOExtension):
    """Quick patch for ItemEOExtension's V2"""

    def _get_bands(self) -> list[Band] | None:
        """Get or sets a list of :class:`~pystac.Band` objects that represent
        the available bands.
        """
        bands = self._get_property(BANDS_PROP, list[dict[str, Any]])

        # get assets with eo:bands even if not in item
        if bands is None:
            asset_bands: list[dict[str, Any]] = []
            for _, value in self.item.get_assets().items():
                if BANDS_PROP in value.extra_fields:
                    asset_bands.extend(
                        cast(list[dict[str, Any]], value.extra_fields.get(BANDS_PROP))
                    )
            if any(asset_bands):
                bands = asset_bands

        if bands is not None:
            return [Band(b) for b in bands]
        return None

    def get_assets(
        self,
        name: str | None = None,
        common_name: str | None = None,
    ) -> dict[str, pystac.Asset]:
        """Get the item's assets where eo:bands are defined.

        Args:
            name: If set, filter the assets such that only those with a
                matching ``eo:band.name`` are returned.
            common_name: If set, filter the assets such that only those with a matching
                ``eo:band.common_name`` are returned.

        Returns:
            Dict[str, Asset]: A dictionary of assets that match ``name``
                and/or ``common_name`` if set or else all of this item's assets were
                eo:bands are defined.
        """
        kwargs = {"name": name, COMMON_NAME_PROP: common_name}  # "eo:common_name"
        return {
            key: asset
            for key, asset in self.item.get_assets().items()
            if BANDS_PROP in asset.extra_fields
            and all(
                v is None or any(v == b.get(k) for b in asset.extra_fields[BANDS_PROP])
                for k, v in kwargs.items()
            )
        }

    def __repr__(self) -> str:
        return f"<ItemEOExtensionV2 Item id={self.item.id}>"


class AssetEOExtension(EOExtension, eo.AssetEOExtension):
    def _get_bands(self) -> list[Band] | None:
        if BANDS_PROP not in self.properties:
            return None
        raw_bands = cast(list[dict[str, Any]], self.properties.get(BANDS_PROP))

        asset_eo_props = {
            k: v
            for k, v in self.properties.items()
            if k.startswith(PREFIX) and k not in (CLOUD_COVER_PROP, SNOW_COVER_PROP)
        }
        if asset_eo_props:
            return [Band({**asset_eo_props, **band}) for band in raw_bands]
        return [Band(b) for b in raw_bands]

    def __repr__(self) -> str:
        return f"<AssetEOExtensionV2 Asset href={self.asset_href}>"


class ItemAssetsEOExtension(EOExtension, eo.ItemAssetsEOExtension):
    def _get_bands(self) -> list[Band] | None:
        if BANDS_PROP not in self.properties:
            return None
        return list(
            map(
                lambda band: Band(band),
                cast(list[dict[str, Any]], self.properties.get(BANDS_PROP)),
            )
        )


class SummariesEOExtension(eo.SummariesEOExtension):
    """A concrete implementation of :class:`~pystac.extensions.base.SummariesExtension`
    that extends the ``summaries`` field of a :class:`~pystac.Collection` to include
    properties defined in the :stac-ext:`Electro-Optical Extension <eo>`.
    """

    @property
    def bands(self) -> list[Band] | None:
        """Get or sets the summary of :attr:`EOExtension.bands` values
        for this Collection.
        """

        return map_opt(
            lambda bands: [Band(b) for b in bands],
            self.summaries.get_list(BANDS_PROP),
        )

    @bands.setter
    def bands(self, v: list[Band] | None) -> None:
        self._set_summary(BANDS_PROP, map_opt(lambda x: [b.to_dict() for b in x], v))


class EOExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {
        "eo",
        *[uri for uri in SCHEMA_URIS if uri != SCHEMA_URI],
    }
    stac_object_types = {pystac.STACObjectType.ITEM}

    def _migrate_obj_with_bands(self, obj: dict[str, Any]) -> None:
        """Handles the migration of bands inside the metadata.

        - If object is a STAC Item, pass obj["properties"]
        - If object is an item asset, pass the asset
        """
        if "eo:bands" not in obj:
            return None

        old_bands = obj.pop("eo:bands")

        if old_bands and isinstance(old_bands[0], int):
            return None

        to_be_renamed = frozenset(
            [
                "common_name",
                "center_wavelength",
                "full_width_half_max",
                "solar_illumination",
            ]
        )

        def transform_band(band_obj: dict[str, Any]) -> dict[str, Any]:
            return {
                PREFIX + k if k in to_be_renamed else k: v for k, v in band_obj.items()
            }

        if "bands" not in obj:
            obj["bands"] = [transform_band(band) for band in old_bands]

        elif len(obj["bands"]) == len(old_bands):
            for band, old_band in zip(obj["bands"], old_bands):
                band.update(transform_band(old_band))

        else:
            old_bands_by_name = {band["name"]: band for band in old_bands}
            seen = set()
            for idx, band in enumerate(obj["bands"]):
                name = band["name"]
                if name in old_bands_by_name:
                    seen.add(name)
                    obj["bands"][idx].update(transform_band(old_bands_by_name[name]))
            obj["bands"].extend(
                transform_band(band) for band in old_bands if band["name"] not in seen
            )

        bands = obj["bands"]
        n_elements = len(bands)

        # If no bands, skip
        if not n_elements:
            return None

        promotable = frozenset(PREFIX + k for k in to_be_renamed)

        counters: dict[str, Counter[str]] = {
            key: Counter(
                json.dumps(band[key], sort_keys=True) for band in bands if key in band
            )
            for key in promotable
        }

        for k, counter in counters.items():
            if counter.total() != n_elements:
                continue
            dom_element, dom_count = counter.most_common(1)[0]

            if dom_count == 1 and len(bands) > 1:
                continue

            obj[k] = json.loads(dom_element)
            for band in bands:
                if json.dumps(band.get(k), sort_keys=True) == dom_element:
                    del band[k]

        # Next make sure "bands" is empty
        if all([len(b) == 0 for b in bands]):
            del obj["bands"]

    def migrate(
        self,
        obj: dict[str, Any],
        version: STACVersionID,
        info: STACJSONDescription,
    ) -> None:
        if version < "0.9":
            # Some eo fields became common_metadata
            if (
                "eo:platform" in obj["properties"]
                and "platform" not in obj["properties"]
            ):
                obj["properties"]["platform"] = obj["properties"]["eo:platform"]
                del obj["properties"]["eo:platform"]

            if (
                "eo:instrument" in obj["properties"]
                and "instruments" not in obj["properties"]
            ):
                obj["properties"]["instruments"] = [obj["properties"]["eo:instrument"]]
                del obj["properties"]["eo:instrument"]

            if (
                "eo:constellation" in obj["properties"]
                and "constellation" not in obj["properties"]
            ):
                obj["properties"]["constellation"] = obj["properties"][
                    "eo:constellation"
                ]
                del obj["properties"]["eo:constellation"]

            # Some eo fields became view extension fields
            eo_to_view_fields = [
                "off_nadir",
                "azimuth",
                "incidence_angle",
                "sun_azimuth",
                "sun_elevation",
            ]

            for field in eo_to_view_fields:
                if f"eo:{field}" in obj["properties"]:
                    if "stac_extensions" not in obj:
                        obj["stac_extensions"] = []
                    if view.SCHEMA_URI not in obj["stac_extensions"]:
                        obj["stac_extensions"].append(view.SCHEMA_URI)
                    if f"view:{field}" not in obj["properties"]:
                        obj["properties"][f"view:{field}"] = obj["properties"][
                            f"eo:{field}"
                        ]
                        del obj["properties"][f"eo:{field}"]

            # eo:epsg became proj:epsg in Projection Extension <2.0.0 and became
            # proj:code in Projection Extension 2.0.0
            eo_epsg = PREFIX + "epsg"
            proj_epsg = projection.PREFIX + "epsg"
            proj_code = projection.PREFIX + "code"
            if (
                eo_epsg in obj["properties"]
                and proj_epsg not in obj["properties"]
                and proj_code not in obj["properties"]
            ):
                obj["stac_extensions"] = obj.get("stac_extensions", [])
                if set(obj["stac_extensions"]).intersection(
                    projection.ProjectionExtensionHooks.pre_2
                ):
                    obj["properties"][proj_epsg] = obj["properties"].pop(eo_epsg)
                else:
                    obj["properties"][proj_code] = (
                        f"EPSG:{obj['properties'].pop(eo_epsg)}"
                    )
                    if not projection.ProjectionExtensionHooks().has_extension(obj):
                        obj["stac_extensions"].append(
                            projection.ProjectionExtension.get_schema_uri()
                        )

                if not any(prop.startswith(PREFIX) for prop in obj["properties"]):
                    obj["stac_extensions"].remove(eo.EOExtension.get_schema_uri())

        if version < "1.0.0-beta.1" and info.object_type == pystac.STACObjectType.ITEM:
            # gsd moved from eo to common metadata
            if "eo:gsd" in obj["properties"]:
                obj["properties"]["gsd"] = obj["properties"]["eo:gsd"]
                del obj["properties"]["eo:gsd"]

            # The way EObands were declared in assets changed.
            # In 1.0.0-beta.1 they are inlined into assets as
            # opposed to having indices back into a property-level array.
            if "eo:bands" in obj["properties"]:
                eo_bands = obj["properties"]["eo:bands"]
                for asset in obj["assets"].values():
                    if "eo:bands" in asset:
                        new_eo_bands: list[dict[str, Any]] = []
                        for band_index in asset["eo:bands"]:
                            new_eo_bands.append(eo_bands[band_index])
                        asset["eo:bands"] = new_eo_bands

        # Bands moved to common metadata
        # The migration must apply to assets as well
        if version < "2.0.0":
            # if "eo:bands" in obj.get("properties", {}):
            if "properties" in obj:
                self._migrate_obj_with_bands(obj["properties"])
                if "assets" in obj.keys():
                    for asset in obj["assets"].values():
                        self._migrate_obj_with_bands(asset)

        super().migrate(obj, version, info)


for uri in SCHEMA_URIS:
    try:
        pystac.EXTENSION_HOOKS.remove_extension_hooks(uri)
    except KeyError:
        pass
pystac.EXTENSION_HOOKS.add_extension_hooks(EOExtensionHooks())

pystac.extensions.eo.EOExtension = EOExtension

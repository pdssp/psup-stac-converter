import datetime as dt
from typing import Literal, Optional

import pandas as pd
from geojson_pydantic import Feature
from pydantic import BaseModel, field_serializer, field_validator


class CubedataDimensionBase(BaseModel):
    """The properties of the Dimension object from the Cubedata STAC extensions

    The model currently fits the extension version pystac is using.

    The description field uses CommonMark's syntax: https://commonmark.org/
    """

    type: Optional[str]
    description: Optional[str] = None
    axis: Optional[str]
    extent: Optional[list[str | int | float | None]]
    values: Optional[list[str | int | float | None]]
    step: Optional[int | float | str | float | None]
    reference_system: Optional[str | int]
    unit: Optional[str] = None

    @field_serializer("extent", "values", mode="plain")
    def ser_number(
        self, value: list[str | int | float | None]
    ) -> list[str | int | float | None]:
        return [element if pd.notnull(element) else None for element in value]


class CubedataVariable(BaseModel):
    """A *Variable Object* defines a variable (or a multi-dimensional array).
    The variable may have dimensions, which are described
    by `CubedataDimensionBase`-derived objects.

    **type**: The Variable `type` indicates whether what kind of variable is being described. It has two allowed values:

    1. `data`: a variable indicating some measured value, for example "precipitation", "temperature", etc.
    2. `auxiliary`: a variable that contains coordinate data, but isn't a dimension in `cube:dimensions`.
      For example, the values of the datacube might be provided in the projected coordinate reference system, but
      the datacube could have a variable `lon` with dimensions `(y, x)`, giving the longitude at each point.

    See the [CF Conventions](http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#terminology)
    for more on auxiliary coordinates.

    - dimensions: list[str] - **REQUIRED.** The dimensions of the variable. This should refer to keys in the ``cube:dimensions`` object or be an empty list if the variable has no dimensions.
    - type: Literal["data", "auxiliary"] - **REQUIRED.** Type of the variable, either `data` or `auxiliary`.
    - description: Optional[str] - Detailed multi-line description to explain the variable. [CommonMark 0.29](http://commonmark.org/) syntax MAY be used for rich text representation.
    - extent: Optional[list[str | int | float | None]] - If the variable consists of [ordinal](https://en.wikipedia.org/wiki/Level_of_measurement#Ordinal_scale) values, the extent (lower and upper bounds) of the values as two-element array. Use `null` for open intervals.
    - values: Optional[list[str | int | float]] - An (ordered) list of all values, especially useful for [nominal](https://en.wikipedia.org/wiki/Level_of_measurement#Nominal_level) values.
    - unit: Optional[str] - The unit of measurement for the data, preferably compliant to [UDUNITS-2](https://ncics.org/portfolio/other-resources/udunits2/) units (singular).

    """

    dimensions: list[str]
    type: Literal["data", "auxiliary"]
    description: Optional[str] = None
    extent: Optional[list[str | int | float | None]] = None
    values: Optional[list[str | int | float]] = None
    unit: Optional[str] = None

    @field_serializer("extent", mode="plain")
    def ser_number(
        self, value: list[str | int | float | None]
    ) -> list[str | int | float | None]:
        return [element if pd.notnull(element) else None for element in value]


class HorizontalSpatialRasterDimension(CubedataDimensionBase):
    """A spatial raster dimension in one of the horizontal (x or y) directions.

    - type: str = "spatial" — **REQUIRED.** Type of the dimension, always `spatial`.
    - axis: Literal["x", "y"] — **REQUIRED.** Axis of the spatial raster dimension (`x`, `y`).
    - extent: list[int | float] — **REQUIRED.** Extent (lower and upper bounds) of the dimension as two-element array. Open intervals with `null` are not allowed.
    - values: list[int | float] — Optionally, an ordered list of all values.
    - step: int | float | None — The space between the values. Use `null` for irregularly
    spaced steps.
    - reference_system: str | int — The spatial reference system for the data,
    specified as [numerical EPSG code](http://www.epsg-registry.org/),
      [WKT2 (ISO 19162) string](http://docs.opengeospatial.org/is/18-010r7/18-010r7.html)
      or [PROJJSON object](https://proj.org/specifications/projjson.html). Defaults to EPSG code 4326.
    """

    type: str = "spatial"
    axis: Literal["x", "y"]
    extent: list[int | float]
    values: Optional[list[int | float]] = None
    step: Optional[int | float | None] = None
    reference_system: Optional[str | int] = None


class VerticalSpatialRasterDimension(CubedataDimensionBase):
    """A spatial dimension in vertical (z) direction.

    A Vertical Spatial Dimension Object MUST specify an `extent` or `values`. It MAY specify both.

    - type: str = "spatial" - **REQUIRED.** Type of the dimension, always `spatial`.
    - axis: str = "z" - **REQUIRED.** Axis of the spatial dimension, always `z`.
    - extent: Optional[list[int | float]] - If the dimension consists of [ordinal](https://en.wikipedia.org/wiki/Level_of_measurement#Ordinal_scale) values, the extent (lower and upper bounds) of the values as two-element array. Use `null` for open intervals.
    - values: Optional[list[int | float | str]] - An ordered list of all values, especially useful for [nominal](https://en.wikipedia.org/wiki/Level_of_measurement#Nominal_level) values.
    - step: Optional[int | float | None] - If the dimension consists of [interval](https://en.wikipedia.org/wiki/Level_of_measurement#Interval_scale) values, the space between the values. Use `null` for irregularly spaced steps.
    - unit: Optional[str] - The unit of measurement for the data, preferably compliant to [UDUNITS-2](https://ncics.org/portfolio/other-resources/udunits2/) units (singular).
    - reference_system: Optional[str | int] - The spatial reference system for the data,
    specified as [numerical EPSG code](http://www.epsg-registry.org/),
      [WKT2 (ISO 19162) string](http://docs.opengeospatial.org/is/18-010r7/18-010r7.html)
      or [PROJJSON object](https://proj.org/specifications/projjson.html). Defaults to EPSG code 4326.
    """

    type: str = "spatial"
    axis: str = "z"
    extent: Optional[list[int | float]] = None
    values: Optional[list[int | float | str]] = None
    step: Optional[int | float | None] = None
    unit: Optional[str] = None
    reference_system: Optional[str | int] = None


class TemporalDimension(CubedataDimensionBase):
    """A temporal dimension based on the ISO 8601 standard. The temporal reference system for the data is expected to be ISO 8601 compliant
    (Gregorian calendar / UTC). Data not compliant with ISO 8601 can be represented as an *Additional Dimension Object* with `type` set to `temporal`.

    - type: str = "temporal" - **REQUIRED.** Type of the dimension, always `temporal`.
    - extent: list[dt.datetime] - **REQUIRED.** Extent (lower and upper bounds) of the dimension as two-element array. The dates and/or times must be strings compliant to [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601). `null` is allowed for open date ranges.
    - values: Optional[list[dt.datetime]] - If the dimension consists of an ordered list of specific values they can be listed here. The dates and/or times must be strings compliant to [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601).
    - step: Optional[dt.datetime | None] - The space between the temporal instances as [ISO 8601 duration](https://en.wikipedia.org/wiki/ISO_8601#Durations), e.g. `P1D`. Use `null` for irregularly spaced steps.
    """

    type: str = "temporal"
    extent: Optional[list[dt.datetime]] = None
    values: Optional[list[dt.datetime]] = None
    step: Optional[dt.datetime | None] = None


class SpatialVectorDimension(CubedataDimensionBase):
    """A vector dimension that defines a spatial dimension based on geometries.

    For a general explanation what a vector datacube and a vector dimension is,
    please read the article "[Vector Data Cubes](https://r-spatial.org/r/2022/09/12/vdc.html)".

    - type: str = "geometry" - **REQUIRED.** Type of the dimension, always `geometry`.
    - axes: list[Literal["x", "y", "z"]] = ["x", "y"] - Axes of the vector dimension as
    an ordered set of `x`, `y` and `z`. Defaults to `x` and `y`.
    - bbox: list[float | int] - **REQUIRED.** A single bounding box of the geometries
    as defined for [STAC Collections](https://github.com/radiantearth/stac-spec/blob/master/collection-spec/collection-spec.md#spatial-extent-object), but not nested.
    - values: Optional[list[str]] - Optionally, a representation of the geometries. This could be
    a list of WKT strings or other identifiers.
    - geometry_types: Optional[Feature] - A set of geometry types. If not present, mixed
    geometry types must be assumed.
    - reference_system: Optional[str | int] - The spatial reference system for the data,
    specified as [numerical EPSG code](http://www.epsg-registry.org/),
    [WKT2 (ISO 19162) string](http://docs.opengeospatial.org/is/18-010r7/18-010r7.html)
    or [PROJJSON object](https://proj.org/specifications/projjson.html). Defaults to EPSG code 4326.
    """

    type: str = "geometry"
    axes: list[Literal["x", "y", "z"]] = ["x", "y"]
    bbox: list[float | int]
    values: Optional[list[str]] = None
    geometry_types: Optional[Feature] = None
    reference_system: Optional[str | int] = None


class AdditionalDimension(CubedataDimensionBase):
    """An additional dimension that is not `spatial`, but may be `temporal`
    if the data is not compliant with ISO 8601 (see below).

    An Additional Dimension Object MUST specify an `extent` or `values`. It MAY specify both.

    Note on "Additional Dimension" with type `temporal`:
        You can distinguish the "Temporal Dimension" from an "Additional Dimension" by checking whether
        the extent exists and contains strings.
        So if the `type` equals `temporal` and `extent` is an array of strings/null, then you have a
        "Temporal Dimension",
        otherwise you have an "Additional Dimension".

    - type: str - **REQUIRED.** Custom type of the dimension, never `spatial` or `geometry`.
    - extent: Optional[list[int | float | None]] - If the dimension consists of
    [ordinal](https://en.wikipedia.org/wiki/Level_of_measurement#Ordinal_scale) values, the
    extent (lower and upper bounds) of the values as two-element array. Use `null` for open intervals.
    - values: Optional[list[int | float | str]] - An ordered list of all values, especially useful for
    [nominal](https://en.wikipedia.org/wiki/Level_of_measurement#Nominal_level) values.
    - step: Optional[int | float | str] - If the dimension consists of
    [interval](https://en.wikipedia.org/wiki/Level_of_measurement#Interval_scale) values,
    the space between the values. Use `null` for irregularly spaced steps.
    - unit: Optional[str] - The unit of measurement for the data, preferably compliant to
    [UDUNITS-2](https://ncics.org/portfolio/other-resources/udunits2/) units (singular).
    - reference_system: Optional[str] - The reference system for the data.

    """

    type: str
    extent: Optional[list[int | float | None]] = None
    values: Optional[list[int | float | str]] = None
    step: Optional[int | float | str] = None
    unit: Optional[str] = None
    reference_system: Optional[str] = None

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value in ["spatial", "geometry"]:
            raise ValueError(f"{value} is not allowed.")
        return value

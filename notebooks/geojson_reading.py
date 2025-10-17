import marimo

from psup_stac_converter.exceptions import FileExtensionError

__generated_with = "0.15.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import json
    from pathlib import Path
    from typing import Any

    import geopandas as gpd
    import marimo as mo
    from shapely.geometry import shape

    return Any, Path, gpd, json, mo, shape


@app.cell
def _(Path, mo):
    # As a preference, the raw data is stored in ./data/raw
    file_browser = mo.ui.file_browser(initial_path=Path("./data/raw"), multiple=False)
    return (file_browser,)


@app.cell
def _(file_browser, mo):
    mo.vstack([file_browser])
    return


@app.cell
def _(Any, Path, file_browser, json):
    def open_json_file(fpath: Path | None) -> dict[str, Any]:
        if fpath is None:
            raise ValueError("Select a valid JSON first!")

        if not fpath.suffix.endswith("json"):
            raise FileExtensionError(
                expected_extensions=["json", "geojson"], current_extension=fpath.suffix
            )

        with open(fpath, "r") as f:
            return json.load(f)

    geojson_file = open_json_file(file_browser.path(index=0))
    return (geojson_file,)


@app.cell
def _(geojson_file, gpd, mo, shape):
    n_features = len(geojson_file["features"])

    records = []
    for _feature in mo.status.progress_bar(
        collection=geojson_file["features"], total=n_features
    ):
        record = _feature["properties"]
        record["geometry"] = shape(_feature["geometry"])
        records.append(record)

    gpd.GeoDataFrame.from_records(records)
    return (n_features,)


@app.cell
def _(geojson_file, mo, n_features):
    for _feature in mo.status.progress_bar(
        collection=geojson_file["features"], total=n_features
    ):
        print(_feature["properties"])
    return


@app.cell
def _(geojson_file, mo, n_features, shape):
    for _feature in mo.status.progress_bar(
        collection=geojson_file["features"], total=n_features
    ):
        print(shape(_feature["geometry"]))
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

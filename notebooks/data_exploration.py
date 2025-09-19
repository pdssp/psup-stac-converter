import marimo

__generated_with = "0.15.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import json
    from pathlib import Path
    from typing import Any
    from io import StringIO
    import geopandas as gpd
    import pandas as pd
    from shapely.geometry import shape
    return Path, StringIO, gpd, json, mo, pd, shape


@app.cell
def _(Path, mo):
    file_browser = mo.ui.file_browser(
        initial_path=Path("./data/raw/catalogs/"), multiple=False
    )
    return (file_browser,)


@app.cell
def _(file_browser, mo):
    mo.vstack([mo.md(f"""**Current file:** {file_browser.path(index=0)}"""), file_browser])
    return


@app.cell
def _(Path, file_browser, gpd, json, shape):
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

        return gpd.GeoDataFrame.from_records(records)




    def open_gdf_file(fpath: Path | None) -> gpd.GeoDataFrame:
        if fpath is None:
            raise ValueError("Select a valid JSON first!")

        if not fpath.suffix.endswith("json"):
            raise ValueError("""Suffix must end with "json" (eg. .json, .geojson)""")


        if fpath.name.startswith("crocus_ls"):
            return open_problematic_df(filename=fpath) 


        return gpd.read_file(fpath)


    df = open_gdf_file(file_browser.path(index=0))
    df
    return (open_gdf_file,)


@app.cell
def _(Path, open_gdf_file):
    costard_craters_file = Path("/home/sboomi/PythonProjects/psup-stac-converter/data/raw/catalogs/costard_craters.json")

    costard_craters = open_gdf_file(costard_craters_file)
    costard_craters
    return (costard_craters,)


@app.cell
def _(StringIO, costard_craters, gpd, pd):
    from bs4 import BeautifulSoup


    class CostardCratersUtils:
        @staticmethod
        def extract_infos_from_description(description: str):
            """
            extracts information in the following order:
            fid, lat, lon, diam, type, lon_earth
            """
            soup = BeautifulSoup(description, "html.parser")
            buffer = StringIO(str(soup.find_all("table")[-1]))
            desc_df = pd.read_html(buffer)[0]
            desc_df.columns = ["name", "value"]
            return tuple(desc_df["value"].tolist())

        @staticmethod
        def transform(df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
            transformed_df = df.copy()
            (
                transformed_df["fid"],
                transformed_df["lat"],
                transformed_df["lon"],
                transformed_df["diam"],
                transformed_df["type"],
                transformed_df["lon_earth"],
            ) = zip(
                *transformed_df["description"].map(
                    CostardCratersUtils.extract_infos_from_description
                )
            )
            transformed_df = transformed_df.drop("description", axis=1)
            return transformed_df


    trans_costar_craters = CostardCratersUtils.transform(costard_craters)
    trans_costar_craters
    return


@app.cell
def _(mo):
    mo.md(r"""# Crocus et al""")
    return


@app.cell
def _(Path, open_gdf_file):
    crocus_ls_file = Path("/home/sboomi/PythonProjects/psup-stac-converter/data/raw/catalogs/crocus_ls150-310.json")

    crocus_ls = open_gdf_file(crocus_ls_file)
    crocus_ls
    return


@app.cell
def _(Path, open_gdf_file):
    detection_crater_file = Path("/home/sboomi/PythonProjects/psup-stac-converter/data/raw/catalogs/detections_crateres_benjamin_bultel_icarus.json")

    detection_crater = open_gdf_file(detection_crater_file)
    detection_crater
    return (detection_crater,)


@app.cell
def _(detection_crater, gpd):
    crater_type = {
        "Non visible": "non-visible",
        "1": "visible",
        "0": "unknown"
    }


    class DetectionCraterUtils:
        @staticmethod
        def break_f6(f6: str):
            """
            extracts information in the following order:
            fid, lat, lon, diam, type, lon_earth
            """
            return sorted(f6.split(","))

        @staticmethod
        def clean_crater_qual(crater_qual_name: str | None):
            if crater_qual_name is None:
                return "unknown"
        
            return crater_type[crater_qual_name]

        @staticmethod
        def transform(df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
            transformed_df = df.copy()

            transformed_df.columns = [col.lower() for col in transformed_df.columns]
            transformed_df = transformed_df.rename(columns={"diameter__": "diameter"})
            transformed_df["f6"] = transformed_df["f6"].apply(DetectionCraterUtils.break_f6)
            transformed_df["ejecta"] = transformed_df["ejecta"].apply(DetectionCraterUtils.clean_crater_qual)
            transformed_df["wall"] = transformed_df["wall"].apply(DetectionCraterUtils.clean_crater_qual)
            transformed_df["floor"] = transformed_df["floor"].astype(int).astype(str).apply(DetectionCraterUtils.clean_crater_qual)
            transformed_df["central_pe"] = transformed_df["central_pe"].apply(DetectionCraterUtils.clean_crater_qual)
            return transformed_df


    trans_detection_craters = DetectionCraterUtils.transform(detection_crater)
    trans_detection_craters
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

import marimo

__generated_with = "0.15.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import json
    from pathlib import Path
    from typing import Literal
    from io import StringIO
    import geopandas as gpd
    import pandas as pd
    from shapely.geometry import shape
    import altair as alt
    import httpx

    return Literal, Path, StringIO, alt, gpd, httpx, json, mo, pd, shape


@app.cell
def _(mo):
    mo.md(r"""# PSUP data""")
    return


@app.cell
def _(Path, pd):
    def sizeof_fmt(num: int, suffix: str = "B") -> str:
        for unit in ["", "Ki", "Mi", "Gi"]:
            if abs(num) < 1024.0:
                return f"{num:3.1f} {unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f} Ei{suffix}"

    psup_refs = pd.read_csv("./data/raw/psup_refs.csv")
    psup_refs = psup_refs.sort_values(by=["total_size", "rel_path"], ascending=False)
    psup_refs["h_total_size"] = psup_refs["total_size"].apply(sizeof_fmt)
    psup_refs["extension"] = psup_refs["rel_path"].apply(
        lambda p: Path(p).suffix.lstrip(".")
    )
    psup_refs["root"] = psup_refs["rel_path"].apply(lambda p: p.split("/")[0])
    # psup_refs = psup_refs.drop_duplicates(subset=['rel_path'])
    psup_refs
    return (psup_refs,)


@app.cell
def _(alt, mo, psup_refs):
    lfchart = mo.ui.altair_chart(
        alt.Chart(psup_refs[psup_refs["h_total_size"].str.endswith("GiB")])
        .mark_bar()
        .encode(
            alt.X("total_size:Q", bin=True),
            alt.Y("count()", scale=alt.Scale(type="log")),
        )
        .properties(
            title=alt.Title(
                "Histogram of PSUP files' size", subtitle="For files >=1 GiB"
            )
        )
    )

    sfchart = mo.ui.altair_chart(
        alt.Chart(psup_refs[~psup_refs["h_total_size"].str.endswith("GiB")])
        .mark_bar()
        .encode(
            alt.X("total_size:Q", bin=True),
            alt.Y("count()", scale=alt.Scale(type="log")),
        )
        .properties(
            title=alt.Title(
                "Histogram of PSUP files' size", subtitle="For files < 1 GiB"
            )
        )
    )
    return lfchart, sfchart


@app.cell
def _(alt, mo, psup_refs):
    # Disable max row error
    alt.data_transformers.disable_max_rows()

    _chart = (
        alt.Chart(psup_refs)
        .mark_bar()
        .encode(
            alt.X("total_size:Q", bin=True),
            alt.Y("count()", scale=alt.Scale(type="log")),
        )
        .properties(
            title=alt.Title(
                "Histogram of PSUP files' size", subtitle="Accounted for all files"
            )
        )
    )

    psup_byte_chart = mo.ui.altair_chart(_chart)
    return (psup_byte_chart,)


@app.cell
def _(lfchart, mo, psup_byte_chart, sfchart):
    mo.vstack([psup_byte_chart, mo.hstack([lfchart, sfchart])])
    return


@app.cell
def _(pd, psup_refs):
    gby_files = psup_refs.groupby("extension")["total_size"]
    pd.DataFrame(
        {
            "total_size": gby_files.sum(),
            "file_count": gby_files.count(),
            "average_file_size": gby_files.mean().round(0),
        }
    ).sort_values("average_file_size", ascending=False)
    return


@app.cell
def _(mo, psup_refs):
    file_extension = mo.ui.dropdown.from_series(psup_refs["extension"])
    root_cat = mo.ui.dropdown.from_series(psup_refs["root"])
    return file_extension, root_cat


@app.cell
def _(file_extension, mo, root_cat):
    mo.hstack([file_extension, root_cat])
    return


@app.cell
def _(file_extension, pd, psup_refs, root_cat):
    def filter_refs(df: pd.DataFrame) -> pd.DataFrame:
        filtered_df = df.copy()

        if root_cat.value is not None:
            filtered_df = filtered_df[filtered_df["root"].str.contains(root_cat.value)]

        if file_extension.value is not None:
            filtered_df = filtered_df[
                filtered_df["extension"].str.contains(file_extension.value)
            ]

        return filtered_df

    filtered_psup_refs = filter_refs(psup_refs)
    filtered_psup_refs
    return (filtered_psup_refs,)


@app.cell
def _(Path, mo):
    dl_folder = Path("./data/raw/downloads")

    dl_browser = mo.ui.file_browser(
        initial_path=Path("./data/raw/downloads"), multiple=False
    )
    dl_browser
    return (dl_folder,)


@app.cell
def _(Path, dl_folder, httpx, mo, pd):
    def download_file(
        url: str,
        output_file: Path,
        total_size: int,
        error_on_exist: bool = True,
        chunk_size: int = 1024,
    ):
        if output_file.exists() and error_on_exist:
            raise FileExistsError(
                f"{output_file} already exists! To override, set `error_on_exist` to False."
            )

        # ...existing code...
        with (
            httpx.stream("GET", url) as r,
            open(output_file, "wb") as of,
            mo.status.progress_bar(
                total=(total_size // chunk_size)
                + (1 if total_size % chunk_size > 0 else 0),
                title=f"Downloading {output_file}",
                subtitle=f"File destination: {output_file}",
                show_eta=True,
                show_rate=True,
            ) as bar,
        ):
            for data in r.iter_bytes(chunk_size=chunk_size):
                of.write(data)
                bar.update()
        # ...existing code...

    def download_row_batch(df: pd.DataFrame):
        # Function on filtered dataframe
        for row in df.itertuples():
            output_file = dl_folder / Path(row.rel_path)
            output_file.parent.mkdir(exist_ok=True, parents=True)
            try:
                download_file(row.href, output_file, total_size=row.total_size)
            except FileExistsError:
                print(f"{output_file} already exists. Skipping.")

    button = mo.ui.run_button(label="Download!")
    button

    return button, download_row_batch


@app.cell
def _(button, download_row_batch, filtered_psup_refs, mo):
    mo.stop(not button.value, "Click 'Download!' to download your files!")

    download_row_batch(filtered_psup_refs)
    return


@app.cell
def _():
    return


@app.cell
def _(mo):
    mo.md(r"""# Mars features""")
    return


@app.cell
def _(Path, mo):
    file_browser = mo.ui.file_browser(
        initial_path=Path("./data/raw/catalogs/"), multiple=False
    )
    return (file_browser,)


@app.cell
def _(file_browser, mo):
    mo.vstack(
        [mo.md(f"""**Current file:** {file_browser.path(index=0)}"""), file_browser]
    )
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
    costard_craters_file = Path(
        "/home/sboomi/PythonProjects/psup-stac-converter/data/raw/catalogs/costard_craters.json"
    )

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
    crocus_ls_file = Path(
        "/home/sboomi/PythonProjects/psup-stac-converter/data/raw/catalogs/crocus_ls150-310.json"
    )

    crocus_ls = open_gdf_file(crocus_ls_file)
    crocus_ls
    return


@app.cell
def _(Path, open_gdf_file):
    detection_crater_file = Path(
        "/home/sboomi/PythonProjects/psup-stac-converter/data/raw/catalogs/detections_crateres_benjamin_bultel_icarus.json"
    )

    detection_crater = open_gdf_file(detection_crater_file)
    detection_crater
    return (detection_crater,)


@app.cell
def _(detection_crater, gpd):
    crater_type = {"Non visible": "non-visible", "1": "visible", "0": "unknown"}

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
            transformed_df["f6"] = transformed_df["f6"].apply(
                DetectionCraterUtils.break_f6
            )
            transformed_df["ejecta"] = transformed_df["ejecta"].apply(
                DetectionCraterUtils.clean_crater_qual
            )
            transformed_df["wall"] = transformed_df["wall"].apply(
                DetectionCraterUtils.clean_crater_qual
            )
            transformed_df["floor"] = (
                transformed_df["floor"]
                .astype(int)
                .astype(str)
                .apply(DetectionCraterUtils.clean_crater_qual)
            )
            transformed_df["central_pe"] = transformed_df["central_pe"].apply(
                DetectionCraterUtils.clean_crater_qual
            )
            return transformed_df

    trans_detection_craters = DetectionCraterUtils.transform(detection_crater)
    trans_detection_craters
    return


@app.cell
def _(mo):
    mo.md(r"""# MOLA data""")
    return


@app.cell
def _(dl_folder):
    mola_folder = dl_folder / "MOLA"
    list(mola_folder.iterdir())
    return (mola_folder,)


@app.cell
def _(Literal, Path, bidx, json, mola_folder, namespace):
    import rasterio
    from attr import asdict
    from rasterio.transform import from_gcps

    def infos_from_tif(
        tif_file: Path,
        verbose: bool = False,
        aspect: "Literal['meta', 'tags']" = "meta",
        meta_member: "Literal['subdatasets', 'stats', 'checksum']" | None = None,
        indent: int = 2,
    ):
        print(tif_file)
        with rasterio.open(tif_file) as src:
            info = dict(src.profile)
            info["shape"] = (info["height"], info["width"])
            info["bounds"] = src.bounds
            if src.crs:
                epsg = src.crs.to_epsg()
                if epsg:
                    info["crs"] = f"EPSG:{epsg}"
                else:
                    info["crs"] = src.crs.to_string()
            else:
                info["crs"] = None

            info["res"] = src.res
            info["colorinterp"] = [ci.name for ci in src.colorinterp]
            info["units"] = [units or None for units in src.units]
            info["descriptions"] = src.descriptions
            info["indexes"] = src.indexes
            info["mask_flags"] = [
                [flag.name for flag in flags] for flags in src.mask_flag_enums
            ]

            if src.crs:
                info["lnglat"] = src.lnglat()

            gcps, gcps_crs = src.gcps

            if gcps:
                info["gcps"] = {"points": [p.asdict() for p in gcps]}
                if gcps_crs:
                    epsg = gcps_crs.to_epsg()
                    if epsg:
                        info["gcps"]["crs"] = f"EPSG:{epsg}"
                    else:
                        info["gcps"]["crs"] = src.crs.to_string()
                else:
                    info["gcps"]["crs"] = None

                info["gcps"]["transform"] = from_gcps(gcps)

            if verbose:
                stats = [asdict(so) for so in src.stats()]
                info["stats"] = stats
                info["checksum"] = [src.checksum(i) for i in src.indexes]

            if aspect == "meta":
                if meta_member == "subdatasets":
                    for name in src.subdatasets:
                        print(name)
                elif meta_member == "stats":
                    st = src.statistics(bidx)
                    print("{st.min} {st.max} {st.mean} {st.std}".format(st=st))
                elif meta_member == "checksum":
                    print(str(src.checksum(bidx)))
                elif meta_member:
                    if isinstance(info[meta_member], (list, tuple)):
                        print(" ".join(map(str, info[meta_member])))
                    else:
                        print(info[meta_member])
                else:
                    print(json.dumps(info, sort_keys=True, indent=indent))

            elif aspect == "tags":
                print(json.dumps(src.tags(ns=namespace), indent=indent))

    for tif_file in mola_folder.glob("*tif"):
        infos_from_tif(tif_file, verbose=True)
    return


@app.cell
def _():
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

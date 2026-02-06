import marimo

__generated_with = "0.19.8"
app = marimo.App(width="medium")


@app.cell
def _():
    import json
    import numpy as np
    from io import StringIO
    from pathlib import Path
    from typing import Literal

    import altair as alt
    import geopandas as gpd
    import httpx
    import marimo as mo
    import pandas as pd
    from shapely.geometry import shape

    return Literal, Path, alt, gpd, httpx, json, mo, np, pd, shape


@app.cell
def _(mo):
    mo.md(r"""
    # PSUP data
    """)
    return


@app.cell
def _(Path, pd):
    def sizeof_fmt(num: int, suffix: str = "B") -> str:
        for unit in ["", "Ki", "Mi", "Gi", "Ti"]:
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
    psup_refs["category"] = psup_refs["rel_path"].apply(lambda p: p.split("/")[0])
    psup_refs["root"] = psup_refs["rel_path"].apply(lambda p: p.split("/")[1])
    # psup_refs = psup_refs.drop_duplicates(subset=['rel_path'])
    psup_refs
    return psup_refs, sizeof_fmt


@app.cell
def _(psup_refs, sizeof_fmt):
    psup_refs.groupby("root")["total_size"].sum().apply(sizeof_fmt)
    return


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
def _(filtered_psup_refs):
    sorted(filtered_psup_refs["file_name"].unique())
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Mars features
    """)
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
def _(costard_craters, gpd):
    from bs4 import BeautifulSoup
    from pydantic.alias_generators import to_snake

    class CostardCratersUtils:
        @staticmethod
        def extract_infos_from_description(description: str):
            """
            extracts information in the following order:
            fid, lat, lon, diam, type, lon_earth
            """
            soup = BeautifulSoup(description, "html.parser")
            nested_table = soup.find_all("table")[-1]
            attributes = []

            for tr in nested_table.find_all("tr"):
                td_name, td_value = tr.find_all("td")
                name = td_name.get_text().lower()
                value = td_value.get_text()
                if name in ["lat", "lon", "diam", "lon_earth"]:
                    value = float(value.replace(",", "."))
                else:
                    value = int(value)
                attributes.append(value)
            return tuple(attributes)

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
            transformed_df.columns = transformed_df.columns.map(to_snake)
            return transformed_df

    trans_costar_craters = CostardCratersUtils.transform(costard_craters)
    trans_costar_craters
    return (trans_costar_craters,)


@app.cell
def _(trans_costar_craters):
    trans_costar_craters["timestamp"].unique()
    return


@app.cell
def _(pd, trans_costar_craters):
    bins = pd.IntervalIndex.from_tuples(
        [(_lat, _lat + 10) for _lat in range(-90, 90, 10)]
    )

    trans_costar_craters["interval_lat"] = pd.cut(
        trans_costar_craters["lat"], bins=bins
    )

    trans_costar_craters[["interval_lat", "type"]].groupby(
        ["interval_lat", "type"]
    ).get_group
    return


@app.cell
def _(trans_costar_craters):
    trans_costar_craters.plot()
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Southern pole CO2 amount on the Crocus line

    $L_s \in [150, 310]$
    """)
    return


@app.cell
def _(Path, open_gdf_file):
    crocus_ls_file = Path(
        "/home/sboomi/PythonProjects/psup-stac-converter/data/raw/catalogs/crocus_ls150-310.json"
    )

    crocus_ls = open_gdf_file(crocus_ls_file)
    crocus_ls.columns = ["crocus_type", "solar_longitude", "title", "geometry"]
    crocus_ls
    return (crocus_ls,)


@app.cell
def _(crocus_ls):
    crocus_ls["solar_longitude"] == crocus_ls["title"]
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
def _(detection_crater, gpd, pd):
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
            if crater_qual_name is None or pd.isna(crater_qual_name):
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
def _(Path, open_gdf_file):
    lcp_flathaut_file = Path(
        "/home/sboomi/PythonProjects/psup-stac-converter/data/raw/catalogs/lcp_flahaut_et_al.json"
    )

    lcp_flathaut = open_gdf_file(lcp_flathaut_file)
    lcp_flathaut
    return (lcp_flathaut,)


@app.cell
def _(lcp_flathaut, pd):
    lcp_flathaut.other_dete.apply(
        lambda chem: chem.split(",") if pd.notnull(chem) else []
    )
    return


@app.cell
def _(Path, open_gdf_file):
    from shapely import Point

    # the type is always 1
    lcp_vmwalls_file = Path(
        "/home/sboomi/PythonProjects/psup-stac-converter/data/raw/catalogs/lcp_vmwalls.json"
    )

    lcp_vmwalls = open_gdf_file(lcp_vmwalls_file)
    lcp_vmwalls["geometry"] = lcp_vmwalls.apply(
        lambda row: Point(row["N2"], row["N1"], row["N3"]), axis=1
    )
    lcp_vmwalls = lcp_vmwalls.drop(["N1", "N2", "N3", "type"], axis=1)
    type(lcp_vmwalls)
    return


@app.cell
def _(mo):
    mo.md(r"""
    # MOLA data
    """)
    return


@app.cell
def _(dl_folder):
    mola_folder = dl_folder / "MOLA"
    list(mola_folder.iterdir())
    return (mola_folder,)


@app.cell
def _(Literal, Path, bidx, json, mo, mola_folder, namespace, rc):
    import rasterio
    from attr import asdict
    from rasterio.transform import from_gcps

    def infos_from_tif(
        tif_file: Path,
        verbose: bool = False,
        aspect: Literal["meta", "tags"] = "meta",
        meta_member: Literal["subdatasets", "stats", "checksum"] | None = None,
        indent: int = 2,
    ):
        md_text = f"""# {tif_file}"""
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
                    md_text += "\n## Subdatasets:"
                    for name in src.subdatasets:
                        md_text += f"\n - {name}"
                elif meta_member == "stats":
                    st = src.statistics(bidx)
                    md_text += "\n## Statistics:"
                    md_text += "{st.min} {st.max} {st.mean} {st.std}".format(st=st)
                elif meta_member == "checksum":
                    md_text += f"\n**Checksum:** {rc.checksum(bidx)}"
                elif meta_member:
                    if isinstance(info[meta_member], (list, tuple)):
                        md_text += "\n" + " ".join(map(str, info[meta_member]))
                    else:
                        md_text += "\n" + str(info[meta_member])
                else:
                    mo.json(json.dumps(info, sort_keys=True, indent=indent))

            elif aspect == "tags":
                mo.json(json.dumps(src.tags(ns=namespace), indent=indent))

            mo.md(md_text)

    for tif_file in mola_folder.glob("*tif"):
        infos_from_tif(tif_file, verbose=True)
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Fernando's photometry analysis

    The data is an archive.
    """)
    return


@app.cell
def _(np):
    import spectral.io.envi as envi
    import matplotlib.pyplot as plt

    img = envi.open(
        "/home/sboomi/Téléchargements/psup_photometry/fusion_chain_omega_inv.hdr",
        "/home/sboomi/Téléchargements/psup_photometry/fusion_chain_omega_inv",
    )
    cube = np.copy(img._memmap)

    print(cube.shape)
    cube[cube == 65535] = np.nan

    plt.imshow(cube[400, :, :])
    return


@app.cell
def _(np):
    import spectral.io.envi as envi
    import matplotlib.pyplot as plt

    img = envi.open(
        "/home/sboomi/Téléchargements/psup_photometry/GEO_fusion.hdr",
        "/home/sboomi/Téléchargements/psup_photometry/GEO_fusion",
    )
    cube = np.copy(img._memmap)

    print(cube.shape, np.min(cube), np.max(cube))
    cube[cube == 65535] = np.nan

    print(cube)
    plt.imshow(cube[1, :, :], aspect="auto")
    plt.colorbar()
    plt.show()
    return


@app.cell
def _(psup_refs):
    # OMEGA maps

    files = [
        "albedo_r1080_equ_map.fits",
        "ferric_bd530_equ_map.fits",
        "ferric_nnphs_equ_map.fits",
        "olivine_osp1_equ_map.fits",
        "olivine_osp2_equ_map.fits",
        "olivine_osp3_equ_map.fits",
        "pyroxene_bd2000_equ_map.fits",
        "albedo_filled.fits",
        "albedo_unfilled.fits",
        "emissivite_5.03mic_OMEGA0.fits",
    ]

    psup_refs[psup_refs["file_name"].isin(files)]
    return (files,)


@app.cell
def _(files, np):
    from astropy.io import fits

    for omegamap_file in files:
        _f = f"data/raw/downloads/omega/fits/{omegamap_file}"
        _hdul = fits.open(_f)
        print(_f)
        for k, v in _hdul[0].header.items():
            print(f"[{k}] {v}")
        print("Image data shape:", _hdul[0].data.shape)
        print("Image minmax", np.nanmin(_hdul[0].data), np.nanmax(_hdul[0].data))

        print("\n=================\n")
    return


@app.cell
def _():
    return


@app.cell
def _():
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

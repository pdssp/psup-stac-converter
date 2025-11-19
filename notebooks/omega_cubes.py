import marimo

__generated_with = "0.15.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from pathlib import Path
    import pandas as pd
    import numpy as np
    import httpx
    import re
    import datetime as dt
    import time
    import tempfile
    from pystac.extensions.datacube import Dimension, Variable
    import xarray as xr
    import scipy.io as sio
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    from shapely import box, to_geojson, bounds
    import json

    return (
        Path,
        Variable,
        bounds,
        box,
        dt,
        json,
        make_axes_locatable,
        mo,
        np,
        pd,
        plt,
        re,
        sio,
        to_geojson,
        xr,
    )


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

    # filter by omega
    psup_refs = psup_refs[psup_refs["category"].str.contains("omega")]
    psup_refs = psup_refs.drop("category", axis=1)
    psup_refs
    return (psup_refs,)


@app.cell
def _(Path, pd, psup_refs):
    # divide both in two frames
    def divide_by_channel(df: pd.DataFrame, name: str):
        df_next = df[df["root"].str.contains(name)].drop("root", axis=1)
        df_next["name"] = df_next["file_name"].apply(lambda x: Path(x).stem)
        df_next = df_next.set_index("name")
        if "sedkO1SmI" in df_next.index:
            df_next = df_next.drop("sedkO1SmI")
        return df_next

    data_cubes_refs = divide_by_channel(psup_refs, "cubes_L2")
    c_channel_refs = divide_by_channel(psup_refs, "cubes_L3")

    print("N° items in C channel:", c_channel_refs.index.nunique())
    print("N° items in data cubes:", data_cubes_refs.index.nunique())
    return c_channel_refs, data_cubes_refs


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# OMEGA_C_channel_Proj Dataset description""")
    return


@app.cell
def _(c_channel_refs):
    c_channel_refs.sort_values("name")
    return


@app.cell
def _(c_channel_refs):
    ex_ids = ["5964_3", "3644_4"]

    # read .sav file
    # Taking a light file
    c_channel_refs.loc[
        c_channel_refs.index.str.contains(ex_ids[0])
        & c_channel_refs["extension"].str.contains("sav"),
        :,
    ]
    return (ex_ids,)


@app.cell
def _(c_channel_refs, ex_ids):
    c_channel_refs.loc[ex_ids[0], "href"]
    return


@app.cell
def _(ex_ids, sio):
    # stored here
    example_sav = sio.readsav(f"./data/raw/downloads/cube_omega/{ex_ids[0]}.sav")
    example_sav
    return (example_sav,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## The idl .sav file structure

    * **carte[*,120,*] =** Reflectance of the surface at a given longitude, latitude and wavelength λ.The refectance is defined by the “reflectance factor” I(λ)/(F cos(i)) where i is the solar incidence angle with λ from 0.97 to 2.55 µm (second dimension of the cube with 120 wavelengths). The spectra are corrected for atmospheric and aerosol contributions according to the method described in Vincendon et al. (Icarus, 251, 2015). It therefore corresponds to albedo for a lambertian surface. The first dimension of the cube refers to the length of scan. It can be 16, 32, 64, or 128 pixels. It gives the first spatial dimension.
    * **carte_donnees** identifies 5 backplanes by the variable are added to the spectra:
        1. **carte_donnees[*,0,*] =** Altitude based on the MOLA topography (in m)
        2. **carte_donnees[*,1,*] =** Incidence (in degree) on the ellipsoid at a given longitude and latitude.
        3. **carte_donnees[*,2,*] =** Incidence wrt (in degree) of the local gravity at a given longitude and latitude.
        4. **carte_donnees[*,3,*] =** Effective dust opacity at a given longitude and latitude as τeff = τMER/cos i, where i is the solar incidence angle and τMER is the dust opacity measured by the Mars Exploration Rovers (MERs) during the same solar longitude and Martian year as the OMEGA observation (see Audouard et al. J. Geophys. Res. Planets, 119, 1969–1989 for more details).
        5. **Carte_donnees[*,4,*] =** The watericelin index value at a given longitude and latitude. This criterion, described in Langevin et al. (2007) is based on the 1.5 μm band depth. It can be used to detect icy frost presence at the surface and thick clouds in the atmosphere. Every OMEGA pixel with a watericelin value > 1.5% should be excluded.
        6. **Carte_donnees[*,5,*] =** The icecloud index at a given longitude and latitude. This criterion (reflectance at 3.4 μm divided by reflectance at 3.52 μm) is described in Langevin et al. (2007) to identify the presence of water ice clouds. Its values range from 0.5 to 1.0. The smallest values unambiguously indicate the presence of icy clouds. We usually exclude any OMEGA pixel with a value < 0.8.
    * **lati =** Planetocentric latitude (in degree). The values of the table correspond to each pixel of the reflectance cube.
    * **longi =** Eastward longitude (in degree). The values of the table correspond to each pixel of the reflectance cube.
    wave = 1-D table containing the wavelengths (in µm).
    * **solarlongi =** Areocentric longitude Ls.
    * **max_lat_proj =** Maximum latitude of the reflectance cube.
    * **min_lat_proj =** Minimum latitude of the reflectance cube.
    * **max_lon_proj =** Easternmost longitude of the reflectance cube.
    * **min_lon_proj =** Westernmost longitude of the reflectance cube.
    """
    )
    return


@app.cell
def _(example_sav):
    x_dim, n_wavelength, y_dim = example_sav["carte"].shape
    print(f"Image {x_dim} x {y_dim} px, {n_wavelength} wavelengths.")
    return (n_wavelength,)


@app.cell
def _(mo, n_wavelength):
    wl_slider = mo.ui.slider(
        start=0, stop=n_wavelength - 1, label="Wavelength number", value=0
    )
    wl_slider
    return (wl_slider,)


@app.cell
def _(example_sav, make_axes_locatable, plt, wl_slider):
    def display_c_chan_map(wl_number: int):
        fig, ax = plt.subplots(1, 1)

        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)

        img_display = ax.imshow(
            example_sav["carte"][:, wl_number, :],
            cmap="gray",
            vmin=0,
            vmax=1,
            extent=[
                example_sav["longi"][0, :].min(),
                example_sav["longi"][0, :].max(),
                example_sav["lati"][:, 0].min(),
                example_sav["lati"][:, 0].max(),
            ],
        )
        ax.set_title(f"Region at {wl_number}th wavelength")

        fig.colorbar(img_display, cax=cax, orientation="vertical")

    display_c_chan_map(wl_number=wl_slider.value)
    plt.show()
    return


@app.cell
def _(example_sav, np, plt):
    _, data_info_idxs, _ = example_sav["carte_donnees"].shape
    datainfo_values = [
        "altitude",
        "incidence_angle",
        "incidence_wrt_angle",
        "effective_dust_opacity",
        "water_ice_lin",
        "ice_cloud_idx",
    ]

    fig, ax = plt.subplots(2, data_info_idxs, figsize=(12, 12))

    for data_info_idx in range(data_info_idxs):
        if data_info_idx >= len(datainfo_values):
            data_text = "unspecified"
        else:
            data_text = datainfo_values[data_info_idx]
        ax[0, data_info_idx].imshow(
            example_sav["carte_donnees"][:, data_info_idx, :], cmap="gray"
        )
        ax[0, data_info_idx].set_title(data_text)

        _min_map = np.nanmin(example_sav["carte_donnees"][:, data_info_idx, :])
        _max_map = np.nanmax(example_sav["carte_donnees"][:, data_info_idx, :])
        normalized_map = (
            example_sav["carte_donnees"][:, data_info_idx, :] - _min_map
        ) / (_max_map - _min_map)
        ax[1, data_info_idx].hist(normalized_map.ravel() * 255, bins=range(256))

        print(
            f"[{data_text}] {np.mean(example_sav['carte_donnees'][:, data_info_idx, :])}"
        )

    plt.show()
    return


@app.cell
def _(box, example_sav, np):
    # Planetocentric boundaries in degrees
    min_lat, max_lat = (
        np.nanmin(example_sav["lati"]),
        np.nanmax(example_sav["lati"]),
    )
    min_lon, max_lon = (
        np.nanmin(example_sav["longi"]),
        np.nanmax(example_sav["longi"]),
    )

    # Ls
    solar_longitude = example_sav["solarlongi"]

    # extrema stats
    max_lat_proj, min_lat_proj, max_lon_proj, min_lon_proj = (
        example_sav["max_lat_proj"],
        example_sav["min_lat_proj"],
        example_sav["max_lon_proj"],
        example_sav["min_lon_proj"],
    )

    img_box = box(min_lon, min_lat, max_lon, max_lat)
    img_box_proj = box(min_lon_proj, min_lat_proj, max_lon_proj, max_lat_proj)
    print(img_box, img_box_proj)
    return


@app.cell
def _(ex_ids, xr):
    ex_nc_ds = xr.open_dataset(f"./data/raw/downloads/cube_omega/{ex_ids[0]}.nc")
    ex_nc_ds
    return (ex_nc_ds,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## The netCDF4 .nc file structure

    * **Dimensions:**
        * **wavelength =** Wavelength (in µm).
        * **latitude =** Planetocentric latitude (in deg).
        * **longitude =** Eastward longitude (in deg).
    * **3D cube (wavelength, latitude, longitude)**
        * **Reflectance =** “reflectance factor” I(λ)/(F cos(i)) where i is the solar incidence angle with λ from 0.97 to 2.55 µm (second dimension of the cube with 120 wavelengths). See above for detailed description.
    * **2D variables (latitude, longitude)**
        * **altitude =** Altitude (in m) at a given longitude and latitude (MOLA – ellipsoid as reference).
        *i**ncidence_g =** Incidence angle (in degree) with respect to the outward normal to the reference ellipsoid at a given longitude and latitude.
        * **incidence_n =** ncidence wrt (in degrees) of the local gravity at a given longitude and latitude.
        * **tau =** Effective dust opacity at a given longitude and latitude as τeff = τMER/cos i, where i is the solar incidence angle and τMER is the dust opacity measured by the Mars Exploration Rovers (MERs) during the same solar longitude and Martian year as the OMEGA observation (see Audouard et al. J. Geophys. Res. Planets, 119, 1969–1989 for more details).
        * **watericelin =** The watericelin index value at a given longitude and latitude. This criterion, described in Langevin et al. (2007) is based on the 1.5 μm band depth. It can be used to detect icy frost presence at the surface and thick clouds in the atmosphere. Every OMEGA pixel with a watericelin value > 1.5% should be excluded.
        * **icecloudindex =** The icecloud index value at a given longitude and latitude. This criterion (reflectance at 3.4 μm divided by reflectance at 3.52 μm) is described in Langevin et al. (2007) to identify the presence of water ice clouds. Its values range from 0.5 to 1.0. The smallest values unambiguously indicate the presence of icy clouds. We usually exclude any OMEGA pixel with a value < 0.8.
    * **Scalar variables**
        * **solar_longitude =** Mars-Sun angle, measured from the Northern Hemisphere spring equinox where Ls=0 at the time of measurement.
        * **data_quality =** Data quality id as defined in EAICD.
        * **start_time =** Time when acquisition starts.
        * **stop_time =** Time when acquisition stops.
    * **Global attributes:**
        * **_NCProperties =** "version=1|netcdflibversion=4.4.1.1|hdf5libversion=1.10.1"
        * **Conventions =** "CF-1.6"
        * **title =** "OMEGA observations acquired with the C channels - Orbit # [number] - Cube # [number]"
        * **:history =** "Created [creationdate]" ;
        * **institution =** "Institut d\'Astrophysique Spatiale, CNRS et Universite Paris-Sud 11"
        * **source =** "surface observation"
        * **reference =** the references listed herein below
        * **cube_number =** "[number]"
        * **orbit_number =** "[number]"
    """
    )
    return


@app.cell
def _():
    from psup_stac_converter.utils.models import (
        CubedataVariable,
        HorizontalSpatialRasterDimension,
        VerticalSpatialRasterDimension,
        TemporalDimension,
        SpatialVectorDimension,
        AdditionalDimension,
    )

    return (
        CubedataVariable,
        HorizontalSpatialRasterDimension,
        VerticalSpatialRasterDimension,
    )


@app.cell
def _(ex_nc_ds):
    print("[DIMS]\n", ex_nc_ds.dims)
    print("[DATA VARIABLES]", ex_nc_ds.data_vars)
    print("[COORDINATES]", ex_nc_ds.coords)
    print("[ATTRIBUTES]", ex_nc_ds.attrs)
    return


@app.cell
def _(ex_nc_ds):
    ex_nc_ds.sizes  # Z, Y and X
    return


@app.cell
def _(ex_nc_ds):
    for _k in ex_nc_ds.data_vars.keys():
        print(_k)
        print("------")
        # print(ex_nc_ds.data_vars[_k])
        print(ex_nc_ds.data_vars[_k].values)
        print(ex_nc_ds.data_vars[_k].attrs)
        print("======\n")
    return


@app.cell
def _(CubedataVariable, ex_nc_ds):
    l3_cube_variables = {}

    for _k in ex_nc_ds.data_vars.keys():
        _vars_attrs = ex_nc_ds.data_vars[_k].attrs
        if "valid_min" in _vars_attrs and "valid_max" in _vars_attrs:
            extent = [
                _vars_attrs["valid_min"].item(),
                _vars_attrs["valid_max"].item(),
            ]
            values = None
        else:
            extent = None
            # Should be a scalar
            values = [ex_nc_ds.data_vars[_k].values.item()]

        l3_cube_variables[_k] = CubedataVariable(
            description=_vars_attrs["long_name"],
            type="data",
            dimensions=["wavelength", "latitude", "longitude"],
            unit=_vars_attrs["units"],
            extent=extent,
            values=values,
        )
    return (l3_cube_variables,)


@app.cell
def _(ex_nc_ds):
    for _k in ex_nc_ds.coords.keys():
        print(_k)
        print("------")
        # print(ex_nc_ds.coords[_k])
        print(ex_nc_ds.coords[_k].data)
        print(ex_nc_ds.coords[_k].coords)
        print(ex_nc_ds.coords[_k].attrs)
        print("==========================")
    return


@app.cell
def _(
    CubedataVariable,
    HorizontalSpatialRasterDimension,
    VerticalSpatialRasterDimension,
    ex_nc_ds,
    l3_cube_variables,
    np,
):
    l3_cube_dimensions = {}

    def find_step_from_values(vals: np.ndarray) -> float | None:
        steps = vals[1:] - vals[:-1]
        unique_steps = np.unique(steps)
        if unique_steps.size > 1 or unique_steps.size == 0:
            return None
        return unique_steps.item()

    for _k in ex_nc_ds.coords:
        _k_attrs = ex_nc_ds.coords[_k].attrs
        if _k in ["longitude", "latitude"]:
            l3_cube_dimensions[_k] = HorizontalSpatialRasterDimension(
                axis=_k_attrs["axis"].lower(),
                extent=[
                    _k_attrs["valid_min"].item(),
                    _k_attrs["valid_max"].item(),
                ],
                unit=_k_attrs["units"],
                step=find_step_from_values(ex_nc_ds.coords[_k].values),
                description=_k_attrs["long_name"],
            )
            l3_cube_variables[_k] = CubedataVariable(
                dimensions=[_k_attrs["axis"].lower()],
                type="auxiliary",
                extent=[
                    _k_attrs["valid_min"].item(),
                    _k_attrs["valid_max"].item(),
                ],
                unit=_k_attrs["units"],
                step=find_step_from_values(ex_nc_ds.coords[_k].values),
                description=_k_attrs["long_name"],
            )
        elif _k == "wavelength":
            l3_cube_dimensions[_k] = VerticalSpatialRasterDimension(
                extent=[
                    _k_attrs["valid_min"].item(),
                    _k_attrs["valid_max"].item(),
                ],
                unit=_k_attrs["units"],
                step=find_step_from_values(ex_nc_ds.coords[_k].values),
                description=_k_attrs["long_name"],
            )
            l3_cube_variables[_k] = CubedataVariable(
                dimensions=[_k_attrs["axis"].lower()],
                type="auxiliary",
                extent=[
                    _k_attrs["valid_min"].item(),
                    _k_attrs["valid_max"].item(),
                ],
                unit=_k_attrs["units"],
                step=find_step_from_values(ex_nc_ds.coords[_k].values),
                description=_k_attrs["long_name"],
            )

    print(l3_cube_variables)
    return (find_step_from_values,)


@app.cell
def _(ex_nc_ds):
    ex_nc_ds.attrs
    return


@app.cell
def _(dt, ex_nc_ds, json, re):
    json.dumps(
        {
            "created": dt.datetime.strptime(
                re.match(
                    r"Created (\d{2}/\d{2}/\d{2})", ex_nc_ds.attrs["history"]
                ).group(1),
                "%d/%m/%y",
            )
        },
        indent=4,
        sort_keys=True,
        default=str,
    )
    return


@app.cell
def _():
    ex_txt = """
    FILENAME=cube5964_3.sav
    ORBIT NUMBER=5964
    CUBE NUMBER=3
    START_TIME                     = 2008-08-24T09:35:24.085
    STOP_TIME                      = 2008-08-24T09:55:27.080
    SOLAR LONGITUDE =      117.152
    EASTERNMOST_LONGITUDE          = 105.663
    WESTERNMOST_LONGITUDE          = 96.893
    MAXIMUM LATITUDE =      59.9688
    MINIMUM LATITUDE =      37.9375
    DATA_QUALITY_ID                = 5
    """
    return


@app.cell
def _(mo):
    mo.md(r"""# OMEGA_data_cubes Dataset description""")
    return


@app.cell
def _(data_cubes_refs):
    data_cubes_refs
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    This dataset contains all the OMEGA observations acquired with the C, L and VIS channels until April 2016, 11, after filtering. Filtering processes have been implemented to remove some instrumental artefacts and observational conditions. Each OMEGA record is available as a netCDF4.nc file and an idl.sav

    Both files contain the cubes of reflectance of the surface at a given longitude, latitude and wavelength λ. The surface reflectance is defined as I/F/cos(i) where:

    * channel C=[0.93-2.73 µm]; L=[2.55-5.10 µm]; Visible=[0.38-1.05 µm];
    * atmospheric attenuation is corrected (1-5 µm);
    * airborne dust scattering is corrected (0.4-2.5 µm and for 5 µm emissivity estimations);
    * thermal contribution is removed (> 3 µm); L channel data and VIS channel are co-registered with C channel when available.

    Please note that longitudes range from -180 to 180 degrees east.
    """
    )
    return


@app.cell
def _(sio):
    example_sav_l2 = sio.readsav(f"./data/raw/downloads/cube_omega/D195_2.sav")
    example_sav_l2
    return (example_sav_l2,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### The idl .sav file structure:

    *   **wvl** = Electromagnetic wavelength (in µm). The channels are ordered as follow: C,L,VIS.
    *   **lat** = Planetocentric latitude (in degree). Values of the table correspond to each pixel of the data cube.
    *   **lon** = Eastward longitude (in degree). Values of the table correspond to each pixel of the data cube, they range from -180 to +180 degrees.

    #### 3D cube

    *   **ldat\_j** = Reflectance of the surface at a given longitude, latitude and wavelength. The surface reflectance is defined as I/F/cos(i) for the three channels. Note that:
        *   atmospheric attenuation is corrected (1-5 µm);
        *   airborne dust scattering is corrected (0.4-2.5 µm and for 5 µm emissivity estimations);
        *   thermal contribution is removed (> 3 µm);
        *   channels are co-registered.

    #### 2D variables

    Some parameters are detailed in the OMEGA EAICD.

    *   **altitude** = Altitude (in m) at a given longitude and latitude (MOLA – ellipsoid as reference).
    *   **incidence\_g** = Incidence angle (in degree) with respect to the outward normal to the reference ellipsoid at a given longitude and latitude.
    *   **emergence\_g** = Emergence angle (in degree) with respect to the outward normal to the reference ellipsoid.
    *   **incidence\_l** = Incidence angle (in degree) with respect to the local normal.
    *   **watericelin** = The watericelin index value at a given longitude and latitude. This criterion, described in Langevin et al. (2007) is based on the 1.5 μm band depth. It can be used to detect icy frost presence at the surface and thick clouds in the atmosphere. Every OMEGA pixel with a watericelin value < 0.985 should be excluded.
    *   **icecloudindex** = The icecloud index value at a given longitude and latitude. This criterion (reflectance at 3.4 μm divided by reflectance at 3.52 μm) is described in Langevin et al. (2007) to identify the presence of water ice clouds. Its values range from 0.5 to 1.0. The smallest values unambiguously indicate the presence of icy clouds. We usually exclude any OMEGA pixel with a value < 0.8.
    *   **heure** = Martian hour at local true solar time LTST of the observation.
    *   **leslon0** = East longitude (in degree) of the pixel footprint corner point 0.
    *   **leslon1** = East longitude (in degree) of the pixel footprint corner point 1.
    *   **leslon2** = East longitude (in degree) of the pixel footprint corner point 2.
    *   **leslon3** = East longitude (in degree) of the pixel footprint corner point 3.
    *   **leslat0** = North latitude (in degree) of the pixel footprint corner point 0.
    *   **leslat1** = North latitude (in degree) of the pixel footprint corner point 1.
    *   **leslat2** = North latitude (in degree) of the pixel footprint corner point 2.
    *   **leslat3** = North latitude (in degree) of the pixel footprint corner point 3.
    *   **spacecraft\_distance** = Slant distance (in m) from the spacecraft to the pixel footprint center point.
    *   **therm** = Temperature (in K) at 5 µm at a given longitude and latitude.

    #### Scalar variables

    *   **solarlong** = Areocentric longitude Ls.
    *   **data\_quality** = Data quality ID as defined in EAICD.
    *   **pointing\_mode** = Image acquisition attitude control mode.
    *   **year** = Martian Year of the observation.
    *   **pres** = Mask that indicates working channels:
        *   pres\[0\] = 1 if C channel is OK,
        *   pres\[1\] = 1 if L channel is OK,
        *   pres\[2\] = 1 if VIS channel is OK.
    *   **tag\_ok** = Index to indicate that the target is Mars. If tag\_ok = 0 => target is not Mars. Otherwise target is Mars.
    *   **tag\_l** = Mask for the L channel; tag\_l = 0 means no L channel data.
    *   **tag\_c** = Mask for the C channel: tag\_c = 0 means no C channel data.

    **Note:** other parameters are present; please contact [F. Poulet](https://www.ias.u-psud.fr/pperso/fpoulet/) for additional information regarding to these parameters.
    """
    )
    return


@app.cell
def _(example_sav_l2):
    dc_dims = example_sav_l2["lat"].shape
    print(dc_dims)
    return


@app.cell
def _(bounds, box, example_sav_l2, json, np, to_geojson):
    def extract_l2_sav_info(sav_dataset: dict):
        orbit_cube_idx = "D195_2"
        orbit_number, cube_number = orbit_cube_idx.split("_")
        sav_info = {"orbit_number": orbit_number, cube_number: int(cube_number)}

        cube_dims = sav_dataset["lat"].shape
        em_wl_range = sav_dataset["wvl"].size
        bbox = box(
            xmin=sav_dataset["lon"][0, :].min(),
            xmax=sav_dataset["lon"][0, :].max(),
            ymin=sav_dataset["lat"][:, 0].min(),
            ymax=sav_dataset["lat"][:, 0].max(),
        )
        sav_info["dims"] = cube_dims
        sav_info["wavelength_n_values"] = em_wl_range
        sav_info["wavelength_range"] = [
            np.nanmin(sav_dataset["wvl"]).item(),
            np.nanmax(sav_dataset["wvl"]).item(),
        ]
        sav_info["footprint"] = json.loads(to_geojson(bbox))
        sav_info["bbox"] = bounds(bbox).tolist()
        # retrieve scalar data
        sav_info["solar_longitude"] = sav_dataset["solarlong"].item()
        sav_info["data_quality"] = sav_dataset["data_quality"].item()
        sav_info["pointing_mode"] = sav_dataset["pointing_mode"].decode().strip('"')
        sav_info["martian_year"] = sav_dataset["year"]
        sav_info["prop_working_channels"] = sav_dataset["pres"].tolist()
        sav_info["is_target_mars"] = bool(sav_dataset["tag_ok"] != 0)
        sav_info["is_l_channel_working"] = sav_dataset["tag_l"] != 0
        sav_info["is_c_channel_working"] = sav_dataset["tag_c"] != 0
        sav_info["martian_time"] = (
            f"""{sav_dataset["year"]}:{sav_dataset["solarlong"]}:{np.nanmin(sav_dataset["heure"])}"""
        )

        return sav_info

    for k, v in extract_l2_sav_info(example_sav_l2).items():
        print(k, v, type(v))
    return


@app.cell
def _(xr):
    # ex_nc_ds_l2 = xr.open_dataset("./data/raw/downloads/cube_omega/D195_2.nc")
    ex_nc_ds_l2 = xr.open_dataset("./data/raw/downloads/cube_omega/0228_3.nc")
    ex_nc_ds_l2
    return (ex_nc_ds_l2,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### The netCDF4 .nc file structure

    #### Dimensions:

    *   **wavelength** = Wavelength in µm. The channel’s wavelengths are ordered as follow: C,L,VIS.
    *   **pixel\_x** = abscissa of the pixel
    *   **pixel\_y** = ordinate of the pixel

    #### 3D cube (wavelength, pixel\_x, pixel\_y)

    *   **Reflectance** = Surface reflectance a given longitude, latitude and wavelength defined as I/F/cos(i) for the three channel. Note that:
        *   atmospheric attenuation is corrected (1-5 µm);
        *   airborne dust scattering is corrected (0.4-2.5 µm and for 5 µm emissivity estimations);
        *   thermal contribution is removed (> 3 µm);
        *   channels are co-registered.

    #### 2D variables (pixel\_x, pixel\_y)

    Some parameters are detailed in the OMEGA EAICD.

    *   **latitude** = Planetocentric latitude (in deg).
    *   **longitude** = Eastward longitude (in deg), ranges from -180 to 180 degrees.
    *   **altitude** = Altitude (in m) at a given longitude and latitude (MOLA – ellipsoid as reference).
    *   **incidence\_g** = Incidence angle (in degree) with respect to the outward normal to the reference ellipsoid at a given longitude and latitude.
    *   **emergence\_g** = Emergence angle (in degree) with respect to the outward normal to the reference ellipsoid.
    *   **incidence\_l** = Incidence angle (in degree) with respect to the local normal.
    *   **watericelin** = The watericelin index value at a given longitude and latitude. This criterion, described in Langevin et al. (2007) is based on the 1.5 μm band depth. It can be used to detect icy frost presence at the surface and thick clouds in the atmosphere. Every OMEGA pixel with a watericelin value < 0.985 should be excluded.
    *   **icecloudindex** = The icecloud index value at a given longitude and latitude. This criterion (reflectance at 3.4 μm divided by reflectance at 3.52 μm) is described in Langevin et al. (2007) to identify the presence of water ice clouds. Its values range from 0.5 to 1.0. The smallest values unambiguously indicate the presence of icy clouds. We usually exclude any OMEGA pixel with a value < 0.8.
    *   **hour\_at\_LTST** = Martian hour at local true solar time LTST of the observation.
    *   **leslon0** = East longitude (in degree) of the pixel footprint corner point 0.
    *   **leslon1** = East longitude (in degree) of the pixel footprint corner point 1.
    *   **leslon2** = East longitude (in degree) of the pixel footprint corner point 2.
    *   **leslon3** = East longitude (in degree) of the pixel footprint corner point 3.
    *   **leslat0** = North latitude (in degree) of the pixel footprint corner point 0.
    *   **leslat1** = North latitude (in degree) of the pixel footprint corner point 1.
    *   **leslat2** = North latitude (in degree) of the pixel footprint corner point 2.
    *   **leslat3** = North latitude (in degree) of the pixel footprint corner point 3.
    *   **spacecraft\_distance** = Slant distance (in m) from the spacecraft to the pixel footprint center point.
    *   **therm** = Temperature (in K) at 5 µm at a given longitude and latitude.

    #### Scalar variables

    *   **solar\_longitude** = Areocentric longitude Ls.
    *   **data\_quality** = Data quality ID as defined in EAICD.
    *   **pointing\_mode** = Image acquisition attitude control mode.
    *   **year** = Martian Year of the observation.
    *   **pres** = Mask that indicates working channels.
        *   pres\[0\] = 1 if C channel is OK,
        *   pres\[1\] = 1 if L channel is OK,
        *   pres\[2\] = 1 if VIS channel is OK.
    *   **tag\_ok** = Index to indicate that the target is Mars. If tag\_ok = 0 => target is not Mars. Otherwise target is Mars.
    *   **tag\_l** = Mask for the L channel; tag\_l = 0 means no L channel data.
    *   **tag\_c** = Mask for the C channel: tag\_c = 0 means no C channel data.

    #### Global attributes:

    *   **\_NCProperties** = "version=1|netcdflibversion=4.4.1.1|hdf5libversion=1.10.1"
    *   **Conventions** = "CF-1.6"
    *   **title** = "OMEGA observations acquired with the C, L and VIS channels - Orbit # \[number\] - Cube # \[number\]"
    *   **:history** = "Created \[creationdate\]" ;
    *   **institution** = "Institut d\\'Astrophysique Spatiale, CNRS et Universite Paris-Sud 11"
    *   **source** = "surface observation"
    *   **reference** = The references listed herein-below.
    *   **cube\_number** = "\[number\]"
    *   **orbit\_number** = "\[number\]"
    """
    )
    return


@app.cell
def _(ex_nc_ds_l2):
    print("[DIMS]\n", ex_nc_ds_l2.dims)
    print("[DATA VARIABLES]", ex_nc_ds_l2.data_vars)
    print("[COORDINATES]", ex_nc_ds_l2.coords)
    print("[ATTRIBUTES]", ex_nc_ds_l2.attrs)
    return


@app.cell
def _(ex_nc_ds_l2):
    ex_nc_ds_l2.dims
    return


@app.cell
def _(ex_nc_ds_l2):
    for _k in ex_nc_ds_l2.data_vars.keys():
        print(_k)
        print("------")
        # print(ex_nc_ds_l2.data_vars[_k])
        print(ex_nc_ds_l2.data_vars[_k].values)
        print(ex_nc_ds_l2.data_vars[_k].attrs)
        print("======")
    return


@app.cell
def _(CubedataVariable, ex_nc_ds_l2):
    from pydantic import ValidationError

    l2_cube_variables = {}

    for _k in ex_nc_ds_l2.data_vars.keys():
        _vars_attrs = ex_nc_ds_l2.data_vars[_k].attrs
        if "valid_min" in _vars_attrs and "valid_max" in _vars_attrs:
            extent_l2 = [
                _vars_attrs["valid_min"].item(),
                _vars_attrs["valid_max"].item(),
            ]
            values_l2 = None
        else:
            extent_l2 = None
            # Should be a scalar
            values_l2 = [ex_nc_ds_l2.data_vars[_k].values.item()]

        l2_cube_variables[_k] = CubedataVariable(
            description=_vars_attrs["long_name"],
            type="data",
            dimensions=["wavelength", "pixel_y", "pixel_x"],
            unit=_vars_attrs["units"],
            extent=extent_l2,
            values=values_l2,
        )
    return (l2_cube_variables,)


@app.cell
def _(ex_nc_ds_l2):
    for _k in ex_nc_ds_l2.coords.keys():
        print(_k)
        print("------")
        # print(ex_nc_ds_l2.coords[_k])
        print(ex_nc_ds_l2.coords[_k].values)
        print(ex_nc_ds_l2.coords[_k].coords)
        print(ex_nc_ds_l2.coords[_k].attrs)
        print("==========================")
    return


@app.cell
def _(
    CubedataVariable,
    HorizontalSpatialRasterDimension,
    Variable,
    VerticalSpatialRasterDimension,
    ex_nc_ds,
    ex_nc_ds_l2,
    find_step_from_values,
    json,
    l2_cube_variables,
    l3_cube_variables,
):
    l2_cube_dimensions = {}

    for _k in ex_nc_ds_l2.coords.keys():
        _k_attrs = ex_nc_ds_l2.coords[_k].attrs
        if _k in ["pixel_x", "pixel_y"]:
            l2_cube_dimensions[_k] = HorizontalSpatialRasterDimension(
                axis=_k_attrs["axis"].lower(),
                extent=[
                    _k_attrs["valid_min"].item(),
                    _k_attrs["valid_max"].item(),
                ],
                unit=_k_attrs["units"],
                step=find_step_from_values(ex_nc_ds_l2.coords[_k].values),
                description=_k_attrs["long_name"],
            )
            l3_cube_variables[_k] = CubedataVariable(
                dimensions=[_k_attrs["axis"].lower()],
                type="auxiliary",
                extent=[
                    _k_attrs["valid_min"].item(),
                    _k_attrs["valid_max"].item(),
                ],
                unit=_k_attrs["units"],
                step=find_step_from_values(ex_nc_ds_l2.coords[_k].values),
                description=_k_attrs["long_name"],
            )
        elif _k == "wavelength":
            l2_cube_dimensions[_k] = VerticalSpatialRasterDimension(
                extent=[
                    _k_attrs["valid_min"].item(),
                    _k_attrs["valid_max"].item(),
                ],
                unit=_k_attrs["units"],
                step=find_step_from_values(ex_nc_ds.coords[_k].values),
                description=_k_attrs["long_name"],
            )
            l3_cube_variables[_k] = CubedataVariable(
                dimensions=[_k_attrs["axis"].lower()],
                type="auxiliary",
                extent=[
                    _k_attrs["valid_min"].item(),
                    _k_attrs["valid_max"].item(),
                ],
                unit=_k_attrs["units"],
                step=find_step_from_values(ex_nc_ds_l2.coords[_k].values),
                description=_k_attrs["long_name"],
            )

    for _k, _v in l2_cube_variables.items():
        json.dumps({_k: Variable(properties={_k: _v.model_dump(exclude_none=True)})})
    return


@app.cell
def _(ex_nc_ds_l2):
    ex_nc_ds_l2.attrs
    return


@app.cell
def _(dt, ex_nc_ds_l2, re):
    dt.datetime.strptime(
        re.match(r"Created (\d{2}/\d{2}/\d{2})", ex_nc_ds_l2.attrs["history"]).group(1),
        "%d/%m/%y",
    ).isoformat()
    return


@app.cell
def _(ex_nc_ds_l2):
    ex_nc_ds_l2.isel(wavelength=100)
    return


@app.cell
def _(ex_nc_ds_l2, plt):
    ex_nc_ds_l2.Reflectance[100].plot(cmap=plt.cm.get_cmap("viridis"))
    plt.title("Reflectance map based on 100th wavelength")
    return


@app.cell
def _(Path, ex_nc_ds_l2, mo, np, plt):
    # import numpy as np
    from PIL import Image
    from typing import Literal
    from tempfile import TemporaryDirectory

    def convert_arr_to_thumbnail(
        data: np.ndarray,
        resize_dims: tuple[int, int],
        mode: Literal["L", "RGB", "RGBA"] = "L",
        cmap: str | None = None,
    ) -> Image.Image:
        """
        Converts a 2D or 3D NumPy array into a resized PNG-style image.
        Applies a matplotlib colormap if provided.
        """

        # Normalizes data between 0 and 1
        result = np.asarray(data, dtype=float)

        result_min = np.nanmin(result[~np.isneginf(result)])
        result_max = np.nanmax(result[~np.isposinf(result)])
        if np.isnan(result_max) or np.isnan(result_min):
            raise ValueError(
                f"Seems like the array's size is NaN (min={result_min}, max={result_max})"
            )

        result = (result - result_min) / (result_max - result_min + 1e-8)
        # occult the NaNs and infs
        # result = np.nan_to_num(result, nan=0., posinf=255., neginf=0.)

        if cmap is not None:
            cm = plt.get_cmap(cmap)
            result = cm(result)[..., :4]  # includes alpha
            result = (result * 255).astype(np.uint8)
            if mode == "RGB":
                result = result[..., :3]
        else:
            result = (result * 255).astype(np.uint8)
            if mode in ["RGB", "RGBA"]:
                result = np.stack([result] * (3 if mode == "RGB" else 4), axis=-1)

        img = Image.fromarray(result, mode=mode)
        img = img.resize(resize_dims, Image.Resampling.LANCZOS)

        return img

    tempdir = TemporaryDirectory()
    resized_img = convert_arr_to_thumbnail(
        getattr(ex_nc_ds_l2.Reflectance, "mean")("wavelength").values,
        (256, 256),
        mode="RGBA",
        cmap="viridis",
    )

    resized_img.save(Path(tempdir.name) / "test.png")
    mo.image(src=Path(tempdir.name) / "test.png")
    return


@app.cell
def _(ex_nc_ds_l2, plt):
    plt.imshow(getattr(ex_nc_ds_l2.Reflectance, "mean")("wavelength").values)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

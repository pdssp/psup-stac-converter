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
    import time
    import tempfile
    import xarray as xr
    import scipy.io as sio
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    from shapely import box

    return Path, box, make_axes_locatable, mo, np, pd, plt, sio, xr


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
def _(xr):
    ex_nc_ds = xr.open_dataset("./data/raw/downloads/cube_omega/3644_4.nc")
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
def _(ex_nc_ds):
    for _k in ex_nc_ds.keys():
        print(_k)

    print(ex_nc_ds["solar_longitude"].encoding)
    print(ex_nc_ds.encoding)
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
def _():
    return


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
def _():
    return


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
def _():
    return


if __name__ == "__main__":
    app.run()

import marimo

__generated_with = "0.15.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from tempfile import TemporaryDirectory
    from psup_stac_converter.utils.io import PsupIoHandler
    from pathlib import Path
    import yaml
    from psup_stac_converter.omega.c_channel_proj import OmegaCChannelProj
    from psup_stac_converter.omega.data_cubes import OmegaDataCubes
    from psup_stac_converter.omega._base import OmegaDataReader
    import xarray as xr
    import matplotlib.pyplot as plt
    import numpy as np

    return (
        OmegaCChannelProj,
        OmegaDataCubes,
        OmegaDataReader,
        Path,
        PsupIoHandler,
        mo,
        np,
        plt,
        xr,
        yaml,
    )


@app.cell
def _(mo):
    config_file = mo.ui.file(kind="area", filetypes=[".yaml", ".yml"])
    config_file
    return (config_file,)


@app.cell
def _(
    OmegaCChannelProj,
    OmegaDataCubes,
    Path,
    PsupIoHandler,
    config_file,
    yaml,
):
    with open(config_file.name() or "converter-params.yml", "r") as file:
        config = yaml.safe_load(file)

    psup_data_inventory_file = Path(
        config["settings"]["psup_inventory_file"]
    ).expanduser()
    raw_data_folder = Path(config["settings"]["raw_data_path"]).expanduser()
    psup_archive = PsupIoHandler(
        psup_data_inventory_file, output_folder=raw_data_folder
    )

    omega_data_cubes_builder = OmegaDataCubes(psup_archive)
    omega_c_channel_builder = OmegaCChannelProj(psup_archive)

    omega_c_channel_builder, omega_data_cubes_builder
    return omega_c_channel_builder, omega_data_cubes_builder


@app.cell
def _(OmegaDataReader, mo, omega_c_channel_builder, omega_data_cubes_builder):
    # UI elements
    omega_c_chan_idx_slider = mo.ui.slider(
        start=0,
        stop=omega_c_channel_builder.n_elements - 1,
        label="Element index",
        value=0,
    )
    omega_data_cube_idx_slider = mo.ui.slider(
        start=0,
        stop=omega_data_cubes_builder.n_elements - 1,
        label="Element index",
        value=0,
    )
    dl_button = mo.ui.run_button(label="Download dataset!")
    dl_button_c_chan = mo.ui.run_button(label="Download dataset (C channel L3)!")
    dl_button_common = mo.ui.run_button(label="Download dataset for both")

    def val_to_omega_idx(v: int, data_reader: OmegaDataReader) -> str:
        return data_reader.omega_data_ids[v]

    def expose_orbit_cube_info(idx: int, data_reader: OmegaDataReader) -> str:
        orbit_cube_idx = val_to_omega_idx(idx, data_reader)
        info_omega = data_reader.find_info_by_orbit_cube(orbit_cube_idx)
        fmt = f"[{orbit_cube_idx}]\n\n"
        for row in info_omega.itertuples():
            fmt += f"{row.file_name} ({row.h_total_size})" + "\n\n"

        return fmt

    return (
        dl_button,
        dl_button_c_chan,
        dl_button_common,
        expose_orbit_cube_info,
        omega_c_chan_idx_slider,
        omega_data_cube_idx_slider,
        val_to_omega_idx,
    )


@app.cell
def _(np, xr):
    # functions for processes

    def select_rgb_img(ds: xr.Dataset) -> xr.Dataset:
        channels = [
            ds.wavelength.size // 2 - ds.wavelength.size // 3,
            ds.wavelength.size // 2,
            ds.wavelength.size // 2 + ds.wavelength.size // 3,
        ]
        return ds.isel(wavelength=channels)

    def select_for_data_cubes(
        ds: xr.Dataset,
    ) -> tuple[xr.Dataset, xr.Dataset, xr.Dataset]:
        """
        channel:
            C=[0.93-2.73 µm]
            L=[2.55-5.10 µm]
            Visible=[0.38-1.05 µm]
        atmospheric attenuation is corrected (1-5 µm);
        airborne dust scattering is corrected (0.4-2.5 µm and for 5 µm emissivity estimations);
        thermal contribution is removed (> 3 µm); L channel data and VIS channel are co-registered with C channel when
        available.

        """
        d_wl = ds.wavelength.values[1:] - ds.wavelength.values[:-1]
        c_break, l_break = np.where(d_wl < 0)[0]
        sel_c = select_rgb_img(ds.isel(wavelength=range(0, c_break + 1)))
        sel_l = select_rgb_img(ds.isel(wavelength=range(c_break, l_break + 1)))
        sel_vis = select_rgb_img(ds.isel(wavelength=range(l_break, ds.wavelength.size)))
        return (sel_vis, sel_c, sel_l)

    return select_for_data_cubes, select_rgb_img


@app.cell
def _(mo):
    mo.md(r"""# OMEGA C Channel Data""")
    return


@app.cell
def _(omega_c_channel_builder):
    omega_c_channel_builder.omega_data
    return


@app.cell
def _(
    dl_button_c_chan,
    expose_orbit_cube_info,
    mo,
    omega_c_chan_idx_slider,
    omega_c_channel_builder,
    val_to_omega_idx,
):
    mo.vstack(
        [
            mo.hstack(
                [
                    omega_c_chan_idx_slider,
                    mo.md(
                        expose_orbit_cube_info(
                            omega_c_chan_idx_slider.value, omega_c_channel_builder
                        )
                    ),
                ]
            ),
            mo.hstack(
                [
                    mo.md(
                        f"**{
                            val_to_omega_idx(
                                omega_c_chan_idx_slider.value,
                                omega_c_channel_builder,
                            )
                        }**"
                    ),
                    dl_button_c_chan,
                ]
            ),
        ]
    )
    return


@app.cell
def _(
    dl_button_c_chan,
    omega_c_chan_idx_slider,
    omega_c_channel_builder,
    val_to_omega_idx,
):
    omega_c_chan_ds = None
    if dl_button_c_chan.value:
        omega_c_chan_ds = omega_c_channel_builder.open_file(
            val_to_omega_idx(omega_c_chan_idx_slider.value, omega_c_channel_builder),
            file_extension="nc",
            on_disk=False,
        )
        print(omega_c_chan_ds)
    else:
        print("Press button to download dataset!")
    return (omega_c_chan_ds,)


@app.cell
def _(omega_c_chan_ds, plt, select_rgb_img):
    # Extract image
    if omega_c_chan_ds:
        image_omega_c_chan = select_rgb_img(omega_c_chan_ds)
        image_omega_c_chan.Reflectance.plot.imshow(rgb="wavelength")
    else:
        print("No dataset loaded. Press the download button first.")

    plt.show()
    return


@app.cell
def _(mo):
    mo.md(r"""# OMEGA Data cubes""")
    return


@app.cell
def _(omega_data_cubes_builder):
    omega_data_cubes_builder.omega_data
    return


@app.cell
def _(
    dl_button,
    expose_orbit_cube_info,
    mo,
    omega_data_cube_idx_slider,
    omega_data_cubes_builder,
    val_to_omega_idx,
):
    mo.vstack(
        [
            mo.hstack(
                [
                    omega_data_cube_idx_slider,
                    mo.md(
                        expose_orbit_cube_info(
                            omega_data_cube_idx_slider.value,
                            omega_data_cubes_builder,
                        )
                    ),
                ]
            ),
            mo.hstack(
                [
                    mo.md(
                        f"**{
                            val_to_omega_idx(
                                omega_data_cube_idx_slider.value,
                                omega_data_cubes_builder,
                            )
                        }**"
                    ),
                    dl_button,
                ]
            ),
        ]
    )
    return


@app.cell
def _(
    dl_button,
    omega_data_cube_idx_slider,
    omega_data_cubes_builder,
    val_to_omega_idx,
):
    omega_dc_ds = None
    if dl_button.value:
        omega_dc_ds = omega_data_cubes_builder.open_file(
            val_to_omega_idx(
                omega_data_cube_idx_slider.value, omega_data_cubes_builder
            ),
            file_extension="nc",
            on_disk=False,
        )
        print(omega_dc_ds)
    else:
        print("Press button to download dataset!")
    return (omega_dc_ds,)


@app.cell
def _(mo, omega_dc_ds):
    if omega_dc_ds:
        prop_working_channels = omega_dc_ds.pres.values.item().strip("[]").split()
        prop_working_channels = [float(el) == 1.0 for el in prop_working_channels]

        chan_l_unavail = omega_dc_ds.tag_l.item() == 0
        chan_c_unavail = omega_dc_ds.tag_c.item() == 0

        display_datacube_text = f"""
        **Areocentric solar longitude:** $L_s= {omega_dc_ds.solar_longitude.item()}$

        Data quality level: {omega_dc_ds.data_quality.item()}

        Pointing mode: {omega_dc_ds.pointing_mode.item()}

        {"The target is Mars" if omega_dc_ds.tag_ok.item() != 0 else ""}

        ------------
        * C channel is {"**OK**" if prop_working_channels[0] else "*KO*"} and the data is {"*unavailable*" if chan_c_unavail else "**available**"}
        * L channel is {"**OK**" if prop_working_channels[1] else "*KO*"} and the data is {"*unavailable*" if chan_l_unavail else "**available**"}
        * VIS channel is {"**OK**" if prop_working_channels[2] else "*KO*"}
        """
    else:
        display_datacube_text = "No dataset loaded. Press the download button first."

    mo.md(display_datacube_text)
    return


@app.cell
def _(omega_dc_ds, plt, select_for_data_cubes):
    # Extract image
    if omega_dc_ds:
        channel_names = ["VIS", "C", "L"]
        imgs_ds = select_for_data_cubes(omega_dc_ds)
        _fig, _ax = plt.subplots(1, 3, figsize=(12, 6))

        for i_img, img_ds in enumerate(imgs_ds):
            img_ds.Reflectance.plot.imshow(rgb="wavelength", ax=_ax[i_img])
            _ax[i_img].set_title(f"Channel {channel_names[i_img]}")
    else:
        print("No dataset loaded. Press the download button first.")

    plt.show()
    return


@app.cell
def _(np, omega_dc_ds):
    # Other plots

    # The watericelin index value at a given longitude and latitude. This criterion, described in Langevin et al. (2007) is based on the 1.5 μm band depth. It can be used to detect icy frost presence at the surface and thick clouds in the atmosphere. Every OMEGA pixel with a watericelin value < 0.985 should be excluded.
    omega_dc_ds.watericelin.where(omega_dc_ds.watericelin >= 0.985, np.nan).plot()
    return


@app.cell
def _(np, omega_dc_ds):
    # icecloudindex = The icecloud index value at a given longitude and latitude. This criterion (reflectance at 3.4 μm divided by reflectance at 3.52 μm) is described in Langevin et al. (2007) to identify the presence of water ice clouds. Its values range from 0.5 to 1.0. The smallest values unambiguously indicate the presence of icy clouds. We usually exclude any OMEGA pixel with a value < 0.8.

    omega_dc_ds.icecloudsindex.where(omega_dc_ds.icecloudsindex >= 0.8, np.nan).plot()
    return


@app.cell
def _(mo):
    mo.md(r"""# Comparison between L2 and L3 products""")
    return


@app.cell
def _(OmegaCChannelProj, OmegaDataCubes):
    def compare_txt_l2_l3(
        omega_idx: str,
        omega_c_channel_builder: OmegaCChannelProj,
        omega_data_cubes_builder: OmegaDataCubes,
    ):
        c_chan_info = omega_c_channel_builder.find_info_by_orbit_cube(omega_idx)
        ds_info = omega_data_cubes_builder.find_info_by_orbit_cube(omega_idx)
        fmt = "**[Datacube (L2)]**\n\n"

        for row in ds_info.itertuples():
            fmt += f"{row.file_name} ({row.h_total_size})" + "\n\n"

        fmt += "\n\n**[C Channel (L3)]**\n\n"
        for row in c_chan_info.itertuples():
            fmt += f"{row.file_name} ({row.h_total_size})" + "\n\n"

        return fmt

    return (compare_txt_l2_l3,)


@app.cell
def _(mo, omega_c_channel_builder, omega_data_cubes_builder):
    common_omega_idx = omega_c_channel_builder.omega_data_ids.intersection(
        omega_data_cubes_builder.omega_data_ids
    )
    common_omega_idx_slider = mo.ui.slider(
        start=0,
        stop=common_omega_idx.size - 1,
        label="Common indexes",
        value=0,
    )
    return common_omega_idx, common_omega_idx_slider


@app.cell
def _(
    common_omega_idx,
    common_omega_idx_slider,
    compare_txt_l2_l3,
    dl_button_common,
    mo,
    omega_c_channel_builder,
    omega_data_cubes_builder,
):
    mo.hstack(
        [
            mo.vstack(
                [
                    common_omega_idx_slider,
                    mo.md(f"**#{common_omega_idx[common_omega_idx_slider.value]}**"),
                    dl_button_common,
                ]
            ),
            mo.vstack(
                [
                    mo.md(
                        compare_txt_l2_l3(
                            common_omega_idx[common_omega_idx_slider.value],
                            omega_c_channel_builder,
                            omega_data_cubes_builder,
                        )
                    )
                ]
            ),
        ]
    )
    return


@app.cell
def _(
    common_omega_idx,
    common_omega_idx_slider,
    dl_button_common,
    omega_c_channel_builder,
    omega_data_cubes_builder,
):
    omega_ds = [None, None]
    if dl_button_common.value:
        omega_ds[0] = omega_data_cubes_builder.open_file(
            common_omega_idx[common_omega_idx_slider.value],
            file_extension="nc",
            on_disk=False,
        )

        omega_ds[1] = omega_c_channel_builder.open_file(
            common_omega_idx[common_omega_idx_slider.value],
            file_extension="nc",
            on_disk=False,
        )
    else:
        print("Press button to download dataset!")
    return (omega_ds,)


@app.cell
def _(
    common_omega_idx,
    common_omega_idx_slider,
    np,
    omega_ds,
    plt,
    select_rgb_img,
):
    # Extract image
    if omega_ds[0] and omega_ds[1]:
        img_omega = [None, None]
        fig, ax = plt.subplots(1, 2, figsize=(12, 6))

        d_wl = omega_ds[0].wavelength.values[1:] - omega_ds[0].wavelength.values[:-1]
        breakpoints = np.where(d_wl < 0)[0]
        img_omega[0] = select_rgb_img(
            omega_ds[0].isel(wavelength=range(0, breakpoints[0] + 1))
        )
        img_omega[0].Reflectance.plot.imshow(rgb="wavelength", ax=ax[0])

        ax[0].set_title("L2 data cube")

        img_omega[1] = select_rgb_img(omega_ds[1])
        img_omega[1].Reflectance.plot.imshow(rgb="wavelength", ax=ax[1])

        ax[1].set_title("L3 C Channel")

        fig.suptitle(
            f"RGB representation for cube #{common_omega_idx[common_omega_idx_slider.value]}"
        )
    else:
        print("No dataset loaded. Press the download button first.")

    plt.show()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

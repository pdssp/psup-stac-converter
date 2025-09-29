from pystac.extensions.eo import Band
from pystac.extensions.scientific import Publication


def _center_wavelength(min_wl: float, max_wl: float) -> float:
    return (min_wl + max_wl) / 2


def _fwhm(min_wl, max_wl) -> float:
    return max_wl - min_wl


publications = {
    "hyd_global_290615.json": Publication(
        citation="Carter, J., F. Poulet, J.‐P. Bibring, N. Mangold, and S. Murchie (2013), Hydrous minerals on Mars as seen by the CRISM and OMEGA imaging spectrometers: Updated global view, J. Geophys. Res. Planets, 118, 831–858",
        doi="doi: 10.1029/2012JE004145",
    ),
    "detections_crateres_benjamin_bultel_icarus.json": Publication(
        citation="B. Bultel, C. Quantin-Nataf, M. Andréani, H. Clénet, L. Lozac’h (2015), Deep alteration between Hellas and Isidis Basins, In Icarus Volume 260, 2015, Pages 141-160",
        doi="doi:10.1016/j.icarus.2015.06.037",
    ),
    "lcp_flahaut_et_al.json": Publication(
        citation="C. Quantin, J. Flahaut, H. Clenet, P. Allemand, P. Thomas (2012), Composition and structures of the subsurface in the vicinity of Valles Marineris as revealed by central uplifts of impact craters, Icarus, Volume 221, Issue 1, 2012, Pages 436-452",
        doi="doi:10.1016/j.icarus.2012.07.031",
    ),
    "lcp_vmwalls.json": Publication(
        citation="J. Flahaut, C. Quantin, H. Clenet, P. Allemand, J. F. Mustard, P. Thomas (2012), Pristine Noachian crust and key geologic transitions in the lower walls of Valles Marineris: Insights into early igneous processes on Mars, In Icarus, Volume 221, Issue 1, 2012, Pages 420-435",
        doi="doi:10.1016/j.icarus.2011.12.027",
    ),
    "crocus_ls150-310.json": Publication(
        citation="F. Schmidt, B. Schmitt, S. Douté, F. Forget, J.-J. Jian, P. Martin, Y. Langevin, J.-P. Bibring (2010), Sublimation of the Martian CO2 Seasonal South Polar Cap, In Planetary and Space Science, Volume 58, Issues 10, 2010, Pages 1129-1138",
        doi="doi:10.1016/j.pss.2010.03.018",
    ),
    "scalloped_depression.json": Publication(
        citation="A.Séjourné, F.Costard, J.Gargani, R.J.Soare, C.Marmo (2012), Evidence of an eolian ice-rich and stratified permafrost in Utopia Planitia, Mars, In Icarus, Volume 60, Issue 1, 2012, Pages 248-254",
        doi="doi:10.1016/j.pss.2011.09.004",
    ),
    "costard_craters.json": Publication(
        citation="F.M Costard (1989), The spatial distribution of volatiles in the Martian hydrolithosphere, Earth Moon Planet, Volume 45, Pages 265-290.",
        doi="doi:10.1007/BF00057747",
    ),
}

instruments = {
    "hyd_global_290615.json": "",
    "scalloped_depression.json": {
        "name": "HiRISE",
        "id": "hirise",
        "link": "https://www.uahirise.org/",  # Put this in Assets
        "platform": {"name": "MRO (Mars Reconnaissance Orbiter)", "id": "mro"},
    },
}

platforms = ["tgo", "mro", "mex", "ody"]
tgo_instruments = ["cassis"]
mro_instruments = ["crism", "ctx", "hirise", "sharad"]
mex_instruments = ["hrsc", "omega"]
ody_instruments = ["themis"]


# TODO: add this in extra fields
acknowledgements = {
    "scalloped_depression.json": "Authors are funded by the Programme Nationale de Planétologie of Institut National des Sciences de l'Univers. We acknowledge the HiRISE Team and the Orsay Planetary Picture Library as well as the HRSC Team for the data provided (http://fototek.geol.u-psud.fr/). Special thanks to Indiana Romaire for the help estimating the dip using ArcGIS."
}


# TODO: add a processing since some products are stated to be L4


# OMEGA instrument (0.38-5.1 µm, sampled at 14nm)"
# https://www.ias.u-psud.fr/omega/instrument.html
# https://marssi.univ-lyon1.fr/wiki/OMEGA
omega_bands = [
    Band.create(
        name="Visible-SWIR",
        common_name="v",
        description="[Operational] 0.36-1.05 µm; Fully functional, routine operations",
        center_wavelength=_center_wavelength(0.36, 1.05),
        full_width_half_max=_fwhm(0.36, 1.05),
        solar_illumination=None,
    ),
    Band.create(
        name="NIR-SWIR",
        common_name="c",
        description="[Discontinued] 0.95-2.65 µm, Non-op since August 2010 (final orbit #8485)",
        center_wavelength=_center_wavelength(0.95, 2.65),
        full_width_half_max=_fwhm(0.95, 2.65),
        solar_illumination=None,
    ),
    Band.create(
        name="IR-MWIR",
        common_name="l",
        description="[Operational] 2.55-5.09 µm, Limited operations, on-demand only",
        center_wavelength=_center_wavelength(2.55, 5.09),
        full_width_half_max=_fwhm(2.55, 5.09),
        solar_illumination=None,
    ),
]


# CRISM instrument
# https://marssi.univ-lyon1.fr/wiki/CRISM
# http://crism.jhuapl.edu/index.php
crism_bands = [
    Band.create(
        name="VNIR",
        common_name="vnir",
        description="362-1053 nanometers",
        center_wavelength=_center_wavelength(0.362, 1.053),
        full_width_half_max=_fwhm(0.362, 1.053),
        solar_illumination=None,
    ),
    Band.create(
        name="IR",
        common_name="ir",
        description="1002-3920 nanometers",
        center_wavelength=_center_wavelength(1.002, 3.92),
        full_width_half_max=_fwhm(1.002, 3.92),
        solar_illumination=None,
    ),
]

# HiRISE instrument
# https://www.uahirise.org/
# https://hirise.lpl.arizona.edu/index.php
# https://www.uahirise.org/specs/
hirise_bands = [
    Band.create(
        name="Blue-Green",
        common_name="blue-green",
        description="400 to 600 nm",
        center_wavelength=_center_wavelength(0.4, 0.6),
        full_width_half_max=_fwhm(0.4, 0.6),
        solar_illumination=None,
    ),
    Band.create(
        name="Red",
        common_name="red",
        description="550 to 850 nm",
        center_wavelength=_center_wavelength(0.55, 0.85),
        full_width_half_max=_fwhm(0.55, 0.85),
        solar_illumination=None,
    ),
    Band.create(
        name="NIR",
        common_name="nir",
        description="800 to 1000 nm",
        center_wavelength=_center_wavelength(0.8, 1),
        full_width_half_max=_fwhm(0.8, 1),
        solar_illumination=None,
    ),
]

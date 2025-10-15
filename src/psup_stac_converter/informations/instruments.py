from pystac.extensions.eo import Band

platforms = ["tgo", "mro", "mex", "ody"]
tgo_instruments = ["cassis"]
mro_instruments = ["crism", "ctx", "hirise", "sharad"]
mex_instruments = ["hrsc", "omega"]
ody_instruments = ["themis"]


def _center_wavelength(min_wl: float, max_wl: float, round_digit: int = 3) -> float:
    return round((min_wl + max_wl) / 2, round_digit)


def _fwhm(min_wl, max_wl, round_digit: int = 3) -> float:
    return round(max_wl - min_wl, round_digit)


# OMEGA instrument (0.38-5.1 µm, sampled at 14nm)"
# https://www.ias.u-psud.fr/omega/instrument.html
# https://marssi.univ-lyon1.fr/wiki/OMEGA


# CRISM instrument
# https://marssi.univ-lyon1.fr/wiki/CRISM
# http://crism.jhuapl.edu/index.php

# HiRISE instrument
# https://www.uahirise.org/
# https://hirise.lpl.arizona.edu/index.php
# https://www.uahirise.org/specs/

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

# TODO: add a processing since some products are stated to be L4
# the processing level can be found on NASA's resources

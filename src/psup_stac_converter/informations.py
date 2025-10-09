import pystac
from pydantic import BaseModel, ConfigDict, HttpUrl
from pystac.extensions.eo import Band
from pystac.extensions.scientific import Publication
from shapely import Polygon


class GeoJsonFeaturesDesc(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # do not use FilePath because the file might not exist
    name: str
    description: str
    footprint: Polygon
    keywords: list[str]
    publications: Publication


class OmegaMineralMapDesc(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    thumbnail: HttpUrl  # ends with "*_reduce.png"
    raster_description: str
    raster_name: str
    raster_lng_description: str
    publication: Publication
    raster_keywords: list[str]


def _center_wavelength(min_wl: float, max_wl: float) -> float:
    return (min_wl + max_wl) / 2


def _fwhm(min_wl, max_wl) -> float:
    return max_wl - min_wl


geojson_features = {
    "hyd_global_290615.json": GeoJsonFeaturesDesc(
        name="hyd_global_290615.json",
        **{
            "description": "Hydrated mineral sites",
            "footprint": Polygon(((-180, -90), (180, 90), (180, 90), (180, -90))),
            "keywords": [],
            "publications": Publication(
                citation="Carter, J., F. Poulet, J.‐P. Bibring, N. Mangold, and S. Murchie (2013), Hydrous minerals on Mars as seen by the CRISM and OMEGA imaging spectrometers: Updated global view, J. Geophys. Res. Planets, 118, 831–858",
                doi="doi: 10.1029/2012JE004145",
            ),
        },
    ),
    "detections_crateres_benjamin_bultel_icarus.json": GeoJsonFeaturesDesc(
        name="detections_crateres_benjamin_bultel_icarus.json",
        **{
            "description": "Central peaks hydrated phases between isidis and hellas",
            "footprint": Polygon(((65, -19), (135.5, -19), (135.5, -2), (65, -2))),
            "keywords": [],
            "publications": Publication(
                citation="B. Bultel, C. Quantin-Nataf, M. Andréani, H. Clénet, L. Lozac’h (2015), Deep alteration between Hellas and Isidis Basins, In Icarus Volume 260, 2015, Pages 141-160",
                doi="doi:10.1016/j.icarus.2015.06.037",
            ),
        },
    ),
    "lcp_flahaut_et_al.json": GeoJsonFeaturesDesc(
        name="lcp_flahaut_et_al.json",
        **{
            "description": "Central peaks mineralogy south Valles Marineris",
            "footprint": Polygon(((-62, -16), (-37, -16), (-37, -4), (-62, -4))),
            "keywords": [],
            "publications": Publication(
                citation="C. Quantin, J. Flahaut, H. Clenet, P. Allemand, P. Thomas (2012), Composition and structures of the subsurface in the vicinity of Valles Marineris as revealed by central uplifts of impact craters, Icarus, Volume 221, Issue 1, 2012, Pages 436-452",
                doi="doi:10.1016/j.icarus.2012.07.031",
            ),
        },
    ),
    "lcp_vmwalls.json": GeoJsonFeaturesDesc(
        name="lcp_vmwalls.json",
        **{
            "description": "Valles Marineris low Calcium-Pyroxene",
            "footprint": Polygon(((-63, -16), (-37, -16), (-37, -4), (-63, -4))),
            "keywords": [],
            "publications": Publication(
                citation="J. Flahaut, C. Quantin, H. Clenet, P. Allemand, J. F. Mustard, P. Thomas (2012), Pristine Noachian crust and key geologic transitions in the lower walls of Valles Marineris: Insights into early igneous processes on Mars, In Icarus, Volume 221, Issue 1, 2012, Pages 420-435",
                doi="doi:10.1016/j.icarus.2011.12.027",
            ),
        },
    ),
    "crocus_ls150-310.json": GeoJsonFeaturesDesc(
        name="crocus_ls150-310.json",
        **{
            "description": "Seasonal South polar cap limits",
            "footprint": Polygon(((-180, -50), (-90, -50), (0, -50), (90, -50))),
            "keywords": [
                "polar  cap",
                "seasonal",
                "south",
                "CO2",
                "crocus line",
                "inner crocus line",
                "outer crocus line",
                "snowdrop  distance",
            ],
            "publications": Publication(
                citation="F. Schmidt, B. Schmitt, S. Douté, F. Forget, J.-J. Jian, P. Martin, Y. Langevin, J.-P. Bibring (2010), Sublimation of the Martian CO2 Seasonal South Polar Cap, In Planetary and Space Science, Volume 58, Issues 10, 2010, Pages 1129-1138",
                doi="doi:10.1016/j.pss.2010.03.018",
            ),
        },
    ),
    "scalloped_depression.json": GeoJsonFeaturesDesc(
        name="scalloped_depression.json",
        **{
            "description": "Scalloped depressions",
            "footprint": Polygon(((75, 39), (75, 52), (109, 52), (109, 39))),
            "keywords": [
                "northern  plains",
                "periglacial",
                "thermokarst",
                "ground ice",
            ],
            "publications": Publication(
                citation="A.Séjourné, F.Costard, J.Gargani, R.J.Soare, C.Marmo (2012), Evidence of an eolian ice-rich and stratified permafrost in Utopia Planitia, Mars, In Icarus, Volume 60, Issue 1, 2012, Pages 248-254",
                doi="doi:10.1016/j.pss.2011.09.004",
            ),
            "acknowledgements": "Authors are funded by the Programme Nationale de Planétologie of Institut National des Sciences de l'Univers. We acknowledge the HiRISE Team and the Orsay Planetary Picture Library as well as the HRSC Team for the data provided (http://fototek.geol.u-psud.fr/). Special thanks to Indiana Romaire for the help estimating the dip using ArcGIS.",
        },
    ),
    "costard_craters.json": GeoJsonFeaturesDesc(
        name="costard_craters.json",
        **{
            "description": "Lobate impact craters",
            "footprint": Polygon(((-180, -90), (180, 90), (180, 90), (180, -90))),
            "keywords": ["global", "craters", "ejecta", "lithosphere"],
            "publications": Publication(
                citation="F.M Costard (1989), The spatial distribution of volatiles in the Martian hydrolithosphere, Earth Moon Planet, Volume 45, Pages 265-290.",
                doi="doi:10.1007/BF00057747",
            ),
        },
    ),
}

# OMEGA - publications
omega_map_publications = [
    Publication(
        citation="A. Ody, F. Poulet, Y. Langevin, J.‐P. Bibring, G. Bellucci, F. Altieri, B. Gondet, M. Vincendon, J.Carter and N. Manaud (2012), Global maps of anhydrous minerals at the surface of Mars from OMEGA/MEx, J. Geophys. Res., 117, E00J14",
        doi="doi:10.1029/2012JE004117",
    ),
    Publication(
        citation="M. Vincendon, J. Audouard, F. Altieri, A. Ody (2015), Mars Express measurements of surface albedo changes over 2004–2010, In Icarus, Volume 251, 2015, Pages 145-163, ISSN 0019-1035",
        doi="doi:10.1016/j.icarus.2014.10.029",
    ),
    Publication(
        citation="J. Audouard, F. Poulet, M. Vincendon, J.-P. Bibring, F. Forget, Y. Langevin, B. Gondet (2014), Mars surface thermal inertia and heterogeneities from OMEGA/MEX, In Icarus Volume 233, 2014, Pages 194-213",
        doi="doi:10.1016/j.icarus.2014.01.045",
    ),
    Publication(
        citation="F. Poulet, C. Quantin-Nataf, H. Ballans, K. Dassas, J. Audouard, J. Carter, B. Gondet, L. Lozac’h, J.-C. Malapert, C. Marmo, L. Riu, A. Séjourné (2018), PSUP: a Planetary SUrface Portal, Planetary and Space Science, Volume 150, 2018, Pages 2-8",
        doi="doi:10.1016/j.pss.2017.01.016",
    ),
]


# OMEGA mineral map - descriptions
omega_mineral_maps = {
    "albedo_r1080_equ_map.fits": OmegaMineralMapDesc(
        raster_name="albedo_r1080_equ_map.fits",
        raster_description="OMEGA NIR albedo",
        raster_lng_description="""This data product is a global NIR 1-micrometer albedo map of Mars based on reflectance data acquired by the Mars Express OMEGA hyperspectral camera from January 2004 to August 2010""",
        raster_keywords=["albedo", "global"],
        thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/albedo_r1080_equ_map_reduce.png/sitools/upload/download-thumb.png",
        publication=Publication(
            citation="""
        Ody, A., F. Poulet, Y. Langevin, J.-P. Bibring, G. Bellucci, F. Altieri, B. Gondet, M. Vincendon, J. Carter, and N. Manaud (2012), Global maps of anhydrous minerals at the surface of Mars from OMEGA/MEx, J. Geophys. Res., 117, E00J14
        """,
            doi="doi:10.1029/2012JE004117",
        ),
    ),
    "ferric_bd530_equ_map.fits": OmegaMineralMapDesc(
        raster_name="ferric_bd530_equ_map.fits",
        raster_description="OMEGA Ferric BD530",
        raster_lng_description="""This data product is a global ferric oxide spectral parameter map of Mars based on reflectance data acquired by the Mars Express OMEGA hyperspectral camera from January 2004 to August 2010. This ferric oxide spectral parameter (DB530) is based on the strength of the 0.53 micrometer ferric absorption edge.""",
        raster_keywords=["ferric oxides", "global"],
        thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/ferric_bd530_equ_map_reduce.png/sitools/upload/download-thumb.png",
        publication=Publication(
            citation="""
        Ody, A., F. Poulet, Y. Langevin, J.-P. Bibring, G. Bellucci, F. Altieri, B. Gondet, M. Vincendon, J. Carter, and N. Manaud (2012), Global maps of anhydrous minerals at the surface of Mars from OMEGA/MEx, J. Geophys. Res., 117, E00J14
        """,
            doi="doi:10.1029/2012JE004117",
        ),
    ),
    "ferric_nnphs_equ_map.fits": OmegaMineralMapDesc(
        raster_name="ferric_nnphs_equ_map.fits",
        raster_description="OMEGA Ferric Nanophase",
        raster_lng_description="""This data product is a global nanophase ferric oxide (dust) spectral parameter map of Mars based on reflectance data acquired by the Mars Express OMEGA hyperspectral camera from January 2004 to August 2010. This nanophase ferric oxide spectral parameter (NNPHS) is based on the absorption feature centered at 0.86 micrometer.""",
        raster_keywords=["nanophase ferric oxides", "global"],
        thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/ferric_nnphs_equ_map_reduce.png/sitools/upload/download-thumb.png",
        publication=Publication(
            citation="""
        Ody, A., F. Poulet, Y. Langevin, J.-P. Bibring, G. Bellucci, F. Altieri, B. Gondet, M. Vincendon, J. Carter, and N. Manaud (2012), Global maps of anhydrous minerals at the surface of Mars from OMEGA/MEx, J. Geophys. Res., 117, E00J14
        """,
            doi="doi:10.1029/2012JE004117",
        ),
    ),
    "olivine_osp1_equ_map.fits": OmegaMineralMapDesc(
        raster_name="olivine_osp1_equ_map.fits",
        raster_description="OMEGA Olivine SP1",
        raster_lng_description="""This data product is a global olivine spectral parameter map of Mars based on reflectance data acquired by the Mars Express OMEGA hyperspectral camera from January 2004 to August 2010. This olivine spectral parameter (OSP1) detects Mg-rich and/or small grain size and/or low abundance olivine.""",
        raster_keywords=["olivine", "global"],
        thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/olivine_osp1_equ_map_reduce.png/sitools/upload/download-thumb.png",
        publication=Publication(
            citation="""
        Ody, A., F. Poulet, Y. Langevin, J.-P. Bibring, G. Bellucci, F. Altieri, B. Gondet, M. Vincendon, J. Carter, and N. Manaud (2012), Global maps of anhydrous minerals at the surface of Mars from OMEGA/MEx, J. Geophys. Res., 117, E00J14
        """,
            doi="doi:10.1029/2012JE004117",
        ),
    ),
    "olivine_osp2_equ_map.fits": OmegaMineralMapDesc(
        raster_name="olivine_osp2_equ_map.fits",
        raster_description="OMEGA Olivine SP2",
        raster_lng_description="""This data product is a global olivine spectral parameter map of Mars based on reflectance data acquired by the Mars Express OMEGA hyperspectral camera from January 2004 to August 2010. This olivine spectral parameter (OSP2) is sensitive to olivine with high iron content and/or large grain size and/or high abundance.""",
        raster_keywords=["olivine", "global"],
        thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/olivine_osp2_equ_map_reduce.png/sitools/upload/download-thumb.png",
        publication=Publication(
            citation="""
        Ody, A., F. Poulet, Y. Langevin, J.-P. Bibring, G. Bellucci, F. Altieri, B. Gondet, M. Vincendon, J. Carter, and N. Manaud (2012), Global maps of anhydrous minerals at the surface of Mars from OMEGA/MEx, J. Geophys. Res., 117, E00J14
        """,
            doi="doi:10.1029/2012JE004117",
        ),
    ),
    "olivine_osp3_equ_map.fits": OmegaMineralMapDesc(
        raster_name="olivine_osp3_equ_map.fits",
        raster_description="OMEGA Olivine SP3",
        raster_lng_description="""This data product is a global olivine spectral parameter map of Mars based on reflectance data acquired by the Mars Express OMEGA hyperspectral camera from January 2004 to August 2010. This olivine spectral parameter (OSP3) determines the full band depth at 1.36 micrometer relative to a continuum. It preferentially detects olivine with a large Fe content and/or with large grain size and/or with high abundance.""",
        raster_keywords=["olivine", "global"],
        thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/olivine_osp3_equ_map_reduce.png/sitools/upload/download-thumb.png",
        publication=Publication(
            citation="""
        Ody, A., F. Poulet, Y. Langevin, J.-P. Bibring, G. Bellucci, F. Altieri, B. Gondet, M. Vincendon, J. Carter, and N. Manaud (2012), Global maps of anhydrous minerals at the surface of Mars from OMEGA/MEx, J. Geophys. Res., 117, E00J14
        """,
            doi="doi:10.1029/2012JE004117",
        ),
    ),
    "pyroxene_bd2000_equ_map.fits": OmegaMineralMapDesc(
        raster_name="pyroxene_bd2000_equ_map.fits",
        raster_description="OMEGA Pyroxene",
        raster_lng_description="""This data product is a global pyroxene spectral parameter map of Mars based on reflectance data acquired by the Mars Express OMEGA hyperspectral camera from January 2004 to August 2010. This pyroxene spectral parameter (BD2000) is based on its 2 micrometer absorption band due to both high-calcium and low-calcium pyroxene.""",
        raster_keywords=["pyroxene", "global"],
        thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/pyroxene_bd2000_equ_map_reduce.png/sitools/upload/download-thumb.png",
        publication=Publication(
            citation="""
        Ody, A., F. Poulet, Y. Langevin, J.-P. Bibring, G. Bellucci, F. Altieri, B. Gondet, M. Vincendon, J. Carter, and N. Manaud (2012), Global maps of anhydrous minerals at the surface of Mars from OMEGA/MEx, J. Geophys. Res., 117, E00J14
        """,
            doi="doi:10.1029/2012JE004117",
        ),
    ),
    "albedo_filled.fits": OmegaMineralMapDesc(
        raster_name="albedo_filled.fits",
        raster_description="OMEGA Albedo Filled",
        raster_lng_description="""60 ppd global map of Solar Albedo from OMEGA data fileld with TES 20 ppd solar albedo global maps (Putzig and Mellon, 2007b) (21600x10800 pixels). This map is 100% filled. Variable name is "albedo". "latitude" and "longitude" indicate the coordinates of the centers of the pixels. Reference : Vincendon et al., Icarus, 2015""",
        raster_keywords=["albedo", "filled", "global"],
        thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/albedo_filled_reduce.png/sitools/upload/download-thumb.png",
        publication=Publication(
            citation="""
        M. Vincendon, J. Audouard, F. Altieri, A. Ody, Mars Express measurements of surface albedo changes over 2004–2010, Icarus, Volume 251, 2015, Pages 145-163, ISSN 0019-1035
        """,
            doi="https://doi.org/10.1016/j.icarus.2014.10.029",
        ),
    ),
    "albedo_unfilled.fits": OmegaMineralMapDesc(
        raster_name="albedo_unfilled.fits",
        raster_description="OMEGA Albedo Unfilled",
        raster_lng_description="""60 ppd global map of Solar Albedo from OMEGA data only (21600 x 10800 pixels). This map is filled at 94.79% (rest are NaN). Variable name is "albedo". "latitude" and "longitude" indicate the coordinates of the centers of the pixels. Reference : Vincendon et al., Icarus, 2015.""",
        raster_keywords=["albedo", "unfilled", "global"],
        thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/albedo_unfilled_reduce.png/sitools/upload/download-thumb.png",
        publication=Publication(
            citation="""
        M. Vincendon, J. Audouard, F. Altieri, A. Ody, Mars Express measurements of surface albedo changes over 2004–2010, Icarus, Volume 251, 2015, Pages 145-163, ISSN 0019-1035
        """,
            doi="https://doi.org/10.1016/j.icarus.2014.10.029",
        ),
    ),
    "emissivite_5.03mic_OMEGA0.fits": OmegaMineralMapDesc(
        raster_name="emissivite_5.03mic_OMEGA0.fits",
        raster_description="OMEGA0 Emissivity at 5.03 mic",
        raster_lng_description="""40 ppd global maps of surface emissivity at 5.03 mic. Holes are set to NaN.""",
        raster_keywords=["emissivity", "5mic", "global"],
        thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/emissivite_5.03mic_OMEGA0_reduce.png/sitools/upload/download-thumb.png",
        publication=Publication(
            citation="""
        J. Audouard, F. Poulet, M. Vincendon, J.-P. Bibring, F. Forget, Y. Langevin, B. Gondet, Mars surface thermal inertia and heterogeneities from OMEGA/MEX, Icarus, Volume 233, 2014, Pages 194-213, ISSN 0019-1035,
        """,
            doi="https://doi.org/10.1016/j.icarus.2014.01.045",
        ),
    ),
}

# Data providers
data_providers = [
    pystac.Provider(
        name="Institut d'Astrophysique Spatiale (IAS) - IDOC",
        description="The Integrated Data and Operation Center (IDOC) is responsible for processing, archiving\nand distributing data from space science missions in which the IAS institute is involved.\n",
        roles=[
            pystac.ProviderRole.PROCESSOR,
            pystac.ProviderRole.PRODUCER,
            pystac.ProviderRole.HOST,
        ],
        url="https://idoc.ias.universite-paris-saclay.fr",
    ),
    pystac.Provider(
        name="Géosciences Paris-Saclay (GEOPS)",
        description='GEOPS is a joint laboratory of the \u201cUniversit\u00e9 de Paris-Sud\u201d (UPSUD) and the "Centre National\nde la Recherche Scientifique" (CNRS).\n',
        roles=[
            pystac.ProviderRole.PROCESSOR,
            pystac.ProviderRole.PRODUCER,
        ],
        url="http://geops.geol.u-psud.fr",
    ),
    pystac.Provider(
        name="Planetary SUrface Portal (PSUP)",
        description="PSUP is a french research service, by Observatoire Paris-Sud and Observatoire de Lyon, to help\nthe distribution of high added-value datasets of planetary surfaces.\n",
        roles=[
            pystac.ProviderRole.LICENSOR,
        ],
        url="https://psup.cnrs.fr",
    ),
]


# Mission platforms
platforms = ["tgo", "mro", "mex", "ody"]

# Related insturments
tgo_instruments = ["cassis"]
mro_instruments = ["crism", "ctx", "hirise", "sharad"]
mex_instruments = ["hrsc", "omega"]
ody_instruments = ["themis"]


# TODO: add a processing since some products are stated to be L4
# the processing level can be found on NASA's resources

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

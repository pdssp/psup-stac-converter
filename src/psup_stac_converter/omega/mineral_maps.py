import datetime as dt
import json
from pathlib import Path

import pystac
from pydantic import BaseModel, ConfigDict, HttpUrl
from pystac.extensions.scientific import Publication
from shapely import Polygon, bounds, to_geojson

from psup_stac_converter.extensions import apply_eo, apply_sci, apply_ssys
from psup_stac_converter.informations.data_providers import providers
from psup_stac_converter.informations.instruments import omega_bands
from psup_stac_converter.informations.publications import omega_map_publications
from psup_stac_converter.utils.io import PsupIoHandler


class OmegaMineralMapDesc(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    thumbnail: HttpUrl  # ends with "*_reduce.png"
    raster_description: str
    raster_name: str
    raster_lng_description: str
    publication: Publication
    raster_keywords: list[str]
    created_at: dt.datetime


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
        created_at=dt.datetime(2012, 5, 2, 0, 0),
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
        created_at=dt.datetime(2012, 5, 2, 0, 0),
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
        created_at=dt.datetime(2012, 5, 2, 0, 0),
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
        created_at=dt.datetime(2012, 5, 2, 0, 0),
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
        created_at=dt.datetime(2012, 5, 2, 0, 0),
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
        created_at=dt.datetime(2012, 5, 2, 0, 0),
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
        created_at=dt.datetime(2012, 5, 2, 0, 0),
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
        created_at=dt.datetime(2014, 7, 10, 0, 0),
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
        created_at=dt.datetime(2014, 7, 10, 0, 0),
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
        created_at=dt.datetime(2013, 7, 1, 0, 0),
        # Global map is 4ppd (15x15km at eq), cylindrical projection
        # Represents mean TI from OMEGA, [30, 1050] Jm^-2s^-1/2K^-1
        # Observations are restricted between lat -45,45
    ),
}


def _spatial_extent() -> pystac.SpatialExtent:
    return pystac.SpatialExtent(bboxes=[[-180.0, -90.0, 180.0, 90.0]])


def _temporal_extent() -> pystac.TemporalExtent:
    return pystac.TemporalExtent(
        intervals=[
            [
                min([v.created_at for v in omega_mineral_maps.values()]),
                max([v.created_at for v in omega_mineral_maps.values()]),
            ]
        ]
    )


def _create_pystac_item(
    omega_map_item: OmegaMineralMapDesc, psup_archive: PsupIoHandler
) -> pystac.Item:
    map_geometry = Polygon(((-180, -90), (180, 90), (180, 90), (180, -90)))
    footprint = json.loads(to_geojson(map_geometry))
    bbox = bounds(map_geometry).tolist()
    timestamp = omega_map_item.created_at
    stac_item_properties = {
        "description": omega_map_item.raster_description,
        "long_description": omega_map_item.raster_lng_description,
        "keywords": omega_map_item.raster_keywords,
    }
    pystac_item = pystac.Item(
        id=Path(omega_map_item.raster_name).stem.replace("_", "-"),
        properties=stac_item_properties,
        geometry=footprint,
        bbox=bbox,
        datetime=timestamp,
    )
    # assets
    thumbn_asset = pystac.Asset(
        href=str(omega_map_item.thumbnail),
        media_type=pystac.MediaType.PNG,
        roles=["thumbnail"],
        description="PNG thumbnail preview for visualizations",
    )
    pystac_item.add_asset("thumbnail", thumbn_asset)
    remote_fits = psup_archive.find_file_remote_path(omega_map_item.raster_name)

    # Source: https://www.iana.org/assignments/media-types/media-types.xhtml
    fits_asset = pystac.Asset(
        href=str(remote_fits),
        media_type="application/fits",
        roles=["visual", "data"],
        description="FITS data",
    )
    pystac_item.add_asset("fits", fits_asset)
    # extensions
    pystac_item = apply_sci(pystac_item, publications=omega_map_item.publication)
    pystac_item = apply_ssys(pystac_item)
    pystac_item = apply_eo(pystac_item, bands=omega_bands)
    # common metadata
    pystac_item.common_metadata.platform = "mex"
    pystac_item.common_metadata.instruments = ["omega"]
    pystac_item.common_metadata.gsd = 5000
    return pystac_item


def omega_maps_collection_generator(psup_archive: PsupIoHandler) -> pystac.Collection:
    """Generates a STAC collection of the OMEGA mineral maps dataset.

    Args:
        psup_archive (PsupIoHandler): The handler for I/O operations related to
        PSUP's raw data. It's mostly used to operate on the outside.

    Returns:
        pystac.Collection: A STAC collection representing each item of the OMEGA
        mineral maps.
    """
    collection_extent = pystac.Extent(
        spatial=_spatial_extent(), temporal=_temporal_extent()
    )

    master_collection = pystac.Collection(
        id="urn:pdssp:ias:collection:omega_mineral_maps",
        extent=collection_extent,
        license="CC-BY-4.0",
        description="""PSUP OMEGA mineral maps are OMEGA-based NIR albedo, Ferric BD530, Ferric Nanophase, Olivine SP1, SP2, SP3, Pyroxene and Emissivity at 5.03µm. OMEGA is the VISNIR imaging spectrometer onboard ESA/Mars-Express spacecraft operating around Mars from January 2004. All maps are provided in FITS file format via the "download" column.

This Dataset is also available as a VO TAP service (ivo://idoc/psup/omega_maps/q/epn_core).""",
        providers=providers,
        keywords=list(
            set(
                [
                    kw
                    for omega_map_item in omega_mineral_maps.values()
                    for kw in omega_map_item.raster_keywords
                ]
            )
        ),
    )

    # Apply extensions here
    master_collection = apply_ssys(master_collection)
    master_collection = apply_sci(
        master_collection, publications=omega_map_publications
    )

    # iterate on the maps
    for omega_map_item in omega_mineral_maps.values():
        omega_item = _create_pystac_item(omega_map_item, psup_archive=psup_archive)
        master_collection.add_item(omega_item)

    return master_collection

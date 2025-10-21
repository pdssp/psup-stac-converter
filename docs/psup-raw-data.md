# PSUP

[PSUP (**P**lanetary **SU**rface **P**ortal)](http://psup.ias.u-psud.fr/sitools/client-user/index.html?project=PLISonMars) is a SaaS (Software as a Service) application hosting and sharing several TB of data, primarily centered on the surface of Mars and addressed to the French community of planetary scientists.

The data in question is composed different kind of information like albedo, mineral and thermal inertia, mosaics, image footprints and rasters, all collected from past recent Martian missions, primarily from MEX (Mars EXpress) and MRO (Mars Reconnaissance Orbiter) missions. The service then exposes this data through three services:

1. **MarsSI:** [Martian surface data processing Information System](https://marssi.univ-lyon1.fr/MarsSI/). A service that allows the user to manage and process data, and at the same time visualize and merge high level products and catalogs thanks to a web-based interface.
2. **Datasets:** distributes some of the specific high level data with an emphasis on products issues by the science teams of Observatory of Paris Sud (OSUPS) and Observatory of Lyon (OSUL).
3. **MarsVisu:** a 3D interactive map providing some visualization and merging of high level products and local nomenclature-based catalogs. This service uses the [SITools2](https://github.com/SITools2/SITools2-core) REST API to manage de data, and the [MIZAR](https://sitools2.github.io/MIZAR/) module to display it.

![psup_graph](/img/psup_structure.jpg)

## Datasets

The datasets are mostly stored on the [SITools database](http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/). They consist of catalogues, images, hyperspectral cubes and DTMs (Digital Terrain Model), all from Mars' database, organized into collections.

* Photometry maps
* MOLA: contains topography of Mars
* OMEGA data cubes
* Geojson features
* OMEGA data

An overview of the datasets available can be found there (F. Poulet, 2018)

| Dataset                      | Source                                              | Format             | Level | Access                     |
| ---------------------------- | --------------------------------------------------- | ------------------ | ----- | -------------------------- |
| Global mosaics               | Viking imager, THEMIS, MOLA, CTX, TES, OMEGA        | Raster/Images      | L4    | MarsVisu/Bakcground Layers |
| Mineral global maps          | OMEGA & TES                                         | Raster/Images      | L4    | MarsVisu/Mineral Layers    |
| Images                       | CTX & HiRISE                                        | Raster/Images      | L3    | MarsVisu & MarsSI          |
| DTM                          | CTX & HiRISE                                        | Raster/Images      | L4    | MarsSI & MarsVisu          |
| Hyperspectral cubes          | OMEGA & CRISM                                       | Rasters/Data cubes | L3    | MarsVisu & MarsSI          |
| Hydrated mineral sites       | OMEGA & CRISM                                       | Vectors            | L4    | MarsVisu/Catalogs          |
| Crocus line                  | OMEGA                                               | Vectors            | L4    | MarsVisu/Catalogs          |
| Regional and global catalogs | Peer-reviewed works based on OMEGA, CRISM, CTX, MOC | Vectors            | L4    | MarsVisu/Catalogs          |

Since the data is hosted through the API, it can be linked from here as an asset.

!!! warning "SITools deprecation"
    SITools is actually deprecated. The REST API links might not be a good idea as a reference


## Geojson features

Geojson features, otherwise known as PSUP Catalogs, all regroup vector catalogs and their associated metadata, under the [GeoJson](https://geojson.org/) format. They regroup the following characteristics:

* Hydrated mineral terrains
* Central peaks hydrated phases between Isidis and Hellas
* Central peaks mineralogy south Valles Marineris
* Valles Marineris low Calcium-Pyroxene deposits
* Seasonal South polar cap limits
* Scalloped depressions
* Lobate impact craters

Each one of them has a defined footprint range, which is a bbox enclosing all the features. If the features aren't constrained to any region unlike Valles Marineris, the total range goes from $[-180, -90, 180, 90]$. They also have some optional keywords and a brief description.

Since the features are written in GeoJson, turning them as a STAC catalog is easy. The best way to read a GeoJson set of features is using the [GeoPandas package](https://geopandas.org/en/stable/index.html), which is an adaptation of the Pandas library, for geographical features. By using `gpd.read_file()`, examining the contents of these features is straightforward.

If, for whatever reason, Geopandas can't open the file (ex. the dataset from *Seasonal South polar cap limits*), a manual conversion using a mix of Shapely and Pandas can still be done to resolve the issue.

Assuming each set of feature is a collection, they can be connected under the same catalog. The collection thus bears the name of the feature, given by the metadata, the description, the keywords and the spatial extent given by the footprint. Since these are features interpreted from raster images, contents from the MEX and MRO missions, a temporal dimension was thus not given. By default, each feature bears the same date as the day the related article was published. If a range is demanded, the dates are fixed by default on the Pandas library's maximum and minimum date.

## OMEGA mineral maps

!!! info "Available data"
    An attempt has already been made under [the PDSSP's STAC repository's test branch](https://github.com/pdssp/pdssp-stac-repo/tree/test). The data from the OMEGA instrument is divided in 3 parts.


PSUP OMEGA mineral maps are

- OMEGA-based NIR albedo
- Ferric BD530
- Ferric Nanophase
- Olivine SP1
- Olivine SP2
- Olivine SP3
- Pyroxene
- Emissivity at 5.03µm

OMEGA is the VISNIR imaging spectrometer onboard ESA/Mars-Express spacecraft operating around Mars from January 2004. All maps are provided in FITS file format via the "download" column.

This Dataset is also available as a [VO TAP service](ivo://idoc/psup/omega_maps/q/epn_core).

Since this part of the original data only has 8 items, The information was hardcoded in the package, and then automatically generated as a collection.

??? note "OMEGA maps data (from `psup_stac_converter/omega/mineral_maps.py`)"
    ``` python
    omega_mineral_maps = {
        "albedo_r1080_equ_map.fits": OmegaMineralMapDesc(
            raster_name="albedo_r1080_equ_map.fits",
            raster_description="OMEGA NIR albedo",
            raster_lng_description="""This data product is a global NIR 1-micrometer albedo map of Mars     based on reflectance data acquired by the Mars Express OMEGA hyperspectral camera from January  2004 to August 2010""",
            raster_keywords=["albedo", "global"],
            thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/   albedo_r1080_equ_map_reduce.png/sitools/upload/download-thumb.png",
            publication=Publication(
                citation="""
            Ody, A., F. Poulet, Y. Langevin, J.-P. Bibring, G. Bellucci, F. Altieri, B. Gondet, M.  Vincendon, J. Carter, and N. Manaud (2012), Global maps of anhydrous minerals at the surface     of Mars from OMEGA/MEx, J. Geophys. Res., 117, E00J14
            """,
                doi="doi:10.1029/2012JE004117",
            ),
            created_at=dt.datetime(2012, 5, 2, 0, 0),
        ),
        "ferric_bd530_equ_map.fits": OmegaMineralMapDesc(
            raster_name="ferric_bd530_equ_map.fits",
            raster_description="OMEGA Ferric BD530",
            raster_lng_description="""This data product is a global ferric oxide spectral parameter map of  Mars based on reflectance data acquired by the Mars Express OMEGA hyperspectral camera from  January 2004 to August 2010. This ferric oxide spectral parameter (DB530) is based on the    strength of the 0.53 micrometer ferric absorption edge.""",
            raster_keywords=["ferric oxides", "global"],
            thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/   ferric_bd530_equ_map_reduce.png/sitools/upload/download-thumb.png",
            publication=Publication(
                citation="""
            Ody, A., F. Poulet, Y. Langevin, J.-P. Bibring, G. Bellucci, F. Altieri, B. Gondet, M.  Vincendon, J. Carter, and N. Manaud (2012), Global maps of anhydrous minerals at the surface     of Mars from OMEGA/MEx, J. Geophys. Res., 117, E00J14
            """,
                doi="doi:10.1029/2012JE004117",
            ),
            created_at=dt.datetime(2012, 5, 2, 0, 0),
        ),
        "ferric_nnphs_equ_map.fits": OmegaMineralMapDesc(
            raster_name="ferric_nnphs_equ_map.fits",
            raster_description="OMEGA Ferric Nanophase",
            raster_lng_description="""This data product is a global nanophase ferric oxide (dust) spectral  parameter map of Mars based on reflectance data acquired by the Mars Express OMEGA   hyperspectral camera from January 2004 to August 2010. This nanophase ferric oxide spectral   parameter (NNPHS) is based on the absorption feature centered at 0.86 micrometer.""",
            raster_keywords=["nanophase ferric oxides", "global"],
            thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/   ferric_nnphs_equ_map_reduce.png/sitools/upload/download-thumb.png",
            publication=Publication(
                citation="""
            Ody, A., F. Poulet, Y. Langevin, J.-P. Bibring, G. Bellucci, F. Altieri, B. Gondet, M.  Vincendon, J. Carter, and N. Manaud (2012), Global maps of anhydrous minerals at the surface     of Mars from OMEGA/MEx, J. Geophys. Res., 117, E00J14
            """,
                doi="doi:10.1029/2012JE004117",
            ),
            created_at=dt.datetime(2012, 5, 2, 0, 0),
        ),
        "olivine_osp1_equ_map.fits": OmegaMineralMapDesc(
            raster_name="olivine_osp1_equ_map.fits",
            raster_description="OMEGA Olivine SP1",
            raster_lng_description="""This data product is a global olivine spectral parameter map of Mars  based on reflectance data acquired by the Mars Express OMEGA hyperspectral camera from January   2004 to August 2010. This olivine spectral parameter (OSP1) detects Mg-rich and/or small grain    size and/or low abundance olivine.""",
            raster_keywords=["olivine", "global"],
            thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/   olivine_osp1_equ_map_reduce.png/sitools/upload/download-thumb.png",
            publication=Publication(
                citation="""
            Ody, A., F. Poulet, Y. Langevin, J.-P. Bibring, G. Bellucci, F. Altieri, B. Gondet, M.  Vincendon, J. Carter, and N. Manaud (2012), Global maps of anhydrous minerals at the surface     of Mars from OMEGA/MEx, J. Geophys. Res., 117, E00J14
            """,
                doi="doi:10.1029/2012JE004117",
            ),
            created_at=dt.datetime(2012, 5, 2, 0, 0),
        ),
        "olivine_osp2_equ_map.fits": OmegaMineralMapDesc(
            raster_name="olivine_osp2_equ_map.fits",
            raster_description="OMEGA Olivine SP2",
            raster_lng_description="""This data product is a global olivine spectral parameter map of Mars  based on reflectance data acquired by the Mars Express OMEGA hyperspectral camera from January   2004 to August 2010. This olivine spectral parameter (OSP2) is sensitive to olivine with high     iron content and/or large grain size and/or high abundance.""",
            raster_keywords=["olivine", "global"],
            thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/   olivine_osp2_equ_map_reduce.png/sitools/upload/download-thumb.png",
            publication=Publication(
                citation="""
            Ody, A., F. Poulet, Y. Langevin, J.-P. Bibring, G. Bellucci, F. Altieri, B. Gondet, M.  Vincendon, J. Carter, and N. Manaud (2012), Global maps of anhydrous minerals at the surface     of Mars from OMEGA/MEx, J. Geophys. Res., 117, E00J14
            """,
                doi="doi:10.1029/2012JE004117",
            ),
            created_at=dt.datetime(2012, 5, 2, 0, 0),
        ),
        "olivine_osp3_equ_map.fits": OmegaMineralMapDesc(
            raster_name="olivine_osp3_equ_map.fits",
            raster_description="OMEGA Olivine SP3",
            raster_lng_description="""This data product is a global olivine spectral parameter map of Mars  based on reflectance data acquired by the Mars Express OMEGA hyperspectral camera from January   2004 to August 2010. This olivine spectral parameter (OSP3) determines the full band depth at     1.36 micrometer relative to a continuum. It preferentially detects olivine with a large Fe  content and/or with large grain size and/or with high abundance.""",
            raster_keywords=["olivine", "global"],
            thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/   olivine_osp3_equ_map_reduce.png/sitools/upload/download-thumb.png",
            publication=Publication(
                citation="""
            Ody, A., F. Poulet, Y. Langevin, J.-P. Bibring, G. Bellucci, F. Altieri, B. Gondet, M.  Vincendon, J. Carter, and N. Manaud (2012), Global maps of anhydrous minerals at the surface     of Mars from OMEGA/MEx, J. Geophys. Res., 117, E00J14
            """,
                doi="doi:10.1029/2012JE004117",
            ),
            created_at=dt.datetime(2012, 5, 2, 0, 0),
        ),
        "pyroxene_bd2000_equ_map.fits": OmegaMineralMapDesc(
            raster_name="pyroxene_bd2000_equ_map.fits",
            raster_description="OMEGA Pyroxene",
            raster_lng_description="""This data product is a global pyroxene spectral parameter map of  Mars based on reflectance data acquired by the Mars Express OMEGA hyperspectral camera from  January 2004 to August 2010. This pyroxene spectral parameter (BD2000) is based on its 2     micrometer absorption band due to both high-calcium and low-calcium pyroxene.""",
            raster_keywords=["pyroxene", "global"],
            thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/   pyroxene_bd2000_equ_map_reduce.png/sitools/upload/download-thumb.png",
            publication=Publication(
                citation="""
            Ody, A., F. Poulet, Y. Langevin, J.-P. Bibring, G. Bellucci, F. Altieri, B. Gondet, M.  Vincendon, J. Carter, and N. Manaud (2012), Global maps of anhydrous minerals at the surface     of Mars from OMEGA/MEx, J. Geophys. Res., 117, E00J14
            """,
                doi="doi:10.1029/2012JE004117",
            ),
            created_at=dt.datetime(2012, 5, 2, 0, 0),
        ),
        "albedo_filled.fits": OmegaMineralMapDesc(
            raster_name="albedo_filled.fits",
            raster_description="OMEGA Albedo Filled",
            raster_lng_description="""60 ppd global map of Solar Albedo from OMEGA data field with TES 20  ppd solar albedo global maps (Putzig and Mellon, 2007b) (21600x10800 pixels). This map is 100%   filled. Variable name is "albedo". "latitude" and "longitude" indicate the coordinates of the     centers of the pixels. Reference : Vincendon et al., Icarus, 2015""",
            raster_keywords=["albedo", "filled", "global"],
            thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/   albedo_filled_reduce.png/sitools/upload/download-thumb.png",
            publication=Publication(
                citation="""
            M. Vincendon, J. Audouard, F. Altieri, A. Ody, Mars Express measurements of surface albedo  changes over 2004–2010, Icarus, Volume 251, 2015, Pages 145-163, ISSN 0019-1035
            """,
                doi="https://doi.org/10.1016/j.icarus.2014.10.029",
            ),
            created_at=dt.datetime(2014, 7, 10, 0, 0),
        ),
        "albedo_unfilled.fits": OmegaMineralMapDesc(
            raster_name="albedo_unfilled.fits",
            raster_description="OMEGA Albedo Unfilled",
            raster_lng_description="""60 ppd global map of Solar Albedo from OMEGA data only (21600 x   10800 pixels). This map is filled at 94.79% (rest are NaN). Variable name is "albedo".    "latitude" and "longitude" indicate the coordinates of the centers of the pixels. Reference :  Vincendon et al., Icarus, 2015.""",
            raster_keywords=["albedo", "unfilled", "global"],
            thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/   albedo_unfilled_reduce.png/sitools/upload/download-thumb.png",
            publication=Publication(
                citation="""
            M. Vincendon, J. Audouard, F. Altieri, A. Ody, Mars Express measurements of surface albedo  changes over 2004–2010, Icarus, Volume 251, 2015, Pages 145-163, ISSN 0019-1035
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
            thumbnail="http://psup.ias.u-psud.fr/sitools/datastorage/user/storage/marsdata/omega/png/   emissivite_5.03mic_OMEGA0_reduce.png/sitools/upload/download-thumb.png",
            publication=Publication(
                citation="""
            J. Audouard, F. Poulet, M. Vincendon, J.-P. Bibring, F. Forget, Y. Langevin, B. Gondet, Mars    surface thermal inertia and heterogeneities from OMEGA/MEX, Icarus, Volume 233, 2014, Pages    194-213, ISSN 0019-1035,
            """,
                doi="https://doi.org/10.1016/j.icarus.2014.01.045",
            ),
            created_at=dt.datetime(2013, 7, 1, 0, 0),
            # Global map is 4ppd (15x15km at eq), cylindrical projection
            # Represents mean TI from OMEGA, [30, 1050] Jm^-2s^-1/2K^-1
            # Observations are restricted between lat -45,45
        ),
    }
    ```

The date has been established according to the publication date. Eventually the items can be complemented by the data found in the FITS file. Keep in mind theese FITS files are expensive to open. Therefore it would be wiser to do some data introspection first with the [astropy](https://www.astropy.org/) module.


## OMEGA data cubes

This dataset contains all the OMEGA observations acquired with the C, L and VIS channels until April 2016, 11, after filtering. Filtering processes have been implemented to remove some instrumental artefacts and observational conditions. Each OMEGA record is available as a `netCDF4.nc` file and an `idl.sav` file.

Both files contain the cubes of reflectance of the surface at a given longitude, latitude and wavelength $\lambda$. The surface reflectance is defined as $I/F/\cos(i)$ where:

- **Channels:**
    - $C=[0.93, 2.73 \mu m]$
    - $L=[2.55, 5.10 \mu m]$
    - $\text{Visible}=[0.38, 1.05 \mu m]$
- Atmospheric attenuation is corrected (1-5 µm);
- Airborne dust scattering is corrected (0.4-2.5 µm and for 5 µm emissivity estimations);
- Thermal contribution is removed (> 3 µm); L channel data and VIS channel are co-registered with C channel when available.

Please note that longitudes range from -180 to 180 degrees east.

An OMEGA data cube's ID is labeled with an orbit and a cube number connected by an underscore `_`. They usually come with two files: the `.sav`file and the `.nc`file.

Both files, serving as assets, are similar on the common points that need to be extracted from. An IDL `.sav` file is opened using [the IDL program](https://www.nv5geospatialsoftware.com/), while a NetCDF `.nc` file can be opened using third party libraries as indicated by [Unidata's documentation](https://docs.unidata.ucar.edu/nug/current/index.html). Both are multi-dimensional arrays, typically providing information on geospatial and atmospheric data respectfully.

Although `.sav` files are typcially meant to be read with IDL, it's possible to open them with Python, in particular with the `readsav` function from [scipy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.io.readsav.html)'s IO module. Meanwhile, NetCDF files can be opened using any modern programming language. The converter uses [xarray](https://docs.xarray.dev/en/stable/index.html) to open them. In both cases, these two files respect a key-value configuration simplifying the process.

The structure of both files for OMEGA data cubes goes as follow:

### .sav file

**Dimensions**

- **wvl:** Electromagnetic wavelength (in µm). The channels are ordered as follow: C,L,VIS.
- **lat:** Planetocentric latitude (in degree). Values of the table correspond to each pixel of the data cube.
- **lon:** Eastward longitude (in degree). Values of the table correspond to each pixel of the data cube, they range from -180 to +180 degrees.

**3D cube**

- **ldat_j:** Reflectance of the surface at a given longitude, latitude and wavelength. The surface reflectance is defined as I/F/cos(i) for the three channels. Note that:
    - atmospheric attenuation is corrected (1-5 µm);
    - airborne dust scattering is corrected (0.4-2.5 µm and for 5 µm emissivity estimations);
    - thermal contribution is removed (> 3 µm);
    - channels are co-registered.

**2D variables**

*Some parameters are detailed in the OMEGA EAICD[^1].*

- **altitude:** Altitude (in m) at a given longitude and latitude (MOLA – ellipsoid as reference).
- **incidence_g:** Incidence angle (in degree) with respect to the outward normal to the reference ellipsoid at a given longitude and latitude.
- **emergence_g:** Emergence angle (in degree) with respect to the outward normal to the reference ellipsoid.
- **incidence_l:** Incidence angle (in degree) with respect to the local normal.
- **watericelin:** The watericelin index value at a given longitude and latitude. This criterion, described in Langevin et al. (2007) is based on the 1.5 μm band depth. It can be used to detect icy frost presence at the surface and thick clouds in the atmosphere. Every OMEGA pixel with a watericelin value < 0.985 should be excluded.
- **icecloudindex:** The icecloud index value at a given longitude and latitude. This criterion (reflectance at 3.4 μm divided by reflectance at 3.52 μm) is described in Langevin et al. (2007) to identify the presence of water ice clouds. Its values range from 0.5 to 1.0. The smallest values unambiguously indicate the presence of icy clouds. We usually exclude any OMEGA pixel with a value < 0.8.
- **heure:** Martian hour at local true solar time LTST of the observation.
- **leslon0:** East longitude (in degree) of the pixel footprint corner point 0.
- **leslon1:** East longitude (in degree) of the pixel footprint corner point 1.
- **leslon2:** East longitude (in degree) of the pixel footprint corner point 2.
- **leslon3:** East longitude (in degree) of the pixel footprint corner point 3.
- **leslat0:** North latitude (in degree) of the pixel footprint corner point 0.
- **leslat1:** North latitude (in degree) of the pixel footprint corner point 1.
- **leslat2:** North latitude (in degree) of the pixel footprint corner point 2.
- **leslat3:** North latitude (in degree) of the pixel footprint corner point 3.
- **spacecraft_distance:** Slant distance (in m) from the spacecraft to the pixel footprint center point.
- **therm:** Temperature (in K) at 5 µm at a given longitude and latitude.

**Scalar variables**

- **solarlong:** Areocentric longitude Ls.
- **data_quality:** Data quality ID as defined in EAICD.
- **pointing_mode:** Image acquisition attitude control mode.
- **year:** Martian Year of the observation.
- **pres:** Mask that indicates working channels:
    - pres[0]=1 if C channel is OK,
    - pres[1]=1 if L channel is OK,
    - pres[2]=1 if VIS channel is OK.
- **tag_ok:** Index to indicate that the target is Mars. If tag_ok= 0 => target is not Mars. Otherwise target is Mars.
- **tag_l:** Mask for the L channel; tag_l= 0 means no L channel data.
- **tag_c:** Mask for the C channel: tag_c= 0 means no C channel data.

And other parameters as well.

### .nc file

**Dimensions:**

- **wavelength:** Wavelength in µm. The channel’s wavelengths are ordered as follow: C,L,VIS.
- **pixel_x:** abscissa of the pixel
- **pixel_y:** ordinate of the pixel

**3D cube (wavelength, pixel_x, pixel_y)**

- **Reflectance:** Surface reflectance a given longitude, latitude and wavelength defined as I/F/cos(i) for the three channel. Note that:
    - atmospheric attenuation is corrected (1-5 µm);
    - airborne dust scattering is corrected (0.4-2.5 µm and for 5 µm emissivity estimations);
    - thermal contribution is removed (> 3 µm);
    - channels are co-registered.

**2D variables (pixel_x, pixel_y)**

*Some parameters are detailed in the OMEGA EAICD[^1].*

- **latitude:** Planetocentric latitude (in deg).
- **longitude:** Eastward longitude (in deg), ranges from -180 to 180 degrees.
- **altitude:** Altitude (in m) at a given longitude and latitude (MOLA – ellipsoid as reference).
- **incidence_g:** Incidence angle (in degree) with respect to the outward normal to the reference ellipsoid at a given longitude and latitude.
- **emergence_g:** Emergence angle (in degree) with respect to the outward normal to the reference ellipsoid.
- **incidence_l:** Incidence angle (in degree) with respect to the local normal.
- **watericelin:** The watericelin index value at a given longitude and latitude. This criterion, described in Langevin et al. (2007) is based on the 1.5 μm band depth. It can be used to detect icy frost presence at the surface and thick clouds in the atmosphere. Every OMEGA pixel with a watericelin value < 0.985 should be excluded.
- **icecloudindex:** The icecloud index value at a given longitude and latitude. This criterion (reflectance at 3.4 μm divided by reflectance at 3.52 μm) is described in Langevin et al. (2007) to identify the presence of water ice clouds. Its values range from 0.5 to 1.0. The smallest values unambiguously indicate the presence of icy clouds. We usually exclude any OMEGA pixel with a value < 0.8.
- **hour_at_LTST:** Martian hour at local true solar time LTST of the observation.
- **leslon0:** East longitude (in degree) of the pixel footprint corner point 0.
- **leslon1:** East longitude (in degree) of the pixel footprint corner point 1.
- **leslon2:** East longitude (in degree) of the pixel footprint corner point 2.
- **leslon3:** East longitude (in degree) of the pixel footprint corner point 3.
- **leslat0:** North latitude (in degree) of the pixel footprint corner point 0.
- **leslat1:** North latitude (in degree) of the pixel footprint corner point 1.
- **leslat2:** North latitude (in degree) of the pixel footprint corner point 2.
- **leslat3:** North latitude (in degree) of the pixel footprint corner point 3.
- **spacecraft_distance:** Slant distance (in m) from the spacecraft to the pixel footprint center point.
- **therm:** Temperature (in K) at 5 µm at a given longitude and latitude.

**Scalar variables**

- **solar_longitude:** Areocentric longitude Ls.
- **data_quality:** Data quality ID as defined in EAICD.
- **pointing_mode:** Image acquisition attitude control mode.
- **year:** Martian Year of the observation.
- **pres:** Mask that indicates working channels.
    - pres[0]=1 if C channel is OK,
    - pres[1]=1 if L channel is OK,
    - pres[2]=1 if VIS channel is OK.
- **tag_ok:** Index to indicate that the target is Mars. If tag_ok=0 => target is not Mars. Otherwise target is Mars.
- **tag_l:** Mask for the L channel; tag_l=0 means no L channel data.
- **tag_c:** Mask for the C channel: tag_c=0 means no C channel data.

**Global attributes:**

- **_NCProperties:** "version=1|netcdflibversion=4.4.1.1|hdf5libversion=1.10.1"
- **Conventions:** "CF-1.6"
- **title:** "OMEGA observations acquired with the C, L and VIS channels - Orbit # [number] - Cube # [number]"
- **:history:** "Created [creationdate]" ;
- **institution:** "Institut d\'Astrophysique Spatiale, CNRS et Universite Paris-Sud 11"
- **source:** "surface observation"
- **reference:** The references listed herein-below.
- **cube_number:** "[number]"
- **orbit_number:** "[number]"

## OMEGA C channel projection


These data cubes have been specifically selected and filtered for studies of the surface mineralogy between 1 and 2.5 µm.

They contain all the OMEGA observations acquired with the C channel after filtering. Filtering processes have been implemented to remove some instrumental artefacts and observational conditions. Each OMEGA record is available as a `netCDF4.nc` file and an `idl.sav`.

Both files contain the cubes of reflectance of the surface at a given longitude, latitude and wavelength $\lambda$. The reflectance is defined by the “reflectance factor” $I(\lambda)/(F \cos(i))$ where i is the solar incidence angle with $\lambda$ from 0.97 to 2.55 µm (second dimension of the cube with 120 wavelengths). The spectra are corrected for atmospheric and aerosol contributions according to the method described in Vincendon et al. (Icarus, 251, 2015)[^2]. It therefore corresponds to albedo for a lambertian surface. The first dimension of the cube refers to the length of scan. It can be 32, 64, or 128 pixels. It gives the first spatial dimension. The third dimension refers to the rank of the scan. It is the second spatial dimension.

Much like its predecessor, this collection follows the same pattern. The notable difference is the presence of text files giving ample information on the basic metadata. Since this collection is only limited to OMEGA's C band and since it has lightweight data to rely on, creating a STAC collection is faster and easier than the data cubes one.

### .sav file

- **carte[*,120,*]:** Reflectance of the surface at a given longitude, latitude and wavelength λ.The refectance is defined by the “reflectance factor” I(λ)/(F cos(i)) where i is the solar incidence angle with λ from 0.97 to 2.55 µm (second dimension of the cube with 120 wavelengths). The spectra are corrected for atmospheric and aerosol contributions according to the method described in Vincendon et al. (Icarus, 251, 2015). It therefore corresponds to albedo for a lambertian surface. The first dimension of the cube refers to the length of scan. It can be 16, 32, 64, or 128 pixels. It gives the first spatial dimension.
carte_donnees identifies 5 backplanes by the variable are added to the spectra:
    - **carte_donnees[*,0,*]:** Altitude based on the MOLA topography (in m)
    - **carte_donnees[*,1,*]:** Incidence (in degree) on the ellipsoid at a given longitude and latitude.
    - **carte_donnees[*,2,*]:** Incidence wrt (in degree) of the local gravity at a given longitude and     latitude.
    - **carte_donnees[*,3,*]:** Effective dust opacity at a given longitude and latitude as $\tau_{eff} =\tau_{MER} /\cos i$, where $i$ is the solar incidence angle and $\tau_{MER}$ is the dust opacity    measured by the Mars Exploration Rovers (MERs) during the same solar longitude and Martian year as the     OMEGA observation[^3].
    - **Carte_donnees[*,4,*]:** The watericelin index value at a given longitude and latitude. This     criterion, described in Langevin et al. (2007) is based on the 1.5 μm band depth. It can be used to     detect icy frost presence at the surface and thick clouds in the atmosphere. Every OMEGA pixel with a   watericelin value > 1.5% should be excluded.
    - **Carte_donnees[*,5,*]:** The icecloud index at a given longitude and latitude. This criterion (reflectance at 3.4 μm divided by reflectance at 3.52 μm) is described in Langevin et al. (2007) to identify the presence of water ice clouds. Its values range from 0.5 to 1.0. The smallest values unambiguously indicate the presence of icy clouds. We usually exclude any OMEGA pixel with a value < 0.8.
- **lati:** Planetocentric latitude (in degree). The values of the table correspond to each pixel of the reflectance cube.
- **longi:** Eastward longitude (in degree). The values of the table correspond to each pixel of the reflectance cube.
- **wave:** 1-D table containing the wavelengths (in µm).
- **solarlongi:** Areocentric longitude Ls.
- **max_lat_proj:** Maximum latitude of the reflectance cube.
- **min_lat_proj:** Minimum latitude of the reflectance cube.
- **max_lon_proj:** Easternmost longitude of the reflectance cube.
- **min_lon_proj:** Westernmost longitude of the reflectance cube.

### .nc file

**Dimensions:**

- **wavelength:** Wavelength (in µm).
- **latitude:** Planetocentric latitude (in deg).
- **longitude:** Eastward longitude (in deg).

**3D cube (wavelength, latitude, longitude):**

- **Reflectance:** “reflectance factor” I(λ)/(F cos(i)) where i is the solar incidence angle with λ from 0.97 to 2.55 µm (second dimension of the cube with 120 wavelengths). See above for detailed description.

**2D variables (latitude, longitude)**

- **altitude:** Altitude (in m) at a given longitude and latitude (MOLA – ellipsoid as reference).
- **incidence_g:** Incidence angle (in degree) with respect to the outward normal to the reference ellipsoid at a given longitude and latitude.
- **incidence_n:** ncidence wrt (in degrees) of the local gravity at a given longitude and latitude.
- **tau:** Effective dust opacity at a given longitude and latitude as $\tau_{eff}=\tau_{MER} /\cos i$, where $i$ is the solar incidence angle and $\tau_{MER}$ is the dust opacity measured by the Mars Exploration Rovers (MERs) during the same solar longitude and Martian year as the OMEGA observation[^3].
- **watericelin:** The watericelin index value at a given longitude and latitude. This criterion, described in Langevin et al. (2007) is based on the 1.5 μm band depth. It can be used to detect icy frost presence at the surface and thick clouds in the atmosphere. Every OMEGA pixel with a watericelin value > 1.5% should be excluded.
- **icecloudindex:** The icecloud index value at a given longitude and latitude. This criterion (reflectance at 3.4 μm divided by reflectance at 3.52 μm) is described in Langevin et al. (2007) to identify the presence of water ice clouds. Its values range from 0.5 to 1.0. The smallest values unambiguously indicate the presence of icy clouds. We usually exclude any OMEGA pixel with a value < 0.8.

**Scalar variables**

- **solar_longitude:** Mars-Sun angle, measured from the Northern Hemisphere spring equinox where Ls=0 at the time of measurement.
- **data_quality:** Data quality id as defined in EAICD.
- **start_time:** Time when acquisition starts.
- **stop_time:** Time when acquisition stops.

**Global attributes:**

- **_NCProperties:** "version=1|netcdflibversion=4.4.1.1|hdf5libversion=1.10.1"
- **Conventions:** "CF-1.6"
- **title:** "OMEGA observations acquired with the C channels - Orbit # [number] - Cube # [number]"
- **:history:** "Created [creationdate]" ;
- **institution:** "Institut d\'Astrophysique Spatiale, CNRS et Universite Paris-Sud 11"
- **source:** "surface observation"
- **reference:** the references listed herein below
- **cube_number:** "[number]"
- **orbit_number:** "[number]"


[^1]: [**OMEGA EAICD** (Experiment Archive Interface Control)](https://www.ias.u-psud.fr/omega/documents/EAICD_OMEGA.pdf)
[^2]: **M. Vincendon, J. Audouard, F. Altieri, A. Ody (2015)**, Mars Express measurements of surface albedo changes over 2004–2010, In Icarus, Volume 251, 2015, Pages 145-163, ISSN 0019-1035,
[^3]: Audouard, J., F. Poulet, M. Vincendon, R. E. Milliken, D. Jouglet, J. Bibring, B. Gondet, and Y. Langevin (2014), Water in the Martian regolith from OMEGA/Mars Express, J. Geophys. Res. Planets,119, 1969–1989, [doi:10.1002/2014JE004649](https://doi.org/10.1002%2F2014JE004649)

import logging

from psup_stac_converter.informations.publications import omega_data_cubes
from psup_stac_converter.omega._base import OmegaDataReader
from psup_stac_converter.utils.io import PsupIoHandler


class OmegaDataCubes(OmegaDataReader):
    def __init__(
        self, psup_io_handler: PsupIoHandler, log: logging.Logger | None = None
    ):
        super().__init__(
            psup_io_handler,
            data_type="data_cubes_slice",
            collection_id="urn:pdssp:ias:collection:omega_data_cubes",
            collection_description="""
This dataset contains all the OMEGA observations acquired with the C, L and VIS channels until April 2016, 11, after filtering. Filtering processes have been implemented to remove some instrumental artefacts and observational conditions. Each OMEGA record is available as a `netCDF4.nc` file and an `idl.sav`

Both files contain the cubes of reflectance of the surface at a given longitude, latitude and wavelength $\lambda$. The surface reflectance is defined as $\frac{I(\lambda)}{F \cos(i)}$  where:

- channel $C=[0.93-2.73 \mu m]$; $L=[2.55-5.10 \mu m]$; $\text{Visible}=[0.38-1.05 \mu m]$;
- atmospheric attenuation is corrected (1-5 µm);
- airborne dust scattering is corrected (0.4-2.5 µm and for 5 µm emissivity estimations);
- thermal contribution is removed (> 3 µm); L channel data and VIS channel are co-registered with C channel when available.

Please note that longitudes range from -180 to 180 degrees east.
""",
            publications=omega_data_cubes,
            log=log,
        )

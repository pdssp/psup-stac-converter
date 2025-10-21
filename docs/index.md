# PSUP processor

Processes PSUP catalogs and converts them to STAC.

## Dataset description

This dataset is composed of several categories of value-added ​data (maps, radiometrically corrected data) from space missions in which the OSU are involved. These products are global and local maps of the surface properties (chemical and mineralogical composition, physical properties, ...) and geomorphological landforms (lobate impact craters, scalloped depressions, ...).

### OMEGA mineral maps

PSUP OMEGA mineral maps are OMEGA-based NIR albedo, Ferric BD530, Ferric Nanophase, Olivine SP1, SP2, SP3, Pyroxene and Emissivity at 5.03µm. OMEGA is the VISNIR imaging spectrometer onboard ESA/Mars-Express spacecraft operating around Mars from January 2004. All maps are provided in FITS file format.

### Feature catalogs

PSUP Catalogs are Hydrated mineral terrains, Central peaks hydrated phases between Isidis and Hellas, Central peaks mineralogy south Valles Marineris, Valles Marineris low Calcium-Pyroxene, Seasonal South polar cap limits, Scalloped depressions and Lobate impact craters. This dataset contains vector catalogs and their associated metadatas. All catalogs are provided in JSON file format via the "download" column.

### OMEGA C Channel Proj dataset

These data cubes have been specifically selected and filtered for studies of the surface mineralogy between 1 and 2.5 µm.

They contain all the OMEGA observations acquired with the C channel after filtering. Filtering processes have been implemented to remove some instrumental artefacts and observational conditions. Each OMEGA record is available as a `netCDF4.nc` file and an `idl.sav`.

Both files contain the cubes of reflectance of the surface at a given longitude, latitude and wavelength $\lambda$. The reflectance is defined by the “reflectance factor” $I(\lambda)/(F \cos(i))$ where $i$ is the solar incidence angle with $\lambda$ from 0.97 to 2.55 µm (second dimension of the cube with 120 wavelengths). The spectra are corrected for atmospheric and aerosol contributions according to the method described in [Vincendon et al. (Icarus, 251, 2015)](https://www.sciencedirect.com/science/article/abs/pii/S0019103514005764). It therefore corresponds to albedo for a lambertian surface. The first dimension of the cube refers to the length of scan. It can be 32, 64, or 128 pixels. It gives the first spatial dimension. The third dimension refers to the rank of the scan. It is the second spatial dimension.

### OMEGA data cubes

This dataset contains all the OMEGA observations acquired with the C, L and VIS channels until April 2016, 11, after filtering. Filtering processes have been implemented to remove some instrumental artefacts and observational conditions. Each OMEGA record is available as a `netCDF4.nc` file and an `idl.sav`file.

Both files contain the cubes of reflectance of the surface at a given longitude, latitude and wavelength $\lambda$. The surface reflectance is defined as $I/F/\cos(i)$ where:

* channel C=[0.93-2.73 µm]; L=[2.55-5.10 µm]; Visible=[0.38-1.05 µm];
* atmospheric attenuation is corrected (1-5 µm);
* airborne dust scattering is corrected (0.4-2.5 µm and for 5 µm emissivity estimations);
* thermal contribution is removed (> 3 µm); L channel data and VIS channel are co-registered with C channel when available.

*Please note that longitudes range from -180 to 180 degrees east.*

The availability of value-added data allows their display and scientific analysis in a 3D directly on the visualization interface "Mars Visu".

![mars_visu_img](../img/mars_visu_example.png))

## Features

This project is divided in two parts: a scraper crawling through the inventory and compiling a feed result about each file, from its relative location to its size (in B), and a converter that goes through the required items and turns them into a STAC catalog.

The scraper uses [scrapy](https://www.scrapy.org/) as a library and can extract information on the dataset, as well as WKT projections on [VESPA](https://voparis-vespa-crs.obspm.fr/web/) for several bodies of the solar system.

The converter mostly uses the [pystac](https://pystac.readthedocs.io/en/stable/) library to generate the catalog, the respective collections and their items and assets. The generated catalog will respect the original PSUP dataset organization, and present at least four collections as children items:

- Mars' features dataset
- OMEGA mineral maps
- OMEGA C Channel
- OMEGA data cubes

The data can range from small text and JSON files to ~10GB multidimensional arrays of data. As such, the converter uses a toolset of libraries depending of the case:

* [Geopandas](https://geopandas.org/en/stable/index.html) for GeoJSON
* [Xarray](https://docs.xarray.dev/en/stable/index.html) for multidimensional arrays like NetCDF files
* [Astropy](https://www.astropy.org/) for FITS maps
* [Scipy](https://docs.scipy.org/doc/scipy/reference/io.html) for IDL data
* [Pydantic](https://docs.pydantic.dev/latest/), for data items
* etc...

Data exploration files can be found in `./notebooks`, where each notebook uses the [marimo](https://marimo.io/) library.

## Installation

This project uses [uv](https://docs.astral.sh/uv/) as a dependency manager. First, you'll need to install uv following the instructions on the website, according to your OS. Once uv is working, you can enter the following command to install all the dependencies:

```shell
# Install it without the dependencies
$ uv sync --locked --no-default-groups
```
If everything worked, you can now try the CLI commands for both the scraper and the converter:

**For the converter:**

```console
$ uv run psup-stac --help

 Usage: psup-stac [OPTIONS] COMMAND [ARGS]...

 Utility package to convert PSUP data to STAC format

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --from-config         -c      FILE  Path to a config file (YAML) to load defaults from                                                                                                     │
│ --install-completion                Install completion for the current shell.                                                                                                              │
│ --show-completion                   Show completion for the current shell, to copy it or customize the installation.                                                                       │
│ --help                              Show this message and exit.                                                                                                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ create-stac-catalog    Converts raw input into a STAC catalog. The user must have a scraped CSV file as a feed to rely on, an input folder to store downloaded raw products, and an output │
│                        folder to put the catalog in.                                                                                                                                       │
│ describe-folders       Shows the target folders from config                                                                                                                                │
│ show-wkt-projections   Displays the available WKT projections of the solar system from a WKT CSV file                                                                                      │
│ describe-tif           Displays the metadata from a rasterized image                                                                                                                       │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

```

**For the scraper:**

```console
$ uv run psup-scraper --help

 Usage: psup-scraper [OPTIONS] COMMAND [ARGS]...

 Retrieves metadata available on PSUP (psup.ias.u-psud.fr/sitools/datastorage/user/storage)

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                                                                                                                    │
│ --show-completion             Show completion for the current shell, to copy it or customize the installation.                                                                             │
│ --help                        Show this message and exit.                                                                                                                                  │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ scraper-settings   Show the current scrapy settings (editable in ./src/psup_scraper/settings.py)                                                                                           │
│ get-data-ref       Crawls the data tree to obtain the references, from files, to links, to their actual size in B                                                                          │
│ check-data         Shows a representation of the scraped result in the std console.                                                                                                        │
│ get-wkt-proj       Retrieves VESPA's projections under a CSV file                                                                                                                          │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯



```

!!! tip "Without `uv`"
    You can avoid using `uv run` for simplicity, but you'll need to activate the virtual environment first.


## Config file (YAML) example

The CLI accepts a config file via `--from-config` / `-c`. The settings loader expects keys similar to:

```yaml
settings:
  # The level of logging
  log_level: "DEBUG"
  # Logging formatter
  log_format: "%(asctime)s [%(levelname)s] %(message)s"
  # Where the user keeps their data
  data_path: "./data"
  # Where the raw data can be downloaded
  # Used mostly for relatively lightweight files whose metadata can be extracted and stored "on the fly"
  raw_data_path: "./data/raw"
  # Where the catalog should lie
  output_data_path: "./data/processed"
  # Folder containing anything that can be used as a side material for processing
  extra_data_path: "./data/extra"
  # Contains the scrapped results from the WKT projections
  wkt_file_name: "wkt_solar_system.csv"
  # Contains all the scraped results by using `psup-scraper get-data-ref -O <psup-inventory-file> -f csv --clean`
  psup_inventory_file: "./data/raw/psup_refs.csv"
```
You can find an example from [`converter-params.example.yml`](./converter-params.example.yml)

If you want to use the default configuration, you can simply clone this file and rename it `converter-params.yml`. If you're using a data directory different from the one by default, make sure it's not committed to version control, particularily in feature addition.

Once you're satisfied with your configuration, place the config path when running:

```bash
psup-stac --from-config converter-params.yml <command>
```

## Classical usage

This tool aims at catalog creation based on the indicated resources, either contained in the code or in the scraped data. Therefore, it will need an inventory file of some sorts. The quickest way to create an inventory is to generate a CSV feed using the scraper.

> [!CAUTION]
> The converter as for now can only handle CSV format.

To generate your feed, simply use the following command. Note that the output file's path must be the same as indicated in your `converter-params.yml`file. This is important if you need consistency between the two applications:

```console
$ uv run psup-scraper get-data-ref -O <psup-inventory-file-path-csv> -f csv --clean
```

Once the inventory is created, you can start the conversion process in one go using the following command:

```console
$ uv run psup-stac --from-config converter-params.yml  create-stac-catalog --clean
```

If you don't want to use a configuration file, you can pass the arguments in the CLI like so:

```console
$ uv run psups-stac create-stac-catalog -I <path-to-raw-data> -O <path-to-catalog-results> -l <psup-inventory-file-path-csv> --clean
```
Wait for your catalog to be generated. If something goes wrong in the process, you can restart it by launching the previous command.

## Other commands

**Show input and output folder structure**

```console
$ uv run psup-stac describe-folders -I <path-to-raw-data> -O <path-to-catalog-results>
```

**Show WKT Solar System projections**

```console
$ uv run psup-stac show-wkt-projections <path-to-wkt-file-csv>
```
You can also generate this file using the following command:

```console
$ uv run psup-scraper get-wkt-proj -O <wkt-data-path-csv> -f csv --clean
```

## References

See [References](./references.md) for more information.

---

[PSUP Catalog](http://psup.ias.u-psud.fr/sitools/client-user/index.html?project=PLISonMars)

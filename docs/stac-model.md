# Spatio-Temporal Asset Catalog (STAC)

The STAC structure was created by the OGC in 2023 as a standard language to describe geospatial information under a standard convention everybody uses, to ease up the development tools, browser and server applications centered under time and space data.

STAC data is organized in **items**. STAC items are enriched [GeoJSON](https://geojson.org/) structures encompassing not only the bounding box and the object type, but also a variety of properties:

```json
{
    "stac_version": "1.0.0", // The version of STAC
    "type": "Feature", // The type of object
    "id": "20201211_223832_CS2", // The idea of object
    "bbox": [], //The bounding box
    "geometry": {}, // The geometry of the object (ie. polygons)
    "properties": {}, // Other properties
    "collection": "simple-collection", // The collection it belongs to
    "links": [], // The links contained within
    "assets": {} // The assets
}
```

Items can be sorted and rearranged by **collections**. These collections extend directly the catalog with additional fields of research, like spatial or temporal data, the providers, certain keywords or the license.

```json
{
    "stac_version": "1.0.0",
    "type": "Collection",
    "license": "ISC",
    "id": "20201211_223832_CS2",
    "description": "A simple collection example",
    "links": [],
    "extent": {},
    "summaries": {}
}
```

The STAC API is a simple endpoint called `/stac/search`, that accepts spatial and temporal coordinates.

* `bbox` (tuple of 4 floats): In order, WSEN (West-South-East-North)
* `time` (ISO format timestamp/ISO format timestamp): asks for items from/to the selected dates.
* `limit` (number, optional): the limit of objects requested
* `page`(number, optional): the number of the page, defaults to the first page
The response is a GeoJSON `FeatureCollection`, STAC-compliant.

STAC can also load extensions. The list of extensions is found [on the stac-extensions website](https://stac-extensions.github.io/). Whenever a catalogue is using an extension, the name must be specified in the field to avoid confusion (ex. `extension:field`). Users can submit their extensions following the instructions [on their Github page](https://github.com/stac-extensions/stac-extensions.github.io#using-the-stac-extensions-template).

STAC catalogues lie at the top of hierarchy and can be divided in two types :

* **Static catalogues:** implemented as a set of flat files on a FTP service, a web server or a datalake like S3, Azure Storage, Google Cloud Storage, etc...
* **Dynamic catalogues:** generate their responses dynamically, backed by a server, like Planet and DigitalGlobe who already own a curated list of items, through their own API
STAC specs were designed so that it can be used as a layer of abstraction between the two.

## STAC standardization process

Most of the process follows the STAC best practices [available in the corresponding Github repo](https://github.com/radiantearth/stac-spec/blob/master/best-practices.md).

Usually it's best to automate the process using a programming language, like Python or R. Several tools coded with these languages are available at [stac-utils](https://github.com/stac-utils). These modules support primarily Python and Javascript but they're also available for other tools, like PotsgreSQL, the JVM, Rust or a CLI.

Among the tools, [pystac](https://github.com/stac-utils/pystac) is the most developed and used so far, since it allows catalog generation with ease. It's a Python package using its own ORM to generate catalog samples, all while being straightforward to use.

## Using extensions

 STAC extensions allows the items in the collection to have some unique attributes depending of the context, which allows better classification. It is one step above common metadata, in the sense that they give the item more concrete attributes.

Common extensions include

* **EO:** electro-optical observations, like the cloud coverage or the number of bands
* **View:** takes account of the angles of view, like the incident angle
* **Proj:** the type of CRS used for the projection
* **Raster:** provides information in rasterized images
* **Contact:** information on the contact
* **Scientific:** whether the objects are the source or complementary material of a scientific article

Using extensions on their own is fairly easy, as long as **the extension exists** and **the fields are properly referenced**, which is necessary to pass the lint check. Using an ORM just like `pystac` automates the process. However, it is not without risk: some of the extensions may be outdated. But implementing them should be fairly easy, as long as the nomenclature is respected, as evidenced by [pystac's EO extension](https://github.com/stac-utils/pystac/blob/main/pystac/extensions/eo.py) and this tutorial on [how to create a custom extension using pystac](https://pystac.readthedocs.io/en/stable/tutorials/adding-new-and-custom-extensions.html).

For planets, there's only one extension called [Solar System (`ssys`)](https://github.com/stac-extensions/ssys) that specifies on which Solar System body the item is located.

The projection extension is quite tricky. At first, it was used for the Earth System, but the OBSPM managed to create codes for sphere and projection coordinates for each solar system body. This repo contains the [WKT table of several bodies of the Solar System](../data/wkt_solar_system.csv). Naturally for images, it will boil down to **the level of processing** and for the features, their imagery of reference, including projection.

## Storage

The typical storage of a STAC catalog is within a datalake, like AWS's S3 or Azure's ABS (Azure Blob Storage). Hosting the files locally is also a possibility, but sharing them will eventually require some form of FTP. Besides, if the catalog is static, the best place needs to reference some assets, like TIF files, which are heavy in terms of storage.

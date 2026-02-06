import marimo

__generated_with = "0.19.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pystac
    from pathlib import Path
    from pystac.extensions.datacube import DatacubeExtension

    return Path, mo, pystac


@app.cell
def _(Path, pystac):
    catalog = pystac.Catalog.from_file(
        Path.home() / "PDSSP/psup-stac-repo/catalog/catalog.json"
    )
    catalog.describe()
    return (catalog,)


@app.cell
def _(catalog, mo, pystac):
    mo.md(f"""
    **ID:** `{catalog.id}`

    **Title:** {catalog.title or "N/A"}"

    **Description:** {catalog.description or "N/A"}

    ----
    Created with STAC v{pystac.get_stac_version()}
    """)
    return


@app.cell
def _(catalog):
    collections = list(catalog.get_collections())

    print(f"Number of collections: {len(collections)}")
    print("Collections IDs:")
    for collection in collections:
        print(f"- {collection.id}")
        if collection is None:
            print("\tCollection is Empty. Check your downloads and try again.")
        else:
            subcollections = collection.get_children()
            for subcollection in subcollections:
                print(f"\t- {subcollection.id}")
    return


@app.cell
def _(catalog, pystac):
    for _item in catalog.get_all_items():
        try:
            _item.validate()
        except pystac.errors.STACValidationError as e:
            print(f"{_item.id} is invalid")
            print(e)
            # print("==========================")
            # if DatacubeExtension.has_extension(_item):
            #     cube_item = DatacubeExtension.ext(_item)
            #     print(cube_item.dimensions)
            print("========================== =============================")
        else:
            pass
            # print("Valid!")
    return


@app.cell
def _(catalog):
    catalog.validate_all()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

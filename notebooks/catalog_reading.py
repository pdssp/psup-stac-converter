import marimo

__generated_with = "0.15.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pystac

    return mo, pystac


@app.cell
def _(pystac):
    catalog = pystac.Catalog.from_file("./data/processed/catalog.json")
    catalog.describe()
    return (catalog,)


@app.cell
def _(catalog, mo, pystac):
    mo.md(
        f"""
    **ID:** `{catalog.id}`

    **Title:** {catalog.title or "N/A"}"

    **Description:** {catalog.description or "N/A"}

    ----
    Created with STAC v{pystac.get_stac_version()}
    """
    )
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
def _(catalog):
    items = list(catalog.get_all_items())

    print(f"Number of items: {len(items)}")
    for item in items:
        print(f"- {item.id}")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

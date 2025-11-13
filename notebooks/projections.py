import marimo

__generated_with = "0.15.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    from pystac.extensions.projection import ProjectionExtension
    from pydantic import BaseModel
    import datetime as dt
    from psup_stac_converter.utils.io import WktIoHandler

    return (WktIoHandler,)


@app.cell
def _(WktIoHandler):
    wkt_io_handler = WktIoHandler("./data/extra/wkt_solar_system.csv")
    wkt_io_handler.pick_sphere_projection_by_body_and_kind("Mars", "ocentric")
    return


@app.cell
def _():
    from stac_validator import stac_validator

    stac = stac_validator.StacValidate("./data/processed/catalog.json", extensions=True)
    stac.run()
    stac.message
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

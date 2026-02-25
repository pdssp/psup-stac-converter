import json
from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from astropy.io import fits
from attr import asdict
from PIL import Image
from rasterio.transform import from_gcps
from rich.console import Console

console = Console()


def infos_from_tif(
    tif_file: Path,
    verbose: bool = False,
    aspect: Literal["meta", "tags"] = "meta",
    meta_member: Literal["subdatasets", "stats", "checksum"] | None = None,
    indent: int = 2,
    bidx: int = 1,
    namespace: str = "",
):
    """Shows information on a rastrized file on the standard console

    Args:
        tif_file (Path): _description_
        verbose (bool, optional): _description_. Defaults to False.
        aspect (Literal[&quot;meta&quot;, &quot;tags&quot;], optional): _description_. Defaults to "meta".
        meta_member (Literal[&quot;subdatasets&quot;, &quot;stats&quot;, &quot;checksum&quot;] | None, optional): _description_. Defaults to None.
        indent (int, optional): _description_. Defaults to 2.
        bidx (int, optional): _description_. Defaults to 1.
        namespace (str, optional): _description_. Defaults to "".
    """
    console.print(tif_file)
    with rasterio.open(tif_file) as src:
        info = dict(src.profile)
        info["shape"] = (info["height"], info["width"])
        info["bounds"] = src.bounds
        if src.crs:
            epsg = src.crs.to_epsg()
            if epsg:
                info["crs"] = f"EPSG:{epsg}"
            else:
                info["crs"] = src.crs.to_string()
        else:
            info["crs"] = None

        info["res"] = src.res
        info["colorinterp"] = [ci.name for ci in src.colorinterp]
        info["units"] = [units or None for units in src.units]
        info["descriptions"] = src.descriptions
        info["indexes"] = src.indexes
        info["mask_flags"] = [
            [flag.name for flag in flags] for flags in src.mask_flag_enums
        ]

        if src.crs:
            info["lnglat"] = src.lnglat()

        gcps, gcps_crs = src.gcps

        if gcps:
            info["gcps"] = {"points": [p.asdict() for p in gcps]}
            if gcps_crs:
                epsg = gcps_crs.to_epsg()
                if epsg:
                    info["gcps"]["crs"] = f"EPSG:{epsg}"
                else:
                    info["gcps"]["crs"] = src.crs.to_string()
            else:
                info["gcps"]["crs"] = None

            info["gcps"]["transform"] = from_gcps(gcps)

        if verbose:
            stats = [asdict(so) for so in src.stats()]
            info["stats"] = stats
            info["checksum"] = [src.checksum(i) for i in src.indexes]

        if aspect == "meta":
            if meta_member == "subdatasets":
                console.print("Subdatasets:")
                for name in src.subdatasets:
                    console.print(name)
            elif meta_member == "stats":
                st = src.statistics(bidx)
                console.print("Statistics:")
                console.print("{st.min} {st.max} {st.mean} {st.std}".format(st=st))
            elif meta_member == "checksum":
                console.print(f"Checksum: {src.checksum(bidx)}")
            elif meta_member:
                if isinstance(info[meta_member], (list, tuple)):
                    console.print("\n" + " ".join(map(str, info[meta_member])))
                else:
                    console.print("\n" + str(info[meta_member]))
            else:
                console.print_json(json.dumps(info, sort_keys=True, indent=indent))

        elif aspect == "tags":
            console.print_json(json.dumps(src.tags(ns=namespace), indent=indent))


def fits_header_to_dict(
    fits_file: Path, channel_n: int = 0, lowercase: bool = False
) -> dict[str, int | float | str]:
    if not fits_file.exists():
        raise FileNotFoundError(f"{fits_file} doesn't exist")
    fits_obj = {}

    with fits.open(fits_file) as hdul:
        for header_key, header_val in hdul[channel_n].header.items():
            if header_key == "":
                continue

            if lowercase:
                header_key = header_key.lower()

            fits_obj[header_key] = header_val

    return fits_obj


def convert_arr_to_thumbnail(
    data: np.ndarray,
    resize_dims: tuple[int, int],
    mode: Literal["L", "RGB", "RGBA"] = "L",
    cmap: str | None = None,
) -> Image.Image:
    """
    Converts a 2D or 3D NumPy array into a resized PNG-style image.
    Applies a matplotlib colormap if provided.
    """

    # Normalizes data between 0 and 1
    result = np.asarray(data, dtype=float)

    result_min = np.nanmin(result[~np.isneginf(result)])
    result_max = np.nanmax(result[~np.isposinf(result)])
    if np.isnan(result_max) or np.isnan(result_min):
        raise ValueError(
            f"Seems like the array's size is NaN (min={result_min}, max={result_max})"
        )

    result = (result - result_min) / (result_max - result_min + 1e-8)

    if cmap is not None:
        cm = plt.get_cmap(cmap)
        result = cm(result)[..., :4]  # includes alpha
        result = (result * 255).astype(np.uint8)
        if mode == "RGB":
            result = result[..., :3]
    else:
        result = (result * 255).astype(np.uint8)
        # Turn a 1-band image into a RGB or RGBA image
        if mode in ["RGB", "RGBA"] and result.ndim == 2:
            result = np.stack([result] * (3 if mode == "RGB" else 4), axis=-1)
        elif result.ndim == 3 and result.shape[-1] == 3:
            if mode == "RGBA":
                alpha = np.full((*result.shape[:2], 1), 255, dtype=result.dtype)
                result = np.concatenate([result, alpha], axis=-1)

    img = Image.fromarray(result, mode=mode)
    img = img.resize(resize_dims, Image.Resampling.LANCZOS)

    return img

import json
from pathlib import Path
from typing import Literal

import rasterio
from attr import asdict
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

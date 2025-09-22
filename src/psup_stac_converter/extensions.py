import pystac

from psup_stac_converter.stac_extra.ssys_extension import (
    SCHEMA_URI,
    SolSysExtension,
    SolSysTargetClass,
)

type StacInstance = pystac.Catalog | pystac.Collection | pystac.Item


def apply_ssys(
    stac_instance: StacInstance, mars_local_time: str | None = None
) -> StacInstance:
    if isinstance(stac_instance, pystac.Item):
        ssys = SolSysExtension.ext(stac_instance, add_if_missing=True)
        ssys.apply(
            targets=["mars"],
            target_class=SolSysTargetClass.PLANET,
            local_time=mars_local_time,
        )

    elif isinstance(stac_instance, pystac.Collection):
        # Adding SSYS extension
        ssys = SolSysExtension.summaries(stac_instance, add_if_missing=True)
        ssys.targets = ["mars"]
        ssys.target_class = SolSysTargetClass.PLANET

    elif isinstance(stac_instance, pystac.Catalog):
        stac_instance.stac_extensions.append(SCHEMA_URI)
        stac_instance.extra_fields["ssys:targets"] = ["mars"]
        stac_instance.extra_fields["ssys:target_class"] = SolSysTargetClass.PLANET.value

    return stac_instance

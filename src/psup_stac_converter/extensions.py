import pystac
from pystac.extensions.eo import Band, EOExtension
from pystac.extensions.scientific import Publication, ScientificExtension

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


def apply_sci(
    stac_instance: StacInstance, publications: Publication | list[Publication]
) -> StacInstance:
    if isinstance(stac_instance, pystac.Item):
        publications = (
            [publications] if not isinstance(publications, list) else publications
        )

        sci = ScientificExtension.ext(stac_instance, add_if_missing=True)
        sci.apply(publications=publications)
    elif isinstance(stac_instance, pystac.Collection):
        sci = ScientificExtension.summaries(stac_instance, add_if_missing=True)
        if isinstance(publications, list):
            stac_instance.extra_fields["sci:publications"] = publications
        else:
            sci.citation = publications.citation
            sci.doi = publications.doi

    elif isinstance(stac_instance, pystac.Catalog):
        pass
    return stac_instance


# TODO: proj
def apply_proj(stac_instance: StacInstance) -> StacInstance:
    pass


def apply_eo(stac_instance: StacInstance, bands=list[Band]) -> StacInstance:
    if isinstance(stac_instance, pystac.Item) or isinstance(
        stac_instance, pystac.Asset
    ):
        eo = EOExtension.ext(stac_instance, add_if_missing=True)
        eo.apply(bands=bands)
    elif isinstance(stac_instance, pystac.Collection):
        eo = EOExtension.summaries(stac_instance, add_if_missing=True)
        eo.bands = bands
    return stac_instance

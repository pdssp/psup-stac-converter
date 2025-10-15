import pystac

providers = [
    pystac.Provider(
        name="Institut d'Astrophysique Spatiale (IAS) - IDOC",
        description="The Integrated Data and Operation Center (IDOC) is responsible for processing, archiving\nand distributing data from space science missions in which the IAS institute is involved.\n",
        roles=[
            pystac.ProviderRole.PROCESSOR,
            pystac.ProviderRole.PRODUCER,
            pystac.ProviderRole.HOST,
        ],
        url="https://idoc.ias.universite-paris-saclay.fr",
    ),
    pystac.Provider(
        name="Géosciences Paris-Saclay (GEOPS)",
        description='GEOPS is a joint laboratory of the \u201cUniversit\u00e9 de Paris-Sud\u201d (UPSUD) and the "Centre National\nde la Recherche Scientifique" (CNRS).\n',
        roles=[
            pystac.ProviderRole.PROCESSOR,
            pystac.ProviderRole.PRODUCER,
        ],
        url="http://geops.geol.u-psud.fr",
    ),
    pystac.Provider(
        name="Planetary SUrface Portal (PSUP)",
        description="PSUP is a french research service, by Observatoire Paris-Sud and Observatoire de Lyon, to help\nthe distribution of high added-value datasets of planetary surfaces.\n",
        roles=[
            pystac.ProviderRole.LICENSOR,
        ],
        url="https://psup.cnrs.fr",
    ),
]

from pydantic import BaseModel, ConfigDict
from pystac.extensions.scientific import Publication
from shapely import Polygon


class GeoJsonFeaturesDesc(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # do not use FilePath because the file might not exist
    name: str
    description: str
    footprint: Polygon
    keywords: list[str]
    publications: Publication


geojson_features = {
    "hyd_global_290615.json": GeoJsonFeaturesDesc(
        name="hyd_global_290615.json",
        **{
            "description": "Hydrated mineral sites",
            "footprint": Polygon(((-180, -90), (-180, 90), (180, 90), (180, -90))),
            "keywords": [],
            "publications": Publication(
                citation="Carter, J., F. Poulet, J.-P. Bibring, N. Mangold, and S. Murchie (2013), Hydrous minerals on Mars as seen by the CRISM and OMEGA imaging spectrometers: Updated global view, J. Geophys. Res. Planets, 118, 831–858",
                doi="doi: 10.1029/2012JE004145",
            ),
        },
    ),
    "detections_crateres_benjamin_bultel_icarus.json": GeoJsonFeaturesDesc(
        name="detections_crateres_benjamin_bultel_icarus.json",
        **{
            "description": "Central peaks hydrated phases between isidis and hellas",
            "footprint": Polygon(((65, -19), (135.5, -19), (135.5, -2), (65, -2))),
            "keywords": [],
            "publications": Publication(
                citation="B. Bultel, C. Quantin-Nataf, M. Andréani, H. Clénet, L. Lozac’h (2015), Deep alteration between Hellas and Isidis Basins, In Icarus Volume 260, 2015, Pages 141-160",
                doi="doi:10.1016/j.icarus.2015.06.037",
            ),
        },
    ),
    "lcp_flahaut_et_al.json": GeoJsonFeaturesDesc(
        name="lcp_flahaut_et_al.json",
        **{
            "description": "Central peaks mineralogy south Valles Marineris",
            "footprint": Polygon(((-62, -16), (-37, -16), (-37, -4), (-62, -4))),
            "keywords": [],
            "publications": Publication(
                citation="C. Quantin, J. Flahaut, H. Clenet, P. Allemand, P. Thomas (2012), Composition and structures of the subsurface in the vicinity of Valles Marineris as revealed by central uplifts of impact craters, Icarus, Volume 221, Issue 1, 2012, Pages 436-452",
                doi="doi:10.1016/j.icarus.2012.07.031",
            ),
        },
    ),
    "lcp_vmwalls.json": GeoJsonFeaturesDesc(
        name="lcp_vmwalls.json",
        **{
            "description": "Valles Marineris low Calcium-Pyroxene",
            "footprint": Polygon(((-63, -16), (-37, -16), (-37, -4), (-63, -4))),
            "keywords": [],
            "publications": Publication(
                citation="J. Flahaut, C. Quantin, H. Clenet, P. Allemand, J. F. Mustard, P. Thomas (2012), Pristine Noachian crust and key geologic transitions in the lower walls of Valles Marineris: Insights into early igneous processes on Mars, In Icarus, Volume 221, Issue 1, 2012, Pages 420-435",
                doi="doi:10.1016/j.icarus.2011.12.027",
            ),
        },
    ),
    "crocus_ls150-310.json": GeoJsonFeaturesDesc(
        name="crocus_ls150-310.json",
        **{
            "description": "Seasonal South polar cap limits",
            "footprint": Polygon(((-180, -90), (180, -90), (180, -50), (-180, -50))),
            "keywords": [
                "polar  cap",
                "seasonal",
                "south",
                "CO2",
                "crocus line",
                "inner crocus line",
                "outer crocus line",
                "snowdrop  distance",
            ],
            "publications": Publication(
                citation="F. Schmidt, B. Schmitt, S. Douté, F. Forget, J.-J. Jian, P. Martin, Y. Langevin, J.-P. Bibring (2010), Sublimation of the Martian CO2 Seasonal South Polar Cap, In Planetary and Space Science, Volume 58, Issues 10, 2010, Pages 1129-1138",
                doi="doi:10.1016/j.pss.2010.03.018",
            ),
        },
    ),
    "scalloped_depression.json": GeoJsonFeaturesDesc(
        name="scalloped_depression.json",
        **{
            "description": "Scalloped depressions",
            "footprint": Polygon(((75, 39), (75, 52), (109, 52), (109, 39))),
            "keywords": [
                "northern  plains",
                "periglacial",
                "thermokarst",
                "ground ice",
            ],
            "publications": Publication(
                citation="A.Séjourné, F.Costard, J.Gargani, R.J.Soare, C.Marmo (2012), Evidence of an eolian ice-rich and stratified permafrost in Utopia Planitia, Mars, In Icarus, Volume 60, Issue 1, 2012, Pages 248-254",
                doi="doi:10.1016/j.pss.2011.09.004",
            ),
            "acknowledgements": "Authors are funded by the Programme Nationale de Planétologie of Institut National des Sciences de l'Univers. We acknowledge the HiRISE Team and the Orsay Planetary Picture Library as well as the HRSC Team for the data provided (http://fototek.geol.u-psud.fr/). Special thanks to Indiana Romaire for the help estimating the dip using ArcGIS.",
        },
    ),
    "costard_craters.json": GeoJsonFeaturesDesc(
        name="costard_craters.json",
        **{
            "description": "Lobate impact craters",
            "footprint": Polygon(((-180, -90), (-180, 90), (180, 90), (180, -90))),
            "keywords": ["global", "craters", "ejecta", "lithosphere"],
            "publications": Publication(
                citation="F.M Costard (1989), The spatial distribution of volatiles in the Martian hydrolithosphere, Earth Moon Planet, Volume 45, Pages 265-290.",
                doi="doi:10.1007/BF00057747",
            ),
        },
    ),
}

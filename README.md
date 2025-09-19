# PSUP processor

Processes the catalogs

# Description of the dataset


PSUP Catalogs are Hydrated mineral terrains, Central peaks hydrated phases between Isidis and Hellas, Central peaks mineralogy south Valles Marineris, Valles Marineris low Calcium-Pyroxene, Seasonal South polar cap limits, Scalloped depressions and Lobate impact craters. This dataset contains vector catalogs and their associated metadatas. All catalogs are provided in JSON file format via the "download" column.

Each Catalog is also visible in 3D over Martian surface via the PSUP module "Mars Visu".


## References

- **Hydrated mineral terrains:** Carter, J., F. Poulet, J.‐P. Bibring, N. Mangold, and S. Murchie (2013), Hydrous minerals on Mars as seen by the CRISM and OMEGA imaging spectrometers: Updated global view, J. Geophys. Res. Planets, 118, 831–858, [doi: 10.1029/2012JE004145](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2012JE004145).
- **Central peaks hydrated phases between Isidis and Hellas:** B. Bultel, C. Quantin-Nataf, M. Andréani, H. Clénet, L. Lozac’h (2015), Deep alteration between Hellas and Isidis Basins, In Icarus Volume 260, 2015, Pages 141-160, [doi:10.1016/j.icarus.2015.06.037](https://www.sciencedirect.com/science/article/abs/pii/S0019103515002894)
- **Central peaks mineralogy south Valles Marineris:** C. Quantin, J. Flahaut, H. Clenet, P. Allemand, P. Thomas (2012), Composition and structures of the subsurface in the vicinity of Valles Marineris as revealed by central uplifts of impact craters, Icarus, Volume 221, Issue 1, 2012, Pages 436-452, [doi:10.1016/j.icarus.2012.07.031](https://www.sciencedirect.com/science/article/abs/pii/S0019103512003077).
- **Valles Marineris low Calcium-Pyroxene deposits:** J. Flahaut, C. Quantin, H. Clenet, P. Allemand, J. F. Mustard, P. Thomas (2012), Pristine Noachian crust and key geologic transitions in the lower walls of Valles Marineris: Insights into early igneous processes on Mars, In Icarus, Volume 221, Issue 1, 2012, Pages 420-435, [doi:10.1016/j.icarus.2011.12.027](https://www.sciencedirect.com/science/article/abs/pii/S0019103512000140)
- **Seasonal South polar cap limits:** F. Schmidt, B. Schmitt, S. Douté, F. Forget, J.-J. Jian, P. Martin, Y. Langevin, J.-P. Bibring (2010), Sublimation of the Martian CO2 Seasonal South Polar Cap, In Planetary and Space Science, Volume 58, Issues 10, 2010, Pages 1129-1138, [doi:10.1016/j.pss.2010.03.018](https://www.sciencedirect.com/science/article/pii/S0032063310001005).
- **Scalloped depressions:** A.Séjourné, F.Costard, J.Gargani, R.J.Soare, C.Marmo (2012), Evidence of an eolian ice-rich and stratified permafrost in Utopia Planitia, Mars, In Icarus, Volume 60, Issue 1, 2012, Pages 248-254, [doi:10.1016/j.pss.2011.09.004](https://www.sciencedirect.com/science/article/pii/S0032063311002790).
- **Lobate impact craters:** F.M Costard (1989), The spatial distribution of volatiles in the Martian hydrolithosphere, Earth Moon Planet, Volume 45, Pages 265-290. [doi:10.1007/BF00057747](https://link.springer.com/article/10.1007%2FBF00057747).



# Useful commands

**Generate a catalog**

```shell
$ uv run psup-stac create-stac-catalog hyd_global-290615.json -md ./data/raw/vector.csv -I ./data/raw/catalogs -O ./data/processed --clean
```


**Preview the contents**

```shell
$ uv run psup-stac preview-data -md ./data/raw/vector.csv --catalog ./data/raw/catalogs 
```



---
[PSUP Catalog](http://psup.ias.u-psud.fr/sitools/client-user/index.html?project=PLISonMars)

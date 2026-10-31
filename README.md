# In the shadow of the volcano

Every Holocene volcano in the Smithsonian Institution's Global Volcanism Program (GVP) database, Volcanoes of the World, on one map, with the number of people living within 5, 10, 30 and 100 km of each and the date of its last eruption: 1,215 volcanoes and 9,918 confirmed eruptions. Because many people live near more than one volcano, the study gives a firm lower bound (each person counted once) beside the simple sum.

Interactive page: https://maps.tristanhotham.com/volcano-neighbours/
Paper: https://doi.org/10.5281/zenodo.23847550
Blog post: https://blog.tristanhotham.com/2026/10/31/volcano-neighbours/

## Headline results

- At least 52.9 million people live within 10 km of a Holocene volcano (simple sum 56.4 million), at least 147.5 million within 30 km (sum 273.5 million) and at least 532.4 million within 100 km (sum 2.47 billion, which counts many people several times).
- Indonesia has at least 41.8 million people within 30 km of its 101 volcanoes, 28% of the world lower bound, followed by Mexico (18.7 million), Japan (10.1 million), the Philippines (9.7 million), Italy (8.2 million) and Taiwan (6.7 million).
- 76 volcanoes have a million or more people within 30 km. The most crowded are the Tatun Volcanic Group beside Taipei (6.7 million), Michoacán-Guanajuato in Mexico (5.8 million), Tangkuban Parahu above Bandung (5.7 million), Penanggungan (4.6 million) and Merapi (4.3 million); Vesuvius has 3.9 million.
- 231 volcanoes have erupted since 2000; 21 of them have a million or more people within 30 km, led by Tangkuban Parahu, Merapi, Slamet, Pacaya and Taal. At least 84.4 million people live within 30 km of a volcano that has erupted since 1900.
- Recorded eruptions rose 8.8 times from the 1600s to the 1900s, but eruptions of VEI 4 or more only 2.0 times: the rising curve is mostly better reporting.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded). |
| `header.png` | Social card, 1200 x 630. |
| `data/volcanoes.csv` | All 1,215 Holocene volcanoes: GVP attributes, last known eruption and its class, population within 5, 10, 30 and 100 km, eruption counts, largest VEI (340 KB). |
| `data/volcanoes_by_population.csv` | The 1,209 volcanoes with population figures, sorted by people within 30 km. |
| `data/eruptions.csv` | The 9,918 confirmed Holocene eruptions in VOTW 5.3.5 (975 KB). |
| `data/countries.csv` | Per country: volcanoes, recent eruptions, lower bound and sum of people within 10, 30 and 100 km, most crowded volcano. |
| `data/eruptions_by_century.csv` | Eruptions per century, of VEI 4 or more, dated by observation. |
| `data/results.json` | Every number used in the page, paper, blog and collage. |
| `data/page/` | Page data: volcanoes, countries, Natural Earth outlines and city names, plate boundaries. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures, blog post, figures and meta, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots from the Playwright check at 1280 px and 390 px. |

## Method in brief

- Volcano list: GVP Holocene volcano list, VOTW 5.3.5 (export header: downloaded 2026). Eruption list: GVP confirmed Holocene eruptions, VOTW 5.3.5 (downloaded 2026). Both from public GitHub copies identified by their headers (sources below).
- Populations: current GVP exports no longer include them, so the population within 5, 10, 30 and 100 km comes from the GVP list of VOTW 5.1.7, joined by volcano number (6 newer volcanoes have none). The figures are identical to a GVP export of 2020: a fixed snapshot of unstated year. For 16 volcanoes, mostly large volcanic fields, the figure is the same at 10 and 30 km; they are flagged.
- Lower bound: sort volcanoes by population within r km and keep each one more than 2r km from every volcano already kept; their circles do not overlap, so their populations sum to a true lower bound on distinct people. The simple sum is the upper bound. The same is done per country (a border volcano counts for both countries) and per group of last eruption.
- Last eruption is the GVP's last known eruption (the end of a long eruption, or the present year if continuing).
- Caveats: distance is not hazard; the population snapshot predates recent growth; the lower bound is loose at 100 km; eruption counts in the past are incomplete.

## How to rerun

Needs Python 3 with numpy, pandas, shapely, pyproj, matplotlib, openpyxl, fontTools and Pillow, xelatex and pdftotext, and Node with Playwright for the QA script. Raw inputs are read in place (paths and provenance in `code/common.py`) from `/home/claude/newdata/raw2/volcano/` and Natural Earth files in `/home/claude/newdata/raw/geo/`. Intermediates go to `/dev/shm/volcano` (set `VOLCTMP` to change).

```
python3 code/01_clean.py        # read and join the GVP lists, NCEI deaths
python3 code/02_analyse.py      # results.json and derived tables
python3 code/03_page_data.py    # page data
python3 code/04_build_site.py   # index.html
python3 code/05_figures.py      # header, paper and blog figures
python3 code/06_paper.py        # paper PDF
python3 code/07_readme.py       # README and licences
python3 reddit/collage.py       # collage
python3 code/08_release.py      # blog post, Zenodo files
node code/12_qa.js              # screenshots and console check
```

## Sources and licences

- Global Volcanism Program, 2025. Volcanoes of the World (v. 5.3.5). Distributed by Smithsonian Institution, compiled by Venzke, E. https://volcano.si.edu/ (accessed via the named GitHub mirrors). Volcano list (copy: https://github.com/bciupak/Wizualizacja-Danych-Projekty) and eruption list (copy: https://github.com/im-hana-s/ML-mini-project, `data/raw/gvp_eruption_list.xlsx`).
- Global Volcanism Program, 2024. Volcanoes of the World (v. 5.1.7). Distributed by Smithsonian Institution, compiled by Venzke, E. Population snapshot. https://volcano.si.edu/ (accessed via the named GitHub mirrors). Population columns (copy: https://github.com/Matteo2979/Volcano-Analysis, `GVP_Volcano_List.csv`).
- GVP data are used under the Smithsonian's terms of use (https://volcano.si.edu/gvp_termsofuse.cfm): non-commercial use with credit; no open licence. The tables in `data/` derived from them keep those terms (see `data/LICENSE`). This work is not endorsed by the Smithsonian Institution.
- NOAA NCEI/WDS Global Significant Volcanic Eruptions Database, doi:10.7289/V5JW8BSH (US Government, public domain); eruptions with deaths, copy of 2024 from the same Matteo2979 repository.
- Bird, P. (2003) An updated digital model of plate boundaries. G3 4(3), 1027. GeoJSON by Hugo Ahlenius, Nordpil (https://github.com/fraxen/tectonicplates), Open Data Commons Attribution License 1.0.
- Natural Earth countries and populated places (public domain). Base map tiles on the page: © Esri.

Text and figures are CC BY 4.0 (figures show GVP-derived values, credited above); code is MIT (see `LICENSE`).

## Citation

Hotham, T. (2026) In the shadow of the volcano: how many people live near the world's Holocene volcanoes, from the Smithsonian's Volcanoes of the World. Zenodo. https://doi.org/10.5281/zenodo.23847550

Please also cite the GVP database: Global Volcanism Program, 2025. Volcanoes of the World (v. 5.3.5). Distributed by Smithsonian Institution, compiled by Venzke, E. https://volcano.si.edu/ (accessed via the named GitHub mirrors)

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.

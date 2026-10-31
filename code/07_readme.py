"""README.md, LICENSE and data/LICENSE, with every number from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
G = R["glob"]; c = R["c"]
M = lambda v: mfmt(v)
size = lambda f: f"{os.path.getsize(os.path.join(ROOT, f)) // 1024} KB"
t30 = R["top30"]
readme = f"""# In the shadow of the volcano

Every Holocene volcano in the Smithsonian Institution's Global Volcanism Program (GVP) database, Volcanoes of the World, on one map, with the number of people living within 5, 10, 30 and 100 km of each and the date of its last eruption: {R['n_volc']:,} volcanoes and {R['n_erupt']:,} confirmed eruptions. Because many people live near more than one volcano, the study gives a firm lower bound (each person counted once) beside the simple sum.

Interactive page: {URL}
Paper: https://doi.org/{{10.5281/zenodo.23847550}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/volcano-neighbours/}}

## Headline results

- At least {M(G['10']['floor'])} people live within 10 km of a Holocene volcano (simple sum {M(G['10']['sum'])}), at least {M(G['30']['floor'])} within 30 km (sum {M(G['30']['sum'])}) and at least {M(G['100']['floor'])} within 100 km (sum {M(G['100']['sum'])}, which counts many people several times).
- Indonesia has at least {M(c['IDN']['floor30'])} people within 30 km of its {c['IDN']['n']} volcanoes, {R['idn_share_floor30']:.0f}% of the world lower bound, followed by Mexico ({M(c['MEX']['floor30'])}), Japan ({M(c['JPN']['floor30'])}), the Philippines ({M(c['PHL']['floor30'])}), Italy ({M(c['ITA']['floor30'])}) and Taiwan ({M(c['TWN']['floor30'])}).
- {R['n30_1m']} volcanoes have a million or more people within 30 km. The most crowded are the Tatun Volcanic Group beside Taipei ({M(t30[0]['p30'])}), Michoacán-Guanajuato in Mexico ({M(t30[1]['p30'])}), Tangkuban Parahu above Bandung ({M(t30[2]['p30'])}), Penanggungan ({M(t30[3]['p30'])}) and Merapi ({M(t30[4]['p30'])}); Vesuvius has {M(R['v']['vesuvius']['p30'])}.
- {R['by_ecls'][0]['n']} volcanoes have erupted since 2000; {R['recent_n30_1m']} of them have a million or more people within 30 km, led by Tangkuban Parahu, Merapi, Slamet, Pacaya and Taal. At least {M(R['since1900']['floor30'])} people live within 30 km of a volcano that has erupted since 1900.
- Recorded eruptions rose {R['ratio_all_1900_1600']:.1f} times from the 1600s to the 1900s, but eruptions of VEI 4 or more only {R['ratio_vei4_1900_1600']:.1f} times: the rising curve is mostly better reporting.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded). |
| `header.png` | Social card, 1200 x 630. |
| `data/volcanoes.csv` | All {R['n_volc']:,} Holocene volcanoes: GVP attributes, last known eruption and its class, population within 5, 10, 30 and 100 km, eruption counts, largest VEI ({size('data/volcanoes.csv')}). |
| `data/volcanoes_by_population.csv` | The {R['n_pop']:,} volcanoes with population figures, sorted by people within 30 km. |
| `data/eruptions.csv` | The {R['n_erupt']:,} confirmed Holocene eruptions in VOTW 5.3.5 ({size('data/eruptions.csv')}). |
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
- Populations: current GVP exports no longer include them, so the population within 5, 10, 30 and 100 km comes from the GVP list of VOTW 5.1.7, joined by volcano number ({R['meta']['n_nopop']} newer volcanoes have none). The figures are identical to a GVP export of 2020: a fixed snapshot of unstated year. For {R['n_flat']} volcanoes, mostly large volcanic fields, the figure is the same at 10 and 30 km; they are flagged.
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

- {GVP_CITE}. Volcano list (copy: https://github.com/bciupak/Wizualizacja-Danych-Projekty) and eruption list (copy: https://github.com/im-hana-s/ML-mini-project, `data/raw/gvp_eruption_list.xlsx`).
- {GVP_CITE_POP}. Population columns (copy: https://github.com/Matteo2979/Volcano-Analysis, `GVP_Volcano_List.csv`).
- GVP data are used under the Smithsonian's terms of use (https://volcano.si.edu/gvp_termsofuse.cfm): non-commercial use with credit; no open licence. The tables in `data/` derived from them keep those terms (see `data/LICENSE`). This work is not endorsed by the Smithsonian Institution.
- NOAA NCEI/WDS Global Significant Volcanic Eruptions Database, doi:10.7289/V5JW8BSH (US Government, public domain); eruptions with deaths, copy of 2024 from the same Matteo2979 repository.
- Bird, P. (2003) An updated digital model of plate boundaries. G3 4(3), 1027. GeoJSON by Hugo Ahlenius, Nordpil (https://github.com/fraxen/tectonicplates), Open Data Commons Attribution License 1.0.
- Natural Earth countries and populated places (public domain). Base map tiles on the page: © Esri.

Text and figures are CC BY 4.0 (figures show GVP-derived values, credited above); code is MIT (see `LICENSE`).

## Citation

Hotham, T. (2026) In the shadow of the volcano: how many people live near the world's Holocene volcanoes, from the Smithsonian's Volcanoes of the World. Zenodo. https://doi.org/{{10.5281/zenodo.23847550}}

Please also cite the GVP database: {GVP_CITE}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
import re
check_dashes(re.sub(r"^\|[-|]+\|$", "", readme, flags=re.M), "README")   # table rule lines are markdown syntax, not text
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = open("/home/claude/studies/plague-map/LICENSE", encoding="utf-8").read().split("\n\n\nThis licence covers")[0]
lic += """


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post and the figures are released under
CC BY 4.0. The data files in data/ are derived from the Smithsonian Institution
Global Volcanism Program database Volcanoes of the World and are shared under
the Smithsonian's terms of use (non-commercial use, with credit), not under an
open licence (see data/LICENSE). Plate boundaries: Bird (2003), GeoJSON by Hugo
Ahlenius, Nordpil, ODC-By 1.0. Country outlines and places: Natural Earth
(public domain). NOAA NCEI data: public domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
open(os.path.join(DATA, "LICENSE"), "w", encoding="utf-8").write(f"""Data in this folder

The volcano, eruption and population values are taken or derived from the Smithsonian Institution Global Volcanism
Program database, Volcanoes of the World, and are shared under the Smithsonian's terms of use
(https://volcano.si.edu/gvp_termsofuse.cfm): free for non-commercial use, with credit. Please cite:

  {GVP_CITE}
  {GVP_CITE_POP}

Deaths (NOAA NCEI Global Significant Volcanic Eruptions Database, doi:10.7289/V5JW8BSH) are US Government data in the
public domain. Plate boundaries in page/plates.json: Bird (2003), GeoJSON by Hugo Ahlenius, Nordpil, Open Data Commons
Attribution License 1.0. Country outlines and city names in page/: Natural Earth, public domain.
Derived counts and bounds (countries.csv, results.json, eruptions_by_century.csv) are by Tristan Hotham (2026).
""")
print("README", len(readme.split()), "words")

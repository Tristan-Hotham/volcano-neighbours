"""Shared paths and helpers for the volcano-neighbours project.

Raw inputs (read in place, never copied into the repo). All were fetched from public GitHub mirrors of the
Smithsonian Global Volcanism Program (GVP) database, Volcanoes of the World (VOTW):

  VOLC   GVP_Volcano_List_Holocene_202605041745.xls  (Excel XML spreadsheet)
         Header: "Global Volcanism Program - Volcanoes of the World 5.3.5", "Downloaded on 04 May 2026".
         Mirror: github.com/bciupak/Wizualizacja-Danych-Projekty, "Wulkany na swiecie/".
         1,215 Holocene volcanoes: number, name, country, region, landform, type, activity evidence,
         last known eruption, latitude, longitude, elevation, tectonic setting, dominant rock type.
  ERUP   cand/h_erupt.xlsx, sheet "Eruption List" (renamed from gvp_eruption_list.xlsx)
         Header: "Global Volcanism Program - Volcanoes of the World 5.3.5", "Holocene Eruptions Search Result",
         "Downloaded on 24 April 2026". Mirror: github.com/im-hana-s/ML-mini-project, data/raw/gvp_eruption_list.xlsx.
         9,918 confirmed Holocene eruptions.
  POP    cand/c1_GVP_Volcano_List.csv (renamed from GVP_Volcano_List.csv)
         Mirror: github.com/Matteo2979/Volcano-Analysis, committed 2024; the repository README cites VOTW v. 5.1.7
         (26 Apr 2024). The only recent full list found with the GVP's population columns (within 5, 10, 30 and
         100 km of each volcano); current GVP list downloads no longer include them. The same figures appear
         unchanged in the GVP export used by TidyTuesday in 2020, so they are a fixed snapshot.
  NCEI   cand/m_ncei.csv: NOAA NCEI/WDS Global Significant Volcanic Eruptions Database, eruptions with deaths
         recorded (442 rows, -141 to 2024), from the same Matteo2979 repository. doi:10.7289/V5JW8BSH. US public domain.
  PLATES plates/PB2002_boundaries.json: Bird (2003) plate boundary model as GeoJSON by Hugo Ahlenius, Nordpil,
         github.com/fraxen/tectonicplates. Open Data Commons Attribution License 1.0.
  GEO    /home/claude/newdata/raw/geo/ ne_10m and ne_50m admin 0 countries, ne_10m_populated_places_simple
         (Natural Earth, public domain).

Citation requested by the GVP (version and source; volcano.si.edu shows a DOI only for the current version, 5.4.0,
so none is given for 5.3.5 or 5.1.7):
  Global Volcanism Program, 2025. Volcanoes of the World (v. 5.3.5). Distributed by Smithsonian Institution, compiled by Venzke, E.
  https://volcano.si.edu/ (accessed via the named GitHub mirrors)
  Global Volcanism Program, 2024. Volcanoes of the World (v. 5.1.7). Distributed by Smithsonian Institution, compiled by Venzke, E.
  https://volcano.si.edu/ (accessed via the named GitHub mirrors)
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAWD = "/home/claude/newdata/raw2/volcano"
VOLC = f"{RAWD}/GVP_Volcano_List_Holocene_202605041745.xls"
ERUP = f"{RAWD}/cand/h_erupt.xlsx"
POP = f"{RAWD}/cand/c1_GVP_Volcano_List.csv"
NCEI = f"{RAWD}/cand/m_ncei.csv"
PLATES = f"{RAWD}/plates/PB2002_boundaries.json"
GEO = "/home/claude/newdata/raw/geo"
NE10 = f"{GEO}/ne_10m_admin_0_countries.geojson"
NE50 = f"{GEO}/ne_50m_admin_0_countries.geojson"
PLACES = f"{GEO}/ne_10m_populated_places_simple.geojson"
DATA = os.path.join(ROOT, "data")
PAGE = os.path.join(DATA, "page")
WORK = os.environ.get("VOLCTMP", "/dev/shm/volcano")   # intermediates live in memory, not in the repo
for d in (DATA, PAGE, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "volcano-neighbours"
URL = "https://maps.tristanhotham.com/volcano-neighbours/"
REPO = "https://github.com/Tristan-Hotham/volcano-neighbours"
DOI = "10.5281/zenodo.23847550"
DOI_URL = "https://doi.org/10.5281/zenodo.23847550"
BLOG = "https://blog.tristanhotham.com/2026/10/31/volcano-neighbours/"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
GVP_CITE = "Global Volcanism Program, 2025. Volcanoes of the World (v. 5.3.5). Distributed by Smithsonian Institution, compiled by Venzke, E. https://volcano.si.edu/ (accessed via the named GitHub mirrors)"
GVP_CITE_POP = "Global Volcanism Program, 2024. Volcanoes of the World (v. 5.1.7). Distributed by Smithsonian Institution, compiled by Venzke, E. Population snapshot. https://volcano.si.edu/ (accessed via the named GitHub mirrors)"
RINGS = [5, 10, 30, 100]

# Last known eruption classes, used for colour everywhere (page, figures, collage)
ECLS = [("2000", "2000 or later", 2000, 9999, "#B3261E"),
        ("1900", "1900 to 1999", 1900, 1999, "#E8743B"),
        ("1500", "1500 to 1899", 1500, 1899, "#E9B949"),
        ("ce", "1 to 1499 CE", 1, 1499, "#8DA9B8"),
        ("bce", "Before 1 CE (Holocene)", -12000, 0, "#4E6E8E"),
        ("unk", "No dated eruption", None, None, "#9C948A")]


def ecls(y):
    if y is None:
        return "unk"
    for k, _, a, b, _ in ECLS[:-1]:
        if a <= y <= b:
            return k
    raise ValueError(y)


# GVP country names that differ from Natural Earth ADMIN names, mapped to ISO A3 (ADM0_A3) codes.
# Shared volcanoes ("Chile-Argentina") belong to each country named.
CMAP = {"United States": "USA", "Russia": "RUS", "DR Congo": "COD", "North Korea": "PRK", "South Korea": "KOR",
        "Tanzania": "TZA", "Cabo Verde": "CPV", "Sao Tome and Principe": "STP", "Cote d'Ivoire": "CIV",
        "Taiwan": "TWN", "Syria": "SYR", "Iran": "IRN", "Vietnam": "VNM", "Laos": "LAO", "Bolivia": "BOL",
        "Saint Kitts and Nevis": "KNA", "Saint Vincent and the Grenadines": "VCT", "Saint Lucia": "LCA",
        "Federated States of Micronesia": "FSM", "Micronesia": "FSM", "United Kingdom": "GBR", "Netherlands": "NLD",
        "Turkey": "TUR", "Turkiye": "TUR", "Türkiye": "TUR", "Czech Republic": "CZE", "Czechia": "CZE",
        "Korea, North": "PRK", "Korea, South": "KOR", "Burma (Myanmar)": "MMR", "Myanmar": "MMR",
        "Solomon Islands": "SLB", "Papua New Guinea": "PNG", "New Zealand": "NZL", "Antarctica": "ATA",
        "Libya": "LBY", "Sudan": "SDN", "Chad": "TCD", "Niger": "NER", "Mali": "MLI", "Algeria": "DZA",
        "Uganda": "UGA", "Rwanda": "RWA", "Kenya": "KEN", "Eritrea": "ERI", "Djibouti": "DJI", "Ethiopia": "ETH",
        "Yemen": "YEM", "Saudi Arabia": "SAU", "Jordan": "JOR", "Armenia": "ARM", "Azerbaijan": "AZE",
        "Georgia": "GEO", "Mongolia": "MNG", "China": "CHN", "India": "IND", "Pakistan": "PAK", "Afghanistan": "AFG",
        "Greece": "GRC", "Italy": "ITA", "Spain": "ESP", "Portugal": "PRT", "France": "FRA", "Germany": "DEU",
        "Iceland": "ISL", "Norway": "NOR", "Japan": "JPN", "Philippines": "PHL", "Indonesia": "IDN",
        "Mexico": "MEX", "Guatemala": "GTM", "El Salvador": "SLV", "Honduras": "HND", "Nicaragua": "NIC",
        "Costa Rica": "CRI", "Panama": "PAN", "Colombia": "COL", "Ecuador": "ECU", "Peru": "PER", "Chile": "CHL",
        "Argentina": "ARG", "Canada": "CAN", "Grenada": "GRD", "Dominica": "DMA", "Vanuatu": "VUT", "Tonga": "TON",
        "Samoa": "WSM", "Fiji": "FJI", "Australia": "AUS", "Cameroon": "CMR", "Nigeria": "NGA", "Madagascar": "MDG",
        "Comoros": "COM", "Union of the Comoros": "COM", "Equatorial Guinea": "GNQ", "Malaysia": "MYS", "Thailand": "THA", "Cambodia": "KHM",
        "Hungary": "HUN", "Slovakia": "SVK", "Romania": "ROU", "Ukraine": "UKR", "Tajikistan": "TJK",
        "Kyrgyzstan": "KGZ", "Kazakhstan": "KAZ", "Mauritius": "MUS", "Egypt": "EGY", "Morocco": "MAR",
        "Undersea Features": None}


def countries_of(gvp):
    """List of plain country names in a GVP country field ("Chile-Argentina" -> ["Chile", "Argentina"])."""
    g = gvp.split(" - ")[0].strip()          # "Japan - administered by Russia" -> Japan; "France - claimed by Vanuatu" -> France
    if g == "Undersea Features":
        return []
    return [p.strip() for p in g.split("-")] if g not in ("Guinea-Bissau", "Timor-Leste") else [g]


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def jsave(obj, path, indent=None):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def mfmt(v):
    """Millions with one decimal, or thousands, for prose ("12.3 million", "840,000")."""
    v = float(v)
    if v >= 1e9:
        return f"{v / 1e9:.2f} billion"
    if v >= 1e6:
        return f"{v / 1e6:.1f} million"
    return f"{round(v, -3):,.0f}" if v >= 1e4 else f"{round(v):,}"


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "yr": return str(int(v))
    if f == "pc": return f"{round(float(v))}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "m": return mfmt(v)
    if f == "m0": return f"{round(float(v) / 1e6):,} million"
    if f == "bn": return f"{float(v) / 1e9:.1f} billion"
    raise ValueError(f)


def fill(text, R, f=fmt):
    return re.sub(r"\{\{(?!IMG|DOI|BLOG_URL|DOI_URL|TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: f(get(R, m.group(1)), m.group(3)), text)


def check_dashes(text, where):
    for bad in ("—", "–", "--"):
        assert bad not in text, (where, bad, text[max(0, text.find(bad) - 80):text.find(bad) + 80])


def hav(lat1, lon1, lat2, lon2):
    import numpy as np
    r = np.pi / 180
    a = np.sin((lat2 - lat1) * r / 2) ** 2 + np.cos(lat1 * r) * np.cos(lat2 * r) * np.sin((lon2 - lon1) * r / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(np.minimum(1, a)))

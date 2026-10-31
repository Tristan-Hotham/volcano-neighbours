"""Read the GVP volcano list (VOTW 5.3.5), the GVP population columns (VOTW 5.1.7), the GVP eruption list (VOTW 5.3.5)
and the NOAA NCEI deaths table; clean and join them. Writes WORK/clean.json and data/volcanoes.csv, data/eruptions.csv."""
import re, html
import numpy as np, pandas as pd, openpyxl
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from common import *

# ---------- volcano list (Excel 2003 XML) ----------
x = open(VOLC, encoding="utf-8").read()
rows = [[html.unescape(c) for c in re.findall(r"<Data[^>]*>(.*?)</Data>", r, re.S)] for r in re.findall(r"<Row.*?</Row>", x, re.S)]
assert "Volcanoes of the World 5.3.5" in rows[0][0] and "04 May 2026" in rows[0][2], rows[0]
V = pd.DataFrame(rows[2:], columns=rows[1])
V = V.rename(columns={"Volcano Number": "vnum", "Volcano Name": "name", "Country": "country", "Volcanic Region Group": "region_group",
                      "Volcanic Region": "region", "Volcano Landform": "landform", "Primary Volcano Type": "type",
                      "Activity Evidence": "evidence", "Last Known Eruption": "last_txt", "Latitude": "lat", "Longitude": "lon",
                      "Elevation (m)": "elev", "Tectonic Setting": "tectonic", "Dominant Rock Type": "rock"})
V["vnum"] = V.vnum.astype(int)
for c in ("lat", "lon"):
    V[c] = V[c].astype(float)
V["elev"] = pd.to_numeric(V.elev, errors="coerce")
assert V.vnum.is_unique and len(V) == 1215


def lastyear(s):
    s = s.strip()
    if s == "Unknown" or not s:
        return None
    m = re.match(r"^(\d+) (CE|BCE)$", s)
    assert m, s
    return int(m.group(1)) * (1 if m.group(2) == "CE" else -1)


V["last"] = V.last_txt.map(lastyear)

# ---------- population columns (VOTW 5.1.7 export) ----------
P = pd.read_csv(POP, encoding="latin-1")
pc = {f"Population within {r} km": f"p{r}" for r in RINGS}
P = P.rename(columns={"Volcano Number": "vnum", **pc})[["vnum", *pc.values()]]
assert P.vnum.is_unique and len(P) == 1288
V = V.merge(P, on="vnum", how="left")
n_nopop = int(V.p30.isna().sum())
for r in RINGS:   # rings are nested
    ok = V[f"p{r}"].notna()
assert (V.loc[ok, "p5"] <= V.loc[ok, "p10"]).all() and (V.loc[ok, "p10"] <= V.loc[ok, "p30"]).all() and (V.loc[ok, "p30"] <= V.loc[ok, "p100"]).all()

# ---------- eruption list ----------
wb = openpyxl.load_workbook(ERUP, read_only=True)
ws = wb["Eruption List"]
it = ws.iter_rows(values_only=True)
h0 = next(it); h1 = next(it)
assert "Volcanoes of the World 5.3.5" in h0[0] and "24 April 2026" in h0[5], h0
E = pd.DataFrame(list(it), columns=list(h1)).replace("NULL", None)
E = E.rename(columns={"Volcano Number": "vnum", "Volcano Name": "vname", "Eruption Number": "enum", "Eruption Category": "cat",
                      "Area of Activity": "area", "VEI": "vei", "VEI Modifier": "vei_mod", "Start Year Modifier": "sy_mod",
                      "Start Year": "sy", "Start Year Uncertainty": "sy_unc", "Start Month": "sm", "Start Day": "sd",
                      "Evidence Method (dating)": "method", "End Year Modifier": "ey_mod", "End Year": "ey", "End Month": "em", "End Day": "ed"})
E = E[["vnum", "vname", "enum", "cat", "area", "vei", "vei_mod", "sy_mod", "sy", "sy_unc", "sm", "sd", "method", "ey_mod", "ey", "em", "ed"]]
for c in ("vnum", "enum", "sy"):
    E[c] = pd.to_numeric(E[c], errors="coerce")
E["vei"] = pd.to_numeric(E.vei, errors="coerce")
E["sy_unc"] = pd.to_numeric(E.sy_unc, errors="coerce")
assert len(E) == 9918 and (E.cat == "Confirmed Eruption").all() and E.sy.notna().all() and E.enum.is_unique
E["sy"] = E.sy.astype(int)
n_e_unmatched = int((~E.vnum.isin(V.vnum)).sum())
# per volcano: number of eruptions, the latest eruption start in the eruption list, and the largest VEI
g = E.groupby("vnum")
V["n_erupt"] = V.vnum.map(g.size()).fillna(0).astype(int)
V["n_erupt_1500"] = V.vnum.map(E[E.sy >= 1500].groupby("vnum").size()).fillna(0).astype(int)
V["last_erup_list"] = V.vnum.map(g.sy.max())
V["max_vei"] = V.vnum.map(g.vei.max())
V["continuing"] = V.vnum.isin(E[E.ey_mod == ">"].vnum)
# the volcano list's last known eruption should agree with the eruption list (the lists were downloaded 10 days apart)
both = V[V["last"].notna() & V.last_erup_list.notna()]
n_last_disagree = int((both["last"] != both.last_erup_list).sum())

# ---------- countries ----------
ne = jload(NE10)["features"]
ADMIN = {f["properties"]["ADMIN"]: f["properties"]["ADM0_A3"] for f in ne}
ISO_NAME = {f["properties"]["ADM0_A3"]: f["properties"]["ADMIN"] for f in ne}
ISO_NAME.update({"USA": "United States", "RUS": "Russia", "COD": "DR Congo", "PRK": "North Korea", "KOR": "South Korea",
                 "TZA": "Tanzania", "CPV": "Cabo Verde", "STP": "Sao Tome and Principe", "FSM": "Micronesia", "ATA": "Antarctica"})
iso_of = {}
for gname in V.country.unique():
    for c in countries_of(gname):
        iso = CMAP.get(c, ADMIN.get(c))
        assert iso, ("no ISO for", c)
        iso_of[c] = iso
V["isos"] = V.country.map(lambda s: "|".join(iso_of[c] for c in countries_of(s)))

# the territory a volcano sits in (Natural Earth), to flag overseas territories (Montserrat, Reunion...)
geoms = [shape(f["geometry"]) for f in ne]
tree = STRtree(geoms)


def where(lat, lon):
    p = Point(lon, lat)
    for i in tree.query(p):
        if geoms[i].contains(p):
            return ne[i]["properties"]["ADM0_A3"]
    i = tree.nearest(p)
    return ne[i]["properties"]["ADM0_A3"] if geoms[i].distance(p) < 0.3 else ""


V["ne_iso"] = [where(a, b) for a, b in zip(V.lat, V.lon)]
V["ecls"] = V["last"].map(lambda y: ecls(None if pd.isna(y) else int(y)))

# ---------- NOAA NCEI eruptions with deaths ----------
N = pd.read_csv(NCEI)
N = N.rename(columns={"Year": "year", "Mo": "month", "Dy": "day", "Name": "name", "Location": "location", "Country": "country",
                      "Latitude": "lat", "Longitude": "lon", "Elevation (m)": "elev", "Type": "type", "VEI": "vei",
                      "Total Deaths": "deaths", "Total Injuries": "injuries", "Total Houses Destroyed": "houses"})
assert len(N) == 442
# match each NCEI event to the nearest GVP volcano within 15 km (for the popup's deadliest-eruption line)
d = hav(N.lat.values[:, None], N.lon.values[:, None], V.lat.values[None, :], V.lon.values[None, :])
j = d.argmin(1)
N["vnum"] = np.where(d.min(1) <= 15, V.vnum.values[j], np.nan)
n_ncei_matched = int(N.vnum.notna().sum())

# ---------- save ----------
cols = ["vnum", "name", "country", "isos", "ne_iso", "region_group", "region", "landform", "type", "evidence", "last_txt", "last", "ecls",
        "lat", "lon", "elev", "tectonic", "rock", "p5", "p10", "p30", "p100", "n_erupt", "n_erupt_1500", "last_erup_list", "max_vei", "continuing"]
V = V[cols].sort_values("vnum")
clean = {"V": json.loads(V.to_json(orient="records")),
         "E": json.loads(E.to_json(orient="records")),
         "N": json.loads(N.to_json(orient="records")),
         "iso_name": ISO_NAME,
         "meta": {"n_volc": len(V), "n_nopop": n_nopop, "nopop": V[V.p30.isna()].name.tolist(), "n_pop_rows": len(P),
                  "n_pop_not_in_535": int((~P.vnum.isin(V.vnum)).sum()), "n_erupt": len(E), "n_e_unmatched": n_e_unmatched,
                  "n_last_disagree": n_last_disagree, "n_ncei": len(N), "n_ncei_matched": n_ncei_matched}}
jsave(clean, f"{WORK}/clean.json")

out = V.rename(columns={"vnum": "volcano_number", "isos": "country_iso3", "ne_iso": "territory_iso3", "last_txt": "last_known_eruption",
                        "last": "last_known_eruption_year", "ecls": "last_eruption_class", "elev": "elevation_m",
                        "p5": "population_within_5km", "p10": "population_within_10km", "p30": "population_within_30km",
                        "p100": "population_within_100km", "n_erupt": "n_eruptions_holocene", "n_erupt_1500": "n_eruptions_since_1500",
                        "last_erup_list": "latest_eruption_start_in_eruption_list", "max_vei": "max_vei", "continuing": "has_continuing_eruption"})
out.to_csv(f"{DATA}/volcanoes.csv", index=False)
E.rename(columns={"vnum": "volcano_number", "vname": "volcano_name", "enum": "eruption_number", "cat": "category", "area": "area_of_activity",
                  "vei_mod": "vei_modifier", "sy_mod": "start_year_modifier", "sy": "start_year", "sy_unc": "start_year_uncertainty",
                  "sm": "start_month", "sd": "start_day", "method": "evidence_method", "ey_mod": "end_year_modifier", "ey": "end_year",
                  "em": "end_month", "ed": "end_day"}).to_csv(f"{DATA}/eruptions.csv", index=False)
print(clean["meta"])
print(V.ecls.value_counts().to_dict())

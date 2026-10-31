"""All results: data/results.json (every number quoted anywhere) and the derived tables in data/."""
import numpy as np, pandas as pd
from common import *

C = jload(f"{WORK}/clean.json")
V = pd.DataFrame(C["V"]); E = pd.DataFrame(C["E"]); N = pd.DataFrame(C["N"]); M = C["meta"]
ISO_NAME = C["iso_name"]
VP = V[V.p30.notna()].copy()
R = {"meta": M}
R["n_volc"] = len(V); R["n_pop"] = len(VP); R["n_erupt"] = len(E)
R["n_countries"] = len({i for s in V.isos for i in s.split("|") if i})
R["n_volc_with_erupt"] = int((V.n_erupt > 0).sum())
R["n_unknown_last"] = int((V.ecls == "unk").sum())
R["last_year_data"] = int(V["last"].max())
R["first_erupt_year"] = int(E.sy.min())

# ---------- global totals: sum over volcanoes (upper bound) and disjoint rings (lower bound) ----------
LAT, LON = VP.lat.values, VP.lon.values
D = hav(LAT[:, None], LON[:, None], LAT[None, :], LON[None, :])
np.fill_diagonal(D, np.inf)


def floor(idx, r):
    """Greedy set of volcanoes whose r-km rings do not overlap, most populous first: their populations are
    disjoint, so the sum is a true lower bound on the number of people within r km of any volcano in idx."""
    col = f"p{r}"
    order = sorted(idx, key=lambda i: -VP[col].values[i])
    picked = []
    for i in order:
        if VP[col].values[i] <= 0:
            break
        if all(D[i, j] > 2 * r for j in picked):
            picked.append(i)
    return float(VP[col].values[picked].sum()), len(picked)


ALL = list(range(len(VP)))
R["glob"] = {}
for r in RINGS:
    c = f"p{r}"
    lo, k = floor(ALL, r)
    R["glob"][str(r)] = {"sum": float(VP[c].sum()), "floor": lo, "floor_n": k, "zero": int((VP[c] == 0).sum()),
                         "median": float(VP[c].median()), "near_other": int((D.min(1) <= 2 * r).sum())}
G = R["glob"]
R["glob_share_floor_100"] = 100 * G["100"]["floor"] / G["100"]["sum"]
for k, col, th in (("n30_1m", "p30", 1e6), ("n10_100k", "p10", 1e5), ("n100_10m", "p100", 1e7), ("n5_100k", "p5", 1e5), ("n10_1m", "p10", 1e6), ("n30_100k", "p30", 1e5)):
    R[k] = int((VP[col] >= th).sum())
R["n10_zero_pct"] = 100 * G["10"]["zero"] / len(VP)
# the most crowded volcanoes hold most of the total
s30 = VP.p30.sort_values(ascending=False)
R["top20_share30"] = 100 * s30.head(20).sum() / s30.sum()
R["top100_share30"] = 100 * s30.head(100).sum() / s30.sum()

# ---------- countries (a shared volcano counts for each country named) ----------
rows = []
for iso in sorted({i for s in V.isos for i in s.split("|") if i}):
    m = V.isos.str.split("|").map(lambda l: iso in l)
    sub = V[m]; idx = [i for i, ok in enumerate(VP.isos.str.split("|").map(lambda l: iso in l)) if ok]
    row = {"iso": iso, "name": ISO_NAME.get(iso, iso), "n": int(len(sub)), "n_pop": len(idx),
           "n_since1900": int((sub["last"] >= 1900).sum()), "n_since2000": int((sub["last"] >= 2000).sum()),
           "n_erupt": int(sub.n_erupt.sum())}
    for r in (10, 30, 100):
        row[f"sum{r}"] = float(sub[f"p{r}"].sum())
        row[f"floor{r}"], _ = floor(idx, r) if idx else (0.0, 0)
    if idx:
        t = VP.iloc[idx].sort_values("p30", ascending=False).iloc[0]
        row["top"] = t["name"]; row["top_p30"] = float(t.p30)
    else:
        row["top"] = ""; row["top_p30"] = 0.0
    rows.append(row)
CT = pd.DataFrame(rows).sort_values("sum30", ascending=False)
CT.to_csv(f"{DATA}/countries.csv", index=False)
R["countries"] = json.loads(CT.head(25).to_json(orient="records"))
R["n_country_rows"] = len(CT)
cmap = {r["iso"]: r for r in json.loads(CT.to_json(orient="records"))}
R["c"] = {k: cmap[k] for k in ("IDN", "PHL", "JPN", "MEX", "ITA", "GTM", "ETH", "USA", "ECU", "SLV", "CRI", "NIC", "COL", "CHN", "RUS", "ISL", "GBR", "FRA", "NZL", "CHL", "PER", "PNG", "TUR", "IRN", "DEU", "ESP", "KEN", "RWA", "COD", "UGA", "CMR", "TWN", "ARM", "SAU", "YEM")}
R["c_top_floor30"] = json.loads(CT.sort_values("floor30", ascending=False).head(10)[["iso", "name", "floor30", "sum30"]].to_json(orient="records"))
R["c_rank_floor30"] = [r["iso"] for r in R["c_top_floor30"]]
R["c_rank_sum30"] = CT.iso.head(10).tolist()
R["c_rank_floor10"] = CT.sort_values("floor10", ascending=False).iso.head(10).tolist()
R["c_rank_floor100"] = CT.sort_values("floor100", ascending=False).iso.head(10).tolist()
R["idn_share_floor30"] = 100 * cmap["IDN"]["floor30"] / G["30"]["floor"]
R["c_top5_floor30_share"] = 100 * sum(cmap[i]["floor30"] for i in R["c_rank_floor30"][:5]) / G["30"]["floor"]

# ---------- volcanoes ----------
def vrow(t):
    return {"vnum": int(t.vnum), "name": t["name"], "country": t.country, "type": t.type, "last": None if pd.isna(t["last"]) else int(t["last"]),
            "last_txt": t.last_txt, "ecls": t.ecls, "elev": None if pd.isna(t.elev) else int(t.elev), "p5": float(t.p5), "p10": float(t.p10),
            "p30": float(t.p30), "p100": float(t.p100), "n_erupt": int(t.n_erupt), "flat": bool(t.p10 == t.p30 and t.p30 > 0)}


for r in RINGS:
    R[f"top{r}"] = [vrow(t) for _, t in VP.sort_values(f"p{r}", ascending=False).head(20).iterrows()]
VP.sort_values("p30", ascending=False).to_csv(f"{DATA}/volcanoes_by_population.csv", index=False,
    columns=["vnum", "name", "country", "type", "last_txt", "lat", "lon", "elev", "p5", "p10", "p30", "p100", "n_erupt"])
NAMED = {"Vesuvius": "vesuvius", "Campi Flegrei": "flegrei", "Merapi": "merapi", "Popocatepetl": "popo", "Taal": "taal",
         "Aira": "sakura", "Fujisan": "fuji", "Etna": "etna", "Mayon": "mayon", "Pinatubo": "pinatubo", "Agua": "agua",
         "Fuego": "fuego", "Pacaya": "pacaya", "San Salvador": "sansal", "Tangkuban Parahu": "tangkuban", "Gede-Pangrango": "gede",
         "Kelud": "kelud", "Rainier": "rainier", "Hood": "hood", "Auckland Volcanic Field": "auckland", "Hekla": "hekla",
         "Nyiragongo": "nyira", "Ruiz, Nevado del": "ruiz", "Tambora": "tambora", "Krakatau": "krakatau", "Pelee": "pelee",
         "Soufriere Hills": "soufriere", "Iztaccihuatl": "izta", "Ilopango": "ilopango", "Cotopaxi": "cotopaxi",
         "Guagua Pichincha": "pichincha", "Masaya": "masaya", "Arenal": "arenal", "Ischia": "ischia", "Colli Albani": "albani",
         "Chichinautzin": "chichinautzin", "Ubinas": "ubinas", "Misti, El": "misti", "Unzendake": "unzen", "Asosan": "aso",
         "Semeru": "semeru", "Kilauea": "kilauea", "Erebus": "erebus", "Santorini": "santorini", "Michoacan-Guanajuato": "michoacan",
         "La Palma": "lapalma", "Lewotobi": "lewotobi", "Reykjanes": "reykjanes",
         "Ruang": "ruang", "Ibu": "ibu", "Kanlaon": "kanlaon", "Bulusan": "bulusan", "Galunggung": "galunggung", "Salak": "salak", "Sundoro": "sundoro"}
R["v"] = {}
for nm, key in NAMED.items():
    t = V[V.name == nm]
    if len(t) == 1 and not pd.isna(t.iloc[0].p30):
        R["v"][key] = vrow(t.iloc[0])
miss = [n for n, k in NAMED.items() if k not in R["v"]]
R["named_missing"] = miss
ves, cf = V[V.name == "Vesuvius"].iloc[0], V[V.name == "Campi Flegrei"].iloc[0]
R["ves_cf_km"] = float(hav(ves.lat, ves.lon, cf.lat, cf.lon))

# ---------- recent eruptions near people ----------
R["by_ecls"] = []
for k, lab, a, b, col in ECLS:
    sub = VP[VP.ecls == k]; idx = [i for i, e in enumerate(VP.ecls.values) if e == k]
    R["by_ecls"].append({"k": k, "label": lab, "col": col, "n": int((V.ecls == k).sum()), "n_pop": int(len(sub)),
                         "sum10": float(sub.p10.sum()), "sum30": float(sub.p30.sum()), "sum100": float(sub.p100.sum()),
                         "floor10": floor(idx, 10)[0], "floor30": floor(idx, 30)[0], "floor100": floor(idx, 100)[0]})
BE = {b["k"]: b for b in R["by_ecls"]}
idx1900 = [i for i, y in enumerate(VP["last"].values) if not pd.isna(y) and y >= 1900]
R["since1900"] = {"n": len(idx1900), "floor10": floor(idx1900, 10)[0], "floor30": floor(idx1900, 30)[0], "floor100": floor(idx1900, 100)[0],
                  "sum30": float(VP.p30.values[idx1900].sum())}
R["recent"] = [vrow(t) for _, t in VP[VP["last"] >= 2000].sort_values("p30", ascending=False).head(20).iterrows()]
R["recent1900"] = [vrow(t) for _, t in VP[(VP["last"] >= 1900) & (VP["last"] < 2000)].sort_values("p30", ascending=False).head(10).iterrows()]
R["recent_n30_1m"] = int(((VP["last"] >= 2000) & (VP.p30 >= 1e6)).sum())
# eruptions that started in the latest two years of the list
y1 = int(E.sy.max())
R["latest_year"] = y1
lat2 = E[E.sy >= y1 - 1]
R["latest2"] = {"y0": y1 - 1, "y1": y1, "n_erupt": int(len(lat2)), "n_volc": int(lat2.vnum.nunique())}
idxl = [i for i, v in enumerate(VP.vnum.values) if v in set(lat2.vnum)]
R["latest2"]["floor30"] = floor(idxl, 30)[0]; R["latest2"]["sum30"] = float(VP.p30.values[idxl].sum())
R["latest2"]["top"] = [vrow(t) for _, t in VP.iloc[idxl].sort_values("p30", ascending=False).head(8).iterrows()]
R["n_continuing"] = int(V.continuing.sum())

# ---------- eruptions through time ----------
E["cent"] = (np.floor(E.sy / 100) * 100).astype(int)
cent = []
for c0 in range(-10000, 2100, 100):
    s = E[E.cent == c0]
    yrs = 100 if c0 < 2000 else (y1 - 2000 + 1)
    cent.append({"c": c0, "n": int(len(s)), "vei4": int((s.vei >= 4).sum()), "vei3": int((s.vei >= 3).sum()), "years": yrs,
                 "obs": int((s.method == "Observations: Reported").sum()), "volc": int(s.vnum.nunique())})
CE = pd.DataFrame(cent)
CE.to_csv(f"{DATA}/eruptions_by_century.csv", index=False)
R["centuries"] = [c for c in cent if c["c"] >= 0]
R["cent_bce"] = {"n": int((E.sy < 0).sum()), "pct": 100 * (E.sy < 0).mean()}
cc = {c["c"]: c for c in cent}
R["cc"] = {str(k): cc[k] for k in (1000, 1500, 1600, 1700, 1800, 1900, 2000)}
R["ratio_all_1900_1600"] = cc[1900]["n"] / cc[1600]["n"]
R["ratio_vei4_1900_1600"] = cc[1900]["vei4"] / cc[1600]["vei4"]
R["ratio_all_1900_1700"] = cc[1900]["n"] / cc[1700]["n"]
R["ratio_vei4_1900_1700"] = cc[1900]["vei4"] / cc[1700]["vei4"]
R["rate_2000"] = cc[2000]["n"] / cc[2000]["years"]
R["rate_1900"] = cc[1900]["n"] / 100
R["share_since1800"] = 100 * (E.sy >= 1800).mean()
R["share_since1900"] = 100 * (E.sy >= 1900).mean()
R["n_since1800"] = int((E.sy >= 1800).sum())
R["obs_share"] = 100 * (E.method == "Observations: Reported").mean()
R["vei_known_pct"] = 100 * E.vei.notna().mean()
R["n_vei7"] = int((E.vei >= 7).sum())
R["vei7"] = [{"name": r.vname, "y": int(r.sy)} for r in E[E.vei >= 7].sort_values("sy").itertuples()]
R["n_vei6_since1500"] = int(((E.vei >= 6) & (E.sy >= 1500)).sum())
R["vei6_since1500"] = [{"name": r.vname, "y": int(r.sy)} for r in E[(E.vei >= 6) & (E.sy >= 1500)].sort_values("sy").itertuples()]
# share of volcanoes whose eruption record starts only after 1800 (among volcanoes with any eruption since 1800)
first = E.groupby("vnum").sy.min()
R["n_volc_first_after1800"] = int((first >= 1800).sum())
R["active_1900_volc"] = int(E[E.sy >= 1900].vnum.nunique())

# decades since 1900, for the page chart
dec = E[E.sy >= 1900].assign(d=lambda d: (d.sy // 10) * 10).groupby("d").agg(n=("enum", "size"), volc=("vnum", "nunique")).reset_index()
R["decades"] = json.loads(dec.to_json(orient="records"))

# ---------- deadliest eruptions (NOAA NCEI) ----------
N["deaths"] = pd.to_numeric(N.deaths, errors="coerce")
R["ncei"] = {"n": len(N), "deaths": float(N.deaths.sum()), "y0": int(N.year.min()), "y1": int(N.year.max()),
             "since1900": float(N[N.year >= 1900].deaths.sum()), "n_since1900": int((N.year >= 1900).sum()),
             "top": [{"y": int(r.year), "vnum": None if pd.isna(r.vnum) else int(r.vnum), "name": r.name, "country": r.country, "deaths": float(r.deaths), "vei": None if pd.isna(r.vei) else int(r.vei)}
                     for r in N.sort_values("deaths", ascending=False).head(12).itertuples()]}
vd = N.dropna(subset=["vnum"]).groupby("vnum").deaths.sum()
R["ncei"]["n_volc"] = int(len(vd))
# the deadliest volcanoes, by how many live near them today
dead = VP.set_index("vnum").join(vd.rename("deaths"), how="inner").sort_values("deaths", ascending=False).head(10)
R["ncei"]["dead_volc"] = [{"name": n, "deaths": float(d), "p30": float(p)} for n, d, p in zip(dead.name, dead.deaths, dead.p30)]

# ---------- types, settings, elevation ----------
R["by_type"] = json.loads(VP.groupby("type").agg(n=("vnum", "size"), sum30=("p30", "sum")).sort_values("sum30", ascending=False).head(8).reset_index().to_json(orient="records"))
R["strato_share_sum30"] = 100 * VP[VP.type == "Stratovolcano"].p30.sum() / VP.p30.sum()
R["n_strato"] = int((V.type == "Stratovolcano").sum())
R["subduction_share_sum30"] = 100 * VP[VP.tectonic.str.startswith("Subduction")].p30.sum() / VP.p30.sum()
R["n_subduction"] = int(V.tectonic.str.startswith("Subduction").sum())
R["high_crowd"] = [vrow(t) for _, t in VP[VP.elev >= 4000].sort_values("p30", ascending=False).head(5).iterrows()]

flat = VP[(VP.p10 == VP.p30) & (VP.p30 > 1e4)]
R["n_flat"] = int(len(flat)); R["flat_names"] = flat.name.tolist()
R["n_fields"] = int((V.type == "Volcanic field").sum())
# ---------- checks on facts quoted in words ----------
print("TOP30", R["top30"][0]["name"])
assert G["10"]["floor"] <= G["10"]["sum"] and G["100"]["floor"] < G["100"]["sum"]
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: R[k] for k in ("n_volc", "n_pop", "n_countries", "glob", "n30_1m", "n10_100k", "n100_10m", "top20_share30", "glob_share_floor_100")}, indent=1))
print("countries by sum30", R["c_rank_sum30"]); print("by floor30", R["c_rank_floor30"]); print("floor10", R["c_rank_floor10"]); print("floor100", R["c_rank_floor100"])
for r in (10, 30, 100):
    print(r, [(t["name"], t["country"], int(t[f"p{r}"])) for t in R[f"top{r}"][:12]])
print("recent", [(t["name"], t["last"], int(t["p30"])) for t in R["recent"][:12]])
print("by_ecls", [(b["k"], b["n"], int(b["floor30"]), int(b["sum30"])) for b in R["by_ecls"]])
print("since1900", R["since1900"], "latest2", {k: v for k, v in R["latest2"].items() if k != "top"}, [(t["name"], int(t["p30"])) for t in R["latest2"]["top"]])
print("cent", [(c["c"], c["n"], c["vei4"]) for c in R["centuries"]][-10:], R["ratio_all_1900_1600"], R["ratio_vei4_1900_1600"])
print("missing named", miss, "ncei", R["ncei"]["deaths"], [(t["name"], t["y"], t["deaths"]) for t in R["ncei"]["top"][:6]])
print("strato", R["strato_share_sum30"], "subd", R["subduction_share_sum30"], "vei7", R["vei7"], R["vei6_since1500"])

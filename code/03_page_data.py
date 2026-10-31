"""Page data: data/page/volcanoes.json (every Holocene volcano with its attributes, populations and eruption counts),
data/page/world.json (country outlines, simplified), data/page/cities.json (city labels), data/page/plates.json
(plate boundaries, simplified). Natural Earth is public domain; PB2002 (Bird 2003, GeoJSON by Hugo Ahlenius, Nordpil)
is ODC-By 1.0."""
import pandas as pd
from shapely.geometry import shape, mapping, LineString, MultiLineString
from common import *

C = jload(f"{WORK}/clean.json")
V = pd.DataFrame(C["V"]); N = pd.DataFrame(C["N"])
# common names for some GVP primary names (display and search only; GVP names are kept in the data)
ALIAS = {"Aira": "Sakurajima", "Fujisan": "Mount Fuji", "Popocatepetl": "Popocatépetl", "Pelee": "Mont Pelée", "Ruiz, Nevado del": "Nevado del Ruiz",
         "Misti, El": "El Misti", "Michoacan-Guanajuato": "includes Parícutin", "Tatun Volcanic Group": "Taipei", "Campi Flegrei": "Phlegraean Fields, Naples",
         "Vesuvius": "Naples", "Unzendake": "Mount Unzen", "Asosan": "Mount Aso", "Hakoneyama": "Hakone", "Gede-Pangrango": "Gede", "Krakatau": "Krakatoa",
         "Soufriere Hills": "Montserrat", "Soufriere St. Vincent": "La Soufrière", "Rainier": "Mount Rainier", "St. Helens": "Mount St. Helens",
         "Hood": "Mount Hood", "Kilauea": "Hawaii", "Mauna Loa": "Hawaii", "Teide": "Tenerife", "La Palma": "Cumbre Vieja", "Ilopango": "San Salvador",
         "Reykjanes": "Grindavík, Svartsengi", "Hunga Tonga-Hunga Ha'apai": "Hunga Tonga", "Santorini": "Thera", "Agua": "Antigua", "Ararat": "Ağrı Dağı",
         "Damavand": "Tehran", "Kilimanjaro": "Tanzania", "Erciyes Dagi": "Kayseri", "Colli Albani": "Alban Hills, Rome", "Etna": "Sicily"}
dead = N.dropna(subset=["vnum"]).sort_values("deaths", ascending=False).drop_duplicates("vnum").set_index("vnum")
tot = N.dropna(subset=["vnum"]).groupby("vnum").deaths.sum()
EK = [e[0] for e in ECLS]
num = lambda v: None if v is None or pd.isna(v) else int(v)
out = []
for t in V.sort_values("p30", ascending=False, na_position="last").itertuples():
    d = dead.loc[t.vnum] if t.vnum in dead.index else None
    out.append([int(t.vnum), t.name, ALIAS.get(t.name, ""), t.country, round(t.lat, 3), round(t.lon, 3), num(t.elev), t.type, t.last_txt, num(t.last),
                EK.index(t.ecls), num(t.p5), num(t.p10), num(t.p30), num(t.p100), int(t.n_erupt), num(t.max_vei), t.isos, t.tectonic, t.rock,
                [int(d.year), int(d.deaths), int(tot.loc[t.vnum])] if d is not None and not pd.isna(d.deaths) else None, int(bool(t.continuing))])
jsave(out, f"{PAGE}/volcanoes.json")


def rnd(c):
    return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 2), round(c[1], 2)]


feats = []
for f in jload(NE50)["features"]:
    p = f["properties"]
    g = shape(f["geometry"]).simplify(0.07, preserve_topology=True)
    if g.is_empty or p["ADM0_A3"] == "ATA":
        continue
    gj = mapping(g)
    feats.append({"type": "Feature", "properties": {"iso": p["ADM0_A3"], "n": C["iso_name"].get(p["ADM0_A3"], p.get("NAME_EN") or p["NAME"])},
                  "geometry": {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}})
jsave({"type": "FeatureCollection", "features": feats}, f"{PAGE}/world.json")

cities = []
for f in jload(PLACES)["features"]:
    p = f["properties"]
    lon, lat = f["geometry"]["coordinates"]
    if (p.get("pop_max") or 0) >= 200000:
        cities.append({"name": p["name"], "lat": round(lat, 3), "lon": round(lon, 3), "pop": int(p["pop_max"])})
cities.sort(key=lambda c: -c["pop"])
jsave(cities, f"{PAGE}/cities.json")

pl = []
for f in jload(PLATES)["features"]:
    g = shape(f["geometry"]).simplify(0.05)
    lines = [g] if g.geom_type == "LineString" else list(g.geoms)
    for ln in lines:
        cs = [[round(y, 2), round(x, 2)] for x, y in ln.coords]
        # split where the line jumps across the antimeridian
        seg = [cs[0]]
        for a, b in zip(cs, cs[1:]):
            if abs(a[1] - b[1]) > 180:
                pl.append(seg); seg = []
            seg.append(b)
        if len(seg) > 1:
            pl.append(seg)
jsave(pl, f"{PAGE}/plates.json")
print(len(out), "volcanoes;", len(feats), "countries;", len(cities), "cities;", len(pl), "plate lines;",
      {f: os.path.getsize(f"{PAGE}/{f}") // 1024 for f in os.listdir(PAGE)}, "KB")

ct = pd.read_csv(f"{DATA}/countries.csv")
jsave([[r.iso, r.name, int(r.n), int(r.n_since1900), int(r.n_since2000), int(r.n_erupt), round(r.floor10), round(r.sum10), round(r.floor30), round(r.sum30),
        round(r.floor100), round(r.sum100), r.top if isinstance(r.top, str) else ""] for r in ct.itertuples()], f"{PAGE}/countries.json")

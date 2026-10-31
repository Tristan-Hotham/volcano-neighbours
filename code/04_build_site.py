"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (volcanoes, countries, world, cities, plates) is embedded. Facts stated in words are checked
here against the results. The full-screen map snippet (copied from the drinks-map reference) goes before </body>.
10.5281/zenodo.23847550 and https://blog.tristanhotham.com/2026/10/31/volcano-neighbours/ are left for the publisher to fill."""
import re
from common import *

R = jload(f"{DATA}/results.json")
names = lambda L, n: [t["name"] for t in L[:n]]
# facts stated in words (page, and reused by the blog, paper and collage)
assert R["c_rank_floor30"][:5] == ["IDN", "MEX", "JPN", "PHL", "ITA"], R["c_rank_floor30"]
assert R["c"]["TWN"]["n"] == 2 and R["c"]["TWN"]["top"] == "Tatun Volcanic Group"
cn = sorted(R["c"].values(), key=lambda c: -c["n"])
assert [c["iso"] for c in cn[:3]] == ["USA", "JPN", "IDN"], [c["iso"] for c in cn[:3]]
assert all(R["c"][i]["floor30"] < 1.5e6 for i in ("RUS", "CHL", "ISL")) and all(R["c"][i]["n"] >= 35 for i in ("RUS", "CHL", "ISL"))
assert names(R["top30"], 5) == ["Tatun Volcanic Group", "Michoacan-Guanajuato", "Tangkuban Parahu", "Penanggungan", "Merapi"]
assert names(R["top10"], 4) == ["Michoacan-Guanajuato", "Tatun Volcanic Group", "Campi Flegrei", "Ilopango"]
assert names(R["top100"], 2) == ["Gede-Pangrango", "Salak"] and R["top100"][1]["p100"] > 38e6
assert "Hakoneyama" in names(R["top100"], 6) and R["v"]["fuji"]["p100"] > 2e7
assert R["top10"][0]["p5"] == R["top10"][0]["p100"] == R["top10"][0]["p10"]         # "at every distance"
assert names(R["recent"], 5) == ["Tangkuban Parahu", "Merapi", "Slamet", "Pacaya", "Taal"]
assert [t["name"] for t in R["latest2"]["top"][:2]] == ["Mayon", "Poas"]
assert R["by_ecls"][0]["k"] == "2000" and R["by_ecls"][5]["k"] == "unk"
assert R["ncei"]["y0"] == -141 and [t["name"] for t in R["ncei"]["top"][:5]] == ["Tambora", "Krakatau", "Ilopango", "Pelee", "Ruiz, Nevado del"]
assert [t["y"] for t in R["ncei"]["top"][:5]] == [1815, 1883, 450, 1902, 1985]
assert 20 <= R["ves_cf_km"] <= 30 and R["v"]["vesuvius"]["p30"] > 3e6 and R["v"]["flegrei"]["p30"] > 2.5e6   # "most of the city lies within 30 km of both"
assert R["glob"]["10"]["floor"] / R["glob"]["10"]["sum"] > .9                                                # "the two bounds almost meet"
assert R["glob"]["100"]["floor"] < 8e8 < R["glob"]["100"]["sum"]                                                # Brown et al. figure lies between the bounds
assert R["rate_2000"] > R["rate_1900"]
assert R["cc"]["2000"]["years"] == R["latest_year"] - 1999


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl, R)
    assert not re.search(r"\{\{(?!DOI\}\}|BLOG_URL\}\})", html), re.findall(r"\{\{[^}]*\}\}", html)[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    rd = lambda f: open(f"{PAGE}/{f}", encoding="utf-8").read()
    html = html.replace("/*RESULTS*/", J(R)).replace("/*VOLCANOES*/", rd("volcanoes.json")).replace("/*WORLD*/", rd("world.json"))
    html = html.replace("/*CITIES*/", rd("cities.json")).replace("/*PLATES*/", rd("plates.json")).replace("/*COUNTRIES*/", rd("countries.json"))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    check_dashes(vis, "page text")
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    for bad in ("DSIT", "DCMS", "civil serv", "Civil Serv"):
        assert bad not in html, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()

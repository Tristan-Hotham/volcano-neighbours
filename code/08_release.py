"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23847550, https://doi.org/10.5281/zenodo.23847550 and https://blog.tristanhotham.com/2026/10/31/volcano-neighbours/ are left for the publisher to fill."""
import re, shutil, zipfile, json as _json
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release")
NAME = "Hotham_In_the_Shadow_of_the_Volcano"
m1 = lambda v: round(v / 1e6, 1)

# numbers written out in the blog's alt text, checked against results
V = pd.read_csv(f"{DATA}/volcanoes.csv")
J = V[(V.lon > 104.8) & (V.lon < 115.2) & (V.lat > -9.2) & (V.lat < -5.6) & V.population_within_30km.notna()]
assert len(J) == 33, len(J)
ct = {c["iso"]: c for c in R["countries"]}
assert [round(ct[i]["floor30"] / 1e6, 1) for i in ("IDN", "MEX", "JPN", "PHL", "ITA", "TWN")] == [41.8, 18.7, 10.1, 9.7, 8.2, 6.7]
assert R["c_rank_floor30"][6:10] == ["GTM", "SLV", "ETH", "ECU"]
G = R["glob"]
assert round(G["5"]["floor"] / 1e6) == round(G["5"]["sum"] / 1e6) == 42 and (round(G["10"]["floor"] / 1e6), round(G["10"]["sum"] / 1e6)) == (53, 56)
assert (round(G["30"]["floor"] / 1e6), round(G["30"]["sum"] / 1e6), round(G["100"]["floor"] / 1e6), round(G["100"]["sum"] / 1e7) / 100) == (147, 274, 532, 2.47)
assert [m1(t["p30"]) for t in R["top30"][:5]] == [6.7, 5.8, 5.7, 4.6, 4.3]
assert {"Chichinautzin", "Vesuvius", "Campi Flegrei", "Ilopango"} <= {t["name"] for t in R["top30"]}
assert [(m1(t["p30"]), t["last"]) for t in R["recent"][:5]] == [(5.7, 2019), (4.3, 2026), (2.9, 2014), (2.5, 2021), (2.4, 2026)]
assert [t["name"] for t in R["recent"][5:8]] == ["Kelud", "Guagua Pichincha", "Masaya"]
cs = {c["c"]: c for c in R["centuries"]}
assert 1400 < cs[1800]["n"] < 1600 and 2800 < cs[1900]["n"] < 3000 and cs[1900]["vei4"] == 64
assert min(cs[c]["vei4"] for c in range(0, 1500, 100)) == 7 and max(cs[c]["vei4"] for c in range(0, 1500, 100)) == 18
assert [t["name"] for t in R["ncei"]["top"]][:4] == ["Tambora", "Krakatau", "Ilopango", "Pelee"]

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = fill(post, R)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for line in post.splitlines():
    if "{{IMG|" in line:
        assert line.startswith("{{IMG|") and line.endswith("}}"), line[:60]
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert not re.search(r"\{\{(?!IMG\||DOI_URL\}\})", post), re.findall(r"\{\{[^}]*\}\}", post)[:5]
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
check_dashes(vis, "blog")
assert AI in post
for bad in ("DSIT", "DCMS", "civil serv"):
    assert bad not in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "In the shadow of the volcano: who lives near the world's volcanoes",
        "slug": "volcano-neighbours",
        "excerpt": f"I mapped all {R['n_volc']:,} of the world's Holocene volcanoes and the people around them. At least {G['30']['floor'] / 1e6:.0f} million people live within 30 km of one, and {R['n30_1m']} volcanoes have a million or more neighbours.",
        "seo_description": "A map of the world's Holocene volcanoes and the people living within 10, 30 and 100 km of them, by country, by volcano and by last eruption.",
        "tags": ["volcanoes", "population", "maps", "data visualisation", "Ring of Fire", "Indonesia", "natural hazards"],
        "header_alt": f"Title card reading 'In the shadow of the volcano' in black and red on pale paper, beside a Pacific-centred world map with dashed plate boundaries and volcanoes drawn as circles sized by nearby population, largest on Java, Taiwan, the Philippines and in Mexico. Text: at least {G['30']['floor'] / 1e6:.0f} million people live within 30 km of one of the world's {R['n_volc']:,} Holocene volcanoes."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/volcano-neighbours_code_and_data.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data", "data/page"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            p = os.path.join(ROOT, d, fn)
            if os.path.isdir(p) or fn.endswith(".pyc"):
                continue
            z.write(p, f"volcano-neighbours/{d}/{fn}")
    for fn in ("README.md", "LICENSE", "reddit/collage.py"):
        if os.path.exists(os.path.join(ROOT, fn)):
            z.write(os.path.join(ROOT, fn), f"volcano-neighbours/{fn}")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("Michoac\\'an", "Michoacán")
assert "\\" not in ab, ab
zmeta = {"title": "In the Shadow of the Volcano: How Many People Live Near the World's Holocene Volcanoes, from the Smithsonian's Volcanoes of the World Database",
         "upload_type": "publication", "publication_type": "workingpaper",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{URL}\">{URL}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p>"
                        f"<p>Data: {GVP_CITE}. {GVP_CITE_POP}. NOAA NCEI Global Significant Volcanic Eruptions Database, doi:10.7289/V5JW8BSH. Bird (2003) plate boundaries (ODC-By 1.0). Natural Earth.</p>"
                        "<p>Licences: the paper is CC BY 4.0 and the code MIT. The tables in data/ are derived from the Smithsonian Global Volcanism Program database and are shared under the Smithsonian's terms of use (non-commercial use with credit), not under CC BY. This work is not endorsed by the Smithsonian Institution.</p>"
                        f"<p>{AI}</p>",
         "keywords": ["volcanoes", "population exposure", "Holocene", "Global Volcanism Program", "Volcanoes of the World", "Ring of Fire", "reporting bias", "maps"],
         "license": "cc-by-4.0",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": URL, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://volcano.si.edu/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "10.7289/V5JW8BSH", "relation": "isDerivedFrom", "resource_type": "dataset", "scheme": "doi"}]}
jsave(zmeta, f"{Z}/metadata.json", indent=2)
s = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
check_dashes(s, "metadata")
print("blog words", words, "; images", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")

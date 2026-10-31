"""Reddit collage (2400 x 3000, light): a Pacific-centred world map of Holocene volcanoes sized by people within 30 km,
with plate boundaries (the Ring of Fire), callouts on open sea, and panels for countries and the most crowded volcanoes.
Every number comes from data/results.json. Run from the repo root or anywhere: python3 reddit/collage.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
V = pd.read_csv(f"{DATA}/volcanoes.csv")
OUT = os.path.join(ROOT, "reddit", "in_the_shadow_of_the_volcano.png")
P30MAX = 6.8e6
HALO = [pe.withStroke(linewidth=4, foreground=BG)]
m = lambda v: (f"{v / 1e6:.1f}m" if v < 1e7 else f"{v / 1e6:.0f}m").replace(".0m", "m")
DN = {"Tatun Volcanic Group": "Tatun group", "Michoacan-Guanajuato": "Michoacán-Guanajuato", "Popocatepetl": "Popocatépetl",
      "San Pablo Volcanic Field": "San Pablo field", "Chichinautzin": "Chichinautzin"}
dn = lambda n: DN.get(n, n)

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
# ---------- title ----------
fig.text(.04, .962, "In the shadow of the volcano", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(.04, .905, f"At least {R['glob']['30']['floor'] / 1e6:.0f} million people live within 30 km of one of the world's {R['n_volc']:,} Holocene volcanoes,\n"
                    "counting each person once. Each circle is a volcano, sized by the people within 30 km and coloured by its last eruption.",
         fontproperties=SERP, fontsize=15.5, color=FG, va="top", linespacing=1.45)

# ---------- map ----------
ax = fig.add_axes([0, .45, 1, .40])
ext = worldmap(ax, lw=.35)
for x, y in plates_xy():
    ax.plot(x, y, color=HOT, lw=1.0, alpha=.45, ls=(0, (3, 2)), zorder=2)
d = V.sort_values("population_within_30km", ascending=False, na_position="first")
x, y = xy(d.lon.values, d.lat.values)
s = np.maximum(3, 900 * d.population_within_30km.fillna(0).values / P30MAX)
ax.scatter(x, y, s=s, c=[ECOL[k] for k in d.last_eruption_class], alpha=.85, edgecolors="#fff", linewidths=.5, zorder=5)


SEAL = []


def sea(lon, lat, text, size=13, col=COOL, style="italic", ha="center", rot=0, sp=0):
    X, Y = xy(lon, lat)
    SEAL.append(ax.text(X, Y, text, fontsize=size, color=col, style=style, ha=ha, va="center", rotation=rot, zorder=7, path_effects=HALO, fontproperties=SERP))


sea(-150, 1, "P A C I F I C   O C E A N", 15)
sea(72, -5, "I N D I A N   O C E A N", 12.5)
sea(-38, 20, "ATLANTIC", 11.5, ha="right")
sea(-178, -55, "the Ring of Fire: plate boundaries (dashed)\nring the Pacific with volcanoes", 11, col=HOT, style="italic")

CALL = [  # volcano, label lon/lat (on open sea or paper), alignment, label
    ("Fujisan", 166, 47, "left", "Fuji, near Tokyo"),
    ("Tatun Volcanic Group", 166, 31, "left", "Tatun group, Taipei"),
    ("Taal", 166, 15, "left", "Taal, near Manila"),
    ("Tangkuban Parahu", 100, -30, "right", "Tangkuban Parahu, Bandung"),
    ("Merapi", 100, -46, "right", "Merapi, Yogyakarta"),
    ("Michoacan-Guanajuato", -101, -9, "right", "Michoacán-Guanajuato (incl. Parícutin)"),
    ("Popocatepetl", -95, -24.5, "right", "Popocatépetl, near Mexico City"),
    ("Pacaya", -89, -40, "right", "Pacaya, Guatemala City"),
    ("Vesuvius", 2, 86, "left", "Vesuvius, Naples"),
]
LABELS = []
for name, lo, la, ha, lab in CALL:
    t = V[V.name == name].iloc[0]
    X0, Y0 = xy(t.lon, t.lat); X1, Y1 = xy(lo, la)
    if la > 85:   # above the map, on paper
        Y1 = ext[3] + 0.3e6
    lab = lab or dn(name)
    sep = ": " if la > 85 else "\n"
    txt = f"{lab}{sep}{m(t.population_within_30km)} within 30 km{', ' if la > 85 else chr(10)}last erupted {t.last_known_eruption.replace(' CE', '')}"
    ax.plot([X0, X1], [Y0, Y1], color=FG, lw=.7, zorder=6, alpha=.75)
    LABELS.append(ax.text(X1 + (8e4 if ha == "left" else -8e4), Y1, txt, fontsize=9.3, ha=ha, va="center", color=FG, zorder=8, path_effects=HALO, linespacing=1.1))
ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])

# ---------- legend ----------
lg = fig.add_axes([.04, .405, .92, .04]); lg.axis("off"); lg.set_xlim(0, 1); lg.set_ylim(0, 1)
lg.text(0, .82, "Last known eruption", fontsize=11, color=FG, fontweight="medium", va="center")
for i, (k, lab, _, _, col) in enumerate(ECLS):
    xx = (i % 3) * .2; yy = .42 - (i // 3) * .42
    lg.scatter([xx + .008], [yy], s=110, color=col, edgecolors="#fff", clip_on=False)
    lg.text(xx + .022, yy, lab.replace(" (Holocene)", ""), fontsize=10.5, va="center", color=FG)
lg.text(.66, .82, "People within 30 km (circle area)", fontsize=11, color=FG, fontweight="medium", va="center")
for j, (p, l) in enumerate(((1e5, "100,000"), (1e6, "1 million"), (5e6, "5 million"))):
    lg.scatter([.675 + j * .11], [.25], s=max(3, 900 * p / P30MAX), facecolors="none", edgecolors=MUT, linewidths=1, clip_on=False)
    lg.text(.69 + j * .11 + (.012 if p > 2e6 else 0), .25, l, fontsize=10, va="center", color=FG)

# ---------- stats row ----------
st = [(f"{R['glob']['30']['floor'] / 1e6:.0f}m+", HOT, "people within 30 km of one,\neach counted once (at least)"),
      (f"{R['n30_1m']}", FG, "volcanoes with a million\nor more within 30 km"),
      (f"{R['c']['IDN']['floor30'] / 1e6:.0f}m+", "#C98A0B", "of them in Indonesia,\nthe most of any country"),
      (f"{R['recent_n30_1m']}", COOL, "million-plus volcanoes that\nhave erupted since 2000")]
for i, (big, col, sub) in enumerate(st):
    X = .04 + i * .235
    fig.text(X, .392, big, fontproperties=DISP, fontsize=40, color=col, va="top")
    fig.text(X, .343, sub, fontsize=11.5, color=FG, va="top", linespacing=1.4)

# ---------- panels ----------
C = sorted(R["countries"], key=lambda c: -c["floor30"])[:12]
a1 = fig.add_axes([.17, .11, .30, .15], facecolor=BG)
yy = np.arange(len(C))
a1.barh(yy, [c["sum30"] / 1e6 for c in C], color=HOT, alpha=.2, height=.7)
a1.barh(yy, [c["floor30"] / 1e6 for c in C], color=HOT, height=.7)
for yv, c in zip(yy, C):
    a1.text(c["sum30"] / 1e6 + 1.2, yv, m(c["floor30"]), va="center", fontsize=10)
a1.set_yticks(yy); a1.set_yticklabels([c["name"] for c in C], fontsize=10.5); a1.invert_yaxis(); a1.set_xlim(0, 100)
a1.tick_params(axis="x", labelsize=9); a1.set_xlabel("millions", fontsize=9.5, color=MUT)
for sp in ("top", "right"): a1.spines[sp].set_visible(False)
fig.text(.04, .283, "Countries: people within 30 km of their volcanoes", fontsize=12.5, color=FG, fontweight="medium")
fig.text(.04, .27, "solid: each person once (at least)   pale: simple sum", fontsize=9.8, color=MUT)

T = R["top30"][:12]
a2 = fig.add_axes([.71, .11, .25, .15], facecolor=BG)
yy = np.arange(len(T))
a2.barh(yy, [t["p30"] / 1e6 for t in T], color=[ECOL[t["ecls"]] for t in T], height=.7)
for yv, t in zip(yy, T):
    a2.text(t["p30"] / 1e6 + .1, yv, m(t["p30"]), va="center", fontsize=10)
a2.set_yticks(yy); a2.set_yticklabels([f"{dn(t['name'])}, {t['country'].replace('Philippines', 'Phil.').replace('Indonesia', 'Indon.')}" for t in T], fontsize=10.2); a2.invert_yaxis(); a2.set_xlim(0, 8.2)
a2.tick_params(axis="x", labelsize=9); a2.set_xlabel("millions", fontsize=9.5, color=MUT)
for sp in ("top", "right"): a2.spines[sp].set_visible(False)
fig.text(.52, .283, "The most crowded volcanoes: people within 30 km", fontsize=12.5, color=FG, fontweight="medium")
fig.text(.52, .27, "coloured by last eruption, as on the map", fontsize=9.8, color=MUT)

# ---------- footer ----------
fig.text(.04, .074, "Source: Smithsonian Global Volcanism Program, Volcanoes of the World 5.3.5 (volcano.si.edu, via GitHub mirrors).\n"
                    "Population within 30 km: the GVP's own figures from v. 5.1.7, a fixed snapshot. Plate boundaries: Bird (2003), via Nordpil.\n"
                    "Outlines: Natural Earth. 'At least' sums only volcanoes whose circles do not overlap. Distances are not hazard zones.\n"
                    "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/volcano-neighbours",
         fontsize=9.6, color=MUT, va="top", linespacing=1.5)
# check: every map label sits on open sea or paper, clear of land and of volcano circles
from shapely.geometry import box as sbox, Polygon as SPoly, Point as SPt
from shapely.ops import unary_union
fig.canvas.draw()
land = unary_union([SPoly(r).buffer(0) for iso, rings in world_shapes() if iso != "ATA" for r in rings if len(r) > 3]).intersection(sbox(ext[0], ext[2], ext[1], ext[3]))   # land as drawn (clipped to the map)
inv = ax.transData.inverted(); px = (ax.transData.transform((1e6, 0))[0] - ax.transData.transform((0, 0))[0]) / 1e6   # pixels per metre
dotsg = [SPt(a, b).buffer(np.sqrt(sz / np.pi) * 200 / 72 / px) for a, b, sz in zip(x, y, s) if sz > 20]
bad = []
for t in LABELS + SEAL:
    e = t.get_window_extent(); (a0, b0), (a1, b1) = inv.transform([(e.x0, e.y0), (e.x1, e.y1)])
    bx = sbox(a0, b0, a1, b1)
    over_land = bx.intersection(land).area / bx.area
    over_dots = sum(1 for g in dotsg if g.intersects(bx))
    if over_land > .01 or over_dots:
        bad.append((t.get_text().split(chr(10))[0], round(over_land, 3), over_dots))
boxes = []
for t in LABELS + SEAL:
    e = t.get_window_extent(); boxes.append((t.get_text().split(chr(10))[0], sbox(e.x0, e.y0, e.x1, e.y1)))
for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
        if boxes[i][1].intersects(boxes[j][1]):
            bad.append(("overlap", boxes[i][0], boxes[j][0]))
print("labels over land or data:", bad or "none")
fig.savefig(OUT, dpi=200, facecolor=BG)
print(OUT)

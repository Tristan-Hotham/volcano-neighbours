"""Static figures: header.png (1200 x 630), paper figures (release/paper/f_*.png) and blog figures (release/blog/b_*.png).
Every number drawn comes from data/results.json or data/volcanoes.csv."""
import shutil
import pandas as pd
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
V = pd.read_csv(f"{DATA}/volcanoes.csv")
VP = V[V.population_within_30km.notna()].copy()
PAP = os.path.join(ROOT, "release", "paper"); BLOG = os.path.join(ROOT, "release", "blog")
for d in (PAP, BLOG):
    os.makedirs(d, exist_ok=True)
DN = {"Tatun Volcanic Group": "Tatun group (Taipei)", "Michoacan-Guanajuato": "Michoacán-Guanajuato", "Popocatepetl": "Popocatépetl",
      "Aira": "Aira (Sakurajima)", "Fujisan": "Fuji", "Campi Flegrei": "Campi Flegrei", "San Pablo Volcanic Field": "San Pablo field",
      "Gede-Pangrango": "Gede-Pangrango", "Hakoneyama": "Hakone", "Poas": "Poás", "Pelee": "Pelée", "Ruiz, Nevado del": "Nevado del Ruiz",
      "Guagua Pichincha": "Guagua Pichincha (Quito)", "Dieng Volcanic Complex": "Dieng complex", "Chichinautzin": "Chichinautzin (Mexico City)"}
dn = lambda n: DN.get(n, n)
ECK = [e[0] for e in ECLS]
P30MAX = 6.8e6
assert R["top30"][0]["name"] == "Tatun Volcanic Group" and round(R["top30"][0]["p30"] / 1e6, 1) == 6.7 and R["top30"][0]["p30"] <= P30MAX


def dots(ax, df, col="population_within_30km", smax=420, alpha=.85, ec="#FFFFFF", lw=.4, minsize=2.5, zorder=5):
    d = df.sort_values(col, ascending=False, na_position="first")
    x, y = xy(d.lon.values, d.lat.values)
    p = d[col].fillna(0).values
    s = np.maximum(minsize, smax * p / P30MAX)
    ax.scatter(x, y, s=s, c=[ECOL[k] for k in d.last_eruption_class], alpha=alpha, edgecolors=ec, linewidths=lw, zorder=zorder)


def plates(ax, lw=.8, alpha=.55):
    for x, y in plates_xy():
        ax.plot(x, y, color=HOT, lw=lw, alpha=alpha, ls=(0, (3, 2)), zorder=2)


# ---------- world map (paper and blog) ----------
fig = plt.figure(figsize=(12, 6.6), facecolor=BG); ax = fig.add_axes([0, .08, 1, .92])
worldmap(ax); plates(ax); dots(ax, V)
hs = [Line2D([], [], marker="o", ls="", ms=8, mfc=ECOL[k], mec="#fff", label=ELAB[k]) for k in ECK]
fig.legend(handles=hs, loc="lower left", ncol=6, frameon=False, fontsize=9.5, title="Last known eruption", title_fontsize=9.5, bbox_to_anchor=(.01, 0), alignment="left")
for p, lab in ((1e5, "100k"), (1e6, "1m"), (5e6, "5m")):
    ax.scatter([], [], s=420 * p / P30MAX, c="none", edgecolors=MUT, label=lab)
fig.text(.99, .985, "Circle area: people within 30 km (largest: 6.7 million, Tatun group, Taipei).  Dashed lines: plate boundaries.", ha="right", va="top", fontsize=9, color=MUT)
save(fig, f"{PAP}/f_map.png")

# ---------- global bounds ----------
fig, ax = plt.subplots(figsize=(9, 3.4), facecolor=BG); ax.set_facecolor(BG)
for i, r in enumerate(RINGS):
    g = R["glob"][str(r)]
    ax.barh(i, g["sum"] / 1e6, color=HOT, alpha=.22, height=.6); ax.barh(i, g["floor"] / 1e6, color=HOT, height=.6)
    ax.text(g["sum"] / 1e6 + 25, i, f"at least {mshort(g['floor'])}; sum {mshort(g['sum'])}", va="center", fontsize=10)
ax.set_yticks(range(4)); ax.set_yticklabels([f"within {r} km" for r in RINGS]); ax.invert_yaxis()
ax.set_xlabel("people (millions)"); ax.set_xlim(0, 3300)
for s in ("top", "right"): ax.spines[s].set_visible(False)
fig.tight_layout(); save(fig, f"{PAP}/f_bounds.png")

# ---------- countries ----------
C = pd.DataFrame(R["countries"]); C = C.sort_values("floor30", ascending=False).head(15)
fig, ax = plt.subplots(figsize=(9, 5.6), facecolor=BG); ax.set_facecolor(BG)
yy = np.arange(len(C))
ax.barh(yy, C.sum30 / 1e6, color=HOT, alpha=.22, height=.66, label="sum over volcanoes (upper bound)")
ax.barh(yy, C.floor30 / 1e6, color=HOT, height=.66, label="each person counted once (lower bound)")
for y, f, s in zip(yy, C.floor30, C.sum30):
    ax.text(s / 1e6 + 1, y, f"{mshort(f)}", va="center", fontsize=9.5)
ax.set_yticks(yy); ax.set_yticklabels(C.name); ax.invert_yaxis(); ax.set_xlabel("people within 30 km of the country's Holocene volcanoes (millions)")
ax.legend(frameon=False, loc="lower right", fontsize=9.5)
for s in ("top", "right"): ax.spines[s].set_visible(False)
fig.tight_layout(); save(fig, f"{PAP}/f_countries.png")


# ---------- top volcanoes ----------
def topbars(rows, name, title_x, lab=lambda r: mshort(r["p30"]), key="p30", h=6.4):
    fig, ax = plt.subplots(figsize=(9, h), facecolor=BG); ax.set_facecolor(BG)
    yy = np.arange(len(rows))
    ax.barh(yy, [r[key] / 1e6 for r in rows], color=[ECOL[r["ecls"]] for r in rows], height=.68)
    mx = max(r[key] for r in rows) / 1e6
    for y, r in zip(yy, rows):
        ax.text(r[key] / 1e6 + mx * .01, y, lab(r), va="center", fontsize=9.5)
    ax.set_yticks(yy); ax.set_yticklabels([f"{dn(r['name'])}{' *' if r.get('flat') else ''}, {r['country'].split(' - ')[0]}" for r in rows], fontsize=9.5); ax.invert_yaxis()
    ax.set_xlabel(title_x); ax.set_xlim(0, mx * 1.18)
    present = [k for k in ECK if any(r["ecls"] == k for r in rows)]
    ax.legend(handles=[Line2D([], [], marker="s", ls="", ms=9, mfc=ECOL[k], mec=ECOL[k], label=ELAB[k]) for k in present], frameon=False, loc="lower right", fontsize=9, title="last eruption", title_fontsize=9)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.tight_layout(); save(fig, name)


topbars(R["top30"], f"{PAP}/f_top30.png", "people within 30 km (millions); * same at 10 and 30 km")
topbars(R["recent"], f"{PAP}/f_recent.png", "people within 30 km (millions), erupted since 2000", lab=lambda r: f"{mshort(r['p30'])} · {r['last']}")

# ---------- by last eruption ----------
B = R["by_ecls"]
fig, ax = plt.subplots(figsize=(9, 3.6), facecolor=BG); ax.set_facecolor(BG)
for i, b in enumerate(B):
    ax.barh(i, b["sum30"] / 1e6, color=b["col"], alpha=.25, height=.62); ax.barh(i, b["floor30"] / 1e6, color=b["col"], height=.62)
    ax.text(b["sum30"] / 1e6 + .8, i, f"at least {mshort(b['floor30'])} ({b['n']} volcanoes)", va="center", fontsize=9.5)
ax.set_yticks(range(len(B))); ax.set_yticklabels([b["label"] for b in B]); ax.invert_yaxis(); ax.set_xlim(0, 112)
ax.set_xlabel("people within 30 km (millions): solid, each once; pale, sum")
for s in ("top", "right"): ax.spines[s].set_visible(False)
fig.tight_layout(); save(fig, f"{PAP}/f_ecls.png")

# ---------- centuries ----------
D = pd.DataFrame(R["centuries"])
fig, axs = plt.subplots(2, 1, figsize=(9, 5.4), facecolor=BG, sharex=True)
for ax, key, col, t in ((axs[0], "n", "#E8743B", "all confirmed eruptions"), (axs[1], "vei4", "#7A1712", "eruptions of VEI 4 or more")):
    ax.set_facecolor(BG)
    ax.bar(D.c + 50, D[key], width=86, color=[col if c < 2000 else col + "80" for c in D.c])
    ax.set_title(t, loc="left", fontsize=11)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
axs[1].set_xlabel(f"century of eruption start (last bar: 2000 to {R['latest_year']})")
axs[1].set_xticks(range(0, 2100, 200)); fig.tight_layout(); save(fig, f"{PAP}/f_centuries.png")

# ---------- Java: 30 km circles overlap ----------
bb = (104.8, 115.2, -9.2, -5.6)
fig = plt.figure(figsize=(12, 4.9), facecolor=BG); ax = fig.add_axes([0, .1, 1, .88]); regional(ax, bb)
J = VP[(VP.lon > bb[0]) & (VP.lon < bb[1]) & (VP.lat > bb[2]) & (VP.lat < bb[3])].sort_values("population_within_30km", ascending=False)
for t in J.itertuples():
    cx, cy = circle_lonlat(t.lon, t.lat, 30)
    ax.fill(cx, cy, color=ECOL[t.last_eruption_class], alpha=.13, zorder=2, lw=0)
    ax.plot(cx, cy, color=ECOL[t.last_eruption_class], lw=.7, alpha=.7, zorder=3)
ax.scatter(J.lon, J.lat, s=12, c=[ECOL[k] for k in J.last_eruption_class], edgecolors="#fff", linewidths=.4, zorder=4)
cities = [c for c in jload(PLACES)["features"] if bb[0] < c["geometry"]["coordinates"][0] < bb[1] and bb[2] < c["geometry"]["coordinates"][1] < bb[3] and (c["properties"].get("pop_max") or 0) > 1.5e6]
cities.sort(key=lambda c: -c["properties"]["pop_max"]); kept = []
for c in cities:
    lo, la = c["geometry"]["coordinates"]
    if any(abs(lo - a) < .6 and abs(la - b) < .4 for a, b in kept):
        continue
    kept.append((lo, la))
    ax.plot(lo, la, "s", ms=4, color=FG, zorder=6)
    ax.text(lo + .06, la + .06, c["properties"]["name"], fontsize=10, zorder=6, color=FG, fontweight="medium",
            path_effects=[__import__("matplotlib.patheffects", fromlist=["x"]).withStroke(linewidth=3, foreground=BG)])
PE = __import__("matplotlib.patheffects", fromlist=["x"]).withStroke(linewidth=2.5, foreground=BG)
for k, dy in (("Tangkuban Parahu", .36), ("Merapi", -.4), ("Gede-Pangrango", -.42), ("Penanggungan", -.42), ("Slamet", -.4)):
    t = J[J.name == k].iloc[0]
    ax.text(t.lon, t.lat + dy, k, fontsize=9, ha="center", va="center", color=FG, zorder=7, path_effects=[PE])
ax.text(bb[0] + 2.2, bb[2] + .45, "Indian Ocean", fontsize=10.5, color=COOL, style="italic")
ax.text(bb[0] + 4.6, bb[3] - .45, "Java Sea", fontsize=10.5, color=COOL, style="italic")
fig.text(.01, .03, f"Java: {len(J)} Holocene volcanoes and their 30 km circles. Where circles overlap, the same people are counted for more than one volcano.", fontsize=10, color=MUT)
save(fig, f"{PAP}/f_java.png")

# ---------- blog copies ----------
for a, b in (("f_map", "b_world_map"), ("f_bounds", "b_bounds"), ("f_countries", "b_countries"), ("f_top30", "b_top30"), ("f_java", "b_java"),
             ("f_recent", "b_recent"), ("f_centuries", "b_centuries")):
    shutil.copy(f"{PAP}/{a}.png", f"{BLOG}/{b}.png")

# ---------- header (1200 x 630) ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.33, .06, .67, .88]); worldmap(ax, lw=.25); plates(ax, lw=.6, alpha=.45); dots(ax, V, smax=260, lw=.3, minsize=1.6)
fig.text(.04, .80, "In the shadow", fontproperties=DISP, fontsize=46, color=FG)
fig.text(.04, .69, "of the volcano", fontproperties=DISP, fontsize=46, color=HOT)
fig.text(.04, .50, f"At least {R['glob']['30']['floor'] / 1e6:.0f} million people\nlive within 30 km of one of the\nworld's {R['n_volc']:,} Holocene volcanoes.", fontproperties=SERP, fontsize=17, color=FG, va="top", linespacing=1.5)
ov = fig.add_axes([0, 0, 1, 1], facecolor="none"); ov.set_xlim(0, 1); ov.set_ylim(0, 1); ov.axis("off")
for i, k in enumerate(["2000", "1900", "1500", "ce", "bce"]):
    ov.scatter([.047 + (i % 2) * .2], [.22 - (i // 2) * .045], s=70, color=ECOL[k], edgecolors="#fff", linewidths=.5)
    fig.text(.06 + (i % 2) * .2, .22 - (i // 2) * .045, "erupted " + ELAB[k].replace(" (Holocene)", "").replace("Before 1 CE", "BCE"), fontsize=10, color=MUT, va="center")
fig.text(.04, .05, "maps.tristanhotham.com/volcano-neighbours", fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print(sorted(os.listdir(PAP)), sorted(os.listdir(BLOG)))

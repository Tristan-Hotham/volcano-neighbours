"""House style for static figures: fonts (a static Fraunces Black cut from the variable font, written to memory),
colours, Natural Earth outlines and plate boundaries in a Pacific-centred Equal Earth projection, and regional maps."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
from pyproj import Transformer
from shapely.geometry import shape, box
from common import *

FONTS = "/home/claude/ref/fonts"
FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": 900, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-Black.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
fm.fontManager.addfont(f"{FONTS}/IBMPlexMono-Regular.ttf")
fm.fontManager.addfont(f"{FONTS}/IBMPlexMono-Medium.ttf")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#6A635E", "axes.labelcolor": "#1F1C1B",
                     "xtick.color": "#6A635E", "ytick.color": "#6A635E"})
BG, FG, MUT, LAND, RULE, HOT, COOL, SEA = "#F7F4EF", "#1F1C1B", "#6A635E", "#E6DFD3", "#E1DAD0", "#B3261E", "#2F5D8A", "#F7F4EF"
ECOL = {k: c for k, _, _, _, c in ECLS}
ELAB = {k: l for k, l, _, _, _ in ECLS}
LON0 = 150
PROJ = Transformer.from_crs(4326, f"+proj=eqearth +lon_0={LON0} +datum=WGS84", always_xy=True)
SEAM = LON0 - 180            # -30: the meridian where the Pacific-centred map is cut
_WORLD = None


def world_shapes():
    """Natural Earth 50m countries, cut at the seam meridian and projected (Pacific-centred Equal Earth)."""
    global _WORLD
    if _WORLD is None:
        _WORLD = []
        L, Rb = box(-180, -90, SEAM - 1e-6, 90), box(SEAM + 1e-6, -90, 180, 90)
        for f in jload(NE50)["features"]:
            g0 = shape(f["geometry"])
            rings = []
            for half in (L, Rb):
                g = g0.intersection(half)
                if g.is_empty:
                    continue
                for p in ([g] if g.geom_type == "Polygon" else [q for q in getattr(g, "geoms", []) if q.geom_type == "Polygon"]):
                    a = np.array(p.exterior.coords)
                    x, y = PROJ.transform(a[:, 0], a[:, 1])
                    rings.append(np.column_stack([x, y]))
            _WORLD.append((f["properties"]["ADM0_A3"], rings))
    return _WORLD


def xy(lon, lat):
    return PROJ.transform(np.asarray(lon, dtype=float), np.asarray(lat, dtype=float))


def plates_xy():
    out = []
    for f in jload(PLATES)["features"]:
        g = shape(f["geometry"])
        for ln in ([g] if g.geom_type == "LineString" else list(g.geoms)):
            a = np.array(ln.coords)
            # break at the seam and at the antimeridian
            seg = [a[0]]
            for p, q in zip(a, a[1:]):
                if abs(p[0] - q[0]) > 180 or (p[0] - SEAM) * (q[0] - SEAM) < 0:
                    if len(seg) > 1:
                        out.append(np.array(seg))
                    seg = []
                seg.append(q)
            if len(seg) > 1:
                out.append(np.array(seg))
    res = []
    for s in out:
        x, y = xy(s[:, 0], s[:, 1])
        res.append((x, y))
    return res


def worldmap(ax, land=LAND, ec="#FFFFFF", lw=.3, ext=None):
    for iso, rings in world_shapes():
        if iso == "ATA":
            continue
        for r in rings:
            ax.add_patch(MPoly(r, closed=True, fc=land, ec=ec, lw=lw, zorder=1))
    if ext is None:
        x0, _ = xy(SEAM + .01, 0); x1, _ = xy(SEAM - .01, 0)
        _, y0 = xy(LON0, -58); _, y1 = xy(LON0, 78)
        ext = (x0, x1, y0, y1)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")
    return ext


def regional(ax, bbox, land=LAND, ec="#FFFFFF", lw=.6):
    """Plain lon/lat map (cos-latitude aspect) for a small region: bbox = (lon0, lon1, lat0, lat1)."""
    B = box(bbox[0] - 2, bbox[2] - 2, bbox[1] + 2, bbox[3] + 2)
    for f in jload(NE10)["features"]:
        g = shape(f["geometry"])
        if not g.intersects(B):
            continue
        g = g.intersection(B)
        for p in ([g] if g.geom_type == "Polygon" else [q for q in getattr(g, "geoms", []) if q.geom_type == "Polygon"]):
            ax.add_patch(MPoly(np.array(p.exterior.coords), closed=True, fc=land, ec=ec, lw=lw, zorder=1))
    ax.set_xlim(bbox[0], bbox[1]); ax.set_ylim(bbox[2], bbox[3])
    ax.set_aspect(1 / np.cos(np.radians((bbox[2] + bbox[3]) / 2))); ax.axis("off")


def circle_lonlat(lon, lat, km, n=90):
    t = np.linspace(0, 2 * np.pi, n)
    dlat = km / 111.2
    return lon + dlat * np.sin(t) / np.cos(np.radians(lat)), lat + dlat * np.cos(t)


def save(fig, name, dpi=200):
    fig.savefig(name, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)


def mshort(n):
    n = float(n)
    if n >= 1e9: return f"{n / 1e9:.2f}bn"
    if n >= 1e6: return (f"{n / 1e6:.0f}m" if n >= 1e7 else f"{n / 1e6:.1f}m").replace(".0m", "m")
    if n >= 1e3: return f"{n / 1e3:.0f}k"
    return f"{n:.0f}"

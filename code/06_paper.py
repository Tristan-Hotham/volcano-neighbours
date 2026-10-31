"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/Hotham_In_the_Shadow_of_the_Volcano.tex and .pdf (figures f_*.png sit beside them)."""
import re, subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_In_the_Shadow_of_the_Volcano"
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
# facts stated in words in the paper
assert R["c_rank_floor30"][5] == "TWN"
ratio = lambda i: R["c"][i]["sum30"] / R["c"][i]["floor30"]
assert min(ratio("SLV"), ratio("GTM")) > max(ratio(i) for i in ("IDN", "MEX", "JPN", "PHL", "ITA", "TWN"))
assert R["v"]["tambora"]["p30"] < 1e5 and R["v"]["ilopango"]["p30"] > 2e6
assert [t["name"] for t in R["top30"][:5]][3] == "Penanggungan" and R["top30"][3]["ecls"] == "unk"
assert R["v"]["merapi"]["ecls"] == "2000" and R["v"]["taal"]["ecls"] == "2000"


def tfmt(v, f):
    if f == "pc": return f"{round(float(v))}\\%"
    return tex(fmt(v, f or "raw"))


rows = "".join(f"Within {r} km & {R['glob'][str(r)]['floor']:,.0f} & {R['glob'][str(r)]['floor_n']} & {R['glob'][str(r)]['sum']:,.0f} & {R['glob'][str(r)]['zero']}\\\\\n" for r in RINGS)
TB = ("\\begin{table}[tbp]\\centering\\footnotesize\\setlength{\\tabcolsep}{4pt}\\caption{People near Holocene volcanoes: lower bound (sum over non-overlapping circles, with the number of volcanoes kept), "
      "upper bound (simple sum over all " + f"{R['n_pop']:,}" + " volcanoes with figures) and the number of volcanoes with nobody within the distance.}\\label{tab:bounds}"
      "\\begin{tabular}{lrrrr}\\toprule Distance & Lower bound & Volcanoes kept & Upper bound & Volcanoes with nobody\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
C = sorted(R["countries"], key=lambda c: -c["floor30"])[:20]
rows = "".join(f"{tex(c['name'])} & {c['n']} & {c['n_since2000']} & {c['floor10'] / 1e6:.1f} & {c['floor30'] / 1e6:.1f} & {c['sum30'] / 1e6:.1f} & {c['floor100'] / 1e6:.1f} & {tex(c['top'])}\\\\\n" for c in C)
TC = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Countries ranked by the lower bound of people within 30 km of their Holocene volcanoes (millions). "
      "Lower bounds (LB) count each person once; the 30 km sum is the upper bound.}\\label{tab:countries}\\setlength{\\tabcolsep}{4pt}"
      "\\begin{tabular}{lrrrrrrl}\\toprule Country & Volcanoes & Since 2000 & LB 10 km & LB 30 km & Sum 30 km & LB 100 km & Most crowded (30 km)\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(t['name'])}{'$^*$' if t['flat'] else ''} & {tex(t['country'].split(' - ')[0])} & {tex(t['last_txt'])} & {t['p10']:,.0f} & {t['p30']:,.0f} & {t['p100']:,.0f}\\\\\n" for t in R["top30"])
TT = ("\\begin{table}[tbp]\\centering\\small\\caption{The twenty volcanoes with most people within 30 km (GVP names and figures). $^*$ same figure at 10 and 30 km.}\\label{tab:top}\\setlength{\\tabcolsep}{4pt}"
      "\\begin{tabular}{lllrrr}\\toprule Volcano & Country & Last eruption & Within 10 km & Within 30 km & Within 100 km\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("\\url{{{meta.page}}}", "\\url{%s}" % URL).replace("\\url{{{meta.repo}}}", "\\url{%s}" % REPO)
t = fill(t, R, tfmt)
t = t.replace("{{TABLE_BOUNDS}}", TB).replace("{{TABLE_COUNTRIES}}", TC).replace("{{TABLE_TOP}}", TT)
assert not re.search(r"\{\{(?!DOI\}\})", t), re.findall(r"\{\{[^}]*\}\}", t)[:5]
check_dashes(t, "paper")
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l or l.startswith("!")][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–") + txt.count("--"))

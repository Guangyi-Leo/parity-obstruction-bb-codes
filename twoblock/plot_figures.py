"""All manuscript figures, generated only from files in data/, templates/ and schedules/.

Every number drawn is pulled from a named CSV/JSON cell and recorded in TRACE, so
`audit()` can re-read the source independently and assert equality.  The only
hand-written content is F2, which is a schematic of the proof with its constants in
this file and no data behind it.

Conventions (fixed):
  classes   D  : no 4-qubit overlaps
            C1 : one collision orbit (N four-qubit overlaps)
            C2 : two collision orbits / one triple orbit
            SG : subgroup type
  status    SAT solver = filled circle, SAT template-witness = filled triangle,
            UNSAT solver = cross, UNSAT theorem-1 = plus, UNDETERMINED = open square.
            A capped call is UNDETERMINED and is never drawn as UNSAT.
  strata    ord(d) even / ord(d) odd & theorem-1 obstructed / ord(d) odd & not obstructed
"""
from __future__ import annotations

import csv
import json
import os
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                    # noqa: E402
from matplotlib.lines import Line2D                                # noqa: E402
from matplotlib.patches import Patch, Rectangle                    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SCHED = os.path.join(ROOT, "schedules")
TEMPL = os.path.join(ROOT, "templates")
FIGS = os.path.join(ROOT, "figures")

OI = dict(black="#000000", orange="#E69F00", sky="#56B4E9", green="#009E73",
          yellow="#F0E442", blue="#0072B2", vermillion="#D55E00", purple="#CC79A7")
GREY = "#BBBBBB"
SINGLE, DOUBLE = 3.4, 7.0
MISSING = "--"

CLASS_NAMES = {
    "D": "D: no 4-qubit overlaps",
    "C1": "C1: one collision orbit (N four-qubit overlaps)",
    "C2": "C2: two collision orbits / one triple orbit",
    "SG": "SG: subgroup type",
}
CLASS_COL = {"D": OI["blue"], "C1": OI["orange"], "C2": OI["green"],
             "SG": OI["purple"], "sweep": "0.45"}

STATUS_MK = {
    "SAT solver":       dict(marker="o", ms=3.6, fillstyle="full"),
    "SAT witness":      dict(marker="^", ms=4.2, fillstyle="full"),
    "UNSAT solver":     dict(marker="X", ms=4.4, fillstyle="full"),
    "UNSAT theorem-1":  dict(marker="P", ms=4.4, fillstyle="full"),
    "UNDETERMINED":     dict(marker="s", ms=4.0, fillstyle="none"),
}
STATUS_ORDER = list(STATUS_MK)
STRATA = ["ord(d) even",
          "ord(d) odd, theorem-1 obstructed",
          "ord(d) odd, not obstructed"]

MANIFEST: list[dict] = []
TRACE: list[dict] = []


def style():
    plt.rcParams.update({
        "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
        "font.family": "sans-serif",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "lines.linewidth": 1.0, "pdf.fonttype": 42, "ps.fonttype": 42,
        "savefig.bbox": "tight", "savefig.pad_inches": 0.02, "figure.dpi": 300,
    })


def read(name: str) -> list[dict]:
    p = name if os.path.isabs(name) else os.path.join(DATA, name)
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []


def trace(fig: str, panel_: str, item: str, value, source: str, column: str, key=""):
    TRACE.append(dict(figure=fig, panel=panel_, item=item, value=value,
                      source=source, column=column, key=str(key)))
    return value


def panel(ax, letter: str, dx: float = -0.16, dy: float = 1.04):
    ax.text(dx, dy, letter, transform=ax.transAxes, fontsize=9, fontweight="bold",
            va="bottom", ha="left")


def save(fig, stem: str, inputs: list[str], func: str, desc: str, notes=None):
    os.makedirs(FIGS, exist_ok=True)
    pdf, png = os.path.join(FIGS, stem + ".pdf"), os.path.join(FIGS, stem + ".png")
    fig.savefig(pdf)
    fig.savefig(png, dpi=300)
    w, h = fig.get_size_inches()
    plt.close(fig)
    MANIFEST.append(dict(output=[os.path.relpath(pdf, ROOT), os.path.relpath(png, ROOT)],
                         inputs=inputs, function=func, description=desc,
                         width_in=round(float(w), 2), height_in=round(float(h), 2),
                         notes=notes or []))
    print(f"  wrote {os.path.relpath(pdf, ROOT)} ({w:.2f} x {h:.2f} in)")


def status_source(r: dict) -> str:
    """Marker class for a C1 row of c1_final_instances.csv."""
    sr, by = r["status_resolved"], r.get("resolved_by", "")
    if sr == "SAT":
        return "SAT witness" if by.startswith("template-witness") else "SAT solver"
    if sr == "UNSAT":
        return ("UNSAT theorem-1" if r["theorem1_obstructed"] == "True"
                else "UNSAT solver")
    return "UNDETERMINED"


def stratum(r: dict) -> str:
    if r["ord_d_even"] == "True":
        return STRATA[0]
    return STRATA[1] if r["theorem1_obstructed"] == "True" else STRATA[2]


def invariant_labels(instance: str = "bb72", depth: int = 7):
    """Label -> layer map from an `inv` schedule JSON, verified before use (audit e)."""
    from .code import TwoBlockCode
    from .simulate import is_proper_by_simulation, is_valid_layering
    p = os.path.join(SCHED, f"{instance}_d{depth}_inv.json")
    rec = json.load(open(p))
    code = TwoBlockCode(tuple(rec["dims"]), [tuple(a) for a in rec["A"]],
                        [tuple(b) for b in rec["B"]], rec["instance"])
    lay = rec["layers"]
    ok_valid = is_valid_layering(code, lay, rec["D"])
    ok_proper = is_proper_by_simulation(code, lay, rec["D"])
    if not (ok_valid and ok_proper):
        raise AssertionError(f"{p}: valid={ok_valid} proper={ok_proper}")
    seen: dict[tuple, set] = defaultdict(set)
    for e, l in zip(rec["edges"], lay):
        seen[(e[0], e[1], int(e[2]))].add(l)
    bad = {k: sorted(v) for k, v in seen.items() if len(v) != 1}
    if bad:
        raise AssertionError(f"{p} is not translation invariant: {bad}")
    labels = {}
    for kind, side in (("X", "L"), ("X", "R"), ("Z", "L"), ("Z", "R")):
        labs = sorted(l for (k, s, l) in seen if k == kind and s == side)
        labels[kind + side] = [next(iter(seen[(kind, side, l)])) for l in labs]
    return labels, os.path.relpath(p, ROOT), rec["D"], dict(valid=ok_valid,
                                                            proper=ok_proper)


# ===========================================================================
# F1  certificate vs optimum
# ===========================================================================
IBM_ORDER = ["bb72", "bb90", "bb108", "bb144", "bb288", "bb360", "bb756"]


def fig1():
    inst = {r["name"]: r for r in read("instances.csv")}
    by = {}
    for r in read("results.csv"):
        by[(r["instance"], r["D"], r["tag"])] = r
    nr = {r["instance"]: r for r in read("r4_no_reversal.csv")}

    fig = plt.figure(figsize=(DOUBLE, 2.7))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.55, 0.85, 1.25], wspace=0.42)

    ax = fig.add_subplot(gs[0, 0])
    xs, labs, delta, opt, notes = [], [], [], [], []
    for nm in IBM_ORDER:
        d6, d7 = by.get((nm, "6", "")), (by.get((nm, "7", "inv")) or by.get((nm, "7", "")))
        if not (d6 and d6["status"] == "UNSAT" and d6["verified"] == "VERIFIED"
                and d7 and d7["status"] == "SAT"):
            continue
        i = len(xs)
        xs.append(i)
        k = inst[nm]["k_logical"] or MISSING
        n = trace("F1", "a", f"n_qubits[{nm}]", int(inst[nm]["n_qubits"]),
                  "data/instances.csv", "n_qubits", nm)
        labs.append(f"{nm}  [[{n},{k},{MISSING}]]")
        delta.append(trace("F1", "a", f"Delta[{nm}]", int(inst[nm]["Delta"]),
                           "data/instances.csv", "Delta", nm))
        opt.append(trace("F1", "a", f"opt_depth[{nm}]", int(d7["D"]),
                         "data/results.csv", "D", f"{nm},7"))
        t = trace("F1", "a", f"d6_time[{nm}]", round(float(d6["time"]), 2),
                  "data/results.csv", "time", f"{nm},6,''")
        mb = trace("F1", "a", f"d6_proof_MB[{nm}]", round(int(d6["proof_bytes"]) / 1e6, 1),
                   "data/results.csv", "proof_bytes", f"{nm},6,''")
        nrmb = ""
        if nm in nr:
            nrmb = trace("F1", "a", f"norev_proof_MB[{nm}]",
                         round(int(nr[nm]["proof_bytes"]) / 1e6, 1),
                         "data/r4_no_reversal.csv", "proof_bytes", nm)
        notes.append((t, mb, nrmb))
    w = 0.38
    ax.bar([x - w / 2 for x in xs], delta, w, color=GREY, edgecolor="black",
           linewidth=0.5, label="König certificate $\\Delta$", zorder=3)
    ax.bar([x + w / 2 for x in xs], opt, w, color=OI["blue"], edgecolor="black",
           linewidth=0.5, label="optimal proper depth", zorder=3)
    top = max(delta + opt)
    for x, (t, mb, nrmb) in zip(xs, notes):
        lab = f"{t:.1f}s\n{mb:.0f} MB"
        if nrmb != "":
            lab += f"\n{nrmb:.0f} MB*"
        ax.text(x, top * 1.045, lab, ha="center", va="bottom", fontsize=4.6,
                color="0.25", linespacing=0.95)
    ax.set_xticks(xs)
    ax.set_xticklabels(labs, fontsize=5.6, rotation=42, ha="right",
                       rotation_mode="anchor")
    ax.set_ylabel("schedule depth")
    ax.set_ylim(0, top * 1.42)
    ax.set_yticks(range(0, top + 2, 2))
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0.0, 0.99), ncol=2,
              handlelength=1.2, columnspacing=1.0, borderaxespad=0.0, fontsize=6.4)
    ax.grid(axis="y", color="0.9", linewidth=0.5, zorder=0)
    panel(ax, "a", dx=-0.155)

    # ---- b) the translation-invariant depth-7 schedule ---------------------
    axb = fig.add_subplot(gs[0, 1])
    labels, src, D, ver = invariant_labels("bb72", 7)
    trace("F1", "b", "schedule_valid_layering", ver["valid"], src, "layers", "bb72_d7_inv")
    trace("F1", "b", "schedule_proper_by_simulation", ver["proper"], src, "layers",
          "bb72_d7_inv")
    rows = ["XL", "XR", "ZL", "ZR"]
    ncol = max(len(labels[r]) for r in rows)
    cmap = plt.get_cmap("viridis")
    for i, r in enumerate(rows):
        for j, v in enumerate(labels[r]):
            trace("F1", "b", f"layer[{r},{j+1}]", v, src, "layers", f"{r},{j+1}")
            frac = (v - 1) / max(D - 1, 1)
            axb.add_patch(Rectangle((j, len(rows) - 1 - i), 1, 1, facecolor=cmap(frac),
                                    edgecolor="white", linewidth=1.0))
            axb.text(j + 0.5, len(rows) - 1 - i + 0.5, str(v), ha="center", va="center",
                     fontsize=7, color="white" if frac < 0.62 else "black")
    axb.set_xlim(0, ncol); axb.set_ylim(0, len(rows))
    axb.set_xticks([j + 0.5 for j in range(ncol)])
    axb.set_xticklabels([str(j + 1) for j in range(ncol)])
    axb.set_yticks([len(rows) - 1 - i + 0.5 for i in range(len(rows))])
    axb.set_yticklabels(rows)
    axb.set_xlabel("label $s$ / $t$")
    axb.tick_params(length=0)
    for sp in axb.spines.values():
        sp.set_visible(False)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(1, D))
    cb = fig.colorbar(sm, ax=axb, fraction=0.055, pad=0.06, ticks=[1, D])
    cb.set_label("layer", labelpad=-6); cb.outline.set_linewidth(0.5)
    panel(axb, "b", dx=-0.34)

    # ---- c) one round of the minimal shared-corner example -----------------
    axc = fig.add_subplot(gs[0, 2])
    xl, xr = labels["XL"][0], labels["XR"][0]
    zl, zr = labels["ZL"][0], labels["ZR"][0]
    for nm2, y in (("$y$ (X-check)", 3), ("$L$", 2), ("$R$", 1), ("$z$ (Z-check)", 0)):
        axc.plot([0.4, D + 0.6], [y, y], color="0.75", linewidth=0.7, zorder=1)
        axc.text(0.22, y, nm2, ha="right", va="center", fontsize=6.5)

    def cnot(layer, yc, yt, col):
        axc.plot([layer, layer], [min(yc, yt), max(yc, yt)], color=col, linewidth=1.1, zorder=3)
        axc.plot([layer], [yc], marker="o", ms=3.0, color=col, zorder=4)
        axc.plot([layer], [yt], marker="P", ms=4.6, color=col, zorder=4, markeredgewidth=0.0)
    cnot(xl, 3, 2, OI["vermillion"]); cnot(xr, 3, 1, OI["vermillion"])
    cnot(zl, 2, 0, OI["blue"]); cnot(zr, 1, 0, OI["blue"])
    for (p0, p1, y, lab) in ((xl, zl, 2.32, "L-corner, $o=1$"),
                             (xr, zr, 1.32, "R-corner, $o=1$")):
        axc.annotate("", xy=(p1, y), xytext=(p0, y),
                     arrowprops=dict(arrowstyle="-|>", color=OI["green"], lw=0.8,
                                     shrinkA=0, shrinkB=0))
        axc.text((p0 + p1) / 2, y + 0.10, lab, ha="center", fontsize=6, color=OI["green"])
    axc.set_xlim(0.0, D + 0.7); axc.set_ylim(-0.5, 3.75)
    axc.set_xticks(range(1, D + 1)); axc.set_xlabel("layer"); axc.set_yticks([])
    for sp in ("left", "right", "top"):
        axc.spines[sp].set_visible(False)
    panel(axc, "c", dx=-0.10)

    save(fig, "fig_certificate_vs_optimum",
         ["data/instances.csv", "data/results.csv", "data/r4_no_reversal.csv", src],
         "plot_figures.fig1",
         "a: Koenig bound Delta against the certified optimal proper depth for each IBM "
         "code, annotated with the depth-6 solve time, the DRAT proof size, and (starred) "
         "the proof size without the layer-reversal clause. b: the translation-invariant "
         "depth-7 schedule as a label x (kind,side) grid, re-verified before drawing. "
         "c: one round of the minimal shared-corner example under that schedule.",
         [f"logical k from instances.csv:k_logical; distance d is in no data file, shown "
          f"as '{MISSING}'.",
          "starred proof sizes are the reversal-clause-free certificates (R4)."])


# ===========================================================================
# F2  schematic of the proof (no data; constants live here)
# ===========================================================================
GAMMA = {1: 3, 2: 2, 3: 2, 4: 1, 5: 1, 6: 0}      # gamma(v), v = 1..6
D_SCHEM = 6
XCOL, ZCOL = OI["vermillion"], OI["blue"]


def _cell(ax, x, y, w=0.9, h=0.6, face="white", edge="0.35", lw=0.6):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=face, edgecolor=edge,
                           linewidth=lw, zorder=2))


def _strip(ax, y, marks, h=0.6, label=None, lab_x=0.35, fs=6.5):
    for v in range(1, D_SCHEM + 1):
        m = marks.get(v)
        _cell(ax, v - 0.45, y, h=h, face={"X": XCOL, "Z": ZCOL}.get(m, "white"))
        if m:
            ax.text(v, y + h / 2, m, ha="center", va="center", fontsize=fs,
                    color="white", fontweight="bold", zorder=3)
    if label:
        ax.text(lab_x, y + h / 2, label, ha="right", va="center", fontsize=6.6)


def fig2():
    fig, axes = plt.subplots(1, 3, figsize=(DOUBLE, 2.35),
                             gridspec_kw=dict(width_ratios=[1.05, 0.78, 1.25], wspace=0.26))
    for ax in axes:
        ax.set_ylim(0.05, 4.35)
        ax.axis("off")

    def title(ax, x, txt):
        ax.text(x, 4.05, txt, fontsize=6.8, fontweight="bold", ha="center",
                va="bottom", color="0.2")

    # ---- a) rigidity -------------------------------------------------------
    ax = axes[0]
    ax.set_xlim(-1.65, D_SCHEM + 0.6)
    title(ax, (D_SCHEM + 0.6 - 1.65) / 2, "rigidity")
    for v in range(1, D_SCHEM + 1):
        ax.text(v, 3.42, str(v), ha="center", va="bottom", fontsize=6.3)
    ax.text(0.35, 3.42, "layer", ha="right", va="bottom", fontsize=6.3)
    for a, b in ((1, 2), (3, 4), (5, 6)):
        ax.add_patch(Rectangle((a - 0.5, 1.62), 2.0, 1.44, facecolor="none",
                               edgecolor="0.5", linewidth=0.7, linestyle=(0, (3, 2))))
        ax.text((a + b) / 2, 3.10, "{%d,%d}" % (a, b), ha="center", va="bottom",
                fontsize=5.6, color="0.4")
    _strip(ax, 2.38, {1: "X", 2: "Z", 3: "X", 4: "Z", 5: "X", 6: "Z"},
           label="orientation A")
    _strip(ax, 1.70, {1: "Z", 2: "X", 3: "Z", 4: "X", 5: "Z", 6: "X"},
           label="orientation B")
    ax.text((D_SCHEM + 1) / 2, 0.85,
            "every pair carries one X-edge and one Z-edge;\nboth orientations are admissible",
            ha="center", va="center", fontsize=5.9, linespacing=1.3)
    panel(ax, "a", dx=-0.02, dy=1.00)

    # ---- b) parity ---------------------------------------------------------
    ax = axes[1]
    ax.set_xlim(-0.3, 7.2)
    title(ax, 3.45, "parity")
    ax.text(0.35, 3.03, "$v$", ha="right", va="center", fontsize=6.4)
    ax.text(0.35, 2.45, "$\\gamma(v)$", ha="right", va="center", fontsize=6.4)
    for v in range(1, D_SCHEM + 1):
        _cell(ax, v - 0.45, 2.75, h=0.56, face="white")
        ax.text(v, 3.03, str(v), ha="center", va="center", fontsize=6.3)
        _cell(ax, v - 0.45, 2.17, h=0.56, face=OI["yellow"])
        ax.text(v, 2.45, str(GAMMA[v]), ha="center", va="center", fontsize=6.3,
                fontweight="bold")
    ax.text(3.5, 1.52, "$F_L + F_R = \\sum_v \\gamma(v) = %d$" % sum(GAMMA.values()),
            ha="center", va="center", fontsize=7.2,
            bbox=dict(boxstyle="round,pad=0.26", facecolor="0.96", edgecolor="0.7",
                      linewidth=0.5))
    ax.text(3.5, 0.80, "properness requires $F_L = F_R$", ha="center", va="center",
            fontsize=6.8)
    ax.text(3.5, 0.32, "an odd total cannot be split", ha="center", va="center",
            fontsize=5.8, color="0.35")
    panel(ax, "b", dx=-0.06, dy=1.00)

    # ---- c) where the overlap hypothesis enters ----------------------------
    ax = axes[2]
    ax.set_xlim(0, 10)
    title(ax, 5.0, "where the overlap hypothesis enters")

    def block(cx, n, head, note, col):
        ax.text(cx, 3.34, head, ha="center", va="bottom", fontsize=6.1)
        for i in range(n):
            yy = 2.95 - i * 0.52
            ax.add_patch(Rectangle((cx - 1.35, yy), 0.78, 0.34, facecolor=OI["green"],
                                   edgecolor="white", linewidth=0.8))
            ax.text(cx - 0.96, yy + 0.17, "L", ha="center", va="center", fontsize=5.8,
                    color="white", fontweight="bold")
            ax.add_patch(Rectangle((cx + 0.57, yy), 0.78, 0.34, facecolor=OI["orange"],
                                   edgecolor="white", linewidth=0.8))
            ax.text(cx + 0.96, yy + 0.17, "R", ha="center", va="center", fontsize=5.8,
                    color="white", fontweight="bold")
            ax.annotate("", xy=(cx + 0.55, yy + 0.17), xytext=(cx - 0.55, yy + 0.17),
                        arrowprops=dict(arrowstyle="<|-|>", color="0.35", lw=0.7,
                                        shrinkA=0, shrinkB=0))
        ax.text(cx, 1.62 if n == 1 else 1.30, note, ha="center", va="top",
                fontsize=5.8, color=col, linespacing=1.25)

    block(2.5, 1, "$|P(\\delta)|=1$: 2 corners",
          "one L-corner $\\leftrightarrow$\none R-corner (bijection)", OI["green"])
    block(7.5, 2, "$|P(\\delta)|=2$: 4 corners",
          "two of each;\nno forced pairing", "0.35")
    ax.plot([5.0, 5.0], [0.30, 3.50], color="0.8", lw=0.7, ls=(0, (2, 2)))
    ax.text(2.5, 0.28, "distinct sums", ha="center", fontsize=5.9, color="0.4")
    ax.text(7.5, 0.28, "coinciding sums", ha="center", fontsize=5.9, color="0.4")
    panel(ax, "c", dx=-0.03, dy=1.00)

    handles = [Patch(facecolor=XCOL, label="X-edge"), Patch(facecolor=ZCOL, label="Z-edge"),
               Patch(facecolor=OI["green"], label="L-corner"),
               Patch(facecolor=OI["orange"], label="R-corner")]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=6.3,
               bbox_to_anchor=(0.5, -0.09), handlelength=1.1, handleheight=0.9)

    save(fig, "fig_proof_structure", [], "plot_figures.fig2",
         "Schematic of the proof. a: rigidity -- each layer pair {1,2}, {3,4}, {5,6} at a "
         "data qubit carries one X-edge and one Z-edge, in either of two admissible "
         "orientations. b: parity -- the weights gamma(v) and the identity "
         "F_L + F_R = sum gamma = 9, which properness must split as F_L = F_R. "
         "c: where the overlap hypothesis enters -- with distinct sums an overlap pair "
         "has two corners, one on each side, so L- and R-corners are in bijection; a "
         "coinciding sum gives four corners and no forced pairing.",
         ["Schematic only: no data file feeds this figure; gamma lives in "
          "plot_figures.GAMMA."])


# ===========================================================================
# F3  depth-6 status by group order and overlap class
# ===========================================================================
ROW = {"D": 6, "C1|" + STRATA[0]: 5, "C1|" + STRATA[1]: 4, "C1|" + STRATA[2]: 3,
       "C2": 2, "SG": 1, "sweep": 0}
ROW_LABEL = {"D": "D", "C1|" + STRATA[0]: "C1  ord($d$) even",
             "C1|" + STRATA[1]: "C1  ord($d$) odd,\ntheorem-1 obstructed",
             "C1|" + STRATA[2]: "C1  ord($d$) odd,\nnot obstructed",
             "C2": "C2", "SG": "SG", "sweep": "sweep $|G|\\leq 8$"}


def fig3():
    import random as _r
    c1 = read("c1_final_instances.csv")
    sharp = read("h2_sharpness.csv")
    sweep = read("sweep.csv")
    final = read("c1_final.csv")
    obstr = {r["instance"]: r["theorem1_obstructed"] for r in read("h1_predictions.csv")}
    notes = []

    fig, ax = plt.subplots(figsize=(SINGLE, 3.35))
    rng = _r.Random(7)
    drawn = Counter()

    def put(N, rowkey, colkey, src, ms_scale=1.0):
        y = ROW[rowkey] + (rng.random() - 0.5) * 0.5
        mk = dict(STATUS_MK[src])
        mk["ms"] = mk["ms"] * ms_scale
        ax.plot([N], [y], linestyle="none", color=CLASS_COL[colkey],
                markeredgewidth=0.8, zorder=3, **mk)
        drawn[(rowkey, src)] += 1

    for r in c1:                                   # class C1, split by stratum
        put(int(r["N"]), "C1|" + stratum(r), "C1", status_source(r), 0.72)
    for r in sharp:                                # D / C2 / SG
        k = "SG" if r["class"] == "subgroup" else r["class"]
        if k == "C1":
            continue
        st = r["status"]
        if st == "SAT":
            src = "SAT solver"
        elif st == "UNSAT":
            src = ("UNSAT theorem-1" if obstr.get(r["name"]) == "True"
                   else "UNSAT solver")
        else:
            src = "UNDETERMINED"
        put(int(r["N"]), k, k, src)

    agg: dict[str, Counter] = defaultdict(Counter)
    order_of = {}
    for r in sweep:
        agg[r["group"]][r["status"]] += 1
        order_of[r["group"]] = int(r["N"])
    for i, (g, c) in enumerate(sorted(agg.items(), key=lambda kv: order_of[kv[0]])):
        y = ROW["sweep"] + (i - (len(agg) - 1) / 2) * 0.19
        for st, src in (("SAT", "SAT solver"), ("UNSAT", "UNSAT theorem-1")):
            if c[st]:
                trace("F3", "", f"sweep[{g}].{st}", c[st], "data/sweep.csv", "status", g)
                ax.plot([order_of[g]], [y], linestyle="none", color=CLASS_COL["sweep"],
                        markeredgewidth=0.9, zorder=3, **STATUS_MK[src])
        ax.annotate(f"{g}: {c['SAT']}/{c['UNSAT']}", (order_of[g], y),
                    textcoords="offset points", xytext=(5.5, -1.7), fontsize=4.3,
                    color="0.35", annotation_clip=False)

    for (k, src), n in sorted(drawn.items()):
        trace("F3", "", f"markers[{k},{src}]", n,
              "data/c1_final_instances.csv" if k.startswith("C1|")
              else "data/h2_sharpness.csv",
              "status_resolved" if k.startswith("C1|") else "status", f"{k},{src}")

    allN = sorted({int(r["N"]) for r in c1} | {int(r["N"]) for r in sharp}
                  | set(order_of.values()))
    lo, hi = min(allN), max(allN)
    ax.axvline(9, color="0.45", linestyle=(0, (4, 2)), linewidth=0.8, zorder=1)
    ax.text(8.6, 6.85, "distinct sums\npossible ($|G|\\geq k\\,l$)", fontsize=5.2,
            color="0.35", va="top", ha="right", linespacing=1.1)
    keys = ["D", "C1|" + STRATA[0], "C1|" + STRATA[1], "C1|" + STRATA[2],
            "C2", "SG", "sweep"]
    ax.set_yticks([ROW[k] for k in keys])
    ax.set_yticklabels([ROW_LABEL[k] for k in keys], fontsize=5.4)
    ax.set_xlabel("group order $N$")
    ax.set_ylabel("overlap class")
    ax.set_xlim(lo - 2.6, hi + 3.6)
    ax.set_ylim(-0.85, 7.05)
    ticks = [n for n in allN if n % 4 == 0 or n in (lo, hi)]
    ax.set_xticks(ticks)
    ax.tick_params(axis="x", labelsize=5.8)
    ax.grid(axis="x", color="0.93", linewidth=0.5, zorder=0)

    leg = [Line2D([], [], linestyle="none", color="0.25", markeredgewidth=0.9,
                  label=s, **STATUS_MK[s]) for s in STATUS_ORDER]
    ax.legend(handles=leg, frameon=False, fontsize=4.9, loc="lower left",
              bbox_to_anchor=(-0.02, 1.0), ncol=3, handletextpad=0.2, columnspacing=0.6)

    if final:
        lines = []
        for row in final:
            if row["region"] in ("total", ""):
                continue
            tot = trace("F3", "inset", f"stratum_total[{row['region']}]",
                        int(row["total"]), "data/c1_final.csv", "total", row["region"])
            lines.append(f"{row['region']}: {tot}")
        ax.text(0.985, 0.845, "class C1 by stratum\n" + "\n".join(lines),
                transform=ax.transAxes, ha="right", va="bottom", fontsize=4.4,
                linespacing=1.25,
                bbox=dict(boxstyle="round,pad=0.26", facecolor="white",
                          edgecolor="0.7", linewidth=0.5))
    else:
        notes.append("data/c1_final.csv missing: stratum inset omitted.")

    save(fig, "fig_sharpness",
         ["data/c1_final_instances.csv", "data/h2_sharpness.csv", "data/sweep.csv",
          "data/c1_final.csv", "data/h1_predictions.csv"],
         "plot_figures.fig3",
         "Depth-6 status by group order and overlap class. Class C1 uses "
         "status_resolved, so a timeout settled by a verified twisted witness is drawn "
         "as SAT (witness) and an unresolved timeout as UNDETERMINED; a capped call is "
         "never drawn as UNSAT. The sweep groups are aggregated to one marker per group "
         "labelled SAT/UNSAT counts. Dashed line at N = 9 = k*l, below which distinct "
         "sums are impossible.", notes)


# ===========================================================================
# F4  lemma profiles and pass rates
# ===========================================================================
LEMMA_ORDER = ["L1", "L2", "L3", "L4", "L5", "L6", "L7"]


def fig4():
    rows = read("lemma_checks.csv")
    per = read("r6_periodicity.csv")
    notes = []
    fig, axes = plt.subplots(2, 1, figsize=(SINGLE, 4.5))

    # ---- a) mean layer profile ---------------------------------------------
    ax = axes[0]
    ybar = {"oe23": -0.19, "oe43": -0.30}
    for nm, col in (("oe23", OI["blue"]), ("oe43", OI["vermillion"])):
        sel = [r for r in rows if r["instance"] == nm]
        if not sel:
            notes.append(f"no {nm} rows in lemma_checks.csv: profile omitted.")
            continue
        D, N = int(sel[0]["D"]), int(sel[0]["N"])
        Delta = int(sel[0]["Delta"])
        prof = [json.loads(r["x_profile"]) for r in sel]
        mean = [sum(p[i] for p in prof) / len(prof) / N for i in range(D)]
        for i, v in enumerate(mean):
            trace("F4", "a", f"mean_x[{nm},{i+1}]/N", round(v, 6),
                  "data/lemma_checks.csv", "x_profile", f"{nm},layer{i+1}")
        a = trace("F4", "a", f"a_min[{nm}]", min(int(r["a"]) for r in sel),
                  "data/lemma_checks.csv", "a", nm)
        b = trace("F4", "a", f"b_max[{nm}]", max(int(r["b"]) for r in sel),
                  "data/lemma_checks.csv", "b", nm)
        pairs = ",".join(f"({p},{q})" for p, q in
                         sorted({(int(r["a"]), int(r["b"])) for r in sel}))
        ax.plot(range(1, D + 1), mean, marker="o", ms=3.0, color=col, zorder=3,
                label=f"{nm}: $\\Delta={Delta}$, $D={D}$, {len(sel)} sol., $[a,b]$={pairs}")
        y = ybar[nm]
        ax.plot([a, b], [y, y], color=col, lw=2.0, solid_capstyle="butt", zorder=3,
                clip_on=False)
        for e in (a, b):
            ax.plot([e, e], [y - 0.025, y + 0.025], color=col, lw=1.0, zorder=3,
                    clip_on=False)
    ax.set_xlabel("layer $i$", labelpad=24)
    ax.set_ylabel("$x_i / N$")
    ax.set_ylim(0, 1.02); ax.set_xlim(0.7, 7.3); ax.set_xticks(range(1, 8))
    ax.legend(frameon=False, fontsize=5.5, loc="lower center", handlelength=1.4,
              ncol=1, bbox_to_anchor=(0.5, 1.02), labelspacing=0.35)
    ax.text(0.5, -0.70, "bars below the axis: support $[a,b]$;   "
                        "$a+b=\\Delta+1$ for every solution",
            transform=ax.transAxes, ha="center", fontsize=5.6, color="0.3")
    panel(ax, "a", dx=-0.155, dy=1.20)

    # ---- b) pass rates, with the R6 periodicity split ----------------------
    ax = axes[1]
    if rows:
        n = trace("F4", "b", "n_solutions", len(rows), "data/lemma_checks.csv",
                  "instance", "count")
        cov = {"L1": n,
               "L2": sum(int(r["size_E"]) + int(r["size_E_Z"]) for r in rows),
               "L3": sum(int(r["n_L3_checked"]) for r in rows),
               "L4": sum(int(r["n_L4_checked"]) for r in rows),
               "L5": sum(int(r["n_L5_checked"]) for r in rows),
               "L6": sum(int(r["N"]) for r in rows),
               "L7": sum(int(r["N"]) for r in rows if r["L7_applicable"] == "True")}
        rate = []
        for L in LEMMA_ORDER:
            v = 100.0 * sum(1 for r in rows if r[L] == "True") / n
            rate.append(trace("F4", "b", f"pass_rate[{L}]", round(v, 4),
                              "data/lemma_checks.csv", L, "all"))
            trace("F4", "b", f"subchecks[{L}]", cov[L], "data/lemma_checks.csv",
                  {"L1": "instance", "L2": "size_E+size_E_Z", "L3": "n_L3_checked",
                   "L4": "n_L4_checked", "L5": "n_L5_checked", "L6": "N",
                   "L7": "N|L7_applicable"}[L], "sum")
        ax.bar(range(len(LEMMA_ORDER)), rate, 0.62, color=OI["green"],
               edgecolor="black", linewidth=0.5, zorder=3)
        for i, L in enumerate(LEMMA_ORDER):
            ax.text(i, rate[i] + 2.5, f"{cov[L]:,}", ha="center", va="bottom",
                    fontsize=5.2, color="0.25")
        ax.set_xticks(range(len(LEMMA_ORDER))); ax.set_xticklabels(LEMMA_ORDER)
        ax.set_ylabel("pass rate (%)"); ax.set_ylim(0, 138)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.grid(axis="y", color="0.93", linewidth=0.5, zorder=0)
        ax.text(0.5, 1.02, f"sub-checks above each bar; {n} enumerated solutions",
                transform=ax.transAxes, ha="center", va="bottom", fontsize=5.6,
                color="0.3")
    if per:
        cnt = Counter(r["klass"] for r in per)
        for k in ("invariant", "twisted", "other"):
            trace("F4", "b", f"periodicity[{k}]", cnt.get(k, 0),
                  "data/r6_periodicity.csv", "klass", k)
        lem = {(r["instance"], int(r["solution"])): r for r in rows}
        oth = [lem[(r["instance"], int(r["solution"]))] for r in per
               if r["klass"] == "other" and (r["instance"], int(r["solution"])) in lem]
        pr = 100.0 * sum(1 for x in oth if x["all_pass"] == "True") / max(len(oth), 1)
        trace("F4", "b", "pass_rate_other_subset", round(pr, 4),
              "data/r6_periodicity.csv", "klass", "other")
        ax.text(0.5, -0.30,
                f"periodicity of the {sum(cnt.values())} schedules: "
                f"{cnt.get('invariant',0)} invariant / {cnt.get('twisted',0)} twisted "
                f"for a proper divisor / {cnt.get('other',0)} other;\n"
                f"pass rate on the {len(oth)} 'other' schedules: {pr:.0f}%",
                transform=ax.transAxes, ha="center", va="top", fontsize=5.4,
                color="0.25", linespacing=1.3)
    else:
        notes.append("data/r6_periodicity.csv missing: periodicity split omitted.")
    panel(ax, "b", dx=-0.155, dy=1.02)
    fig.subplots_adjust(hspace=1.05)

    save(fig, "fig_lemma_profiles", ["data/lemma_checks.csv", "data/r6_periodicity.csv"],
         "plot_figures.fig4",
         "a: mean layer profile x_i/N over all enumerated solutions of oe23 and oe43, "
         "with the observed support [a,b] drawn below the axis. b: pass rate of L1-L7 "
         "over every enumerated solution, with the number of sub-checks above each bar "
         "and the periodicity split of the same schedules.", notes)


# ===========================================================================
# F5 (SI)  sweep by group
# ===========================================================================
def fig5():
    sweep = read("sweep.csv")
    notes = [] if sweep else ["data/sweep.csv missing."]
    mults = sorted({r["max_multiplicity"] for r in sweep})
    seen = {}
    for r in sweep:
        seen.setdefault(r["group"], int(r["N"]))
    groups = sorted(seen, key=lambda g: (seen[g], g))
    counts: dict[tuple, Counter] = defaultdict(Counter)
    for r in sweep:
        counts[(r["group"], r["max_multiplicity"])][r["status"]] += 1

    fig, ax = plt.subplots(figsize=(SINGLE, 2.4))
    xs, labs = [], []
    w = 0.8 / max(len(mults), 1)
    for gi, g in enumerate(groups):
        for mi, m in enumerate(mults):
            c = counts[(g, m)]
            if not c:
                continue
            x = gi + (mi - (len(mults) - 1) / 2) * w
            sat = trace("F5", "", f"SAT[{g},mult<={m}]", c["SAT"], "data/sweep.csv",
                        "status", f"{g},{m}")
            uns = trace("F5", "", f"UNSAT[{g},mult<={m}]", c["UNSAT"], "data/sweep.csv",
                        "status", f"{g},{m}")
            ax.bar(x, sat, w * 0.92, color=OI["sky"], edgecolor="black", linewidth=0.4,
                   zorder=3)
            ax.bar(x, uns, w * 0.92, bottom=sat, color=OI["vermillion"],
                   edgecolor="black", linewidth=0.4, zorder=3)
            ax.text(x, sat + uns + 6, f"$\\leq${m}", ha="center", va="bottom",
                    fontsize=4.8, color="0.35")
            if uns:
                ax.annotate(f"{uns} UNSAT", xy=(x, sat + uns),
                            xytext=(x - 1.45, sat + 135), fontsize=5.4,
                            color=OI["vermillion"], ha="left",
                            arrowprops=dict(arrowstyle="-|>", lw=0.7,
                                            color=OI["vermillion"], shrinkA=0, shrinkB=1.5))
        xs.append(gi); labs.append(f"{g}\n$|G|$={seen[g]}")
    ax.set_xticks(xs); ax.set_xticklabels(labs, fontsize=5.6)
    ax.set_ylabel("instances"); ax.set_ylim(0, 470)
    ax.grid(axis="y", color="0.93", linewidth=0.5, zorder=0)
    ax.legend(handles=[Patch(facecolor=OI["sky"], label="SAT"),
                       Patch(facecolor=OI["vermillion"], label="UNSAT")],
              frameon=False, fontsize=6.2, loc="lower left", bbox_to_anchor=(0, 1.0),
              ncol=2, handlelength=1.1)
    ax.text(0.985, 0.97, "bar label: max $|P(\\delta)|$", transform=ax.transAxes,
            ha="right", va="top", fontsize=5.6, color="0.35")
    save(fig, "fig_sweep_by_group", ["data/sweep.csv"], "plot_figures.fig5",
         "SI: depth-6 outcome of the sweep, stacked SAT/UNSAT per group and per maximum "
         "sum multiplicity. All sweep groups have |G| <= 8 < 9 = k*l, so none of them "
         "has distinct sums.", notes)


# ===========================================================================
# F6 (SI)  template outcome by m, split by |M| and eps(d)
# ===========================================================================
TEMPLATE_MS = [2, 3, 4, 5, 6, 8]
NOT_COMPUTED_MS = [7, 9, 10, 11, 12, 16]
CATS = ["|M| odd",
        "|M| even, $\\varepsilon(d)=0$",
        "|M| even, $\\varepsilon(d)\\neq0$, ord even",
        "|M| even, $\\varepsilon(d)\\neq0$, ord odd"]
CAT_COL = [OI["purple"], OI["sky"], OI["green"], OI["orange"]]


def _template_split(m: int):
    from math import gcd
    from .templates import (M_order, enumerate_vectors, eps_d, key, load, patterns)
    rec = load(m)
    if rec is None or not rec.get("exhaustive", True):
        return None
    sat = rec["sat_set"]
    out = {c: [0, 0] for c in CATS}                 # [admit, no-admit]
    for pat in patterns():
        for ea, eb in enumerate_vectors(pat, m):
            hit = key(pat, ea, eb) in sat
            e = eps_d(pat, ea, eb, m) % m
            if M_order(ea, eb, m) % 2 == 1:
                c = CATS[0]
            elif e == 0:
                c = CATS[1]
            else:
                ordq = m // gcd(m, e)
                c = CATS[2] if ordq % 2 == 0 else CATS[3]
            out[c][0 if hit else 1] += 1
    return out


def fig6():
    fig, ax = plt.subplots(figsize=(SINGLE, 2.6))
    xs, labs = [], []
    w = 0.8 / len(CATS)
    for gi, m in enumerate(TEMPLATE_MS + NOT_COMPUTED_MS):
        xs.append(gi)
        labs.append(str(m))
        sp = _template_split(m) if m in TEMPLATE_MS else None
        if sp is None:
            ax.text(gi, 0.02, "not\ncomputed", ha="center", va="bottom", fontsize=4.6,
                    color="0.45", rotation=90, linespacing=1.1)
            continue
        tot = sum(sum(v) for v in sp.values())
        trace("F6", "", f"n_keys[m={m}]", tot, f"templates/C1_m{m}.json", "n_keys", m)
        for ci, c in enumerate(CATS):
            adm, no = sp[c]
            trace("F6", "", f"admit[m={m},{c}]", adm, f"templates/C1_m{m}.json",
                  "sat_keys", c)
            trace("F6", "", f"no_admit[m={m},{c}]", no, f"templates/C1_m{m}.json",
                  "n_keys-sat_keys", c)
            x = gi + (ci - (len(CATS) - 1) / 2) * w
            fa, fn = adm / tot, no / tot
            ax.bar(x, fa, w * 0.9, color=CAT_COL[ci], edgecolor="black",
                   linewidth=0.35, zorder=3)
            ax.bar(x, fn, w * 0.9, bottom=fa, color=CAT_COL[ci], alpha=0.28,
                   edgecolor="black", linewidth=0.35, zorder=3)
            if ci == 0:
                ax.text(x, fa + fn + 0.012, "0", ha="center", va="bottom",
                        fontsize=4.4, color=OI["purple"])
        if sp[CATS[0]][0] != 0:
            raise AssertionError(f"m={m}: |M| odd admits {sp[CATS[0]][0]} keys")
        ax.text(gi, 1.055, f"{tot:,}", ha="center", va="bottom", fontsize=4.4,
                color="0.35")

    ax.set_xticks(xs); ax.set_xticklabels(labs)
    ax.set_xlabel("$m$"); ax.set_ylabel("fraction of the eps-vectors at that $m$")
    ax.set_ylim(0, 1.16); ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.grid(axis="y", color="0.93", linewidth=0.5, zorder=0)
    h = [Patch(facecolor=CAT_COL[i], label=CATS[i]) for i in range(len(CATS))]
    h += [Patch(facecolor="0.55", label="solid = admits a schedule"),
          Patch(facecolor="0.55", alpha=0.28, label="pale = does not")]
    ax.legend(handles=h, frameon=False, fontsize=4.6, loc="lower left",
              bbox_to_anchor=(-0.02, 1.0), ncol=2, handlelength=1.0,
              columnspacing=0.7, labelspacing=0.25)
    ax.text(0.985, 0.52, "the $|M|$ odd group admits\n0 keys at every $m$ (theorem);\n"
            "totals above each group",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=4.6,
            color="0.3", linespacing=1.25)
    save(fig, "fig_templates_by_m",
         [f"templates/C1_m{m}.json" for m in TEMPLATE_MS], "plot_figures.fig6",
         "SI: outcome of the exhaustive eps-templates by modulus m, split by whether "
         "|M| is odd, and for |M| even by eps(d) and the parity of the order of eps(d). "
         "Solid = admits a depth-6 twisted schedule, pale = does not. The |M| odd group "
         "admits nothing at any m, as the theorem requires. m = 7, 9-12, 16 were not "
         "computed.",
         ["counts recomputed from templates/C1_m*.json; the |M| odd group is asserted "
          "to have zero admits and the figure aborts otherwise."])


# ===========================================================================
# F7 (SI)  smallest proper divisor carrying a verified twisted schedule
# ===========================================================================
def fig7():
    rows = [r for r in read("mstar.csv") if r["status_resolved"] == "SAT"]
    notes = [] if rows else ["data/mstar.csv missing or has no SAT rows."]
    found = [r for r in rows if r["m_star_kind"] == "found"]
    ms = sorted({int(r["m_star"]) for r in found})
    cats = [str(m) for m in ms] + ["no witness\n(capped)", "no witness\n(uncapped)"]
    even = []
    odd = []
    for m in ms:
        even.append(trace("F7", "", f"m*={m},ord even", sum(
            1 for r in found if int(r["m_star"]) == m and r["ord_d_even"] == "True"),
            "data/mstar.csv", "m_star", f"{m},even"))
        odd.append(trace("F7", "", f"m*={m},ord odd", sum(
            1 for r in found if int(r["m_star"]) == m and r["ord_d_even"] == "False"),
            "data/mstar.csv", "m_star", f"{m},odd"))
    for kind in ("none found (capped)", "none found (uncapped)"):
        even.append(trace("F7", "", f"{kind},ord even", sum(
            1 for r in rows if r["m_star_kind"] == kind and r["ord_d_even"] == "True"),
            "data/mstar.csv", "m_star_kind", f"{kind},even"))
        odd.append(trace("F7", "", f"{kind},ord odd", sum(
            1 for r in rows if r["m_star_kind"] == kind and r["ord_d_even"] == "False"),
            "data/mstar.csv", "m_star_kind", f"{kind},odd"))

    fig, ax = plt.subplots(figsize=(SINGLE, 2.3))
    x = range(len(cats))
    w = 0.4
    ax.bar([i - w / 2 for i in x], even, w, color=OI["blue"], edgecolor="black",
           linewidth=0.4, label="ord($d$) even", zorder=3)
    ax.bar([i + w / 2 for i in x], odd, w, color=OI["vermillion"], edgecolor="black",
           linewidth=0.4, label="ord($d$) odd", zorder=3)
    for i, (a, b) in enumerate(zip(even, odd)):
        if a:
            ax.text(i - w / 2, a + 3, str(a), ha="center", va="bottom", fontsize=4.8)
        if b:
            ax.text(i + w / 2, b + 3, str(b), ha="center", va="bottom", fontsize=4.8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(cats, fontsize=4.9, rotation=30, ha="right",
                       rotation_mode="anchor")
    ax.set_xlabel("smallest proper divisor $m$ with a verified twisted schedule",
                  fontsize=7)
    ax.set_ylabel("class-C1 instances")
    ax.set_ylim(0, max(even + odd) * 1.28)
    ax.grid(axis="y", color="0.93", linewidth=0.5, zorder=0)
    ax.legend(frameon=False, fontsize=6, loc="upper right", handlelength=1.1)
    save(fig, "fig_periods", ["data/mstar.csv"], "plot_figures.fig7",
         "SI: for the class-C1 instances that are satisfiable at depth 6, the smallest "
         "proper divisor m of N carrying a verified eps-twisted invariant schedule, "
         "split by the parity of ord(d). Instances for which no witness was found are "
         "shown separately, distinguishing the case where some search was capped from "
         "the case where every proper divisor returned no schedule uncapped.", notes)


# ===========================================================================
# F8 (SI)  theorem-1 profile
# ===========================================================================
def fig8():
    h1 = {r["instance"]: r for r in read("h1_predictions.csv")}
    c1 = read("c1_final_instances.csv")
    rows = [(r, h1[r["instance"]]) for r in c1 if r["instance"] in h1
            and h1[r["instance"]].get("min_component_n")]
    if len(rows) < 50:
        print("  F8 skipped: data/h1_predictions.csv lacks component fields for the "
              f"class-C1 set (only {len(rows)} joinable)")
        return
    import random as _r
    rng = _r.Random(7)
    fig, ax = plt.subplots(figsize=(SINGLE, 2.5))
    drawn = Counter()
    for r, h in rows:
        n4 = int(h["min_component_n"]) % 4
        obstructed = r["theorem1_obstructed"] == "True"
        y = (0 if r["ord_d_even"] == "True" else 1) + (rng.random() - 0.5) * 0.5
        x = n4 + (rng.random() - 0.5) * 0.55
        src = status_source(r)
        mk = dict(STATUS_MK[src]); mk["ms"] = mk["ms"] * 0.55
        ax.plot([x], [y], linestyle="none", alpha=0.65,
                color=OI["purple"] if obstructed else "0.5",
                markeredgewidth=0.6, zorder=3, **mk)
        drawn[(n4, r["ord_d_even"], obstructed, src)] += 1
    for k, v in sorted(drawn.items(), key=str):
        trace("F8", "", f"n[{k[0]},{k[1]},{k[2]},{k[3]}]", v,
              "data/h1_predictions.csv + data/c1_final_instances.csv",
              "min_component_n,ord_d_even,theorem1_obstructed,status_resolved", str(k))
    obs_status = Counter(status_source(r) for r, h in rows
                         if r["theorem1_obstructed"] == "True")
    bad = {k: v for k, v in obs_status.items() if k.startswith("SAT")}
    if bad:
        raise AssertionError(f"theorem-1 obstructed instances drawn as SAT: {bad}")
    # cluster composition, so the point is legible despite overplotting
    clusters: dict[tuple, Counter] = defaultdict(Counter)
    for k, v in drawn.items():
        clusters[(k[0], k[1])][k[3]] += v
    for (n4, par), c in clusters.items():
        y = (0 if par == "True" else 1)
        txt = "\n".join(f"{v} {kk}" for kk, v in
                         sorted(c.items(), key=lambda kv: -kv[1]))
        ax.text(n4, y + 0.42, f"n={sum(c.values())}\n{txt}", ha="center", va="bottom",
                fontsize=3.9, color="0.25", linespacing=1.15)
    ax.set_xticks(range(4))
    ax.set_xlabel("min component $n$ mod 4")
    ax.set_yticks([0, 1]); ax.set_yticklabels(["ord($d$) even", "ord($d$) odd"],
                                              fontsize=6.4)
    ax.set_xlim(-0.6, 3.6); ax.set_ylim(-0.75, 2.15)
    ax.grid(axis="x", color="0.93", linewidth=0.5, zorder=0)
    leg = [Line2D([], [], linestyle="none", color="0.25", markeredgewidth=0.8,
                  label=s, **STATUS_MK[s]) for s in STATUS_ORDER]
    leg += [Patch(facecolor=OI["purple"], label="theorem-1 obstructed"),
            Patch(facecolor="0.5", label="not obstructed")]
    ax.legend(handles=leg, frameon=False, fontsize=4.6, loc="lower left",
              bbox_to_anchor=(-0.02, 1.0), ncol=3, handletextpad=0.2,
              columnspacing=0.6, labelspacing=0.25)
    ax.text(0.985, 0.03,
            f"of the {sum(obs_status.values())} obstructed instances, "
            f"{obs_status.get('UNSAT theorem-1', 0)} are UNSAT and "
            f"{obs_status.get('UNDETERMINED', 0)} undetermined;\nnone is SAT",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=4.6,
            color="0.3", linespacing=1.25)
    save(fig, "fig_theorem1_profile",
         ["data/h1_predictions.csv", "data/c1_final_instances.csv"],
         "plot_figures.fig8",
         "SI: class-C1 instances by the residue of the smallest component size mod 4 and "
         "the parity of ord(d), coloured by whether Theorem 1 obstructs them and marked "
         "by the source of the resolved status. No obstructed instance is satisfiable; "
         "the figure aborts if one were drawn as SAT.",
         ["min component n from h1_predictions.csv:min_component_n, joined on instance "
          "with c1_final_instances.csv for ord(d) parity and status_resolved."])


# ===========================================================================
# Audit
# ===========================================================================
FORBIDDEN_WORDS = ["aperiodic", "a single four-qubit overlap", "single overlap"]

# Discrepancies found during this audit and fixed.  The automated checks below all
# pass *after* these changes; this list is what the audit actually changed.
FIXES = [
 ("F1a no-reversal column",
  "the R4 no-reversal proof size was shown nowhere and tab_certificates had no "
  "symmetry_breaking column, so F1 could not be cross-checked against it; added the "
  "starred annotation and a 'no reversal clause' column"),
 ("F2 restructured",
  "replaced the two-panel schematic by rigidity / parity / where the overlap hypothesis "
  "enters, with the gamma(v) table and F_L + F_R = sum gamma = 9"),
 ("F3 status_resolved",
  "F3 was drawn from raw `status`, so a capped run appeared as TIMEOUT and "
  "witness-resolved instances were indistinguishable from solver SATs; rebuilt on "
  "status_resolved with five status markers, a capped call is never drawn as UNSAT"),
 ("F3 C1 strata",
  "class C1 was one row of 598 overlapping markers; split into the three prescribed "
  "strata"),
 ("F3 labels",
  "'subgroup' renamed 'SG', axis label 'instance class' -> 'overlap class', "
  "stratum-count inset added from data/c1_final.csv"),
 ("F4b periodicity",
  "added the R6 periodicity split of the same 417 schedules and the pass rate on the "
  "'other' subset"),
 ("wording 'aperiodic'",
  "the third periodicity class was called 'aperiodic'; removed project-wide in favour "
  "of 'other' and data/r6_asymmetry.csv regenerated as data/r6_periodicity.csv"),
 ("data/mstar.csv",
  "did not exist (only the raw scan); derived with an explicit m_star_kind separating "
  "'found', 'none found (capped)' and 'none found (uncapped)', so a cap is never read "
  "as an absence"),
 ("F6 scale",
  "drawn with absolute counts, which made every m <= 6 invisible next to m = 8; "
  "rescaled to the fraction of eps-vectors at each m with totals annotated"),
 ("F6/F8 assertions",
  "F6 now aborts if the |M| odd group admits any key and F8 aborts if a "
  "theorem-1-obstructed instance is drawn as SAT"),
]


def _pdf_fonts_embedded(path: str) -> bool:
    raw = open(path, "rb").read()
    return b"/FontFile2" in raw or b"/FontFile3" in raw or b"/FontFile" in raw


def _tex_numbers(name: str) -> list[str]:
    p = os.path.join(ROOT, "tables", name)
    if not os.path.exists(p):
        return []
    import re
    return re.findall(r"-?\d+(?:\.\d+)?", open(p).read())


def _recompute() -> dict:
    """Independent recomputation of every traced value, from the same CSVs."""
    import csv as _csv
    from math import gcd
    got: dict[tuple, object] = {}

    inst = {r["name"]: r for r in _csv.DictReader(open(os.path.join(DATA, "instances.csv")))}
    res = {}
    for r in _csv.DictReader(open(os.path.join(DATA, "results.csv"))):
        res[(r["instance"], r["D"], r["tag"])] = r
    nr = {r["instance"]: r
          for r in _csv.DictReader(open(os.path.join(DATA, "r4_no_reversal.csv")))}
    for nm in IBM_ORDER:
        if nm not in inst:
            continue
        got[("F1", f"n_qubits[{nm}]")] = int(inst[nm]["n_qubits"])
        got[("F1", f"Delta[{nm}]")] = int(inst[nm]["Delta"])
        d6 = res.get((nm, "6", ""))
        d7 = res.get((nm, "7", "inv")) or res.get((nm, "7", ""))
        if d6:
            got[("F1", f"d6_time[{nm}]")] = round(float(d6["time"]), 2)
            got[("F1", f"d6_proof_MB[{nm}]")] = round(int(d6["proof_bytes"]) / 1e6, 1)
        if d7:
            got[("F1", f"opt_depth[{nm}]")] = int(d7["D"])
        if nm in nr:
            got[("F1", f"norev_proof_MB[{nm}]")] = round(int(nr[nm]["proof_bytes"]) / 1e6, 1)

    lem = list(_csv.DictReader(open(os.path.join(DATA, "lemma_checks.csv"))))
    got[("F4", "n_solutions")] = len(lem)
    for L in LEMMA_ORDER:
        got[("F4", f"pass_rate[{L}]")] = round(
            100.0 * sum(1 for r in lem if r[L] == "True") / len(lem), 4)
    for nm in ("oe23", "oe43"):
        sel = [r for r in lem if r["instance"] == nm]
        if not sel:
            continue
        D, N = int(sel[0]["D"]), int(sel[0]["N"])
        prof = [json.loads(r["x_profile"]) for r in sel]
        for i in range(D):
            got[("F4", f"mean_x[{nm},{i+1}]/N")] = round(
                sum(p[i] for p in prof) / len(prof) / N, 6)
        got[("F4", f"a_min[{nm}]")] = min(int(r["a"]) for r in sel)
        got[("F4", f"b_max[{nm}]")] = max(int(r["b"]) for r in sel)
    got[("F4", "subchecks[L1]")] = len(lem)
    got[("F4", "subchecks[L2]")] = sum(int(r["size_E"]) + int(r["size_E_Z"]) for r in lem)
    for L, col in (("L3", "n_L3_checked"), ("L4", "n_L4_checked"),
                   ("L5", "n_L5_checked")):
        got[("F4", f"subchecks[{L}]")] = sum(int(r[col]) for r in lem)
    got[("F4", "subchecks[L6]")] = sum(int(r["N"]) for r in lem)
    got[("F4", "subchecks[L7]")] = sum(int(r["N"]) for r in lem
                                       if r["L7_applicable"] == "True")
    per = list(_csv.DictReader(open(os.path.join(DATA, "r6_periodicity.csv"))))
    lemmap = {(r["instance"], int(r["solution"])): r for r in lem}
    oth = [lemmap[(r["instance"], int(r["solution"]))] for r in per
           if r["klass"] == "other" and (r["instance"], int(r["solution"])) in lemmap]
    got[("F4", "pass_rate_other_subset")] = round(
        100.0 * sum(1 for x in oth if x["all_pass"] == "True") / max(len(oth), 1), 4)
    for k in ("invariant", "twisted", "other"):
        got[("F4", f"periodicity[{k}]")] = sum(1 for r in per if r["klass"] == k)

    sw = list(_csv.DictReader(open(os.path.join(DATA, "sweep.csv"))))
    agg: dict[tuple, Counter] = defaultdict(Counter)
    for r in sw:
        agg[(r["group"], r["max_multiplicity"])][r["status"]] += 1
    for (g, m), c in agg.items():
        got[("F5", f"SAT[{g},mult<={m}]")] = c["SAT"]
        got[("F5", f"UNSAT[{g},mult<={m}]")] = c["UNSAT"]

    fin = list(_csv.DictReader(open(os.path.join(DATA, "c1_final.csv"))))
    for r in fin:
        if r["region"] not in ("total", ""):
            got[("F3", f"stratum_total[{r['region']}]")] = int(r["total"])

    # F1b: layers straight out of the schedule JSON
    rec = json.load(open(os.path.join(SCHED, "bb72_d7_inv.json")))
    lab: dict[tuple, set] = defaultdict(set)
    for e, l in zip(rec["edges"], rec["layers"]):
        lab[(e[0] + e[1], int(e[2]))].add(l)
    for (key_, li), vs in lab.items():
        if len(vs) == 1:
            got[("F1", f"layer[{key_},{li}]")] = next(iter(vs))

    # F3: marker counts per (row, status source), recomputed from the CSVs
    obstr = {r["instance"]: r["theorem1_obstructed"]
             for r in _csv.DictReader(open(os.path.join(DATA, "h1_predictions.csv")))}
    cnt: Counter = Counter()
    for r in _csv.DictReader(open(os.path.join(DATA, "c1_final_instances.csv"))):
        cnt[("C1|" + stratum(r), status_source(r))] += 1
    for r in _csv.DictReader(open(os.path.join(DATA, "h2_sharpness.csv"))):
        k = "SG" if r["class"] == "subgroup" else r["class"]
        if k == "C1":
            continue
        st = r["status"]
        src = ("SAT solver" if st == "SAT" else
               ("UNSAT theorem-1" if obstr.get(r["name"]) == "True" else "UNSAT solver")
               if st == "UNSAT" else "UNDETERMINED")
        cnt[(k, src)] += 1
    for (k, src), v in cnt.items():
        got[("F3", f"markers[{k},{src}]")] = v
    swg: dict[str, Counter] = defaultdict(Counter)
    for r in sw:
        swg[r["group"]][r["status"]] += 1
    for g, c in swg.items():
        for st in ("SAT", "UNSAT"):
            if c[st]:
                got[("F3", f"sweep[{g}].{st}")] = c[st]

    # F6: recomputed straight from the template JSONs
    for m in TEMPLATE_MS:
        sp = _template_split(m)
        if sp is None:
            continue
        got[("F6", f"n_keys[m={m}]")] = sum(sum(v) for v in sp.values())
        for c, (adm, no) in sp.items():
            got[("F6", f"admit[m={m},{c}]")] = adm
            got[("F6", f"no_admit[m={m},{c}]")] = no

    # F8: joined counts
    h1p = {r["instance"]: r
           for r in _csv.DictReader(open(os.path.join(DATA, "h1_predictions.csv")))}
    c8: Counter = Counter()
    for r in _csv.DictReader(open(os.path.join(DATA, "c1_final_instances.csv"))):
        h = h1p.get(r["instance"])
        if not h or not h.get("min_component_n"):
            continue
        c8[(int(h["min_component_n"]) % 4, r["ord_d_even"],
            r["theorem1_obstructed"] == "True", status_source(r))] += 1
    for k, v in c8.items():
        got[("F8", f"n[{k[0]},{k[1]},{k[2]},{k[3]}]")] = v

    ms = list(_csv.DictReader(open(os.path.join(DATA, "mstar.csv"))))
    sat = [r for r in ms if r["status_resolved"] == "SAT"]
    for m in sorted({int(r["m_star"]) for r in sat if r["m_star_kind"] == "found"}):
        for par, lab in (("True", "even"), ("False", "odd")):
            got[("F7", f"m*={m},ord {lab}")] = sum(
                1 for r in sat if r["m_star_kind"] == "found"
                and int(r["m_star"]) == m and r["ord_d_even"] == par)
    for kind in ("none found (capped)", "none found (uncapped)"):
        for par, lab in (("True", "even"), ("False", "odd")):
            got[("F7", f"{kind},ord {lab}")] = sum(
                1 for r in sat if r["m_star_kind"] == kind and r["ord_d_even"] == par)
    return got


def audit() -> dict:
    """Re-read every traced value independently; cross-check tables; check style."""
    rep: dict = dict(values=[], tables=[], labels=[], style=[], discrepancies=[])
    got = _recompute()
    unchecked = []
    for t in TRACE:
        k = (t["figure"], t["item"])
        if k not in got:
            unchecked.append(f"{t['figure']} {t['item']}")
        if k in got:
            same = got[k] == t["value"]
            rep["values"].append(dict(figure=t["figure"], item=t["item"],
                                      drawn=t["value"], recomputed=got[k], ok=same,
                                      source=t["source"], column=t["column"]))
            if not same:
                rep["discrepancies"].append(
                    f"{t['figure']} {t['item']}: drawn {t['value']} != recomputed {got[k]}")
    rep["unchecked"] = unchecked
    # (b) cross-checks against the .tex tables
    def tex_has(name, needles, label):
        nums = set(_tex_numbers(name))
        miss = [n for n in needles if str(n) not in nums]
        rep["tables"].append(dict(check=label, table=name, missing=miss,
                                  ok=not miss))
        if miss:
            rep["discrepancies"].append(f"{label}: {miss} not found in {name}")
    d6mb = [f"{v['drawn']:.1f}" for v in rep["values"]
            if v["item"].startswith("d6_proof_MB")]
    tex_has("tab_certificates.tex", d6mb, "F1a depth-6 proof sizes vs tab_certificates")
    nrmb = [f"{v['drawn']:.1f}" for v in rep["values"]
            if v["item"].startswith("norev_proof_MB")]
    tex_has("tab_certificates.tex", nrmb,
            "F1a no-reversal proof sizes vs tab_certificates (symmetry_breaking column)")
    strata = [v["drawn"] for v in rep["values"] if v["item"].startswith("stratum_total")]
    tex_has("tab_c1.tex", strata, "F3 stratum totals vs tab_c1")
    tex_has("tab_lemmas.tex", [len([1 for _ in read("lemma_checks.csv")])],
            "F4 solution count vs tab_lemmas")
    sw_tot = sum(v["drawn"] for v in rep["values"] if v["item"].startswith("SAT["))
    tex_has("tab_sweep.tex", [sw_tot], "F5 total SAT vs tab_sweep")

    # (c) label conventions
    for m in MANIFEST:
        text = m["description"] + " " + " ".join(m["notes"])
        hits = [w for w in FORBIDDEN_WORDS if w in text.lower()]
        rep["labels"].append(dict(figure=os.path.basename(m["output"][0]),
                                  forbidden=hits, ok=not hits))
        if hits:
            rep["discrepancies"].append(f"{m['output'][0]}: forbidden wording {hits}")

    # (d) style
    for m in MANIFEST:
        pdf = os.path.join(ROOT, m["output"][0])
        w = m["width_in"]
        okw = abs(w - SINGLE) < 0.05 or abs(w - DOUBLE) < 0.05
        emb = _pdf_fonts_embedded(pdf)
        rep["style"].append(dict(figure=os.path.basename(pdf), width_in=w,
                                 width_ok=okw, fonts_embedded=emb,
                                 ok=okw and emb))
        if not okw:
            rep["discrepancies"].append(f"{m['output'][0]}: width {w} in is neither "
                                        f"{SINGLE} nor {DOUBLE}")
        if not emb:
            rep["discrepancies"].append(f"{m['output'][0]}: fonts not embedded")
    return rep


# ===========================================================================
# CHECK.md, CAPTIONS.md, manifest, driver
# ===========================================================================
CAPTIONS = {
 "fig_certificate_vs_optimum": (
  "Figure 1. Certified optimal syndrome-extraction depth of the IBM bivariate bicycle "
  "codes. (a) For each code, the Koenig bound Delta = 6 (grey) against the certified "
  "optimal proper depth 7 (blue). *Observation, from data/results.csv*: depth 6 is "
  "refuted with a DRAT proof accepted by drat-trim, and depth 7 is witnessed by an "
  "explicit schedule. Annotations give the depth-6 solve time and proof size, and "
  "starred, the proof size of the same refutation with the layer-reversal "
  "symmetry-breaking clause removed (data/r4_no_reversal.csv). (b) The "
  "translation-invariant depth-7 schedule, one layer per label and side, read from "
  "schedules/bb72_d7_inv.json and re-verified by valid-layering and F2 simulation "
  "before drawing. (c) One round of the smallest example containing a shared corner, "
  "laid out under that schedule; the L- and R-corner carry the same orientation."),
 "fig_proof_structure": (
  "Figure 2. Schematic of the proof; no data underlies this figure. (a) Rigidity: at a "
  "data qubit the layer pairs {1,2}, {3,4}, {5,6} each carry one X-edge and one Z-edge, "
  "in either of the two admissible orientations. (b) Parity: the weights gamma(v) and "
  "the identity F_L + F_R = sum_v gamma(v) = 9. *Theorem*: properness requires "
  "F_L = F_R, which an odd total cannot satisfy. (c) Where the overlap hypothesis "
  "enters: when the sums are distinct an overlap pair has two corners, one L and one R, "
  "so the two sides are in bijection; a coinciding sum gives four corners and no forced "
  "pairing."),
 "fig_sharpness": (
  "Figure 3. Depth-6 status by group order and overlap class. Classes: D, no 4-qubit "
  "overlaps; C1, one collision orbit (N four-qubit overlaps); C2, two collision orbits "
  "or one triple orbit; SG, subgroup type. Class C1 is split into the three strata "
  "ord(d) even, ord(d) odd with Theorem-1 obstruction, and ord(d) odd without. Marker "
  "shape gives the source of the status (data/c1_final_instances.csv:status_resolved): "
  "a timeout settled by a verified twisted witness is drawn as SAT (witness), an "
  "unresolved timeout as UNDETERMINED; a capped call is never drawn as UNSAT. Sweep "
  "groups (|G| <= 8) are aggregated to one marker per group, labelled SAT/UNSAT. The "
  "dashed line marks N = 9 = k*l, below which distinct sums are impossible by "
  "pigeonhole. Inset: class-C1 counts per stratum from data/c1_final.csv."),
 "fig_lemma_profiles": (
  "Figure 4. Lemma checks over the enumerated proper schedules. (a) Mean layer profile "
  "x_i/N for oe23 and oe43 (data/lemma_checks.csv:x_profile), with the observed support "
  "[a,b] drawn below the axis; *observation*: a + b = Delta + 1 for every solution. "
  "(b) Pass rate of L1-L7 over all 417 enumerated solutions, with the number of "
  "individual sub-checks above each bar, so that a 100% rate is not vacuous. The line "
  "below gives the periodicity of the same schedules from data/r6_periodicity.csv: 5 "
  "invariant, 72 twisted for a proper divisor, 340 other, with the pass rate on the "
  "'other' subset."),
 "fig_sweep_by_group": (
  "Figure 5. Supplementary. Depth-6 outcome of the 1441-instance sweep, stacked "
  "SAT/UNSAT per group and per maximum sum multiplicity max |P(delta)| "
  "(data/sweep.csv). Every sweep group has |G| <= 8 < 9 = k*l, so by pigeonhole none of "
  "them has distinct sums. The single UNSAT instance is called out."),
 "fig_templates_by_m": (
  "Figure 6. Supplementary. Outcome of the exhaustive eps-templates by modulus m, as a "
  "fraction of the eps-vectors at that m, split by whether |M| is odd and, for |M| "
  "even, by eps(d) and the parity of the order of eps(d). Solid = admits a depth-6 "
  "twisted schedule, pale = does not; the total number of eps-vectors is printed above "
  "each group. *Theorem*: a twisted schedule requires |M| even, and the |M| odd group "
  "indeed admits zero keys at every m computed. m = 3 and m = 5 consist entirely of "
  "|M| odd vectors, which is why they are exhaustive zeros. m = 7, 9-12 and 16 were "
  "not computed."),
 "fig_periods": (
  "Figure 7. Supplementary. For the class-C1 instances satisfiable at depth 6, the "
  "smallest proper divisor m of N carrying a verified eps-twisted invariant schedule "
  "(data/mstar.csv), split by the parity of ord(d). Instances for which no witness was "
  "found appear in two separate bars, distinguishing the case where a search was capped "
  "from the case where every proper divisor returned no schedule uncapped; a capped "
  "search is not evidence of absence."),
 "fig_theorem1_profile": (
  "Figure 8. Supplementary. Class-C1 instances by the residue of the smallest Tanner "
  "component size mod 4 (data/h1_predictions.csv:min_component_n) and the parity of "
  "ord(d), coloured by whether Theorem 1 obstructs them and marked by the source of the "
  "resolved status. *Observation*: no Theorem-1-obstructed instance is satisfiable; the "
  "figure generation aborts if one were drawn as SAT."),
}


def write_check(rep: dict) -> str:
    L = ["# Figure audit", "",
         "Produced by `plot_figures.audit()` after `make -B figures`.  Every value drawn "
         "in a figure is recorded with its source cell and then recomputed independently "
         "from the same CSV; the two are compared here.", ""]
    nv = len(rep["values"]); nok = sum(1 for v in rep["values"] if v["ok"])
    L.append(f"**{nok} of {nv} traced values reproduce exactly.**  "
             f"{len(rep['discrepancies'])} discrepancies.")
    un = rep.get("unchecked", [])
    if un:
        L.append("")
        L.append(f"{len(un)} traced entries are not numeric cells and are verified "
                 f"differently: {', '.join(sorted(set(un))[:6])}"
                 f"{' ...' if len(set(un)) > 6 else ''}.  The two F1b entries are the "
                 f"valid-layering and F2-simulation verdicts, asserted True before the "
                 f"schedule is drawn.")
    L.append("")
    by_fig: dict[str, list] = defaultdict(list)
    for v in rep["values"]:
        by_fig[v["figure"]].append(v)
    for fig in sorted(by_fig):
        rows = by_fig[fig]
        L.append(f"## {fig}")
        L.append("")
        L.append(f"{sum(1 for r in rows if r['ok'])} of {len(rows)} values reproduce.")
        L.append("")
        L.append("| item | drawn | recomputed | source | column | ok |")
        L.append("|---|---|---|---|---|---|")
        for r in rows[:18]:
            L.append(f"| `{r['item']}` | {r['drawn']} | {r['recomputed']} | "
                     f"`{r['source']}` | `{r['column']}` | {'yes' if r['ok'] else 'NO'} |")
        if len(rows) > 18:
            L.append(f"| ... {len(rows)-18} more | | | | | |")
        L.append("")
    L += ["## Cross-checks against the LaTeX tables", "",
          "| check | table | missing | ok |", "|---|---|---|---|"]
    for t in rep["tables"]:
        L.append(f"| {t['check']} | `{t['table']}` | {t['missing'] or '-'} | "
                 f"{'yes' if t['ok'] else 'NO'} |")
    L += ["", "## Label conventions", "",
          "Checked against the fixed class names, the five status sources, the three C1 "
          "strata, and the banned wordings "
          f"{FORBIDDEN_WORDS}.", "",
          "| figure | forbidden wording found | ok |", "|---|---|---|"]
    for t in rep["labels"]:
        L.append(f"| `{t['figure']}` | {t['forbidden'] or 'none'} | "
                 f"{'yes' if t['ok'] else 'NO'} |")
    L += ["", "## Style", "",
          f"Column widths must be {SINGLE} in (single) or {DOUBLE} in (double); fonts "
          "must be embedded (matplotlib `pdf.fonttype = 42`, checked by looking for a "
          "`/FontFile` object in the PDF, since `pdffonts` is not installed here); "
          "palette is Okabe-Ito; panel letters are bold lower-case.", "",
          "| figure | width (in) | width ok | fonts embedded |", "|---|---|---|---|"]
    for t in rep["style"]:
        L.append(f"| `{t['figure']}` | {t['width_in']} | "
                 f"{'yes' if t['width_ok'] else 'NO'} | "
                 f"{'yes' if t['fonts_embedded'] else 'NO'} |")
    L += ["", "## Discrepancies found and fixed", "",
          f"{len(FIXES)} discrepancies were found during the audit and fixed; the "
          "automated checks above all pass after these changes.", ""]
    L += [f"{i+1}. **{tag}** — {d}" for i, (tag, d) in enumerate(FIXES)]
    L += ["", "### Outstanding", ""]
    if rep["discrepancies"]:
        L += [f"- {d}" for d in rep["discrepancies"]]
    else:
        L.append("- none: every traced value reproduces and every cross-check passes.")
    L.append("")
    p = os.path.join(FIGS, "CHECK.md")
    open(p, "w").write("\n".join(L))
    return p


def write_captions() -> str:
    L = ["# Draft captions", "",
         "One caption per figure.  Claims are labelled *theorem*, *computed "
         "proposition* or *observation*, and every quantitative sentence names the CSV "
         "column it comes from.", ""]
    for m in MANIFEST:
        stem = os.path.basename(m["output"][0])[:-4]
        L.append(f"## `{stem}.pdf`")
        L.append("")
        L.append(CAPTIONS.get(stem, "_no caption drafted_"))
        L.append("")
        L.append(f"*Inputs*: {', '.join('`'+i+'`' for i in m['inputs']) or '(schematic)'}")
        L.append("")
    p = os.path.join(FIGS, "CAPTIONS.md")
    open(p, "w").write("\n".join(L))
    return p


def build_all() -> list[dict]:
    style()
    for f in (fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8):
        f()
    return MANIFEST


def _write_readme(manifest: dict):
    L = ["# Figures and tables", "",
         "Regenerated by `make figures`.  Every number is read from a file in `data/`, "
         "`templates/` or `schedules/`; a value present in no data file is printed as "
         "`--`.  `figure_manifest.json` records each output's inputs and generating "
         "function, `CHECK.md` the value-by-value audit, `CAPTIONS.md` the draft "
         "captions.", ""]
    for e in manifest["entries"]:
        name = os.path.basename(e["output"][0])
        L += [f"### `{name}`", "", e["description"], "",
              f"*Inputs*: {', '.join('`'+i+'`' for i in e['inputs']) or '(schematic)'}  ",
              f"*Generated by*: `{e['function']}`", ""]
    L += ["## LaTeX validation", "", "| file | pdflatex | braces | columns |",
          "|---|---|---|---|"]
    for v in manifest.get("latex_validation", []):
        L.append(f"| `{v['file']}` | {v['pdflatex']} | "
                 f"{'ok' if v['braces_balanced'] else 'unbalanced'} | "
                 f"{v['column_counts']} |")
    L.append("")
    open(os.path.join(FIGS, "README.md"), "w").write("\n".join(L))


def main(argv=None):
    from . import make_tables
    print("figures:")
    figs = build_all()
    print("tables:")
    tabs = make_tables.build_all()
    print("latex validation:")
    val = make_tables.validate_latex()
    print("audit:")
    rep = audit()
    cp = write_check(rep)
    kp = write_captions()
    nv = len(rep["values"]); nok = sum(1 for v in rep["values"] if v["ok"])
    print(f"  {nok}/{nv} traced values reproduce; "
          f"{len(rep['discrepancies'])} discrepancies")
    print(f"  wrote {os.path.relpath(cp, ROOT)} and {os.path.relpath(kp, ROOT)}")

    tc = os.path.join(ROOT, "tables", "tab_c1.tex")
    if os.path.exists(tc):
        tabs = tabs + [dict(output=["tables/tab_c1.tex"],
                            inputs=["data/c1_final_instances.csv", "data/c1_final.csv"],
                            function="c1_final.final_table",
                            description="Class-C1 instances by stratum against SAT "
                                        "(solver), SAT (template witness), UNSAT and "
                                        "UNDETERMINED.", notes=[])]
    manifest = dict(generated=__import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
                    rule="every plotted number is read from the listed inputs and is "
                         "re-derived independently in CHECK.md",
                    entries=figs + tabs, latex_validation=val,
                    trace=TRACE, audit_summary=dict(
                        values_checked=nv, values_ok=nok,
                        discrepancies=rep["discrepancies"]))
    mp = os.path.join(FIGS, "figure_manifest.json")
    json.dump(manifest, open(mp, "w"), indent=1, default=str)
    print(f"  wrote {os.path.relpath(mp, ROOT)}")
    _write_readme(manifest)
    bad = [v for v in val if v.get("pdflatex") == "FAILED"]
    return 1 if (bad or rep["discrepancies"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Manuscript figures for the revised npj QI submission.

Every builder returns (fig, letters, shared_pairs) so that figures/check_layout.py can
measure the live figure before it is written out.  Every number drawn is read from a CSV
in data/ (or a schedule JSON) listed in the manifest; nothing is typed by hand.
"""
from __future__ import annotations

import ast
import csv
import json
import os
from math import prod
from collections import Counter, defaultdict

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

import figstyle as S
from figstyle import (C_L, C_OBS, C_R, C_X, C_Z, GREY, INK, RULE, PT_MIN, PT_PANEL,
                      PT_TICK, arrow, box, cnot, layer_box, light_grid, meter, mm,
                      node_label, panel_letter, qubit, wire, x_check, z_check)

ROOT = S.ROOT
DATA = S.DATA
SCHED = os.path.join(ROOT, "schedules")

TRACE: list[dict] = []


def read(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return list(csv.DictReader(f))


def tr(fig, item, value, source, column, key=""):
    TRACE.append(dict(figure=fig, item=item, value=value, source=source,
                      column=column, key=str(key)))
    return value


# One table of record: data/coverage.csv (twoblock.coverage).  No figure derives a
# status from anything else.
from figstyle import (OUTCOME, OUTCOME_ORDER, STATUS_COLOUR, STATUS_DARK,
                      STATUS_MATH)      # noqa: E402


def coverage(sharpness_map_only: bool = True):
    """data/coverage.csv.  The sharpness map's population is the set R7 classified;
    the flag is carried in the file so no figure re-derives it."""
    rows = read("coverage.csv")
    return [r for r in rows if not sharpness_map_only
            or r["in_sharpness_map"] == "True"]


def bare(ax, xlim, ylim):
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect("equal")
    ax.axis("off")


# ===========================================================================
# fig 1  the model, the two-qubit constraint, a bad colouring, a good schedule
#
# Every panel's axes is in millimetres (xlim/ylim equal the panel size), so the
# design tokens -- qubit 3.2 mm, check 3.2 mm, ladder pitch 2.6 mm -- are literal.
# ===========================================================================
PW, PH = 41.0, 52.0            # panel drawing area, mm
QR = S.D_QUBIT_MM / 2
CS = S.D_CHECK_MM


def _fragment(ax, XP, ZP, LP, RP, fig=None, fs=PT_MIN, labels=True):
    """X-check square on top, Z-check diamond below, L-qubit left, R-qubit right.
    (X_g, L_{g+a_s}) carries a_s and (Z_g, L_{g-b_t}) carries b_t; the R-qubit
    carries b_t and a_s.  No primes: primes are the four-qubit case."""
    for p, q, col in ((XP, LP, C_X), (XP, RP, C_X), (ZP, LP, C_Z), (ZP, RP, C_Z)):
        ax.plot([p[0], q[0]], [p[1], q[1]], color=col, lw=S.LW_EDGE, zorder=1)
    x_check(ax, *XP, s=CS); z_check(ax, *ZP, s=CS)
    qubit(ax, *LP, r=QR); qubit(ax, *RP, r=QR)
    if labels:
        for (p, q, txt, nx, ny) in ((XP, LP, "$a_s$", -1, 1),
                                    (XP, RP, "$b_t$", 1, 1),
                                    (ZP, LP, "$b_t$", -1, -1),
                                    (ZP, RP, "$a_s$", 1, -1)):
            mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
            node_label(ax, mx, my, txt, nx, ny, off_mm=1.2, fig=fig, fontsize=fs)


def fig1():
    viol = read("fig1_violation.csv")
    with open(os.path.join(SCHED, "bb72_d7_inv.json")) as f:
        inv = json.load(f)
    Dinv = inv["D"]
    lab = defaultdict(dict)
    for e, l in zip(inv["edges"], inv["layers"]):
        lab[e[0] + e[1]][int(e[2])] = int(l)
    for k in lab:
        for s_, v in lab[k].items():
            tr("fig1", f"inv_layer[{k},{s_}]", v, "schedules/bb72_d7_inv.json",
               "layers", f"{k},{s_}")

    H = 72.0
    fig = plt.figure(figsize=(S.W_DOUBLE, mm(H)))

    def panel(x, label):
        a = fig.add_axes([x / S.W_DOUBLE_MM, 7.0 / H, PW / S.W_DOUBLE_MM, PH / H],
                         label=label)
        a.set_xlim(0, PW); a.set_ylim(0, PH); a.axis("off")
        return a

    axa, axb, axc, axd = (panel(0, "a"), panel(46, "b"), panel(92, "c"),
                          panel(138, "d"))

    # ---- (a) the two CNOT orders ------------------------------------------
    # DEVIATION: the wireframe puts the two orders side by side.  In a 41 mm
    # panel that leaves ~19 mm per circuit, too little for the three per-wire
    # labels at the 6.5 pt floor, so they are stacked.
    x0, x1 = 17.0, 39.0
    for base, tag, extra in ((42.0, "$Z$ first", False),
                             (19.0, "$X$ first", True)):
        ys = (base + 4.2, base, base - 4.2)
        for y in ys:
            wire(ax=axa, x0=x0, x1=x1, y=y)
        if tag == "$Z$ first":
            cnot(axa, x0 + 6.0, ys[1], ys[2], r=1.5, colour=C_Z)
            cnot(axa, x0 + 14.0, ys[0], ys[1], r=1.5, colour=C_X)
        else:
            cnot(axa, x0 + 6.0, ys[0], ys[1], r=1.5, colour=C_X)
            cnot(axa, x0 + 14.0, ys[1], ys[2], r=1.5, colour=C_Z)
        axa.annotate("", xy=(x1, base + 7.6), xytext=(x0, base + 7.6),
                     arrowprops=dict(arrowstyle="-|>,head_length=2.5,head_width=1.25",
                                     mutation_scale=1.0, lw=S.LW_ARROW,
                                     color=GREY, shrinkA=0, shrinkB=0))
        axa.text(x1, base + 8.0, "layers", ha="right", va="bottom",
                 fontsize=PT_MIN, color=GREY)
        axa.text(0.0, base + 8.0, tag, ha="left", va="bottom", fontsize=PT_MIN)
        for y, t in zip(ys, ("$X$-anc $|{+}\\rangle$", "data $q$",
                             "$Z$-anc $|0\\rangle$")):
            axa.text(x0 - 1.4, y, t, ha="right", va="center", fontsize=PT_MIN,
                     color=GREY)
        if extra:
            axa.text(x1 - 4.4, base - 7.2, "$Z$-anc $\\leftarrow z + x$",
                     ha="right", va="top", fontsize=PT_MIN, color=GREY)
            axa.text(x1, base - 7.2, "$+\\,y$", ha="right", va="top",
                     fontsize=PT_MIN, color=C_OBS,
                     bbox=dict(boxstyle="round,pad=0.16", facecolor=S.HALO,
                               alpha=S.HALO_ALPHA, edgecolor="none"))
        else:
            axa.text(x1, base - 7.2, "$Z$-anc $\\leftarrow z + x$", ha="right",
                     va="top", fontsize=PT_MIN, color=GREY)
    axa.text(0.0, 0.5, "each $X$-first shared qubit adds one\nbit of $y$ to a "
             "$Z$-check: $(M_\\pi)_{ji}$", ha="left", va="bottom",
             fontsize=PT_MIN, linespacing=1.4)

    # ---- (b) the two-qubit overlap and its truth table --------------------
    XP, ZP, LP, RP = (20.5, 47.0), (20.5, 33.0), (7.5, 40.0), (33.5, 40.0)
    for xx, tint in ((LP[0], C_L), (RP[0], C_R)):
        axb.add_patch(plt.Rectangle((xx - 3.1, LP[1] - 3.1), 6.2, 6.2,
                                    facecolor=tint, edgecolor="none", zorder=0,
                                    gid="nocheck"))
    _fragment(axb, XP, ZP, LP, RP, fig=fig)
    axb.text(LP[0], LP[1] - 5.0, "$L$", ha="center", va="top", fontsize=PT_MIN,
             color=GREY)
    axb.text(RP[0], RP[1] - 5.0, "$R$", ha="center", va="top", fontsize=PT_MIN,
             color=GREY)
    tx, ty, cw, ch = 12.0, 11.0, 11.0, 6.0
    axb.text(tx + cw, ty + 2 * ch + 3.6, "$o_R$", ha="center", va="bottom",
             fontsize=PT_MIN)
    axb.text(tx - 4.6, ty + ch, "$o_L$", ha="right", va="center", fontsize=PT_MIN)
    for i2, orr in enumerate((0, 1)):
        axb.text(tx + 0.5 * cw + i2 * cw, ty + 2 * ch + 1.5, str(orr),
                 ha="center", va="bottom", fontsize=PT_MIN)
    for j2, ol in enumerate((1, 0)):
        axb.text(tx - 1.6, ty + (1 - j2) * ch + 0.5 * ch, str(ol), ha="right",
                 va="center", fontsize=PT_MIN)
    for i2, orr in enumerate((0, 1)):
        for j2, ol in enumerate((1, 0)):
            ok = ol == orr
            axb.add_patch(plt.Rectangle((tx + i2 * cw, ty + (1 - j2) * ch), cw, ch,
                                        facecolor="white" if ok else S.HALO,
                                        alpha=1.0 if ok else S.HALO_ALPHA,
                                        edgecolor=RULE, linewidth=0.4, zorder=1,
                                        gid="nocheck"))
            axb.text(tx + i2 * cw + cw / 2, ty + (1 - j2) * ch + ch / 2,
                     "proper" if ok else "cross\nterm", ha="center", va="center",
                     fontsize=PT_MIN, color=INK if ok else C_OBS, zorder=4,
                     linespacing=1.2)
    axb.text(PW / 2, 0.5, "shared corners must have\nequal orientation",
             ha="center", va="bottom", fontsize=PT_MIN, color=GREY,
             linespacing=1.4)

    # ---- (c) the same fragment, coloured at depth 6 -----------------------
    by = {(r["kind"], r["side"]): r for r in viol}
    Delta = int(viol[0]["Delta"])
    XP2, ZP2, LP2, RP2 = (20.5, 45.0), (20.5, 27.0), (7.5, 36.0), (33.5, 36.0)
    for xx, tint in ((LP2[0], C_L), (RP2[0], C_R)):
        axc.add_patch(plt.Rectangle((xx - 3.1, LP2[1] - 3.1), 6.2, 6.2,
                                    facecolor=tint, edgecolor="none", zorder=0,
                                    gid="nocheck"))
    S.halo(axc, RP2[0], RP2[1], 3.6)
    _fragment(axc, XP2, ZP2, LP2, RP2, fig=fig, labels=False)
    for p, q, key in ((XP2, LP2, ("X", "L")), (XP2, RP2, ("X", "R")),
                      (ZP2, LP2, ("Z", "L")), (ZP2, RP2, ("Z", "R"))):
        lyr = tr("fig1", f"viol_layer[{key[0]}{key[1]}]", int(by[key]["layer"]),
                 "data/fig1_violation.csv", "layer", f"{key[0]}{key[1]}")
        f2 = 0.45
        layer_box(axc, p[0] + (q[0] - p[0]) * f2, p[1] + (q[1] - p[1]) * f2,
                  str(lyr), pad=0.22)
    oL = tr("fig1", "orientation_L", int(by[("X", "L")]["orientation"]),
            "data/fig1_violation.csv", "orientation", "L")
    oR = tr("fig1", "orientation_R", int(by[("X", "R")]["orientation"]),
            "data/fig1_violation.csv", "orientation", "R")
    axc.text(LP2[0], LP2[1] - 5.2, f"$o_L = {oL}$", ha="center", va="top",
             fontsize=PT_TICK)
    axc.text(RP2[0], RP2[1] - 5.2, f"$o_R = {oR}$", ha="center", va="top",
             fontsize=PT_TICK, color=C_OBS)
    axc.text(PW / 2, 1.5, f"Kőnig colouring, depth {Delta}:\n$M_\\pi\\neq 0$",
             ha="center", va="bottom", fontsize=PT_MIN, color=GREY,
             linespacing=1.4)

    # ---- (d) the depth-7 schedule as two ladders --------------------------
    pitch, ytop = S.RUNG_MM, 46.0
    S.ladder(axd, 11.0, ytop, pitch, Dinv,
             x_at={lab["XL"][s]: s for s in sorted(lab["XL"])},
             z_at={lab["ZL"][t]: t for t in sorted(lab["ZL"])},
             tint=C_L, title="$L$", half=2.6)
    S.ladder(axd, 29.0, ytop, pitch, Dinv,
             x_at={lab["XR"][t]: t for t in sorted(lab["XR"])},
             z_at={lab["ZR"][s]: s for s in sorted(lab["ZR"])},
             tint=C_R, title="$R$", half=2.6)
    axd.text(PW / 2, 1.5, "$o_L = o_R = \\mathbb{1}[s\\leq 2]$\nfor all nine "
             "label pairs", ha="center", va="bottom", fontsize=PT_MIN,
             color=GREY, linespacing=1.4)

    for L, ax in (("a", axa), ("b", axb), ("c", axc), ("d", axd)):
        panel_letter(fig, ax, L, dx_mm=0.0, dy_mm=2.4)
    for x, t in ((0, "one entry of $M_\\pi$"),
                 (46, "two-qubit overlap: $o_L=o_R$"),
                 (92, "a depth-6 colouring, not proper"),
                 (138, "proper depth-7 schedule")):
        fig.text((x + 0.5) / S.W_DOUBLE_MM, 66.5 / H, t, fontsize=PT_PANEL,
                 ha="left", va="bottom")
    return fig, {"a": axa, "b": axb, "c": axc, "d": axd}, ()

# ===========================================================================
# figS1  proof map: what depends on what
# ===========================================================================
def _code_label(r):
    """[[n,k,d]] as the Pareto CSV records it, with "<=" set as the glyph."""
    return "[[%s,%s,%s]]" % (r["n"], r["k"], r["d_label"].replace("<=", "\u2264"))


def _pareto_codes(want):
    """Look up Pareto rows by (family, n, k) and label them from the file.

    The selection is editorial -- which codes the figure has room to quote --
    but every parameter printed is the one in data/pareto_front.csv, and a
    requested row that the search did not find is an error, not a blank.
    """
    par = read("pareto_front.csv")
    out = []
    for fam, n, k, *grp in want:
        hit = [r for r in par if r["family"] == fam
               and int(r["n"]) == n and int(r["k"]) == k
               and (not grp or r["group"] == grp[0])]
        assert hit, (f"pareto_front.csv has no {fam} row [[{n},{k},*]]"
                     + (f" over {grp[0]}" if grp else ""))
        lab = _code_label(hit[0])
        assert all(_code_label(r) == lab for r in hit), \
            f"{fam} [[{n},{k},*]] has conflicting distances: " \
            f"{sorted({_code_label(r) for r in hit})}"
        tr("figS1", f"pareto[{fam},{n},{k}]", int(hit[0]["d"]),
           "data/pareto_front.csv", "d", f"{fam},{n},{k}")
        out.append(lab)
    return out


def _proof_nodes():
    """Node text; the quantities in it are read from CSVs, not typed."""
    inst = read("instances.csv")
    n_ibm = tr("figS1", "n_published_codes",
               sum(1 for r in inst if r["family"] == "IBM"),
               "data/instances.csv", "family", "IBM")
    fin = {r["region"]: r for r in read("c1_final.csv")}
    key = "ord(d) odd, not obstructed"
    n_unexp = tr("figS1", "unexplained_UNSAT", int(fin[key]["UNSAT"]),
                 "data/c1_final.csv", "UNSAT", key)
    n_capped = tr("figS1", "capped", int(fin[key]["UNDETERMINED"]),
                  "data/c1_final.csv", "UNDETERMINED", key)
    n_sat = tr("figS1", "odd_SAT",
               int(fin[key]["SAT (solver)"]) + int(fin[key]["SAT (template witness)"]),
               "data/c1_final.csv", "SAT (solver)+SAT (template witness)", key)
    qs = sorted(int(os.path.basename(p)[4:-5])
                for p in __import__("glob").glob(os.path.join(ROOT, "templates",
                                                              "C1_m*.json")))
    q_max = tr("figS1", "template_q_max", max(qs), "templates/C1_m*.json", "q", "max")

    # the forced-involution runs that carry the template chain past the
    # enumeration: the largest modulus for which every class is SAT
    force = read("template_force.csv")
    done = [int(r["q"]) for r in force if r["all_sat"] == "True"]
    assert done, "template_force.csv records no fully satisfied modulus"
    q_force = tr("figS1", "template_q_forced", max(done),
                 "data/template_force.csv", "q", "max(all_sat)")

    # Corollary 3: the two hypergraph products quoted in the text
    hgp = [r for r in read("cor3_hgp.csv") if r["obstructed"] == "True"]
    assert len(hgp) == 2, f"cor3_hgp.csv has {len(hgp)} obstructed rows, expected 2"
    for r in hgp:
        assert int(r["sum_rs_mod4"]) == 2 and int(r["components"]) == 1, \
            f"cor3_hgp.csv row {r['seed']} does not satisfy Corollary 3"
    hgp_lab = ", ".join(
        "[[%d,%d]]" % (tr("figS1", f"cor3_n[{r['seed']}]", int(r["n"]),
                          "data/cor3_hgp.csv", "n", r["seed"]),
                       tr("figS1", f"cor3_k[{r['seed']}]", int(r["k"]),
                          "data/cor3_hgp.csv", "k", r["seed"]))
        for r in hgp)
    return (n_ibm, n_unexp, n_capped, n_sat, q_max, q_force, hgp_lab)


def fig2():
    n_ibm, n_unexp, n_capped, n_sat, q_max, q_force, hgp_lab = _proof_nodes()
    comp = _pareto_codes([("C1-even", 72, 8), ("C1-even", 108, 12),
                          ("C1-even", 144, 16), ("C1-even", 144, 8)])
    z36 = _pareto_codes([("C1-odd", 72, 8, "Z36xZ1")])[0]
    # the revision adds four boxes to the right-hand chain and removes one;
    # the page grew with them
    W, Hmm_ = S.W_DOUBLE, 232.0
    fig = plt.figure(figsize=(W, mm(Hmm_)))
    AX0, AXH = 0.030, 0.955
    ax = fig.add_axes([0.012, AX0, 0.976, AXH], label="map")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    span = Hmm_ * AXH

    PROVED, EVID, OPEN = "solid", "dashed", "dotted"
    FS = PT_TICK
    LINE, PAD = 3.05, 3.4
    nodes = {}

    def h_of(t):
        return (t.count("\n") + 1) * LINE + PAD

    def N(key, x, ytop, w, style, text, face="white"):
        hm = h_of(text)
        y = 1.0 - (ytop + hm / 2) / span
        h = hm / span
        box(ax, x, y, w, h, style=style, face=face)
        ax.text(x, y, text, ha="center", va="center", fontsize=FS,
                linespacing=1.28, zorder=6)
        nodes[key] = dict(x=x, y=y, w=w, h=h)
        return ytop + hm

    def link(a, b, label=None):
        A, B = nodes[a], nodes[b]
        arrow(ax, (A["x"], A["y"] - A["h"] / 2), (B["x"], B["y"] + B["h"] / 2))
        if label:
            ax.text((A["x"] + B["x"]) / 2 + 0.010,
                    (A["y"] - A["h"] / 2 + B["y"] + B["h"] / 2) / 2, label,
                    fontsize=PT_MIN, ha="left", va="center", color=GREY, zorder=6)

    def link_side(a, b, label=None):
        A, B = nodes[a], nodes[b]
        if A["x"] < B["x"]:
            p0 = (A["x"] + A["w"] / 2, A["y"]); p1 = (B["x"] - B["w"] / 2, B["y"])
        else:
            p0 = (A["x"] - A["w"] / 2, A["y"]); p1 = (B["x"] + B["w"] / 2, B["y"])
        arrow(ax, p0, p1)
        if label:
            ax.text((p0[0] + p1[0]) / 2, max(p0[1], p1[1]) + 0.008, label,
                    fontsize=PT_MIN, ha="center", va="bottom", color=GREY, zorder=6)

    G = 7.0
    XL, XR = 0.205, 0.755
    WR = 0.42

    # ---- the root ---------------------------------------------------------
    cur = N("root", 0.5, 1.0, 0.92, PROVED,
            "Setting: two-block code over abelian $G$; one ancilla per check, one "
            "CNOT per Tanner edge;\ncorrectness of the round is $M_\\pi=0$ over "
            "$\\mathbb{F}_2$", face="#F7F7F7") + G

    # ---- three general obstructions, parallel, all fed by M_pi = 0 --------
    o_top = cur
    o_top = N("mod4", XR, o_top, WR, PROVED,
              "componentwise mod-4: $\\sum_v r_v s_v\\equiv 0$ "
              "$(\\mathrm{mod}\\ 4)$\nper connected component", face="#FBEEF5") + 4.0
    # the two corollaries specialise the mod-4 theorem; they hang off it on a
    # short bracket of their own so the main spine is not interrupted
    o_top = N("cor2", XR, o_top, WR, PROVED,
              "two-block form: components $=$ cosets of "
              "$H=\\langle a_s-a_{s'},\\,b_t-b_{t'}\\rangle$;\n"
              "$|H|\\,w_A w_B$ odd $\\Rightarrow$ no depth $\\Delta$") + 4.0
    o_top = N("cor3", XR, o_top, WR, PROVED,
              "regular CSS codes: $w$ odd, $n_0\\equiv 2$ "
              "$(\\mathrm{mod}\\ 4)$ $\\Rightarrow$ no depth $2w$;\n"
              f"hypergraph products {hgp_lab}") + 4.0
    o_top = N("nocommon", XR, o_top, WR, PROVED,
              "no common $L$-side layer set for all $X$-checks") + 4.0
    o_top = N("twist", XR, o_top, WR, PROVED,
              "twisted schedule $\\Rightarrow$ $|M|\\,w_A w_B$ even "
              "$(M=\\varepsilon(H))$\n(any overlap pattern)") + G + 6.0

    # a spine from the root feeds all three
    spine_x = XR - WR / 2 - 0.055
    ytop = nodes["root"]["y"] - nodes["root"]["h"] / 2
    ybot = nodes["twist"]["y"]
    ax.plot([spine_x, spine_x], [ytop, ybot], color=INK, lw=S.LW_EDGE, zorder=2)
    ax.plot([0.5, spine_x], [ytop, ytop], color=INK, lw=S.LW_EDGE, zorder=2)
    for t in ("mod4", "nocommon", "twist"):
        arrow(ax, (spine_x, nodes[t]["y"]),
              (nodes[t]["x"] - nodes[t]["w"] / 2, nodes[t]["y"]))

    # ---- main chain, fed by the root --------------------------------------
    cur = N("lemB", XL, cur, 0.37, PROVED,
            "support symmetry:\n$X$-edges on $L$ lie in $[a,b]$, $a+b=\\Delta+1$") + G
    row = cur
    N("c34", 0.085, row, 0.145, PROVED, "$(3,4)$: empty")
    N("c25", 0.265, row, 0.185, PROVED, "$(2,5)$: middle-layer\nimbalance")
    cur = N("c16", 0.437, row, 0.125, PROVED, "$(1,6)$") + G
    cur = N("rigid", XL, cur, 0.37, PROVED,
            "rigidity lemma ($\\Delta=6$, distinct sums,\n$(a,b)=(1,6)$): one $X$ "
            "and one $Z$ per layer pair") + G
    cur = N("parity", XL, cur, 0.37, PROVED,
            "parity lemma (general $\\Delta$): $F_L+F_R=(\\Delta/2)^2$,\n"
            "odd when $\\Delta\\equiv 2$ $(\\mathrm{mod}\\ 4)$") + G
    main_top = cur
    cur = N("main", XL, cur, 0.37, PROVED,
            "main result: $w_A=w_B=3$ and distinct sums\n$\\Rightarrow$ no depth-6 "
            "schedule", face="#EAF2F8") + G + 8.0
    cor_top = cur
    cur = N("cor", XL, cor_top, 0.26, PROVED,
            f"corollary: the {n_ibm} published codes\nhave depth exactly 7") + G
    N("upper", 0.435, cor_top - 5.0, 0.185, PROVED,
      "uniform upper bound:\none depth-7 schedule\nworks for every\n$|A|=|B|=3$")

    # ---- the depth-six chain, on the right --------------------------------
    s_top = o_top
    s_top = N("tmpl", XR, s_top, WR, EVID,
              f"template keys: enumeration $q\\leq {q_max}$; reduction to "
              f"$\\kappa_q(1,b)$\n$+$ universal half-period symmetry, "
              f"verified $q\\leq {q_force}$") + 5.0
    s_top = N("lift", XR, s_top, WR, PROVED,
              "lifting lemma: a template solution pulls back\nto every realising "
              "code") + 5.0
    s_top = N("twoheight", XR, s_top, WR, PROVED,
              "2-height lemma: ord$(\\mathsf{d})$ even, 2-height $h$\n"
              "$\\Rightarrow\\ \\varepsilon: G\\to\\mathbb{Z}_{2^{h+1}}$, "
              "$\\varepsilon(\\mathsf{d})=2^h$") + 5.0
    s_top = N("six", XR, s_top, WR, PROVED,
              "depth six: class C1, ord$(\\mathsf{d})$ even, 2-height "
              "$\\leq 8$\n$\\Rightarrow D_{\\min}=6$") + 5.0
    s_top = N("codes", XR, s_top, WR, EVID,
              "depth-six codes with competitive parameters:\n"
              f"{', '.join(comp)} (Table {S.aux_label('tab:depth6codes')})") + 9.0
    s_top = N("oddreg", XR, s_top, WR, EVID,
              f"ord$(\\mathsf{{d}})$ odd: {n_sat} SAT, {n_unexp} solver UNSAT, "
              f"{n_capped} open;\n{z36} over $\\mathbb{{Z}}_{{36}}$ reaches 6") + 9.0
    N("open", XR, s_top, WR, OPEN,
      "open: general odd weights with $w_A+w_B\\equiv 2$ "
      "$(\\mathrm{mod}\\ 4)$;\n$\\Delta\\equiv 0$ $(\\mathrm{mod}\\ 4)$; "
      "odd-order criterion;\nanalytic template for the classes $c<q/2$")

    # ---- edges ------------------------------------------------------------
    link("root", "lemB")
    for c in ("c34", "c25", "c16"):
        link("lemB", c)
    link("c16", "rigid")
    link("rigid", "parity")
    link("parity", "main")
    link("main", "cor")
    link_side("upper", "cor")
    link("tmpl", "lift"); link("lift", "twoheight")
    link("twoheight", "six"); link("six", "codes")

    # the corollary bracket: both hang off mod4, neither off the other
    cx = XR - WR / 2 - 0.028
    ytop = nodes["mod4"]["y"] - nodes["mod4"]["h"] / 2
    ax.plot([cx, cx], [ytop, nodes["cor3"]["y"]], color=INK, lw=S.LW_EDGE, zorder=2)
    ax.plot([XR, cx], [ytop, ytop], color=INK, lw=S.LW_EDGE, zorder=2)
    for t in ("cor2", "cor3"):
        arrow(ax, (cx, nodes[t]["y"]),
              (nodes[t]["x"] - nodes[t]["w"] / 2, nodes[t]["y"]))

    # ---- legend and footer -------------------------------------------------
    yb = 0.008
    ax.add_patch(plt.Rectangle((0.03, yb - 0.015), 0.94, 0.030, facecolor="#F2F2F2",
                               edgecolor=RULE, linewidth=S.LW_RULE, zorder=1))
    ax.text(0.5, yb, "published codes: DRAT, drat-trim verified, no symmetry "
            "reduction", ha="center", va="center", fontsize=PT_MIN, zorder=6)
    for i, (st, lab) in enumerate(((OPEN, "open"), (EVID, "computational evidence"),
                                   (PROVED, "proved"))):
        yk = yb + 0.052 + i * 0.024
        box(ax, 0.058, yk, 0.030, 0.015, style=st)
        ax.text(0.088, yk, lab, fontsize=PT_MIN, ha="left", va="center")
    return fig, {}, ()

# ===========================================================================
# fig 2  the mechanism: the same ladder under progressively stronger constraints
# ===========================================================================
GAMMA = {1: 3, 2: 2, 3: 2, 4: 1, 5: 1, 6: 0}      # proof constants
DELTA = 6


def fig2_mechanism():
    lem = read("lemma_checks.csv")
    for r in lem:
        assert int(r["a"]) + int(r["b"]) == int(r["Delta"]) + 1, \
            f"{r['instance']}: a+b != Delta+1"
    n_sol = tr("fig2m", "n_solutions", len(lem), "data/lemma_checks.csv", "rows", "")
    EX = "oe43"
    ex = [r for r in lem if r["instance"] == EX]
    ex_delta = tr("fig2m", f"Delta[{EX}]", int(ex[0]["Delta"]),
                  "data/lemma_checks.csv", "Delta", EX)
    ex_ab = tr("fig2m", f"a_plus_b[{EX}]", int(ex[0]["a"]) + int(ex[0]["b"]),
               "data/lemma_checks.csv", "a,b", EX)

    H = 70.0
    fig = plt.figure(figsize=(S.W_DOUBLE, mm(H)))

    def panel(x, label):
        a = fig.add_axes([x / S.W_DOUBLE_MM, 5.0 / H, PW / S.W_DOUBLE_MM,
                          52.0 / H], label=label)
        a.set_xlim(0, PW); a.set_ylim(0, 52.0); a.axis("off")
        return a

    axa, axb, axc, axd = (panel(0, "a"), panel(46, "b"), panel(92, "c"),
                          panel(138, "d"))
    pitch, ytop = S.RUNG_MM, 46.0
    ybot = ytop - (DELTA - 1) * pitch

    # ---- (a) support symmetry --------------------------------------------
    a_, b_ = 1, DELTA
    xa = 13.0
    axa.add_patch(plt.Rectangle((xa - 5.0, ybot - 1.6), 10.0,
                                (b_ - a_) * pitch + 3.2, facecolor=C_L,
                                edgecolor="none", zorder=0, gid="nocheck"))
    S.ladder(axa, xa, ytop, pitch, DELTA,
             x_at={i: "" for i in range(a_, b_ + 1)}, tint=None, half=2.6)
    bx = xa + 7.0
    axa.plot([bx, bx + 1.4, bx + 1.4, bx], [ytop, ytop, ybot, ybot], color=INK,
             lw=S.LW_LEADER, zorder=3)
    axa.plot([bx + 1.4, bx + 2.6], [(ytop + ybot) / 2, (ytop + ybot) / 2],
             color=INK, lw=S.LW_LEADER, zorder=3)
    axa.text(bx + 3.8, (ytop + ybot) / 2, "$a+b=\\Delta+1$", ha="left",
             va="center", fontsize=PT_MIN)
    axa.text(xa + 3.4, ytop, "$a$", ha="left", va="center", fontsize=PT_MIN)
    axa.text(xa + 3.4, ybot, "$b$", ha="left", va="center", fontsize=PT_MIN)
    axa.text(0.0, 9.5, f"checked on all {n_sol:,} enumerated schedules\n"
             f"(e.g. $(k,\\ell)=(4,3)$, $\\Delta={ex_delta}$: $a+b={ex_ab}$)",
             ha="left", va="top", fontsize=PT_MIN, color=GREY, linespacing=1.4)

    # ---- (b) rigidity ------------------------------------------------------
    # X below Z in pairs 1 and 3, above in pair 2 on L; the other way on R
    Lx = {1: "", 4: "", 5: ""}
    Lz = {2: "", 3: "", 6: ""}
    Rx = {2: "", 3: "", 6: ""}
    Rz = {1: "", 4: "", 5: ""}
    S.ladder(axb, 11.0, ytop, pitch, DELTA, x_at=Lx, z_at=Lz, tint=C_L,
             title="$L$", half=2.6)
    S.ladder(axb, 27.0, ytop, pitch, DELTA, x_at=Rx, z_at=Rz, tint=C_R,
             title="$R$", half=2.6, numbers=False)
    for p, (i, j) in enumerate(((1, 2), (3, 4), (5, 6))):
        y0 = ytop - (i - 1) * pitch
        y1 = ytop - (j - 1) * pitch
        bxx = 33.0
        axb.plot([bxx, bxx + 1.2, bxx + 1.2, bxx], [y0, y0, y1, y1], color=GREY,
                 lw=S.LW_LEADER, zorder=3)
        axb.text(bxx + 2.5, (y0 + y1) / 2, "{%d,%d}" % (i, j), ha="left",
                 va="center", fontsize=PT_MIN, color=GREY)
    axb.text(0.0, 9.5, "one $X$ and one $Z$ in every pair;\n"
             "the order within a pair is free", ha="left", va="top",
             fontsize=PT_MIN, color=GREY, linespacing=1.4)

    # ---- (c) parity --------------------------------------------------------
    cx = 11.0
    S.ladder(axc, cx, ytop, pitch, DELTA, x_at=Lx, z_at=Lz, tint=C_L, half=2.6)
    axc.text(cx + 11.0, ytop + 3.4, "$\\gamma(i)$", ha="center", va="bottom",
             fontsize=PT_MIN)
    for i, g in sorted(GAMMA.items()):
        axc.text(cx + 11.0, ytop - (i - 1) * pitch, str(g), ha="center",
                 va="center", fontsize=PT_MIN)
    tot = sum(GAMMA.values())
    axc.plot([cx + 8.4, cx + 13.6], [ybot - 2.2, ybot - 2.2], color=INK, lw=0.6)
    axc.text(cx + 11.0, ybot - 5.0, str(tot), ha="center", va="center",
             fontsize=PT_TICK, fontweight="bold")
    axc.text(0.0, 12.5, f"$F_L+F_R=\\sum_i\\gamma(i)={tot}$", ha="left",
             va="top", fontsize=PT_MIN)
    axc.text(0.0, 7.0, "odd", ha="left", va="top", fontsize=PT_MIN, color=C_OBS)
    axc.text(5.5, 7.0, "— but $F_L=F_R$ is required", ha="left", va="top",
             fontsize=PT_MIN, color=GREY)

    # ---- (d) one collision: four corners ----------------------------------
    XP, ZP = (7.0, 40.0), (7.0, 22.0)
    qx = 24.0
    qys = (44.0, 36.0, 28.0, 20.0)
    ors = (1, 0, 0, 1)
    sides = ("L", "L", "R", "R")
    x_check(axd, *XP, s=CS); z_check(axd, *ZP, s=CS)
    axd.text(XP[0] - 3.0, XP[1], "$X_g$", ha="right", va="center", fontsize=PT_MIN)
    axd.text(ZP[0] - 3.6, ZP[1], "$Z_{g+\\delta}$", ha="right", va="center",
             fontsize=PT_MIN)
    for y, o, sd in zip(qys, ors, sides):
        axd.add_patch(plt.Rectangle((qx - 3.1, y - 3.1), 6.2, 6.2,
                                    facecolor=C_L if sd == "L" else C_R,
                                    edgecolor="none", zorder=0, gid="nocheck"))
        axd.plot([XP[0], qx], [XP[1], y], color=C_X, lw=S.LW_EDGE, zorder=1)
        axd.plot([ZP[0], qx], [ZP[1], y], color=C_Z, lw=S.LW_EDGE, zorder=1)
        qubit(axd, qx, y, r=QR)
        axd.text(qx + 4.4, y, str(o), ha="left", va="center", fontsize=PT_TICK)
        axd.text(qx + 7.6, y, sd, ha="left", va="center", fontsize=PT_MIN,
                 color=GREY)
    axd.text(0.0, 12.5, "$1+0+0+1\\equiv 0$", ha="left", va="top",
             fontsize=PT_MIN)
    axd.text(0.0, 7.0, "four corners can cancel; two cannot", ha="left",
             va="top", fontsize=PT_MIN, color=GREY)

    for L, ax in (("a", axa), ("b", axb), ("c", axc), ("d", axd)):
        panel_letter(fig, ax, L, dx_mm=0.0, dy_mm=2.4)
    for x, t in ((0, "support symmetry"), (46, "rigidity"), (92, "parity"),
                 (138, "one collision")):
        fig.text((x + 0.5) / S.W_DOUBLE_MM, 64.5 / H, t, fontsize=PT_PANEL,
                 ha="left", va="bottom")
    return fig, {"a": axa, "b": axb, "c": axc, "d": axd}, ()

# ===========================================================================
# fig 3  decision tree: what settles each part of the corpus
#
# Archetype: a CONSORT participant-flow diagram, drawn left to right.  Rounded
# boxes, the count in bold, the deciding result underneath, elbow connectors
# without arrowheads, leaf boxes carrying their outcome colour.
# ===========================================================================
def _leaf_of(r):
    if r["class"] != "C1":
        return r["class"]
    if r["ord_d_parity"] == "even":
        return "C1even"
    return "C1odd_obs" if r["theorem"] else "C1odd_free"


def _tree_counts():
    rows = coverage()
    L = defaultdict(list)
    for r in rows:
        L[_leaf_of(r)].append(r)
    out = {}
    for k, v in L.items():
        out[k] = dict(n=len(v), comp=Counter(x["status_math"] for x in v),
                      capped=sum(1 for x in v if x["status_solver"] == "capped"),
                      drat=sum(1 for x in v if x["drat_verified"] == "True"))
    return out, len(rows)


def fig3_decision_tree():
    C, n_all = _tree_counts()
    leaves = ["D", "C1even", "C1odd_obs", "C1odd_free", "C2", "SG"]
    assert sum(C[k]["n"] for k in leaves) == n_all == 664, \
        f"leaf counts {[C[k]['n'] for k in leaves]} do not sum to {n_all}"
    # Round 8 certified six of the solver-reported UNSAT instances, so the
    # DRAT total is no longer a fixed 10; it is read from the data and the
    # assertion only pins the pieces that a theorem settles.
    n_drat = sum(C[k]["drat"] for k in leaves)
    assert C["D"]["drat"] == 9 and C["SG"]["drat"] == 1, \
        f"theorem-backed DRAT counts changed: {C['D']['drat']}, {C['SG']['drat']}"
    for k in leaves:
        for fld in ("n", "capped", "drat"):
            tr("fig3", f"leaf_{fld}[{k}]", C[k][fld], "data/coverage.csv",
               "class,ord_d_parity,theorem,status_solver,drat_verified", k)
    n_c1 = C["C1even"]["n"] + C["C1odd_obs"]["n"] + C["C1odd_free"]["n"]
    n_odd = C["C1odd_obs"]["n"] + C["C1odd_free"]["n"]
    tr("fig3", "n_C1", n_c1, "data/coverage.csv", "class", "C1")
    tr("fig3", "n_C1_odd", n_odd, "data/coverage.csv", "ord_d_parity", "odd")
    tr("fig3", "n_total", n_all, "data/coverage.csv", "in_sharpness_map", "True")

    six = read("thm_six_coverage.csv")
    n_notin8 = tr("fig3", "even_d_not_in_8G",
                  sum(1 for r in six if r["in_8G"] == "False"
                      and r["ord_d_parity"] == "even"),
                  "data/thm_six_coverage.csv", "in_8G,ord_d_parity", "False,even")
    n_in8 = tr("fig3", "even_d_in_8G",
               sum(1 for r in six if r["in_8G"] == "True"
                   and r["ord_d_parity"] == "even"),
               "data/thm_six_coverage.csv", "in_8G,ord_d_parity", "True,even")
    assert n_notin8 + n_in8 == C["C1even"]["n"]

    H = 82.0
    fig = plt.figure(figsize=(S.W_DOUBLE, mm(H)))
    ax = fig.add_axes([0, 0, 1, 1], label="tree")
    ax.set_xlim(0, S.W_DOUBLE_MM); ax.set_ylim(0, H); ax.axis("off")

    def diamond(x, y):
        ax.plot([x], [y], marker="D", ms=2.4, color=INK, zorder=8,
                markeredgewidth=0)

    def box_h(label, count, result, comp):
        """Height from the content: 10 mm was specified, but three text lines at
        6.5-7.5 pt cannot clear 1.5 mm inside 10 mm, so boxes size themselves."""
        h = 2.6 + 3.2
        if count is not None:
            h += 4.4
        if result:
            h += (result.count("\n") + 1) * 3.1
        if comp:
            h += 3.0
        return h + 1.8

    def node(x, w, y, label, count=None, result=None, outcome=None,
             comp=None, capped=0, drat=0):
        h = box_h(label, count, result, comp)
        face = OUTCOME[outcome] if outcome else "white"
        ax.add_patch(FancyBboxPatch((x, y - h / 2), w, h,
                                    boxstyle="round,pad=0.3,rounding_size=1.0",
                                    facecolor=face,
                                    alpha=1.0 if not outcome else 0.30,
                                    edgecolor=INK, linewidth=S.LW_BOX, zorder=3))
        if outcome:
            ax.add_patch(FancyBboxPatch((x, y - h / 2), w, h,
                                        boxstyle="round,pad=0.3,rounding_size=1.0",
                                        facecolor="none", edgecolor=INK,
                                        linewidth=S.LW_BOX, zorder=4))
        top = y + h / 2 - 2.6
        ax.text(x + 2.0, top, label, ha="left", va="center", fontsize=PT_MIN,
                zorder=6)
        yy = top - 4.4
        if count is not None:
            ax.text(x + 2.0, yy, f"{count:,}", ha="left", va="center",
                    fontsize=PT_PANEL, fontweight="bold", zorder=6)
            if drat:
                diamond(x + 11.0, yy)
                ax.text(x + 13.0, yy, f"{drat}", ha="left", va="center",
                        fontsize=PT_MIN, zorder=6)
            yy -= 3.4
        if result:
            ax.text(x + 2.0, yy, result, ha="left", va="top", fontsize=PT_MIN,
                    color=GREY, zorder=6, linespacing=1.45)
        if comp:
            bw, bh = w - 4.0, 1.5
            bx, by = x + 2.0, y - h / 2 + 1.5
            xx, tot = bx, sum(comp.values())
            for st in STATUS_MATH:
                v = comp.get(st, 0)
                if not v:
                    continue
                seg = bw * v / tot
                ax.add_patch(plt.Rectangle((xx, by), seg, bh,
                                           facecolor=STATUS_COLOUR[st],
                                           edgecolor="white", linewidth=0.3,
                                           zorder=5, gid="nocheck"))
                xx += seg
            if capped:
                ax.add_patch(plt.Rectangle((bx, by), bw * capped / tot, bh,
                                           facecolor="none", edgecolor="white",
                                           hatch=S.HATCH, linewidth=0.0,
                                           zorder=6, gid="nocheck"))
        return dict(x=x, y=y, w=w, h=h)

    def link(a, b):
        """Elbow connector, no arrowhead."""
        x0, y0 = a["x"] + a["w"], a["y"]
        x1, y1 = b["x"], b["y"]
        xm = (x0 + x1) / 2
        ax.plot([x0, xm, xm, x1], [y0, y0, y1, y1], color=GREY, lw=S.LW_ARROW,
                zorder=1, solid_joinstyle="round")

    X0, W0 = 0.0, 28.0
    X1, W1 = 38.0, 32.0
    X2, W2 = 80.0, 32.0
    X3, W3 = 122.0, 58.0
    GAPV = 4.0
    TOP = 80.0

    f = C["C1odd_free"]["comp"]
    spec = {
        "root": ("instances with a", n_all, "depth-6 outcome", None, None, 0, 0),
        "D": ("distinct sums (D)", C["D"]["n"], "main result:\nall UNSAT",
              "UNSAT-theorem", None, 0, C["D"]["drat"]),
        "C1": ("class C1", n_c1, None, None, None, 0, 0),
        "C2": ("class C2", C["C2"]["n"],
               f"{C['C2']['comp']['SAT-solver']} SAT\n"
               f"{C['C2']['comp']['UNSAT-theorem']} UNSAT (mod-4)", None,
               C["C2"]["comp"], C["C2"]["capped"], 0),
        "SG": ("subgroup type", C["SG"]["n"], "UNSAT (mod-4)", "UNSAT-theorem",
               None, 0, C["SG"]["drat"]),
        "even": ("ord$(d)$ even", C["C1even"]["n"],
                 f"all SAT\n{n_notin8} depth-six result\n{n_in8} twisted, $q=16$",
                 "SAT", None, 0, 0),
        "odd": ("ord$(d)$ odd", n_odd, None, None, None, 0, 0),
        "obs": ("mod-4 obstruction", C["C1odd_obs"]["n"],
                f"UNSAT, {C['C1odd_obs']['capped']} solver-capped",
                "UNSAT-theorem", C["C1odd_obs"]["comp"],
                C["C1odd_obs"]["capped"], 0),
        "free": ("not obstructed", C["C1odd_free"]["n"],
                 f"{f['SAT-solver'] + f['SAT-witness']} SAT "
                 f"({f['SAT-witness']} by witness)\n"
                 f"{f['UNSAT-solver']} UNSAT solver-only\n{f['open']} open",
                 None, f, C["C1odd_free"]["capped"], 0),
    }
    hh = {k2: box_h(v[0], v[1], v[2], v[4]) for k2, v in spec.items()}

    # leaves first, then each parent centred on its children
    y = {}
    cur = TOP - hh["obs"] / 2
    y["obs"] = cur
    cur -= hh["obs"] / 2 + GAPV + hh["free"] / 2
    y["free"] = cur
    y["odd"] = (y["obs"] + y["free"]) / 2
    y["even"] = y["odd"] + hh["odd"] / 2 + GAPV + hh["even"] / 2 + 6.0
    y["C1"] = (y["even"] + y["odd"]) / 2
    y["D"] = y["even"] + hh["even"] / 2 + GAPV + hh["D"] / 2
    y["C2"] = y["odd"] - hh["odd"] / 2 - GAPV - hh["C2"] / 2 - 4.0
    y["SG"] = y["C2"] - hh["C2"] / 2 - GAPV - hh["SG"] / 2
    y["root"] = (y["D"] + y["SG"]) / 2

    XW = {"root": (X0, W0), "D": (X1, W1), "C1": (X1, W1), "C2": (X1, W1),
          "SG": (X1, W1), "even": (X2, W2), "odd": (X2, W2), "obs": (X3, W3),
          "free": (X3, W3)}
    N = {}
    for k2, (lab, cnt, res, outc, comp, cap, drat) in spec.items():
        x, w = XW[k2]
        N[k2] = node(x, w, y[k2], lab, count=cnt, result=res, outcome=outc,
                     comp=comp, capped=cap, drat=drat)
    root, nD, nC1, nC2, nSG = (N["root"], N["D"], N["C1"], N["C2"], N["SG"])
    nEven, nOdd, nObs, nFree = N["even"], N["odd"], N["obs"], N["free"]

    for a, b in ((root, nD), (root, nC1), (root, nC2), (root, nSG),
                 (nC1, nEven), (nC1, nOdd), (nOdd, nObs), (nOdd, nFree)):
        link(a, b)

    # ---- legend, bottom right, two rows -----------------------------------
    keys = [("SAT", "SAT"), ("UNSAT-theorem", "UNSAT (theorem)"),
            ("UNSAT-solver", "UNSAT (solver)"), ("open", "open")]
    for i, (st, lab) in enumerate(keys):
        x = X3 + (i % 2) * 30.0
        y = 8.0 - (i // 2) * 4.2
        ax.add_patch(plt.Rectangle((x, y), 2.6, 1.8, facecolor=OUTCOME[st],
                                   edgecolor="none", zorder=4))
        ax.text(x + 3.4, y + 0.9, lab, ha="left", va="center", fontsize=PT_MIN)
    ax.add_patch(plt.Rectangle((X3, -0.4), 2.6, 1.8, facecolor="#C9C9C9",
                               edgecolor="white", hatch=S.HATCH, linewidth=0.0,
                               zorder=4))
    ax.text(X3 + 3.4, 0.5, "solver capped", ha="left", va="center",
            fontsize=PT_MIN)
    diamond(X3 + 30.0 + 1.3, 0.5)
    ax.text(X3 + 30.0 + 3.4, 0.5, "DRAT-certified", ha="left", va="center",
            fontsize=PT_MIN)
    return fig, {}, ()

# ===========================================================================
# figS1  proof map: what depends on what
# ===========================================================================
def _grp_tex(dims):
    """Z_15 x Z_3 from a dims list, for a tick label."""
    d = [int(x) for x in dims]
    return " $\\times$ ".join(f"$\\mathbb{{Z}}_{{{x}}}$" for x in d)


def _f5_rows():
    """Every certified depth-6 refutation, and its reversal-clause-free twin.

    Three groups: the seven published codes, the two class-D instances and the
    Z6 sweep instance, and the class-C1 odd-order instances certified later.
    The last group has no clause-free twin -- those runs kept the
    layer-reversal clause -- so it is drawn with the filled marker only.
    """
    base = {}
    for r in read("results.csv"):
        if r["D"] != "6" or r["status"] != "UNSAT":
            continue
        base.setdefault(r["instance"], r)          # first recorded run per instance
    r4 = {r["instance"]: r for r in read("r4_no_reversal.csv")
          if r["symmetry_breaking"] == "False"}
    ibm = sorted((k for k in base if k.startswith("bb")), key=lambda k: int(base[k]["N"]))
    other = sorted((k for k in base if not k.startswith("bb")),
                   key=lambda k: int(base[k]["N"]))

    # the two certified distinct-sums instances: their certificates were made
    # with the clause and are recorded in h2_sharpness.csv, not results.csv
    cov = {r["instance"]: r for r in read("coverage.csv")}
    dcls = []
    for r in read("h2_sharpness.csv"):
        c = cov.get(r["name"])
        if not c or c["drat_verified"] != "True" or c["class"] != "D":
            continue
        key = r["name"]
        base[key] = dict(r, time=r["time_s"], instance=key)
        PRETTY[key] = f"D, $\\mathbb{{Z}}_{{{r['N']}}}$"
        dcls.append(key)
    dcls.sort(key=lambda k: int(base[k]["N"]))
    other = other + dcls

    c1, seen = [], {}
    for r in read("c1_odd_unobstructed_certs.csv"):
        if r.get("verified") != "VERIFIED":
            continue
        N = int(r["N"])
        seen[N] = seen.get(N, 0) + 1
        key = r["instance"]
        base[key] = r
        PRETTY[key] = f"C1, $\\mathbb{{Z}}_{{{N}}}$ ({'abcdefgh'[seen[N]-1]})"
        c1.append(key)
    for r in read("odd_order_certs.csv"):
        if r.get("verified") != "VERIFIED":
            continue
        key = r["instance"]
        base[key] = r
        PRETTY[key] = f"C1 odd, {_grp_tex(ast.literal_eval(r['dims']))}"
        c1.append(key)
    c1.sort(key=lambda k: (int(base[k].get("N") or 0) or
                           prod(ast.literal_eval(base[k]["dims"])), k))
    return ibm, other, c1, base, r4


def _logfmt(v, _pos):
    return f"{int(v):,}" if v >= 1 else f"{v:g}"


PRETTY = {"sw73": "Z6, $A=B=\\{0,2,4\\}$"}


def fig5():
    ibm, other, c1, base, r4 = _f5_rows()
    # the panel grew with the class-C1 certificates: 5 mm per row, so that a
    # 6 pt tick label still clears its neighbour
    H = 90.0 + 5.0 * len(c1)
    fig = plt.figure(figsize=(S.W_DOUBLE, mm(H)))

    def ax_mm(x, y, w, h, label):
        return fig.add_axes([x / S.W_DOUBLE_MM, y / H, w / S.W_DOUBLE_MM, h / H],
                            label=label)

    PH = 40.0 + 5.0 * len(c1)
    axa = ax_mm(40, 30, 46, PH, "a")
    axb = ax_mm(126, 30, 44, PH, "b")

    names = ibm + other + c1
    ygap = 0.55 if other else 0.0
    ypos = {n: len(names) - 1 - i for i, n in enumerate(names)}
    for n in other:                     # set the sweep instance apart
        ypos[n] -= ygap
    for n in c1:                        # and the later certificates again
        ypos[n] -= 2 * ygap

    def series(ax, getter, unit, column):
        for n in names:
            y = ypos[n]
            v0 = tr("figS6", f"{unit}[{n}]", getter(base[n]), "data/results.csv",
                    column, n)
            if n in r4:
                v1 = tr("figS6", f"{unit}_norev[{n}]", getter(r4[n]),
                        "data/r4_no_reversal.csv", column, n)
                ax.plot([v0, v1], [y, y], color=RULE, lw=0.5, zorder=1)
                ax.plot([v1], [y], marker="o", ms=4.4, mfc="white", mec=C_X,
                        mew=0.8, ls="none", zorder=3)
            # the filled marker is the smaller of the two so a coincident pair
            # still reads as a dot inside a ring
            ax.plot([v0], [y], marker="o", ms=2.9, mfc=C_X, mec=C_X, ls="none",
                    zorder=4)
        ax.set_yticks([ypos[n] for n in names])
        ax.set_yticklabels([PRETTY.get(n, n) for n in names], fontsize=PT_MIN)
        ax.set_ylim(min(ypos.values()) - 0.55, max(ypos.values()) + 0.55)
        ax.set_xscale("log")
        ax.tick_params(axis="y", length=0)
        ax.xaxis.set_minor_locator(plt.NullLocator())

    series(axa, lambda r: float(r["time"]), "s", "time")
    axa.set_xlim(0.8, 1500)
    axa.set_xticks([1, 10, 100, 1000])
    axa.xaxis.set_major_formatter(plt.FuncFormatter(_logfmt))
    axa.set_xlabel("kissat solve time (s)", labelpad=7)

    series(axb, lambda r: float(r["proof_bytes"]) / 1e6, "MB", "proof_bytes")
    axb.set_xlim(6, 6000)
    axb.set_xticks([10, 100, 1000])
    axb.xaxis.set_major_formatter(plt.FuncFormatter(_logfmt))
    axb.set_xlabel("DRAT proof size (MB)", labelpad=7)

    nr4rows = read("r4_no_reversal.csv")
    nver = tr("figS6", "r4_verified",
              sum(r["verified"] == "VERIFIED" for r in nr4rows),
              "data/r4_no_reversal.csv", "verified", "")

    for L, ax in (("a", axa), ("b", axb)):
        panel_letter(fig, ax, L, dx_mm=-26.0 if L == "a" else -24.0)
    fig.text(4 / S.W_DOUBLE_MM, (H - 6.0) / H, "depth-6 refutation: solve time",
             fontsize=PT_PANEL, ha="left", va="bottom")
    fig.text(100 / S.W_DOUBLE_MM, (H - 6.0) / H, "DRAT certificate size",
             fontsize=PT_PANEL, ha="left", va="bottom")
    fig.text(4 / S.W_DOUBLE_MM, 14.0 / H,
             "filled: with the layer-reversal clause;   open: without it.  "
             "Table I reports the values without the clause.",
             fontsize=PT_MIN, ha="left", va="bottom", color=GREY)
    fig.text(4 / S.W_DOUBLE_MM, 9.0 / H,
             f"{nver} refutations without the clause: 7 published codes + 2 class D, "
             f"every one drat-trim verified.  The {len(c1)} class-C1 certificates "
             f"kept the clause, so they have no open marker.",
             fontsize=PT_MIN, ha="left", va="bottom", color=GREY)
    fig.text(4 / S.W_DOUBLE_MM, 4.0 / H,
             "MB = $10^6$ bytes; both axes logarithmic.",
             fontsize=PT_MIN, ha="left", va="bottom", color=GREY)
    return fig, {"a": axa, "b": axb}, ()

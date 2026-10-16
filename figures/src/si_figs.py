"""Supplementary figures for the revised npj QI submission.

Same design system as the main figures (figstyle.py); same contract: every builder
returns (fig, letters, shared_pairs) and every number is read from a data file listed in
the manifest.  Single column (88 mm).
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter, defaultdict
from math import gcd

import matplotlib.pyplot as plt
import numpy as np

import figstyle as S
from figstyle import (C_OBS, C_X, C_Z, GREY, INK, PT_MIN, PT_PANEL, PT_TICK,
                      STATUS_ORDER, STATUS_SHADE, mm, panel_letter)

ROOT = S.ROOT
DATA = S.DATA
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


def coverage(sharpness_map_only: bool = True):
    """data/coverage.csv -- the one table of record for depth-6 status."""
    rows = read("coverage.csv")
    return [r for r in rows if not sharpness_map_only
            or r["in_sharpness_map"] == "True"]


def _fig_mm(w_mm, h_mm):
    return plt.figure(figsize=(mm(w_mm), mm(h_mm))), w_mm, h_mm


def _ax_mm(fig, W, H, x, y, w, h, label):
    return fig.add_axes([x / W, y / H, w / W, h / H], label=label)


def swatch_key(fig, W, H, x0, ys, items, per_row, sw=2.2, gap=6.0, off=3.4):
    """Small colour key: filled square then label, laid out left to right in rows.

    Used only where the coloured element itself is too thin to carry a direct label.
    """
    rows = [items[i:i + per_row] for i in range(0, len(items), per_row)]
    for row, y in zip(rows, ys):
        x = x0
        for col, lab in row:
            fig.add_artist(plt.Rectangle((x / W, (y - sw / 2) / H), sw / W, sw / H,
                                         transform=fig.transFigure, facecolor=col,
                                         edgecolor="none", zorder=3))
            t = fig.text((x + off) / W, y / H, lab, fontsize=PT_MIN, ha="left",
                         va="center")
            fig.canvas.draw()
            w = t.get_window_extent(renderer=fig.canvas.get_renderer()).width
            x += off + w / fig.dpi * 25.4 + gap


def head(fig, W, H, ax, letter, title, sub=None):
    """Bold panel letter at the left margin, title on the same baseline, grey
    sub-line 4 mm below it, all outside the axes.

    `letter=None` on a one-panel figure: a lone "a" labels nothing.
    """
    y1 = ax.get_position().y1 * H
    n_sub = (sub.count("\n") + 1) if sub else 0
    y_title = y1 + 2.0 + n_sub * 3.4 + 2.8          # clear a multi-line sub-line
    x_title = 3.0
    if letter:
        fig.text(3.0 / W, y_title / H, letter, fontsize=S.PT_LETTER,
                 fontweight="bold", ha="left", va="bottom", color=INK)
        x_title = 8.5
    fig.text(x_title / W, y_title / H, title, fontsize=PT_PANEL, ha="left",
             va="bottom")
    if sub:
        fig.text(3.0 / W, (y1 + 2.0) / H, sub, fontsize=PT_MIN, ha="left",
                 va="bottom", color=GREY, linespacing=1.45)


# ===========================================================================
# S1  sweep outcome by group and by maximum sum multiplicity
# ===========================================================================
def fig_sweep_by_group():
    rows = read("sweep.csv")
    Ns = {}
    for r in rows:
        Ns.setdefault(r["group"], int(r["N"]))
    cnt = defaultdict(Counter)
    for r in rows:
        cnt[(r["group"], r["max_multiplicity"])][r["status"]] += 1
    keys = sorted(cnt, key=lambda gm: (Ns[gm[0]], gm[0], gm[1]))

    fig, W, H = _fig_mm(88.0, 76.0)
    ax = _ax_mm(fig, W, H, 27, 19, 55, 44, "a")

    y = np.arange(len(keys))[::-1]
    labs = []
    for yy, (g, m) in zip(y, keys):
        sat = tr("S1", f"SAT[{g},<={m}]", cnt[(g, m)]["SAT"], "data/sweep.csv",
                 "status", f"{g},{m}")
        uns = tr("S1", f"UNSAT[{g},<={m}]", cnt[(g, m)]["UNSAT"], "data/sweep.csv",
                 "status", f"{g},{m}")
        ax.barh(yy, sat, height=0.62, color=C_X, edgecolor="none", zorder=2)
        if uns:
            ax.barh(yy, uns, left=sat, height=0.62, color=C_OBS, edgecolor="none",
                    zorder=3)
        ax.text(sat + uns + 12, yy, f"{sat + uns:,}", ha="left", va="center",
                fontsize=PT_TICK)
        labs.append(f"{g.replace('x', chr(0x00D7))}   $\\leq${m}")
    ax.set_yticks(y); ax.set_yticklabels(labs, fontsize=PT_TICK)
    ax.set_ylim(-0.65, len(keys) - 0.35)
    ax.set_xlim(0, 470); ax.set_xticks([0, 100, 200, 300, 400])
    ax.set_xlabel("instances decided at depth $\\Delta=6$", labelpad=7)
    ax.tick_params(axis="y", length=0)

    # the UNSAT segment is one instance in 470 and so cannot be seen; it is named
    # in place, on its own row, in the colour of the segment
    total_unsat = sum(cnt[k]["UNSAT"] for k in keys)
    for i, k in enumerate(keys):
        if cnt[k]["UNSAT"]:
            ax.text(120, y[i], f"{cnt[k]['UNSAT']} UNSAT", ha="left", va="center",
                    fontsize=PT_MIN, color=C_OBS)
    nsat = sum(cnt[k]["SAT"] for k in keys)
    tr("S1", "total_SAT", nsat, "data/sweep.csv", "status", "all")
    tr("S1", "total_UNSAT", total_unsat, "data/sweep.csv", "status", "all")

    head(fig, W, H, ax, None,
         f"depth-6 sweep: {nsat + total_unsat:,} instances, {nsat:,} SAT and "
         f"{total_unsat} UNSAT")
    fig.text(3.0 / W, 3.0 / H,
             "every sweep group has $|G|\\leq8<9=kl$, so none has distinct sums",
             fontsize=PT_MIN, ha="left", va="bottom", color=GREY)
    return fig, {}, ()


# ===========================================================================
# S2  exhaustive eps-template outcome by modulus
# ===========================================================================
TEMPLATE_QS = [2, 3, 4, 5, 6, 8]
NOT_COMPUTED = "$q$ = 7, 9\u201312, 16 not computed"
CATS = ["$|M|$ odd",
        "$|M|$ even, $\\bar{\\mathsf{d}}=0$",
        "$|M|$ even, $\\bar{\\mathsf{d}}\\neq0$,\nord$(\\bar{\\mathsf{d}})$ even",
        "$|M|$ even, $\\bar{\\mathsf{d}}\\neq0$,\nord$(\\bar{\\mathsf{d}})$ odd"]


def _template_split(m: int):
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    from twoblock.templates import (M_order, enumerate_vectors, eps_d, key, load,
                                    patterns)
    rec = load(m)
    if rec is None:
        return None
    sat = rec["sat_set"]
    out = {c: [0, 0] for c in CATS}                 # [admits, does not]
    out["_in8"] = [0, 0]                            # eps(d) in 8 Z_m: [admits, all]
    for pat in patterns():
        for ea, eb in enumerate_vectors(pat, m):
            hit = key(pat, ea, eb) in sat
            e = eps_d(pat, ea, eb, m) % m
            if M_order(ea, eb, m) % 2 == 1:
                c = CATS[0]
            elif e == 0:
                c = CATS[1]
            else:
                c = CATS[2] if (m // gcd(m, e)) % 2 == 0 else CATS[3]
            out[c][0 if hit else 1] += 1
            # 8 Z_m = <gcd(8, m)>, so eps(d) lies in it iff gcd(8, m) divides it
            if e % gcd(8, m) == 0:
                out["_in8"][1] += 1
                if hit:
                    out["_in8"][0] += 1
    return out


def fig_templates_by_q():
    split = {m: _template_split(m) for m in TEMPLATE_QS}
    fig, W, H = _fig_mm(88.0, 88.0)
    ax = _ax_mm(fig, W, H, 38, 16, 44, 51, "a")

    ncol, nrow = len(TEMPLATE_QS), len(CATS)
    for j, m in enumerate(TEMPLATE_QS):
        tot_m = sum(sum(v) for v in split[m].values() if v is not split[m]["_in8"])
        tr("S2", f"n_keys[m={m}]", tot_m, f"templates/C1_m{m}.json", "n_keys", m)
        ax.text(j, -1.05, f"{tot_m:,}", ha="center", va="center", fontsize=PT_MIN,
                color=GREY)
        in8_adm, in8_all = split[m]["_in8"]
        tr("S2", f"eps_d_in_8Zm[m={m}]", in8_all, f"templates/C1_m{m}.json",
           "d-bar mod gcd(8,q)", m)
        ax.text(j, -1.85, f"{in8_all:,}", ha="center", va="center", fontsize=PT_MIN,
                color=C_X)
        for i, c in enumerate(CATS):
            adm, no = split[m][c]
            tr("S2", f"admit[m={m},{c}]", adm, f"templates/C1_m{m}.json", "sat_keys", c)
            tr("S2", f"total[m={m},{c}]", adm + no, f"templates/C1_m{m}.json",
               "n_keys", c)
            yy = nrow - 1 - i
            if adm + no == 0:
                ax.text(j, yy, "n/a", ha="center", va="center", fontsize=PT_MIN,
                        color="#C4C4C4", zorder=4)
                continue
            f = adm / (adm + no)
            ax.add_patch(plt.Rectangle((j - 0.5, yy - 0.5), 1, 1, zorder=1,
                                       facecolor=C_X, alpha=0.10 + 0.85 * f,
                                       edgecolor="white", linewidth=0.8,
                                       gid="nocheck"))
            ax.text(j, yy, f"{100 * f:.0f}", ha="center", va="center",
                    fontsize=PT_TICK, zorder=4,
                    color="white" if f > 0.55 else INK)
    if any(split[m][CATS[0]][0] for m in TEMPLATE_QS):
        raise AssertionError("|M| odd admits a key at some m")

    ax.set_xlim(-0.5, ncol - 0.5); ax.set_ylim(-2.4, nrow - 0.5)
    ax.set_xticks(range(ncol))
    ax.set_xticklabels([str(m) for m in TEMPLATE_QS], fontsize=PT_TICK)
    ax.set_yticks(list(range(nrow)) + [-1.05, -1.85])
    ax.set_yticklabels(CATS[::-1] + ["$\\varepsilon$-vectors in total",
                                     "of those, $\\bar{\\mathsf{d}}\\in 8\\mathbb{Z}_q$"],
                       fontsize=PT_MIN, linespacing=1.35)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.xaxis.set_ticks_position("bottom")
    ax.set_xlabel("twist modulus $q$", labelpad=5)

    head(fig, W, H, ax, None,
         "per cent of $\\varepsilon$-vectors admitting a depth-6 twisted schedule",
         "exhaustive over every $\\varepsilon$-vector at that $m$;   " + NOT_COMPUTED)
    fig.text(3.0 / W, 3.0 / H,
             "the $|M|$ odd row is 0 at every $q$: twisted-schedule parity",
             fontsize=PT_MIN, ha="left", va="bottom", color=GREY)
    return fig, {}, ()


# ===========================================================================
# S3  smallest proper divisor carrying a verified twisted schedule
# ===========================================================================
def fig_periods():
    sat = {r["instance"] for r in coverage()
           if r["status_math"] in ("SAT-solver", "SAT-witness")}
    rows = [r for r in read("mstar.csv") if r["instance"] in sat]
    found = [r for r in rows if r["m_star_kind"] == "found"]
    ms = sorted({int(r["m_star"]) for r in found})
    kinds = [k for k in ("none found (capped)", "none found (uncapped)")
             if any(r["m_star_kind"] == k for r in rows)]
    # The old label read "within cap" for the *uncapped* kind, which was
    # backwards.  For every instance in this category data/mstar.csv records
    # unknown_ms = [] -- no capped twisted call -- and tested_ms equal to the
    # proper divisors of N, so the search was complete, not truncated.
    cats = [f"$q^*={m}$" for m in ms] + \
           [r"no period; none twisted at any $q \mid N$" if "uncapped" in k
            else "no period; twisted search capped" for k in kinds]

    even, odd = [], []
    for m in ms:
        even.append(tr("S3", f"q*={m},ord even",
                       sum(1 for r in found if int(r["m_star"]) == m
                           and r["ord_d_even"] == "True"),
                       "data/mstar.csv", "m_star,ord_d_even", f"{m},even"))
        odd.append(tr("S3", f"q*={m},ord odd",
                      sum(1 for r in found if int(r["m_star"]) == m
                          and r["ord_d_even"] == "False"),
                      "data/mstar.csv", "m_star,ord_d_even", f"{m},odd"))
    for k in kinds:
        even.append(tr("S3", f"{k},ord even",
                       sum(1 for r in rows if r["m_star_kind"] == k
                           and r["ord_d_even"] == "True"),
                       "data/mstar.csv", "m_star_kind,ord_d_even", f"{k},even"))
        odd.append(tr("S3", f"{k},ord odd",
                      sum(1 for r in rows if r["m_star_kind"] == k
                          and r["ord_d_even"] == "False"),
                      "data/mstar.csv", "m_star_kind,ord_d_even", f"{k},odd"))

    fig, W, H = _fig_mm(88.0, 80.0)
    ax = _ax_mm(fig, W, H, 40, 23, 42, 44, "a")
    y = np.arange(len(cats))[::-1]
    x0 = 0.7
    for yy, e, o in zip(y, even, odd):
        tot = e + o
        if e:
            ax.barh(yy, e - x0, left=x0, height=0.55, color=C_X, edgecolor="none",
                    zorder=2)
        if o:
            ax.barh(yy, o - x0, left=x0, height=0.55, color=C_Z, edgecolor="none",
                    zorder=2)
        ax.text(tot * 1.25, yy, str(tot), ha="left", va="center", fontsize=PT_MIN)
    ax.set_yticks(y); ax.set_yticklabels(cats, fontsize=PT_MIN)
    ax.set_ylim(-0.62, len(cats) + 0.55)
    ax.set_xscale("log"); ax.set_xlim(x0, 900)
    ax.set_xticks([1, 10, 100])
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: f"{int(v):,}"))
    ax.set_xlabel("class-C1 instances satisfiable at depth 6", labelpad=7)
    ax.tick_params(axis="y", length=0)
    # the two series are named once, in the free space at the top right
    # the two series are named once, in the free space at the top right
    ax.text(1.1, y[0] + 0.95, "ord$(\\mathsf{d})$ even", color=C_X, fontsize=PT_MIN,
            ha="left", va="center")
    ax.text(28, y[0] + 0.95, "ord$(\\mathsf{d})$ odd", color=C_Z, fontsize=PT_MIN,
            ha="left", va="center")

    n = tr("S3", "n_SAT_rows", len(rows), "data/mstar.csv", "status_resolved", "SAT")
    head(fig, W, H, ax, None,
         "smallest proper divisor $q^*$ with a verified twisted schedule",
         f"{n} class-C1 instances that are satisfiable at depth 6")
    fig.text(3.0 / W, 3.0 / H,
             "every $q^*$ found is even;   log scale, count on every bar",
             fontsize=PT_MIN, ha="left",
             va="bottom", color=GREY, linespacing=1.4)
    return fig, {}, ()


# ===========================================================================
# S4  componentwise mod-4 obstruction profile
# ===========================================================================
from figstyle import STATUS_COLOUR, STATUS_DARK, STATUS_MATH      # noqa: E402


def fig_theorem1_profile():
    h1 = {r["instance"]: r for r in read("h1_predictions.csv")}
    cov = {r["instance"]: r for r in coverage() if r["class"] == "C1"}
    par = {r["instance"]: r["ord_d_even"]
           for r in read("c1_final_instances.csv")}
    rows = [(cov[n], h1[n]) for n in sorted(cov)
            if n in h1 and h1[n].get("min_component_n")]
    cell = Counter()
    comp = defaultdict(Counter)
    obst = {}
    for r, h in rows:
        k = (int(h["min_component_n"]) % 4, par.get(r["instance"]) == "True")
        cell[k] += 1
        comp[k][r["status_math"]] += 1
        obst[k] = obst.get(k, True) and bool(r["theorem"])
    for k in sorted(cell, key=str):
        tr("S4", f"cell[n%4={k[0]},ord_even={k[1]}]", cell[k],
           "data/h1_predictions.csv + data/c1_final_instances.csv",
           "min_component_n,ord_d_even", str(k))
    bad = {k: v for k, c in comp.items() if obst.get(k)
           for k2, v in c.items() if k2.startswith("SAT")}
    if bad:
        raise AssertionError(f"obstructed instances drawn as SAT: {bad}")

    fig, W, H = _fig_mm(88.0, 116.0)
    axa = _ax_mm(fig, W, H, 24, 84, 58, 16, "a")
    axb = _ax_mm(fig, W, H, 24, 30, 58, 22, "b")

    for j in range(4):
        for i, ev in enumerate((True, False)):
            v = cell[(j, ev)]
            yy = 1 - i
            if v:
                axa.add_patch(plt.Rectangle((j - 0.5, yy - 0.5), 1, 1, zorder=1,
                                            facecolor=C_OBS if obst[(j, ev)] else C_X,
                                            alpha=0.9, edgecolor="white",
                                            linewidth=0.8, gid="nocheck"))
                axa.text(j, yy, f"{v:,}", ha="center", va="center", fontsize=PT_TICK,
                         color="white", zorder=4)
            else:
                axa.text(j, yy, "0", ha="center", va="center", fontsize=PT_MIN,
                         color="#C4C4C4", zorder=4)
    axa.set_xlim(-0.5, 3.5); axa.set_ylim(-0.5, 1.5)
    axa.set_xticks(range(4))
    axa.set_xticklabels(["0", "1", "2", "3"], fontsize=PT_TICK)
    axa.set_yticks([1, 0])
    axa.set_yticklabels(["ord$(d)$ even", "ord$(d)$ odd"], fontsize=PT_TICK)
    axa.tick_params(length=0)
    for sp in axa.spines.values():
        sp.set_visible(False)
    axa.xaxis.set_ticks_position("bottom")
    axa.set_xlabel("$\\sum_v r_v s_v \\;\\mathrm{mod}\\; 4$ per component",
                   labelpad=5)

    occ = [k for k in sorted(cell, key=lambda k: (-cell[k], str(k))) if cell[k]]
    y = np.arange(len(occ))[::-1]
    labs = []
    for yy, k in zip(y, occ):
        x = 0.0
        for st in STATUS_MATH:
            v = comp[k].get(st, 0)
            if not v:
                continue
            tr("S4", f"status[{k}|{st}]", v, "data/coverage.csv", "status_math",
               f"{k}|{st}")
            axb.barh(yy, v, left=x, height=0.52, color=STATUS_COLOUR[st],
                     edgecolor="white", linewidth=0.6, zorder=2)
            x += v
        axb.text(x + 7, yy, f"{cell[k]:,}", ha="left", va="center", fontsize=PT_TICK)
        labs.append(f"$n\\equiv{k[0]}$, ord$(d)$ " + ("even" if k[1] else "odd"))
    axb.set_yticks(y); axb.set_yticklabels(labs, fontsize=PT_MIN)
    axb.set_ylim(-0.7, len(occ) - 0.3)
    axb.set_xlim(0, 320); axb.set_xticks([0, 100, 200, 300])
    axb.set_xlabel("class-C1 instances", labelpad=7)
    axb.tick_params(axis="y", length=0)

    nobs = sum(cell[k] for k in cell if obst.get(k))
    cobs = Counter()
    for k in cell:
        if obst.get(k):
            cobs.update(comp[k])
    tr("S4", "obstructed_total", nobs, "data/coverage.csv", "theorem", "nonempty")
    for st, v in cobs.items():
        tr("S4", f"obstructed[{st}]", v, "data/coverage.csv", "status_math", st)

    head(fig, W, H, axa, "a", "where the componentwise mod-4 condition obstructs",
         "rose: obstructed;   blue: not obstructed")
    # the outcome ramp is ordered, so naming the order replaces a six-swatch key
    # The key is wrapped to the column: one line of five status names is about
    # 115 mm and the figure is 88 mm wide, so it used to run off the page.
    _k = STATUS_MATH[:-1]
    head(fig, W, H, axb, "b", "resolved status of the same instances",
         "segments left to right, darkest to lightest:\n"
         + ", ".join(_k[:3]) + ",\n"
         + ", ".join(_k[3:]) + f"; {STATUS_MATH[-1]} in rose")
    fig.text(3.0 / W, 3.0 / H,
             f"all {nobs} obstructed instances are UNSAT by the mod-4 result;\n"
             f"{sum(1 for r, _h in rows if bool(r['theorem']) and r['status_solver'] == 'capped')}"
             f" of them had a capped solver call, and none of the {nobs} is SAT",
             linespacing=1.45,
             fontsize=PT_MIN, ha="left", va="bottom", color=GREY)
    return fig, {"a": axa, "b": axb}, ()


# ===========================================================================
# S5  layer profiles and lemma pass rates

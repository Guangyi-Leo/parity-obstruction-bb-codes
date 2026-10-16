"""Scene data for Fig. 2: why six layers fail, and the one case where they do not.

Fig. 2 is an argument, not a measurement, so the quantities it shows are
*derived* here from real instances and written to data/fig2_scene.json.  There
is deliberately no recorded Delta = 6, D = 6 run for a distinct-sums code --
that is exactly what the paper proves impossible, and data/lemma_checks.csv
contains no such row.

Left three regions (the impossibility), from bb72 (Delta = 6, k = l = 3,
distinct sums):
  support   a + b = Delta + 1
  rigidity  Delta / 2 slab pairs, one X and one Z per pair on every guide line
  parity    the per-X-tile counts sum to F_L + F_R = k*l, which is odd for
            k = l = 3, while F_L = F_R is required -- the contradiction.

The lemma forms are corroborated on every proper schedule on record: each row
of data/lemma_checks.csv is checked for a + b == Delta + 1 and, where L7
applies, F_L + F_R == k*l.

Right region (the escape): a real four-qubit overlap.  h2_Z10_C1_0 has ten of
them, is SAT at depth six, and the four corner orientations of such an overlap
cancel -- which is why one repeated sum reopens depth 6.
"""
from __future__ import annotations

import csv
import json
import os

from .code import TwoBlockCode
from .simulate import orientation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SCHED = os.path.join(ROOT, "schedules")


def _lemma_corroboration():
    p = os.path.join(DATA, "lemma_checks.csv")
    rows = list(csv.DictReader(open(p)))
    n_ab, ok_ab, n_f, ok_f = 0, 0, 0, 0
    for r in rows:
        n_ab += 1
        ok_ab += int(int(r["a"]) + int(r["b"]) == int(r["Delta"]) + 1)
        if r["L7_applicable"] != "True":
            continue
        fl = json.loads(r["F_L_hist"])
        fr = json.loads(r["F_R_hist"])
        if len(fl) == 1 and len(fr) == 1:
            n_f += 1
            ok_f += int(int(next(iter(fl))) + int(next(iter(fr)))
                        == int(r["k"]) * int(r["l"]))
    return dict(rows=len(rows), a_plus_b_checked=n_ab, a_plus_b_ok=ok_ab,
                F_sum_checked=n_f, F_sum_ok=ok_f,
                source="data/lemma_checks.csv")


def _four_qubit_overlap(name="h2_Z10_C1_0"):
    """A real four-qubit overlap and its four corner orientations."""
    sched = os.path.join(SCHED, f"{name}_d6.json")
    if not os.path.exists(sched):
        return None
    with open(sched) as f:
        d = json.load(f)
    code = TwoBlockCode(d["dims"], [tuple(a) for a in d["A"]],
                        [tuple(b) for b in d["B"]], name)
    lay = {}
    for (kind, side, lab1, chk, qub), L in zip(d["edges"], d["layers"]):
        lay[code.edge_id(kind, side, chk, lab1 - 1)] = L
    lay = [lay[e] for e in range(code.n_edges)]
    quad = [op for op in code.overlap_pairs if len(op.corners) == 4]
    op = quad[0]
    els = code.G.elements
    os_ = []
    par = 0
    for cid in op.corners:
        c = code.corners[cid]
        o = orientation(code, lay, c)
        par ^= o
        os_.append(dict(side=c.side, qubit=list(els[c.qubit]), o=o,
                        x_layer=lay[c.ex], z_layer=lay[c.ez]))
    return dict(instance=name, N=code.N, D=d["D"],
                n_four_qubit_overlaps=len(quad),
                n_two_qubit_overlaps=sum(1 for o in code.overlap_pairs
                                         if len(o.corners) == 2),
                corners=os_, parity=par,
                sum_str=" + ".join(str(c["o"]) for c in os_),
                source=f"schedules/{name}_d6.json")


def _support(Delta):
    """The support band [a, b] to draw, and where the choice comes from.

    a + b = Delta + 1 fixes b once a is chosen.  Both patterns that occur on
    the recorded proper schedules are a = 1 (b = Delta) and a = 2
    (b = Delta - 1); the figure draws a = 2, because a = 1 tints the whole
    stack and so shows nothing.  Counts are read from data/lemma_checks.csv.
    """
    import collections
    rows = list(csv.DictReader(open(os.path.join(DATA, "lemma_checks.csv"))))
    seen = collections.Counter(int(r["a"]) for r in rows)
    a = 2
    return dict(Delta=Delta, a=a, b=Delta + 1 - a, a_plus_b=Delta + 1,
                text="a + b = \u0394 + 1 = %d" % (Delta + 1),
                a_counts={str(k): v for k, v in sorted(seen.items())},
                note="a = 2 drawn; a = 1 would tint the whole stack",
                source="data/lemma_checks.csv")


def build(out="fig2_scene.json"):
    with open(os.path.join(SCHED, "bb72_d7_inv.json")) as f:
        d = json.load(f)
    code = TwoBlockCode(d["dims"], [tuple(a) for a in d["A"]],
                        [tuple(b) for b in d["B"]], d["instance"])
    Delta, k, l = code.Delta, code.k, code.l
    scene = dict(
        reference=dict(instance=d["instance"], N=code.N, k=k, l=l, Delta=Delta,
                       distinct_sums=code.distinct_sums(),
                       source="schedules/bb72_d7_inv.json"),
        support=_support(Delta),
        rigidity=dict(n_pairs=Delta // 2,
                      pairs=[[2 * i + 1, 2 * i + 2] for i in range(Delta // 2)]),
        parity=dict(kl=k * l, odd=bool((k * l) % 2),
                    text=f"Σ γ(i) = kℓ = {k * l}"),
        corroboration=_lemma_corroboration(),
        collision=_four_qubit_overlap(),
    )
    p = os.path.join(DATA, out)
    with open(p, "w") as f:
        json.dump(scene, f, indent=1)
    return scene


if __name__ == "__main__":
    s = build()
    r = s["reference"]
    print(f"reference {r['instance']}: N={r['N']} k={r['k']} l={r['l']} "
          f"Delta={r['Delta']} distinct sums={r['distinct_sums']}")
    print(f"  support : {s['support']['text']}")
    print(f"  rigidity: {s['rigidity']['n_pairs']} slab pairs "
          f"{s['rigidity']['pairs']}")
    print(f"  parity  : {s['parity']['text']}  odd={s['parity']['odd']}")
    c = s["corroboration"]
    print(f"  corroboration on {c['rows']} recorded proper schedules: "
          f"a+b=Delta+1 on {c['a_plus_b_ok']}/{c['a_plus_b_checked']}, "
          f"F_L+F_R=kl on {c['F_sum_ok']}/{c['F_sum_checked']}")
    q = s["collision"]
    if q:
        print(f"  collision: {q['instance']} N={q['N']} D={q['D']}  "
              f"{q['n_four_qubit_overlaps']} four-qubit overlaps")
        print(f"    orientations {q['sum_str']} -> parity {q['parity']}")
        for c2 in q["corners"]:
            print(f"      {c2['side']} at {tuple(c2['qubit'])}: "
                  f"X@{c2['x_layer']} Z@{c2['z_layer']} o={c2['o']}")


# --------------------------------------------------------------------
# Round 7 redesign: the flow-diagram content
# --------------------------------------------------------------------
def _pills(Delta):
    """The (a, b) splits allowed by a + b = Delta + 1 with 1 <= a < b."""
    return [[a, Delta + 1 - a] for a in range(1, (Delta + 1) // 2 + 1)
            if a < Delta + 1 - a]


def _gamma(Delta):
    """gamma(i) for the rigidity layout: Z tiles above each X tile.

    The layout is forced once the pairs {1,2}, {3,4}, ... each carry one X and
    one Z on each of the two guide lines: put X on the lower slab of each pair
    on the L line and on the upper slab on the R line.  Counting Z tiles above
    each X tile then gives the profile, whose total must be k*l.
    """
    pairs = [(2 * i + 1, 2 * i + 2) for i in range(Delta // 2)]
    tiles = {}
    for lo, hi in pairs:
        tiles[(lo, 0)] = "X"
        tiles[(hi, 0)] = "Z"
        tiles[(lo, 1)] = "Z"
        tiles[(hi, 1)] = "X"
    out = []
    for (lay, gi), kind in sorted(tiles.items()):
        if kind != "X":
            continue
        out.append(sum(1 for (l2, g2), k2 in tiles.items()
                       if g2 == gi and k2 == "Z" and l2 > lay))
    return sorted(out, reverse=True)


def _template_grid():
    """The m = 2 template as 2 classes x 12 entries, from the table of record.

    tables/tab_template_m2.tex is generated from data/template_main.csv by
    twoblock/make_tables.py; the per-cell layers live only in that table, so
    they are read back from it rather than retyped.
    """
    p = os.path.join(ROOT, "tables", "tab_template_m2.tex")
    if not os.path.exists(p):
        return None
    rows = []
    for line in open(p):
        if r"$\bullet$" not in line or "&" not in line:
            continue
        cells = [c.strip() for c in line.split("&")]
        if len(cells) < 9:
            continue
        cls, lab, etype = cells[0], cells[1], cells[2]
        lay = next((i + 1 for i, c in enumerate(cells[3:9])
                    if r"$\bullet$" in c), None)
        if lay is None:
            continue
        rows.append(dict(cls=int(cls), label=int(lab),
                         etype=etype.replace("$", "").replace(" ", ""),
                         layer=lay))
    return rows


def build_round7(out="fig2_scene.json"):
    """Extend the scene with what the flow diagram needs."""
    scene = build(out)
    D = scene["reference"]["Delta"]
    k = scene["reference"]["k"]
    l = scene["reference"]["l"]
    g = _gamma(D)
    assert sum(g) == k * l, f"gamma {g} sums to {sum(g)}, not k*l={k*l}"
    scene["flow"] = dict(
        pills=_pills(D),
        gamma=g, gamma_total=sum(g),
        # a + b = Delta + 1 with a = 3 gives the band [3, 4]: two layers for
        # the k = 3 X-edges of the L block, so the branch dies immediately.
        branch_narrow=dict(a=3, b=4, n_layers=2, n_edges=k,
                           text=f"no room: {k} edges, 2 layers",
                           derivable=True),
        # The a = 2 branch is excluded by a counting argument that lives in the
        # manuscript, not in this repository: no file here computes F_L and F_R
        # for a hypothetical depth-6 schedule.  The strings are carried through
        # verbatim and must be checked against the manuscript.
        branch_count=dict(a=2, b=5,
                          F_L="F_L = 4 + [c = 3]", F_R="F_R = 4 + [c = 4]",
                          derivable=False,
                          source="manuscript text (Round 7 brief); "
                                 "not derivable from this repository"),
        template=_template_grid(),
    )
    with open(os.path.join(DATA, out), "w") as f:
        json.dump(scene, f, indent=1)
    return scene

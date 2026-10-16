"""Pattern cards for Fig. 3: what the class of an instance looks like.

A two-block code's class is decided by the multiset of the k*l sums
a_s + b_t.  For k = l = 3 that is a 3 x 3 grid, and the class is legible in it:

  D   all nine sums distinct                      -> no two checks share a
                                                     four-qubit overlap
  C1  every sum repeated exactly twice            -> n4 = N, n6 = 0
  C2  some other repetition pattern

Fig. 3 draws that grid for one representative of each class, with coincident
cells joined, so a reader can see the class rather than look it up.  The
representatives, their sums and the coincidence groups are all computed here
from A and B and written to data/fig3_scene.json.
"""
from __future__ import annotations

import ast
import csv
import json
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

VERDICT = {"D": "UNSAT by theorem",
           "C1": r"SAT iff $d \notin 8G$",
           "C2": "mostly SAT"}


def _rows(name):
    with open(os.path.join(DATA, name)) as f:
        return list(csv.DictReader(f))


def _grid(N, A, B):
    """The k x l table of sums, and the groups of coincident cells."""
    A = [ast.literal_eval(str(a)) if isinstance(a, str) else a for a in A]
    sums = [[(int(a[0]) + int(b[0])) % N for b in B] for a in A]
    where = defaultdict(list)
    for i, row in enumerate(sums):
        for j, v in enumerate(row):
            where[v].append([i, j])
    groups = [cells for v, cells in sorted(where.items()) if len(cells) > 1]
    return sums, groups


def build(out="fig3_scene.json"):
    sharp = {r["name"]: r for r in _rows("h2_sharpness.csv")}
    ov = {r["instance"]: r for r in _rows("r7_overlap_counts.csv")}
    cards = []
    for klass in ("D", "C1", "C2"):
        pick = None
        for name, r in sharp.items():
            if r.get("class") != klass:
                continue
            A = ast.literal_eval(r["A"])
            B = ast.literal_eval(r["B"])
            if len(A) != 3 or len(B) != 3 or len(A[0]) != 1:
                continue            # cards are 3 x 3 over a cyclic group
            pick = (name, int(r["N"]), A, B, r)
            break
        if pick is None:
            continue
        name, N, A, B, r = pick
        sums, groups = _grid(N, A, B)
        o = ov.get(name, {})
        cards.append(dict(
            klass=klass, instance=name, N=N,
            A=[a[0] for a in A], B=[b[0] for b in B],
            sums=sums, groups=groups,
            n_distinct=len({v for row in sums for v in row}),
            distinct_sums=(r.get("distinct_sums") == "True"),
            n2=o.get("n2"), n4=o.get("n4"), n6=o.get("n6"),
            verdict=VERDICT[klass],
            source="data/h2_sharpness.csv, data/r7_overlap_counts.csv"))
    scene = dict(cards=cards)
    with open(os.path.join(DATA, out), "w") as f:
        json.dump(scene, f, indent=1)
    return scene


if __name__ == "__main__":
    s = build()
    for c in s["cards"]:
        print(f"{c['klass']:3} {c['instance']:18} N={c['N']:3} "
              f"A={c['A']} B={c['B']}")
        for row in c["sums"]:
            print("      ", row)
        print(f"      distinct sums={c['n_distinct']}/9  groups={c['groups']}")
        print(f"      n2={c['n2']} n4={c['n4']} n6={c['n6']}  -> {c['verdict']}")

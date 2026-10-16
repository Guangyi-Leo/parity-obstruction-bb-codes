"""The general mod-4 obstruction must reproduce the old verdict everywhere.

twoblock/mod4.py states the obstruction on H_X and H_Z directly: per connected
component, sum_v r_v s_v where r_v, s_v are the X- and Z-degrees of data qubit v.  The
old form (twoblock/components.py) assumed the component regular and tested
n * Delta_X * Delta_Z / 2 for oddness.  Every instance in this repository is a two-block
code and so is regular, which is exactly where the two must agree.

Writes data/mod4_agreement.csv.
"""
from __future__ import annotations

import ast
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from twoblock.code import TwoBlockCode                                  # noqa: E402
from twoblock.components import theorem1_obstructed                     # noqa: E402
from twoblock.mod4 import obstruction_general, obstructed               # noqa: E402

DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "mod4_agreement.csv")


def _read(name):
    p = os.path.join(DATA, name)
    with open(p) as f:
        return list(csv.DictReader(f))


def _cases():
    h2 = {r["name"]: r for r in _read("h2_sharpness.csv")}
    h4 = {r["instance"]: r for r in _read("h4_features.csv")}
    inst = {r["name"]: r for r in _read("instances.csv")}
    for r in _read("r7_overlap_counts.csv"):
        n = r["instance"]
        if n in h2:
            s = h2[n]; yield n, "classified", [int(s["N"])], s["A"], s["B"]
        elif n in h4:
            s = h4[n]; yield n, "classified", [int(s["N"])], s["A"], s["B"]
        elif n in inst:
            s = inst[n]
            yield n, "classified", ast.literal_eval(s["dims"]), s["A_json"], s["B_json"]
    for r in _read("sweep.csv"):
        yield r["name"], "sweep", ast.literal_eval(r["dims"]), r["A"], r["B"]


def test_mod4_general_matches_old():
    rows, bad = [], []
    n_cls = n_sweep = 0
    for name, src, dims, A, B in _cases():
        code = TwoBlockCode(tuple(dims),
                            [tuple(a) for a in ast.literal_eval(A)],
                            [tuple(b) for b in ast.literal_eval(B)], name)
        comps = obstruction_general(code.H_X(), code.H_Z())
        new, old = obstructed(code.H_X(), code.H_Z()), theorem1_obstructed(code)
        rows.append(dict(instance=name, source=src, n_components=len(comps),
                         hypothesis_met=all(c["hypothesis_met"] for c in comps),
                         sum_rs=sum(c["sum_rs"] for c in comps),
                         mod4=str([c["sum_rs_mod4"] for c in comps]),
                         obstructed_general=new, obstructed_old=old))
        if new != old:
            bad.append((name, new, old))
        n_cls += src == "classified"
        n_sweep += src == "sweep"
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    n_ob = sum(1 for r in rows if r["obstructed_general"])
    n_hyp = sum(1 for r in rows if r["hypothesis_met"])
    print(f"[wrote {os.path.relpath(OUT, ROOT)}: {len(rows)} instances]")
    assert not bad, f"general and old verdict disagree on {bad[:5]}"
    print(f"A1 general mod-4 form agrees with n*Delta_X*Delta_Z/2 on all {len(rows)} "
          f"instances ({n_cls} classified + {n_sweep} sweep); hypothesis met on "
          f"{n_hyp}, obstructed {n_ob}")


if __name__ == "__main__":
    test_mod4_general_matches_old()

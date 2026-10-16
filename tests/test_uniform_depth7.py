"""Item 12: is the depth-7 uniform schedule good for the whole family?

The schedule of Table S10 assigns a layer to a Tanner edge from its (check kind,
qubit side, label) alone -- nothing about the group element -- so it can be applied
verbatim to any two-block code with k = l = 3.  If every one of the nine label pairs
has equal L- and R-corner orientations, the properness XOR cancels pairwise on every
overlap pair whatever the group, which is the upper bound for the family.

Writes data/uniform_depth7.csv.
"""
from __future__ import annotations

import csv
import json
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from twoblock.code import TwoBlockCode                                  # noqa: E402
from twoblock import instances                                         # noqa: E402
from twoblock.overlaps import counts                                   # noqa: E402
from twoblock.simulate import (                                        # noqa: E402
    is_proper_by_simulation, is_valid_layering,
)

SEED = 7
DEPTH = 7
CAP = 60.0
OUT = os.path.join(ROOT, "data", "uniform_depth7.csv")
SCHED = os.path.join(ROOT, "schedules", "bb72_d7_inv.json")


def table_s10():
    with open(SCHED) as f:
        d = json.load(f)
    pi = {}
    for e, l in zip(d["edges"], d["layers"]):
        pi.setdefault(e[0] + e[1], {})[int(e[2])] = int(l)
    return {k: tuple(pi[k][s] for s in sorted(pi[k])) for k in
            ("XL", "XR", "ZL", "ZR")}


def orientations(pi):
    """[(s, t, o_L, o_R)] over the nine label pairs, 1-based labels."""
    out = []
    for s in range(3):
        for t in range(3):
            oL = int(pi["XL"][s] < pi["ZL"][t])
            oR = int(pi["XR"][t] < pi["ZR"][s])
            out.append((s + 1, t + 1, oL, oR))
    return out


def apply_uniform(code, pi):
    lay = [0] * code.n_edges
    for e in code.edges:
        lay[e.eid] = pi[e.kind + e.side][e.lab]
    return lay


def random_instances(want_distinct, n_want, rng, ns=(10, 12, 14, 15, 16, 18, 20,
                                                     21, 22, 24, 26, 28)):
    out, seen = [], set()
    tries = 0
    while len(out) < n_want and tries < 200000:
        tries += 1
        N = rng.choice(ns)
        A = tuple(sorted([0] + rng.sample(range(1, N), 2)))
        B = tuple(sorted([0] + rng.sample(range(1, N), 2)))
        if (N, A, B) in seen:
            continue
        seen.add((N, A, B))
        code = TwoBlockCode((N,), [(x,) for x in A], [(x,) for x in B],
                            f"u7_Z{N}_{'-'.join(map(str, A))}_{'-'.join(map(str, B))}")
        ds = code.distinct_sums()
        if want_distinct and not ds:
            continue
        if not want_distinct:
            if ds:
                continue
            if counts(code)["klass"] not in ("C1", "C2"):
                continue
        out.append(code)
    return out


def test_uniform_depth7():
    pi = table_s10()
    print(f"T10 Table S10: X L={pi['XL']} R={pi['XR']};  Z L={pi['ZL']} R={pi['ZR']}")
    ors = orientations(pi)
    bad = [(s, t, a, b) for s, t, a, b in ors if a != b]
    print("T10 orientation table (s, t) -> (o_L, o_R):")
    for s in range(1, 4):
        row = "  ".join(f"({s},{t}) {a}/{b}" for ss, t, a, b in ors if ss == s
                        for _ in [0] for a, b in [(a, b)])
        print(f"      {row}")
    assert not bad, f"L and R orientations differ on {bad}"
    print(f"T10 all nine label pairs have o_L == o_R")

    rng = random.Random(SEED)
    groups = [("published", [instances.get(n) for n in
                             ("bb72", "bb90", "bb108", "bb144", "bb288", "bb360",
                              "bb756")]),
              ("random distinct-sums", random_instances(True, 20, rng)),
              ("random C1/C2", random_instances(False, 20, rng))]
    rows, fails = [], []
    for label, codes in groups:
        npass = 0
        for code in codes:
            t0 = time.time()
            code.check_structure()
            lay = apply_uniform(code, pi)
            valid = is_valid_layering(code, lay, DEPTH)
            proper = is_proper_by_simulation(code, lay, DEPTH) if valid else False
            dt = time.time() - t0
            assert dt < CAP, f"{code.name}: simulation exceeded {CAP} s"
            kl = counts(code)["klass"]
            rows.append(dict(group=label, instance=code.name, N=code.N, klass=kl,
                             distinct_sums=code.distinct_sums(), valid=valid,
                             proper=proper, seconds=round(dt, 3)))
            npass += bool(valid and proper)
            if not (valid and proper):
                fails.append((label, code.name, valid, proper))
        print(f"T10 {label:22s} {npass}/{len(codes)} proper at depth {DEPTH}")
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"[wrote {os.path.relpath(OUT, ROOT)}: {len(rows)} instances]")
    assert not fails, f"the uniform schedule failed on {fails[:5]}"
    print(f"T10: the Table S10 schedule is a proper depth-{DEPTH} schedule on all "
          f"{len(rows)} instances tested")


if __name__ == "__main__":
    test_uniform_depth7()

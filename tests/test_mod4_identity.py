"""The corner count behind the mod-4 obstruction, checked numerically.

For a data qubit v with r_v X-edges and s_v Z-edges, the corners at v are the r_v * s_v
pairs (X-edge, Z-edge), so the whole code has sum_v r_v s_v corners.  Each corner is
X-first or Z-first under a given layering.  This test records, for 200 random valid
depth-Delta layerings of bb72 and of oe23 (proper or not), the total corner count, the
number that are X-first, and sum_v r_v s_v.  Writes data/mod4_identity.csv.
"""
from __future__ import annotations

import csv
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))

from tests.test_small import random_layering                            # noqa: E402
from twoblock import instances                                         # noqa: E402
from twoblock.simulate import (                                        # noqa: E402
    is_proper_by_simulation, is_valid_layering,
)

SEED = 7
N_SAMPLES = 200
OUT = os.path.join(ROOT, "data", "mod4_identity.csv")


def sum_rs(code) -> int:
    tot = 0
    for v in code.vertices:
        if v[0] not in ("L", "R"):
            continue
        es = [code.edges[e] for e in code.data_edges[v]]
        tot += sum(1 for e in es if e.kind == "X") * sum(1 for e in es if e.kind == "Z")
    return tot


def test_mod4_identity():
    rng = random.Random(SEED)
    rows, bad_total, bad_half = [], [], []
    for name in ("bb72", "oe23"):
        code = instances.get(name)
        code.check_structure()
        D = code.Delta
        srs = sum_rs(code)
        n_corners = len(code.corners)
        for i in range(N_SAMPLES):
            lay = random_layering(code, D, rng)
            assert is_valid_layering(code, lay, D)
            xf = sum(1 for c in code.corners if lay[c.ex] < lay[c.ez])
            proper = is_proper_by_simulation(code, lay, D)
            rows.append(dict(instance=name, sample=i, Delta=D, n_corners=n_corners,
                             sum_rs=srs, x_first=xf, half_sum_rs=srs / 2,
                             x_first_equals_half=(2 * xf == srs), proper=proper))
            if n_corners != srs:
                bad_total.append((name, i, n_corners, srs))
            if 2 * xf != srs:
                bad_half.append((name, i, xf, srs / 2, proper))
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    n = len(rows)
    print(f"[wrote {os.path.relpath(OUT, ROOT)}: {n} layerings]")

    assert not bad_total, f"corner count != sum_v r_v s_v on {bad_total[:3]}"
    print(f"A2 corner count: len(code.corners) == sum_v r_v s_v on all {n} layerings "
          f"(bb72 {rows[0]['sum_rs']}, oe23 {rows[-1]['sum_rs']})")

    ok_half = n - len(bad_half)
    print(f"A2 X-first == sum_v r_v s_v / 2: holds on {ok_half} of {n} layerings")
    if bad_half:
        xs = sorted({b[2] for b in bad_half})
        print(f"A2 the half-identity does NOT hold for a general valid layering: "
              f"X-first ranges over {xs[0]}..{xs[-1]} against a half-sum of "
              f"{bad_half[0][3]:.0f}")
        prop = [b for b in bad_half if b[4]]
        print(f"A2 of the {len(bad_half)} counterexamples, {len(prop)} are proper "
              f"schedules")
    return rows


if __name__ == "__main__":
    test_mod4_identity()

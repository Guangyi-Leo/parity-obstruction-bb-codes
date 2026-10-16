"""Derive the fig-1 panel (a)/(b) content: a genuine depth-Delta edge colouring of bb72
and one overlap pair whose two shared corners carry opposite orientations.

No solver: the colouring comes from the Koenig/Kempe construction used by test T5, and
the violated pair is found by evaluating the properness parity directly.  The result is
written to data/fig1_violation.csv so that every number drawn in fig 1 comes from a CSV.
"""
from __future__ import annotations

import csv
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))

from tests.test_small import random_layering                       # noqa: E402
from twoblock import instances                                    # noqa: E402
from twoblock.simulate import is_valid_layering                    # noqa: E402

FIELDS = ["role", "kind", "side", "label", "layer", "check_g", "qubit_h",
          "corner", "orientation", "pair_xor", "N", "Delta", "instance"]


def main():
    code = instances.get("bb72")
    D = code.Delta
    rng = random.Random(7)
    lay = random_layering(code, D, rng, greedy_tries=1)
    assert is_valid_layering(code, lay, D), "colouring is not a valid depth-Delta layering"

    # first overlap pair whose two shared corners disagree
    chosen = None
    for op in code.overlap_pairs:
        if len(op.corners) != 2:
            continue
        o = [1 if lay[code.corners[c].ex] < lay[code.corners[c].ez] else 0
             for c in op.corners]
        if o[0] != o[1]:
            chosen = (op, o)
            break
    assert chosen, "no violated two-corner pair found in this colouring"
    op, o = chosen
    rows = []
    for idx, cid in enumerate(op.corners):
        cor = code.corners[cid]
        for role, eid in (("X", cor.ex), ("Z", cor.ez)):
            e = code.edges[eid]
            rows.append(dict(role=role, kind=e.kind, side=e.side, label=e.lab1,
                             layer=lay[eid], check_g=e.check, qubit_h=e.qubit,
                             corner=("L" if cor.side == "L" else "R"),
                             orientation=o[idx], pair_xor=(o[0] ^ o[1]),
                             N=code.N, Delta=D, instance=code.name))
    out = os.path.join(ROOT, "data", "fig1_violation.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {os.path.relpath(out, ROOT)}: pair (X_{op.gx}, Z_{op.gz}), "
          f"orientations {o}, XOR {o[0] ^ o[1]} (violation)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""R7 -- integer overlap counts n2 / n4 / n6 and the class labels.

P := H_X H_Z^T over the integers; P[x,z] is the number of data qubits shared by X-check
x and Z-check z, always even for a CSS pair.  Since P[x,z] = 2*|P(z-x)| and every delta
occurs for exactly N ordered pairs (x,z),

    n2 = N * #{delta : |P(delta)| = 1},
    n4 = N * #{delta : |P(delta)| = 2},
    n6 = N * #{delta : |P(delta)| = 3}.

Class labels (used verbatim everywhere):
    D  : "no 4-qubit overlaps"                            n4 = n6 = 0
    C1 : "one collision orbit (N four-qubit overlaps)"     n4 = N, n6 = 0
    C2 : "two collision orbits or one triple orbit"        n4 = 2N, n6 = 0  or  n4 = 0, n6 = N
    SG : "subgroup type"                                   A = B = a subgroup
"""
from __future__ import annotations

from collections import Counter

import numpy as np

from .code import TwoBlockCode

LABEL_TEXT = {
    "D": "no 4-qubit overlaps",
    "C1": "one collision orbit (N four-qubit overlaps)",
    "C2": "two collision orbits or one triple orbit",
    "SG": "subgroup type",
    "other": "other",
}


def is_subgroup(code: TwoBlockCode) -> bool:
    """A = B and A is a subgroup of G."""
    G = code.G
    if sorted(code.A) != sorted(code.B):
        return False
    S = set(code.A)
    if G.zero not in S:
        return False
    return all(G.add(x, y) in S for x in S for y in S)


def counts(code: TwoBlockCode) -> dict:
    N = code.N
    P = code.overlap_matrix()
    vals = Counter(int(v) for v in np.asarray(P).ravel())
    n2, n4, n6 = vals.get(2, 0), vals.get(4, 0), vals.get(6, 0)
    mult = Counter(len(v) for v in code.sum_sets().values())

    # structural identity: n_{2c} = N * #{delta : |P(delta)| = c}
    exp2, exp4, exp6 = N * mult.get(1, 0), N * mult.get(2, 0), N * mult.get(3, 0)
    assert (n2, n4, n6) == (exp2, exp4, exp6), (
        f"{code.name}: overlap counts {(n2, n4, n6)} != N*multiplicities "
        f"{(exp2, exp4, exp6)}")
    odd = [int(v) for v in np.asarray(P).ravel() if int(v) % 2]
    assert not odd, f"{code.name}: odd entry in H_X H_Z^T"

    # Pair-count identity.  A delta with |P(delta)| = c yields C(c,2) unordered
    # colliding pairs, so N * sum_delta C(c,2) = n4 + 3*n6, NOT n4 + 2*n6: a triple
    # orbit contributes three unordered pairs, not two.  Both are reported.
    n_pairs = sum(c * (c - 1) // 2 for c in
                  (len(v) for v in code.sum_sets().values()))
    pair_rhs = N * n_pairs
    assert n4 + 3 * n6 == pair_rhs, (
        f"{code.name}: n4+3*n6 = {n4 + 3*n6} != N*sum C(c,2) = {pair_rhs}")

    if is_subgroup(code):
        klass = "SG"
    elif n4 == 0 and n6 == 0:
        klass = "D"
    elif n4 == N and n6 == 0:
        klass = "C1"
    elif (n4 == 2 * N and n6 == 0) or (n4 == 0 and n6 == N):
        klass = "C2"
    else:
        klass = "other"

    # equivalences demanded by R7
    distinct = code.distinct_sums()
    if klass == "D":
        assert distinct, f"{code.name}: class D but sums are not distinct"
    if distinct:
        assert n4 == 0 and n6 == 0, f"{code.name}: distinct sums but n4={n4} n6={n6}"
    if klass == "C1":
        # C1 means: exactly one delta_0 with |P(delta_0)| = 2 and |P(delta)| <= 1 for
        # every other delta.  Equivalently n4 = N and n6 = 0.  Both halves are checked
        # so that a pattern with an extra triple (n6 != 0) can never be labelled C1.
        assert mult.get(2, 0) == 1, (
            f"{code.name}: C1 label but {mult.get(2, 0)} deltas of multiplicity 2")
        assert max(mult) <= 2, (
            f"{code.name}: C1 label but a delta of multiplicity {max(mult)} exists")
        assert n4 == N and n6 == 0, (
            f"{code.name}: C1 label but (n4, n6) = ({n4}, {n6}) != ({N}, 0)")

    return dict(instance=code.name, N=N, n2=n2, n4=n4, n6=n6,
                mult_histogram=dict(sorted(mult.items())),
                max_overlap_entry=int(np.asarray(P).max()),
                distinct_sums=distinct, is_subgroup=is_subgroup(code),
                klass=klass, label=LABEL_TEXT[klass],
                pair_rhs=pair_rhs, n4_plus_3n6=n4 + 3 * n6,
                n4_plus_2n6=n4 + 2 * n6,
                stated_identity_holds=(n4 + 2 * n6) == pair_rhs)


FIELDS = ["instance", "family", "N", "n2", "n4", "n6", "max_overlap_entry",
          "mult_histogram", "distinct_sums", "is_subgroup", "klass", "label",
          "n4_plus_3n6", "pair_rhs", "n4_plus_2n6", "stated_identity_holds"]


def main(argv=None):
    import csv
    import json
    import os
    from collections import Counter

    from . import instances as _inst
    from .solve import DATA, ROOT

    rows = []
    for nm in list(_inst.IBM) + list(_inst.ONE_EVEN) + ["k5", "sw73"]:
        r = counts(_inst.get(nm))
        r["family"] = "named"
        rows.append(r)
    src = os.path.join(DATA, "h2_sharpness.csv")
    relabel = Counter()
    if os.path.exists(src):
        for x in csv.DictReader(open(src)):
            code = TwoBlockCode((int(x["N"]),), [tuple(a) for a in json.loads(x["A"])],
                                [tuple(b) for b in json.loads(x["B"])], x["name"])
            r = counts(code)
            r["family"] = "H2/H4"
            old = "SG" if x["class"] == "subgroup" else x["class"]
            relabel[(old, r["klass"])] += 1
            rows.append(r)
    out = os.path.join(DATA, "r7_overlap_counts.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            r = dict(r)
            r["mult_histogram"] = json.dumps(r["mult_histogram"])
            w.writerow(r)
    print(f"R7: {len(rows)} instances; every class equivalence asserted "
          f"(the run would have aborted on a mismatch)")
    print(f"  class counts: {dict(Counter(r['klass'] for r in rows))}")
    print(f"  labels: " + "; ".join(f"{k} = {v!r}" for k, v in LABEL_TEXT.items()
                                    if k != "other"))
    if relabel:
        print(f"  previous label -> R7 label: {dict(relabel)}  "
              f"({'no relabelling needed' if all(a == b for a, b in relabel) else 'RELABELLED'})")
    bad = [r for r in rows if not r["stated_identity_holds"]]
    print(f"  identity n4 + 3*n6 = N * sum_delta C(|P(delta)|,2): holds on all "
          f"{len(rows)} (asserted)")
    print(f"  the variant n4 + 2*n6 fails on {len(bad)} instances "
          f"(a triple orbit gives C(3,2)=3 pairs, so it contributes 3N not 2N): "
          f"{[r['instance'] for r in bad][:6]}")
    print(f"  wrote {os.path.relpath(out, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

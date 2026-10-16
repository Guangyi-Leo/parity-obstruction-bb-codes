"""Instance definitions: IBM bivariate bicycle codes, one-even test codes, the sweep."""
from __future__ import annotations

import csv
import itertools
import json
import os

from .code import TwoBlockCode

SEED = 7
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# ---------------------------------------------------------------------------
# IBM bivariate bicycle codes -- Bravyi, Cross, Gambetta, Maslov, Rall, Yoder,
# "High-threshold and low-overhead fault-tolerant quantum memory", Nature 627
# (2024), Table 1.  Monomial x^i y^j is the group element (i, j) of Z_ell x Z_m.
#   bb72 : [[72,12,6]]    A = x^3 + y + y^2      B = y^3 + x + x^2
#   bb90 : [[90,8,10]]    A = x^9 + y + y^2      B = 1 + x^2 + x^7
#   bb108: [[108,8,10]]   A = x^3 + y + y^2      B = y^3 + x + x^2
#   bb144: [[144,12,12]]  A = x^3 + y + y^2      B = y^3 + x + x^2
#   bb288: [[288,12,18]]  A = x^3 + y^2 + y^7    B = y^3 + x + x^2
#   bb360: [[360,12,<=24]] A = x^9 + y + y^2     B = y^3 + x^25 + x^26
#   bb756: [[756,16,<=34]] A = x^3 + y^10 + y^17 B = y^5 + x^3 + x^19
# ---------------------------------------------------------------------------
IBM: dict[str, tuple] = {
    "bb72":  ((6, 6),   [(3, 0), (0, 1), (0, 2)],    [(0, 3), (1, 0), (2, 0)]),
    "bb90":  ((15, 3),  [(9, 0), (0, 1), (0, 2)],    [(0, 0), (2, 0), (7, 0)]),
    "bb108": ((9, 6),   [(3, 0), (0, 1), (0, 2)],    [(0, 3), (1, 0), (2, 0)]),
    "bb144": ((12, 6),  [(3, 0), (0, 1), (0, 2)],    [(0, 3), (1, 0), (2, 0)]),
    "bb288": ((12, 12), [(3, 0), (0, 2), (0, 7)],    [(0, 3), (1, 0), (2, 0)]),
    "bb360": ((30, 6),  [(9, 0), (0, 1), (0, 2)],    [(0, 3), (25, 0), (26, 0)]),
    "bb756": ((21, 18), [(3, 0), (0, 10), (0, 17)],  [(0, 5), (3, 0), (19, 0)]),
}

# One-even test codes: proper depth-Delta schedules exist; used for the lemma checks.
ONE_EVEN: dict[str, tuple] = {
    "oe23": ((12, 1), [(0, 0), (1, 0)],                         [(0, 0), (4, 0), (8, 0)]),  # Delta=5
    "oe21": ((8, 1),  [(0, 0), (3, 0)],                         [(0, 0)]),                  # Delta=3
    "oe43": ((16, 1), [(0, 0), (1, 0), (2, 0), (3, 0)],         [(0, 0), (4, 0), (8, 0)]),  # Delta=7
    "oe12": ((8, 1),  [(0, 0)],                                 [(0, 0), (4, 0)]),          # Delta=3
}

# Optional larger instance (section 6, optional block).
OPTIONAL: dict[str, tuple] = {
    "k5": ((26, 1), [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)],
           [(0, 0), (5, 0), (10, 0), (15, 0), (20, 0)]),        # Delta=10
}

# Notable sweep instance: the only one of the 1441 sweep codes that is UNSAT at
# depth 6.  A = B = {0,2,4} is the index-2 subgroup of Z6, so every nonzero |P(delta)|
# equals 3 and H_X H_Z^T has entries up to 6.  Named here so that the refutation can
# be re-run with a DRAT certificate (`solve.py --instance sw73 --depth 6 --proof`).
SWEEP_NOTABLE: dict[str, tuple] = {
    "sw73": ((6,), [(0,), (2,), (4,)], [(0,), (2,), (4,)]),
}

ALL: dict[str, tuple] = {**IBM, **ONE_EVEN, **OPTIONAL, **SWEEP_NOTABLE}

# Groups used by the small sweep.  Z2xZ2xZ2 is *not* of the form Z_ell x Z_m, so
# it is represented as the genuine triple product (2,2,2); code.Group supports
# arbitrary products of cyclic factors.
SWEEP_GROUPS: list[tuple[str, tuple[int, ...]]] = [
    ("Z4",       (4,)),
    ("Z2xZ2",    (2, 2)),
    ("Z6",       (6,)),
    ("Z8",       (8,)),
    ("Z2xZ4",    (2, 4)),
    ("Z2xZ2xZ2", (2, 2, 2)),
]


def get(name: str) -> TwoBlockCode:
    if name not in ALL:
        raise KeyError(f"unknown instance {name!r}; known: {sorted(ALL)}")
    dims, A, B = ALL[name]
    return TwoBlockCode(dims, A, B, name)


def sweep_instances() -> list[TwoBlockCode]:
    """All (A, B) with |A| = |B| = 3, 0 in A, 0 in B, over the sweep groups.

    Translation normalisation (0 in A, 0 in B) is the only quotient applied; no
    further relabelling is factored out, so a few isomorphic duplicates remain.
    Exact duplicates of (dims, sorted A, sorted B) are removed.
    """
    out: list[TwoBlockCode] = []
    seen: set[tuple] = set()
    for gname, dims in SWEEP_GROUPS:
        elts = [tuple(e) for e in itertools.product(*(range(d) for d in dims))]
        zero = tuple(0 for _ in dims)
        rest = [e for e in elts if e != zero]
        subsets = [(zero,) + c for c in itertools.combinations(rest, 2)]
        for A in subsets:
            for B in subsets:
                key = (dims, tuple(sorted(A)), tuple(sorted(B)))
                if key in seen:
                    continue
                seen.add(key)
                nm = f"sw_{gname}_A{'-'.join('.'.join(map(str, a)) for a in A)}" \
                     f"_B{'-'.join('.'.join(map(str, b)) for b in B)}"
                out.append(TwoBlockCode(dims, list(A), list(B), nm))
    return out


def instance_table(names=None) -> list[dict]:
    names = names or (list(IBM) + list(ONE_EVEN) + list(OPTIONAL) + list(SWEEP_NOTABLE))
    rows = []
    for nm in names:
        c = get(nm)
        facts = c.check_structure()
        facts["family"] = ("IBM" if nm in IBM else "one-even" if nm in ONE_EVEN
                           else "sweep" if nm in SWEEP_NOTABLE else "optional")
        facts["A_json"] = json.dumps([list(a) for a in c.A])
        facts["B_json"] = json.dumps([list(b) for b in c.B])
        facts["A_poly"] = "+".join("x^%d y^%d" % tuple(a) if len(a) == 2 else str(a) for a in c.A)
        facts["B_poly"] = "+".join("x^%d y^%d" % tuple(b) if len(b) == 2 else str(b) for b in c.B)
        rows.append(facts)
    return rows


def write_instance_csv(path: str | None = None) -> str:
    path = path or os.path.join(DATA, "instances.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rows = instance_table()
    fields = ["name", "family", "group", "dims", "N", "n_qubits", "k_logical", "k", "l", "Delta",
              "n_edges", "n_corners", "n_overlap_pairs", "distinct_sums",
              "max_overlap_entry", "multiplicity_histogram", "A_json", "B_json",
              "A_poly", "B_poly"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            r = dict(r)
            r["multiplicity_histogram"] = json.dumps(r["multiplicity_histogram"])
            w.writerow(r)
    return path


def main():
    path = write_instance_csv()
    rows = instance_table()
    print(f"{'name':7} {'group':10} {'N':>4} {'k':>2} {'l':>2} {'Δ':>2} "
          f"{'edges':>6} {'distinct':>8} {'maxovl':>6}  mult-hist")
    bad = []
    for r in rows:
        print(f"{r['name']:7} {r['group']:10} {r['N']:4d} {r['k']:2d} {r['l']:2d} {r['Delta']:2d} "
              f"{r['n_edges']:6d} {str(r['distinct_sums']):>8} {r['max_overlap_entry']:6d}  "
              f"{r['multiplicity_histogram']}")
        if r["family"] in ("IBM", "one-even") and not r["distinct_sums"]:
            bad.append(r["name"])
    print(f"\nwrote {path}")
    if bad:
        print(f"FAIL: expected distinct sums for {bad}")
        return 1
    print("OK: all IBM and one-even instances have distinct sums (max overlap entry 2)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

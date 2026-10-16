"""Per-group, per-class census of the instance set, raw and up to equivalence.

The generator (twoblock/sharpness.py) deduplicates *literal* pairs (A, B): it keeps a
set of the sorted tuples it has already drawn and skips repeats.  There is no
canonicalisation, so two sampled instances can still be equivalent as codes.  This
module counts both: the raw number of sampled pairs, and the number of equivalence
classes under the relation that actually leaves a two-block code unchanged,

    (A, B) ~ (u*A + t1, u*B + t2)   for u in the units of Z_N, t1, t2 in Z_N
    (A, B) ~ (B, A)

(translating A and B relabels the L- and R-qubits; multiplying by a unit is an
automorphism of Z_N; the swap exchanges the two blocks).  Writes
data/instances_by_group.csv.
"""
from __future__ import annotations

import csv
import json
import os
from collections import Counter
from math import gcd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "instances_by_group.csv")


def _read(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return list(csv.DictReader(f))


def canonical(N: int, A, B) -> tuple:
    """Lexicographically smallest representative of the equivalence class."""
    units = [u for u in range(1, N) if gcd(u, N) == 1] or [1]
    best = None
    for X, Y in ((A, B), (B, A)):
        for u in units:
            uX = [(u * x) % N for x in X]
            uY = [(u * y) % N for y in Y]
            for t1 in range(N):
                sX = tuple(sorted((x + t1) % N for x in uX))
                if sX[0] != 0:
                    continue
                for t2 in range(N):
                    sY = tuple(sorted((y + t2) % N for y in uY))
                    if sY[0] != 0:
                        continue
                    cand = (sX, sY)
                    if best is None or cand < best:
                        best = cand
    return best


def build() -> list[dict]:
    cov = {r["instance"]: r for r in _read("coverage.csv")}
    src = {}
    for r in _read("h2_sharpness.csv"):
        src[r["name"]] = (int(r["N"]), json.loads(r["A"]), json.loads(r["B"]))
    for r in _read("h4_features.csv"):
        src.setdefault(r["instance"], (int(r["N"]), json.loads(r["A"]),
                                       json.loads(r["B"])))
    for r in _read("instances.csv"):
        src.setdefault(r["name"], (int(r["N"]), json.loads(r["A_json"]),
                                   json.loads(r["B_json"])))

    rows = {}
    for name, c in cov.items():
        if c["in_sharpness_map"] != "True" or name not in src:
            continue
        N, A, B = src[name]
        if any(len(a) != 1 for a in A):          # non-cyclic: not canonicalised here
            key = (N, "noncyclic", name)
        else:
            key = canonical(N, [a[0] for a in A], [b[0] for b in B])
        g = rows.setdefault((N, c["class"]), dict(N=N, klass=c["class"], sampled=0,
                                                  canon=set()))
        g["sampled"] += 1
        g["canon"].add(key)
    out = []
    for (N, kl), g in sorted(rows.items()):
        out.append(dict(N=N, group=f"Z{N}", klass=kl, sampled=g["sampled"],
                        inequivalent=len(g["canon"]),
                        duplicates=g["sampled"] - len(g["canon"])))
    return out


def main(argv=None):
    rows = build()
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["N", "group", "klass", "sampled",
                                          "inequivalent", "duplicates"])
        w.writeheader(); w.writerows(rows)
    print(f"  wrote {os.path.relpath(OUT, ROOT)}: {len(rows)} (group, class) cells")
    s = sum(r["sampled"] for r in rows)
    q = sum(r["inequivalent"] for r in rows)
    print(f"  sampled instances {s}, inequivalent up to (unit, translation, swap) {q}, "
          f"duplicates {s - q}")
    by = Counter()
    for r in rows:
        by[r["klass"]] += r["duplicates"]
    print(f"  duplicates by class: {dict(by)}")
    for r in rows:
        if r["duplicates"]:
            print(f"    Z{r['N']:<3d} {r['klass']:3s} sampled {r['sampled']:3d} "
                  f"inequivalent {r['inequivalent']:3d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

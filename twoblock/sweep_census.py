"""Orbit census of the even-order sweep (data/sweep.csv, |G| = 2..8).

Same equivalence as the odd-order sweep: Aut(G), independent translations of A
and B, and the block swap (twoblock/equiv.py).  Writes data/sweep_census.csv --
one row per group -- and prints the orbit representatives' outcome split, which
is the number the manuscript may quote as "1,441 instances (N inequivalent)".
"""
from __future__ import annotations

import ast
import collections
import csv
import json
import os

from .equiv import automorphisms, canonical

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def load(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def build(src="sweep.csv", out="sweep_census.csv"):
    rows = load(os.path.join(DATA, src))
    by_group = collections.defaultdict(list)
    for r in rows:
        by_group[(r["group"], r["dims"])].append(r)

    out_rows, orbit_rows = [], []
    for (gname, dimss), rs in sorted(by_group.items(),
                                     key=lambda kv: (len(ast.literal_eval(kv[0][1])),
                                                     kv[0][0])):
        dims = tuple(ast.literal_eval(dimss))
        auts = automorphisms(dims)
        orbits = collections.defaultdict(list)
        for r in rs:
            A = [tuple(x) for x in ast.literal_eval(r["A"])]
            B = [tuple(x) for x in ast.literal_eval(r["B"])]
            orbits[canonical(dims, A, B, auts)].append(r)
        split = collections.Counter()
        for key, members in orbits.items():
            # the representative is the first member in file order
            rep = members[0]
            split[rep["status"]] += 1
            orbit_rows.append(dict(group=gname, dims=dimss, n_members=len(members),
                                   rep=rep["name"], rep_status=rep["status"],
                                   A=rep["A"], B=rep["B"],
                                   distinct_sums=rep["distinct_sums"],
                                   statuses="|".join(sorted({m["status"]
                                                             for m in members}))))
        out_rows.append(dict(
            group=gname, dims=dimss, N=rs[0]["N"], aut_order=len(auts),
            normalised_pairs=len(rs), orbits=len(orbits),
            rep_SAT=split.get("SAT", 0), rep_UNSAT=split.get("UNSAT", 0),
            rep_capped=split.get("capped", 0) + split.get("UNKNOWN", 0),
            mixed_orbits=sum(1 for m in orbits.values()
                             if len({x["status"] for x in m}) > 1)))
    p = os.path.join(DATA, out)
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        w.writeheader()
        w.writerows(out_rows)
    p2 = os.path.join(DATA, "sweep_census_orbits.csv")
    with open(p2, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(orbit_rows[0]))
        w.writeheader()
        w.writerows(sorted(orbit_rows, key=lambda r: (r["group"], r["rep"])))
    return out_rows, orbit_rows


if __name__ == "__main__":
    rows, orbs = build()
    hdr = f"{'group':10} {'|Aut|':>5} {'pairs':>6} {'orbits':>7} {'SAT':>5} {'UNSAT':>6} {'capped':>7} {'mixed':>6}"
    print(hdr); print("-" * len(hdr))
    tot = collections.Counter()
    for r in rows:
        print(f"{r['group']:10} {r['aut_order']:5} {r['normalised_pairs']:6} "
              f"{r['orbits']:7} {r['rep_SAT']:5} {r['rep_UNSAT']:6} "
              f"{r['rep_capped']:7} {r['mixed_orbits']:6}")
        for k in ("normalised_pairs", "orbits", "rep_SAT", "rep_UNSAT",
                  "rep_capped", "mixed_orbits"):
            tot[k] += int(r[k])
    print("-" * len(hdr))
    print(f"{'total':10} {'':>5} {tot['normalised_pairs']:6} {tot['orbits']:7} "
          f"{tot['rep_SAT']:5} {tot['rep_UNSAT']:6} {tot['rep_capped']:7} "
          f"{tot['mixed_orbits']:6}")
    uns = [o for o in orbs if o["rep_status"] == "UNSAT"]
    print("\nUNSAT orbits:", len(uns))
    for o in uns:
        print(f"  {o['group']}  rep={o['rep']}  A={o['A']}  B={o['B']}  "
              f"orbit size={o['n_members']}  statuses={o['statuses']}")

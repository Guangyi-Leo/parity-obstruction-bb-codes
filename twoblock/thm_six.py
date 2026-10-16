"""Coverage of the depth-six theorem: does d lie in 8G, and what happened at depth 6?

in_8G(d) is decided directly -- is there an x in G with 8x = d -- so an odd-order
group, where 8 is invertible, correctly gives True for every element.
Writes data/thm_six_coverage.csv.
"""
from __future__ import annotations

import ast
import csv
import os
from collections import Counter

from .code import Group

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "thm_six_coverage.csv")


def _read(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return list(csv.DictReader(f))


def in_8G(G: Group, d: tuple) -> bool:
    for x in G.elements:
        acc, k, base = tuple(0 for _ in x), 8, x
        while k:
            if k & 1:
                acc = G.add(acc, base)
            base = G.add(base, base)
            k >>= 1
        if acc == tuple(d):
            return True
    return False


def main(argv=None):
    feats = {r["instance"]: r for r in _read("h4_features.csv")}
    cov = {r["instance"]: r for r in _read("coverage.csv")}
    fin = _read("c1_final_instances.csv")
    rows = []
    for c in fin:
        n = c["instance"]
        f = feats.get(n)
        if not f or not f.get("d"):
            continue
        dims = tuple(int(p[1:]) for p in f["group"].split("x"))
        G = Group(dims)
        d = tuple(ast.literal_eval(f["d"]))
        cv = cov.get(n, {})
        rows.append(dict(instance=n, group=f["group"], N=f["N"], d=f["d"],
                         ord_d=f.get("ord_d", ""),
                         ord_d_parity="even" if c["ord_d_even"] == "True" else "odd",
                         in_8G=in_8G(G, d),
                         status_math=cv.get("status_math", ""),
                         status_solver=cv.get("status_solver", ""),
                         resolved=c["status_resolved"]))
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"  wrote {os.path.relpath(OUT, ROOT)}: {len(rows)} class-C1 instances")

    tab = Counter((r["in_8G"], r["ord_d_parity"], r["resolved"]) for r in rows)
    print(f"\n  {'in 8G':>6} {'ord(d)':>7} {'SAT':>6} {'UNSAT':>7} {'capped':>7} "
          f"{'total':>7}")
    for g in (False, True):
        for par in ("even", "odd"):
            sat = tab[(g, par, "SAT")]
            uns = tab[(g, par, "UNSAT")]
            cap = tab[(g, par, "UNDETERMINED")]
            print(f"  {str(g):>6} {par:>7} {sat:6d} {uns:7d} {cap:7d} "
                  f"{sat + uns + cap:7d}")

    bad = [r for r in rows if not r["in_8G"] and r["resolved"] != "SAT"]
    if bad:
        print(f"\n  BLOCKING DEFECT: {len(bad)} instances with d not in 8G are not SAT")
        for r in bad[:10]:
            print(f"    {r['instance']} {r['group']} d={r['d']} "
                  f"ord_d={r['ord_d']} -> {r['resolved']}")
    else:
        n_not = sum(1 for r in rows if not r["in_8G"])
        print(f"\n  every one of the {n_not} instances with d not in 8G is SAT")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

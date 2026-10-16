"""Item 4: the odd orders and order 9 the original sweep never covered.

data/sweep.csv covers |G| in {4, 6, 8} only, so no odd order and no order 9.
Order 9 matters: it is the smallest order at which distinct sums are possible
(9 = k*l), e.g. Z3xZ3 with A = {(0,0),(1,0),(2,0)}, B = {(0,0),(0,1),(0,2)}.

Enumerating every normalised (A, B) is wasteful -- most are equivalent as codes.
This module canonicalises first, under the relation that leaves a two-block code
unchanged,

    (A, B) ~ (phi(A) + t1, phi(B) + t2)   phi in Aut(G), t1, t2 in G
    (A, B) ~ (B, A)

and solves one representative per orbit.  Rows are appended to data/sweep_odd.csv
as they finish, so a stopped run loses nothing, and a call that hits the cap is
recorded `capped`, never as a verdict.
"""
from __future__ import annotations

import argparse
import collections
import csv
import itertools
import json
import os
import time
from math import gcd

from .code import TwoBlockCode
from .encode import encode
from .simulate import is_proper_by_simulation, is_valid_layering
from .solve import CERTS, DATA, run_solver

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUPS = [("Z3", (3,)), ("Z5", (5,)), ("Z7", (7,)), ("Z9", (9,)), ("Z3xZ3", (3, 3))]
OUT = os.path.join(DATA, "sweep_odd.csv")
FIELDS = ["name", "group", "dims", "A", "B", "N", "k", "l", "Delta",
          "distinct_sums", "max_multiplicity", "mult_histogram", "orbit_size",
          "D", "status", "time", "proper_by_simulation", "nvars", "nclauses",
          "source"]


def automorphisms(dims):
    """Every automorphism of G, as a callable on element tuples."""
    if len(dims) == 1:
        n = dims[0]
        return [(lambda u: (lambda g: ((u * g[0]) % n,)))(u)
                for u in range(1, n) if gcd(u, n) == 1]
    a, b = dims
    if a != b:
        return [lambda g: g]
    n = a
    out = []
    for m in itertools.product(range(n), repeat=4):
        if gcd((m[0] * m[3] - m[1] * m[2]) % n, n) != 1:
            continue
        out.append((lambda mm: (lambda g: ((mm[0] * g[0] + mm[1] * g[1]) % n,
                                           (mm[2] * g[0] + mm[3] * g[1]) % n)))(m))
    return out


def canonical(dims, A, B, auts):
    """Smallest representative of the orbit.

    Only translations that put 0 into the set can matter, so t1 ranges over
    -phi(A) and t2 over -phi(B): nine pairs, not |G|^2.
    """
    def shifts(P):
        out = []
        for h in P:
            t = tuple((-u) % d for u, d in zip(h, dims))
            out.append(tuple(sorted(tuple((u + v) % d for u, v, d in
                                          zip(g, t, dims)) for g in P)))
        return out

    best = None
    for X, Y in ((A, B), (B, A)):
        for phi in auts:
            sxs = shifts([phi(g) for g in X])
            sys_ = shifts([phi(g) for g in Y])
            for sX in sxs:
                for sY in sys_:
                    cand = (sX, sY)
                    if best is None or cand < best:
                        best = cand
    return best


def orbits():
    """One representative per orbit, per group, with the orbit size."""
    out = []
    for gname, dims in GROUPS:
        elts = [tuple(e) for e in itertools.product(*(range(d) for d in dims))]
        zero = tuple(0 for _ in dims)
        rest = [e for e in elts if e != zero]
        subsets = [(zero,) + c for c in itertools.combinations(rest, 2)]
        auts = automorphisms(dims)
        seen = {}
        for A in subsets:
            for B in subsets:
                key = canonical(dims, list(A), list(B), auts)
                if key in seen:
                    seen[key][1] += 1
                else:
                    seen[key] = [(list(A), list(B)), 1]
        for key, (AB, size) in sorted(seen.items(), key=str):
            A, B = AB
            nm = (f"sw9_{gname}_A{'-'.join('.'.join(map(str, a)) for a in A)}"
                  f"_B{'-'.join('.'.join(map(str, b)) for b in B)}")
            out.append((gname, dims, A, B, nm, size))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=6)
    ap.add_argument("--timeout", type=float, default=20.0)
    ap.add_argument("--census", action="store_true", help="orbit counts, then stop")
    a = ap.parse_args(argv)

    t0 = time.time()
    todo = orbits()
    per = collections.Counter(g for g, *_ in todo)
    tot = collections.Counter()
    for g, dims, A, B, nm, size in todo:
        tot[g] += size
    print(f"  canonicalised in {time.time() - t0:.0f} s")
    for g, _ in GROUPS:
        print(f"    {g:6s} {tot[g]:5d} normalised pairs -> {per[g]:4d} orbits")
    if a.census:
        return 0

    done = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            done = {r["name"]: r for r in csv.DictReader(f)}
    d = os.path.join(CERTS, "sweep_odd")
    os.makedirs(d, exist_ok=True)

    rows = []
    for i, (gname, dims, A, B, nm, size) in enumerate(todo):
        if nm in done:
            rows.append(done[nm]); continue
        code = TwoBlockCode(tuple(dims), [tuple(x) for x in A],
                            [tuple(x) for x in B], nm)
        code.check_structure()
        enc = encode(code, a.depth)
        cnf = os.path.join(d, f"{nm}_d{a.depth}.cnf")
        enc.write_dimacs(cnf)
        res = run_solver(cnf, None, timeout=a.timeout)
        os.remove(cnf)
        hist = {}
        for v in code.sum_sets().values():
            hist[len(v)] = hist.get(len(v), 0) + 1
        status = res.status if res.status in ("SAT", "UNSAT") else "capped"
        proper = ""
        if status == "SAT":
            lay = enc.decode_model(res.model)
            assert is_valid_layering(code, lay, a.depth), nm
            proper = is_proper_by_simulation(code, lay, a.depth)
            assert proper, f"{nm}: SAT model is not proper"
        rows.append(dict(name=nm, group=gname, dims=json.dumps(list(dims)),
                         A=json.dumps(A), B=json.dumps(B), N=code.N, k=code.k,
                         l=code.l, Delta=code.Delta,
                         distinct_sums=code.distinct_sums(),
                         max_multiplicity=max(hist),
                         mult_histogram=json.dumps(dict(sorted(hist.items()))),
                         orbit_size=size, D=a.depth, status=status,
                         time=round(res.time, 3), proper_by_simulation=proper,
                         nvars=enc.nvars, nclauses=len(enc.clauses),
                         source="sweep_odd"))
        with open(OUT, "w", newline="") as f:       # incremental, resumable
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader(); w.writerows(rows)
        if (i + 1) % 25 == 0:
            print(f"    {i+1}/{len(todo)}  {time.time()-t0:.0f} s", flush=True)

    print(f"\n  wrote {os.path.relpath(OUT, ROOT)}: {len(rows)} orbits, "
          f"{time.time()-t0:.0f} s")
    st = collections.Counter((r["group"], str(r["status"])) for r in rows)
    print(f"  {'group':7s} {'orbits':>7s} {'SAT':>5s} {'UNSAT':>6s} {'capped':>7s}")
    for g, _ in GROUPS:
        print(f"  {g:7s} {per[g]:7d} {st[(g,'SAT')]:5d} {st[(g,'UNSAT')]:6d} "
              f"{st[(g,'capped')]:7d}")
    ds = [r for r in rows if str(r["distinct_sums"]) == "True"]
    bad = [r for r in ds if str(r["status"]) != "UNSAT"]
    print(f"  distinct-sums orbits: {len(ds)}; all UNSAT: {not bad}")
    for r in bad[:6]:
        print(f"    NOT UNSAT: {r['name']} status={r['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

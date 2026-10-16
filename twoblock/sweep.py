"""Small sweep over two-block codes with k = l = 3 (specification section 6/o1).

Every A, B of size 3 containing the identity, over the groups Z4, Z2xZ2, Z6, Z8,
Z2xZ4 and Z2xZ2xZ2, solved at depth 6 with a 600 s timeout.  Solver runs are
single-threaded; only the sweep uses a process pool.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

from .code import TwoBlockCode
from .encode import encode
from .instances import SWEEP_GROUPS, sweep_instances
from .simulate import is_proper_by_simulation, is_valid_layering
from .solve import CERTS, DATA, run_solver

FIELDS = ["idx", "name", "group", "dims", "A", "B", "N", "k", "l", "Delta",
          "distinct_sums", "max_multiplicity", "mult_histogram", "max_overlap_entry",
          "D", "status", "time", "proper_by_simulation", "nvars", "nclauses",
          "proof_bytes", "verified"]


def _one(job) -> dict:
    idx, dims, A, B, name, gname, D, timeout, proof = job
    code = TwoBlockCode(tuple(dims), [tuple(a) for a in A], [tuple(b) for b in B], name)
    code.check_structure()
    hist = code.multiplicity_histogram()
    row = dict(idx=idx, name=name, group=gname, dims=json.dumps(list(dims)),
               A=json.dumps([list(a) for a in code.A]), B=json.dumps([list(b) for b in code.B]),
               N=code.N, k=code.k, l=code.l, Delta=code.Delta,
               distinct_sums=code.distinct_sums(), max_multiplicity=max(hist),
               mult_histogram=json.dumps(hist),
               max_overlap_entry=int(code.overlap_matrix().max()), D=D)
    d = os.path.join(CERTS, "sweep")
    os.makedirs(d, exist_ok=True)
    cnf = os.path.join(d, f"sw{idx:05d}_d{D}.cnf")
    drat = os.path.join(d, f"sw{idx:05d}_d{D}.drat") if proof else None
    enc = encode(code, D)
    enc.write_dimacs(cnf)
    res = run_solver(cnf, drat, timeout=timeout)
    row.update(status=res.status, time=round(res.time, 3), nvars=enc.nvars,
               nclauses=len(enc.clauses), proof_bytes=res.proof_bytes, verified=res.verified)
    row["proper_by_simulation"] = ""
    if res.status == "SAT":
        lay = enc.decode_model(res.model)
        assert is_valid_layering(code, lay, D), f"{name}: invalid layering from SAT model"
        ok = is_proper_by_simulation(code, lay, D)
        assert ok, f"{name}: SAT model is not proper by simulation -- encoding is wrong"
        row["proper_by_simulation"] = True
    for f in (cnf, drat):
        if f and os.path.exists(f):
            os.remove(f)
    return row


def run_sweep(depth: int = 6, timeout: float = 600, workers: int = 12,
              out: str | None = None, limit: int | None = None, proof: bool = False) -> str:
    out = out or os.path.join(DATA, "sweep.csv")
    codes = sweep_instances()
    if limit:
        codes = codes[:limit]
    gname_of = {}
    for gname, dims in SWEEP_GROUPS:
        gname_of[tuple(dims)] = gname
    jobs = [(i, c.G.dims, [list(a) for a in c.A], [list(b) for b in c.B], c.name,
             gname_of[c.G.dims], depth, timeout, proof) for i, c in enumerate(codes)]
    print(f"sweep: {len(jobs)} instances, depth {depth}, timeout {timeout}s, {workers} workers",
          flush=True)
    os.makedirs(DATA, exist_ok=True)
    t0 = time.time()
    done = 0
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(_one, j): j for j in jobs}
            for fut in as_completed(futs):
                row = fut.result()
                w.writerow(row)
                done += 1
                if done % 100 == 0 or done == len(jobs):
                    f.flush()
                    print(f"  {done}/{len(jobs)} done ({time.time()-t0:.0f}s)", flush=True)
    print(f"sweep finished in {time.time()-t0:.0f}s -> {out}", flush=True)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Small sweep over k=l=3 two-block codes.")
    ap.add_argument("--depth", type=int, default=6)
    ap.add_argument("--timeout", type=float, default=600)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--proof", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    path = run_sweep(args.depth, args.timeout, args.workers, args.out, args.limit, args.proof)

    rows = list(csv.DictReader(open(path)))
    from collections import Counter
    per = Counter((r["max_multiplicity"], r["status"]) for r in rows)
    print("\nmax-multiplicity x status:")
    for (m, s), n in sorted(per.items()):
        print(f"  mult<={m}  {s:8} {n:5d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

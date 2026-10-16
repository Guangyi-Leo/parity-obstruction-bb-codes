"""Depth 6 for the two odd-order [[90,12,6]] instances of Supplement S8.

Both are class C1 with ord(d) odd, so no theorem settles them and the answer
has to come from the solver:

  Z45        A = {0,12,33}, B = {0,24,39}   -- never decided; the pysat run
                                               crashed, so S8 says nothing
  Z15 x Z3   A/B as in S8                   -- reported UNSAT by CaDiCaL at
                                               523 s with no proof logged

Each is re-run with kissat, DRAT logging on, and the proof checked by
drat-trim.  A capped run is recorded as UNKNOWN; it is never reported as
UNSAT.  Writes data/odd_order_certs.csv, resumable.
"""
from __future__ import annotations

import argparse
import csv
import os
import time

from .code import TwoBlockCode
from .solve import solve_instance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "odd_order_certs.csv")
COLS = ["instance", "group", "dims", "n", "k", "A", "B", "status", "time",
        "proof_bytes", "verified", "verify_time", "solver", "solver_version",
        "timeout", "run"]

TARGETS = [
    dict(instance="odd_Z45_C1_90_12_6", group="Z45", dims=[45], n=90, k=12,
         A=[(0,), (12,), (33,)], B=[(0,), (24,), (39,)]),
    dict(instance="odd_Z15xZ3_C1_90_12_6", group="Z15xZ3", dims=[15, 3],
         n=90, k=12, A=[(0, 0), (8, 2), (13, 1)], B=[(0, 0), (1, 1), (14, 2)]),
]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=float, default=7200.0)
    ap.add_argument("--verify-timeout", type=float, default=7200.0)
    ap.add_argument("--only", default=None, help="run one instance by name")
    a = ap.parse_args(argv)

    done = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            for r in csv.DictReader(f):
                done[r["instance"]] = r

    tg = [t for t in TARGETS if not a.only or t["instance"] == a.only]
    t0 = time.time()
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in done.values():
            w.writerow({k: r.get(k, "") for k in COLS})
        f.flush()
        for t in tg:
            if t["instance"] in done:
                print(f"  {t['instance']}: already on file", flush=True)
                continue
            code = TwoBlockCode(t["dims"], t["A"], t["B"], t["instance"])
            print(f"  {t['instance']}: solving depth 6, cap {a.timeout:.0f}s",
                  flush=True)
            res = solve_instance(code, 6, timeout=a.timeout, proof=True,
                                 tag="oddcert", record=False,
                                 verify_timeout=a.verify_timeout)
            row = dict(instance=t["instance"], group=t["group"],
                       dims=t["dims"], n=t["n"], k=t["k"], A=t["A"], B=t["B"],
                       status=res.get("status"), time=res.get("time"),
                       proof_bytes=res.get("proof_bytes"),
                       verified=res.get("verified"),
                       verify_time=res.get("verify_time", ""),
                       solver=res.get("solver"),
                       solver_version=res.get("solver_version"),
                       timeout=a.timeout, run="task6")
            w.writerow(row)
            f.flush()
            print(f"  {t['instance']:26} {row['status']:8} "
                  f"{str(row['verified']):13} {row['proof_bytes']} B  "
                  f"{row['time']}s   [{time.time()-t0:.0f}s]", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

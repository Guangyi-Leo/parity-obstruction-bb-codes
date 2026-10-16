"""Round 8 item 2: try to certify the 62 solver-reported UNSAT instances.

`data/coverage.csv` records 62 class-C1 instances whose depth-6 refutation came
from the solver alone -- UNSAT, but with no DRAT proof on file, so the claim
rests on trusting kissat.  This re-runs every one of them with DRAT logging at
a 600 s cap and checks each proof with drat-trim, so the ones that certify can
be moved from "solver-reported" to "certified".

Writes data/c1_odd_unobstructed_certs.csv, one row per instance *attempted*,
resumable: re-running picks up where it stopped.  Every row carries
`n_targets` (62) and `run`, so a partial file cannot be mistaken for a
complete pass -- an absent instance means "not attempted", never "failed".

Status: paused after 6 of 62 by request.  The six are all VERIFIED.
"""
from __future__ import annotations

import argparse
import ast
import csv
import os
import time

from .code import TwoBlockCode
from .solve import solve_instance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "c1_odd_unobstructed_certs.csv")
COLS = ["instance", "N", "A", "B", "status", "time", "proof_bytes",
        "verified", "verify_time", "solver", "solver_version", "timeout",
        "n_targets", "run"]


def _rows(name):
    p = os.path.join(DATA, name)
    with open(p) as f:
        return list(csv.DictReader(f))


def targets():
    """The 62, with their label sets."""
    names = [r["instance"] for r in _rows("coverage.csv")
             if r.get("in_sharpness_map") == "True"
             and r["status_math"] == "UNSAT-solver"]
    ab = {r["name"]: r for r in _rows("h2_sharpness.csv")}
    out = []
    for n in names:
        r = ab[n]
        out.append((n, int(r["N"]), ast.literal_eval(r["A"]),
                    ast.literal_eval(r["B"])))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=float, default=600.0)
    ap.add_argument("--verify-timeout", type=float, default=600.0)
    a = ap.parse_args(argv)

    done = {}
    if os.path.exists(OUT):
        for r in _rows(os.path.basename(OUT)):
            done[r["instance"]] = r
    tg = targets()
    print(f"{len(tg)} solver-reported UNSAT instances; {len(done)} already done",
          flush=True)
    t0 = time.time()
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in done.values():
            w.writerow({k: r.get(k, "") for k in COLS})
        f.flush()
        for i, (name, N, A, B) in enumerate(tg, 1):
            if name in done:
                continue
            code = TwoBlockCode([N], [tuple(x) for x in A],
                                [tuple(x) for x in B], name)
            res = solve_instance(code, 6, timeout=a.timeout, proof=True,
                                 tag="cert", record=False,
                                 verify_timeout=a.verify_timeout)
            row = dict(instance=name, N=N, A=A, B=B,
                       status=res.get("status"), time=res.get("time"),
                       proof_bytes=res.get("proof_bytes"),
                       verified=res.get("verified"),
                       verify_time=res.get("verify_time", ""),
                       solver=res.get("solver"),
                       solver_version=res.get("solver_version"),
                       timeout=a.timeout, n_targets=len(tg),
                       run="round8-partial")
            w.writerow(row)
            f.flush()
            print(f"  {i:3}/{len(tg)} {name:22} {row['status']:8} "
                  f"{str(row['verified']):13} {row['proof_bytes']} B  "
                  f"{row['time']}s   [{time.time()-t0:.0f}s]", flush=True)

    rows = _rows(os.path.basename(OUT))
    import collections
    print("\nstatus :", dict(collections.Counter(r["status"] for r in rows)))
    print("verified:", dict(collections.Counter(r["verified"] for r in rows)))
    ok = [r for r in rows if r["verified"] == "VERIFIED"]
    if ok:
        mb = sorted(int(r["proof_bytes"]) / 1e6 for r in ok)
        print(f"certified {len(ok)}/{len(rows)}; proof size "
              f"min {mb[0]:.2f} MB, median {mb[len(mb)//2]:.2f} MB, "
              f"max {mb[-1]:.2f} MB, total {sum(mb):.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""P0 -- per-instance minimal-period scan on the REDUCED twisted system.

For each class-C1 instance the reduced system has 2*Delta*m label variables (12m for
k = l = 3) plus corner variables, with constraints indexed by eps-classes; it never
touches the expanded 2N*Delta-edge instance.  Scanning rules:

  * only proper divisors m | N with m < N (m = N is the original solver status);
  * ord(d) even -> start at m0 = 2^(v2(d)+1); every smaller divisor fails to separate
    d, and odd divisors cannot work, so m0 is the smallest candidate.  Stop at the
    first m that admits;
  * ord(d) odd -> scan every proper divisor, odd ones included;
  * every solver call is capped in wall clock; a capped call is recorded UNKNOWN for
    that (instance, m) and never retried in this run.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

from .code import TwoBlockCode
from .solve import DATA

FIELDS = ["instance", "N", "status", "theorem1_obstructed", "ord_d", "ord_d_even",
          "v2_d", "m", "exists", "eps_found", "n_homs", "n_unknown", "seconds",
          "scan_index"]


def v2(n: int) -> int:
    if n == 0:
        return 10 ** 9
    v = 0
    while n % 2 == 0:
        n //= 2
        v += 1
    return v


def proper_divisors(N: int) -> list[int]:
    return [m for m in range(2, N) if N % m == 0]


def scan_order(N: int, d: int, ord_d: int) -> list[int]:
    ds = proper_divisors(N)
    if ord_d % 2 == 0:
        m0 = 2 ** (v2(d) + 1)
        return [m for m in ds if m >= m0]
    return ds


def _one(job) -> list[dict]:
    from .encode import UNKNOWN, find_twisted_invariant_schedule_Zm, homomorphisms_to_Zm
    from .simulate import is_proper_by_simulation, is_valid_layering
    row, depth, cap = job
    N = int(row["N"])
    d = json.loads(row["d"])[0] % N
    ord_d = int(row["ord_d"])
    code = TwoBlockCode((N,), [tuple(a) for a in json.loads(row["A"])],
                        [tuple(b) for b in json.loads(row["B"])], row["instance"])
    out = []
    for idx, m in enumerate(scan_order(N, d, ord_d)):
        t0 = time.time()
        found, unk, nh = None, 0, 0
        for h in homomorphisms_to_Zm(code.G, m):
            nh += 1
            res = find_twisted_invariant_schedule_Zm(code, depth, h["coeffs"], m,
                                                     timeout=cap)
            if res == UNKNOWN:
                unk += 1
                continue
            if res is not None:
                lay = res[1]
                if not (is_valid_layering(code, lay, depth)
                        and is_proper_by_simulation(code, lay, depth)):
                    raise AssertionError(
                        f"{row['instance']} m={m}: twisted schedule failed verification")
                found = h["name"]
                break
        exists = True if found else ("UNKNOWN" if unk else False)
        out.append(dict(instance=row["instance"], N=N, status=row["status"],
                        theorem1_obstructed=row.get("theorem1_obstructed", ""),
                        ord_d=ord_d, ord_d_even=(ord_d % 2 == 0), v2_d=v2(d), m=m,
                        exists=exists, eps_found=found or "", n_homs=nh,
                        n_unknown=unk, seconds=round(time.time() - t0, 2),
                        scan_index=idx))
        if found:
            break                       # m* found; larger divisors are irrelevant
    return out


def run(depth: int = 6, cap: float = 60.0, workers: int = 20,
        feat: str | None = None, out: str | None = None,
        limit: int | None = None, start: int = 0) -> str:
    feat = feat or os.path.join(DATA, "h4_features.csv")
    out = out or os.path.join(DATA, "h4_mstar_scan.csv")
    rows = list(csv.DictReader(open(feat)))[start:]
    if limit:
        rows = rows[:limit]
    done = set()
    if os.path.exists(out):
        done = {r["instance"] for r in csv.DictReader(open(out))}
    todo = [r for r in rows if r["instance"] not in done]
    print(f"P0 divisor scan: {len(todo)} of {len(rows)} instances to do "
          f"({len(done)} already recorded); {cap:.0f}s cap per solver call; "
          f"{workers} workers", flush=True)
    if not todo:
        print("  nothing to do")
        return out
    new = not os.path.exists(out)
    fh = open(out, "a", newline="")
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    if new:
        w.writeheader()
        fh.flush()
    t0, n, nrows, unk = time.time(), 0, 0, 0
    try:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(_one, (r, depth, cap)) for r in todo]
            for fut in as_completed(futs):
                for rec in fut.result():
                    w.writerow(rec)
                    nrows += 1
                    unk += rec["n_unknown"]
                fh.flush()
                n += 1
                if n % 50 == 0 or n == len(todo):
                    print(f"  [{n:4d}/{len(todo)}] {nrows} rows, {unk} capped calls, "
                          f"{time.time()-t0:.0f}s", flush=True)
    finally:
        fh.close()
    print(f"wrote {out} (+{nrows} rows, {unk} capped solver calls)")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cap", type=float, default=60.0)
    ap.add_argument("--workers", type=int, default=20)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--start", type=int, default=0)
    a = ap.parse_args(argv)
    run(cap=a.cap, workers=a.workers, limit=a.limit, start=a.start)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

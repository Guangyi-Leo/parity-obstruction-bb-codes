"""B2: twisted schedules outside class C1.

For every SAT instance of class C2 or SG in data/h2_sharpness.csv, search for a
Z_m-twisted depth-6 schedule for each proper divisor m | N (and m = N), over every
non-trivial homomorphism eps: G -> Z_m, with a wall-clock cap per (instance, m, eps).
Every schedule found must have |M| even, where M = <alpha_s - alpha_s', beta_t -
beta_t'> <= Z_m.  Writes data/b2_twisted_outside_c1.csv.
"""
from __future__ import annotations

import argparse
import ast
import csv
import os
import time

from .code import TwoBlockCode
from .encode import (UNKNOWN, eps_value_m, find_twisted_invariant_schedule_Zm,
                     homomorphisms_to_Zm)
from .simulate import is_proper_by_simulation
from .twisted_identity import subgroup_M

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "b2_twisted_outside_c1.csv")
DEPTH = 6
FIELDS = ["instance", "klass", "N", "m", "eps", "result", "abs_M", "M_parity",
          "proper", "seconds"]


def divisors(n: int) -> list[int]:
    return [d for d in range(2, n + 1) if n % d == 0]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=float, default=120.0, help="s per (instance, m)")
    a = ap.parse_args(argv)

    with open(os.path.join(DATA, "h2_sharpness.csv")) as f:
        sharp = list(csv.DictReader(f))
    todo = [r for r in sharp
            if ("SG" if r["class"] == "subgroup" else r["class"]) in ("C2", "SG")
            and r["status"] == "SAT"]
    print(f"  {len(todo)} SAT instances of class C2 or SG")

    rows, found, odd = [], [], []
    for r in todo:
        n = r["name"]
        N = int(r["N"])
        code = TwoBlockCode((N,), [tuple(x) for x in ast.literal_eval(r["A"])],
                            [tuple(x) for x in ast.literal_eval(r["B"])], n)
        klass = "SG" if r["class"] == "subgroup" else r["class"]
        for m in divisors(N):
            t0 = time.time()
            budget = a.cap
            for h in homomorphisms_to_Zm(code.G, m):
                if h["trivial"]:
                    continue
                left = budget - (time.time() - t0)
                if left <= 0:
                    rows.append(dict(instance=n, klass=klass, N=N, m=m,
                                     eps=h["name"], result="capped", abs_M="",
                                     M_parity="", proper="",
                                     seconds=round(time.time() - t0, 2)))
                    break
                res = find_twisted_invariant_schedule_Zm(code, DEPTH, h["coeffs"], m,
                                                         timeout=left)
                if res is UNKNOWN or res == UNKNOWN:
                    continue
                if res is None:
                    continue
                labels, lay = res
                ea = [eps_value_m(h["coeffs"], x, m) for x in code.A]
                eb = [eps_value_m(h["coeffs"], x, m) for x in code.B]
                Ms = subgroup_M(ea, eb, m)
                proper = is_proper_by_simulation(code, lay, DEPTH)
                rec = dict(instance=n, klass=klass, N=N, m=m, eps=h["name"],
                           result="found", abs_M=Ms,
                           M_parity="even" if Ms % 2 == 0 else "odd",
                           proper=proper, seconds=round(time.time() - t0, 2))
                rows.append(rec)
                found.append(rec)
                if Ms % 2:
                    odd.append(rec)
                assert proper, f"{n} m={m} {h['name']}: schedule is not proper"
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader(); w.writerows(rows)
    print(f"  wrote {os.path.relpath(OUT, ROOT)}: {len(rows)} rows")
    Ms = sorted({r["abs_M"] for r in found})
    print(f"  twisted schedules found: {len(found)} over "
          f"{len({r['instance'] for r in found})} instances")
    print(f"  |M| values: {Ms} ({len(Ms)} distinct); with |M| odd: {len(odd)}")
    for r in odd[:5]:
        print(f"    ODD |M| {r['instance']} m={r['m']} {r['eps']} |M|={r['abs_M']}")
    return 1 if odd else 0


if __name__ == "__main__":
    raise SystemExit(main())

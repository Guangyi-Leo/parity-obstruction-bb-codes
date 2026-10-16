"""R6 -- periodicity classification of the validated schedules.

Given a concrete schedule, asking whether it is eps-twisted invariant is a direct
consistency check, not a search: the schedule is twisted for eps iff lay(e) is constant
on every class (kind, side, label, eps(check)).  So this module needs no solver; the
30 s cap is kept only as a guard.

Classes:
  invariant           lay depends on the label alone (eps trivial)
  twisted(m)          lay = f(label, eps(g)) for some eps: G -> Z_m, m | N proper
  other               no proper divisor m | N and homomorphism eps was found for which
                      the schedule is eps-twisted invariant
"""
from __future__ import annotations

import csv
import json
import os
import time
from collections import Counter, defaultdict

from .code import TwoBlockCode
from .encode import eps_value_m, homomorphisms_to_Zm
from .solve import DATA, ROOT

SCHED = os.path.join(ROOT, "schedules")
FIELDS = ["instance", "solution", "N", "D", "klass", "m", "eps", "n_divisors_tested",
          "seconds"]


def is_twisted_for(code: TwoBlockCode, lay, coeffs, m: int) -> bool:
    """lay constant on every (kind, side, label, eps(check)) class?"""
    seen: dict[tuple, int] = {}
    for e in code.edges:
        eg = eps_value_m(coeffs, code.G.elements[e.check], m)
        k = (e.kind, e.side, e.lab, eg)
        v = lay[e.eid]
        if k in seen:
            if seen[k] != v:
                return False
        else:
            seen[k] = v
    return True


def classify(code: TwoBlockCode, lay, cap: float = 30.0) -> dict:
    t0 = time.time()
    N = code.N
    if is_twisted_for(code, lay, tuple(0 for _ in code.G.dims), 1):
        return dict(klass="invariant", m=1, eps="trivial", n_divisors_tested=0,
                    seconds=round(time.time() - t0, 3))
    tested = 0
    for m in [x for x in range(2, N) if N % x == 0]:
        for h in homomorphisms_to_Zm(code.G, m):
            if h["trivial"]:
                continue
            tested += 1
            if time.time() - t0 > cap:
                return dict(klass="UNKNOWN (cap)", m="", eps="",
                            n_divisors_tested=tested,
                            seconds=round(time.time() - t0, 3))
            if is_twisted_for(code, lay, h["coeffs"], m):
                return dict(klass="twisted", m=m, eps=h["name"],
                            n_divisors_tested=tested,
                            seconds=round(time.time() - t0, 3))
    return dict(klass="other", m="", eps="", n_divisors_tested=tested,
                seconds=round(time.time() - t0, 3))


def run(cap: float = 30.0, out: str | None = None) -> str:
    out = out or os.path.join(DATA, "r6_periodicity.csv")
    files = sorted(f for f in os.listdir(SCHED) if f.endswith("_enum.json"))
    rows = []
    for f in files:
        rec = json.load(open(os.path.join(SCHED, f)))
        code = TwoBlockCode(tuple(rec["dims"]), [tuple(a) for a in rec["A"]],
                            [tuple(b) for b in rec["B"]], rec["instance"])
        for i, lay in enumerate(rec["solutions"]):
            c = classify(code, lay, cap)
            rows.append(dict(instance=rec["instance"], solution=i, N=code.N,
                             D=rec["D"], **c))
        print(f"  {rec['instance']:8} {len(rec['solutions']):4d} schedules  "
              f"{dict(Counter(r['klass'] for r in rows if r['instance']==rec['instance']))}",
              flush=True)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    tally = Counter(r["klass"] for r in rows)
    print(f"\nR6: {len(rows)} validated schedules -> {dict(tally)}")
    # lemma pass rate on the "other" subset
    lem = {(r["instance"], int(r["solution"])): r
           for r in csv.DictReader(open(os.path.join(DATA, "lemma_checks.csv")))}
    LEM = ["L1", "L2", "L3", "L4", "L5", "L6", "L7"]
    for sub in ("other", "twisted", "invariant"):
        sel = [lem[(r["instance"], r["solution"])] for r in rows
               if r["klass"] == sub and (r["instance"], r["solution"]) in lem]
        if not sel:
            print(f"  {sub:10}: no schedules")
            continue
        rates = {L: sum(1 for x in sel if x[L] == "True") / len(sel) for L in LEM}
        allp = sum(1 for x in sel if x["all_pass"] == "True")
        print(f"  {sub:10}: {len(sel):4d} schedules, L1-L7 pass "
              + " ".join(f"{L}={100*rates[L]:.0f}%" for L in LEM)
              + f", all={100*allp/len(sel):.0f}%")
    print(f"wrote {out}")
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cap", type=float, default=30.0)
    a = ap.parse_args()
    run(a.cap)

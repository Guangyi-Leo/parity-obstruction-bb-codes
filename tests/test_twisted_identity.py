"""sum_{c in coset} (F_L(c)+F_R(c)) = |M| k l, on every twisted witness and template.

Witnesses: each class-C1 instance that data/mstar.csv records as carrying a twisted
schedule is re-solved at its m*, the homomorphism eps that admits it is stored in the
schedule JSON alongside m, and the identity is checked over the cosets of M in eps(G).
Templates: the same, from the label tables of the template solutions.

`--full` walks every admissible template key (about 25 minutes); the default samples
`--sample` keys per modulus so the test stays fast.  Writes data/twisted_identity.csv.
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from twoblock.code import TwoBlockCode                                   # noqa: E402
from twoblock.encode import (                                            # noqa: E402
    eps_value_m, find_twisted_invariant_schedule_Zm, homomorphisms_to_Zm,
    solve_twisted_system,
)
from twoblock.simulate import is_proper_by_simulation                    # noqa: E402
from twoblock.templates import DEPTH, K, L, deltas_for, load             # noqa: E402
from twoblock.twisted_identity import (                                  # noqa: E402
    OUT, check_labels, f_from_labels, subgroup_M, write,
)

DATA = os.path.join(ROOT, "data")
SCHED = os.path.join(ROOT, "schedules")
SEED = 7


def _read(name):
    with open(os.path.join(DATA, name)) as f:
        return list(csv.DictReader(f))


def _parse_key(kk):
    head, sa, sb = kk.split("|")
    p, q = head.split("-")
    return (((int(p[0]), int(p[1])), (int(q[0]), int(q[1]))),
            [int(x) for x in sa.split(",")], [int(x) for x in sb.split(",")])


# ------------------------------------------------------------------ witnesses
def witnesses(limit=None):
    feats = {r["instance"]: r for r in _read("h4_features.csv")}
    rows, stored, bad = [], 0, []
    todo = [r for r in _read("mstar.csv") if r["m_star_kind"] == "found"]
    if limit:
        todo = todo[:limit]
    for r in todo:
        n = r["instance"]
        f = feats.get(n)
        if not f:
            continue
        m = int(r["m_star"])
        dims = tuple(int(p[1:]) for p in f["group"].split("x"))
        code = TwoBlockCode(dims, [tuple(a) for a in ast.literal_eval(f["A"])],
                            [tuple(b) for b in ast.literal_eval(f["B"])], n)
        got = None
        for h in homomorphisms_to_Zm(code.G, m):
            if h["trivial"]:
                continue
            res = find_twisted_invariant_schedule_Zm(code, DEPTH, h["coeffs"], m)
            if res is not None and res != "unknown" and not isinstance(res, str):
                got = (h, res)
                break
        if got is None:
            bad.append((n, m, "no eps admits at m*"))
            continue
        h, (labels, lay) = got
        assert is_proper_by_simulation(code, lay, DEPTH), f"{n}: witness not proper"
        ea = [eps_value_m(h["coeffs"], a, m) for a in code.A]
        eb = [eps_value_m(h["coeffs"], b, m) for b in code.B]
        image = sorted({eps_value_m(h["coeffs"], g, m) for g in code.G.elements})
        # store eps and m next to the witness
        p = os.path.join(SCHED, f"{n}_d{DEPTH}_twisted_m{m}.json")
        with open(p, "w") as fh:
            json.dump(dict(instance=n, dims=list(dims), A=[list(a) for a in code.A],
                           B=[list(b) for b in code.B], D=DEPTH, m=m,
                           eps_coeffs=list(h["coeffs"]), eps_name=h["name"],
                           eps_image=image, eps_on_A=ea, eps_on_B=eb,
                           abs_M=subgroup_M(ea, eb, m), layers=lay,
                           proper_by_simulation=True), fh)
        stored += 1
        # cross-check the label formula against the expanded layering
        FL_lab = {c: f_from_labels(labels, ea, eb, m, c) for c in image}
        rows += check_labels("witness", n, labels, ea, eb, m, code.k, code.l, image)
        del FL_lab
    return rows, stored, bad


# ------------------------------------------------------------------ templates
def templates(sample=None, ms=(2, 3, 4, 5, 6, 8)):
    rng = random.Random(SEED)
    rows, n_keys = [], 0
    for m in ms:
        rec = load(m)
        if rec is None:
            continue
        sat = sorted(rec["sat_set"])
        if not sat:
            continue
        keys = sat if sample is None else rng.sample(sat, min(sample, len(sat)))
        for kk in keys:
            pat, ea, eb = _parse_key(kk)
            lab = solve_twisted_system(K, L, ea, eb, deltas_for(pat, ea, eb, m),
                                       list(range(m)), DEPTH, m)
            assert lab is not None, f"m={m}: admissible key {kk} is unsatisfiable"
            rows += check_labels("template", kk, lab, ea, eb, m, K, L)
            n_keys += 1
    return rows, n_keys


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="every admissible key")
    ap.add_argument("--sample", type=int, default=40, help="keys per modulus")
    ap.add_argument("--witness-limit", type=int, default=None)
    ap.add_argument("--out", default=None,
                    help="where to write; the sampled run must not overwrite the "
                         "exhaustive record in data/twisted_identity.csv")
    a = ap.parse_args(argv)

    t0 = time.time()
    wrows, stored, bad = witnesses(a.witness_limit)
    assert not bad, f"witness recovery failed for {bad[:5]}"
    trows, n_keys = templates(None if a.full else a.sample)
    rows = wrows + trows
    out = a.out or (OUT if a.full
                    else os.path.join(DATA, "twisted_identity_sample.csv"))
    write(rows, out)

    n_bad = [r for r in rows if not r["equal"]]
    wm = {r["name"]: r["abs_M"] for r in wrows}
    odd = {n: v for n, v in wm.items() if v % 2}
    print(f"[wrote {os.path.relpath(out, ROOT)}: {len(rows)} cosets from "
          f"{len(wm)} witnesses and {n_keys} template keys, "
          f"{time.time() - t0:.0f} s]")
    print(f"B1 stored eps and m alongside {stored} twisted witnesses in schedules/")
    assert not n_bad, f"identity fails on {n_bad[:5]}"
    print(f"B1 identity sum_coset (F_L+F_R) = |M| k l holds on all {len(rows)} cosets")
    print(f"B1 |M| over the witnesses: {sorted(set(wm.values()))}; "
          f"odd |M|: {len(odd)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

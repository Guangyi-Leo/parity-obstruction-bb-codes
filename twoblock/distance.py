"""H3 (optional) -- randomised information-set-decoding distance upper bounds.

For a CSS code with parity checks H_X and H_Z, a non-trivial logical Z operator is a
vector in ker(H_X) that is not in the row space of H_Z, and symmetrically for X.
The distance is the minimum weight over both families.  Finding it exactly is hard,
so this reports an **upper bound**: repeatedly permute the columns at random, put a
basis of ker(H_X) into reduced row echelon form under that column order, and keep the
lightest row that is still a non-trivial logical.  Random pairwise sums of reduced
rows are also tried.  Seeded with 7.

Every number produced here is an upper bound and is labelled as such.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import time

import numpy as np

from .code import TwoBlockCode
from .solve import DATA

SEED = 7
FIELDS = ["instance", "N", "class", "status", "selection", "n_qubits", "k_logical",
          "dX_upper", "dZ_upper", "d_upper", "trials", "time_s", "method", "reason"]


def rref(M: np.ndarray):
    """Row-reduced echelon form over F2; returns (rows, pivot columns)."""
    M = (np.asarray(M) % 2).astype(np.uint8).copy()
    nrows, ncols = M.shape
    piv, r = [], 0
    for c in range(ncols):
        pr = None
        for i in range(r, nrows):
            if M[i, c]:
                pr = i
                break
        if pr is None:
            continue
        if pr != r:
            M[[r, pr]] = M[[pr, r]]
        col = M[:, c].copy()
        col[r] = 0
        M[col == 1] ^= M[r]
        piv.append(c)
        r += 1
        if r == nrows:
            break
    return M[:r], piv


def nullspace(M: np.ndarray) -> np.ndarray:
    """Basis of {v : M v^T = 0} over F2, as rows."""
    M = (np.asarray(M) % 2).astype(np.uint8)
    ncols = M.shape[1]
    R, piv = rref(M)
    free = [c for c in range(ncols) if c not in piv]
    out = np.zeros((len(free), ncols), dtype=np.uint8)
    for i, f in enumerate(free):
        out[i, f] = 1
        for j, p in enumerate(piv):
            out[i, p] = R[j, f]
    return out


def _isd_bound(ker: np.ndarray, stab: np.ndarray, trials: int, rng) -> int | None:
    """Lightest vector of `ker` outside rowspace(`stab`) seen over random column orders."""
    if ker.shape[0] == 0:
        return None
    S, spiv = rref(stab)

    def trivial(v: np.ndarray) -> bool:
        w = v.copy()
        for j, p in enumerate(spiv):
            if w[p]:
                w ^= S[j]
        return not w.any()

    n = ker.shape[1]
    best = None
    for _ in range(trials):
        perm = rng.permutation(n)
        R, _ = rref(ker[:, perm])
        inv = np.empty(n, dtype=int)
        inv[perm] = np.arange(n)
        rows = R[:, inv]
        cand = list(rows)
        if rows.shape[0] >= 2:                     # a few random pairwise sums
            idx = rng.integers(0, rows.shape[0], size=(min(8, rows.shape[0]), 2))
            cand += [rows[i] ^ rows[j] for i, j in idx if i != j]
        for v in cand:
            w = int(v.sum())
            if w == 0 or (best is not None and w >= best):
                continue
            if not trivial(v):
                best = w
    return best


def distance_upper_bound(code: TwoBlockCode, trials: int = 2000, seed: int = SEED):
    rng = np.random.default_rng(seed)
    Hx, Hz = code.H_X(), code.H_Z()
    dZ = _isd_bound(nullspace(Hx), Hz, trials, rng)      # logical Z: ker(Hx) \ rs(Hz)
    dX = _isd_bound(nullspace(Hz), Hx, trials, rng)      # logical X: ker(Hz) \ rs(Hx)
    both = [d for d in (dX, dZ) if d is not None]
    return dX, dZ, (min(both) if both else None)


def validate(trials: int = 300) -> list[tuple]:
    """Reproduce published distances of the IBM codes as a check on the ISD routine."""
    from . import instances as _inst
    known = {"bb72": 6, "bb90": 10, "bb108": 10, "bb144": 12}
    out = []
    for nm, d in known.items():
        _, _, got = distance_upper_bound(_inst.get(nm), trials)
        out.append((nm, got, d, got == d))
        print(f"  validate {nm}: ISD d<={got}, published d={d}  "
              f"{'match' if got == d else 'MISMATCH'}", flush=True)
    return out


def run(trials: int = 2000, out: str | None = None) -> str:
    out = out or os.path.join(DATA, "h3_distance.csv")
    src = os.path.join(DATA, "h2_sharpness.csv")
    if not os.path.exists(src):
        raise SystemExit("data/h2_sharpness.csv missing; run `make h2` first")
    h2 = list(csv.DictReader(open(src)))

    def build(r):
        return TwoBlockCode((int(r["N"]),), [tuple(a) for a in json.loads(r["A"])],
                            [tuple(b) for b in json.loads(r["B"])], r["name"])

    spec = [(r, "specified") for r in h2
            if r["class"] == "C1" and r["status"] == "SAT" and int(r["N"]) in (16, 20, 24)]
    chosen = {r["name"] for r, _ in spec}
    # supplementary: any H2 instance that actually encodes something
    supp = [(r, "supplementary") for r in h2
            if r["name"] not in chosen and r["status"] == "SAT" and build(r).logical_k() > 0]
    print(f"H3: {len(spec)} specified instances (class C1, SAT, N in 16/20/24) "
          f"+ {len(supp)} supplementary (any SAT H2 instance with k>0), "
          f"{trials} ISD trials each", flush=True)

    rows = []
    for r, sel in spec + supp:
        code = build(r)
        k = code.logical_k()
        if k == 0:
            rows.append(dict(instance=r["name"], N=int(r["N"]), **{"class": r["class"]},
                             status=r["status"], selection=sel, n_qubits=2 * code.N,
                             k_logical=0, dX_upper="", dZ_upper="", d_upper="",
                             trials=0, time_s=0.0, method="randomised ISD (upper bound)",
                             reason="k=0: the code encodes no logical qubits, so there "
                                    "is no logical operator and no distance"))
            print(f"  {r['name']:14} [[{2*code.N},0,--]]  k=0, distance undefined",
                  flush=True)
            continue
        t0 = time.time()
        dX, dZ, d = distance_upper_bound(code, trials)
        el = time.time() - t0
        rows.append(dict(instance=r["name"], N=int(r["N"]), **{"class": r["class"]},
                         status=r["status"], selection=sel, n_qubits=2 * code.N,
                         k_logical=k, dX_upper=dX, dZ_upper=dZ, d_upper=d,
                         trials=trials, time_s=round(el, 2),
                         method="randomised ISD (upper bound)", reason=""))
        print(f"  {r['name']:14} [[{2*code.N},{k},<={d}]]  dX<={dX} dZ<={dZ} "
              f"({el:.1f}s)  [{sel}]", flush=True)

    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    nz = [r for r in rows if r["k_logical"]]
    print(f"\n{len(rows)} instances; {len(nz)} have k>0 and a distance bound.")
    if not any(r["selection"] == "specified" and r["k_logical"] for r in rows):
        print("NOTE: every instance in the specified selection has k=0, so the "
              "experiment yields no distance for them. Reported as such, not omitted.")
    print("\nvalidation of the ISD routine against published distances:")
    validate()
    print(f"wrote {out}")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="H3 distance upper bounds.")
    ap.add_argument("--trials", type=int, default=2000)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    run(a.trials, a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

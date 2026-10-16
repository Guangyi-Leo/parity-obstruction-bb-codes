"""H2 -- sharpness of the depth-Delta obstruction at larger N.

Groups Z_N for N in {10,12,14,16,18,20,24}, k = l = 3, depth 6.  Candidates (A, B)
with a_1 = b_1 = 0 are drawn uniformly at random (seed 7) and classified by the
multiplicity histogram of the nine sums a_s + b_t:

    D  = distinct sums                 histogram {1: 9}
    C1 = exactly one coincidence       histogram {1: 7, 2: 1}
    C2 = {1: 5, 2: 2} or {1: 6, 3: 1}

Four instances are kept per class per N (a class is skipped if fewer exist).  The
subgroup instances A = B = {0, N/3, 2N/3} are added for N in {12, 18}.

Every SAT model is re-checked by F2 simulation and the run aborts if one fails.
Like the sweep, the case list is fanned out over a process pool; each individual
solver invocation is single-threaded.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed

from .code import TwoBlockCode
from .components import summary as comp_summary
from .encode import encode
from .simulate import is_proper_by_simulation, is_valid_layering
from .solve import CERTS, DATA, LOGS, run_solver, verify_proof

SEED = 7
NS = [10, 12, 14, 16, 18, 20, 24]
CLASSES = ["D", "C1", "C2"]
PER_CLASS = 4
SUBGROUP_NS = [12, 18]

FIELDS = ["name", "N", "class", "A", "B", "hist", "distinct_sums", "theorem1_obstructed",
          "n_components", "min_component_n", "status", "time_s", "proper_sim",
          "D_depth", "nvars", "nclauses", "proof_bytes", "verified"]


def classify(hist: dict[int, int]) -> str | None:
    h = {int(k): int(v) for k, v in hist.items()}
    if h == {1: 9}:
        return "D"
    if h == {1: 7, 2: 1}:
        return "C1"
    if h in ({1: 5, 2: 2}, {1: 6, 3: 1}):
        return "C2"
    return None


def _hist_of(N: int, A, B) -> dict[int, int]:
    sums = Counter(((a[0] + b[0]) % N) for a in A for b in B)
    return dict(sorted(Counter(sums.values()).items()))


def sample_instances(seed: int = SEED, draws: int = 200000) -> list[dict]:
    """Random (A, B) with a_1 = b_1 = 0, up to PER_CLASS kept per (N, class)."""
    rng = random.Random(seed)
    out: list[dict] = []
    for N in NS:
        keep: dict[str, list] = {c: [] for c in CLASSES}
        seen: set[tuple] = set()
        for _ in range(draws):
            if all(len(v) >= PER_CLASS for v in keep.values()):
                break
            A = tuple(sorted([(0,)] + [(x,) for x in rng.sample(range(1, N), 2)]))
            B = tuple(sorted([(0,)] + [(x,) for x in rng.sample(range(1, N), 2)]))
            if (A, B) in seen:
                continue
            seen.add((A, B))
            hist = _hist_of(N, A, B)
            cls = classify(hist)
            if cls and len(keep[cls]) < PER_CLASS:
                keep[cls].append((A, B, hist))
        for cls in CLASSES:
            for i, (A, B, hist) in enumerate(keep[cls]):
                out.append(dict(N=N, cls=cls, A=[list(a) for a in A], B=[list(b) for b in B],
                                hist=hist, name=f"h2_Z{N}_{cls}_{i}"))
    for N in SUBGROUP_NS:
        A = [[0], [N // 3], [2 * N // 3]]
        out.append(dict(N=N, cls="subgroup", A=A, B=list(A), hist=_hist_of(N, A, A),
                        name=f"h2_Z{N}_subgroup"))
    return out


def _build(spec) -> TwoBlockCode:
    return TwoBlockCode((spec["N"],), [tuple(a) for a in spec["A"]],
                        [tuple(b) for b in spec["B"]], spec["name"])


def _one(job) -> dict:
    spec, depth, timeout = job
    code = _build(spec)
    code.check_structure()
    cs = comp_summary(code)
    enc = encode(code, depth)
    d = os.path.join(CERTS, "h2")
    os.makedirs(d, exist_ok=True)
    cnf = os.path.join(d, f"{spec['name']}_d{depth}.cnf")
    enc.write_dimacs(cnf)
    res = run_solver(cnf, None, timeout=timeout)
    row = dict(name=spec["name"], N=spec["N"], **{"class": spec["cls"]},
               A=json.dumps(spec["A"]), B=json.dumps(spec["B"]),
               hist=json.dumps(spec["hist"]), distinct_sums=code.distinct_sums(),
               theorem1_obstructed=cs["theorem1_obstructed"],
               n_components=cs["n_components"], min_component_n=cs["min_component_n"],
               status=res.status, time_s=round(res.time, 3), proper_sim="",
               D_depth=depth, nvars=enc.nvars, nclauses=len(enc.clauses),
               proof_bytes=0, verified="")
    if res.status == "SAT":
        lay = enc.decode_model(res.model)
        if not is_valid_layering(code, lay, depth):
            raise AssertionError(f"{spec['name']}: SAT model violates vertex distinctness")
        if not is_proper_by_simulation(code, lay, depth):
            raise AssertionError(
                f"{spec['name']}: SAT model FAILS F2 simulation -- aborting H2")
        row["proper_sim"] = True
        sp = os.path.join(os.path.dirname(CERTS), "schedules", f"{spec['name']}_d{depth}.json")
        with open(sp, "w") as f:
            json.dump({"instance": spec["name"], "dims": [spec["N"]], "A": spec["A"],
                       "B": spec["B"], "D": depth, "layers": lay,
                       "proper_by_simulation": True}, f)
    os.remove(cnf)
    return row


def run(depth: int = 6, timeout: float = 1800, workers: int = 20,
        out: str | None = None) -> str:
    out = out or os.path.join(DATA, "h2_sharpness.csv")
    specs = sample_instances()
    print(f"H2: {len(specs)} instances (N in {NS}, classes {CLASSES} + subgroup), "
          f"depth {depth}, timeout {timeout:.0f}s, {workers} workers", flush=True)
    by = Counter((s["N"], s["cls"]) for s in specs)
    missing = [(N, c) for N in NS for c in CLASSES if by[(N, c)] < PER_CLASS]
    if missing:
        print(f"  classes with fewer than {PER_CLASS} instances: "
              f"{[(N, c, by[(N,c)]) for N, c in missing]}", flush=True)

    rows, t0 = [], time.time()
    os.makedirs(DATA, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(_one, (s, depth, timeout)) for s in specs]
            for fut in as_completed(futs):
                row = fut.result()
                rows.append(row)
                w.writerow(row)
                f.flush()
                print(f'  [{len(rows):3d}/{len(specs)}] {row["name"]:22} '
                      f'{row["class"]:8} {row["status"]:8} {row["time_s"]:9.2f}s', flush=True)
    print(f"H2 solved in {time.time()-t0:.0f}s", flush=True)

    # certificates: one DRAT for an UNSAT class-D instance at N = 10 and N = 24
    for N in (10, 24):
        cand = [r for r in rows if r["N"] == N and r["class"] == "D" and r["status"] == "UNSAT"]
        if not cand:
            print(f"  no UNSAT class-D instance at N={N}; no certificate produced", flush=True)
            continue
        r = sorted(cand, key=lambda x: x["name"])[0]
        spec = next(s for s in specs if s["name"] == r["name"])
        code = _build(spec)
        enc = encode(code, depth)
        d = os.path.join(CERTS, "h2")
        cnf = os.path.join(d, f"{spec['name']}_d{depth}.cnf")
        drat = os.path.join(d, f"{spec['name']}_d{depth}.drat")
        enc.write_dimacs(cnf)
        res = run_solver(cnf, drat, timeout=timeout)
        verdict, vt, _ = verify_proof(cnf, drat)
        r["proof_bytes"] = res.proof_bytes
        r["verified"] = verdict
        with open(os.path.join(LOGS, f"{spec['name']}_d{depth}.log"), "w") as f:
            f.write(f"cmd={res.cmd}\nstatus={res.status} time={res.time:.2f}\n"
                    f"proof_bytes={res.proof_bytes} verified={verdict} verify_s={vt:.2f}\n")
        print(f"  certificate {spec['name']}: {res.status}, "
              f"{res.proof_bytes/1e6:.1f} MB, drat-trim {verdict} ({vt:.1f}s)", flush=True)

    with open(out, "w", newline="") as f:                 # rewrite with proof columns
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["N"], r["class"], r["name"])))

    tally = Counter((r["class"], r["status"]) for r in rows)
    print("\nclass x status:")
    for (c, s), n in sorted(tally.items()):
        print(f"  {c:9} {s:9} {n:3d}")
    bad = [r for r in rows if r["theorem1_obstructed"] and r["status"] == "SAT"]
    if bad:
        print(f"\nSTOP: Theorem-1-obstructed instances came back SAT: {[r['name'] for r in bad]}")
    print(f"wrote {out}")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="H2 sharpness experiment.")
    ap.add_argument("--depth", type=int, default=6)
    ap.add_argument("--timeout", type=float, default=1800)
    ap.add_argument("--workers", type=int, default=20)
    ap.add_argument("--out", default=None)
    ap.add_argument("--h4", action="store_true",
                    help="run the H4 extension (30 class-C1 per N over a wider N range) "
                         "and append to data/h2_sharpness.csv")
    a = ap.parse_args(argv)
    if a.h4:
        run_h4(a.depth, a.timeout, a.workers, a.out)
    else:
        run(a.depth, a.timeout, a.workers, a.out)
    return 0




# ---------------------------------------------------------------------------
# H4 step 1: extend the class-C1 sample to N in 10..24 and 28,30,32,36.
# Rows are appended to data/h2_sharpness.csv with class "C1"; names carry an
# h4_ prefix so the extension stays identifiable.
# ---------------------------------------------------------------------------
H4_NS = list(range(10, 25)) + [28, 30, 32, 36]
H4_PER_N = 30


def sample_c1(N: int, count: int, rng, exclude: set) -> list[dict]:
    """`count` distinct class-C1 (A, B) over Z_N with a_1 = b_1 = 0."""
    out, seen = [], set(exclude)
    tries = 0
    while len(out) < count and tries < 400000:
        tries += 1
        A = tuple(sorted([(0,)] + [(x,) for x in rng.sample(range(1, N), 2)]))
        B = tuple(sorted([(0,)] + [(x,) for x in rng.sample(range(1, N), 2)]))
        if (A, B) in seen:
            continue
        seen.add((A, B))
        hist = _hist_of(N, A, B)
        if classify(hist) != "C1":
            continue
        out.append(dict(N=N, cls="C1", A=[list(a) for a in A], B=[list(b) for b in B],
                        hist=hist, name=f"h4_Z{N}_C1_{len(out)}"))
    return out


def h4_specs(seed: int = SEED, out_csv: str | None = None) -> list[dict]:
    """Sample the H4 extension, skipping (N, A, B) already present in the CSV."""
    out_csv = out_csv or os.path.join(DATA, "h2_sharpness.csv")
    have: set = set()
    if os.path.exists(out_csv):
        for r in csv.DictReader(open(out_csv)):
            A = tuple(tuple(a) for a in json.loads(r["A"]))
            B = tuple(tuple(b) for b in json.loads(r["B"]))
            have.add((int(r["N"]), A, B))
    rng = random.Random(seed)
    specs = []
    for N in H4_NS:
        excl = {(A, B) for (n, A, B) in have if n == N}
        got = sample_c1(N, H4_PER_N, rng, excl)
        if len(got) < H4_PER_N:
            print(f"  N={N}: only {len(got)} distinct class-C1 instances found", flush=True)
        specs.extend(got)
    return specs


def run_h4(depth: int = 6, timeout: float = 600, workers: int = 20,
           out: str | None = None) -> str:
    out = out or os.path.join(DATA, "h2_sharpness.csv")
    specs = h4_specs(out_csv=out)
    print(f"H4 step 1: {len(specs)} new class-C1 instances over N in {H4_NS}, "
          f"depth {depth}, timeout {timeout:.0f}s, {workers} workers", flush=True)
    rows, t0 = [], time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_one, (s, depth, timeout)) for s in specs]
        for fut in as_completed(futs):
            row = fut.result()
            rows.append(row)
            if len(rows) % 25 == 0 or len(rows) == len(specs):
                print(f"  [{len(rows):3d}/{len(specs)}] {time.time()-t0:.0f}s", flush=True)
    existing = list(csv.DictReader(open(out))) if os.path.exists(out) else []
    allrows = existing + rows
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(sorted(allrows, key=lambda r: (int(r["N"]), r["class"], r["name"])))
    tally = Counter(r["status"] for r in rows)
    print(f"H4 step 1 finished in {time.time()-t0:.0f}s; new rows: {dict(tally)}")
    print(f"appended to {out} (now {len(allrows)} rows)")
    return out


if __name__ == "__main__":
    raise SystemExit(main())

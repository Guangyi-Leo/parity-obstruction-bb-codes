"""The code search behind Table 2 and Tables S14-S16, with a reproduction check.

``search2.py`` scans a group for two-block codes with w_A = w_B = 3, keeps the
Pareto-optimal (k, d) pairs per collision family and writes ``res_<l>x<m>.json``.
The scan is exhaustive for N <= 36 and samples 4e5 pairs per group above that;
the sampling seeds are fixed, so a re-run must reproduce the recorded files in
``revision/scripts/`` byte-for-byte in content.  A mismatch means the seed
handling changed and is reported as a failure -- the tables are never edited to
match a new run.

    python -m twoblock.code_search --list
    python -m twoblock.code_search --groups 18x1 --compare revision/scripts
    python -m twoblock.code_search --exhaustive 18,24,27,36 \
                                   --sampled 45,54,72 --samples 400000 \
                                   --compare revision/scripts
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE = os.path.join(ROOT, "twoblock")
WORK = os.path.join(ROOT, "revision", "work")
REF = os.path.join(ROOT, "revision", "scripts")
# N = 20 is a stray trial run with no families; it is not in the paper
SKIP = {(5, 4)}


def reference_groups(ref=REF):
    """(l, m, N) for every recorded run, newest naming, excluding the strays."""
    out = []
    for p in sorted(glob.glob(os.path.join(ref, "res_*.json"))):
        l, m = (int(x) for x in os.path.basename(p)[4:-5].split("x"))
        if (l, m) in SKIP:
            continue
        out.append((l, m, l * m))
    return sorted(out, key=lambda t: (t[2], t[0]))


def _load(p):
    with open(p) as f:
        return json.load(f)


def compare(l, m, ref=REF, work=WORK):
    """True when the fresh run reproduces the recorded one."""
    name = f"res_{l}x{m}.json"
    rp, wp = os.path.join(ref, name), os.path.join(work, name)
    if not os.path.exists(rp):
        return None, f"no reference {name}"
    if not os.path.exists(wp):
        return None, f"not run: {name} absent from revision/work"
    a, b = _load(rp), _load(wp)
    if a == b:
        return True, "identical"
    diffs = []
    for fam in sorted(set(a["families"]) | set(b["families"])):
        if a["families"].get(fam) != b["families"].get(fam):
            diffs.append(fam)
    return False, f"differs in families {diffs or '(header)'}"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--groups", default=None, help="e.g. 18x1,24x1")
    ap.add_argument("--exhaustive", default=None, help="orders to scan in full")
    ap.add_argument("--sampled", default=None, help="orders to sample")
    ap.add_argument("--samples", type=int, default=400000)
    ap.add_argument("--compare", default=None, help="reference directory")
    a = ap.parse_args(argv)

    groups = reference_groups()
    if a.list:
        for l, m, N in groups:
            print(f"  Z{l}xZ{m:<4} N={N:3d}  {'exhaustive' if N <= 36 else 'sampled'}")
        return 0

    if a.groups:
        want = {tuple(int(x) for x in g.split("x")) for g in a.groups.split(",")}
        sel = [(l, m, N) for l, m, N in groups if (l, m) in want]
    else:
        ex = {int(x) for x in (a.exhaustive or "").split(",") if x.strip()}
        sa = {int(x) for x in (a.sampled or "").split(",") if x.strip()}
        sel = [(l, m, N) for l, m, N in groups if N in ex or N in sa]
    if not sel:
        print("  no groups selected")
        return 2

    os.makedirs(WORK, exist_ok=True)
    if CODE not in sys.path:
        sys.path.insert(0, CODE)
    cwd = os.getcwd()
    os.chdir(WORK)                       # search2 writes res_*.json beside it
    try:
        import search2
        for l, m, N in sel:
            sample = None if N <= 36 else a.samples
            kind = "exhaustive" if sample is None else f"{sample} sampled"
            print(f"\n  Z{l}xZ{m} (N={N}, {kind})", flush=True)
            t0 = time.time()
            search2.run(l, m, sample=sample)
            print(f"  ... {time.time()-t0:.0f}s", flush=True)
    finally:
        os.chdir(cwd)

    rc = 0
    if a.compare:
        print("\n  reproduction against", a.compare)
        for l, m, N in sel:
            ok, why = compare(l, m, ref=os.path.join(ROOT, a.compare))
            mark = "OK  " if ok else ("----" if ok is None else "DIFF")
            print(f"    {mark} Z{l}xZ{m:<4} {why}")
            if ok is False:
                rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

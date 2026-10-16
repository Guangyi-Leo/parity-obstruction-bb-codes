"""Run the revision's verification scripts and turn their output into CSVs.

The scripts in ``twoblock/`` that came with the revision print prose.  Every
number the manuscript quotes from them has to be readable from a file, so each
run is executed here, its stdout kept under ``revision/work/logs/`` and the
quantities pulled out by a parser that *fails* when the expected line is not
there.  A missing line is an error, never a blank cell.

Runs are grouped by cost::

    fast    seconds to a few minutes   -- always run
    slow    ~10-20 min each            -- run with --slow
    search  hours                      -- run with --search (Task 7 territory)

A run that is not executed is not invented: the CSV simply has no row for it,
and ``--check`` reports which rows are missing.

    python -m twoblock.revision_runs            # the fast set
    python -m twoblock.revision_runs --slow     # + keys16 q=32, force32 q>=64
    python -m twoblock.revision_runs --check    # report coverage, run nothing
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
CODE = os.path.join(ROOT, "twoblock")
WORK = os.path.join(ROOT, "revision", "work")
LOGS = os.path.join(WORK, "logs")
PY = sys.executable


# ----------------------------------------------------------------- parsers
def _findall(pat, text, what, at_least=1):
    hits = re.findall(pat, text)
    assert len(hits) >= at_least, \
        f"{what}: expected >= {at_least} match of {pat!r}, found {len(hits)}"
    return hits


def p_bravyi(text):
    rows = []
    for n, k, d, depth, ok in _findall(
            r"Bravyi Table 5 on \[\[(\d+),(\d+),(\d+)\]\]: depth=(\d+).*?"
            r"M_pi==0: (True|False)", text, "bravyi table-5 checks", 2):
        rows.append(dict(item="bravyi_table5", code=f"[[{n},{k},{d}]]",
                         depth=int(depth), value=ok, unit="M_pi==0"))
    bo = _findall(r"Bravyi orientations \(o_L, o_R\): (.+)", text, "bravyi orientations")[0]
    ti = _findall(r"Table I orientations: (.+)", text, "Table I orientations")[0]
    rows.append(dict(item="orientations_bravyi", code="", depth=7,
                     value=bo.strip(), unit="(o_L,o_R)"))
    rows.append(dict(item="orientations_tableI", code="", depth=7,
                     value=ti.strip(), unit="(o_L,o_R)"))
    same, orb = _findall(r"Table I in the symmetry orbit of Bravyi Table 5: "
                         r"(True|False)\s+\(orbit size (\d+)", text,
                         "orbit membership")[0]
    rows.append(dict(item="tableI_in_bravyi_orbit", code="", depth=7,
                     value=same, unit="bool"))
    rows.append(dict(item="tableI_orbit_size", code="", depth=7,
                     value=int(orb), unit="schedules"))
    sch, orbits = _findall(r"translation-invariant proper depth-7 schedules: "
                           r"(\d+); orbits[^:]*: (\d+)", text,
                           "schedule/orbit totals")[0]
    rows.append(dict(item="invariant_depth7_schedules", code="", depth=7,
                     value=int(sch), unit="schedules"))
    rows.append(dict(item="invariant_depth7_orbits", code="", depth=7,
                     value=int(orbits), unit="orbits"))
    return rows


def p_pullback(text):
    q, M, keys, degen, ok, tot, fails = _findall(
        r"q=(\d+), M=(\d+): (\d+) keys with dbar!=0 \((\d+) degenerate\);"
        r".*?verified by F2 simulation: (\d+)/(\d+); failures: \[(.*?)\]",
        text, "pullback summary")[0]
    return [dict(q=int(q), M=int(M), keys=int(keys), degenerate=int(degen),
                 verified=int(ok), total=int(tot),
                 all_verified=(ok == tot), failures=fails.strip())]


def p_keys16(text):
    q, ok, tot = _findall(r"q=(\d+) structure=\S+: (\d+)/(\d+) representatives SAT",
                          text, "keys16 summary")[0]
    return [dict(q=int(q), kind="representatives", sat=int(ok), total=int(tot),
                 all_sat=(ok == tot))]


def p_force(text):
    q, ok, tot = _findall(r"q=(\d+) block-dependent universal sigma A: "
                          r"(\d+)/(\d+) SAT", text, "force32 summary")[0]
    return [dict(q=int(q), kind="forced_involutions", sat=int(ok),
                 total=int(tot), all_sat=(ok == tot))]


def p_universal3(text):
    rows = []
    for q, pairing, res in _findall(r"q=(\d+) (sigma_\S+=sigma_\S+, "
                                    r"sigma_\S+=sigma_\S+): (None|\{.*)", text,
                                    "universal3 pairings", 1):
        rows.append(dict(q=int(q), ansatz=pairing, found=(res.strip() != "None"),
                         witness=res.strip()))
    return rows


def p_universal4(text):
    rows = []
    for q, lab, perms in _findall(r"q=(\d+) ([AB]): (L=\S+, R=\S+): SAT for all b",
                                  text, "universal4 pairs", 1):
        rows.append(dict(q=int(q), ansatz=f"pair {lab}", found=True,
                         witness=perms))
    return rows


def p_sat_for_b(text):
    """family.py / twolevel.py / struct_test2.py: '...: SAT for b in [...]'."""
    rows = []
    for line in text.splitlines():
        m = re.match(r"q=(\d+)[:\s](.*?): SAT for b in \[(.*?)\]"
                     r"(?:; UNSAT for \[(.*?)\])?", line.strip())
        if not m:
            continue
        q, ansatz, sat, unsat = m.groups()
        sat_b = [int(x) for x in sat.split(",") if x.strip()]
        unsat_b = [int(x) for x in (unsat or "").split(",") if x.strip()]
        rows.append(dict(q=int(q), ansatz=ansatz.strip(" :"),
                         n_sat=len(sat_b), sat_b=" ".join(map(str, sat_b)),
                         # the scripts that print no UNSAT list enumerate every
                         # b, so the total is q; leaving it blank would read as
                         # "nothing was tried"
                         n_total=(len(sat_b) + len(unsat_b)) if unsat_b else int(q)))
    assert rows, "no 'SAT for b in [...]' line found"
    return rows


def p_struct_test2(text):
    """struct_test2.py: 'q=16 T depends only on (...): n/N keys SAT'."""
    rows = []
    for q, hyp, ok, tot in _findall(
            r"q=(\d+) T depends only on \((.*?)\): (\d+)/(\d+) keys SAT",
            text, "struct_test2 coarse-grainings", 1):
        rows.append(dict(q=int(q), ansatz=f"T depends only on ({hyp})",
                         n_sat=int(ok), sat_b="", n_total=int(tot)))
    return rows


CODE_RE = re.compile(r"\[\[\d+,\d+,[^\]]*\]\]")


def p_mpi(text):
    """A demo: every reported schedule must close the round (M_pi == 0).

    Some scripts put the code on the line itself, others announce it on the
    line before, so the last [[n,k,d]] seen carries forward -- otherwise seven
    independent checks all come out as the same nameless row.
    """
    rows, last_code = [], ""
    for line in text.splitlines():
        c = CODE_RE.search(line)
        if c:
            last_code = c.group(0)
        m = re.search(r"(.*?)\bdepth=(\d+).*?M_pi==0: (True|False)", line)
        if not m:
            continue
        what, depth, ok = m.groups()
        what = CODE_RE.sub("", what).strip().rstrip(":").strip()
        rows.append(dict(code=last_code, what=what or "schedule",
                         depth=int(depth), proper=ok))
    assert rows, "no 'M_pi==0' line found"
    return rows


# ------------------------------------------------------------------- runs
# (key, script, argv, cost, parser, csv)
RUNS = [
    ("bravyi_cycle",      "bravyi_cycle.py",   [],            "fast", p_bravyi,     "rev_bravyi_cycle.csv"),
    ("pullback_q2_M7",    "pullback_demo.py",  ["2", "7"],    "fast", p_pullback,   "rev_pullback.csv"),
    ("pullback_q4_M7",    "pullback_demo.py",  ["4", "7"],    "fast", p_pullback,   "rev_pullback.csv"),
    ("keys16_q8",         "keys16.py",         ["8"],         "fast", p_keys16,     "rev_template_keys.csv"),
    ("keys16_q16",        "keys16.py",         ["16"],        "fast", p_keys16,     "rev_template_keys.csv"),
    ("keys16_q32",        "keys16.py",         ["32"],        "slow", p_keys16,     "rev_template_keys.csv"),
    ("force_q64",         "force32.py",        ["64"],        "slow", p_force,      "rev_template_keys.csv"),
    ("force_q128",        "force32.py",        ["128"],       "slow", p_force,      "rev_template_keys.csv"),
    ("force_q256",        "force32.py",        ["256"],       "slow", p_force,      "rev_template_keys.csv"),
    ("force_q512",        "force32.py",        ["512"],       "slow", p_force,      "rev_template_keys.csv"),
    ("universal3_q8",     "universal3.py",     ["8"],         "fast", p_universal3, "rev_universal.csv"),
    ("universal3_q16",    "universal3.py",     ["16"],        "slow", p_universal3, "rev_universal.csv"),
    ("universal4",        "universal4.py",     ["2", "4", "8", "16"], "fast", p_universal4, "rev_universal.csv"),
    ("family_q8_half",    "family.py",         ["8", "sigma-half"],  "fast", p_sat_for_b, "rev_sigma_negative.csv"),
    ("family_q16_half",   "family.py",         ["16", "sigma-half"], "slow", p_sat_for_b, "rev_sigma_negative.csv"),
    ("family_q8_two",     "family.py",         ["8", "sigma-two"],   "fast", p_sat_for_b, "rev_sigma_negative.csv"),
    ("twolevel_q8",       "twolevel.py",       ["8"],         "fast", p_sat_for_b,  "rev_sigma_negative.csv"),
    ("twolevel_q16",      "twolevel.py",       ["16"],        "slow", p_sat_for_b,  "rev_sigma_negative.csv"),
    ("struct_test2_q16",  "struct_test2.py",   ["16"],        "slow", p_struct_test2, "rev_sigma_negative.csv"),
    # the two coarse-grainings Supplement S5 quotes: a schedule depending on c
    # only through (c mod 2, floor(4c/q)), and only through (c mod 4, 1[c>=q/2])
    ("family_q16_typed_pq", "family.py", ["16", "typed:parity+quarter"], "slow", p_sat_for_b, "rev_sigma_negative.csv"),
    ("family_q16_typed_m4h", "family.py", ["16", "typed:mod4+half"],     "slow", p_sat_for_b, "rev_sigma_negative.csv"),
    ("family_q16_half_typed", "family.py", ["16", "sigma-half-typed"],   "slow", p_sat_for_b, "rev_sigma_negative.csv"),
    ("demo72",            "demo72.py",         [],            "fast", p_mpi,        "rev_class_schedules.csv"),
    ("demo144",           "demo144.py",        [],            "slow", p_mpi,        "rev_class_schedules.csv"),
    ("demo144b",          "demo144b.py",       [],            "slow", p_mpi,        "rev_class_schedules.csv"),
    ("check_tableI",      "independent_check.py", ["tableI"], "fast", p_mpi,        "rev_class_schedules.csv"),
    ("check_z14",         "independent_check.py", ["z14"],    "fast", p_mpi,        "rev_class_schedules.csv"),
]
COSTS = {"fast": 0, "slow": 1, "search": 2}


def _run_one(key, script, argv, timeout):
    os.makedirs(LOGS, exist_ok=True)
    log = os.path.join(LOGS, f"{key}.log")
    cmd = [PY, os.path.join(CODE, script), *argv]
    t0 = time.time()
    with open(log, "w") as f:
        f.write(f"$ {' '.join(cmd)}\n")
        f.flush()
        rc = subprocess.call(cmd, cwd=WORK, stdout=f, stderr=subprocess.STDOUT,
                             timeout=timeout)
    dt = time.time() - t0
    with open(log) as f:
        text = f.read()
    return rc, dt, text, log


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--slow", action="store_true", help="also run the ~10-20 min runs")
    ap.add_argument("--search", action="store_true", help="also run the code search")
    ap.add_argument("--only", default=None, help="comma-separated run keys")
    ap.add_argument("--check", action="store_true", help="report coverage, run nothing")
    ap.add_argument("--timeout", type=float, default=7200.0)
    a = ap.parse_args(argv)

    want = COSTS["search"] if a.search else COSTS["slow"] if a.slow else COSTS["fast"]
    keys = set(a.only.split(",")) if a.only else None
    sel = [r for r in RUNS if (keys is None and COSTS[r[3]] <= want)
           or (keys is not None and r[0] in keys)]

    if a.check:
        os.makedirs(WORK, exist_ok=True)
        for key, script, args_, cost, _p, out in RUNS:
            log = os.path.join(LOGS, f"{key}.log")
            print(f"  {key:20s} {cost:7s} {'ran' if os.path.exists(log) else 'NOT RUN':8s} "
                  f"-> data/{out}")
        return 0

    tables, failed = {}, []
    for key, script, args_, cost, parser, out in sel:
        print(f"  {key:20s} {script} {' '.join(args_)}", end="", flush=True)
        try:
            rc, dt, text, log = _run_one(key, script, args_, a.timeout)
        except subprocess.TimeoutExpired:
            print(f"   TIMEOUT after {a.timeout:.0f}s -- recorded as not run")
            failed.append((key, "timeout"))
            continue
        if rc != 0:
            print(f"   exit {rc}; see {log}")
            failed.append((key, f"exit {rc}"))
            continue
        try:
            rows = parser(text)
        except AssertionError as e:
            print(f"   PARSE FAILED: {e}")
            failed.append((key, "parse"))
            continue
        for r in rows:
            r.update(run=key, script=script, args=" ".join(args_),
                     seconds=round(dt, 1))
        tables.setdefault(out, []).extend(rows)
        print(f"   {len(rows):2d} row(s)  [{dt:.0f}s]")

    for out, rows in tables.items():
        cols, seen = [], set()
        for r in rows:
            for k in r:
                if k not in seen:
                    seen.add(k)
                    cols.append(k)
        p = os.path.join(DATA, out)
        old = []
        if os.path.exists(p):
            with open(p) as f:
                old = [r for r in csv.DictReader(f) if r.get("run") not in
                       {x["run"] for x in rows}]
        with open(p, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(old + rows)
        print(f"  -> data/{out}  {len(old) + len(rows)} rows")

    if failed:
        print(f"\n  {len(failed)} run(s) did not produce a row: {failed}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

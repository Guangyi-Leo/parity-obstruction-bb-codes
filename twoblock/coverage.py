"""One table of record for every depth-6 instance: data/coverage.csv.

Every figure and every count in the text is meant to read this file rather than
re-deriving status from a different CSV with its own conventions.

    status_math    what is actually established, mathematically
        UNSAT-theorem   a theorem settles it: the componentwise mod-4 condition, or
                        k = l = 3 with distinct sums.  Recorded regardless of what the
                        solver did, so a capped run that a theorem already excludes is
                        never "open".
        UNSAT-cert      refuted by the solver AND the DRAT proof was drat-trim verified
        UNSAT-solver    refuted by the solver with no verified certificate on record
        SAT-solver      a schedule was found by the solver
        SAT-witness     the solver capped, and a verified twisted schedule resolved it
        open            no theorem applies and the solver capped
    status_solver  what the solver alone returned: unsat / sat / capped
"""
from __future__ import annotations

import ast
import csv
import os
from collections import Counter

from .code import TwoBlockCode
from .mod4 import obstructed as mod4_obstructed
from .overlaps import counts as overlap_counts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "coverage.csv")
FIELDS = ["instance", "source", "class", "class_source", "in_sharpness_map",
          "ord_d_parity", "status_math", "status_solver", "has_drat",
          "drat_verified", "symmetry_breaking", "nosym_verified", "theorem",
          "k", "l", "N"]


CERTS = [os.path.join(ROOT, "certs"), os.path.join(ROOT, "certs_nosym")]


def _drat_on_disk(instance: str) -> bool:
    """A certificate exists only if the .drat file is actually there."""
    for d in CERTS:
        for suffix in ("_d6.drat", "_d6_norev.drat"):
            if os.path.exists(os.path.join(d, instance + suffix)):
                return True
    return False


def _read(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return list(csv.DictReader(f))


def _row(instance, source, klass, parity, solver, has_drat, verified, theorem,
         resolved_by="", k="", l="", N="", nosym=False):
    """Apply the four precedence rules once, in one place."""
    if theorem:
        math = "UNSAT-theorem"
    elif solver == "unsat":
        math = "UNSAT-cert" if verified else "UNSAT-solver"
    elif solver == "sat":
        math = "SAT-solver"
    elif resolved_by.startswith("template-witness"):
        math = "SAT-witness"
    else:
        math = "open"
    return dict(instance=instance, source=source, **{"class": klass},
                class_source="", in_sharpness_map=False, ord_d_parity=parity, status_math=math, status_solver=solver,
                has_drat=has_drat, drat_verified=verified,
                symmetry_breaking="yes", nosym_verified=nosym,
                theorem=theorem or "", k=k, l=l, N=N)


_THEOREM_CACHE: dict = {}


def theorems_for(dims, A, B, name="") -> tuple[str, bool, bool]:
    """Which theorems claim this code, decided from the code itself.

    Both criteria are evaluated for every instance: the distinct-sums criterion of the
    main theorem (k = l = 3) and the componentwise mod-4 obstruction.  Trusting a
    per-file `theorem1_obstructed` column instead is what let `sw73` -- which the mod-4
    theorem does claim -- be recorded as certificate-only.
    """
    key = _sig(dims, A, B)
    if key in _THEOREM_CACHE:
        return _THEOREM_CACHE[key]
    code = TwoBlockCode(tuple(key[0]), list(key[1]), list(key[2]), name or "tmp")
    ds = code.distinct_sums() and code.k == 3 and code.l == 3
    m4 = mod4_obstructed(code.H_X(), code.H_Z())
    label = "; ".join(x for x in (("distinct sums, k=l=3" if ds else ""),
                                  ("componentwise mod-4" if m4 else "")) if x)
    _THEOREM_CACHE[key] = (label, ds, m4)
    return _THEOREM_CACHE[key]


def _sig(dims, A, B):
    """Canonical signature of a code, so the same code under two names is one row."""
    import ast
    a = tuple(sorted(tuple(x) for x in (A if isinstance(A, list) else ast.literal_eval(A))))
    b = tuple(sorted(tuple(x) for x in (B if isinstance(B, list) else ast.literal_eval(B))))
    return (tuple(dims), a, b)


def _round8_certs() -> dict:
    """Instances certified by the Round 8 DRAT re-run, name -> proof bytes.

    `data/c1_odd_unobstructed_certs.csv` records a re-run of the
    solver-reported UNSAT instances with DRAT logging and drat-trim.  Only
    rows that actually verified count.  The file may be partial -- the run is
    resumable -- so an absent instance means "not attempted", not "failed".

    This sets has_drat / drat_verified.  It deliberately does NOT change
    status_math: that column says how the depth-6 result is established in
    the argument (a theorem, a certificate run, or the solver alone), and
    re-deciding that on a partial pass would make the table describe an
    incomplete run.
    """
    out = {}
    for r in _read("c1_odd_unobstructed_certs.csv"):
        if r.get("verified") == "VERIFIED":
            out[r["instance"]] = int(r.get("proof_bytes") or 0)
    return out


def build() -> list[dict]:
    nosym = {r["instance"] for r in _read("r4_no_reversal.csv")
             if r["verified"] == "VERIFIED"}
    r8 = _round8_certs()
    seen_sig: dict = {}
    # the recomputed overlap class is authoritative wherever R7 covered the instance
    r7 = {r["instance"]: r["klass"] for r in _read("r7_overlap_counts.csv")}
    out: dict[str, dict] = {}

    # ---- the published codes and sw73, from the certificate runs ---------
    inst = {r["name"]: r for r in _read("instances.csv")}
    for r in _read("results.csv"):
        if r["D"] != "6":
            continue
        n = r["instance"]
        if n in out:
            continue
        i = inst.get(n)
        if i is None:
            # results.csv is the log of the named/published runs; a row for an
            # instance that is not in instances.csv came from an ad-hoc solve
            # and is not part of this table.  Skip it rather than crash.
            print(f"  [coverage] skipping {n}: not in instances.csv")
            continue
        import ast as _ast
        dims = _ast.literal_eval(i["dims"])
        seen_sig[_sig(dims, i["A_json"], i["B_json"])] = n
        thm, ds, _m4 = theorems_for(dims, i["A_json"], i["B_json"], n)
        k, l = int(r["k"]), int(r["l"])
        pb = int(r["proof_bytes"] or 0)
        out[n] = _row(n, "results.csv", "D" if ds else "other", "",
                      {"UNSAT": "unsat", "SAT": "sat"}.get(r["status"], "capped"),
                      pb > 0, r["verified"] == "VERIFIED", thm,
                      k=k, l=l, N=r["N"], nosym=n in nosym)

    # ---- class-C1 study: the resolved status is the one of record --------
    feats = {q["instance"]: q for q in _read("h4_features.csv")}
    for r in _read("c1_final_instances.csv"):
        n = r["instance"]
        f = feats.get(n)
        if f:
            thm, _ds, _m4 = theorems_for([int(f["N"])], f["A"], f["B"], n)
        else:
            thm = ("componentwise mod-4" if r["theorem1_obstructed"] == "True" else "")
        solver = {"UNSAT": "unsat", "SAT": "sat"}.get(r["status"], "capped")
        hd = _drat_on_disk(n)
        out[n] = _row(n, "c1_final_instances.csv", "C1",
                      "even" if r["ord_d_even"] == "True" else "odd",
                      solver, hd, False, thm, resolved_by=r.get("resolved_by", ""),
                      k=3, l=3, N=r["N"], nosym=n in nosym)

    # ---- H2 sharpness: classes D, C1, C2, SG ------------------------------
    t1 = {r["instance"]: r for r in _read("h1_predictions.csv")}
    for r in _read("h2_sharpness.csv"):
        n = r["name"]
        if n in out:                       # the C1 study already settled it
            out[n]["nosym_verified"] = out[n]["nosym_verified"] or n in nosym
            continue
        sg = _sig([int(r["N"])], r["A"], r["B"])
        if sg in seen_sig:
            continue
        seen_sig[sg] = n
        klass = "SG" if r["class"] == "subgroup" else r["class"]
        thm, ds, _m4 = theorems_for([int(r["N"])], r["A"], r["B"], n)
        pb = int(r["proof_bytes"] or 0)
        out[n] = _row(n, "h2_sharpness.csv", klass, "",
                      {"UNSAT": "unsat", "SAT": "sat"}.get(r["status"], "capped"),
                      pb > 0, r["verified"] == "VERIFIED", thm,
                      k=3, l=3, N=r["N"], nosym=n in nosym)

    # ---- H4 feature set (any C1 instance not already covered) -------------
    for r in _read("h4_features.csv"):
        n = r["instance"]
        if n in out:
            continue
        thm, _ds, _m4 = theorems_for([int(r["N"])], r["A"], r["B"], n)
        out[n] = _row(n, "h4_features.csv", "C1", "",
                      {"UNSAT": "unsat", "SAT": "sat"}.get(r["status"], "capped"),
                      _drat_on_disk(n), False, thm, k=3, l=3, N=r["N"],
                      nosym=n in nosym)

    # ---- the sweep --------------------------------------------------------
    for r in _read("sweep.csv"):
        n = r["name"]
        if n in out:
            continue
        import ast as _ast
        sg = _sig(_ast.literal_eval(r["dims"]), r["A"], r["B"])
        if sg in seen_sig:                 # the same code already has a row
            continue
        seen_sig[sg] = n
        thm, ds, _m4 = theorems_for(_ast.literal_eval(r["dims"]), r["A"], r["B"], n)
        k, l = int(r["k"]), int(r["l"])
        pb = int(r["proof_bytes"] or 0)
        out[n] = _row(n, "sweep.csv", "sweep", "",
                      {"UNSAT": "unsat", "SAT": "sat"}.get(r["status"], "capped"),
                      pb > 0, r["verified"] == "VERIFIED", thm,
                      k=k, l=l, N=r["N"], nosym=n in nosym)
    # Every row gets an overlap class.  R7 is authoritative where it ran; everything
    # else is classified here, so no depth-6 instance is left unlabelled and the
    # count of class `other` is a number, not a gap.
    ab = {}
    for q in _read("h2_sharpness.csv"):
        ab[q["name"]] = ([int(q["N"])], q["A"], q["B"])
    for q in _read("h4_features.csv"):
        ab.setdefault(q["instance"], ([int(q["N"])], q["A"], q["B"]))
    import ast as _ast
    for q in _read("sweep.csv"):
        ab.setdefault(q["name"], (_ast.literal_eval(q["dims"]), q["A"], q["B"]))
    for q in _read("instances.csv"):
        ab.setdefault(q["name"], (_ast.literal_eval(q["dims"]), q["A_json"],
                                  q["B_json"]))
    for n, r in out.items():
        if n in r7:
            r["class"] = r7[n]
            r["class_source"] = "r7_overlap_counts.csv"
            r["in_sharpness_map"] = True
        elif n in ab:
            dims, A, B = ab[n]
            key = _sig(dims, A, B)
            code = TwoBlockCode(tuple(key[0]), list(key[1]), list(key[2]), n)
            r["class"] = overlap_counts(code)["klass"]
            r["class_source"] = "recomputed"
    # Round 8: mark the instances whose UNSAT now has a checked DRAT proof
    for n, pb in r8.items():
        if n in out:
            out[n]["has_drat"] = True
            out[n]["drat_verified"] = True
    return [out[k] for k in sorted(out)]


def totals(rows) -> dict:
    c = Counter(r["status_math"] for r in rows)
    capped_thm = sum(1 for r in rows
                     if r["status_solver"] == "capped" and r["status_math"]
                     == "UNSAT-theorem")
    return dict(theorem_excluded=c["UNSAT-theorem"],
                drat_verified_unsat=c["UNSAT-cert"],
                drat_verified_any=sum(1 for r in rows
                                      if str(r["drat_verified"]) == "True"),
                solver_only_unsat=c["UNSAT-solver"],
                capped_but_theorem_excluded=capped_thm,
                open=c["open"], sat_solver=c["SAT-solver"],
                sat_witness=c["SAT-witness"], total=len(rows))


def main(argv=None):
    rows = build()
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader(); w.writerows(rows)
    print(f"  wrote {os.path.relpath(OUT, ROOT)}: {len(rows)} depth-6 instances")
    t = totals(rows)
    print(f"  theorem-excluded              {t['theorem_excluded']:5d}")
    print(f"  DRAT-verified UNSAT           {t['drat_verified_unsat']:5d}"
          f"   (in the partition; theorem-excluded takes precedence)")
    print(f"  ... with a verified certificate on record, in any category: "
          f"{t['drat_verified_any']}")
    print(f"  solver-only UNSAT             {t['solver_only_unsat']:5d}")
    print(f"  capped but theorem-excluded   {t['capped_but_theorem_excluded']:5d}")
    print(f"  open                          {t['open']:5d}")
    print(f"  (SAT solver {t['sat_solver']}, SAT witness {t['sat_witness']}, "
          f"total {t['total']})")
    cert = [r["instance"] for r in rows if r["status_math"] == "UNSAT-cert"]
    print(f"  DRAT-verified but claimed by no theorem: "
          f"{', '.join(sorted(cert)) or 'none'}")
    m = [r for r in rows if str(r["in_sharpness_map"]) == "True"]
    print(f"  sharpness-map population {len(m)}: "
          + ", ".join(f"{k} {v}" for k, v in
                      sorted(Counter(r["class"] for r in m).items())))
    sw = [r for r in rows if r["source"] == "sweep.csv"]
    print(f"  sweep {len(sw)}: "
          + ", ".join(f"{k} {v}" for k, v in
                      sorted(Counter(r["class"] for r in sw).items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

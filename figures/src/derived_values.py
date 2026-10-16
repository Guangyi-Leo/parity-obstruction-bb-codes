"""Quantities the manuscript states that no single CSV cell holds.

Each one is a named derivation from a file in the repository: the expression is
recorded next to the value, so a number in the text can be traced to the rows it
was computed from rather than to whatever cell happens to carry the same digits.
Written to figures/derived_values.csv by figures/src/build.py.
"""
from __future__ import annotations

import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(ROOT, "data")
IBM = ["bb72", "bb90", "bb108", "bb144", "bb288", "bb360", "bb756"]


def _rows(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return list(csv.DictReader(f))


def compute() -> list[dict]:
    out = []

    def add(name, value, expr, source):
        out.append(dict(name=name, value=value, expression=expr, source=source))

    # ---- class-C1 strata ---------------------------------------------------
    c1 = _rows("c1_final_instances.csv")
    odd = [r for r in c1 if r["ord_d_even"] == "False"]
    obs = [r for r in odd if r["theorem1_obstructed"] == "True"]
    add("c1_ord_d_odd_total", len(odd),
        "count(rows where ord_d_even == False)", "data/c1_final_instances.csv")
    add("c1_ord_d_odd_obstructed", len(obs),
        "count(rows where ord_d_even == False and theorem1_obstructed == True)",
        "data/c1_final_instances.csv")
    add("c1_ord_d_odd_unobstructed", len(odd) - len(obs),
        "count(rows where ord_d_even == False and theorem1_obstructed == False)",
        "data/c1_final_instances.csv")
    add("c1_ord_d_even_total", len(c1) - len(odd),
        "count(rows where ord_d_even == True)", "data/c1_final_instances.csv")

    # ---- certificate ranges, with and without the layer-reversal clause ----
    res = {}
    for r in _rows("results.csv"):
        if r["D"] == "6" and r["status"] == "UNSAT":
            res.setdefault(r["instance"], r)
    nos = {r["instance"]: r for r in _rows("r4_no_reversal.csv")
           if r["symmetry_breaking"] == "False"}

    def span(tag, rows, src, note):
        if not rows:
            return
        t = [float(r["time"]) for r in rows]
        p = [float(r["proof_bytes"]) / 1e6 for r in rows]
        add(f"{tag}_solve_min_s", min(t), f"min(time) over {note}", src)
        add(f"{tag}_solve_max_s", max(t), f"max(time) over {note}", src)
        add(f"{tag}_proof_min_MB", min(p), f"min(proof_bytes)/1e6 over {note}", src)
        add(f"{tag}_proof_max_MB", max(p), f"max(proof_bytes)/1e6 over {note}", src)

    span("sym", [res[n] for n in IBM if n in res], "data/results.csv",
         "the 7 IBM depth-6 refutations with the layer-reversal clause (certs/)")
    span("nosym", [nos[n] for n in IBM if n in nos], "data/r4_no_reversal.csv",
         "the 7 IBM depth-6 refutations without the clause (certs_nosym/)")
    span("nosym_all", list(nos.values()), "data/r4_no_reversal.csv",
         "all 9 rows without the clause (certs_nosym/)")

    # ---- test coverage ------------------------------------------------------
    cov = _rows("t7_model_coverage.csv")
    t2 = [r for r in cov if r["test"] == "T2"]
    if t2:
        per = {int(r["n_layerings"]) for r in t2}
        add("t2_layerings_per_instance", sorted(per)[0] if len(per) == 1 else -1,
            "n_layerings, identical for every T2 instance",
            "data/t7_model_coverage.csv")
        add("t2_layerings_total", sum(int(r["n_layerings"]) for r in t2),
            "sum(n_layerings) over the T2 rows", "data/t7_model_coverage.csv")
        add("t2_instances", len(t2), "count(T2 rows)", "data/t7_model_coverage.csv")

    # ---- coverage: the five totals the abstract needs ----------------------
    cov = _rows("coverage.csv")
    if cov:
        cl = [r for r in cov if r["in_sharpness_map"] == "True"]
        src = "data/coverage.csv"
        add("coverage_theorem_excluded",
            sum(1 for r in cov if r["status_math"] == "UNSAT-theorem"),
            "count(status_math == 'UNSAT-theorem')", src)
        add("coverage_drat_verified",
            sum(1 for r in cov if r["drat_verified"] == "True"),
            "count(drat_verified) -- certificates on record, any category", src)
        add("coverage_unsat_cert",
            sum(1 for r in cov if r["status_math"] == "UNSAT-cert"),
            "count(status_math == 'UNSAT-cert') -- the partition class", src)
        add("coverage_solver_only_unsat",
            sum(1 for r in cov if r["status_math"] == "UNSAT-solver"),
            "count(status_math == 'UNSAT-solver')", src)
        # the solver refutations split by whether a proof was logged and checked
        add("coverage_solver_unsat_certified",
            sum(1 for r in cov if r["status_math"] == "UNSAT-solver"
                and r["drat_verified"] == "True"),
            "count(status_math == 'UNSAT-solver' and drat_verified)", src)
        add("coverage_solver_unsat_uncertified",
            sum(1 for r in cov if r["status_math"] == "UNSAT-solver"
                and r["drat_verified"] != "True"),
            "count(status_math == 'UNSAT-solver' and not drat_verified)", src)
        add("coverage_capped_but_excluded",
            sum(1 for r in cov if r["status_solver"] == "capped"
                and r["status_math"] == "UNSAT-theorem"),
            "count(status_solver == 'capped' and status_math == 'UNSAT-theorem')", src)
        add("coverage_open", sum(1 for r in cov if r["status_math"] == "open"),
            "count(status_math == 'open')", src)
        add("h2_class_D_count",
            sum(1 for r in cov if r["class"] == "D"
                and r["source"] == "h2_sharpness.csv"),
            "count(class == 'D' and source == 'h2_sharpness.csv')", src)
        add("sharpness_map_total", len(cl),
            "count(in_sharpness_map) -- the population of the sharpness map", src)
        add("sweep_class_other",
            sum(1 for r in cov if r["source"] == "sweep.csv"
                and r["class"] == "other"),
            "count(source == 'sweep.csv' and class == 'other')", src)

    # ---- the main-text template (C2) ---------------------------------------
    tpl = _rows("template_main.csv")
    if tpl:
        t = tpl[0]
        for f in ("N", "n_qubits", "k_logical", "m", "n_constraints"):
            if t.get(f):
                add(f"template_m2_{f}", int(t[f]), f"{f} of the chosen m = 2 template",
                    "data/template_main.csv")

    # ---- twisted schedules outside class C1 (B2) ---------------------------
    b2 = _rows("b2_twisted_outside_c1.csv")
    if b2:
        fnd = [r for r in b2 if r["result"] == "found"]
        add("b2_schedules_found", len(fnd), "count(result == 'found')",
            "data/b2_twisted_outside_c1.csv")
        add("b2_instances_with_schedule", len({r["instance"] for r in fnd}),
            "distinct instances with a twisted schedule",
            "data/b2_twisted_outside_c1.csv")
        add("b2_distinct_absM", len({r["abs_M"] for r in fnd}),
            "distinct |M| values among them", "data/b2_twisted_outside_c1.csv")
        add("b2_odd_absM", sum(1 for r in fnd if r["M_parity"] == "odd"),
            "schedules with |M| odd (must be 0)",
            "data/b2_twisted_outside_c1.csv")
        add("b2_capped", sum(1 for r in b2 if r["result"] == "capped"),
            "count(result == 'capped') -- never read as absence",
            "data/b2_twisted_outside_c1.csv")

    # ---- twisted coset identity (B1) ---------------------------------------
    ti = _rows("twisted_identity.csv")
    if ti:
        src = "data/twisted_identity.csv"
        add("twisted_identity_cosets", len(ti), "count(rows)", src)
        add("twisted_identity_witnesses",
            len({r["name"] for r in ti if r["kind"] == "witness"}),
            "distinct witnesses", src)
        # key strings repeat across moduli, so count distinct keys within each m
        tmp = [r for r in ti if r["kind"] == "template"]
        per_m = {}
        for r in tmp:
            per_m.setdefault(r["m"], set()).add(r["name"])
        add("twisted_identity_template_keys", sum(len(v) for v in per_m.values()),
            "sum over m of the distinct template keys at that m", src)
        add("twisted_identity_failures",
            sum(1 for r in ti if r["equal"] != "True"),
            "count(equal != True) -- must be 0", src)

    # ---- quantities the redrawn figures no longer trace directly -----------
    cov = _rows("coverage.csv")
    if cov:
        m = [r for r in cov if r["in_sharpness_map"] == "True"]
        c1e = [r for r in m if r["class"] == "C1" and r["ord_d_parity"] == "even"]
        add("c1_even_sat_solver",
            sum(1 for r in c1e if r["status_math"] == "SAT-solver"),
            "count(class C1, ord(d) even, status_math == 'SAT-solver')",
            "data/coverage.csv")
        add("c1_even_sat_witness",
            sum(1 for r in c1e if r["status_math"] == "SAT-witness"),
            "count(class C1, ord(d) even, status_math == 'SAT-witness')",
            "data/coverage.csv")
    per = _rows("r6_periodicity.csv")
    if per:
        from collections import Counter as _C
        k = _C(r["klass"] for r in per)
        add("periodicity_invariant", k["invariant"], "count(klass == 'invariant')",
            "data/r6_periodicity.csv")
        add("periodicity_twisted", k["twisted"], "count(klass == 'twisted')",
            "data/r6_periodicity.csv")
        add("periodicity_other", k["other"], "count(klass == 'other')",
            "data/r6_periodicity.csv")
        add("periodicity_total", len(per), "count(rows)", "data/r6_periodicity.csv")

    # ---- solver cross-check -------------------------------------------------
    xc = _rows("solver_crosscheck.csv")
    if xc:
        agree = [r for r in xc if r["cadical_status"] == r["glucose_status"]
                 and r["cadical_status"] in ("SAT", "UNSAT")]
        add("crosscheck_rows", len(xc), "count(rows)", "data/solver_crosscheck.csv")
        add("crosscheck_agree", len(agree),
            "count(rows where cadical_status == glucose_status, both decided)",
            "data/solver_crosscheck.csv")

    # ---- the revision's verification runs -----------------------------------
    bc = {r["item"]: r["value"] for r in _rows("rev_bravyi_cycle.csv")}
    if bc:
        add("bravyi_invariant_depth7_schedules",
            int(bc["invariant_depth7_schedules"]),
            "translation-invariant proper depth-7 schedules, from bravyi_cycle.py",
            "data/rev_bravyi_cycle.csv")
        add("bravyi_invariant_depth7_orbits", int(bc["invariant_depth7_orbits"]),
            "their orbits under label perms x reversal x duality x block swap",
            "data/rev_bravyi_cycle.csv")
    pb = {int(r["q"]): r for r in _rows("rev_pullback.csv")}
    for q in sorted(pb):
        add(f"pullback_keys_q{q}", int(pb[q]["keys"]),
            f"admissible keys at q = {q}, all verified by F2 simulation",
            "data/rev_pullback.csv")
        add(f"pullback_degenerate_q{q}", int(pb[q]["degenerate"]),
            f"of those, with a repeated entry", "data/rev_pullback.csv")
    reps = {int(r["q"]): int(r["representatives"])
            for r in _rows("rev_key_representatives.csv")}
    for q, n in sorted(reps.items()):
        add(f"template_reps_q{q}", n,
            f"key representatives under the three symmetries at q = {q}",
            "data/rev_key_representatives.csv")
    force = [r for r in _rows("template_force.csv") if r["all_sat"] == "True"]
    if force:
        add("template_force_qmax", max(int(r["q"]) for r in force),
            "largest modulus with every class SAT under the fixed involutions",
            "data/template_force.csv")
        add("template_force_keys_qmax",
            max(((int(r["q"]), int(r["total"])) for r in force))[1],
            "keys decided at that modulus", "data/template_force.csv")
    hgp = [r for r in _rows("cor3_hgp.csv") if r["obstructed"] == "True"]
    for i, r in enumerate(sorted(hgp, key=lambda r: int(r["n"])), 1):
        add(f"cor3_hgp_n{i}", int(r["n"]),
            f"physical qubits of the Corollary 3 example {r['seed']}",
            "data/cor3_hgp.csv")
        add(f"cor3_hgp_k{i}", int(r["k"]),
            f"logical qubits of {r['seed']}", "data/cor3_hgp.csv")

    # the two coarse-grainings of Supplement S5, and the certified odd-order
    # [[90,12,6]] instances of Supplement S8
    neg = {r["ansatz"]: r for r in _rows("rev_sigma_negative.csv")
           if r.get("q") == "16"}
    for key, name, what in (
            ("ansatz=typed:parity+quarter", "typed_parity_quarter_q16",
             "values of b at q = 16 admitting a schedule that depends on c "
             "only through (c mod 2, floor(4c/q))"),
            ("ansatz=typed:mod4+half", "typed_mod4_half_q16",
             "and only through (c mod 4, 1[c >= q/2])"),
            ("ansatz=sigma-half-typed", "typed_sigma_half_q16",
             "values of b admitting the type-dependent half-period symmetry")):
        if key in neg:
            add(name, int(neg[key]["n_sat"]), what, "data/rev_sigma_negative.csv")
    odd = _rows("odd_order_certs.csv")
    for r in odd:
        if r["verified"] != "VERIFIED":
            continue
        add(f"odd_cert_seconds[{r['group']}]", round(float(r["time"])),
            f"kissat refutation of the {r['group']} [[90,12,6]] instance, s",
            "data/odd_order_certs.csv")
        add(f"odd_cert_GB[{r['group']}]", round(int(r["proof_bytes"]) / 1e9, 1),
            "its drat-trim verified DRAT proof, GB", "data/odd_order_certs.csv")

    # ---- equivalence census of the two sweeps -------------------------------
    cen = _rows("sweep_census.csv")
    if cen:
        add("sweep_census_orbits", sum(int(r["orbits"]) for r in cen),
            "sum of the per-group orbit counts", "data/sweep_census.csv")
    sodd = _rows("sweep_odd.csv")
    if sodd:
        add("sweep_odd_pairs", sum(int(r["orbit_size"]) for r in sodd),
            "sum of orbit_size over the orbit representatives",
            "data/sweep_odd.csv")
    return out


def write(path=None) -> list[dict]:
    rows = compute()
    p = path or os.path.join(ROOT, "figures", "derived_values.csv")
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name", "value", "expression", "source"])
        w.writeheader()
        w.writerows(rows)
    return rows


if __name__ == "__main__":
    for r in write():
        print(f"  {r['name']:28s} {r['value']!s:>12s}   {r['expression']}")

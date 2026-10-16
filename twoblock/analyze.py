"""Per-solution lemma checks (specification section 5).

For a proper schedule:
    x_i     = number of X-edges on the L side in layer i (i = 1..D)
    Lambda  = {i : x_i > 0},  a = min Lambda,  b = max Lambda
    E       = X-checks whose L-layers contain a or b

    L1  a + b == D + 1
    L2  every check in E contains both a and b (X-checks/L-layers and,
        symmetrically, Z-checks/R-layers -- reported as L2_X and L2_Z)
    L3  (T1) for every X-check in E and every R-edge with layer v strictly inside
        (a,b): at that R-qubit the Z-edge labelled s_a has layer > v and the
        Z-edge labelled s_b has layer < v, where s_a / s_b are the labels of the
        check's L-edges in layers a / b
    L4  (T2) for every X-check not in E and every L-edge at layer p: at that
        L-qubit the Z-edge labelled t_a has layer > p and the one labelled t_b
        has layer < p, where t_a / t_b label the check's R-edges in layers a / b
    L5  (straddling) for every X-check not in E and every L-edge at layer p:
        among the Z-layers of that qubit inside [a,b], at least one is > p and
        at least one is < p
    L6  (F-balance) for every X-check, F_L == F_R (when the sums a_s+b_t are
        distinct); otherwise F_L + F_R is even
    L7  (Theorem F count) if every x_i is in {0, N} then F_L + F_R == k*l
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter

from .code import TwoBlockCode
from .simulate import is_proper_by_simulation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SCHED = os.path.join(ROOT, "schedules")

LEMMAS = ["L1", "L1_Z", "L2_X", "L2_Z", "L2", "L3", "L4", "L5", "L6", "L7"]

# The manuscript names the statements; the code has always named them L1..L7.  Both
# vocabularies are written out, so a figure or a table can use either.  Every one of
# these is stated for general (k, l): none refers to the (1,6) pair structure, which
# is a k = l = 3, Delta = 6 argument and was never one of these columns.
STATEMENT_OF = {
    "support_symmetry":  ("L1", "L1_Z"),      # a + b = Delta + 1, both sides
    "extremal_both_ends": ("L2",),            # every check in E carries a and b
    "T1":                ("L3",),
    "T2":                ("L4",),
    "straddling":        ("L5",),
    "F_balance":         ("L6",),
    "theorem_F_count":   ("L7",),
}
STATEMENTS = list(STATEMENT_OF) + ["corner_bijection", "F_parity"]


class LemmaReport:
    def __init__(self):
        self.results: dict[str, bool] = {}
        self.counts: dict[str, int] = {}
        self.failures: list[str] = []

    def record(self, name: str, ok: bool, detail: str = ""):
        self.results[name] = bool(ok)
        if not ok:
            self.failures.append(f"{name}: {detail}")


def _layer_sets(code: TwoBlockCode, lay, kind: str, side: str):
    """check index -> {label(1-based): layer} for edges of the given kind/side."""
    out: list[dict[int, int]] = [dict() for _ in range(code.N)]
    for e in code.edges:
        if e.kind == kind and e.side == side:
            out[e.check][e.lab1] = lay[e.eid]
    return out


def _qubit_zlayers(code: TwoBlockCode, lay, side: str):
    """data qubit h -> {label(1-based): layer} for the Z-edges at that qubit."""
    out: list[dict[int, int]] = [dict() for _ in range(code.N)]
    for e in code.edges:
        if e.kind == "Z" and e.side == side:
            out[e.qubit][e.lab1] = lay[e.eid]
    return out


def analyze_schedule(code: TwoBlockCode, lay, D: int, solution_id: int = 0,
                     verify_proper: bool = True) -> dict:
    N, k, l = code.N, code.k, code.l
    rep = LemmaReport()
    proper = is_proper_by_simulation(code, lay, D) if verify_proper else None
    if verify_proper and not proper:
        raise AssertionError(f"{code.name}: schedule #{solution_id} is not proper -- refusing to analyse")

    # ---- layer profile on the X/L side --------------------------------------
    x = [0] * (D + 2)
    for e in code.edges:
        if e.kind == "X" and e.side == "L":
            x[lay[e.eid]] += 1
    Lam = [i for i in range(1, D + 1) if x[i] > 0]
    a, b = min(Lam), max(Lam)

    # ---- the same profile on the Z/R side (labels s from A, mirror of X/L) ---
    xz = [0] * (D + 2)
    for e in code.edges:
        if e.kind == "Z" and e.side == "R":
            xz[lay[e.eid]] += 1
    LamZ = [i for i in range(1, D + 1) if xz[i] > 0]
    aZ, bZ = min(LamZ), max(LamZ)

    XL = _layer_sets(code, lay, "X", "L")     # X-check -> {s: layer}
    XR = _layer_sets(code, lay, "X", "R")     # X-check -> {t: layer}
    ZR = _layer_sets(code, lay, "Z", "R")     # Z-check -> {s: layer}
    zL = _qubit_zlayers(code, lay, "L")       # L-qubit -> {t: layer}
    zR = _qubit_zlayers(code, lay, "R")       # R-qubit -> {s: layer}
    # qubit reached by an X-edge of check g with label s (L side) / t (R side)
    xLq = [dict() for _ in range(N)]
    xRq = [dict() for _ in range(N)]
    for e in code.edges:
        if e.kind == "X":
            (xLq if e.side == "L" else xRq)[e.check][e.lab1] = e.qubit

    # ---- corner bijection ---------------------------------------------------
    # With distinct sums an overlap pair has one corner on each side, so the L- and
    # R-corners of every pair are in bijection.  A property of the code, not of the
    # schedule, but recorded per row so the table stands alone.
    bij = []
    for op in code.overlap_pairs:
        sides = [code.corners[cid].side for cid in op.corners]
        if sides.count("L") != sides.count("R"):
            bij.append((op.gx, op.gz, sides.count("L"), sides.count("R")))
    rep.record("corner_bijection", not bij,
               f"pairs with unequal L/R corner counts: {bij[:3]}")

    # ---- L1 -----------------------------------------------------------------
    rep.record("L1", a + b == D + 1, f"a={a} b={b} D={D} (a+b={a+b}, want {D+1})")
    rep.record("L1_Z", aZ + bZ == D + 1, f"aZ={aZ} bZ={bZ} D={D}")

    # ---- E and L2 -----------------------------------------------------------
    Eset, bad2x = [], []
    for g in range(N):
        ls = set(XL[g].values())
        if a in ls or b in ls:
            Eset.append(g)
            if not (a in ls and b in ls):
                bad2x.append((g, sorted(ls)))
    EsetZ, bad2z = [], []
    for g in range(N):
        ls = set(ZR[g].values())
        if aZ in ls or bZ in ls:
            EsetZ.append(g)
            if not (aZ in ls and bZ in ls):
                bad2z.append((g, sorted(ls)))
    rep.record("L2_X", not bad2x, f"X-checks in E missing a or b: {bad2x[:3]}")
    rep.record("L2_Z", not bad2z, f"Z-checks in E_Z missing aZ or bZ: {bad2z[:3]}")
    rep.record("L2", not bad2x and not bad2z, f"X:{bad2x[:2]} Z:{bad2z[:2]}")
    Ein = set(Eset)

    # ---- L3 (T1) ------------------------------------------------------------
    n3 = 0
    bad3 = []
    for g in Eset:
        inv = {v: s for s, v in XL[g].items()}
        s_a, s_b = inv.get(a), inv.get(b)
        if s_a is None or s_b is None:      # already reported by L2
            continue
        for t, v in XR[g].items():
            if not (a < v < b):
                continue
            h = xRq[g][t]
            n3 += 1
            if not (zR[h][s_a] > v):
                bad3.append(dict(check=g, t=t, v=v, s_a=s_a, layer=zR[h][s_a], want=">v"))
            if not (zR[h][s_b] < v):
                bad3.append(dict(check=g, t=t, v=v, s_b=s_b, layer=zR[h][s_b], want="<v"))
    rep.record("L3", not bad3, f"{len(bad3)}/{n3} violations, first={bad3[:2]}")

    # ---- L4 (T2) and L5 (straddling) ----------------------------------------
    n4 = n4_vac = n5 = 0
    bad4, bad5 = [], []
    for g in range(N):
        if g in Ein:
            continue
        invR = {v: t for t, v in XR[g].items()}
        t_a, t_b = invR.get(a), invR.get(b)
        for s, p in XL[g].items():
            h = xLq[g][s]
            zl = zL[h]
            if t_a is None or t_b is None:
                n4_vac += 1
            else:
                n4 += 1
                if not (zl[t_a] > p):
                    bad4.append(dict(check=g, s=s, p=p, t_a=t_a, layer=zl[t_a], want=">p"))
                if not (zl[t_b] < p):
                    bad4.append(dict(check=g, s=s, p=p, t_b=t_b, layer=zl[t_b], want="<p"))
            inside = [v for v in zl.values() if a <= v <= b]
            n5 += 1
            if not (any(v > p for v in inside) and any(v < p for v in inside)):
                bad5.append(dict(check=g, s=s, p=p, inside=sorted(inside)))
    rep.record("L4", not bad4, f"{len(bad4)}/{n4} violations ({n4_vac} vacuous), first={bad4[:2]}")
    rep.record("L5", not bad5, f"{len(bad5)}/{n5} violations, first={bad5[:2]}")

    # ---- L6 (F-balance) and L7 (Theorem F count) ----------------------------
    distinct = code.distinct_sums()
    allN = all(v in (0, N) for v in x[1:D + 1])
    bad6, bad7 = [], []
    FLs, FRs = [], []
    for g in range(N):
        FL = sum(sum(1 for v in zL[xLq[g][s]].values() if v > p) for s, p in XL[g].items())
        FR = sum(sum(1 for v in zR[xRq[g][t]].values() if v > p) for t, p in XR[g].items())
        FLs.append(FL)
        FRs.append(FR)
        if distinct:
            if FL != FR:
                bad6.append(dict(check=g, F_L=FL, F_R=FR))
        elif (FL + FR) % 2:
            bad6.append(dict(check=g, F_L=FL, F_R=FR, parity="odd"))
        if allN and FL + FR != k * l:
            bad7.append(dict(check=g, F_L=FL, F_R=FR, want=k * l))
    # F_parity: F_L(g) + F_R(g) even for EVERY X-check, whatever the class.  L6 only
    # tests this on the non-distinct-sums branch; here it is unconditional.
    bad_par = [dict(check=g, F_L=FL, F_R=FR) for g, (FL, FR) in
               enumerate(zip(FLs, FRs)) if (FL + FR) % 2]
    rep.record("F_parity", not bad_par,
               f"{len(bad_par)}/{N} X-checks with F_L+F_R odd, first={bad_par[:2]}")
    rep.record("L6", not bad6, f"{len(bad6)}/{N} violations, first={bad6[:2]}")
    rep.record("L7", not bad7 if allN else True,
               f"{len(bad7)}/{N} violations, first={bad7[:2]}")

    row = dict(instance=code.name, solution=solution_id, N=N, k=k, l=l, Delta=code.Delta, D=D,
               distinct_sums=distinct, proper=proper,
               a=a, b=b, aZ=aZ, bZ=bZ, Lambda=json.dumps(Lam),
               x_profile=json.dumps([x[i] for i in range(1, D + 1)]),
               all_x_in_0_N=allN, size_E=len(Eset), size_E_Z=len(EsetZ),
               n_L3_checked=n3, n_L4_checked=n4, n_L4_vacuous=n4_vac, n_L5_checked=n5,
               L7_applicable=allN, F_L_hist=json.dumps(dict(sorted(Counter(FLs).items()))),
               F_R_hist=json.dumps(dict(sorted(Counter(FRs).items()))))
    row.update({nm: rep.results[nm] for nm in LEMMAS})
    row["corner_bijection"] = rep.results["corner_bijection"]
    row["F_parity"] = rep.results["F_parity"]
    row["all_pass"] = all(rep.results[nm] for nm in LEMMAS) and \
        rep.results["corner_bijection"] and rep.results["F_parity"]
    row["failures"] = " | ".join(rep.failures)
    return row


def analyze_enum_file(path: str) -> list[dict]:
    with open(path) as f:
        rec = json.load(f)
    code = TwoBlockCode(tuple(rec["dims"]), [tuple(a) for a in rec["A"]],
                        [tuple(b) for b in rec["B"]], rec["instance"])
    code.check_structure()
    return [analyze_schedule(code, lay, rec["D"], i) for i, lay in enumerate(rec["solutions"])]


FIELDS = ["instance", "schedule_id", "period_class", "solution", "N", "k", "l",
          "Delta", "D", "distinct_sums", "proper",
          "a", "b", "aZ", "bZ", "Lambda", "x_profile", "all_x_in_0_N", "size_E", "size_E_Z",
          "n_L3_checked", "n_L4_checked", "n_L4_vacuous", "n_L5_checked", "L7_applicable",
          "F_L_hist", "F_R_hist"] + STATEMENTS + LEMMAS + ["all_pass", "failures"]


def _period_classes() -> dict:
    p = os.path.join(DATA, "r6_periodicity.csv")
    if not os.path.exists(p):
        return {}
    with open(p) as f:
        return {(r["instance"], int(r["solution"])): r["klass"]
                for r in csv.DictReader(f)}


def decorate(rows: list[dict]) -> list[dict]:
    """Add schedule_id, period_class and the statement-named columns."""
    per = _period_classes()
    for r in rows:
        r["schedule_id"] = f"{r['instance']}#{r['solution']}"
        r["period_class"] = per.get((r["instance"], int(r["solution"])), "")
        for name, codes in STATEMENT_OF.items():
            r[name] = all(r[c] for c in codes)
    return rows


def write_csv(rows: list[dict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def summarize(rows: list[dict]) -> list[dict]:
    out = []
    insts = sorted({r["instance"] for r in rows})
    for inst in insts + ["ALL"]:
        sel = rows if inst == "ALL" else [r for r in rows if r["instance"] == inst]
        rec = dict(instance=inst, n_solutions=len(sel))
        for nm in LEMMAS:
            npass = sum(1 for r in sel if r[nm])
            rec[nm + "_pass"] = npass
            rec[nm + "_rate"] = round(npass / len(sel), 6) if sel else 0.0
        rec["all_pass"] = sum(1 for r in sel if r["all_pass"])
        rec["all_rate"] = round(rec["all_pass"] / len(sel), 6) if sel else 0.0
        out.append(rec)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run the lemma checks on enumerated schedules.")
    ap.add_argument("--enum", nargs="*", default=None,
                    help="enumeration JSON files (default: schedules/*_enum.json)")
    ap.add_argument("--out", default=os.path.join(DATA, "lemma_checks.csv"))
    args = ap.parse_args(argv)

    paths = args.enum
    if not paths:
        paths = sorted(os.path.join(SCHED, f) for f in os.listdir(SCHED) if f.endswith("_enum.json"))
    if not paths:
        print("no enumeration files found; run `make m3` first", file=sys.stderr)
        return 1

    rows: list[dict] = []
    for p in paths:
        r = analyze_enum_file(p)
        rows.extend(r)
        print(f"{os.path.basename(p)}: {len(r)} solutions, "
              f"{sum(1 for x in r if x['all_pass'])} pass all lemmas", flush=True)
    write_csv(decorate(rows), args.out)
    summ = summarize(rows)
    write_csv_summary = os.path.join(os.path.dirname(args.out), "lemma_summary.csv")
    with open(write_csv_summary, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summ[0].keys()))
        w.writeheader()
        w.writerows(summ)

    hdr = f"{'instance':10} {'#sol':>5} " + " ".join(f"{nm:>6}" for nm in LEMMAS) + f" {'ALL':>6}"
    print("\n" + hdr)
    print("-" * len(hdr))
    for rec in summ:
        print(f"{rec['instance']:10} {rec['n_solutions']:5d} "
              + " ".join(f"{rec[nm+'_rate']*100:5.1f}%" for nm in LEMMAS)
              + f" {rec['all_rate']*100:5.1f}%")
    print(f"\nwrote {args.out} and {write_csv_summary}")

    fails = [r for r in rows if not r["all_pass"]]
    if fails:
        print("\n" + "!" * 70)
        print(f"LEMMA CHECK FAILURES: {len(fails)} of {len(rows)} solutions")
        for r in fails[:20]:
            print(f"  {r['instance']} #{r['solution']}  a={r['a']} b={r['b']} D={r['D']}"
                  f"  x={r['x_profile']}\n    {r['failures']}")
        print("!" * 70)
        return 1
    print(f"\nOK: all {len(rows)} solutions pass all lemma checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())

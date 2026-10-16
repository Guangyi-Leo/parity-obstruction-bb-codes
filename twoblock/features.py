"""H4 -- feature analysis of the class-C1 instances.  No new theory is introduced.

For every C1 instance there is exactly one coincidence a_s + b_t = a_{s'} + b_{t'}.
Writing d = a_s - a_{s'} ( = b_{t'} - b_t ) and delta_0 for the coincident sum, this
module records a handful of group-theoretic features of (d, delta_0) together with
Tanner-graph facts, and reports the contingency table of each feature against the
recorded depth-6 status.  Only **exact** separations are reported; nothing is fitted.

A separation on a feature whose values are nearly all singletons is not evidence, so
every reported separation carries the number of distinct values and the largest cell,
and separations whose cells are mostly singletons are flagged as vacuous.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import os
from collections import Counter, defaultdict

from .code import TwoBlockCode
from .components import summary as comp_summary
from .solve import DATA

FEATURES = ["d_canon", "ord_d", "index_N_over_ord_d", "d_in_2G", "ord_d_mod4",
            "ord_delta0", "n_components", "min_component_n", "theorem1_obstructed"]
FIELDS = (["instance", "N", "group", "A", "B", "status", "time_s", "d", "delta0"]
          + FEATURES)


def coincident_pair(code: TwoBlockCode):
    """The unique delta with |P(delta)| = 2, and the two (s,t) pairs realising it."""
    P = code.sum_sets()
    dbl = [(delta, sts) for delta, sts in P.items() if len(sts) == 2]
    if len(dbl) != 1 or any(len(v) > 2 for v in P.values()):
        return None
    delta0, ((s, t), (s2, t2)) = dbl[0][0], sorted(dbl[0][1])
    return delta0, (s, t), (s2, t2)


def features_of(code: TwoBlockCode) -> dict | None:
    cp = coincident_pair(code)
    if cp is None:
        return None
    G = code.G
    delta0, (s, t), (s2, t2) = cp
    d = G.sub(code.A[s], code.A[s2])
    # d and -d describe the same coincidence; canonicalise
    d_canon = min(d, G.sub(G.zero, d))
    twoG = G.doubles()
    cs = comp_summary(code)
    ordd = G.order_of(d)
    return dict(
        d=json.dumps(list(d)), delta0=json.dumps(list(delta0)),
        d_canon=json.dumps(list(d_canon)),
        ord_d=ordd, index_N_over_ord_d=code.N // ordd,
        d_in_2G=d in twoG, ord_d_mod4=ordd % 4,
        ord_delta0=G.order_of(delta0),
        n_components=cs["n_components"], min_component_n=cs["min_component_n"],
        theorem1_obstructed=cs["theorem1_obstructed"],
    )


def build(src: str | None = None, out: str | None = None) -> tuple[list[dict], str]:
    src = src or os.path.join(DATA, "h2_sharpness.csv")
    out = out or os.path.join(DATA, "h4_features.csv")
    rows = []
    skipped = 0
    for r in csv.DictReader(open(src)):
        if r["class"] != "C1":
            continue
        code = TwoBlockCode((int(r["N"]),), [tuple(a) for a in json.loads(r["A"])],
                            [tuple(b) for b in json.loads(r["B"])], r["name"])
        f = features_of(code)
        if f is None:
            skipped += 1
            continue
        rows.append(dict(instance=r["name"], N=int(r["N"]), group=code.G.label(),
                         A=r["A"], B=r["B"], status=r["status"],
                         time_s=r["time_s"], **f))
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["N"], r["instance"])))
    if skipped:
        print(f"  {skipped} rows skipped: multiplicity pattern is not a single coincidence")
    return rows, out


# --------------------------------------------------------------------------
# contingency tables and exact separation
# --------------------------------------------------------------------------
def contingency(rows, key) -> dict:
    tab: dict = defaultdict(Counter)
    for r in rows:
        tab[r[key]][r["status"]] += 1
    return tab


def separates(rows, keys) -> dict:
    """Does the joint value of `keys` never mix SAT with UNSAT?"""
    tab: dict = defaultdict(Counter)
    for r in rows:
        tab[tuple(r[k] for k in keys)][r["status"]] += 1
    mixed = [v for v, c in tab.items() if len(c) > 1]
    cells = sorted((sum(c.values()) for c in tab.values()), reverse=True)
    singleton = sum(1 for n in cells if n == 1)
    return dict(keys=list(keys), separates=not mixed, n_values=len(tab),
                max_cell=cells[0] if cells else 0,
                singleton_cells=singleton,
                frac_singleton=round(singleton / len(tab), 3) if tab else 0.0,
                n_mixed_values=len(mixed))


def report(rows, verbose: bool = True) -> dict:
    dec = [r for r in rows if r["status"] in ("SAT", "UNSAT")]
    tally = Counter(r["status"] for r in rows)
    out = dict(n_rows=len(rows), n_decided=len(dec), status=dict(tally),
               single=[], pairs=[], notes=[])
    if verbose:
        print(f"\nH4 step 3: {len(dec)} decided class-C1 instances "
              f"({tally['SAT']} SAT, {tally['UNSAT']} UNSAT, "
              f"{len(rows)-len(dec)} other)\n")

    for f in FEATURES:
        tab = contingency(dec, f)
        sep = separates(dec, (f,))
        out["single"].append(sep)
        if verbose:
            vals = sorted(tab, key=lambda v: (str(type(v)), v))
            print(f"--- {f} ---  ({sep['n_values']} distinct values, "
                  f"separates={sep['separates']})")
            shown = vals if len(vals) <= 14 else vals[:14]
            for v in shown:
                c = tab[v]
                print(f"    {str(v):>14}  SAT={c['SAT']:4d}  UNSAT={c['UNSAT']:4d}"
                      + ("   <-- mixed" if len(c) > 1 else ""))
            if len(vals) > 14:
                print(f"    ... {len(vals)-14} more values")
            print()

    for a, b in itertools.combinations(FEATURES, 2):
        out["pairs"].append(separates(dec, (a, b)))

    def useful(s):
        # a separation whose cells are almost all singletons carries no information
        return s["separates"] and s["frac_singleton"] < 0.5 and s["max_cell"] >= 5

    sing_sep = [s for s in out["single"] if s["separates"]]
    pair_sep = [s for s in out["pairs"] if s["separates"]]
    if verbose:
        print("=" * 72)
        print(f"single features that separate SAT from UNSAT exactly: "
              f"{[s['keys'][0] for s in sing_sep] or 'none'}")
        for s in sing_sep:
            print(f"    {s['keys'][0]}: {s['n_values']} values, max cell {s['max_cell']}, "
                  f"{100*s['frac_singleton']:.0f}% singleton cells"
                  f"{'' if useful(s) else '   <-- vacuous, values are nearly all unique'}")
        print(f"\nfeature pairs that separate exactly: {len(pair_sep)}")
        for s in sorted(pair_sep, key=lambda x: -x["max_cell"]):
            print(f"    {s['keys'][0]} x {s['keys'][1]}: {s['n_values']} values, "
                  f"max cell {s['max_cell']}, {100*s['frac_singleton']:.0f}% singleton"
                  f"{'' if useful(s) else '   <-- vacuous'}")
        real = [s for s in sing_sep + pair_sep if useful(s)]
        print("\n" + ("NO non-vacuous exact separation was found."
                      if not real else
                      f"non-vacuous exact separations: "
                      f"{[' x '.join(s['keys']) for s in real]}"))
        print("=" * 72)
    out["non_vacuous"] = [s for s in sing_sep + pair_sep if useful(s)]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="H4 feature analysis on class C1.")
    ap.add_argument("--src", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--twisted", action="store_true",
                    help="also run the invariant / eps-twisted-invariant study")
    ap.add_argument("--depth", type=int, default=6)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--zm", action="store_true",
                    help="run the eps: G -> Z_m study for m = 2..12 (H4 step 5)")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--which", default="even", choices=("even", "odd", "all"))
    ap.add_argument("--budget", type=int, default=200000,
                    help="conflict budget per solve; 0 means unlimited")
    a = ap.parse_args(argv)
    rows, out = build(a.src, a.out)
    print(f"wrote {out} ({len(rows)} class-C1 instances)")
    rep = report(rows)
    with open(os.path.join(DATA, "h4_separation.json"), "w") as f:
        json.dump(rep, f, indent=1, default=str)
    print(f"wrote {os.path.join(DATA, 'h4_separation.json')}")
    if a.twisted:
        run_twisted_study(a.depth, a.src, limit=a.limit)
    if a.zm:
        run_zm_study(a.depth, workers=a.workers, limit=a.limit,
                     which=a.which, conf_budget=(a.budget or None))
        rep5 = report_zm()
        with open(os.path.join(DATA, "h4_zm_report.json"), "w") as f:
            json.dump(rep5, f, indent=1, default=str)
    return 0




# --------------------------------------------------------------------------
# H4 step 4: invariant and eps-twisted invariant schedules at depth 6
# --------------------------------------------------------------------------
TWIST_FIELDS = ["instance", "N", "group", "eps", "eps_coeffs", "trivial", "exists",
                "labels", "valid_layering", "proper_by_simulation", "status",
                "consistent"]


def run_twisted_study(depth: int = 6, src: str | None = None, out: str | None = None,
                      limit: int | None = None) -> str:
    from .encode import (find_invariant_schedule, find_twisted_invariant_schedule,
                         homomorphisms_to_Z2)
    from .simulate import is_proper_by_simulation, is_valid_layering

    src = src or os.path.join(DATA, "h2_sharpness.csv")
    out = out or os.path.join(DATA, "h4_twisted.csv")
    c1 = [r for r in csv.DictReader(open(src)) if r["class"] == "C1"]
    if limit:
        c1 = c1[:limit]

    def build_code(r):
        return TwoBlockCode((int(r["N"]),), [tuple(a) for a in json.loads(r["A"])],
                            [tuple(b) for b in json.loads(r["B"])], r["name"])

    # (i) the plain invariant search on one C1 instance
    probe = build_code(c1[0])
    plain = find_invariant_schedule(probe, depth)
    print(f"H4 step 4(i): plain translation-invariant search on {probe.name} "
          f"(N={probe.N}) at depth {depth}: "
          f"{'FOUND' if plain else 'none'} (expected none)")

    # (ii) every eps, every C1 instance
    rows = []
    for r in c1:
        code = build_code(r)
        for h in homomorphisms_to_Z2(code.G):
            res = find_twisted_invariant_schedule(code, depth, h["coeffs"])
            rec = dict(instance=r["name"], N=int(r["N"]), group=code.G.label(),
                       eps=h["name"], eps_coeffs=json.dumps(list(h["coeffs"])),
                       trivial=h["trivial"], exists=res is not None, labels="",
                       valid_layering="", proper_by_simulation="",
                       status=r["status"], consistent="")
            if res is not None:
                labels, lay = res
                v = is_valid_layering(code, lay, depth)
                p = is_proper_by_simulation(code, lay, depth)
                if not (v and p):
                    raise AssertionError(
                        f"{r['name']} eps={h['name']}: twisted schedule failed "
                        f"verification (valid={v}, proper={p}) -- encoding is wrong")
                rec["labels"] = json.dumps(
                    {f"{a}{b}": {str(e): list(v2) for e, v2 in d.items()}
                     for (a, b), d in labels.items()})
                rec["valid_layering"] = v
                rec["proper_by_simulation"] = p
            if r["status"] in ("SAT", "UNSAT"):
                rec["consistent"] = not (rec["exists"] and r["status"] == "UNSAT")
            rows.append(rec)

    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TWIST_FIELDS)
        w.writeheader()
        w.writerows(rows)

    found = [r for r in rows if r["exists"]]
    nontriv = [r for r in found if not r["trivial"]]
    bad = [r for r in rows if r["consistent"] is False]
    print(f"\nH4 step 4(ii): {len(rows)} (instance, eps) searches over "
          f"{len({r['instance'] for r in rows})} class-C1 instances at depth {depth}")
    print(f"  twisted schedules found : {len(found)}  "
          f"(non-trivial eps: {len(nontriv)})")
    if found:
        insts = {r["instance"] for r in found}
        sat = {r["instance"] for r in found if r["status"] == "SAT"}
        print(f"  instances admitting one : {len(insts)}; "
              f"of these {len(sat)} are recorded SAT and {len(insts)-len(sat)} are not")
        print(f"  every found schedule re-verified by F2 simulation: "
              f"{all(r['proper_by_simulation'] is True for r in found)}")
        by_eps = Counter(r["eps"] for r in found)
        print(f"  by eps: {dict(by_eps)}")
        adm = Counter(r["eps"] for r in rows)
        print(f"  searches per eps (i.e. groups admitting it): {dict(adm)}")
    else:
        print("  no twisted schedule exists at this depth for any C1 instance "
              "and any eps.")
    if bad:
        print(f"  INCONSISTENT (schedule found but recorded UNSAT): "
              f"{[r['instance'] for r in bad][:10]}")

    # does "admits a twisted invariant schedule" separate SAT from UNSAT exactly?
    per_inst: dict[str, dict] = {}
    for r in rows:
        d = per_inst.setdefault(r["instance"], dict(status=r["status"], adm=False))
        d["adm"] = d["adm"] or r["exists"]
    dec = {k: v for k, v in per_inst.items() if v["status"] in ("SAT", "UNSAT")}
    sat = [k for k, v in dec.items() if v["status"] == "SAT"]
    uns = [k for k, v in dec.items() if v["status"] == "UNSAT"]
    sat_yes = [k for k in sat if dec[k]["adm"]]
    uns_yes = [k for k in uns if dec[k]["adm"]]
    print(f"\n  admits a twisted invariant schedule vs recorded status:")
    print(f"    SAT   : {len(sat_yes):4d} of {len(sat):4d} admit one")
    print(f"    UNSAT : {len(uns_yes):4d} of {len(uns):4d} admit one   <- must be 0")
    if not uns_yes and sat and len(sat_yes) == len(sat):
        print("    => twisted-invariant existence separates SAT from UNSAT exactly "
              "on this sample (a sufficient condition that is also necessary here).")
    elif not uns_yes:
        print(f"    => sufficient but not necessary: {len(sat)-len(sat_yes)} SAT "
              f"instances admit no twisted invariant schedule.")
    print(f"wrote {out}")
    return out



# --------------------------------------------------------------------------
# H4 step 5: eps: G -> Z_m twisted schedules for m = 2..12
# --------------------------------------------------------------------------
ZM_FIELDS = ["instance", "N", "status", "theorem1_obstructed", "m", "eps", "eps_coeffs",
             "image_size", "surjective", "exists", "valid_layering",
             "proper_by_simulation"]
MS = list(range(2, 13))


def even_divisors(N: int) -> list[int]:
    """Even m with m | N and 2 <= m < N.

    Odd m are excluded by the even-order criterion: a twisted schedule requires
    |M| even, where M = <eps(d)> <= Z_m, and for odd m every |M| is odd.
    """
    return [m for m in range(2, N) if N % m == 0 and m % 2 == 0]


def _zm_one(job) -> list[dict]:
    """All m for one instance.  `which` selects even, odd or all divisors of N."""
    from .encode import UNKNOWN, find_twisted_invariant_schedule_Zm, homomorphisms_to_Zm
    from .simulate import is_proper_by_simulation, is_valid_layering
    row, depth, which, budget = job
    N = int(row["N"])
    code = TwoBlockCode((N,), [tuple(a) for a in json.loads(row["A"])],
                        [tuple(b) for b in json.loads(row["B"])], row["instance"])
    ms = {"even": even_divisors, "odd": odd_divisors,
          "all": lambda n: sorted(set(even_divisors(n)) | set(odd_divisors(n)))}[which](N)
    out = []
    for m in ms:
        for h in homomorphisms_to_Zm(code.G, m):
            res = find_twisted_invariant_schedule_Zm(code, depth, h["coeffs"], m,
                                                     conf_budget=budget)
            unknown = (res == UNKNOWN)
            rec = dict(instance=row["instance"], N=N, status=row["status"],
                       theorem1_obstructed=row.get("theorem1_obstructed", ""),
                       m=m, eps=h["name"], eps_coeffs=json.dumps(list(h["coeffs"])),
                       image_size=h["image_size"], surjective=h["image_size"] == m,
                       exists=("UNKNOWN" if unknown else (res is not None)),
                       valid_layering="", proper_by_simulation="")
            if not unknown and res is not None:
                lay = res[1]
                v = is_valid_layering(code, lay, depth)
                p = is_proper_by_simulation(code, lay, depth)
                if not (v and p):
                    raise AssertionError(
                        f"{row['instance']} m={m} {h['name']}: twisted schedule failed "
                        f"verification (valid={v}, proper={p})")
                rec["valid_layering"], rec["proper_by_simulation"] = v, p
            out.append(rec)
    return out


def run_zm_study(depth: int = 6, ms=None, feat: str | None = None,
                 out: str | None = None, workers: int = 16,
                 limit: int | None = None, which: str = "even",
                 conf_budget: int | None = 200000) -> str:
    """5a.  Writes each instance's rows as soon as it finishes, so an interrupted run
    keeps everything already computed and a re-run resumes where it stopped."""
    import time as _t
    from concurrent.futures import ProcessPoolExecutor, as_completed
    feat = feat or os.path.join(DATA, "h4_features.csv")
    out = out or os.path.join(DATA, "h4_twisted_zm.csv")
    rows = list(csv.DictReader(open(feat)))
    if limit:
        rows = rows[:limit]
    done_pairs = set()
    if os.path.exists(out):
        for r in csv.DictReader(open(out)):
            done_pairs.add((r["instance"], int(r["m"])))
    todo = []
    for r in rows:
        want = {"even": even_divisors, "odd": odd_divisors,
                "all": lambda n: sorted(set(even_divisors(n)) | set(odd_divisors(n)))
                }[which](int(r["N"]))
        if any((r["instance"], m) not in done_pairs for m in want):
            todo.append(r)
    print(f"5a[{which}]: {len(todo)} of {len(rows)} instances still to do "
          f"(resuming from {len(done_pairs)} recorded (instance,m) pairs); "
          f"conflict budget {conf_budget}; {workers} workers", flush=True)
    if not todo:
        print("  nothing to do")
        return out

    new_file = not os.path.exists(out)
    fh = open(out, "a", newline="")
    w = csv.DictWriter(fh, fieldnames=ZM_FIELDS)
    if new_file:
        w.writeheader()
        fh.flush()
    n_rows, t0, done = 0, _t.time(), 0
    try:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(_zm_one, (r, depth, which, conf_budget)) for r in todo]
            for fut in as_completed(futs):
                for rec in fut.result():
                    if (rec["instance"], rec["m"]) in done_pairs:
                        continue
                    w.writerow(rec)
                    n_rows += 1
                fh.flush()                       # nothing is held in memory
                done += 1
                if done % 25 == 0 or done == len(todo):
                    print(f"  [{done:4d}/{len(todo)}] {n_rows} rows written, "
                          f"{_t.time()-t0:.0f}s", flush=True)
    finally:
        fh.close()
    print(f"wrote {out} (+{n_rows} rows)")
    return out


def _v2(n: int) -> int:
    v = 0
    while n % 2 == 0 and n:
        n //= 2
        v += 1
    return v


def report_zm(feat: str | None = None, zm: str | None = None, verbose: bool = True) -> dict:
    """H4 steps 5c/5d/5e: equivalence with SAT, smallest working m, ord(d) relation."""
    feat = feat or os.path.join(DATA, "h4_features.csv")
    zm = zm or os.path.join(DATA, "h4_twisted_zm.csv")
    F = {r["instance"]: r for r in csv.DictReader(open(feat))}
    Z = list(csv.DictReader(open(zm)))

    per: dict[str, dict] = {}
    for r in Z:
        d = per.setdefault(r["instance"], dict(found_ms=set(), status=r["status"],
                                               obstructed=r["theorem1_obstructed"]))
        if r["exists"] == "True":
            d["found_ms"].add(int(r["m"]))

    # 5c -- soundness first: a twisted schedule on an UNSAT instance is impossible
    bad = [(i, sorted(v["found_ms"])) for i, v in per.items()
           if v["status"] == "UNSAT" and v["found_ms"]]
    if bad:
        raise AssertionError(
            "ABORT: twisted invariant schedule found for instances recorded UNSAT: "
            f"{bad[:10]} -- this cannot happen if the encoding is correct")

    rows = []
    for i, v in per.items():
        f = F.get(i, {})
        ordd = int(f.get("ord_d", 0) or 0)
        # a twisted schedule expanded and passed through F2 simulation is a witness:
        # it settles SAT even where the solver timed out
        resolved = "SAT" if v["found_ms"] else v["status"]
        rows.append(dict(instance=i, N=int(f.get("N", 0) or 0), status=v["status"],
                         status_resolved=resolved,
                         theorem1_obstructed=v["obstructed"],
                         any_twisted=bool(v["found_ms"]),
                         smallest_m=(min(v["found_ms"]) if v["found_ms"] else ""),
                         n_working_m=len(v["found_ms"]),
                         working_ms=json.dumps(sorted(v["found_ms"])),
                         ord_d=ordd, v2_ord_d=_v2(ordd) if ordd else "",
                         three_div_ord_d=(ordd % 3 == 0) if ordd else "",
                         d_in_2G=f.get("d_in_2G", ""),
                         ord_delta0=f.get("ord_delta0", "")))
    out_csv = os.path.join(DATA, "h4_zm_summary.csv")
    with open(out_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["N"], r["instance"])))

    # 5c -- restrict to instances Theorem 1 does not already obstruct
    elig = [r for r in rows if r["theorem1_obstructed"] != "True"
            and r["status"] in ("SAT", "UNSAT")]
    tab = defaultdict(Counter)
    for r in elig:
        tab[r["any_twisted"]][r["status"]] += 1
    sat_no = [r["instance"] for r in elig if r["status"] == "SAT" and not r["any_twisted"]]
    uns_yes = [r["instance"] for r in elig if r["status"] == "UNSAT" and r["any_twisted"]]

    upgraded = [r for r in rows if r["status"] == "TIMEOUT" and r["any_twisted"]]
    still_to = [r for r in rows if r["status"] == "TIMEOUT" and not r["any_twisted"]]
    if verbose:
        print(f"\nH4 step 5: timeouts settled by a verified twisted witness: "
              f"{len(upgraded)} of {len(upgraded)+len(still_to)}")
        if upgraded:
            print(f"  {[r['instance'] for r in upgraded][:12]}"
                  f"{' ...' if len(upgraded) > 12 else ''}")
        print(f"\nH4 step 5c: {len(elig)} class-C1 instances that Theorem 1 does NOT "
              f"obstruct (of {len(rows)} total)\n")
        print(f"  {'any twisted m in 2..12':>24} | {'SAT':>6} {'UNSAT':>7}")
        print("  " + "-" * 42)
        for k in (True, False):
            print(f"  {str(k):>24} | {tab[k]['SAT']:6d} {tab[k]['UNSAT']:7d}")
        print()
        print(f"  SAT with no twisted schedule (exceptions): {len(sat_no)}")
        if sat_no:
            print(f"    {sat_no[:15]}{' ...' if len(sat_no) > 15 else ''}")
        print(f"  UNSAT with a twisted schedule            : {len(uns_yes)}  "
              f"<- must be 0 (would have aborted)")
        eq = not sat_no and not uns_yes
        print(f"\n  => 'some m in 2..12 admits a twisted schedule' is "
              f"{'EXACTLY equivalent to SAT' if eq else 'NOT equivalent to SAT'} "
              f"on this sample.")
        sep = separates(elig, ("any_twisted",))
        print(f"     separation check: {sep['n_values']} values, max cell "
              f"{sep['max_cell']}, {100*sep['frac_singleton']:.0f}% singleton cells "
              f"-> {'non-vacuous' if sep['max_cell'] >= 5 and sep['frac_singleton'] < 0.5 else 'VACUOUS'}")

        # 5d -- smallest working m against the 2-adic valuation of ord(d)
        print(f"\nH4 step 5d: smallest working m vs ord(d)\n")
        grid = defaultdict(Counter)
        for r in elig:
            grid[(r["v2_ord_d"], r["three_div_ord_d"])][r["smallest_m"] or "none"] += 1
        allm = sorted({k for c in grid.values() for k in c},
                      key=lambda x: (x == "none", x))
        hdr = f"  {'v2(ord d)':>10} {'3|ord d':>8} | " + " ".join(f"{str(k):>5}" for k in allm)
        print(hdr)
        print("  " + "-" * (len(hdr) - 2))
        for kk in sorted(grid, key=lambda x: (x[0] if x[0] != "" else -1, x[1])):
            c = grid[kk]
            print(f"  {str(kk[0]):>10} {str(kk[1]):>8} | "
                  + " ".join(f"{c.get(k,0):5d}" for k in allm))
        print("\n  (columns are the smallest m in 2..12 that admits a twisted schedule)")
        for feat_name in ("v2_ord_d", "three_div_ord_d", "d_in_2G", "ord_d"):
            sp = separates(elig, (feat_name,))
            print(f"  separation by {feat_name:16}: exact={sp['separates']}, "
                  f"{sp['n_values']} values, max cell {sp['max_cell']}, "
                  f"{100*sp['frac_singleton']:.0f}% singleton"
                  + ("" if sp["separates"] and sp["max_cell"] >= 5
                     and sp["frac_singleton"] < 0.5 else "   (not a usable separation)"))
    print(f"wrote {out_csv}")
    return dict(n_eligible=len(elig), contingency={str(k): dict(v) for k, v in tab.items()},
                sat_without_twisted=sat_no, unsat_with_twisted=uns_yes,
                equivalent=not sat_no and not uns_yes,
                n_timeout=len(upgraded) + len(still_to),
                timeouts_settled_by_witness=[r["instance"] for r in upgraded],
                out=out_csv)




def odd_divisors(N: int) -> list[int]:
    """Odd m with m | N and 3 <= m < N."""
    return [m for m in range(3, N) if N % m == 0 and m % 2 == 1]


if __name__ == "__main__":
    raise SystemExit(main())

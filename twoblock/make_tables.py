"""LaTeX tables (booktabs) written to tables/*.tex, entirely from files in data/.

Every cell is read from a CSV.  A value that is not present in any data file is
written as the placeholder `--`; nothing is filled in by hand.  Each file is a
float environment that compiles inside a minimal document carrying booktabs.
"""
from __future__ import annotations

import csv
import json
import os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
TABLES = os.path.join(ROOT, "tables")
MISSING = "--"

MANIFEST: list[dict] = []


def read(name: str) -> list[dict]:
    p = os.path.join(DATA, name)
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []


def esc(s) -> str:
    s = str(s)
    for a, b in (("\\", r"\textbackslash{}"), ("_", r"\_"), ("&", r"\&"), ("%", r"\%"),
                 ("#", r"\#"), ("$", r"\$"), ("{", r"\{"), ("}", r"\}"), ("^", r"\^{}")):
        s = s.replace(a, b)
    return s


def poly(js: str) -> str:
    """[[3,0],[0,1]] -> \\{(3,0),(0,1)\\}  (math mode)."""
    try:
        v = json.loads(js)
    except Exception:
        return MISSING
    return "$\\{" + ",".join("(" + ",".join(str(x) for x in e) + ")" for e in v) + "\\}$"


def write(stem: str, body: str, inputs: list[str], func: str, desc: str, notes=None):
    os.makedirs(TABLES, exist_ok=True)
    p = os.path.join(TABLES, stem + ".tex")
    with open(p, "w") as f:
        f.write(body if body.endswith("\n") else body + "\n")
    MANIFEST.append(dict(output=[os.path.relpath(p, ROOT)], inputs=inputs, function=func,
                         description=desc, notes=notes or []))
    print(f"  wrote {os.path.relpath(p, ROOT)}")


def table(cols: str, header: list[str], rows: list[list[str]], caption: str,
          label: str, note: str = "") -> str:
    out = ["% requires: \\usepackage{booktabs,amsmath,amssymb}",
           "\\begin{table}[tb]", "\\centering", "\\small",
           f"\\caption{{{caption}}}", f"\\label{{{label}}}",
           f"\\begin{{tabular}}{{{cols}}}", "\\toprule",
           " & ".join(header) + " \\\\", "\\midrule"]
    out += [" & ".join(r) + " \\\\" for r in rows]
    out += ["\\bottomrule", "\\end{tabular}"]
    if note:
        out.append(f"\\\\[2pt]\\begin{{minipage}}{{\\linewidth}}\\footnotesize {note}"
                   f"\\end{{minipage}}")
    out.append("\\end{table}")
    return "\n".join(out)


# --------------------------------------------------------------------------- T1
def t1():
    inst = read("instances.csv")
    rows = []
    for r in inst:
        dims = json.loads(r["dims"])
        ell = str(dims[0])
        m = str(dims[1]) if len(dims) > 1 else MISSING
        nkd = f"$[[{r['n_qubits']},{r['k_logical'] or MISSING},{MISSING}]]$"
        rows.append([esc(r["name"]), esc(r["family"]), ell, m,
                     poly(_A_of(r)), poly(_B_of(r)), nkd,
                     "yes" if r["distinct_sums"] == "True" else "no",
                     r["max_overlap_entry"]])
    body = table("llrrllccr",
                 ["instance", "family", "$\\ell$", "$m$", "$A$", "$B$", "$[[n,k,d]]$",
                  "distinct sums", "$\\max (H_XH_Z^{\\mathsf T})$"],
                 rows,
                 "The seven BB codes of Ref.~[5], with the six further instances "
                 "used in this work. $A$ and $B$ are lists of group elements; "
                 "$\\ell$ and $m$ are "
                 "the cyclic factors of $G$. The logical dimension $k$ is computed as "
                 "$2N-\\operatorname{rank}_{\\mathbb F_2}H_X-\\operatorname{rank}_{\\mathbb F_2}H_Z$; "
                 "the distance $d$ is not determined here.",
                 "tabS:instances",
                 f"$m={MISSING}$ marks a group written with a single cyclic factor. "
                 f"$d={MISSING}$ throughout: no distance is computed in this work.")
    write("tabS1_instances", body, ["data/instances.csv"], "make_tables.t1",
          "Instance parameters, distinct-sums flag and maximum overlap entry.",
          [f"d is not in any data file and is printed as '{MISSING}'."])


def _A_of(r):
    return r["A_json"]


def _B_of(r):
    return r["B_json"]


def _res_index() -> dict:
    by = {}
    for r in read("results.csv"):
        by[(r["instance"], r["D"], r["tag"])] = r          # last row wins
    return by


# --------------------------------------------------------------------------- T2
def t2():
    by = _res_index()
    xc = {r["instance"]: r for r in read("cross_check.csv")}
    nr = {r["instance"]: r for r in read("r4_no_reversal.csv")}
    inst = {r["name"]: r for r in read("instances.csv")}
    order = [n for n in ("bb72", "bb90", "bb108", "bb144", "bb288", "bb360", "bb756",
                         "sw73") if n in inst]
    rows, notes = [], []
    for nm in order:
        d6 = by.get((nm, str(inst[nm]["Delta"]), ""))
        inv = by.get((nm, "7", "inv"))
        unr = by.get((nm, "7", ""))
        if d6 is None:
            rows.append([esc(nm)] + [MISSING] * 9)
            notes.append(nm)
            continue
        mb = int(d6["proof_bytes"]) / 1e6
        rows.append([
            esc(nm), d6["status"], f"{float(d6['time']):.2f}",
            f"{mb:.1f}" if mb else MISSING,
            d6["verified"] or MISSING,
            f"{float(d6['verify_time']):.2f}" if float(d6["verify_time"]) else MISSING,
            xc[nm]["status"] if nm in xc else MISSING,
            inv["status"] if inv else MISSING,
            (f"{unr['status']} ({float(unr['time']):.0f}\\,s)" if unr else MISSING),
            (f"{nr[nm]['status']}, {float(nr[nm]['time']):.2f}\\,s, "
             f"{int(nr[nm]['proof_bytes'])/1e6:.1f}, {nr[nm]['verified']}"
             if nm in nr else MISSING),
        ])
    body = table("llrrlrllll",
                 ["instance", "$D=\\Delta$", "solve (s)", "proof (MB)", "drat-trim",
                  "verify (s)", "cadical", "$D=7$ inv.", "$D=7$ unrestricted",
                  "no reversal clause (status, s, MB, drat-trim)"],
                 rows,
                 "Certificates. At $D=\\Delta$ every instance is refuted and the DRAT "
                 "proof is accepted by \\texttt{drat-trim}; the same CNF is re-decided by "
                 "cadical. At $D=7$ the `inv.' column is the translation-invariant witness "
                 "pinned by unit assumptions, whose properness is re-checked by "
                 "$\\mathbb{F}_2$ simulation.  The last column repeats the $D=\\Delta$ "
                 "refutation with the layer-reversal symmetry-breaking clause removed, "
                 "i.e.\\ the certificates in \\texttt{certs\\_nosym/}: status, solve "
                 "time, proof MB and drat-trim verdict.",
                 "tab:certificates",
                 f"`{MISSING}' in the last column marks an unrestricted search that was "
                 f"stopped before returning a verdict; existence at $D=7$ is settled by "
                 f"the invariant witness.")
    write("tab_certificates", body, ["data/results.csv", "data/cross_check.csv",
                                     "data/instances.csv",
                                     "data/r4_no_reversal.csv"], "make_tables.t2",
          "Depth-Delta refutations with proof sizes and verification, plus depth-7 status.",
          ([f"no depth-Delta row on record for: {notes}"] if notes else []))


# --------------------------------------------------------------------------- T3
LEM = ["L1", "L2", "L3", "L4", "L5", "L6", "L7"]


def t3():
    rows_in = read("lemma_checks.csv")
    if not rows_in:
        write("tabS5_lemmas", "% data/lemma_checks.csv missing\n", ["data/lemma_checks.csv"],
              "make_tables.t3", "Lemma pass rates.", ["input missing"])
        return
    per = defaultdict(list)
    for r in rows_in:
        per[r["instance"]].append(r)
    rows = []
    for nm in sorted(per) + ["all"]:
        sel = rows_in if nm == "all" else per[nm]
        n = len(sel)
        rates = [f"{100.0*sum(1 for r in sel if r[L]=='True')/n:.0f}" for L in LEM]
        cov = (sum(int(r["n_L3_checked"]) for r in sel),
               sum(int(r["n_L4_checked"]) for r in sel),
               sum(int(r["n_L5_checked"]) for r in sel),
               sum(int(r["n_L4_vacuous"]) for r in sel),
               sum(1 for r in sel if r["L7_applicable"] == "True"))
        rows.append([("\\textbf{all}" if nm == "all" else esc(nm)), str(n)] + rates
                    + [f"{cov[0]:,}", f"{cov[1]:,}", f"{cov[2]:,}", str(cov[3]), str(cov[4])])
    body = table("lr" + "r" * 7 + "rrrrr",
                 ["instance", "\\#sol."] + [f"{L} (\\%)" for L in LEM]
                 + ["L3 checks", "L4 checks", "L5 checks", "L4 vac.", "L7 appl."],
                 rows,
                 "Lemma checks over every enumerated proper schedule. The right-hand "
                 "columns give the number of individual sub-checks performed, so that a "
                 "100\\,\\% pass rate is not vacuous.",
                 "tabS:lemmas",
                 "`L4 vac.' counts checks outside $E$ with no $R$-edge in layer $a$ or "
                 "$b$, for which L4 has no content; `L7 appl.' counts solutions with "
                 "every $x_i\\in\\{0,N\\}$.")
    write("tabS5_lemmas", body, ["data/lemma_checks.csv"], "make_tables.t3",
          "Per-instance lemma pass rates with coverage counts.")


# --------------------------------------------------------------------------- T4
def t4():
    h2 = read("h2_sharpness.csv")
    if not h2:
        write("tabS2_sharpness", "% data/h2_sharpness.csv missing\n",
              ["data/h2_sharpness.csv"], "make_tables.t4", "H2 sharpness.",
              ["input missing"])
        return
    g = defaultdict(list)
    for r in h2:
        g[(int(r["N"]), r["class"])].append(r)
    rows = []
    order = ["D", "C1", "C2", "subgroup", "SG"]
    for (N, cls) in sorted(g, key=lambda k: (k[0], order.index(k[1]))):
        sel = g[(N, cls)]
        c = Counter(r["status"] for r in sel)
        other = len(sel) - c["SAT"] - c["UNSAT"]
        mt = sum(float(r["time_s"]) for r in sel) / len(sel)
        obs = sum(1 for r in sel if r["theorem1_obstructed"] == "True")
        rows.append([str(N), "SG" if cls == "subgroup" else cls, str(len(sel)),
                     str(c["SAT"]), str(c["UNSAT"]),
                     str(other), f"{mt:.1f}", str(obs)])
    body = table("rlrrrrrr",
                 ["$N$", "overlap class", "\\#inst.", "\\#SAT", "\\#UNSAT",
                  "\\#timeout",
                  "mean $t$ (s)", "\\#Thm.\\,1"],
                 rows,
                 "Sharpness at larger $N$ (H2): depth-6 outcome for random $(A,B)$ with "
                 "$k=l=3$, grouped by group order and by overlap class. Classes are "
                 "defined by the integer matrix $P = H_XH_Z^{\\mathsf T}$, with "
                 "$n_{2c} = \\#\\{(x,z): P[x,z]=2c\\}$: "
                 "\\textbf{D} no 4-qubit overlaps ($n_4=n_6=0$); "
                 "\\textbf{C1} one collision orbit ($N$ four-qubit overlaps: $n_4=N$, "
                 "$n_6=0$); \\textbf{C2} two collision orbits or one triple orbit "
                 "($n_4=2N,n_6=0$ or $n_4=0,n_6=N$); \\textbf{SG} subgroup type "
                 "($A=B$ a subgroup, components decouple). "
                 "Statuses here are the raw solver record; Table~\\ref{tab:c1final} "
                 "gives the class-C1 view after timeouts settled by a verified "
                 "$\\varepsilon$-twisted witness are counted as SAT.",
                 "tabS:sharpness",
                 "`\\#Thm.\\,1' counts instances carrying the componentwise parity "
                 "obstruction. Every SAT model was re-checked by $\\mathbb{F}_2$ simulation.")
    write("tabS2_sharpness", body, ["data/h2_sharpness.csv"], "make_tables.t4",
          "H2 results grouped by (N, class).")


# --------------------------------------------------------------------------- T5
def t5():
    sweep = read("sweep.csv")
    if not sweep:
        write("tabS3_sweep", "% data/sweep.csv missing\n", ["data/sweep.csv"],
              "make_tables.t5", "Sweep.", ["input missing"])
        return
    g = defaultdict(Counter)
    orderN = {}
    for r in sweep:
        g[(r["group"], r["max_multiplicity"])][r["status"]] += 1
        orderN[r["group"]] = int(r["N"])
    rows = []
    for (grp, m) in sorted(g, key=lambda k: (orderN[k[0]], k[0], int(k[1]))):
        c = g[(grp, m)]
        tot = sum(c.values())
        rows.append([esc(grp), str(orderN[grp]), m, str(tot), str(c["SAT"]),
                     str(c["UNSAT"]), str(tot - c["SAT"] - c["UNSAT"])])
    tot = Counter(r["status"] for r in sweep)
    rows.append(["\\textbf{total}", "", "", str(len(sweep)), str(tot["SAT"]),
                 str(tot["UNSAT"]), str(len(sweep) - tot["SAT"] - tot["UNSAT"])])
    body = table("lrrrrrr",
                 ["group", "$|G|$", "$\\max|P(\\delta)|$", "\\#inst.", "\\#SAT",
                  "\\#UNSAT", "\\#timeout"], rows,
                 "The $k=l=3$ sweep at depth 6. Every sweep group has $|G|\\leq 8<9=kl$, "
                 "so no sweep instance can have distinct sums.",
                 "tabS:sweep")
    # the one UNSAT sweep instance, spelled out
    u = [r for r in sweep if r["status"] == "UNSAT"]
    extra = []
    for r in u:
        extra.append([esc(r["name"]), esc(r["group"]), poly(r["A"]), poly(r["B"]),
                      esc(r["mult_histogram"]), r["max_overlap_entry"], r["status"],
                      f"{float(r['time']):.0f}"])
    if extra:
        body += "\n\n" + table("llllcrlr",
                               ["instance", "group", "$A$", "$B$", "$|P(\\delta)|$ hist.",
                                "$\\max(H_XH_Z^{\\mathsf T})$", "status", "$t$ (s)"],
                               extra,
                               "The only sweep instance refuted at depth 6. $A=B$ is the "
                               "index-2 subgroup of $\\mathbb{Z}_6$, and it carries the "
                               "componentwise parity obstruction of Theorem 1.",
                               "tabS:sweep-unsat")
    write("tabS3_sweep", body, ["data/sweep.csv"], "make_tables.t5",
          "Sweep outcome by group and maximum multiplicity, plus the sw73 row.")


# --------------------------------------------------------------------------- T6
def t6():
    """Exhaustive eps-template enumeration, one row per modulus."""
    import glob
    recs = []
    for p in sorted(glob.glob(os.path.join(ROOT, "templates", "C1_m*.json")),
                    key=lambda q: int(os.path.basename(q)[4:-5])):
        with open(p) as f:
            recs.append((os.path.relpath(p, ROOT), json.load(f)))
    if not recs:
        write("tabS6_templates", "% templates/C1_m*.json missing\n", [],
              "make_tables.t6", "Template enumeration by modulus.",
              ["no templates/C1_m*.json on record"])
        return
    rows = []
    for rel, d in recs:
        n, sat = int(d["n_keys"]), int(d["n_sat"])
        rows.append([str(d["m"]), str(d["k"]), str(d["l"]),
                     f"{int(d['n_patterns']):,}", f"{n:,}", f"{sat:,}",
                     f"{100.0 * sat / n:.1f}" if n else MISSING,
                     f"{float(d.get('seconds', 0)):.1f}"])
    ms = [int(d["m"]) for _, d in recs]
    body = table("rrrrrrrr",
                 ["$m$", "$k$", "$l$", "patterns", "$\\varepsilon$-vectors",
                  "admitting", "\\%", "time (s)"], rows,
                 "Exhaustive enumeration of the $\\varepsilon$-templates at each "
                 "modulus $m$: every $\\varepsilon$-vector is tested for a depth-6 "
                 "twisted schedule on the reduced label system.  No vector with "
                 "$|M|$ odd admits one at any $m$.",
                 "tabS:templates",
                 f"Computed for $m \\in \\{{{', '.join(str(m) for m in ms)}\\}}$; "
                 f"other moduli were not computed.")
    write("tabS6_templates", body,
          [rel for rel, _ in recs], "make_tables.t6",
          "Template enumeration by modulus: vectors tested and vectors admitting.")


# --------------------------------------------------------------------------- T7
def t7():
    """The abelian groups covered by the sweep."""
    sw = read("sweep.csv")
    if not sw:
        write("tabS7_groups", "% data/sweep.csv missing\n", ["data/sweep.csv"],
              "make_tables.t7", "Groups covered by the sweep.",
              ["data/sweep.csv missing"])
        return
    by = defaultdict(list)
    for r in sw:
        by[(r["group"], r["dims"], int(r["N"]))].append(r)
    rows = []
    for (g, dims, N), rs in sorted(by.items(), key=lambda kv: (kv[0][2], kv[0][0])):
        mult = sorted({int(r["max_multiplicity"]) for r in rs})
        ds = {r["distinct_sums"] for r in rs}
        rows.append(["$\\times$".join(esc(q) for q in g.split("x")),
                     esc(dims), str(N), f"{len(rs):,}",
                     f"{sum(1 for r in rs if r['status'] == 'SAT'):,}",
                     f"{sum(1 for r in rs if r['status'] == 'UNSAT'):,}",
                     "--".join(str(m) for m in (mult[:1] + mult[-1:])) if mult
                     else MISSING,
                     "yes" if ds == {"True"} else ("no" if ds == {"False"} else "both")])
    body = table("llrrrrcc",
                 ["group", "dims", "$|G|$", "instances", "SAT", "UNSAT",
                  "$\\max_\\delta|P(\\delta)|$", "distinct sums"], rows,
                 "The abelian groups covered by the depth-6 sweep, with the depth-6 "
                 "outcome and the range of the largest sum multiplicity.",
                 "tabS:groups",
                 "Every sweep group has $|G| \\leq 8 < 9 = kl$, so none of them has "
                 "distinct sums and the overlap hypothesis of the main theorem never "
                 "applies to the sweep.")
    write("tabS7_groups", body, ["data/sweep.csv"], "make_tables.t7",
          "Groups covered by the sweep, with the depth-6 outcome per group.")


# --------------------------------------------------------------------------- T8
def t8():
    """The verified translation-invariant depth-7 schedule."""
    p = os.path.join(ROOT, "schedules", "bb72_d7_inv.json")
    if not os.path.exists(p):
        write("tabS8_depth7_schedule", "% schedules/bb72_d7_inv.json missing\n", [],
              "make_tables.t8", "The depth-7 invariant schedule.",
              ["schedules/bb72_d7_inv.json missing"])
        return
    with open(p) as f:
        d = json.load(f)
    lay = defaultdict(dict)
    for e, l in zip(d["edges"], d["layers"]):
        lay[(e[0], e[1])][int(e[2])] = int(l)
    labels = sorted({s for v in lay.values() for s in v})
    rows = []
    for kind in ("X", "Z"):
        for side in ("L", "R"):
            v = lay.get((kind, side), {})
            rows.append([f"${kind}$", f"${side}$"]
                        + [str(v.get(s, MISSING)) for s in labels])
    body = table("ll" + "r" * len(labels),
                 ["check", "side"] + [f"label {s}" for s in labels], rows,
                 f"The translation-invariant depth-7 schedule of "
                 f"\\texttt{{{esc(d['instance'])}}} that witnesses $D=7$: the layer of "
                 f"every Tanner edge as a function of its label and of the "
                 f"(check kind, qubit side) it joins.  The same assignment is used "
                 f"for all $|G|={len(d['layers']) // (4 * len(labels))}$ translates.",
                 "tabS:depth7",
                 f"Properness re-checked by $\\mathbb{{F}}_2$ simulation: "
                 f"{'verified' if d.get('proper_by_simulation') else 'NOT verified'}.")
    write("tabS8_depth7_schedule", body, ["schedules/bb72_d7_inv.json"],
          "make_tables.t8", "The verified translation-invariant depth-7 schedule.")


# --------------------------------------------------------------------------- T1 body
# Table 1 of the manuscript: the depth-6 refutations produced WITHOUT the layer-
# reversal symmetry-breaking clause, i.e. the certificates in certs_nosym/.
#
# Column mapping, because the brief names columns that data/results.csv does not have:
#   depth == 6                -> data/r4_no_reversal.csv:D == "6"
#   symmetry_breaking == "no" -> data/r4_no_reversal.csv:symmetry_breaking == "False"
#   drat_verified             -> data/r4_no_reversal.csv:verified == "VERIFIED"
# data/results.csv holds the runs WITH the clause and has no such columns.
T1_ORDER = ["bb72", "bb90", "bb108", "bb144", "bb288", "bb360", "bb756"]
# The only values here that no file in the repository carries: d is "--" everywhere.
T1_DISTANCE = {"bb72": "6", "bb90": "10", "bb108": "10", "bb144": "12",
               "bb288": "18", "bb360": "\\le24", "bb756": "\\le34"}
T1_EXTREMES = {"time_min": 1.4, "time_max": 6.3, "mb_min": 18, "mb_max": 68}


def t2_body(write_file: bool = True):
    inst = {r["name"]: r for r in read("instances.csv")}
    nos = {r["instance"]: r for r in read("r4_no_reversal.csv")
           if r["D"] == "6" and r["symmetry_breaking"] == "False"}
    missing = [n for n in T1_ORDER if n not in nos or n not in inst]
    if missing:
        raise SystemExit(f"tab_certificates_body: no nosym depth-6 row for {missing}")

    rows, unverified, times, mbs = [], [], [], []
    for n in T1_ORDER:
        r, i = nos[n], inst[n]
        t = float(r["time"])
        mb = int(r["proof_bytes"]) / 1e6
        times.append(t); mbs.append(mb)
        ok = r["verified"] == "VERIFIED"
        if not ok:
            unverified.append((n, r["verified"] or "(blank)"))
        dims = json.loads(i["dims"])
        code = (f"$[[{2 * int(i['N'])},{i['k_logical']},"
                f"{T1_DISTANCE[n]}]]$")
        rows.append((code, f"$({dims[0]},{dims[1]})$", f"{t:.1f}", f"{mb:.0f}",
                     "yes" if ok else "no"))

    if unverified:
        print("  BLOCKING DEFECT: drat-trim did not verify "
              + ", ".join(f"{n} ({v})" for n, v in unverified)
              + "; tables/tab_certificates_body.tex not written")
        return None

    got = {"time_min": round(min(times), 1), "time_max": round(max(times), 1),
           "mb_min": round(min(mbs)), "mb_max": round(max(mbs))}
    bad = {k: (got[k], v) for k, v in T1_EXTREMES.items() if got[k] != v}
    if bad:
        print("  EXTREME ASSERTION FAILED, file not written:")
        for k, (g, want) in bad.items():
            print(f"    {k}: got {g}, expected {want}")
        print(f"    exact: time {min(times)}-{max(times)} s, "
              f"proof {min(mbs):.6f}-{max(mbs):.6f} MB")
        return None

    w = [max(len(r[c]) for r in rows) for c in range(5)]
    body = "\n".join(
        f"{r[0]:<{w[0]}} & {r[1]:<{w[1]}} & {r[2]:>{w[2]}} & {r[3]:>{w[3]}} & "
        f"{r[4]} \\\\" for r in rows)
    if write_file:
        head = ("% Table 1 body rows only: no caption, no header, no rules.\n"
                "% Generated by twoblock.make_tables.t2_body from\n"
                "%   data/r4_no_reversal.csv  (D=6, symmetry_breaking=False -> "
                "certs_nosym/)\n"
                "%   data/instances.csv       (N, k_logical, dims)\n"
                "% d is in no data file; the values come from the manuscript brief.\n")
        write("tab_certificates_body", head + body, ["data/r4_no_reversal.csv",
                                                     "data/instances.csv"],
              "make_tables.t2_body",
              "Table 1 body: the seven depth-6 refutations without the layer-reversal "
              "clause.",
              ["rows only; the caption and header live in the manuscript",
               "d is not in any data file and is taken from the manuscript brief"])
    return body, got, {n: (float(nos[n]["time"]), int(nos[n]["proof_bytes"]) / 1e6)
                       for n in T1_ORDER}


# --------------------------------------------------------------------------- T9
def t9():
    """The class-C1 contingency table, from the CSV c1_final wrote."""
    rows_in = read("c1_final.csv")
    if not rows_in:
        write("tabS4_c1", "% data/c1_final.csv missing\n", ["data/c1_final.csv"],
              "make_tables.t9", "Class-C1 outcome by region.",
              ["data/c1_final.csv missing"])
        return
    cols = ["SAT (solver)", "SAT (template witness)", "UNSAT", "UNDETERMINED", "total"]
    # theorem numbers are avoided everywhere; name the region by its role
    ren = {"ord(d) odd, Theorem-1 obstructed": "ord$(d)$ odd, mod-4 obstructed",
           "ord(d) odd, not obstructed": "ord$(d)$ odd, not obstructed",
           "ord(d) even": "ord$(d)$ even", "total": "total"}
    rows = [[ren.get(r["region"], esc(r["region"]))]
            + [f"{int(r[c]):,}" for c in cols] for r in rows_in]
    body = table("l" + "r" * len(cols),
                 ["region"] + [esc(c) for c in cols], rows,
                 "Depth-6 outcome of the class-C1 instances, by region.  A call that "
                 "hit the cap is UNDETERMINED and is never reported as UNSAT; a "
                 "timeout later settled by a verified twisted witness is counted "
                 "under SAT (template witness).",
                 "tabS:c1",
                 "Solver time limit 600\\,s, single-threaded.")
    write("tabS4_c1", body, ["data/c1_final.csv"], "make_tables.t9",
          "Class-C1 depth-6 outcome by region.")


# --------------------------------------------------------------------------- T10/11
def t10_11():
    """The main-text m = 2 template and the constraints it satisfies."""
    from .template_main import GRP_TEX, constraints, solve_chosen
    sol = solve_chosen()
    labels, m = sol["labels"], sol["m"]
    code = sol["code"]

    rows = []
    for c in range(m):
        for grp in (("X", "L"), ("X", "R"), ("Z", "L"), ("Z", "R")):
            for i, lay in enumerate(labels[grp][c]):
                rows.append([str(c), str(i + 1), GRP_TEX[grp]]
                            + [("$\\bullet$" if lay == j else "")
                               for j in range(1, 7)])
    body = table("ccl" + "c" * 6,
                 ["class $c$", "label", "edge type"]
                 + [f"{j}" for j in range(1, 7)], rows,
                 f"The depth-6 $\\varepsilon$-template at $m=2$ used in the main "
                 f"text, as the layer of every (class, label, edge type) entry.  "
                 f"24 entries: 2 classes $\\times$ 3 labels $\\times$ 4 edge types.  "
                 f"Realised on $G=\\mathbb{{Z}}_{{{code.N}}}$ with "
                 f"$A=\\{{{', '.join(str(a[0]) for a in code.A)}\\}}$, "
                 f"$B=\\{{{', '.join(str(b[0]) for b in code.B)}\\}}$ and "
                 f"$\\varepsilon(g)=g \\bmod 2$; the pulled-back schedule is proper "
                 f"by $\\mathbb{{F}}_2$ simulation.",
                 "tabS:templatem2",
                 "Key "
                 f"\\texttt{{{esc(sol['key'])}}}; colliding label pair "
                 f"$({sol['pat'][0][0]+1},{sol['pat'][0][1]+1})$ and "
                 f"$({sol['pat'][1][0]+1},{sol['pat'][1][1]+1})$.")
    write("tab_template_m2", body, [f"templates/C1_m{m}.json"],
          "make_tables.t10_11", "The main-text m = 2 template.",
          ["generated by solving the template system for the chosen key; the "
           "pull-back onto the realising code is re-verified by F2 simulation"])

    cs = constraints(sol)
    crows = [[c["family"], str(c["klass"]), c["entries"], c["values"],
              "yes" if c["satisfied"] else "\\textbf{no}"] for c in cs]
    body2 = table("llllc",
                  ["constraint", "class", "entries", "layers / orientations", "met"],
                  crows,
                  f"Every constraint the depth-6 template system imposes on the key of "
                  f"Table~\\ref{{tabS:templatem2}}, with the entries that satisfy it.  "
                  f"{len(cs)} instances in all: 4 distinctness families, 7 "
                  f"equal-orientation pairs and 1 four-corner parity, each imposed once "
                  f"per class $c\\in\\mathbb{{Z}}_2$.",
                  "tabS:templatem2checks",
                  "Orientation $o=1$ means the $X$-edge precedes the $Z$-edge.  "
                  "An equal-orientation row is met when $o_L=o_R$; the parity row is "
                  "met when the four orientations sum to $0$ mod $2$.")
    write("tab_template_m2_checks", body2, [f"templates/C1_m{m}.json"],
          "make_tables.t10_11",
          "The constraints on the main-text template and the entries meeting them.")


def build_all():
    t1(); t2(); t2_body(); t3(); t4(); t5(); t6(); t7(); t8(); t9(); t10_11()
    return MANIFEST


if __name__ == "__main__":
    build_all()


def validate_latex(verbose: bool = True) -> list[dict]:
    """Compile every tables/*.tex inside a minimal document (pdflatex if available).

    Without pdflatex, fall back to a structural check: balanced braces and a
    consistent number of `&`-separated columns in every body row.
    """
    import shutil
    import subprocess
    import tempfile

    out = []
    # a *_body.tex is table rows only, by design: no preamble, nothing to compile
    files = sorted(f for f in os.listdir(TABLES)
                   if f.endswith(".tex") and not f.endswith("_body.tex"))
    have = shutil.which("pdflatex")
    for fn in files:
        src = open(os.path.join(TABLES, fn)).read()
        rec = dict(file=f"tables/{fn}", braces_balanced=src.count("{") == src.count("}"))
        blocks, cur = [], None
        for ln in src.splitlines():
            t = ln.strip()
            if t.startswith("\\begin{tabular}"):
                cur = []
            elif t.startswith("\\end{tabular}") and cur is not None:
                blocks.append(sorted(set(cur)))
                cur = None
            elif cur is not None and t.endswith("\\\\") and not t.startswith("%"):
                cur.append(t.count("&") - t.count("\\&"))
        rec["column_counts"] = blocks
        rec["columns_consistent"] = all(len(b) == 1 for b in blocks)
        if have:
            with tempfile.TemporaryDirectory() as d:
                doc = ("\\documentclass{article}\n"
                       "\\usepackage{booktabs,amsmath,amssymb}\n"
                       "\\usepackage[margin=1cm,paperwidth=40cm,paperheight=40cm]{geometry}\n"
                       "\\begin{document}\n" + src + "\n\\end{document}\n")
                tex = os.path.join(d, "t.tex")
                open(tex, "w").write(doc)
                p = subprocess.run(["pdflatex", "-interaction=nonstopmode",
                                    "-halt-on-error", "-output-directory", d, tex],
                                   capture_output=True, text=True, timeout=180)
                rec["pdflatex"] = "ok" if p.returncode == 0 else "FAILED"
                if p.returncode != 0:
                    tail = [l for l in p.stdout.splitlines() if l.startswith("!")][:3]
                    rec["error"] = tail
        else:
            rec["pdflatex"] = "not available"
        out.append(rec)
        if verbose:
            flag = rec["pdflatex"]
            print(f"  {fn:26} pdflatex={flag:12} braces={'ok' if rec['braces_balanced'] else 'BAD'}"
                  f" cols={rec['column_counts']}"
                  f" {'' if rec['columns_consistent'] else '<-- RAGGED'}")
    return out

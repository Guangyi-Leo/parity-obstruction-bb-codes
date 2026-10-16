"""Build every manuscript and supplementary figure, measure it, and write the
manifest, the captions and the layout-check log.

  ./.venv/bin/python figures/src/build.py        (or: make figures)

Nothing here is hand-placed: each figure is produced by its builder, measured at final
print size by figures/check_layout.py, and written as PDF (vector, fonts embedded) and
PNG at 600 dpi.  The build fails if any layout check fails or any cross-check of a
plotted number against its CSV disagrees.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import figstyle as S                                              # noqa: E402
S.use_style()

import check_layout as CL                                          # noqa: E402
import manuscript_figs as M
import round7 as R7                                        # noqa: E402
import check_text_numbers as CTN                                   # noqa: E402
import derived_values as DERIVED                                   # noqa: E402
import page_fit as PFIT                                            # noqa: E402
import si_figs as SI                                               # noqa: E402
sys.path.insert(0, os.path.join(S.FIGS))
import test_check_layout as CLTEST                                 # noqa: E402

ROOT, FIGS, DATA = S.ROOT, S.FIGS, S.DATA
DPI_PNG = 600

def _named(fn, src):
    """Tag a builder lambda with the function the manifest should record."""
    fn._src = src
    return fn


# (public name, builder, section, LaTeX label, old names kept as aliases, inputs,
#  caption sentences, notes)
FIGURES = [
    ("fig1_degree_bound_to_cross_term", _named(lambda: R7.build_fig1("fig1"), "round7.build_fig1"), "main",
     "fig:setup", ["fig1_setup_certificate"],
     ["data/fig1_scene.json", "data/fig1_violation.csv",
      "schedules/bb72_d7_inv.json"],
     ("The model, the two-qubit overlap constraint, a depth-6 colouring that fails "
      "it, and the depth-7 schedule that meets it.",
      "The lattice and the two circuit insets are built from data/fig1_scene.json; "
      "the violating overlap pair is data/fig1_violation.csv (bb72, N = 36, "
      "Delta = 6) and the depth-7 schedule is schedules/bb72_d7_inv.json.",
      "A depth-Delta colouring exists but cannot be proper: the two corners of one "
      "overlap pair take opposite orientations, so their parities do not cancel."),
     ["the depth-6 colouring drawn is a global proper 6-edge-colouring of all 432 "
      "edges; only properness fails"]),
    ("fig2_why_six_layers_fail", _named(lambda: R7.build_fig2("fig2"), "round7.build_fig2"), "main",
     "fig:mechanism", ["fig2_mechanism"],
     ["data/fig2_scene.json", "data/lemma_checks.csv"],
     ("The four ingredients of the lower bound, and the one change that makes "
      "depth six attainable.",
      "The staircase is built from data/fig2_scene.json; a + b = Delta + 1 is "
      "verified on all 417 enumerated schedules of data/lemma_checks.csv.",
      "F_L + F_R = 9 is odd while a proper schedule needs F_L = F_R, so depth Delta "
      "is impossible when the overlaps are two-qubit."),
     ["gamma(i) is a property of the model (MODEL.md), not of a data file",
      "the right-hand cap states the 2-height hypothesis of Theorem 15"]),
    ("fig3_where_depth6_is_attainable", _named(lambda: R7.build_fig3("fig3"), "round7.build_fig3"), "main",
     "fig:sharpness", ["fig3_decision_tree"],
     ["data/fig3_scene.json", "data/coverage.csv", "data/thm_six_coverage.csv",
      "data/c1_odd_unobstructed_certs.csv", "build_tex/main.aux"],
     ("Minimum depth of a proper schedule by collision structure.",
      "664 instances with a recorded depth-6 outcome, read from data/coverage.csv; "
      "the even-order column is data/thm_six_coverage.csv and the certified share "
      "of the solver refutations is data/c1_odd_unobstructed_certs.csv.",
      "Two of the three columns are settled by a theorem for their whole class; "
      "the odd-order column is decided instance by instance and 30 are open."),
     ["the even-order cells were merged: the 2-height lemma covers the whole class",
      "the supplementary table is quoted by the number LaTeX printed, read from "
      "build_tex/main.aux"]),
    ("figS1_proof_map", M.fig2, "si", "figS:proofmap", ["fig2_proof_map"],
     ["data/instances.csv", "data/c1_final.csv", "data/thm_six_coverage.csv",
      "templates/C1_m*.json", "data/template_force.csv", "data/cor3_hgp.csv",
      "data/pareto_front.csv", "build_tex/main.aux"],
     ("What depends on what: the three general obstructions, the main chain and the "
      "depth-six chain.",
      "Counts are read from data/instances.csv, data/c1_final.csv and "
      "data/thm_six_coverage.csv; the largest enumerated modulus from "
      "templates/C1_m*.json.",
      "The three obstructions are parallel consequences of M_pi = 0; only the "
      "depth-six chain rests on computation.  The two corollaries of the mod-4 "
      "theorem quote data/cor3_hgp.csv, the template chain data/template_force.csv "
      "and the competitive codes data/pareto_front.csv."),
     ["solid = proved, dashed = computational evidence, dotted = open"]),
    ("figS2_sweep_by_group", SI.fig_sweep_by_group, "si", "figS:sweep",
     ["fig_sweep_by_group"], ["data/sweep.csv"],
     ("Depth-6 outcome of the exhaustive sweep, by group and by the largest sum "
      "multiplicity S(delta).",
      "1,441 instances of data/sweep.csv over six abelian groups of order at most 8.",
      "Only one sweep instance is UNSAT at depth 6, and no sweep group has distinct "
      "sums."),
     []),
    ("figS3_templates_by_q", SI.fig_templates_by_q, "si", "figS:templates",
     ["fig_templates_by_m"],
     ["templates/C1_m2.json", "templates/C1_m3.json", "templates/C1_m4.json",
      "templates/C1_m5.json", "templates/C1_m6.json", "templates/C1_m8.json"],
     ("Exhaustive epsilon-template outcome by twist modulus q.",
      "Every epsilon-vector at q = 2, 3, 4, 5, 6, 8 (144 to 9,216 per modulus) from "
      "templates/C1_m*.json; q = 7, 9–12 and 16 were not computed.",
      "No vector with |M| odd admits a depth-6 twisted schedule at any q."),
     ["the figure aborts if the |M| odd row is ever non-zero"]),
    ("figS4_periods", SI.fig_periods, "si", "figS:periods", ["fig_periods"],
     ["data/mstar.csv", "data/coverage.csv"],
     ("Smallest proper divisor q* of N carrying a verified twisted schedule.",
      "The class-C1 instances data/coverage.csv records as satisfiable at depth 6, "
      "with q* from data/mstar.csv.",
      "Every q* found is even; 6 instances have no period within the cap."),
     ["log scale with a count on every bar, so the small bars stay readable"]),
    ("figS5_theorem1_profile", SI.fig_theorem1_profile, "si", "figS:mod4",
     ["fig_theorem1_profile"],
     ["data/h1_predictions.csv", "data/coverage.csv",
      "data/c1_final_instances.csv"],
     ("Where the componentwise mod-4 condition obstructs, and the resolved status of "
      "the same instances.",
      "598 class-C1 instances joined from data/h1_predictions.csv and "
      "data/coverage.csv.",
      "Obstruction coincides exactly with the residue 2 and ord(d) odd on this set, "
      "and no obstructed instance is satisfiable."),
     ["the figure aborts if an obstructed instance is drawn as SAT"]),
    ("figS6_certificates", M.fig5, "si", "figS:certificates",
     ["fig5_certificates", "figS1_certificates"],
     ["data/results.csv", "data/r4_no_reversal.csv"],
     ("Cost of the depth-6 certificates, with and without the layer-reversal clause.",
      "The eight depth-6 refutations of data/results.csv paired with the "
      "reversal-clause-free runs of data/r4_no_reversal.csv.",
      "The refutations survive removal of the only symmetry-breaking clause, at a "
      "modest cost in time and proof size."),
     ["MB = 10^6 bytes; Table I reports the values without the clause"]),
]


DEVIATIONS = [
 "- **fig5, lemma-check coverage.**  The brief asks for the periodicity split "
 "(5 invariant / 72 twisted / 340) *from `data/lemma_checks.csv`*.  That file has no "
 "periodicity column: the split lives in `data/r6_periodicity.csv` (column `klass`), "
 "which is what panel d reads.  Panel c reads the coverage itself from "
 "`data/lemma_checks.csv`.",
 "- **fig5, name of the third periodicity class.**  The brief calls it *aperiodic*.  "
 "The CSV class is `other`, and the previous round removed the word *aperiodic* "
 "project-wide, so the figure says **no proper period** instead.  The count, 340, is "
 "the brief's.",
 "- **fig5 placement.**  Assigned to the supplement, as the brief allows: the main "
 "text already carries a full-page proof map (fig2, 180 x 208 mm) and fig5 is another "
 "120 mm of column.",
 "- **fig5, the two class-D rows of R4.**  `data/r4_no_reversal.csv` has 9 rows; two "
 "of them (`h2_Z10_D_0`, `h2_Z12_D_0`) are not in the depth-6 certificate set of "
 "`data/results.csv`, so they carry no paired marker.  They are still counted in the "
 "'9 of 9 verified' statement, which is what the CSV supports.",
 "- **fig3, the observed supports.**  No enumerated instance has Delta = 6, so the "
 "panel draws the identity for the manuscript's case (Delta = 6, a + b = 7) and cites "
 "the observed pairs with their own Delta (oe43, Delta = 7).  The identity itself is "
 "asserted on all 417 solutions when the figure is built.",
 "- **No theorem numbers anywhere.**  The manuscript numbers by `\\label` and the "
 "numbering may shift, and there is no `supplement.tex` in the repository, so the SI "
 "numbering is not fixed either: every box and header names its result by role.  "
 "`Theorem 1` -> componentwise mod-4 obstruction, `Theorem F` -> no common L-side "
 "layer set, `Lemma B` -> support symmetry, `Theorem A` -> one arm trivial, "
 "`Theorem E` -> balanced support, `Parity Lemma` -> parity count, `Main Theorem` -> "
 "main result, `Corollary` -> consequence, `Twisted-class theorem` -> twisted "
 "classes.  The same rename was applied to `fig_theorem1_profile`, whose file name "
 "is kept as a stable identifier.",
 "- **The (2,5) case box.**  Named by role as `(2,5): middle-layer imbalance`, "
 "the case being closed by counting the corners of the layer-2 and layer-5 edges and "
 "finding F_L != F_R for both values of c.",
 "- **Fonts.**  Text is TeX Gyre Heros (Helvetica metrics) throughout.  Three math "
 "glyphs have no Heros form and fall back to the standard mathtext faces, embedded in "
 "the PDF alongside it: `Cmsy10` for the operators, `STIXNonUnicode` for the "
 "blackboard-bold F of F_2.",
]


# Supplementary figures the brief names but whose source is not in this repository.
# Recorded so the manifest is complete and the gap is visible, not built.
PENDING = [
    dict(output=["figures/figS7_pipeline.pdf"], section="si", label="figS:pipeline",
         aliases=["fig_architecture"], inputs=[], function="",
         description="Pipeline / architecture overview (original Fig. 1, to be "
                     "restyled).",
         notes=["source not in this repository: no fig_architecture script, figure or "
                "data file exists under stab-qram/ or stab-qram/repo/."],
         layout_check="NOT BUILT"),
    dict(output=["figures/figS8_depth_scaling.pdf"], section="si",
         label="figS:depthscaling", aliases=["depth_analysis_ab"], inputs=[],
         function="",
         description="Depth scaling (original, to be restyled).",
         notes=["source not in this repository: no depth_analysis_ab script, figure "
                "or data file exists."],
         layout_check="NOT BUILT"),
    dict(output=["figures/figS9_locality.pdf"], section="si", label="figS:locality",
         aliases=["locality_2d_heatmap_analysis"], inputs=[], function="",
         description="Locality heat map (original, to be restyled).",
         notes=["source not in this repository: no locality_2d_heatmap_analysis "
                "script, figure or data file exists."],
         layout_check="NOT BUILT"),
]


def tables_manifest():
    """Stem -> label -> the .tex on disk, so the manuscript can be wired from here."""
    import glob
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "tables", "*.tex"))):
        with open(p) as f:
            src = f.read()
        m = re.search(r"\\label\{([^}]*)\}", src)
        out.append(dict(output=[os.path.relpath(p, ROOT)],
                        section="si" if "tabS" in os.path.basename(p) else "main",
                        label=m.group(1) if m else "",
                        generated_by="twoblock.make_tables"))
    return out


def main() -> int:
    if CLTEST.main():
        print("  check_layout self-test FAILED; not building")
        return 1
    reps, manifest = [], []
    for name, fn, section, label, aliases, inputs, caption, notes in FIGURES:
        out = fn()
        fig = out[0] if isinstance(out, tuple) else out
        letters, shared = (out[1], out[2]) if (isinstance(out, tuple)
                                               and len(out) == 3) else ({}, ())
        rep = CL.check(fig, name, letters, shared)
        reps.append(rep)
        pdf = os.path.join(FIGS, name + ".pdf")
        png = os.path.join(FIGS, name + ".png")
        fig.savefig(pdf)
        fig.savefig(png, dpi=DPI_PNG)
        manifest.append(dict(
            output=[f"figures/{name}.pdf", f"figures/{name}.png"],
            section=section, label=label, aliases=aliases, inputs=inputs,
            function=getattr(fn, "_src", f"{fn.__module__}.{fn.__name__}"),
            width_mm=rep["width_mm"], height_mm=rep["height_mm"],
            description=" ".join(caption), notes=notes,
            layout_check="PASS" if rep["pass"] else "FAIL"))
        print(f"  {name:26s} {rep['width_mm']:5.1f} x {rep['height_mm']:5.1f} mm  "
              f"{'PASS' if rep['pass'] else 'FAIL'}")

    DERIVED.write()
    trace = M.TRACE + SI.TRACE
    with open(os.path.join(FIGS, "figure_values.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["figure", "item", "value", "source",
                                          "column", "key"])
        w.writeheader()
        w.writerows(trace)

    with open(os.path.join(FIGS, "figure_manifest.json"), "w") as f:
        json.dump(dict(generated=datetime.now().isoformat(timespec="seconds"),
                       tables=tables_manifest(),
                       rule="every plotted number is read from the listed inputs; the "
                            "value of every one of them is written to "
                            "figures/figure_values.csv and re-derived in CHECK.md",
                       fonts="TeX Gyre Heros (Helvetica metrics), pdf.fonttype=42",
                       png_dpi=DPI_PNG, entries=manifest + PENDING), f, indent=1)

    write_captions()
    write_readme(manifest)
    ok = write_check(reps, trace, page_fit(manifest))
    return 0 if ok and all(r["pass"] for r in reps) else 1


def write_captions():
    L = ["# Figure captions", "",
         "One sentence on what the panel shows, then the data source and n, then the "
         "one takeaway.", ""]
    for name, fn, section, label, aliases, inputs, caption, notes in FIGURES:
        what, source, take = caption
        where = {"main": "main text", "si": "supplementary",
                 "fallback": "built, not referenced"}[section]
        head_ = f"## `{name}` ({where}"
        head_ += f", \\label{{{label}}})" if label else ")"
        L += [head_, "", f"{what} {source} {take}", ""]
        if notes:
            L += ["".join(f"*{n}*  " for n in notes), ""]
    with open(os.path.join(FIGS, "CAPTIONS.md"), "w") as f:
        f.write("\n".join(L))


def write_readme(manifest):
    L = ["# Figures", "",
         "Regenerated by `make figures`, which runs `figures/src/make_fig1_data.py` "
         "and then `figures/src/build.py`.  No PDF is edited by hand.  Every plotted "
         "number is read from a file in `data/`, `templates/` or `schedules/`; "
         "`figure_manifest.json` records each output's inputs and generating "
         "function, `figure_values.csv` every value drawn, `CHECK.md` the layout "
         "checks and the cross-checks, `CAPTIONS.md` the captions.", "",
         "Design system in `figures/src/figstyle.py`; layout checks in "
         "`figures/check_layout.py`.  Fonts: TeX Gyre Heros (Helvetica metrics) from "
         "`figures/fonts/`, embedded as Type 42.", ""]
    for sec, title in (("main", "Main text"), ("si", "Supplementary"),
                       ("fallback", "Built but not referenced")):
        L += [f"## {title}", ""]
        for e in manifest + PENDING:
            if e["section"] != sec:
                continue
            L += [f"### `{os.path.basename(e['output'][0])}`", "", e["description"],
                  ""]
            if e.get("layout_check") == "NOT BUILT":
                L += ["*Not built.*  " + "  ".join(e["notes"]), ""]
                continue
            L += [f"*Size*: {e['width_mm']} x {e['height_mm']} mm.  "
                  + (f"*Label*: `\\ref{{{e['label']}}}`.  " if e.get("label") else "")
                  + (f"*Also known as*: "
                     + ", ".join(f"`{a}`" for a in e["aliases"]) + ".  "
                     if e.get("aliases") else "")
                  + f"*Inputs*: " + ", ".join(f"`{i}`" for i in e["inputs"]) + ".  "
                  f"*Generated by*: `{e['function']}`.  "
                  f"*Layout check*: {e['layout_check']}.", ""]
            if e["notes"]:
                L += ["".join(f"*{n}*  " for n in e["notes"]), ""]
    with open(os.path.join(FIGS, "README.md"), "w") as f:
        f.write("\n".join(L))


# ---------------------------------------------------------------- cross-checks
def _rows(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return list(csv.DictReader(f))


def cross_checks(trace):
    """Re-derive the headline numbers of fig 4 and fig 5 straight from the CSVs."""
    out = []

    def add(what, drawn, recomputed, source):
        out.append((what, drawn, recomputed, drawn == recomputed, source))

    # --- fig 3: the decision tree, against coverage.csv --------------------
    cov = [r for r in _rows("coverage.csv") if r["in_sharpness_map"] == "True"]

    def _leaf(r):
        if r["class"] != "C1":
            return r["class"]
        if r["ord_d_parity"] == "even":
            return "C1even"
        return "C1odd_obs" if r["theorem"] else "C1odd_free"

    want = Counter(_leaf(r) for r in cov)
    drawn = {t["key"]: int(t["value"]) for t in trace
             if t["figure"] == "fig3" and t["item"].startswith("leaf_n[")}
    for k in sorted(want):
        add(f"fig3 leaf '{k}'", drawn.get(k, -1), want[k], "data/coverage.csv")
    add("fig3 leaf counts sum to the population", sum(drawn.values()), len(cov),
        "data/coverage.csv")
    add("fig3 DRAT markers",
        sum(int(t["value"]) for t in trace
            if t["figure"] == "fig3" and t["item"].startswith("leaf_drat[")),
        sum(1 for r in cov if r["drat_verified"] == "True"), "data/coverage.csv")
    add("fig3 capped, hatched",
        sum(int(t["value"]) for t in trace
            if t["figure"] == "fig3" and t["item"].startswith("leaf_capped[")),
        sum(1 for r in cov if r["status_solver"] == "capped"), "data/coverage.csv")
    six = _rows("thm_six_coverage.csv")
    add("fig3 ord(d) even, d not in 8G",
        next(int(t["value"]) for t in trace if t["item"] == "even_d_not_in_8G"),
        sum(1 for r in six if r["in_8G"] == "False"
            and r["ord_d_parity"] == "even"), "data/thm_six_coverage.csv")

    # --- figS6: certificate cost -------------------------------------------
    res = {}
    for r in _rows("results.csv"):
        if r["D"] == "6" and r["status"] == "UNSAT":
            res.setdefault(r["instance"], r)
    for t in trace:
        if t["figure"] == "figS6" and t["item"].startswith("MB["):
            inst = t["item"][3:-1]
            add(f"figS6 proof size {inst} (MB)", round(float(t["value"]), 6),
                round(float(res[inst]["proof_bytes"]) / 1e6, 6), "data/results.csv")
        if t["figure"] == "figS6" and t["item"].startswith("s["):
            inst = t["item"][2:-1]
            add(f"figS6 solve time {inst} (s)", float(t["value"]),
                float(res[inst]["time"]), "data/results.csv")

    add("figS6 R4 runs drat-trim VERIFIED",
        next(int(t["value"]) for t in trace if t["item"] == "r4_verified"),
        sum(1 for r in _rows("r4_no_reversal.csv") if r["verified"] == "VERIFIED"),
        "data/r4_no_reversal.csv")
    add("figS6 R4 runs in total", len(_rows("r4_no_reversal.csv")),
        sum(1 for r in _rows("r4_no_reversal.csv")
            if r["symmetry_breaking"] == "False"), "data/r4_no_reversal.csv")
    return out


def page_fit(manifest):
    """Artwork + caption against the text height of a page, caption set for real."""
    import re
    with open(os.path.join(FIGS, "CAPTIONS.md")) as f:
        cap = f.read()
    blocks = {}
    for b in re.split(r"\n## ", cap)[1:]:
        nm = b.split("`")[1]
        blocks[nm] = " ".join(l for l in b.split("\n")
                              if l.strip() and not l.startswith("`"))
    ents = [(os.path.basename(e["output"][0])[:-4], e["width_mm"], e["height_mm"],
             blocks[os.path.basename(e["output"][0])[:-4]]) for e in manifest]
    return PFIT.fit(ents)


def _text_number_section():
    p = os.path.join(FIGS, "text_numbers_expected.txt")
    if not os.path.exists(p):
        return ["_no expected-number list_", ""]
    with open(p) as f:
        toks = [t.strip() for line in f if not line.startswith("#")
                for t in line.split(",") if t.strip()]
    src = CTN.sources()
    anchors = {}
    ap = os.path.join(FIGS, "text_anchors.csv")
    if os.path.exists(ap):
        with open(ap) as f:
            for r in csv.DictReader(f):
                anchors[r["number"].strip()] = r
    seen, order = set(), []
    for t in toks:
        if t not in seen:
            seen.add(t); order.append(t)
    L = [f"Every number the manuscript is expected to state in sections 4-5, looked "
         f"up in `figures/figure_values.csv`, `data/`, `templates/` and `tables/` "
         f"({len(src):,} numeric values).  With that many sources almost any integer "
         f"can be made to match something, so a bare hit is not evidence: a number "
         f"counts as sourced only if it matches its anchor in "
         f"`figures/text_anchors.csv`, or matches some value exactly.  A cell that "
         f"merely rounds to it is not an explanation.", "",
         "| number | verdict | source | meaning |", "|---|---|---|---|"]
    def cell(x):                     # keep a source key inside one table cell
        return str(x).replace("\n", " ").replace("|", "\\|")

    bad, amb, mism = [], [], []
    for t in order:
        a = anchors.get(t)
        if a:
            sub = [(x, w, g) for x, w, g in src if a["source_contains"] in w]
            grade, hits, _ = CTN.explain(t, sub) if sub else ("none", [], 0)
            if hits:
                rule, where, x = hits[0]
                extra = "" if rule == "exact" else f" ({rule} from {x:g})"
                L.append(f"| {t} | anchored | `{cell(where)}`{extra} | {a['note']} |")
            else:
                bad.append(t); mism.append(t)
                have = sorted({x for x, w, _g in sub}) if sub else []
                got = (", ".join(f"{x:g}" for x in have[:3]) if have
                       else "that source holds no value")
                alt = ""
                for x, w, _g in src:
                    if not w.startswith("derived:") or a["source_contains"] in w:
                        continue
                    _gr, hh, _n = CTN.explain(t, [(x, w, "strong")])
                    if hh:
                        alt = f"  Matches `{cell(w.split(' = ')[0])}` = {x:g} instead."
                        break
                L.append(f"| {t} | **anchor mismatch** | the anchored quantity is "
                         f"{got}, not {t}.{alt} | {a['note']} |")
            continue
        grade, hits, n_exact = CTN.explain(t, src)
        if grade in ("strong", "medium") and hits:
            note = (f"exact, but {n_exact} different sources carry this value"
                    if n_exact > 1 else "exact")
            if n_exact > 1:
                amb.append(t)
            L.append(f"| {t} | {grade} | `{cell(hits[0][1])}` | {note} |")
        elif hits:
            bad.append(t)
            rule, where, x = hits[0]
            L.append(f"| {t} | **no source** | nearest: `{cell(where)}` "
                     f"({rule} from {x:g}) | a cell that rounds to it, not a source |")
        else:
            bad.append(t)
            L.append(f"| {t} | **no source** | none | |")
    L += ["", f"{len(order) - len(bad)} of {len(order)} numbers are sourced."]
    if amb:
        L.append("Exact but unanchored, so the quantity they refer to is ambiguous: "
                 + ", ".join(f"**{t}**" for t in amb)
                 + ".  Add a row to `figures/text_anchors.csv` to pin each one.")
    if mism:
        L.append("**Anchor mismatches: " + ", ".join(mism) + ".**  Each of these "
                 "equals something in the repository, but not the quantity the text "
                 "claims it is.  Either the sentence names the wrong quantity or the "
                 "number is stale; the row says what the anchored quantity actually "
                 "is, and what the stated number does match.")
    nosrc = [t for t in bad if t not in mism]
    if nosrc:
        L.append("**No source at all: " + ", ".join(nosrc) + ".**  Nothing in "
                 "`data/`, `templates/`, `tables/`, `derived_values.csv` or "
                 "`figure_values.csv` equals them.")
    L.append("")
    return L


def _findings():
    """Everything in figures/findings/*.md, in name order: the round-by-round
    answers that are not produced by the build itself."""
    import glob
    out = []
    for p in sorted(glob.glob(os.path.join(FIGS, "findings", "*.md"))):
        with open(p) as f:
            out += f.read().rstrip().split("\n") + [""]
    return out


def _regression_section():
    p = os.path.join(FIGS, "check_layout_regression.json")
    if not os.path.exists(p):
        return ["_no recorded regression run_"]
    with open(p) as f:
        rec = json.load(f)
    L = ["Two measurements in `check_layout.py` were wrong until 2026-09-08: "
         "`Patch.get_transform()` already composes `get_patch_transform()`, and the "
         "tick artists of an axes turned off with `axis(\"off\")`, or of a tick "
         "outside the view interval, still report themselves as visible.  The table "
         "compares the checker with those three patches reverted "
         "(`figures/check_layout_pre_20260908.py`) against the checker as it now "
         "stands, on the same live figures.", "",
         "| figure | T1 | T2 | T3 | T4 | T5 | T6 | T7 | overall |",
         "|---|---|---|---|---|---|---|---|---|"]
    titles = {"superseded": "The three superseded figures, rebuilt from "
                            "`twoblock/plot_figures.py`",
              "current": "The eleven current figures",
              "probes": "Purpose-built probes (`figures/test_check_layout.py`)"}
    for sec in ("probes", "superseded", "current"):
        L.insert(len(L) - 2 if False else len(L), "")
        L[-1] = f"| **{titles[sec]}** ||||||||"
        for r in rec.get(sec, []):
            cells = []
            for k in ("T1", "T2", "T3", "T4", "T5", "T6", "T7"):
                a, b = r["pre"].get(k), r["now"].get(k)
                if not a or not b:
                    cells.append("-"); continue
                pa = "PASS" if a[0] else "FAIL"
                pb = "PASS" if b[0] else "FAIL"
                cells.append(pa if pa == pb else f"**{pa}->{pb}**")
            oa = "PASS" if r["pre_pass"] else "FAIL"
            ob = "PASS" if r["now_pass"] else "FAIL"
            ov = oa if oa == ob else f"**{oa}->{ob}**"
            L.append(f"| `{r['name']}` | " + " | ".join(cells) + f" | {ov} |")
    L += ["", "Reading it:", "",
          "- `probe_patch_transform` is a label placed 0.30 mm from a filled "
          "rectangle.  The old checker **passed** it; the fixed one fails it at "
          "0.30 mm.  That is the false negative the patch-transform bug caused, and "
          "it is the only clean demonstration available, because the misplacement "
          "depends on where a rectangle sits and no production figure happened to "
          "hide a collision behind it.",
          "- `probe_hidden_axis_ticks` is a note in the corner of an axes turned "
          "off.  The old checker failed it against ticks that are never drawn; the "
          "fixed one passes.",
          "- The three superseded figures **fail under both checkers**: they were "
          "never passing, because their type runs down to 4.4 pt (T5) with text "
          "colliding (T1).  They cannot show 'old passed, new fails'.  What they do "
          "show is that the measurement changed materially: T2 findings fall from "
          "22 to 14 on `fig_certificate_vs_optimum` and from 31 to 14 on "
          "`fig_proof_structure`, and `fig_sharpness` loses a bogus T6 failure on "
          "its own y-axis label.",
          "- Of the eleven current figures, six fail under the old checker and pass "
          "under the fixed one.  The dominant effect of the fix is removing false "
          "positives; the false negative is real but only the probe exhibits it.", ""]
    return L


def write_check(reps, trace, fits):
    xc = cross_checks(trace)
    ok = all(c[3] for c in xc)
    L = ["# Figure check log", "",
         f"Generated {datetime.now().isoformat(timespec='seconds')} by "
         "`figures/src/build.py`.  Every figure is rebuilt from its builder, measured "
         "at final print size and written as PDF and PNG at "
         f"{DPI_PNG} dpi; there are no manual edits to any PDF.", "",
         CL.render_report(reps), "",
         "## Cross-checks of plotted numbers against the CSVs", "",
         "Each row re-reads the source column and compares it with the value the "
         "figure actually drew (recorded in `figures/figure_values.csv`).", "",
         "| quantity | drawn | re-derived from the CSV | source | |",
         "|---|---|---|---|---|"]
    for what, drawn, recomputed, good, source in xc:
        L.append(f"| {what} | {drawn} | {recomputed} | `{source}` | "
                 f"{'OK' if good else '**MISMATCH**'} |")
    L += ["", f"{sum(1 for c in xc if c[3])} of {len(xc)} cross-checks agree.", "",
          "## Values behind every figure", "",
          f"`figures/figure_values.csv` records all {len(trace)} plotted quantities "
          "with the file and column each was read from.", "",
          "## Page fit", "",
          f"Caption set for real at {PFIT.CAPTION_PT} pt with leading "
          f"{PFIT.LEADING}, in the figure's own column width, using the metrics of "
          f"the figure font; {PFIT.SEP_MM} mm between artwork and caption; budget "
          f"{PFIT.BUDGET_MM:.0f} mm of text height.", "",
          "| figure | artwork (mm) | caption lines | caption (mm) | total (mm) | "
          "fits |", "|---|---|---|---|---|---|"]
    for r in fits:
        L.append(f"| `{r['figure']}` | {r['width_mm']:.0f} x {r['art_mm']:.0f} | "
                 f"{r['caption_lines']} | {r['caption_mm']} | {r['total_mm']} | "
                 f"{'yes' if r['fits'] else '**NO**'} |")
    L += ["", "## Numbers in the text", ""] + _text_number_section() + [
          "## Checker regression", ""] + _regression_section() + [
          "## Deviations from the figure brief", "", *DEVIATIONS, "",
          *_findings()]
    with open(os.path.join(FIGS, "CHECK.md"), "w") as f:
        f.write("\n".join(L))
    return ok


if __name__ == "__main__":
    raise SystemExit(main())

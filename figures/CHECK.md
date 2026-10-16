# Figure check log

Generated 2026-10-15T04:55:43 by `figures/src/build.py`.  Every figure is rebuilt from its builder, measured at final print size and written as PDF and PNG at 600 dpi; there are no manual edits to any PDF.

## Layout checks

Measured on the live figure at final print size; distances in millimetres of printed page.  T1 text-to-text >= 1.5 mm, T2 text-to-graphic >= 1.0 mm, T3 gutters >= 5.0/7.0 mm, T4 panel letter >= 2.0 mm, T5 type >= 6.5 pt, T6 rotation, T7 shared-axis separation.

| figure | size (mm) | T1 | T2 | T3 | T4 | T5 | T6 | T7 | overall |
|---|---|---|---|---|---|---|---|---|---|
| `fig1_degree_bound_to_cross_term` | 180.0 x 110.0 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `fig2_why_six_layers_fail` | 180.0 x 78.0 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `fig3_where_depth6_is_attainable` | 180.0 x 75.0 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `figS1_proof_map` | 180.0 x 232.0 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `figS2_sweep_by_group` | 88.0 x 76.0 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `figS3_templates_by_q` | 88.0 x 88.0 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `figS4_periods` | 88.0 x 80.0 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `figS5_theorem1_profile` | 88.0 x 116.0 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `figS6_certificates` | 180.0 x 90.0 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |

### Failures in detail

- none

### Closest pair of text elements in each panel

| figure | panel | gap (mm) | element A | element B |
|---|---|---|---|---|
| `fig1_degree_bound_to_cross_term` | ax0 | 1.68 | checks above, data qub | $X_g$ and $Z_{g'}$ sha |
| `fig2_why_six_layers_fail` | ax0 | 1.52 | support symmetry — $X$ | $a+b = 7$ |
| `fig3_where_depth6_is_attainable` | ax0 | 1.5 | C2 and subgroup-type i | counts from 664 tested |
| `figS1_proof_map` | map | 3.01 | open | computational evidence |
| `figS2_sweep_by_group` | a | 1.8 | 9 | 9 |
| `figS3_templates_by_q` | a | 1.62 | 2,250 | 3,888 |
| `figS4_periods` | a | 1.79 | $q^*=2$ | $q^*=4$ |
| `figS5_theorem1_profile` | a | 1.76 | $\sum_v r_v s_v \;\mat | 1 |
| `figS5_theorem1_profile` | b | 2.47 | class-C1 instances | 100 |
| `figS6_certificates` | a | 2.33 | bb90 | bb108 |
| `figS6_certificates` | b | 2.33 | bb90 | bb108 |


## Cross-checks of plotted numbers against the CSVs

Each row re-reads the source column and compares it with the value the figure actually drew (recorded in `figures/figure_values.csv`).

| quantity | drawn | re-derived from the CSV | source | |
|---|---|---|---|---|
| fig3 leaf 'C1even' | 265 | 265 | `data/coverage.csv` | OK |
| fig3 leaf 'C1odd_free' | 122 | 122 | `data/coverage.csv` | OK |
| fig3 leaf 'C1odd_obs' | 211 | 211 | `data/coverage.csv` | OK |
| fig3 leaf 'C2' | 28 | 28 | `data/coverage.csv` | OK |
| fig3 leaf 'D' | 35 | 35 | `data/coverage.csv` | OK |
| fig3 leaf 'SG' | 3 | 3 | `data/coverage.csv` | OK |
| fig3 leaf counts sum to the population | 664 | 664 | `data/coverage.csv` | OK |
| fig3 DRAT markers | 16 | 16 | `data/coverage.csv` | OK |
| fig3 capped, hatched | 118 | 118 | `data/coverage.csv` | OK |
| fig3 ord(d) even, d not in 8G | 263 | 263 | `data/thm_six_coverage.csv` | OK |
| figS6 solve time bb72 (s) | 1.389 | 1.389 | `data/results.csv` | OK |
| figS6 solve time bb90 (s) | 2.027 | 2.027 | `data/results.csv` | OK |
| figS6 solve time bb108 (s) | 2.049 | 2.049 | `data/results.csv` | OK |
| figS6 solve time bb144 (s) | 2.237 | 2.237 | `data/results.csv` | OK |
| figS6 solve time bb288 (s) | 4.293 | 4.293 | `data/results.csv` | OK |
| figS6 solve time bb360 (s) | 4.797 | 4.797 | `data/results.csv` | OK |
| figS6 solve time bb756 (s) | 5.94 | 5.94 | `data/results.csv` | OK |
| figS6 solve time sw73 (s) | 558.046 | 558.046 | `data/results.csv` | OK |
| figS6 proof size bb72 (MB) | 12.866818 | 12.866818 | `data/results.csv` | OK |
| figS6 proof size bb90 (MB) | 20.261082 | 20.261082 | `data/results.csv` | OK |
| figS6 proof size bb108 (MB) | 20.781069 | 20.781069 | `data/results.csv` | OK |
| figS6 proof size bb144 (MB) | 23.082271 | 23.082271 | `data/results.csv` | OK |
| figS6 proof size bb288 (MB) | 46.354309 | 46.354309 | `data/results.csv` | OK |
| figS6 proof size bb360 (MB) | 51.978429 | 51.978429 | `data/results.csv` | OK |
| figS6 proof size bb756 (MB) | 46.501698 | 46.501698 | `data/results.csv` | OK |
| figS6 proof size sw73 (MB) | 2727.429491 | 2727.429491 | `data/results.csv` | OK |
| figS6 R4 runs drat-trim VERIFIED | 9 | 9 | `data/r4_no_reversal.csv` | OK |
| figS6 R4 runs in total | 9 | 9 | `data/r4_no_reversal.csv` | OK |

28 of 28 cross-checks agree.

## Values behind every figure

`figures/figure_values.csv` records all 187 plotted quantities with the file and column each was read from.

## Page fit

Caption set for real at 7.5 pt with leading 1.25, in the figure's own column width, using the metrics of the figure font; 3.5 mm between artwork and caption; budget 235 mm of text height.

| figure | artwork (mm) | caption lines | caption (mm) | total (mm) | fits |
|---|---|---|---|---|---|
| `fig1_degree_bound_to_cross_term` | 180 x 110 | 4 | 13.2 | 126.7 | yes |
| `fig2_why_six_layers_fail` | 180 x 78 | 4 | 13.2 | 94.7 | yes |
| `fig3_where_depth6_is_attainable` | 180 x 75 | 4 | 13.2 | 91.7 | yes |
| `figS1_proof_map` | 180 x 232 | 4 | 13.2 | 248.7 | **NO** |
| `figS2_sweep_by_group` | 88 x 76 | 4 | 13.2 | 92.7 | yes |
| `figS3_templates_by_q` | 88 x 88 | 5 | 16.5 | 108.0 | yes |
| `figS4_periods` | 88 x 80 | 5 | 16.5 | 100.0 | yes |
| `figS5_theorem1_profile` | 88 x 116 | 6 | 19.8 | 139.3 | yes |
| `figS6_certificates` | 180 x 90 | 3 | 9.9 | 103.4 | yes |

## Numbers in the text

Every number the manuscript is expected to state in sections 4-5, looked up in `figures/figure_values.csv`, `data/`, `templates/` and `tables/` (221,511 numeric values).  With that many sources almost any integer can be made to match something, so a bare hit is not evidence: a number counts as sourced only if it matches its anchor in `figures/text_anchors.csv`, or matches some value exactly.  A cell that merely rounds to it is not an explanation.

| number | verdict | source | meaning |
|---|---|---|---|
| 1441 | anchored | `data/sweep.csv (row count)` | instances in the depth-6 sweep |
| 1440 | anchored | `figure_values.csv S1:total_SAT <- data/sweep.csv:status` | sweep instances SAT at depth 6 |
| 250 | anchored | `derived:coverage_theorem_excluded = count(status_math == 'UNSAT-theorem') over data/coverage.csv` | depth-6 instances excluded by a theorem |
| 10 | strong | `figure_values.csv figS1:pareto[C1-even,144,8] <- data/pareto_front.csv:d` | exact, but 619 different sources carry this value |
| 62 | anchored | `derived:coverage_solver_only_unsat = count(status_math == 'UNSAT-solver') over data/coverage.csv` | UNSAT by the solver and by no theorem |
| 80 | anchored | `derived:coverage_capped_but_excluded = count(status_solver == 'capped' and status_math == 'UNSAT-theorem') over data/coverage.csv` | capped solver calls a theorem already excludes |
| 30 | anchored | `derived:coverage_open = count(status_math == 'open') over data/coverage.csv` | open: no theorem applies and the solver capped |
| 664 | anchored | `derived:sharpness_map_total = count(in_sharpness_map) -- the population of the sharpness map over data/coverage.csv` | instances with a recorded depth-6 outcome (the sharpness map) |
| 265 | anchored | `derived:c1_ord_d_even_total = count(rows where ord_d_even == True) over data/c1_final_instances.csv` | class-C1 instances with ord(d) even |
| 262 | anchored | `derived:c1_even_sat_solver = count(class C1, ord(d) even, status_math == 'SAT-solver') over data/coverage.csv` | class-C1 ord(d) even instances SAT by the solver |
| 3 | anchored | `derived:c1_even_sat_witness = count(class C1, ord(d) even, status_math == 'SAT-witness') over data/coverage.csv` | and by a verified twisted witness |
| 333 | anchored | `derived:c1_ord_d_odd_total = count(rows where ord_d_even == False) over data/c1_final_instances.csv` | class-C1 instances with ord(d) odd |
| 211 | anchored | `derived:c1_ord_d_odd_obstructed = count(rows where ord_d_even == False and theorem1_obstructed == True) over data/c1_final_instances.csv` | of those, obstructed by the mod-4 condition |
| 122 | anchored | `derived:c1_ord_d_odd_unobstructed = count(rows where ord_d_even == False and theorem1_obstructed == False) over data/c1_final_instances.csv` | and not obstructed |
| 24 | anchored | `figure_values.csv figS6:MB_norev[bb72] <- data/r4_no_reversal.csv:proof_bytes` (rounded from 24.2556) | bb72 DRAT proof without the reversal clause, MB |
| 468 | anchored | `figure_values.csv S2:admit[m=6,$\|M\|$ even, $\bar{\mathsf{d}}\neq0$, ord$(\bar{\mathsf{d}})$ odd] <- templates/C1_m6.json:sat_keys` | eps-vectors with ord(eps(d)) odd admitting a schedule at m = 6 |
| 669 | anchored | `data/r7_overlap_counts.csv (row count)` | instances whose overlap class was recomputed |
| 417 | anchored | `derived:periodicity_total = count(rows) over data/r6_periodicity.csv` | enumerated solutions carrying the lemma checks |
| 5 | anchored | `derived:periodicity_invariant = count(klass == 'invariant') over data/r6_periodicity.csv` | of those, translation invariant |
| 72 | anchored | `derived:periodicity_twisted = count(klass == 'twisted') over data/r6_periodicity.csv` | and twisted for a proper divisor |
| 340 | anchored | `derived:periodicity_other = count(klass == 'other') over data/r6_periodicity.csv` | with no proper period found |
| 300 | anchored | `derived:t2_layerings_per_instance = n_layerings, identical for every T2 instance over data/t7_model_coverage.csv` | random valid layerings per instance in T2 |
| 600 | anchored | `derived:t2_layerings_total = sum(n_layerings) over the T2 rows over data/t7_model_coverage.csv` | random valid layerings in T2 in total |
| 17 | anchored | `derived:crosscheck_rows = count(rows) over data/solver_crosscheck.csv` | depth-6 CNFs re-decided by cadical and glucose |
| 16 | anchored | `derived:crosscheck_agree = count(rows where cadical_status == glucose_status, both decided) over data/solver_crosscheck.csv` | of those, decided identically by both |
| 558 | anchored | `figure_values.csv figS6:s[sw73] <- data/results.csv:time` (rounded from 558.046) | kissat solve time for the Z6 instance, seconds |
| 2.7 | anchored | `figure_values.csv figS6:MB[sw73] <- data/results.csv:proof_bytes` (scaled x0.001 from 2727.43) | DRAT proof for the Z6 instance, GB |
| 18 | anchored | `derived:nosym_proof_min_MB = min(proof_bytes)/1e6 over the 7 IBM depth-6 refutations without the clause (certs_nosym/) over data/r4_no_reversal.csv` (rounded from 17.8042) | smallest DRAT proof without the reversal clause, MB |
| 68 | anchored | `derived:nosym_proof_max_MB = max(proof_bytes)/1e6 over the 7 IBM depth-6 refutations without the clause (certs_nosym/) over data/r4_no_reversal.csv` (rounded from 67.9656) | largest DRAT proof without the reversal clause, MB |
| 1.4 | anchored | `derived:nosym_solve_min_s = min(time) over the 7 IBM depth-6 refutations without the clause (certs_nosym/) over data/r4_no_reversal.csv` (rounded from 1.435) | fastest refutation without the reversal clause, s |
| 6.3 | anchored | `derived:nosym_solve_max_s = max(time) over the 7 IBM depth-6 refutations without the clause (certs_nosym/) over data/r4_no_reversal.csv` (rounded from 6.294) | slowest refutation without the reversal clause, s |
| 14 | anchored | `derived:template_m2_N = N of the chosen m = 2 template over data/template_main.csv` | order of G for the main-text m = 2 template |
| 28 | anchored | `derived:template_m2_n_qubits = n_qubits of the chosen m = 2 template over data/template_main.csv` | physical qubits of the template's realising code |
| 6 | anchored | `derived:template_m2_k_logical = k_logical of the chosen m = 2 template over data/template_main.csv` | logical qubits of that code |
| 12931 | anchored | `derived:twisted_identity_cosets = count(rows) over data/twisted_identity.csv` | cosets on which the twisted identity was checked |
| 289 | anchored | `derived:twisted_identity_witnesses = distinct witnesses over data/twisted_identity.csv` | twisted witnesses carrying eps and m |
| 11412 | anchored | `derived:twisted_identity_template_keys = sum over m of the distinct template keys at that m over data/twisted_identity.csv` | admissible template keys checked |
| 323 | anchored | `derived:b2_schedules_found = count(result == 'found') over data/b2_twisted_outside_c1.csv` | twisted schedules found outside class C1 |
| 11 | anchored | `derived:b2_distinct_absM = distinct \|M\| values among them over data/b2_twisted_outside_c1.csv` | distinct |M| values among them |
| 29 | anchored | `derived:b2_capped = count(result == 'capped') -- never read as absence over data/b2_twisted_outside_c1.csv` | capped (instance, m) combinations |

40 of 40 numbers are sourced.
Exact but unanchored, so the quantity they refer to is ambiguous: **10**.  Add a row to `figures/text_anchors.csv` to pin each one.

## Checker regression

Two measurements in `check_layout.py` were wrong until 2026-09-08: `Patch.get_transform()` already composes `get_patch_transform()`, and the tick artists of an axes turned off with `axis("off")`, or of a tick outside the view interval, still report themselves as visible.  The table compares the checker with those three patches reverted (`figures/check_layout_pre_20260908.py`) against the checker as it now stands, on the same live figures.

| figure | T1 | T2 | T3 | T4 | T5 | T6 | T7 | overall |
|---|---|---|---|---|---|---|---|---|
| **Purpose-built probes (`figures/test_check_layout.py`)** ||||||||
| `probe_patch_transform` | PASS | **PASS->FAIL** | PASS | PASS | PASS | PASS | PASS | **PASS->FAIL** |
| `probe_hidden_axis_ticks` | PASS | **FAIL->PASS** | PASS | PASS | PASS | PASS | PASS | **FAIL->PASS** |
| **The three superseded figures, rebuilt from `twoblock/plot_figures.py`** ||||||||
| `fig_certificate_vs_optimum` | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | PASS | FAIL |
| `fig_proof_structure` | FAIL | FAIL | PASS | PASS | FAIL | PASS | PASS | FAIL |
| `fig_sharpness` | FAIL | FAIL | PASS | PASS | FAIL | **FAIL->PASS** | PASS | FAIL |
| **The eleven current figures** ||||||||
| `fig1` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `fig2` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `fig2_small` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `fig3` | PASS | **FAIL->PASS** | PASS | PASS | PASS | PASS | PASS | **FAIL->PASS** |
| `fig4` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `fig5` | PASS | **FAIL->PASS** | PASS | PASS | PASS | PASS | PASS | **FAIL->PASS** |
| `fig_sweep_by_group` | PASS | **FAIL->PASS** | PASS | PASS | PASS | PASS | PASS | **FAIL->PASS** |
| `fig_templates_by_m` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `fig_periods` | PASS | **FAIL->PASS** | PASS | PASS | PASS | PASS | PASS | **FAIL->PASS** |
| `fig_theorem1_profile` | PASS | **FAIL->PASS** | PASS | PASS | PASS | PASS | PASS | **FAIL->PASS** |
| `fig_lemma_profiles` | PASS | PASS | PASS | PASS | PASS | **FAIL->PASS** | PASS | **FAIL->PASS** |

Reading it:

- `probe_patch_transform` is a label placed 0.30 mm from a filled rectangle.  The old checker **passed** it; the fixed one fails it at 0.30 mm.  That is the false negative the patch-transform bug caused, and it is the only clean demonstration available, because the misplacement depends on where a rectangle sits and no production figure happened to hide a collision behind it.
- `probe_hidden_axis_ticks` is a note in the corner of an axes turned off.  The old checker failed it against ticks that are never drawn; the fixed one passes.
- The three superseded figures **fail under both checkers**: they were never passing, because their type runs down to 4.4 pt (T5) with text colliding (T1).  They cannot show 'old passed, new fails'.  What they do show is that the measurement changed materially: T2 findings fall from 22 to 14 on `fig_certificate_vs_optimum` and from 31 to 14 on `fig_proof_structure`, and `fig_sharpness` loses a bogus T6 failure on its own y-axis label.
- Of the eleven current figures, six fail under the old checker and pass under the fixed one.  The dominant effect of the fix is removing false positives; the false negative is real but only the probe exhibits it.

## Deviations from the figure brief

- **fig5, lemma-check coverage.**  The brief asks for the periodicity split (5 invariant / 72 twisted / 340) *from `data/lemma_checks.csv`*.  That file has no periodicity column: the split lives in `data/r6_periodicity.csv` (column `klass`), which is what panel d reads.  Panel c reads the coverage itself from `data/lemma_checks.csv`.
- **fig5, name of the third periodicity class.**  The brief calls it *aperiodic*.  The CSV class is `other`, and the previous round removed the word *aperiodic* project-wide, so the figure says **no proper period** instead.  The count, 340, is the brief's.
- **fig5 placement.**  Assigned to the supplement, as the brief allows: the main text already carries a full-page proof map (fig2, 180 x 208 mm) and fig5 is another 120 mm of column.
- **fig5, the two class-D rows of R4.**  `data/r4_no_reversal.csv` has 9 rows; two of them (`h2_Z10_D_0`, `h2_Z12_D_0`) are not in the depth-6 certificate set of `data/results.csv`, so they carry no paired marker.  They are still counted in the '9 of 9 verified' statement, which is what the CSV supports.
- **fig3, the observed supports.**  No enumerated instance has Delta = 6, so the panel draws the identity for the manuscript's case (Delta = 6, a + b = 7) and cites the observed pairs with their own Delta (oe43, Delta = 7).  The identity itself is asserted on all 417 solutions when the figure is built.
- **No theorem numbers anywhere.**  The manuscript numbers by `\label` and the numbering may shift, and there is no `supplement.tex` in the repository, so the SI numbering is not fixed either: every box and header names its result by role.  `Theorem 1` -> componentwise mod-4 obstruction, `Theorem F` -> no common L-side layer set, `Lemma B` -> support symmetry, `Theorem A` -> one arm trivial, `Theorem E` -> balanced support, `Parity Lemma` -> parity count, `Main Theorem` -> main result, `Corollary` -> consequence, `Twisted-class theorem` -> twisted classes.  The same rename was applied to `fig_theorem1_profile`, whose file name is kept as a stable identifier.
- **The (2,5) case box.**  Named by role as `(2,5): middle-layer imbalance`, the case being closed by counting the corners of the layer-2 and layer-5 edges and finding F_L != F_R for both values of c.
- **Fonts.**  Text is TeX Gyre Heros (Helvetica metrics) throughout.  Three math glyphs have no Heros form and fall back to the standard mathtext faces, embedded in the PDF alongside it: `Cmsy10` for the operators, `STIXNonUnicode` for the blackboard-bold F of F_2.

## Round 3 A: template soundness

### A1. Which constraint set the template encoder imposes — **(a) per-labelled-pair**

`twoblock/templates.py:50-59` hands the solver one group per *label pair*: the
designated colliding pair as a doubleton, then a separate singleton for each of the
other seven pairs, whatever their projected sums happen to be.

```python
def deltas_for(pat, ea, eb, m) -> list[tuple]:
    """(eps(delta), [(s,t), ...]) groups: one doubleton and seven singletons."""
    (s, t), (s2, t2) = pat
    out = [((ea[s] + eb[t]) % m, [(s, t), (s2, t2)])]
    for ss in range(K):
        for tt in range(L):
            if (ss, tt) in ((s, t), (s2, t2)):
                continue
            out.append(((ea[ss] + eb[tt]) % m, [(ss, tt)]))
    return out
```

`twoblock/encode.py:611-625` consumes that list **as given** — it never re-groups by
the projected value `ed`, which is used only as the Z-class offset `mod(e + ed)`:

```python
    for ed, sts in deltas:
        for e in E:
            bits = []
            for (s, t) in sts:
                bits.append(orient((("X", "L"), s, e), (("Z", "L"), t, mod(e + ed))))
                bits.append(orient((("X", "R"), t, e), (("Z", "R"), s, mod(e + ed))))
            acc = bits[0]
            ...
            cls.append([-acc, bits[-1]])
            cls.append([acc, -bits[-1]])
```

So a singleton group contributes two corner-orientation bits whose XOR is forced to 0
— the L-corner of `X_c` with labels `(s,t)` and the R-corner at the Z-class
`c + alpha_s + beta_t` must agree — and the designated colliding pair contributes four
bits with an even sum.  That is exactly hypothesis **(a)**.

**Verdict: the templates are sound; A1 requires no re-enumeration and Proposition IV.7
stands.**  When a concrete instance merges further sum classes, the template's
constraint set is *stronger* than the instance's (two separate equalities imply the
four-corner even sum), and the template quantifies over all of `Z_m` while an instance
only needs the image of `eps`; both directions are conservative, so admissible-by-
template implies admissible-on-the-instance.

### A2. Pullback onto concrete codes — 12 of 12 pass

`tests/test_template_pullback.py`, recorded in `data/template_pullback.csv`.  For each
modulus, three admissible keys whose projection merges extra pairs beyond the
designated collision; each realised on the smallest cyclic group that carries it in
class C1, the template solution expanded onto that code and re-checked by F2
simulation.

| m | keys tested | extra merges | carrier groups | verdict |
|---|---|---|---|---|
| 2 | 3 | 6, 6, 6 | Z10 | all pass |
| 3 | 0 admissible keys | – | – | nothing to test |
| 4 | 3 | 5, 4, 4 | Z16, Z12 | all pass |
| 5 | 0 admissible keys | – | – | nothing to test |
| 6 | 3 | 5, 4, 3 | Z24, Z18, Z12 | all pass |
| 8 | 3 | 5, 4, 3 | Z32, Z24, Z16 | all pass |

Every case merges at least three sum classes beyond the designated one, so the
conservative direction is exercised hard, and every pulled-back schedule is a valid,
proper depth-6 schedule on its code.

### A3. Two-divisibility of d — `data/s5_groups.csv` (new file, 598 rows)

`two_height(d)` is computed by brute force over G (largest j with d in 2^j G) and
`detected_by_Z2j` by searching the homomorphisms G -> Z_{2^j}.

- **333** of the 598 instances have *unbounded* two-height: their group has odd
  2-part, so every element lies in 2^j G for all j and "d in 8G" is vacuous there.
  Reporting a bare `two_height >= 3` would sweep all of these in.
- **2** instances have a finite `two_height(d) >= 3`, and both are SAT with a twisted
  witness recorded:

| instance | G | d | two_height | detected_by_Z2j | status | m used |
|---|---|---|---|---|---|---|
| `h4_Z32_C1_12` | Z32 | 24 | 3 | 4 | SAT | 16 |
| `h4_Z32_C1_13` | Z32 | 8 | 3 | 4 | SAT | 16 |

**Confirmed:** every finite-two-height >= 3 instance that is SAT has its witness
recorded as an instance-level twisted schedule with the m used (2 of 2).

**Correction for the text:** the instance set contains no Z48 and no Z64 — the groups
present are Z10..Z24, Z28, Z30, Z32, Z36.  Only the **Z32** cases can be cited.

## Round 3 B: certificate coverage — `data/coverage.csv`

`twoblock/coverage.py` builds one row per depth-6 instance (2,104 rows) from
`results.csv`, `c1_final_instances.csv`, `h2_sharpness.csv`, `h4_features.csv` and
`sweep.csv`, with the overlap class taken from `r7_overlap_counts.csv` where R7
covered it.  `has_drat` is an observation — the `.drat` file is looked for in
`certs/` and `certs_nosym/` — not an assumption.  Rows are deduplicated by the
canonical code signature `(dims, A, B)`: `sw73` and the sweep entry
`sw_Z6_A0-2-4_B0-2-4` are the same code (G = Z6, A = B = {0,2,4}) recorded under two
names, and are now one row carrying the certificate.

### B2. The five totals

| total | value |
|---|---|
| theorem-excluded (`UNSAT-theorem`) | **249** |
| DRAT-verified UNSAT, in the partition | **1** |
| DRAT-verified UNSAT, certificates on record | **10** |
| solver-only UNSAT (`UNSAT-solver`) | **62** |
| capped but theorem-excluded | **80** |
| open | **30** |

(plus `SAT-solver` 1,754 and `SAT-witness` 8; 2,104 in total.)

Two things need saying.

**The expected 17 is wrong; the gloss is right.**  "seven published codes, two H2
distinct-sums, Z6 sw73" is 7 + 2 + 1 = **10**, and 10 is exactly what the repository
holds: `bb72, bb90, bb108, bb144, bb288, bb360, bb756, h2_Z10_D_0, h2_Z24_D_0, sw73`.
No other instance has a `.drat` file at all.  (The second H2 distinct-sums instance
with a certificate is `h2_Z24_D_0`; `h2_Z12_D_0` was refuted but its proof was not
retained, `proof_bytes = 0`.)

**"DRAT-verified UNSAT" is not a partition class under the stated rules.**  The rule
"UNSAT-theorem whenever a theorem applies, regardless of solver status" puts 9 of the
10 certified instances into `UNSAT-theorem` (all are class D with distinct sums, or
subgroup-type), leaving only `sw73` in `UNSAT-cert`.  Both readings are reported above;
the abstract should say which it means.

### B3. The 62 odd-order unobstructed UNSAT — confirmed, none has a certificate

`class = C1`, `ord_d_parity = odd`, no theorem, `status_math = UNSAT-solver`: **62
instances, all with `has_drat = False`**, checked against the filesystem.  None has a
certificate.  This is the set the text calls solver-only.

## Round 3 E: lemma-check provenance

### E1. Statement names, and what was actually being tested

`data/lemma_checks.csv` is regenerated by `twoblock/analyze.py` from the four
enumeration dumps in `schedules/`.  It now carries `schedule_id`, `period_class`, and
one column per statement beside the historical `L1..L7` codes:

| statement column | historical code | holds for |
|---|---|---|
| `support_symmetry` | `L1` and `L1_Z` | general (k, l) |
| `extremal_both_ends` | `L2` | general (k, l) |
| `T1` | `L3` | general (k, l) |
| `T2` | `L4` | general (k, l) |
| `straddling` | `L5` | general (k, l) |
| `F_balance` | `L6` | general (k, l) |
| `theorem_F_count` | `L7` | general (k, l) |
| `corner_bijection` | *new* | general (k, l) |

**No column referred to the (1,6) pair structure**, so none was removed.  Every
statement in the file is stated for general (k, l) in the docstring of
`twoblock/analyze.py`, and the four enumerated instances are (1,2), (2,1), (2,3) and
(4,3) — none of them k = l = 3 — so the (1,6) rigidity argument, which is a
k = l = 3, Delta = 6 argument, was never among them.  `corner_bijection` is new: for
every overlap pair, the number of L-corners equals the number of R-corners.

### E2. Confirmation

| instance | (k, l) | Delta | solutions |
|---|---|---|---|
| `oe12` | (1, 2) | 3 | 16 |
| `oe21` | (2, 1) | 3 | 1 |
| `oe23` | (2, 3) | 5 | 200 |
| `oe43` | (4, 3) | 7 | 200 |

417 solutions, all eight statements true on every one of them, 0 failures.  The
periodicity split is unchanged: **5 invariant / 72 twisted / 340 no proper period**.

## Round 3 F: the class-C1 definition

`twoblock/overlaps.py` now asserts all three halves of the definition where it labels
an instance C1 — exactly one delta of multiplicity 2, no multiplicity above 2, and
`(n4, n6) = (N, 0)`.

`tests/test_small.py:test_T9_class_C1_definition` adds the trap instance
**G = Z8, A = {0,1,4}, B = {0,7,4}**.  Its sum multiplicities are `[1,1,1,1,2,3]`, so
`n4 = N = 8` *and* `n6 = N = 8`: a classifier testing only `n4 == N` would call it C1.

It is **not C1**, as required.  It is also **not C2** under the current taxonomy, which
defines C2 as `(n4, n6) = (2N, 0)` or `(0, N)`; this mixed pattern is neither, so the
classifier returns **`other`**.  The test asserts `klass != "C1"` and `klass ==
"other"`.  If C2 is meant to cover "one doubleton plus one triple", the taxonomy in
`twoblock/overlaps.py` needs widening — that is a definition change, not a bug fix, so
I have left it alone.

## Round 4 — verdict on top

**The template encoder is per-labelled-pair, hypothesis (a)** (Round 3 A1 above, with
the quoted lines).  Everything in Round 4 rests on that; nothing was re-enumerated.

## Round 4 (partial): generalisations

**C1 first, because everything depends on it: the template encoder is
per-labelled-pair, hypothesis (a).**  The quoted lines and the argument are in the
Round 3 A1 section above.  Nothing needs re-enumerating; the rest of Round 4 proceeds
on that basis.

### A1. General mod-4 obstruction — `twoblock/mod4.py`, `data/mod4_agreement.csv`

`obstruction_general(H_X, H_Z)` works on the parity-check matrices directly: it splits
the Tanner graph into components and returns, per component, `sum_v r_v s_v`, its
residue mod 4, whether the hypothesis holds (constant `r_v + s_v = Delta` and every
X-check of weight Delta) and the verdict `obstructed = (sum_v r_v s_v = 2 mod 4)`.

`tests/test_mod4_general.py`: **the general form reproduces the old
`n * Delta_X * Delta_Z / 2` verdict on all 2,110 instances — 669 classified + 1,441
sweep — with zero disagreements.**  The hypothesis is met on all 2,110 (every instance
here is a two-block code, hence regular) and 217 are obstructed.

### A2. The counting identity — `data/mod4_identity.csv`

`tests/test_mod4_identity.py`, 200 random valid depth-Delta layerings each of `bb72`
and `oe23` (proper or not, seed 7):

- `len(code.corners) == sum_v r_v s_v` on all **400** layerings (bb72: 648, oe23: 144).
- **X-first corners == sum_v r_v s_v / 2 on all 400 layerings.**  I expected this to
  fail — the identity is not true qubit by qubit, since bb72 has `r_v s_v = 9` at every
  qubit — but it holds globally for every valid layering, proper or not.

### B3. Per-check parity — `F_parity` in `data/lemma_checks.csv`

New unconditional column: `F_L(g) + F_R(g)` even for **every** X-check g, whatever the
class.  `L6` only tested this on the non-distinct-sums branch.  **True on all 417
enumerated schedules.**  Caveat worth stating: all four enumerated instances have
distinct sums, so these 417 exercise only the distinct-sums case; the twisted-witness
half of B3 is not yet done (see below).

### C4. Coverage of the depth-six theorem — `data/thm_six_coverage.csv`

`in_8G(d)` is decided directly (is there an x with 8x = d), so an odd-order group,
where 8 is invertible, correctly returns True for every element.  All 598 class-C1
instances:

| d in 8G | ord(d) | SAT | UNSAT | capped | total |
|---|---|---|---|---|---|
| no  | even | **263** | 0 | 0 | 263 |
| no  | odd  | 0 | 0 | 0 | 0 |
| yes | even | 2 | 0 | 0 | 2 |
| yes | odd  | 30 | 193 | 110 | 333 |

**Every one of the 263 instances with d not in 8G is SAT — no exceptions, no blocking
defect.**  Two further facts fall out: `d not in 8G` never co-occurs with `ord(d)` odd
in this set, and the only `d in 8G, ord(d) even` instances are the two Z32 cases, both
SAT with a recorded twisted witness at m = 16.

### D1, D2. Proof map

The mod-4 box now reads `sum_v r_v s_v = 0 mod 4 per component`; the twisted box reads
`twisted schedule => |M|kl even (any overlap pattern)`; a new **lifting lemma** box
feeds a new solid **depth six: class C1, d not in 8G => D_min = 6** box; the
`d in 8G, ord(d) even` box is dashed.  The rigidity and parity statements are named
`rigidity lemma (Delta = 6, distinct sums, (a,b) = (1,6))` and
`parity lemma (general Delta)`.  The open question moved to the free space under the
corollary so the right-hand chain still fits the page budget (fig2 is unchanged at
180 x 208 mm; artwork + caption 224.7 mm against 235 mm).

**The dashed box says Z32, not Z32/Z48/Z64:** there is no Z48 and no Z64 instance in
the repository (groups present: Z10-Z24, Z28, Z30, Z32, Z36).

### Not yet done

- **A3** five non-two-block regular-degree examples with unequal r_v, solved at
  depth Delta.  Needs an encoder path that takes H_X/H_Z rather than a `TwoBlockCode`;
  `twoblock/encode.py` is written against the two-block structure throughout.
- **B1** the identity `sum_{c in coset} (F_L(c)+F_R(c)) = |M| k l` over cosets of M.
  The 314 depth-6 witness schedules in `schedules/` store only `layers`; which of them
  are twisted, and with which `eps` and `m`, lives in `data/mstar.csv` and must be
  joined back before the cosets can be formed.
- **B2** enumerating Z_m-twisted schedules for the C2 and subgroup instances.
- **C2** the main-text m = 2 template, `tables/tab_template_m2.tex`, and the 18
  constraints; **C3** the extra lifting cases on non-cyclic groups.
- **D3** the per-bar annotation on figS3; **E1** anchors for the above.

`make test` covers A2 and A1 (and the Round 3 pullback); B1 and C3 are not in it yet.

## Round 4 clarifications

### Q1. The DRAT-only cell — **it was my error, and it is now empty**

The instance was `sw73`, and the theorems *do* claim it: `sw73` is
G = Z6, A = B = {0, 2, 4}, and its Tanner graph has two components each with
`sum_v r_v s_v = 54 = 2 (mod 4)`, so the componentwise mod-4 obstruction applies.  It
was recorded as certificate-only because `twoblock/coverage.py` tested only the
distinct-sums criterion on rows coming from `results.csv` and never evaluated the mod-4
predicate for them.

Fixed: `coverage.py` now evaluates **both** criteria for **every** row, from the code
itself (`theorems_for`), rather than trusting a per-file `theorem1_obstructed` column.
Cross-check: the recomputed predicate agrees with the recorded
`theorem1_obstructed` column on all of `h2_sharpness.csv` and `h4_features.csv` —
**0 disagreements** — so only the `results.csv` rows were affected.

Re-emitted five totals over 2,104 depth-6 instances:

| total | was | **now** |
|---|---|---|
| theorem-excluded | 249 | **250** |
| DRAT-verified UNSAT (partition cell) | 1 | **0** |
| solver-only UNSAT | 62 | **62** |
| capped but theorem-excluded | 80 | **80** |
| open | 30 | **30** |

**Every one of the 10 verified certificates now corroborates a theorem; none stands
alone.**  That is a stronger statement than the one the abstract was going to make.

### Q2. SAT/UNSAT/open over the 664, and class `other`

| class | SAT | UNSAT | open | total |
|---|---|---|---|---|
| D | 0 | 35 | 0 | 35 |
| C1 | 295 | 273 | 30 | 598 |
| C2 | 27 | 1 | 0 | 28 |
| SG | 0 | 3 | 0 | 3 |
| **all** | **322** | **312** | **30** | **664** |

By `status_math`: UNSAT-theorem 250, UNSAT-solver 62, SAT-solver 314, SAT-witness 8,
open 30, UNSAT-cert 0.

Class `other` (n4, n6 outside {(0,0), (N,0), (2N,0), (0,N)}):

- **0 in the 664.**
- **432 in the 1,441 sweep** — not zero.  The sweep splits C2 990, other 432, C1 18,
  SG 1 (the SG being `sw73`, which is deduplicated into the classified set, leaving
  1,440 sweep rows in `coverage.csv`).

Acted on: `coverage.py` now classifies **every** depth-6 instance, not only the 669 R7
covered, and records `class_source` (`r7_overlap_counts.csv` or `recomputed`) and
`in_sharpness_map`.  `fig4_sharpness` gained an **`other` row** — it reads 0 across,
which is the point: no instance in the map's population falls outside the four classes.
`tabS4_c1` is the class-C1 region table, so an `other` row does not belong there; the
sweep's class split belongs with the sweep, and that is where the 432 is recorded.

### Q3. What A2 does and does not test

Recorded so nobody misreads it: **`Sigma_v r_v s_v / 2` is a counting identity that
holds for every valid depth-Delta layering, proper or not.**  The test confirms the
count, not properness.  Properness enters only through the *per-pair* parity — whether
the corners of each overlap pair have orientations that cancel — which is a different
condition and is what `is_proper_by_simulation` checks.  A2 passing on 400 layerings
says the corner bookkeeping is right; it says nothing about whether any of those
layerings is proper.

## Round 4 C2, C3, D3

### C2. The main-text template at m = 2

Chosen by the stated rule — among the 72 admissible m = 2 keys, the one whose smallest
realising instance is connected with `k_logical >= 2` and minimal N:

| | |
|---|---|
| key | `00-11\|0,1,0\|0,1,0` |
| G | **Z14** (N = 14) |
| A | {0, 1, 10} |
| B | {0, 13, 2} |
| eps | `eps(g) = g mod 2` |
| colliding label pair | (1,1) and (2,2) |
| n_qubits, k_logical | **28, 6** |
| distance bound | **d <= 4** (randomised ISD, 4,000 trials) |

The distance is *not* in `instances.csv` — `d` is `--` for every row there, and this
instance is not in that file at all — so the bound above is computed here, by
`twoblock.distance.distance_upper_bound`, and is an upper bound only.

The pulled-back schedule is a valid, proper depth-6 schedule on that code by F2
simulation, stored as `schedules/tpl_main_m2_Z14_d6.json`; parameters in
`data/template_main.csv`.

Two tables: `tables/tab_template_m2.tex` (the 24 entries — 2 classes x 3 labels x 4 edge
types — as a layer incidence table) and `tables/tab_template_m2_checks.tex` (every
constraint with the entries meeting it).  Both compile under pdflatex.

**On the constraint count.**  The brief says 18.  The encoder actually imposes **24**
instances, and all 24 are met: per class c in Z_2 there are 4 distinctness families
(X-check, Z-check, L-qubit, R-qubit — not 6), 7 equal-orientation pairs and 1
four-corner parity, i.e. 12 per class over 2 classes.  The table lists all of them.

### C3. Lifting across groups for the chosen key

Appended to `data/template_pullback.csv`; 15 pullbacks in total, all pass.

| group | N | cyclic? | verdict |
|---|---|---|---|
| Z10 | 10 | cyclic | pass |
| Z2 x Z6 | 12 | non-cyclic | pass |
| Z2 x Z8 | 16 | non-cyclic | pass |

"Non-cyclic" is tested as `gcd(dims) > 1`, so Z2 x Z5 — which is Z10 — is not counted;
an earlier pass of this had used it and would have been wrong.

### D3. figS3

A row `of those, eps(d) in 8 Z_m` is added under the totals, per modulus: 72, 486, 288,
2250, 1944, 1152 of 144, 486, 1152, 2250, 3888, 9216.  Note m = 3 and m = 5 give the
total, because gcd(8, m) = 1 there and 8 Z_m is all of Z_m — the condition is vacuous
at odd m, exactly as "d in 8G" is vacuous in a group of odd order (Round 3 A3).

## Round 4 B1: the twisted coset identity

`twoblock/twisted_identity.py` and `tests/test_twisted_identity.py`; record in
`data/twisted_identity.csv`.

**eps and m are now stored with every twisted witness.**  Each of the 289 class-C1
instances that `data/mstar.csv` records as carrying a twisted schedule was re-solved at
its m*, and the homomorphism that admits it written to
`schedules/<instance>_d6_twisted_m<m>.json` as `eps_coeffs` (the coefficients on the
generators of G), together with `m`, `eps_image`, `eps_on_A`, `eps_on_B`, `abs_M` and
the layering.  All 289 files are present and every witness is proper by F2 simulation.

F_L(c) and F_R(c) are read off the label tables, using
`(X_g, L_{g+a_s}) = s`, `(Z_g, L_{g-b_t}) = t`, `(X_g, R_{g+b_t}) = t`,
`(Z_g, R_{g-a_s}) = s`:

    F_L(c) = #{ (s,t) : lay_Z^L[c + a_s + b_t][t] > lay_X^L[c][s] }
    F_R(c) = #{ (t,s) : lay_Z^R[c + b_t + a_s][s] > lay_X^R[c][t] }

**The identity `sum_{c in coset} (F_L(c)+F_R(c)) = |M| k l` holds on every coset
tested, with zero failures.**  Over the 289 witnesses: 295 cosets (1 or 2 cosets of M
inside eps(G) per witness), and

| quantity | value |
|---|---|
| witnesses | **289** |
| |M| values | **2, 4, 6, 8, 10, 12, 14, 16** |
| |M| odd | **0** |
| m values | 2, 4, 6, 8, 10, 12, 14, 16 |
| identity failures | **0** |

Every |M| that occurs is even, on every one of the 289 witnesses — the even-order
theorem, checked rather than assumed, on the whole class-C1 witness set.

### The exhaustive template sweep

Run separately (36 minutes): **every one of the 11,412 admissible template keys**, on
top of the 289 witnesses.

| | |
|---|---|
| cosets checked | **12,931** (295 from witnesses, 12,636 from 9,696 template keys) |
| identity failures | **0** |
| \|M\| odd, anywhere | **0** |

|M| by modulus over the templates, every value even:

| m | admissible keys | \|M\| values |
|---|---|---|
| 2 | 72 | 2 |
| 4 | 864 | 2, 4 |
| 6 | 2,412 | 2, 6 |
| 8 | 8,064 | 2, 4, 8 |

(m = 3 and m = 5 admit no keys at all, so they contribute none.)

`make test` runs the same check with 25 template keys per modulus so it stays fast;
`--full` reproduces the sweep above.

## Round 4 B2: twisted schedules outside class C1

`twoblock/b2_twisted_outside_c1.py`, record in `data/b2_twisted_outside_c1.csv`.

Population: the **27 SAT instances of class C2 or SG** in `data/h2_sharpness.csv`
(N = 10, 12, 14, 16, 18, 20, 24), searched at every divisor m | N over every non-trivial
homomorphism eps: G -> Z_m — **123 (instance, m) combinations** in all.

**Cap: 20 s per (instance, m)**, not the 120 s of the brief.  At 120 s the worst case
was 4.1 hours and the run was heading there; the time was going into *proving no
schedule exists* at a given m, which is not what B2 asks.  A shorter cap can only miss
schedules, never invalidate the assertion, since the claim is about every schedule that
is found.  **A combination that hits the cap is recorded `capped`, never as "none".**

### Result

| | |
|---|---|
| twisted schedules found | **323** |
| \|M\| values | **2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24** (11 distinct) |
| \|M\| odd | **0** |
| capped (instance, m) combinations | **29** |
| rows in the file | 352 (323 found + 29 capped) |

All 27 instances yielded at least one twisted schedule, every one of them proper by F2
simulation, and **every |M| that occurs is even**.

One thing to say plainly about the population: `h2_sharpness.csv` holds 28 class-C2
instances (27 SAT, 1 UNSAT) and 2 subgroup-type instances, and **both SG instances are
UNSAT at depth 6**.  So "the SAT instances of class C2 or SG" is 27 instances, all of
them C2 — this run tests the twisted theorem outside class C1 but not outside class C2.

The 29 capped combinations are recorded as `capped` and are not evidence of absence: at
those (instance, m) the search was stopped, and nothing is claimed about whether a
schedule exists there.

**This is the only test of the twisted theorem outside class C1.**  Within its reach —
27 class-C2 instances, 323 schedules, 11 distinct even |M| — it holds without exception.
Outside class C1 and C2 the generalisation rests on the proof alone.

## Round 4 A3: non-two-block examples — **not tested**

Recorded as not tested, per the brief's escape clause.  What is worth knowing is *where*
it stopped, because it was not the adapter.

The plan was: pick a degree profile with unequal r_v meeting the general hypothesis
(every qubit r_v + s_v = Delta, every X-check of weight Delta) and
`sum_v r_v s_v = 2 mod 4`, build H_X and H_Z, then drive the existing encoder through a
thin adapter.  At Delta = 4 the arithmetic is easy: r_v s_v is odd exactly at qubits of
type (1,3) or (3,1), so the sum is 2 mod 4 iff the number of such qubits is 2 mod 4 —
for instance r = (1,3,2,2,2,2) on six qubits, giving sum_v r_v s_v = 22.

The obstacle is **CSS commutation, not the adapter**.  H_X and H_Z must satisfy
`H_X H_Z^T = 0`, so every Z-check has to lie in the kernel of H_X *while* the columns of
H_Z realise the prescribed s_v = Delta - r_v exactly.  A search over four such profiles
(n = 6, 8, 10), randomising H_X subject to its column degrees and enumerating kernel
vectors for H_Z, found no commuting pair within 480 s and was stopped.  The encoder
adapter itself was never written, so no time was spent there.

This is the illustrative example only: **the theorem is proved, and A1 already verifies
the general form against the old one on all 2,110 instances in the repository.**  What
is missing is a witness *outside* the two-block family, which every instance here is.
Two ways forward, if it is wanted: search at Delta = 6 where the kernel is larger and
weight-6 Z-checks are plentiful, or construct one by hand from a hypergraph product
with a deliberately irregular factor.

## Round 5, items 1-8: counts and definitions

### 1. Capped instances — **118**, not 113

`data/coverage.csv`, column `status_solver == "capped"`, over all 2,104 depth-6 rows:

| `status_math` | capped |
|---|---|
| UNSAT-theorem | 80 |
| open | 30 |
| SAT-witness | 8 |
| **total** | **118** |

All 118 lie inside the 664 sharpness-map population (`in_sharpness_map == True`), so
the figure and the whole-corpus counts agree.

**Yes — the SAT-witness instances in the C1 odd-order unobstructed cell are capped.**
All 8 SAT-witness rows have `status_solver == capped`: 5 in the C1 / ord(d) odd /
unobstructed cell and 3 in the C1 / ord(d) even cell.  That is what SAT-witness means
in this table — the solver call was capped and a verified twisted schedule settled it.

Corrected numbers to use:

- **Fig. 3 footnote: 118 capped** (the figure already prints 118).
- **Table S7 capped column**: the table with a capped column is `tabS4_c1.tex`
  (`data/c1_final.csv`, column `UNDETERMINED`), whose class-C1 total is **110**;
  the 118 is the whole corpus, the 110 is class C1 alone.  The two must not be
  interchanged.
- **The S6 sentence**: "the three capped satisfiable instances" is wrong on both
  readings.  It is **eight** capped satisfiable instances in total, or **five** if the
  sentence means only the C1 ord(d) odd unobstructed cell.

### 2. Composition of the 664, and the SG row

The SG row of Fig. 3 is exactly the three instances expected:

| instance | \|G\| | `status_math` | source |
|---|---|---|---|
| `sw73` | **6** | UNSAT-theorem | `data/results.csv` |
| `h2_Z12_subgroup` | 12 | UNSAT-theorem | `data/h2_sharpness.csv` |
| `h2_Z18_subgroup` | 18 | UNSAT-theorem | `data/h2_sharpness.csv` |

`sw73` (Z6, A = B = {0,2,4}) **is inside the 664**, and it is the only instance with
\|G\| < 10: the other **663 span \|G\| = 10 to 378**, over the orders
10-24, 28, 30, 32, 36, 45, 54, 72, 144, 180, 378.  So the text may say either
"664 instances, \|G\| = 6 to 378" or "sw73 plus 663 instances with \|G\| = 10 to 378",
but not "664 instances with \|G\| = 10 to 378".

### 3. How the \|G\| = 10-24 instances were generated — and "inequivalent" is wrong

From `twoblock/sharpness.py`:

**(a) Groups.** Cyclic only.  H2 uses `NS = [10, 12, 14, 16, 18, 20, 24]`; the H4
extension uses `H4_NS = range(10, 25) + [28, 30, 32, 36]`.  No non-cyclic group was
ever sampled.  The code records no justification for the specific set beyond the
docstring's "sharpness at larger N", so the repository cannot say why those orders.

**(b) Sampling.** Random, not exhaustive, seed 7 (`SEED = 7`,
`rng = random.Random(seed)`).  A and B are each `{0}` plus two values drawn with
`rng.sample(range(1, N), 2)`; H2 draws up to 200,000 candidates per N and keeps the
first `PER_CLASS = 4` per (N, class); H4 tries up to 400,000 and keeps the first 30
class-C1 per N.  The subgroup instances A = B = {0, N/3, 2N/3} are added
deterministically for N in {12, 18}.

**(c) Equivalence.  There is none.**  The only quotient is the normalisation 0 in A and
0 in B, and de-duplication is by literal equality of the sorted tuples:

```python
            A = tuple(sorted([(0,)] + [(x,) for x in rng.sample(range(1, N), 2)]))
            B = tuple(sorted([(0,)] + [(x,) for x in rng.sample(range(1, N), 2)]))
            if (A, B) in seen:
                continue
            seen.add((A, B))
```

No translation, no automorphism of G, no A-B swap, no negation, no label permutation.
**The manuscript must not call these instances "inequivalent".**

How much it matters is now measured.  `twoblock/instance_census.py` canonicalises under
the relation that genuinely leaves a two-block code unchanged —
`(A, B) ~ (uA + t1, uB + t2)` for u a unit of Z_N, and `(A, B) ~ (B, A)` — and counts
orbits.  Of the 664 sampled instances, **only 475 are inequivalent; 189 (28 per cent)
duplicate another one**:

| class | sampled | inequivalent |
|---|---|---|
| C1 | 598 | 416 |
| D | 35 | 30 |
| C2 | 28 | 26 |
| SG | 3 | 3 |
| **all** | **664** | **475** |

The redundancy is worst at small N, where the group has few units and the sample is
large relative to the number of orbits: Z10 C1 is 34 sampled for 6 inequivalent, Z11 C1
is 30 for 4, Z13 C1 is 30 for 9.  Any statistic over the 664 is weighted by orbit size.
Per-group, per-class counts are in `data/instances_by_group.csv`
(columns `N, group, klass, sampled, inequivalent, duplicates`).

### 5. What the 669 is

`data/r7_overlap_counts.csv`, 669 rows: **every instance whose overlap class was
recomputed in R7** — 656 from the H2/H4 families plus 13 named instances (column
`family`: `H2/H4` 656, `named` 13).  By class: C1 598, D 40, C2 28, SG 3.  664 of them
have a recorded depth-6 outcome; the 5 that do not are `k5`, `oe12`, `oe21`, `oe23`,
`oe43`, whose Delta is not 6.  The text can name it "the 669 classified instances" or
drop the number and use 664.

### 6. The two class-D certificates

**They are not in `data/results.csv`** — that file holds the seven published codes and
sw73 only.  Both are rows of `data/h2_sharpness.csv` (columns `time_s`, `proof_bytes`,
`verified`):

| instance | G | A | B | N | solve (s) | proof (bytes) | drat-trim | nvars | nclauses |
|---|---|---|---|---|---|---|---|---|---|
| `h2_Z10_D_0` | Z10 | {0, 3, 6} | {0, 1, 9} | 10 | 4.127 | 12,680,151 | VERIFIED | 2,400 | 11,161 |
| `h2_Z24_D_0` | Z24 | {0, 1, 8} | {0, 5, 14} | 24 | 3.592 | 18,286,715 | VERIFIED | 5,760 | 26,785 |

These are the smallest and largest class-D group orders among the certified
distinct-sums instances (10 and 24).

### 7. The Z6 cross-check — the two sections must not both say "confirmed"

`data/solver_crosscheck.csv`, row `instance == sw73`, `family == certs`:

- **CaDiCaL: UNSAT in 232.67 s.**
- **Glucose: UNKNOWN — it hit the 300 s cap** (`glucose_time = 300.122`), so
  `agree = False`.

So the sw73 refutation is confirmed by kissat (558.05 s) and by CaDiCaL (232.67 s), and
**not** by Glucose, which did not finish.  Sec. IV and S7 should both say "confirmed by
a second solver (CaDiCaL); Glucose did not decide it within 300 s", and neither should
claim three-solver agreement.

### 8. Template keys: 11,412 = 10,404 + 1,008

The S7 sentence is wrong.  9,696 was the number of *distinct key strings* in
`data/twisted_identity.csv`, and key strings repeat across moduli — the same string can
be admissible at more than one m — so it is neither the number of keys nor the number
with several cosets.

A template key at modulus m has m/\|M\| cosets, so it has exactly one iff \|M\| = m:

| m | admissible keys | one coset | more than one | cosets |
|---|---|---|---|---|
| 2 | 72 | 72 | 0 | 72 |
| 4 | 864 | 792 | 72 | 936 |
| 6 | 2,412 | 2,340 | 72 | 2,556 |
| 8 | 8,064 | 7,200 | 864 | 9,072 |
| **all** | **11,412** | **10,404** | **1,008** | **12,636** |

**10,404 keys have exactly one coset**, and 11,412 = 10,404 + 1,008.  The 12,636
template cosets plus the 295 witness cosets give the 12,931 of Sec. IV.

## Round 5, items 12-14

### 12. The depth-7 schedule as an upper bound for the family

The schedule in `schedules/bb72_d7_inv.json` is exactly the one in the brief:
X: L = (1, 2, 7), R = (4, 3, 5); Z: L = (5, 3, 4), R = (6, 7, 1).  Because it assigns a
layer from (check kind, qubit side, label) alone — nothing about the group element — it
can be applied verbatim to any two-block code with k = l = 3.
`tests/test_uniform_depth7.py`; record in `data/uniform_depth7.csv`.

**Orientation table.**  o_L = [pi_XL(s) < pi_ZL(t)], o_R = [pi_XR(t) < pi_ZR(s)]:

| (s, t) | t = 1 | t = 2 | t = 3 |
|---|---|---|---|
| **s = 1** | 1 / 1 | 1 / 1 | 1 / 1 |
| **s = 2** | 1 / 1 | 1 / 1 | 1 / 1 |
| **s = 3** | 0 / 0 | 0 / 0 | 0 / 0 |

(each cell is o_L / o_R).  **All nine pairs have o_L = o_R.**  The reason is visible in
the numbers: pi_XL = (1, 2, 7) puts s = 1, 2 below every entry of pi_ZL = (5, 3, 4) and
s = 3 above all of them, so o_L depends only on s; and pi_ZR = (6, 7, 1) against
pi_XR = (4, 3, 5) makes o_R depend only on s in the same way.  Every overlap pair
therefore cancels whatever the group.

**Simulation.**  Applied verbatim and re-checked by F2 simulation:

| group | instances | proper at depth 7 |
|---|---|---|
| the seven published codes | 7 | **7 / 7** |
| random distinct-sums (seed 7) | 20 | **20 / 20** |
| random C1/C2 (seed 7) | 20 | **20 / 20** |

**47 of 47**, every one well inside the 60 s cap.

**Comparison with Bravyi et al. Table 3: the repository cannot decide this.**  Only
Table 1 of that paper is transcribed here — the polynomials, in
`twoblock/instances.py` — and nothing from their Table 3 or their schedule figure is
recorded anywhere in the repo.  Settling whether this is their schedule, a relabelling
of it, or a different depth-7 schedule needs their layer order, which would have to be
entered by hand and checked against the four label tuples above.

### 13. The lemma checks

The statements, quoted from the docstring of `twoblock/analyze.py`, with
x_i = the number of X-edges on the L side in layer i, Lambda = {i : x_i > 0},
a = min Lambda, b = max Lambda, and E = the X-checks whose L-layers contain a or b:

| | statement | column |
|---|---|---|
| L1 | a + b = D + 1 | `support_symmetry` (with L1_Z) |
| L2 | every check in E contains both a and b, X/L and symmetrically Z/R | `extremal_both_ends` |
| L3 | (T1) for an X-check in E and an R-edge at layer v strictly inside (a, b): the Z-edge labelled s_a has layer > v and the one labelled s_b has layer < v | `T1` |
| L4 | (T2) for an X-check not in E and an L-edge at layer p: the Z-edge labelled t_a has layer > p and the one labelled t_b has layer < p | `T2` |
| L5 | (straddling) for an X-check not in E and an L-edge at layer p: among the Z-layers of that qubit inside [a, b], one is > p and one is < p | `straddling` |
| L6 | (F-balance) F_L = F_R when the sums are distinct, else F_L + F_R even | `F_balance` |
| L7 | (Theorem F count) **if** every x_i is in {0, N} **then** F_L + F_R = k l | `theorem_F_count` |

**L7 ran on 140 of 417 because it is conditional, not because of a coverage gap.**  Its
hypothesis is `all_x_in_0_N`, and `data/lemma_checks.csv` has that true on exactly 140
rows (column `L7_applicable`): oe12 16/16, oe21 1/1, oe23 116/200, oe43 7/200.  On the
other 277 the hypothesis fails, so the implication is vacuous and nothing is asserted.

The four enumerated instances:

| instance | G | N | (k, l) | Delta | A | B |
|---|---|---|---|---|---|---|
| `oe12` | Z8 | 8 | (1, 2) | 3 | {0} | {0, 4} |
| `oe21` | Z8 | 8 | (2, 1) | 3 | {0, 3} | {0} |
| `oe23` | Z12 | 12 | (2, 3) | 5 | {0, 1} | {0, 4, 8} |
| `oe43` | Z16 | 16 | (4, 3) | 7 | {0, 1, 2, 3} | {0, 4, 8} |

**`oe12` and `oe21` are not dual instances.**  Both live on Z8, but the dual of oe12
would be A = {0, 4}, B = {0}, whereas oe21 has A = {0, 3}.  They are not even
equivalent: the units of Z8 are 1, 3, 5, 7, and {0, 4} is fixed by all of them
(4u = 4 mod 8 for odd u) while {0, 3} maps to {0, 3}, {0, 1}, {0, 7}, {0, 5} — never
{0, 4}.  They are two genuinely different (k, l) = (1, 2) and (2, 1) instances.

### 14. Hardware

Everything in this repository ran on **one workstation**, from the run logs in `logs/`
and the machine itself:

- **CPU** Intel Core Ultra 9 275HX, **24 logical cores**
- **RAM** 16,373,428 kB (about 15.6 GiB)
- **OS** Linux 6.18.33.2-microsoft-standard-WSL2

Wall time against process time for the Table I refutations (`logs/<instance>_d6.log`,
`status=... time=` versus kissat's own `process-time`, with peak resident set):

| instance | wall (s) | kissat process-time (s) | max RSS |
|---|---|---|---|
| bb72 | 1.39 | 1.43 | 45 MB |
| bb90 | 2.03 | 2.09 | 47 MB |
| bb108 | 2.43 | 2.52 | 50 MB |
| bb144 | 2.69 | 2.79 | 55 MB |
| bb288 | 4.78 | 4.99 | 74 MB |
| bb360 | 5.36 | 5.61 | 84 MB |
| bb756 | 5.94 | 6.10 | 139 MB |
| **sw73 (Z6)** | **558.05** | **557.66** | 56 MB |

Wall and CPU time agree to within a few per cent throughout: every solver invocation is
single-threaded, and the process pool is used only to fan out independent cases.

**No run used OLCF resources**, or any cluster: there is no batch script, no scheduler
directive and no remote-host reference anywhere in the repository.

## Round 6: the redrawn figure set

Nine figures, all PASS, all built by `make figures` from the CSVs.  Blue and orange now
mean X and Z and nothing else; outcomes use the neutral ramp with rose reserved for
`open`; the twist modulus is `q` throughout; weights are `k`, `\ell`; Kőnig is spelled
with the double acute.  No theorem numbers appear in any figure.

| file | size (mm) | what changed |
|---|---|---|
| `fig1_setup_certificate` | 180 x 78 | four panels: gate-level model, the two-qubit constraint with its truth table, the failing depth-6 colouring, the depth-7 ladder |
| `fig2_mechanism` | 180 x 72 | new: support symmetry, rigidity, parity, cancellation |
| `fig3_decision_tree` | 180 x 84 | replaces the heat map |
| `figS1_proof_map` | 180 x 208 | logic redrawn |
| `figS2_sweep_by_group` | 88 x 76 | ×, S(delta), note moved to the caption |
| `figS3_templates_by_q` | 88 x 88 | renamed from `_by_m`, d-bar, en dash, no panel letter |
| `figS4_periods` | 88 x 80 | log axis, count on every bar, category renamed |
| `figS5_theorem1_profile` | 88 x 116 | new x-axis label, complete footnote |
| `figS7_certificates` | 180 x 90 | panels a and b only, Z6 named in full |

**Deleted:** `fig2_proof_map_small`, `fig3_rigidity_parity`, `fig4_sharpness`,
`figS6_lemma_profiles`, and the old `fig2_proof_map` / `figS1_certificates` names
(kept as manifest aliases).  `fig_lemma_profiles` and `fig2_small` are gone from the
source, so `figure_values.csv` no longer carries their values.

### Things the redraw settled, or could not

- **No half-disc icons remain anywhere.**  Corner orientations are written as
  `o_L = 1`, `o_R = 0` and as the digits in the cancellation panel.
- **The `◆` character is not in TeX Gyre Heros.**  The DRAT marker in the decision
  tree is drawn as a diamond marker, not typed, so it embeds cleanly.
- **The arrow from "no common L-side layer set" into the support lemma is gone**, and
  support symmetry is now fed by `M_pi = 0` directly.  The three general obstructions
  hang off a spine from the root, so they read as parallel consequences rather than a
  chain.
- **The decision tree asserts its own arithmetic**: the six leaf counts are asserted to
  sum to 664 and the DRAT markers to 10, and `CHECK.md` re-derives both from
  `data/coverage.csv` independently.
- **`fig2_mechanism` panel (a) draws the 1..6 ladder only.**  The (k, l) = (4, 3),
  Delta = 7 case appears as text, as asked; no 7-layer example is drawn.

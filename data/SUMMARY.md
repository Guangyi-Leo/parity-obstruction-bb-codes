# Interleaved syndrome-extraction depth of two-block codes

SAT certificates and lemma checks.  Every number below is produced by `make all` from a fixed seed (7); nothing is hand-entered.

*Generated 2026-09-08 19:17:46*

## Environment

| component | version |
|---|---|
| python | 3.11.15 |
| platform | Linux-6.18.33.2-microsoft-standard-WSL2-x86_64-with-glibc2.39 |
| kissat | 4.0.4 (git 8af8e56) |
| cadical | 3.0.1 (git c607304) |
| drat-trim | git 2e3b2dc |
| numpy | 2.4.6 |
| python-sat | 1.9.dev15 |

Solver runs are single-threaded.  Command lines for every run are recorded in `logs/<instance>_d<D>.log`.

## (i) Instances

`distinct sums` means the k*l sums a_s + b_t are pairwise distinct, which is equivalent to every entry of H_X H_Z^T being 0 or 2.

| instance | family | group | N | qubits | k | l | Δ | edges | distinct sums | max H_X H_Z^T entry | \|P(δ)\| histogram |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bb72 | IBM | Z6xZ6 | 36 | 72 | 3 | 3 | 6 | 432 | True | 2 | {"1": 9} |
| bb90 | IBM | Z15xZ3 | 45 | 90 | 3 | 3 | 6 | 540 | True | 2 | {"1": 9} |
| bb108 | IBM | Z9xZ6 | 54 | 108 | 3 | 3 | 6 | 648 | True | 2 | {"1": 9} |
| bb144 | IBM | Z12xZ6 | 72 | 144 | 3 | 3 | 6 | 864 | True | 2 | {"1": 9} |
| bb288 | IBM | Z12xZ12 | 144 | 288 | 3 | 3 | 6 | 1728 | True | 2 | {"1": 9} |
| bb360 | IBM | Z30xZ6 | 180 | 360 | 3 | 3 | 6 | 2160 | True | 2 | {"1": 9} |
| bb756 | IBM | Z21xZ18 | 378 | 756 | 3 | 3 | 6 | 4536 | True | 2 | {"1": 9} |
| oe23 | one-even | Z12xZ1 | 12 | 24 | 2 | 3 | 5 | 120 | True | 2 | {"1": 6} |
| oe21 | one-even | Z8xZ1 | 8 | 16 | 2 | 1 | 3 | 48 | True | 2 | {"1": 2} |
| oe43 | one-even | Z16xZ1 | 16 | 32 | 4 | 3 | 7 | 224 | True | 2 | {"1": 12} |
| oe12 | one-even | Z8xZ1 | 8 | 16 | 1 | 2 | 3 | 48 | True | 2 | {"1": 2} |
| k5 | optional | Z26xZ1 | 26 | 52 | 5 | 5 | 10 | 520 | True | 2 | {"1": 25} |
| sw73 | sweep | Z6 | 6 | 12 | 3 | 3 | 6 | 72 | False | 6 | {"3": 3} |

## (ii) Certificates

Depth Δ = 6 is refuted with a DRAT proof checked by `drat-trim` (the checker must print `s VERIFIED`).  Depth 7 is witnessed by an explicit schedule whose properness is re-checked independently by F2 linear-map simulation of the CNOT circuit, not by the SAT encoding.

| instance | N | Δ | D | assumption | status | solve s | proof MB | drat-trim | verify s | proper (sim) | vars | clauses |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bb72 | 36 | 6 | 6 | - | UNSAT | 1.39 | 12.9 | VERIFIED | 1.28 | - | 8640 | 40177 |
| bb72 | 36 | 6 | 7 | - | SAT | 117.29 | - | - | - | True | 10152 | 48817 |
| bb72 | 36 | 6 | 7 | inv | SAT | 0.01 | - | - | - | True | 10152 | 49249 |
| bb90 | 45 | 6 | 6 | - | UNSAT | 2.03 | 20.3 | VERIFIED | 1.59 | - | 10800 | 50221 |
| bb90 | 45 | 6 | 7 | - | SAT | 413.95 | - | - | - | True | 12690 | 61021 |
| bb90 | 45 | 6 | 7 | inv | SAT | 0.01 | - | - | - | True | 12690 | 61561 |
| bb108 | 54 | 6 | 6 | - | UNSAT | 2.43 | 20.8 | VERIFIED | 2.23 | - | 12960 | 60265 |
| bb108 | 54 | 6 | 7 | inv | SAT | 0.01 | - | - | - | True | 15228 | 73873 |
| bb144 | 72 | 6 | 6 | - | UNSAT | 2.69 | 23.1 | VERIFIED | 2.89 | - | 17280 | 80353 |
| bb144 | 72 | 6 | 7 | inv | SAT | 0.01 | - | - | - | True | 20304 | 98497 |
| bb288 | 144 | 6 | 6 | - | UNSAT | 4.78 | 46.4 | VERIFIED | 13.14 | - | 34560 | 160705 |
| bb288 | 144 | 6 | 7 | inv | SAT | 0.02 | - | - | - | True | 40608 | 196993 |
| bb360 | 180 | 6 | 6 | - | UNSAT | 5.36 | 52.0 | VERIFIED | 19.75 | - | 43200 | 200881 |
| bb360 | 180 | 6 | 7 | inv | SAT | 0.03 | - | - | - | True | 50760 | 246241 |
| bb756 | 378 | 6 | 6 | - | UNSAT | 5.94 | 46.5 | VERIFIED | 28.65 | - | 90720 | 421849 |
| bb756 | 378 | 6 | 7 | inv | SAT | 0.06 | - | - | - | True | 106596 | 517105 |
| sw73 | 6 | 6 | 6 | - | UNSAT | 558.05 | 2727.4 | VERIFIED | 897.42 | - | 1512 | 6913 |

Runs that have not returned a status yet (launched with a 12 h timeout and still in flight when this report was generated, or not started):

- `bb108` depth 7 (unrestricted)
- `bb144` depth 7 (unrestricted)
- `bb288` depth 7 (unrestricted)
- `bb360` depth 7 (unrestricted)
- `bb756` depth 7 (unrestricted)

The unrestricted depth-7 search is a solver-performance question, not an existence question: the `inv` rows above already exhibit a depth-7 schedule for every one of these codes, verified by F2 simulation.

**Timeouts / unknown: 0**

Independent re-decision of the same CNFs with a second solver (a DRAT proof rules out a bug in kissat; this also rules out a mistake in how the proof is produced or checked):

| instance | D | solver | version | status | s |
|---|---|---|---|---|---|
| bb72 | 6 | cadical | 3.0.1 (git c607304) | UNSAT | 2.24 |
| bb90 | 6 | cadical | 3.0.1 (git c607304) | UNSAT | 1.96 |
| bb108 | 6 | cadical | 3.0.1 (git c607304) | UNSAT | 2.83 |
| bb144 | 6 | cadical | 3.0.1 (git c607304) | UNSAT | 3.46 |
| bb288 | 6 | cadical | 3.0.1 (git c607304) | UNSAT | 1.92 |
| bb360 | 6 | cadical | 3.0.1 (git c607304) | UNSAT | 2.96 |
| bb756 | 6 | cadical | 3.0.1 (git c607304) | UNSAT | 6.19 |
| sw73 | 6 | cadical | 3.0.1 (git c607304) | UNSAT | 287.68 |

### Translation-invariant schedules

Translating every vertex by g in G is a symmetry of the problem, so it is natural to ask for schedules where the layer of an edge depends only on its label (kind, side, s or t) and not on which check it belongs to.  Such a schedule is just 2Δ numbers and its constraint system involves only k, l, D and the multiplicities |P(δ)| — not the group — so one solution serves every code with the same parameters.  `encode.find_invariant_schedule` decides this exactly.

| instance | k | l | Δ | invariant at depth Δ | invariant at depth Δ+1 |
|---|---|---|---|---|---|
| bb72 | 3 | 3 | 6 | none | `XL=[1, 2, 7] XR=[4, 3, 5] ZL=[5, 3, 4] ZR=[6, 7, 1]` |
| bb90 | 3 | 3 | 6 | none | `XL=[1, 2, 7] XR=[4, 3, 5] ZL=[5, 3, 4] ZR=[6, 7, 1]` |
| bb108 | 3 | 3 | 6 | none | `XL=[1, 2, 7] XR=[4, 3, 5] ZL=[5, 3, 4] ZR=[6, 7, 1]` |
| bb144 | 3 | 3 | 6 | none | `XL=[1, 2, 7] XR=[4, 3, 5] ZL=[5, 3, 4] ZR=[6, 7, 1]` |
| bb288 | 3 | 3 | 6 | none | `XL=[1, 2, 7] XR=[4, 3, 5] ZL=[5, 3, 4] ZR=[6, 7, 1]` |
| bb360 | 3 | 3 | 6 | none | `XL=[1, 2, 7] XR=[4, 3, 5] ZL=[5, 3, 4] ZR=[6, 7, 1]` |
| bb756 | 3 | 3 | 6 | none | `XL=[1, 2, 7] XR=[4, 3, 5] ZL=[5, 3, 4] ZR=[6, 7, 1]` |
| oe23 | 2 | 3 | 5 | `XL=[5, 1] XR=[4, 3, 2] ZL=[3, 4, 2] ZR=[1, 5]` | `XL=[3, 4] XR=[2, 5, 1] ZL=[6, 2, 5] ZR=[3, 4]` |
| oe21 | 2 | 1 | 3 | `XL=[3, 1] XR=[2] ZL=[2] ZR=[1, 3]` | `XL=[4, 1] XR=[2] ZL=[2] ZR=[1, 4]` |
| oe43 | 4 | 3 | 7 | `XL=[1, 7, 6, 2] XR=[5, 4, 3] ZL=[4, 3, 5] ZR=[6, 1, 2, 7]` | `XL=[7, 1, 8, 2] XR=[6, 4, 3] ZL=[3, 4, 6] ZR=[2, 7, 1, 8]` |
| oe12 | 1 | 2 | 3 | `XL=[2] XR=[3, 1] ZL=[1, 3] ZR=[2]` | `XL=[1] XR=[2, 3] ZL=[2, 3] ZR=[4]` |
| k5 | 5 | 5 | 10 | none | `XL=[11, 3, 4, 8, 1] XR=[10, 5, 2, 7, 6] ZL=[2, 7, 10, 5, 6] ZR=[1, 8, 9, 3, 11]` |
| sw73 | 3 | 3 | 6 | none | `XL=[1, 2, 3] XR=[4, 5, 6] ZL=[4, 5, 6] ZR=[1, 2, 7]` |

Every schedule shown was expanded to all 2NΔ edges and re-verified by F2 simulation. The depth-Δ column is `none` for exactly the instances that are UNSAT at depth Δ in table (ii), and the depth-Δ+1 witnesses are what the `inv`-tagged rows there pin down with unit assumptions.

## (iii) Lemma pass rates

One row per (instance, enumerated solution).  `L2` is the conjunction of the X/L-side and Z/R-side readings, both reported separately.

| instance | #solutions | L1 | L1_Z | L2_X | L2_Z | L2 | L3 | L4 | L5 | L6 | L7 | all |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| oe12 | 16 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| oe21 | 1 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| oe23 | 200 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| oe43 | 200 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| ALL | 417 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

Coverage (how much each lemma actually had to check, so that a 100% pass rate is not vacuous):

| instance | #sol | (a,b) observed | #distinct x-profiles | L3 sub-checks | L4 sub-checks | L4 vacuous | L5 sub-checks | L7 applicable |
|---|---|---|---|---|---|---|---|---|
| oe12 | 16 | [(2, 2)] | 1 | 0 | 0 | 0 | 0 | 16 |
| oe21 | 1 | [(1, 3)] | 1 | 8 | 0 | 0 | 0 | 1 |
| oe23 | 200 | [(1, 5), (2, 4)] | 4 | 3960 | 880 | 0 | 880 | 116 |
| oe43 | 200 | [(1, 7), (2, 6)] | 24 | 5423 | 5484 | 0 | 5484 | 7 |

**No failures: all 417 enumerated solutions pass all 10 lemma checks.**

## (iv) Small sweep (k = l = 3, depth 6, 600 s timeout)

All A, B of size 3 containing the identity, over Z4, Z2xZ2, Z6, Z8, Z2xZ4 and Z2xZ2xZ2.  Z2xZ2xZ2 is not of the form Z_ell x Z_m, so the group is built as a genuine triple product rather than misrepresented as a two-factor group.

| max \|P(δ)\| | #instances | #distinct sums | SAT | UNSAT | TIMEOUT | mean s | max s |
|---|---|---|---|---|---|---|---|
| 2 | 1206 | 0 | 1206 | 0 | 0 | 0.87 | 9.62 |
| 3 | 235 | 0 | 234 | 1 | 0 | 2.29 | 513.84 |

By group and maximum overlap multiplicity:

| group | max \|P(δ)\| | #instances | SAT | UNSAT | TIMEOUT |
|---|---|---|---|---|---|
| Z4 | 3 | 9 | 9 | 0 | 0 |
| Z2xZ2 | 3 | 9 | 9 | 0 | 0 |
| Z6 | 2 | 72 | 72 | 0 | 0 |
| Z6 | 3 | 28 | 27 | 1 | 0 |
| Z8 | 2 | 378 | 378 | 0 | 0 |
| Z8 | 3 | 63 | 63 | 0 | 0 |
| Z2xZ4 | 2 | 378 | 378 | 0 | 0 |
| Z2xZ4 | 3 | 63 | 63 | 0 | 0 |
| Z2xZ2xZ2 | 2 | 378 | 378 | 0 | 0 |
| Z2xZ2xZ2 | 3 | 63 | 63 | 0 | 0 |

Every sweep group has order at most 8, which is smaller than k*l = 9, so by pigeonhole **no** sweep instance can have distinct sums: all of them have some |P(δ)| >= 2 (observed distinct-sum instances: 0).  The sweep therefore probes exactly the coinciding-sums regime, complementary to the IBM codes above.

Result: 1440 SAT, 1 UNSAT, 0 TIMEOUT at depth 6 out of 1441 instances.  Depth Δ = 6 is refuted for every distinct-sum IBM code in table (ii), yet is achievable across almost the whole coinciding-sums sweep.

The exceptions:

| group | A | B | \|P(δ)\| histogram | max H_X H_Z^T entry | status | time s |
|---|---|---|---|---|---|---|
| Z6 | [[0], [2], [4]] | [[0], [2], [4]] | {"3": 3} | 6 | UNSAT | 513.838 |

`sw_Z6_A0-2-4_B0-2-4` takes A = B = {0, 2, 4}, the index-2 subgroup of Z6, so every nonzero |P(δ)| equals 3.  It is registered as instance `sw73` so the refutation can be re-run with a certificate (`solve.py --instance sw73 --depth 6 --proof`).

## (v) k5 at depth 10 — exhaustive case split on x₁

x₁ is the number of X-edges on the L side in layer 1.  Those edges form a matching between the N X-checks and the N L-qubits, so 0 ≤ x₁ ≤ N and the N+1 equality cases are exhaustive.  That bound is machine-checked rather than only argued: one extra job forces x₁ ≥ N+1 and must come back UNSAT.  *(This run fans the split out over a process pool, a deviation from section 9 noted in the README; each solver invocation is still single-threaded.)*

| x₁ | status | solve s | vars | clauses | proper (sim) |
|---|---|---|---|---|---|
| 0 | INTERRUPTED | 6141 |  |  | - |
| 1 | INTERRUPTED | 6141 |  |  | - |
| 2 | INTERRUPTED | 6141 |  |  | - |
| 3 | INTERRUPTED | 6141 |  |  | - |
| 4 | INTERRUPTED | 6141 |  |  | - |
| 5 | INTERRUPTED | 6141 |  |  | - |
| 6 | INTERRUPTED | 6141 |  |  | - |
| 7 | INTERRUPTED | 6141 |  |  | - |
| 8 | INTERRUPTED | 6141 |  |  | - |
| 9 | INTERRUPTED | 6141 |  |  | - |
| 10 | INTERRUPTED | 6141 |  |  | - |
| 11 | INTERRUPTED | 6141 |  |  | - |
| 12 | INTERRUPTED | 6141 |  |  | - |
| 13 | INTERRUPTED | 6141 |  |  | - |
| 14 | INTERRUPTED | 6141 |  |  | - |
| 15 | INTERRUPTED | 6141 |  |  | - |
| 16 | INTERRUPTED | 6141 |  |  | - |
| 17 | INTERRUPTED | 6141 |  |  | - |
| 18 | INTERRUPTED | 6141 |  |  | - |
| 19 | INTERRUPTED | 6141 |  |  | - |
| 20 | INTERRUPTED | 6141 |  |  | - |
| 21 | INTERRUPTED | 6141 |  |  | - |
| 22 | NOT_STARTED |  |  |  | - |
| 23 | NOT_STARTED |  |  |  | - |
| 24 | NOT_STARTED |  |  |  | - |
| 25 | NOT_STARTED |  |  |  | - |
| 26 | NOT_STARTED |  |  |  | - |

Exhaustiveness job `x₁ ≥ 27`: **UNSAT** (0.18 s) — confirms x₁ never exceeds N, so the cases above cover every schedule.

Totals: 22 INTERRUPTED, 5 NOT_STARTED out of 27 cases.

`INTERRUPTED` means the run was stopped by hand before its timeout, with the elapsed time it had actually reached; `NOT_STARTED` means the case was still queued.  Neither is a TIMEOUT and neither says anything about satisfiability — **k5 at depth 10 is unresolved.**  Re-run with `make o3split`.

**Verdict incomplete**: 27 of 27 cases did not return a satisfiability verdict, so depth 10 is not settled.

## Twisted schedules: theorem, proposition, and what was computed

**Theorem (proved).**  A twisted schedule requires $|M|$ even, where $M = \langle \alpha_s-\alpha_{s'},\ \beta_t-\beta_{t'}\rangle \le \mathbb{Z}_m$ is generated by all six label differences.

**Proposition (computed, $J = 3$).**  For a class-C1 instance, if some homomorphism $\varepsilon: G \to \mathbb{Z}_{2^j}$ with $j \le 3$ has $\varepsilon(d) \neq 0$ — equivalently $\mathrm{two\_height}(d) \le 2$ — then a depth-$\Delta$ schedule exists.  $J = 3$ because the exhaustive tables reach $m = 8 = 2^3$; the $m = 16$ table was not computed.  This is a statement about the instances and groups tabulated here, not about all groups.

**Empirical necessary condition.**  $\varepsilon(d) \neq 0$: over every enumerated key of the tables below, no eps-vector with $\varepsilon(d) = 0$ admits a schedule.  It is necessary but not sufficient.

| m | eps-vectors | admit a depth-6 schedule | provenance |
|---|---|---|---|
| 2 | 144 | 72 | exhaustive |
| 3 | 486 | 0 | exhaustive |
| 4 | 1,152 | 864 | exhaustive |
| 5 | 2,250 | 0 | exhaustive |
| 6 | 3,888 | 2412 | exhaustive |
| 7 | -- | -- | not computed |
| 8 | 9,216 | 8064 | exhaustive |
| 9 | -- | -- | not computed |
| 10 | -- | -- | not computed |
| 11 | -- | -- | not computed |
| 12 | -- | -- | not computed |
| 16 | -- | -- | not computed |

Exhaustive rows: $m = [2, 3, 4, 5, 6, 8]$.  The odd rows that were computed, $m = 3$ and $m = 5$, are **exhaustive zero** (0 of 486 and 0 of 2250), consistent with the theorem, since every subgroup of $\mathbb{Z}_m$ has odd order for odd $m$.  Rows marked *not computed* were cancelled and no claim is made about them.

*exhaustive*, *spot-check* and *capped* are three distinct words in this report.  A capped run is UNKNOWN and is never reported as UNSAT.

### Superseded empirical fit (SI)

An earlier fit of ours, "a template exists iff $\operatorname{ord}(\varepsilon(d))$ is even", is **false**: at $m = 6$ it fails on 468 of 3888 keys.  It was stated after checking only $m = 2, 3, 4$.  A related error: an apparent counterexample to the theorem itself dissolved once $M$ was computed as the subgroup generated by all six label differences rather than $\langle\varepsilon(d)\rangle$; with the correct $M$ the theorem has zero violations on every enumerated key.  Details in `data/criterion_refutation.json`.

The remaining gap is reported as counts, not as a rule: at $m = 6$, of the 2916 keys with $\varepsilon(d) \neq 0$ and $|M|$ even, **2412 admit and 504 do not**.

## Undetermined instances

Of the 598 class-C1 instances solved at depth 6 with a 600 s single-threaded limit, 118 hit the limit.  Of those, **8** are settled constructively: an eps-twisted invariant schedule exists, was expanded to all 2N*Delta edges and passed the F2 simulation check, which proves satisfiability without the solver.  The remaining **110** are recorded as UNDETERMINED.

| region | undetermined |
|---|---|
| ord(d) odd, Theorem-1 obstructed | 80 |
| ord(d) odd, not obstructed | 30 |

By group order: N=15: 1, N=17: 12, N=18: 4, N=19: 16, N=20: 4, N=21: 25, N=22: 6, N=23: 26, N=28: 3, N=30: 10, N=36: 3.

UNDETERMINED instances are excluded from every separation statistic and from every contingency table except `tables/tabS4_c1.tex`, where they appear in their own column.  **No theorem or proposition in this paper depends on them**: the certified results are the depth-6 refutations of section (ii), which are UNSAT with drat-trim-verified proofs, and the depth-7 witnesses, which are verified by F2 simulation.

### Consistency checks on the class-C1 set

| check | statement | outcome |
|---|---|---|
| C1 | every UNSAT not explained by Theorem 1 has ord(d) odd | **PASS** (62 of 193 UNSAT unexplained, all with ord(d) odd) |
| C2 | every SAT with ord(d) even admits a Z_(2^(v2(d)+1)) twisted schedule | **PASS** (265 instances, 0 exceptions) |
| C3 | every SAT with ord(d) odd has minimal period m* = N | **FAILS** (24 of 30 have a proper even period) |

C3 does not hold.  24 of the 30 satisfiable instances with $\operatorname{ord}(d)$ odd have a *proper* even period, at $m^* \in [6, 10, 12, 14]$ — for example `h4_Z12_C1_11` ($N=12$, $m^*=6$), `h4_Z12_C1_6` ($N=12$, $m^*=6$), `h2_Z18_C1_1` ($N=18$, $m^*=6$), `h4_Z18_C1_0` ($N=18$, $m^*=6$).  This is the same point as the theorem's scope: $\operatorname{ord}(d)$ odd does **not** preclude a twisted schedule; what the theorem forbids is $|M|$ odd, and $|M|$ is even for every one of these.  Each schedule was expanded and passed the F2 simulation check.

## Capped runs

Every solver call in the minimal-period scan carries a 60 s wall-clock cap. A capped call is recorded **UNKNOWN** for that (instance, m) and is never retried in the run and never counted as UNSAT.  190 individual calls hit the cap, producing 36 (instance, m) pairs with an UNKNOWN verdict.

By group order: N=18: 2, N=20: 5, N=22: 6, N=28: 3, N=30: 12, N=36: 8.  By modulus: m=2: 1, m=3: 1, m=4: 1, m=6: 1, m=9: 3, m=10: 9, m=11: 6, m=12: 1, m=14: 3, m=15: 8, m=18: 2.

| instance | N | m | cap (s) | solver | capped calls |
|---|---|---|---|---|---|
| h2_Z18_C1_2 | 18 | 9 | 60 | glucose42 | 4 |
| h4_Z18_C1_28 | 18 | 9 | 60 | glucose42 | 5 |
| h2_Z20_C1_0 | 20 | 10 | 60 | glucose42 | 3 |
| h2_Z20_C1_3 | 20 | 10 | 60 | glucose42 | 4 |
| h4_Z20_C1_11 | 20 | 10 | 60 | glucose42 | 4 |
| h4_Z20_C1_25 | 20 | 10 | 60 | glucose42 | 3 |
| h4_Z20_C1_8 | 20 | 10 | 60 | glucose42 | 4 |
| h4_Z22_C1_14 | 22 | 11 | 60 | glucose42 | 10 |
| h4_Z22_C1_17 | 22 | 11 | 60 | glucose42 | 10 |
| h4_Z22_C1_21 | 22 | 11 | 60 | glucose42 | 10 |
| h4_Z22_C1_28 | 22 | 11 | 60 | glucose42 | 10 |
| h4_Z22_C1_5 | 22 | 11 | 60 | glucose42 | 10 |
| h4_Z22_C1_6 | 22 | 11 | 60 | glucose42 | 10 |
| h4_Z28_C1_1 | 28 | 14 | 60 | glucose42 | 6 |
| h4_Z28_C1_22 | 28 | 14 | 60 | glucose42 | 6 |
| h4_Z28_C1_25 | 28 | 14 | 60 | glucose42 | 6 |
| h4_Z30_C1_13 | 30 | 10 | 60 | glucose42 | 4 |
| h4_Z30_C1_13 | 30 | 15 | 60 | glucose42 | 8 |
| h4_Z30_C1_17 | 30 | 15 | 60 | glucose42 | 8 |
| h4_Z30_C1_18 | 30 | 10 | 60 | glucose42 | 4 |
| h4_Z30_C1_18 | 30 | 15 | 60 | glucose42 | 8 |
| h4_Z30_C1_21 | 30 | 15 | 60 | glucose42 | 8 |
| h4_Z30_C1_23 | 30 | 15 | 60 | glucose42 | 8 |
| h4_Z30_C1_26 | 30 | 15 | 60 | glucose42 | 8 |
| h4_Z30_C1_27 | 30 | 15 | 60 | glucose42 | 8 |
| h4_Z30_C1_28 | 30 | 15 | 60 | glucose42 | 8 |
| h4_Z30_C1_29 | 30 | 10 | 60 | glucose42 | 4 |
| h4_Z30_C1_3 | 30 | 10 | 60 | glucose42 | 3 |
| h4_Z36_C1_23 | 36 | 2 | 60 | glucose42 | 0 |
| h4_Z36_C1_23 | 36 | 3 | 60 | glucose42 | 0 |
| h4_Z36_C1_23 | 36 | 4 | 60 | glucose42 | 0 |
| h4_Z36_C1_23 | 36 | 6 | 60 | glucose42 | 0 |
| h4_Z36_C1_23 | 36 | 9 | 60 | glucose42 | 0 |
| h4_Z36_C1_23 | 36 | 12 | 60 | glucose42 | 0 |
| h4_Z36_C1_23 | 36 | 18 | 60 | glucose42 | 0 |
| h4_Z36_C1_6 | 36 | 18 | 60 | glucose42 | 6 |

## Solvers used

| stage | solver | why |
|---|---|---|
| depth-Delta refutations, depth-7 search, sweep, H2, H4 step 1 | kissat 4.0.4 (external binary), proofs checked by drat-trim | DRAT proofs |
| independent re-decision of the depth-6 CNFs | cadical 3.0.1 | second solver |
| label-level twisted systems, uncapped | pysat cadical195 | default |
| label-level twisted systems, capped | pysat glucose42 | pysat's CaDiCaL has no limited-solve, so a wall-clock cap needs an interruptible backend |

Switching the capped path from cadical195 to glucose42 was checked for agreement first: **88 of 88** randomly drawn label-level systems at $m = 2, 4, 6$ gave the same verdict under both, with 0 disagreements.  glucose42 was also no slower on the hard case measured (1.82 s vs 3.03 s).

## Verification chain

What each result rests on, from the bottom up:

1. `code.check_structure()` asserts the Tanner graph, the degrees, `(H_X H_Z^T)[g, g+δ] = 2·|P(δ)|`, and that every corner lies in exactly one overlap pair.
2. **T2** checks the parity condition against the F2 circuit simulation per overlap pair on 1200 random valid layerings, and asserts the circuit cannot deviate from the ideal map outside the (z, y) block.
3. **T3** checks that brute-force enumeration of *all* valid layerings and SAT enumeration agree exactly — 4 instances, up to 331,776 layerings — so the CNF is neither over- nor under-constrained.
4. **T6** checks that layer reversal maps proper schedules to proper schedules, which is the sole justification for the one symmetry-breaking clause; without it the UNSAT results would not be sound.
5. **T5** exhibits a valid depth-Δ layering for every IBM code, so the depth-6 refutations are caused by properness and not by the scheduling constraints.
6. Each UNSAT is certified by a DRAT proof that `drat-trim` accepts, and re-decided by cadical; each SAT is decoded to a schedule that is re-verified by F2 simulation.
7. `certs/*.cnf` is byte-identical to a fresh `encode()`, tying each certificate to the published encoding.

Output of `make test`:

```
=== test_T1_structure ===
T1 structure: OK (bb72: 432 edges, all degrees 6, overlap entries in {0,2})

=== test_T2_encoding_vs_simulation ===
T2 oe21 D=3: 300 random layerings agree (parity == simulation); 0 of them proper
T2 oe12 D=3: 300 random layerings agree (parity == simulation); 0 of them proper
T2 coinc831: multiplicity histogram {1: 5, 2: 2}, max overlap entry 4
T2 coinc831 D=6: 300 random layerings agree; 0 of them proper
T2 coinc831 D=7: 300 random layerings agree; 0 of them proper

=== test_T3_exhaustive ===
T3 tiny_11 D=2: 8 valid layerings, 0 proper, SAT enumeration agrees (0)
T3 tiny_12 D=3: 72 valid layerings, 2 proper, SAT enumeration agrees (2)
T3 oe21 D=3: 65544 valid layerings, 2 proper, SAT enumeration agrees (2)
T3 oe12 D=3: 331776 valid layerings, 16 proper, SAT enumeration agrees (16)

=== test_T4_round_trip ===
T4 oe21 D=3: model -> schedule -> unit assumptions -> SAT, identical
T4 oe12 D=3: model -> schedule -> unit assumptions -> SAT, identical
T4 oe23 D=5: model -> schedule -> unit assumptions -> SAT, identical

=== test_T5_depth6_structurally_feasible ===
T5 bb72: a valid depth-6 layering exists (vertex constraints satisfiable); this one is improper
T5 bb90: a valid depth-6 layering exists (vertex constraints satisfiable); this one is improper
T5 bb108: a valid depth-6 layering exists (vertex constraints satisfiable); this one is improper
T5 bb144: a valid depth-6 layering exists (vertex constraints satisfiable); this one is improper
T5 bb288: a valid depth-6 layering exists (vertex constraints satisfiable); this one is improper
T5 bb360: a valid depth-6 layering exists (vertex constraints satisfiable); this one is improper
T5 bb756: a valid depth-6 layering exists (vertex constraints satisfiable); this one is improper

=== test_T6_layer_reversal_is_a_symmetry ===
T6 oe21 D=3: 1 schedules, all reversals still proper
T6 oe12 D=3: 16 schedules, all reversals still proper
T6 oe23 D=5: 40 schedules, all reversals still proper
T6 oe43 D=7: 40 schedules, all reversals still proper
T6 bb72 D=7: reversal of the invariant schedule is still proper
T6 bb144 D=7: reversal of the invariant schedule is still proper
T6 bb756 D=7: reversal of the invariant schedule is still proper
T6: layer reversal verified as a symmetry on 100 proper schedules

ALL TESTS PASSED
```

## Timings

- main solver runs: 17, total solve time 1114.0 s, total drat-trim verification 967.0 s, total proof size 2949.3 MB

- sweep: 1441 instances, total solve time 1590.7 s (8 workers)

- lemma checks: 417 solutions analysed


Figures: 4 main text and 7 supplementary built (3 more named but not built: figS7_pipeline.pdf, figS8_depth_scaling.pdf, figS9_locality.pdf), by `make figures` from data/, templates/ and schedules/ only.  315 plotted values are recorded in `figures/figure_values.csv` with the file and column each came from.  Layout checks: all pass.  See `figures/CHECK.md`.

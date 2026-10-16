# H4 / H5 / step 6 — state at 2026-09-08 02:41, paused on request

No experiment is running.  Nothing below is an estimate: every number is read from a
file in `data/` or `templates/`.

## Complete and on disk

| output | contents |
|---|---|
| `data/h2_sharpness.csv` | 656 rows (H2 + the H4 extension). Class C1: 287 SAT, 193 UNSAT, 118 TIMEOUT at the 600 s single-threaded limit |
| `data/h4_features.csv` | 598 class-C1 instances with the step-2 features |
| `data/h4_separation.json` | step 3: **no** single feature and **no** feature pair separates SAT from UNSAT exactly |
| `data/h4_twisted.csv` | step 4: 986 (instance, eps) searches at m = 2 |
| `templates/C1_m{2,3,4,5,6}.json` | exhaustive eps-templates, 7 920 keys total |
| `data/criterion_refutation.json` | what was falsified and what was not (see below) |
| `data/h4_extra_keys_m6.json` | the 468 m = 6 keys that admit with ord(eps(d)) odd |
| `data/snapshot_023627/` | copy of every data file and template as of the pause |

## Findings that are settled

* Theorem-1 obstruction: **0 SAT / 131 UNSAT**; ord(d) even: **262 SAT / 0 UNSAT**.
  The two criteria cover disjoint regions.  All 62 UNSAT instances that Theorem 1 does
  not explain have ord(d) **odd** (0 exceptions).
* Step 4: a Z2-twisted schedule exists for 194 instances, always with non-trivial eps,
  every one verified by F2 simulation.  **0 of 193 UNSAT** instances admit one, so it is
  a sound sufficient condition for SAT; 95 SAT instances admit none, so it is not
  necessary.
* **The even-order theorem holds** on every enumerated key of m = 2,3,4,5,6
  (7 920 keys, 0 violations of necessity), where
  `M = <alpha_s - alpha_s', beta_t - beta_t'> <= Z_m`.  It is necessary, **not**
  sufficient (|M| even but no schedule: 54 / 270 / 990 at m = 2 / 4 / 6).
* **An empirical fit of ours was false**: "template membership iff ord(eps(d)) even"
  fails on 468 of 3 888 keys at m = 6.  The surviving *sufficient* direction,
  ord(eps(d)) even => a template exists, holds 1944/1944 at m = 6.
* m = 6 reconciliation, per pattern (216 keys): "eps(d) != 0 and |M| even" = 162, of
  which **134 admit**; **28** have eps(d) != 0 and |M| even yet no schedule; **0**
  admits have eps(d) = 0.

## Not done

* **5a (per-instance Z_m study) produced no output.**  The first implementation buffered
  every result in the parent process and wrote the CSV only at the end, so when the run
  was paused all of it was lost.  `data/h4_twisted_zm.csv` does not exist.
* Step 6 (`twoblock/c1_final.py`) is written and imports cleanly but has never run: it
  reads `h4_twisted_zm.csv`.
* Templates m = 8, 10, 12 (exhaustive) and m = 7 (exhaustive, the independent test of
  the theorem) were not built.  m = 9, 11 spot checks were not run.
* `figures/`, `tables/` and `data/SUMMARY.md` still reflect the state **before** the H4
  extension; they were not regenerated.

## Why 5a stalled

It was not hung.  17 of 20 workers were at 100 % CPU on the tail instances (N = 32, 36),
where the searches are UNSAT proofs at m = 16 and m = 18.  Measured calibration on
N = 36, m = 18 (18 homomorphisms per instance):

| conflict budget | instance | ord(d) | found | none | UNKNOWN | seconds |
|---|---|---|---|---|---|---|
| 50 000 | h4_Z36_C1_0 | 9 | 1 | 4 | 13 | 12.4 |
| 50 000 | h4_Z36_C1_16 | 9 | 3 | 4 | 11 | 9.3 |
| 50 000 | h4_Z36_C1_1 | 18 | 0 | 4 | 14 | 10.3 |
| 50 000 | h4_Z36_C1_10 | 4 | 6 | 9 | 3 | 6.0 |
| 200 000 | h4_Z36_C1_0 | 9 | 4 | 4 | 10 | 50.3 |
| 200 000 | h4_Z36_C1_16 | 9 | 8 | 10 | 0 | 25.4 |

A budget of 50 000 leaves most m = 18 searches UNKNOWN; 200 000 resolves many more but
costs 25–50 s per instance at that m alone.  No budget was chosen.

## Fixes applied before stopping

* `run_zm_study` now appends each instance's rows and flushes as soon as that instance
  finishes, and skips (instance, m) pairs already in the CSV, so an interrupted run
  keeps its work and a re-run resumes.  Verified: 12-instance run wrote 24 rows, re-run
  reported "nothing to do".
* `solve_twisted_system` / `find_twisted_invariant_schedule_Zm` accept a **conflict
  budget** (not wall clock, so runs are reproducible) and return the sentinel `UNKNOWN`
  when it runs out.
* `run_zm_study(which=...)` covers even / odd / all divisors of N in one code path; the
  separate non-incremental `run_zm_odd_supplement` was removed so there is only one way
  to do this.

## To resume

```
make h5zm                 # 5a, resumable; add --which all --budget <n>
make h6                   # step 6, needs h4_twisted_zm.csv
make h5templates H5_MS=7  # the independent test of the theorem (predicts 0/6174)
make figures && make report
```

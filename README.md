# A parity obstruction to degree-optimal syndrome extraction in bivariate bicycle codes

Code and data for the paper. Version **3.0.0** — npj Quantum Information
revision, 2026-10-15.

This repository rebuilds every table, every figure and the manuscript PDF from
the data files, and re-checks every number in the text against the file it came
from. The 10.2 GB of DRAT proofs are on Zenodo (see
[Verifying the proofs](#verifying-the-proofs)); everything else is here.

## What the paper is about

A two-block (bivariate bicycle) CSS code over an abelian group `G` has checks
`H_X = [A | B]` and `H_Z = [Bᵀ | Aᵀ]`. Measuring all its stabilisers takes a
schedule of CNOT layers, and the question is how few layers suffice when the
X and Z rounds are *interleaved*. The degree bound says Δ = w_A + w_B layers
might be enough; the published cycle for the gross code uses seven. The paper
settles which is right, and when:

* **Distinct sums ⇒ depth 7 is optimal.** If the `w_A·w_B` sums `a_s + b_t` are
  pairwise distinct, no proper depth-6 schedule exists. The obstruction is a
  parity argument: support symmetry forces `a + b = Δ + 1`, rigidity forces one
  X and one Z per layer pair on every qubit, and the resulting count
  `F_L + F_R = (Δ/2)²` is odd while properness needs `F_L = F_R`.
* **One repeated sum can reopen depth 6.** With a single coincidence the
  overlap pair gains four corners instead of two, and four corners can cancel
  (`1 + 0 + 0 + 1 ≡ 0`). A twisted schedule built from an ε-template on `Z_q`
  achieves depth six whenever the collision element `𝖽` has even order and
  2-height at most 8.
* **A componentwise mod-4 obstruction** rules out a further family, with two
  corollaries: a two-block form, and one for regular CSS codes that also
  excludes hypergraph products such as `[[98,18]]` and `[[450,32]]`.
* **Eighteen DRAT proofs** certify the refutations no theorem covers.

## Reproducing

```bash
conda env create -f environment.yml && conda activate stab-qram   # or: pip install -r requirements.txt
bash setup_solvers.sh        # builds kissat, cadical and drat-trim from source
bash run.sh                  # rebuild everything and re-check it
make test                    # the lemma and identity test suite, ~3 min
```

`run.sh` does **not** re-run the SAT solver — those runs take days, and their
outputs are the CSVs in `data/`. What it does, in nine stages, is rebuild every
derived artefact from those files and re-check it:

1. recompute the named derivations (`figures/derived_values.csv`);
2. rebuild the revision's result tables (`data/cor3_hgp.csv`,
   `data/pareto_front.csv`, `data/template_force.csv`, …);
3. regenerate the 12 `.tex` tables;
4. regenerate the nine figure PDFs and PNGs (600 dpi) and run the layout
   checker T1–T9 on each — all nine must pass;
5. run the layout checker's own self-tests;
6. check that the retired notation (`d ∈ 8G`, `k = ℓ = 3`, `Table S7`) is gone
   from the figure **text layers**, and that the new notation is present;
7. build `main.tex` with `latexmk` and fail if any figure was read from
   anywhere but `figures/`;
8. run the manuscript acceptance checks (abstract ≤ 150 words, no `TODO`, no
   retired notation, no overfull box above 10 pt, no undefined reference);
9. audit every number the manuscript quotes against the file it came from.

Optional, slower stages:

```bash
bash run.sh --revision        # + the revision's verification scripts   (~5 min)
bash run.sh --revision-slow   # + key enumeration at q = 32 and the
                              #   forced-involution runs q = 64…512    (~35 min)
bash run.sh --search          # + the code search behind Table 2 and
                              #   Tables S14–S16                       (hours)
```

`--search` re-runs `twoblock/search2.py` for every group and **compares the
result with the recorded `revision/scripts/res_*.json`**. The sampling seeds are
fixed, so a difference means the seed handling changed; it is reported as a
failure rather than silently adopted.

## What is where

| path | contents |
|---|---|
| `twoblock/` | 67 modules: the SAT encoder, the F₂ simulator, the mod-4 and parity lemmas, the König colouring, the template enumerator, the equivalence census, the code search, and the revision's verification scripts |
| `data/` | 60 CSV/JSON files — every instance, outcome, certificate record and derived table |
| `figures/src/` | the nine figure builders, the layout checker T1–T9, the number auditor |
| `figures/` | the nine figure PDFs/PNGs, layered SVGs, the manifest, `CHECK.md` |
| `templates/`, `schedules/` | enumerated ε-templates and verified schedules |
| `tables/` | the 12 generated `.tex` tables |
| `tests/` | the lemma, pullback and identity tests |
| `certs/`, `certs_nosym/` | the CNFs (xz-compressed) and `PROOFS.sha256` |
| `revision/scripts/` | the recorded run artefacts: `res_*.json`, solver logs, `pareto_table.txt` |
| `main.tex` | the manuscript (revtex4-2, embedded bibliography) |

Every number in a figure is read from a file: `figures/figure_values.csv`
records all of them with the file and column each came from, and
`figures/CHECK.md` re-derives the headline ones straight from the CSVs.

## Verifying the proofs

The 27 DRAT proofs total 10.2 GB; the largest is 2.6 GB, well over GitHub's
100 MB per-file limit, so they are in the Zenodo archive rather than here.

```bash
# with the Zenodo archive unpacked over certs/ and certs_nosym/
bash verify_proofs.sh

# without it: each refutation is re-run from the shipped CNF with kissat and
# the fresh proof is checked instead
bash verify_proofs.sh
```

`certs/PROOFS.sha256` and `certs_nosym/PROOFS.sha256` give the SHA-256 and the
byte size of every recorded proof, so a downloaded proof can be matched against
the one the paper used. When a proof is re-solved rather than downloaded, the
script reports whether the fresh proof is byte-identical to the recorded one; a
difference is *not* a failure — two different proofs of the same CNF are both
valid certificates. Only "drat-trim did not say VERIFIED" is a failure.

## Reference figures

`figures/ref/` holds only provenance. The five published figures studied while
designing ours are **not** redistributed: one is CC BY-NC-ND 4.0 and one carries
the arXiv non-exclusive licence with no reuse right. `figures/ref/SOURCES.md`
gives the DOI, figure number, licence and exact crop for each, so they can be
fetched from the publisher. Nothing in `figures/` is traced or adapted from them.

## Hardware and versions

All runs were single-threaded on one workstation: Intel Core Ultra 9 275HX,
24 logical cores, 15.6 GiB, Linux/WSL2. Solvers: kissat 4.0.4 (git `8af8e56`),
CaDiCaL 3.0.1 (git `c607304`), drat-trim (git `2e3b2dc`), built by
`setup_solvers.sh`. Python 3.11; see `environment.yml` for the pinned stack.

Figures are typeset in TeX Gyre Heros, shipped in `figures/fonts/`. They are
required: with a fallback font every text metric changes and the layout checker
fails.

## Licence

Code: MIT (`LICENSE-MIT`). Data, figures and the manuscript text:
CC BY 4.0 (`LICENSE-CC-BY-4.0`).

## Citing

See `CITATION.cff`. This repository is
<https://github.com/Guangyi-Leo/A-parity-obstruction-to-degree-optimal-syndrome-extraction-in-bivariate-bicycle-codes>;
it was renamed from `Guangyi-Leo/Stab-QRAM`, and the package for that earlier
paper (arXiv:2509.26494) stays reachable at tag `v1.0`. The Zenodo DOI is a placeholder until the record is
deposited; it appears in `CITATION.cff` and in the manuscript's Data
availability statement, and both must be updated together.

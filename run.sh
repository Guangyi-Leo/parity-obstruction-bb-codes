#!/usr/bin/env bash
# Regenerate every table and every figure from data/, then rebuild the PDF.
#
# What this does NOT do by default is re-run the solver: the depth-6 sweep and
# the DRAT certification take days, and their outputs are the CSVs in data/ and
# the proofs in certs/.  Everything derived from them -- the .tex tables, the
# nine figure PDFs, the manuscript -- is rebuilt here, and every number in the
# text is re-checked against a file.
#
#   bash run.sh                 rebuild the derived artefacts (minutes)
#   bash run.sh --revision      + re-run the revision's fast verification scripts
#   bash run.sh --revision-slow + the ~10-20 min template runs (keys16 q=32,
#                                 forced involutions q = 64..512)
#   bash run.sh --search        + the code search behind Tables 2 and S14-S16
#                                 (hours; exhaustive at N <= 36, sampled above)
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-./.venv/bin/python}"
[ -x "$PY" ] || PY="python3"
export PYTHONPATH="$PWD:$PWD/figures/src:$PWD/figures:${PYTHONPATH:-}"

REVISION=0; REVSLOW=0; SEARCH=0
for a in "$@"; do
    case "$a" in
        --revision)      REVISION=1 ;;
        --revision-slow) REVISION=1; REVSLOW=1 ;;
        --search)        REVISION=1; REVSLOW=1; SEARCH=1 ;;
        *) echo "unknown option: $a" >&2; exit 2 ;;
    esac
done

say() { printf '\n=== %s ===\n' "$1"; }

# ---------------------------------------------------------------------------
say "1/9  derived values"
$PY figures/src/derived_values.py | tail -3

# ---------------------------------------------------------------------------
say "2/9  revision result tables"
# Corollary 3 is recomputed; the Pareto front and the q >= 32 template runs are
# read from the recorded artefacts unless --search / --revision-slow re-run them.
$PY -m twoblock.revision_tables

if [ "$REVISION" = 1 ]; then
    say "2b/9  revision verification scripts"
    if   [ "$SEARCH"  = 1 ]; then $PY -m twoblock.revision_runs --search
    elif [ "$REVSLOW" = 1 ]; then $PY -m twoblock.revision_runs --slow
    else                          $PY -m twoblock.revision_runs
    fi
fi

if [ "$SEARCH" = 1 ]; then
    say "2c/9  code search behind Table 2 and Tables S14-S16"
    # exhaustive at N <= 36, 4e5 sampled pairs per group above; the seeds are
    # fixed, so the result must match revision/scripts/res_*.json exactly
    $PY -m twoblock.code_search --exhaustive 18,24,27,36 --sampled 45,54,72 \
        --samples 400000 --compare revision/scripts
fi

# ---------------------------------------------------------------------------
say "3/9  tables"
$PY -m twoblock.make_tables

# ---------------------------------------------------------------------------
say "4/9  figures"
$PY - <<'PYEOF'
import os, sys
import matplotlib
matplotlib.use("Agg")
import figstyle as S
S.use_style()
import check_layout as CL
import round7 as R7, si_figs as SI, manuscript_figs as M

FIGS = [
    ("fig1_degree_bound_to_cross_term", lambda: R7.build_fig1("fig1")),
    ("fig2_why_six_layers_fail",        lambda: R7.build_fig2("fig2")),
    ("fig3_where_depth6_is_attainable", lambda: R7.build_fig3("fig3")),
    ("figS1_proof_map",                 M.fig2),
    ("figS2_sweep_by_group",            SI.fig_sweep_by_group),
    ("figS3_templates_by_q",            SI.fig_templates_by_q),
    ("figS4_periods",                   SI.fig_periods),
    ("figS5_theorem1_profile",          SI.fig_theorem1_profile),
    ("figS6_certificates",              M.fig5),
]
bad = []
for name, fn in FIGS:
    r = fn()
    fig = r[0] if isinstance(r, tuple) else r
    rep = CL.check(fig, name)
    fails = [c["id"] for c in rep["checks"] if not c["pass_"]]
    S.save_all(fig, os.path.join("figures", name), dpi_png=600)
    print(f"  {name:34} {rep['width_mm']:3.0f}x{rep['height_mm']:<4.0f} "
          f"{'PASS' if not fails else 'FAIL ' + ','.join(fails)}")
    if fails:
        bad.append((name, fails))
if bad:
    sys.exit(f"layout checks failed: {bad}")
print("  all nine figures pass T1-T9")
PYEOF

# ---------------------------------------------------------------------------
say "5/9  layout-checker self-tests"
$PY - <<'PYEOF'
import sys
import test_check_layout as T
bad = []
for n in sorted(d for d in dir(T) if d.startswith("probe_")):
    r = getattr(T, n)()
    ok = r[0] if isinstance(r, tuple) else r
    print(f"  {n}: {'PASS' if ok else 'FAIL'}")
    if not ok:
        bad.append(n)
if bad:
    sys.exit(f"checker probes failed: {bad}")
PYEOF

# ---------------------------------------------------------------------------
say "6/9  retired notation is gone from the figure text layers"
$PY figures/src/check_figure_text.py

# ---------------------------------------------------------------------------
say "7/9  the manuscript"
./build_tex.sh

# ---------------------------------------------------------------------------
say "8/9  manuscript acceptance checks"
$PY -m twoblock.check_manuscript

# ---------------------------------------------------------------------------
say "9/9  every number in the manuscript has a source"
$PY figures/src/check_text_numbers.py --expect "$($PY - <<'PYEOF'
import csv
print(",".join(r["number"] for r in csv.DictReader(open("figures/text_anchors.csv"))))
PYEOF
)" | tail -4

printf '\nrun.sh: OK\n'

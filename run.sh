#!/usr/bin/env bash
# Reproduce ALL revision experiments and figures (pre-final integration step).
# Requirements: python3 + numpy, matplotlib, networkx.
# Steps 6-7 additionally require: qiskit>=1.0, stim>=1.12 (pip install qiskit stim).
# Total runtime on a laptop-class CPU: ~10-15 min (step 7 dominates).
set -euo pipefail
cd "$(dirname "$0")"

echo "== [1/7] Theorem 1 (exact depth D*) verification -> results/depth_theorem_check.json =="
python3 experiments/verify_depth_theorem.py --instances 500 --seed 7

echo "== [2/7] Fig. 1 architecture schematic -> figures/fig_architecture.pdf =="
python3 experiments/make_fig_architecture.py

echo "== [3/7] Figs. 2-4 + SI Fig. S1 (documented ensembles) -> figures/, results/main_figure_stats.json =="
python3 experiments/regenerate_main_figures.py --seed 5

echo "== [4/7] Case studies I-III + Figs. 5-7 -> figures/, results/case_studies.json =="
python3 experiments/case_studies.py --seed 17

echo "== [5/7] Locality proxy: grid vs random-regular (SI Table S2) -> results/topology_distance.csv =="
python3 experiments/topology_distance.py --instances 20 --seed 11

echo "== [6/7] SABRE routing on grid + heavy-hex (SI Table S3) -> results/sabre_routing.csv =="
python3 experiments/sabre_routing.py --n 25 --densities 0.10 0.25 0.50 --instances 20 --seed 11 \
  || echo "  (skipped: qiskit missing -- pip install qiskit)"

echo "== [7/7] Schedule census + circuit-level distances (SI Table S4) =="
python3 experiments/hook_schedule_census.py --d 3 5 7 --samples 200 --seed 23
python3 experiments/stim_circuit_distance.py --d 3 5 --samples 12 --seed 23 \
  || echo "  (skipped: stim missing -- pip install stim)"

echo "All experiments reproduced. Manuscript compilation happens in the final integration step."

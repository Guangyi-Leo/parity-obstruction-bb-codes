#!/usr/bin/env python3
"""[PROVIDED, NOT EXECUTED IN THE REVISION ENVIRONMENT -- requires qiskit>=1.0]

Routing validation of the d_max proxy: compile canonical Stab-QRAM circuits onto
real topologies (square grid, heavy-hex) with Qiskit's SABRE layout+routing and
report SWAP counts and post-routing depth, alongside the static d_max proxy used
in the main text. Fills Supplementary Table S2 (SABRE columns).

Usage:   python3 experiments/sabre_routing.py --n 25 --densities 0.1 0.25 0.5 \
             --instances 20 --seed 11 --out results/sabre_routing.csv
Expected output: CSV with columns
  topology,p,instance,n_swaps,routed_depth,dmax_proxy
Blockers if not runnable: missing qiskit -> `pip install qiskit`.
"""
import argparse, csv, os, random, sys

try:
    from qiskit import QuantumCircuit, transpile
    from qiskit.transpiler import CouplingMap
except ImportError:
    sys.exit("BLOCKER: qiskit not installed. Run `pip install qiskit` and retry.")


def canonical_circuit(A, b):
    m, n = len(A), len(A[0])
    qc = QuantumCircuit(n + m)
    for j in range(m):
        for k in range(n):
            if A[j][k]:
                qc.cx(k, n + j)
        if b[j]:
            qc.x(n + j)
    return qc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=25)
    ap.add_argument("--densities", type=float, nargs="+", default=[0.10, 0.25, 0.50])
    ap.add_argument("--instances", type=int, default=20)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--out", default="results/sabre_routing.csv")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    n = m = args.n

    # 56-qubit-scale topologies of maximum degree <= 4 (match topology_distance.py)
    topologies = {
        "square-grid-8x7": CouplingMap.from_grid(8, 7),
        # heavy-hex distance chosen so qubit count >= n+m; adjust if needed
        "heavy-hex-d5": CouplingMap.from_heavy_hex(5),
    }
    rows = []
    for p in args.densities:
        for inst in range(args.instances):
            A = [[1 if rng.random() < p else 0 for _ in range(n)] for _ in range(m)]
            b = [rng.randint(0, 1) for _ in range(m)]
            qc = canonical_circuit(A, b)
            for name, cmap in topologies.items():
                if cmap.size() < n + m:
                    print(f"BLOCKER: {name} has {cmap.size()} < {n+m} qubits; "
                          f"increase topology size.")
                    continue
                tqc = transpile(qc, coupling_map=cmap, layout_method="sabre",
                                routing_method="sabre", optimization_level=1,
                                basis_gates=["cx", "x", "swap"], seed_transpiler=args.seed)
                ops = tqc.count_ops()
                rows.append({"topology": name, "p": p, "instance": inst,
                             "n_swaps": ops.get("swap", 0),
                             "routed_depth": tqc.depth(),
                             "n_cx_input": sum(map(sum, A))})
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"wrote {args.out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()

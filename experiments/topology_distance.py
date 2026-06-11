#!/usr/bin/env python3
"""Locality proxy of Stab-QRAM interaction graphs on structured vs random hardware.

For random Bernoulli(p) specifications A (n=m=25, i.e. 50 logical qubits), this
script maps the bipartite interaction graph onto two 56-node hardware graphs of
maximum degree 4 -- (i) a random 4-regular graph and (ii) an 8x7 square grid --
using the degree-prioritized greedy placement heuristic of the main text, and
reports the mean and maximum physical shortest-path distance between the endpoints
of logical CNOTs. Purpose: quantify how much the random-regular ("expander-like")
connectivity model understates distances relative to planar lattices of equal
degree (Supplementary Section S4, Table S2).

Output: results/topology_distance.csv (+ stdout summary)
Usage:  python3 experiments/topology_distance.py --instances 20 --seed 11
"""
import argparse, csv, os, statistics
import networkx as nx
import random


def greedy_place(logical_edges, logical_nodes, H, spl):
    """Degree-prioritized greedy placement.
    Sort logical qubits by degree (desc); place each at the free physical node
    minimizing the sum of distances to its already-placed logical neighbours
    (first node goes to a graph center)."""
    deg = {v: 0 for v in logical_nodes}
    adj = {v: [] for v in logical_nodes}
    for u, v in logical_edges:
        deg[u] += 1; deg[v] += 1
        adj[u].append(v); adj[v].append(u)
    order = sorted(logical_nodes, key=lambda v: -deg[v])
    centers = nx.center(H)
    free = set(H.nodes())
    place = {}
    for v in order:
        placed_nb = [place[u] for u in adj[v] if u in place]
        if not placed_nb:
            cand = min(free, key=lambda x: (min(spl[x][c] for c in centers), x))
        else:
            cand = min(free, key=lambda x: (sum(spl[x][p] for p in placed_nb), x))
        place[v] = cand
        free.discard(cand)
    return place


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=25)
    ap.add_argument("--instances", type=int, default=20)
    ap.add_argument("--densities", type=float, nargs="+", default=[0.10, 0.25, 0.50])
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--out", default="results/topology_distance.csv")
    args = ap.parse_args()
    n = m = args.n
    rng = random.Random(args.seed)

    # hardware graphs: 56 physical qubits each, max degree 4
    Hreg = nx.random_regular_graph(4, 56, seed=args.seed)
    while not nx.is_connected(Hreg):
        Hreg = nx.random_regular_graph(4, 56, seed=rng.randint(0, 10**6))
    Hgrid = nx.convert_node_labels_to_integers(nx.grid_2d_graph(8, 7))
    hw = {"random-4-regular": Hreg, "square-grid-8x7": Hgrid}
    spl = {name: dict(nx.all_pairs_shortest_path_length(G)) for name, G in hw.items()}

    rows = []
    for p in args.densities:
        per = {name: {"dbar": [], "dmax": []} for name in hw}
        for inst in range(args.instances):
            A = [[1 if rng.random() < p else 0 for _ in range(n)] for _ in range(m)]
            ledges = [(("a", k), ("d", j)) for j in range(m) for k in range(n) if A[j][k]]
            if not ledges:
                continue
            lnodes = [("a", k) for k in range(n)] + [("d", j) for j in range(m)]
            for name, G in hw.items():
                pl = greedy_place(ledges, lnodes, G, spl[name])
                dists = [spl[name][pl[u]][pl[v]] for u, v in ledges]
                per[name]["dbar"].append(statistics.mean(dists))
                per[name]["dmax"].append(max(dists))
        for name in hw:
            rows.append({
                "hardware": name, "p": p, "instances": len(per[name]["dbar"]),
                "mean_dbar": round(statistics.mean(per[name]["dbar"]), 2),
                "sd_dbar": round(statistics.stdev(per[name]["dbar"]), 2),
                "mean_dmax": round(statistics.mean(per[name]["dmax"]), 2),
                "sd_dmax": round(statistics.stdev(per[name]["dmax"]), 2)})

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Numerical verification of the exact scheduled-depth theorem (Theorem 1).

For random affine specifications (A, b) over F_2 this script checks that
  (i)  the pendant-edge Koenig construction yields a PROPER edge coloring of the
       augmented bipartite graph using exactly
       D* = max( max_k colweight_k , max_j (rowweight_j + b_j) ) colors;
  (ii) the resulting gate schedule is valid (each layer acts on disjoint qubits);
  (iii) for small instances, an EXHAUSTIVE search confirms that no schedule of the
       same gate multiset uses fewer than D* layers (exact optimality).

Outputs: results/depth_theorem_check.json
Usage:   python3 experiments/verify_depth_theorem.py --instances 500 --seed 7
"""
import argparse, itertools, json, random, os


def dstar(A, b):
    m, n = len(A), len(A[0])
    col = [sum(A[j][k] for j in range(m)) for k in range(n)]
    row = [sum(A[j]) for j in range(m)]
    vals = col + [row[j] + b[j] for j in range(m)]
    return max(vals) if vals else 0


def gate_list(A, b):
    """Canonical gate multiset: one CNOT per nonzero A_jk, one X per nonzero b_j."""
    g = []
    for j, rowj in enumerate(A):
        for k, a in enumerate(rowj):
            if a:
                g.append(("cx", k, j))
    for j, bj in enumerate(b):
        if bj:
            g.append(("x", None, j))
    return g


def gate_qubits(g):
    t, k, j = g
    return frozenset({("a", k), ("d", j)}) if t == "cx" else frozenset({("d", j)})


def koenig_schedule(A, b):
    """Color the augmented bipartite graph (pendant edge per b_j=1) with D* colors
    via exact backtracking (Koenig's theorem guarantees feasibility)."""
    m, n = len(A), len(A[0])
    edges = []
    for j in range(m):
        for k in range(n):
            if A[j][k]:
                edges.append((("a", k), ("d", j), ("cx", k, j)))
        if b[j]:
            edges.append((("u", j), ("d", j), ("x", None, j)))
    D = dstar(A, b)
    # order edges by max endpoint degree (helps backtracking)
    deg = {}
    for u, v, _ in edges:
        deg[u] = deg.get(u, 0) + 1
        deg[v] = deg.get(v, 0) + 1
    edges.sort(key=lambda e: -(max(deg[e[0]], deg[e[1]])))
    used = {}  # vertex -> set of colors
    color = [None] * len(edges)

    def bt(i):
        if i == len(edges):
            return True
        u, v, _ = edges[i]
        for c in range(D):
            if c not in used.get(u, set()) and c not in used.get(v, set()):
                used.setdefault(u, set()).add(c)
                used.setdefault(v, set()).add(c)
                color[i] = c
                if bt(i + 1):
                    return True
                used[u].discard(c)
                used[v].discard(c)
                color[i] = None
        return False

    ok = bt(0)
    assert ok, "Koenig coloring failed -- this contradicts the theorem"
    layers = [[] for _ in range(D)]
    for (u, v, g), c in zip(edges, color):
        layers[c].append(g)
    return layers, D


def schedule_is_valid(layers):
    for L in layers:
        occ = set()
        for g in L:
            q = gate_qubits(g)
            if occ & q:
                return False
            occ |= q
    return True


def min_layers_exhaustive(gates, upper):
    """Exact minimum number of disjoint layers, by backtracking partition search."""
    gates = sorted(gates, key=lambda g: -len(gate_qubits(g)))

    def feasible(L):
        layers = [set() for _ in range(L)]

        def bt(i):
            if i == len(gates):
                return True
            q = gate_qubits(gates[i])
            tried = set()
            for l in range(L):
                key = frozenset(layers[l])
                if key in tried or (layers[l] & q):
                    continue
                tried.add(key)
                layers[l] |= q
                if bt(i + 1):
                    return True
                layers[l] -= q
            return False

        return bt(0)

    for L in range(1, upper + 1):
        if feasible(L):
            return L
    return upper


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", type=int, default=500)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--exhaustive-max-gates", type=int, default=10)
    ap.add_argument("--out", default="results/depth_theorem_check.json")
    args = ap.parse_args()
    rng = random.Random(args.seed)

    stats = {"instances": 0, "koenig_valid": 0, "koenig_uses_Dstar": 0,
             "exhaustive_checked": 0, "exhaustive_matches_Dstar": 0}
    for _ in range(args.instances):
        n, m = rng.randint(1, 4), rng.randint(1, 4)
        p = rng.uniform(0.2, 0.9)
        A = [[1 if rng.random() < p else 0 for _ in range(n)] for _ in range(m)]
        b = [rng.randint(0, 1) for _ in range(m)]
        gs = gate_list(A, b)
        if not gs:
            continue
        D = dstar(A, b)
        layers, used = koenig_schedule(A, b)
        stats["instances"] += 1
        stats["koenig_valid"] += int(schedule_is_valid(layers))
        stats["koenig_uses_Dstar"] += int(used == D and sum(len(L) for L in layers) == len(gs))
        if len(gs) <= args.exhaustive_max_gates:
            stats["exhaustive_checked"] += 1
            stats["exhaustive_matches_Dstar"] += int(min_layers_exhaustive(gs, D) == D)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(stats, f, indent=2)
    print(json.dumps(stats, indent=2))
    ok = (stats["koenig_valid"] == stats["instances"] ==
          stats["koenig_uses_Dstar"]) and (
          stats["exhaustive_checked"] == stats["exhaustive_matches_Dstar"])
    print("ALL CHECKS PASSED" if ok else "CHECK FAILED")


if __name__ == "__main__":
    main()

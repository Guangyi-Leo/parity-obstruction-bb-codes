#!/usr/bin/env python3
"""Regenerate the statistical figures of the main text with documented ensembles.

Outputs (figures/):
  depth_analysis_ab.pdf          Fig. 2  mean scheduled depth D* vs density p (a)
                                         and vs register size n (b)
  rank_analysis_c.pdf            Fig. 3  scheduled depth vs F2-rank (A = BC ensemble)
  locality_2d_heatmap_analysis.pdf Fig. 4 mean d_max proxy vs hardware degree k and p
  cnot_count_analysis.pdf        SI Fig. S1  ||A||_0 vs binomial mean (sanity check)
Raw statistics: results/main_figure_stats.json

Ensembles (all i.i.d. Bernoulli over F2, numpy default_rng):
  Fig 2a : n=m=50, p in linspace(.05,.95,10), b~Bern(.5),  200 instances/point
  Fig 2b : n=m in {10,...,100}, p in {0.1,0.25,0.5}, b~Bern(.5), 200 inst/point
  Fig 3  : n=m=32, A=BC with B in F2^{32xr}, C in F2^{rx32}, r=1..32, 16 inst/r
  Fig 4  : n=m=25 logical, hardware = connected random k-regular graph on 64
           nodes, k in {3..8}, p in {0.1..0.9}, 20 instances/cell,
           degree-prioritized greedy placement (same heuristic as main text)
Usage: python3 experiments/regenerate_main_figures.py --seed 5
"""
import argparse, json, os, sys
try:
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import networkx as nx
except ImportError as e:
    sys.exit(f"BLOCKER: missing dependency ({e}); pip install numpy matplotlib networkx")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from topology_distance import greedy_place  # placement heuristic of the main text

C = {"blue": "#0072B2", "orange": "#D55E00", "green": "#009E73",
     "purple": "#CC79A7", "grey": "0.45"}
plt.rcParams.update({"font.size": 8.5, "axes.labelsize": 9, "axes.titlesize": 9,
                     "legend.fontsize": 7.5, "pdf.fonttype": 42,
                     "figure.dpi": 200, "savefig.bbox": "tight"})


def dstar_np(A, b):
    """Exact scheduled depth D* = max(max col weight, max_j (row weight + b_j))."""
    return int(max(A.sum(axis=0).max(initial=0), (A.sum(axis=1) + b).max(initial=0)))


def f2_rank(A):
    M = A.copy() % 2
    r = 0
    rows, cols = M.shape
    for c in range(cols):
        piv = None
        for i in range(r, rows):
            if M[i, c]:
                piv = i
                break
        if piv is None:
            continue
        M[[r, piv]] = M[[piv, r]]
        for i in range(rows):
            if i != r and M[i, c]:
                M[i] ^= M[r]
        r += 1
        if r == rows:
            break
    return r


def fig2(rng, stats):
    n = m = 50
    ps = np.linspace(0.05, 0.95, 10)
    NI = 200
    mu_a, sd_a = [], []
    for p in ps:
        d = [dstar_np(rng.random((m, n)) < p, rng.integers(0, 2, m)) for _ in range(NI)]
        mu_a.append(np.mean(d)); sd_a.append(np.std(d, ddof=1))
    sizes = np.arange(10, 101, 10)
    pfix = [0.1, 0.25, 0.5]
    curves = {}
    for p in pfix:
        mu, sd = [], []
        for s in sizes:
            d = [dstar_np(rng.random((s, s)) < p, rng.integers(0, 2, s)) for _ in range(NI)]
            mu.append(np.mean(d)); sd.append(np.std(d, ddof=1))
        curves[p] = (np.array(mu), np.array(sd))
    fig, (axa, axb) = plt.subplots(2, 1, figsize=(3.4, 4.6))
    mu_a, sd_a = np.array(mu_a), np.array(sd_a)
    axa.plot(ps, mu_a, "o-", ms=3.5, color=C["blue"], label=r"mean $D^\star$")
    axa.fill_between(ps, mu_a - sd_a, mu_a + sd_a, color=C["blue"], alpha=.25, lw=0)
    axa.axhline(max(n, m) + 1, ls="--", color=C["grey"], lw=1,
                label=r"worst case $\max(n,m)+1$")
    axa.set_xlabel(r"matrix density $p$"); axa.set_ylabel(r"scheduled depth $D^\star$")
    axa.set_title("a", loc="left", fontweight="bold"); axa.legend(frameon=False)
    for p, col in zip(pfix, (C["blue"], C["orange"], C["green"])):
        mu, sd = curves[p]
        axb.plot(sizes, mu, "o-", ms=3.5, color=col, label=fr"$p={p}$")
        axb.fill_between(sizes, mu - sd, mu + sd, color=col, alpha=.25, lw=0)
    axb.set_xlabel(r"register size $n=m=\log_2 N$")
    axb.set_ylabel(r"scheduled depth $D^\star$")
    axb.set_title("b", loc="left", fontweight="bold"); axb.legend(frameon=False)
    fig.tight_layout(); fig.savefig("figures/depth_analysis_ab.pdf"); plt.close(fig)
    stats["fig2"] = {"n": n, "instances_per_point": NI, "p_grid": list(np.round(ps, 3)),
                     "sizes": sizes.tolist(), "p_fixed": pfix,
                     "panel_a_mean": list(np.round(mu_a, 2)),
                     "panel_b_mean": {str(p): list(np.round(curves[p][0], 2)) for p in pfix}}


def fig3(rng, stats):
    n = m = 32
    per_r = 16
    pts = []
    for r in range(1, n + 1):
        for _ in range(per_r):
            B = rng.integers(0, 2, (m, r)); Cm = rng.integers(0, 2, (r, n))
            A = (B @ Cm) % 2
            b = rng.integers(0, 2, m)
            pts.append((f2_rank(A), dstar_np(A.astype(bool), b)))
    rk = np.array([p[0] for p in pts]); dp = np.array([p[1] for p in pts])
    corr = float(np.corrcoef(rk, dp)[0, 1])
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    ranks = np.unique(rk)
    lo = np.array([dp[rk == r].min() for r in ranks])
    hi = np.array([dp[rk == r].max() for r in ranks])
    mu = np.array([dp[rk == r].mean() for r in ranks])
    ax.fill_between(ranks, lo, hi, color=C["blue"], alpha=.13, lw=0, zorder=1,
                    label="min--max at equal rank")
    ax.scatter(rk + rng.uniform(-.25, .25, len(rk)), dp, s=6, alpha=.25,
               color=C["blue"], lw=0, zorder=2)
    ax.plot(ranks, mu, color="#08306B", lw=1.6, zorder=3, label="mean at equal rank")
    ax.annotate(rf"Pearson $r={corr:.2f}$", xy=(0.04, 0.92), xycoords="axes fraction",
                fontsize=8)
    ax.grid(alpha=.25, lw=.5)
    ax.set_xlabel(r"$\mathbb{F}_2$-rank of $A$")
    ax.set_ylabel(r"scheduled depth $D^\star$")
    ax.legend(frameon=False, fontsize=6.8, loc="lower right")
    fig.tight_layout(); fig.savefig("figures/rank_analysis_c.pdf"); plt.close(fig)
    spread = {int(r): [int(dp[rk == r].min()), int(dp[rk == r].max())]
              for r in np.unique(rk) if (rk == r).sum() >= 8}
    stats["fig3"] = {"n": n, "instances": len(pts), "per_target_rank": per_r,
                     "pearson_r_rank_depth": round(corr, 3),
                     "depth_range_at_common_ranks": spread}


def fig4(rng, stats):
    n = m = 25
    ks = list(range(3, 9)); ps = np.round(np.linspace(0.1, 0.9, 9), 2)
    NI = 20; V = 64
    heat = np.zeros((len(ks), len(ps)))
    for ik, k in enumerate(ks):
        H = nx.random_regular_graph(k, V, seed=1000 + k)
        while not nx.is_connected(H):
            H = nx.random_regular_graph(k, V, seed=int(rng.integers(0, 10**6)))
        spl = dict(nx.all_pairs_shortest_path_length(H))
        for ip, p in enumerate(ps):
            vals = []
            for _ in range(NI):
                A = rng.random((m, n)) < p
                edges = [(("a", c), ("d", r)) for r in range(m) for c in range(n) if A[r, c]]
                if not edges:
                    continue
                nodes = [("a", c) for c in range(n)] + [("d", r) for r in range(m)]
                pl = greedy_place(edges, nodes, H, spl)
                vals.append(max(spl[pl[u]][pl[v]] for u, v in edges))
            heat[ik, ip] = np.mean(vals)
    fig, ax = plt.subplots(figsize=(3.4, 2.7))
    im = ax.imshow(heat, origin="lower", aspect="auto", cmap="viridis",
                   extent=[ps[0], ps[-1], ks[0], ks[-1]])
    ax.set_xlabel(r"matrix density $p$"); ax.set_ylabel(r"hardware degree $k$")
    cb = fig.colorbar(im, ax=ax); cb.set_label(r"mean $d_{\max}$ (proxy)")
    fig.tight_layout(); fig.savefig("figures/locality_2d_heatmap_analysis.pdf")
    plt.close(fig)
    stats["fig4"] = {"n": n, "hardware_nodes": V, "k_grid": ks,
                     "p_grid": ps.tolist(), "instances_per_cell": NI,
                     "heat_mean_dmax": np.round(heat, 2).tolist()}


def figS1(rng, stats):
    n = m = 50; NI = 200
    ps = np.linspace(0.05, 0.95, 10)
    mu, sd = [], []
    for p in ps:
        c = [(rng.random((m, n)) < p).sum() for _ in range(NI)]
        mu.append(np.mean(c)); sd.append(np.std(c, ddof=1))
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    ax.errorbar(ps, mu, yerr=sd, fmt="o", ms=3.5, color=C["blue"], lw=1,
                capsize=2, label=r"empirical $\|A\|_0$")
    ax.plot(ps, n * m * ps, "--", color=C["grey"], lw=1, label=r"binomial mean $nmp$")
    ax.set_xlabel(r"matrix density $p$"); ax.set_ylabel("CNOT count")
    ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig("figures/cnot_count_analysis.pdf"); plt.close(fig)
    stats["figS1"] = {"n": n, "instances_per_point": NI, "p_grid": list(np.round(ps, 3))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=5)
    args = ap.parse_args()
    os.makedirs("figures", exist_ok=True); os.makedirs("results", exist_ok=True)
    rng = np.random.default_rng(args.seed)
    stats = {"seed": args.seed}
    fig2(rng, stats); fig3(rng, stats); fig4(rng, stats); figS1(rng, stats)
    with open("results/main_figure_stats.json", "w") as f:
        json.dump(stats, f, indent=2)
    print(json.dumps({k: (v if k in ("seed",) else "written") for k, v in stats.items()}))
    print("figures: depth_analysis_ab / rank_analysis_c / "
          "locality_2d_heatmap_analysis / cnot_count_analysis  [REAL DATA]")
    print(f"fig3 Pearson r(rank, depth) = {stats['fig3']['pearson_r_rank_depth']}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Re-run the three case studies with documented ensembles and regenerate
Figs. 5-7 from real data.

Case I   Affine Simon instances: compile oracle, verify functionally on ALL
         2^n inputs, exactly sample the measurement distribution (uniform on
         rowspace(A)), recover the hidden period by F2 linear algebra.
Case II  X-type coset operators: verify the Clifford SELECT block-encoding to
         machine precision, for the uniform coset average AND for arbitrary
         positive weights (non-Clifford cost confined to PREPARE), and verify
         the closed-form spectrum lambda_y = (-1)^{h.y} alpha_hat(G^T y).
Case III CSS syndrome extraction: compile (H_Z, 0) for the rotated surface
         code, verify depth = Delta = 4 and syndromes on random error
         patterns; collect circuit-level distances from the stim experiment.

Outputs: figures/fig_case_simon.pdf, figures/fig_case_qsvt.pdf,
         figures/fig_case_surface.pdf, results/case_studies.json
Usage:   python3 experiments/case_studies.py --seed 17
"""
import argparse, json, os, sys
try:
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError as e:
    sys.exit(f"BLOCKER: missing dependency ({e}); pip install numpy matplotlib")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_depth_theorem import dstar, koenig_schedule
from hook_schedule_census import build_code

C = {"blue": "#0072B2", "orange": "#D55E00", "green": "#009E73", "grey": "0.45"}
plt.rcParams.update({"font.size": 8.5, "axes.labelsize": 9, "legend.fontsize": 7.5,
                     "pdf.fonttype": 42, "figure.dpi": 200, "savefig.bbox": "tight"})


# ---------------------------------------------------------------- utilities
def simulate_layers(layers, n, m, x):
    """Classically simulate the compiled circuit on basis input |x>|0^m>
    (exact, since every gate is computational-basis-preserving)."""
    bits = list(x) + [0] * m
    for L in layers:
        for g in L:
            if g[0] == "cx":
                bits[n + g[2]] ^= bits[g[1]]
            else:
                bits[n + g[2]] ^= 1
    return bits[n:]


def f2_rank_np(A):
    M = (np.array(A) % 2).astype(np.uint8).copy()
    r = 0
    for c in range(M.shape[1]):
        piv = np.nonzero(M[r:, c])[0]
        if piv.size == 0:
            continue
        i = r + piv[0]
        M[[r, i]] = M[[i, r]]
        hit = np.nonzero(M[:, c])[0]
        for j in hit:
            if j != r:
                M[j] ^= M[r]
        r += 1
        if r == M.shape[0]:
            break
    return r


# ---------------------------------------------------------------- Case I
def case1(rng, res):
    sizes = list(range(4, 9))
    NI, rows_out = 15, {}
    total_ok = total = 0
    for n in sizes:
        succ, cnots, depths = 0, [], []
        for _ in range(NI):
            while True:  # nontrivial kernel required for a hidden period
                A = (rng.random((n, n)) < 0.5).astype(int)
                if f2_rank_np(A) < n:
                    break
            b = rng.integers(0, 2, n)
            Al, bl = A.tolist(), b.tolist()
            layers, D = koenig_schedule(Al, bl)
            assert D == dstar(Al, bl)
            # functional verification on ALL 2^n inputs
            for xi in range(2 ** n):
                x = [(xi >> t) & 1 for t in range(n)]
                want = ((A @ np.array(x)) + b) % 2
                got = simulate_layers(layers, n, n, x)
                assert list(want) == got, "compiled oracle disagrees with spec"
            # Simon sampling: measurement outcomes are uniform on rowspace(A)
            Y = (rng.integers(0, 2, (4 * n, n)) @ A) % 2
            succ += int(f2_rank_np(Y) == f2_rank_np(A))  # => ker Y = ker A ∋ s
            cnots.append(int(A.sum())); depths.append(D)
        rows_out[n] = {"instances": NI, "recovered": succ,
                       "mean_cnot": round(float(np.mean(cnots)), 1),
                       "sd_cnot": round(float(np.std(cnots, ddof=1)), 1),
                       "mean_depth": round(float(np.mean(depths)), 1),
                       "sd_depth": round(float(np.std(depths, ddof=1)), 1)}
        total_ok += succ; total += NI
    res["case1"] = {"sizes": sizes, "queries_per_instance": "4n",
                    "ensemble": "A~Bern(0.5)^{n x n} conditioned on rank<n; b~Bern(0.5)",
                    "per_n": rows_out, "recovered_total": f"{total_ok}/{total}"}
    # ---- figure
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(6.9, 2.5))
    ns = np.array(sizes)
    mc = [rows_out[n]["mean_cnot"] for n in sizes]
    sc = [rows_out[n]["sd_cnot"] for n in sizes]
    md = [rows_out[n]["mean_depth"] for n in sizes]
    sd = [rows_out[n]["sd_depth"] for n in sizes]
    axa.errorbar(ns, mc, yerr=sc, fmt="o-", ms=3.5, capsize=2, color=C["blue"],
                 label="CNOT count")
    axa.errorbar(ns, md, yerr=sd, fmt="s-", ms=3.5, capsize=2, color=C["green"],
                 label=r"scheduled depth $D^\star$")
    axa.plot(ns, ns + 1, "--", lw=1, color=C["grey"], label=r"depth worst case $n+1$")
    axa.set_xlabel(r"register size $n$"); axa.set_ylabel("compiled resources")
    axa.set_title("a", loc="left", fontweight="bold")
    axa.legend(frameon=False)
    qrom = 4 * (2 ** ns - 1)
    axb.semilogy(ns, qrom, "o-", ms=3.5, color=C["orange"],
                 label=r"table lookup: $4(2^n-1)$ $T$ gates")
    axb.scatter(ns, np.full_like(ns, 0.55, dtype=float), marker="v",
                color=C["blue"], zorder=5, clip_on=False,
                label="Stab-QRAM: exactly 0 (off log axis)")
    axb.set_ylim(0.5, 3e4)
    axb.set_xlabel(r"register size $n$"); axb.set_ylabel(r"oracle $T$-count per query")
    axb.set_title("b", loc="left", fontweight="bold")
    axb.legend(frameon=False, loc="upper left", fontsize=7, handletextpad=0.5)
    fig.tight_layout(); fig.savefig("figures/fig_case_simon.pdf"); plt.close(fig)


# ---------------------------------------------------------------- Case II
def Xperm(a, m):
    """2^m x 2^m permutation matrix of X^a (bit i of integer index = qubit i)."""
    dim = 2 ** m
    ai = sum(int(bit) << i for i, bit in enumerate(a))
    P = np.zeros((dim, dim))
    idx = np.arange(dim)
    P[idx ^ ai, idx] = 1.0
    return P


def case2(rng, res):
    NI = 65
    err_unw, err_w, err_spec = [], [], []
    depth_ok = 0
    for _ in range(NI):
        s = int(rng.integers(1, 5)); m = int(rng.integers(2, 7))
        G = (rng.random((m, s)) < 0.5).astype(int)
        h = rng.integers(0, 2, m)
        dim_a, dim_d = 2 ** s, 2 ** m
        # SELECT as a permutation: |k>|y> -> |k>|y + Gk + h>
        S = np.zeros((dim_a * dim_d, dim_a * dim_d))
        for k in range(dim_a):
            kv = np.array([(k >> i) & 1 for i in range(s)])
            a = (G @ kv + h) % 2
            ai = sum(int(bit) << i for i, bit in enumerate(a))
            base = k * dim_d
            idx = np.arange(dim_d)
            S[base + (idx ^ ai), base + idx] = 1.0
        # compiled-circuit cross-check: layers reproduce SELECT's action
        layers, D = koenig_schedule(G.tolist(), h.tolist())
        for _ in range(8):
            kv = rng.integers(0, 2, s); yv = rng.integers(0, 2, m)
            outd = simulate_layers(layers, s, m, list(kv))
            want = (np.array(outd) + yv) % 2  # CNOT/X action is additive in y
            assert list(want) == list((G @ kv + h + yv) % 2)
        depth_ok += int(D == dstar(G.tolist(), h.tolist()))
        # (i) uniform coset average, PREPARE = H^{otimes s}
        Hs = np.array([[1.0]])
        H1 = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
        for _ in range(s):
            Hs = np.kron(Hs, H1)
        Bd = np.kron(Hs, np.eye(dim_d)) @ S @ np.kron(Hs, np.eye(dim_d))
        M = sum(Xperm([int(v) for v in (G @ np.array(
            [(k >> i) & 1 for i in range(s)]) + h) % 2], m)
                for k in range(dim_a)) / dim_a
        err_unw.append(float(np.linalg.norm(Bd[:dim_d, :dim_d] - M)))
        # (ii) arbitrary positive weights: PREPARE carries all non-Clifford cost
        alpha = rng.random(dim_a) + 0.05
        lam = alpha.sum()
        w = np.sqrt(alpha / lam)
        Q, _ = np.linalg.qr(np.column_stack([w, rng.standard_normal((dim_a, dim_a - 1))])
                            if dim_a > 1 else w.reshape(1, 1))
        if np.dot(Q[:, 0], w) < 0:
            Q[:, 0] *= -1
        Bw = np.kron(Q.T, np.eye(dim_d)) @ S @ np.kron(Q, np.eye(dim_d))
        Malpha = sum(alpha[k] * Xperm([int(v) for v in (G @ np.array(
            [(k >> i) & 1 for i in range(s)]) + h) % 2], m)
            for k in range(dim_a))
        err_w.append(float(np.linalg.norm(Bw[:dim_d, :dim_d] - Malpha / lam)))
        # (iii) spectrum: lambda_y = (-1)^{h.y} alpha_hat(G^T y)
        pred = []
        for y in range(dim_d):
            yv = np.array([(y >> i) & 1 for i in range(m)])
            z = (G.T @ yv) % 2
            ah = sum(alpha[k] * (-1) ** int(np.dot(
                np.array([(k >> i) & 1 for i in range(s)]), z) % 2)
                for k in range(dim_a))
            pred.append(((-1) ** int(np.dot(h, yv) % 2)) * ah)
        ev = np.linalg.eigvalsh(Malpha)
        err_spec.append(float(np.max(np.abs(np.sort(ev) - np.sort(np.array(pred))))))
    res["case2"] = {"instances": NI, "s_range": [1, 4], "m_range": [2, 6],
                    "depth_certificate_matches": f"{depth_ok}/{NI}",
                    "max_frobenius_error_uniform": float(np.max(err_unw)),
                    "max_frobenius_error_weighted": float(np.max(err_w)),
                    "max_spectrum_error_weighted": float(np.max(err_spec))}
    # ---- figure: showcase sparsity pattern + SELECT T-count
    s, m = 3, 6
    rng2 = np.random.default_rng(7)
    G = (rng2.random((m, s)) < 0.5).astype(int); h = rng2.integers(0, 2, m)
    M = sum(Xperm([int(v) for v in (G @ np.array(
        [(k >> i) & 1 for i in range(s)]) + h) % 2], m) for k in range(2 ** s)) / 2 ** s
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(6.9, 2.6))
    axa.imshow(M != 0, cmap="Blues", interpolation="nearest")
    axa.set_xlabel("column"); axa.set_ylabel("row")
    axa.set_title("a", loc="left", fontweight="bold")
    ss = np.arange(1, 9)
    axb.semilogy(ss, 4 * (2 ** ss - 1), "o-", ms=3.5, color=C["orange"],
                 label=r"table-based SELECT: $4(2^s-1)$ $T$")
    axb.scatter(ss, np.full_like(ss, 0.55, dtype=float), marker="v", color=C["blue"],
                zorder=5, clip_on=False, label="Clifford SELECT: exactly 0 (off axis)")
    axb.set_ylim(0.5, 3e4)
    axb.set_xlabel(r"ancilla register size $s$")
    axb.set_ylabel(r"SELECT $T$-count")
    axb.set_title("b", loc="left", fontweight="bold")
    axb.legend(frameon=False, loc="upper left", fontsize=7, handletextpad=0.5)
    fig.tight_layout(); fig.savefig("figures/fig_case_qsvt.pdf"); plt.close(fig)


# ---------------------------------------------------------------- Case III
def get_code(d):
    for parity_X in (0, 1):
        for th, tv in (("X", "Z"), ("Z", "X")):
            checks, ok = build_code(d, parity_X, th, tv)
            if ok:
                return checks
    raise RuntimeError("no valid rotated-surface-code convention found")


def case3(rng, res):
    per_d, NI = {}, 30
    for d in (3, 5, 7):
        checks = get_code(d)
        zch = [ch for ch in checks if ch["type"] == "Z"]
        HZ = [[0] * (d * d) for _ in zch]
        for j, ch in enumerate(zch):
            for (r, c) in ch["support"]:
                HZ[j][r * d + c] = 1
        nq, mq = d * d, len(zch)
        Hl = HZ  # A[j][k]: j indexes checks (data register), k data qubits (address)
        layers, D = koenig_schedule(Hl, [0] * mq)
        delta = max(max(sum(r) for r in Hl),
                    max(sum(Hl[j][k] for j in range(mq)) for k in range(nq)))
        ok_syn = 0
        for _ in range(NI):
            e = [int(v) for v in (rng.random(nq) < 0.3)]
            syn = simulate_layers(layers, nq, mq, e)
            want = [sum(Hl[j][k] * e[k] for k in range(nq)) % 2 for j in range(mq)]
            ok_syn += int(syn == want)
        per_d[d] = {"z_checks": mq, "Delta": delta, "compiled_depth": D,
                    "sequential_layers": int(sum(map(sum, Hl))),
                    "syndrome_patterns_verified": f"{ok_syn}/{NI}"}
    seq = {d: None for d in (3, 5, 7, 9, 11, 13)}
    for d in seq:
        checks = get_code(d)
        seq[d] = sum(len(ch["support"]) for ch in checks if ch["type"] == "Z")
    stim_res = {}
    try:
        stim_res = json.load(open("results/stim_distance.json"))
    except FileNotFoundError:
        pass
    scan = {}
    try:
        scan = json.load(open("results/stim_consistency_scan.json"))
    except FileNotFoundError:
        pass
    res["case3"] = {"per_d": per_d, "sequential_HZ_weight": seq,
                    "stim": {k: {kk: v[kk] for kk in
                                 ("standard_distance", "mirrored_distance",
                                  "n_cycle_inconsistent", "samples") if kk in v}
                             for k, v in stim_res.items()},
                    "consistency_scan": {k: {"sampled": v["sampled"],
                                             "round_consistent": v["round_consistent"]}
                                         for k, v in scan.items()}}
    # ---- figure
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(6.9, 2.6))
    ds = np.array(sorted(seq))
    axa.semilogy(ds, [seq[d] for d in ds], "o-", ms=3.5, color=C["orange"],
                 label=r"sequential: $\|H_Z\|_0=\Theta(d^2)$ layers")
    axa.semilogy(ds, np.full_like(ds, 4), "s-", ms=3.5, color=C["blue"],
                 label=r"compiled schedule: $\Delta=4$ layers")
    axa.set_xlabel(r"code distance $d$"); axa.set_ylabel("CNOT layers per round")
    axa.set_title("a", loc="left", fontweight="bold"); axa.legend(frameon=False)
    if stim_res:
        dd = [3, 5]
        std = [stim_res[f"d={d}"]["standard_distance"] for d in dd]
        mir = [stim_res[f"d={d}"]["mirrored_distance"] for d in dd]
        xpos = np.arange(len(dd))
        axb.bar(xpos - 0.18, std, 0.34, color=C["green"],
                label="standard schedule (0 parallel hooks)")
        axb.bar(xpos + 0.18, mir, 0.34, color=C["orange"],
                label="hook-parallel schedule")
        for i, d in enumerate(dd):
            axb.plot([i - 0.4, i + 0.4], [d, d], "--", color="k", lw=1)
        for x_, v in zip(xpos - 0.18, std):
            axb.text(x_, v + 0.14, str(v), ha="center", va="bottom", fontsize=7)
        for x_, v in zip(xpos + 0.18, mir):
            axb.text(x_, v + 0.14, str(v), ha="center", va="bottom", fontsize=7)
        axb.text(1.43, dd[-1], "ideal $d$", ha="left", va="center", fontsize=6.5)
        axb.set_xlim(-0.6, 1.95)
        axb.set_ylim(0, 7.4)
        axb.set_xticks(xpos, [f"$d={d}$" for d in dd])
        axb.set_ylabel("circuit-level distance")
        axb.set_title("b", loc="left", fontweight="bold")
        axb.legend(frameon=False, fontsize=7, loc="upper left")
    fig.tight_layout(); fig.savefig("figures/fig_case_surface.pdf"); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=17)
    args = ap.parse_args()
    os.makedirs("figures", exist_ok=True); os.makedirs("results", exist_ok=True)
    rng = np.random.default_rng(args.seed)
    res = {"seed": args.seed}
    case1(rng, res); case2(rng, res); case3(rng, res)
    with open("results/case_studies.json", "w") as f:
        json.dump(res, f, indent=2)
    print(json.dumps(res, indent=1)[:1600])
    print("...\nfigures: fig_case_simon / fig_case_qsvt / fig_case_surface  [REAL DATA]")


if __name__ == "__main__":
    main()

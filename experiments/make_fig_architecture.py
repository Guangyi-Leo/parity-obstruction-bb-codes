#!/usr/bin/env python3
"""Generate Fig. 1 (fig_architecture.pdf): the Stab-QRAM compilation pipeline.

Panel a: specification (A, b); panel b: augmented bipartite interaction graph with a
proper D*-edge-coloring (computed, not hand-coded); panel c: the scheduled circuit.

Output: figures/fig_architecture.pdf (and .png preview)
Usage:  python3 experiments/make_fig_architecture.py
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle, Rectangle

# ---- worked example ---------------------------------------------------------
A = [[1, 1, 0, 1],
     [0, 1, 1, 0],
     [1, 0, 1, 1]]
b = [0, 1, 0]
m, n = len(A), len(A[0])

# ---- D* and Koenig coloring (same routine as verify_depth_theorem.py) -------
col_w = [sum(A[j][k] for j in range(m)) for k in range(n)]
row_w = [sum(A[j]) for j in range(m)]
DSTAR = max(col_w + [row_w[j] + b[j] for j in range(m)])

edges = []
for j in range(m):
    for k in range(n):
        if A[j][k]:
            edges.append((("a", k), ("d", j)))
    if b[j]:
        edges.append((("u", j), ("d", j)))
deg = {}
for u, v in edges:
    deg[u] = deg.get(u, 0) + 1
    deg[v] = deg.get(v, 0) + 1
edges.sort(key=lambda e: -(max(deg[e[0]], deg[e[1]])))
used, color = {}, {}


def bt(i):
    if i == len(edges):
        return True
    u, v = edges[i]
    for c in range(DSTAR):
        if c not in used.get(u, set()) and c not in used.get(v, set()):
            used.setdefault(u, set()).add(c)
            used.setdefault(v, set()).add(c)
            color[(u, v)] = c
            if bt(i + 1):
                return True
            used[u].discard(c)
            used[v].discard(c)
            del color[(u, v)]
    return False


assert bt(0), "coloring failed"
PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00"]  # colorblind safe

fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.55),
                         gridspec_kw={"width_ratios": [0.85, 1.0, 1.45]})
plt.subplots_adjust(wspace=0.32, left=0.045, right=0.985, top=0.86, bottom=0.07)

# ---- panel a: specification --------------------------------------------------
ax = axes[0]
ax.set_title(r"$\mathbf{a}$  specification $(A,\mathbf{b})$", loc="left", fontsize=9)
for j in range(m):
    for k in range(n):
        ax.add_patch(Rectangle((k, m - 1 - j), 1, 1, facecolor="#444444" if A[j][k] else "white",
                               edgecolor="0.55", lw=0.7))
        ax.text(k + 0.5, m - 1 - j + 0.5, str(A[j][k]), ha="center", va="center",
                fontsize=8, color="white" if A[j][k] else "0.45")
for j in range(m):
    ax.add_patch(Rectangle((n + 0.5, m - 1 - j), 1, 1, facecolor="#8B0000" if b[j] else "white",
                           edgecolor="0.55", lw=0.7))
    ax.text(n + 1.0, m - 1 - j + 0.5, str(b[j]), ha="center", va="center",
            fontsize=8, color="white" if b[j] else "0.45")
ax.text(n / 2, m + 0.32, r"$A\in\mathbb{F}_2^{3\times 4}$", ha="center", fontsize=8)
ax.text(n + 1.0, m + 0.32, r"$\mathbf{b}$", ha="center", fontsize=8)
for k in range(n):
    ax.text(k + 0.5, -0.34, rf"$x_{k+1}$", ha="center", fontsize=7.5)
for j in range(m):
    ax.text(-0.34, m - 1 - j + 0.5, rf"$d_{j+1}$", ha="right", va="center", fontsize=7.5)
ax.set_xlim(-1.0, n + 1.8)
ax.set_ylim(-0.8, m + 0.85)
ax.set_aspect("equal")
ax.axis("off")

# ---- panel b: augmented bipartite graph with coloring ------------------------
ax = axes[1]
ax.set_title(r"$\mathbf{b}$  edge-colored graph $G_A^{\prime}$", loc="left", fontsize=9)
ya = {k: 3.1 - k * 1.0 for k in range(n)}          # address column
yd = {j: 2.6 - j * 1.3 for j in range(m)}          # data column
pos = {("a", k): (0.0, ya[k]) for k in range(n)}
pos.update({("d", j): (2.0, yd[j]) for j in range(m)})
pos.update({("u", j): (3.15, yd[j]) for j in range(m) if b[j]})  # pendant: horizontal, aligned with d_j
for (u, v), c in color.items():
    (x1, y1), (x2, y2) = pos[u], pos[v]
    ax.plot([x1, x2], [y1, y2], color=PALETTE[c], lw=2.0, zorder=1,
            solid_capstyle="round")
for k in range(n):
    x, y = pos[("a", k)]
    ax.add_patch(Circle((x, y), 0.17, facecolor="white", edgecolor="black", lw=1.0, zorder=3))
    ax.text(x - 0.40, y, rf"$x_{k+1}$", ha="right", va="center", fontsize=8)
for j in range(m):
    x, y = pos[("d", j)]
    ax.add_patch(Rectangle((x - 0.16, y - 0.16), 0.32, 0.32, facecolor="white",
                           edgecolor="black", lw=1.0, zorder=3))
    if b[j]:  # pendant edge leaves to the right: label below to avoid the edge
        ax.text(x, y - 0.28, rf"$d_{j+1}$", ha="center", va="top", fontsize=8)
    else:
        ax.text(x + 0.40, y, rf"$d_{j+1}$", ha="left", va="center", fontsize=8)
for j in range(m):
    if b[j]:
        x, y = pos[("u", j)]
        ax.add_patch(Circle((x, y), 0.13, facecolor="#8B0000", edgecolor="black",
                            lw=0.8, zorder=3))
        ax.text(x, y + 0.28, rf"$u_{j+1}$", ha="center", va="bottom", fontsize=8)
        ax.text(x, y - 0.30, rf"$b_{j+1}{{=}}1$", ha="center", va="top", fontsize=6.5, color="#8B0000")
ax.text(1.0, -0.75, rf"$D^\star={DSTAR}$ colors $=$ layers", ha="center", fontsize=8)
ax.set_xlim(-0.9, 3.8)
ax.set_ylim(-1.15, 3.7)
ax.set_aspect("equal")
ax.axis("off")

# ---- panel c: scheduled circuit ----------------------------------------------
ax = axes[2]
ax.set_title(r"$\mathbf{c}$  scheduled Clifford circuit", loc="left", fontsize=9)
wires = [("a", k) for k in range(n)] + [("d", j) for j in range(m)]
wy = {w: (n + m - 1 - i) * 0.62 for i, w in enumerate(wires)}
x0, dx = 1.05, 1.30
ax.set_xlim(-0.85, x0 + DSTAR * dx + 0.15)
ax.set_ylim(-0.5, (n + m - 1) * 0.62 + 0.55)
for w in wires:
    ax.plot([0.25, x0 + DSTAR * dx - 0.30], [wy[w], wy[w]], color="black", lw=0.8, zorder=1)
    lbl = rf"$|x_{w[1]+1}\rangle$" if w[0] == "a" else rf"$|0\rangle_{{d_{w[1]+1}}}$"
    ax.text(0.12, wy[w], lbl, ha="right", va="center", fontsize=7.5)
layers = [[] for _ in range(DSTAR)]
for (u, v), c in color.items():
    layers[c].append((u, v))
for ell, L in enumerate(layers):
    xc = x0 + ell * dx
    if ell:
        ax.plot([xc - dx / 2 - 0.06, xc - dx / 2 - 0.06],
                [-0.32, (n + m - 1) * 0.62 + 0.30], ls=":", lw=0.7, color="0.6")
    ax.text(xc, (n + m - 1) * 0.62 + 0.42, rf"$L_{ell+1}$", ha="center", fontsize=8,
            color=PALETTE[ell])
    offs = [(-0.27, 0.0, 0.27), (-0.27, 0.0, 0.27), (-0.27, 0.0, 0.27)][0]
    Ls = sorted(L, key=lambda e: wy[e[1]], reverse=True)
    for gi, (u, v) in enumerate(Ls):
        xg = xc + offs[gi % 3] if len(Ls) > 1 else xc
        if u[0] == "a":  # CNOT
            yc, yt = wy[u], wy[v]
            ax.plot([xg, xg], [yc, yt], color=PALETTE[ell], lw=1.6, zorder=2)
            ax.add_patch(Circle((xg, yc), 0.07, facecolor=PALETTE[ell],
                                edgecolor=PALETTE[ell], zorder=3))
            ax.add_patch(Circle((xg, yt), 0.15, facecolor="white",
                                edgecolor=PALETTE[ell], lw=1.6, zorder=3))
            ax.plot([xg - 0.15, xg + 0.15], [yt, yt], color=PALETTE[ell], lw=1.4, zorder=4)
            ax.plot([xg, xg], [yt - 0.15, yt + 0.15], color=PALETTE[ell], lw=1.4, zorder=4)
        else:  # X gate (pendant edge)
            yt = wy[v]
            ax.add_patch(Rectangle((xg - 0.15, yt - 0.15), 0.30, 0.30, facecolor="white",
                                   edgecolor=PALETTE[ell], lw=1.6, zorder=3))
            ax.text(xg, yt, "X", ha="center", va="center", fontsize=8,
                    color=PALETTE[ell], zorder=4)
ax.set_aspect("equal")
ax.axis("off")

os.makedirs("figures", exist_ok=True)
fig.savefig("figures/fig_architecture.pdf")
fig.savefig("figures/fig_architecture.png", dpi=220)
print(f"wrote figures/fig_architecture.pdf  (D* = {DSTAR}, edges = {len(edges)})")

"""The mod-4 obstruction in its general form, stated on H_X and H_Z directly.

Hypothesis (per connected component of the Tanner graph):
    every data qubit v has r_v X-neighbours and s_v Z-neighbours with r_v + s_v = Delta,
    and every X-check has weight Delta.
Quantity:
    sum_v r_v s_v -- the number of corners in the component, since a qubit with r_v
    X-edges and s_v Z-edges carries r_v * s_v of them.
Reading:
    a proper schedule splits the corners evenly into X-first and Z-first, so
    sum_v r_v s_v must be even and half of it must itself be even; the component is
    obstructed exactly when sum_v r_v s_v = 2 (mod 4).

The old form assumed the component regular with constant (Delta_X, Delta_Z) and tested
n * Delta_X * Delta_Z / 2 for oddness; that is the special case r_v = Delta_X for all v.
"""
from __future__ import annotations

import numpy as np


def obstruction_general(HX, HZ) -> list[dict]:
    """Per connected component: (sum r_v s_v mod 4, hypothesis_met, obstructed)."""
    HX = np.asarray(HX) % 2
    HZ = np.asarray(HZ) % 2
    mx, n = HX.shape
    mz, n2 = HZ.shape
    assert n == n2, f"H_X has {n} columns, H_Z has {n2}"

    r = HX.sum(axis=0).astype(int)          # X-neighbours of each data qubit
    s = HZ.sum(axis=0).astype(int)          # Z-neighbours of each data qubit
    wx = HX.sum(axis=1).astype(int)         # X-check weights

    # bipartite adjacency: qubit j <-> ("X", i) / ("Z", i)
    adj: dict = {("q", j): [] for j in range(n)}
    for i in range(mx):
        adj[("X", i)] = [("q", j) for j in np.nonzero(HX[i])[0]]
        for v in adj[("X", i)]:
            adj[v].append(("X", i))
    for i in range(mz):
        adj[("Z", i)] = [("q", j) for j in np.nonzero(HZ[i])[0]]
        for v in adj[("Z", i)]:
            adj[v].append(("Z", i))

    seen, out = set(), []
    for start in adj:
        if start in seen:
            continue
        stack, comp = [start], {"q": [], "X": [], "Z": []}
        seen.add(start)
        while stack:
            v = stack.pop()
            comp[v[0]].append(v[1])
            for w in adj[v]:
                if w not in seen:
                    seen.add(w); stack.append(w)
        qs = comp["q"]
        if not qs:
            continue                         # an isolated check carries no corners
        deg = {int(r[j] + s[j]) for j in qs}
        wts = {int(wx[i]) for i in comp["X"]}
        delta = next(iter(deg)) if len(deg) == 1 else None
        met = (len(deg) == 1 and (not wts or wts == deg))
        tot = int(sum(int(r[j]) * int(s[j]) for j in qs))
        out.append(dict(component=len(out), n=len(qs), n_X=len(comp["X"]),
                        n_Z=len(comp["Z"]), Delta=delta, hypothesis_met=met,
                        sum_rs=tot, sum_rs_mod4=tot % 4,
                        obstructed=bool(met and tot % 4 == 2)))
    return out


def obstructed(HX, HZ) -> bool:
    """True iff some component carries the obstruction."""
    return any(c["obstructed"] for c in obstruction_general(HX, HZ))

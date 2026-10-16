"""A Koenig edge colouring of the Tanner graph, and the scene data for Fig. 1.

The Tanner graph of a two-block code is bipartite and Delta-regular (every
check carries k + l edges; every data qubit carries k edges of one kind and l
of the other).  Koenig's theorem therefore gives a proper edge colouring with
exactly Delta colours, i.e. a depth-Delta schedule in which every layer is a
perfect matching.  Such a schedule always exists -- it is the degree bound --
and for bb72 it is *improper* in the M_pi sense: some overlap pair has its two
shared corners oriented differently, so the two checks fail to commute through
the cycle.  That contrast is the subject of Fig. 1, and it is computed here
rather than drawn by hand.

Written by figures/src/manuscript_figs.py via data/fig1_scene.json.
"""
from __future__ import annotations

import json
import os

from .code import TwoBlockCode
from .simulate import orientation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SCHED = os.path.join(ROOT, "schedules")


def konig_colouring(code: TwoBlockCode) -> list[int]:
    """Proper edge colouring with Delta colours, 1-based, by alternating paths.

    For each edge in turn pick a colour `a` free at the check and `b` free at
    the qubit.  If they differ, flip the maximal alternating a/b path hanging
    off the qubit -- in a bipartite graph that path cannot return to the check,
    so after the flip `a` is free at both ends.
    """
    D = code.Delta
    colour = [0] * code.n_edges
    # free[v] is the set of colours unused at vertex v
    free = {v: set(range(1, D + 1)) for v in code.vertices}

    def vert_of(e, end):
        ed = code.edges[e]
        return (ed.kind, ed.check) if end == "c" else (ed.side, ed.qubit)

    def edge_at(v, c):
        for e in code.incident(v):
            if colour[e] == c:
                return e
        return None

    for e in range(code.n_edges):
        cv, qv = vert_of(e, "c"), vert_of(e, "q")
        a = min(free[cv])
        b = min(free[qv])
        if a == b:
            colour[e] = a
            free[cv].discard(a)
            free[qv].discard(a)
            continue
        # walk the maximal a/b alternating path starting at the qubit end
        path, v, want = [], qv, a
        while True:
            nxt = edge_at(v, want)
            if nxt is None:
                break
            path.append(nxt)
            ed = code.edges[nxt]
            other = ((ed.kind, ed.check) if v == (ed.side, ed.qubit)
                     else (ed.side, ed.qubit))
            v, want = other, (b if want == a else a)
        touched = set()
        for p in path:                      # swap a <-> b along the path
            colour[p] = b if colour[p] == a else a
            touched.add(vert_of(p, "c"))
            touched.add(vert_of(p, "q"))
        # A vertex interior to the path keeps one a-edge and one b-edge, so its
        # free set is unchanged, while each endpoint gains one colour and loses
        # the other.  Rebuilding from `colour` is exact and costs one pass over
        # six incident edges; updating in place per edge is not, because the two
        # path edges at an interior vertex each rewrite what the other just set.
        for w in touched:
            free[w] = set(range(1, D + 1)) - {colour[x] for x in code.incident(w)
                                              if colour[x]}
        colour[e] = a
        free[cv].discard(a)
        free[qv].discard(a)
    return colour


def verify_colouring(code: TwoBlockCode, colour: list[int]) -> dict:
    """A colouring is proper iff no vertex sees a colour twice."""
    bad = 0
    for v in code.vertices:
        cs = [colour[e] for e in code.incident(v)]
        if len(set(cs)) != len(cs):
            bad += 1
    return dict(n_colours=len(set(colour)), vertices_with_repeat=bad,
                uncoloured=sum(1 for c in colour if c == 0))


def pair_orientations(code: TwoBlockCode, lay, op) -> dict:
    """Orientation of every shared corner of one overlap pair, by side."""
    out = {}
    for cid in op.corners:
        c = code.corners[cid]
        out[c.side] = orientation(code, lay, c)
    par = 0
    for cid in op.corners:
        par ^= orientation(code, lay, code.corners[cid])
    return dict(o=out, parity=par, n_corners=len(op.corners))

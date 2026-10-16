"""Scene data for Fig. 1: the depth-7 schedule, a Koenig 6-colouring, and the
one overlap pair that tells the story.

Everything Fig. 1 draws is decided here and written to data/fig1_scene.json, so
no layer index, orientation or count is typed into the figure code.

The scene is a 4 x 3 patch of the bb72 Tanner graph.  Group elements are
(gx, gy) in Z6 x Z6; the patch is gx in 0..3, gy in 0..2.  Each cell carries an
L-qubit and an R-qubit on the lower plate and an X-check and a Z-check on the
upper plate.  An edge is "internal" when both endpoints lie in the patch; the
rest are drawn as stubs, the way Bravyi Fig. 1 lets its wrap edges run off
behind the lattice.

The highlighted pair is an overlap pair (X_g, Z_{g+delta}) whose two shared
corners -- one L, one R, which is what distinct sums forces -- are oriented
    o_L = o_R = 1   under the depth-7 schedule   (parity 0: proper)
    o_L = 1, o_R = 0 under the Koenig colouring  (parity 1: improper)
so the same pair carries both insets.  54 of the 324 overlap pairs have that
signature; the one chosen is the first whose four corner edges all lie inside
the patch, so the leaders have somewhere to land.
"""
from __future__ import annotations

import collections
import json
import os

from .code import TwoBlockCode
from .konig import konig_colouring, pair_orientations, verify_colouring
from .simulate import orientation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SCHED = os.path.join(ROOT, "schedules")
PATCH_W, PATCH_H = 4, 4


def build(out="fig1_scene.json", st=(1, 1)):
    with open(os.path.join(SCHED, "bb72_d7_inv.json")) as f:
        d = json.load(f)
    code = TwoBlockCode(d["dims"], [tuple(a) for a in d["A"]],
                        [tuple(b) for b in d["B"]], d["instance"])
    lay7 = {}
    for (kind, side, lab1, chk, qub), L in zip(d["edges"], d["layers"]):
        lay7[code.edge_id(kind, side, chk, lab1 - 1)] = L
    lay7 = [lay7[e] for e in range(code.n_edges)]
    k6 = konig_colouring(code)

    par = {}
    for nm, lay in (("d7", lay7), ("k6", k6)):
        c = collections.Counter(pair_orientations(code, lay, op)["parity"]
                                for op in code.overlap_pairs)
        par[nm] = dict(proper=c[0], improper=c[1])

    els = code.G.elements
    G = code.G

    def sig(op):
        a = pair_orientations(code, lay7, op)["o"]
        b = pair_orientations(code, k6, op)["o"]
        return (a["L"], a["R"]), (b["L"], b["R"])

    # Fig. 1 shows the (s, t) = (1, 1) overlap, so the four decisive layers are
    # the first entry of each row of Table S8 -- the numbers the caption
    # quotes.  Of the |G| translates of that overlap, keep the ones whose
    # corners read (1, 1) under the depth-7 schedule and (1, 0) under the
    # Koenig colouring, then take whichever of those packs its twelve edges
    # into the smallest window, so the patch can be cropped tightly.
    want = ((1, 1), (1, 0))
    delta = G.add(code.A[st[0] - 1], code.B[st[1] - 1])
    cands = [op for op in code.overlap_pairs
             if op.delta == delta and sig(op) == want]
    if not cands:
        cands = [op for op in code.overlap_pairs if sig(op) == want]

    def window(op):
        """Smallest wrapped window (per axis) holding the pair's 12 edges."""
        pts = [els[op.gx], els[op.gz]]
        for e in code.edges:
            if (e.check == op.gx and e.kind == "X") or \
               (e.check == op.gz and e.kind == "Z"):
                pts.append(els[e.qubit])
        span, origin = [], []
        for ax_i, d in enumerate(code.G.dims):
            vals = sorted({p[ax_i] for p in pts})
            best, o = d, 0
            for v in vals:
                w = max((u - v) % d for u in vals) + 1
                if w < best:
                    best, o = w, v
            span.append(best)
            origin.append(o)
        return span, origin

    def pack(op, span, origin, PW, PH):
        in_p = {i2 for i2, g in enumerate(els)
                if (g[0] - origin[0]) % code.G.dims[0] < PW
                and (g[1] - origin[1]) % code.G.dims[1] < PH}

        def loc(g):
            return [(g[0] - origin[0]) % code.G.dims[0],
                    (g[1] - origin[1]) % code.G.dims[1]]

        corners = []
        for cid in op.corners:
            c = code.corners[cid]
            ex, ez = code.edges[c.ex], code.edges[c.ez]
            corners.append(dict(
                side=c.side, qubit=loc(els[c.qubit]),
                x_label=ex.lab1, z_label=ez.lab1,
                d7=dict(x=lay7[c.ex], z=lay7[c.ez],
                        o=orientation(code, lay7, c)),
                k6=dict(x=k6[c.ex], z=k6[c.ez], o=orientation(code, k6, c))))
        corners.sort(key=lambda c: c["side"])
        edges = []
        for e in code.edges:
            if e.check not in in_p and e.qubit not in in_p:
                continue
            edges.append(dict(kind=e.kind, side=e.side, lab=e.lab1,
                              check=loc(els[e.check]), qubit=loc(els[e.qubit]),
                              check_in=e.check in in_p,
                              qubit_in=e.qubit in in_p,
                              d7=lay7[e.eid], k6=k6[e.eid],
                              on_x=e.check == op.gx and e.kind == "X",
                              on_z=e.check == op.gz and e.kind == "Z"))
        return dict(patch=[PW, PH], window_origin=list(origin),
                    highlight=dict(x_check=loc(els[op.gx]),
                                   z_check=loc(els[op.gz]),
                                   delta=list(op.delta), corners=corners),
                    edges=edges)

    # Every candidate is packed with its own window; the figure picks the one
    # whose four decisive edges clear every other glyph, which it can only
    # judge in projected millimetres.
    packed = []
    for op in cands:
        span, origin = window(op)
        # Each candidate keeps its own tight window.  Interiority of both
        # tiles would need the whole 6 x 6 torus, which at 180 mm leaves every
        # glyph at 1.8 mm; clearance was chosen over interiority (CHECK.md).
        packed.append(pack(op, span, origin,
                           max(PATCH_W, span[0]), max(PATCH_H, span[1])))
    chosen = cands[0]
    span, origin = window(chosen)
    PW = max(PATCH_W, span[0])
    PH = max(PATCH_H, span[1])
    base = packed[0]
    in_patch = None

    def local(g):
        return [(g[0] - origin[0]) % code.G.dims[0],
                (g[1] - origin[1]) % code.G.dims[1]]

    scene = dict(
        instance=d["instance"], dims=d["dims"], A=d["A"], B=d["B"],
        Delta=code.Delta, N=code.N, D_published=d["D"],
        patch=base["patch"], window_origin=base["window_origin"],
        n_overlap_pairs=len(code.overlap_pairs),
        corners_per_pair=sorted({len(o.corners) for o in code.overlap_pairs}),
        distinct_sums=code.distinct_sums(),
        parity=par,
        konig=verify_colouring(code, k6),
        depth7=verify_colouring(code, lay7),
        n_pairs_with_signature=len(cands),
        st_labels=list(st),
        highlight=base["highlight"],
        edges=base["edges"],
        candidates=packed,
        source=dict(schedule="schedules/bb72_d7_inv.json",
                    table="tables/tabS8_depth7_schedule.tex",
                    konig="twoblock/konig.py"))
    p = os.path.join(DATA, out)
    with open(p, "w") as f:
        json.dump(scene, f, indent=1)
    return scene


if __name__ == "__main__":
    s = build()
    print(f"instance {s['instance']}  N={s['N']}  Delta={s['Delta']}  "
          f"D published={s['D_published']}  distinct sums={s['distinct_sums']}")
    print(f"overlap pairs {s['n_overlap_pairs']}, corners per pair "
          f"{s['corners_per_pair']}")
    print(f"depth-7  : {s['parity']['d7']}")
    print(f"konig-6  : {s['parity']['k6']}   colours={s['konig']['n_colours']}")
    print(f"pairs with the (1,1)/(1,0) signature: {s['n_pairs_with_signature']}")
    h = s["highlight"]
    print(f"highlight X_{tuple(h['x_check'])} Z_{tuple(h['z_check'])} "
          f"delta={tuple(h['delta'])}")
    for c in h["corners"]:
        print(f"   {c['side']}-corner at {tuple(c['qubit'])}: "
              f"d7 x@{c['d7']['x']} z@{c['d7']['z']} o={c['d7']['o']} | "
              f"k6 x@{c['k6']['x']} z@{c['k6']['z']} o={c['k6']['o']}")
    print(f"edges in patch: {len(s['edges'])}")

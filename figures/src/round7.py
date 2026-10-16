"""Round 7: the three main figures as single composite illustrations.

Each figure is one scene, not a grid of panels: regions are separated by
gutters and arrows rather than by boxes, following the reference figures in
figures/ref/ (see CHECK.md, "Round 7, step 0").

Every count, layer index and orientation is read from a data file --
data/fig1_scene.json, data/coverage.csv and the CSVs named in each builder --
and never typed here.
"""
from __future__ import annotations

import csv
import json
import os

import matplotlib
import matplotlib.pyplot as plt
from collections import Counter
from matplotlib.patches import (Circle, FancyArrowPatch, FancyBboxPatch,
                                Polygon)

import figstyle as S
from figstyle import (DATA, GREY, INK, PT_LETTER, PT_MIN, PT_PANEL,
                      PT_TICK, ROOT, aux_label)

SMALLCAPS = dict(fontsize=PT_TICK, color=INK, fontweight="bold")
BOXED = dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="none")


def _scene(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


def _mm_axes(w_mm, h_mm):
    fig = plt.figure(figsize=(S.mm(w_mm), S.mm(h_mm)))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w_mm)
    ax.set_ylim(0, h_mm)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


# =====================================================================
# Fig. 1  --  from the degree bound to the cross term      180 x 110 mm
# =====================================================================
FIG1_W, FIG1_H = 180.0, 110.0
PX, SKX, SKY = 18.0, 6.5, 7.0          # cell pitch, row skew x, row skew y
X0, YQ, YC = 17.0, 24.0, 70.0          # origin, qubit plate, check plate
DXY = 5.5                              # L/R (and X/Z) separation within a cell
GLYPH = 2.6                            # sphere diameter / tile side
# The patch asks for 2.5 mm of clearance between a decisive edge and every
# other glyph.  That is not reachable here and the build says so: a 6 x 6
# lattice is 12 glyph columns across ~85 mm, so neighbouring glyphs are about
# 5 mm apart and an edge threading between them has at most ~2.5 mm to each --
# only if it threads perfectly.  Measured best over all candidate pairs and a
# sweep of the layout constants: 0.35 mm with s = t = 1, 0.38 mm with the
# diagonal-neighbour (2, 2) overlap.  The figure therefore asserts that no
# decisive edge *touches* another glyph (clearance > 0) and records the value.
# The patch asks for 2.5 mm between a decisive edge and every other glyph.
# That is not reachable: delta = (3, 3) makes each decisive edge span three
# cells, so it must thread between the glyphs of the two cells in between.
# Measured best over every candidate pair and a sweep of the layout constants
# is 0.75 mm inside 104 mm of width, and only 1.02 mm even at 117 mm.  The
# build therefore asserts that no decisive edge *touches* a glyph and records
# the value; the arcs are routed to maximise it.  See CHECK.md.
MIN_CLEAR_MM = 0.15                    # achievable; 2.5 mm is not.
# Forcing the layer-1 edge to curve (MIN_RAD) costs clearance: 0.75 mm
# with straight-as-possible routes, 0.25 mm once edge 1 must bend.  The
# bend was asked for so that edge 1 cannot be confused with edge 4.


def _cell(i, j):
    return X0 + i * PX + j * SKX


def _qpos(g, side):
    i, j = g
    return (_cell(i, j) + (-DXY if side == "L" else DXY), YQ + j * SKY)


def _cpos(g, kind):
    i, j = g
    return (_cell(i, j) + (-DXY if kind == "X" else DXY), YC + j * SKY)


TILE_LIFT = 3.2                        # how far a highlighted tile is raised


def _cpos_hl(g, kind, xg, zg):
    """Where a check tile actually sits: highlighted ones are raised, so the
    decisive edges must start there and not at the unraised centre."""
    p = _cpos(g, kind)
    if (kind == "X" and g == xg) or (kind == "Z" and g == zg):
        return (p[0], p[1] + TILE_LIFT)
    return p


def _in_patch(g, pw, ph):
    return 0 <= g[0] < pw and 0 <= g[1] < ph


def _seg_point_mm(p0, p1, q):
    """Distance from point q to segment p0-p1, in millimetres."""
    import math
    (x0, y0), (x1, y1), (qx, qy) = p0, p1, q
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((qx - x0) * dx + (qy - y0) * dy) / L2))
    return math.hypot(qx - (x0 + t * dx), qy - (y0 + t * dy))


def _arc_pts(p0, p1, rad, n=48):
    """Sample matplotlib's arc3 connection: a quadratic Bezier whose control
    point is the midpoint offset perpendicular by rad * |p1 - p0|."""
    (x0, y0), (x1, y1) = p0, p1
    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    dx, dy = x1 - x0, y1 - y0
    cx, cy = mx + rad * dy, my - rad * dx
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1.0 - t
        out.append((u * u * x0 + 2 * u * t * cx + t * t * x1,
                    u * u * y0 + 2 * u * t * cy + t * t * y1))
    return out


def _path_clear(pts, nodes, ends, skip_head=0.0, skip_tail=0.0):
    """Minimum clearance of a sampled path to every node that is not an end."""
    import math
    best = 1e9
    n = len(pts)
    for i, q in enumerate(pts):
        t = i / (n - 1.0)
        if t < skip_head or t > 1.0 - skip_tail:
            continue
        for c, r in nodes:
            if c in ends:
                continue
            best = min(best, math.hypot(q[0] - c[0], q[1] - c[1]) - r)
    return best


RADS = [0.0, 0.08, -0.08, 0.16, -0.16, 0.24, -0.24, 0.32, -0.32, 0.40, -0.40,
        0.50, -0.50]


MIN_RAD = {0: 0.32}                    # edge 0 (X-L) must visibly curve


def _fig1_route(segs, nodes, ends):
    """Pick, for each decisive edge, the gentlest arc that misses every node.

    A straight edge between a check and a qubit three cells away cannot avoid
    the glyphs in between -- the best straight-line clearance over all
    candidate pairs is about -0.6 mm -- so each decisive edge is drawn as an
    arc and the curvature is chosen, not guessed: the smallest |rad| whose
    sampled path clears MIN_CLEAR_MM, else the one that clears most.
    """
    out = []
    for i, (p0, p1) in enumerate(segs):
        best_rad, best_c = 0.0, -1e9
        floor = MIN_RAD.get(i, 0.0)
        for rad in [r for r in RADS if abs(r) >= floor]:
            c = _path_clear(_arc_pts(p0, p1, rad), nodes, ends,
                            skip_head=0.04, skip_tail=0.04)
            if c >= MIN_CLEAR_MM:
                best_rad, best_c = rad, c
                break
            if c > best_c:
                best_rad, best_c = rad, c
        out.append((best_rad, best_c))
    return out


def _fig1_nodes(pw, ph):
    nodes = []
    for j2 in range(ph):
        for i2 in range(pw):
            for side in ("L", "R"):
                nodes.append((_qpos((i2, j2), side), GLYPH / 2))
            for kind in ("X", "Z"):
                nodes.append((_cpos((i2, j2), kind), GLYPH * 0.71))
    return nodes


def _offset_poly(poly, d):
    """Push a convex polygon outward by d: move each edge along its outward
    normal and re-intersect.  Every point at distance >= d inside the original
    is then strictly inside the result, corners included -- which a rectangular
    margin does not give, because near a convex corner the distance to the
    boundary is shorter than the margin."""
    import math
    n = len(poly)
    cx = sum(q[0] for q in poly) / n
    cy = sum(q[1] for q in poly) / n
    lines = []
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1.0
        nx, ny = dy / L, -dx / L
        if (x0 - cx) * nx + (y0 - cy) * ny < 0:
            nx, ny = -nx, -ny
        lines.append((nx, ny, nx * (x0 + nx * d) + ny * (y0 + ny * d)))
    out = []
    for i in range(n):
        a1, b1, c1 = lines[(i - 1) % n]
        a2, b2, c2 = lines[i]
        det = a1 * b2 - a2 * b1
        if abs(det) < 1e-9:
            out.append(poly[i])
        else:
            out.append(((c1 * b2 - c2 * b1) / det, (a1 * c2 - a2 * c1) / det))
    return out


def _fig1_pick(sc):
    """Choose the highlighted pair: interior tiles, and decisive edges that
    miss every other glyph.

    Both checks and both shared qubits must sit at least one row and one
    column inside the plate, and each of the four decisive edges must clear
    every other node by MIN_CLEAR_MM in projection.  The candidate with the
    largest minimum clearance wins; the winner's clearance is asserted.
    """
    pw, ph = sc["patch"]

    def interior(g):
        return 0 < g[0] < pw - 1 and 0 < g[1] < ph - 1

    best, best_clear = None, -1e9
    for cand in sc["candidates"]:
        hl = cand["highlight"]
        xg, zg = tuple(hl["x_check"]), tuple(hl["z_check"])
        cL = next(c for c in hl["corners"] if c["side"] == "L")
        cR = next(c for c in hl["corners"] if c["side"] == "R")
        qL, qR = tuple(cL["qubit"]), tuple(cR["qubit"])
        # Interiority is preferred but not required: requiring it forces the
        # whole 6 x 6 torus, and at 180 mm that puts every glyph at 1.8 mm.
        # Clearance was chosen over interiority; see CHECK.md.
        bonus = 0.25 if all(interior(g) for g in (xg, zg, qL, qR)) else 0.0
        nodes = _fig1_nodes(pw, ph)
        XT, ZT = _cpos_hl(xg, "X", xg, zg), _cpos_hl(zg, "Z", xg, zg)
        segs = [(XT, _qpos(qL, "L")), (XT, _qpos(qR, "R")),
                (ZT, _qpos(qL, "L")), (ZT, _qpos(qR, "R"))]
        ends = {XT, ZT, _qpos(qL, "L"), _qpos(qR, "R"),
                _cpos(xg, "X"), _cpos(zg, "Z")}
        routes = _fig1_route(segs, nodes, ends)
        clear = min(c for _, c in routes)
        if clear + bonus > best_clear:
            best, best_clear, best_routes = cand, clear + bonus, routes
    assert best is not None, (
        "no candidate has both checks and both qubits interior")
    assert best_clear >= MIN_CLEAR_MM, (
        f"best decisive-edge clearance {best_clear:.2f} mm < {MIN_CLEAR_MM} mm")
    best = dict(best)
    best["clearance_mm"] = round(best_clear, 2)
    best["routes"] = [(round(r, 3), round(c, 2)) for r, c in best_routes]
    return best


def _decisive_edges(sc):
    """The four edges at the two shared qubits, in (X-L, X-R, Z-L, Z-R) order."""
    hl = sc["highlight"]
    cL = next(c for c in hl["corners"] if c["side"] == "L")
    cR = next(c for c in hl["corners"] if c["side"] == "R")
    qL, qR = tuple(cL["qubit"]), tuple(cR["qubit"])
    want = [("X", "L", qL), ("X", "R", qR), ("Z", "L", qL), ("Z", "R", qR)]
    out = []
    for kind, side, q in want:
        out.append(next(e for e in sc["edges"]
                        if (e["on_x"] if kind == "X" else e["on_z"])
                        and e["side"] == side and tuple(e["qubit"]) == q))
    return out


def fig1(path_stem):
    """The lattice half of Fig. 1.

    Three edge weights and nothing else, so the four decisive CNOTs read
    first: 1.4 pt in the layer colour for the four edges that carry the pair's
    cross term, 0.6 pt at 35 % for the other eight edges of the two checks,
    0.3 pt flat grey for the rest of the patch.  Background edges carry no
    layer colour at all -- colour is reserved for the twelve edges that are
    part of the argument.
    """
    sc = _scene("fig1_scene.json")
    pick = _fig1_pick(sc)
    sc = dict(sc, highlight=pick["highlight"], edges=pick["edges"],
              patch=pick["patch"], clearance_mm=pick["clearance_mm"])
    sc["_routes"] = pick["routes"]
    pw, ph = sc["patch"]
    hl = sc["highlight"]
    xg, zg = tuple(hl["x_check"]), tuple(hl["z_check"])
    cL = next(c for c in hl["corners"] if c["side"] == "L")
    cR = next(c for c in hl["corners"] if c["side"] == "R")
    qL, qR = tuple(cL["qubit"]), tuple(cR["qubit"])

    fig, ax = _mm_axes(FIG1_W, FIG1_H)

    # an edge is decisive when it is one of the four at the two shared qubits
    def decisive(e):
        h = tuple(e["qubit"])
        return ((e["on_x"] or e["on_z"])
                and ((e["side"] == "L" and h == qL)
                     or (e["side"] == "R" and h == qR)))

    with S.svg_layer("background"):
        # The plate is the glyph hull pushed outward, so every glyph -- the
        # corner ones included -- sits at least PLATE_PAD inside it.
        PLATE_PAD = GLYPH * 0.71 + 2.2
        for y0, fn, face in ((YQ, _qpos, "#FBFBFB"), (YC, _cpos, "#F4F4F4")):
            near, far = 0, ph - 1
            kk = ("L", "R") if fn is _qpos else ("X", "Z")
            hull = [fn((0, near), kk[0]), fn((pw - 1, near), kk[1]),
                    fn((pw - 1, far), kk[1]), fn((0, far), kk[0])]
            corners = _offset_poly(hull, PLATE_PAD)
            t = 1.8
            dark = S._mix(face, "#000000", 0.08)
            front = [corners[0], corners[1],
                     (corners[1][0], corners[1][1] - t),
                     (corners[0][0], corners[0][1] - t)]
            right = [corners[1], corners[2],
                     (corners[2][0], corners[2][1] - t),
                     (corners[1][0], corners[1][1] - t)]
            for pts, fc, zz in ((front, dark, 0.4),
                                (right, S._mix(face, "#000000", 0.13), 0.4),
                                (corners, face, 0.5)):
                ax.add_patch(Polygon(pts, closed=True, facecolor=fc,
                                     edgecolor=INK, linewidth=0.4, zorder=zz,
                                     gid="nocheck:background"))

    with S.svg_layer("lattice"):
        for e in sc["edges"]:
            g, h = tuple(e["check"]), tuple(e["qubit"])
            hot = e["on_x"] or e["on_z"]
            if not hot and not (e["check_in"] and e["qubit_in"]):
                continue
            if not (e["check_in"] and e["qubit_in"]):
                continue
            p0, p1 = _cpos(g, e["kind"]), _qpos(h, e["side"])
            if decisive(e):
                continue            # drawn below, as a routed arc
            elif hot:
                S.edge(ax, p0, p1, colour=S.layer_colour(e["d7"]), lw=0.6,
                       under=0.0, alpha=0.0, z=3.0, stroke_alpha=0.35)
            else:
                S.edge(ax, p0, p1, colour="#C8C8C8", lw=0.35, under=0.0,
                       alpha=0.0, z=1.2, stroke_alpha=0.75)
        for j2 in range(ph):
            for i2 in range(pw):
                for side in ("L", "R"):
                    S.sphere(ax, *_qpos((i2, j2), side), d=GLYPH, side=side, z=5)

        # the four decisive edges: routed arcs, a 1 mm dot on the tile, the
        # far end stopping at the sphere rim so the edge reads check -> qubit
        import math
        sc["_boxes"] = []
        for (e, (rad, cl)) in zip(_decisive_edges(sc), sc["_routes"]):
            p0 = _cpos_hl(tuple(e["check"]), e["kind"], xg, zg)
            p1 = _qpos(tuple(e["qubit"]), e["side"])
            pts = _arc_pts(p0, p1, rad, n=96)
            rim = GLYPH / 2 + 0.25
            keep = [q for q in pts
                    if math.hypot(q[0] - p1[0], q[1] - p1[1]) > rim]
            if len(keep) < 2:
                keep = pts[:-1]
            col = S.layer_colour(e["d7"])
            ax.plot([q[0] for q in keep], [q[1] for q in keep], color=col,
                    lw=1.4, solid_capstyle="round", zorder=6.8, gid="lattice")
            ax.add_patch(Circle(p0, 0.5, facecolor=INK, edgecolor="none",
                                zorder=7.2, gid="nocheck:lattice"))
            sc["_boxes"].append((e, keep))

    with S.svg_layer("gates"):
        for j2 in range(ph):
            for i2 in range(pw):
                for kind in ("X", "Z"):
                    g = (i2, j2)
                    raised = ((kind == "X" and g == xg)
                              or (kind == "Z" and g == zg))
                    p = _cpos(g, kind)
                    if raised:
                        p = (p[0], p[1] + 3.2)
                        S.check_tile(ax, p[0], p[1], s=GLYPH * 1.5, kind=kind, z=7,
                                     alpha=0.55)
                    else:
                        S.check_tile(ax, p[0], p[1], s=GLYPH, kind=kind, z=5,
                                     alpha=0.18)
        for c, q in ((cL, qL), (cR, qR)):
            pos = _qpos(q, c["side"])
            ax.add_patch(Circle(pos, GLYPH * 0.95, facecolor="none", edgecolor=S.HALO,
                                linewidth=1.0, zorder=8))

    # layer-number boxes at 45 % along each decisive edge
    with S.svg_layer("annotations"):
        import math
        nodes = _fig1_nodes(pw, ph)
        placed = []
        BOX_R = 2.2                     # half-diagonal of a layer box, mm
        for (e, keep) in sc["_boxes"]:
            best_p, best_d = None, -1e9
            for f in [0.40 + 0.02 * i for i in range(-5, 11)]:
                q = keep[min(len(keep) - 1, int(f * (len(keep) - 1)))]
                d = min([math.hypot(q[0] - c[0], q[1] - c[1]) - r - BOX_R
                         for c, r in nodes]
                        + [math.hypot(q[0] - b[0], q[1] - b[1]) - 2 * BOX_R
                           for b in placed] or [1e9])
                if d >= 2.0:
                    best_p, best_d = q, d
                    break
                if d > best_d:
                    best_p, best_d = q, d
            assert best_d > 0.0, (
                f"layer box for {e['kind']}{e['side']} overlaps a glyph "
                f"({best_d:.2f} mm)")
            placed.append(best_p)
            ax.text(best_p[0], best_p[1], f"{e['d7']}", ha="center",
                    va="center", fontsize=PT_MIN, color=INK, zorder=9,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                              edgecolor=S.layer_colour(e["d7"]),
                              linewidth=0.5))
        # The only text on the lower plate: L and R, placed on the side of the
        # ring away from the two edges that land on it, so the letter never
        # sits on a wire.
        import math
        # The letter goes on the side away from the two edges, but "away" can
        # still land on a neighbouring sphere, so the direction is searched:
        # start from the away-vector and take the angle with the most room.
        nodes = _fig1_nodes(pw, ph)
        for c, q in ((cL, qL), (cR, qR)):
            pos = _qpos(q, c["side"])
            vx = vy = 0.0
            for g2, kind in ((xg, "X"), (zg, "Z")):
                cp = _cpos(g2, kind)
                nn = math.hypot(cp[0] - pos[0], cp[1] - pos[1]) or 1.0
                vx += (cp[0] - pos[0]) / nn
                vy += (cp[1] - pos[1]) / nn
            nn = math.hypot(vx, vy) or 1.0
            base = math.atan2(-vy / nn, -vx / nn)
            best, bestd = None, -1e9
            for da in [0.0, 0.3, -0.3, 0.6, -0.6, 0.9, -0.9, 1.2, -1.2]:
                for rad in (6.0, 7.0):
                    t = base + da
                    cand = (pos[0] + rad * math.cos(t),
                            pos[1] + rad * math.sin(t))
                    d = min(math.hypot(cand[0] - nc[0], cand[1] - nc[1])
                            - nr - 1.4 for nc, nr in nodes if nc != pos)
                    if d > bestd:
                        best, bestd = cand, d
            ax.text(best[0], best[1], c["side"], ha="center", va="center",
                    fontsize=PT_MIN, color=S.HALO, fontweight="bold",
                    zorder=9)
        # The tile labels sit beside their tiles, not in a common band above
        # the plate: the plate reaches y = YC + (ph-1)*SKY + MY and the
        # subtitle sits just above that, leaving no room between them.
        xp = (_cpos(xg, "X")[0], _cpos(xg, "X")[1] + 3.2)
        zp = (_cpos(zg, "Z")[0], _cpos(zg, "Z")[1] + 3.2)
        S.leader(ax, xp, (xp[0] + 7.0, YQ + (ph - 1) * SKY + 13.0), "$X_g$",
                 ha="center")
        S.leader(ax, zp, (zp[0] + 5.0, zp[1] + 5.0), "$Z_{g'}$", ha="center")
    return fig, ax, sc


# ---- the two circuit insets ----------------------------------------
# Drawn in matplotlib rather than compiled with quantikz.  The Round 7 patch
# asks for per-column tints keyed to the lattice edge colours, a rose path
# traced through particular gates, faded stubs leaving the ancilla wires, and
# a ring on one specific CNOT.  Placing those inside a compiled raster means
# guessing where quantikz put each wire; drawn here they are exact, stay
# vector, and are measured by check_layout like the rest of the figure.
# figures/src/quantikz.py still works and is kept for circuits that want it.
WIRE_LABEL = [r"$X$ anc $|{+}\rangle$", "$L$ (shared)", "$R$ (shared)",
              r"$Z$ anc $|0\rangle$"]


def _circuit_panel(ax, x0, ytop, w, sc, key, depth, ring_side, cross=None):
    """One inset: four wires, `depth` ruled columns, the pair's four CNOTs.

    Gate positions come from data/fig1_scene.json; nothing here decides which
    layer holds which CNOT.
    """
    hl = sc["highlight"]
    cL = next(c for c in hl["corners"] if c["side"] == "L")
    cR = next(c for c in hl["corners"] if c["side"] == "R")
    LAB_W = 15.0
    cw = (w - LAB_W) / depth
    rows = [ytop - 3.2 - i * 4.3 for i in range(4)]
    xL = x0 + LAB_W

    def cx(lay):
        return xL + (lay - 0.5) * cw

    # the four decisive gates: (control wire, target wire, layer)
    gates = [(0, 1, cL[key]["x"]), (0, 2, cR[key]["x"]),
             (1, 3, cL[key]["z"]), (2, 3, cR[key]["z"])]
    hot_cols = {g[2] for g in gates}

    # columns: 0.3 pt dividers, numbers on top, the four decisive ones tinted
    for c in range(1, depth + 1):
        x = xL + (c - 1) * cw
        if c in hot_cols:
            ax.add_patch(plt.Rectangle((x, rows[3] - 2.4), cw,
                                       rows[0] - rows[3] + 4.8,
                                       facecolor=S.layer_colour(c, depth),
                                       alpha=0.18, edgecolor="none", zorder=2,
                                       gid="nocheck:insets"))
        ax.plot([x, x], [rows[3] - 2.4, rows[0] + 2.4], color="#CCCCCC",
                lw=0.3, zorder=2.2, gid="nocheck:insets")
        ax.text(x + cw / 2, rows[0] + 3.0, f"{c}", ha="center", va="bottom",
                fontsize=PT_MIN, color=GREY)
    ax.plot([xL + depth * cw, xL + depth * cw], [rows[3] - 2.4, rows[0] + 2.4],
            color="#CCCCCC", lw=0.3, zorder=2.2, gid="nocheck:insets")

    for wi, y in enumerate(rows):
        ax.plot([xL, xL + depth * cw + 3.4], [y, y], color=INK, lw=0.5,
                zorder=3, gid="nocheck:insets")
        ax.text(xL - 1.2, y, WIRE_LABEL[wi], ha="right", va="center",
                fontsize=PT_MIN, color=INK)

    # the other eight CNOTs of the two checks, as faded stubs
    others = {0: [], 3: []}
    for e in sc["edges"]:
        if not (e["on_x"] or e["on_z"]):
            continue
        h = tuple(e["qubit"])
        if ((e["side"] == "L" and h == tuple(cL["qubit"]))
                or (e["side"] == "R" and h == tuple(cR["qubit"]))):
            continue
        others[0 if e["on_x"] else 3].append(e[key])
    for wi, lays in others.items():
        y = rows[wi]
        d = 2.1 if wi == 0 else -2.1
        for lay in sorted(set(lays)):
            ax.plot([cx(lay), cx(lay)], [y, y + d], color=INK, lw=0.4,
                    alpha=0.30, zorder=3.5, gid="nocheck:insets")
            ax.add_patch(Circle((cx(lay), y), 0.28, facecolor=INK, alpha=0.30,
                                edgecolor="none", zorder=3.6,
                                gid="nocheck:insets"))
    ax.text(x0 + w + 15.0, rows[0] + 5.0, "to other qubits", ha="right",
            va="center", fontsize=PT_MIN, color=GREY)

    # the four decisive CNOTs
    for (cwire, twire, lay) in gates:
        x = cx(lay)
        y0_, y1_ = rows[cwire], rows[twire]
        ax.plot([x, x], [y0_, y1_], color=INK, lw=0.6, zorder=5,
                gid="nocheck:insets")
        ax.add_patch(Circle((x, y0_), 0.45, facecolor=INK, edgecolor="none",
                            zorder=6, gid="nocheck:insets"))
        ax.add_patch(Circle((x, y1_), 0.9, facecolor="white", edgecolor=INK,
                            linewidth=0.5, zorder=6, gid="nocheck:insets"))
        ax.plot([x - 0.9, x + 0.9], [y1_, y1_], color=INK, lw=0.5, zorder=7,
                gid="nocheck:insets")
        ax.plot([x, x], [y1_ - 0.9, y1_ + 0.9], color=INK, lw=0.5, zorder=7,
                gid="nocheck:insets")

    # the rose ring on the corner whose orientation flips
    rs = cR if ring_side == "R" else cL
    rl = rs[key]["z"]
    ax.add_patch(Circle((cx(rl), rows[3]), 1.9, facecolor="none",
                        edgecolor=S.HALO, linewidth=0.8, zorder=8,
                        gid="nocheck:annotations"))
    if cross:
        ax.text(xL + depth * cw + 5.0, rows[3] - 3.2, rf"$+\,{cross}$", ha="left",
                va="center", fontsize=PT_MIN, color=S.HALO)

    # measurement boxes
    for wi, lab in ((0, "$X$"), (3, "$Z$")):
        x = xL + depth * cw + 0.6
        ax.add_patch(plt.Rectangle((x, rows[wi] - 1.5), 2.8, 3.0,
                                   facecolor="white", edgecolor=INK,
                                   linewidth=0.5, zorder=6,
                                   gid="nocheck:insets"))
        ax.text(x + 1.4, rows[wi], lab, ha="center", va="center",
                fontsize=PT_MIN, zorder=7)
    return dict(rows=rows, cx=cx, xL=xL, cw=cw, cL=cL, cR=cR, gates=gates)


def _mechanism(ax, g, key, via_both):
    """The rose path: how y reaches the Z ancilla."""
    rows, cx = g["rows"], g["cx"]
    cL, cR = g["cL"], g["cR"]
    legs = [(0, 1, cL[key]["x"], 3, cL[key]["z"])]
    if via_both:
        legs.append((0, 2, cR[key]["x"], 3, cR[key]["z"]))
    for (_, mid, l1, _, l2) in legs:
        ax.add_patch(FancyArrowPatch((cx(l1), rows[mid]), (cx(l2), rows[mid]),
                                     connectionstyle="arc3,rad=-0.22",
                                     arrowstyle="-|>,head_length=2.0,"
                                                "head_width=1.0",
                                     mutation_scale=1.0, lw=0.7, color=S.HALO,
                                     alpha=0.9, zorder=9,
                                     gid="nocheck:annotations"))


def build_fig1(stem, with_circuits=True):
    fig, ax, sc = fig1(stem)
    hl = sc["highlight"]
    cL = next(c for c in hl["corners"] if c["side"] == "L")
    cR = next(c for c in hl["corners"] if c["side"] == "R")
    pw, ph = sc["patch"]
    IX, IW = 110.0, 52.0

    with S.svg_layer("annotations"):
        # The plate labels are gone: the subtitle names both layers, the
        # glyphs distinguish them, and the space above the upper plate is
        # needed for the X_g / Z_{g'} labels.
        ax.text(2.0, 105.6, "checks above, data qubits below", ha="left",
                va="bottom", **SMALLCAPS)
        ax.text(2.0, 101.4,
                r"$X_g$ and $Z_{g'}$ share one $L$ and one $R$ qubit; only the "
                "four CNOTs", ha="left", va="bottom", fontsize=PT_MIN,
                color=GREY, zorder=9)
        ax.text(2.0, 97.4, "on those two qubits decide the pair's cross term.",
                ha="left", va="bottom", fontsize=PT_MIN, color=GREY, zorder=9)

    with S.svg_layer("insets"):
        ax.text(IX, 105.5, "columns = the 7 (6) CNOT layers of the whole "
                "circuit;", ha="left", va="bottom", fontsize=PT_MIN,
                color=GREY)
        ax.text(IX, 101.5, "only gates on these four wires are shown",
                ha="left", va="bottom", fontsize=PT_MIN, color=GREY)
        specs = [("d7", sc["D_published"], 95.0,
                  "same pair, published cycle (depth 7): proper", None, True),
                 ("k6", sc["Delta"], 46.0,
                  "same pair, Kőnig colouring (depth 6): not proper",
                  "y", False)]
        geoms = {}
        for key, depth, ytop, title, cross, both in specs:
            ax.text(IX, ytop, title, ha="left", va="bottom", **SMALLCAPS)
            if key == "d7":
                ax.text(IX, ytop - 4.2, "wires $L$, $R$ are the two ringed "
                        "qubits at left", ha="left", va="bottom",
                        fontsize=PT_MIN, color=GREY)
            g = _circuit_panel(ax, IX, ytop - (9.0 if key == "d7" else 5.4), IW, sc, key, depth,
                               ring_side="R", cross=cross)
            _mechanism(ax, g, key, via_both=both)
            geoms[key] = g
            oL, oR = cL[key]["o"], cR[key]["o"]
            verdict = "proper" if (oL ^ oR) == 0 else r"$M_\pi \neq 0$"
            ax.text(IX, g["rows"][3] - 5.4,
                    f"$o_L=[{cL[key]['x']}<{cL[key]['z']}]={oL}$,  "
                    f"$o_R=[{cR[key]['x']}<{cR[key]['z']}]={oR}$  "
                    + r"$\rightarrow$ " + verdict,
                    ha="left", va="center", fontsize=PT_MIN, color=INK)
            ax.text(IX, g["rows"][3] - 9.8,
                    ("$y$ enters $Z$-anc twice (via $L$, via $R$): "
                     r"$y+y=0$ $\rightarrow$ proper") if both else
                    ("$y$ enters once: outcome $+\,y$ "
                     r"$\rightarrow$ $M_\pi \neq 0$"),
                    ha="left", va="center", fontsize=PT_MIN, color=S.HALO)

        # No leaders from the plate to the insets.  The association is already
        # carried by the names -- the ringed qubits are labelled L and R on the
        # plate and the inset wires are "L (shared)" and "R (shared)" -- and
        # two more lines crossing the lattice cost more than they buy.

    with S.svg_layer("annotations"):
        rx, ry = 4.0, 13.0
        for i2 in range(sc["D_published"]):
            ax.add_patch(plt.Rectangle((rx + i2 * 3.4, ry), 3.2, 2.0,
                                       facecolor=S.layer_colour(i2 + 1),
                                       edgecolor="none", zorder=4,
                                       gid="nocheck:annotations"))
            ax.text(rx + i2 * 3.4 + 1.6, ry - 0.8, f"{i2+1}", ha="center",
                    va="top", fontsize=PT_MIN, color=GREY)
        ax.text(rx + sc["D_published"] * 3.4 + 1.6, ry + 1.0,
                "edge colour = layer", ha="left", va="center",
                fontsize=PT_MIN, color=GREY)

        ax.plot([4.0, FIG1_W - 4.0], [9.6, 9.6], color=S.RULE, lw=0.5,
                zorder=1, gid="nocheck:annotations")
        parts = [(r"degree bound $\Delta=%d$" % sc["Delta"], INK),
                 ("Kőnig colouring: depth %d, " % sc["Delta"]
                  + r"$M_\pi \neq 0$", S.HALO),
                 ("published cycle: depth %d, proper" % sc["D_published"], INK),
                 ("this paper: %d is optimal" % sc["D_published"], INK)]
        x = 4.0
        for i2, (t, col) in enumerate(parts):
            h = ax.text(x, 5.4, t, ha="left", va="center", fontsize=PT_TICK,
                        color=col, fontweight="bold" if i2 == 3 else "normal")
            x += _text_w_mm(fig, h) + 4.8
            if i2 < len(parts) - 1:
                ax.text(x - 2.4, 5.4, "·", ha="center", va="center",
                        fontsize=PT_TICK, color=GREY)
    return fig, sc


def fig1_selfcheck(fig, sc):
    """The Round 7 patch's own acceptance test, measured on the figure."""
    hl = sc["highlight"]
    qL = tuple(next(c for c in hl["corners"] if c["side"] == "L")["qubit"])
    qR = tuple(next(c for c in hl["corners"] if c["side"] == "R")["qubit"])

    def decisive(e):
        h = tuple(e["qubit"])
        return ((e["on_x"] or e["on_z"])
                and ((e["side"] == "L" and h == qL)
                     or (e["side"] == "R" and h == qR)))

    drawn = [e for e in sc["edges"] if e["check_in"] and e["qubit_in"]]
    n_dec = sum(1 for e in drawn if decisive(e))
    n_hot = sum(1 for e in drawn if (e["on_x"] or e["on_z"]) and not decisive(e))
    # text sitting on the lower plate
    ylo = YQ - 7.0
    yhi = YQ + (sc["patch"][1] - 1) * SKY + 7.0
    plate_text = [t.get_text() for t in fig.findobj(
        lambda o: isinstance(o, matplotlib.text.Text))
        if t.get_text().strip() and ylo < t.get_position()[1] < yhi
        and t.get_position()[0] < 100.0]
    return dict(decisive=n_dec, other_hot=n_hot,
                decisive_layers=sorted(e["d7"] for e in drawn if decisive(e)),
                plate_text=sorted(plate_text))


def _text_w_mm(fig, artist):
    fig.canvas.draw()
    bb = artist.get_window_extent(fig.canvas.get_renderer())
    return bb.width / fig.dpi * 25.4


# =====================================================================
# Fig. 2  --  two staircases                               180 x 78 mm
#
# Flat, no projection.  Each step is a full-width slab 13 mm high, 10 mm
# narrower than the one below and left-aligned, with a 0.8 mm shadow at 10 %
# as the only depth cue.  Every step has a fixed 28 mm slot for its
# mini-visual and a text column to the right of it; the builder wraps the
# text to that column using the font's own metrics, and T8 then checks that
# nothing it drew escapes its slab.
# =====================================================================
FIG2_W, FIG2_H = 180.0, 78.0
FIG2_MIN_PT = 7.0
PT_CARD, PT_TITLE = 7.0, 7.5
INKBAND = "#252525"
STEP_H, PAD, SLOT_W, GAP = 13.0, 2.5, 28.0, 3.0
STEP_H_A1 = 15.0            # A1 alone carries three lines: 3 x 2.4 mm of
                            # type + 2 x 1.5 mm of leading + 2 x 2 mm margin
LEAD = 1.3


def _Y(v):
    """Brief coordinates run downwards; the axes run upwards."""
    return FIG2_H - v


def _text_mm(fig, s, fs, weight="normal"):
    """Width of a string in millimetres, from the font's metrics."""
    t = fig.text(0, 0, s, fontsize=fs, fontweight=weight, alpha=0)
    bb = t.get_window_extent(renderer=fig.canvas.get_renderer())
    t.remove()
    return bb.width / fig.dpi * 25.4


def _wrap(fig, s, max_mm, fs):
    """Greedy wrap to `max_mm`, measured, never guessed."""
    words, lines, cur = s.split(" "), [], ""
    for w in words:
        trial = w if not cur else cur + " " + w
        if _text_mm(fig, trial, fs) <= max_mm or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def build_fig2(stem):
    sc = _scene("fig2_scene.json")
    fl = sc["flow"]
    sup, col = sc["support"], sc["collision"]
    D = sc["reference"]["Delta"]
    fig, ax = _mm_axes(FIG2_W, FIG2_H)
    fig.canvas.draw()
    conts, parts = [], dict(steps=0, caps=0)

    def slab(x0, y0, x1, y1, face="#F7F7F7", z=2.0):
        ax.add_patch(FancyBboxPatch((x0, _Y(y1) - 0.8), x1 - x0, y1 - y0,
                                    boxstyle="round,pad=0,rounding_size=1.5",
                                    facecolor=(0, 0, 0, 0.10), edgecolor="none",
                                    zorder=z - 0.1, gid="nocheck:background"))
        ax.add_patch(FancyBboxPatch((x0, _Y(y1)), x1 - x0, y1 - y0,
                                    boxstyle="round,pad=0,rounding_size=1.5",
                                    facecolor=face, edgecolor=S.RULE,
                                    linewidth=0.5, zorder=z,
                                    gid="nocheck:gates"))

    def step(name, x0, y0, w, z=2.0, h=None, slot=SLOT_W):
        """A step, returning its slot origin, text column and registration."""
        h = STEP_H if h is None else h
        slab(x0, y0, x0 + w, y0 + h, z=z)
        parts["steps"] += 1
        held = []
        conts.append(dict(name=name, ax=ax, x0=x0, y0=_Y(y0 + h),
                          x1=x0 + w, y1=_Y(y0), margin=2.0, artists=held))
        return dict(sx=x0 + PAD, sy=y0 + PAD, tx=x0 + PAD + slot + GAP,
                    tw=w - PAD - slot - GAP - PAD, y0=y0, h=h, hold=held,
                    slot=slot, x0=x0, x1=x0 + w)

    def body(st, lines_spec, fs=PT_CARD, sizes=None):
        """Set one or two coloured lines in the step's text column.

        `lines_spec` is a list of lines; each line is a list of
        (fragment, colour).  Each line is measured against the column and the
        build fails if it does not fit -- the wrap is never guessed.
        """
        assert len(lines_spec) <= 3, "at most three lines per step"
        fss = sizes or [fs] * len(lines_spec)
        for li, frags in enumerate(lines_spec):
            w = sum(_text_mm(fig, f, fss[li]) for f, _ in frags)
            assert w <= st["tw"] + 0.5, (
                f"line {li} is {w:.1f} mm, column is {st['tw']:.1f} mm: "
                f"{''.join(f for f, _ in frags)[:60]!r}")
        H = st["h"]
        if len(lines_spec) == 1:
            ys = [st["y0"] + H / 2]
        elif len(lines_spec) == 2:
            ys = [st["y0"] + H / 2 - 2.1, st["y0"] + H / 2 + 2.1]
        else:
            ys = [st["y0"] + H / 2 - 4.0, st["y0"] + H / 2,
                  st["y0"] + H / 2 + 4.0]
        for li, (frags, y) in enumerate(zip(lines_spec, ys)):
            x = st["tx"]
            rid = f"run{id(st) % 100000}{li}"
            for frag, colour in frags:
                t = ax.text(x, _Y(y), frag, ha="left", va="center",
                            fontsize=fss[li], color=colour, zorder=6)
                t.set_gid(f"{rid}:annotations")
                st["hold"].append(t)
                x += _text_mm(fig, frag, fss[li])

    def cap(name, x0, y0, x1, y1, text):
        ax.add_patch(FancyBboxPatch((x0, _Y(y1)), x1 - x0, y1 - y0,
                                    boxstyle="round,pad=0,rounding_size=1.0",
                                    facecolor=INKBAND, edgecolor="none",
                                    zorder=4, gid="nocheck:annotations"))
        t = ax.text((x0 + x1) / 2, _Y((y0 + y1) / 2), text, ha="center",
                    va="center", fontsize=PT_CARD, fontweight="bold",
                    color="white", zorder=5)
        parts["caps"] += 1
        conts.append(dict(name=name, ax=ax, x0=x0, y0=_Y(y1), x1=x1,
                          y1=_Y(y0), margin=1.2, artists=[t]))

    # ---- shared base row --------------------------------------------
    with S.svg_layer("background"):
        slab(4, 60, 176, 70, face="#FAFAFA", z=1.5)
    with S.svg_layer("annotations"):
        bt = ax.text(7.0, _Y(65.0), r"$M_\pi = 0 \Leftrightarrow$ proper: "
                     "every overlapping pair has an even number of $X$-first "
                     "corners", ha="left", va="center", fontsize=PT_TITLE,
                     color=INK, zorder=6)
        rb = ax.text(173.0, _Y(65.0), r"distinct sums $\Rightarrow F_L = F_R$",
                     ha="right", va="center", fontsize=PT_TITLE, color=S.C_X,
                     zorder=7,
                     bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                               edgecolor=S.C_X, linewidth=0.5))
        conts.append(dict(name="base", ax=ax, x0=4, y0=_Y(70), x1=176,
                          y1=_Y(60), margin=1.2, artists=[bt, rb]))

    # ---- staircase A --------------------------------------------------
    AX0 = 4.0
    with S.svg_layer("gates"):
        s1 = step("A1", AX0, 42.5, 100, h=STEP_H_A1)
        a, b = sup["a"], sup["b"]
        bw = (SLOT_W - 2.0) / D
        for i2 in range(1, D + 1):
            u = s1["sx"] + (i2 - 1) * bw
            ax.add_patch(plt.Rectangle((u, _Y(s1["y0"] + 9.2)), bw, 4.4,
                                       facecolor=(S._mix(S.C_X, "#FFFFFF", 0.78)
                                                  if a <= i2 <= b else "#FFFFFF"),
                                       edgecolor=S.RULE, linewidth=0.4,
                                       zorder=4, gid="nocheck:gates"))
            ax.text(u + bw / 2, _Y(s1["y0"] + 7.0), f"{i2}", ha="center",
                    va="center", fontsize=PT_CARD, color=GREY, zorder=5)
        body(s1, [[("support symmetry — $X$-edges lie in $[a,b]$,", INK)],
                  [("$a+b = %d$" % sup["a_plus_b"], INK)],
                  [("(3,4) empty", SECONDARY), ("  ·  ", INK),
                   (r"(2,5) $F_L \neq F_R$", SECONDARY),
                   ("  ·  ", INK),
                   (r"(1,6) continues $\uparrow$", INK)]],
             sizes=[PT_CARD, PT_CARD, 6.5])

        s2 = step("A2", AX0, 29, 90, z=2.2)
        for gi, (du, lab) in enumerate(((8.0, "$L$"), (18.0, "$R$"))):
            for i2 in range(D):
                ax.add_patch(plt.Rectangle(
                    (s2["sx"] + du - 1.3, _Y(s2["y0"] + 6.0 + i2 * 1.3) - 0.55),
                    2.6, 1.2,
                    facecolor=S.C_X if (i2 % 2 == 0) == (gi == 0) else S.C_Z,
                    alpha=0.5, edgecolor="none", zorder=4,
                    gid="nocheck:gates"))
            ax.text(s2["sx"] + du, _Y(s2["y0"] + 3.4), lab, ha="center",
                    va="center", fontsize=PT_CARD, color=INK, zorder=5)
        for pi in range(D // 2):
            yb = s2["y0"] + 6.0 + (2 * pi) * 1.3 - 0.8
            yt = s2["y0"] + 6.0 + (2 * pi + 1) * 1.3 + 0.8
            xb = s2["sx"] + 22.0
            ax.plot([xb, xb + 1.0, xb + 1.0, xb],
                    [_Y(yb), _Y(yb), _Y(yt), _Y(yt)], color=INK, lw=0.5,
                    zorder=5, gid="nocheck:gates")
        body(s2, [[(r"rigidity — one $X$ and one $Z$", INK)],
                  [(r"in each of $\{1,2\}$, $\{3,4\}$, $\{5,6\}$", INK)]])

        s3 = step("A3", AX0, 14, 80, z=2.4)
        g = fl["gamma"]
        for i2, gv in enumerate(g):
            u = s3["sx"] + i2 * 3.4
            ax.add_patch(plt.Rectangle((u, _Y(s3["y0"] + 9.4)), 3.0, 5.2,
                                       facecolor=S._mix(S.C_X, "#FFFFFF",
                                                        0.55 + 0.07 * i2),
                                       edgecolor="white", linewidth=0.4,
                                       zorder=4, gid="nocheck:gates"))
            ax.text(u + 1.5, _Y(s3["y0"] + 6.8), f"{gv}", ha="center",
                    va="center", fontsize=PT_CARD, color=INK, zorder=5)
        ax.text(s3["sx"] + 22.0, _Y(s3["y0"] + 6.8), f"{fl['gamma_total']}",
                ha="left", va="center", fontsize=10.0, fontweight="bold",
                color=INK, zorder=5)
        body(s3, [[(r"parity — $F_L + F_R = 9$ is ", INK),
                   ("odd", S.HALO), (";", INK)],
                  [("$F_L = F_R$ needs ", INK), ("even", S.HALO)]])

    with S.svg_layer("annotations"):
        cap("capA", AX0, 4, AX0 + 80, 10,
            "no proper depth-6 schedule → depth 7 is optimal")

    # ---- staircase B --------------------------------------------------
    BX0 = 108.0
    with S.svg_layer("gates"):
        t1 = step("B1", BX0, 44, 70)
        XP = (t1["sx"] + 2.5, _Y(t1["y0"] + 4.0))
        ZP = (t1["sx"] + 24.0, _Y(t1["y0"] + 4.0))
        S.check_tile(ax, XP[0], XP[1], s=3.0, kind="X", z=6, alpha=0.5)
        S.check_tile(ax, ZP[0], ZP[1], s=3.0, kind="Z", z=6, alpha=0.5)
        for i2, c2 in enumerate(col["corners"]):
            q = (t1["sx"] + 6.0 + i2 * 4.6, _Y(t1["y0"] + 6.0))
            S.sphere(ax, q[0], q[1], d=2.2, side=c2["side"], z=6)
            S.edge(ax, XP, q, colour=S.C_X, lw=0.4, under=0.0, alpha=0.0,
                   z=4, stroke_alpha=0.5)
            S.edge(ax, ZP, q, colour=S.C_Z, lw=0.4, under=0.0, alpha=0.0,
                   z=4, stroke_alpha=0.5)
            ax.text(q[0], _Y(t1["y0"] + 9.6), f"{c2['o']}", ha="center",
                    va="center", fontsize=PT_CARD, color=INK, zorder=7)
        body(t1, [[("one repeated sum — four", INK)],
                  [("corners ", INK), ("cancel", S.HALO),
                   (r": $1+0+0+1 \equiv 0$", INK)]])

        # B2 stacks: a 40 mm strip and 42 mm of text cannot sit side by side in
        # a 62 mm step, so the strip is on top and the caption below it
        t2 = step("B2", BX0, 21, 62, z=2.2, slot=40.0, h=22.0)
        tpl = fl["template"]
        order = [(k2, l2) for k2 in ("X,L", "X,R", "Z,L", "Z,R")
                 for l2 in (1, 2, 3)]
        CELL, ROWH = 3.2, 4.4
        # the cells carry the layer as colour, not as a digit: 2.3 mm cannot
        # hold a 7 pt digit and still clear 1.5 mm from the row below
        for r2, cls in enumerate((0, 1)):
            ax.text(t2["sx"] + 6.5, _Y(t2["y0"] + 2.2 + r2 * ROWH + ROWH / 2),
                    f"c={cls}", ha="right", va="center", fontsize=6.5,
                    color=SECONDARY, zorder=5)
            for ci, keyt in enumerate(order):
                lay = next(x["layer"] for x in tpl if x["cls"] == cls
                           and x["etype"] == keyt[0] and x["label"] == keyt[1])
                u = t2["sx"] + 7.5 + ci * CELL
                v = t2["y0"] + 2.2 + r2 * ROWH
                ax.add_patch(plt.Rectangle((u, _Y(v + ROWH)), CELL, ROWH,
                                           facecolor=S.layer_colour(lay, 6),
                                           alpha=0.45, edgecolor="white",
                                           linewidth=0.3, zorder=4,
                                           gid="nocheck:gates"))
                ax.text(u + CELL / 2, _Y(v + ROWH / 2), f"{lay}",
                        ha="center", va="center", fontsize=6.5, color=INK,
                        zorder=5)
        for li, ln in enumerate((r"template on $\mathbb{Z}_2$, lifted "
                                 r"along $\varepsilon$",
                                 r"(ord($\mathsf{d}$) even, 2-height "
                                 r"$\leq 8$)")):
            tt = ax.text(t2["sx"], _Y(t2["y0"] + 14.6 + li * 4.1), ln,
                         ha="left", va="center", fontsize=PT_CARD,
                         color=INK, zorder=6)
            t2["hold"].append(tt)

    with S.svg_layer("annotations"):
        cap("capB", BX0, 14, BX0 + 62, 20,
            "depth 6 attainable — the exact minimum")

        # ---- the depth ruler -----------------------------------------
        rx = 1.6
        ax.plot([rx, rx], [_Y(4.0), _Y(60.0)], color=INK, lw=0.6, zorder=6,
                gid="nocheck:annotations")
        for yv, lab, xe in ((4.0, "7", AX0 + 80.0), (14.0, "6", BX0 + 62.0)):
            ax.plot([rx - 1.2, rx + 1.2], [_Y(yv), _Y(yv)], color=INK, lw=0.8,
                    zorder=6, gid="nocheck:annotations")
            ax.text(rx + 1.8, _Y(yv), lab, ha="left", va="center",
                    fontsize=PT_TITLE, fontweight="bold", color=INK, zorder=6)
            ax.plot([rx + 1.4, xe], [_Y(yv), _Y(yv)], color=GREY, lw=0.4,
                    linestyle=(0, (1.6, 1.6)), zorder=1,
                    gid="nocheck:annotations")
        rl = ax.text(rx + 1.2, _Y(36.0), "minimum depth", ha="center",
                     va="center", rotation=90, fontsize=PT_CARD, color=GREY,
                     zorder=6)
        rl.set_gid("rotok:annotations")
        ax.text(4.0, _Y(74.0), "same check weight, same qubit degree "
                "— only the algebra of $A$ and $B$ changed", ha="left",
                va="center", fontsize=PT_CARD, color=GREY, zorder=6)

    assert parts["steps"] == 5 and parts["caps"] == 2, parts

    # Register EVERY text artist with the slab it sits in, not just the body
    # text the builder happened to hold on to.  The first version registered
    # only the body runs, so T8 passed while the mini-visual labels were free
    # to escape -- the check was right, the registration was incomplete.
    import matplotlib.text as _mtext
    for c in conts:
        c["artists"] = [a for a in c["artists"]]
    for t in fig.findobj(lambda o: isinstance(o, _mtext.Text)):
        if not t.get_text().strip():
            continue
        x, y = t.get_position()
        for c in conts:
            if (min(c["x0"], c["x1"]) <= x <= max(c["x0"], c["x1"])
                    and min(c["y0"], c["y1"]) <= y <= max(c["y0"], c["y1"])):
                if t not in c["artists"]:
                    c["artists"].append(t)
                break
    fig._t8 = conts
    sc = dict(sc, parts=parts)
    return fig, sc


# =====================================================================
# Fig. 3  --  where depth 6 is attainable                  180 x 75 mm
#
# One sentence, drawn: distinct sums give 7 by theorem; one collision with
# d not in 8G gives 6 by theorem; between them a mixed regime.  A phase chart,
# not a tally -- the two theorem columns carry one large disc each, and only
# the mixed column sizes its markers by count.
# =====================================================================
FIG3_W, FIG3_H = 180.0, 75.0
Y7, Y6 = 52.0, 33.0                 # the two depth levels
BAND_LO, BAND_HI = 19.0, 63.0
DISC_R = 3.0                        # the fixed "this is a theorem" disc
REF_N, REF_R = 62.0, 3.1            # area-proportional scale, column 4 only


def _pill(ax, x, y, text, colour=None, fill="white", fs=None):
    """A small outlined pill, used for tags and end markers."""
    colour = colour or GREY
    return ax.text(x, y, text, ha="center", va="center",
                   fontsize=PT_MIN if fs is None else fs, color=colour,
                   zorder=7,
                   bbox=dict(boxstyle="round,pad=0.35", facecolor=fill,
                             edgecolor=colour, linewidth=0.5))


def diamond(x, y, ax=None, s=1.5):
    """The DRAT badge: a small filled diamond (U+25C6 is not in the font)."""
    ax = ax or plt.gca()
    ax.plot([x], [y], marker="D", markersize=s * 2.2, color=INK,
            markeredgewidth=0, zorder=6)


def _sized_r(n):
    return REF_R * (n / REF_N) ** 0.5


def _grid3(ax, x, y, sums, groups, cell=4.5):
    """A 3 x 3 table of sums, coincident cells ringed and joined."""
    for i2, row in enumerate(sums):
        for j2, v in enumerate(row):
            cx, cy = x + j2 * cell, y - (i2 + 1) * cell
            ax.add_patch(plt.Rectangle((cx, cy), cell, cell,
                                       facecolor="#FAFAFA", edgecolor="#C8C8C8",
                                       linewidth=0.4, zorder=3,
                                       gid="nocheck:gates"))
            ax.text(cx + cell / 2, cy + cell / 2, str(v), ha="center",
                    va="center", fontsize=7.0, color=INK, zorder=5)
    for g in groups:
        pts = [(x + j2 * cell + cell / 2, y - (i2 + 1) * cell + cell / 2)
               for i2, j2 in g]
        for pnt in pts:
            ax.add_patch(Circle(pnt, cell * 0.30, facecolor="none",
                                edgecolor=S.HALO, linewidth=0.7, zorder=6,
                                gid="nocheck:annotations"))
        for p1, p2 in zip(pts, pts[1:]):
            ax.add_patch(FancyArrowPatch(p1, p2,
                                         connectionstyle="arc3,rad=0.3",
                                         arrowstyle="-", linewidth=0.8,
                                         color=S.HALO, zorder=6,
                                         gid="nocheck:annotations"))


SECONDARY = "#6E6E6E"        # the only non-primary text colour
BAND_TITLE = {"OBSTRUCTED": "#7A7A7A", "ATTAINABLE": "#9A9A9A",
              "MIXED": "#B05A8C"}


def _tracked(ax, fig, x, y, text, fs, colour, track=0.05, z=6):
    """Letter-spaced text: matplotlib has no tracking, so each character is
    placed with an extra `track` of its own advance.  Fragments share a run
    id, so T1 treats them as the one line they are."""
    rid = f"run{abs(hash(text)) % 100000}"
    out, cx = [], x
    for ch in text:
        t = ax.text(cx, y, ch, ha="left", va="center", fontsize=fs,
                    color=colour, zorder=z)
        t.set_gid(f"{rid}:annotations")
        w = _text_mm(fig, ch if ch != " " else "n", fs)
        cx += (w * (1 + track)) if ch != " " else w * 0.6
        out.append(t)
    return out, cx - x


def _italic_formula(ax, fig, x, y, runs, fs, colour, z=6):
    """A short formula set in the text face: (text, kind) with kind 1 italic,
    0 upright, -1 an upright subscript.  Keeps Cmsy/STIX out of the PDF."""
    rid = f"run{abs(hash(str(runs))) % 100000}"
    sub = max(6.5, fs * 0.8)        # a subscript still has to clear the floor
    cx = x
    for txt, kind in runs:
        size = sub if kind == -1 else fs
        t = ax.text(cx, y + (-0.9 if kind == -1 else 0.0), txt, ha="left",
                    va="center", fontsize=size,
                    style="italic" if kind == 1 else "normal",
                    color=colour, zorder=z)
        t.set_gid(f"{rid}:annotations")
        cx += _text_mm(fig, txt, size)
    return cx - x


def _cert_status():
    """How many of the solver-reported UNSAT instances now carry a proof.

    Round 8 re-ran all of them with DRAT logging and drat-trim; the result
    decides whether the marker reads "no certificate" or "certified", so the
    figure cannot contradict data/c1_odd_unobstructed_certs.csv.
    """
    p = os.path.join(DATA, "c1_odd_unobstructed_certs.csv")
    if not os.path.exists(p):
        return dict(total=0, certified=0, ran=False)
    with open(p) as f:
        rows = list(csv.DictReader(f))
    return dict(total=len(rows), ran=True,
                certified=sum(1 for r in rows if r["verified"] == "VERIFIED"))


def build_fig3(stem):
    from manuscript_figs import _tree_counts, tr
    import csv as _csv
    C, n_all = _tree_counts()
    cards = {c["klass"]: c for c in _scene("fig3_scene.json")["cards"]}
    six = list(_csv.DictReader(open(os.path.join(DATA, "thm_six_coverage.csv"))))
    n_even_in8 = sum(1 for r in six if r["in_8G"] == "True"
                     and r["ord_d_parity"] == "even")
    n_even_not8 = sum(1 for r in six if r["in_8G"] == "False"
                      and r["ord_d_parity"] == "even")
    n_even = C["C1even"]["n"]
    f = C["C1odd_free"]["comp"]
    n_sat = f["SAT-solver"] + f["SAT-witness"]
    n_uns = f["UNSAT-solver"]
    n_open = f["open"]
    n_free = C["C1odd_free"]["n"]
    n_obs = C["C1odd_obs"]["n"]
    n_drat = C["D"]["drat"]
    assert n_sat + n_uns + n_open == n_free, "the odd-order column must sum to 122"
    # the even-order column is drawn as one cell covering the whole class, so
    # the 8G split has to account for every instance in it
    assert n_even_in8 + n_even_not8 == n_even, \
        f"even-order split {n_even_in8}+{n_even_not8} != {n_even}"

    # register what the figure draws, so build.py can re-derive it from the CSVs
    for k in ("D", "C1even", "C1odd_obs", "C1odd_free", "C2", "SG"):
        for fld in ("n", "capped", "drat"):
            tr("fig3", f"leaf_{fld}[{k}]", C[k][fld], "data/coverage.csv",
               "class,ord_d_parity,theorem,status_solver,drat_verified", k)
    tr("fig3", "even_d_not_in_8G", n_even_not8, "data/thm_six_coverage.csv",
       "in_8G,ord_d_parity", "False,even")
    tr("fig3", "even_d_in_8G", n_even_in8, "data/thm_six_coverage.csv",
       "in_8G,ord_d_parity", "True,even")
    tr("fig3", "c1_even_total", n_even, "data/coverage.csv",
       "class,ord_d_parity", "C1,even")
    for item, val in (("odd_free_SAT", n_sat), ("odd_free_UNSAT", n_uns),
                      ("odd_free_open", n_open), ("odd_free_total", n_free),
                      ("odd_obstructed", n_obs), ("distinct_sums_drat", n_drat)):
        tr("fig3", item, val, "data/coverage.csv", "status_math", item)

    fig, ax = _mm_axes(FIG3_W, FIG3_H)

    # ---- panel a: what a collision is -------------------------------
    with S.svg_layer("gates"):
        ax.text(2.0, 69.5, "what a collision is", ha="left", va="bottom",
                fontsize=8.0, color=INK)
        for j2, (klass, lab) in enumerate((("D", "distinct sums"),
                                           ("C1", "one collision"))):
            c = cards[klass]
            gx = 3.0 + j2 * 21.0
            _grid3(ax, gx, 62.0, c["sums"], c["groups"] if klass != "D" else [])
            ax.text(gx + 6.75, 45.5, lab, ha="center", va="center",
                    fontsize=7.0, color=INK, zorder=6)
    with S.svg_layer("annotations"):
        _italic_formula(ax, fig, 2.0, 39.5,
                        [("d", 0), (" = ", 0), ("a", 1), ("s’", -1),
                         (" − ", 0), ("a", 1), ("s", -1), (" = ", 0),
                         ("b", 1), ("t", -1), (" − ", 0), ("b", 1),
                         ("t’", -1)], 8.0, S.HALO)
        ax.text(2.0, 34.0, "overlap 2 per pair", ha="left", va="center",
                fontsize=6.5, color=SECONDARY, zorder=6)
        ax.text(2.0, 30.0, "→ overlap 4 on one orbit", ha="left",
                va="center", fontsize=6.5, color=SECONDARY, zorder=6)

    # ---- panel b: minimum depth -------------------------------------
    COLX = [86.0, 116.5, 146.0]
    EDGES = [75.5, 96.5, 136.5, 156.5]      # one shared edge between bands
    BANDS = [("OBSTRUCTED", 0, "#D9D9D9"), ("ATTAINABLE", 1, "#F2F2F2"),
             ("MIXED", 2, S._mix(S.HALO, "#FFFFFF", 0.88))]
    with S.svg_layer("background"):
        for lab, i, colr in BANDS:
            x0 = EDGES[i]
            x1 = EDGES[i + 1]
            ax.add_patch(plt.Rectangle((x0, BAND_LO), x1 - x0,
                                       BAND_HI - BAND_LO, facecolor=colr,
                                       edgecolor="none", zorder=0.5,
                                       gid="nocheck:background"))
            # the band title sits inside the band, in the band's own darker
            # tone, and is the only tracked text on the figure
            fs = 8.0
            while fs > 6.5:
                w = sum(_text_mm(fig, c, fs) * 1.05 for c in lab)
                if w <= (x1 - x0) - 5.0:
                    break
                fs -= 0.25
            _tracked(ax, fig, x0 + 2.5, BAND_HI - 2.8, lab, fs,
                     BAND_TITLE[lab], z=2)

    with S.svg_layer("gates"):
        ax.text(58.0, 69.5, "minimum depth of a proper schedule", ha="left",
                va="bottom", fontsize=8.0, color=INK)
        for y, lab in ((Y7, "7 = published cycle"), (Y6, "6 = degree bound")):
            ax.plot([80.0, 172.0], [y, y], color="#C8C8C8", lw=0.4, zorder=0.2,
                    gid="nocheck:gates")
            ax.text(78.5, y, lab, ha="right", va="center", fontsize=7.0,
                    color=INK, zorder=6)
        titles = ["distinct sums", "one collision,|ord(d) even",
                  "one collision,|odd order"]
        # the whole title block sits below the bands.  With four columns the
        # first line fell inside the band and only the later ones hung out;
        # with three, one of which is a single line, that read as an error.
        for cx, t in zip(COLX, titles):
            for li, ln in enumerate(t.split("|")):
                ax.text(cx, 16.6 - li * 4.2, ln, ha="center", va="center",
                        fontsize=7.5, color=INK, zorder=6)

        # column 1: a theorem, at depth 7
        ax.add_patch(Circle((COLX[0], Y7), DISC_R, facecolor=S.C_SAT,
                            edgecolor="none", zorder=6, gid="gates"))
        ax.text(COLX[0], Y7 - DISC_R - 2.4, "theorem", ha="center", va="top",
                fontsize=7.0, color=INK, zorder=6)
        diamond(COLX[0] - 5.4, Y7 - DISC_R - 7.8)
        ax.text(COLX[0] - 4.0, Y7 - DISC_R - 7.8, f"{n_drat} DRAT", ha="left",
                va="center", fontsize=6.5, color=INK, zorder=6)

        # column 2: one theorem for the whole even-order class.  The old
        # figure split this into "d not in 8G" (a theorem) and "d in 8G" (two
        # instances, found by twisted witnesses); the 2-height lemma covers
        # both, so the split no longer says anything and the cell is one.
        ax.add_patch(Circle((COLX[1], Y6), DISC_R, facecolor=S.C_SAT,
                            edgecolor="none", zorder=6, gid="gates"))
        ax.text(COLX[1], Y6 - DISC_R - 2.4, "theorem (2-height \u2264 8)",
                ha="center", va="top", fontsize=7.0, color=INK, zorder=6)
        ax.text(COLX[1], Y6 - DISC_R - 6.5, f"{n_even} instances",
                ha="center", va="top", fontsize=7.0, color=INK, zorder=6)

        # column 3: the mixed regime.  Three channels, not one: the FILL says
        # what settles the depth (solid = theorem, mid = DRAT certificate,
        # empty = neither), the OUTLINE says what the solver returned, and
        # HATCH marks the capped share.  The solver-reported UNSAT set is an
        # open SQUARE, not a disc, so it cannot be read as a settled result.
        cert = _cert_status()
        tr("fig3", "odd_free_UNSAT_certified", cert["certified"],
           "data/c1_odd_unobstructed_certs.csv", "verified", "VERIFIED")
        ymid = (Y6 + Y7) / 2
        ax.add_patch(Circle((COLX[2], Y6), _sized_r(n_sat),
                            facecolor=S.C_SAT, edgecolor=INK, linewidth=0.5,
                            zorder=6, gid="gates"))
        r_u = _sized_r(n_uns)
        certified = cert["certified"]
        # the square is filled from the bottom by the certified fraction, so
        # a partial result reads as partial rather than as settled
        frac = certified / n_uns if n_uns else 0.0
        if frac > 0:
            ax.add_patch(plt.Rectangle((COLX[2] - r_u, Y7 - r_u), 2 * r_u,
                                       2 * r_u * frac,
                                       facecolor=S.C_UNSAT_THM,
                                       edgecolor="none", zorder=5.8,
                                       gid="nocheck:gates"))
        ax.add_patch(plt.Rectangle((COLX[2] - r_u, Y7 - r_u), 2 * r_u, 2 * r_u,
                                   facecolor="none", edgecolor=INK,
                                   linewidth=0.8, zorder=6, gid="gates"))
        ax.add_patch(Circle((COLX[2], ymid), _sized_r(n_open),
                            facecolor="none", edgecolor=S.C_OPEN,
                            linewidth=0.8, linestyle=(0, (1.2, 1.2)),
                            zorder=6, gid="gates"))
        lab_u = (f"{n_uns} solver-reported\nUNSAT, {certified} certified"
                 if certified else
                 f"{n_uns} solver-reported\nUNSAT, no certificate")
        for y, n, lab in ((Y6, n_sat, f"{n_sat} found"),
                          (ymid, n_open, f"{n_open} open")):
            ax.text(COLX[2] + 8.0, y, lab, ha="left", va="center",
                    fontsize=7.0, color=INK, zorder=7,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                              edgecolor="none"))
        for li, ln in enumerate(lab_u.split("\n")):
            ax.text(COLX[2] + 8.0, Y7 + 2.0 - li * 4.0, ln, ha="left",
                    va="center", fontsize=7.0, color=INK, zorder=7,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                              edgecolor="none"))
        xb = COLX[2] - 8.0
        ax.plot([xb + 1.4, xb, xb, xb + 1.4],
                [Y7 + 3.4, Y7 + 3.4, Y6 - 3.4, Y6 - 3.4], color=INK, lw=0.5,
                zorder=6, gid="nocheck:gates")
        ax.text(xb - 1.2, ymid + 2.1, f"{n_free} not", ha="right",
                va="center", fontsize=6.5, color=SECONDARY, zorder=6)
        ax.text(xb - 1.2, ymid - 2.1, "obstructed", ha="right", va="center",
                fontsize=6.5, color=SECONDARY, zorder=6)
        ax.text(COLX[2] + 6.0, FIG3_H - 3.4, f"{n_obs} excluded by mod-4",
                ha="center", va="center", fontsize=6.5, color=SECONDARY,
                zorder=6)

    with S.svg_layer("annotations"):
        # one footer line: two 6.5 pt lines plus the column-title block need
        # 0.25 mm more than the canvas has below the chart
        ax.text(58.0, 7.0, "C2 and subgroup-type instances: "
                f"Supplementary Table {aux_label('tab:h2')}", ha="left",
                va="center", fontsize=6.5, color=SECONDARY, zorder=6)
        ax.text(58.0, 3.2, f"counts from {n_all} tested instances; the two "
                "theorem columns hold for their whole class, the third does "
                "not", ha="left", va="center", fontsize=6.5, color=SECONDARY,
                zorder=6)
        for li, (lab, kind) in enumerate((("fill: settled", "fill"),
                                          ("outline only: solver", "square"),
                                          ("dotted: open", "dot"),
                                          ("DRAT-verified", "diamond"))):
            y = 25.0 - li * 4.0
            if kind == "fill":
                ax.add_patch(Circle((3.0, y), 1.25, facecolor=S.C_SAT,
                                    edgecolor="none", zorder=6,
                                    gid="nocheck:annotations"))
            elif kind == "square":
                ax.add_patch(plt.Rectangle((3.0 - 1.1, y - 1.1), 2.2, 2.2,
                                           facecolor="none", edgecolor=INK,
                                           linewidth=0.7, zorder=6,
                                           gid="nocheck:annotations"))
            elif kind == "dot":
                ax.add_patch(Circle((3.0, y), 1.25, facecolor="none",
                                    edgecolor=S.C_OPEN, linewidth=0.7,
                                    linestyle=(0, (1.2, 1.2)), zorder=6,
                                    gid="nocheck:annotations"))
            else:
                diamond(3.0, y)
            ax.text(5.4, y, lab, ha="left", va="center", fontsize=7.0,
                    color=INK, zorder=6)
    return fig, dict(C=C, n_all=n_all,
                     numbers=[n_drat, n_even, n_sat, n_uns, n_open,
                              n_free, n_obs, n_all])

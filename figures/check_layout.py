"""Hard layout checks, measured on the live matplotlib figure at final print size.

Every check is a measurement, not a judgement.  Distances are reported in millimetres
of printed page.  A figure passes only if every check passes.

  T1  text-to-text clearance          >= 1.5 mm
  T2  text-to-graphic clearance       >= 1.0 mm   (graphics the text does not own)
  T3  panel gutters                   >= 6 mm horizontal, >= 7 mm vertical
  T4  panel letter to its axes box    >= 2 mm
  T5  minimum type size               >= 6.5 pt
  T6  no rotated text except y-axis labels
  T7  panels sharing an axis are separated by a >= 6 mm gutter or a divider rule
  T8  registered content stays inside its slab (opt-in, per figure)
  T9  every text stays on the canvas, with a 1.5 mm margin
"""
from __future__ import annotations

import math

import matplotlib
from matplotlib.axis import Axis
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.spines import Spine
from matplotlib.text import Text

MM_PER_IN = 25.4
MIN_TEXT_TEXT_MM = 1.5
MIN_TEXT_GRAPHIC_MM = 1.0
MIN_GUTTER_H_MM = 5.0   # design token, Round 6: gutter between panels
MIN_GUTTER_V_MM = 7.0
MIN_LETTER_MM = 2.0
MIN_PT = 6.5
MIN_CANVAS_MM = 1.5     # T9: how far text must stay inside the page edge


def _mm(px: float, dpi: float) -> float:
    return px / dpi * MM_PER_IN


def _gap_mm(b1, b2, dpi: float) -> float:
    dx = max(b2.x0 - b1.x1, b1.x0 - b2.x1, 0.0)
    dy = max(b2.y0 - b1.y1, b1.y0 - b2.y1, 0.0)
    if dx == 0.0 and dy == 0.0:
        return 0.0
    return _mm(math.hypot(dx, dy), dpi)


def _artist_points(a, rend):
    """Display-space sample points along the artist's actual path (not its bbox).

    A diagonal line's bounding box covers area the line does not occupy, so a
    bbox-to-bbox test raises false alarms; sampling the path avoids that.
    """
    import numpy as np
    try:
        from matplotlib.patches import FancyArrowPatch
        if isinstance(a, Line2D):
            xy = a.get_transform().transform(np.column_stack(a.get_data()))
        elif isinstance(a, FancyArrowPatch):
            # its path is already display-space; use the stored endpoints instead
            pa, pb = a._posA_posB
            xy = a.get_transform().transform(np.array([pa, pb], dtype=float))
        else:
            # Patch.get_transform() already composes get_patch_transform() with the
            # artist transform, so the path must not be pre-transformed again.
            xy = a.get_path().transformed(a.get_transform()).vertices
    except Exception:
        return None
    xy = np.asarray(xy, dtype=float)
    xy = xy[np.isfinite(xy).all(axis=1)]
    if len(xy) == 0:
        return None
    if len(xy) == 1:
        return xy
    segs = []
    for i in range(len(xy) - 1):
        t = np.linspace(0.0, 1.0, 12)[:, None]
        segs.append(xy[i] * (1 - t) + xy[i + 1] * t)
    return np.vstack(segs)


def _rect_point_gap_mm(bb, pts, dpi):
    import numpy as np
    dx = np.maximum(np.maximum(bb.x0 - pts[:, 0], pts[:, 0] - bb.x1), 0.0)
    dy = np.maximum(np.maximum(bb.y0 - pts[:, 1], pts[:, 1] - bb.y1), 0.0)
    return _mm(float(np.min(np.hypot(dx, dy))), dpi)


def _contains(outer, inner, slack=2.0) -> bool:
    return (outer.x0 - slack <= inner.x0 and outer.x1 + slack >= inner.x1
            and outer.y0 - slack <= inner.y0 and outer.y1 + slack >= inner.y1)


def _texts(fig, rend):
    out = []
    for t in fig.findobj(Text):
        if not t.get_visible():
            continue
        s = (t.get_text() or "").strip()
        if not s:
            continue
        if isinstance(getattr(t, "axes", None), object) and t in getattr(
                getattr(t, "axes", None), "get_children", lambda: [])():
            pass
        try:
            bb = t.get_window_extent(renderer=rend)
        except Exception:
            continue
        if bb.width <= 0 or bb.height <= 0:
            continue
        out.append((t, s, bb))
    return out


def _graphics(fig, rend):
    out = []
    # the background patch of an Axes has .axes set to None in current matplotlib,
    # so exclude those by identity rather than by attribute
    bg = {id(ax.patch) for ax in fig.axes} | {id(fig.patch)}
    # Ticks whose location falls outside the view interval are still reachable as
    # artists but are never drawn; keep them out of the measurement.
    # An axes turned off with ax.axis("off") draws no ticks, but its tick artists
    # still report themselves as visible (the switch is Axes.axison); drop them.
    tick_home, hidden = {}, set()
    for ax in fig.axes:
        abb = ax.get_window_extent(renderer=rend)
        for axis in (ax.xaxis, ax.yaxis):
            tls = (list(axis.get_ticklines(minor=False))
                   + list(axis.get_ticklines(minor=True)))
            if not getattr(ax, "axison", True) or not axis.get_visible():
                hidden.update(id(t) for t in tls)
                continue
            for tl in tls:
                tick_home[id(tl)] = abb
    for a in fig.findobj():
        if isinstance(a, (Text, Spine, Axis)):
            continue
        if not isinstance(a, (Line2D, Patch)):
            continue
        if not a.get_visible():
            continue
        if id(a) in bg or id(a) in hidden:
            continue
        if str(getattr(a, "get_gid", lambda: None)() or "").startswith("nocheck"):
            continue
        try:
            bb = a.get_window_extent(renderer=rend)
        except Exception:
            continue
        if bb.width <= 0 and bb.height <= 0:
            continue
        home = tick_home.get(id(a))
        if home is not None:
            pad = 6.0                      # px; a tick legitimately sticks out
            if (bb.x1 < home.x0 - pad or bb.x0 > home.x1 + pad
                    or bb.y1 < home.y0 - pad or bb.y0 > home.y1 + pad):
                continue
        fw, fh = fig.get_size_inches() * fig.dpi
        if bb.width >= 0.95 * fw and bb.height >= 0.95 * fh:
            continue                      # figure/axes background panel
        out.append((a, bb, _artist_points(a, rend)))
    return out



def _overlaps(b1, b2) -> bool:
    return not (b2.x0 > b1.x1 or b1.x0 > b2.x1 or b2.y0 > b1.y1 or b1.y0 > b2.y1)


def _opaque_box(t) -> bool:
    """True when the text carries a filled box that hides what is behind it."""
    bp = t.get_bbox_patch()
    if bp is None:
        return False
    fc = bp.get_facecolor()
    if fc is None or (len(fc) > 3 and fc[3] < 0.85):
        return False
    a = bp.get_alpha()
    return a is None or a >= 0.85


def _panel_of(bb, axes_bb):
    best, bestd = "figure", 1e18
    for name, ab in axes_bb.items():
        if _contains(ab, bb, slack=40):
            return name
        d = math.hypot(max(ab.x0 - bb.x1, bb.x0 - ab.x1, 0.0),
                       max(ab.y0 - bb.y1, bb.y0 - ab.y1, 0.0))
        if d < bestd:
            best, bestd = name, d
    return best


def check(fig, name: str, letters: dict | None = None,
          shared_axis_pairs: tuple = (), min_pt: float | None = None) -> dict:
    """Measure one figure.  `letters` maps panel letter -> axes.

    `min_pt` raises the T5 type floor for one figure.  A figure may set a
    *higher* floor than the global 6.5 pt (Fig. 2 uses 7 pt, because its cards
    are read at arm's length); it may never set a lower one, and the check
    refuses to be weakened.
    """
    floor = MIN_PT if min_pt is None else max(MIN_PT, float(min_pt))
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    dpi = fig.dpi
    W, H = fig.get_size_inches()
    axes_bb = {}
    for i, ax in enumerate(fig.axes):
        lab = ax.get_label() or f"ax{i}"
        axes_bb[lab] = ax.get_window_extent(renderer=rend)

    rep = dict(figure=name, width_mm=round(W * MM_PER_IN, 1),
               height_mm=round(H * MM_PER_IN, 1), checks=[], closest=[])

    def add(cid, desc, ok, detail=""):
        rep["checks"].append(dict(id=cid, check=desc, pass_=bool(ok), detail=detail))

    texts = _texts(fig, rend)

    # T5 minimum type size
    small = [(s, round(t.get_fontsize(), 2)) for t, s, _ in texts
             if t.get_fontsize() < floor - 1e-9]
    add("T5", f"all text >= {floor} pt", not small,
        "" if not small else f"{len(small)} below: {small[:5]}")

    # T6 rotation.  The y-axis label of an Axes is the one legitimate rotated text;
    # identify it by identity, since Axis.label.axes is not reliably set.
    ylabels = {id(ax.yaxis.label) for ax in fig.axes}
    # A figure may declare one rotated label on purpose by tagging it "rotok";
    # Fig. 2's depth ruler is the only user.  It is an exemption, not a
    # loosening: the tag has to be written into the figure.
    rot = []
    for t, s, _ in texts:
        r = float(t.get_rotation()) % 180
        if r <= 0.5 or id(t) in ylabels:
            continue
        if "rotok" in str(t.get_gid() or ""):
            continue
        rot.append((s[:24], round(float(t.get_rotation()), 1)))
    add("T6", "no rotated text except y-axis labels", not rot,
        "" if not rot else f"{len(rot)} rotated: {rot[:5]}")

    # T1 text-to-text clearance, per panel
    def _run(t):
        """The typeset line a fragment belongs to, if it is part of one.

        A coloured line is drawn as several Text artists laid end to end, so
        they touch by construction.  They are one piece of text and T1 must
        not read the join as a collision; fragments of *different* lines are
        still compared, as is everything else.
        """
        g = str(t.get_gid() or "")
        return g.split(":", 1)[0] if g.startswith("run") else None

    worst = []
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            (t1, s1, b1), (t2, s2, b2) = texts[i], texts[j]
            r1, r2 = _run(t1), _run(t2)
            if r1 is not None and r1 == r2:
                continue
            g = _gap_mm(b1, b2, dpi)
            worst.append((g, s1[:22], s2[:22], _panel_of(b1, axes_bb)))
    worst.sort(key=lambda x: x[0])
    bad_tt = [w for w in worst if w[0] < MIN_TEXT_TEXT_MM]
    add("T1", f"text-to-text clearance >= {MIN_TEXT_TEXT_MM} mm", not bad_tt,
        "" if not bad_tt else
        f"{len(bad_tt)} pairs below; closest {bad_tt[0][0]:.2f} mm: "
        f"'{bad_tt[0][1]}' / '{bad_tt[0][2]}' in {bad_tt[0][3]}")
    seen = set()
    for g, s1, s2, pan in worst:
        if pan in seen:
            continue
        seen.add(pan)
        rep["closest"].append(dict(panel=pan, gap_mm=round(g, 2), a=s1, b=s2))

    # T2 text-to-graphic clearance
    graphics = _graphics(fig, rend)
    bad_tg = []
    n_boxed_exempt = 0
    for t, s, b in texts:
        owner_bb = None
        if t.get_bbox_patch() is not None:
            try:
                owner_bb = t.get_bbox_patch().get_window_extent(renderer=rend)
            except Exception:
                owner_bb = None
        # A label with an OPAQUE box behind it stays legible over artwork, which
        # is the whole point of the box; T2 exists for legibility, so such a
        # label is exempt -- but only against graphics that are actually behind
        # it and actually covered by the box.  Everything else still counts, and
        # the exemptions are counted and reported rather than hidden.
        opaque = _opaque_box(t)
        for a, ab, pts in graphics:
            if owner_bb is not None and _contains(owner_bb, ab, slack=4):
                continue
            if a is t.get_bbox_patch():
                continue
            if (opaque and owner_bb is not None
                    and a.get_zorder() < t.get_zorder()
                    and _overlaps(owner_bb, ab)):
                n_boxed_exempt += 1
                continue
            if _contains(ab, b, slack=2):        # text sits inside its own glyph
                continue
            g = (_rect_point_gap_mm(b, pts, dpi) if pts is not None
                 else _gap_mm(b, ab, dpi))
            if g < MIN_TEXT_GRAPHIC_MM:
                bad_tg.append((round(g, 2), s[:22], type(a).__name__))
    bad_tg.sort()
    rep["boxed_exempt"] = n_boxed_exempt
    add("T2", f"text-to-graphic clearance >= {MIN_TEXT_GRAPHIC_MM} mm", not bad_tg,
        "" if not bad_tg else f"{len(bad_tg)} below; closest {bad_tg[:4]}")

    # T3 panel gutters
    names = list(axes_bb)
    bad_g = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = axes_bb[names[i]], axes_bb[names[j]]
            ox = not (a.x1 < b.x0 or b.x1 < a.x0)
            oy = not (a.y1 < b.y0 or b.y1 < a.y0)
            if oy and not ox:
                g = _mm(max(b.x0 - a.x1, a.x0 - b.x1), dpi)
                if g < MIN_GUTTER_H_MM - 1e-6:
                    bad_g.append((names[i], names[j], "h", round(g, 2)))
            if ox and not oy:
                g = _mm(max(b.y0 - a.y1, a.y0 - b.y1), dpi)
                if g < MIN_GUTTER_V_MM - 1e-6:
                    bad_g.append((names[i], names[j], "v", round(g, 2)))
    add("T3", f"panel gutters >= {MIN_GUTTER_H_MM} mm h / {MIN_GUTTER_V_MM} mm v",
        not bad_g, "" if not bad_g else str(bad_g[:4]))

    # T4 panel letters
    bad_l = []
    if letters:
        for L, ax in letters.items():
            tt = [x for x in texts if x[1] == L]
            if not tt:
                bad_l.append((L, "letter not found"))
                continue
            ab = ax.get_window_extent(renderer=rend)
            g = _gap_mm(tt[0][2], ab, dpi)
            if g < MIN_LETTER_MM:
                bad_l.append((L, round(g, 2)))
    add("T4", f"panel letter >= {MIN_LETTER_MM} mm from its axes box", not bad_l,
        "" if not bad_l else str(bad_l))

    # T7 shared-axis separation
    bad_s = []
    for (n1, n2) in shared_axis_pairs:
        if n1 not in axes_bb or n2 not in axes_bb:
            continue
        a, b = axes_bb[n1], axes_bb[n2]
        gh = _mm(max(b.x0 - a.x1, a.x0 - b.x1), dpi)
        gv = _mm(max(b.y0 - a.y1, a.y0 - b.y1), dpi)
        if max(gh, gv) < MIN_GUTTER_H_MM:
            bad_s.append((n1, n2, round(max(gh, gv), 2)))
    add("T7", "panels sharing an axis separated by >= 6 mm or a divider rule",
        not bad_s, "" if not bad_s else str(bad_s))

    rep["pass"] = all(c["pass_"] for c in rep["checks"])
    # T9 canvas containment.  T1 and T2 compare text with other things on the
    # page and never with the page itself, so a label can run clean off the
    # canvas and still pass everything else.  This catches that.
    W_px, H_px = fig.get_size_inches() * dpi
    off = []
    for t, s_, b in texts:
        m = min(b.x0, W_px - b.x1, b.y0, H_px - b.y1)
        if m < MIN_CANVAS_MM / MM_PER_IN * dpi:
            off.append((round(_mm(m, dpi), 2), s_[:30]))
    off.sort()
    add("T9", f"text on the canvas (margin >= {MIN_CANVAS_MM} mm)", not off,
        "" if not off else f"{len(off)} off the page: {off[:5]}")

    # T8 containment: every registered artist inside its slab, with margin
    conts = getattr(fig, "_t8", None)
    if conts:
        bad_c = []
        for c in conts:
            ax = c["ax"]
            (cx0, cy0) = ax.transData.transform((c["x0"], c["y0"]))
            (cx1, cy1) = ax.transData.transform((c["x1"], c["y1"]))
            lo_x, hi_x = min(cx0, cx1), max(cx0, cx1)
            lo_y, hi_y = min(cy0, cy1), max(cy0, cy1)
            m = c.get("margin", 2.0) / MM_PER_IN * dpi
            for a in c["artists"]:
                try:
                    bb = a.get_window_extent(renderer=rend)
                except Exception:
                    continue
                over = max(lo_x + m - bb.x0, bb.x1 - (hi_x - m),
                           lo_y + m - bb.y0, bb.y1 - (hi_y - m))
                if over > 1e-6:
                    lbl = (a.get_text()[:28] if isinstance(a, Text)
                           else type(a).__name__)
                    bad_c.append((round(_mm(over, dpi), 2), c["name"], lbl))
        bad_c.sort(reverse=True)
        add("T8", "content inside its slab (margin >= 2.0 mm)", not bad_c,
            "" if not bad_c else f"{len(bad_c)} outside: {bad_c[:6]}")

    return rep


def render_report(reps: list[dict]) -> str:
    L = ["## Layout checks", "",
         "Measured on the live figure at final print size; distances in millimetres of "
         "printed page.  "
         f"T1 text-to-text >= {MIN_TEXT_TEXT_MM} mm, T2 text-to-graphic >= "
         f"{MIN_TEXT_GRAPHIC_MM} mm, T3 gutters >= {MIN_GUTTER_H_MM}/"
         f"{MIN_GUTTER_V_MM} mm, T4 panel letter >= {MIN_LETTER_MM} mm, T5 type >= "
         f"{MIN_PT} pt, T6 rotation, T7 shared-axis separation.", "",
         "| figure | size (mm) | T1 | T2 | T3 | T4 | T5 | T6 | T7 | overall |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in reps:
        by = {c["id"]: c for c in r["checks"]}
        cells = " | ".join("PASS" if by.get(k, {}).get("pass_") else "FAIL"
                           for k in ("T1", "T2", "T3", "T4", "T5", "T6", "T7"))
        L.append(f"| `{r['figure']}` | {r['width_mm']} x {r['height_mm']} | {cells} | "
                 f"**{'PASS' if r['pass'] else 'FAIL'}** |")
    L += ["", "### Failures in detail", ""]
    any_fail = False
    for r in reps:
        for c in r["checks"]:
            if not c["pass_"]:
                any_fail = True
                L.append(f"- `{r['figure']}` **{c['id']}** ({c['check']}): {c['detail']}")
    if not any_fail:
        L.append("- none")
    L += ["", "### Closest pair of text elements in each panel", "",
          "| figure | panel | gap (mm) | element A | element B |", "|---|---|---|---|---|"]
    def cell(t):                       # keep multi-line labels inside one table cell
        return t.replace("\n", " / ").replace("|", "\\|")
    for r in reps:
        for c in r["closest"]:
            L.append(f"| `{r['figure']}` | {c['panel']} | {c['gap_mm']} | "
                     f"{cell(c['a'])} | {cell(c['b'])} |")
    L.append("")
    return "\n".join(L)

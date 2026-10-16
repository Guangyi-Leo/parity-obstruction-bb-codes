"""Shared design system for the manuscript figures (npj QI).

One palette, one glyph grammar, one type scale, used by every figure.  All sizes are
specified in millimetres at final print scale; helpers convert to inches/points.

Everything is drawn with matplotlib rather than TikZ on purpose: the layout checker in
figures/check_layout.py measures the bounding box of every text artist and every line,
which is only possible for a live matplotlib figure.
"""
from __future__ import annotations

import glob
import json
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm                                  # noqa: E402
import matplotlib.pyplot as plt                                        # noqa: E402
from matplotlib.patches import (Circle, Ellipse, FancyArrowPatch,  # noqa: E402
                                FancyBboxPatch, Polygon, Rectangle, Wedge)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FIGS = os.path.join(ROOT, "figures")
DATA = os.path.join(ROOT, "data")

# ---------------------------------------------------------------- geometry
MM = 1.0 / 25.4                      # mm -> inch
W_DOUBLE_MM, W_SINGLE_MM = 180.0, 88.0
W_DOUBLE, W_SINGLE = W_DOUBLE_MM * MM, W_SINGLE_MM * MM


def mm(x: float) -> float:
    """millimetres -> inches"""
    return x * MM


# ---------------------------------------------------------------- type scale
PT_PANEL = 7.5        # axis labels and panel text
PT_TICK = 7.0         # tick labels and annotations
PT_MIN = 6.5          # hard floor
PT_LETTER = 9.0       # panel letters, bold

# ---------------------------------------------------------------- palette
# Okabe-Ito, colour-blind safe.  Blue and orange mean X and Z and nothing else.
C_X = "#0072B2"       # X-checks
C_Z = "#E69F00"       # Z-checks
INK = "#252525"
GREY = "#8C8C8C"
RULE = "#D0D0D0"
C_QUBIT_FILL = "#FFFFFF"      # data qubit
C_L = "#F2F2F2"       # L-qubit tint behind ladders
C_R = "#DADADA"       # R-qubit tint
C_OBS = "#CC79A7"     # rose: the cross term, and `open`
HALO = "#CC79A7"      # highlight halo, drawn at 25 % alpha
HALO_ALPHA = 0.25

# Outcome ramp.  Four categories only; the six status_math values map onto them.
C_SAT = "#4D4D4D"
C_UNSAT_THM = "#A6A6A6"
C_UNSAT_SOLVER = "#D9D9D9"
C_OPEN = C_OBS
OUTCOME = {"SAT": C_SAT, "UNSAT-theorem": C_UNSAT_THM,
           "UNSAT-solver": C_UNSAT_SOLVER, "open": C_OPEN}
OUTCOME_ORDER = ["SAT", "UNSAT-theorem", "UNSAT-solver", "open"]
STATUS_TO_OUTCOME = {"SAT-solver": "SAT", "SAT-witness": "SAT",
                     "UNSAT-theorem": "UNSAT-theorem",
                     "UNSAT-cert": "UNSAT-theorem",
                     "UNSAT-solver": "UNSAT-solver", "open": "open"}
HATCH = "////"        # capped share, same hue
STATUS_MATH = ["UNSAT-theorem", "UNSAT-cert", "UNSAT-solver", "SAT-solver",
               "SAT-witness", "open"]
STATUS_COLOUR = {k: OUTCOME[STATUS_TO_OUTCOME[k]] for k in STATUS_MATH}
STATUS_DARK = {"SAT-solver", "SAT-witness"}      # white text on the dark end
STATUS_SHADE = STATUS_COLOUR
STATUS_ORDER = STATUS_MATH

# box border styles
BOX_SOLID = "-"
BOX_DASHED = (0, (2.0 / 0.5, 1.2 / 0.5))       # 2 pt on / 1.2 pt off at 0.5 pt
BOX_DOTTED = (0, (0.6 / 0.5, 1.2 / 0.5))       # 0.6 pt dots / 1.2 pt gaps

# ---------------------------------------------------------------- geometry (mm)
GUTTER_MM = 5.0
D_QUBIT_MM = 3.2          # data qubit diameter
D_CHECK_MM = 3.2          # X square / Z diamond
LAYERBOX_MM = (2.6, 2.0)  # layer index box
RUNG_MM = 4.2             # ladder rung pitch: 2.6 mm was specified, but
                          # 6.5 pt rung numbers are 2.3 mm tall, so 2.6 mm
                          # leaves 0.3 mm and fails the 1.5 mm text rule
TICK_MM = 1.8             # ladder tick
CHECK_FILL_ALPHA = 0.15

# Line weights (pt)
LW_SPINE, LW_DATA, LW_EDGE, LW_RULE = 0.6, 0.9, 0.8, 0.4
LW_LEADER, LW_ARROW, LW_BOX = 0.5, 0.6, 0.5
ARROW_HEAD_PT = 2.5
# head_length/head_width are in points at mutation_scale 1, so the printed head is
# exactly 3 pt long and 3 pt across whatever the figure size.
# head_length/head_width are given in points (mutation_scale 1), so the printed head
# is 3 pt long whatever the figure size.  zorder 5 puts shaft and head above the boxes
# (zorder 3) and below their text (zorder 6): without it the head is painted over by
# the box it points at.
ARROW = dict(arrowstyle="-|>,head_length=2.5,head_width=1.25", mutation_scale=1.0,
             lw=LW_ARROW, color=INK, shrinkA=1.0, shrinkB=1.5, joinstyle="miter",
             zorder=5)


def use_style():
    for p in glob.glob(os.path.join(FIGS, "fonts", "*.otf")):
        try:
            fm.fontManager.addfont(p)
        except Exception:
            pass
    fam = [f for f in ("TeX Gyre Heros", "Helvetica", "Arial", "DejaVu Sans")
           if f in {x.name for x in fm.fontManager.ttflist}]
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": fam,
        "mathtext.fontset": "custom",
        "mathtext.rm": fam[0], "mathtext.it": f"{fam[0]}:italic",
        "mathtext.bf": f"{fam[0]}:bold", "mathtext.default": "it",
        "mathtext.cal": fam[0], "mathtext.sf": fam[0], "mathtext.tt": fam[0],
        "font.size": PT_TICK,
        "axes.labelsize": PT_PANEL, "axes.titlesize": PT_PANEL,
        "xtick.labelsize": PT_TICK, "ytick.labelsize": PT_TICK,
        "legend.fontsize": PT_TICK,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": LW_SPINE, "axes.edgecolor": INK,
        "xtick.major.width": LW_SPINE, "ytick.major.width": LW_SPINE,
        "xtick.major.size": 2.0, "ytick.major.size": 2.0,
        "xtick.color": INK, "ytick.color": INK, "text.color": INK,
        "lines.linewidth": LW_DATA, "axes.grid": False,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "savefig.bbox": None, "figure.dpi": 600,
        # long polylines are split rather than handed to Agg whole
        "agg.path.chunksize": 20000,
    })
    return fam[0]


def panel_letter(fig, ax, letter, dx_mm=-6.5, dy_mm=2.4):
    """Bold letter outside the axes at top-left, offset in millimetres."""
    bb = ax.get_position()
    x = bb.x0 + mm(dx_mm) / fig.get_size_inches()[0]
    y = bb.y1 + mm(dy_mm) / fig.get_size_inches()[1]
    return fig.text(x, y, letter, fontsize=PT_LETTER, fontweight="bold", va="bottom",
                    ha="left", color=INK)


def light_grid(ax, axis="y"):
    ax.grid(axis=axis, color=RULE, linewidth=0.3, zorder=0)
    ax.set_axisbelow(True)


def divider(fig, x=None, y=None, lo=0.0, hi=1.0):
    """0.4 pt light-grey rule separating panels that share an axis."""
    if x is not None:
        fig.add_artist(plt.Line2D([x, x], [lo, hi], color=RULE, lw=LW_RULE,
                                  transform=fig.transFigure, zorder=0))
    if y is not None:
        fig.add_artist(plt.Line2D([lo, hi], [y, y], color=RULE, lw=LW_RULE,
                                  transform=fig.transFigure, zorder=0))


# ---------------------------------------------------------------- glyphs
def x_check(ax, x, y, s=0.30, **kw):
    """X-check: square, blue border with a 15 % blue fill."""
    ax.add_patch(Rectangle((x - s / 2, y - s / 2), s, s, facecolor=C_X,
                           alpha=CHECK_FILL_ALPHA, edgecolor="none", zorder=3))
    ax.add_patch(Rectangle((x - s / 2, y - s / 2), s, s, facecolor="none",
                           edgecolor=C_X, linewidth=LW_EDGE, zorder=4, **kw))


def z_check(ax, x, y, s=0.30, **kw):
    """Z-check: square rotated 45 degrees, orange border with a 15 % fill."""
    h = s * 0.72
    pts = [(x, y + h), (x + h, y), (x, y - h), (x - h, y)]
    ax.add_patch(Polygon(pts, closed=True, facecolor=C_Z,
                         alpha=CHECK_FILL_ALPHA, edgecolor="none", zorder=3))
    ax.add_patch(Polygon(pts, closed=True, facecolor="none", edgecolor=C_Z,
                         linewidth=LW_EDGE, zorder=4, **kw))


def qubit(ax, x, y, r=0.15, side="L", **kw):
    """Data qubit: white circle with an ink stroke."""
    ax.add_patch(Circle((x, y), r, facecolor=C_QUBIT_FILL, edgecolor=INK,
                        linewidth=LW_SPINE, zorder=5, **kw))


def halo(ax, x, y, r, **kw):
    """The rose highlight used for the cross term."""
    ax.add_patch(Circle((x, y), r, facecolor=HALO, alpha=HALO_ALPHA,
                        edgecolor="none", zorder=2, **kw))


def half_disc(ax, x, y, r=0.10, up=True, color=None):
    """Corner orientation: filled half-disc on a baseline rule (never a word)."""
    t1, t2 = (0, 180) if up else (180, 360)
    ax.add_patch(Wedge((x, y), r, t1, t2, facecolor=color or INK, edgecolor=INK,
                       linewidth=0.4, zorder=5))
    ax.plot([x - r * 1.25, x + r * 1.25], [y, y], color=INK, lw=0.5, zorder=6,
            solid_capstyle="butt")


def ladder(ax, x, y_top, pitch, n, x_at=None, z_at=None, tint=None,
           title=None, fs=None, half=0.10, numbers=True):
    """Vertical layer ladder: rung i at y_top - (i-1)*pitch, for i = 1..n.

    `x_at` / `z_at` map a rung to the label to print beside its tick; X ticks are
    blue squares, Z ticks orange diamonds.  `tint` fills the band behind it.
    """
    fs = fs or PT_MIN
    ys = [y_top - (i - 1) * pitch for i in range(1, n + 1)]
    if tint:
        # a background tint the rung numbers sit on: theirs, so not a clearance
        ax.add_patch(Rectangle((x - half * 2.4, ys[-1] - pitch * 0.62),
                               half * 4.8, (n - 1) * pitch + pitch * 1.24,
                               facecolor=tint, edgecolor="none", zorder=0,
                               gid="nocheck"))
    ax.plot([x, x], [ys[0] + pitch * 0.45, ys[-1] - pitch * 0.45], color=RULE,
            lw=LW_RULE, zorder=1)
    for i, y in enumerate(ys, start=1):
        ax.plot([x - half * 0.55, x + half * 0.55], [y, y], color=RULE,
                lw=LW_RULE, zorder=1)
        if numbers:
            ax.text(x - half * 1.9, y, str(i), ha="right", va="center",
                    fontsize=fs, color=GREY)
    for rung, lab in (x_at or {}).items():
        y = y_top - (rung - 1) * pitch
        ax.add_patch(Rectangle((x - half * 0.42, y - half * 0.42), half * 0.84,
                               half * 0.84, facecolor=C_X, edgecolor=C_X,
                               linewidth=0.0, zorder=4))
        ax.text(x + half * 0.95, y, str(lab), ha="left", va="center",
                fontsize=fs, color=C_X)
    for rung, lab in (z_at or {}).items():
        y = y_top - (rung - 1) * pitch
        d = half * 0.52
        ax.add_patch(Polygon([(x, y + d), (x + d, y), (x, y - d), (x - d, y)],
                             closed=True, facecolor=C_Z, edgecolor=C_Z,
                             linewidth=0.0, zorder=4))
        ax.text(x + half * 0.95, y, str(lab), ha="left", va="center",
                fontsize=fs, color=C_Z)
    if title:
        ax.text(x, ys[0] + pitch * 1.05, title, ha="center", va="bottom",
                fontsize=fs)
    return ys


def layer_box(ax, x, y, text, pad=0.16, fs=None):
    """Layer index in a small rounded box sitting on an edge."""
    return ax.text(x, y, text, ha="center", va="center", fontsize=fs or PT_MIN,
                   zorder=6, color=INK,
                   bbox=dict(boxstyle=f"round,pad={pad}", facecolor="white",
                             edgecolor=RULE, linewidth=0.4))


def node_label(ax, x, y, text, nx, ny, off_mm=1.2, fig=None, r=0.0, **kw):
    """Label offset `off_mm` along the outward normal, measured from the node boundary.

    `r` is the node radius in data units; the anchor is placed on the boundary first so
    that the offset is genuine clearance and not eaten by the glyph.
    """
    import numpy as np
    n = np.hypot(nx, ny) or 1.0
    dx, dy = nx / n, ny / n
    x, y = x + dx * r, y + dy * r
    ha = "left" if dx > 0.3 else ("right" if dx < -0.3 else "center")
    va = "bottom" if dy > 0.3 else ("top" if dy < -0.3 else "center")
    tr = ax.transData
    import matplotlib.transforms as mt
    dpi = (fig or ax.figure).dpi
    shift = mt.ScaledTranslation(dx * off_mm * MM, dy * off_mm * MM,
                                 mt.Affine2D().scale(dpi))
    return ax.text(x, y, text, ha=ha, va=va, fontsize=kw.pop("fontsize", PT_TICK),
                   transform=tr + shift, zorder=7, color=INK, **kw)


def arrow(ax, p0, p1, **kw):
    a = dict(ARROW)
    a.update(kw)
    ax.add_patch(FancyArrowPatch(p0, p1, **a))


# ---------------------------------------------------------------- circuits
def wire(ax, x0, x1, y, label=None, fs=None):
    ax.plot([x0, x1], [y, y], color=INK, lw=LW_EDGE, zorder=2,
            solid_capstyle="round")
    if label:
        ax.text(x0 - 0.05, y, label, ha="right", va="center",
                fontsize=fs or PT_TICK)


def cnot(ax, x, y_ctrl, y_targ, r=0.085, colour=None):
    """Control dot on y_ctrl, XOR target on y_targ, joined by a vertical line."""
    c = colour or INK
    ax.plot([x, x], [y_ctrl, y_targ], color=c, lw=LW_EDGE, zorder=3)
    ax.add_patch(Circle((x, y_ctrl), r * 0.42, facecolor=c, edgecolor=c,
                        linewidth=0, zorder=4))
    ax.add_patch(Circle((x, y_targ), r, facecolor="white", edgecolor=c,
                        linewidth=LW_EDGE, zorder=4))
    ax.plot([x - r, x + r], [y_targ, y_targ], color=c, lw=LW_EDGE, zorder=5)
    ax.plot([x, x], [y_targ - r, y_targ + r], color=c, lw=LW_EDGE, zorder=5)


def meter(ax, x, y, w=0.17, h=0.11, colour=None):
    """Measurement box."""
    c = colour or INK
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, facecolor="white",
                           edgecolor=c, linewidth=LW_EDGE, zorder=4))
    import numpy as _np
    t = _np.linspace(0.15 * 3.14159, 0.85 * 3.14159, 24)
    ax.plot(x + 0.33 * w * _np.cos(t), y - 0.22 * h + 0.5 * h * _np.sin(t),
            color=c, lw=0.5, zorder=5)
    ax.plot([x, x + 0.30 * w], [y - 0.22 * h, y + 0.28 * h], color=c, lw=0.5,
            zorder=5)


def aux_label(key):
    """The number LaTeX printed for \\label{key}.

    A figure that quotes a supplementary table by number must not carry that
    number as a literal: inserting one table upstream renumbers every table
    after it and the figure would then point at the wrong one.

    The authority is build_tex/main.aux, so the number is only ever as stale as
    the last build.  A fresh clone has no build_tex/ yet -- the figures would
    then be unbuildable before the manuscript, and the manuscript needs the
    figures -- so build_tex/labels.json, written by build_tex.sh and shipped
    with the source, is the fallback.
    """
    aux = os.path.join(ROOT, "build_tex", "main.aux")
    if os.path.exists(aux):
        pat = re.compile(r"\\newlabel\{" + re.escape(key) + r"\}\{\{([^}]*)\}")
        with open(aux) as f:
            for line in f:
                m = pat.search(line)
                if m:
                    return m.group(1)
        raise SystemExit(f"label {key!r} is not in {aux}; rerun latexmk so the "
                         "figures can quote its number")

    cached = os.path.join(ROOT, "build_tex", "labels.json")
    if os.path.exists(cached):
        with open(cached) as f:
            labels = json.load(f)
        if key in labels:
            return labels[key]
        raise SystemExit(f"label {key!r} is in neither {aux} (absent) nor "
                         f"{cached}; run ./build_tex.sh")
    raise SystemExit(f"neither {aux} nor {cached} exists: run ./build_tex.sh "
                     "once so the figures can quote the manuscript's numbers")


def box(ax, x, y, w, h, style="solid", face="white", lw=LW_EDGE, ec=INK, **kw):
    ls = {"solid": "-", "dashed": (0, (3.2, 1.8)), "dotted": (0, (0.8, 1.6))}[style]
    p = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                       boxstyle="round,pad=0.008,rounding_size=0.012",
                       facecolor=face, edgecolor=ec, linewidth=lw, linestyle=ls,
                       zorder=3, **kw)
    ax.add_patch(p)
    return p


# ==================================================================
# Round 7: the rendering layer
#
# Five primitives that give the composite figures depth and a single icon
# family, following the reference figures in figures/ref/ (see CHECK.md,
# "Round 7, step 0"). Everything is in millimetres: the axes of every Round 7
# scene are millimetre axes, so `d`, `w`, `t` below are millimetres on the
# printed page.
#
# Gradients and shadows are built from stacked vector primitives, never from a
# rasterised image, so the PDF and the layered SVG stay resolution-free and the
# layout checker can still measure every artist.
# ==================================================================

# ---- SVG layers ---------------------------------------------------------
# Every artist is tagged with the named group it belongs to, so the SVG can be
# regrouped into `background / lattice / gates / annotations / insets` for
# finishing in Inkscape. The same tag carries the layout checker's "skip me"
# flag: a gid of "nocheck:<group>" is decorative (shadows, gradient rings,
# tints) and is not measured. check_layout.py keys on the "nocheck" prefix.
SVG_LAYERS = ["background", "lattice", "gates", "annotations", "insets"]
_LAYER = ["background"]


class svg_layer:
    """`with S.svg_layer("lattice"): ...` tags everything drawn inside."""

    def __init__(self, name):
        if name not in SVG_LAYERS:
            raise ValueError(f"unknown SVG layer {name!r}; use {SVG_LAYERS}")
        self.name = name

    def __enter__(self):
        _LAYER.append(self.name)
        return self

    def __exit__(self, *exc):
        _LAYER.pop()
        return False


def _g(nocheck=False, gid=None):
    """Build the gid for an artist drawn in the current layer."""
    if gid is not None and ":" in gid:
        return gid
    tag = _LAYER[-1]
    if gid:
        tag = f"{tag}.{gid}"
    return f"nocheck:{tag}" if nocheck else tag


SHADOW_RGBA = (0.0, 0.0, 0.0, 0.12)   # drop shadow: #000 at 12 %
SHADOW_OFF_MM = 0.3                   # offset, right and down


def _mix(c1, c2, t):
    """Blend two colours in sRGB; t = 0 gives c1, t = 1 gives c2."""
    a = matplotlib.colors.to_rgb(c1)
    b = matplotlib.colors.to_rgb(c2)
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def _desat(c, keep=0.70):
    """Drop to `keep` of the original chroma, holding luminance."""
    r, g, b = matplotlib.colors.to_rgb(c)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return tuple(lum + (v - lum) * keep for v in (r, g, b))


# Seven layer colours: viridis endpoints #440154 -> #FDE725, desaturated to
# 70 % chroma so they never compete with the X/Z blue and orange, which stay
# reserved for check identity. The layer colour goes on the edges only.
LAYER7 = [matplotlib.colors.to_hex(_desat(matplotlib.cm.viridis(t), 0.70))
          for t in [i / 6.0 for i in range(7)]]


def layer_colour(i, n=7):
    """Colour of layer `i` (1-based) in an n-layer schedule."""
    if n == 7:
        return LAYER7[min(max(int(i) - 1, 0), 6)]
    t = 0.0 if n <= 1 else (int(i) - 1) / (n - 1)
    return matplotlib.colors.to_hex(_desat(matplotlib.cm.viridis(t), 0.70))


def _shadow(ax, patch_factory, zorder):
    """Add the shared drop shadow: the same shape, offset, #000 at 12 %."""
    p = patch_factory(SHADOW_OFF_MM, -SHADOW_OFF_MM)
    p.set_facecolor(SHADOW_RGBA)
    p.set_edgecolor("none")
    p.set_zorder(zorder)
    p.set_gid(_g(True))
    ax.add_patch(p)
    return p


SPHERE_NR, SPHERE_NA = 16, 32      # polar mesh: radial x angular cells
_SPH_CMAP = {}


def _sphere_cmap(side):
    """Colormap from the highlight core to the rim, cached per side."""
    if side not in _SPH_CMAP:
        rim, core = (("#D9D9D9", "#FFFFFF") if side == "L"
                     else ("#9C9C9C", "#EDEDED"))
        _SPH_CMAP[side] = matplotlib.colors.LinearSegmentedColormap.from_list(
            f"sphere{side}", [core, rim])
    return _SPH_CMAP[side]


def sphere(ax, x, y, d=None, side="L", z=5, shadow=True, gid=None):
    """A data qubit as a smoothly shaded sphere, in vector.

    The disc is a 16 x 32 polar mesh drawn with Gouraud shading, which the PDF
    backend writes as a Type-4 (free-form Gouraud triangle) shading: smooth,
    resolution-free, and about 500 vertices.  Vertex colour comes from the
    distance to a highlight centre offset 0.2 r up and to the left, so the
    specular sits where a light source would put it.  A 0.5 pt outline sits on
    top and a 12 % Ellipse shadow beneath.

    `side="R"` is the darker sphere: L and R differ in value, not hue, because
    blue and orange are reserved for check identity, and value survives
    greyscale printing.
    """
    import numpy as np

    d = D_QUBIT_MM if d is None else d
    r = d / 2.0
    if shadow:
        ax.add_patch(Ellipse((x + SHADOW_OFF_MM, y - SHADOW_OFF_MM), d, d,
                             facecolor=SHADOW_RGBA, edgecolor="none",
                             zorder=z - 1, gid=_g(True)))
    rad = np.linspace(0.0, r, SPHERE_NR)
    ang = np.linspace(0.0, 2 * np.pi, SPHERE_NA)
    R, T = np.meshgrid(rad, ang, indexing="ij")
    X = x + R * np.cos(T)
    Y = y + R * np.sin(T)
    hx, hy = x - 0.2 * r, y + 0.2 * r          # highlight centre
    # The profile is raised to a power so the ramp is concentrated into a small
    # specular core, as the stacked-ring renderer got for free by shrinking each
    # ring towards the highlight; a linear profile reads as a flat disc.
    C = (np.hypot(X - hx, Y - hy) / (1.22 * r)) ** 1.9
    m = ax.pcolormesh(X, Y, np.clip(C, 0.0, 1.0), shading="gouraud",
                      cmap=_sphere_cmap(side), vmin=0.0, vmax=1.0,
                      edgecolors="none", antialiased=False, zorder=z,
                      rasterized=False)
    m.set_gid(_g(True, "spheremesh"))
    m._sphere_params = (x, y, r, side)
    ax.add_patch(Circle((x, y), r, facecolor="none", edgecolor=INK,
                        linewidth=LW_SPINE, zorder=z + 0.5, gid=_g(gid=gid)))
    return m


def slab(ax, x, y, w, dep, t=2.0, face="#F7F7F7", shade=0.08, z=1,
         skew=(0.45, 0.32), label=None, label_kw=None, gid=None):
    """One schedule layer as a thin isometric plate.

    The top face is a parallelogram of width `w` and depth `dep` skewed up and
    to the right; `t` millimetres of extrusion give the front and right side
    faces, both darkened by `shade` (8 %). Returns the four corners of the top
    face so a caller can place tiles on it.
    """
    kx, ky = dep * skew[0], dep * skew[1]
    top = [(x, y), (x + w, y), (x + w + kx, y + ky), (x + kx, y + ky)]
    front = [(x, y), (x + w, y), (x + w, y - t), (x, y - t)]
    right = [(x + w, y), (x + w + kx, y + ky), (x + w + kx, y + ky - t),
             (x + w, y - t)]
    dark = _mix(face, "#000000", shade)
    for pts, fc, zz in ((front, dark, z), (right, _mix(face, "#000000",
                                                       shade * 1.6), z),
                        (top, face, z + 0.2)):
        ax.add_patch(Polygon(pts, closed=True, facecolor=fc, edgecolor=INK,
                             linewidth=LW_SPINE * 0.8, zorder=zz,
                             gid=_g(True)))
    if label:
        kw = dict(ha="right", va="center", fontsize=PT_MIN, color=GREY)
        kw.update(label_kw or {})
        ax.text(x - 1.2, y - t / 2 + 0.3, label, zorder=z + 1, gid=_g(gid=gid), **kw)
    return top


def check_tile(ax, x, y, s=None, kind="X", z=5, shadow=False, alpha=0.32,
               gid=None):
    """An X- or Z-check as a tinted rounded tile with a white inner rule.

    Same silhouette for both, so the tile reads as one icon family; identity is
    carried by hue (blue X, orange Z) *and* by the inner rule's inset, so the
    pair survives greyscale.
    """
    s = D_CHECK_MM if s is None else s
    col = C_X if kind == "X" else C_Z
    bs = "round,pad=0,rounding_size=%.3f" % (s * 0.22)
    if shadow:
        _shadow(ax, lambda dx, dy: FancyBboxPatch(
            (x - s / 2 + dx, y - s / 2 + dy), s, s, boxstyle=bs), z - 1)
    ax.add_patch(FancyBboxPatch((x - s / 2, y - s / 2), s, s, boxstyle=bs,
                                facecolor=col, alpha=alpha, edgecolor="none",
                                zorder=z, gid=_g(True)))
    ax.add_patch(FancyBboxPatch((x - s / 2, y - s / 2), s, s, boxstyle=bs,
                                facecolor="none", edgecolor=col,
                                linewidth=LW_EDGE, zorder=z + 0.3, gid=_g(gid=gid)))
    if s < 4.0:          # below ~4 mm the inner rule reads as a slash, not a rule
        return
    i = s * 0.30
    ax.add_patch(FancyBboxPatch((x - s / 2 + i / 2, y - s / 2 + i / 2),
                                s - i, s - i,
                                boxstyle="round,pad=0,rounding_size=%.3f"
                                % (s * 0.14),
                                facecolor="none", edgecolor="white",
                                linewidth=1.0, zorder=z + 0.2, gid=_g(True)))


def edge(ax, p0, p1, colour=None, z=2, lw=0.9, under=2.2, alpha=0.25,
         dashed=False, gid=None, stroke_alpha=1.0):
    """A Tanner edge: a 0.9 pt stroke over a 2.2 pt underlay at 25 % alpha.

    The underlay is what makes a dense lattice readable — it separates an edge
    from the ones it crosses without any of them changing weight (Bravyi Fig. 1
    does this with a value ramp; the underlay is the same trick in colour).
    """
    colour = INK if colour is None else colour
    (x0, y0), (x1, y1) = p0, p1
    if under > 0 and alpha > 0:
        ax.plot([x0, x1], [y0, y1], color=colour, lw=under, alpha=alpha,
                solid_capstyle="round", zorder=z - 0.1, gid=_g(True))
    ax.plot([x0, x1], [y0, y1], color=colour, lw=lw, alpha=stroke_alpha,
            linestyle=(0, (2.2, 1.2)) if dashed else "-",
            solid_capstyle="round", zorder=z, gid=_g(gid=gid))


def leader(ax, anchor, xy, text, fs=None, ha="left", va="center", z=8,
           colour=None, dot=True, box=True, gid=None):
    """A 0.5 pt leader from a 1 mm dot on the artwork to text in a white box.

    Naming a thing where it sits beats a colour key (Google Fig. 1); the white
    box is what lets the label sit over a dense lattice.
    """
    colour = INK if colour is None else colour
    ax.plot([anchor[0], xy[0]], [anchor[1], xy[1]], color=colour, lw=0.5,
            solid_capstyle="round", zorder=z, gid=_g(True))
    if dot:
        ax.add_patch(Circle(anchor, 0.5, facecolor=colour, edgecolor="none",
                            zorder=z + 0.1, gid=_g(True)))
    bbox = dict(boxstyle="round,pad=0.3", facecolor="white",
                edgecolor="none") if box else None
    return ax.text(xy[0], xy[1], text, ha=ha, va=va,
                   fontsize=PT_MIN if fs is None else fs, color=INK,
                   zorder=z + 0.2, bbox=bbox, gid=_g(gid=gid))


def save_layered_svg(fig, path):
    """Write `fig` as an SVG whose top level is named, Inkscape-visible groups.

    matplotlib emits one <g id="..."> per artist, in paint order, with no
    transform on the ancestor <g> elements and clip paths referenced per
    element by url -- so the per-artist groups can be regrouped without
    changing geometry.

    The grouping keeps **document order exactly**, by wrapping consecutive
    runs of same-layer artists rather than gathering each layer into one
    group.  Gathering would repaint whole groups in layer order and silently
    hide any artist whose zorder interleaved with another layer's; runs cannot,
    so the SVG always shows what the PDF shows.  A layer that interleaves
    appears as `lattice`, `lattice-2`, ... which Inkscape lists as separate
    layers -- the cost of keeping the two outputs identical.

    Artists tagged `nocheck:<layer>` land in `<layer>` too; the prefix is only
    the layout checker's flag.  Untagged matplotlib internals go to
    `background`.
    """
    import xml.etree.ElementTree as ET

    for a in fig.findobj():
        try:
            a.set_rasterized(False)
        except Exception:
            pass
    # A Gouraud mesh is a PDF Type-4 shading (small) but tens of thousands of
    # SVG triangles (~3 MB per sphere).  SVG has a native way to say the same
    # thing, so each sphere is swapped for one path filled with a shared
    # <radialGradient>; the meshes are restored afterwards.
    swapped = []
    for a in list(fig.findobj()):
        prm = getattr(a, "_sphere_params", None)
        if prm is None or not a.get_visible():
            continue
        x, y, r, side = prm
        axp = a.axes
        a.set_visible(False)
        c = Circle((x, y), r, facecolor="#EEEEEE", edgecolor="none",
                   zorder=a.get_zorder(), gid=f"svggrad-{side}")
        axp.add_patch(c)
        swapped.append((a, c))
    try:
        fig.savefig(path, format="svg")
    finally:
        for a, c in swapped:
            c.remove()
            a.set_visible(True)
    if swapped:
        _svg_sphere_gradients(path)

    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    INK_NS = "http://www.inkscape.org/namespaces/inkscape"
    tree = ET.parse(path)
    root = tree.getroot()
    SVG = "{http://www.w3.org/2000/svg}"
    fig_g = root.find(f"{SVG}g")
    if fig_g is None:
        return path

    def layer_of(el):
        gid = el.get("id") or ""
        if gid.startswith("svggrad-"):
            return "lattice"
        tag = gid.split(":", 1)[-1].split(".", 1)[0]
        return tag if tag in SVG_LAYERS else "background"

    # The artist groups are nested inside <g id="axes_1">, not at the figure
    # level, so every parent that holds tagged children is regrouped in place.
    parents = [fig_g] + [g for g in fig_g.iter(f"{SVG}g") if g is not fig_g]
    parents = [q for q in parents
               if any((c.tag == f"{SVG}g"
                       and (c.get("id") or "").split(":", 1)[-1]
                       .split(".", 1)[0] in SVG_LAYERS)
                      or (c.get("id") or "").startswith("svggrad-")
                      for c in list(q))]
    seen = {}
    for parent in parents:
        children = [c for c in list(parent) if c.tag != f"{SVG}defs"]
        if not children:
            continue
        for c in children:
            parent.remove(c)
        runs, cur, cur_tag = [], [], None
        for c in children:
            t = layer_of(c)
            if t != cur_tag and cur:
                runs.append((cur_tag, cur))
                cur = []
            cur_tag = t
            cur.append(c)
        if cur:
            runs.append((cur_tag, cur))
        for tag, els in runs:
            seen[tag] = seen.get(tag, 0) + 1
            name = tag if seen[tag] == 1 else f"{tag}-{seen[tag]}"
            g = ET.SubElement(parent, f"{SVG}g")
            g.set("id", name)
            g.set(f"{{{INK_NS}}}groupmode", "layer")
            g.set(f"{{{INK_NS}}}label", name)
            for el in els:
                g.append(el)
    root.set("xmlns:inkscape", INK_NS)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return path


def _svg_sphere_gradients(path):
    """Give the swapped sphere paths a shared <radialGradient> fill.

    Two gradients are defined once (L and R) and referenced by every sphere,
    which is how SVG is meant to express this.  The stops sample the same
    profile the Gouraud mesh uses, C = (d / 1.22 r) ** 1.9, so the SVG and the
    PDF show the same sphere.
    """
    import re
    import xml.etree.ElementTree as ET

    SVG = "{http://www.w3.org/2000/svg}"
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    tree = ET.parse(path)
    root = tree.getroot()

    defs = root.find(f"{SVG}defs")
    if defs is None:
        defs = ET.Element(f"{SVG}defs")
        root.insert(0, defs)
    for side, (rim, core) in (("L", ("#D9D9D9", "#FFFFFF")),
                              ("R", ("#9C9C9C", "#EDEDED"))):
        g = ET.SubElement(defs, f"{SVG}radialGradient")
        g.set("id", f"sphere{side}")
        g.set("gradientUnits", "objectBoundingBox")
        # highlight 0.2 r up and to the left; SVG y grows downwards
        g.set("cx", "0.40")
        g.set("cy", "0.40")
        g.set("r", "0.61")
        for f in (0.0, 0.25, 0.5, 0.75, 1.0):
            st = ET.SubElement(g, f"{SVG}stop")
            st.set("offset", f"{f:.2f}")
            st.set("stop-color",
                   matplotlib.colors.to_hex(_mix(core, rim, f ** 1.9)))

    n = 0
    for grp in root.iter(f"{SVG}g"):
        gid = grp.get("id") or ""
        if not gid.startswith("svggrad-"):
            continue
        side = gid.split("-", 1)[1][:1]
        for el in grp.iter():
            if el.tag != f"{SVG}path":
                continue
            st = el.get("style") or ""
            st = re.sub(r"fill:\s*[^;]+;?", "", st)
            el.set("style", (st + ";" if st and not st.endswith(";") else st)
                   + f"fill:url(#sphere{side});")
            el.attrib.pop("fill", None)
            n += 1
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return n


def svg_layer_order_report(fig):
    """Check that the layered SVG still paints the figure the PDF shows.

    `save_layered_svg` paints whole groups in the order background, lattice,
    gates, annotations, insets.  That is faithful only where it does not
    reorder two artists that actually overlap: if an artist in an earlier group
    has a HIGHER zorder than an overlapping artist in a later group, the SVG
    hides it and the PDF does not.

    Comparing zorder ranges alone over-reports, because two groups can share a
    zorder band and never touch on the page.  So each candidate inversion is
    confirmed by a bounding-box overlap; only confirmed ones are defects.
    """
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    items = {k: [] for k in SVG_LAYERS}
    for a in fig.findobj():
        gid = getattr(a, "get_gid", lambda: None)()
        if not gid:
            continue
        tag = str(gid).split(":", 1)[-1].split(".", 1)[0]
        if tag not in items:
            continue
        try:
            bb = a.get_window_extent(renderer=rend)
            z = float(a.get_zorder())
        except Exception:
            continue
        if bb.width <= 0 and bb.height <= 0:
            continue
        items[tag].append((z, bb, type(a).__name__))

    order = [k for k in SVG_LAYERS if items[k]]
    ranges = [(k, min(z for z, _, _ in items[k]),
               max(z for z, _, _ in items[k])) for k in order]
    confirmed = []
    for i, early in enumerate(order):
        for late in order[i + 1:]:
            for za, ba, ta in items[early]:
                for zb, bb, tb in items[late]:
                    if za <= zb:
                        continue
                    if (bb.x0 > ba.x1 or ba.x0 > bb.x1
                            or bb.y0 > ba.y1 or ba.y0 > bb.y1):
                        continue
                    confirmed.append((early, ta, za, late, tb, zb))
    return dict(layers=ranges, inversions=confirmed)


def save_all(fig, stem, dpi_png=300, svg=True, close=True):
    """Save one figure: PDF first (vector), then PNG, then the layered SVG.

    Order matters -- the PDF is the deliverable and is written before anything
    rasterises.  `dpi_png` is 300 for the check loop and 600 for the final
    `make figures`.  The figure is closed afterwards unless a caller still
    needs it, so a build of nine figures never holds more than one.
    """
    out = {"pdf": stem + ".pdf"}
    fig.savefig(out["pdf"])
    out["png"] = stem + ".png"
    fig.savefig(out["png"], dpi=dpi_png)
    if svg:
        d = os.path.join(FIGS, "svg")
        os.makedirs(d, exist_ok=True)
        out["svg"] = save_layered_svg(
            fig, os.path.join(d, os.path.basename(stem) + ".svg"))
    if close:
        plt.close(fig)
    return out

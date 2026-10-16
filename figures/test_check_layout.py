"""Self-test for the measurements in check_layout.py.

Two purpose-built probes, each isolating one measurement that was wrong before
2026-09-08 and that no real figure would have exposed on its own:

  probe_patch_transform   a label 0.30 mm from a filled rectangle.  Patch.get_transform()
                          already composes get_patch_transform(); composing it a second
                          time put every rectangle in the wrong place, so a genuine
                          collision measured as clear -- a false negative.
  probe_hidden_axis_ticks a note in the corner of an axes turned off with axis("off").
                          Its tick artists still report themselves as visible although
                          nothing is drawn, so the note collided with ticks that are not
                          on the page -- a false positive.

Run directly, or let figures/src/build.py run it before it builds anything.
"""
from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                        # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_layout as CL                                              # noqa: E402

MM = 1 / 25.4
GAP_MM = 0.30           # deliberately below MIN_TEXT_GRAPHIC_MM


def _bare(fig, off=False):
    ax = fig.add_axes([0.2, 0.2, 0.6, 0.6], label="p")
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    if off:
        ax.axis("off")
    else:
        ax.set_xticks([]); ax.set_yticks([])
    return ax


def probe_patch_transform():
    fig = plt.figure(figsize=(60 * MM, 40 * MM))
    ax = _bare(fig)
    ax.add_patch(plt.Rectangle((1, 1), 4, 4, facecolor="#0072B2", edgecolor="none"))
    per_mm = 10.0 / (0.6 * 60)                    # data units per millimetre
    ax.text(5 + GAP_MM * per_mm, 3, "label", fontsize=7, ha="left", va="center")
    return fig


def probe_hidden_axis_ticks():
    fig = plt.figure(figsize=(60 * MM, 40 * MM))
    ax = _bare(fig, off=True)
    ax.text(0.0, 0.0, "note at the corner", fontsize=7, ha="left", va="bottom")
    return fig


def _t2(fig, name):
    rep = CL.check(fig, name, None, ())
    c = next(x for x in rep["checks"] if x["id"] == "T2")
    return c["pass_"], c["detail"]


def main() -> int:
    bad = []

    ok, detail = _t2(probe_patch_transform(), "probe_patch_transform")
    if ok:
        bad.append("probe_patch_transform: T2 passed, but the label is "
                   f"{GAP_MM} mm from the rectangle and must be flagged")
    elif f"{GAP_MM:.1f}" not in detail and "0.3" not in detail:
        bad.append(f"probe_patch_transform: T2 flagged, but not at {GAP_MM} mm: "
                   f"{detail}")

    ok, detail = _t2(probe_hidden_axis_ticks(), "probe_hidden_axis_ticks")
    if not ok:
        bad.append("probe_hidden_axis_ticks: T2 failed against tick artists of an "
                   f"axes that draws none: {detail}")

    for b in bad:
        print("  FAIL " + b)
    if not bad:
        print("  check_layout self-test: 2 probes pass "
              "(patch placement, hidden-axis ticks)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())


def probe_boxed_text_exemption():
    """Round 7: a label with an OPAQUE box is legible over artwork behind it.

    T2 exists for legibility.  A white box behind a label delivers exactly that,
    so such a label must not be failed for sitting over a graphic it covers --
    but it must still be failed when the graphic is drawn *on top of* it, where
    the box does not help.  Both directions are probed.

    Expected: the covered case passes and is counted in `boxed_exempt`; the
    covering case still fails.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import figstyle as S
    import check_layout as CL
    S.use_style()

    out = {}
    for tag, gz in (("behind", 1), ("in_front", 9)):
        fig = plt.figure(figsize=(S.mm(60), S.mm(30)))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, 60)
        ax.set_ylim(0, 30)
        ax.axis("off")
        ax.plot([5, 55], [15, 15], color="#888888", lw=1.0, zorder=gz)
        ax.text(30, 15, "label", ha="center", va="center", zorder=5,
                fontsize=S.PT_MIN,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                          edgecolor="none"))
        rep = CL.check(fig, f"probe_boxed_{tag}")
        t2 = [c for c in rep["checks"] if c["id"] == "T2"][0]
        out[tag] = (t2["pass_"], rep.get("boxed_exempt", 0))
        plt.close(fig)
    ok = (out["behind"][0] and out["behind"][1] >= 1
          and not out["in_front"][0])
    return ok, out

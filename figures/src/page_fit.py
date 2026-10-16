"""Does figure + caption fit the text height of a journal page?

The caption is laid out for real at the caption size in the figure's own column
width, using the metrics of the figure font, and its height is (lines x leading).
A figure fails if figure height + separation + caption height exceeds the budget.
"""
from __future__ import annotations

import os
import sys

import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figstyle as S                                                   # noqa: E402

CAPTION_PT = 7.5          # caption type size
LEADING = 1.25            # baseline-to-baseline, as a multiple of the type size
SEP_MM = 3.5              # rule-of-thumb separation between artwork and caption
BUDGET_MM = 235.0         # usable text height of a two-column page
PT_MM = 25.4 / 72.0


def _measure(fig, rend, txt, pt):
    t = fig.text(0, 0, txt, fontsize=pt)
    w = t.get_window_extent(renderer=rend).width / fig.dpi * 25.4
    t.remove()
    return w


def wrap_lines(text: str, width_mm: float, pt: float = CAPTION_PT) -> int:
    """Number of lines the text occupies when set at `pt` in a `width_mm` column."""
    probe = plt.figure(figsize=(1, 1))
    rend = probe.canvas.get_renderer()
    space = _measure(probe, rend, "n n", pt) - _measure(probe, rend, "nn", pt)
    lines, cur = 1, 0.0
    for word in text.split():
        w = _measure(probe, rend, word, pt)
        if cur and cur + space + w > width_mm:
            lines += 1
            cur = w
        else:
            cur += (space + w) if cur else w
    plt.close(probe)
    return lines


def caption_mm(text: str, width_mm: float) -> tuple[int, float]:
    n = wrap_lines(text, width_mm)
    return n, n * CAPTION_PT * LEADING * PT_MM


def fit(entries) -> list[dict]:
    """entries: (name, width_mm, height_mm, caption_text)."""
    out = []
    for name, w, h, cap in entries:
        n, ch = caption_mm(cap, w)
        total = h + SEP_MM + ch
        out.append(dict(figure=name, width_mm=w, art_mm=h, caption_lines=n,
                        caption_mm=round(ch, 1), total_mm=round(total, 1),
                        budget_mm=BUDGET_MM, fits=total <= BUDGET_MM))
    return out

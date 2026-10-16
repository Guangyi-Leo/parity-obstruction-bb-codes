"""Strings that must not survive in a figure's text layer.

The revision retired a notation (`d in 8G`, `k = l = 3`, the Z32 cell) and
corrected a table reference.  A figure can still *look* right while the old
string sits in its PDF text layer, so each retired string is checked against
the layer itself rather than against the drawing code.

pdftotext is not assumed: PyMuPDF reads the layer directly.  A missing
extractor is a failure, never a silent pass -- that is exactly how a missing
`pdftotext` turned these checks green while proving nothing.

    python figures/src/check_figure_text.py
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FIGS = os.path.join(ROOT, "figures")

# figure stem -> patterns that must NOT appear in its text layer
FORBIDDEN = {
    "fig2_why_six_layers_fail":        [r"8G"],
    "fig3_where_depth6_is_attainable": [r"8G", r"Table S7"],
    "figS1_proof_map":                 [r"k\s*=\s*ℓ", r"8G", r"Z32"],
}
# and strings that must be present, so a "clean" grep cannot mean "empty figure"
REQUIRED = {
    "fig3_where_depth6_is_attainable": [r"ord\(d\) even", r"Table S9"],
    "figS1_proof_map":                 [r"w\s*A\s*=\s*w\s*B\s*=\s*3|wA\s*=\s*wB\s*=\s*3",
                                        r"2-height lemma"],
    "fig2_why_six_layers_fail":        [r"2-height"],
}


def text_of(pdf):
    try:
        import pymupdf
    except ImportError:                                  # pragma: no cover
        try:
            import fitz as pymupdf
        except ImportError:
            raise SystemExit("no PDF text extractor (pymupdf); cannot check "
                             "figure text layers -- refusing to report a pass")
    with pymupdf.open(pdf) as doc:
        return "".join(page.get_text() for page in doc)


def main() -> int:
    bad = []
    for stem in sorted(set(FORBIDDEN) | set(REQUIRED)):
        pdf = os.path.join(FIGS, stem + ".pdf")
        if not os.path.exists(pdf):
            bad.append((stem, "missing", pdf))
            print(f"  {stem:34s} MISSING {pdf}")
            continue
        t = text_of(pdf)
        hits = [p for p in FORBIDDEN.get(stem, []) if re.search(p, t)]
        miss = [p for p in REQUIRED.get(stem, []) if not re.search(p, t)]
        for p in hits:
            bad.append((stem, "forbidden", p))
        for p in miss:
            bad.append((stem, "missing string", p))
        status = "PASS" if not (hits or miss) else "FAIL"
        extra = ""
        if hits:
            extra += "  retired string still present: " + ", ".join(hits)
        if miss:
            extra += "  expected string absent: " + ", ".join(miss)
        print(f"  {stem:34s} {status}{extra}")
    if bad:
        print(f"\n  {len(bad)} figure-text defect(s)")
        return 1
    print("\n  every figure text layer is clean and carries the new notation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

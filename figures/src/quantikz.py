"""Compile a quantikz circuit with tectonic and hand it back as an image.

The Round 7 brief asks for the circuit insets to be set with quantikz rather
than drawn by hand, so they are compiled here by `tools/tectonic` (a static
binary; TinyTeX is untouched) and rasterised with PyMuPDF at 600 dpi for
placement inside a matplotlib scene.

Two consequences, both recorded in CHECK.md:
  * the inset is a raster inside an otherwise vector figure.  600 dpi at final
    print size is above the 300 dpi a journal asks for, and the PDF keeps it as
    a single image object.
  * check_layout.py cannot measure text it did not draw, so the type inside the
    inset is not covered by T1/T2.  The type size is therefore fixed in the TeX
    preamble at the same 6.5 pt floor the rest of the figure uses, and the
    compiled box is measured and reported instead.

The font is TeX Gyre Heros (`tgheros`, the same face the figures use), not
Computer Modern, so the inset does not read as a foreign object.
"""
from __future__ import annotations

import hashlib
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TECTONIC = os.path.join(ROOT, "tools", "tectonic")
CACHE = os.path.join(ROOT, "figures", "_quantikz")

PREAMBLE = r"""
\documentclass[border=1pt]{standalone}
\usepackage{tgheros}
\renewcommand{\familydefault}{\sfdefault}
\usepackage[T1]{fontenc}
\usepackage{amsmath}
\usepackage{tikz}
\usepackage{quantikz}
\usepackage{xcolor}
\renewcommand{\rmdefault}{qhv}
\begin{document}
\fontsize{6.5}{7.8}\selectfont
"""
POSTAMBLE = "\n\\end{document}\n"


def available() -> bool:
    return os.path.exists(TECTONIC)


def compile_tex(body: str, name: str, dpi: int = 600):
    """Compile `body`, returning (RGBA array, width_mm, height_mm).

    Results are cached on a hash of the source so `make figures` does not
    recompile unchanged circuits.
    """
    import numpy as np
    import pymupdf

    os.makedirs(CACHE, exist_ok=True)
    src = PREAMBLE + body + POSTAMBLE
    h = hashlib.sha1((src + f"|{dpi}").encode()).hexdigest()[:12]
    stem = os.path.join(CACHE, f"{name}_{h}")
    pdf = stem + ".pdf"
    if not os.path.exists(pdf):
        tex = stem + ".tex"
        with open(tex, "w") as f:
            f.write(src)
        r = subprocess.run([TECTONIC, "-X", "compile", tex, "--outfmt", "pdf",
                            "--outdir", CACHE, "-Z", "search-path=" + CACHE],
                           capture_output=True, text=True, timeout=600)
        if r.returncode != 0 or not os.path.exists(pdf):
            raise RuntimeError(f"tectonic failed for {name}:\n"
                               f"{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    doc = pymupdf.open(pdf)
    page = doc[0]
    w_mm = page.rect.width / 72.0 * 25.4
    h_mm = page.rect.height / 72.0 * 25.4
    pix = page.get_pixmap(dpi=dpi, alpha=True)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, pix.n)
    return arr, w_mm, h_mm


def place(ax, body, name, x, y, w_mm=None, h_mm=None, dpi=600, z=6):
    """Draw a compiled circuit into a millimetre axes with its top-left at (x, y).

    The circuit is scaled to `w_mm` if given (height follows, aspect kept), else
    to `h_mm`, else drawn at its natural size.  Returns the box actually used.
    """
    arr, nw, nh = compile_tex(body, name, dpi=dpi)
    if w_mm is not None:
        s = w_mm / nw
    elif h_mm is not None:
        s = h_mm / nh
    else:
        s = 1.0
    if w_mm is not None and h_mm is not None:
        s = min(w_mm / nw, h_mm / nh)
    W, H = nw * s, nh * s
    ax.imshow(arr, extent=(x, x + W, y - H, y), zorder=z,
              interpolation="antialiased")
    return dict(x=x, y=y, w=W, h=H, natural=(nw, nh), scale=s)

# Reference figures (Round 7, step 0)

Downloaded 2026-09-20 for **visual study only**. Nothing here is redrawn,
traced or reused in our figures; the Round 7 composites imitate *layout
conventions* (depth cues, icon families, leaders), not artwork.

Licences were read from the publisher/arXiv pages, not assumed. **One differs
from the Round 7 brief**: the Google Quantum AI figure is CC BY-NC-ND 4.0, not
CC BY 4.0 — ND forbids distributing an adapted version, so it is study-only.

| file | source | figure | licence | reuse |
|---|---|---|---|---|
| `bravyi_fig1.png` | Bravyi et al., *High-threshold and low-overhead fault-tolerant quantum memory*, Nature **627**, 778 (2024). https://www.nature.com/articles/s41586-024-07107-7 | Fig. 1, "Tanner graphs of surface and BB codes" | CC BY 4.0 | reusable with attribution (we do not reuse it) |
| `bravyi_fig2.png` | as above | Fig. 2, "Syndrome measurement circuit" (the 8-round timeline) | CC BY 4.0 | reusable with attribution (we do not reuse it) |
| `google_fig1.png` | Google Quantum AI, *Quantum error correction below the surface code threshold*, Nature **638**, 920 (2025). https://www.nature.com/articles/s41586-024-08449-y | Fig. 1, "Surface code performance" (device map + three data panels) | **CC BY-NC-ND 4.0** | study only; no adapted reuse |
| `shaw-terhal_fig1.png` | Shaw & Terhal, *Lowering connectivity requirements for bivariate bicycle codes using morphing circuits*, Phys. Rev. Lett. **134**, 090602 (2025); arXiv:2407.16336. https://arxiv.org/pdf/2407.16336 | Fig. 1, morphing-protocol schematic | CC BY 4.0 (arXiv) | reusable with attribution (we do not reuse it) |
| `yoder_fig1.png` | Yoder et al., *Tour de gross: a modular quantum computer based on bivariate bicycle codes*, arXiv:2506.03094. https://arxiv.org/pdf/2506.03094 | Fig. 1 (p. 3), "(a) Quantum architectures, (b) Logical capability estimates" | arXiv non-exclusive distribution licence 1.0 | **study only, no reuse** |

## Provenance of the crops

`bravyi_fig1.png`, `bravyi_fig2.png`, `google_fig1.png` are the publishers'
full-resolution PNGs (`media.springernature.com/full/...`), unmodified.

The two arXiv figures were extracted from the PDFs with PyMuPDF 1.28.2
(poppler is not installed in this environment; `pdftoppm` was unavailable):

    shaw-terhal_fig1.png  page 2, clip (50,46)-(300,136) pt, 400 dpi
    yoder_fig1.png        page 3, clip (55,425)-(540,642) pt, 200 dpi

Shaw & Terhal Fig. 1 is a single-column figure ~73 pt tall, so it was rendered
at 400 dpi rather than 200 to be legible; the brief's 200 dpi is used for
Yoder. Source PDFs are kept beside the crops (`shaw_terhal.pdf`, `yoder.pdf`).

The Nature article URLs answer 303 to an `idp.nature.com` cookie check; both
resolve to the article with `curl -L`. No URL was blocked.

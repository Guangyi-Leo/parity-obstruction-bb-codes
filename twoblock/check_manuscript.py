"""The manuscript's own acceptance checks, so they survive the session.

Five things the revision has to keep true:

  * the abstract is at most 150 words
  * no `% TODO` is left in the source
  * the retired notation is gone (`\\bar d`, `k\\ell`, `$k=\\ell`, `(k,\\ell)`,
    `d\\notin8G`, `8G\\setminus`)
  * no overfull box above 10 pt
  * no undefined reference or citation

Each one is reported with the evidence, and a missing build log is a failure
rather than a silent pass.

    python -m twoblock.check_manuscript
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "main.tex")
LOG = os.path.join(ROOT, "build_tex", "main.log")
ABSTRACT_MAX = 150
OVERFULL_MAX_PT = 10.0
RETIRED = [r"\bar d", r"k\ell", r"$k=\ell", r"(k,\ell)", r"d\notin8G",
           r"8G\setminus"]


def abstract_words(tex):
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    if not m:
        raise SystemExit("main.tex has no abstract")
    t = re.sub(r"(?<!\\)%.*", "", m.group(1))
    t = re.sub(r"\$[^$]*\$", "MATH", t)              # a formula is one token
    for _ in range(4):                               # keep \emph{...} contents
        t = re.sub(r"\\[a-zA-Z]+\s*(?:\[[^\]]*\])?\{([^{}]*)\}", r" \1 ", t)
    t = re.sub(r"\\[a-zA-Z]+", " ", t)
    t = re.sub(r"[{}~\\]", " ", t)
    return [w for w in t.split() if re.search(r"[A-Za-z0-9]", w)]


def main() -> int:
    bad = []

    def check(name, ok, detail=""):
        print(f"  {'PASS' if ok else 'FAIL'}  {name}{('  ' + detail) if detail else ''}")
        if not ok:
            bad.append(name)

    with open(TEX) as f:
        tex = f.read()

    n = len(abstract_words(tex))
    check(f"abstract <= {ABSTRACT_MAX} words", n <= ABSTRACT_MAX, f"({n})")

    todos = [i for i, ln in enumerate(tex.splitlines(), 1) if "TODO" in ln]
    check("no TODO left", not todos,
          "" if not todos else f"lines {todos}")

    hits = []
    for i, ln in enumerate(tex.splitlines(), 1):
        for pat in RETIRED:
            if pat in ln:
                hits.append((i, pat))
    check("retired notation gone", not hits,
          "" if not hits else f"{hits[:4]}")

    if not os.path.exists(LOG):
        check("build log present", False, f"{LOG} missing -- build first")
        return 1
    with open(LOG, errors="replace") as f:
        log = f.read()
    over = [(float(m.group(1)), m.group(0))
            for m in re.finditer(r"Overfull \\[hv]box \(([0-9.]+)pt too", log)]
    big = [o for o in over if o[0] > OVERFULL_MAX_PT]
    check(f"no overfull box above {OVERFULL_MAX_PT:g} pt", not big,
          f"({len(over)} overfull in all, largest "
          f"{max([o[0] for o in over], default=0):.2f} pt)")

    und = re.findall(r"(?:Reference|Citation) `([^']*)' on page", log)
    check("no undefined reference or citation", not und,
          "" if not und else f"{sorted(set(und))[:5]}")

    bangs = [ln for ln in log.splitlines() if ln.startswith("!")]
    check("no LaTeX errors", not bangs, "" if not bangs else f"{bangs[:2]}")

    if bad:
        print(f"\n  {len(bad)} manuscript check(s) failed: {', '.join(bad)}")
        return 1
    print("\n  the manuscript passes every acceptance check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

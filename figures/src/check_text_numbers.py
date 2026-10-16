"""Every number in the manuscript text must come from a file in the repository.

Usage
    python figures/src/check_text_numbers.py manuscript.tex --sections 4-5
    python figures/src/check_text_numbers.py --expect 1441,1440,417,...

The first form pulls every number out of the named sections of a .tex file.  The
second checks an explicit list, so the audit can be run before the .tex is in the
repository.  Either way each number is looked up in

    figures/derived_values.csv  named derivations (counts, minima, maxima)
    figures/figure_values.csv   every quantity any figure drew
    data/*.csv                  every numeric cell, and each file's row count
    data/*.json                 every numeric leaf
    tables/*.tex                the generated tables

With tens of thousands of source values almost any integer can be made to match
something, so a bare hit is not evidence.  Each number is graded:

    strong    exact match against a value a figure actually drew
              (figures/figure_values.csv) or against a generated table
    medium    exact match against a cell or a row count of a data file
    weak      only a rounded or unit-scaled match, i.e. some cell happens to round
              to it.  Weak is not an explanation; it is a number still to anchor.

Index-like columns (idx, solution, id) are not sources: an ordinal is not a
measured quantity.  Numbers graded weak, and numbers with no match at all, are
both reported as defects.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
NUM = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?(?![\w])")
SCALES = [10 ** k for k in range(-9, 10)]
# an ordinal is not a measured quantity
INDEX_COLS = {"idx", "index", "id", "solution", "n", "no", "row"}


def _f(tok: str):
    try:
        return float(tok.replace(",", ""))
    except ValueError:
        return None


# ---------------------------------------------------------------- sources
def sources() -> list[tuple[float, str, str]]:
    out: list[tuple[float, str]] = []

    p = os.path.join(ROOT, "figures", "derived_values.csv")
    if os.path.exists(p):
        with open(p) as f:
            for r in csv.DictReader(f):
                v = _f(r["value"])
                if v is not None:
                    out.append((v, f"derived:{r['name']} = {r['expression']} "
                                   f"over {r['source']}", "strong"))

    p = os.path.join(ROOT, "figures", "figure_values.csv")
    if os.path.exists(p):
        with open(p) as f:
            for r in csv.DictReader(f):
                v = _f(r["value"])
                if v is not None:
                    out.append((v, f"figure_values.csv {r['figure']}:{r['item']} "
                                   f"<- {r['source']}:{r['column']}", "strong"))

    for p in sorted(glob.glob(os.path.join(ROOT, "data", "*.csv"))):
        rel = os.path.relpath(p, ROOT)
        with open(p) as f:
            rows = list(csv.DictReader(f))
        out.append((float(len(rows)), f"{rel} (row count)", "medium"))
        for r in rows:
            for k, v in r.items():
                if (k or "").strip().lower() in INDEX_COLS:
                    continue
                x = _f(v or "")
                if x is not None:
                    out.append((x, f"{rel}:{k}", "medium"))

    for p in sorted(glob.glob(os.path.join(ROOT, "data", "*.json"))
                    + glob.glob(os.path.join(ROOT, "templates", "*.json"))):
        rel = os.path.relpath(p, ROOT)
        try:
            with open(p) as f:
                doc = json.load(f)
        except Exception:
            continue

        def walk(o, path=""):
            if isinstance(o, dict):
                for k, v in o.items():
                    walk(v, f"{path}.{k}" if path else str(k))
            elif isinstance(o, list):
                for v in o[:5000]:
                    walk(v, path)
            elif isinstance(o, (int, float)) and not isinstance(o, bool):
                out.append((float(o), f"{rel}:{path}", "medium"))
        walk(doc)

    for p in sorted(glob.glob(os.path.join(ROOT, "tables", "*.tex"))):
        rel = os.path.relpath(p, ROOT)
        with open(p) as f:
            for m in NUM.finditer(f.read()):
                v = _f(m.group(0))
                if v is not None:
                    out.append((v, rel, "strong"))
    return out


# ---------------------------------------------------------------- matching
def explain(tok: str, src, limit: int = 3):
    """Return (grade, [(rule, where, source_value), ...], n_exact)."""
    v = _f(tok)
    if v is None:
        return "none", [], 0
    dec = len(tok.split(".")[1]) if "." in tok else 0
    exact = [(g, where, x) for x, where, g in src if x == v]
    if exact:
        exact.sort(key=lambda h: 0 if h[0] == "strong" else 1)
        grade = exact[0][0]
        return grade, [("exact", w, x) for _, w, x in exact[:limit]], len(exact)
    loose = []
    for x, where, _g in src:
        if round(x, dec) == v and abs(x - v) < max(0.5 * 10 ** -dec, 1e-12):
            loose.append(("rounded", where, x))
        else:
            for sc in SCALES:
                if sc == 1:
                    continue
                y = x * sc
                if abs(y) > 1e12 or abs(y) < 1e-6:
                    continue
                if round(y, dec) == v:
                    loose.append((f"scaled x{sc:g}", where, x))
                    break
        if len(loose) >= limit:
            break
    return ("weak" if loose else "none"), loose, 0


# ---------------------------------------------------------------- tex input
def numbers_from_tex(path: str, sections: str | None):
    with open(path) as f:
        tex = f.read()
    tex = re.sub(r"(?<!\\)%.*", "", tex)
    for cmd in ("label", "ref", "eqref", "cite", "citep", "citet", "input",
                "includegraphics", "usepackage", "documentclass", "bibliography"):
        tex = re.sub(r"\\" + cmd + r"\s*(\[[^\]]*\])?\s*\{[^}]*\}", " ", tex)
    parts = re.split(r"\\section\*?\{", tex)
    if sections:
        lo, hi = (int(x) for x in sections.split("-")) if "-" in sections \
            else (int(sections), int(sections))
        keep = parts[lo:hi + 1]                      # parts[0] is the preamble
        if not keep:
            raise SystemExit(f"{path}: no sections {sections} (found {len(parts)-1})")
        tex = "\n".join(keep)
    return [m.group(0) for m in NUM.finditer(tex)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tex", nargs="*", help="LaTeX source to audit")
    ap.add_argument("--sections", default=None, help="e.g. 4-5")
    ap.add_argument("--expect", default=None,
                    help="comma-separated numbers to audit instead of a .tex")
    ap.add_argument("--anchors", default=os.path.join(ROOT, "figures",
                                                      "text_anchors.csv"),
                    help="number -> intended source, so a lucky match cannot pass")
    a = ap.parse_args()

    if a.tex:
        toks = []
        for p in a.tex:
            toks += numbers_from_tex(p, a.sections)
        origin = " + ".join(a.tex) + (f" sections {a.sections}" if a.sections else "")
    elif a.expect:
        toks = [t.strip() for t in a.expect.split(",") if t.strip()]
        origin = "--expect list"
    else:
        ap.error("give a .tex file or --expect")

    src = sources()
    anchors = {}
    if a.anchors and os.path.exists(a.anchors):
        with open(a.anchors) as f:
            for r in csv.DictReader(f):
                anchors.setdefault(r["number"].strip(), []).append(r)
    seen, order = set(), []
    for t in toks:
        if t not in seen:
            seen.add(t); order.append(t)

    print(f"# numbers audited: {len(order)} distinct, from {origin}")
    print(f"# sources: {len(src)} numeric values from figure_values.csv, data/, "
          f"templates/ and tables/\n")
    strong, medium, weak, none, mismatched, ambiguous = [], [], [], [], [], []
    for t in order:
        anc = anchors.get(t)
        if anc:
            want = anc[0]["source_contains"]
            sub = [(x, w, g) for x, w, g in src if want in w]
            grade, hits, n_exact = explain(t, sub) if sub else ("none", [], 0)
            if hits:
                rule, where, x = hits[0]
                extra = "" if rule == "exact" else f"  [{rule} from {x:g}]"
                print(f"  {t:>8s}  anchor {where}{extra}")
                print(f"            {anc[0]['note']}")
                strong.append(t)
            else:
                mismatched.append(t)
                have = sorted({x for x, w, _g in sub}) if sub else []
                got = (", ".join(f"{x:g}" for x in have[:4])
                       if have else "that source holds no value")
                print(f"  {t:>8s}  ANCHOR MISMATCH  {anc[0]['note']}: the anchored "
                      f"quantity is {got}")
            continue
        grade, hits, n_exact = explain(t, src)
        {"strong": strong, "medium": medium, "weak": weak,
         "none": none}[grade].append(t)
        if n_exact > 1:
            ambiguous.append((t, n_exact))
        if hits:
            rule, where, x = hits[0]
            extra = "" if rule == "exact" else f"  [{rule} from {x:g}]"
            amb = f"  (+{n_exact - 1} other exact sources)" if n_exact > 1 else ""
            print(f"  {t:>8s}  {grade:<6s} {where}{extra}{amb}")
        else:
            print(f"  {t:>8s}  {grade:<6s} NO SOURCE")
    print(f"\nanchored/strong {len(strong)}   medium {len(medium)}   "
          f"weak {len(weak)}   no source {len(none)}   anchor mismatch "
          f"{len(mismatched)}")
    bad = mismatched + weak + none
    if ambiguous:
        print("unanchored and ambiguous (an exact match, but to several different "
              "quantities; add a row to figures/text_anchors.csv to pin it): "
              + ", ".join(f"{t} ({n} sources)" for t, n in ambiguous))
    if bad:
        print("defects: " + ", ".join(bad))
        print("  a number is a defect when it has no exact source, when its only "
              "support is some cell that happens to round to it, or when it "
              "contradicts its anchor.")
    missing = bad
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())

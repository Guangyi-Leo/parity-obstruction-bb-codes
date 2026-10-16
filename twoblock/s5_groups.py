"""Two-divisibility of the defining element d, per class-C1 instance.

For each instance the defining element d is measured two ways:

    two_height(d)     largest j with d in 2^j G, computed by brute force over G
                      (reported as the cap when d is 2-divisible without bound)
    detected_by_Z2j   smallest j >= 1 for which some homomorphism G -> Z_{2^j} is
                      nonzero on d; blank when no power of two detects d

and joined with the depth-6 outcome and, where the instance is satisfiable, the
witness that resolved it.  Writes data/s5_groups.csv.
"""
from __future__ import annotations

import ast
import csv
import os

from .code import Group
from .encode import eps_value_m, homomorphisms_to_Zm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "s5_groups.csv")
J_CAP = 8                       # 2^8 = 256 > every |G| in the class-C1 set
FIELDS = ["instance", "group", "N", "v2_N", "d", "ord_d", "two_height",
          "two_height_unbounded",
          "detected_by_Z2j", "status_resolved", "resolved_by", "m_star", "twisted_ms",
          "witness_recorded"]


def _read(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return list(csv.DictReader(f))


def two_height(G: Group, d: tuple, cap: int = J_CAP):
    """max j with d in 2^j G, by brute force; (value, hit_cap)."""
    elems = list(G.elements)
    best = 0
    for j in range(cap + 1):
        img = set()
        for x in elems:
            acc, k, base = tuple(0 for _ in x), 1 << j, x
            while k:                              # 2^j * x by repeated doubling
                if k & 1:
                    acc = G.add(acc, base)
                base = G.add(base, base)
                k >>= 1
            img.add(acc)
        if tuple(d) in img:
            best = j
        else:
            return best, False
    return best, True


def detected_by(G: Group, d: tuple, cap: int = J_CAP):
    for j in range(1, cap + 1):
        m = 1 << j
        for h in homomorphisms_to_Zm(G, m):
            if eps_value_m(h["coeffs"], tuple(d), m) % m:
                return j
    return None


def main(argv=None):
    feats = {r["instance"]: r for r in _read("h4_features.csv")}
    fin = {r["instance"]: r for r in _read("c1_final_instances.csv")}
    out = []
    for name in sorted(fin):
        f, c = feats.get(name), fin[name]
        if not f or not f.get("d"):
            continue
        A = ast.literal_eval(f["A"])
        dims = tuple(int(x) for x in ast.literal_eval(f.get("dims", "null") or "null")
                     ) if f.get("dims") else None
        if dims is None:                      # reconstruct from the group name
            g = f["group"]
            dims = tuple(int(p[1:]) for p in g.split("x"))
        G = Group(dims)
        d = tuple(ast.literal_eval(f["d"]))
        th, capped = two_height(G, d)
        det = detected_by(G, d)
        tw = c.get("twisted_ms") or "[]"
        witness = bool(ast.literal_eval(tw)) or bool(c.get("m_star"))
        v2N = 0
        n = int(f["N"])
        while n % 2 == 0:
            n //= 2; v2N += 1
        out.append(dict(instance=name, group=f["group"], N=f["N"], v2_N=v2N,
                        d=f["d"], ord_d=f.get("ord_d", ""), two_height=th,
                        two_height_unbounded=capped,
                        detected_by_Z2j="" if det is None else det,
                        status_resolved=c.get("status_resolved", ""),
                        resolved_by=c.get("resolved_by", ""),
                        m_star=c.get("m_star", ""), twisted_ms=tw,
                        witness_recorded=witness))
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader(); w.writerows(out)
    print(f"  wrote {os.path.relpath(OUT, ROOT)}: {len(out)} rows")

    unb = [r for r in out if r["two_height_unbounded"]]
    deep = [r for r in out if r["two_height"] >= 3 and not r["two_height_unbounded"]]
    deep_sat = [r for r in deep if r["status_resolved"] == "SAT"]
    bad = [r for r in deep_sat if not r["witness_recorded"]]
    print(f"  two-height unbounded (odd 2-part: every element lies in 2^j G for all "
          f"j): {len(unb)} instances -- 'd in 8G' is vacuous there")
    print(f"  finite two_height(d) >= 3 (d in 8G, not deeper by accident): "
          f"{len(deep)} instances, {len(deep_sat)} of them SAT")
    print(f"  of those SAT, {len(deep_sat) - len(bad)} have a twisted witness recorded "
          f"with the m used; {len(bad)} do not")
    for r in bad:
        print(f"    MISSING WITNESS {r['instance']} {r['group']} d={r['d']} "
              f"two_height={r['two_height']} m_star={r['m_star']}")
    groups = sorted({r["group"] for r in deep_sat})
    print(f"  groups carrying them: {', '.join(groups)}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

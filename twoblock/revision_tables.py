"""CSVs for the revision's new results, so figures and text can read them.

Three products, each from an artefact that is already in the repository:

    data/cor3_hgp.csv       Corollary 3 applied to hypergraph products --
                            recomputed here, not copied from a log
    data/pareto_front.csv   the Pareto-optimal (k, d) pairs of the code search
    data/template_force.csv the forced-involution template runs, q = 32..512

The code search and the q >= 32 template runs take hours, so their CSVs are
parsed from the recorded run artefacts (``pareto_table.txt``, ``force*.log``)
rather than re-run; the Corollary 3 examples cost a second and are recomputed.
"""
from __future__ import annotations

import csv
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
# where the revision scripts and their run artefacts live
REV = os.path.join(ROOT, "revision", "scripts")
CODE = os.path.join(ROOT, "twoblock")


# ---------------------------------------------------------------- Corollary 3
# the hypergraph products quoted in the text, as (n of the seed circulant, taps)
HGP_SEEDS = [(7, (0, 1, 3)), (15, (0, 1, 4))]


def cor3_hgp(path=None):
    """Recompute the Corollary 3 examples with the revision's own hgp.py."""
    # hgp.py lives in the code directory (Task 5 moved the revision scripts
    # there); revision/scripts keeps only the recorded run artefacts
    if CODE not in sys.path:
        sys.path.insert(0, CODE)
    import numpy as np
    import networkx as nx
    import hgp as H                                   # the script of record

    rows = []
    for n, taps in HGP_SEEDS:
        h = H.circ(n, taps)
        HX, HZ = H.hgp(h, h)
        assert not ((HX @ HZ.T) % 2).any(), f"circulant_{n}: not a CSS code"
        nq = HX.shape[1]
        rv, sv = HX.sum(0), HZ.sum(0)
        g = nx.Graph()
        for i, j in zip(*np.nonzero(HX)):
            g.add_edge(("X", i), ("q", j))
        for i, j in zip(*np.nonzero(HZ)):
            g.add_edge(("Z", i), ("q", j))
        ncomp = nx.number_connected_components(g)
        k = nq - H.rank_f2(HX) - H.rank_f2(HZ)
        s = int((rv * sv).sum())
        rows.append(dict(seed=f"circulant_{n}", taps="+".join(f"x^{t}" for t in taps),
                         n=nq, k=k, w=int(set(HX.sum(1)).pop()),
                         components=ncomp, sum_rs=s, sum_rs_mod4=s % 4,
                         obstructed=(s % 4 == 2 and ncomp == 1)))
    p = path or os.path.join(DATA, "cor3_hgp.csv")
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return rows


# ---------------------------------------------------------------- Pareto front
PAR = re.compile(r"^\s*(\d+)\s+(\S+)\s+(\S+)\s+"
                 r"\[\[(\d+),(\d+),(<=)?(\d+)\]\]\s+(\S+)\s+"
                 r"(\[\[.*?\]\])\s+(\[\[.*?\]\])\s+(\S+)\s*$")


def pareto_front(path=None):
    src = os.path.join(REV, "pareto_table.txt")
    rows = []
    with open(src) as f:
        for line in f:
            m = PAR.match(line)
            if not m:
                continue
            (N, group, fam, n, k, le, d, exact, A, B, tag) = m.groups()
            rows.append(dict(N=int(N), group=group, family=fam, n=int(n),
                             k=int(k), d=int(d), d_exact=(exact != "-"),
                             d_label=("" if exact != "-" else "<=") + d,
                             A=A, B=B, tag=tag))
    assert rows, f"no rows parsed from {src}"
    p = path or os.path.join(DATA, "pareto_front.csv")
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return rows


# ------------------------------------------------------- forced-involution runs
FORCE = re.compile(r"^q=(\d+)\s+block-dependent universal sigma A:\s+"
                   r"(\d+)/(\d+)\s+SAT\s*$")


def template_force(path=None):
    rows = []
    for src in sorted(glob.glob(os.path.join(REV, "force*.log")),
                      key=lambda s: int(re.search(r"force(\d+)", s).group(1))):
        last = None
        with open(src) as f:
            for line in f:
                m = FORCE.match(line)
                if m:
                    last = m
        assert last, f"{src}: no summary line"
        q, got, want = (int(x) for x in last.groups())
        rows.append(dict(q=q, sat=got, total=want, all_sat=(got == want),
                         log=os.path.relpath(src, ROOT)))
    assert rows, "no force*.log found"
    p = path or os.path.join(DATA, "template_force.csv")
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return rows


# --------------------------------------------------- template key counts
# the manuscript lists one representative count per modulus; the enumeration
# is combinatorial and instant, so it is recomputed rather than read from a log
KEY_QS = [2, 4, 8, 16, 32, 64, 128, 256, 512]


def key_representatives(path=None):
    if CODE not in sys.path:
        sys.path.insert(0, CODE)
    from keys16 import representatives
    rows = [dict(q=q, representatives=len(representatives(q))) for q in KEY_QS]
    p = path or os.path.join(DATA, "rev_key_representatives.csv")
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return rows


def write_all():
    return dict(cor3_hgp=cor3_hgp(), pareto_front=pareto_front(),
                template_force=template_force(),
                rev_key_representatives=key_representatives())


if __name__ == "__main__":
    for name, rows in write_all().items():
        print(f"  data/{name}.csv  {len(rows)} rows")

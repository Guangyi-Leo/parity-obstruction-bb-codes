"""Pull each C1 template back onto a concrete code and re-check it by F2 simulation.

The template is enumerated on the *label* system: the eight sum classes are the seven
non-colliding label pairs plus the one designated colliding pair.  A concrete instance
can merge more classes than that -- two label pairs whose sums differ in G can have the
same image under eps -- and the interesting question is whether a template solution
still expands to a proper schedule there.  This test picks, for each modulus, keys whose
projected sums merge at least one pair beyond the designated collision, realises each on
the smallest cyclic group that carries it, expands the template solution and simulates.

Writes data/template_pullback.csv.  Run with `python -m tests.test_template_pullback`.
"""
from __future__ import annotations

import csv
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twoblock.code import TwoBlockCode                                  # noqa: E402
from twoblock.encode import (                                           # noqa: E402
    expand_twisted_schedule_Zm, solve_twisted_system,
)
from twoblock.overlaps import counts                                    # noqa: E402
from twoblock.simulate import (                                         # noqa: E402
    is_proper_by_simulation, is_valid_layering,
)
from twoblock.templates import DEPTH, K, L, deltas_for, load            # noqa: E402

MS = [2, 3, 4, 5, 6, 8]
PER_M = 3                       # keys to test per modulus
N_CAP = 12                      # largest multiple of m searched for a carrier group
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "data", "template_pullback.csv")


def parse_key(kk: str):
    head, sa, sb = kk.split("|")
    p, q = head.split("-")
    pat = ((int(p[0]), int(p[1])), (int(q[0]), int(q[1])))
    return pat, tuple(int(x) for x in sa.split(",")), tuple(int(x) for x in sb.split(","))


def extra_merges(pat, ea, eb, m) -> int:
    """How many sum classes the projection merges beyond the designated collision."""
    ds = deltas_for(pat, ea, eb, m)
    return len(ds) - len({ed for ed, _ in ds})


def carrier(pat, ea, eb, m, n_cap=N_CAP):
    """Smallest cyclic G = Z_N with eps(x) = x mod m realising the key in class C1."""
    (s, t), (s2, t2) = pat
    want = {(s, t), (s2, t2)}
    for N in range(m, n_cap * m + 1, m):
        if N < 8:
            continue
        r1 = [x for x in range(N) if x % m == ea[1] % m]
        r2 = [x for x in range(N) if x % m == ea[2] % m]
        q1 = [x for x in range(N) if x % m == eb[1] % m]
        q2 = [x for x in range(N) if x % m == eb[2] % m]
        for a1, a2, b1, b2 in itertools.product(r1, r2, q1, q2):
            A, B = [0, a1, a2], [0, b1, b2]
            if len(set(A)) != 3 or len(set(B)) != 3:
                continue
            P = {}
            for si, a in enumerate(A):
                for ti, b in enumerate(B):
                    P.setdefault((a + b) % N, []).append((si, ti))
            sizes = sorted(len(v) for v in P.values())
            if sizes != [1, 1, 1, 1, 1, 1, 1, 2]:
                continue
            pair = next(set(v) for v in P.values() if len(v) == 2)
            if pair != want:
                continue
            return N, A, B
    return None


def check_key(m, kk):
    pat, ea, eb = parse_key(kk)
    got = carrier(pat, ea, eb, m)
    if got is None:
        return dict(m=m, key=kk, G="", A="", B="", extra_merges=extra_merges(pat, ea, eb, m),
                    verdict="no carrier found")
    N, A, B = got
    code = TwoBlockCode((N,), [(x,) for x in A], [(x,) for x in B],
                        f"pb_m{m}_Z{N}")
    code.check_structure()
    assert counts(code)["klass"] == "C1", f"{code.name}: carrier is not class C1"

    ds = deltas_for(pat, ea, eb, m)
    labels = solve_twisted_system(K, L, list(ea), list(eb), ds, list(range(m)),
                                  DEPTH, m)
    assert labels is not None, f"m={m} key {kk}: template says admissible but the " \
                               f"label system is unsatisfiable"
    lay = expand_twisted_schedule_Zm(code, labels, (1,), m)
    valid = is_valid_layering(code, lay, DEPTH)
    proper = is_proper_by_simulation(code, lay, DEPTH)
    return dict(m=m, key=kk, G=f"Z{N}", A=str(A), B=str(B),
                extra_merges=extra_merges(pat, ea, eb, m),
                verdict="pass" if (valid and proper) else
                        ("invalid layering" if not valid else "not proper"))


def c3_chosen_key():
    """C3: the main-text key on three groups -- one cyclic, two non-cyclic."""
    from twoblock.encode import expand_twisted_schedule_Zm
    from twoblock.template_main import CHOSEN, parse_key, realisations

    pat, ea, eb = parse_key(CHOSEN["key"])
    m = CHOSEN["m"]
    from math import gcd

    def is_cyclic(d):
        # Z_a x Z_b is cyclic iff gcd(a, b) = 1, so Z2 x Z5 = Z10 does not count
        g = 0
        for x in d:
            g = gcd(g, x)
        return len(d) == 1 or g == 1

    picked, seen_dims = [], set()
    for N, dims, A, B, h in realisations(pat, ea, eb, m, n_max=28):
        cyclic = is_cyclic(dims)
        if dims in seen_dims:
            continue
        if cyclic and any(is_cyclic(d) for d in seen_dims):
            continue
        if not cyclic and sum(1 for d in seen_dims if not is_cyclic(d)) >= 2:
            continue
        seen_dims.add(dims)
        picked.append((N, dims, A, B, h))
        if len(picked) == 3:
            break

    rows = []
    ds = deltas_for(pat, ea, eb, m)
    labels = solve_twisted_system(K, L, list(ea), list(eb), ds, list(range(m)),
                                  DEPTH, m)
    for N, dims, A, B, h in picked:
        code = TwoBlockCode(tuple(dims), [tuple(x) for x in A],
                            [tuple(x) for x in B],
                            "c3_" + "x".join(f"Z{d}" for d in dims))
        code.check_structure()
        assert counts(code)["klass"] == "C1"
        lay = expand_twisted_schedule_Zm(code, labels, h["coeffs"], m)
        ok = is_valid_layering(code, lay, DEPTH) and \
            is_proper_by_simulation(code, lay, DEPTH)
        merged = extra_merges(pat, ea, eb, m)
        rows.append(dict(m=m, key=CHOSEN["key"],
                         G="x".join(f"Z{d}" for d in dims), A=str(A), B=str(B),
                         extra_merges=merged,
                         verdict="pass" if ok else "FAIL"))
        print(f"C3 {rows[-1]['G']:10s} N={N:3d} {'cyclic' if len(dims)==1 else 'non-cyclic':11s} "
              f"{rows[-1]['verdict']}")
    assert all(r["verdict"] == "pass" for r in rows), rows
    return rows


def test_template_pullback():
    rows, bad = [], []
    for m in MS:
        rec = load(m)
        if rec is None:
            print(f"T8 m={m}: no template on record")
            continue
        sat = sorted(rec["sat_set"])
        if not sat:
            print(f"T8 m={m}: 0 admissible keys, nothing to pull back")
            continue
        merged = [kk for kk in sat if extra_merges(*parse_key(kk), m) > 0]
        pick = merged[:PER_M]
        if len(pick) < PER_M:
            print(f"T8 m={m}: only {len(merged)} admissible keys merge an extra pair "
                  f"(of {len(sat)} admissible)")
        for kk in pick:
            r = check_key(m, kk)
            rows.append(r)
            if r["verdict"] != "pass":
                bad.append(r)
            print(f"T8 m={m} {r['G'] or '--':5s} +{r['extra_merges']} merged  "
                  f"{r['verdict']:16s} {kk}")
    rows += c3_chosen_key()
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["m", "key", "G", "A", "B", "extra_merges",
                                          "verdict"])
        w.writeheader(); w.writerows(rows)
    print(f"[wrote {os.path.relpath(OUT)}: {len(rows)} pullbacks, "
          f"{sum(1 for r in rows if r['verdict'] == 'pass')} pass]")
    assert not bad, f"template pullback failed on {bad}"
    print(f"T8: every template solution pulled back to a proper depth-{DEPTH} schedule "
          f"on a concrete class-C1 code ({len(rows)} cases)")


if __name__ == "__main__":
    test_template_pullback()

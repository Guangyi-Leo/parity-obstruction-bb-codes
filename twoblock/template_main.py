"""C2: choose the main-text template at m = 2 and emit it as a table.

Among the admissible m = 2 keys, take the one whose smallest realising instance is
connected, has k_logical >= 2 and the smallest N.  A realising instance is a class-C1
two-block code with a homomorphism eps: G -> Z_2 whose values on A and B are the key's,
and whose one colliding label pair is the key's designated pair.
"""
from __future__ import annotations

import itertools
import json
import os
from math import gcd

from .code import Group, TwoBlockCode
from .encode import eps_value_m, homomorphisms_to_Zm
from .templates import DEPTH, K, L, deltas_for, load

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_key(kk):
    head, sa, sb = kk.split("|")
    p, q = head.split("-")
    return (((int(p[0]), int(p[1])), (int(q[0]), int(q[1])))
            , [int(x) for x in sa.split(",")], [int(x) for x in sb.split(",")])


def abelian_groups(N: int):
    """Every abelian group of order N as a dims tuple, up to the obvious ordering."""
    out = []
    for a in range(1, N + 1):
        if N % a:
            continue
        b = N // a
        if a <= b:
            if a == 1:
                out.append((b,))
            else:
                out.append((a, b))
    return out


def realisations(pat, ea, eb, m, n_max=32):
    """Smallest realising instances, in order of N."""
    (s, t), (s2, t2) = pat
    want = {(s, t), (s2, t2)}
    for N in range(8, n_max + 1):
        for dims in abelian_groups(N):
            G = Group(dims)
            for h in homomorphisms_to_Zm(G, m):
                if h["trivial"]:
                    continue
                pre = {}
                for g in G.elements:
                    pre.setdefault(eps_value_m(h["coeffs"], g, m), []).append(g)
                if any(ea[i] not in pre for i in range(K)) or \
                   any(eb[i] not in pre for i in range(L)):
                    continue
                zero = tuple(0 for _ in dims)
                if ea[0] != eps_value_m(h["coeffs"], zero, m) or \
                   eb[0] != eps_value_m(h["coeffs"], zero, m):
                    continue
                for a1 in pre[ea[1]]:
                    for a2 in pre[ea[2]]:
                        A = [zero, a1, a2]
                        if len(set(A)) != 3:
                            continue
                        for b1 in pre[eb[1]]:
                            for b2 in pre[eb[2]]:
                                B = [zero, b1, b2]
                                if len(set(B)) != 3:
                                    continue
                                P = {}
                                for si, x in enumerate(A):
                                    for ti, y in enumerate(B):
                                        P.setdefault(G.add(x, y), []).append((si, ti))
                                if sorted(len(v) for v in P.values()) != \
                                        [1, 1, 1, 1, 1, 1, 1, 2]:
                                    continue
                                if next(set(v) for v in P.values()
                                        if len(v) == 2) != want:
                                    continue
                                yield N, dims, A, B, h


def evaluate(pat, ea, eb, m, n_max=32):
    """First realisation that is connected with k_logical >= 2."""
    from .components import components
    for N, dims, A, B, h in realisations(pat, ea, eb, m, n_max):
        code = TwoBlockCode(tuple(dims), [tuple(x) for x in A],
                            [tuple(x) for x in B], f"tpl_m{m}_{dims}")
        code.check_structure()
        comps = components(code)
        kl = code.logical_k()
        if len(comps) == 1 and kl >= 2:
            return dict(N=N, dims=dims, A=A, B=B, eps=h, k_logical=kl,
                        n_components=1)
    return None


def choose(m: int = 2, n_max: int = 32):
    rec = load(m)
    best = None
    for kk in sorted(rec["sat_set"]):
        pat, ea, eb = parse_key(kk)
        got = evaluate(pat, ea, eb, m, n_max)
        if got is None:
            continue
        got["key"] = kk
        got["pat"] = pat
        got["ea"], got["eb"] = ea, eb
        if best is None or got["N"] < best["N"] or (
                got["N"] == best["N"] and got["k_logical"] > best["k_logical"]):
            best = got
    return best


# --------------------------------------------------------------------------- tables
CHOSEN = dict(key="00-11|0,1,0|0,1,0", m=2, dims=(14,),
              A=[(0,), (1,), (10,)], B=[(0,), (13,), (2,)], eps_coeffs=(1,))
GRP_TEX = {("X", "L"): "$X$, $L$", ("X", "R"): "$X$, $R$",
           ("Z", "L"): "$Z$, $L$", ("Z", "R"): "$Z$, $R$"}


def solve_chosen(rec=None):
    from .encode import expand_twisted_schedule_Zm, solve_twisted_system
    from .simulate import is_proper_by_simulation, is_valid_layering
    rec = rec or CHOSEN
    pat, ea, eb = parse_key(rec["key"])
    m = rec["m"]
    labels = solve_twisted_system(K, L, ea, eb, deltas_for(pat, ea, eb, m),
                                  list(range(m)), DEPTH, m)
    assert labels is not None, "the chosen key is not admissible"
    code = TwoBlockCode(tuple(rec["dims"]), [tuple(x) for x in rec["A"]],
                        [tuple(x) for x in rec["B"]], "tpl_main")
    code.check_structure()
    lay = expand_twisted_schedule_Zm(code, labels, rec["eps_coeffs"], m)
    assert is_valid_layering(code, lay, DEPTH)
    assert is_proper_by_simulation(code, lay, DEPTH), "pullback is not proper"
    return dict(rec, pat=pat, ea=ea, eb=eb, labels=labels, code=code, lay=lay)


def _orient(labels, ea, eb, m, c, s, t, side):
    """Orientation of the corner: 1 iff the X-edge precedes the Z-edge."""
    if side == "L":
        x = labels[("X", "L")][c % m][s]
        z = labels[("Z", "L")][(c + ea[s] + eb[t]) % m][t]
    else:
        x = labels[("X", "R")][c % m][t]
        z = labels[("Z", "R")][(c + ea[s] + eb[t]) % m][s]
    return int(x < z), x, z


def constraints(sol) -> list[dict]:
    labels, ea, eb, m = sol["labels"], sol["ea"], sol["eb"], sol["m"]
    (s0, t0), (s1, t1) = sol["pat"]
    out = []
    for e in range(m):
        for fam, slots in (
            ("X-check, distinct layers",
             [(("X", "L"), s, e) for s in range(K)]
             + [(("X", "R"), t, e) for t in range(L)]),
            ("Z-check, distinct layers",
             [(("Z", "L"), t, e) for t in range(L)]
             + [(("Z", "R"), s, e) for s in range(K)]),
            ("$L$-qubit, distinct layers",
             [(("X", "L"), s, (e - ea[s]) % m) for s in range(K)]
             + [(("Z", "L"), t, (e + eb[t]) % m) for t in range(L)]),
            ("$R$-qubit, distinct layers",
             [(("X", "R"), t, (e - eb[t]) % m) for t in range(L)]
             + [(("Z", "R"), s, (e + ea[s]) % m) for s in range(K)]),
        ):
            lays = [labels[g][c][i] for g, i, c in slots]
            out.append(dict(family=fam, klass=e,
                            entries=", ".join(f"{GRP_TEX[g]}$_{{{i+1}}}$@{c}"
                                              for g, i, c in slots),
                            values=", ".join(str(v) for v in lays),
                            satisfied=len(set(lays)) == len(lays)))
    for e in range(m):
        for s in range(K):
            for t in range(L):
                if (s, t) in ((s0, t0), (s1, t1)):
                    continue
                oL, xL, zL = _orient(labels, ea, eb, m, e, s, t, "L")
                oR, xR, zR = _orient(labels, ea, eb, m, e, s, t, "R")
                out.append(dict(family=f"equal orientation $(s,t)=({s+1},{t+1})$",
                                klass=e,
                                entries=f"$o_L$ ({xL} vs {zL}), $o_R$ ({xR} vs {zR})",
                                values=f"{oL}, {oR}", satisfied=oL == oR))
    for e in range(m):
        bits = []
        for (s, t) in ((s0, t0), (s1, t1)):
            for side in ("L", "R"):
                bits.append(_orient(labels, ea, eb, m, e, s, t, side)[0])
        out.append(dict(family="four-corner parity (colliding pair)", klass=e,
                        entries=f"$o$ at $({s0+1},{t0+1})$ and $({s1+1},{t1+1})$, "
                                f"both sides",
                        values=", ".join(map(str, bits)),
                        satisfied=sum(bits) % 2 == 0))
    return out

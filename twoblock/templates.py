"""H4 step 5b -- eps-templates for class C1.

For a class-C1 instance the label-level twisted system depends on the group only
through

    * which two (s,t) pairs coincide (the C1 coincidence pattern), and
    * the vector (eps(a_1..3), eps(b_1..3)) in Z_m^6.

So the question "does a twisted depth-6 schedule exist?" can be tabulated once per m
by solving the 12m-variable problem over every eps-vector consistent with the
coincidence, with no reference to any particular code.  That table is the template.

Normalisation: instances are translation-normalised with 0 in A and 0 in B, and the
label lists are sorted, so a_1 = b_1 = 0 and hence eps(a_1) = eps(b_1) = 0.  The
template is enumerated under that normalisation, over all 18 coincidence patterns
{(s,t),(s',t')} with s != s' and t != t'.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

from .encode import solve_twisted_system

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = os.path.join(ROOT, "templates")
K = L = 3
DEPTH = 6


def patterns() -> list[tuple]:
    """All C1 coincidence patterns ((s,t),(s',t')) with s != s', t != t'."""
    out = []
    for ss in itertools.combinations(range(K), 2):
        for tt in itertools.combinations(range(L), 2):
            out.append(((ss[0], tt[0]), (ss[1], tt[1])))
            out.append(((ss[0], tt[1]), (ss[1], tt[0])))
    return out


def key(pat, ea, eb) -> str:
    (s, t), (s2, t2) = pat
    return (f"{s}{t}-{s2}{t2}|" + ",".join(map(str, ea)) + "|" + ",".join(map(str, eb)))


def deltas_for(pat, ea, eb, m) -> list[tuple]:
    """(eps(delta), [(s,t), ...]) groups: one doubleton and seven singletons."""
    (s, t), (s2, t2) = pat
    out = [((ea[s] + eb[t]) % m, [(s, t), (s2, t2)])]
    for ss in range(K):
        for tt in range(L):
            if (ss, tt) in ((s, t), (s2, t2)):
                continue
            out.append(((ea[ss] + eb[tt]) % m, [(ss, tt)]))
    return out


def _chunk(job) -> list[tuple[str, bool]]:
    m, pat, vecs = job
    E = list(range(m))
    cache: dict = {}
    out = []
    for ea, eb in vecs:
        ds = deltas_for(pat, ea, eb, m)
        sig = (tuple(ea), tuple(eb), tuple((d, tuple(v)) for d, v in ds))
        if sig not in cache:
            cache[sig] = solve_twisted_system(K, L, ea, eb, ds, E, DEPTH, m) is not None
        out.append((key(pat, ea, eb), cache[sig]))
    return out


def enumerate_vectors(pat, m) -> list[tuple]:
    """(ea, eb) in Z_m^6 with ea[0]=eb[0]=0 obeying the coincidence equation."""
    (s, t), (s2, t2) = pat
    out = []
    for ea1, ea2, eb1, eb2 in itertools.product(range(m), repeat=4):
        ea = (0, ea1, ea2)
        eb = (0, eb1, eb2)
        if (ea[s] + eb[t]) % m != (ea[s2] + eb[t2]) % m:
            continue
        out.append((ea, eb))
    return out


def expected_keys(m: int) -> int:
    """18 * m**3.

    There are 18 coincidence patterns, and for each one the normalised vector
    (ea, eb) has ea[0] = eb[0] = 0 -- four free coordinates in Z_m -- cut by
    the single coincidence equation ea[s] + eb[t] = ea[s'] + eb[t'] (mod m),
    which is solvable for one coordinate in terms of the others.  So m**3
    vectors per pattern.
    """
    return 18 * m ** 3


def build_template(m: int, workers: int = 12) -> dict:
    pats = patterns()
    jobs = []
    total = 0
    seen = set()
    for pat in pats:
        vecs = enumerate_vectors(pat, m)
        total += len(vecs)
        for ea, eb in vecs:
            kk = key(pat, ea, eb)
            assert kk not in seen, f"duplicate normalised key {kk}"
            seen.add(kk)
    assert total == expected_keys(m), (
        f"enumerator produced {total} keys, expected 18*{m}^3 = "
        f"{expected_keys(m)}")
    jobs = []
    for pat in pats:
        vecs = enumerate_vectors(pat, m)
        for i in range(0, len(vecs), 256):
            jobs.append((m, pat, vecs[i:i + 256]))
    t0 = time.time()
    sat_keys, n = [], 0
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for fut in as_completed([ex.submit(_chunk, j) for j in jobs]):
            for kk, ok in fut.result():
                n += 1
                if ok:
                    sat_keys.append(kk)
    rec = dict(m=m, D=DEPTH, k=K, l=L,
               normalisation="eps(a_1)=eps(b_1)=0 (0 in A and 0 in B, labels sorted)",
               key_format="s t - s' t' | eps(a_1),eps(a_2),eps(a_3) | eps(b_1),eps(b_2),eps(b_3)",
               n_patterns=len(pats), n_keys=n, n_sat=len(sat_keys),
               seconds=round(time.time() - t0, 1),
               sat_keys=sorted(sat_keys))
    assert n == total, f"{n} != {total}"
    return rec


def save(rec: dict) -> str:
    os.makedirs(TEMPLATES, exist_ok=True)
    p = os.path.join(TEMPLATES, f"C1_m{rec['m']}.json")
    with open(p, "w") as f:
        json.dump(rec, f)
    return p


def load(m: int) -> dict | None:
    p = os.path.join(TEMPLATES, f"C1_m{m}.json")
    if not os.path.exists(p):
        return None
    rec = json.load(open(p))
    rec["sat_set"] = set(rec.get("sat_keys") or [])
    rec.setdefault("exhaustive", True)
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build the class-C1 eps-templates.")
    ap.add_argument("--ms", default="2-12")
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args(argv)
    lo, hi = (int(x) for x in a.ms.split("-")) if "-" in a.ms else (int(a.ms), int(a.ms))
    for m in range(lo, hi + 1):
        rec = build_template(m, a.workers)
        p = save(rec)
        print(f"  m={m:2d}: {rec['n_keys']:7d} eps-vectors, {rec['n_sat']:7d} admit a "
              f"depth-{DEPTH} twisted schedule "
              f"({100*rec['n_sat']/max(rec['n_keys'],1):5.1f}%)  "
              f"{rec['seconds']:7.1f}s -> {os.path.relpath(p, ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# ---------------------------------------------------------------------------
# Characterising a template: is membership equivalent to a simple predicate?
# ---------------------------------------------------------------------------
def parse_key(kk: str):
    pat, ea, eb = kk.split("|")
    a, b = pat.split("-")
    pattern = ((int(a[0]), int(a[1])), (int(b[0]), int(b[1])))
    return pattern, tuple(int(x) for x in ea.split(",")), tuple(int(x) for x in eb.split(","))


def eps_d(pattern, ea, eb, m) -> int:
    """eps(d) where d = a_s - a_s' for the coincident pair."""
    (s, _t), (s2, _t2) = pattern
    return (ea[s] - ea[s2]) % m


def _ord_Zm(e: int, m: int) -> int:
    """Order of e in Z_m."""
    from math import gcd
    return m // gcd(m, e % m)


PREDICATES = {
    "ord_Zm(eps(d)) even": lambda e, m: _ord_Zm(e, m) % 2 == 0,
    "eps(d) != 0": lambda e, m: e % m != 0,
    "eps(d) odd": lambda e, m: (e % m) % 2 == 1,
    "v2(eps(d)) < v2(m)": lambda e, m: _v2(e % m) < _v2(m),
    "2*eps(d) != 0 mod m": lambda e, m: (2 * e) % m != 0,
}


def _v2(n: int) -> int:
    if n == 0:
        return 10 ** 6
    v = 0
    while n % 2 == 0:
        n //= 2
        v += 1
    return v


def characterise(m: int) -> dict:
    rec = load(m)
    if rec is None:
        return {}
    sat = rec["sat_set"]
    allk = []
    for pat in patterns():
        for ea, eb in enumerate_vectors(pat, m):
            allk.append((key(pat, ea, eb), pat, ea, eb))
    out = dict(m=m, n_keys=len(allk), n_sat=len(sat), predicates={})
    for name, fn in PREDICATES.items():
        agree = mism = 0
        for kk, pat, ea, eb in allk:
            e = eps_d(pat, ea, eb, m)
            if fn(e, m) == (kk in sat):
                agree += 1
            else:
                mism += 1
        out["predicates"][name] = dict(agree=agree, mismatch=mism,
                                       exact=mism == 0,
                                       rate=round(agree / len(allk), 4))
    return out


# ---------------------------------------------------------------------------
# Using a template: predict, for a code and an m, whether a twisted schedule exists
# ---------------------------------------------------------------------------
def instance_key(code, coeffs, m: int):
    """(template_m, key) for this code under eps = coeffs mod m, or None.

    If eps is not surjective its image is a subgroup gamma*Z_{m/gamma}; the system is
    then exactly the m' = m/gamma system with every eps-value divided by gamma, so the
    lookup is redirected to the template for m'.
    """
    from math import gcd

    from .encode import eps_value_m

    P = code.sum_sets()
    dbl = [(d, sts) for d, sts in P.items() if len(sts) == 2]
    if len(dbl) != 1 or any(len(v) > 2 for v in P.values()):
        return None                                     # not class C1
    (s, t), (s2, t2) = sorted(dbl[0][1])
    ea = [eps_value_m(coeffs, a, m) for a in code.A]
    eb = [eps_value_m(coeffs, b, m) for b in code.B]
    if not any(v % m for v in ea + eb):
        # eps is non-trivial on G but kills every a_s and b_t: each eps-class then
        # carries an independent copy of the *untwisted* system, so the answer is
        # whatever the untwisted problem gives -- which is UNSAT at depth 6 for C1.
        return "degenerate", None
    g = 0
    for v in ea + eb + [m]:
        g = gcd(g, v)
    g = g or m
    mp = m // g
    ea = tuple((v // g) % mp for v in ea)
    eb = tuple((v // g) % mp for v in eb)
    if ea[0] or eb[0]:
        return None                                     # normalisation broken
    return mp, key(((s, t), (s2, t2)), ea, eb)


def predict(code, m: int, cache: dict | None = None) -> bool | None:
    """Does some eps: G -> Z_m admit a twisted depth-6 schedule, per the templates?"""
    from .encode import homomorphisms_to_Zm

    cache = cache if cache is not None else {}
    any_known = False
    for h in homomorphisms_to_Zm(code.G, m):
        ik = instance_key(code, h["coeffs"], m)
        if ik is None:
            continue
        mp, kk = ik
        if mp == "degenerate":
            any_known = True            # decided: reduces to the untwisted system
            continue
        if mp not in cache:
            cache[mp] = load(mp)
        tpl = cache[mp]
        if tpl is None:
            continue                                    # template not built yet
        any_known = True
        if kk in tpl["sat_set"]:
            return True
    return False if any_known else None


# ---------------------------------------------------------------------------
# Theorem-backed templates for odd m
#
# A twisted schedule requires |M| even, where M = <eps(d)> <= Z_m.  For odd m every
# element of Z_m has odd order, so |M| is odd and no eps-vector can admit one.  Those
# templates are therefore recorded from the criterion rather than enumerated, with a
# random spot check reported separately.
# ---------------------------------------------------------------------------
THEOREM = ("theorem (under review): a twisted schedule requires |M| even, where "
           "M = <alpha_s - alpha_s', beta_t - beta_t'> <= Z_m is generated by all six "
           "label differences; for odd m every subgroup of Z_m has odd order, so "
           "|M| is odd")


def _spot_one(job):
    m, pat, ea, eb = job
    return solve_twisted_system(K, L, ea, eb, deltas_for(pat, ea, eb, m),
                                list(range(m)), DEPTH, m) is not None


def theorem_backed_template(m: int, spot: int = 500, seed: int = 7,
                            workers: int = 20) -> dict:
    import random as _r
    import time as _t
    from concurrent.futures import ProcessPoolExecutor

    assert m % 2 == 1, "theorem-backed shortcut applies to odd m only"
    pats = patterns()
    per = {pat: enumerate_vectors(pat, m) for pat in pats}
    n_keys = sum(len(v) for v in per.values())
    rng = _r.Random(seed)
    flat = [(pat, ea, eb) for pat in pats for (ea, eb) in per[pat]]
    sample = rng.sample(flat, min(spot, len(flat)))
    t0 = _t.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        got = list(ex.map(_spot_one, [(m, p, a, b) for p, a, b in sample]))
    admits = sum(1 for g in got if g)
    rec = dict(m=m, n_keys=n_keys, admit=0, source=THEOREM,
               D=DEPTH, k=K, l=L, exhaustive=False,
               normalisation="eps(a_1)=eps(b_1)=0 (0 in A and 0 in B, labels sorted)",
               key_format="s t - s' t' | eps(a_1),eps(a_2),eps(a_3) | eps(b_1),eps(b_2),eps(b_3)",
               n_patterns=len(pats), n_sat=0, sat_keys=[],
               spot_check=dict(n=len(sample), seed=seed, admits=admits,
                               result=f"spot check {admits}/{len(sample)}, "
                                      f"{'consistent with the theorem under review' if admits == 0 else 'CONTRADICTS THE THEOREM'}",
                               seconds=round(_t.time() - t0, 1)))
    return rec


# ---------------------------------------------------------------------------
# M = < all label differences >  <= Z_m   (the subgroup the theorem refers to)
# ---------------------------------------------------------------------------
def M_order(ea, eb, m: int) -> int:
    """|M| where M = <alpha_s - alpha_s', beta_t - beta_t'> <= Z_m."""
    from math import gcd
    g = m
    for v in ea:
        for w in ea:
            g = gcd(g, (v - w) % m)
    for v in eb:
        for w in eb:
            g = gcd(g, (v - w) % m)
    return m // g if g else 1


def theorem_table(m: int) -> dict:
    """Cross-tabulate |M| parity against template membership for one m."""
    rec = load(m)
    if rec is None or not rec.get("exhaustive", True):
        return {}
    sat = rec["sat_set"]
    tab = {"even": {"admit": 0, "no": 0}, "odd": {"admit": 0, "no": 0}}
    extras = []
    for pat in patterns():
        for ea, eb in enumerate_vectors(pat, m):
            kk = key(pat, ea, eb)
            par = "even" if M_order(ea, eb, m) % 2 == 0 else "odd"
            hit = kk in sat
            tab[par]["admit" if hit else "no"] += 1
            if par == "even" and not hit:
                extras.append((pat, ea, eb))
    return dict(m=m, n_keys=rec["n_keys"], n_admit=rec["n_sat"], table=tab,
                necessity_violations=tab["odd"]["admit"],
                sufficiency_gaps=tab["even"]["no"], gap_examples=extras[:5])


# ---------------------------------------------------------------------------
# P2 / R1 -- sufficiency and necessity counts on the even-m templates
# ---------------------------------------------------------------------------
def r1_counts(ms=(6, 8, 10, 12)) -> list[dict]:
    """For each m: does ord(eps(d)) even always admit?  do eps(d)=0 or |M| odd ever?"""
    from math import gcd
    out = []
    for m in ms:
        rec = load(m)
        if rec is None or not rec.get("exhaustive", True):
            out.append(dict(m=m, available=False))
            continue
        sat = rec["sat_set"]
        n_ord_even = n_ord_even_admit = 0
        n_epsd0_admit = n_Modd_admit = 0
        n_admit = 0
        for pat in patterns():
            for ea, eb in enumerate_vectors(pat, m):
                kk = key(pat, ea, eb)
                hit = kk in sat
                n_admit += hit
                e = eps_d(pat, ea, eb, m) % m
                ordq = m // gcd(m, e) if e else 1
                if ordq % 2 == 0:
                    n_ord_even += 1
                    n_ord_even_admit += hit
                if hit and e == 0:
                    n_epsd0_admit += 1
                if hit and M_order(ea, eb, m) % 2 == 1:
                    n_Modd_admit += 1
        out.append(dict(m=m, available=True, n_keys=rec["n_keys"], n_admit=n_admit,
                        ord_even_keys=n_ord_even, ord_even_admit=n_ord_even_admit,
                        sufficiency_holds=(n_ord_even == n_ord_even_admit),
                        epsd0_admit=n_epsd0_admit, M_odd_admit=n_Modd_admit))
    return out

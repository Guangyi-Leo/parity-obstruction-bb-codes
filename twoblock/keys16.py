"""
Enumerate class-schedule keys at modulus q = 2^j with dbar = q/2 (the only keys Theorem 12 needs after the
2-height reduction), up to the symmetries of the class system:
  * label permutations  -> designated collision fixed to {(1,1),(2,2)}, so alpha=(0,h,a3), beta=(0,h,b3), h=q/2
  * simultaneous swap of labels 1<->2 + renormalisation:  (a3,b3) ~ (a3+h, b3+h)
  * A<->B duality (L<->R):                                (a3,b3) ~ (b3,a3)
  * units w of Z_q (T'(c)=T(w^{-1}c)):                     (a3,b3) ~ (w a3, w b3)
Each representative is decided by SAT; optional structural hypothesis tested with extra clauses.
"""
import sys, itertools, time, math, json
sys.path.insert(0, '/mnt/user-data/outputs')
from pysat.solvers import Solver
from pysat.formula import IDPool


def units(q):
    return [w for w in range(1, q) if math.gcd(w, q) == 1]


def canon(q, a3, b3):
    h = q // 2
    best = None
    for w in units(q):
        for (x, y) in ((a3, b3), (b3, a3)):
            for sh in (0, h):
                key = ((w * (x + sh)) % q, (w * (y + sh)) % q)
                if best is None or key < best: best = key
    return best


def representatives(q):
    reps = {}
    for a3 in range(q):
        for b3 in range(q):
            reps.setdefault(canon(q, a3, b3), (a3, b3))
    return reps


def build(q, alpha, beta, des, D=6, structure=None):
    pool = IDPool(); clauses = []
    edges = [(c, k, lab) for c in range(q) for k in ('XL', 'XR', 'ZL', 'ZR') for lab in range(3)]
    x = {(e, i): pool.id(('x', e, i)) for e in edges for i in range(1, D + 1)}
    for e in edges:
        lits = [x[(e, i)] for i in range(1, D + 1)]; clauses.append(lits)
        clauses += [[-a, -b] for a, b in itertools.combinations(lits, 2)]
    def distinct(es):
        for i in range(1, D + 1):
            clauses.extend([-a, -b] for a, b in itertools.combinations([x[(e, i)] for e in es], 2))
    for c in range(q):
        distinct([(c, 'XL', s) for s in range(3)] + [(c, 'XR', t) for t in range(3)])
        distinct([(c, 'ZL', t) for t in range(3)] + [(c, 'ZR', s) for s in range(3)])
        distinct([((c - alpha[s]) % q, 'XL', s) for s in range(3)] + [((c + beta[t]) % q, 'ZL', t) for t in range(3)])
        distinct([((c - beta[t]) % q, 'XR', t) for t in range(3)] + [((c + alpha[s]) % q, 'ZR', s) for s in range(3)])
    def orient(ex, ez):
        o = pool.id(('o', ex, ez))
        for i in range(1, D + 1):
            for j in range(1, D + 1):
                if i < j: clauses.append([-x[(ex, i)], -x[(ez, j)], o])
                elif i > j: clauses.append([-x[(ex, i)], -x[(ez, j)], -o])
        return o
    (s1, t1), (s2, t2) = des
    for c in range(q):
        for s in range(3):
            for t in range(3):
                if (s, t) in des: continue
                cz = (c + alpha[s] + beta[t]) % q
                oL, oR = orient((c, 'XL', s), (cz, 'ZL', t)), orient((c, 'XR', t), (cz, 'ZR', s))
                clauses += [[-oL, oR], [oL, -oR]]
        cz = (c + alpha[s1] + beta[t1]) % q
        os = [orient((c, 'XL', s1), (cz, 'ZL', t1)), orient((c, 'XR', t1), (cz, 'ZR', s1)),
              orient((c, 'XL', s2), (cz, 'ZL', t2)), orient((c, 'XR', t2), (cz, 'ZR', s2))]
        for bits in itertools.product([0, 1], repeat=4):
            if sum(bits) % 2: clauses.append([(-o if b else o) for o, b in zip(os, bits)])
    if structure == 'antipodal-reversal':      # T(c+h, e) = 7 - T(c, e)
        h = q // 2
        for e in edges:
            c, k, lab = e; e2 = ((c + h) % q, k, lab)
            for i in range(1, D + 1):
                clauses += [[-x[(e, i)], x[(e2, D + 1 - i)]]]
    elif structure == 'antipodal-equal':       # T(c+h, e) = T(c, e)  (i.e. a Z_h-twist; must be UNSAT by Thm 3)
        h = q // 2
        for e in edges:
            c, k, lab = e; e2 = ((c + h) % q, k, lab)
            for i in range(1, D + 1):
                clauses += [[-x[(e, i)], x[(e2, i)]]]
    elif structure == 'antipodal-LR':          # T(c+h, XL, s) = T(c, XR, s) etc. (swap blocks at the antipode)
        h = q // 2
        sw = {'XL': 'XR', 'XR': 'XL', 'ZL': 'ZR', 'ZR': 'ZL'}
        for e in edges:
            c, k, lab = e; e2 = ((c + h) % q, sw[k], lab)
            for i in range(1, D + 1):
                clauses += [[-x[(e, i)], x[(e2, i)]]]
    return clauses, x


def solve(q, alpha, beta, des, structure=None):
    clauses, x = build(q, alpha, beta, des, structure=structure)
    with Solver(name='cadical195', bootstrap_with=clauses) as s:
        r = s.solve()
        if not r: return False, None
        model = set(l for l in s.get_model() if l > 0)
        return True, {e: i for (e, i), v in x.items() if v in model}


if __name__ == '__main__':
    q = int(sys.argv[1]); structure = sys.argv[2] if len(sys.argv) > 2 else None
    h = q // 2; des = ((0, 0), (1, 1))
    reps = representatives(q)
    print(f'q={q}: {q*q} keys with dbar=q/2 (designated {{(1,1),(2,2)}}), {len(reps)} inequivalent; structure={structure}', flush=True)
    t0 = time.time(); results = {}
    for key, (a3, b3) in sorted(reps.items()):
        alpha, beta = (0, h, a3), (0, h, b3)
        r, T = solve(q, alpha, beta, des, structure)
        results[str(key)] = (r, T if T is None else {f'{c},{k},{lab}': i for (c, k, lab), i in T.items()})
        print(f'  key a3={a3:3d} b3={b3:3d}: {"SAT" if r else "UNSAT"}   [{time.time()-t0:.0f}s]', flush=True)
    n_sat = sum(1 for v in results.values() if v[0])
    print(f'q={q} structure={structure}: {n_sat}/{len(reps)} representatives SAT  [{time.time()-t0:.0f}s]')
    with open(f'keys_q{q}_{structure}.json', 'w') as f: json.dump(results, f)

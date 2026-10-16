"""
Irreducible key family for dbar = q/2:  alpha = (0, h, 1), beta = (0, h, b), h = q/2, b in Z_q.
Test structural ansaetze for class schedules.
"""
import sys, itertools, time, json
sys.path.insert(0, '.')
from keys16 import build
from pysat.solvers import Solver
from pysat.formula import IDPool

D = 6
KINDS = ('XL', 'XR', 'ZL', 'ZR')


def solve(q, b, ansatz=None, want_model=False):
    h = q // 2; alpha, beta = (0, h, 1), (0, h, b); des = ((0, 0), (1, 1))
    clauses, x = build(q, alpha, beta, des)
    top = max(abs(l) for cl in clauses for l in cl)
    pool = IDPool(start_from=top + 1)
    edges = sorted(set(e for (e, i) in x))
    if ansatz == 'sigma-half':          # T(c+h, e) = sigma(T(c, e)) for a solver-chosen permutation sigma of [6]
        sg = {(i, j): pool.id(('sg', i, j)) for i in range(1, D + 1) for j in range(1, D + 1)}
        for i in range(1, D + 1):
            clauses.append([sg[(i, j)] for j in range(1, D + 1)])
            clauses.append([sg[(j, i)] for j in range(1, D + 1)])
            for j1, j2 in itertools.combinations(range(1, D + 1), 2):
                clauses += [[-sg[(i, j1)], -sg[(i, j2)]], [-sg[(j1, i)], -sg[(j2, i)]]]
        for (c, k, lab) in edges:
            e2 = ((c + h) % q, k, lab)
            for i in range(1, D + 1):
                for j in range(1, D + 1):
                    clauses.append([-x[((c, k, lab), i)], -sg[(i, j)], x[(e2, j)]])
    elif ansatz == 'sigma-half-typed':  # sigma may depend on the edge type (XL/XR/ZL/ZR)
        for k in KINDS:
            sg = {(i, j): pool.id(('sg', k, i, j)) for i in range(1, D + 1) for j in range(1, D + 1)}
            for i in range(1, D + 1):
                clauses.append([sg[(i, j)] for j in range(1, D + 1)])
                clauses.append([sg[(j, i)] for j in range(1, D + 1)])
                for j1, j2 in itertools.combinations(range(1, D + 1), 2):
                    clauses += [[-sg[(i, j1)], -sg[(i, j2)]], [-sg[(j1, i)], -sg[(j2, i)]]]
            for (c, kk, lab) in edges:
                if kk != k: continue
                e2 = ((c + h) % q, k, lab)
                for i in range(1, D + 1):
                    for j in range(1, D + 1):
                        clauses.append([-x[((c, k, lab), i)], -sg[(i, j)], x[(e2, j)]])
    elif ansatz == 'sigma-two':         # T(c+2, e) = sigma(T(c, e)) for a solver-chosen sigma (period-2 up to a permutation)
        sg = {(i, j): pool.id(('sg', i, j)) for i in range(1, D + 1) for j in range(1, D + 1)}
        for i in range(1, D + 1):
            clauses.append([sg[(i, j)] for j in range(1, D + 1)])
            clauses.append([sg[(j, i)] for j in range(1, D + 1)])
            for j1, j2 in itertools.combinations(range(1, D + 1), 2):
                clauses += [[-sg[(i, j1)], -sg[(i, j2)]], [-sg[(j1, i)], -sg[(j2, i)]]]
        for (c, k, lab) in edges:
            e2 = ((c + 2) % q, k, lab)
            for i in range(1, D + 1):
                for j in range(1, D + 1):
                    clauses.append([-x[((c, k, lab), i)], -sg[(i, j)], x[(e2, j)]])
    elif ansatz and ansatz.startswith('typed:'):   # T(c) depends only on a feature of c
        feat = {'parity+half': lambda c: (c % 2, c >= h), 'parity+quarter': lambda c: (c % 2, (4 * c) // q),
                'mod4+half': lambda c: (c % 4, c >= h), 'parity+eighth': lambda c: (c % 2, (8 * c) // q),
                'mod4+quarter': lambda c: (c % 4, (4 * c) // q)}[ansatz[6:]]
        groups = {}
        for c in range(q): groups.setdefault(feat(c), []).append(c)
        for cs in groups.values():
            for c in cs[1:]:
                for k in KINDS:
                    for lab in range(3):
                        for i in range(1, D + 1):
                            clauses += [[-x[((cs[0], k, lab), i)], x[((c, k, lab), i)]]]
    with Solver(name='cadical195', bootstrap_with=clauses) as s:
        r = s.solve()
        if not r or not want_model: return r, None
        model = set(l for l in s.get_model() if l > 0)
        return r, {e: i for (e, i), v in x.items() if v in model}


if __name__ == '__main__':
    q = int(sys.argv[1]); ansatz = sys.argv[2] if len(sys.argv) > 2 else None
    if ansatz == 'None': ansatz = None
    t0 = time.time(); res = {}
    for b in range(q):
        r, _ = solve(q, b, ansatz)
        res[b] = bool(r)
    print(f'q={q} ansatz={ansatz}: SAT for b in {[b for b in range(q) if res[b]]}; UNSAT for {[b for b in range(q) if not res[b]]}  [{time.time()-t0:.0f}s]', flush=True)

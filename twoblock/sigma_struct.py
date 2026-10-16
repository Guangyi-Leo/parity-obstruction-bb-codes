import sys, itertools; sys.path.insert(0, '.')
from keys16 import build
from pysat.solvers import Solver
from pysat.formula import IDPool
D = 6; KINDS = ('XL', 'XR', 'ZL', 'ZR')
def solve_typed(q, b, fixed_sigma=None):
    h = q // 2; alpha, beta = (0, h, 1), (0, h, b); des = ((0, 0), (1, 1))
    clauses, x = build(q, alpha, beta, des)
    top = max(abs(l) for cl in clauses for l in cl)
    pool = IDPool(start_from=top + 1)
    edges = sorted(set(e for (e, i) in x))
    sg = {}
    for k in KINDS:
        for i in range(1, D + 1):
            for j in range(1, D + 1):
                sg[(k, i, j)] = pool.id(('sg', k, i, j))
        for i in range(1, D + 1):
            clauses.append([sg[(k, i, j)] for j in range(1, D + 1)])
            clauses.append([sg[(k, j, i)] for j in range(1, D + 1)])
            for j1, j2 in itertools.combinations(range(1, D + 1), 2):
                clauses += [[-sg[(k, i, j1)], -sg[(k, i, j2)]], [-sg[(k, j1, i)], -sg[(k, j2, i)]]]
        for (c, kk, lab) in edges:
            if kk != k: continue
            e2 = ((c + h) % q, k, lab)
            for i in range(1, D + 1):
                for j in range(1, D + 1):
                    clauses.append([-x[((c, k, lab), i)], -sg[(k, i, j)], x[(e2, j)]])
    if fixed_sigma:
        for k in KINDS:
            for i in range(1, D + 1):
                clauses.append([sg[(k, i, fixed_sigma[k][i - 1])]])
    with Solver(name='cadical195', bootstrap_with=clauses) as s:
        if not s.solve(): return None
        model = set(l for l in s.get_model() if l > 0)
        sig = {k: tuple(next(j for j in range(1, D + 1) if sg[(k, i, j)] in model) for i in range(1, D + 1)) for k in KINDS}
        T = {e: i for (e, i), v in x.items() if v in model}
        return sig, T
if __name__ == '__main__':
    q = int(sys.argv[1])
    for b in range(q):
        r = solve_typed(q, b)
        if r is None: print(f'q={q} b={b}: UNSAT'); continue
        sig, T = r
        print(f'q={q} b={b}: ' + '  '.join(f'{k}:{sig[k]}' for k in KINDS))

import sys, itertools; sys.path.insert(0, '.')
from keys16 import build
from pysat.solvers import Solver
from pysat.formula import IDPool
D = 6; KINDS = ('XL', 'XR', 'ZL', 'ZR')
def joint(q, bs, forced=None):
    """one CNF: for every b in bs a copy of the class system of kappa_q(1,b) with the ansatz
    T_b(c+h,e) = sigma_type(T_b(c,e)); the four sigma's are shared by all copies."""
    h = q // 2; des = ((0, 0), (1, 1))
    all_clauses = []; offset = 0; xs = []
    for b in bs:
        clauses, x = build(q, (0, h, 1), (0, h, b), des)
        top = max(abs(l) for cl in clauses for l in cl)
        all_clauses += [[(l + offset if l > 0 else l - offset) for l in cl] for cl in clauses]
        xs.append({k: v + offset for k, v in x.items()})
        offset += top
    pool = IDPool(start_from=offset + 1)
    sg = {(k, i, j): pool.id(('sg', k, i, j)) for k in KINDS for i in range(1, D + 1) for j in range(1, D + 1)}
    for k in KINDS:
        for i in range(1, D + 1):
            all_clauses.append([sg[(k, i, j)] for j in range(1, D + 1)])
            all_clauses.append([sg[(k, j, i)] for j in range(1, D + 1)])
            for j1, j2 in itertools.combinations(range(1, D + 1), 2):
                all_clauses += [[-sg[(k, i, j1)], -sg[(k, i, j2)]], [-sg[(k, j1, i)], -sg[(k, j2, i)]]]
    for x in xs:
        edges = sorted(set(e for (e, i) in x))
        for (c, k, lab) in edges:
            e2 = ((c + h) % q, k, lab)
            for i in range(1, D + 1):
                for j in range(1, D + 1):
                    all_clauses.append([-x[((c, k, lab), i)], -sg[(k, i, j)], x[(e2, j)]])
    if forced:
        for k in KINDS:
            for i in range(1, D + 1): all_clauses.append([sg[(k, i, forced[k][i - 1])]])
    with Solver(name='cadical195', bootstrap_with=all_clauses) as s:
        if not s.solve(): return None
        model = set(l for l in s.get_model() if l > 0)
        return {k: tuple(next(j for j in range(1, D + 1) if sg[(k, i, j)] in model) for i in range(1, D + 1)) for k in KINDS}
if __name__ == '__main__':
    q = int(sys.argv[1])
    r = joint(q, list(range(q)))
    print(f'q={q}: universal type-dependent sigma for all b:', r)

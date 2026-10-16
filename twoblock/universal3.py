import sys, itertools; sys.path.insert(0, '.')
from keys16 import build
from pysat.solvers import Solver
from pysat.formula import IDPool
D = 6; KINDS = ('XL', 'XR', 'ZL', 'ZR')
def joint_sym(q, bs, pairs):
    h = q // 2; des = ((0, 0), (1, 1)); all_clauses = []; offset = 0; xs = []
    for b in bs:
        clauses, x = build(q, (0, h, 1), (0, h, b), des)
        top = max(abs(l) for cl in clauses for l in cl)
        all_clauses += [[(l + offset if l > 0 else l - offset) for l in cl] for cl in clauses]
        xs.append({k: v + offset for k, v in x.items()}); offset += top
    pool = IDPool(start_from=offset + 1)
    sg = {(k, i, j): pool.id(('sg', k, i, j)) for k in KINDS for i in range(1, D + 1) for j in range(1, D + 1)}
    for k in KINDS:
        for i in range(1, D + 1):
            all_clauses.append([sg[(k, i, j)] for j in range(1, D + 1)]); all_clauses.append([sg[(k, j, i)] for j in range(1, D + 1)])
            for j1, j2 in itertools.combinations(range(1, D + 1), 2):
                all_clauses += [[-sg[(k, i, j1)], -sg[(k, i, j2)]], [-sg[(k, j1, i)], -sg[(k, j2, i)]]]
    for (k1, k2) in pairs:
        for i in range(1, D + 1):
            for j in range(1, D + 1):
                all_clauses += [[-sg[(k1, i, j)], sg[(k2, i, j)]], [sg[(k1, i, j)], -sg[(k2, i, j)]]]
    for x in xs:
        for (c, k, lab) in sorted(set(e for (e, i) in x)):
            e2 = ((c + h) % q, k, lab)
            for i in range(1, D + 1):
                for j in range(1, D + 1):
                    all_clauses.append([-x[((c, k, lab), i)], -sg[(k, i, j)], x[(e2, j)]])
    with Solver(name='cadical195', bootstrap_with=all_clauses) as s:
        if not s.solve(): return None
        model = set(l for l in s.get_model() if l > 0)
        return {k: tuple(next(j for j in range(1, D + 1) if sg[(k, i, j)] in model) for i in range(1, D + 1)) for k in KINDS}
q = int(sys.argv[1]); bs = list(range(q))
print(f'q={q} sigma_XL=sigma_ZR, sigma_XR=sigma_ZL:', joint_sym(q, bs, [('XL', 'ZR'), ('XR', 'ZL')]), flush=True)
print(f'q={q} sigma_XL=sigma_XR, sigma_ZL=sigma_ZR:', joint_sym(q, bs, [('XL', 'XR'), ('ZL', 'ZR')]), flush=True)
print(f'q={q} sigma_XL=sigma_ZL, sigma_XR=sigma_ZR:', joint_sym(q, bs, [('XL', 'ZL'), ('XR', 'ZR')]), flush=True)

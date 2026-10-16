import sys, itertools; sys.path.insert(0, '.')
from keys16 import build
from pysat.solvers import Solver
from pysat.formula import IDPool
D = 6; KINDS = ('XL', 'XR', 'ZL', 'ZR')
SA = {'XL': (3,4,1,2,6,5), 'ZL': (3,4,1,2,6,5), 'XR': (2,1,6,5,4,3), 'ZR': (2,1,6,5,4,3)}
def solve(q, b, shift2, typed=True, fix_top=True):
    h = q // 2; alpha, beta = (0, h, 1), (0, h, b); des = ((0, 0), (1, 1))
    clauses, x = build(q, alpha, beta, des)
    top = max(abs(l) for cl in clauses for l in cl); pool = IDPool(start_from=top + 1)
    edges = sorted(set(e for (e, i) in x))
    def add_perm(name, kinds_group, shift, fixed=None):
        sg = {(i, j): pool.id((name, i, j)) for i in range(1, D + 1) for j in range(1, D + 1)}
        for i in range(1, D + 1):
            clauses.append([sg[(i, j)] for j in range(1, D + 1)]); clauses.append([sg[(j, i)] for j in range(1, D + 1)])
            for j1, j2 in itertools.combinations(range(1, D + 1), 2):
                clauses.extend([[-sg[(i, j1)], -sg[(i, j2)]], [-sg[(j1, i)], -sg[(j2, i)]]])
        if fixed:
            for i in range(1, D + 1): clauses.append([sg[(i, fixed[i - 1])]])
        for (c, k, lab) in edges:
            if k not in kinds_group: continue
            e2 = ((c + shift) % q, k, lab)
            for i in range(1, D + 1):
                for j in range(1, D + 1):
                    clauses.append([-x[((c, k, lab), i)], -sg[(i, j)], x[(e2, j)]])
    # level 1: block-dependent universal sigma, shift h
    add_perm('sL', ('XL', 'ZL'), h, SA['XL'] if fix_top else None)
    add_perm('sR', ('XR', 'ZR'), h, SA['XR'] if fix_top else None)
    # level 2: shift2 with solver-chosen permutation per type (or per block)
    if typed:
        for k in KINDS: add_perm('t' + k, (k,), shift2)
    else:
        add_perm('tL', ('XL', 'ZL'), shift2); add_perm('tR', ('XR', 'ZR'), shift2)
    with Solver(name='cadical195', bootstrap_with=clauses) as s:
        return s.solve()
q = int(sys.argv[1]); h = q // 2
for typed in (True, False):
    res = [solve(q, b, h // 2, typed=typed) for b in range(q)]
    print(f'q={q}: level-1 sigma A at shift {h}, level-2 {"type" if typed else "block"}-dependent permutation at shift {h//2}: SAT for b in {[b for b in range(q) if res[b]]}', flush=True)

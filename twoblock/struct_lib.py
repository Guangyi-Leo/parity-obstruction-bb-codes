import sys, itertools
sys.path.insert(0, '.')
from keys16 import build
from pysat.solvers import Solver

def solve_with_typing(q, alpha, beta, des, typ):
    """impose T(c, e) = T(c', e) whenever typ(c) == typ(c')"""
    clauses, x = build(q, alpha, beta, des)
    groups = {}
    for c in range(q): groups.setdefault(typ(c), []).append(c)
    for cs in groups.values():
        c0 = cs[0]
        for c in cs[1:]:
            for k in ('XL', 'XR', 'ZL', 'ZR'):
                for lab in range(3):
                    for i in range(1, 7):
                        clauses += [[-x[((c0, k, lab), i)], x[((c, k, lab), i)]]]
    with Solver(name='cadical195', bootstrap_with=clauses) as s:
        return s.solve()

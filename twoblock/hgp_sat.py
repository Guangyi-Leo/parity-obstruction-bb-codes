import sys, itertools, time, threading
import numpy as np
from hgp import circ, hgp
from pysat.solvers import Solver
from pysat.formula import IDPool

def encode(HX, HZ, D):
    """generic CSS encoder: edges (type, check, qubit); properness per overlapping pair"""
    pool = IDPool(); clauses = []
    edges = [('X', i, j) for i, j in zip(*np.nonzero(HX))] + [('Z', i, j) for i, j in zip(*np.nonzero(HZ))]
    x = {(e, l): pool.id(('x', e, l)) for e in edges for l in range(1, D + 1)}
    for e in edges:
        lits = [x[(e, l)] for l in range(1, D + 1)]; clauses.append(lits)
        clauses += [[-a, -b] for a, b in itertools.combinations(lits, 2)]
    byv = {}
    for e in edges:
        byv.setdefault(('q', e[2]), []).append(e); byv.setdefault((e[0], e[1]), []).append(e)
    for es in byv.values():
        for l in range(1, D + 1):
            clauses += [[-a, -b] for a, b in itertools.combinations([x[(e, l)] for e in es], 2)]
    def orient(ex, ez):
        o = pool.id(('o', ex, ez))
        for i in range(1, D + 1):
            for j in range(1, D + 1):
                if i < j: clauses.append([-x[(ex, i)], -x[(ez, j)], o])
                elif i > j: clauses.append([-x[(ex, i)], -x[(ez, j)], -o])
        return o
    xq = {}; zq = {}
    for e in edges: (xq if e[0] == 'X' else zq).setdefault(e[2], []).append(e)
    pairs = {}
    for q in xq:
        for ex in xq[q]:
            for ez in zq.get(q, []): pairs.setdefault((ex[1], ez[1]), []).append((ex, ez))
    for cs in pairs.values():
        lits = [orient(ex, ez) for ex, ez in cs]
        acc = lits[0]
        for l in lits[1:-1]:
            t = pool.id(('t', acc, l)); clauses += [[-acc, -l, -t], [acc, l, -t], [-acc, l, t], [acc, -l, t]]; acc = t
        clauses += [[-acc, lits[-1]], [acc, -lits[-1]]]
    return clauses, x, edges

H = circ(7, (0, 1, 3)); HX, HZ = hgp(H, H)
for D, cap in ((7, 900), (6, 900)):
    clauses, x, edges = encode(HX, HZ, D)
    t0 = time.time()
    with Solver(name='cadical195', bootstrap_with=clauses) as s:
        timer = threading.Timer(cap, s.interrupt); timer.start()
        r = s.solve_limited(expect_interrupt=True); timer.cancel()
    print(f'HGP(7) [[98,18]]: depth {D}: {"SAT" if r else ("UNSAT" if r is False else "capped")}  ({time.time()-t0:.0f}s, {len(clauses)} clauses)', flush=True)

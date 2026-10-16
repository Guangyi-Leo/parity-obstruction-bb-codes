#!/usr/bin/env python3
"""
Independent re-implementation used to cross-check the manuscript
"A parity obstruction to degree-optimal syndrome extraction in bivariate bicycle codes".

Requires: numpy, networkx, python-sat  (pip install numpy networkx python-sat)

Sub-commands
  python independent_check.py tableI      # Prop. 8: Table I schedule proper (corner parity + F2 simulation) on the 7 BB codes
  python independent_check.py identity    # Eq.(2)/(4) equivalence and the Theorem-1 identity on random depth-6 layerings
  python independent_check.py sat         # depth-6 refutations: [[72,12,6]], [[90,8,10]], Z9 / Z3xZ3 orbits, Z10; depth 7 SAT
  python independent_check.py z14         # Theorem 12 example: Z14, A={0,1,10}, B={0,13,2}; Table S3 template pulled back
  python independent_check.py s2          # counterexample to Theorem S2 as stated (k even): Z12, A={0,1}, B={0,4,8}, a=2
  python independent_check.py ti          # Theorem 2 / Prop. 8: no TI proper schedule at depth 6, 8496 at depth 7
  python independent_check.py classes q   # re-enumerate the class-schedule keys of Prop. 11 / Table S2 for modulus q
"""
import sys, itertools, random, time, math
import numpy as np


# ----------------------------------------------------------------------------- groups and codes
class Group:
    def __init__(self, orders):
        self.orders = tuple(orders)
        self.elems = list(itertools.product(*[range(n) for n in self.orders]))
        self.index = {g: i for i, g in enumerate(self.elems)}
        self.N = len(self.elems)
    def add(self, g, h): return tuple((a + b) % n for a, b, n in zip(g, h, self.orders))
    def sub(self, g, h): return tuple((a - b) % n for a, b, n in zip(g, h, self.orders))
    def smul(self, k, g): return tuple((k * a) % n for a, n in zip(g, self.orders))
    def zero(self): return tuple(0 for _ in self.orders)
    def order(self, g):
        k, x = 1, g
        while any(x): x = self.add(x, g); k += 1
        return k


class TwoBlockCode:
    """X_g: L_{g+a_s} (label s), R_{g+b_t} (label t);  Z_g: L_{g-b_t} (label t), R_{g-a_s} (label s)."""
    def __init__(self, G, A, B):
        self.G, self.A, self.B = G, [tuple(a) for a in A], [tuple(b) for b in B]
        self.edges = []
        for g in G.elems:
            self.edges += [('XL', g, s) for s in range(len(self.A))]
            self.edges += [('XR', g, t) for t in range(len(self.B))]
            self.edges += [('ZL', g, t) for t in range(len(self.B))]
            self.edges += [('ZR', g, s) for s in range(len(self.A))]
    def qubit(self, e):
        kind, g, lab = e; G, N = self.G, self.G.N
        if kind == 'XL': return G.index[G.add(g, self.A[lab])]
        if kind == 'XR': return N + G.index[G.add(g, self.B[lab])]
        if kind == 'ZL': return G.index[G.sub(g, self.B[lab])]
        if kind == 'ZR': return N + G.index[G.sub(g, self.A[lab])]
    def check(self, e): return (e[0][0], e[1])
    def HX_HZ(self):
        N = self.G.N
        HX = np.zeros((N, 2 * N), dtype=np.uint8); HZ = np.zeros((N, 2 * N), dtype=np.uint8)
        for e in self.edges:
            (HX if e[0][0] == 'X' else HZ)[self.G.index[e[1]], self.qubit(e)] ^= 1
        return HX, HZ
    def sums(self): return [self.G.add(a, b) for a in self.A for b in self.B]
    def distinct_sums(self): s = self.sums(); return len(set(s)) == len(s)
    def overlap_multiplicities(self):
        S = {}
        for s in self.sums(): S[s] = S.get(s, 0) + 1
        return S
    def pairs(self):
        xq, zq = {}, {}
        for e in self.edges:
            (xq if e[0][0] == 'X' else zq).setdefault(self.qubit(e), []).append(e)
        corners = {}
        for q in xq:
            for ex in xq[q]:
                for ez in zq.get(q, []):
                    corners.setdefault((ex[1], ez[1]), []).append((q, ex, ez))
        return corners


def rank_f2(M):
    M = M.copy() % 2; r = 0; rows, cols = M.shape
    for c in range(cols):
        piv = next((i for i in range(r, rows) if M[i, c]), None)
        if piv is None: continue
        M[[r, piv]] = M[[piv, r]]
        for i in range(rows):
            if i != r and M[i, c]: M[i] ^= M[r]
        r += 1
        if r == rows: break
    return r


# ----------------------------------------------------------------------------- schedules and checks
def is_layering(code, pi):
    seen = set()
    for e, i in pi.items():
        for v in (('q', code.qubit(e)), code.check(e)):
            if (v, i) in seen: return False
            seen.add((v, i))
    return True


def corner_parity_ok(code, pi):
    bad = sum(1 for cs in code.pairs().values() if sum(pi[ex] < pi[ez] for (_, ex, ez) in cs) % 2)
    return bad == 0, bad


def f2_simulate(code, pi):
    """Compose the CNOT layers as an F2-linear map on (x, y, z); return (M_pi, whole map matches Eq. (1))."""
    N = code.G.N; n = 2 * N; dim = n + 2 * N
    T = np.eye(dim, dtype=np.uint8)
    for layer in range(1, max(pi.values()) + 1):
        for e, i in pi.items():
            if i != layer: continue
            q, gi = code.qubit(e), code.G.index[e[1]]
            c, t = (n + gi, q) if e[0][0] == 'X' else (q, n + N + gi)
            T[t] ^= T[c]
    HX, HZ = code.HX_HZ()
    I = np.eye(dim, dtype=np.uint8)
    ok = (np.array_equal(T[:n, :n], I[:n, :n]) and np.array_equal(T[:n, n:n + N], HX.T)
          and np.array_equal(T[n:n + N], I[n:n + N]) and np.array_equal(T[n + N:, :n], HZ)
          and np.array_equal(T[n + N:, n + N:], I[n + N:, n + N:]))
    return T[n + N:, n:n + N].copy(), ok


def verify(code, pi, name=''):
    ok_lay = is_layering(code, pi); ok_par, bad = corner_parity_ok(code, pi); M, ok_lin = f2_simulate(code, pi)
    print(f'{name}: depth={max(pi.values())} layering={ok_lay} corner-parity proper={ok_par} (bad pairs {bad}) '
          f'F2-sim map ok={ok_lin} M_pi==0: {not M.any()}')
    return ok_lay and ok_par and ok_lin and not M.any()


def ti_schedule(code, table):
    return {e: table[e[0]][e[2]] for e in code.edges}


def twisted_schedule(code, eps, T):
    return {e: T[(eps(e[1]), e[0], e[2])] for e in code.edges}


# ----------------------------------------------------------------------------- SAT encoding
def encode_depth(code, D):
    from pysat.formula import IDPool
    pool = IDPool(); clauses = []
    x = {(e, i): pool.id(('x', e, i)) for e in code.edges for i in range(1, D + 1)}
    for e in code.edges:
        lits = [x[(e, i)] for i in range(1, D + 1)]
        clauses.append(lits)
        clauses += [[-a, -b] for a, b in itertools.combinations(lits, 2)]
    byv = {}
    for e in code.edges:
        byv.setdefault(('q', code.qubit(e)), []).append(e); byv.setdefault(code.check(e), []).append(e)
    for es in byv.values():
        for i in range(1, D + 1):
            clauses += [[-a, -b] for a, b in itertools.combinations([x[(e, i)] for e in es], 2)]
    def orient(ex, ez):
        o = pool.id(('o', ex, ez))
        for i in range(1, D + 1):
            for j in range(1, D + 1):
                if i < j: clauses.append([-x[(ex, i)], -x[(ez, j)], o])
                elif i > j: clauses.append([-x[(ex, i)], -x[(ez, j)], -o])
        return o
    def xor_zero(lits):
        acc = lits[0]
        for l in lits[1:-1]:
            t = pool.id(('t', acc, l))
            clauses.extend([[-acc, -l, -t], [acc, l, -t], [-acc, l, t], [acc, -l, t]]); acc = t
        clauses.extend([[-acc, lits[-1]], [acc, -lits[-1]]])
    for cs in code.pairs().values():
        xor_zero([orient(ex, ez) for (_, ex, ez) in cs])
    return clauses, x, pool


def solve_depth(code, D, extra=(), time_limit=None):
    from pysat.solvers import Solver
    import threading
    clauses, x, pool = encode_depth(code, D); clauses += list(extra(x) if callable(extra) else extra)
    t0 = time.time()
    with Solver(name='cadical195', bootstrap_with=clauses) as s:
        if time_limit:
            timer = threading.Timer(time_limit, s.interrupt); timer.start()
            res = s.solve_limited(expect_interrupt=True); timer.cancel()
        else:
            res = s.solve()
        dt = time.time() - t0
        if res:
            model = set(l for l in s.get_model() if l > 0)
            pi = {e: i for (e, i), v in x.items() if v in model}
            print(f'  SAT   depth {D}  ({dt:.1f}s)'); return True, pi
        print(f'  {"UNSAT" if res is False else "capped"} depth {D}  ({dt:.1f}s)'); return res, None


# ----------------------------------------------------------------------------- data
BB = {
 '[[72,12,6]]':   ((6, 6),  [(3,0),(0,1),(0,2)],   [(0,3),(1,0),(2,0)]),
 '[[90,8,10]]':   ((15,3),  [(9,0),(0,1),(0,2)],   [(0,3),(2,0),(7,0)]),
 '[[108,8,10]]':  ((9, 6),  [(3,0),(0,1),(0,2)],   [(0,3),(1,0),(2,0)]),
 '[[144,12,12]]': ((12,6),  [(3,0),(0,1),(0,2)],   [(0,3),(1,0),(2,0)]),
 '[[288,12,18]]': ((12,12), [(3,0),(0,2),(0,7)],   [(0,3),(1,0),(2,0)]),
 '[[360,12,24]]': ((30,6),  [(9,0),(0,1),(0,2)],   [(0,3),(25,0),(26,0)]),
 '[[756,16,34]]': ((21,18), [(3,0),(0,10),(0,17)], [(0,5),(3,0),(19,0)]),
}
TABLE_I = {'XL': [1, 2, 7], 'XR': [4, 3, 5], 'ZL': [5, 3, 4], 'ZR': [6, 7, 1]}
TABLE_S3 = {0: {'XL': [3,6,1], 'XR': [4,2,5], 'ZL': [5,3,2], 'ZR': [1,4,6]},
            1: {'XL': [5,4,2], 'XR': [1,3,6], 'ZL': [4,6,1], 'ZR': [3,2,5]}}


def bb_codes():
    return {name: TwoBlockCode(Group(lm), A, B) for name, (lm, A, B) in BB.items()}


def components(code):
    import networkx as nx
    Gr = nx.Graph()
    for e in code.edges: Gr.add_edge(('c',) + code.check(e), ('q', code.qubit(e)))
    return list(nx.connected_components(Gr))


# ----------------------------------------------------------------------------- sub-commands
def cmd_tableI():
    for name, code in bb_codes().items():
        l, m = code.G.orders; HX, HZ = code.HX_HZ()
        print(f'{name}: distinct sums={code.distinct_sums()}, lm={l*m}, sum r_v s_v mod 4 = {(18*l*m)%4}, '
              f'Tanner components={len(components(code))}, k={2*code.G.N-rank_f2(HX)-rank_f2(HZ)}')
        verify(code, ti_schedule(code, TABLE_I), '  Table I')


def random_layering(code, D, rng):
    import networkx as nx
    remaining = set(code.edges); pi = {}
    for layer in range(1, D + 1):
        H = nx.Graph(); top = set()
        for e in remaining:
            u = ('c',) + code.check(e); v = ('q', code.qubit(e)); H.add_edge(u, v, e=e); top.add(u)
        nodes = list(H.nodes()); rng.shuffle(nodes)
        H2 = nx.Graph(); H2.add_nodes_from(nodes); H2.add_edges_from(H.edges(data=True))
        M = nx.bipartite.hopcroft_karp_matching(H2, top_nodes=[n for n in nodes if n in top])
        for u in top:
            e = H2[u][M[u]]['e']; pi[e] = layer; remaining.discard(e)
    return pi


def cmd_identity(trials=30):
    code = bb_codes()['[[72,12,6]]']; G = code.G; rng = random.Random(1)
    HX, HZ = code.HX_HZ(); rv, sv = HX.sum(0), HZ.sum(0); target = int((rv * sv).sum()) // 2
    agree = ident = 0
    for _ in range(trials):
        pi = random_layering(code, 6, rng); assert is_layering(code, pi)
        M, ok = f2_simulate(code, pi); assert ok
        P = np.zeros_like(M); tot = 0
        for (gx, gz), cs in code.pairs().items():
            n1 = sum(pi[ex] < pi[ez] for (_, ex, ez) in cs); tot += n1; P[G.index[gz], G.index[gx]] = n1 % 2
        agree += np.array_equal(M, P); ident += (tot == target)
    print(f'[[72,12,6]]: M_pi == corner-parity matrix on {agree}/{trials} random depth-6 layerings; '
          f'sum_v N_v = (1/2) sum_v r_v s_v = {target} on {ident}/{trials}')


def cmd_sat():
    codes = bb_codes()
    print('[[72,12,6]] depth 7:'); r, pi = solve_depth(codes['[[72,12,6]]'], 7); verify(codes['[[72,12,6]]'], pi, '  solver')
    print('[[72,12,6]] depth 6 (Theorem 7):'); solve_depth(codes['[[72,12,6]]'], 6)
    print('[[90,8,10]] depth 6 (Theorem 1):'); solve_depth(codes['[[90,8,10]]'], 6, time_limit=600)
    for orders, A, B in [((9,), [(0,),(1,),(2,)], [(0,),(3,),(6,)]),
                         ((3,3), [(0,0),(0,1),(0,2)], [(0,0),(1,0),(2,0)]),
                         ((3,3), [(0,0),(0,1),(0,2)], [(0,0),(1,0),(2,1)]),
                         ((10,), [(0,),(3,),(6,)], [(0,),(1,),(9,)])]:
        c = TwoBlockCode(Group(orders), A, B)
        print(f'G={orders} A={A} B={B} distinct sums={c.distinct_sums()} depth 6:'); solve_depth(c, 6, time_limit=600)


def cmd_z14():
    G = Group((14,)); code = TwoBlockCode(G, [(0,),(1,),(10,)], [(0,),(13,),(2,)])
    HX, HZ = code.HX_HZ()
    print('overlap multiplicities:', sorted(code.overlap_multiplicities().values(), reverse=True),
          ' n =', 2 * G.N, ' k =', 2 * G.N - rank_f2(HX) - rank_f2(HZ))
    T = {(c, k, lab): lay for c in (0, 1) for k, lays in TABLE_S3[c].items() for lab, lay in enumerate(lays)}
    verify(code, twisted_schedule(code, lambda g: g[0] % 2, T), '  Table S3 pulled back along g mod 2')
    print('solver, depth 6:'); r, pi = solve_depth(code, 6, time_limit=600)
    if pi: verify(code, pi, '  solver')


def cmd_s2():
    G = Group((12,)); code = TwoBlockCode(G, [(0,),(1,)], [(0,),(4,),(8,)])   # k=2, l=3, Delta=5, a=(l+1)/2=2
    def extra(x):
        return [[-x[(e, 1)]] for e in code.edges if e[0] == 'XL'] + [[-x[(e, 5)]] for e in code.edges if e[0] == 'XL']
    print('Z12, A={0,1}, B={0,4,8}, depth 5, X L-edges confined to layers [2,4] (a=2, b=4):')
    r, pi = solve_depth(code, 5, extra=extra)
    if pi:
        verify(code, pi, '  found'); print('  X L-edge layers used:', sorted(set(pi[e] for e in code.edges if e[0] == 'XL')))


def cmd_ti():
    for D in (6, 7):
        found = 0
        for X in itertools.permutations(range(1, D + 1), 6):
            XL, XR = X[:3], X[3:]
            for Z in itertools.permutations(range(1, D + 1), 6):
                ZL, ZR = Z[:3], Z[3:]
                if set(XL) & set(ZL) or set(XR) & set(ZR): continue
                if all((XL[s] < ZL[t]) == (XR[t] < ZR[s]) for s in range(3) for t in range(3)): found += 1
        print(f'depth {D}: translation-invariant proper schedules (distinct sums): {found}')


def class_schedule_exists(q, alpha, beta, des, D=6):
    from pysat.solvers import Solver
    from pysat.formula import IDPool
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
    with Solver(name='cadical195', bootstrap_with=clauses) as sv:
        return sv.solve()


def cmd_classes(q):
    keys = []
    for (s1, s2) in itertools.combinations(range(3), 2):
        for (t1, t2) in itertools.combinations(range(3), 2):
            for des in (((s1, t1), (s2, t2)), ((s1, t2), (s2, t1))):
                for a2, a3, b2, b3 in itertools.product(range(q), repeat=4):
                    alpha, beta = (0, a2, a3), (0, b2, b3); (sa, ta), (sb, tb) = des
                    if (alpha[sa] + beta[ta] - alpha[sb] - beta[tb]) % q == 0: keys.append((alpha, beta, des))
    adm = adm0 = 0; t0 = time.time()
    for alpha, beta, des in keys:
        (sa, ta), (sb, tb) = des; dbar = (alpha[sb] - alpha[sa]) % q
        if class_schedule_exists(q, alpha, beta, des):
            adm += 1; adm0 += (dbar == 0)
    n_nz = sum(1 for a, b, d in keys if (a[d[1][0]] - a[d[0][0]]) % q)
    print(f'q={q}: keys={len(keys)} (18q^3={18*q**3}); admissible={adm}; admissible with dbar=0: {adm0}; '
          f'keys with dbar!=0: {n_nz}  [{time.time()-t0:.0f}s]')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'tableI'
    {'tableI': cmd_tableI, 'identity': cmd_identity, 'sat': cmd_sat, 'z14': cmd_z14, 's2': cmd_s2, 'ti': cmd_ti,
     'classes': lambda: cmd_classes(int(sys.argv[2]))}[cmd]()

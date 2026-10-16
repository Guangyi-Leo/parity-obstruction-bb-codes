import sys, random; sys.path.insert(0, '/mnt/user-data/outputs'); sys.path.insert(0, '.')
from independent_check import Group, TwoBlockCode, twisted_schedule, verify
from pullback_demo import class_schedule
from tb import Grp, build_H, isd_distance, code_k
def run(name, orders, A, B, q, eps):
    G = Group(orders); code = TwoBlockCode(G, A, B)
    S = code.overlap_multiplicities()
    delta0 = next(x for x, m in S.items() if m == 2)
    pairs = [(s, t) for s, a in enumerate(A) for t, b in enumerate(B) if G.add(a, b) == delta0]
    des = (pairs[0], pairs[1])
    alpha = tuple(eps(a) for a in A); beta = tuple(eps(b) for b in B)
    d = G.sub(A[des[1][0]], A[des[0][0]])
    print(f'{name}: collision {des} d={d} ord={G.order(d)}; q={q} key alpha={alpha} beta={beta} dbar={(alpha[des[1][0]]-alpha[des[0][0]])%q}')
    T = class_schedule(q, alpha, beta, des)
    assert T is not None
    for c in range(q):
        print(f'   class {c}: ' + '  '.join(f'{k}={[T[(c,k,l)] for l in range(3)]}' for k in ('XL','XR','ZL','ZR')))
    pi = twisted_schedule(code, eps, {(c, k, lab): i for (c, k, lab), i in T.items()})
    verify(code, pi, f'   {name} pulled-back schedule')
    g = Grp(*orders) if len(orders) == 2 else Grp(orders[0], 1)
    A2 = [g.idx(a if len(a) == 2 else (a[0], 0)) for a in A]; B2 = [g.idx(b if len(b) == 2 else (b[0], 0)) for b in B]
    HX, HZ = build_H(g, A2, B2); n = 2 * g.N
    print(f'   k={code_k(HX,HZ,n)}  ISD distance bound (10000 iterations): d<={isd_distance(HX, HZ, n, iters=10000, p=2, rng=random.Random(5))}', flush=True)
if __name__ == '__main__':
    # [[144,8,<=10]] C1-h0: d=(7,5), eps = y mod 2 gives eps(d)=1
    run('[[144,8,10]] Z12xZ6', (12, 6), [(0,0),(1,0),(7,5)], [(0,0),(4,3),(9,4)], 2, lambda g: g[1] % 2)
    # [[144,16,<=6]] C1-h1: d=(10,0) of order 6, 2-height 1 -> eps: Z12xZ6 -> Z4, eps(x,y) = x mod 4 gives eps(d)=2
    run('[[144,16,6]] Z12xZ6', (12, 6), [(0,0),(10,0),(10,4)], [(0,0),(2,0),(8,2)], 4, lambda g: g[0] % 4)
    # [[108,12,<=6]] C1-h0 over Z54: d=(39,) -> eps = g mod 2
    run('[[108,12,6]] Z54', (54,), [(0,),(6,),(39,)], [(0,),(39,),(51,)], 2, lambda g: g[0] % 2)
    # [[108,4,<=12]] C1-h0 over Z9xZ6: d=(2,3) -> eps = y mod 2 (3 mod 2 = 1)
    run('[[108,4,12]] Z9xZ6', (9, 6), [(0,0),(5,4),(7,1)], [(0,0),(2,0),(7,3)], 2, lambda g: g[1] % 2)

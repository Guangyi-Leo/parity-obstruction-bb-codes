import itertools, sys, time
from tb import *

def exact_min_logical_weight(HX, HZ, n, wmax):
    """exact minimum weight of a nontrivial X-logical (ker HZ \\ row HX) if <= wmax, else None (meet in the middle)."""
    N = len(HZ)
    col = [0] * n
    for i, row in enumerate(HZ):
        r = row
        while r:
            b = r & -r; j = b.bit_length() - 1; col[j] |= 1 << i; r ^= b
    LZ = logical_reps(HX, HZ, n)
    def is_log(v):
        return any((v & l).bit_count() & 1 for l in LZ)
    w1 = wmax // 2; w2 = wmax - w1
    table = {}
    for size in range(0, w1 + 1):
        for S in itertools.combinations(range(n), size):
            syn = 0; mask = 0
            for j in S: syn ^= col[j]; mask |= 1 << j
            table.setdefault(syn, []).append(mask)
    best = None
    for size in range(1, w2 + 1):
        for S in itertools.combinations(range(n), size):
            syn = 0; mask = 0
            for j in S: syn ^= col[j]; mask |= 1 << j
            for m1 in table.get(syn, ()):
                v = mask ^ m1
                if v == 0: continue
                w = v.bit_count()
                if (best is None or w < best) and is_log(v): best = w
    return best

if __name__ == '__main__':
    tests = [('[[72,12,6]] gross', 6, 6, [(3,0),(0,1),(0,2)], [(0,3),(1,0),(2,0)], 6),
             ('[[72,8,?]] C1 (Z6xZ6)', 6, 6, [(0,0),(4,3),(5,3)], [(0,0),(1,5),(4,3)], 6),
             ('[[72,4,?]] C1 (Z6xZ6)', 6, 6, [(0,0),(0,5),(4,4)], [(0,0),(1,1),(1,2)], 7)]
    for name, l, m, A, B, wmax in tests:
        G = Grp(l, m); A = [G.idx(a) for a in A]; B = [G.idx(b) for b in B]
        HX, HZ = build_H(G, A, B); n = 2 * G.N
        t0 = time.time(); d = exact_min_logical_weight(HX, HZ, n, wmax)
        print(f'{name}: k={code_k(HX,HZ,n)} exact min logical weight <= {wmax}: {d}  ({time.time()-t0:.0f}s)')

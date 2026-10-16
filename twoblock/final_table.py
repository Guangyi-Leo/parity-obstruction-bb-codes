import json, glob, sys, time
from tb import *
from exact_d import exact_min_logical_weight

rows = []
for f in sorted(glob.glob('res_*.json')):
    R = json.load(open(f))
    l, m = [int(v) for v in R['group'][1:].split('xZ')]
    G = Grp(l, m); n = 2 * G.N
    for fam, codes in R['families'].items():
        for c in codes:
            A = [G.idx(tuple(a)) for a in c['A']]; B = [G.idx(tuple(b)) for b in c['B']]
            HX, HZ = build_H(G, A, B)
            exact = None
            from math import comb
            if comb(n, (c['d_ub'] + 1) // 2) <= 2_500_000 and c['k'] > 0:
                t0 = time.time()
                e = exact_min_logical_weight(HX, HZ, n, c['d_ub'])
                exact = e   # min logical weight <= d_ub (equals d_ub if ISD bound is tight)
            rows.append((G.N, R['group'], fam, c['k'], c['d_ub'], exact, c['A'], c['B'], c.get('d_col'), c['tag']))
rows.sort(key=lambda r: (r[0], r[1], r[2], -r[3]))
print(f'{"N":>3} {"group":9} {"family":8} {"[[n,k,d]]":16} {"exact d":8} {"A":30} {"B":30} {"tag"}')
for N, grp, fam, k, dub, exact, A, B, dcol, tag in rows:
    ex = '-' if exact is None else str(exact)
    print(f'{N:>3} {grp:9} {fam:8} [[{2*N},{k},<={dub}]]{"":6} {ex:8} {str(A):30} {str(B):30} {tag}')

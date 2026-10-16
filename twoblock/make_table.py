import json, glob, sys, time
from math import comb
from tb import *
from exact_d import exact_min_logical_weight
rows = []
for f in sorted(glob.glob('res_*.json')):
    R = json.load(open(f))
    l, m = [int(v) for v in R['group'][1:].split('xZ')]
    G = Grp(l, m); n = 2 * G.N
    for fam, codes in R['families'].items():
        for c in codes:
            if c['k'] == 0 or c['d_ub'] <= 2: continue
            A = [G.idx(tuple(a)) for a in c['A']]; B = [G.idx(tuple(b)) for b in c['B']]
            HX, HZ = build_H(G, A, B)
            exact = None
            if comb(n, (c['d_ub'] + 1) // 2) <= 2_500_000:
                exact = exact_min_logical_weight(HX, HZ, n, c['d_ub'])
            rows.append((G.N, l, m, fam, c['k'], c['d_ub'], exact, c['A'], c['B'], c.get('d_col'), c['tag']))
rows.sort(key=lambda r: (r[0], (r[1], r[2]), r[3], -r[4]))
def grp(l, m): return f'$\\mathbb{{Z}}_{{{l}}}$' if m == 1 else f'$\\mathbb{{Z}}_{{{l}}}\\times\\mathbb{{Z}}_{{{m}}}$'
def elems(E, m):
    return '$\\{' + ','.join((f'{a[0]}' if m == 1 else f'({a[0]},{a[1]})') for a in E) + '\\}$'
fam_name = {'D': 'D', 'C1-even': 'C1, even', 'C1-odd': 'C1, odd'}
for N, l, m, fam, k, dub, exact, A, B, dcol, tag in rows:
    d = f'{dub}' if exact == dub else f'\\le{dub}'
    extra = ''
    if dcol is not None:
        G = Grp(l, m); dd = G.idx(tuple(dcol))
        h = G.two_height(dd)
        extra = (f'{dcol[0]}' if m == 1 else f'({dcol[0]},{dcol[1]})') + f' & {G.order(dd)} & ' + ('--' if h is None else str(h))
    else:
        extra = '-- & -- & --'
    print(f'{grp(l,m)} & {fam_name[fam]} & $[[{2*N},{k},{d}]]$ & {elems(A,m)} & {elems(B,m)} & {extra} \\\\')

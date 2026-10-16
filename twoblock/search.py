import sys, time, random, itertools, math, json, collections
from tb import *


def automorphisms(G):
    N = G.N; auts = []
    for u in range(N):
        if G.idx(tuple(x * G.l for x in G.el(u))) != 0: continue      # l*u == 0
        for v in range(N):
            if G.idx(tuple(x * G.m for x in G.el(v))) != 0: continue  # m*v == 0
            # phi(i,j) = i*u + j*v
            img = [0] * N
            for g in range(N):
                i, j = G.el(g)
                img[g] = G.idx((i * G.el(u)[0] + j * G.el(v)[0], i * G.el(u)[1] + j * G.el(v)[1]))
            if len(set(img)) == N: auts.append(img)
    return auts


def canonical(G, A, B, auts):
    best = None
    for phi in auts:
        PA = [phi[a] for a in A]; PB = [phi[b] for b in B]
        for (P, Q) in ((PA, PB), (PB, PA)):
            for t1 in P:
                p = tuple(sorted(G.sub(a, t1) for a in P))
                for t2 in Q:
                    key = (p, tuple(sorted(G.sub(b, t2) for b in Q)))
                    if best is None or key < best: best = key
    return best


def scan_group(l, m, sample=None, seed=0, kmin=None, verbose=True):
    G = Grp(l, m); N = G.N; n = 2 * N
    rng = random.Random(seed)
    pairs = [(a2, a3) for a2 in range(1, N) for a3 in range(a2 + 1, N)]
    allAB = [(A, B) for A in pairs for B in pairs]
    if sample is not None and len(allAB) > sample:
        allAB = rng.sample(allAB, sample)
    t0 = time.time()
    stats = collections.Counter(); bestk = {}
    records = []   # (cls, tag, k, A, B, d, ord, height)
    for (a2, a3), (b2, b3) in allAB:
        A = [0, a2, a3]; B = [0, b2, b3]
        cls, d = sums_class(G, A, B)
        if cls == 'other': stats['other'] += 1; continue
        if cls == 'C1':
            o = G.order(d); h = G.two_height(d)
            tag = 'C1-odd' if o % 2 else ('C1-h%d' % h)
        else:
            tag = 'D'
        stats[tag] += 1
        HX, HZ = build_H(G, A, B)
        k = code_k(HX, HZ, n)
        stats[(tag, k)] += 1
        records.append((tag, k, A, B, d))
    if verbose:
        print(f'G=Z{l}xZ{m} N={N}: {len(allAB)} pairs scanned in {time.time()-t0:.0f}s; classes: '
              + ', '.join(f'{t}={stats[t]}' for t in sorted(k for k in stats if isinstance(k, str))))
    return G, records, stats


def best_codes(G, records, tags, kmin, iters=300, max_reps=400, seed=1, verbose=True):
    """canonicalise candidates with k >= kmin in the given tag set and compute ISD distance per orbit rep"""
    auts = automorphisms(G)
    rng = random.Random(seed)
    cands = [r for r in records if r[0] in tags and r[1] >= max(kmin, 1)]
    rng.shuffle(cands)
    cands = cands[:3000]
    seen = {}; out = []
    t0 = time.time()
    for tag, k, A, B, d in cands:
        key = canonical(G, A, B, auts)
        if key in seen: continue
        seen[key] = True
        if len(seen) > max_reps: break
        HX, HZ = build_H(G, A, B)
        dist = isd_distance(HX, HZ, 2 * G.N, iters=iters, p=2, rng=random.Random(len(seen)))
        out.append((dist, k, tag, A, B, d))
    out.sort(reverse=True)
    if verbose:
        print(f'   {len(cands)} candidates (k>={kmin}, tags {tags}) -> {len(seen)} orbits, distances in {time.time()-t0:.0f}s; |Aut|={len(auts)}')
    return out


if __name__ == '__main__':
    l, m = int(sys.argv[1]), int(sys.argv[2])
    sample = int(sys.argv[3]) if len(sys.argv) > 3 else None
    G, records, stats = scan_group(l, m, sample=sample)
    ks = collections.Counter()
    for tag, k, A, B, d in records: ks[(tag, k)] += 1
    for tag in ['D', 'C1-h0', 'C1-h1', 'C1-h2', 'C1-h3', 'C1-h4', 'C1-h5', 'C1-odd']:
        row = {k: c for (t, k), c in ks.items() if t == tag}
        if row: print(f'   {tag:7s} k-distribution: {dict(sorted(row.items()))}')
    # distances: top k values per class family
    for tags, label in (( {'D'}, 'distinct sums (depth 7 by Thm 7)'),
                        ( {'C1-h0', 'C1-h1', 'C1-h2'}, 'C1, d not in 8G (depth 6 by Thm 12)'),
                        ( {'C1-h3', 'C1-h4', 'C1-h5'}, 'C1, d in 8G, even order (depth 6 via q=16/32 keys)'),
                        ( {'C1-odd'}, 'C1, odd order (depth 6 undetermined)')):
        kvals = sorted({k for tag, k, *_ in records if tag in tags}, reverse=True)
        if not kvals: continue
        kmin = kvals[min(2, len(kvals) - 1)]   # top three k values
        res = best_codes(G, records, tags, kmin)
        print(f'   == {label}: Pareto-optimal (k, d) among top-k orbits:')
        pareto = []
        for dist, k, tag, A, B, d in sorted(res, key=lambda r: (-r[1], -r[0])):
            if any(k2 >= k and d2 >= dist for (d2, k2) in pareto): continue
            pareto.append((dist, k))
            print(f'      [[{2*G.N},{k},<={dist}]]  {tag}  A={[G.el(a) for a in A]} B={[G.el(b) for b in B]}'
                  + (f'  d={G.el(d)} ord={G.order(d)}' if d is not None else ''))

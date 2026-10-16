import sys, time, random, itertools, math, json, collections
from tb import *
from search import automorphisms, canonical, scan_group

FAMILIES = [('D', {'D'}, 'distinct sums: depth 7 (Thm 7)'),
            ('C1-even', {'C1-h0', 'C1-h1', 'C1-h2', 'C1-h3', 'C1-h4', 'C1-h5'}, 'C1, ord(d) even: depth 6 (Thm 12 / q<=64 keys)'),
            ('C1-odd', {'C1-odd'}, 'C1, ord(d) odd: depth 6 undetermined')]


def pareto(items):
    """items: list of (d, k, ...) -> Pareto-optimal list (max k and d)"""
    out = []
    for it in sorted(items, key=lambda r: (-r[1], -r[0])):
        if any(k2 >= it[1] and d2 >= it[0] for (d2, k2, *_) in out): continue
        out.append(it)
    return out


def run(l, m, sample=None, max_orbits=250, iters=300, iters_final=2000):
    G, records, stats = scan_group(l, m, sample=sample)
    auts = automorphisms(G)
    n = 2 * G.N
    result = {'group': f'Z{l}xZ{m}', 'N': G.N, 'families': {}}
    ks = collections.Counter((tag, k) for tag, k, *_ in records)
    for tag in sorted({t for t, _ in ks}):
        row = {k: c for (t, k), c in ks.items() if t == tag}
        print(f'   {tag:7s} k-distribution: {dict(sorted(row.items()))}')
    for fam, tags, label in FAMILIES:
        cands = [r for r in records if r[0] in tags and r[1] > 0]
        if not cands: continue
        rng = random.Random(7); rng.shuffle(cands)
        cands.sort(key=lambda r: -r[1])          # high k first (stable, so random within k)
        seen = {}; evals = []; t0 = time.time()
        for tag, k, A, B, d in cands:
            key = canonical(G, A, B, auts)
            if key in seen: continue
            seen[key] = 1
            HX, HZ = build_H(G, A, B)
            dist = isd_distance(HX, HZ, n, iters=iters, p=2, rng=random.Random(len(seen)))
            evals.append((dist, k, tag, A, B, d))
            if len(seen) >= max_orbits: break
        front = pareto(evals)
        # firm up the front with more ISD iterations
        front2 = []
        for dist, k, tag, A, B, d in front:
            HX, HZ = build_H(G, A, B)
            dist2 = isd_distance(HX, HZ, n, iters=iters_final, p=2, rng=random.Random(99))
            front2.append((min(dist, dist2), k, tag, A, B, d))
        front2 = pareto(front2)
        print(f'   == {label}: {len(cands)} codes, {len(seen)} orbits evaluated ({time.time()-t0:.0f}s); Pareto front (k, d<=):')
        fam_out = []
        for dist, k, tag, A, B, d in front2:
            extra = f'  d={G.el(d)} ord={G.order(d)} 2-height={G.two_height(d)}' if d is not None else ''
            print(f'      [[{n},{k},<={dist}]]  {tag}  A={[G.el(a) for a in A]} B={[G.el(b) for b in B]}{extra}')
            fam_out.append({'n': n, 'k': k, 'd_ub': dist, 'tag': tag, 'A': [G.el(a) for a in A], 'B': [G.el(b) for b in B],
                            'd_col': (G.el(d) if d is not None else None)})
        result['families'][fam] = fam_out
    with open(f'res_{l}x{m}.json', 'w') as f: json.dump(result, f)
    return result


if __name__ == '__main__':
    l, m = int(sys.argv[1]), int(sys.argv[2])
    sample = int(sys.argv[3]) if len(sys.argv) > 3 else None
    run(l, m, sample=sample)

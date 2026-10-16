"""
2.5: verification protocol for class schedules whose key is degenerate (repeated alpha_s or beta_t):
for every admissible normalised key at modulus q, build a genuine class-C1 code over Z_{qM} realising the key
(a_s = alpha_s + q x_s, b_t = beta_t + q y_t, one collision exactly at the designated pair), pull the class
schedule back along g -> g mod q and run the full F2 circuit simulation.
"""
import sys, itertools, random
sys.path.insert(0, '/mnt/user-data/outputs'); sys.path.insert(0, '.')
from independent_check import Group, TwoBlockCode, twisted_schedule, is_layering, corner_parity_ok, f2_simulate
from keys16 import build
from pysat.solvers import Solver


def class_schedule(q, alpha, beta, des):
    clauses, x = build(q, alpha, beta, des)
    with Solver(name='cadical195', bootstrap_with=clauses) as s:
        if not s.solve(): return None
        model = set(l for l in s.get_model() if l > 0)
        return {e: i for (e, i), v in x.items() if v in model}


def realising_code(q, alpha, beta, des, M, rng):
    """random lifts with exactly the designated collision; returns (G, code) or None"""
    (s1, t1), (s2, t2) = des
    N = q * M
    for _ in range(200):
        xs = [rng.randrange(M) for _ in range(3)]; ys = [rng.randrange(M) for _ in range(3)]
        A = [(alpha[s] + q * xs[s]) % N for s in range(3)]
        B = [(beta[t] + q * ys[t]) % N for t in range(3)]
        # enforce the designated collision exactly: a_s1 + b_t1 = a_s2 + b_t2 (mod N)
        B[t2] = (A[s1] + B[t1] - A[s2]) % N
        if B[t2] % q != beta[t2] % q: continue
        if len(set(A)) < 3 or len(set(B)) < 3: continue
        sums = [(a + b) % N for a in A for b in B]
        cnt = {}
        for v in sums: cnt[v] = cnt.get(v, 0) + 1
        if sorted(cnt.values(), reverse=True) != [2] + [1] * 7: continue
        G = Group((N,))
        return G, TwoBlockCode(G, [(a,) for a in A], [(b,) for b in B])
    return None


def keys(q):
    out = []
    for (s1, s2) in itertools.combinations(range(3), 2):
        for (t1, t2) in itertools.combinations(range(3), 2):
            for des in (((s1, t1), (s2, t2)), ((s1, t2), (s2, t1))):
                for a2, a3, b2, b3 in itertools.product(range(q), repeat=4):
                    alpha, beta = (0, a2, a3), (0, b2, b3); (sa, ta), (sb, tb) = des
                    if (alpha[sa] + beta[ta] - alpha[sb] - beta[tb]) % q == 0 and (alpha[sb] - alpha[sa]) % q != 0:
                        out.append((alpha, beta, des))
    return out


if __name__ == '__main__':
    q = int(sys.argv[1]); M = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    rng = random.Random(3)
    K = keys(q); n_ok = n_deg = 0; fails = []
    for alpha, beta, des in K:
        T = class_schedule(q, alpha, beta, des)
        assert T is not None, (alpha, beta, des)
        degenerate = len(set(alpha)) < 3 or len(set(beta)) < 3
        n_deg += degenerate
        res = realising_code(q, alpha, beta, des, M, rng)
        if res is None: fails.append(('no realising code', alpha, beta, des)); continue
        G, code = res
        pi = twisted_schedule(code, lambda g: g[0] % q, {(c, k, lab): i for (c, k, lab), i in T.items()})
        Mpi, ok_map = f2_simulate(code, pi)
        proper = is_layering(code, pi) and ok_map and not Mpi.any() and corner_parity_ok(code, pi)[0]
        if proper: n_ok += 1
        else: fails.append(('pullback not proper', alpha, beta, des))
    print(f'q={q}, M={M}: {len(K)} keys with dbar!=0 ({n_deg} degenerate); realising C1 codes over Z_{q*M} built and '
          f'pulled-back schedules verified by F2 simulation: {n_ok}/{len(K)}; failures: {fails[:5]}')

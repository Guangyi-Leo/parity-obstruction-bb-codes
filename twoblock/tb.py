"""
Fast two-block code tools with Python-int bit rows: k, class, collision element, 2-height, and an
information-set-decoding (ISD) upper bound on the distance (Prange + Lee-Brickell p=2).
G = Z_l x Z_m, elements encoded as index g = i*m + j.
"""
import random, math, itertools


class Grp:
    def __init__(self, l, m=1):
        self.l, self.m, self.N = l, m, l * m
    def idx(self, e): return (e[0] % self.l) * self.m + (e[1] % self.m)
    def el(self, g): return (g // self.m, g % self.m)
    def add(self, g, h):
        a, b = self.el(g), self.el(h); return self.idx((a[0] + b[0], a[1] + b[1]))
    def sub(self, g, h):
        a, b = self.el(g), self.el(h); return self.idx((a[0] - b[0], a[1] - b[1]))
    def neg(self, g): return self.sub(0, g)
    def order(self, g):
        a = self.el(g)
        o1 = self.l // math.gcd(self.l, a[0]); o2 = self.m // math.gcd(self.m, a[1])
        return o1 * o2 // math.gcd(o1, o2)
    def in_2jG(self, g, j):
        a = self.el(g)
        return a[0] % math.gcd(2 ** j, self.l) == 0 and a[1] % math.gcd(2 ** j, self.m) == 0
    def two_height(self, g):
        """largest j with g in 2^j G (None if g in 2^j G for all j, i.e. odd order)"""
        if self.order(g) % 2 == 1: return None
        j = 0
        while self.in_2jG(g, j + 1): j += 1
        return j


def build_H(G, A, B):
    """H_X = [A | B], H_Z = [B^T | A^T] as lists of int bit-rows over 2N columns (L block bits 0..N-1, R block N..2N-1)."""
    N = G.N
    HX, HZ = [], []
    for g in range(N):
        rx = 0; rz = 0
        for a in A: rx |= 1 << G.add(g, a)
        for b in B: rx |= 1 << (N + G.add(g, b))
        for b in B: rz |= 1 << G.sub(g, b)
        for a in A: rz |= 1 << (N + G.sub(g, a))
        HX.append(rx); HZ.append(rz)
    return HX, HZ


def rref(rows):
    """returns (list of reduced rows, dict pivot_col -> row index)"""
    rows = list(rows); piv = {}
    r = 0
    n = len(rows)
    for i in range(n):
        v = rows[i]
        # reduce v by existing pivots
        for c, j in piv.items():
            if v >> c & 1: v ^= rows[j]
        if v:
            c = v.bit_length() - 1
            # eliminate c from other pivot rows
            for cc, j in piv.items():
                if rows[j] >> c & 1: rows[j] ^= v
            piv[c] = i; rows[i] = v
        else:
            rows[i] = 0
    return rows, piv


def rank(rows):
    _, piv = rref(rows); return len(piv)


def kernel(rows, n):
    """basis of {v : rows . v = 0} over F2, columns 0..n-1"""
    R, piv = rref(rows)
    pivcols = set(piv)
    basis = []
    for f in range(n):
        if f in pivcols: continue
        v = 1 << f
        for c, j in piv.items():
            if R[j] >> f & 1: v |= 1 << c
        basis.append(v)
    return basis


def logical_reps(HX, HZ, n):
    """Z-logical representatives: ker(HX) modulo rowspace(HZ)"""
    K = kernel(HX, n)
    R, piv = rref(HZ)
    reps = []
    for v in K:
        w = v
        for c, j in piv.items():
            if w >> c & 1: w ^= R[j]
        if w:
            c = w.bit_length() - 1
            for cc, j in piv.items():
                if R[j] >> c & 1: R[j] ^= w
            R.append(w); piv[c] = len(R) - 1
            reps.append(v)
    return reps


def code_k(HX, HZ, n):
    return n - rank(HX) - rank(HZ)


def isd_distance(HX, HZ, n, iters=600, p=2, rng=None, stop_at=None):
    """upper bound on d_X = min weight of ker(HZ) \\ rowspace(HX); by the X<->Z duality of two-block codes d_Z = d_X."""
    rng = rng or random.Random(0)
    K = kernel(HZ, n)
    LZ = logical_reps(HZ, HX, n)   # X-logical detector: v nontrivial iff odd overlap with some Z-logical rep
    # (logical_reps(HZ, HX) gives ker(HZ) mod rowspace(HX) = X-logicals; we need Z-logicals = ker(HX) mod rowspace(HZ))
    LZ = logical_reps(HX, HZ, n)
    def is_log(v):
        for l in LZ:
            if (v & l).bit_count() & 1: return True
        return False
    best = n; dim = len(K)
    for it in range(iters):
        cols = list(range(n)); rng.shuffle(cols)
        rows = K[:]; used = [False] * dim; cnt = 0
        for c in cols:
            mask = 1 << c; piv = -1
            for i in range(dim):
                if not used[i] and rows[i] & mask: piv = i; break
            if piv < 0: continue
            used[piv] = True; pr = rows[piv]
            for i in range(dim):
                if i != piv and rows[i] & mask: rows[i] ^= pr
            cnt += 1
            if cnt == dim: break
        for i in range(dim):
            w = rows[i].bit_count()
            if w < best and is_log(rows[i]): best = w
        if p >= 2:
            for i in range(dim):
                ri = rows[i]
                for j in range(i + 1, dim):
                    v = ri ^ rows[j]; w = v.bit_count()
                    if w < best and is_log(v): best = w
        if stop_at is not None and best <= stop_at: break
    return best


def sums_class(G, A, B):
    """returns (class, collision element d or None): 'D' distinct sums, 'C1' one collision, else 'other'"""
    S = {}
    pairs = {}
    for s, a in enumerate(A):
        for t, b in enumerate(B):
            x = G.add(a, b); S[x] = S.get(x, 0) + 1; pairs.setdefault(x, []).append((s, t))
    mult = sorted(S.values(), reverse=True)
    if mult[0] == 1: return 'D', None
    if mult[0] == 2 and (len(mult) == 1 or mult[1] == 1):
        x = next(x for x, m in S.items() if m == 2)
        (s, t), (s2, t2) = pairs[x]
        d = G.sub(A[s2], A[s])
        return 'C1', d
    return 'other', None

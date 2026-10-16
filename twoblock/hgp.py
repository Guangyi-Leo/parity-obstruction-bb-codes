import numpy as np, networkx as nx, itertools
def circ(n, taps):
    H = np.zeros((n, n), dtype=np.uint8)
    for i in range(n):
        for t in taps: H[i, (i + t) % n] = 1
    return H
def hgp(H1, H2):
    m1, n1 = H1.shape; m2, n2 = H2.shape
    HX = np.hstack([np.kron(H1, np.eye(n2, dtype=np.uint8)), np.kron(np.eye(m1, dtype=np.uint8), H2.T)]) % 2
    HZ = np.hstack([np.kron(np.eye(n1, dtype=np.uint8), H2), np.kron(H1.T, np.eye(m2, dtype=np.uint8))]) % 2
    return HX, HZ
def rank_f2(M):
    M = M.copy() % 2; r = 0; rows, cols = M.shape
    for c in range(cols):
        p = next((i for i in range(r, rows) if M[i, c]), None)
        if p is None: continue
        M[[r, p]] = M[[p, r]]
        for i in range(rows):
            if i != r and M[i, c]: M[i] ^= M[r]
        r += 1
        if r == rows: break
    return r
if __name__ == '__main__':
    for n, taps in [(7, (0, 1, 3)), (9, (0, 1, 3)), (11, (0, 1, 3)), (13, (0, 1, 4)), (8, (0, 1, 3)), (15, (0,1,4))]:
        H = circ(n, taps)
        HX, HZ = hgp(H, H)
        assert not ((HX @ HZ.T) % 2).any()
        nq = HX.shape[1]
        rv = HX.sum(0); sv = HZ.sum(0)
        wx = set(HX.sum(1)); wz = set(HZ.sum(1))
        Gr = nx.Graph()
        for i, j in zip(*np.nonzero(HX)): Gr.add_edge(('X', i), ('q', j))
        for i, j in zip(*np.nonzero(HZ)): Gr.add_edge(('Z', i), ('q', j))
        comps = list(nx.connected_components(Gr))
        k = nq - rank_f2(HX) - rank_f2(HZ)
        s = int((rv * sv).sum())
        print(f'HGP(H,H), H=circulant_{n}(1+x^{taps[1]}+x^{taps[2]}): n={nq} k={k} data degrees r+s={set(rv+sv)} X-check weights={wx} '
              f'components={len(comps)} sum r_v s_v={s} mod 4={s%4}  -> {"OBSTRUCTED by Thm 1" if s%4==2 and len(comps)==1 else "not obstructed (or check components)"}')

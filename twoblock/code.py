"""Two-block (bivariate bicycle) codes: group, Tanner graph, corners, overlap pairs.

Definitions follow the specification exactly (section 1).

Group G is a finite abelian group written as a direct product of cyclic factors,
G = Z_{n_1} x ... x Z_{n_r}.  The usual bivariate case is dims=(ell, m) with the
monomial x^i y^j identified with the element (i, j).  The general product form is
supported so that groups such as Z2 x Z2 x Z2 (which is *not* of the form
Z_ell x Z_m) can be handled without misrepresenting them.

Vertices
    data qubits  L_h, R_h   for h in G      (2N total)
    X-checks     X_g        for g in G
    Z-checks     Z_g        for g in G

Edges (this is H_X = [A|B],  H_Z = [B^T|A^T])
    (X_g, L_{g+a_s})  label ("X","L",s)
    (X_g, R_{g+b_t})  label ("X","R",t)
    (Z_g, L_{g-b_t})  label ("Z","L",t)
    (Z_g, R_{g-a_s})  label ("Z","R",s)
"""
from __future__ import annotations

import itertools
import json
from collections import Counter, defaultdict
from dataclasses import dataclass

import numpy as np

GroupElt = tuple[int, ...]


class Group:
    """Finite abelian group Z_{n_1} x ... x Z_{n_r}."""

    def __init__(self, dims):
        self.dims: tuple[int, ...] = tuple(int(d) for d in dims)
        if not self.dims or any(d < 1 for d in self.dims):
            raise ValueError(f"bad group dims {dims}")
        self.order: int = int(np.prod(self.dims))
        self.elements: list[GroupElt] = [tuple(e) for e in itertools.product(*(range(d) for d in self.dims))]
        self._index: dict[GroupElt, int] = {g: i for i, g in enumerate(self.elements)}

    def idx(self, g: GroupElt) -> int:
        return self._index[self.norm(g)]

    def norm(self, g) -> GroupElt:
        return tuple(int(x) % d for x, d in zip(g, self.dims))

    def add(self, g: GroupElt, h: GroupElt) -> GroupElt:
        return tuple((x + y) % d for x, y, d in zip(g, h, self.dims))

    def sub(self, g: GroupElt, h: GroupElt) -> GroupElt:
        return tuple((x - y) % d for x, y, d in zip(g, h, self.dims))

    @property
    def zero(self) -> GroupElt:
        return tuple(0 for _ in self.dims)

    def label(self) -> str:
        return "x".join(f"Z{d}" for d in self.dims)

    def order_of(self, g: GroupElt) -> int:
        """Order of g in G = lcm_i n_i / gcd(n_i, g_i)."""
        from math import gcd, lcm
        o = 1
        for x, d in zip(self.norm(g), self.dims):
            o = lcm(o, d // gcd(d, x) if x % d else 1)
        return o

    def doubles(self) -> set:
        """The subgroup 2G = {2g : g in G}."""
        return {self.add(g, g) for g in self.elements}

    def __len__(self):
        return self.order


@dataclass(frozen=True)
class Edge:
    """One Tanner-graph edge.  ``lab`` is 0-based; ``lab1`` is the 1-based s or t."""
    eid: int
    kind: str    # 'X' or 'Z'
    side: str    # 'L' or 'R'
    lab: int     # 0-based index into A (labels s) or B (labels t)
    check: int   # group index of the check vertex
    qubit: int   # group index h of the data qubit (side tells L or R)

    @property
    def lab1(self) -> int:
        return self.lab + 1

    def label_tuple(self) -> tuple[str, str, int]:
        return (self.kind, self.side, self.lab1)


@dataclass(frozen=True)
class Corner:
    """A corner (eX, eZ) at a data qubit: one X-edge and one Z-edge meeting there."""
    cid: int
    ex: int      # eid of the X-edge
    ez: int      # eid of the Z-edge
    side: str    # 'L' or 'R'
    qubit: int   # group index h


@dataclass(frozen=True)
class OverlapPair:
    """(X_g, Z_{g+delta}) together with the corners the two checks share."""
    gx: int              # group index of X-check
    gz: int              # group index of Z-check
    delta: GroupElt
    corners: tuple[int, ...]


class TwoBlockCode:
    def __init__(self, dims, A, B, name: str = "code"):
        self.name = name
        self.G = Group(dims)
        self.A: list[GroupElt] = [self.G.norm(a) for a in A]
        self.B: list[GroupElt] = [self.G.norm(b) for b in B]
        if len(set(self.A)) != len(self.A):
            raise ValueError("A must consist of distinct group elements")
        if len(set(self.B)) != len(self.B):
            raise ValueError("B must consist of distinct group elements")
        self.k: int = len(self.A)          # Delta_A
        self.l: int = len(self.B)          # Delta_B
        self.Delta: int = self.k + self.l
        self.N: int = self.G.order

        self._build_edges()
        self._build_corners()
        self._build_overlaps()

    # ------------------------------------------------------------------ edges
    def _build_edges(self):
        G, N = self.G, self.N
        self.edges: list[Edge] = []
        # lookup: (kind, side, check_index, lab) -> eid
        self._elookup: dict[tuple[str, str, int, int], int] = {}
        # incidence
        self.check_edges: dict[tuple[str, int], list[int]] = {}   # ('X'|'Z', g) -> eids
        self.data_edges: dict[tuple[str, int], list[int]] = {}    # ('L'|'R', h) -> eids

        for kind in ("X", "Z"):
            for gi in range(N):
                self.check_edges[(kind, gi)] = []
        for side in ("L", "R"):
            for hi in range(N):
                self.data_edges[(side, hi)] = []

        def add(kind, side, lab, gi, hi):
            e = Edge(len(self.edges), kind, side, lab, gi, hi)
            self.edges.append(e)
            self._elookup[(kind, side, gi, lab)] = e.eid
            self.check_edges[(kind, gi)].append(e.eid)
            self.data_edges[(side, hi)].append(e.eid)
            return e.eid

        for gi, g in enumerate(G.elements):
            for s, a in enumerate(self.A):
                add("X", "L", s, gi, G.idx(G.add(g, a)))
            for t, b in enumerate(self.B):
                add("X", "R", t, gi, G.idx(G.add(g, b)))
        for gi, g in enumerate(G.elements):
            for t, b in enumerate(self.B):
                add("Z", "L", t, gi, G.idx(G.sub(g, b)))
            for s, a in enumerate(self.A):
                add("Z", "R", s, gi, G.idx(G.sub(g, a)))

        self.n_edges = len(self.edges)
        # vertex -> incident eids, as a flat list of all vertices (used by the encoder)
        self.vertices: list[tuple[str, int]] = (
            [("X", gi) for gi in range(N)] + [("Z", gi) for gi in range(N)]
            + [("L", hi) for hi in range(N)] + [("R", hi) for hi in range(N)]
        )

    def edge_id(self, kind: str, side: str, check: int, lab: int) -> int:
        return self._elookup[(kind, side, check, lab)]

    def incident(self, v: tuple[str, int]) -> list[int]:
        return self.check_edges[v] if v[0] in ("X", "Z") else self.data_edges[v]

    # ---------------------------------------------------------------- corners
    def _build_corners(self):
        self.corners: list[Corner] = []
        self.corner_index: dict[tuple[int, int], int] = {}
        # corners incident to a check, and to a data qubit
        self.check_corners: dict[tuple[str, int], list[int]] = defaultdict(list)
        for side in ("L", "R"):
            for hi in range(self.N):
                es = self.data_edges[(side, hi)]
                xs = [e for e in es if self.edges[e].kind == "X"]
                zs = [e for e in es if self.edges[e].kind == "Z"]
                for ex in xs:
                    for ez in zs:
                        c = Corner(len(self.corners), ex, ez, side, hi)
                        self.corner_index[(ex, ez)] = c.cid
                        self.corners.append(c)
                        self.check_corners[("X", self.edges[ex].check)].append(c.cid)
                        self.check_corners[("Z", self.edges[ez].check)].append(c.cid)
        self.n_corners = len(self.corners)

    # --------------------------------------------------------------- overlaps
    def sum_sets(self) -> dict[GroupElt, list[tuple[int, int]]]:
        """P(delta) = {(s,t) : a_s + b_t = delta}, 0-based s,t.  Only nonempty deltas."""
        P: dict[GroupElt, list[tuple[int, int]]] = defaultdict(list)
        for s, a in enumerate(self.A):
            for t, b in enumerate(self.B):
                P[self.G.add(a, b)].append((s, t))
        return dict(P)

    def distinct_sums(self) -> bool:
        """True iff all k*l sums a_s + b_t are pairwise distinct."""
        return len(self.sum_sets()) == self.k * self.l

    def multiplicity_histogram(self) -> dict[int, int]:
        h = Counter(len(v) for v in self.sum_sets().values())
        return dict(sorted(h.items()))

    def _build_overlaps(self):
        G = self.G
        P = self.sum_sets()
        self.P = P
        self.overlap_pairs: list[OverlapPair] = []
        for delta, sts in sorted(P.items()):
            for gi, g in enumerate(G.elements):
                gp = G.add(g, delta)
                gpi = G.idx(gp)
                cs: list[int] = []
                for (s, t) in sts:
                    # L-side corner at L_{g+a_s}
                    ex = self.edge_id("X", "L", gi, s)
                    ez = self.edge_id("Z", "L", gpi, t)
                    assert self.edges[ex].qubit == self.edges[ez].qubit == G.idx(G.add(g, self.A[s]))
                    cs.append(self.corner_index[(ex, ez)])
                    # R-side corner at R_{g+b_t}
                    ex = self.edge_id("X", "R", gi, t)
                    ez = self.edge_id("Z", "R", gpi, s)
                    assert self.edges[ex].qubit == self.edges[ez].qubit == G.idx(G.add(g, self.B[t]))
                    cs.append(self.corner_index[(ex, ez)])
                self.overlap_pairs.append(OverlapPair(gi, gpi, delta, tuple(cs)))

    # ------------------------------------------------------------- H matrices
    def H_X(self) -> np.ndarray:
        N = self.N
        H = np.zeros((N, 2 * N), dtype=np.int64)
        for e in self.edges:
            if e.kind == "X":
                col = e.qubit + (0 if e.side == "L" else N)
                H[e.check, col] = 1
        return H

    def H_Z(self) -> np.ndarray:
        N = self.N
        H = np.zeros((N, 2 * N), dtype=np.int64)
        for e in self.edges:
            if e.kind == "Z":
                col = e.qubit + (0 if e.side == "L" else N)
                H[e.check, col] = 1
        return H

    def overlap_matrix(self) -> np.ndarray:
        """Integer matrix H_X H_Z^T over Z."""
        return self.H_X() @ self.H_Z().T

    def logical_k(self) -> int:
        """Number of logical qubits, k = 2N - rank_F2(H_X) - rank_F2(H_Z)."""
        return 2 * self.N - f2_rank(self.H_X()) - f2_rank(self.H_Z())

    # ------------------------------------------------------------- structural
    def check_structure(self) -> dict:
        """Assert every structural property required by section 1; return the facts."""
        N, k, l, D = self.N, self.k, self.l, self.Delta
        assert self.n_edges == 2 * N * D, f"edge count {self.n_edges} != 2*N*Delta = {2*N*D}"

        for gi in range(N):
            for kind in ("X", "Z"):
                deg = len(self.check_edges[(kind, gi)])
                assert deg == D, f"{kind}-check {gi} has degree {deg} != Delta={D}"
        for hi in range(N):
            eL = [self.edges[e] for e in self.data_edges[("L", hi)]]
            eR = [self.edges[e] for e in self.data_edges[("R", hi)]]
            assert sum(e.kind == "X" for e in eL) == k, f"L_{hi}: X-degree != k"
            assert sum(e.kind == "Z" for e in eL) == l, f"L_{hi}: Z-degree != l"
            assert sum(e.kind == "X" for e in eR) == l, f"R_{hi}: X-degree != l"
            assert sum(e.kind == "Z" for e in eR) == k, f"R_{hi}: Z-degree != k"

        M = self.overlap_matrix()
        assert np.all(M % 2 == 0), "H_X H_Z^T has an odd entry (not a valid CSS pair)"
        P = self.sum_sets()
        for gi, g in enumerate(self.G.elements):
            row_expect = np.zeros(N, dtype=np.int64)
            for delta, sts in P.items():
                row_expect[self.G.idx(self.G.add(g, delta))] = 2 * len(sts)
            assert np.array_equal(M[gi], row_expect), f"overlap row {gi} != 2*|P(delta)| pattern"

        # every corner lies in exactly one overlap pair
        seen: list[int] = []
        for op in self.overlap_pairs:
            seen.extend(op.corners)
        assert len(seen) == len(set(seen)) == self.n_corners, (
            f"corner partition broken: {len(seen)} listed, {len(set(seen))} distinct, {self.n_corners} total")
        assert self.n_corners == 2 * N * k * l

        return dict(
            name=self.name, group=self.G.label(), dims=json.dumps(list(self.G.dims)), N=N, n_qubits=2 * N,
            k=k, l=l, Delta=D, n_edges=self.n_edges, n_corners=self.n_corners,
            n_overlap_pairs=len(self.overlap_pairs),
            k_logical=self.logical_k(),
            distinct_sums=self.distinct_sums(),
            max_overlap_entry=int(M.max()),
            multiplicity_histogram=self.multiplicity_histogram(),
            A=[list(a) for a in self.A], B=[list(b) for b in self.B],
        )

    def __repr__(self):
        return f"TwoBlockCode({self.name}, G={self.G.label()}, N={self.N}, k={self.k}, l={self.l})"


def f2_rank(M) -> int:
    """Rank over F2 of an integer 0/1 matrix, via bitset Gaussian elimination."""
    rows = []
    for r in M:
        v = 0
        for j, x in enumerate(r):
            if int(x) & 1:
                v |= 1 << j
        if v:
            rows.append(v)
    rank = 0
    pivots: list[int] = []
    for v in rows:
        for p in pivots:
            v = min(v, v ^ p)
        if v:
            pivots.append(v)
            pivots.sort(reverse=True)
            rank += 1
    return rank

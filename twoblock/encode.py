"""CNF encoding of "does a proper depth-D schedule exist?" (specification section 2).

Variables
    y[e][i]        edge e is in layer i          (i = 1..D, exactly one true)
    P[e][j]        lay(e) >= j                   (j = 2..D; P[e][D+1] := False)
    c[(eX,eZ)][i]  lay(eX) = i and lay(eZ) > i   (i = 1..D-1)
    o[(eX,eZ)]     lay(eX) < lay(eZ)             (corner orientation)

Clauses
    exactly-one over y[e][1..D]  (ALO + pairwise AMO)
    at every vertex v and layer i: pairwise AMO over {y[e][i] : e incident to v}
    properness: for every overlap pair, XOR of its corner o-variables = 0
    symmetry breaking (layer reversal): the L-edge s=1 of X_{(0,0)} lies in the
    first ceil(D/2) layers.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from pysat.card import CardEnc, EncType

from .code import TwoBlockCode


@dataclass
class Encoding:
    code: TwoBlockCode
    D: int
    nvars: int
    clauses: list[list[int]]
    y: list[list[int]]                 # y[eid][i-1]
    ovar: dict[int, int]               # cid -> o variable
    assumptions: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    properness_ranges: list = field(default_factory=list)   # (start, end) per overlap pair
    family_ranges: dict = field(default_factory=dict)      # family -> (start, end)

    def yvar(self, eid: int, layer: int) -> int:
        return self.y[eid][layer - 1]

    # ------------------------------------------------------------------- I/O
    def write_dimacs(self, path: str) -> None:
        with open(path, "w") as f:
            f.write(f"p cnf {self.nvars} {len(self.clauses)}\n")
            f.write("".join(" ".join(map(str, cl)) + " 0\n" for cl in self.clauses))

    def varmap(self) -> dict:
        return {
            "instance": self.code.name,
            "dims": list(self.code.G.dims),
            "A": [list(a) for a in self.code.A],
            "B": [list(b) for b in self.code.B],
            "D": self.D,
            "nvars": self.nvars,
            "nclauses": len(self.clauses),
            "n_edges": self.code.n_edges,
            "y": {str(e): self.y[e] for e in range(self.code.n_edges)},
            "edges": [
                {"eid": e.eid, "kind": e.kind, "side": e.side, "lab1": e.lab1,
                 "check": e.check, "qubit": e.qubit}
                for e in self.code.edges
            ],
            "assumptions": [list(map(_jsonable, a)) for a in self.assumptions],
        }

    def save_varmap(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self.varmap(), f)

    # --------------------------------------------------------------- decoding
    def decode_model(self, model) -> list[int]:
        """model: iterable of signed literals or a set of true variables -> layers list."""
        if isinstance(model, (set, frozenset)):
            true = model
        else:
            true = {v for v in model if v > 0}
        lay = [0] * self.code.n_edges
        for e in range(self.code.n_edges):
            hits = [i + 1 for i in range(self.D) if self.y[e][i] in true]
            if len(hits) != 1:
                raise ValueError(f"edge {e}: {len(hits)} layer variables true (expected 1)")
            lay[e] = hits[0]
        return lay


def _jsonable(x):
    return list(x) if isinstance(x, tuple) else x


def encode(code: TwoBlockCode, D: int, assumptions=None, symmetry_breaking: bool = True,
           card_encoding: int = EncType.totalizer) -> Encoding:
    if D < code.Delta:
        raise ValueError(f"depth {D} < Delta = {code.Delta}: vertex distinctness is infeasible")
    E, C = code.n_edges, code.n_corners
    cls: list[list[int]] = []

    # ---- variable allocation ------------------------------------------------
    nv = 0
    y = [[0] * D for _ in range(E)]
    for e in range(E):
        for i in range(D):
            nv += 1
            y[e][i] = nv
    # P[e][j] for j = 2..D  ->  Pv[e][j-2]
    Pv = [[0] * (D - 1) for _ in range(E)]
    for e in range(E):
        for j in range(2, D + 1):
            nv += 1
            Pv[e][j - 2] = nv
    # corner aux c_i (i = 1..D-1) and o
    cv = [[0] * (D - 1) for _ in range(C)]
    for cid in range(C):
        for i in range(1, D):
            nv += 1
            cv[cid][i - 1] = nv
    ov = [0] * C
    for cid in range(C):
        nv += 1
        ov[cid] = nv

    def P(e: int, j: int) -> int | None:
        """Variable for lay(e) >= j; None encodes the constant False (j = D+1)."""
        if j == D + 1:
            return None
        assert 2 <= j <= D
        return Pv[e][j - 2]

    n_exactly = n_vertex = n_pdef = n_corner = n_proper = n_sym = 0
    fam: dict = {}
    _b = len(cls)

    # ---- exactly-one over layers for every edge -----------------------------
    for e in range(E):
        cls.append(list(y[e]))
        n_exactly += 1
        for i in range(D):
            for j in range(i + 1, D):
                cls.append([-y[e][i], -y[e][j]])
                n_exactly += 1

    fam["exactly_one"] = (_b, len(cls)); _b = len(cls)

    # ---- vertex distinctness: at every vertex and layer, at most one edge ----
    for v in code.vertices:
        inc = code.incident(v)
        for a in range(len(inc)):
            for b in range(a + 1, len(inc)):
                ea, eb = inc[a], inc[b]
                for i in range(D):
                    cls.append([-y[ea][i], -y[eb][i]])
                    n_vertex += 1

    fam["vertex"] = (_b, len(cls)); _b = len(cls)

    # ---- P[e][j] <-> (y[e][j] OR P[e][j+1]) ---------------------------------
    for e in range(E):
        for j in range(2, D + 1):
            p, yj, pn = P(e, j), y[e][j - 1], P(e, j + 1)
            if pn is None:                      # P[e][D] <-> y[e][D]
                cls.append([-p, yj])
                cls.append([p, -yj])
                n_pdef += 2
            else:
                cls.append([-p, yj, pn])
                cls.append([p, -yj])
                cls.append([p, -pn])
                n_pdef += 3

    fam["pdef"] = (_b, len(cls)); _b = len(cls)

    # ---- corner variables ---------------------------------------------------
    for corner in code.corners:
        cid, ex, ez = corner.cid, corner.ex, corner.ez
        for i in range(1, D):
            ci, ya, pb = cv[cid][i - 1], y[ex][i - 1], P(ez, i + 1)
            cls.append([-ci, ya])
            cls.append([-ci, pb])
            cls.append([ci, -ya, -pb])
            n_corner += 3
        o = ov[cid]
        cls.append([-o] + cv[cid])
        n_corner += 1
        for ci in cv[cid]:
            cls.append([o, -ci])
            n_corner += 1

    fam["corner"] = (_b, len(cls)); _b = len(cls)

    # ---- properness: XOR of the corner orientations of each overlap pair = 0 -
    prop_ranges: list[tuple[int, int]] = []
    for op in code.overlap_pairs:
        _pstart = len(cls)
        lits = [ov[cid] for cid in op.corners]
        if len(lits) == 1:
            cls.append([-lits[0]])
            n_proper += 1
        elif len(lits) == 2:
            o1, o2 = lits
            cls.append([-o1, o2])
            cls.append([o1, -o2])
            n_proper += 2
        else:
            # Tseitin XOR chain: t <- o1 xor o2, then t <- t xor o_next, force t = 0
            acc = lits[0]
            for nxt in lits[1:-1]:
                nv += 1
                t = nv
                cls.extend([[-t, acc, nxt], [-t, -acc, -nxt], [t, -acc, nxt], [t, acc, -nxt]])
                n_proper += 4
                acc = t
            last = lits[-1]
            cls.append([-acc, last])            # acc xor last = 0
            cls.append([acc, -last])
            n_proper += 2
        prop_ranges.append((_pstart, len(cls)))

    fam["proper"] = (_b, len(cls)); _b = len(cls)

    # ---- symmetry breaking (layer reversal) ---------------------------------
    if symmetry_breaking:
        e0 = code.edge_id("X", "L", code.G.idx(code.G.zero), 0)
        half = (D + 1) // 2                     # ceil(D/2)
        cls.append([y[e0][i] for i in range(half)])
        n_sym += 1

    fam["symmetry"] = (_b, len(cls)); _b = len(cls)

    # ---- assumptions --------------------------------------------------------
    used = list(assumptions or [])
    n_assume = 0
    for asm in used:
        kind = asm[0]
        if kind in ("count_XL", "count"):
            _, i, cnt = asm
            lits = [y[e.eid][i - 1] for e in code.edges if e.kind == "X" and e.side == "L"]
            new, nv = _card_equals(lits, cnt, nv, card_encoding)
            cls.extend(new)
            n_assume += len(new)
        elif kind == "count_XL_atleast":
            # Used to *prove* that a x_1 = e case split is exhaustive: if forcing
            # x_i >= bound is UNSAT then x_i < bound always holds.
            _, i, cnt = asm
            lits = [y[e.eid][i - 1] for e in code.edges if e.kind == "X" and e.side == "L"]
            new, nv = _card_atleast(lits, cnt, nv, card_encoding)
            cls.extend(new)
            n_assume += len(new)
        elif kind == "fix":
            _, eid, layer = asm
            if not isinstance(eid, int):
                eid = code.edge_id(*eid)
            cls.append([y[eid][layer - 1]])
            n_assume += 1
        else:
            raise ValueError(f"unknown assumption {asm!r}")

    enc = Encoding(code=code, D=D, nvars=nv, clauses=cls, y=y, ovar={c: ov[c] for c in range(C)},
                   assumptions=used, properness_ranges=prop_ranges,
                   family_ranges={**fam, "assume": (_b, len(cls))})
    enc.stats = dict(nvars=nv, nclauses=len(cls), exactly_one=n_exactly, vertex=n_vertex,
                     pdef=n_pdef, corner=n_corner, proper=n_proper, symmetry=n_sym,
                     assume=n_assume, n_edges=E, n_corners=C,
                     n_overlap_pairs=len(code.overlap_pairs))
    return enc


def _card_equals(lits, bound, top_id, encoding):
    """Clauses forcing sum(lits) == bound, allocating aux vars above top_id."""
    if bound < 0 or bound > len(lits):
        return [[1], [-1]], top_id            # trivially unsatisfiable
    if bound == 0:
        return [[-l] for l in lits], top_id
    if bound == len(lits):
        return [[l] for l in lits], top_id
    cnf = CardEnc.equals(lits=list(lits), bound=int(bound), top_id=top_id, encoding=encoding)
    new_top = max(top_id, cnf.nv)
    return [list(c) for c in cnf.clauses], new_top


def _card_atleast(lits, bound, top_id, encoding):
    """Clauses forcing sum(lits) >= bound, allocating aux vars above top_id."""
    if bound <= 0:
        return [], top_id
    if bound > len(lits):
        return [[1], [-1]], top_id                # unsatisfiable by construction
    if bound == len(lits):
        return [[l] for l in lits], top_id
    cnf = CardEnc.atleast(lits=list(lits), bound=int(bound), top_id=top_id, encoding=encoding)
    return [list(c) for c in cnf.clauses], max(top_id, cnf.nv)


def schedule_assumptions(code: TwoBlockCode, layers) -> list:
    """Unit assumptions pinning every edge to its layer (used by the round-trip test)."""
    return [("fix", eid, int(layers[eid])) for eid in range(code.n_edges)]


# ---------------------------------------------------------------------------
# Translation-invariant (label-level) schedules
#
# Translating every vertex by g in G is a symmetry of the whole problem, so it is
# natural to look for schedules that are invariant under it: lay(e) depends only on
# the label (kind, side, s or t) of e, not on which check the edge belongs to.  Such
# a schedule is described by just 2*Delta numbers, and the constraint system it has
# to satisfy involves only k, l, D and the multiset structure of P(delta) -- not the
# group.  A solution therefore gives one uniform schedule valid for every two-block
# code with the same k, l and sum multiplicities.
# ---------------------------------------------------------------------------
LABEL_GROUPS = (("X", "L"), ("X", "R"), ("Z", "L"), ("Z", "R"))


def find_invariant_schedule(code: TwoBlockCode, D: int, solver_name: str = "cadical195"):
    """Search for a translation-invariant proper depth-D schedule.

    Returns ``(labels, layers)`` where ``labels`` maps (kind, side) -> tuple of layers
    indexed by the 0-based label, and ``layers`` is the expanded per-edge schedule;
    returns ``None`` if no invariant schedule of this depth exists.
    """
    from pysat.solvers import Solver

    k, l = code.k, code.l
    size = {("X", "L"): k, ("X", "R"): l, ("Z", "L"): l, ("Z", "R"): k}
    nv = 0
    u: dict[tuple[str, str], list[list[int]]] = {}
    for g in LABEL_GROUPS:
        rows = []
        for _ in range(size[g]):
            rows.append(list(range(nv + 1, nv + 1 + D)))
            nv += D
        u[g] = rows
    cls: list[list[int]] = []
    for g in LABEL_GROUPS:
        for row in u[g]:
            cls.append(list(row))
            for i in range(D):
                for j in range(i + 1, D):
                    cls.append([-row[i], -row[j]])

    def distinct(pairs):
        """All listed (group, index) label-slots must get pairwise distinct layers."""
        for x in range(len(pairs)):
            for y in range(x + 1, len(pairs)):
                (g1, i1), (g2, i2) = pairs[x], pairs[y]
                for i in range(D):
                    cls.append([-u[g1][i1][i], -u[g2][i2][i]])

    XL = [(("X", "L"), s) for s in range(k)]
    XR = [(("X", "R"), t) for t in range(l)]
    ZL = [(("Z", "L"), t) for t in range(l)]
    ZR = [(("Z", "R"), s) for s in range(k)]
    distinct(XL + XR)          # every X-check
    distinct(ZL + ZR)          # every Z-check
    distinct(XL + ZL)          # every L-qubit
    distinct(XR + ZR)          # every R-qubit

    def orient(ga, ia, gb, ib):
        """Fresh variable equivalent to lay(ga,ia) < lay(gb,ib)."""
        nonlocal nv
        nv += 1
        o = nv
        for i in range(D):
            for j in range(D):
                lit = o if i < j else -o
                cls.append([-u[ga][ia][i], -u[gb][ib][j], lit])
        return o

    for delta, sts in code.sum_sets().items():
        bits = []
        for (s, t) in sts:
            bits.append(orient(("X", "L"), s, ("Z", "L"), t))    # corner at L_{g+a_s}
            bits.append(orient(("X", "R"), t, ("Z", "R"), s))    # corner at R_{g+b_t}
        acc = bits[0]
        for nxt in bits[1:-1]:
            nv += 1
            t_ = nv
            cls.extend([[-t_, acc, nxt], [-t_, -acc, -nxt], [t_, -acc, nxt], [t_, acc, -nxt]])
            acc = t_
        cls.append([-acc, bits[-1]])
        cls.append([acc, -bits[-1]])

    with Solver(name=solver_name, bootstrap_with=cls) as s:
        if not s.solve():
            return None
        true = {v for v in s.get_model() if v > 0}
    labels = {g: tuple(next(i + 1 for i in range(D) if row[i] in true) for row in u[g])
              for g in LABEL_GROUPS}
    return labels, expand_label_schedule(code, labels)


def expand_label_schedule(code: TwoBlockCode, labels) -> list[int]:
    """Expand a per-label layer assignment into a per-edge schedule."""
    lay = [0] * code.n_edges
    for e in code.edges:
        lay[e.eid] = labels[(e.kind, e.side)][e.lab]
    return lay


# ---------------------------------------------------------------------------
# eps-twisted translation-invariant schedules
#
# A translation-invariant schedule makes lay(e) depend only on the label of e.
# The twisted version lets it depend additionally on eps(g), where g is the check
# the edge belongs to and eps: G -> Z2 is a group homomorphism:
#
#       lay(e) = f( label(e), eps(check(e)) ).
#
# Because eps is a homomorphism, eps(g + x) = eps(g) + eps(x), so the constraint
# system again closes on finitely many unknowns -- 2 * 2 * Delta of them -- with the
# eps-values of the a_s, the b_t and the deltas entering as fixed offsets.  eps = 0
# recovers find_invariant_schedule.
# ---------------------------------------------------------------------------
def homomorphisms_to_Z2(group) -> list[dict]:
    """Every homomorphism eps: G -> Z2, as {'coeffs': (c_1..c_r), 'name': str}.

    eps(g) = sum_i c_i g_i mod 2; c_i must be 0 whenever the i-th factor has odd
    order, so there are 2^(number of even factors) of them.
    """
    import itertools as _it
    choices = [(0, 1) if d % 2 == 0 else (0,) for d in group.dims]
    out = []
    for c in _it.product(*choices):
        name = "trivial" if not any(c) else "eps=" + "+".join(
            f"g{i+1}" for i, ci in enumerate(c) if ci)
        out.append(dict(coeffs=tuple(c), name=name, trivial=not any(c)))
    return out


def eps_value(coeffs, g) -> int:
    return sum(c * x for c, x in zip(coeffs, g)) % 2


def find_twisted_invariant_schedule(code: TwoBlockCode, D: int, coeffs,
                                    solver_name: str = "cadical195"):
    """Search for an eps-twisted invariant proper depth-D schedule.

    Returns ``(labels, layers)`` with ``labels[(kind, side)][e]`` a tuple indexed by
    the 0-based label and ``e = eps(check)``; or ``None`` if none exists.
    """
    from pysat.solvers import Solver

    k, l = code.k, code.l
    G = code.G
    E = sorted({eps_value(coeffs, g) for g in G.elements})       # image of eps
    ea = [eps_value(coeffs, a) for a in code.A]
    eb = [eps_value(coeffs, b) for b in code.B]
    size = {("X", "L"): k, ("X", "R"): l, ("Z", "L"): l, ("Z", "R"): k}

    nv = 0
    u: dict[tuple, list[int]] = {}
    for grp in LABEL_GROUPS:
        for idx in range(size[grp]):
            for e in (0, 1):
                u[(grp, idx, e)] = list(range(nv + 1, nv + 1 + D))
                nv += D
    cls: list[list[int]] = []
    for key, row in u.items():
        if key[2] not in E:
            continue
        cls.append(list(row))
        for i in range(D):
            for j in range(i + 1, D):
                cls.append([-row[i], -row[j]])

    def distinct(slots):
        for x in range(len(slots)):
            for y in range(x + 1, len(slots)):
                for i in range(D):
                    cls.append([-u[slots[x]][i], -u[slots[y]][i]])

    for e in E:
        # every X-check with eps(g) = e, and every Z-check
        distinct([(("X", "L"), s, e) for s in range(k)]
                 + [(("X", "R"), t, e) for t in range(l)])
        distinct([(("Z", "L"), t, e) for t in range(l)]
                 + [(("Z", "R"), s, e) for s in range(k)])
        # every L-qubit with eps(h) = e, and every R-qubit
        distinct([(("X", "L"), s, e ^ ea[s]) for s in range(k)]
                 + [(("Z", "L"), t, e ^ eb[t]) for t in range(l)])
        distinct([(("X", "R"), t, e ^ eb[t]) for t in range(l)]
                 + [(("Z", "R"), s, e ^ ea[s]) for s in range(k)])

    def orient(ka, kb):
        nonlocal nv
        nv += 1
        o = nv
        for i in range(D):
            for j in range(D):
                cls.append([-u[ka][i], -u[kb][j], o if i < j else -o])
        return o

    for delta, sts in code.sum_sets().items():
        ed = eps_value(coeffs, delta)
        for e in E:
            bits = []
            for (s, t) in sts:
                bits.append(orient((("X", "L"), s, e), (("Z", "L"), t, e ^ ed)))
                bits.append(orient((("X", "R"), t, e), (("Z", "R"), s, e ^ ed)))
            acc = bits[0]
            for nxt in bits[1:-1]:
                nv += 1
                tvar = nv
                cls.extend([[-tvar, acc, nxt], [-tvar, -acc, -nxt],
                            [tvar, -acc, nxt], [tvar, acc, -nxt]])
                acc = tvar
            cls.append([-acc, bits[-1]])
            cls.append([acc, -bits[-1]])

    with Solver(name=solver_name, bootstrap_with=cls) as s:
        if not s.solve():
            return None
        true = {v for v in s.get_model() if v > 0}
    labels: dict[tuple, dict[int, tuple]] = {}
    for grp in LABEL_GROUPS:
        labels[grp] = {}
        for e in E:
            labels[grp][e] = tuple(
                next(i + 1 for i in range(D) if u[(grp, idx, e)][i] in true)
                for idx in range(size[grp]))
    return labels, expand_twisted_schedule(code, labels, coeffs)


def expand_twisted_schedule(code: TwoBlockCode, labels, coeffs) -> list[int]:
    lay = [0] * code.n_edges
    for e in code.edges:
        eg = eps_value(coeffs, code.G.elements[e.check])
        lay[e.eid] = labels[(e.kind, e.side)][eg][e.lab]
    return lay


# ---------------------------------------------------------------------------
# eps: G -> Z_m twisted invariant schedules (generalises the Z2 version above)
#
#       lay(e) = f( label(e), eps(check(e)) ),   eps: G -> Z_m a homomorphism
#
# With 2*Delta labels and m grading values this is a 2*Delta*m-variable problem
# (12m for k = l = 3).  Because eps is a homomorphism the offsets eps(a_s),
# eps(b_t) and eps(delta) are the only way the group enters.
# ---------------------------------------------------------------------------
def homomorphisms_to_Zm(group, m: int) -> list[dict]:
    """Every homomorphism eps: G -> Z_m.

    eps(g) = sum_i c_i g_i mod m is well defined iff n_i c_i = 0 mod m, i.e. iff
    c_i is a multiple of m / gcd(m, n_i); so there are prod_i gcd(m, n_i) of them.
    """
    import itertools as _it
    from math import gcd

    choices = []
    for n in group.dims:
        g = gcd(m, n)
        step = m // g
        choices.append(tuple(j * step for j in range(g)))
    out = []
    for c in _it.product(*choices):
        img = sorted({sum(ci * x for ci, x in zip(c, g)) % m for g in group.elements})
        name = "trivial" if not any(c) else "eps=" + "+".join(
            f"{ci}g{i+1}" for i, ci in enumerate(c) if ci)
        out.append(dict(coeffs=tuple(c), m=m, name=name, trivial=not any(c),
                        image=img, image_size=len(img)))
    return out


def eps_value_m(coeffs, g, m: int) -> int:
    return sum(c * x for c, x in zip(coeffs, g)) % m


def _twisted_cnf(k, l, ea, eb, deltas, E, D, m):
    """CNF for the twisted system.  `deltas` is a list of (ed, [(s,t), ...])."""
    size = {("X", "L"): k, ("X", "R"): l, ("Z", "L"): l, ("Z", "R"): k}
    nv = 0
    u: dict[tuple, list[int]] = {}
    for grp in LABEL_GROUPS:
        for idx in range(size[grp]):
            for e in E:
                u[(grp, idx, e)] = list(range(nv + 1, nv + 1 + D))
                nv += D
    cls: list[list[int]] = []
    for row in u.values():
        cls.append(list(row))
        for i in range(D):
            for j in range(i + 1, D):
                cls.append([-row[i], -row[j]])

    def distinct(slots):
        for x in range(len(slots)):
            for y in range(x + 1, len(slots)):
                for i in range(D):
                    cls.append([-u[slots[x]][i], -u[slots[y]][i]])

    def mod(e):
        return e % m

    for e in E:
        distinct([(("X", "L"), s, e) for s in range(k)]
                 + [(("X", "R"), t, e) for t in range(l)])
        distinct([(("Z", "L"), t, e) for t in range(l)]
                 + [(("Z", "R"), s, e) for s in range(k)])
        distinct([(("X", "L"), s, mod(e - ea[s])) for s in range(k)]
                 + [(("Z", "L"), t, mod(e + eb[t])) for t in range(l)])
        distinct([(("X", "R"), t, mod(e - eb[t])) for t in range(l)]
                 + [(("Z", "R"), s, mod(e + ea[s])) for s in range(k)])

    def orient(ka, kb):
        nonlocal nv
        nv += 1
        o = nv
        for i in range(D):
            for j in range(D):
                cls.append([-u[ka][i], -u[kb][j], o if i < j else -o])
        return o

    for ed, sts in deltas:
        for e in E:
            bits = []
            for (s, t) in sts:
                bits.append(orient((("X", "L"), s, e), (("Z", "L"), t, mod(e + ed))))
                bits.append(orient((("X", "R"), t, e), (("Z", "R"), s, mod(e + ed))))
            acc = bits[0]
            for nxt in bits[1:-1]:
                nv += 1
                tv = nv
                cls.extend([[-tv, acc, nxt], [-tv, -acc, -nxt],
                            [tv, -acc, nxt], [tv, acc, -nxt]])
                acc = tv
            cls.append([-acc, bits[-1]])
            cls.append([acc, -bits[-1]])
    return cls, u, size


UNKNOWN = "unknown"


def solve_twisted_system(k, l, ea, eb, deltas, E, D, m,
                         solver_name: str = "cadical195", conf_budget: int | None = None,
                         timeout: float | None = None):
    """Solve the label-level twisted system.

    Returns the labels dict (satisfiable), None (unsatisfiable), or the sentinel
    ``UNKNOWN`` when a conflict budget was given and ran out.  The budget is on
    conflicts, not wall clock, so a run is reproducible.
    """
    from pysat.solvers import Solver

    import threading

    if timeout and solver_name == "cadical195":
        # pysat's CaDiCaL has no limited-solve, so a wall-clock cap needs an
        # interruptible backend.  glucose42 supports it and is no slower here.
        solver_name = "glucose42"
    cls, u, size = _twisted_cnf(k, l, ea, eb, deltas, E, D, m)
    with Solver(name=solver_name, bootstrap_with=cls) as s:
        if timeout:
            # wall-clock cap: interrupt the solver from a timer thread
            timer = threading.Timer(float(timeout), s.interrupt)
            timer.start()
            try:
                res = s.solve_limited(expect_interrupt=True)
            finally:
                timer.cancel()
            if res is None:
                return UNKNOWN
            if not res:
                return None
        elif conf_budget:
            s.conf_budget(int(conf_budget))
            res = s.solve_limited()
            if res is None:
                return UNKNOWN
            if not res:
                return None
        elif not s.solve():
            return None
        true = {v for v in s.get_model() if v > 0}
    return {grp: {e: tuple(next(i + 1 for i in range(D) if u[(grp, idx, e)][i] in true)
                           for idx in range(size[grp])) for e in E}
            for grp in LABEL_GROUPS}


def find_twisted_invariant_schedule_Zm(code: TwoBlockCode, D: int, coeffs, m: int,
                                       solver_name: str = "cadical195",
                                       conf_budget: int | None = None,
                                       timeout: float | None = None):
    """eps: G -> Z_m twisted invariant search.

    Returns (labels, layers), None (no such schedule), or UNKNOWN if the conflict
    budget ran out.
    """
    G = code.G
    E = sorted({eps_value_m(coeffs, g, m) for g in G.elements})
    ea = [eps_value_m(coeffs, a, m) for a in code.A]
    eb = [eps_value_m(coeffs, b, m) for b in code.B]
    deltas = [(eps_value_m(coeffs, d, m), sts) for d, sts in code.sum_sets().items()]
    labels = solve_twisted_system(code.k, code.l, ea, eb, deltas, E, D, m, solver_name,
                                  conf_budget, timeout)
    if labels is UNKNOWN or labels == UNKNOWN:
        return UNKNOWN
    if labels is None:
        return None
    return labels, expand_twisted_schedule_Zm(code, labels, coeffs, m)


def expand_twisted_schedule_Zm(code: TwoBlockCode, labels, coeffs, m: int) -> list[int]:
    lay = [0] * code.n_edges
    for e in code.edges:
        eg = eps_value_m(coeffs, code.G.elements[e.check], m)
        lay[e.eid] = labels[(e.kind, e.side)][eg][e.lab]
    return lay

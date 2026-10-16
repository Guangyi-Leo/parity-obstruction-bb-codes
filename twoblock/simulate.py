"""Ground-truth properness check by F2 linear-map simulation of the CNOT circuit.

Registers (4N bits, in this order):
    0        .. N-1     data L_h
    N        .. 2N-1    data R_h
    2N       .. 3N-1    X-ancillas y_g
    3N       .. 4N-1    Z-ancillas z_g

For an X-edge (X_g, q):  CNOT control = y_g, target = data q.
For a Z-edge (Z_g, q):  CNOT control = data q, target = z_g.
CNOT(c -> t) acts on the transfer matrix as row_t ^= row_c.

Ideal map:  data' = data + H_X^T y,   y' = y,   z' = z + H_Z data.
A schedule is proper iff the simulated 4N x 4N matrix equals the ideal one.

Rows are stored as Python ints used as bitsets, which is exact and fast.
"""
from __future__ import annotations

from .code import TwoBlockCode


def _reg(code: TwoBlockCode, e) -> tuple[int, int]:
    """(control, target) register indices of the CNOT carried by edge ``e``."""
    N = code.N
    q = e.qubit + (0 if e.side == "L" else N)
    if e.kind == "X":
        return (2 * N + e.check, q)          # y_g -> data q
    return (q, 3 * N + e.check)              # data q -> z_g


def ideal_matrix(code: TwoBlockCode) -> list[int]:
    N = code.N
    rows = [1 << i for i in range(4 * N)]
    for e in code.edges:
        c, t = _reg(code, e)
        if e.kind == "X":
            rows[t] ^= 1 << c            # data q gets y_g
        else:
            rows[t] ^= 1 << c            # z_g gets initial data q
    return rows


def simulate(code: TwoBlockCode, schedule, depth: int | None = None,
             check_disjoint: bool = True) -> list[int]:
    """Run the circuit given by ``schedule`` (eid -> layer, 1-based); return the matrix rows."""
    lay = _as_list(code, schedule)
    D = depth if depth is not None else max(lay)
    N = code.N
    by_layer: list[list[int]] = [[] for _ in range(D + 1)]
    for eid, i in enumerate(lay):
        if not (1 <= i <= D):
            raise ValueError(f"edge {eid} has layer {i} outside 1..{D}")
        by_layer[i].append(eid)

    rows = [1 << i for i in range(4 * N)]
    for i in range(1, D + 1):
        if check_disjoint:
            touched: set[tuple[str, int]] = set()
            for eid in by_layer[i]:
                e = code.edges[eid]
                for v in ((e.kind, e.check), (e.side, e.qubit)):
                    if v in touched:
                        raise ValueError(f"layer {i} is not a matching: vertex {v} used twice")
                    touched.add(v)
        for eid in by_layer[i]:
            c, t = _reg(code, code.edges[eid])
            rows[t] ^= rows[c]
    return rows


def is_proper_by_simulation(code: TwoBlockCode, schedule, depth: int | None = None) -> bool:
    return simulate(code, schedule, depth) == ideal_matrix(code)


def orientation(code: TwoBlockCode, lay, corner) -> int:
    """o = 1 iff lay(eX) < lay(eZ)."""
    return 1 if lay[corner.ex] < lay[corner.ez] else 0


def is_proper_by_parity(code: TwoBlockCode, schedule) -> bool:
    """Direct evaluation of the properness condition (XOR of shared corner orientations)."""
    lay = _as_list(code, schedule)
    for op in code.overlap_pairs:
        par = 0
        for cid in op.corners:
            par ^= orientation(code, lay, code.corners[cid])
        if par:
            return False
    return True


def violated_pairs(code: TwoBlockCode, schedule) -> list:
    lay = _as_list(code, schedule)
    bad = []
    for op in code.overlap_pairs:
        par = 0
        for cid in op.corners:
            par ^= orientation(code, lay, code.corners[cid])
        if par:
            bad.append(op)
    return bad


def is_valid_layering(code: TwoBlockCode, schedule, depth: int) -> bool:
    """Vertex-distinctness: incident edges at every vertex get distinct layers."""
    lay = _as_list(code, schedule)
    if any(not (1 <= i <= depth) for i in lay):
        return False
    for v in code.vertices:
        ls = [lay[e] for e in code.incident(v)]
        if len(set(ls)) != len(ls):
            return False
    return True


def _as_list(code: TwoBlockCode, schedule) -> list[int]:
    if isinstance(schedule, dict):
        return [int(schedule[e]) for e in range(code.n_edges)]
    lay = list(schedule)
    if len(lay) != code.n_edges:
        raise ValueError(f"schedule has {len(lay)} entries, expected {code.n_edges}")
    return [int(x) for x in lay]


def deviation_rows(code: TwoBlockCode, schedule, depth: int | None = None) -> list[int]:
    """XOR of the simulated matrix with the ideal one (all-zero iff proper)."""
    sim = simulate(code, schedule, depth)
    ide = ideal_matrix(code)
    return [s ^ i for s, i in zip(sim, ide)]


def simulation_pair_parities(code: TwoBlockCode, schedule, depth: int | None = None) -> dict:
    """Coefficient of y_g in the final z_{g'} deviation, for every overlap pair.

    Also asserts that the circuit can deviate from the ideal map *only* in those
    entries: the data rows, the y rows and the data-coefficients of the z rows
    must always match the ideal map exactly.
    """
    N = code.N
    dev = deviation_rows(code, schedule, depth)
    for r in range(3 * N):                       # data rows and y rows
        if dev[r]:
            raise AssertionError(f"unexpected deviation in row {r} (data/ancilla-y block)")
    mask_y = ((1 << N) - 1) << (2 * N)
    out = {}
    for g in range(N):
        d = dev[3 * N + g]
        if d & ~mask_y:
            raise AssertionError(f"unexpected deviation outside the y-block in z-row {g}")
        for gx in range(N):
            bit = (d >> (2 * N + gx)) & 1
            if bit:
                out[(gx, g)] = 1
    return out

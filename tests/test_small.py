"""Brute-force cross-checks on tiny instances (specification section 7).

Run with `python -m tests.test_small` or `pytest tests/test_small.py`.
All randomness is seeded with seed = 7.
"""
from __future__ import annotations

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pysat.solvers import Cadical195                                    # noqa: E402

from twoblock.code import TwoBlockCode                                  # noqa: E402
from twoblock.encode import (                                           # noqa: E402
    encode, find_invariant_schedule, schedule_assumptions,
)
from twoblock.enumerate import enumerate_solutions                      # noqa: E402
from twoblock import instances                                          # noqa: E402
from twoblock.simulate import (                                         # noqa: E402
    is_proper_by_parity, is_proper_by_simulation, is_valid_layering,
    simulation_pair_parities,
)

SEED = 7

# Random valid layerings drawn per instance in T2, where the parity criterion is
# checked against the F2 simulation.  Recorded in data/t7_model_coverage.csv so the
# manuscript can cite the coverage instead of a remembered number.
N_AGREEMENT_SAMPLES = 300
COVERAGE: list[dict] = []


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def random_layering(code: TwoBlockCode, D: int, rng: random.Random,
                    greedy_tries: int = 40) -> list[int]:
    """A uniform-ish random proper edge colouring with D colours.

    Repeated randomized greedy; if greedy gets stuck (which happens when D equals
    the maximum degree) the partial colouring is completed with the standard
    bipartite alternating-path (Kempe) repair, which always succeeds for D >= Delta.
    """
    edges = list(range(code.n_edges))
    ends = [(("X" if e.kind == "X" else "Z", e.check), (e.side, e.qubit)) for e in code.edges]
    for _ in range(greedy_tries):
        lay = [0] * code.n_edges
        used: dict[tuple, set[int]] = {v: set() for v in code.vertices}
        rng.shuffle(edges)
        ok = True
        for eid in edges:
            u, v = ends[eid]
            free = [c for c in range(1, D + 1) if c not in used[u] and c not in used[v]]
            if not free:
                ok = False
                break
            c = rng.choice(free)
            lay[eid] = c
            used[u].add(c)
            used[v].add(c)
        if ok:
            return lay
    return _kempe_colouring(code, D, rng)


def _kempe_colouring(code: TwoBlockCode, D: int, rng: random.Random) -> list[int]:
    lay = [0] * code.n_edges
    used: dict[tuple, dict[int, int]] = {v: {} for v in code.vertices}   # colour -> eid
    ends = [(("X" if e.kind == "X" else "Z", e.check), (e.side, e.qubit)) for e in code.edges]
    order = list(range(code.n_edges))
    rng.shuffle(order)
    for eid in order:
        u, v = ends[eid]
        fu = [c for c in range(1, D + 1) if c not in used[u]]
        fv = [c for c in range(1, D + 1) if c not in used[v]]
        common = [c for c in fu if c in fv]
        if common:
            c = rng.choice(common)
            lay[eid] = c
            used[u][c] = used[v][c] = eid
            continue
        alpha, beta = rng.choice(fu), rng.choice(fv)      # alpha free at u, beta free at v
        # Flip the maximal alpha/beta alternating path starting at v.  beta is free
        # at v, so the path leaves v along its alpha-edge; the graph is bipartite and
        # alpha is free at u, so the path cannot reach u.  After the flip alpha is
        # free at both ends and the edge can take it.
        node, cur = v, alpha
        path = []
        while cur in used[node]:
            f = used[node][cur]
            a, b = ends[f]
            nxt = b if a == node else a
            assert nxt != u, "alternating path reached u (impossible in a bipartite graph)"
            path.append((f, node, nxt, cur))
            node, cur = nxt, (beta if cur == alpha else alpha)
        for f, n1, n2, c in path:
            del used[n1][c]
            del used[n2][c]
        for f, n1, n2, c in path:
            other = beta if c == alpha else alpha
            lay[f] = other
            used[n1][other] = used[n2][other] = f
        lay[eid] = alpha
        used[u][alpha] = used[v][alpha] = eid
    assert is_valid_layering(code, lay, D), "Kempe repair produced an invalid colouring"
    return lay


def brute_force_layerings(code: TwoBlockCode, D: int):
    """All layerings satisfying vertex distinctness (DFS with pruning)."""
    n = code.n_edges
    ends = [(("X" if e.kind == "X" else "Z", e.check), (e.side, e.qubit)) for e in code.edges]
    used: dict[tuple, set[int]] = {v: set() for v in code.vertices}
    lay = [0] * n

    def rec(i: int):
        if i == n:
            yield list(lay)
            return
        u, v = ends[i]
        for c in range(1, D + 1):
            if c in used[u] or c in used[v]:
                continue
            used[u].add(c)
            used[v].add(c)
            lay[i] = c
            yield from rec(i + 1)
            used[u].discard(c)
            used[v].discard(c)
    yield from rec(0)


def sat_count_all(code: TwoBlockCode, D: int, limit: int = 10 ** 7) -> int:
    res = enumerate_solutions(code, D, max_solutions=limit, verify=True, symmetry_breaking=False)
    assert res["exhausted"], "SAT enumeration hit the solution cap"
    return res["n_solutions"]


# --------------------------------------------------------------------------
# T1  structure
# --------------------------------------------------------------------------
def test_T1_structure():
    import numpy as np
    code = instances.get("bb72")
    facts = code.check_structure()
    assert facts["N"] == 36 and facts["k"] == 3 and facts["l"] == 3 and facts["Delta"] == 6
    assert code.n_edges == 2 * code.N * code.Delta == 432
    M = code.overlap_matrix()
    assert set(np.unique(M).tolist()) <= {0, 2}, f"overlap entries {np.unique(M)} not in {{0,2}}"
    assert facts["max_overlap_entry"] == 2 and facts["distinct_sums"]
    for gi in range(code.N):
        assert len(code.check_edges[("X", gi)]) == 6
        assert len(code.check_edges[("Z", gi)]) == 6
    for hi in range(code.N):
        for side in ("L", "R"):
            assert len(code.data_edges[(side, hi)]) == 6
    print("T1 structure: OK (bb72: 432 edges, all degrees 6, overlap entries in {0,2})")


# --------------------------------------------------------------------------
# T2  parity condition vs F2 simulation on random valid layerings
# --------------------------------------------------------------------------
def _agreement_samples(code: TwoBlockCode, D: int, n: int, rng: random.Random) -> tuple[int, int]:
    proper = 0
    for _ in range(n):
        lay = random_layering(code, D, rng)
        assert is_valid_layering(code, lay, D)
        par = is_proper_by_parity(code, lay)
        sim = is_proper_by_simulation(code, lay, D)
        assert par == sim, (f"{code.name} D={D}: parity={par} but simulation={sim}\n"
                            f"minimal failing layering: {lay}")
        # stronger: per-overlap-pair agreement, meaningful even when nothing is proper
        sim_pairs = simulation_pair_parities(code, lay, D)
        want = {}
        for op in code.overlap_pairs:
            p = 0
            for cid in op.corners:
                c = code.corners[cid]
                p ^= 1 if lay[c.ex] < lay[c.ez] else 0
            if p:
                want[(op.gx, op.gz)] = 1
        assert sim_pairs == want, (f"{code.name} D={D}: per-pair parity mismatch\n"
                                   f"  simulation-only: {set(sim_pairs) - set(want)}\n"
                                   f"  parity-only:     {set(want) - set(sim_pairs)}\n"
                                   f"  layering: {lay}")
        proper += int(sim)
    return proper, n


def test_T2_encoding_vs_simulation():
    rng = random.Random(SEED)
    for name in ("oe21", "oe12"):
        code = instances.get(name)
        code.check_structure()
        p, n = _agreement_samples(code, code.Delta, N_AGREEMENT_SAMPLES, rng)
        # every sample is asserted to agree, so reaching here means n_agree == n
        COVERAGE.append(dict(test="T2", instance=name, n_layerings=n, n_agree=n,
                             note=f"random valid depth-{code.Delta} layerings; "
                                  f"parity == F2 simulation; {p} proper"))
        print(f"T2 {name} D={code.Delta}: {n} random layerings agree "
              f"(parity == simulation); {p} of them proper")
    # an instance with coinciding sums
    code = TwoBlockCode((8, 1), [(0, 0), (1, 0), (2, 0)], [(0, 0), (2, 0), (4, 0)], "coinc831")
    code.check_structure()
    assert not code.distinct_sums(), "the coinciding-sums instance should have repeated sums"
    print(f"T2 coinc831: multiplicity histogram {code.multiplicity_histogram()}, "
          f"max overlap entry {code.overlap_matrix().max()}")
    for D in (6, 7):
        p, n = _agreement_samples(code, D, 300, rng)
        print(f"T2 coinc831 D={D}: {n} random layerings agree; {p} of them proper")


# --------------------------------------------------------------------------
# T3  exhaustive: brute force vs SAT enumeration
# --------------------------------------------------------------------------
def test_T3_exhaustive():
    for A, B, D in ([(0, 0)], [(0, 0)], 2), ([(0, 0)], [(0, 0), (1, 0)], 3):
        code = TwoBlockCode((3, 1), A, B, f"tiny_{len(A)}{len(B)}")
        code.check_structure()
        total = proper = 0
        for lay in brute_force_layerings(code, D):
            total += 1
            if is_proper_by_simulation(code, lay, D):
                proper += 1
                assert is_proper_by_parity(code, lay)
        got = sat_count_all(code, D)
        assert got == proper, (f"{code.name} D={D}: brute force found {proper} proper layerings "
                               f"out of {total}, SAT enumeration returned {got}")
        print(f"T3 {code.name} D={D}: {total} valid layerings, {proper} proper, "
              f"SAT enumeration agrees ({got})")
    # Same equality on two full-size one-even codes, where the search space is large
    # enough that an over- or under-constrained encoding could not agree by accident.
    for name in ("oe21", "oe12"):
        code = instances.get(name)
        D = code.Delta
        total = proper = 0
        for lay in brute_force_layerings(code, D):
            total += 1
            if is_proper_by_simulation(code, lay, D):
                proper += 1
                assert is_proper_by_parity(code, lay)
        got = sat_count_all(code, D)
        assert got == proper, (f"{name} D={D}: brute force found {proper} proper layerings "
                               f"out of {total}, SAT enumeration returned {got}")
        print(f"T3 {name} D={D}: {total} valid layerings, {proper} proper, "
              f"SAT enumeration agrees ({got})")


# --------------------------------------------------------------------------
# T4  decode round trip
# --------------------------------------------------------------------------
def test_T4_round_trip():
    for name in ("oe21", "oe12", "oe23"):
        code = instances.get(name)
        D = code.Delta
        enc = encode(code, D)
        s = Cadical195(bootstrap_with=enc.clauses)
        assert s.solve(), f"{name} should be SAT at depth {D}"
        lay = enc.decode_model(s.get_model())
        s.delete()
        assert is_proper_by_simulation(code, lay, D)
        enc2 = encode(code, D, assumptions=schedule_assumptions(code, lay))
        s2 = Cadical195(bootstrap_with=enc2.clauses)
        assert s2.solve(), f"{name}: re-encoding the decoded schedule as units is UNSAT"
        lay2 = enc2.decode_model(s2.get_model())
        s2.delete()
        assert lay2 == lay, f"{name}: round trip changed the schedule"
        print(f"T4 {name} D={D}: model -> schedule -> unit assumptions -> SAT, identical")


# --------------------------------------------------------------------------
# T5  (beyond the specified T1-T4) the depth-6 refutations are caused by
#     properness, not by the vertex constraints
# --------------------------------------------------------------------------
def test_T5_depth6_structurally_feasible():
    """A valid depth-Delta layering exists for every IBM code.

    The Tanner graph is bipartite with maximum degree Delta, so by Koenig's theorem a
    proper Delta-edge-colouring exists; this constructs one explicitly.  Hence the
    depth-6 UNSAT results are not an artefact of the exactly-one / vertex-distinctness
    clauses -- those are satisfiable at depth 6 -- but come from the properness
    constraint alone.
    """
    rng = random.Random(SEED)
    for name in ("bb72", "bb90", "bb108", "bb144", "bb288", "bb360", "bb756"):
        code = instances.get(name)
        D = code.Delta
        lay = random_layering(code, D, rng, greedy_tries=1)
        assert is_valid_layering(code, lay, D), f"{name}: no valid depth-{D} layering built"
        proper = is_proper_by_simulation(code, lay, D)
        assert is_proper_by_parity(code, lay) == proper
        print(f"T5 {name}: a valid depth-{D} layering exists "
              f"(vertex constraints satisfiable); this one is "
              f"{'proper' if proper else 'improper'}")


# --------------------------------------------------------------------------
# T6  (beyond the specified T1-T4) layer reversal really is a symmetry
# --------------------------------------------------------------------------
def test_T6_layer_reversal_is_a_symmetry():
    """The one symmetry-breaking clause in the encoding must be sound.

    `encode` adds a single clause forcing the s=1 L-edge of X_{(0,0)} into the first
    ceil(D/2) layers.  That is only sound if i -> D+1-i maps proper schedules to proper
    schedules: reversal flips every corner orientation, and every overlap pair has an
    even number of corners (2*|P(delta)|), so the XOR is preserved.  An unsound clause
    here would invalidate every UNSAT result, so it is checked directly.
    """
    n = 0
    for name in ("oe21", "oe12", "oe23", "oe43"):
        code = instances.get(name)
        D = code.Delta
        res = enumerate_solutions(code, D, max_solutions=40, verify=True)
        assert res["n_solutions"] > 0, f"{name}: expected at least one proper schedule"
        for lay in res["solutions"]:
            rev = [D + 1 - x for x in lay]
            assert is_valid_layering(code, rev, D), f"{name}: reversal broke vertex distinctness"
            assert is_proper_by_simulation(code, rev, D), \
                f"{name}: reversal of a proper schedule is not proper -- the " \
                f"symmetry-breaking clause is unsound\n  schedule: {lay}"
            n += 1
        print(f"T6 {name} D={D}: {res['n_solutions']} schedules, all reversals still proper")
    # and at depth 7 on the large codes, via the translation-invariant witness
    for name in ("bb72", "bb144", "bb756"):
        code = instances.get(name)
        D = 7
        found = find_invariant_schedule(code, D)
        assert found is not None
        lay = found[1]
        rev = [D + 1 - x for x in lay]
        assert is_valid_layering(code, rev, D) and is_proper_by_simulation(code, rev, D), \
            f"{name}: depth-7 reversal is not proper"
        n += 1
        print(f"T6 {name} D=7: reversal of the invariant schedule is still proper")
    print(f"T6: layer reversal verified as a symmetry on {n} proper schedules")


# --------------------------------------------------------------------------
# T7  (beyond the specified T1-T4) model coverage: every constraint family is
#     load-bearing.  See MODEL.md.
# --------------------------------------------------------------------------
def _solve_without(code, D, family):
    """Solve the encoding with one constraint family deleted."""
    enc = encode(code, D)
    a, b = enc.family_ranges[family]
    cls = enc.clauses[:a] + enc.clauses[b:]
    s = Cadical195(bootstrap_with=cls)
    ok = s.solve()
    model = s.get_model() if ok else None
    s.delete()
    return enc, ok, model


def test_T7_model_coverage():
    """Ablate each constraint family and check something observable breaks.

    A family that can be deleted with no observable consequence is either redundant
    or untested; this test fails in that case.
    """
    code = instances.get("oe12")
    D = code.Delta
    findings = {}

    # exactly_one: an edge may end up with no layer, or several
    enc, ok, model = _solve_without(code, D, "exactly_one")
    assert ok, "dropping exactly-one should leave the formula satisfiable"
    true = {v for v in model if v > 0}
    bad = [e for e in range(code.n_edges)
           if sum(1 for i in range(D) if enc.y[e][i] in true) != 1]
    findings["exactly_one"] = f"{len(bad)} edges without exactly one layer"
    assert bad, "dropping exactly-one changed nothing: family is not load-bearing"

    # vertex: the decoded layering may violate vertex distinctness
    for fam, check in (("vertex", "valid"), ("pdef", "proper"), ("corner", "proper")):
        found = False
        for _ in range(40):
            enc, ok, model = _solve_without(code, D, fam)
            assert ok
            try:
                lay = enc.decode_model(model)
            except ValueError:
                found = True
                break
            if check == "valid" and not is_valid_layering(code, lay, D):
                found = True
                break
            if check == "proper" and not is_proper_by_simulation(code, lay, D):
                found = True
                break
            # force a different model next round
            enc.clauses.append([-enc.yvar(e, lay[e]) for e in range(code.n_edges)])
        findings[fam] = ("a model violating "
                         + ("vertex distinctness" if check == "valid" else "properness")
                         + " becomes reachable")
        assert found, f"dropping {fam} produced no observable violation in 40 models"

    # proper: an instance that is UNSAT at depth Delta becomes SAT
    ref = instances.get("bb72")
    enc, ok, _ = _solve_without(ref, ref.Delta, "proper")
    assert ok, "bb72 at depth 6 must become satisfiable once properness is dropped"
    findings["proper"] = "bb72 depth 6 flips UNSAT -> SAT"

    # symmetry: it removes solutions.  oe12 is a poor witness (all its solutions
    # already satisfy the clause), so use oe21, where the reversal pair is split.
    sym = instances.get("oe21")
    full = enumerate_solutions(sym, sym.Delta, max_solutions=100, symmetry_breaking=True)
    none_ = enumerate_solutions(sym, sym.Delta, max_solutions=100, symmetry_breaking=False)
    assert none_["n_solutions"] > full["n_solutions"], (
        "the symmetry clause removed no solution of oe21: not load-bearing")
    findings["symmetry"] = (f"oe21: {full['n_solutions']} solutions with the clause, "
                            f"{none_['n_solutions']} without")

    for k, v in findings.items():
        COVERAGE.append(dict(test="T7", instance=f"{code.name}/{k}", n_layerings=0,
                             n_agree=0, note=f"constraint family ablated: {v}"))
        print(f"T7 {k:12}: {v}")
    print(f"T7: all {len(findings)} constraint families of MODEL.md are load-bearing")


def test_T9_class_C1_definition():
    """C1 means one delta of multiplicity 2 and nothing higher.

    G = Z8, A = {0,1,4}, B = {0,7,4} is the trap: it has one delta of multiplicity 2
    AND one of multiplicity 3, so n4 = N is satisfied while n6 = N is not zero.  A
    classifier that tested only "n4 == N" would call it C1.
    """
    from twoblock.overlaps import counts

    code = TwoBlockCode((8,), [(0,), (1,), (4,)], [(0,), (7,), (4,)], "Z8_014_074")
    code.check_structure()
    r = counts(code)
    sizes = sorted(len(v) for v in code.sum_sets().values())
    assert sizes == [1, 1, 1, 1, 2, 3], f"unexpected multiplicities {sizes}"
    assert r["n4"] == r["N"] and r["n6"] == r["N"], (
        f"expected n4 = n6 = N = {r['N']}, got n4={r['n4']} n6={r['n6']}")
    assert r["klass"] != "C1", f"Z8 {{0,1,4}}/{{0,7,4}} must not be class C1"
    # C2 in this taxonomy is (n4, n6) = (2N, 0) or (0, N); this pattern is neither,
    # so it lands in `other`.  What matters for the C1 claim is only that it is not C1.
    assert r["klass"] == "other", f"expected class 'other', got {r['klass']}"
    print(f"T9 Z8 {{0,1,4}}/{{0,7,4}}: multiplicities {sizes}, "
          f"n4={r['n4']} n6={r['n6']} -> class {r['klass']} (not C1)")
    for name in ("h2_Z10_C1_0",):
        try:
            c = instances.get(name)
        except Exception:
            continue
        rr = counts(c)
        assert rr["klass"] == "C1" and rr["n6"] == 0
    print("T9: the class-C1 definition (n4 = N and n6 = 0) is enforced")


TESTS = [test_T1_structure, test_T2_encoding_vs_simulation, test_T3_exhaustive,
         test_T4_round_trip, test_T5_depth6_structurally_feasible,
         test_T6_layer_reversal_is_a_symmetry, test_T7_model_coverage,
         test_T9_class_C1_definition]


COVERAGE_CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "data", "t7_model_coverage.csv")


def write_coverage():
    import csv
    os.makedirs(os.path.dirname(COVERAGE_CSV), exist_ok=True)
    with open(COVERAGE_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["test", "instance", "n_layerings",
                                          "n_agree", "note"])
        w.writeheader()
        w.writerows(COVERAGE)
    print(f"[wrote {os.path.relpath(COVERAGE_CSV)}: {len(COVERAGE)} rows, "
          f"{sum(r['n_layerings'] for r in COVERAGE)} random layerings checked]")


def main():
    fails = 0
    for t in TESTS:
        print(f"\n=== {t.__name__} ===", flush=True)
        try:
            t()
        except AssertionError as ex:
            fails += 1
            print(f"FAIL {t.__name__}:\n{ex}", flush=True)
    write_coverage()
    print("\n" + ("ALL TESTS PASSED" if not fails else f"{fails} TEST(S) FAILED"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

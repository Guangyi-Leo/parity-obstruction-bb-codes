#!/usr/bin/env python3
"""Hook-orientation census for depth-optimal syndrome-extraction schedules.

Builds the rotated distance-d surface code programmatically (with internal
validation of stabilizer counts, commutation relations, GF(2) ranks, and logical
operators), then:

  (1) verifies that the standard interleaved schedule is a proper 4-edge-coloring
      of the joint Tanner graph with ZERO 'parallel' midpoint hook pairs;
  (2) samples R random proper 4-edge-colorings (randomized greedy with restarts;
      NOT uniform -- disclosed) and counts, for each weight-4 check, whether the
      midpoint-fault hook pair (the two data qubits touched by the 3rd and 4th
      CNOTs of that check) is PARALLEL to the corresponding logical operator
      (X-checks: same-row pair, since logical X is a row; Z-checks: same-column
      pair, since logical Z is a column). Such parallel hooks are the mechanism
      by which a single ancilla fault advances an error chain by two sites
      [Dennis et al. 2002; Tomita & Svore 2014].

Diagonal midpoint pairs are tallied separately and conservatively NOT counted as
parallel (their effect requires circuit-level analysis; see stim script).

Output: results/hook_census.json
Usage:  python3 experiments/hook_schedule_census.py --d 3 5 7 --samples 200 --seed 23
"""
import argparse, itertools, json, os, random


def f2_rank(rows):
    rows = [int("".join(map(str, r)), 2) if isinstance(r, list) else r for r in rows]
    rank = 0
    for i in range(max((r.bit_length() for r in rows), default=0)):
        piv = None
        for j, r in enumerate(rows):
            if (r >> i) & 1:
                piv = j
                break
        if piv is None:
            continue
        pr = rows.pop(piv)
        rows = [r ^ pr if (r >> i) & 1 else r for r in rows]
        rank += 1
    return rank


def build_code(d, parity_X, th, tv):
    """Return (checks, ok). checks: list of dicts {type, corners(list, NW,NE,SW,SE order
    with None for missing)}. Validation: counts, commutation, ranks, logicals."""
    data = [(r, c) for r in range(d) for c in range(d)]
    didx = {q: i for i, q in enumerate(data)}
    checks = []
    for fr in range(-1, d):
        for fc in range(-1, d):
            corners = [(fr, fc), (fr, fc + 1), (fr + 1, fc), (fr + 1, fc + 1)]  # NW NE SW SE
            inside = [q if (0 <= q[0] < d and 0 <= q[1] < d) else None for q in corners]
            sup = [q for q in inside if q is not None]
            if len(sup) < 2:
                continue
            typ = "X" if (fr + fc) % 2 == parity_X else "Z"
            if len(sup) == 2:
                horiz = sup[0][0] == sup[1][0]
                if horiz and typ != th:
                    continue
                if (not horiz) and typ != tv:
                    continue
            checks.append({"type": typ, "corners": inside, "support": sup})
    nX = sum(1 for ch in checks if ch["type"] == "X")
    nZ = len(checks) - nX
    if len(checks) != d * d - 1 or nX != nZ:
        return checks, False
    # commutation of X checks with Z checks
    for cx, cz in itertools.product([c for c in checks if c["type"] == "X"],
                                    [c for c in checks if c["type"] == "Z"]):
        if len(set(cx["support"]) & set(cz["support"])) % 2:
            return checks, False
    # logicals: Xbar = row 0 (horizontal), Zbar = column 0 (vertical)
    Xbar = {(0, c) for c in range(d)}
    Zbar = {(r, 0) for r in range(d)}
    for ch in checks:
        if ch["type"] == "Z" and len(Xbar & set(ch["support"])) % 2:
            return checks, False
        if ch["type"] == "X" and len(Zbar & set(ch["support"])) % 2:
            return checks, False
    if len(Xbar & Zbar) % 2 == 0:
        return checks, False
    # independence: GF(2) rank of each sector equals its count
    for t in "XZ":
        rows = []
        for ch in checks:
            if ch["type"] == t:
                v = 0
                for q in ch["support"]:
                    v |= 1 << didx[q]
                rows.append(v)
        if f2_rank(rows) != (d * d - 1) // 2:
            return checks, False
    return checks, True


def standard_times(ch):
    """Standard interleaved schedule: X checks column-major (NW,SW,NE,SE),
    Z checks row-major (NW,NE,SW,SE); positions with None are skipped."""
    NW, NE, SW, SE = ch["corners"]
    if ch["type"] == "X":
        seq = [NW, SW, NE, SE]
    else:
        seq = [NW, NE, SW, SE]
    return {q: t for t, q in enumerate(seq) if q is not None}


def proper(coloring_per_check):
    for t in range(4):
        seen = set()
        for times in coloring_per_check:
            for q, tt in times.items():
                if tt == t:
                    if q in seen:
                        return False
                    seen.add(q)
    return True


def hook_stats(checks, colorings):
    badX = badZ = diag = 0
    for ch, times in zip(checks, colorings):
        if len(ch["support"]) != 4:
            continue
        pair = sorted(times, key=times.get)[2:]
        (r1, c1), (r2, c2) = pair
        if r1 == r2:      # row-aligned pair
            if ch["type"] == "X":
                badX += 1
        elif c1 == c2:    # column-aligned pair
            if ch["type"] == "Z":
                badZ += 1
        else:
            diag += 1
    return badX, badZ, diag


def random_coloring(checks, rng, max_restarts=2000):
    """Randomized greedy proper 4-edge-coloring of the joint Tanner graph."""
    edges = [(i, q) for i, ch in enumerate(checks) for q in ch["support"]]
    for _ in range(max_restarts):
        rng.shuffle(edges)
        used_c = [set() for _ in checks]          # colors used at each check
        used_q = {}                               # colors used at each data qubit
        times = [dict() for _ in checks]
        pend = list(edges)
        ok = True
        while pend:
            # most-constrained edge first
            pend.sort(key=lambda e: len(used_c[e[0]] | used_q.get(e[1], set())),
                      reverse=True)
            i, q = pend.pop(0)
            avail = [c for c in range(4)
                     if c not in used_c[i] and c not in used_q.get(q, set())]
            if not avail:
                ok = False
                break
            c = rng.choice(avail)
            used_c[i].add(c)
            used_q.setdefault(q, set()).add(c)
            times[i][q] = c
        if ok:
            return times
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--d", type=int, nargs="+", default=[3, 5, 7])
    ap.add_argument("--samples", type=int, default=200)
    ap.add_argument("--seed", type=int, default=23)
    ap.add_argument("--out", default="results/hook_census.json")
    args = ap.parse_args()
    out = {}
    for d in args.d:
        rng = random.Random(args.seed + d)
        code = None
        for parity_X in (0, 1):
            for th, tv in (("X", "Z"), ("Z", "X")):
                checks, ok = build_code(d, parity_X, th, tv)
                if ok:
                    code = checks
                    cfg = (parity_X, th, tv)
                    break
            if code:
                break
        assert code is not None, f"no valid rotated-code configuration found for d={d}"
        std = [standard_times(ch) for ch in code]
        assert proper(std), "standard schedule failed properness check"
        sx, sz, sd_ = hook_stats(code, std)
        assert sx == 0 and sz == 0, "standard schedule has parallel hooks (convention error)"
        n4 = sum(1 for ch in code if len(ch["support"]) == 4)
        res = {"config": {"parity_X": cfg[0], "boundary_h": cfg[1], "boundary_v": cfg[2]},
               "checks": len(code), "weight4_checks": n4,
               "standard": {"proper": True, "parallel_hooks": 0, "diagonal_pairs": sd_},
               "samples": 0, "frac_any_parallel": None,
               "mean_parallel_X": 0.0, "mean_parallel_Z": 0.0, "mean_diagonal": 0.0}
        nb = nx_ = nz_ = nd_ = 0
        for _ in range(args.samples):
            col = random_coloring(code, rng)
            if col is None:
                continue
            assert proper(col)
            bx, bz, dg = hook_stats(code, col)
            res["samples"] += 1
            nb += int(bx + bz > 0)
            nx_ += bx; nz_ += bz; nd_ += dg
        if res["samples"]:
            res["frac_any_parallel"] = round(nb / res["samples"], 3)
            res["mean_parallel_X"] = round(nx_ / res["samples"], 2)
            res["mean_parallel_Z"] = round(nz_ / res["samples"], 2)
            res["mean_diagonal"] = round(nd_ / res["samples"], 2)
        out[f"d={d}"] = res
        print(f"d={d}: {res}")
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()

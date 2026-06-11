#!/usr/bin/env python3
"""Circuit-level validation (EXECUTED in this revision; stim 1.16).

Circuit-level ground truth for the hook-orientation census: build rotated
surface-code memory-Z experiments with (a) the standard interleaved schedule and
(b) random proper 4-edge-colorings, attach uniform depolarizing noise, and compute
the graphlike circuit-level distance with stim's
`search_for_undetectable_logical_errors`. Expectation (to be VERIFIED, not
assumed): standard schedule attains distance d; colorings flagged as containing
parallel midpoint hooks by experiments/hook_schedule_census.py attain distance
ceil(d/2)..d-1. Fills Supplementary Table S3 (circuit-distance column).

SAFETY: the script hard-asserts that (i) the noiseless circuit has deterministic
detectors and (ii) the standard schedule reproduces distance d. If either assert
fails, the lattice/schedule conventions are wrong and NO results are reported.

Usage: python3 experiments/stim_circuit_distance.py --d 3 5 --samples 20 --seed 23
Output: results/stim_distance.json
"""
import argparse, json, os, random, sys

try:
    import stim
except ImportError:
    sys.exit("BLOCKER: stim not installed. Run `pip install stim` and retry.")

# reuse the validated lattice/schedule builders from the census script
sys.path.insert(0, os.path.dirname(__file__))
from hook_schedule_census import build_code, standard_times, proper, random_coloring


def build_memory_circuit(d, checks, times, rounds, p):
    """Rotated memory-Z experiment with per-check CNOT times from `times`.
    Data qubits indexed 0..d^2-1 (row-major); ancillas follow."""
    data = [(r, c) for r in range(d) for c in range(d)]
    didx = {q: i for i, q in enumerate(data)}
    anc0 = len(data)
    c = stim.Circuit()
    nq = anc0 + len(checks)
    c.append("R", range(nq))
    if p:
        c.append("X_ERROR", range(nq), p)
    for ch_i, ch in enumerate(checks):
        if ch["type"] == "X":
            c.append("H", [anc0 + ch_i])
    prev = {}
    for rnd in range(rounds):
        for t in range(4):
            pairs = []
            for ch_i, ch in enumerate(checks):
                for q, tt in times[ch_i].items():
                    if tt == t:
                        a = anc0 + ch_i
                        if ch["type"] == "X":
                            pairs += [a, didx[q]]      # ancilla control -> data target
                        else:
                            pairs += [didx[q], a]      # data control -> ancilla target
            c.append("CX", pairs)
            if p:
                c.append("DEPOLARIZE2", pairs, p)
        for ch_i, ch in enumerate(checks):
            if ch["type"] == "X":
                c.append("H", [anc0 + ch_i])
        meas_order = []
        for ch_i in range(len(checks)):
            if p:
                c.append("X_ERROR", [anc0 + ch_i], p)
            c.append("MR", [anc0 + ch_i])
            meas_order.append(ch_i)
            if checks[ch_i]["type"] == "X":
                c.append("H", [anc0 + ch_i])
        M = len(meas_order)
        for k, ch_i in enumerate(meas_order):
            rec = stim.target_rec(-M + k)
            if rnd == 0:
                if checks[ch_i]["type"] == "Z":
                    c.append("DETECTOR", [rec])
            else:
                c.append("DETECTOR", [rec, stim.target_rec(-2 * M + k)])
        if p:
            c.append("DEPOLARIZE1", range(len(data)), p)
    c.append("M", range(len(data)))
    nD = len(data)
    for ch_i, ch in enumerate(checks):     # final data-readout detectors (Z checks)
        if ch["type"] == "Z":
            targs = [stim.target_rec(-nD + didx[q]) for q in ch["support"]]
            targs.append(stim.target_rec(-nD - len(checks) + ch_i))
            c.append("DETECTOR", targs)
    obs = [stim.target_rec(-nD + didx[(r, 0)]) for r in range(d)]  # logical Z = col 0
    c.append("OBSERVABLE_INCLUDE", obs, 0)
    return c


def graphlike_distance(circ):
    errs = circ.search_for_undetectable_logical_errors(
        dont_explore_detection_event_sets_with_size_above=6,
        dont_explore_edges_with_degree_above=9999,
        dont_explore_edges_increasing_symptom_degree=False,
        canonicalize_circuit_errors=True)
    return len(errs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--d", type=int, nargs="+", default=[3, 5])
    ap.add_argument("--samples", type=int, default=20)
    ap.add_argument("--seed", type=int, default=23)
    ap.add_argument("--p", type=float, default=1e-3)
    ap.add_argument("--out", default="results/stim_distance.json")
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
                    break
            if code:
                break
        std = [standard_times(ch) for ch in code]

        def mirrored_times(ch):
            """Order-swapped variant of the standard schedule: round-consistent,
            but its midpoint hook pairs are PARALLEL to the logical operators
            (the census flags every weight-4 check). Known to reduce the
            circuit-level distance to ~ceil(d/2) [Tomita & Svore 2014]."""
            NW, NE, SW, SE = ch["corners"]
            seq = [NW, NE, SW, SE] if ch["type"] == "X" else [NW, SW, NE, SE]
            return {q: t for t, q in enumerate(seq) if q is not None}

        mir = [mirrored_times(ch) for ch in code]
        # --- self-checks -----------------------------------------------------
        noiseless = build_memory_circuit(d, code, std, rounds=d, p=0.0)
        assert noiseless.detector_error_model(decompose_errors=False) is not None
        sampler = noiseless.compile_detector_sampler()
        dets, obs = sampler.sample(8, separate_observables=True)
        assert not dets.any() and not obs.any(), \
            "noiseless detectors not deterministic -- convention bug, aborting"
        circ_std = build_memory_circuit(d, code, std, rounds=d, p=args.p)
        dist_std = graphlike_distance(circ_std)
        assert dist_std == d, f"standard schedule distance {dist_std} != {d}, aborting"
        # mirrored (hook-parallel) schedule: consistency + circuit distance
        mir0 = build_memory_circuit(d, code, mir, rounds=d, p=0.0)
        mdets, mobs = mir0.compile_detector_sampler().sample(8, separate_observables=True)
        mir_consistent = (not mdets.any()) and (not mobs.any())
        dist_mir = graphlike_distance(
            build_memory_circuit(d, code, mir, rounds=d, p=args.p)) if mir_consistent else None
        # --- random colorings ------------------------------------------------
        # Three outcomes per sampled proper 4-coloring:
        #   "inconsistent": stim reports non-deterministic detectors, i.e. the
        #       coloring does not measure the intended stabilizers round-to-round
        #       (a *stronger* failure than hook orientation);
        #   integer D < d: valid cycle but reduced circuit-level distance;
        #   integer D = d: valid cycle at full distance.
        def parallel_hooks(times):
            nbad = 0
            for ch_i, ch in enumerate(code):
                if len(ch["support"]) != 4:
                    continue
                late = sorted(times[ch_i], key=lambda q: times[ch_i][q])[2:]
                (r1, c1), (r2, c2) = late
                if ch["type"] == "X" and r1 == r2:
                    nbad += 1          # X-hook pair parallel to logical X (row)
                if ch["type"] == "Z" and c1 == c2:
                    nbad += 1          # Z-hook pair parallel to logical Z (col)
            return nbad

        records, dists = [], []
        for _ in range(args.samples):
            col = random_coloring(code, rng)
            nh = parallel_hooks(col)
            circ = build_memory_circuit(d, code, col, rounds=d, p=args.p)
            try:
                D = graphlike_distance(circ)
                dists.append(D)
                records.append({"hooks": nh, "distance": D})
            except ValueError:
                records.append({"hooks": nh, "distance": "inconsistent"})
        ok = [r for r in records if r["distance"] != "inconsistent"]
        out[f"d={d}"] = {
            "standard_distance": dist_std,
            "mirrored_consistent": mir_consistent,
            "mirrored_distance": dist_mir,
            "samples": len(records),
            "n_cycle_inconsistent": len(records) - len(ok),
            "consistent_distances": [r["distance"] for r in ok],
            "min_consistent_distance": min(dists) if dists else None,
            "frac_consistent_below_d":
                round(sum(x < d for x in dists) / len(dists), 3) if dists else None,
            "records": records}
        print(f"d={d}: {out[f'd={d}']}")
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()

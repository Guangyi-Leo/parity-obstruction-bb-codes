"""Incremental enumeration of proper depth-D schedules with blocking clauses."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

from pysat.solvers import Cadical195

from .code import TwoBlockCode
from .encode import encode
from .simulate import is_proper_by_simulation, is_valid_layering

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHED = os.path.join(ROOT, "schedules")


def enum_path(name: str, D: int) -> str:
    return os.path.join(SCHED, f"{name}_d{D}_enum.json")


def enumerate_solutions(code: TwoBlockCode, D: int, max_solutions: int = 200,
                        timeout: float | None = None, verify: bool = True,
                        assumptions=None, progress: bool = False,
                        symmetry_breaking: bool = True) -> dict:
    """Enumerate up to ``max_solutions`` proper depth-D schedules; verify each by simulation."""
    enc = encode(code, D, assumptions=assumptions, symmetry_breaking=symmetry_breaking)
    solver = Cadical195(bootstrap_with=enc.clauses)
    sols: list[list[int]] = []
    t0 = time.time()
    exhausted = False
    while len(sols) < max_solutions:
        if timeout is not None and time.time() - t0 > timeout:
            break
        if not solver.solve():
            exhausted = True
            break
        model = solver.get_model()
        lay = enc.decode_model(model)
        if not is_valid_layering(code, lay, D):
            raise AssertionError(f"{code.name} d{D}: model violates vertex distinctness")
        if verify and not is_proper_by_simulation(code, lay, D):
            raise AssertionError(f"{code.name} d{D}: enumerated model is NOT proper by simulation")
        sols.append(lay)
        solver.add_clause([-enc.yvar(e, lay[e]) for e in range(code.n_edges)])
        if progress and len(sols) % 25 == 0:
            print(f"  {code.name} d{D}: {len(sols)} solutions ({time.time()-t0:.1f}s)", flush=True)
    solver.delete()
    return dict(instance=code.name, dims=list(code.G.dims),
                A=[list(a) for a in code.A], B=[list(b) for b in code.B],
                D=D, k=code.k, l=code.l, Delta=code.Delta, N=code.N,
                n_solutions=len(sols), exhausted=exhausted, verified_by_simulation=verify,
                symmetry_breaking=symmetry_breaking,
                time=round(time.time() - t0, 3), solutions=sols)


def save(result: dict) -> str:
    os.makedirs(SCHED, exist_ok=True)
    p = enum_path(result["instance"], result["D"])
    with open(p, "w") as f:
        json.dump(result, f)
    return p


def main(argv=None):
    from . import instances
    ap = argparse.ArgumentParser(description="Enumerate proper depth-D schedules.")
    ap.add_argument("--instance", required=True)
    ap.add_argument("--depth", type=int, default=None, help="default: Delta")
    ap.add_argument("--max", type=int, default=200)
    ap.add_argument("--timeout", type=float, default=None)
    ap.add_argument("--no-verify", action="store_true")
    ap.add_argument("--no-symmetry", action="store_true",
                    help="drop the layer-reversal symmetry-breaking clause")
    args = ap.parse_args(argv)

    code = instances.get(args.instance)
    code.check_structure()
    D = args.depth if args.depth is not None else code.Delta
    res = enumerate_solutions(code, D, max_solutions=args.max, timeout=args.timeout,
                              verify=not args.no_verify, progress=True,
                              symmetry_breaking=not args.no_symmetry)
    p = save(res)
    print(f"{code.name} D={D}: {res['n_solutions']} solutions "
          f"(exhausted={res['exhausted']}) in {res['time']}s -> {os.path.relpath(p, ROOT)}")
    return 0 if res["n_solutions"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())

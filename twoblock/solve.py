"""Run an external SAT solver, produce and verify DRAT certificates, log results."""
from __future__ import annotations

import argparse
import csv
import fcntl
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass

from .code import TwoBlockCode
from .encode import encode
from .simulate import is_proper_by_simulation, is_valid_layering

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(ROOT, "bin")
DATA = os.path.join(ROOT, "data")
CERTS = os.path.join(ROOT, "certs")
LOGS = os.path.join(ROOT, "logs")
SCHED = os.path.join(ROOT, "schedules")
RESULTS_CSV = os.path.join(DATA, "results.csv")

RESULT_FIELDS = ["instance", "N", "k", "l", "Delta", "D", "status", "time",
                 "proof_bytes", "verified", "solver", "solver_version", "tag",
                 "nvars", "nclauses", "verify_time", "proper_by_simulation",
                 "schedule", "proof", "timestamp"]


def solver_path(name: str) -> str | None:
    p = os.path.join(BIN, name)
    if os.path.isfile(p) and os.access(p, os.X_OK):
        return p
    return shutil.which(name)


def solver_version(path: str) -> str:
    """Version string, with the build commit appended when one is available.

    drat-trim has no --version flag, so fall back to the git revision of the
    checkout that setup_solvers.sh built it from.
    """
    ver = ""
    try:
        out = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=20)
        first = ((out.stdout or out.stderr).strip().splitlines() or [""])[0]
        if first and "usage" not in first.lower():
            ver = first
    except Exception:
        pass
    src = os.path.join(ROOT, "build", os.path.basename(path))
    if os.path.isdir(os.path.join(src, ".git")):
        try:
            sha = subprocess.run(["git", "-C", src, "rev-parse", "--short", "HEAD"],
                                 capture_output=True, text=True, timeout=20).stdout.strip()
            if sha:
                ver = f"{ver} (git {sha})" if ver else f"git {sha}"
        except Exception:
            pass
    return ver or "unknown"


@dataclass
class SolveResult:
    status: str                 # SAT | UNSAT | TIMEOUT | UNKNOWN
    time: float
    solver: str
    solver_version: str
    cmd: str
    model: list[int] | None = None
    proof: str | None = None
    proof_bytes: int = 0
    verified: str = ""          # "", "VERIFIED", "NOT_VERIFIED", "SKIPPED"
    verify_time: float = 0.0
    stdout_tail: str = ""


def run_solver(cnf_path: str, proof_path: str | None = None, timeout: float | None = None,
               solver: str = "kissat", binary_proof: bool = False) -> SolveResult:
    """Run kissat (falling back to cadical) on cnf_path, optionally emitting a DRAT proof."""
    path = solver_path(solver)
    if path is None and solver == "kissat":
        solver, path = "cadical", solver_path("cadical")
    if path is None:
        raise RuntimeError(f"solver {solver!r} not found in {BIN} or PATH; run ./setup_solvers.sh")

    cmd = [path]
    if solver == "kissat":
        if timeout:
            cmd.append(f"--time={int(timeout)}")
        if proof_path and not binary_proof:
            cmd.append("--no-binary")
        cmd.append(cnf_path)
        if proof_path:
            cmd += [proof_path, "-f"]
    else:                                   # cadical
        if timeout:
            cmd += ["-t", str(int(timeout))]
        cmd.append(cnf_path)
        if proof_path:
            cmd.append(proof_path)

    hard = (timeout + 120) if timeout else None
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=hard)
        out, rc = proc.stdout, proc.returncode
    except subprocess.TimeoutExpired as ex:
        out, rc = (ex.stdout or b"").decode(errors="replace") if isinstance(ex.stdout, bytes) else (ex.stdout or ""), -1
    elapsed = time.time() - t0

    status = {10: "SAT", 20: "UNSAT"}.get(rc, "TIMEOUT" if rc in (0, -1, 124) else "UNKNOWN")
    model = None
    if status == "SAT":
        vals: list[int] = []
        for line in out.splitlines():
            if line.startswith("v "):
                vals.extend(int(x) for x in line[2:].split())
        model = [v for v in vals if v != 0]
    res = SolveResult(status=status, time=elapsed, solver=solver,
                      solver_version=solver_version(path), cmd=" ".join(cmd), model=model,
                      stdout_tail="\n".join(out.splitlines()[-15:]))
    if proof_path and os.path.exists(proof_path):
        res.proof = proof_path
        res.proof_bytes = os.path.getsize(proof_path)
    return res


VERIFY_TIMEOUT_DEFAULT = 3600.0


def verify_proof(cnf_path: str, proof_path: str,
                 timeout: float = VERIFY_TIMEOUT_DEFAULT) -> tuple[str, float, str]:
    """Run drat-trim; returns (verdict, seconds, tail-of-output).

    Verdicts are kept distinct on purpose: VERIFIED means drat-trim printed
    `s VERIFIED`; NOT_VERIFIED means it ran to completion and did *not*; and
    VERIFY_TIMEOUT means the check ran out of time, which says nothing about whether
    the proof is valid and must never be reported as a failed verification.
    """
    dt = solver_path("drat-trim")
    if dt is None:
        return "SKIPPED", 0.0, "drat-trim not found"
    cmd = [dt, cnf_path, proof_path, "-t", str(int(timeout))]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 600)
        out = proc.stdout
    except subprocess.TimeoutExpired:
        return "VERIFY_TIMEOUT", time.time() - t0, f"drat-trim exceeded {timeout}s wall clock"
    dt_time = time.time() - t0
    lines = out.splitlines()
    if any(l.strip() == "s VERIFIED" for l in lines):
        verdict = "VERIFIED"
    elif any("TIMEOUT" in l.upper() for l in lines):
        verdict = "VERIFY_TIMEOUT"
    else:
        verdict = "NOT_VERIFIED"
    return verdict, dt_time, "\n".join(lines[-12:])


def append_result(row: dict) -> None:
    os.makedirs(DATA, exist_ok=True)
    exists = os.path.exists(RESULTS_CSV)
    with open(RESULTS_CSV, "a", newline="") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        w = csv.DictWriter(f, fieldnames=RESULT_FIELDS, extrasaction="ignore")
        if not exists or os.path.getsize(RESULTS_CSV) == 0:
            w.writeheader()
        w.writerow(row)
        fcntl.flock(f, fcntl.LOCK_UN)


def solve_instance(code: TwoBlockCode, D: int, timeout: float | None = None, proof: bool = False,
                   assumptions=None, tag: str = "", solver: str = "kissat",
                   record: bool = True, keep_cnf: bool = True, binary_proof: bool = False,
                   verify_timeout: float = VERIFY_TIMEOUT_DEFAULT,
                   symmetry_breaking: bool = True) -> dict:
    for d in (DATA, CERTS, LOGS, SCHED):
        os.makedirs(d, exist_ok=True)
    stem = f"{code.name}_d{D}" + (f"_{tag}" if tag else "")
    cnf_path = os.path.join(CERTS, stem + ".cnf")
    proof_path = os.path.join(CERTS, stem + ".drat") if proof else None

    t_enc = time.time()
    enc = encode(code, D, assumptions=assumptions,
                 symmetry_breaking=symmetry_breaking)
    enc.write_dimacs(cnf_path)
    enc.save_varmap(os.path.join(CERTS, stem + ".varmap.json"))
    t_enc = time.time() - t_enc

    res = run_solver(cnf_path, proof_path, timeout=timeout, solver=solver, binary_proof=binary_proof)

    sched_path, proper = "", ""
    if res.status == "SAT":
        lay = enc.decode_model(res.model)
        if not is_valid_layering(code, lay, D):
            raise AssertionError(f"{stem}: SAT model violates vertex distinctness -- encoding is wrong")
        proper = is_proper_by_simulation(code, lay, D)
        if not proper:
            raise AssertionError(
                f"{stem}: SAT model is NOT proper by F2 simulation -- the encoding is wrong")
        sched_path = os.path.join(SCHED, stem + ".json")
        with open(sched_path, "w") as f:
            json.dump({"instance": code.name, "dims": list(code.G.dims),
                       "A": [list(a) for a in code.A], "B": [list(b) for b in code.B],
                       "D": D, "layers": lay,
                       "edges": [[e.kind, e.side, e.lab1, e.check, e.qubit] for e in code.edges],
                       "proper_by_simulation": True}, f)
    if res.status == "UNSAT" and proof and res.proof:
        res.verified, res.verify_time, vtail = verify_proof(cnf_path, res.proof,
                                                            timeout=verify_timeout)
    else:
        vtail = ""
        if res.status == "UNSAT" and not proof:
            res.verified = "SKIPPED"

    row = dict(instance=code.name, N=code.N, k=code.k, l=code.l, Delta=code.Delta, D=D,
               status=res.status, time=round(res.time, 3), proof_bytes=res.proof_bytes,
               verified=res.verified, solver=res.solver, solver_version=res.solver_version,
               tag=tag, nvars=enc.nvars, nclauses=len(enc.clauses),
               verify_time=round(res.verify_time, 3), proper_by_simulation=proper,
               schedule=os.path.relpath(sched_path, ROOT) if sched_path else "",
               proof=os.path.relpath(res.proof, ROOT) if res.proof else "",
               timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"))
    if record:
        append_result(row)
    with open(os.path.join(LOGS, stem + ".log"), "w") as f:
        f.write(f"instance={code.name} D={D} tag={tag}\nencode_time={t_enc:.2f}s "
                f"nvars={enc.nvars} nclauses={len(enc.clauses)}\n"
                f"solver_version={res.solver_version}\ncmd={res.cmd}\n"
                f"status={res.status} time={res.time:.2f}s\n"
                f"proof_bytes={res.proof_bytes} verified={res.verified} "
                f"verify_time={res.verify_time:.2f}s\n--- solver output (tail) ---\n{res.stdout_tail}\n"
                f"--- drat-trim (tail) ---\n{vtail}\n")
    if not keep_cnf and os.path.exists(cnf_path):
        os.remove(cnf_path)
    row["_stdout_tail"] = res.stdout_tail
    return row


def main(argv=None):
    from . import instances
    ap = argparse.ArgumentParser(description="Solve the depth-D schedule existence problem.")
    ap.add_argument("--instance", required=True)
    ap.add_argument("--depth", type=int, required=True)
    ap.add_argument("--timeout", type=float, default=None)
    ap.add_argument("--proof", action="store_true")
    ap.add_argument("--binary-proof", action="store_true")
    ap.add_argument("--verify-timeout", type=float, default=VERIFY_TIMEOUT_DEFAULT,
                    help="wall-clock bound for drat-trim (a timeout is recorded as "
                         "VERIFY_TIMEOUT, never as a failed verification)")
    ap.add_argument("--solver", default="kissat")
    ap.add_argument("--tag", default="")
    ap.add_argument("--assume-count-xl", nargs=2, type=int, metavar=("LAYER", "COUNT"),
                    default=None, help="force #X-edges on the L side in LAYER to equal COUNT")
    ap.add_argument("--assume-invariant", action="store_true",
                    help="pin every edge to a translation-invariant (label-level) schedule "
                         "found by encode.find_invariant_schedule, via unit assumptions")
    args = ap.parse_args(argv)

    code = instances.get(args.instance)
    code.check_structure()
    asm = None
    tag = args.tag
    if args.assume_count_xl:
        i, e = args.assume_count_xl
        asm = [("count_XL", i, e)]
        tag = tag or f"x{i}eq{e}"
    if args.assume_invariant:
        from .encode import find_invariant_schedule, schedule_assumptions
        found = find_invariant_schedule(code, args.depth)
        if found is None:
            print(json.dumps({"instance": code.name, "D": args.depth, "status": "NO_INVARIANT",
                              "note": "no translation-invariant proper schedule at this depth"},
                             indent=1))
            return 2
        labels, lay = found
        print("invariant labels: "
              + json.dumps({a + b: list(v) for (a, b), v in labels.items()}), flush=True)
        asm = (asm or []) + schedule_assumptions(code, lay)
        tag = tag or "inv"
    row = solve_instance(code, args.depth, timeout=args.timeout, proof=args.proof,
                         assumptions=asm, tag=tag, solver=args.solver,
                         binary_proof=args.binary_proof, verify_timeout=args.verify_timeout)
    print(json.dumps({k: v for k, v in row.items() if not k.startswith("_")}, indent=1))
    return 0 if row["status"] in ("SAT", "UNSAT") else 1


if __name__ == "__main__":
    sys.exit(main())

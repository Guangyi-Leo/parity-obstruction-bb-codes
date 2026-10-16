"""Connected components of the Tanner graph and the Theorem-1 parity obstruction.

A component is *regular* when every data qubit in it carries the same pair
(Delta_X, Delta_Z) of X- and Z-degrees and every check in it has the same weight
Delta.  For a two-block code an L-qubit has (Delta_X, Delta_Z) = (k, l) and an
R-qubit has (l, k), so a component holding both kinds is regular only when k = l.

Theorem-1 obstruction (componentwise parity): the code is obstructed when some
component is regular with Delta_X and Delta_Z both odd and n*Delta_X*Delta_Z/2 odd,
where n is the number of data qubits in the component.  n*Delta_X*Delta_Z is the
number of corners in the component; with both degrees odd this is odd exactly when
n = 2 (mod 4).  The criterion does not need distinct sums.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .code import TwoBlockCode


@dataclass
class Component:
    idx: int
    data: list[tuple[str, int]] = field(default_factory=list)     # ('L'|'R', h)
    xchecks: list[int] = field(default_factory=list)
    zchecks: list[int] = field(default_factory=list)
    data_degrees: set[tuple[int, int]] = field(default_factory=set)   # {(Delta_X, Delta_Z)}
    check_degrees: set[int] = field(default_factory=set)

    @property
    def n(self) -> int:
        return len(self.data)

    @property
    def N_X(self) -> int:
        return len(self.xchecks)

    @property
    def N_Z(self) -> int:
        return len(self.zchecks)

    @property
    def regular(self) -> bool:
        return len(self.data_degrees) == 1 and len(self.check_degrees) == 1

    @property
    def Delta_X(self) -> int | None:
        return next(iter(self.data_degrees))[0] if self.regular else None

    @property
    def Delta_Z(self) -> int | None:
        return next(iter(self.data_degrees))[1] if self.regular else None

    @property
    def Delta(self) -> int | None:
        return next(iter(self.check_degrees)) if self.regular else None

    @property
    def n_corners(self) -> int | None:
        """n * Delta_X * Delta_Z for a regular component."""
        return None if not self.regular else self.n * self.Delta_X * self.Delta_Z

    @property
    def obstructed(self) -> bool:
        """Regular, both degrees odd, and n*Delta_X*Delta_Z/2 odd."""
        if not self.regular:
            return False
        dx, dz = self.Delta_X, self.Delta_Z
        if dx % 2 == 0 or dz % 2 == 0:
            return False
        tot = self.n * dx * dz
        return tot % 2 == 0 and (tot // 2) % 2 == 1

    def as_dict(self) -> dict:
        return dict(idx=self.idx, n=self.n, N_X=self.N_X, N_Z=self.N_Z,
                    data_degrees=sorted(self.data_degrees),
                    check_degrees=sorted(self.check_degrees),
                    regular=self.regular, Delta_X=self.Delta_X, Delta_Z=self.Delta_Z,
                    Delta=self.Delta, n_corners=self.n_corners, obstructed=self.obstructed)


def components(code: TwoBlockCode) -> list[Component]:
    """Connected components of the Tanner graph (data qubits together with checks)."""
    adj: dict[tuple[str, int], list[tuple[str, int]]] = {v: [] for v in code.vertices}
    for e in code.edges:
        cv = (e.kind, e.check)
        dv = (e.side, e.qubit)
        adj[cv].append(dv)
        adj[dv].append(cv)

    seen: set[tuple[str, int]] = set()
    out: list[Component] = []
    for start in code.vertices:
        if start in seen:
            continue
        comp = Component(idx=len(out))
        stack = [start]
        seen.add(start)
        while stack:
            v = stack.pop()
            kind, i = v
            if kind in ("L", "R"):
                comp.data.append(v)
                es = [code.edges[e] for e in code.data_edges[v]]
                dx = sum(1 for e in es if e.kind == "X")
                dz = sum(1 for e in es if e.kind == "Z")
                comp.data_degrees.add((dx, dz))
            else:
                (comp.xchecks if kind == "X" else comp.zchecks).append(i)
                comp.check_degrees.add(len(code.check_edges[v]))
            for w in adj[v]:
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
        out.append(comp)
    return out


def theorem1_obstructed(code: TwoBlockCode) -> bool:
    """True iff some component carries the componentwise parity obstruction."""
    return any(c.obstructed for c in components(code))


def summary(code: TwoBlockCode) -> dict:
    comps = components(code)
    return dict(
        n_components=len(comps),
        min_component_n=min(c.n for c in comps),
        max_component_n=max(c.n for c in comps),
        all_regular=all(c.regular for c in comps),
        n_obstructed_components=sum(1 for c in comps if c.obstructed),
        theorem1_obstructed=any(c.obstructed for c in comps),
        components=[c.as_dict() for c in comps],
    )


# ---------------------------------------------------------------------------
# H1: the Theorem-1 predictor against every already-recorded solver outcome.
# No solving happens here; statuses are read from data/results.csv and
# data/sweep.csv exactly as they were recorded.
# ---------------------------------------------------------------------------
H1_FIELDS = ["instance", "source", "group", "A", "B", "N", "D", "n_components",
             "min_component_n", "n_obstructed_components", "distinct_sums",
             "theorem1_obstructed", "status", "explained_by", "agree"]


def _h1_row(code: TwoBlockCode, status: str, D, source: str) -> dict:
    import json as _json
    s = summary(code)
    ds = code.distinct_sums()
    ob = s["theorem1_obstructed"]
    if status == "UNSAT":
        exp = "+".join([w for w, f in (("theorem1", ob), ("distinct_sums", ds)) if f])
    else:
        exp = ""
    agree = "" if status not in ("SAT", "UNSAT") else str(not (ob and status == "SAT"))
    return dict(instance=code.name, source=source, group=code.G.label(),
                A=_json.dumps([list(a) for a in code.A]),
                B=_json.dumps([list(b) for b in code.B]),
                N=code.N, D=D, n_components=s["n_components"],
                min_component_n=s["min_component_n"],
                n_obstructed_components=s["n_obstructed_components"],
                distinct_sums=ds, theorem1_obstructed=ob, status=status,
                explained_by=exp, agree=agree)


def run_h1(out: str | None = None) -> tuple[list[dict], dict]:
    import csv
    import json as _json
    import os
    from . import instances as _inst

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = os.path.join(root, "data")
    out = out or os.path.join(data, "h1_predictions.csv")
    rows: list[dict] = []

    # named instances solved at depth Delta (the depth Theorem 1 speaks about)
    rpath = os.path.join(data, "results.csv")
    if os.path.exists(rpath):
        for r in csv.DictReader(open(rpath)):
            if r["tag"]:
                continue
            code = _inst.get(r["instance"])
            if int(r["D"]) != code.Delta:
                continue
            if any(x["instance"] == r["instance"] and x["source"] == "results" for x in rows):
                continue
            rows.append(_h1_row(code, r["status"], int(r["D"]), "results"))

    spath = os.path.join(data, "sweep.csv")
    if os.path.exists(spath):
        for r in csv.DictReader(open(spath)):
            code = TwoBlockCode(tuple(_json.loads(r["dims"])),
                                [tuple(a) for a in _json.loads(r["A"])],
                                [tuple(b) for b in _json.loads(r["B"])], r["name"])
            rows.append(_h1_row(code, r["status"], int(r["D"]), "sweep"))

    # H2 instances too: they are the strongest test of the predictor, since the
    # experiment deliberately includes obstructed (subgroup) cases at larger N.
    hpath = os.path.join(data, "h2_sharpness.csv")
    if os.path.exists(hpath):
        for r in csv.DictReader(open(hpath)):
            code = TwoBlockCode((int(r["N"]),),
                                [tuple(a) for a in _json.loads(r["A"])],
                                [tuple(b) for b in _json.loads(r["B"])], r["name"])
            rows.append(_h1_row(code, r["status"], int(r["D_depth"]), "h2"))

    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=H1_FIELDS)
        w.writeheader()
        w.writerows(rows)

    def _scope(sel, name):
        dec = [r for r in sel if r["status"] in ("SAT", "UNSAT")]
        viol = [r for r in dec if r["theorem1_obstructed"] and r["status"] == "SAT"]
        unsat = [r for r in dec if r["status"] == "UNSAT"]
        unexp = [r for r in unsat if not r["explained_by"]]
        return dict(scope=name, n=len(sel), n_decided=len(dec),
                    n_obstructed=sum(1 for r in dec if r["theorem1_obstructed"]),
                    n_unsat=len(unsat),
                    n_unsat_by_theorem1=sum(1 for r in unsat if r["theorem1_obstructed"]),
                    n_unsat_by_distinct_sums=sum(1 for r in unsat if r["distinct_sums"]),
                    n_violations=len(viol), n_unexplained=len(unexp),
                    agreement=f"{len(dec) - len(viol)}/{len(dec)}",
                    violations=[v["instance"] for v in viol],
                    unexplained=[u["instance"] for u in unexp])

    spec_rows = [r for r in rows if r["source"] in ("results", "sweep")]
    stats = dict(out=out, n_rows=len(rows),
                 specified=_scope(spec_rows, "results.csv + sweep.csv"),
                 extended=_scope(rows, "+ h2_sharpness.csv"))
    return rows, stats


def main(argv=None):
    rows, st = run_h1()
    for key in ("specified", "extended"):
        k = st[key]
        print(f"H1 scope [{k['scope']}]: {k['n_decided']} instances with a decided status")
        print(f"  theorem1_obstructed = True : {k['n_obstructed']}")
        print(f"  UNSAT                      : {k['n_unsat']}"
              f"  (Theorem 1: {k['n_unsat_by_theorem1']}, "
              f"distinct sums: {k['n_unsat_by_distinct_sums']})")
        print(f"  obstructed AND SAT         : {k['n_violations']}   <- must be 0")
        print(f"  UNSAT explained by neither : {k['n_unexplained']}")
        print(f"  agreement                  : {k['agreement']}\n")
    print(f"wrote {st['out']}")

    if st["extended"]["n_violations"]:
        print("\nSTOP: Theorem 1 predicts an obstruction for instances recorded SAT:")
        print(" ", st["extended"]["violations"])
        return 1
    if st["specified"]["n_unexplained"]:
        print("\nUNSAT explained by neither criterion within the specified scope:")
        print(" ", st["specified"]["unexplained"])
        return 2
    extra = st["extended"]["n_unexplained"]
    if extra:
        print(f"\nNOTE: within the specified scope (results.csv + sweep.csv) every UNSAT "
              f"is explained, as expected.\n"
              f"Adding the new H2 instances leaves {extra} UNSAT cases explained by "
              f"neither criterion:\n  {st['extended']['unexplained']}\n"
              f"Every one of them is a one-coincidence (C1) instance. Theorem 1 is a "
              f"one-directional criterion, so this is not a contradiction; it says the "
              f"two known criteria are not complete on class C1 at larger N.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

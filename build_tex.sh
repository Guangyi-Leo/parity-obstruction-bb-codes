#!/bin/bash
# Build main.tex.  TEXINPUTS must name ./figures explicitly and must NOT use
# the recursive "//" form: release/ carries a frozen copy of every figure, and
# a recursive search finds those first, so the manuscript silently builds
# against the release instead of the figures just regenerated.
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.TinyTeX/bin/x86_64-linux:/usr/local/texlive/2024/bin/x86_64-linux:$PATH"
export TEXINPUTS=".:./figures:"
mkdir -p build_tex
latexmk -pdf -interaction=nonstopmode -output-directory=build_tex main.tex \
        > build_tex/latexmk.log 2>&1 || true

bad=$(grep -c '^!' build_tex/main.log || true)
und=$(grep -ci 'undefined' build_tex/main.log || true)
echo "  errors=$bad  undefined=$und  $(grep -o '([0-9]* pages' build_tex/main.log | tail -1 | tr -d '(')"

# every figure must come from figures/, never from release/figures/
if grep -E '^INPUT \./release/' build_tex/main.fls | grep -qi fig; then
    echo "  FAIL: a figure was read from release/figures/" >&2
    grep -E '^INPUT \./release/' build_tex/main.fls | grep -i fig >&2
    exit 1
fi
[ "$bad" = 0 ] && [ "$und" = 0 ] || exit 1

python3 - <<'PY'
import json, re, io
aux = io.open("build_tex/main.aux").read()
labels = {m.group(1): m.group(2)
          for m in re.finditer(r"\\newlabel\{([^}]*)\}\{\{([^}]*)\}", aux)}
io.open("build_tex/labels.json", "w").write(json.dumps(labels, indent=1, sort_keys=True))
print(f"  {len(labels)} labels -> build_tex/labels.json")
PY

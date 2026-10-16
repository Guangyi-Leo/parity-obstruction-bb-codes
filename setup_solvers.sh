#!/usr/bin/env bash
# Build kissat, cadical and drat-trim into ./bin  (idempotent)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="$ROOT/bin"; BUILD="$ROOT/build"
mkdir -p "$BIN" "$BUILD"

clone() { # url dir
  if [ -d "$BUILD/$2/.git" ]; then git -C "$BUILD/$2" fetch --depth 1 origin || true
  else git clone --depth 1 "$1" "$BUILD/$2"; fi
}

if [ ! -x "$BIN/kissat" ]; then
  clone https://github.com/arminbiere/kissat.git kissat
  ( cd "$BUILD/kissat" && ./configure && make -j"$(nproc)" )
  cp "$BUILD/kissat/build/kissat" "$BIN/kissat"
fi

if [ ! -x "$BIN/cadical" ]; then
  clone https://github.com/arminbiere/cadical.git cadical
  ( cd "$BUILD/cadical" && ./configure && make -j"$(nproc)" )
  cp "$BUILD/cadical/build/cadical" "$BIN/cadical"
fi

if [ ! -x "$BIN/drat-trim" ]; then
  clone https://github.com/marijnheule/drat-trim.git drat-trim
  ( cd "$BUILD/drat-trim" && make )
  cp "$BUILD/drat-trim/drat-trim" "$BIN/drat-trim"
fi

echo "--- installed ---"
"$BIN/kissat" --version || true
"$BIN/cadical" --version || true
ls -l "$BIN"

#!/usr/bin/env bash
# Re-check the DRAT refutations.
#
# The proofs themselves are not in this repository: they total ~10.4 GB and the
# largest is 2.6 GB, over GitHub's 100 MB per-file limit.  They are in the
# Zenodo archive.  This script works either way:
#
#   * if certs/<name>.drat.xz is present (unpack the Zenodo archive over
#     certs/ and certs_nosym/), the proof is decompressed one at a time,
#     checked with drat-trim, and deleted;
#
#   * if it is not, the refutation is re-run from the shipped CNF with kissat
#     and DRAT logging, and the *fresh* proof is checked instead.  The fresh
#     proof's SHA-256 is compared with PROOFS.sha256 and a difference is
#     reported, not treated as a failure: a proof is a certificate, and two
#     different proofs of the same CNF are both valid.  Only "drat-trim did
#     not say VERIFIED" is a failure.
#
#   bash verify_proofs.sh            # every proof
#   bash verify_proofs.sh bb72       # just the ones whose name matches
#
# Needs drat-trim (and kissat, for the re-run path) on PATH; setup_solvers.sh
# builds both at the versions environment.yml pins.
set -uo pipefail
cd "$(dirname "$0")"
FILTER="${1:-}"
SCRATCH="${SCRATCH:-$(mktemp -d)}"
trap 'rm -rf "$SCRATCH"' EXIT
command -v drat-trim >/dev/null || { echo "drat-trim not on PATH"; exit 1; }

ok=0; bad=0; resolved=0; differ=0
for cz in certs/*.cnf.xz certs_nosym/*.cnf.xz; do
  [ -e "$cz" ] || continue
  base="$(basename "$cz" .cnf.xz)"
  dir="$(dirname "$cz")"
  [ -n "$FILTER" ] && [[ "$base" != *"$FILTER"* ]] && continue
  # only the instances a proof was recorded for
  grep -q "  ${base}.drat  " "$dir/PROOFS.sha256" 2>/dev/null || continue

  xz -dc "$cz" > "$SCRATCH/$base.cnf"
  if [ -f "$dir/$base.drat.xz" ]; then
    xz -dc "$dir/$base.drat.xz" > "$SCRATCH/$base.drat"
    how="archived"
  elif [ -f "$dir/$base.drat" ]; then
    cp "$dir/$base.drat" "$SCRATCH/$base.drat"
    how="archived"
  else
    command -v kissat >/dev/null || {
      echo "  SKIPPED    $base  (no proof present and kissat not on PATH)"
      rm -f "$SCRATCH/$base.cnf"; continue; }
    kissat --no-binary "$SCRATCH/$base.cnf" "$SCRATCH/$base.drat" -q >/dev/null 2>&1
    how="re-solved"; resolved=$((resolved+1))
  fi

  # Capture the output rather than piping into grep: `grep -q` exits on the
  # first match, drat-trim then dies of SIGPIPE (141), and `set -o pipefail`
  # would report that as a failed verification for every proof.
  # drat-trim writes progress with carriage returns, so "s VERIFIED" is not
  # at the start of a line until the CRs are stripped.
  out="$(drat-trim "$SCRATCH/$base.cnf" "$SCRATCH/$base.drat" 2>&1 | tr -d '\r')" || true
  secs="$(printf '%s\n' "$out" | sed -n 's/^c verification time: \(.*\) seconds/\1/p')"
  if printf '%s\n' "$out" | grep -q "^s VERIFIED"; then
    note=""
    if [ "$how" = "re-solved" ]; then
      want="$(grep "  ${base}.drat  " "$dir/PROOFS.sha256" | cut -d' ' -f1)"
      got="$(sha256sum "$SCRATCH/$base.drat" | cut -d' ' -f1)"
      if [ "$want" != "$got" ]; then
        note="  (a different proof from the recorded one; both verify)"
        differ=$((differ+1))
      else
        note="  (byte-identical to the recorded proof)"
      fi
    fi
    echo "  VERIFIED   ${base}  [${how}, ${secs:-?} s]${note}"; ok=$((ok+1))
  else
    echo "  FAILED     $base  [${how}]"; bad=$((bad+1))
    printf '%s\n' "$out" | tail -3 | sed 's/^/             /'
  fi
  rm -f "$SCRATCH/$base.cnf" "$SCRATCH/$base.drat"
done
echo
echo "verified $ok, failed $bad"
[ "$resolved" -gt 0 ] && echo "  $resolved re-solved from the CNF ($differ gave a different, equally valid proof)"
[ "$bad" -eq 0 ]

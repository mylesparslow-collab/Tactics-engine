#!/usr/bin/env bash
# Run the sim harness across N parallel shards and write JSONL to $1.
# Usage: tools/sim/run.sh out.jsonl [shards]   (other SIM_* env vars pass through, see tests/sim.test.ts)
set -euo pipefail
out=${1:?output file}; n=${2:-$(nproc)}
: > "$out"
for i in $(seq 0 $((n-1))); do
  SIM=1 SIM_SHARD="$i/$n" SIM_OUT="$out.$i" npx vitest run tests/sim.test.ts >/dev/null 2>&1 &
done
wait
cat "$out".* > "$out"; rm -f "$out".*
wc -l < "$out"

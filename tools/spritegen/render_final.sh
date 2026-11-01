#!/bin/bash
# usage: render_final.sh <faction-prefix> [jobs]  -> out_final/<faction>/ with eased in-betweens
cd "$(dirname "$0")"
f=$1; j=${2:-2}
mkdir -p out_final/$f
for u in units/${f}_*.py; do id=$(basename $u .py); python3 sheet.py $id out_final/$f --tween --jobs $j >/dev/null 2>out_final/$f/$id.err && rm -f out_final/$f/$id.err && echo "ok $id" || echo "FAIL $id"; done
echo DONE $f

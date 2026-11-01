#!/bin/bash
# usage: render_final.sh <faction-prefix> [jobs] [style]  -> out_<style>/<faction>/ with eased in-betweens
cd "$(dirname "$0")"
f=$1; j=${2:-2}; st=${3:-cel}
o=out_$st/$f
mkdir -p $o
for u in units/${f}_*.py; do id=$(basename $u .py); [ -f $o/$id.json ] && [ -f $o/$id.png ] && { echo "skip $id"; continue; }; python3 sheet.py $id $o --tween --style $st --jobs $j >/dev/null 2>$o/$id.err && rm -f $o/$id.err && echo "ok $id" || echo "FAIL $id"; done
echo DONE $f

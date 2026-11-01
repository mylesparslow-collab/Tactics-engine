#!/usr/bin/env python3
"""Per-card report from a SIM_CARDS=1 run: how often each card was played, what it did, and how its side fared.
Usage: cards.py results.jsonl [faction-prefix]"""
import json, sys
from collections import defaultdict
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
flt = sys.argv[2] if len(sys.argv) > 2 else ''
units = json.load(open('content/units.json')); spells = json.load(open('content/spells.json')); eq = json.load(open('content/equipment.json'))
cost = lambda k: (units.get(k) or spells.get(k) or eq.get(k) or {}).get('cost', 0)
agg = defaultdict(lambda: dict(games=0, n=0, dmg=0, kills=0, taken=0, died=0, wins=0))
for r in rows:
    if 'cards' not in r: continue
    win = {'p0': 0, 'p1': 1}.get(r['result'], -1)
    for k, v in r['cards'].items():
        team, cid = k.split(':', 1)
        a = agg[cid]; a['games'] += 1; a['wins'] += int(team) == win
        for f in ('n', 'dmg', 'kills', 'taken', 'died'): a[f] += v[f]
print(f"{'card':44} cost played/g dmg/play kills/play died% dmg/Tide win%")
for cid, a in sorted(agg.items(), key=lambda kv: kv[0]):
    if flt and not cid.startswith(flt): continue
    n = max(a['n'], 1); c = cost(cid) or 1
    print(f"{cid:44} {c:4} {a['n']/a['games']:8.2f} {a['dmg']/n:8.1f} {a['kills']/n:10.2f} {100*a['died']/n:5.0f} {a['dmg']/n/c:8.2f} {100*a['wins']/a['games']:4.0f}")

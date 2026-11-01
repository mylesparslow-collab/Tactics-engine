#!/usr/bin/env python3
"""Summarise sim JSONL: faction win rates vs the field, seat advantage, matchup grid, mission results.
Usage: report.py results.jsonl [--md]"""
import json, sys, math
from collections import defaultdict

rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
md = '--md' in sys.argv

def ci(w, n):  # 95% Wilson half-width, in points
    if not n: return 0
    p = w / n; z = 1.96
    return 100 * z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)

sk = [r for r in rows if r['mode'] == 'skirmish']
if sk:
    fac = defaultdict(lambda: [0, 0, 0, []])  # wins, games, timeouts, rounds
    grid = defaultdict(lambda: [0, 0])
    p0w = sum(r['result'] == 'p0' for r in sk); dec = sum(r['result'] != 'timeout' for r in sk)
    for r in sk:
        for side, f, o in (('p0', r['p0'], r['p1']), ('p1', r['p1'], r['p0'])):
            s = fac[f]; s[1] += 1; s[3].append(r['rounds'])
            if r['result'] == side: s[0] += 1; grid[(f, o)][0] += 1
            if r['result'] == 'timeout': s[2] += 1
            grid[(f, o)][1] += 1
    print(f"Skirmish: {len(sk)} games, first player wins {100*p0w/max(dec,1):.0f}% of decided games, "
          f"timeouts {len(sk)-dec}, median rounds {sorted(r['rounds'] for r in sk)[len(sk)//2]}\n")
    print('| Faction | Win % vs field | ±95% | Games | Timeouts | Median rounds |' if md else 'faction,win%,ci,games,timeouts,median_rounds')
    if md: print('|---|---|---|---|---|---|')
    for f, (w, n, t, rs) in sorted(fac.items(), key=lambda kv: -kv[1][0] / kv[1][1]):
        med = sorted(rs)[len(rs) // 2]
        print(f"| {f} | {100*w/n:.0f} | {ci(w,n):.0f} | {n} | {t} | {med} |" if md else f"{f},{100*w/n:.1f},{ci(w,n):.1f},{n},{t},{med}")
    fs = sorted(fac)
    print('\nMatchup win % (row vs column):')
    short = [f.split('_')[0][:6] for f in fs]
    print('| | ' + ' | '.join(short) + ' |' if md else ',' + ','.join(short))
    if md: print('|---' * (len(fs) + 1) + '|')
    for a in fs:
        cells = [('-' if a == b else f"{100*grid[(a,b)][0]/max(grid[(a,b)][1],1):.0f}") for b in fs]
        print(f"| {a.split('_')[0][:6]} | " + ' | '.join(cells) + ' |' if md else a + ',' + ','.join(cells))
    maps = defaultdict(lambda: [0, 0])
    for r in sk:
        maps[r['map']][1] += 1; maps[r['map']][0] += r['result'] == 'p0'
    print('\nFirst-player win % by map: ' + ', '.join(f"{m} {100*w/n:.0f}" for m, (w, n) in sorted(maps.items())))

ms = [r for r in rows if r['mode'] == 'mission']
if ms:
    agg = defaultdict(lambda: [0, 0, 0, [], []])
    for r in ms:
        a = agg[(r['index'], r['mission'])]; a[1] += 1; a[3].append(r['rounds'])
        if r['result'] == 'p0': a[0] += 1; a[4].append(r['hp0'])
        if r['result'] == 'timeout': a[2] += 1
    print('\n| # | Mission | Player win % | Games | Timeouts | Median rounds | Median HP left on wins |' if md else '\nindex,mission,player_win%,games,timeouts,median_rounds,median_hp_on_win')
    if md: print('|---|---|---|---|---|---|---|')
    for (i, m), (w, n, t, rs, hp) in sorted(agg.items()):
        mh = sorted(hp)[len(hp) // 2] if hp else '-'
        print(f"| {i+1} | {m} | {100*w/n:.0f} | {n} | {t} | {sorted(rs)[len(rs)//2]} | {mh} |" if md else f"{i+1},{m},{100*w/n:.0f},{n},{t},{sorted(rs)[len(rs)//2]},{mh}")

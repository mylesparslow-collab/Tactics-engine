#!/usr/bin/env python3
"""Static checks for campaign missions that the engine's validateContent does not do.

Usage: python3 tools/campaigns/check_missions.py [campaignId ...]   (no args: every campaign)

Checks, per mission: placed units and spawns sit on passable in-bounds tiles, no two placed units share a tile,
nothing is placed on a Beacon, every tag used by an objective is carried by a placed or spawned unit, and
unitDefeated event triggers name a real tag. Per campaign: unlocks and roster belong to the campaign's faction
(or are spells/equipment of it), and no relic is awarded by two campaigns.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / 'content'
terrain = json.loads((ROOT / 'terrain.json').read_text())
units = json.loads((ROOT / 'units.json').read_text())
spells = json.loads((ROOT / 'spells.json').read_text())
equipment = json.loads((ROOT / 'equipment.json').read_text())
campaigns = json.loads((ROOT / 'campaigns.json').read_text())


def faction_of(rid):
    d = units.get(rid) or spells.get(rid) or equipment.get(rid)
    return d and d.get('faction')


def impassable(tid):
    return terrain.get(tid, {}).get('impassable', False)


def check_mission(mid, errs):
    p = ROOT / 'missions' / f'{mid}.json'
    if not p.exists():
        errs.append(f'{mid}: file missing'); return
    m = json.loads(p.read_text())
    mp = json.loads((ROOT / 'maps' / f"{m['map']}.json").read_text())
    H, W = len(mp['tiles']), len(mp['tiles'][0])
    keys = {(k['x'], k['y']) for k in mp.get('keystones', [])}

    def tile_ok(x, y, what):
        if not (0 <= x < W and 0 <= y < H):
            errs.append(f'{mid}: {what} at {x},{y} out of bounds ({W}x{H})'); return
        tid = mp['legend'].get(mp['tiles'][y][x])
        if impassable(tid):
            errs.append(f'{mid}: {what} at {x},{y} on impassable {tid}')
        if (x, y) in keys:
            errs.append(f'{mid}: {what} at {x},{y} on a Beacon tile')

    tags, seen = set(), {}
    for ti, t in enumerate(m['teams']):
        for u in t.get('units', []):
            tile_ok(u['x'], u['y'], f"team {ti} {u['unit']}")
            if (u['x'], u['y']) in seen:
                errs.append(f"{mid}: {u['unit']} and {seen[(u['x'], u['y'])]} share tile {u['x']},{u['y']}")
            seen[(u['x'], u['y'])] = u['unit']
            if u.get('tag'): tags.add(u['tag'])
    for ev in m.get('events', []):
        for a in ev['do']:
            if a['type'] == 'spawn':
                tile_ok(a['x'], a['y'], f"spawn {a['unit']}")
                if a.get('tag'): tags.add(a['tag'])
            if a['type'] == 'terrain':
                if not (0 <= a['x'] < W and 0 <= a['y'] < H): errs.append(f'{mid}: terrain event out of bounds')
    for kind in ('victory', 'defeat'):
        for c in (m.get('objectives') or {}).get(kind, []):
            if 'tag' in c and c['tag'] not in tags:
                errs.append(f"{mid}: {kind} condition uses tag '{c['tag']}' that no unit carries")
            for x, y in c.get('tiles', []):
                if not (0 <= x < W and 0 <= y < H) or impassable(mp['legend'].get(mp['tiles'][y][x])):
                    errs.append(f'{mid}: reach_tile target {x},{y} is out of bounds or impassable')
    for ev in m.get('events', []):
        t = ev['when'].get('unitDefeated')
        if t and t not in tags:
            errs.append(f"{mid}: event trigger unitDefeated '{t}' names no unit tag")
    for b in (m.get('salvage') or {}).get('bonus', []):
        t = b['condition'].get('tag')
        if t and t not in tags:
            errs.append(f"{mid}: salvage bonus uses tag '{t}' that no unit carries")


def main():
    ids = sys.argv[1:] or list(campaigns)
    errs, awarded = [], {}
    for cid, camp in campaigns.items():
        for rid in camp['startingRoster'] + [r for s in camp['missions'] for r in s.get('unlocks', [])]:
            awarded.setdefault(rid, set()).add(cid)
    for cid in ids:
        camp = campaigns.get(cid)
        if not camp:
            errs.append(f'unknown campaign {cid}'); continue
        fac = camp.get('faction') or faction_of(camp['startingRoster'][0])
        for s in camp['missions']:
            for rid in s.get('unlocks', []):
                if faction_of(rid) != fac: errs.append(f'{cid}: unlock {rid} is not a {fac} relic')
                if len(awarded.get(rid, ())) > 1: errs.append(f'{cid}: {rid} is awarded by several campaigns {sorted(awarded[rid])}')
            check_mission(s['mission'], errs)
    print('\n'.join(errs) if errs else f'OK: {len(ids)} campaign(s) clean')
    sys.exit(1 if errs else 0)


if __name__ == '__main__':
    main()

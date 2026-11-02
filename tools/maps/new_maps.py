#!/usr/bin/env python3
"""Builds the 2026-11 map pack (content/maps/<id>.json).

Each map is written as its top half (rows 0-10, team 1's side); the bottom half is the same half rotated 180
degrees, so both sides get exactly the same ground. Deploy zones are picked automatically around each Beacon.
Run: python3 tools/maps/new_maps.py   (prints a check per map, fails on unreachable or malformed maps)
"""
import json, os, sys
from collections import deque

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'content')
TERRAIN = json.load(open(os.path.join(ROOT, 'terrain.json')))
LEGEND = {
    '.': 'salt_flat', ',': 'silt', 'c': 'dead_coral', 'w': 'wreck', 'p': 'brine_pool', 'T': 'trench',
    '=': 'bone_road', 'X': 'salt_wall', 'o': 'lamp_oil', 'k': 'kelp_husk', 'L': 'lighthouse_stone',
    'B': 'brine_lake', 'r': 'living_reef', 'a': 'calcite',
    's': 'shallows', 'v': 'vent', 'g': 'tangleweed', 'm': 'scrap_field', 'G': 'beam_glass',
    'O': 'razor_oysters', 'M': 'glowmoss', 'u': 'sinkmud',
}
HAZARD = {'vent', 'razor_oysters', 'lamp_oil', 'brine_pool'}
W = 22

def uniform(rows):
    """Height rows given as one digit per row: '2' -> '2222...'."""
    return [r * W if len(r) == 1 else r for r in rows]

MAPS = [
 dict(id='boiling_floor', name='The Boiling Floor',
  description='A field of cracked vents over the old trench mouth. The steam scalds anyone who lingers, unless they were born to the pressure below.',
  tiles=[
   ',,,,,,,,,,,,,,,,,,,,,,',
   ',,uu,,,,,LLL,,,,,,uu,,',
   ',uuu,,,,,,=,,,,,,,,uu,',
   ',,u,,,k,,,=,,,,k,,,,,,',
   ',,,,,,,,,,=,,,,,,,,,,,',
   'TT,,,uu,,,,,,,uu,,,,TT',
   'TTT,,uuv,,,,,,vuu,,TTT',
   ',TT,,,,,,,v,,,,,,,,TT,',
   ',,,,,u,,,,uu,v,,u,,,,,',
   ',v,,,,,,TT,,,,TT,,,,v,',
   ',,,,,,,TTTv,,,TTT,,,,,'],
  heights=uniform(['2','2','2','2','1','1','1','1','0','0','0']),
  wells=[(10, 7), (1, 9)]),
 dict(id='glasswork_reach', name='The Glasswork Reach',
  description='Where the Shoal lamp swept for three hundred years the sand ran to glass. Long, bright lanes to shoot down, and nowhere to hide on them.',
  tiles=[
   '......................',
   '....G....LLL....G.....',
   '...GG.....=.....GG....',
   '..GG......=......GG...',
   '.GG...m...=...m...GG..',
   'GG........=........GG.',
   '......GGGGGGGGGG......',
   '..m...G........G...m..',
   '......G..LLLL..G......',
   '..XX..G..LMML..G..XX..',
   '..XX..G..LLLL..G......'],
  heights=uniform(['2','2','2','1','1','1','1','1',
                   '1111111112222111111111', '1111111112332111111111', '1111111112332111111111']),
  wells=[(10, 9), (4, 7)]),
 dict(id='oyster_banks', name='The Oyster Banks',
  description='Tide-left shallows thick with razor shell and waking reef. Wet going, good for anything that dries out, and the coral is listening.',
  tiles=[
   ',,,,,,,,,,,,,,,,,,,,,,',
   ',,rr,,,,,LLL,,,,,rr,,,',
   ',rrr,,,,,,,,,,,,,,rr,,',
   ',,,,,sss,,,,,,sss,,,,,',
   ',,ss,,sOOs,,,,sOOs,,,,',
   ',sss,,,sss,,,,,ss,,gg,',
   'ss,,,,,,,,rr,,,,,,ggg,',
   's,,gg,,,,rrrr,,,,,,,,s',
   ',,ggg,,ss,,rr,,ss,,,ss',
   ',,,,,,sOs,,,,,sOs,,sss',
   'ss,,,,sss,,aa,,sss,,ss'],
  heights=uniform(['2','2','2','1','1','1','1','1','1','1','1']),
  wells=[(10, 7), (7, 9)]),
 dict(id='breakers_yard', name="Breakers' Yard",
  description='Where the Compact strips the drowned fleets. Hulks for walls, scrap for cover, and oil in every low place.',
  tiles=[
   '......................',
   '..mm.....LLL.....mm...',
   '.mmm......=......mmm..',
   '....wwww..=..wwww.....',
   '....w..m..=..m..w.....',
   '.mm.w..........w..mm..',
   '.m..wwww..o..wwww..m..',
   '..........oo..........',
   '=====mm........mm=====',
   '...www..mmmmmm..www...',
   '...w.o..m....m..w.o...'],
  heights=uniform(['2','2','1','1','1','1','1','1','1','1','1']),
  wells=[(10, 10), (1, 6)]),
 dict(id='tide_steps', name='The Tide Steps',
  description='Terraces cut by the falling sea, stepping down into a basin the tide keeps trying to refill. The Returning Tide walk its water like a road.',
  tiles=[
   '......................',
   '.........LLL..........',
   '..c.......=.......c...',
   '..........=...........',
   'XX..sss...=...sss...XX',
   '.....s....=....s......',
   'ss....................',
   'sss..k....ss....k...ss',
   'ssss....sssss.....ssss',
   'ssssp..sssMsss...pssss',
   'sssss.sssssssss.sssss.'],
  heights=uniform(['3','3','3','3','2','2','1','1','0','0','0']),
  wells=[(10, 9), (4, 9)]),
 dict(id='saltpan_bastions', name='Saltpan Bastions',
  description='A Concord salt works walled into a fortress line. Gates, bastions and killing lanes for anyone who can hold a formation.',
  tiles=[
   '......................',
   '.........LLL..........',
   '....XXX...=...XXX.....',
   '....X.M...=...M.X.....',
   '....X..LL.=.LL..X.....',
   'XXX....LL...LL....XXXX',
   '..sss.....==.....sss..',
   '..XXXX..........XXXX..',
   '..X....mm......mm....X',
   '..X...LL..XX..LL....X.',
   '==....LL..X...........'],
  heights=uniform(['2','2','1','1',
                   '1111111221112211111111', '1111111221112211111111', '1', '1', '1',
                   '1111112211111122111111', '1111112211111122111111']),
  wells=[(7, 4), (11, 10)]),
 dict(id='kelpmire', name='The Kelpmire',
  description='A drowned kelp forest gone to husk and mud, split by a cold channel. Things wait in the stalks.',
  tiles=[
   ',,,,,,,,,,,,,,,,,,,,,,',
   ',,kk,,,,,LLL,,,,,,kk,,',
   ',kkk,,,,,,,,,,,,,kkkk,',
   ',,k,,,gg,,,,,gg,,,,k,,',
   ',,,,,ggkk,,,,kkgg,,,,,',
   'kk,,,,kkk,ss,kkk,,,,kk',
   'kkk,,,,,,,ss,,,,,,,kkk',
   ',kkgg,,uu,ss,uu,,ggkk,',
   ',,,g,,uuu,ss,uuu,,g,,,',
   ',,,,,,,,,,ss,,,,,,,,,,',
   'ss,kk,,gg,ssM,gg,kk,ss'],
  heights=uniform(['2','2','1','1','1',
                   '1111111111001111111111', '1111111111001111111111', '1111111111001111111111',
                   '1111111111001111111111', '1111111111001111111111', '0011111111000111111100']),
  wells=[(12, 10), (4, 8)]),
 dict(id='gull_stacks', name='Gull Stacks',
  description='Sea stacks and sinkholes where the Gyre nest. Ground troops take the long way round; wings do not.',
  tiles=[
   '......................',
   '..LL.....LLL.....LL...',
   '..LL......=......LL...',
   '..........=...........',
   '....TTTT..=..TTTT.....',
   '...TTBBTT...TTBBTT....',
   '...TBBBBT...TBBBBT....',
   '...TBBBBT.LL.TBBBBT...',
   '...TTBBTT.LL..TTBBTT..',
   '....TTTT..MM..TTTT....',
   'TT.......LLLL......TTT'],
  heights=uniform(['1',
                   '1133111111111111133111', '1133111111111111133111', '1', '1', '1', '1',
                   '1111111111331111111111', '1111111111331111111111', '1111111112222111111111',
                   '1111111112222111111111']),
  wells=[(2, 2), (10, 7)]),
]


def mirror(rows):
    return rows + [r[::-1] for r in reversed(rows)]


def build(spec):
    tiles, heights = mirror(spec['tiles']), mirror(spec['heights'])
    H = len(tiles)
    for y, (t, h) in enumerate(zip(tiles, heights)):
        assert len(t) == W and len(h) == W, f"{spec['id']} row {y}: widths {len(t)} {len(h)}"
    terr = lambda x, y: LEGEND[tiles[y][x]]
    hgt = lambda x, y: int(heights[y][x])
    passable = lambda x, y: not TERRAIN[terr(x, y)].get('impassable')
    k1 = (10, 1); k0 = (W - 1 - k1[0], H - 1 - k1[1])
    assert passable(*k1), f"{spec['id']}: keystone on impassable tile"

    def bfs(start, jump=1):
        seen = {start}; q = deque([start])
        while q:
            x, y = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in seen and passable(nx, ny) and abs(hgt(nx, ny) - hgt(x, y)) <= jump:
                    seen.add((nx, ny)); q.append((nx, ny))
        return seen

    reach = bfs(k1)
    assert k0 in reach, f"{spec['id']}: Beacons not connected for jump-1 walkers"
    every = {(x, y) for y in range(H) for x in range(W) if passable(x, y)}
    stranded = every - reach
    # Deploy zone: nearest ~20 safe passable tiles around the Beacon, same height band.
    def zone(k):
        cand = [(abs(x - k[0]) + abs(y - k[1]), x, y) for (x, y) in reach
                if (x, y) != k and terr(x, y) not in HAZARD and abs(hgt(x, y) - hgt(*k)) <= 1 and abs(x - k[0]) + abs(y - k[1]) <= 5]
        cand.sort(key=lambda c: (c[0], c[2], c[1]))
        return [[x, y] for _, x, y in cand[:20]]
    wells = []
    for (x, y) in spec['wells']:
        assert passable(x, y), f"{spec['id']}: well on impassable {x},{y}"
        wells += [{'x': x, 'y': y}, {'x': W - 1 - x, 'y': H - 1 - y}]
    legend = {ch: LEGEND[ch] for ch in sorted(set(''.join(tiles)))}
    out = dict(id=spec['id'], name=spec['name'], description=spec['description'], legend=legend,
               tiles=tiles, heights=heights,
               keystones=[{'team': 0, 'x': k0[0], 'y': k0[1]}, {'team': 1, 'x': k1[0], 'y': k1[1]}],
               deployZones={'0': zone(k0), '1': zone(k1)}, wells=wells)
    return out, stranded


if __name__ == '__main__':
    ok = True
    for spec in MAPS:
        try:
            m, stranded = build(spec)
        except AssertionError as e:
            print('FAIL', e); ok = False; continue
        path = os.path.join(ROOT, 'maps', m['id'] + '.json')
        with open(path, 'w') as f:
            json.dump(m, f, indent=2); f.write('\n')
        used = sorted(set(m['legend'].values()))
        print(f"{m['id']:18} deploy {len(m['deployZones']['0'])}/{len(m['deployZones']['1'])} wells {len(m['wells'])} "
              f"jump-1-unreachable {len(stranded)} terrains {used}")
    sys.exit(0 if ok else 1)

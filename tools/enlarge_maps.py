"""Enlarge maps by duplicating quiet rows/columns in mirrored pairs, and remap every coordinate in maps + missions.
Usage: python3 tools/enlarge_maps.py <content_dir> [target=22]"""
import json, glob, os, sys

content = sys.argv[1]; TARGET = int(sys.argv[2]) if len(sys.argv) > 2 else 22
BASE = {'salt_flat', 'silt', 'calcite', 'bone_road', 'lighthouse_stone'}

def pick_dups(n, line_score, protected):
    """Choose indices to duplicate: mirrored pairs (i, n-1-i) + the middle line if the count is odd; quiet lines first, spread out."""
    need = TARGET - n
    if need <= 0: return []
    chosen = []
    if need % 2 == 1:
        mid = n // 2
        chosen.append(mid if n % 2 == 1 else mid - 1)
    pairs = sorted(range(1, n // 2), key=lambda i: (line_score(i) + line_score(n - 1 - i) + (100 if i in protected or n - 1 - i in protected else 0), i))
    for i in pairs:
        if len(chosen) + 2 > need: break
        if any(abs(i - c) <= 1 for c in chosen if c < n / 2): continue  # spread: no adjacent picks
        chosen += [i, n - 1 - i]
    for i in pairs:  # fill if spreading left us short
        if len(chosen) + 2 > need: break
        if i not in chosen: chosen += [i, n - 1 - i]
    return sorted(set(chosen))

def remap_table(n, dups):
    new, m = 0, {}
    for i in range(n):
        m[i] = [new] + ([new + 1] if i in dups else []); new += len(m[i])
    return m

maps = {}
for f in glob.glob(os.path.join(content, 'maps', '*.json')):
    mp = json.load(open(f)); maps[mp['id']] = (f, mp)

missions = [(f, json.load(open(f))) for f in glob.glob(os.path.join(content, 'missions', '*.json'))]

for mid, (f, mp) in maps.items():
    rows, H, W = mp['tiles'], len(mp['tiles']), len(mp['tiles'][0])
    if W >= TARGET and H >= TARGET: continue
    legend = mp['legend']
    def feat(ch): return 0 if legend.get(ch, ch) in BASE else 1
    pts = set()
    for k in mp.get('keystones', []): pts.add((k['x'], k['y']))
    for w in mp.get('wells', []): pts.add((w['x'], w['y']))
    for _, ms in missions:
        if ms.get('map') != mid: continue
        def collect(o):
            if isinstance(o, dict):
                if isinstance(o.get('x'), int) and isinstance(o.get('y'), int): pts.add((o['x'], o['y']))
                for v in o.values(): collect(v)
            elif isinstance(o, list):
                for v in o: collect(v)
        collect(ms)
    heights = mp.get('heights')
    rs = lambda y: sum(feat(c) for c in rows[y]) * 3 + sum(1 for p in pts if p[1] == y) * 5
    cs = lambda x: sum(feat(rows[y][x]) for y in range(H)) * 3 + sum(1 for p in pts if p[0] == x) * 5
    ry = pick_dups(H, rs, {p[1] for p in pts}); rx = pick_dups(W, cs, {p[0] for p in pts})
    MX, MY = remap_table(W, set(rx)), remap_table(H, set(ry))
    # inserted lines are open ground: structural terrain (walls, trenches, lakes, stone, roads) carries through,
    # scattered features (coral, wreck, oil, pools, reef) become the map's commonest ground
    from collections import Counter
    ground = Counter(c for r in rows for c in r if legend.get(c, c) in BASE).most_common(1)[0][0]
    STRUCT = {'salt_wall', 'trench', 'brine_lake', 'lighthouse_stone', 'bone_road', 'kelp_husk'}
    def open_ch(c): return c if legend.get(c, c) in STRUCT or legend.get(c, c) in BASE else ground
    def grow(grid, is_tiles):
        out = []
        for y in range(H):
            for cy in range(len(MY[y])):
                cells = []
                for x in range(W):
                    for cx in range(len(MX[x])):
                        c = grid[y][x]
                        cells.append(open_ch(c) if is_tiles and (cx or cy) else c)
                out.append(''.join(cells))
        return out
    mp['tiles'] = grow(rows, True)
    if heights: mp['heights'] = grow(heights, False)
    P = lambda x, y: (MX[x][0], MY[y][0])
    for k in mp.get('keystones', []) + mp.get('wells', []): k['x'], k['y'] = P(k['x'], k['y'])
    if 'deployZones' in mp:
        for t, z in mp['deployZones'].items():
            seen, nz = set(), []
            for x, y in z:
                for nx in MX[x]:
                    for ny in MY[y]:
                        if (nx, ny) not in seen: seen.add((nx, ny)); nz.append([nx, ny])
            mp['deployZones'][t] = nz
    for _, ms in missions:
        if ms.get('map') != mid: continue
        def fix(o):
            if isinstance(o, dict):
                if isinstance(o.get('x'), int) and isinstance(o.get('y'), int): o['x'], o['y'] = P(o['x'], o['y'])
                if o.get('type') == 'reach_tile' and 'tiles' in o:
                    o['tiles'] = [[nx, ny] for x, y in o['tiles'] for nx in MX[x] for ny in MY[y]]
                for k, v in o.items():
                    if k != 'tiles': fix(v)
            elif isinstance(o, list):
                for v in o: fix(v)
        fix(ms)
    json.dump(mp, open(f, 'w'), indent=2, ensure_ascii=False)
    print(f'{mid}: {W}x{H} -> {len(mp["tiles"][0])}x{len(mp["tiles"])}  cols {rx} rows {ry}')

for f, ms in missions: json.dump(ms, open(f, 'w'), indent=2, ensure_ascii=False)

#!/usr/bin/env python3
"""Builds the 2026-11 map pack (content/maps/<id>.json).

Every map is drawn with a tiny grid DSL (rect / ellipse / line / blob / scatter ...). Each operation is applied
to a cell AND to its 180-degree rotation, so both sides always get exactly the same ground and the maps are fair.
Maps may be any size and may contain void ('_', the chasm terrain: empty space, no tile drawn).
Deploy zones are picked automatically around each Beacon; the script checks jump-1 reachability between the
Beacons, stranded ground, the walkable tile count and height steps, and prints a report per map.
Run: python3 tools/maps/new_maps.py [--ascii]   (fails on unreachable or malformed maps)
"""
import json, os, random, sys
from collections import deque

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'content')
TERRAIN = json.load(open(os.path.join(ROOT, 'terrain.json')))
LEGEND = {
    '.': 'salt_flat', ',': 'silt', 'c': 'dead_coral', 'w': 'wreck', 'p': 'brine_pool', 'T': 'trench',
    '=': 'bone_road', 'X': 'salt_wall', 'o': 'lamp_oil', 'k': 'kelp_husk', 'L': 'lighthouse_stone',
    'B': 'brine_lake', 'r': 'living_reef', 'a': 'calcite',
    's': 'shallows', 'v': 'vent', 'g': 'tangleweed', 'm': 'scrap_field', 'G': 'beam_glass',
    'O': 'razor_oysters', 'M': 'glowmoss', 'u': 'sinkmud', '_': 'void',
}
HAZARD = {'vent', 'razor_oysters', 'lamp_oil', 'brine_pool'}
NEW_TERRAINS = {'shallows', 'vent', 'tangleweed', 'scrap_field', 'beam_glass', 'razor_oysters', 'glowmoss', 'sinkmud'}
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


class Grid:
    def __init__(self, W, H, base='.', h=1, seed=1):
        assert H % 2 == 0, 'height must be even'
        self.W, self.H = W, H
        self.t = [[base] * W for _ in range(H)]
        self.h = [[h] * W for _ in range(H)]
        self.rng = random.Random(seed)
        self.beacon = None
        self.free = set()      # cells exempt from the +-1 height rule (deliberate jump-2 stacks)

    def inb(self, x, y): return 0 <= x < self.W and 0 <= y < self.H
    def rot(self, x, y): return self.W - 1 - x, self.H - 1 - y

    def put(self, x, y, ch=None, h=None):
        if not self.inb(x, y): return
        for (a, b) in ((x, y), self.rot(x, y)):
            if ch is not None: self.t[b][a] = ch
            if h is not None: self.h[b][a] = h

    def ch(self, x, y): return self.t[y][x] if self.inb(x, y) else '_'
    def passable(self, x, y): return self.inb(x, y) and not TERRAIN[LEGEND[self.t[y][x]]].get('impassable')

    # ---- shapes ----
    def rect(self, x0, y0, x1, y1, ch=None, h=None):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1): self.put(x, y, ch, h)

    def ellipse(self, cx, cy, rx, ry, ch=None, h=None, on=None):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if self.inb(x, y) and ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0 and (on is None or self.t[y][x] in on):
                    self.put(x, y, ch, h)

    def diamond(self, cx, cy, r, ch=None, h=None):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if abs(x - cx) + abs(y - cy) <= r: self.put(x, y, ch, h)

    def line(self, x0, y0, x1, y1, ch=None, h=None, w=1):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            x = round(x0 + (x1 - x0) * i / n); y = round(y0 + (y1 - y0) * i / n)
            for dy in range(w):
                for dx in range(w): self.put(x + dx - (w - 1) // 2, y + dy - (w - 1) // 2, ch, h)

    def path(self, pts, ch=None, h=None, w=1):
        for a, b in zip(pts, pts[1:]): self.line(a[0], a[1], b[0], b[1], ch, h, w)

    def blob(self, cx, cy, rx, ry, ch=None, h=None, wobble=0.35, on=None):
        """Irregular island: an ellipse whose radius is perturbed by a few low-frequency sine terms."""
        import math
        ph = [self.rng.random() * 6.28 for _ in range(3)]
        for y in range(int(cy - ry * 1.5) - 1, int(cy + ry * 1.5) + 2):
            for x in range(int(cx - rx * 1.5) - 1, int(cx + rx * 1.5) + 2):
                if not self.inb(x, y): continue
                a = math.atan2((y - cy) / ry, (x - cx) / rx)
                k = 1 + wobble * (0.5 * math.sin(2 * a + ph[0]) + 0.35 * math.sin(3 * a + ph[1]) + 0.25 * math.sin(5 * a + ph[2]))
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= k * k and (on is None or self.t[y][x] in on):
                    self.put(x, y, ch, h)

    def bite(self, p, passes=1, to='_', protect=()):
        """Ragged edges: cells next to `to` (or the border) are replaced by it with probability p."""
        for _ in range(passes):
            cut = []
            for y in range(self.H):
                for x in range(self.W):
                    if self.t[y][x] == to or (x, y) in protect: continue
                    if any(self.inb(x + dx, y + dy) and self.t[y + dy][x + dx] == to for dx, dy in DIRS) and self.rng.random() < p:
                        cut.append((x, y))
            for x, y in cut: self.put(x, y, to, 0)

    def scatter(self, ch, n, on='.,', where=None, h=None):
        """Place n symmetric pairs of `ch` on cells currently showing one of the chars in `on`."""
        cells = [(x, y) for y in range(self.H) for x in range(self.W)
                 if self.t[y][x] in on and (where is None or where(x, y)) and self.rot(x, y) != (x, y)]
        self.rng.shuffle(cells)
        hazard = TERRAIN[LEGEND[ch]].get('onEnter') or LEGEND[ch] in HAZARD
        placed = 0
        for x, y in cells:
            if placed >= n: break
            if self.t[y][x] not in on: continue
            if hazard and self.beacon and any(abs(x - bx) + abs(y - by) <= 5 for bx, by in (self.beacon, self.rot(*self.beacon))): continue
            self.put(x, y, ch, h); placed += 1

    def cluster(self, ch, cx, cy, r, density=0.6, on='.,'):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if self.inb(x, y) and abs(x - cx) + abs(y - cy) <= r and self.t[y][x] in on and self.rng.random() < density:
                    self.put(x, y, ch)

    def heights(self, fn, on_passable=True):
        for y in range(self.H):
            for x in range(self.W):
                if self.t[y][x] == '_': self.h[y][x] = 0; continue
                v = fn(x, y)
                if v is not None: self.h[y][x] = max(0, min(9, int(round(v))))

    def relax(self):
        """Lower any walkable tile that stands more than 1 above a walkable neighbour (except `free` cells)."""
        changed = True
        while changed:
            changed = False
            for y in range(self.H):
                for x in range(self.W):
                    if not self.passable(x, y) or (x, y) in self.free: continue
                    for dx, dy in DIRS:
                        nx, ny = x + dx, y + dy
                        if self.passable(nx, ny) and (nx, ny) not in self.free and self.h[y][x] - self.h[ny][nx] > 1:
                            self.h[y][x] = self.h[ny][nx] + 1; changed = True

    def place_beacon(self, x, y):
        self.beacon = (x, y)
        self.put(x, y, 'L')
        for dx in (-1, 1): self.put(x + dx, y, 'L')

    def prune(self, min_size=24, to='_', keep_high=99):
        """Turn small stray walkable islands (not holding a Beacon) into `to`."""
        seen = set()
        for y in range(self.H):
            for x in range(self.W):
                if (x, y) in seen or not self.passable(x, y): continue
                comp = [(x, y)]; seen.add((x, y)); q = deque([(x, y)])
                while q:
                    a, b = q.popleft()
                    for dx, dy in DIRS:
                        n = (a + dx, b + dy)
                        if n not in seen and self.passable(*n): seen.add(n); comp.append(n); q.append(n)
                if len(comp) < min_size and self.beacon not in comp and self.rot(*self.beacon) not in comp \
                        and not any(self.h[b][a] >= keep_high for a, b in comp):
                    for a, b in comp: self.put(a, b, to, 0)

    def seal(self, ch='X'):
        """Turn walkable cells cut off from the Beacons (pockets walled in by obstacles) into `ch`."""
        seen = {self.beacon}; q = deque([self.beacon])
        while q:
            a, b = q.popleft()
            for dx, dy in DIRS:
                n = (a + dx, b + dy)
                if n not in seen and self.passable(*n): seen.add(n); q.append(n)
        for y in range(self.H):
            for x in range(self.W):
                if self.passable(x, y) and (x, y) not in seen: self.put(x, y, ch)

    def finish(self, prune=True, **kw):
        if prune: self.prune(**kw)
        self.relax()


# ======================================================================================================
def boiling_floor():
    g = Grid(26, 24, base='_', h=1, seed=11)
    # two ragged basalt plateaus (top one drawn; the rotation makes the bottom one)
    g.blob(12.5, 2.0, 13.0, 5.4, '.', 2, wobble=0.2)
    g.rect(0, 0, 25, 1, '.', 2)
    g.bite(0.3, 1)
    # central island with the vents
    g.blob(12.5, 11.5, 6.6, 3.5, ',', 1, wobble=0.15)
    # rifts: a void band between plateau and island, leaving causeways of bone road
    g.rect(0, 7, 25, 8, '_', 0)
    g.rect(5, 6, 6, 9, '=', 1)
    g.rect(16, 6, 16, 9, '=', 1)
    g.rect(21, 4, 22, 8, '=', 1); g.rect(20, 9, 20, 10, '=', 1)
    # cracks through the plateau
    for (x, y) in ((11, 5), (12, 5), (12, 6), (3, 2), (4, 2), (3, 3), (20, 1), (19, 2), (8, 3), (8, 4)): g.put(x, y, '_', 0)
    g.place_beacon(12, 2)
    g.put(12, 3, '='); g.put(12, 4, '='); g.put(13, 4, '=')
    # vents on the central island, ringed by sinkmud
    for (x, y) in ((11, 10), (14, 10), (12, 11), (9, 11), (15, 12), (13, 9), (10, 13)): g.put(x, y, 'v')
    g.cluster('u', 12, 11, 4, 0.25, on=',')
    g.heights(lambda x, y: (3 if (y <= 1 and not 9 <= x <= 15) or (y <= 3 and (x <= 3 or x >= 22)) else 2) if y < 6 else 1)
    g.scatter('c', 8, on='.'); g.scatter('a', 4, on='.,'); g.scatter('v', 3, on='.', where=lambda x, y: 2 < y < 6)
    g.scatter('u', 3, on='.'); g.scatter('k', 3, on='.,'); g.scatter('T', 2, on='.', where=lambda x, y: y < 6)
    g.scatter('w', 2, on='.'); g.scatter('s', 4, on=',', where=lambda x, y: y > 8); g.scatter('M', 2, on='.,'); g.scatter('g', 3, on='.,')
    g.finish(min_size=12)
    return g, dict(wells=[(5, 3), (19, 3)], big=False)


def glasswork_reach():
    g = Grid(30, 30, base='_', h=1, seed=7)
    c = 14.5
    # four long arms (7 wide) radiating from the hub
    g.rect(11, 0, 17, 14, '.', 2)            # north arm (drawn; rotation makes the south arm)
    g.rect(0, 11, 14, 17, '.', 2)            # west arm  (rotation makes the east arm)
    # diagonal arms: stepped staircases ending in pads
    for i in range(0, 8):
        g.rect(4 + i, 4 + i - 1, 6 + i, 6 + i, '.', 1)       # NW arm staircase
    g.rect(2, 2, 7, 7, '.', 2)                                # NW pad
    for i in range(0, 8):
        g.rect(25 - i - 2, 4 + i - 1, 25 - i, 6 + i, '.', 1)  # NE arm staircase
    g.rect(22, 2, 27, 7, '.', 2)                              # NE pad
    # ragged tips
    g.bite(0.3, 1)
    # hub: ruined lighthouse platform
    g.ellipse(c, c, 5.2, 5.2, 'L', 3)
    g.ellipse(c, c, 3.2, 3.2, 'L', 4)
    g.ellipse(c, c, 1.6, 1.6, 'M', 4)
    g.rect(13, 13, 16, 16, 'L', 4)
    g.put(14, 14, 'M'); g.put(15, 14, 'M')
    # beam-glass lanes down the middle of every arm
    g.rect(14, 1, 15, 8, 'G', 2)
    g.rect(1, 14, 8, 15, 'G', 2)
    g.line(5, 5, 9, 9, 'G', 1)
    g.line(24, 5, 20, 9, 'G', 1)
    g.place_beacon(14, 2)
    g.rect(13, 2, 16, 2, 'L')
    g.put(14, 1, 'L'); g.put(15, 1, 'L')
    g.heights(lambda x, y: None)
    # terrace the arms down from tip (h2) toward the hub (h4 at the centre)
    def hh(x, y):
        d = max(abs(x - c), abs(y - c))
        if d <= 1.6: return 4
        if d <= 3.2: return 3
        if d <= 5.2: return 3 if (abs(x - c) <= 3 or abs(y - c) <= 3) else 2
        if d <= 8: return 2
        return 1 if (abs(x - c) > 3.6 and abs(y - c) > 3.6) else 2
    g.heights(hh)
    g.rect(13, 1, 16, 3, None, 2)
    # ruins and cover
    for (x, y) in ((11, 6), (17, 6), (11, 9), (17, 9)): g.put(x, y, 'X')
    g.put(12, 11, 'X'); g.put(17, 11, 'X')
    g.scatter('m', 12, on='.', where=lambda x, y: abs(x - c) > 3 and abs(y - c) > 3 or abs(x - 14.5) > 3)
    g.scatter('c', 12, on='.'); g.scatter('a', 6, on='.'); g.scatter('w', 6, on='.'); g.scatter('O', 4, on='.')
    g.scatter('k', 6, on='.')
    g.finish()
    return g, dict(wells=[(24, 13), (24, 5)], big=True)


def oyster_banks():
    g = Grid(28, 24, base='_', h=1, seed=23)
    # irregular islands (top half; rotation mirrors them)
    g.blob(13.5, 3.2, 6.6, 3.2, ',', 2, wobble=0.25)        # home island
    g.blob(4.5, 8.0, 4.0, 3.4, ',', 1, wobble=0.3)           # west island
    g.blob(23.0, 6.5, 4.6, 3.4, ',', 1, wobble=0.3)          # east island
    g.blob(13.5, 11.5, 5.0, 2.8, ',', 1, wobble=0.25)        # central island (maps onto itself)
    # shallows strips (2 wide) across the gaps between islands
    g.path([(9, 5), (7, 6), (6, 7)], 's', 1, 2)
    g.path([(18, 5), (20, 6)], 's', 1, 2)
    g.path([(13, 6), (13, 9)], 's', 1, 2)
    g.path([(7, 10), (10, 11)], 's', 1, 2)
    g.path([(19, 9), (21, 9)], 's', 1, 2)
    g.place_beacon(13, 2)
    g.rect(12, 1, 14, 1, 'L')
    g.heights(lambda x, y: 2 if (y < 6 and 8 <= x <= 19) else 1)
    # reef and oyster beds on the islands; tide pools along the strips
    g.blob(3.5, 7.5, 1.7, 1.3, 'r', 1, on=',')
    g.blob(24.0, 5.5, 2.0, 1.3, 'r', 1, on=',')
    g.blob(17.5, 3.0, 1.4, 1.0, 'r', 1, on=',')
    g.cluster('O', 10, 4, 1, 0.8, on=',')
    g.cluster('O', 21, 8, 1, 0.8, on=',')
    g.cluster('O', 13, 12, 2, 0.5, on=',')
    g.cluster('g', 5, 9, 1, 0.9, on=',')
    g.cluster('g', 25, 7, 1, 0.8, on=',')
    g.scatter('O', 3, on='s')
    g.scatter('a', 5, on=','); g.scatter('c', 7, on=','); g.scatter('p', 3, on=','); g.scatter('k', 3, on=',')
    g.scatter('s', 4, on=',')
    g.finish(min_size=12)
    return g, dict(wells=[(4, 8), (22, 6)], big=False)


def breakers_yard():
    g = Grid(32, 20, base='.', h=1, seed=31)
    # a wide scrapyard; a diagonal trench rift cuts across the whole yard through the centre
    g.rect(0, 0, 31, 9, '.', 1)
    g.heights(lambda x, y: 1)
    for x in range(0, 32):
        pass
    g.line(31, 0, 0, 19, 'T', 0, 3)
    # gaps in the rift: bridges of bone road and scrap
    for (x, y) in ((15, 9), (16, 10)):
        pass
    for (bx, by) in ((22, 5), (9, 14), (15, 9)):
        g.rect(bx - 2, by - 1, bx + 2, by + 1, 'm', 1)
        g.line(bx - 3, by - 2, bx + 3, by + 2, '=', 1, 2)
    # hulks (walls of salt plate + wreck) lined up like beached ships
    for (x0, y0, x1, y1) in ((3, 6, 10, 6), (12, 2, 12, 6), (18, 3, 25, 3), (26, 4, 26, 8), (5, 9, 5, 12)):
        g.line(x0, y0, x1, y1, 'w', 1)
    for (x0, y0, x1, y1) in ((4, 6, 6, 6), (12, 3, 12, 4), (20, 3, 22, 3), (26, 5, 26, 6)):
        g.line(x0, y0, x1, y1, 'X', 1)
    g.place_beacon(9, 3)
    g.rect(8, 2, 10, 4, 'L', 2)
    # raised decks around the two Beacons
    g.heights(lambda x, y: 2 if (abs(x - 9) + abs(y - 3) <= 5) else 1)
    g.put(9, 3, 'L'); g.put(8, 3, 'L'); g.put(10, 3, 'L')
    for (mx, my) in ((26, 7), (6, 9)):
        g.ellipse(mx, my, 4.5, 3.0, None, 2); g.ellipse(mx, my, 2.6, 1.6, None, 3)
    g.scatter('m', 30, on='.'); g.scatter('o', 8, on='.'); g.scatter('c', 10, on='.'); g.scatter('=', 8, on='.')
    g.scatter('k', 6, on='.'); g.scatter('p', 3, on='.'); g.scatter('w', 8, on='.'); g.scatter('a', 4, on='.')
    g.scatter('X', 3, on='.'); g.scatter('s', 8, on='.'); g.scatter('u', 6, on='.'); g.scatter('v', 4, on='.'); g.scatter('g', 4, on='.'); g.scatter('M', 2, on='.')
    g.seal('X')
    g.finish(prune=False)
    return g, dict(wells=[(14, 4), (24, 7)], big=True)


def tide_steps():
    g = Grid(24, 28, base='B', h=0, seed=41)
    cx, cy = 11.5, 13.5
    # an octagonal amphitheatre cut out of a flooded lake: terraces above, flooded basin below
    for y in range(28):
        for x in range(24):
            dx, dy = abs(x - cx), abs(y - cy)
            if dx + dy * 0.62 <= 13.4 and dx <= 11.6 and dy <= 13.6:
                g.put(x, y, '.', 1)
    def hh(x, y):
        u = abs(y - cy) / 13.5
        v = abs(x - cx) / 11.5
        if u > 0.85: return 4
        if u > 0.66: return 3
        if u > 0.46: return 2
        if u > 0.26: return 1
        return 0
    g.heights(hh)
    # flooded basin
    g.ellipse(cx, cy, 8.0, 3.8, 's', 0)
    g.ellipse(cx, cy, 4.2, 2.0, 'p', 0)
    g.ellipse(cx, cy, 1.8, 1.0, 'B', 0)
    g.place_beacon(11, 2)
    g.rect(9, 1, 14, 3, 'L', 4)
    # retaining walls between terraces with stair gaps
    for y, gaps in ((6, (5, 6, 11, 12, 17, 18)), (9, (3, 4, 9, 10, 13, 14, 19, 20))):
        for x in range(2, 22):
            if x not in gaps and g.ch(x, y) == '.': g.put(x, y, 'X')
    g.rect(11, 5, 12, 5, '=', 3); g.rect(11, 6, 12, 6, '=', 3); g.rect(11, 7, 12, 7, '=', 2); g.rect(11, 8, 12, 9, '=', 2)
    g.path([(5, 5), (5, 10)], '=', None, 1)
    g.heights(lambda x, y: hh(x, y) if g.ch(x, y) != 'B' else 0)
    g.scatter('s', 10, on='.', where=lambda x, y: abs(y - cy) < 7)
    g.scatter('c', 16, on='.'); g.scatter('k', 8, on='.'); g.scatter('a', 6, on='.'); g.scatter('p', 4, on='.')
    g.scatter('m', 6, on='.'); g.scatter('M', 3, on='.')
    g.finish()
    return g, dict(wells=[(4, 9), (17, 11)], big=False)


def saltpan_bastions():
    import math
    g = Grid(30, 30, base='B', h=1, seed=53)
    cx = cy = 14.5
    # star fort: eight bastion lobes (sides and corners) on a round curtain, set in a flooded pan
    for y in range(30):
        for x in range(30):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy); a = math.atan2(dy, dx)
            lobe = max(0.0, math.cos(8 * a)) ** 0.5
            if d <= 8.6 + 6.4 * lobe: g.put(x, y, '.', 1)
    # inner curtain wall ring with four gates, bastions and the rampart outside it stand a level higher
    for y in range(30):
        for x in range(30):
            if g.t[y][x] == 'B': continue
            dx, dy = x - cx, y - cy; d = math.hypot(dx, dy)
            if 6.0 <= d < 7.2 and not (abs(dx) <= 1.6 or abs(dy) <= 1.6): g.put(x, y, 'X')
            if d >= 7.2: g.put(x, y, None, 2)
    # keep (centre): lighthouse stone block, salt pans and glowmoss
    g.rect(12, 12, 17, 17, 'L', 1)
    g.rect(13, 13, 16, 16, 'p', 1); g.rect(14, 14, 15, 15, 'M', 1)
    g.ellipse(9.5, 9.5, 1.6, 1.6, 'p', 1); g.ellipse(9.5, 19.5, 1.6, 1.6, 'p', 1)
    g.path([(14, 0), (14, 14)], '=', None, 1); g.path([(0, 14), (14, 14)], '=', None, 1)
    g.place_beacon(14, 2)
    g.rect(13, 1, 15, 1, 'L')
    # barricades of scrap in the bastion gorges, salt and glass cover
    for (x, y) in ((9, 5), (20, 5), (5, 9), (24, 9)): g.cluster('m', x, y, 1, 0.9, on='.')
    g.scatter('m', 8, on='.'); g.scatter('c', 8, on='.'); g.scatter('a', 8, on='.'); g.scatter('s', 8, on='.')
    g.scatter('g', 4, on='.'); g.scatter('w', 4, on='.'); g.scatter('M', 2, on='.')
    g.finish(prune=False)
    return g, dict(wells=[(9, 8), (22, 6)], big=False)


def kelpmire():
    import math
    g = Grid(18, 26, base='k', h=2, seed=67)
    # a winding valley: a cold shallows channel meanders down the long axis, banks climb to a kelp rim
    pts = [(2, 0), (3, 4), (11, 6), (13, 9), (8, 12), (8, 13)]
    g.path(pts, 's', 0, 3)
    rp = [g.rot(*q) for q in pts]
    def dist(x, y):
        best = 99
        for (a, b) in list(zip(pts, pts[1:])) + list(zip(rp, rp[1:])):
            ax, ay = a; bx, by = b
            L2 = (bx - ax) ** 2 + (by - ay) ** 2 or 1
            t = max(0, min(1, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / L2))
            best = min(best, math.hypot(x - (ax + t * (bx - ax)), y - (ay + t * (by - ay))))
        return best
    g.heights(lambda x, y: min(3, dist(x, y) / 2.4))
    for y in range(26):
        for x in range(18):
            if g.t[y][x] != 's':
                d = dist(x, y)
                g.put(x, y, ',' if d < 4.5 else 'k', None)
    g.place_beacon(7, 2)
    g.rect(6, 1, 8, 1, 'L')
    g.cluster('u', 9, 6, 2, 0.7, on=',k'); g.cluster('u', 5, 3, 1, 0.8, on=',k'); g.cluster('u', 13, 11, 2, 0.6, on=',k')
    g.cluster('g', 6, 9, 2, 0.6, on=',k'); g.cluster('g', 14, 6, 2, 0.6, on=',k'); g.cluster('g', 3, 8, 1, 0.8, on=',k')
    g.put(6, 5, 'T'); g.put(11, 4, 'T'); g.put(7, 11, 'T')
    g.cluster('M', 4, 11, 1, 0.8, on=',k')
    g.scatter('k', 10, on=','); g.scatter('c', 8, on=',k'); g.scatter('w', 4, on=',k'); g.scatter('a', 4, on=',k')
    g.scatter('s', 6, on=','); g.scatter('p', 3, on=',')
    g.finish(prune=False)
    return g, dict(wells=[(3, 8), (13, 7)], big=False)


def gull_stacks():
    g = Grid(28, 28, base='_', h=1, seed=79)
    # pillar islands of different heights (top half; rotated for the other half)
    g.blob(13.5, 3.5, 4.4, 3.1, ',', 2, wobble=0.25)           # home stack
    g.blob(4.5, 6.5, 3.0, 2.8, '.', 3, wobble=0.3)             # west pillar
    g.blob(23.5, 4.5, 3.0, 2.8, '.', 3, wobble=0.3)            # east pillar
    g.blob(9.5, 12.0, 2.8, 2.2, ',', 2, wobble=0.3)            # low shelf
    g.blob(13.5, 13.5, 3.2, 3.0, '.', 4, wobble=0.15)          # centre stack (onto itself)
    # thin bridges, one tile wide, stepping between heights
    def bridge(pts, h0, h1):
        cells = []
        for a, b in zip(pts, pts[1:]):
            n = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
            for i in range(n):
                cells.append((round(a[0] + (b[0] - a[0]) * i / n), round(a[1] + (b[1] - a[1]) * i / n)))
        cells.append(pts[-1])
        for i, (x, y) in enumerate(cells):
            if g.ch(x, y) == '_': g.put(x, y, '=', round(h0 + (h1 - h0) * (i + 1) / (len(cells) + 1)))
    bridge([(9, 4), (7, 4), (7, 6)], 2, 3)
    bridge([(18, 4), (20, 4)], 2, 3)
    bridge([(13, 7), (13, 10)], 2, 3)
    bridge([(6, 9), (6, 12), (7, 12)], 3, 2)
    bridge([(11, 13), (12, 13)], 2, 4)
    bridge([(22, 7), (22, 10), (17, 10), (16, 12)], 3, 4)
    # the jump-2 stack with a well: reachable by flyers, or by a jump-2 walker from the east bridge
    g.blob(22.5, 12.0, 1.6, 1.5, ',', 6, wobble=0.1)
    g.free |= {(x, y) for y in range(g.H) for x in range(g.W) if g.h[y][x] == 6}
    g.put(21, 10, '=', 4)
    # a second lone flyer perch
    g.blob(3.5, 12.0, 1.3, 1.2, 'a', 5, wobble=0.1)
    g.free |= {(x, y) for y in range(g.H) for x in range(g.W) if g.h[y][x] == 5 and g.ch(x, y) == 'a'}
    g.place_beacon(13, 2)
    g.rect(12, 1, 14, 1, 'L')
    g.cluster('c', 13, 4, 2, 0.4, on=',.'); g.cluster('k', 4, 6, 2, 0.4, on='.'); g.cluster('a', 23, 4, 2, 0.4, on='.')
    g.scatter('c', 8, on=',.'); g.scatter('a', 5, on=',.'); g.scatter('m', 6, on='.'); g.scatter('w', 4, on=',.')
    g.scatter('O', 3, on=',', where=lambda x, y: y > 8); g.scatter('s', 4, on=',.'); g.scatter('M', 3, on=',.'); g.scatter('g', 4, on=',.'); g.scatter('v', 2, on='.')
    g.finish()
    return g, dict(wells=[(4, 6), (22, 12)], big=True, allow_stranded=True)


MAPS = [
    dict(id='boiling_floor', name='The Boiling Floor', build=boiling_floor,
         description='Two scarred basalt plateaus split by a smoking rift, joined by a few bone causeways. The vents on the central island scald anyone who lingers, unless they were born to the pressure below.'),
    dict(id='glasswork_reach', name='The Glasswork Reach', build=glasswork_reach,
         description='Where the Shoal lamp swept for three hundred years the sand ran to glass. Four long arms of bright fused lanes meet at the ruined lighthouse: plenty to shoot down, nowhere to hide on them.'),
    dict(id='oyster_banks', name='The Oyster Banks', build=oyster_banks,
         description='Islands of silt and waking reef strung together by tide-left shallows, and a long drop on every side. Wet going, good for anything that dries out, and the coral is listening.'),
    dict(id='breakers_yard', name="Breakers' Yard", build=breakers_yard,
         description='Where the Compact strips the drowned fleets. A trench torn diagonally through the yard, hulks for walls, scrap for cover, and oil in every low place.'),
    dict(id='tide_steps', name='The Tide Steps', build=tide_steps,
         description='Terraces cut by the falling sea, stepping down from both rims into a basin the tide keeps trying to refill. The Returning Tide walk its water like a road.'),
    dict(id='saltpan_bastions', name='Saltpan Bastions', build=saltpan_bastions,
         description='A Concord salt works walled into a star fort on a flooded pan. Gates, bastion points and killing lanes for anyone who can hold a formation.'),
    dict(id='kelpmire', name='The Kelpmire', build=kelpmire,
         description='A drowned kelp forest gone to husk and mud, split by a cold winding channel. Things wait in the stalks.'),
    dict(id='gull_stacks', name='Gull Stacks', build=gull_stacks,
         description='Sea stacks and sinkholes where the Gyre nest. Ground troops take the thin bridges the long way round; wings do not, and some perches have no road at all.'),
]


def build(spec):
    g, extra = spec['build']()
    W, H = g.W, g.H
    tiles = [''.join(r) for r in g.t]
    heights = [''.join(str(v) for v in r) for r in g.h]
    terr = lambda x, y: LEGEND[tiles[y][x]]
    hgt = lambda x, y: int(heights[y][x])
    passable = lambda x, y: not TERRAIN[terr(x, y)].get('impassable')
    k1 = g.beacon; k0 = (W - 1 - k1[0], H - 1 - k1[1])
    assert passable(*k1), f"{spec['id']}: keystone on impassable tile"

    def bfs(start, jump=1):
        seen = {start}; q = deque([start])
        while q:
            x, y = q.popleft()
            for dx, dy in DIRS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in seen and passable(nx, ny) and abs(hgt(nx, ny) - hgt(x, y)) <= jump:
                    seen.add((nx, ny)); q.append((nx, ny))
        return seen

    reach = bfs(k1)
    assert k0 in reach, f"{spec['id']}: Beacons not connected for jump-1 walkers"
    every = {(x, y) for y in range(H) for x in range(W) if passable(x, y)}
    walk = len(every)
    lo, hi = 200, 750 if extra.get('big') else 480
    assert lo <= walk <= hi, f"{spec['id']}: {walk} walkable tiles (want {lo}-{hi})"
    stranded = every - reach
    if extra.get('allow_stranded'):
        # deliberate perches: reachable only by jump-2 or flyers. Everything else must be on the main body.
        reach2 = bfs(k1, 2)
        assert (every - reach2) <= {p for p in every if hgt(*p) >= 5}, f"{spec['id']}: stranded ground that is not a perch"
    else:
        assert not stranded, f"{spec['id']}: {len(stranded)} unreachable walkable tiles, e.g. {sorted(stranded)[:6]}"
    steps = sum(1 for (x, y) in every for dx, dy in ((1, 0), (0, 1)) if (x + dx, y + dy) in every and abs(hgt(x + dx, y + dy) - hgt(x, y)) > 1)

    def zone(k):
        cand = [(abs(x - k[0]) + abs(y - k[1]), x, y) for (x, y) in reach
                if (x, y) != k and terr(x, y) not in HAZARD and abs(hgt(x, y) - hgt(*k)) <= 1 and abs(x - k[0]) + abs(y - k[1]) <= 5]
        cand.sort(key=lambda c: (c[0], c[2], c[1]))
        return [[x, y] for _, x, y in cand[:20]]
    z0, z1 = zone(k0), zone(k1)
    assert len(z1) >= 16, f"{spec['id']}: deploy zone only {len(z1)} tiles"
    wells = []
    for (x, y) in extra['wells']:
        assert passable(x, y), f"{spec['id']}: well on impassable {x},{y}"
        wells += [{'x': x, 'y': y}, {'x': W - 1 - x, 'y': H - 1 - y}]
    legend = {ch: LEGEND[ch] for ch in sorted(set(''.join(tiles)))}
    used = set(legend.values())
    assert len(used & NEW_TERRAINS) >= 3, f"{spec['id']}: only {sorted(used & NEW_TERRAINS)} of the new terrains"
    out = dict(id=spec['id'], name=spec['name'], description=spec['description'], legend=legend,
               tiles=tiles, heights=heights,
               keystones=[{'team': 0, 'x': k0[0], 'y': k0[1]}, {'team': 1, 'x': k1[0], 'y': k1[1]}],
               deployZones={'0': z0, '1': z1}, wells=wells)
    info = dict(size=f'{W}x{H}', walk=walk, void=sum(r.count('_') for r in tiles), stranded=len(stranded), steps=steps,
                dist=abs(k0[0] - k1[0]) + abs(k0[1] - k1[1]))
    return out, info, g


if __name__ == '__main__':
    ok = True
    only = [a for a in sys.argv[1:] if not a.startswith('--')]
    for spec in MAPS:
        if only and spec['id'] not in only: continue
        try:
            m, info, g = build(spec)
        except AssertionError as e:
            print('FAIL', e); ok = False
            if '--ascii' in sys.argv:
                gg, _ = spec['build'](); print('\n'.join(''.join(r) for r in gg.t))
            continue
        if '--ascii' in sys.argv:
            print(m['id']); print('\n'.join(m['tiles'])); print('\n'.join(m['heights']))
        path = os.path.join(ROOT, 'maps', m['id'] + '.json')
        with open(path, 'w') as f:
            json.dump(m, f, indent=2); f.write('\n')
        used = sorted(set(m['legend'].values()))
        print(f"{m['id']:17} {info['size']:6} walk {info['walk']:3} void {info['void']:3} deploy {len(m['deployZones']['0'])}/{len(m['deployZones']['1'])} "
              f"beacons {info['dist']} stranded {info['stranded']} cliffs {info['steps']} terrains {len(used)}")
    sys.exit(0 if ok else 1)

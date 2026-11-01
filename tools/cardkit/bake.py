"""Bake the relic card frames: cast bronze (gold for heroes) around a full-bleed art window, with a
tide-glass cost gem, a faction enamel name cartouche, a sigil boss and a slate rules panel.
Run: python3 tools/cardkit/bake.py  -> src/ui/kit/card/frame_<faction>[_hero].webp
Card space is 500x700 (5:7); baked at 2x. Coordinates here must match src/ui/cards.css."""
import os, sys, json, math
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'uikit'))
import importlib.util
spec = importlib.util.spec_from_file_location('uk', os.path.join(os.path.dirname(__file__), '..', 'uikit', 'bake.py'))
# reuse the kit's material helpers without re-running its bake (it bakes at import), so copy the bits we need
src = open(spec.origin).read().split("logo('logo.png')")[0]
src = src.replace("os.makedirs(OUT, exist_ok=True)", "")
uk = {'__file__': spec.origin}; exec(compile(src, spec.origin, 'exec'), uk)
blur, fbm, grain, shade, ramp, smooth, sd_round_rect, salt_crust, SALT = (uk[k] for k in
    ['blur', 'fbm', 'grain', 'shade', 'ramp', 'smooth', 'sd_round_rect', 'salt_crust', 'SALT'])

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
OUT = os.path.join(ROOT, 'src', 'ui', 'kit', 'card'); os.makedirs(OUT, exist_ok=True)
K = 2                      # bake scale
W, H = 500 * K, 700 * K
y, x = np.mgrid[0:H, 0:W].astype(np.float32) / K + 0.5 / K   # card units

BRONZE = [(0, (16, 13, 11)), (.4, (46, 38, 30)), (.65, (88, 68, 44)), (.85, (146, 112, 66)), (1, (204, 170, 116))]
GOLD = [(0, (60, 38, 8)), (.35, (140, 96, 24)), (.6, (206, 158, 60)), (.8, (240, 204, 110)), (1, (255, 240, 190))]
VERDI = np.array([62, 108, 96]) / 255.0

def metal_albedo(height, seed, stops):
    n = fbm(H, W, 5, 6, seed); pits = grain(H, W, seed + 1, 1)
    base = ramp(0.45 + (n - 0.5) * 0.5 + height * 0.25, stops)
    cav = np.clip((blur(height, 5) - height) * 6, 0, 1)
    base = base * (1 - cav[..., None] * 0.5) + VERDI * (cav * smooth(.55, .8, n))[..., None] * 0.5
    return base * (0.9 + pits * 0.2)[..., None]

def bar(t):
    """rounded bar profile for t in 0..1 across a band"""
    return np.clip(np.sin(np.clip(t, 0, 1) * math.pi), 0, 1) ** 0.6

def hexrgb(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)]) / 255.0

# ---- geometry (card units) ----
OUTER = (250, 350, 247, 347, 22)   # cx, cy, hw, hh, r
BAND = 24
INNER = (250, 350, 247 - BAND, 347 - BAND, 8)
NAME_Y0, NAME_Y1 = 418, 464        # cartouche
PANEL_TOP = 464
COST = (58, 58, 50)                # cx, cy, r
SIGIL = (448, 50, 30)
RIVETS = [(250, 688), (250, 12)]

def bake(fid, color, hero, seed=41):
    stops = GOLD if hero else BRONZE
    d_out = sd_round_rect(x, y, *OUTER)
    d_in = sd_round_rect(x, y, *INNER)
    t = np.clip(-d_out / BAND, 0, 1)
    border = (d_out < 0) & (d_in > 0)
    # profile: rounded outer rim | engraved groove with bead-and-reel | raised inner bead | step down
    prof = 0.75 * bar(np.clip(t / 0.42, 0, 1)) + 0.15
    prof += 0.55 * bar(np.clip((t - 0.62) / 0.26, 0, 1))
    groove = (t > 0.42) & (t < 0.62)
    along = np.where(np.abs(x - 250) / 247 > np.abs(y - 350) / 347, y, x)       # coordinate along the band
    beads = 0.32 * np.clip(np.cos(along * 2 * math.pi / 9), 0, 1) ** 2 * np.clip(np.sin((t - 0.42) / 0.2 * math.pi), 0, 1)
    prof = np.where(groove, 0.12 + beads, prof)
    hgt = np.where(border, prof, 0.0)
    mask = border.astype(np.float32)

    # corner brackets: heavy L plates with a boss, overlapping into the art
    for sx, sy in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
        if sy == 1 and sx == 1: continue                     # top-left is the cost gem
        if sy == 1 and sx == -1: continue                    # top-right is the sigil
        cx_ = 250 - sx * 247; cy_ = 350 - sy * 347
        lx = (x - cx_) * sx; ly = (y - cy_) * sy             # local coords, 0 at corner, + inward
        arm = np.minimum(np.maximum(lx - 74, ly - 34), np.maximum(lx - 34, ly - 74))
        dl = np.maximum(arm, -np.minimum(lx, ly))
        # cusped inner edge
        dl = np.maximum(dl, -(np.hypot(lx - 74, ly - 74) - 42))
        pl = dl < 0
        hgt = np.where(pl, np.maximum(hgt, 0.55 + 0.35 * np.clip(-dl / 10, 0, 1) ** .5), hgt)
        rr = np.hypot(lx - 22, ly - 22)
        hgt = np.where(rr < 13, np.maximum(hgt, 0.9 + 0.55 * np.sqrt(np.clip(1 - (rr / 13) ** 2, 0, 1))), hgt)
        hgt -= (np.abs(rr - 17) < 1.2) * 0.25 * pl
        mask = np.maximum(mask, pl)

    # name cartouche: full-width banner over the border, pointed ends, round end bosses
    cy = (NAME_Y0 + NAME_Y1) / 2; hh = (NAME_Y1 - NAME_Y0) / 2
    dx = np.abs(x - 250)
    half = 236 - np.abs(y - cy) * 0.5
    d_c = np.maximum(dx - half, np.abs(y - cy) - hh)
    cart = d_c < 0
    tc = np.clip(-d_c / 9, 0, 1)
    hgt = np.where(cart, np.maximum(hgt, 0.45 + 0.5 * bar(tc * 0.5)), hgt)
    d_e = np.maximum(dx - (half - 22), np.abs(y - cy) - (hh - 7))
    enamel = d_e < 0
    mask = np.maximum(mask, cart)

    # cost socket: heavy notched ring + tide glass gem
    r = np.hypot(x - COST[0], y - COST[1]); R = COST[2]
    ring = (r < R) & (r > R - 14)
    ang = np.arctan2(y - COST[1], x - COST[0])
    hgt = np.where(r < R, np.maximum(hgt, np.where(ring, 0.9 * bar((R - r) / 14) + 0.3 - 0.2 * (np.cos(ang * 18) > 0.7), 0.3)), hgt)
    gem = r <= R - 14
    mask = np.maximum(mask, (r < R).astype(np.float32))

    # sigil boss
    rs = np.hypot(x - SIGIL[0], y - SIGIL[1]); Rs = SIGIL[2]
    sring = (rs < Rs) & (rs > Rs - 9)
    hgt = np.where(rs < Rs, np.maximum(hgt, np.where(sring, 0.85 * bar((Rs - rs) / 9) + 0.25, 0.15)), hgt)
    swell = rs <= Rs - 9
    mask = np.maximum(mask, (rs < Rs).astype(np.float32))

    # hero crest at top centre
    if hero:
        dcr = np.maximum(np.abs(x - 250) * 1.0 + (y - 2) * 1.1 - 46, np.abs(y - 22) - 20)
        crest = dcr < 0
        hgt = np.where(crest, np.maximum(hgt, 0.7 + 0.4 * np.clip(-dcr / 14, 0, 1) ** .5), hgt)
        rr = np.hypot(x - 250, y - 20); hgt = np.where(rr < 10, np.maximum(hgt, 1.2 * np.sqrt(np.clip(1 - (rr / 10) ** 2, 0, 1)) + 0.4), hgt)
        mask = np.maximum(mask, crest | (rr < 10))

    for cx_, cy_ in RIVETS:
        rr = np.hypot(x - cx_, y - cy_)
        hgt = np.where(rr < 7, np.maximum(hgt, 0.9 + 0.5 * np.sqrt(np.clip(1 - (rr / 7) ** 2, 0, 1))), hgt)

    hgt = hgt + (fbm(H, W, 4, 18, seed) - 0.5) * 0.1 * (hgt > 0)
    alb = metal_albedo(hgt, seed, stops)
    rgb, ao = shade(hgt, alb, strength=6 * K)
    sc = salt_crust(H, W, (hgt > 0.05).astype(float) * (1 - smooth(0.1, 0.5, hgt)), seed + 9, 0.7 if not hero else 0.3)
    rgb = rgb * (1 - sc[..., None]) + SALT * (0.7 + 0.25 * ao)[..., None] * sc[..., None]

    fc = hexrgb(color)
    e_t = np.clip(-d_e / 8, 0, 1)
    en = fc * 0.5 * (0.45 + 0.55 * e_t)[..., None] * (0.8 + 0.35 * fbm(H, W, 3, 8, seed + 5))[..., None]
    en += (np.exp(-((y - (NAME_Y0 + 13)) / 4) ** 2) * 0.10 * enamel)[..., None]
    rgb = np.where(enamel[..., None], en, rgb)

    g = np.clip(1 - np.hypot(x - COST[0] + 10, y - COST[1] + 12) / (R * 1.15), 0, 1)
    glass = ramp(g ** 0.9, [(0, (3, 18, 34)), (.45, (14, 74, 110)), (.8, (60, 160, 196)), (1, (190, 240, 255))])
    spec = np.exp(-(((x - COST[0] + 13) / 10) ** 2 + ((y - COST[1] + 17) / 6) ** 2)) * 0.55
    rgb = np.where(gem[..., None], np.clip(glass + spec[..., None], 0, 1), rgb)
    rgb = np.where(swell[..., None], fc * 0.22 + 0.03, rgb)

    # rules panel: slate under the cartouche, with a thin bronze inset line
    inside = d_in <= 0
    sl_n = fbm(H, W, 6, 4, seed + 7); sl2 = fbm(H, W, 4, 14, seed + 8)
    slate = ramp(sl_n * .7 + sl2 * .3, [(0, (11, 14, 18)), (.5, (19, 24, 30)), (1, (32, 38, 45))]) + fc * 0.04
    d_p = sd_round_rect(x, y, 250, (PANEL_TOP + 650) / 2 + 4, 247 - BAND - 10, (650 - PANEL_TOP) / 2 - 6, 6)
    line = np.abs(d_p) < 0.9
    slate = np.where(line[..., None], ramp(np.full_like(x, .7), stops) * 0.8, slate)
    pa = smooth(NAME_Y0 - 60, NAME_Y0 + 6, y) * inside
    # inner lip shadow + vignette over the art
    lip = np.exp(-np.clip(-d_in, 0, 99) / 7) * 0.85 + np.clip(1 - (-d_in) / 70, 0, 1) * 0.35
    lip = np.clip(lip, 0, 0.95) * inside
    rgbf = np.where((mask > 0.5)[..., None], rgb, np.where((pa > 0.001)[..., None], slate, 0.015))
    a = np.where(mask > 0.5, 1.0, np.maximum(pa, lip))
    a = np.minimum(a, np.clip(0.5 - d_out * K, 0, 1))
    # drop shadow of raised parts onto the art
    sh = np.roll(np.roll(blur(mask.astype(float), 5 * K), 4 * K, 0), 3 * K, 1) * inside * (mask < 0.5)
    a = np.where(mask > 0.5, a, np.clip(a + sh * 0.6 * (1 - a), 0, 1))
    img = Image.fromarray((np.dstack([np.clip(rgbf, 0, 1), a[..., None]]) * 255).astype(np.uint8), 'RGBA')
    name = f'frame_{fid}{"_hero" if hero else ""}.webp'
    img.save(os.path.join(OUT, name), quality=88, method=6)
    print('wrote', name)

factions = json.load(open(os.path.join(ROOT, 'content', 'factions.json')))
factions = factions if isinstance(factions, dict) else {f['id']: f for f in factions}
only = sys.argv[1:]
for i, (fid, f) in enumerate(list(factions.items()) + [('neutral', {'color': '#5a6f7a'})]):
    if only and fid not in only: continue
    for hero in (False, True):
        bake(fid, f['color'], hero, seed=41 + i * 3)

"""Detailed painted card backdrops, one scene recipe per faction.
Every scene shares the Brinewake signature: the lifted sea hanging overhead, a lighthouse on the horizon whose beam holds
it up, layered hazy ridges, a rippled seabed with salt crust, stones and tide pools, dark foreground rocks and drifting motes.
Each faction adds its own landmarks (salt walls, trench bells, wreck ribs, rusted hulks, coral spires, lamp stairs,
sky-fish, sea stacks and wheeling birds). Pure numpy + PIL; deterministic per seed.
Used by interim_art.py (units) and motif_art.py (spells, equipment): scene(fid, seed) -> (rgb float HxWx3, key rgb, horizon y)."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 512, 768
SS = 2  # supersample for silhouettes
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

# sea-ceiling, sky top, sky horizon, far land, ground near, ground far, key light, accent, prop colour
PAL = {
    'salt_concord':    dict(sea=(30, 52, 78), top=(70, 84, 106), hor=(214, 198, 172), land=(150, 140, 128), gn=(190, 182, 166), gf=(160, 154, 142), key=(255, 226, 180), acc=(120, 160, 210), prop=(92, 88, 84)),
    'hadal_court':     dict(sea=(4, 10, 26), top=(8, 18, 38), hor=(26, 64, 84), land=(16, 28, 44), gn=(18, 24, 36), gf=(26, 40, 56), key=(110, 236, 216), acc=(63, 214, 196), prop=(12, 18, 30)),
    'returning_tide':  dict(sea=(16, 34, 34), top=(34, 50, 46), hor=(128, 146, 128), land=(70, 86, 76), gn=(54, 70, 60), gf=(84, 102, 90), key=(214, 230, 210), acc=(120, 200, 160), prop=(34, 42, 38)),
    'salvage_compact': dict(sea=(30, 24, 26), top=(52, 34, 28), hor=(210, 128, 70), land=(110, 70, 50), gn=(84, 56, 40), gf=(128, 86, 60), key=(255, 196, 126), acc=(240, 120, 50), prop=(46, 30, 24)),
    'reef_ascendant':  dict(sea=(34, 20, 46), top=(60, 30, 62), hor=(226, 140, 128), land=(150, 86, 98), gn=(98, 54, 66), gf=(150, 92, 100), key=(255, 206, 186), acc=(240, 130, 160), prop=(72, 34, 52)),
    'lanternkeepers':  dict(sea=(10, 14, 30), top=(18, 20, 36), hor=(92, 82, 100), land=(46, 44, 56), gn=(34, 32, 40), gf=(56, 52, 62), key=(255, 204, 116), acc=(227, 176, 75), prop=(24, 22, 30)),
    'overcurrent':     dict(sea=(6, 20, 46), top=(14, 34, 66), hor=(118, 184, 218), land=(40, 70, 96), gn=(28, 48, 70), gf=(58, 92, 118), key=(160, 238, 240), acc=(95, 224, 230), prop=(18, 34, 56)),
    'gyre':            dict(sea=(32, 40, 50), top=(54, 60, 70), hor=(184, 178, 132), land=(96, 100, 104), gn=(82, 86, 90), gf=(122, 124, 120), key=(242, 216, 162), acc=(232, 137, 47), prop=(44, 48, 56)),
    'slough':          dict(sea=(14, 22, 18), top=(30, 40, 28), hor=(150, 166, 104), land=(60, 74, 46), gn=(58, 66, 40), gf=(92, 104, 62), key=(226, 236, 150), acc=(181, 201, 52), prop=(22, 26, 20)),
    'hermitage':       dict(sea=(30, 20, 40), top=(52, 34, 66), hor=(214, 140, 80), land=(110, 72, 100), gn=(90, 60, 76), gf=(130, 88, 100), key=(255, 206, 150), acc=(217, 130, 43), prop=(44, 28, 46)),
}

def A(c): return np.asarray(c, np.float32)

def fbm(h, w, octaves, base, seed):
    g = np.random.default_rng(seed); acc = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        n = base * 2 ** o
        img = Image.fromarray((g.random((max(2, n * h // max(h, w) + 1), n)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += amp * np.asarray(img, np.float32) / 255; tot += amp; amp *= 0.5
    return acc / tot

def ridge(seed, n, base_y, amp, rough=4):
    """1D fractal height line (W samples)."""
    g = np.random.default_rng(seed); y = np.zeros(W, np.float32); a = amp
    for o in range(rough):
        k = 3 * 2 ** o
        pts = g.random(k + 2) * 2 - 1
        y += a * np.interp(np.linspace(0, k + 1, W), np.arange(k + 2), pts)
        a *= 0.5
    return base_y + y

def lerp(a, b, t): return A(a)[None, None] * (1 - t[..., None]) + A(b)[None, None] * t[..., None]

class Canvas:
    def __init__(self): self.img = np.zeros((H, W, 3), np.float32)
    def put(self, mask, color, alpha=1.0):
        m = (mask * alpha)[..., None]
        self.img = self.img * (1 - m) + (A(color)[None, None] if np.ndim(color) == 1 else color) * m
    def add(self, light, color, k=1.0):
        self.img += A(color)[None, None] * (light * k)[..., None]

def silhouette(draw_fn, blur=0.0):
    im = Image.new('L', (W * SS, H * SS), 0); d = ImageDraw.Draw(im); draw_fn(d, SS)
    im = im.resize((W, H), Image.LANCZOS)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(im, np.float32) / 255

def haze_col(p, depth):  # depth 0 near .. 1 far: blend prop colour toward horizon
    return tuple(A(p['prop']) * (1 - depth) + A(p['hor']) * depth * 0.85 + A(p['land']) * depth * 0.15)

# ---------- shared layers ----------

def sky(cv, p, hz, seed):
    t = np.clip(yy / hz, 0, 1) ** 1.3
    cv.img = lerp(p['top'], p['hor'], t)
    cl = fbm(H, W, 5, 3, seed); cl2 = fbm(H, W, 4, 9, seed + 1)
    band = np.clip(1 - np.abs(yy - hz * 0.55) / (hz * 0.5), 0, 1)
    clouds = np.clip((cl * 0.7 + cl2 * 0.3 - 0.5) * 3, 0, 1) * band
    lit = np.clip((np.roll(cl, 4, 0) - cl) * 12 + 0.5, 0, 1)  # undersides catch light
    cv.img = cv.img * (1 - clouds[..., None] * 0.45) + (A(p['hor']) * 0.7 + A(p['key']) * 0.3 * lit[..., None]) * clouds[..., None] * 0.45

def hanging_sea(cv, p, seed):
    """The lifted sea seen from below: a dark rippled ceiling with caustic light and a bright refracting edge."""
    g = np.random.default_rng(seed + 7)
    edge = ridge(seed + 11, 0, H * (0.11 + g.random() * 0.05), 22, 5)
    under = yy < edge[None, :]
    rip = fbm(H, W, 4, 6, seed + 12)
    waves = 0.5 + 0.5 * np.sin(yy * 0.35 + rip * 10 + xx * 0.01)
    caust = np.abs(np.sin((xx * 0.05 + rip * 7) + yy * 0.08)) ** 10 * np.clip(rip * 2 - 0.7, 0, 1)
    sea = A(p['sea'])[None, None] * (0.7 + 0.35 * rip[..., None] + 0.15 * waves[..., None]) + A(p['acc'])[None, None] * caust[..., None] * 0.22
    m = under.astype(np.float32)
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    cv.put(m, sea)
    d = np.abs(yy - edge[None, :])
    cv.add((np.exp(-d / 2.5) * 0.28 + np.exp(-d / 22) * 0.12) * (0.6 + 0.8 * rip), tuple(A(p['acc']) * 0.5 + A(p['key']) * 0.5))
    # drips and threads falling from the ceiling
    for i in range(10):
        x = g.random() * W; y0 = np.interp(x, np.arange(W), edge); L = 10 + g.random() * 70
        streak = np.exp(-np.abs(xx - x) / 0.9) * ((yy > y0) & (yy < y0 + L)) * (1 - (yy - y0) / L).clip(0, 1)
        cv.add(streak, p['acc'], 0.2)
    return edge

def lighthouse(cv, p, hz, seed, x=None, sea_y=None):
    g = np.random.default_rng(seed + 21)
    x = W * (0.12 + 0.76 * g.random()) if x is None else x
    h = 60 + g.random() * 40
    def dr(d, s):
        d.polygon([((x - 7) * s, (hz + 2) * s), ((x - 4) * s, (hz - h) * s), ((x + 4) * s, (hz - h) * s), ((x + 7) * s, (hz + 2) * s)], fill=255)
        d.rectangle([(x - 6) * s, (hz - h - 8) * s, (x + 6) * s, (hz - h) * s], fill=255)
        d.polygon([((x - 7) * s, (hz - h - 8) * s), (x * s, (hz - h - 16) * s), ((x + 7) * s, (hz - h - 8) * s)], fill=255)
    m = silhouette(dr)
    cv.put(m, haze_col(p, 0.55))
    ly = hz - h - 4
    # lamp + beam rising to the sea ceiling (the lighthouses hold the sea up)
    cv.add(np.exp(-np.hypot(xx - x, yy - ly) / 4) * 1.2 + np.exp(-np.hypot(xx - x, yy - ly) / 26) * 0.4, p['key'])
    top = sea_y if sea_y is not None else 0
    span = np.clip((ly - yy) / max(1, ly - top), 0, 1)
    beam = np.exp(-np.abs(xx - x) / (3 + span * 26)) * ((yy < ly) & (yy > top - 4)) * (0.55 - span * 0.25)
    cv.add(beam, p['key'], 0.35)

def far_ridges(cv, p, hz, seed):
    for k, (amp, off, depth) in enumerate(((26, -10, 0.85), (34, 6, 0.6))):
        r = ridge(seed + 30 + k, 0, hz + off, amp)
        m = (yy > r[None, :]) & (yy < hz + 30)
        m = m.astype(np.float32) * np.clip((hz + 30 - yy) / 30, 0, 1) + (yy >= hz + 30) * 0
        cv.put(m, haze_col(p, depth), 0.9)

def seabed(cv, p, hz, seed):
    g = np.random.default_rng(seed + 40)
    t = np.clip((yy - hz) / (H - hz), 0, 1)
    ground = lerp(p['gf'], p['gn'], t ** 0.7)
    # sand ripples in perspective
    z = 1 / np.maximum(t, 0.02)
    warp = fbm(H, W, 3, 4, seed + 41) * 6
    rip = 0.5 + 0.5 * np.sin(z * 2.2 + warp + xx / W * 1.5)
    ground *= (0.86 + 0.16 * rip * np.clip(t * 3, 0, 1))[..., None]
    tex = fbm(H, W, 5, 8, seed + 42)
    ground *= (0.85 + 0.3 * tex)[..., None]
    # salt crust patches
    crackle = (fbm(H, W, 2, 90, seed + 44) > 0.52).astype(np.float32)
    salt = crackle * np.clip(t * 4, 0, 1) * (0.5 + 0.5 * fbm(H, W, 3, 5, seed + 43))
    ground = ground * (1 - salt[..., None] * 0.07) + A((236, 232, 222))[None, None] * salt[..., None] * 0.07
    m = (yy >= hz).astype(np.float32)
    cv.put(m, ground)
    # tide pools reflecting the sky
    for i in range(3 + int(g.random() * 3)):
        cx = g.random() * W; ty = 0.15 + g.random() * 0.7; cy = hz + ty * (H - hz)
        rx = 18 + 60 * ty * g.random() + 10; ry = rx * (0.12 + ty * 0.1)
        pm = np.clip(1 - ((xx - cx) / rx) ** 2 - ((yy - cy) / ry) ** 2, 0, 1) ** 0.3
        refl = A(p['hor']) * 0.8 + A(p['key']) * 0.2
        cv.put(pm, tuple(refl), 0.55)
        cv.add(np.exp(-np.abs(yy - (cy - ry * 0.7)) / 1.2) * (pm > 0), p['key'], 0.25)
    # stones with shadows
    for i in range(14):
        ty = g.random() ** 0.7; cy = hz + 4 + ty * (H - hz - 10); cx = g.random() * W
        r = 2 + ty * 16 * (0.5 + g.random())
        sh = np.exp(-(((xx - cx - r * 0.6) / (r * 1.6)) ** 2 + ((yy - cy - r * 0.25) / (r * 0.35)) ** 2))
        cv.img *= (1 - sh * 0.45)[..., None]
        st = np.clip(1 - ((xx - cx) / r) ** 2 - ((yy - cy + r * 0.3) / (r * 0.7)) ** 2, 0, 1) ** 0.4
        shade = np.clip(0.55 + (cx - xx) / (r * 2) * 0.4 + (cy - yy) / (r * 2) * 0.3, 0.3, 1.1)
        cv.put(st, A(p['prop']) * 0.6 + A(p['gn']) * 0.4 * shade[..., None] * 1.2)

def foreground(cv, p, hz, seed):
    g = np.random.default_rng(seed + 60)
    for side in (0, 1):
        for k in range(3):
            def dr(d, s, side=side, k=k):
                cx = (W * (0.0 + g.random() * 0.14)) if side == 0 else (W * (1.0 - g.random() * 0.14))
                cy = H * (0.99 - k * 0.03 - g.random() * 0.04); r = 34 + g.random() * 50 - k * 8
                n = 16; pts = []; ph = g.random() * 6
                for i in range(n):
                    a = math.pi + i / (n - 1) * math.pi
                    rr = r * (0.85 + 0.12 * math.sin(i * 1.7 + ph) + g.random() * 0.08)
                    pts.append(((cx + math.cos(a) * rr * 1.3) * s, (cy + math.sin(a) * rr * (0.6 + g.random() * 0.3)) * s))
                pts += [((cx + r * 1.3) * s, (H + 5) * s), ((cx - r * 1.3) * s, (H + 5) * s)]
                d.polygon(pts, fill=255)
            m = silhouette(dr, blur=1.2)
            tex = fbm(H, W, 4, 16, seed + 61 + side * 3 + k)
            lit = np.clip((W / 2 - xx) / W * (1 if side else -1) * 0, 0, 1)
            cv.put(m, A(p['prop'])[None, None] * (0.45 + 0.35 * tex[..., None]) * (0.8 + 0.1 * k))
    # drifting motes / spores rising
    for i in range(70):
        x = g.random() * W; y = g.random() * H; r = 0.6 + g.random() * 1.8
        cv.add(np.exp(-np.hypot(xx - x, yy - y) / r) * (g.random() * 0.5 + 0.2), p['acc'] if g.random() < 0.5 else p['key'], 0.5)

# ---------- faction landmarks ----------

def birds(cv, p, n, cx, cy, spread, seed, col=None, size=(3, 7)):
    g = np.random.default_rng(seed)
    def dr(d, s):
        for i in range(n):
            a = g.random() * math.tau; r = spread * math.sqrt(g.random())
            x, y = cx + math.cos(a) * r * 1.4, cy + math.sin(a) * r * 0.6
            w = size[0] + g.random() * (size[1] - size[0]); f = g.random() * 0.6
            d.line([((x - w) * s, (y - w * f) * s), (x * s, y * s), ((x + w) * s, (y - w * (0.6 - f)) * s)], fill=255, width=max(1, int(1.6 * s)))
    cv.put(silhouette(dr), col or tuple(A(p['prop']) * 0.8))

def L_salt_concord(cv, p, hz, seed):
    g = np.random.default_rng(seed + 100)
    # fortified salt-block wall with crenels, watch towers and pennants
    y0 = hz - 4; x0 = -20 + g.random() * 60; x1 = W * (0.55 + g.random() * 0.3)
    def dr(d, s):
        d.rectangle([x0 * s, (y0 - 28) * s, x1 * s, (y0 + 6) * s], fill=255)
        x = x0
        while x < x1:
            d.rectangle([x * s, (y0 - 36) * s, (x + 7) * s, (y0 - 27) * s], fill=255); x += 13
        for tx in (x0 + 30, x1 - 16):
            d.rectangle([(tx - 11) * s, (y0 - 66) * s, (tx + 11) * s, (y0 + 6) * s], fill=255)
            d.polygon([((tx - 14) * s, (y0 - 66) * s), (tx * s, (y0 - 86) * s), ((tx + 14) * s, (y0 - 66) * s)], fill=255)
            d.line([(tx * s, (y0 - 86) * s), (tx * s, (y0 - 104) * s)], fill=255, width=2 * s)
    m = silhouette(dr)
    tex = fbm(H, W, 3, 30, seed + 101)
    bricks = ((np.sin(yy * 0.9) > 0.92) | (np.sin(xx * 0.45 + (np.floor(yy / 7) % 2) * 1.5) > 0.96)).astype(np.float32)
    col = A(haze_col(p, 0.35))[None, None] * (0.9 + 0.2 * tex[..., None]) * (1 - bricks[..., None] * 0.18)
    cv.put(m, col)
    cv.add(m * np.clip((W * 0.3 - xx) / W + 0.4, 0, 1) * 0.0, p['key'])
    for tx in (x0 + 30, x1 - 16):  # pennants
        def pen(d, s, tx=tx):
            d.polygon([(tx * s, (y0 - 104) * s), ((tx + 22) * s, (y0 - 99) * s), (tx * s, (y0 - 94) * s)], fill=255)
        cv.put(silhouette(pen), (60, 92, 140))
        cv.add(np.exp(-np.hypot(xx - tx, yy - (y0 - 50)) / 3), p['key'], 0.8)  # arrow-slit lamp
    # salt cairns and road posts across the flat
    for i in range(6):
        ty = 0.08 + g.random() * 0.5; cy = hz + ty * (H - hz); cx = g.random() * W; hgt = 8 + ty * 50
        def cairn(d, s, cx=cx, cy=cy, hgt=hgt):
            for k in range(4):
                r = hgt * (0.32 - k * 0.06); yk = cy - k * hgt * 0.24
                d.ellipse([(cx - r) * s, (yk - r * 0.55) * s, (cx + r) * s, (yk + r * 0.25) * s], fill=255)
        cv.put(silhouette(cairn), (226, 220, 206))

def L_hadal_court(cv, p, hz, seed):
    g = np.random.default_rng(seed + 110)
    # trench walls closing in on both sides, with hanging bells on chains and bioluminescent dots
    for side in (0, 1):
        r = ridge(seed + 111 + side, 0, W * (0.2 + g.random() * 0.08), 26, 5)
        rows = np.arange(H)
        edge = np.interp(yy, rows, r[:H] if len(r) >= H else np.resize(r, H))
        m = (xx < edge) if side == 0 else (xx > W - edge)
        m = m.astype(np.float32) * np.clip((yy - 20) / 200, 0, 1)
        tex = fbm(H, W, 5, 12, seed + 112 + side)
        cv.put(m, A(p['prop'])[None, None] * (0.7 + 0.6 * tex[..., None]))
        rim = np.exp(-np.abs(xx - (edge if side == 0 else W - edge)) / 2) * m.clip(0, 1) * (yy > 40)
        cv.add(rim, p['acc'], 0.25)
    for i in range(3):
        bx = W * (0.15 + i * 0.35) + g.random() * 30; by = H * (0.18 + g.random() * 0.15); sc = 0.6 + g.random() * 0.6
        def bell(d, s, bx=bx, by=by, sc=sc):
            d.line([(bx * s, 0), (bx * s, by * s)], fill=255, width=max(1, int(2 * s * sc)))
            d.polygon([((bx - 6 * sc) * s, by * s), ((bx + 6 * sc) * s, by * s), ((bx + 14 * sc) * s, (by + 26 * sc) * s), ((bx - 14 * sc) * s, (by + 26 * sc) * s)], fill=255)
        cv.put(silhouette(bell), tuple(A(p['prop']) * 1.6))
        cv.add(np.exp(-np.hypot(xx - bx, yy - (by + 28 * sc)) / 5), p['acc'], 0.9)
    for i in range(90):
        x = g.random() * W; y = hz * 0.3 + g.random() * (H - hz * 0.3)
        cv.add(np.exp(-np.hypot(xx - x, yy - y) / (0.8 + g.random())), p['acc'], 0.5 + g.random() * 0.5)

def L_returning_tide(cv, p, hz, seed):
    g = np.random.default_rng(seed + 120)
    # the ribs of a wrecked hull and standing stones hung with kelp
    cx = W * (0.25 + g.random() * 0.5); base = hz + 10 + g.random() * 20; span = 150 + g.random() * 60
    def ribs(d, s):
        d.line([((cx - span / 2) * s, base * s), ((cx + span / 2) * s, (base - 6) * s)], fill=255, width=int(5 * s))
        for k in range(9):
            x = cx - span / 2 + k * span / 8; hgt = 50 + 40 * math.sin(k / 8 * math.pi)
            d.arc([(x - 26) * s, (base - hgt) * s, (x + 26) * s, (base + hgt) * s], 180, 260, fill=255, width=int(4 * s))
    cv.put(silhouette(ribs), haze_col(p, 0.4))
    for i in range(4):
        sx = g.random() * W; ty = 0.1 + g.random() * 0.5; sy = hz + ty * (H - hz); hg = 20 + ty * 90
        def stone(d, s, sx=sx, sy=sy, hg=hg):
            d.polygon([((sx - hg * 0.18) * s, sy * s), ((sx - hg * 0.12) * s, (sy - hg) * s), ((sx + hg * 0.1) * s, (sy - hg * 1.05) * s), ((sx + hg * 0.17) * s, sy * s)], fill=255)
            for k in range(4):
                kx = sx + (k - 1.5) * hg * 0.08
                d.line([(kx * s, (sy - hg * 0.95) * s), ((kx + math.sin(k) * 4) * s, (sy - hg * (0.3 + 0.15 * k)) * s)], fill=255, width=int(2 * s))
        cv.put(silhouette(stone), haze_col(p, 0.25 - ty * 0.2))
    # long kelp ribbons hanging from the sea above
    for i in range(7):
        x = g.random() * W; L = 60 + g.random() * 160; ph = g.random() * 6
        def kelp(d, s, x=x, L=L, ph=ph):
            pts = [((x + math.sin(ph + t / 18) * 8) * s, t * s) for t in range(0, int(L), 4)]
            d.line(pts, fill=255, width=int(3 * s))
        cv.put(silhouette(kelp, blur=0.6), (40, 70, 52), 0.8)

def L_salvage_compact(cv, p, hz, seed):
    g = np.random.default_rng(seed + 130)
    # beached rusted hulks, a salvage crane, smoke plumes and forge glow
    for k in range(2):
        hx = W * (0.1 + 0.55 * k + g.random() * 0.2); hy = hz + 6 + k * 14; L = 120 + g.random() * 80; tilt = (g.random() - 0.5) * 0.3
        def hull(d, s, hx=hx, hy=hy, L=L, tilt=tilt):
            pts = [(hx - L / 2, hy), (hx - L / 2 + 10, hy - 34 - L * tilt * 0.3), (hx + L / 2 - 20, hy - 30 + L * tilt * 0.3), (hx + L / 2, hy - 10), (hx + L / 2 - 10, hy)]
            d.polygon([(a * s, b * s) for a, b in pts], fill=255)
            d.rectangle([(hx - 12) * s, (hy - 62) * s, (hx + 6) * s, (hy - 30) * s], fill=255)
            d.line([((hx - 4) * s, (hy - 62) * s), ((hx - 4) * s, (hy - 90) * s)], fill=255, width=int(3 * s))
        m = silhouette(hull)
        tex = fbm(H, W, 4, 24, seed + 131 + k)
        cv.put(m, A(haze_col(p, 0.45 - k * 0.2))[None, None] * (0.7 + 0.6 * tex[..., None]) * A((1.05, 0.85, 0.75))[None, None])
        fx, fy = hx + 20, hy - 14
        cv.add(np.exp(-np.hypot(xx - fx, yy - fy) / 6) + np.exp(-np.hypot(xx - fx, yy - fy) / 40) * 0.3, p['acc'], 0.9)
    cx = W * (0.7 + g.random() * 0.2)
    def crane(d, s):
        d.line([(cx * s, (hz + 4) * s), (cx * s, (hz - 120) * s)], fill=255, width=int(4 * s))
        d.line([(cx * s, (hz - 118) * s), ((cx - 110) * s, (hz - 96) * s)], fill=255, width=int(3 * s))
        d.line([((cx - 100) * s, (hz - 98) * s), ((cx - 100) * s, (hz - 50) * s)], fill=255, width=max(1, int(1 * s)))
        for k in range(8):
            y = hz - k * 15; d.line([((cx - 5) * s, y * s), ((cx + 5) * s, (y - 15) * s)], fill=255, width=max(1, int(1.2 * s)))
    cv.put(silhouette(crane), haze_col(p, 0.5))
    for i in range(3):  # smoke
        sx = g.random() * W; base = hz - 10
        sm = fbm(H, W, 4, 5, seed + 140 + i)
        col_m = np.exp(-((xx - sx - (base - yy) * 0.35) / (10 + (base - yy).clip(0) * 0.3)) ** 2) * (yy < base) * np.clip(sm * 1.6 - 0.3, 0, 1)
        cv.put(col_m, (60, 48, 44), 0.6)

def L_reef_ascendant(cv, p, hz, seed):
    g = np.random.default_rng(seed + 150)
    # branching coral spires, fan corals and glowing polyp bulbs
    def branch(d, s, x, y, ang, L, w, depth):
        if depth == 0 or L < 4:
            d.ellipse([(x - w * 1.6) * s, (y - w * 1.6) * s, (x + w * 1.6) * s, (y + w * 1.6) * s], fill=255); return
        x2, y2 = x + math.cos(ang) * L, y + math.sin(ang) * L
        d.line([(x * s, y * s), (x2 * s, y2 * s)], fill=255, width=max(1, int(w * s)))
        for k in range(2):
            branch(d, s, x2, y2, ang + (g.random() - 0.5) * 1.1 + (k - 0.5) * 0.7, L * (0.6 + g.random() * 0.2), w * 0.7, depth - 1)
    for i in range(5):
        ty = g.random() * 0.45; cx = g.random() * W; cy = hz + ty * (H - hz) + 2; sc = 0.6 + ty * 1.8
        m = silhouette(lambda d, s: branch(d, s, cx, cy, -math.pi / 2 + (g.random() - 0.5) * 0.3, 40 * sc, 6 * sc, 5))
        cv.put(m, haze_col(p, 0.55 - ty))
    for i in range(3):
        fx = g.random() * W; fy = hz + 8 + g.random() * 40; r = 30 + g.random() * 30
        def fan(d, s, fx=fx, fy=fy, r=r):
            for k in range(13):
                a = math.pi + k / 12 * math.pi
                d.line([(fx * s, fy * s), ((fx + math.cos(a) * r) * s, (fy + math.sin(a) * r) * s)], fill=255, width=max(1, int(1.2 * s)))
            d.arc([(fx - r) * s, (fy - r) * s, (fx + r) * s, (fy + r) * s], 180, 360, fill=255, width=max(1, int(1.5 * s)))
        cv.put(silhouette(fan), (190, 110, 130), 0.7)
    for i in range(40):
        x = g.random() * W; y = hz - 20 + g.random() * (H - hz)
        cv.add(np.exp(-np.hypot(xx - x, yy - y) / (1 + g.random() * 2)), p['acc'], 0.6)

def L_lanternkeepers(cv, p, hz, seed):
    g = np.random.default_rng(seed + 160)
    # a stair-tower climbing toward the sea with lit windows; lantern poles marking the road
    tx = W * (0.15 + g.random() * 0.7); th = 230 + g.random() * 60
    def tower(d, s):
        d.polygon([((tx - 22) * s, (hz + 4) * s), ((tx - 13) * s, (hz - th) * s), ((tx + 13) * s, (hz - th) * s), ((tx + 22) * s, (hz + 4) * s)], fill=255)
        for k in range(10):  # spiral stair
            y = hz - k * th / 10; d.line([((tx - 24 + k % 2 * 40) * s, y * s), ((tx + 16 - k % 2 * 40) * s, (y - th / 10) * s)], fill=255, width=int(2 * s))
    cv.put(silhouette(tower), haze_col(p, 0.35))
    for k in range(7):
        wy = hz - 20 - k * th / 7.5; wx = tx + (g.random() - 0.5) * 12
        cv.add(np.exp(-np.hypot((xx - wx) * 1.6, yy - wy) / 2.5) + np.exp(-np.hypot(xx - wx, yy - wy) / 14) * 0.2, p['key'], 0.9)
    cv.add(np.exp(-np.hypot(xx - tx, yy - (hz - th - 6)) / 7) * 1.4 + np.exp(-np.hypot(xx - tx, yy - (hz - th)) / 50) * 0.35, p['key'])
    for i in range(7):
        ty = 0.05 + i / 7 * 0.6; py = hz + ty * (H - hz); px = W * 0.5 + (g.random() - 0.5) * W * (0.3 + ty); ph = 12 + ty * 70
        def pole(d, s, px=px, py=py, ph=ph):
            d.line([(px * s, py * s), (px * s, (py - ph) * s)], fill=255, width=max(1, int((1 + ty * 3) * s)))
            d.line([(px * s, (py - ph) * s), ((px + ph * 0.18) * s, (py - ph) * s)], fill=255, width=max(1, int((1 + ty * 2) * s)))
        cv.put(silhouette(pole), tuple(A(p['prop']) * 0.8))
        lx, ly = px + ph * 0.18, py - ph * 0.9
        cv.add(np.exp(-np.hypot(xx - lx, yy - ly) / (1.5 + ty * 4)) * 1.2 + np.exp(-np.hypot(xx - lx, yy - ly) / (10 + ty * 40)) * 0.3, p['key'])

def L_overcurrent(cv, p, hz, seed):
    g = np.random.default_rng(seed + 170)
    # vast pale shapes drifting overhead: fish and bell-jellies with lit undersides, droplets rising off the flat
    for i in range(4):
        fx = g.random() * W; fy = H * (0.18 + g.random() * 0.25); L = 40 + g.random() * 120; dirn = 1 if g.random() < 0.5 else -1
        def fish(d, s, fx=fx, fy=fy, L=L, dirn=dirn):
            d.ellipse([(fx - L / 2) * s, (fy - L * 0.16) * s, (fx + L / 2) * s, (fy + L * 0.16) * s], fill=255)
            tx = fx - dirn * L / 2
            d.polygon([(tx * s, fy * s), ((tx - dirn * L * 0.25) * s, (fy - L * 0.18) * s), ((tx - dirn * L * 0.25) * s, (fy + L * 0.18) * s)], fill=255)
        m = silhouette(fish, blur=0.8)
        depth = 0.7 - L / 300
        cv.put(m, haze_col(p, depth), 0.85)
        cv.add(m * np.clip((yy - fy) / (L * 0.16), 0, 1), p['acc'], 0.35)  # belly-light
    for i in range(3):
        jx = g.random() * W; jy = H * (0.2 + g.random() * 0.25); r = 10 + g.random() * 20
        def jelly(d, s, jx=jx, jy=jy, r=r):
            d.pieslice([(jx - r) * s, (jy - r) * s, (jx + r) * s, (jy + r) * s], 180, 360, fill=255)
            for k in range(6):
                x = jx - r * 0.8 + k * r * 0.32
                d.line([(x * s, jy * s), ((x + math.sin(k) * 4) * s, (jy + r * 2.5) * s)], fill=255, width=max(1, int(1 * s)))
        cv.put(silhouette(jelly), (200, 230, 245), 0.55)
        cv.add(np.exp(-np.hypot(xx - jx, yy - jy) / (r * 0.8)), p['acc'], 0.4)
    for i in range(60):
        x = g.random() * W; y = hz - 60 + g.random() * 120; L = 3 + g.random() * 8
        cv.add(np.exp(-np.abs(xx - x) / 0.7) * ((yy < y) & (yy > y - L)), (210, 240, 250), 0.5)

def L_gyre(cv, p, hz, seed):
    g = np.random.default_rng(seed + 180)
    # sea stacks and cliff with nests and lime streaks, wheeling flocks under the wrong sky
    for k in range(3):
        sx = g.random() * W; w = 22 + g.random() * 30; hg = 90 + g.random() * 120; depth = 0.65 - k * 0.2
        r = ridge(seed + 181 + k, 0, 0, 6, 3)
        def stack(d, s, sx=sx, w=w, hg=hg):
            gg = np.random.default_rng(int(sx * 7))
            left = [(sx - w * (1.25 - 0.55 * f) + gg.random() * 6, hz + 6 - hg * f) for f in np.linspace(0, 0.92, 9)]
            top = [(sx - w * 0.6, hz - hg * 0.98), (sx - w * 0.2, hz - hg * 1.03), (sx + w * 0.3, hz - hg * 0.99)]
            right = [(sx + w * (1.25 - 0.55 * f) - gg.random() * 6, hz + 6 - hg * f) for f in np.linspace(0.9, 0, 9)]
            pts = left + top + right
            d.polygon([(a * s, b * s) for a, b in pts], fill=255)
        m = silhouette(stack)
        strata = 0.88 + 0.12 * fbm(H, W, 5, 10, seed + 185 + k) + 0.05 * np.sin(yy * 0.35 + fbm(H, W, 3, 4, seed + 187 + k) * 14)
        lime = np.clip((fbm(H, W, 4, 14, seed + 186 + k) - 0.6) * 4, 0, 1) * np.clip(np.sin(xx * 0.5 + yy * 0.02) * 2, 0, 1)
        col = A(haze_col(p, depth))[None, None] * strata[..., None]
        col = col * (1 - lime[..., None] * 0.6) + A((236, 233, 225))[None, None] * lime[..., None] * 0.6 * (1 - depth)
        cv.put(m, col)
        birds(cv, p, 8, sx, hz - hg - 10, 22, seed + 190 + k, col=(236, 233, 225), size=(1.5, 3))
    for k in range(2):
        birds(cv, p, 22, W * (0.2 + 0.6 * g.random()), H * (0.24 + g.random() * 0.12), 60 + g.random() * 40, seed + 195 + k, col=(28, 31, 38), size=(4, 9))

def L_slough(cv, p, hz, seed):
    g = np.random.default_rng(seed + 150)
    # brine marsh at the trench edge: reed stands, shed skins hanging from reed frames, ground fog
    for k in range(2):  # skin frames: two posts, a crossbar and long pale skins hanging from it
        fx = W * (0.12 + 0.5 * k + g.random() * 0.25); fy = hz + 8 + k * 10; fw = 70 + g.random() * 40; fh = 80 + g.random() * 20
        def frame(d, s, fx=fx, fy=fy, fw=fw, fh=fh):
            d.line([(fx * s, fy * s), (fx * s, (fy - fh) * s)], fill=255, width=int(3 * s))
            d.line([((fx + fw) * s, fy * s), ((fx + fw) * s, (fy - fh) * s)], fill=255, width=int(3 * s))
            d.line([((fx - 6) * s, (fy - fh) * s), ((fx + fw + 6) * s, (fy - fh) * s)], fill=255, width=int(3 * s))
            for j in range(5):
                x = fx + 8 + j * (fw - 16) / 4; L = fh * (0.55 + 0.35 * g.random())
                d.polygon([((x - 4) * s, (fy - fh) * s), ((x + 4) * s, (fy - fh) * s), ((x + 2) * s, (fy - fh + L) * s), ((x - 1) * s, (fy - fh + L + 6) * s)], fill=255)
        m = silhouette(frame)
        cv.put(m, A(haze_col(p, 0.5 - k * 0.2)) * 1.0)
    for i in range(46):  # reeds
        rx = g.random() * W; rh = 30 + g.random() * 60; lean = (g.random() - 0.5) * 14; ry = hz + 4 + g.random() * 40
        def reed(d, s, rx=rx, rh=rh, lean=lean, ry=ry):
            d.line([(rx * s, ry * s), ((rx + lean) * s, (ry - rh) * s)], fill=255, width=max(1, int(1.6 * s)))
            d.ellipse([(rx + lean - 2) * s, (ry - rh - 9) * s, (rx + lean + 2) * s, (ry - rh + 2) * s], fill=255)
        cv.put(silhouette(reed), haze_col(p, 0.3 + 0.4 * (ry - hz) / 44))
    for i in range(3):  # fog
        fy = hz + 6 + i * 22 + g.random() * 8
        cv.add(np.exp(-np.abs(yy - fy) / 12) * (0.25 + 0.25 * fbm(H, W, 3, 60, seed + 160 + i)), p['hor'], 0.5)

LANDMARKS = {
    'salt_concord': L_salt_concord, 'hadal_court': L_hadal_court, 'returning_tide': L_returning_tide,
    'salvage_compact': L_salvage_compact, 'reef_ascendant': L_reef_ascendant, 'lanternkeepers': L_lanternkeepers,
    'overcurrent': L_overcurrent, 'gyre': L_gyre,
    'slough': L_slough,
    'hermitage': L_salvage_compact,  # wreck field on the Hulks; give it its own landmarks when the faction gets painted scenes
}

def scene(fid, seed):
    p = PAL.get(fid, PAL['salt_concord'])
    g = np.random.default_rng(seed)
    hz = H * (0.5 + g.random() * 0.06)
    cv = Canvas()
    sky(cv, p, hz, seed)
    sea_y = hanging_sea(cv, p, seed)
    # low light source behind the subject, off-centre
    sx, sy = W * (0.3 + g.random() * 0.4), hz - 30
    d = np.hypot(xx - sx, (yy - sy) * 1.4)
    cv.add(np.exp(-d / 120) * 0.45 + np.exp(-d / 30) * 0.3, p['key'])
    if fid != 'hadal_court':
        far_ridges(cv, p, hz, seed)
    lighthouse(cv, p, hz, seed, sea_y=float(np.interp(W / 2, np.arange(W), sea_y)))
    seabed(cv, p, hz, seed)
    LANDMARKS.get(fid, L_salt_concord)(cv, p, hz, seed)
    # atmospheric haze band on the horizon
    cv.img = cv.img * 1 + (A(p['hor'])[None, None] - cv.img) * (np.exp(-np.abs(yy - hz) / 14) * 0.35)[..., None]
    foreground(cv, p, hz, seed)
    return cv.img, A(p['key']), hz, (sx, sy)

def paint(arr):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    im = im.filter(ImageFilter.ModeFilter(5)).filter(ImageFilter.SMOOTH_MORE)
    return np.asarray(im, np.float32)

if __name__ == '__main__':
    import sys
    out = sys.argv[1]
    tiles = []
    for fid in PAL:
        for s in (3, 17):
            img, *_ = scene(fid, s)
            tiles.append(Image.fromarray(np.clip(paint(img), 0, 255).astype(np.uint8)).resize((256, 384)))
    sheet = Image.new('RGB', (256 * 4, 384 * 4))
    for i, t in enumerate(tiles): sheet.paste(t, ((i % 4) * 256, (i // 4) * 384))
    sheet.save(out, quality=88)

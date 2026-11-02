"""Interim card art: each unit's 3D model render, hero-framed on a painted faction backdrop.
Stands in until the ChatGPT paintings land at the same path (content/cards/<id>.webp, 2:3, 512x768).
Run: python3 tools/cardkit/interim_art.py <ref_render_dir> [unitId|factionId ...]   (dir holds <unitId>_rgba.png from spritegen refrender.py)"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageFilter
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
OUT = os.path.join(ROOT, 'content', 'cards')
W, H = 512, 768
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

# sky top, sky horizon, ground near, ground far, key light, accent glow
MOODS = {
    'salt_concord':    [(54, 62, 80), (206, 192, 170), (196, 190, 176), (150, 146, 136), (255, 226, 180), (120, 160, 210)],
    'hadal_court':     [(3, 6, 16), (18, 44, 66), (14, 18, 30), (22, 34, 50), (90, 230, 210), (63, 214, 196)],
    'returning_tide':  [(22, 34, 32), (112, 132, 120), (44, 60, 52), (80, 98, 88), (210, 226, 210), (120, 200, 160)],
    'salvage_compact': [(34, 20, 16), (196, 112, 60), (72, 46, 32), (120, 78, 52), (255, 190, 120), (230, 120, 60)],
    'reef_ascendant':  [(36, 16, 40), (222, 128, 118), (88, 46, 58), (140, 84, 92), (255, 200, 180), (240, 130, 160)],
    'lanternkeepers':  [(10, 12, 22), (70, 66, 86), (30, 30, 36), (50, 48, 58), (255, 200, 110), (227, 176, 75)],
    # the sea hanging overhead: abyss-blue sky, cerulean horizon, belly-light cyan from below
    'overcurrent':     [(11, 23, 48), (112, 178, 214), (24, 44, 66), (52, 86, 110), (150, 236, 240), (95, 224, 230)],
    # cold low wind-light under a wrong-coloured (sulphur-green) sky over slate cliffs
    'gyre':            [(46, 52, 62), (172, 168, 128), (70, 76, 84), (112, 116, 118), (240, 214, 160), (232, 137, 47)],
}

def fbm(h, w, octaves, base, seed):
    g = np.random.default_rng(seed); acc = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        n = base * 2 ** o
        img = Image.fromarray((g.random((n, n)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += amp * np.asarray(img, np.float32) / 255; tot += amp; amp *= 0.5
    return acc / tot

def lerp(a, b, t): return np.asarray(a, np.float32)[None, None] * (1 - t[..., None]) + np.asarray(b, np.float32)[None, None] * t[..., None]

def backdrop(fid, seed):
    st, sh, gn, gf, key, acc = MOODS.get(fid, MOODS['salt_concord'])
    hz = H * 0.56 + (seed % 7) * 3
    sky_t = np.clip(yy / hz, 0, 1) ** 1.6
    sky = lerp(st, sh, sky_t)
    cl = fbm(H, W, 5, 3, seed); cl2 = fbm(H, W, 4, 8, seed + 1)
    sky *= (0.82 + 0.35 * (cl * 0.7 + cl2 * 0.3))[..., None]
    # low sun / light source behind the figure, off-centre
    sx = W * (0.32 + (seed % 5) * 0.09); sy = hz - 40
    d = np.hypot(xx - sx, (yy - sy) * 1.4)
    sky += np.asarray(key, np.float32) * (np.exp(-d / 110) * 0.55 + np.exp(-d / 30) * 0.35)[..., None]
    # lighthouse beam
    ang = math.radians(-18 + (seed % 9) * 4)
    bx, by = W * 0.86, hz - 70
    vx, vy = xx - bx, yy - by
    along = vx * -math.cos(ang) + vy * math.sin(ang)
    perp = np.abs(vx * math.sin(ang) + vy * math.cos(ang))
    beam = np.clip(along / 400, 0, 1) * np.exp(-perp / (8 + along.clip(0) * 0.12)) * (yy < hz)
    sky += np.asarray(acc, np.float32) * beam[..., None] * 0.5
    ground_t = np.clip((yy - hz) / (H - hz), 0, 1)
    gr = lerp(gf, gn, ground_t ** 0.7)
    gtex = fbm(H, W, 5, 6, seed + 2)
    streak = fbm(H, W // 8, 3, 4, seed + 3); streak = np.asarray(Image.fromarray((streak * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
    gr *= (0.8 + 0.3 * gtex * (0.5 + 0.5 * streak))[..., None]
    img = np.where((yy < hz)[..., None], sky, gr)
    # haze at the horizon
    haze = np.exp(-np.abs(yy - hz) / 26)
    img = img * (1 - haze[..., None] * 0.55) + np.asarray(sh, np.float32) * haze[..., None] * 0.55
    # distant silhouette: lighthouse tower on a spit
    tower = (np.abs(xx - bx) < (6 + (yy - (hz - 80)) * 0.06)) & (yy > hz - 80) & (yy < hz + 2)
    img = np.where(tower[..., None], img * 0.45, img)
    return img, (sx, sy), np.asarray(key, np.float32), hz

def paint(arr, r=2):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.ModeFilter(3)).filter(ImageFilter.SMOOTH_MORE), np.float32)

def compose(uid, fid, fig, seed, hero):
    bg, (sx, sy), key, hz = backdrop(fid, seed)
    bg = paint(bg)
    fg = fig.crop(fig.getbbox())
    # hero framing: the figure's head near the top, knees under the rules panel (panel starts ~60% down)
    tall = fg.height / fg.width > 1.15
    target_h = H * (0.98 if tall else 0.62)
    s = target_h / fg.height
    if fg.width * s > W * 0.98: s = W * 0.98 / fg.width
    fg = fg.resize((int(fg.width * s), int(fg.height * s)), Image.LANCZOS)
    top = int(H * 0.06) if tall else max(int(H * 0.06), int(H * 0.66) - fg.height)
    left = (W - fg.width) // 2
    canvas = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert('RGBA')
    # ground shadow + back glow
    a = np.asarray(fg, np.float32)[..., 3] / 255
    glow = Image.new('L', (W, H), 0); glow.paste(Image.fromarray((a * 255).astype(np.uint8)), (left, top))
    g = np.asarray(glow.filter(ImageFilter.GaussianBlur(28)), np.float32) / 255
    base = np.asarray(canvas, np.float32)[..., :3]
    base = base + key[None, None] * g[..., None] * 0.35
    feet_y = top + fg.height
    sh = np.exp(-(((xx - W / 2) / (fg.width * 0.45)) ** 2 + ((yy - feet_y + 8) / 22) ** 2))
    base *= (1 - sh * 0.55)[..., None]
    canvas = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert('RGBA')
    # grade the figure toward the scene light, rim from the light side
    fa = np.asarray(fg, np.float32)
    rgb = fa[..., :3] * 0.88 + key[None, None] * 0.12 * (fa[..., :3] / 255)
    edge = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
    rim = np.clip(a - edge, 0, 1) * 2.5
    rgb = rgb + key[None, None] * rim[..., None] * 0.6
    fg = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), fa[..., 3:]]).astype(np.uint8), 'RGBA')
    canvas.alpha_composite(fg, (left, top))
    out = np.asarray(canvas, np.float32)[..., :3]
    # atmosphere + vignette
    vig = np.hypot((xx - W / 2) / W, (yy - H * 0.42) / H) * 1.5
    out *= np.clip(1.08 - vig ** 2 * 0.9, 0.35, 1)[..., None]
    gr = np.random.default_rng(seed).normal(0, 3, out.shape)
    Image.fromarray(np.clip(out + gr, 0, 255).astype(np.uint8)).save(os.path.join(OUT, f'{uid}.webp'), quality=86, method=6)

if __name__ == '__main__':
    REF = sys.argv[1]
    units = json.load(open(os.path.join(ROOT, 'content', 'units.json')))
    only = sys.argv[2:]
    n = 0
    for i, (uid, u) in enumerate(units.items()):
        if only and uid not in only and u.get('faction') not in only: continue
        p = os.path.join(REF, f'{uid}_rgba.png')
        if not os.path.exists(p): continue
        compose(uid, u.get('faction', ''), Image.open(p).convert('RGBA'), i * 7 + 3, u.get('hero'))
        n += 1
    print('wrote', n)

"""Interim card art: each unit's 3D model render, hero-framed on a detailed painted faction scene (scenes.py).
Stands in until the ChatGPT paintings land at the same path (content/cards/<id>.webp, 2:3, 512x768).
Run: python3 tools/cardkit/interim_art.py <ref_render_dir> [unitId|factionId ...]   (dir holds <unitId>_rgba.png from spritegen refrender.py)"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageFilter
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
OUT = os.path.join(ROOT, 'content', 'cards')
W, H = 512, 768
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

sys.path.insert(0, os.path.dirname(__file__))
from scenes import scene, paint, PAL  # detailed per-faction painted scenes

def backdrop(fid, seed):
    img, key, hz, sun = scene(fid, seed)
    return img, sun, key, hz

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

"""Interim card art for spells and equipment: a drawn subject (tools/cardkit/motifs/<id>.svg, 512x512, transparent)
lit and set into the same painted faction backdrop as the unit interim art, so every card shows its own picture.
Stands in until painted art lands at content/cards/<id>.webp (2:3, 512x768).
Run: node tools/cardkit/motif_raster.cjs <png_dir> && python3 tools/cardkit/motif_art.py <png_dir> [cardId|factionId ...]"""
import os, sys, json
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from interim_art import backdrop, paint, MOODS, W, H, xx, yy, OUT, ROOT

def compose(cid, fid, motif, seed, kind):
    bg, _, key, hz = backdrop(fid, seed)
    bg = paint(bg)
    acc = np.asarray(MOODS.get(fid, MOODS['salt_concord'])[5], np.float32)
    fg = motif.crop(motif.getbbox())
    # the subject sits in the open art window above the rules panel (which covers the lower ~40%)
    box_w, box_h = W * 0.84, H * 0.5
    s = min(box_w / fg.width, box_h / fg.height)
    fg = fg.resize((max(1, int(fg.width * s)), max(1, int(fg.height * s))), Image.LANCZOS)
    cx, cy = W // 2, int(H * 0.33)
    left, top = cx - fg.width // 2, cy - fg.height // 2
    a = np.asarray(fg, np.float32)[..., 3] / 255
    mask = Image.new('L', (W, H), 0); mask.paste(Image.fromarray((a * 255).astype(np.uint8)), (left, top))
    base = bg.copy()
    # spells radiate their own light; equipment is lit like an object laid on the ground
    halo = np.asarray(mask.filter(ImageFilter.GaussianBlur(40)), np.float32) / 255
    d = np.hypot((xx - cx) / (fg.width * 0.7 + 1), (yy - cy) / (fg.height * 0.7 + 1))
    if kind == 'spell':
        base += acc[None, None] * (halo * 0.55 + np.exp(-d * 1.6) * 0.35)[..., None]
    else:
        base += key[None, None] * (halo * 0.3)[..., None]
        sh = np.exp(-(((xx - cx) / (fg.width * 0.42 + 1)) ** 2 + ((yy - (top + fg.height + 18)) / 16) ** 2))
        base *= (1 - sh * 0.5)[..., None]
    canvas = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert('RGBA')
    # soften the vector edges into paint, grade toward the scene light, rim on the light side
    fa = np.asarray(fg.filter(ImageFilter.ModeFilter(3)).filter(ImageFilter.SMOOTH), np.float32)
    rgb = fa[..., :3] * 0.86 + key[None, None] * 0.14 * (fa[..., :3] / 255)
    edge = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
    rgb += (acc if kind == 'spell' else key)[None, None] * (np.clip(a - edge, 0, 1) * 2.2)[..., None] * 0.55
    tex = np.asarray(Image.fromarray((np.random.default_rng(seed).random((fg.height // 3 + 1, fg.width // 3 + 1)) * 255).astype(np.uint8))
                     .resize((fg.width, fg.height), Image.BICUBIC), np.float32) / 255
    rgb *= (0.9 + 0.2 * tex)[..., None]
    fg = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), fa[..., 3:]]).astype(np.uint8), 'RGBA')
    canvas.alpha_composite(fg, (left, top))
    out = np.asarray(canvas, np.float32)[..., :3]
    vig = np.hypot((xx - W / 2) / W, (yy - H * 0.38) / H) * 1.5
    out *= np.clip(1.08 - vig ** 2 * 0.9, 0.35, 1)[..., None]
    gr = np.random.default_rng(seed).normal(0, 3, out.shape)
    Image.fromarray(np.clip(out + gr, 0, 255).astype(np.uint8)).save(os.path.join(OUT, f'{cid}.webp'), quality=86, method=6)

if __name__ == '__main__':
    src = sys.argv[1]; only = sys.argv[2:]; n = 0
    for kind, fn in (('spell', 'spells.json'), ('equipment', 'equipment.json')):
        for i, (cid, d) in enumerate(json.load(open(os.path.join(ROOT, 'content', fn))).items()):
            if only and cid not in only and d.get('faction') not in only: continue
            p = os.path.join(src, f'{cid}.png')
            if not os.path.exists(p): continue
            compose(cid, d.get('faction', ''), Image.open(p).convert('RGBA'), i * 11 + (5 if kind == 'spell' else 9), kind)
            n += 1
    print('wrote', n)

"""Render a unit's still and write preview images.

usage: python preview.py <unit_module> [outdir]
Writes <unit>.png (96x112), <unit>_x4.png (nearest-neighbour enlargement) and
<unit>_board.png (the sprite standing on a painted salt-flat tile at board scale and 2x).
"""
import sys, os, time, importlib
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'units'))
from render import render, Camera, Look


def tile_image(w=128, h=64, top=(232, 228, 216)):
    """Quick painted salt-flat diamond for context."""
    rng = np.random.default_rng(3)
    img = Image.new('RGBA', (w, h + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w // 2
    d.polygon([(0, h // 2), (cx, h), (cx, h + 24), (0, h // 2 + 24)], fill=(150, 146, 136, 255))
    d.polygon([(cx, h), (w, h // 2), (w, h // 2 + 24), (cx, h + 24)], fill=(118, 114, 108, 255))
    d.polygon([(0, h // 2), (cx, 0), (w, h // 2), (cx, h)], fill=top + (255,))
    a = np.array(img).astype(np.float64)
    noise = rng.normal(0, 4, a.shape[:2])
    a[..., :3] += noise[..., None] * (a[..., 3:4] > 0)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def board(sprite, scale=1):
    W, H = 128 * 3, 170
    bg = Image.new('RGBA', (W, H), (40, 44, 52, 255))
    t = tile_image()
    for i, ox in enumerate((0, 128, 256)):
        bg.alpha_composite(t, (ox, H - 88))
    spr = Image.fromarray(sprite)
    # tile centre is at (64, 32) of the tile; sprite anchor (48,104)
    bg.alpha_composite(spr, (128 + 64 - 48, H - 88 + 32 - 104))
    if scale != 1:
        bg = bg.resize((W * scale, H * scale), Image.NEAREST)
    return bg


def main():
    mod = importlib.import_module(sys.argv[1])
    out = sys.argv[2] if len(sys.argv) > 2 else '.'
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    P = mod.neutral_pose()
    scene = mod.build(P)
    img = render(scene, getattr(mod, 'CAMERA', Camera()), getattr(mod, 'LOOK', Look()))
    print('render %.1fs' % (time.time() - t0))
    name = mod.UNIT_ID
    Image.fromarray(img).save(os.path.join(out, name + '.png'))
    big = Image.fromarray(img).resize((96 * 4, 112 * 4), Image.NEAREST)
    bgc = Image.new('RGBA', big.size, (128, 128, 128, 255))
    bgc.alpha_composite(big)
    bgc.save(os.path.join(out, name + '_x4.png'))
    b1 = board(img)
    b2 = board(img, 2)
    sheet = Image.new('RGBA', (b2.width, b1.height + b2.height + 8), (20, 22, 26, 255))
    sheet.paste(b1, (0, 0)); sheet.paste(b2, (0, b1.height + 8))
    sheet.save(os.path.join(out, name + '_board.png'))


if __name__ == '__main__':
    main()

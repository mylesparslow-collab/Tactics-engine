"""Alternative finishing styles over the same 3D sculpts (for art-direction comparisons).

    python3 styles.py <unitId> <outdir>   -> one still per style + a side-by-side comparison

Styles:
  painted   current look (soft painterly, Kuwahara, soft alpha)
  pixel     crisp 96x112 pixel art: hard light bands, ~28-colour palette, hard alpha, 1px selective outline
  chunky    classic chunky pixel art: rendered at 48x56 with ~16 colours and an outline, shown 2x
  ink       cel-shaded comic: two hard light bands, saturated flats, thick dark ink outline
  smooth    clean pre-rendered 3D look (no paint filter), like late-90s rendered sprites
"""
import os, sys, importlib, dataclasses
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'units'))
from render import render, Camera, Look


def _outline(rgb, mask, strength=0.35, color=None, thick=1):
    """Selective outline: empty pixels touching the figure take a darkened copy of the touching colour."""
    out = rgb.copy()
    m = mask.copy()
    for _ in range(thick):
        nb_col = np.zeros_like(out)
        nb_cnt = np.zeros(m.shape)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sm = np.roll(m, (dy, dx), (0, 1))
            sc = np.roll(out, (dy, dx), (0, 1))
            nb_col += sc * sm[..., None]
            nb_cnt += sm
        edge = (~m) & (nb_cnt > 0)
        if color is None:
            c = nb_col / np.maximum(nb_cnt, 1)[..., None] * strength
        else:
            c = np.broadcast_to(np.array(color, dtype=np.float64), out.shape)
        out[edge] = c[edge]
        m = m | edge
    return out, m


def _quantize(rgb, mask, n):
    pix = (rgb[mask] * 255).astype(np.uint8)
    if len(pix) == 0:
        return rgb
    im = Image.fromarray(pix.reshape(1, -1, 3), 'RGB')
    q = im.quantize(colors=n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert('RGB')
    out = rgb.copy()
    out[mask] = np.array(q).reshape(-1, 3) / 255.0
    return out


def _pixel_shadow(h, w, ax, ay, rx, ry, a=0.38):
    yy, xx = np.mgrid[0:h, 0:w]
    e = ((xx + 0.5 - ax) / rx) ** 2 + ((yy + 0.5 - ay) / ry) ** 2
    return (e < 1).astype(np.float64) * a


def finish_pixel(img, n_colors, outline_strength=0.3, shadow=(24, 7), thresh=0.55):
    f = img.astype(np.float64) / 255.0
    rgb, A = f[..., :3], f[..., 3]
    mask = A > thresh
    rgb = _quantize(rgb, mask, n_colors)
    rgb, m2 = _outline(rgb, mask, outline_strength)
    h, w = mask.shape
    ax, ay = w / 2, h * (104 / 112)
    sh = _pixel_shadow(h, w, ax, ay, shadow[0] * w / 96, shadow[1] * h / 112)
    alpha = np.where(m2, 1.0, sh)
    rgb = np.where(m2[..., None], rgb, np.array([0.08, 0.09, 0.12]))
    return (np.dstack([rgb, alpha]) * 255 + 0.5).astype(np.uint8)


def styled(mod, P, style):
    look0 = getattr(mod, 'LOOK', Look())
    cam0 = getattr(mod, 'CAMERA', Camera())
    sc = mod.build(P)
    if style == 'painted':
        return render(sc, cam0, look0)
    if style == 'smooth':
        lk = dataclasses.replace(look0, kuwahara=0, bands=0.0, contrast=0.35, edge_dark=0.25, sharpen=0.5,
                                 key_int=1.45, sky_int=0.26)
        for m in sc.materials.values():
            m.brush = m.brush * 0.3
        return render(sc, cam0, lk)
    if style == 'pixel':
        lk = dataclasses.replace(look0, kuwahara=0, bands=0.85, ground_shadow=0.0, edge_dark=0.0,
                                 sharpen=0.0, contrast=0.35)
        return finish_pixel(render(sc, cam0, lk), 28, 0.32)
    if style == 'chunky':
        cam = dataclasses.replace(cam0, width=48, height=56, anchor=(24, 52), ppm=cam0.ppm / 2, ss=8)
        lk = dataclasses.replace(look0, kuwahara=0, bands=1.0, ground_shadow=0.0, edge_dark=0.0,
                                 sharpen=0.0, contrast=0.4)
        small = finish_pixel(render(sc, cam, lk), 16, 0.3, shadow=(22, 6), thresh=0.28)
        return np.array(Image.fromarray(small).resize((96, 112), Image.NEAREST))
    if style == 'ink':
        lk = dataclasses.replace(look0, kuwahara=0, bands=1.0, ground_shadow=0.0, edge_dark=0.0,
                                 sharpen=0.2, contrast=0.2, sky_int=0.45)
        img = render(sc, cam0, lk)
        f = img.astype(np.float64) / 255.0
        rgb, A = f[..., :3], f[..., 3]
        mask = A > 0.5
        # saturate the flats a little
        g = rgb.mean(-1, keepdims=True)
        rgb = np.clip(g + (rgb - g) * 1.25, 0, 1)
        rgb = _quantize(rgb, mask, 24)
        # interior ink lines where colour changes sharply
        lum = rgb @ np.array([0.3, 0.59, 0.11])
        gx = np.abs(np.roll(lum, -1, 1) - lum) + np.abs(np.roll(lum, -1, 0) - lum)
        ink = (gx > 0.22) & mask
        rgb[ink] = rgb[ink] * 0.35
        rgb, m2 = _outline(rgb, mask, color=(0.06, 0.06, 0.09))
        h, w = mask.shape
        sh = _pixel_shadow(h, w, 48, 104, 24, 7, 0.3)
        alpha = np.where(m2, 1.0, sh)
        rgb = np.where(m2[..., None], rgb, np.array([0.08, 0.09, 0.12]))
        return (np.dstack([rgb, alpha]) * 255 + 0.5).astype(np.uint8)
    raise ValueError(style)


STYLES = ['painted', 'pixel', 'chunky', 'ink', 'smooth']
LABELS = {'painted': 'A  Painted (current)', 'pixel': 'B  Pixel art (crisp, 28 colours)',
          'chunky': 'C  Chunky pixel (48x56, 16 colours)', 'ink': 'D  Cel-shaded ink',
          'smooth': 'E  Smooth pre-rendered 3D'}


def main():
    unit, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    mod = importlib.import_module(unit)
    P = mod.neutral_pose()
    imgs = {}
    for s in STYLES:
        imgs[s] = styled(mod, P, s)
        Image.fromarray(imgs[s]).save(os.path.join(out, f'{unit}_{s}.png'))
    # comparison: each style at 3x on grey, and 1x on a dark board strip
    S = 3
    cw = 96 * S + 20
    W, H = cw * len(STYLES) + 20, 112 * S + 200
    sheet = Image.new('RGBA', (W, H), (26, 28, 34, 255))
    d = ImageDraw.Draw(sheet)
    for k, s in enumerate(STYLES):
        x = 20 + k * cw
        d.text((x, 10), LABELS[s], fill=(235, 235, 235, 255))
        bg = Image.new('RGBA', (96 * S, 112 * S), (112, 114, 120, 255))
        bg.alpha_composite(Image.fromarray(imgs[s]).resize((96 * S, 112 * S), Image.NEAREST))
        sheet.paste(bg, (x, 28))
        tile = Image.new('RGBA', (96, 112), (205, 200, 188, 255))
        tile.alpha_composite(Image.fromarray(imgs[s]))
        sheet.paste(tile, (x, 28 + 112 * S + 20))
        tile2 = Image.new('RGBA', (96, 112), (44, 48, 56, 255))
        tile2.alpha_composite(Image.fromarray(imgs[s]))
        sheet.paste(tile2, (x + 110, 28 + 112 * S + 20))
        d.text((x, 28 + 112 * S + 6), 'actual size on light / dark ground', fill=(180, 180, 180, 255))
    sheet.save(os.path.join(out, f'{unit}_styles.png'))
    print(os.path.join(out, f'{unit}_styles.png'))


if __name__ == '__main__':
    main()

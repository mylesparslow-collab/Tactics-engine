"""Render a unit's full sprite sheet + manifest + still.

usage: python sheet.py <unit_module> <outdir> [--jobs N] [--rows idle,move]
Writes <unit>.png (sheet, one animation per row), <unit>.json (manifest),
<unit>_still.png (idle frame 0), and <unit>_preview.gif (all rows, 3x) for review.
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import sys, json, time, argparse, importlib, dataclasses, copy
from multiprocessing import Pool
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'units'))
from render import render, Camera, Look
import kit.fx as fxkit

_mod = None


def _frames(mod, tw):
    fr = mod.frames()
    if tw:
        from tween import tween_all
        fr, _ = tween_all(fr, mod.ROWS)
    return fr


def _rows(mod, tw):
    if tw:
        from tween import tween_all
        return tween_all(mod.frames(), mod.ROWS)[1]
    return mod.ROWS


def _job(args):
    modname, row, i, tw, style = args
    mod = importlib.import_module(modname)
    P, over = _frames(mod, tw)[row][i]
    cam = getattr(mod, 'CAMERA', Camera())
    em = [(pr, s, *fxkit.project(cam, c)) for pr, s, c in fxkit.split(mod.build(copy.deepcopy(P)).parts)[1]]
    if style != 'painted':
        from styles import styled
        return row, i, styled(mod, P, style, over), em
    look = dataclasses.replace(getattr(mod, 'LOOK', Look()), **over)
    return row, i, render(mod.build(P), cam, look), em


def fx_tracks(rows, fr, got_fx):
    """Per-frame emitter tracks for the manifest: [{preset, tracks: {row: [[x, y, strength] | 0, ...]}}].
    The k-th emitter of a preset in a frame belongs to track `preset#k`."""
    tracks = {}
    for name, *_ in rows:
        n = len(fr[name])
        for i in range(n):
            seen = {}
            for pr, s, x, y in got_fx[(name, i)]:
                k = seen.get(pr, 0); seen[pr] = k + 1
                t = tracks.setdefault((pr, k), {})
                t.setdefault(name, [0] * n)[i] = [round(x, 1), round(y, 1), round(s, 2)]
    return [dict(preset=pr, tracks=t) for (pr, k), t in sorted(tracks.items())]


def quantize(img, colors=192):
    """Palette-quantise RGBA (spec asks for palette PNGs) while keeping soft alpha edges."""
    im = Image.fromarray(img)
    return im.quantize(colors=colors, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('unit'); ap.add_argument('out')
    ap.add_argument('--jobs', type=int, default=os.cpu_count())
    ap.add_argument('--rows', default='')
    ap.add_argument('--tween', action='store_true', help='insert eased in-between frames')
    ap.add_argument('--style', default='painted', help='painted | pixel | chunky | ink | smooth (see styles.py)')
    a = ap.parse_args()
    mod = importlib.import_module(a.unit)
    rows = [r for r in _rows(mod, a.tween) if not a.rows or r[0] in a.rows.split(',')]
    fr = _frames(mod, a.tween)
    jobs = [(a.unit, r[0], i, a.tween, a.style) for r in rows for i in range(len(fr[r[0]]))]
    t0 = time.time()
    with Pool(a.jobs) as pool:
        res = pool.map(_job, jobs)
    print('rendered %d frames in %.0fs' % (len(res), time.time() - t0))
    got = {(r, i): img for r, i, img, _ in res}
    got_fx = {(r, i): em for r, i, _, em in res}
    fw, fh = 96, 112
    ncol = max(len(fr[r[0]]) for r in rows)
    sheet = np.zeros((fh * len(rows), fw * ncol, 4), np.uint8)
    manifest = dict(frameWidth=fw, frameHeight=fh, anchor=[48, 104], facing='lower-right', animations={})
    for ri, (name, fps, loop, extra) in enumerate(rows):
        n = len(fr[name])
        for i in range(n):
            sheet[ri * fh:(ri + 1) * fh, i * fw:(i + 1) * fw] = got[(name, i)]
        manifest['animations'][name] = dict(row=ri, frames=n, fps=fps, loop=loop, **extra)
    fx = fx_tracks(rows, fr, got_fx)
    if fx:
        manifest['fx'] = fx   # live smoke / ink / mist emitters, drawn by src/render/fx.ts
    os.makedirs(a.out, exist_ok=True)
    uid = mod.UNIT_ID
    Image.fromarray(sheet).save(os.path.join(a.out, uid + '_rgba.png'))
    quantize(sheet).save(os.path.join(a.out, uid + '.png'), optimize=True)
    Image.fromarray(got[(rows[0][0], 0)]).save(os.path.join(a.out, uid + '_still.png'))
    rv = Image.new('RGBA', (sheet.shape[1], sheet.shape[0]), (104, 106, 112, 255))
    rv.alpha_composite(Image.fromarray(sheet))
    rv.resize((rv.width * 2, rv.height * 2), Image.NEAREST).save(os.path.join(a.out, uid + '_review.png'))
    with open(os.path.join(a.out, uid + '.json'), 'w') as f:
        json.dump(manifest, f, indent=1)
    # review gif: every row played in sequence on grey, 3x
    gif = []
    for name, fps, loop, extra in rows:
        n = len(fr[name])
        reps = 3 if loop else 1
        seq = list(range(n)) * reps
        if extra.get('holdLast'):
            seq += [n - 1] * 4
        for i in seq:
            bg = Image.new('RGBA', (fw, fh), (96, 98, 104, 255))
            bg.alpha_composite(Image.fromarray(got[(name, i)]))
            gif.append((bg.resize((fw * 3, fh * 3), Image.NEAREST), int(1000 / fps)))
    gif[0][0].save(os.path.join(a.out, uid + '_preview.gif'), save_all=True,
                   append_images=[g for g, _ in gif[1:]], duration=[d for _, d in gif], loop=0)


if __name__ == '__main__':
    main()

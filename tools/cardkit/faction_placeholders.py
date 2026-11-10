"""Procedural interim card art for a faction that has no model renders or hand-drawn motifs yet.
Draws a simple figure (units: a crab-in-a-shell silhouette; spells: a radiant burst; equipment: a plate) with PIL,
then sets it into the faction's painted scene exactly like interim_art.py / motif_art.py do, writing
content/cards/<id>.webp (2:3, 512x768). Real art (ChatGPT paintings, or interim_art.py once sprites exist) overwrites
the same path later. Tokens and structures get no card.
Run: python3 tools/cardkit/faction_placeholders.py <factionId> [cardId ...] [--force]   (skips cards that already have a .webp unless --force)"""
import os, sys, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import interim_art, motif_art
from interim_art import ROOT, OUT, PAL

S = 512  # figure canvas, supersampled 2x while drawing

def _h(s):  # stable small int per id
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)

def _mix(a, b, t): return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))

def crab(cid, d, p):
    """A hermit crab in whatever it lives in, shape picked from the id/name; size from cost."""
    k = 2
    im = Image.new('RGBA', (S * k, S * k), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    violet, rust = (123, 79, 143), (217, 130, 43)
    r = _h(cid); name = (d.get('name', '') + cid).lower()
    sc = 0.55 + min(d.get('cost', 40), 90) / 90 * 0.45
    cx, base = S * k // 2, int(S * k * 0.9)
    def P(x, y): return (cx + x * sc * k, base - y * sc * k)
    # legs and claws
    for sgn in (-1, 1):
        for i in range(3):
            dr.line([P(sgn * 30, 40 + i * 10), P(sgn * (95 + i * 12), 14 - i * 4), P(sgn * (115 + i * 14), 0)], fill=_mix(violet, (20, 10, 30), 0.35), width=int(9 * sc * k))
    body = _mix(violet, (255, 255, 255), 0.08)
    dr.ellipse([*P(-70, 120), *P(10, 20)], fill=body)           # head/body
    dr.polygon([P(-70, 100), P(-120, 125), P(-150, 95), P(-110, 70), P(-80, 60)], fill=_mix(violet, (255, 255, 255), 0.18))  # big claw
    dr.polygon([P(-150, 95), P(-185, 120), P(-170, 85)], fill=_mix(violet, (255, 255, 255), 0.3))
    for ex in (-48, -28):
        dr.line([P(ex, 112), P(ex - 4, 160)], fill=body, width=int(7 * sc * k)); dr.ellipse([*P(ex - 9, 172), *P(ex + 3, 158)], fill=(250, 240, 220))
    # the shell: shape from the name
    shell = _mix(rust, (90, 60, 40), (r % 5) / 10)
    if any(w in name for w in ('bell', 'knell', 'tenant')):
        dr.pieslice([*P(-5, 210), *P(165, -30)], 180, 360, fill=shell); dr.rectangle([*P(-5, 90), *P(165, 70)], fill=_mix(shell, (0, 0, 0), 0.25))
    elif any(w in name for w in ('barrel', 'keg', 'jug', 'pot', 'boiler', 'sixpence')):
        dr.rounded_rectangle([*P(-5, 190), *P(160, 20)], radius=int(26 * sc * k), fill=shell)
        for yy_ in (60, 105, 150): dr.line([P(-5, yy_), P(160, yy_)], fill=(40, 28, 20), width=int(6 * sc * k))
    elif any(w in name for w in ('chest', 'strongbox', 'wheelhouse', 'gun', 'prow', 'duchess', 'landlord', 'lifeboat')):
        dr.polygon([P(-5, 30), P(0, 170), P(80, 205), P(160, 160), P(170, 30)], fill=shell)
        dr.line([P(0, 110), P(168, 110)], fill=(40, 28, 20), width=int(6 * sc * k))
    else:  # whelk spiral
        dr.ellipse([*P(-5, 200), *P(165, 15)], fill=shell)
        for i in range(4): dr.arc([*P(10 + i * 18, 185 - i * 18), *P(150 - i * 18, 30 + i * 18)], 200, 330, fill=(60, 38, 24), width=int(6 * sc * k))
    if d.get('hero'): dr.ellipse([*P(60, 240), *P(100, 212)], fill=rust)  # a small crown-light so heroes read
    return im.resize((S, S), Image.LANCZOS)

def burst(cid, d, p):
    k = 2; im = Image.new('RGBA', (S * k, S * k), (0, 0, 0, 0)); dr = ImageDraw.Draw(im); c = S * k // 2
    r = _h(cid); n = 8 + r % 5; col = (217, 130, 43); vio = (123, 79, 143)
    for i in range(n):
        a = i / n * math.tau + (r % 7) * 0.2; L = (0.42 + 0.06 * ((i + r) % 3)) * S * k
        dr.polygon([(c + math.cos(a - .09) * 0.14 * S * k, c + math.sin(a - .09) * 0.14 * S * k), (c + math.cos(a) * L, c + math.sin(a) * L),
                    (c + math.cos(a + .09) * 0.14 * S * k, c + math.sin(a + .09) * 0.14 * S * k)], fill=col if i % 2 else vio)
    dr.ellipse([c - 0.16 * S * k, c - 0.16 * S * k, c + 0.16 * S * k, c + 0.16 * S * k], fill=(250, 232, 190))
    dr.ellipse([c - 0.28 * S * k, c - 0.28 * S * k, c + 0.28 * S * k, c + 0.28 * S * k], outline=vio, width=int(0.02 * S * k))
    return im.resize((S, S), Image.LANCZOS)

def plate(cid, d, p):
    k = 2; im = Image.new('RGBA', (S * k, S * k), (0, 0, 0, 0)); dr = ImageDraw.Draw(im); c = S * k // 2
    r = _h(cid); metal = _mix((150, 140, 130), (217, 130, 43), (r % 4) / 6)
    w = 0.34 * S * k
    dr.polygon([(c - w, c - w * .9), (c + w, c - w * .9), (c + w, c + w * .2), (c, c + w * 1.1), (c - w, c + w * .2)], fill=metal, outline=(60, 40, 30))
    dr.polygon([(c - w * .75, c - w * .7), (c + w * .75, c - w * .7), (c + w * .75, c + w * .12), (c, c + w * .85), (c - w * .75, c + w * .12)], fill=_mix(metal, (255, 255, 255), .15))
    for dx, dy in ((-.55, -.5), (.55, -.5), (-.55, .02), (.55, .02)):
        dr.ellipse([c + dx * w - 10, c + dy * w - 10, c + dx * w + 10, c + dy * w + 10], fill=(70, 50, 40))
    dr.line([(c - w * .4, c - w * .1), (c + w * .4, c - w * .1)], fill=(123, 79, 143), width=int(0.03 * S * k))
    return im.resize((S, S), Image.LANCZOS)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; force = '--force' in sys.argv
    if not args: raise SystemExit(__doc__)
    fid, only = args[0], set(args[1:])
    load = lambda f: json.load(open(os.path.join(ROOT, 'content', f + '.json')))
    units, spells, equip = load('units'), load('spells'), load('equipment')
    nonCard = lambda u: u.get('structure') or u.get('token')
    jobs = [(i, d, 'unit') for i, d in units.items() if d.get('faction') == fid and not nonCard(d)]
    jobs += [(i, d, 'spell') for i, d in spells.items() if d.get('faction') == fid]
    jobs += [(i, d, 'equipment') for i, d in equip.items() if d.get('faction') == fid]
    n = 0
    for idx, (cid, d, kind) in enumerate(jobs):
        if only and cid not in only: continue
        if not force and os.path.exists(os.path.join(OUT, cid + '.webp')): continue
        seed = _h(cid) % 1000
        if kind == 'unit': interim_art.compose(cid, fid, crab(cid, d, PAL[fid]), idx * 7 + 3, d.get('hero'))
        else: motif_art.compose(cid, fid, burst(cid, d, PAL[fid]) if kind == 'spell' else plate(cid, d, PAL[fid]), seed, kind)
        n += 1
    print(f'wrote {n} card images for {fid}')

if __name__ == '__main__':
    main()

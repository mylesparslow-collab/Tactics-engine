"""Procedural interim card art for a faction that has no model renders or hand-drawn motifs yet.
Draws a simple figure (units: a crab-in-a-shell silhouette, or a rearing armed serpent for the Slough; spells: a radiant burst; equipment: a plate) with PIL,
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

COLS = {'hermitage': ((217, 130, 43), (123, 79, 143)), 'slough': ((181, 201, 52), (92, 106, 49))}  # (accent, secondary) per faction
p_fid = 'hermitage'

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

def serpent(cid, d, p):
    """A rearing, armed sea-krait: banded coils, a scaled torso with arms and a weapon, a flared hood and head. Size from cost."""
    k = 2
    im = Image.new('RGBA', (S * k, S * k), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    r = _h(cid); name = (d.get('name', '') + cid).lower()
    black, bone, gold, olive, venom = (30, 32, 34), (230, 223, 200), (217, 169, 58), (92, 106, 49), (181, 201, 52)
    sc = 0.62 + min(d.get('cost', 40), 90) / 90 * 0.38
    cx, base = S * k // 2, int(S * k * 0.95)
    def P(x, y): return (cx + x * sc * k, base - y * sc * k)
    # coils: stacked banded rings that read as a krait
    for i, (w, h_, dx) in enumerate([(150, 46, -14), (125, 44, 18), (100, 42, -8)]):
        y0 = i * 40
        dr.ellipse([*P(dx - w, y0 + h_), *P(dx + w, y0)], fill=black)
        dr.ellipse([*P(dx - w + 14, y0 + h_ - 6), *P(dx + w - 14, y0 + 12)], fill=_mix(black, olive, 0.25))
        for b in range(-3, 4):
            x = dx + b * w / 3.6
            dr.line([P(x, y0 + 4), P(x * 0.97, y0 + h_ - 4)], fill=bone, width=int(6 * sc * k))
    # the tail paddle curling out to one side
    dr.polygon([P(130, 14), P(205, 44), P(230, 22), P(190, 6)], fill=black)
    # torso rising from the top coil: tapered, gold belly stripe
    top = 120
    dr.polygon([P(-46, top), P(46, top), P(34, top + 120), P(-34, top + 120)], fill=_mix(olive, black, 0.35))
    dr.polygon([P(-10, top), P(10, top), P(8, top + 118), P(-8, top + 118)], fill=gold)
    for yy_ in range(top + 14, top + 112, 18): dr.line([P(-38, yy_), P(38, yy_)], fill=_mix(olive, black, 0.6), width=int(3 * sc * k))
    # arms and weapon: a long fang-glaive on the right, a shield of scale on the left (heroes and big units get a second pair)
    wy = top + 78
    dr.line([P(60, 10), P(60, top + 215)], fill=(120, 92, 60), width=int(8 * sc * k))
    if r % 2: dr.polygon([P(60, top + 215), P(44, top + 180), P(76, top + 180)], fill=bone)
    else: dr.polygon([P(60, top + 250), P(46, top + 205), P(60, top + 220), P(74, top + 205)], fill=bone)
    dr.line([P(30, wy), P(52, wy + 6)], fill=_mix(olive, black, 0.2), width=int(14 * sc * k))
    dr.ellipse([*P(-100, wy + 44), *P(-34, wy - 40)], fill=_mix(olive, bone, 0.15), outline=black, width=int(4 * sc * k))
    dr.line([P(-34, wy), P(-60, wy + 2)], fill=_mix(olive, black, 0.2), width=int(14 * sc * k))
    if d.get('hero') or d.get('cost', 0) >= 60:
        dr.line([P(34, wy - 28), P(58, wy - 40)], fill=_mix(olive, black, 0.2), width=int(13 * sc * k))
        dr.line([P(-34, wy - 28), P(-58, wy - 38)], fill=_mix(olive, black, 0.2), width=int(13 * sc * k))
    # head: flared hood and a narrow face
    hy = top + 150
    dr.ellipse([*P(-70, hy + 66), *P(70, hy - 34)], fill=black)
    dr.ellipse([*P(-54, hy + 56), *P(54, hy - 26)], fill=_mix(olive, black, 0.3))
    dr.ellipse([*P(-30, hy + 54), *P(30, hy - 10)], fill=_mix(olive, bone, 0.1))
    for ex in (-13, 13):
        dr.ellipse([*P(ex - 6, hy + 28), *P(ex + 6, hy + 18)], fill=venom)
    dr.line([P(-6, hy - 4), P(-7, hy - 18)], fill=bone, width=int(3 * sc * k)); dr.line([P(6, hy - 4), P(7, hy - 18)], fill=bone, width=int(3 * sc * k))
    if d.get('hero'): dr.arc([*P(-60, hy + 90), *P(60, hy + 30)], 200, 340, fill=venom, width=int(6 * sc * k))  # a crest-light so heroes read
    return im.resize((S, S), Image.LANCZOS)

def burst(cid, d, p):
    k = 2; im = Image.new('RGBA', (S * k, S * k), (0, 0, 0, 0)); dr = ImageDraw.Draw(im); c = S * k // 2
    r = _h(cid); n = 8 + r % 5; col, vio = COLS.get(p_fid, COLS['hermitage'])
    for i in range(n):
        a = i / n * math.tau + (r % 7) * 0.2; L = (0.42 + 0.06 * ((i + r) % 3)) * S * k
        dr.polygon([(c + math.cos(a - .09) * 0.14 * S * k, c + math.sin(a - .09) * 0.14 * S * k), (c + math.cos(a) * L, c + math.sin(a) * L),
                    (c + math.cos(a + .09) * 0.14 * S * k, c + math.sin(a + .09) * 0.14 * S * k)], fill=col if i % 2 else vio)
    dr.ellipse([c - 0.16 * S * k, c - 0.16 * S * k, c + 0.16 * S * k, c + 0.16 * S * k], fill=(250, 232, 190))
    dr.ellipse([c - 0.28 * S * k, c - 0.28 * S * k, c + 0.28 * S * k, c + 0.28 * S * k], outline=vio, width=int(0.02 * S * k))
    return im.resize((S, S), Image.LANCZOS)

def plate(cid, d, p):
    k = 2; im = Image.new('RGBA', (S * k, S * k), (0, 0, 0, 0)); dr = ImageDraw.Draw(im); c = S * k // 2
    r = _h(cid); metal = _mix((150, 140, 130), COLS.get(p_fid, COLS['hermitage'])[0], (r % 4) / 6)
    w = 0.34 * S * k
    dr.polygon([(c - w, c - w * .9), (c + w, c - w * .9), (c + w, c + w * .2), (c, c + w * 1.1), (c - w, c + w * .2)], fill=metal, outline=(60, 40, 30))
    dr.polygon([(c - w * .75, c - w * .7), (c + w * .75, c - w * .7), (c + w * .75, c + w * .12), (c, c + w * .85), (c - w * .75, c + w * .12)], fill=_mix(metal, (255, 255, 255), .15))
    for dx, dy in ((-.55, -.5), (.55, -.5), (-.55, .02), (.55, .02)):
        dr.ellipse([c + dx * w - 10, c + dy * w - 10, c + dx * w + 10, c + dy * w + 10], fill=(70, 50, 40))
    dr.line([(c - w * .4, c - w * .1), (c + w * .4, c - w * .1)], fill=COLS.get(p_fid, COLS['hermitage'])[1], width=int(0.03 * S * k))
    return im.resize((S, S), Image.LANCZOS)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; force = '--force' in sys.argv
    if not args: raise SystemExit(__doc__)
    global p_fid
    fid, only = args[0], set(args[1:]); p_fid = fid
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
        if kind == 'unit': interim_art.compose(cid, fid, (serpent if fid == 'slough' else crab)(cid, d, PAL[fid]), idx * 7 + 3, d.get('hero'))
        else: motif_art.compose(cid, fid, burst(cid, d, PAL[fid]) if kind == 'spell' else plate(cid, d, PAL[fid]), seed, kind)
        n += 1
    print(f'wrote {n} card images for {fid}')

if __name__ == '__main__':
    main()

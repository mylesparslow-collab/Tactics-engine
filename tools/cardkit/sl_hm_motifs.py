"""Emblem drawings (512x512 SVG, transparent) for the Slough and Hermitage spell and equipment cards.
Writes <out_dir>/<cardId>.svg. Then:
  python3 tools/cardkit/sl_hm_motifs.py <svg_dir> && node tools/cardkit/motif_raster.cjs <png_dir> <svg_dir>
  python3 tools/cardkit/motif_art.py <png_dir> slough hermitage"""
import os, sys, math

G, K = '#b5c934', '#16181a'
AMB, AMB2, AMBD = '#e0a63c', '#f3cf72', '#8a5a1c'
BONE, SKIN, REED = '#e8e2c4', '#cfd6b0', '#8a8a4a'
MUD, MUD2 = '#2a2418', '#4a4028'
OR, OR2, ORD = '#d9822b', '#f2b05a', '#8a4a14'
PU, PU2, PUD = '#7a5090', '#a67cc0', '#3e2650'
BR, BR2 = '#c9a24a', '#f0d98a'
RUST, RUST2 = '#9a4a26', '#c9703c'
IRON, IRON2 = '#6a6e78', '#a4a9b4'
TAR = '#1c1a1e'

def S(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">{body}</svg>'

def P(d, f, s=K, w=7, extra=''):
    return f'<path d="{d}" fill="{f}" stroke="{s}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round" {extra}/>'

def C(x, y, r, f, s=K, w=7):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{f}" stroke="{s}" stroke-width="{w}"/>'

def E(x, y, rx, ry, f, s=K, w=7, rot=0):
    return f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{f}" stroke="{s}" stroke-width="{w}" transform="rotate({rot} {x} {y})"/>'

def R(x, y, w, h, f, s=K, sw=7, rx=8, rot=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{f}" stroke="{s}" stroke-width="{sw}" transform="rotate({rot} {x + w / 2} {y + h / 2})"/>'

def L(x1, y1, x2, y2, c=K, w=8):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{w}" stroke-linecap="round"/>'

def drop(x, y, s, f=G, st=K):
    return P(f'M{x} {y - 22 * s} C{x + 16 * s} {y - 2 * s} {x + 16 * s} {y + 18 * s} {x} {y + 18 * s} C{x - 16 * s} {y + 18 * s} {x - 16 * s} {y - 2 * s} {x} {y - 22 * s}Z', f, st, 4)

def gourd(x, y, s=1.0, rot=0, f=G, f2='#d8e87a'):
    return (f'<g transform="translate({x} {y}) rotate({rot}) scale({s})">'
            + E(0, 14, 40, 44, f, K, 7) + E(0, -34, 22, 24, f, K, 7) + E(-14, 4, 10, 22, f2, 'none', 0, 15)
            + L(0, -56, 6, -76, '#6a5a2a', 9) + '</g>')

def glow(c, r=210, o=0.35):
    return f'<radialGradient id="gl"><stop offset="0" stop-color="{c}" stop-opacity="{o}"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient><circle cx="256" cy="256" r="{r}" fill="url(#gl)"/>'

def barrel(x, y, w, h, f=ORD, f2=OR, rot=0):
    return (f'<g transform="rotate({rot} {x + w / 2} {y + h / 2})">'
            + P(f'M{x} {y + 14} Q{x - 16} {y + h / 2} {x} {y + h - 14} L{x + w} {y + h - 14} Q{x + w + 16} {y + h / 2} {x + w} {y + 14}Z', f)
            + E(x + w / 2, y + 14, w / 2, 16, f2) + R(x - 8, y + h * 0.28, w + 16, 14, '#4a4a52', K, 5, 4)
            + R(x - 8, y + h * 0.68, w + 16, 14, '#4a4a52', K, 5, 4) + '</g>')

M = {}

# ---------------- Slough spells ----------------
def sl_bitter_spray():
    b = glow(G, 220, 0.4)
    b += L(70, 440, 150, 300, REED, 14) + L(70, 440, 110, 330, REED, 10)
    b += P('M130 330 Q170 250 300 200', 'none', G, 26) + P('M130 330 Q170 250 300 200', 'none', '#e6f58a', 8)
    import random
    rnd = random.Random(4)
    for i in range(16):
        t = rnd.random(); x = 250 + t * 220 + rnd.uniform(-20, 20); y = 190 + t * 40 + rnd.uniform(-70, 70) * (0.4 + t)
        b += drop(x, y, 0.8 + rnd.random() * 0.9)
    b += drop(430, 260, 2.2, '#d8e87a')
    return b
M['sl_spell_bitter_spray'] = sl_bitter_spray

def sl_old_skin_ward():
    b = glow(AMB, 230, 0.4)
    b += P('M256 60 L420 110 Q430 270 360 370 Q300 450 256 470 Q212 450 152 370 Q82 270 92 110Z', SKIN, K, 9)
    b += P('M256 90 L396 130 Q404 262 342 350 Q296 420 256 440 Q216 420 170 350 Q108 262 116 130Z', AMB, '#8a5a1c', 6)
    for r in range(5):
        for c in range(4 - (r % 2)):
            x = 170 + c * 56 + (28 if r % 2 else 0) + (r * 0); y = 150 + r * 55
            if abs(x - 256) < 150 - r * 14:
                b += P(f'M{x - 26} {y} Q{x} {y + 44} {x + 26} {y}', 'none', AMBD, 4)
    b += P('M170 140 Q150 260 220 400', 'none', '#fbe6a0', 12, 'opacity="0.7"')
    b += E(256, 255, 40, 54, 'none', G, 6)
    return b
M['sl_spell_old_skin_ward'] = sl_old_skin_ward

def sl_shed_oil():
    b = glow(AMB2, 220, 0.4)
    b += P('M200 120 L312 120 L300 170 Q380 230 372 340 Q364 450 256 454 Q148 450 140 340 Q132 230 212 170Z', '#3a5a2a', K, 9)
    b += P('M170 270 Q256 240 342 270 Q350 420 256 438 Q162 420 170 270Z', AMB2, 'none', 0, 'opacity="0.95"')
    b += R(206, 84, 100, 46, '#a98a50', K, 7, 10) + P('M180 250 Q172 330 196 390', 'none', '#ffffff', 10, 'opacity="0.5"')
    b += P('M312 150 Q350 150 360 190 Q372 232 340 232', 'none', K, 8)
    b += drop(430, 140, 1.4, AMB2) + drop(400, 200, 1.0, AMB2) + drop(90, 200, 1.1, AMB2)
    b += L(432, 330, 432, 400, G, 14) + L(398, 365, 466, 365, G, 14)
    return b
M['sl_spell_shed_oil'] = sl_shed_oil

def sl_gourd_volley():
    b = glow(G, 220, 0.3)
    for x, y, s, r in ((150, 130, 1.0, 20), (300, 90, 0.9, -15), (390, 220, 1.0, 40)):
        b += L(x + 20, y - 100, x + 50, y - 30, '#8fa030', 6)
    b += gourd(140, 150, 1.15, 25) + gourd(320, 110, 1.0, -20) + gourd(400, 250, 1.1, 55)
    b += gourd(200, 330, 1.0, 10)
    # burst
    b += P('M280 400 L300 340 L330 380 L370 330 L380 390 L440 380 L400 430 L450 470 L380 470 L360 500 L320 460 L270 490 L280 440 L230 430Z', G, K, 7)
    for x, y in ((250, 330), (420, 340), (440, 440), (240, 480)):
        b += drop(x, y, 1.0, '#d8e87a')
    return b
M['sl_spell_gourd_volley'] = sl_gourd_volley

def sl_mire():
    b = glow('#8a9a40', 220, 0.25)
    b += E(256, 380, 220, 80, MUD, K, 8) + E(256, 380, 160, 52, '#1a160e', 'none', 0) + E(256, 380, 100, 30, '#0c0a06', 'none', 0)
    for rx, ry in ((235, 95), (190, 66), (130, 40)):
        b += E(256, 380, rx, ry, 'none', '#7a8a3a', 4)
    for x, y, r in ((170, 365, 14), (330, 392, 18), (290, 360, 9), (220, 400, 8)):
        b += C(x, y, r, MUD2, '#7a8a3a', 4)
    b += P('M256 380 Q250 300 262 220', 'none', REED, 12) + P('M220 380 Q200 320 190 250', 'none', REED, 10) + P('M300 382 Q320 310 340 260', 'none', REED, 10)
    # watching hood
    b += P('M180 200 Q256 60 332 200 Q300 250 256 250 Q212 250 180 200Z', '#4a5a2a', K, 8)
    b += E(222, 190, 12, 8, G, K, 4) + E(290, 190, 12, 8, G, K, 4) + L(222, 190, 222, 190, K, 2)
    b += P('M230 360 L290 360 L280 385 L240 385Z', K, K, 3, 'opacity="0.0"')
    return b
M['sl_spell_mire'] = sl_mire

def sl_lacquer_the_line():
    b = glow(AMB, 230, 0.4)
    xs = (70, 165, 260, 355)
    for i, x in enumerate(xs):
        y = 130 + i * 22
        b += P(f'M{x} {y} Q{x + 40} {y - 40} {x + 80} {y} L{x + 80} {y + 160} Q{x + 40} {y + 230} {x} {y + 160}Z', AMB if i < 3 else SKIN, K, 8)
        b += P(f'M{x + 10} {y + 10} Q{x + 40} {y - 14} {x + 70} {y + 10}', 'none', AMB2, 6)
        b += E(x + 40, y + 90, 16, 24, 'none', AMBD, 4)
    b += P('M60 120 Q260 30 440 150', 'none', AMB2, 14, 'opacity="0.8"')
    b += P('M60 440 L450 440', 'none', MUD2, 10)
    return b
M['sl_spell_lacquer_the_line'] = sl_lacquer_the_line

def sl_venom_tide():
    b = glow(G, 235, 0.45)
    for i, (y, c) in enumerate(((140, '#7a8a2a'), (230, '#98ac30'), (320, G), (410, '#d0e468'))):
        d = f'M30 {y} ' + ' '.join(f'Q{30 + k * 80 + 40} {y - 50} {30 + (k + 1) * 80} {y}' for k in range(6)) + f' L450 {y + 90} L30 {y + 90}Z'
        b += P(d, c, K, 7)
    b += drop(256, 110, 2.6, '#e6f58a')
    for x, y in ((110, 90), (400, 80), (180, 60), (340, 56)):
        b += drop(x, y, 0.9, '#e6f58a')
    return b
M['sl_spell_venom_tide'] = sl_venom_tide

def sl_last_hiss():
    b = glow(G, 235, 0.45)
    b += P('M60 250 Q256 40 452 250 Q256 150 60 250Z', '#3a4a22', K, 9)
    b += P('M60 250 Q256 150 452 250 Q420 440 256 460 Q92 440 60 250Z', '#a02a3a', K, 9)
    b += E(256, 380, 90, 50, '#6a1a28', 'none', 0)
    b += P('M140 252 Q170 330 190 400 Q196 330 210 232Z', BONE, K, 7) + P('M372 252 Q342 330 322 400 Q316 330 302 232Z', BONE, K, 7)
    b += P('M178 330 L188 396', 'none', G, 8) + P('M334 330 L324 396', 'none', G, 8)
    b += drop(188, 430, 1.1, G) + drop(324, 430, 1.1, G)
    b += P('M256 330 L256 420 M256 420 L236 450 M256 420 L276 450', 'none', '#e04a5a', 9)
    return b
M['sl_spell_last_hiss'] = sl_last_hiss

# ---------------- Slough equipment ----------------
def sl_lacquered_skin_coat():
    b = L(60, 100, 452, 100, '#4a3a20', 16) + L(256, 100, 256, 80, K, 6)
    b += P('M150 100 L200 120 Q256 150 312 120 L362 100 L452 240 L400 290 L370 240 L380 450 L132 450 L142 240 L112 290 L60 240Z', AMB, K, 9)
    b += P('M200 120 Q256 150 312 120 L300 450 L212 450Z', AMBD, K, 5, 'opacity="0.6"')
    for r in range(4):
        for c in range(5):
            x = 150 + c * 50 + (25 if r % 2 else 0); y = 200 + r * 62
            if 130 < x < 380: b += P(f'M{x - 22} {y} Q{x} {y + 36} {x + 22} {y}', 'none', AMBD, 4)
    b += P('M165 150 Q150 300 160 420', 'none', '#fbe6a0', 12, 'opacity="0.6"')
    b += L(256, 150, 256, 450, K, 5)
    return b
M['sl_equip_lacquered_skin_coat'] = sl_lacquered_skin_coat

def sl_fang_caps():
    b = ''
    b += P('M60 200 Q256 440 452 200', 'none', '#6a5a2a', 12)
    for x, rot in ((170, -12), (342, 12)):
        b += (f'<g transform="rotate({rot} {x} 260)">' + P(f'M{x - 60} 110 Q{x} 90 {x + 60} 110 Q{x + 50} 330 {x} 460 Q{x - 50} 330 {x - 60} 110Z', BONE, K, 9)
              + P(f'M{x - 40} 118 Q{x} 108 {x + 40} 118', 'none', '#fff', 6, 'opacity="0.0"')
              + P(f'M{x - 26} 150 Q{x - 24} 330 {x} 430', 'none', '#fff', 9, 'opacity="0.55"')
              + E(x, 120, 56, 22, '#2a2a2a', K, 6) + C(x, 450, 12, G, K, 5) + '</g>')
    b += drop(150, 490, 0.9) + drop(362, 490, 0.9)
    return b
M['sl_equip_fang_caps'] = sl_fang_caps

def sl_leviathan_scale():
    b = P('M256 40 Q440 80 450 260 Q440 420 256 480 Q72 420 62 260 Q72 80 256 40Z', '#5a7a58', K, 10)
    b += P('M256 70 Q410 100 418 260 Q410 400 256 450 Q102 400 94 260 Q102 100 256 70Z', '#6f9170', 'none', 0)
    for dx in (-90, 0, 90):
        b += P(f'M{256 + dx} 460 Q{256 + dx * 0.6} 260 {256 + dx * 0.9} 60', 'none', '#344a34', 9)
    for dx in (-45, 45):
        b += P(f'M{256 + dx} 440 Q{256 + dx * 0.6} 260 {256 + dx * 0.9} 80', 'none', '#8fb08a', 5, 'opacity="0.6"')
    b += P('M180 170 L230 230 M230 170 L180 230', 'none', K, 8) + P('M300 310 L370 360', 'none', BONE, 7) + L(310, 360, 340, 300, BONE, 6)
    b += P('M120 130 Q100 250 140 380', 'none', '#cfe8c8', 12, 'opacity="0.4"')
    return b
M['sl_equip_leviathan_scale'] = sl_leviathan_scale

def sl_gourd_bandolier():
    b = P('M40 90 L90 60 L470 400 L420 450Z', '#9a7a3a', K, 9)
    for i in range(10):
        t = i / 9; x = 80 + t * 360; y = 80 + t * 340
        b += L(x - 14, y + 12, x + 14, y - 12, '#6a4a1a', 5)
    for i in range(6):
        t = (i + 0.5) / 6; x = 100 + t * 340; y = 100 + t * 310
        b += gourd(x + 20, y + 70, 0.62, 0, G) + C(x + 20, y + 14, 8, '#e8f090', K, 4)
    b += P('M 70 100 L 120 130', 'none', K, 0)
    return b
M['sl_equip_gourd_bandolier'] = sl_gourd_bandolier

def sl_spare_skin():
    b = glow(G, 200, 0.18)
    b += P('M256 50 Q330 50 350 120 Q400 150 380 230 Q430 300 380 380 Q360 460 256 470 Q152 460 132 380 Q82 300 132 230 Q112 150 162 120 Q182 50 256 50Z', '#e2e8cc', K, 9)
    b += P('M256 80 Q312 80 326 130 Q370 160 352 232 Q396 296 352 360 Q336 430 256 440 Q176 430 160 360 Q116 296 160 232 Q142 160 186 130 Q200 80 256 80Z', '#c4cc9c', 'none', 0, 'opacity="0.6"')
    for y in (140, 200, 260, 320, 380):
        b += P(f'M190 {y} Q256 {y + 30} 322 {y}', 'none', '#98a070', 5)
    b += P('M256 80 L256 440', 'none', '#98a070', 4)
    b += L(130, 250, 382, 300, G, 16) + L(130, 250, 382, 300, '#e6f58a', 5) + P('M382 300 L412 330 M382 300 L420 290', 'none', G, 10)
    b += C(256, 160, 20, '#f4f6e4', '#98a070', 4)
    return b
M['sl_equip_spare_skin'] = sl_spare_skin

def sl_eldest_hood():
    b = L(256, 60, 256, 470, '#5a4a2a', 14) + C(256, 56, 14, '#8a6a30')
    b += P('M256 80 Q420 100 440 300 Q452 420 400 466 L320 430 L290 470 L256 436 L220 470 L190 430 L112 466 Q60 420 72 300 Q92 100 256 80Z', '#a8a880', K, 9)
    b += P('M256 130 Q356 140 366 290 Q372 370 340 410 Q256 440 172 410 Q140 370 146 290 Q156 140 256 130Z', '#3c3c30', K, 7)
    b += P('M110 200 Q100 300 130 420', 'none', '#d6d6b0', 10, 'opacity="0.5"') + P('M400 180 L380 230 L405 260', 'none', '#6a6a50', 5)
    b += E(256, 300, 66, 14, 'none', G, 12) + E(256, 300, 66, 14, 'none', '#e6f58a', 4)
    b += P('M180 120 L168 150 L196 140 M330 440 L350 470', 'none', '#6a6a50', 5)
    return b
M['sl_equip_eldest_hood'] = sl_eldest_hood

# ---------------- Hermitage spells ----------------
def hm_leftovers():
    b = glow(OR, 220, 0.3)
    b += barrel(90, 210, 150, 200, ORD, OR, -6) + barrel(270, 240, 150, 190, ORD, OR, 7)
    b += E(256, 440, 200, 26, '#2a1a2a', 'none', 0, 0)
    b += P('M180 70 Q256 130 332 70', 'none', OR2, 8, 'stroke-dasharray="3 22"') + P('M256 100 L256 170 M226 150 L256 180 L286 150', 'none', OR2, 12)
    b += R(60, 410, 60, 24, RUST, K, 5, 4, -8) + C(410, 440, 16, IRON, K, 5)
    return b
M['hm_spell_leftovers'] = hm_leftovers

def hm_caulk_and_tar():
    b = glow(PU2, 200, 0.2)
    b += P('M110 200 L110 440 Q256 480 402 440 L402 200Z', IRON, K, 9) + E(256, 200, 146, 36, TAR, K, 8)
    b += P('M150 205 Q256 230 360 205', 'none', '#55525c', 8)
    b += P('M126 230 L130 400', 'none', '#cfd3dc', 9, 'opacity="0.35"')
    b += P('M130 190 Q80 110 180 110', 'none', K, 10)
    b += P('M330 190 L420 40', 'none', '#8a6a30', 18) + P('M404 70 L450 20 L470 50 L430 100Z', TAR, K, 7)
    b += P('M240 236 L240 300 Q240 316 252 300 L252 236Z', TAR, TAR, 3) + P('M300 236 L300 340 Q300 356 312 340 L312 236Z', TAR, TAR, 3)
    b += P('M50 470 Q256 430 462 470', 'none', PU2, 10) + P('M50 470 Q256 430 462 470', 'none', OR2, 4, 'stroke-dasharray="14 18"')
    return b
M['hm_spell_caulk_and_tar'] = hm_caulk_and_tar

def hm_long_memory():
    b = glow(PU2, 220, 0.3)
    b += P('M100 440 Q70 300 130 220 Q150 120 230 90 Q310 70 380 130 L330 200 Q300 180 270 200 L230 260 Q300 280 330 330 Q300 400 200 440Z', OR, K, 9)
    b += P('M250 110 Q350 80 420 160 Q380 220 330 200Z', OR2, K, 8) + P('M230 260 Q300 280 330 330', 'none', K, 8)
    b += P('M150 250 Q140 330 170 400', 'none', OR2, 10, 'opacity="0.7"')
    for i in range(4):
        x = 350 + i * 28
        b += L(x, 300, x, 400, BONE, 9)
    b += L(345, 400, 435, 300, BONE, 9) if False else L(340, 380, 440, 320, BONE, 9)
    b += C(420, 120, 20, '#ffd9a0', K, 5) + C(420, 120, 6, K, K, 1)
    return b
M['hm_spell_long_memory'] = hm_long_memory

def hm_bell_comes_down():
    b = glow(BR2, 230, 0.3)
    for x in (150, 256, 362):
        b += L(x, 20, x, 90, '#ffe9b0', 5)
    b += P('M256 50 Q344 52 350 160 Q356 270 420 340 L420 380 L92 380 L92 340 Q156 270 162 160 Q168 52 256 50Z', BR, K, 10)
    b += P('M256 80 Q320 82 324 160 Q330 270 390 340 L390 350 L256 350Z', '#a88230', 'none', 0, 'opacity="0.55"')
    b += P('M196 110 Q190 220 130 320', 'none', BR2, 14, 'opacity="0.7"')
    b += R(86, 372, 340, 30, BR2, K, 8, 8) + C(256, 24, 14, K, K, 2)
    b += P('M200 402 L256 455 L312 402Z', IRON, K, 8)
    b += P('M60 470 L120 440 L160 480 L200 450 L256 490 L312 450 L352 480 L392 440 L452 470 L440 500 L72 500Z', RUST, K, 7)
    return b
M['hm_spell_the_bell_comes_down'] = hm_bell_comes_down

def hm_bare_claws():
    b = glow('#e89ab0', 220, 0.3)
    b += P('M130 250 Q60 180 90 90 Q130 60 170 110 L170 170 L130 150 L140 230Z', '#e49a8a', K, 8)
    b += P('M382 250 Q452 180 422 90 Q382 60 342 110 L342 170 L382 150 L372 230Z', '#e49a8a', K, 8)
    b += P('M90 90 Q60 50 100 40 L150 70 Q130 90 90 90Z', '#f3b9a8', K, 7) + P('M422 90 Q452 50 412 40 L362 70 Q382 90 422 90Z', '#f3b9a8', K, 7)
    b += E(256, 330, 120, 100, '#e49a8a', K, 9) + P('M170 330 Q256 300 342 330', 'none', '#c4705e', 7)
    b += E(256, 400, 74, 54, '#c4705e', K, 7)
    for x in (130, 196, 316, 382):
        b += L(x, 410, x + (-1 if x < 256 else 1) * 40, 480, '#c4705e', 12)
    b += L(220, 260, 214, 200, '#e49a8a', 10) + L(292, 260, 298, 200, '#e49a8a', 10) + C(214, 192, 14, '#fff', K, 5) + C(298, 192, 14, '#fff', K, 5)
    b += C(216, 194, 5, K, K, 1) + C(296, 194, 5, K, K, 1)
    b += P('M256 20 L240 60 M256 20 L272 60 M256 20 L256 66', 'none', OR2, 8)
    return b
M['hm_spell_bare_claws'] = hm_bare_claws

def hm_salvage_spill():
    b = glow(OR, 220, 0.25)
    b += P('M60 150 L260 190 L230 330 L70 300Z', RUST, K, 9) + P('M260 190 L330 130 L360 170 L300 250Z', IRON, K, 8)
    b += C(110, 350, 36, IRON, K, 8) + C(110, 350, 12, K, K, 2) + L(70, 150, 90, 300, '#c9703c', 8)
    b += P('M250 260 Q330 330 400 470 L130 470 Q190 360 250 260Z', 'none', K, 0)
    # scrap pile
    b += P('M200 330 L280 300 L310 350 L240 380Z', IRON2, K, 8) + P('M300 380 L380 340 L420 400 L330 430Z', RUST2, K, 8)
    b += P('M160 420 L240 400 L260 460 L170 470Z', BR, K, 8) + P('M340 440 L420 430 L440 480 L350 490Z', IRON, K, 8)
    b += P('M380 280 L400 240 L430 262 L410 300Z', BR2, K, 7) + C(320, 300, 20, 'none', IRON2, 9) + C(190, 250, 26, 'none', BR, 9)
    for x in (230, 300, 380): b += L(x, 90, x, 150, '#ffd9a0', 5)
    return b
M['hm_spell_salvage_spill'] = hm_salvage_spill

def hm_off_the_gun_deck():
    b = glow(OR2, 220, 0.25)
    b += '<g transform="rotate(24 256 250)">'
    b += R(70, 190, 330, 90, IRON, K, 9, 40) + R(380, 176, 40, 118, IRON2, K, 8, 10) + P('M70 200 Q30 235 70 270', '#2a2a30', K, 8)
    b += R(150, 188, 14, 94, '#8a8e98', 'none', 0, 3)
    b += R(210, 276, 70, 30, '#8a5a2a', K, 7, 6) + C(240, 330, 52, '#8a5a2a', K, 9) + C(240, 330, 16, K, K, 2) + L(240, 280, 240, 380, '#5a3a1a', 6) + L(190, 330, 290, 330, '#5a3a1a', 6)
    b += '</g>'
    b += L(70, 440, 200, 400, '#ffd9a0', 6) + L(30, 400, 140, 350, '#ffd9a0', 6)
    b += P('M390 470 L440 430 L470 480Z', RUST, K, 6) + C(430, 180, 18, K, K, 2)
    return b
M['hm_spell_off_the_gun_deck'] = hm_off_the_gun_deck

def hm_moving_day():
    b = glow(OR2, 220, 0.3)
    b += barrel(130, 100, 200, 250, ORD, OR, -4)
    b += E(250, 390, 104, 50, '#b0603e', K, 8) + L(180, 420, 150, 480, '#b0603e', 12) + L(250, 438, 250, 490, '#b0603e', 12) + L(320, 420, 354, 480, '#b0603e', 12)
    b += P('M330 380 Q420 360 440 290 L470 300 L450 200 L420 220 L400 330Z', '#c4705e', K, 7)
    b += L(380, 300, 390, 240, '#b0603e', 10) + C(390, 232, 12, '#fff', K, 4)
    b += P('M70 60 Q256 0 440 60', 'none', OR2, 12) + P('M440 60 L410 30 M440 60 L405 90', 'none', OR2, 12)
    b += R(40, 400, 60, 60, ORD, K, 6, 4, 10)
    return b
M['hm_spell_moving_day'] = hm_moving_day

# ---------------- Hermitage equipment ----------------
def hm_tar_caulking():
    b = ''
    for i, (rx, ry, y) in enumerate(((190, 62, 400), (170, 56, 350), (150, 50, 305), (126, 44, 265))):
        b += E(256, y, rx, ry, '#d2b87e', K, 8) + E(256, y, rx - 46, ry - 18, '#8a7448', K, 6)
        b += P(f'M{256 - rx + 30} {y - 10} Q256 {y + ry} {256 + rx - 30} {y - 10}', 'none', '#ecdcaa', 5, 'opacity="0.7"')
    b += E(256, 215, 96, 34, TAR, K, 8)
    b += P('M190 215 Q186 300 200 320 Q216 330 214 300 L218 222Z', TAR, K, 5) + P('M300 222 Q306 330 322 350 Q338 356 334 320 L330 222Z', TAR, K, 5)
    b += P('M240 225 L248 440 L268 440 L276 225Z', TAR, TAR, 3, 'opacity="0.0"')
    b += P('M380 40 L330 190', 'none', '#8a6a30', 20) + P('M300 170 L352 150 L366 206 L316 226Z', TAR, K, 7)
    b += drop(150, 120, 1.0, '#4a4650') + drop(120, 200, 0.7, '#4a4650')
    return b
M['hm_equip_tar_caulking'] = hm_tar_caulking

def hm_filed_claw():
    b = P('M80 420 Q40 280 120 200 Q170 100 280 80 Q380 70 430 130 L350 210 Q320 190 290 215 L250 290 Q330 310 350 380 Q320 460 200 460Z', OR, K, 10)
    b += P('M280 100 Q370 90 410 140 L350 208Z', OR2, K, 7) + P('M250 290 Q330 310 350 380', 'none', K, 8)
    b += P('M150 250 Q140 340 170 420', 'none', OR2, 12, 'opacity="0.7"')
    b += '<g transform="rotate(-38 400 380)">' + R(320, 360, 150, 36, IRON2, K, 7, 6) + ''.join(L(336 + i * 16, 364, 336 + i * 16, 392, K, 3) for i in range(8)) + R(450, 366, 60, 24, '#8a5a2a', K, 6, 10) + '</g>'
    b += P('M440 280 L470 250 M450 310 L490 300', 'none', '#ffe9b0', 6)
    return b
M['hm_equip_filed_claw'] = hm_filed_claw

def hm_spare_plating():
    b = P('M110 110 L402 90 L420 400 L130 430Z', IRON, K, 10)
    b += P('M128 130 L386 112 L396 190 L136 212Z', IRON2, 'none', 0, 'opacity="0.55"')
    for x, y in ((140, 130), (380, 112), (396, 392), (150, 412), (260, 105), (270, 420)):
        b += C(x, y, 13, '#4a4e58', K, 5) + C(x - 3, y - 3, 4, '#d0d4dc', 'none', 0)
    b += P('M200 220 L330 210 L340 320 L210 330Z', RUST, K, 7) + P('M210 240 L320 232 M214 280 L326 272', 'none', RUST2, 5)
    b += P('M170 300 L200 460 L240 330', 'none', K, 0)
    b += R(320, 380, 120, 40, BR, K, 7, 6, -14) + C(446, 340, 9, BR2, K, 4)
    return b
M['hm_equip_spare_plating'] = hm_spare_plating

def hm_grudge_ledger():
    b = R(90, 80, 300, 380, '#5a2e3a', K, 10, 16) + R(110, 80, 280, 380, '#8a4a5a', K, 8, 12)
    b += R(100, 100, 30, 340, '#3e2028', K, 5, 6)
    b += R(160, 130, 190, 80, '#e8d8a8', K, 6, 6)
    for i in range(3):
        b += L(190 + i * 28, 150, 190 + i * 28, 192, K, 7)
    b += L(180, 195, 270, 145, K, 7) + L(275, 150, 330, 150, K, 0)
    for i in range(3):
        b += L(268 + i * 22, 150, 268 + i * 22, 192, K, 7)
    b += L(260, 198, 340, 148, K, 7)
    b += P('M390 340 L470 160 L492 172 L416 352Z', BR, K, 7) + P('M470 160 L478 120 L492 172Z', K, K, 4)
    b += R(150, 360, 80, 30, BR, K, 6, 6)
    b += P('M300 260 Q340 240 370 300', 'none', OR2, 8)
    return b
M['hm_equip_grudge_ledger'] = hm_grudge_ledger

def hm_moulting_sac():
    b = glow(PU2, 200, 0.3)
    b += P('M256 40 Q410 60 430 240 Q440 420 256 470 Q72 420 82 240 Q102 60 256 40Z', '#c9a0d8', K, 9, 'fill-opacity="0.75"')
    b += P('M256 70 Q380 84 396 240 Q404 390 256 436 Q108 390 116 240 Q132 84 256 70Z', '#e6c9ef', 'none', 0, 'opacity="0.45"')
    b += E(256, 300, 90, 70, '#5a2e72', K, 7) + P('M176 300 Q256 260 336 300', 'none', PU2, 6)
    b += L(206, 230, 196, 180, PU, 9) + L(306, 230, 316, 180, PU, 9) + C(196, 172, 12, '#fff', K, 4) + C(316, 172, 12, '#fff', K, 4)
    b += P('M170 370 L140 420 M210 380 L200 440 M300 380 L312 440 M342 370 L372 420', 'none', PU, 10)
    b += P('M130 120 Q110 220 140 330', 'none', '#fff', 12, 'opacity="0.55"')
    b += P('M200 40 Q256 10 312 40', 'none', '#e6c9ef', 10)
    return b
M['hm_equip_moulting_sac'] = hm_moulting_sac

def hm_brass_claw_cap():
    b = glow(BR2, 200, 0.25)
    b += P('M90 450 Q50 280 120 190 Q170 90 280 70 Q390 60 440 130 L350 215 Q320 190 290 215 L250 290 Q330 310 350 400 Q320 470 200 470Z', BR, K, 10)
    b += P('M280 90 Q370 82 414 140 L350 205Z', BR2, K, 7) + P('M250 290 Q330 310 350 400', 'none', K, 8)
    b += P('M140 240 Q130 340 160 420', 'none', '#fff6c8', 14, 'opacity="0.7"')
    b += P('M230 120 Q250 250 220 300', 'none', K, 0)
    b += R(70, 410, 300, 50, '#a88230', K, 9, 10, -8)
    for x, y in ((110, 440), (175, 432), (240, 424), (305, 416)): b += C(x, y, 9, BR2, K, 4)
    b += P('M400 60 L430 30 M430 90 L470 70', 'none', '#ffe9b0', 7)
    return b
M['hm_equip_brass_claw_cap'] = hm_brass_claw_cap

if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    for cid, fn in M.items():
        open(os.path.join(out, cid + '.svg'), 'w').write(S(fn()))
    print('wrote', len(M))

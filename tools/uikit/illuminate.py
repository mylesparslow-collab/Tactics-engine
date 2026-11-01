"""Bake EBB's illuminated initials: burnished gold capitals on a sea-blue painted block with gold
vine scrollwork and a double gold rule, in the manner of a manuscript versal.
Run: python3 tools/uikit/illuminate.py [fontfile]  -> writes src/ui/kit/ill/A.webp .. Z.webp (deterministic).
Default font: tools/uikit/fonts/CormorantGaramond-Bold.ttf (OFL)."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, '..', '..', 'src', 'ui', 'kit', 'ill')
FONT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'fonts', 'CormorantGaramond-Bold.ttf')
S = 768          # working size (4x)
FINAL = 160      # shipped size; shown at 40-80 css px
os.makedirs(OUT, exist_ok=True)


def fbm(n, seed, octaves=5, base=3):
    g = np.random.default_rng(seed)
    acc = np.zeros((n, n)); amp = 1.0; tot = 0
    for o in range(octaves):
        k = base * 2 ** o
        img = Image.fromarray((g.random((k, k)) * 255).astype(np.uint8)).resize((n, n), Image.BICUBIC)
        acc += amp * np.asarray(img) / 255.0; tot += amp; amp *= 0.5
    return acc / tot


def gblur(a, r):
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r))) / 255.0


def emboss(mask, r, strength):
    """Lambert + specular shading from a blurred mask used as a height field."""
    hgt = gblur(mask, r)
    gy, gx = np.gradient(hgt)
    nx, ny, nz = -gx * strength, -gy * strength, np.ones_like(hgt)
    ln = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2); nx /= ln; ny /= ln; nz /= ln
    L = np.array([-0.5, -0.65, 0.58]); L /= np.linalg.norm(L)
    diff = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    Hh = L + np.array([0, 0, 1.0]); Hh /= np.linalg.norm(Hh)
    spec = np.clip(nx * Hh[0] + ny * Hh[1] + nz * Hh[2], 0, 1) ** 40
    return diff, spec


def gold(diff, spec, n):
    """Burnished leaf: dark umber shadows through warm gold to pale highlights, with leaf texture."""
    tex = 0.85 + 0.15 * n
    t = np.clip(diff * tex, 0, 1)[..., None]
    lo, mid, hi = np.array([0.30, 0.17, 0.05]), np.array([0.80, 0.58, 0.24]), np.array([1.0, 0.93, 0.70])
    c = np.where(t < 0.6, lo + (mid - lo) * (t / 0.6), mid + (hi - mid) * ((t - 0.6) / 0.4))
    return np.clip(c + spec[..., None] * np.array([1.0, 0.95, 0.8]) * 0.9, 0, 1)


def comp(base, rgb, a):
    a = a[..., None]
    return base * (1 - a) + rgb * a


def vine_layer(seed):
    """Acanthus curls: a tapered gold spiral in each corner with a tail running along the edge,
    leaves along the stem and white-dot trefoils at the tips."""
    im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im)
    dots = Image.new('L', (S, S), 0); dd = ImageDraw.Draw(dots)
    def dot(x, y, r=4.5): dd.ellipse([x - r, y - r, x + r, y + r], fill=255)
    for k, (cx, cy) in enumerate([(165, 165), (S - 165, 165), (S - 165, S - 165), (165, S - 165)]):
        base = math.pi * (1.25 + 0.5 * k)          # points from centre toward its corner
        for side in ((1,) if k % 2 == 0 else (-1,)):
            pts = []
            for i in range(160):
                th = i / 159 * 2.6 * math.pi
                r = 135 * math.exp(-0.26 * th)
                a = base + side * th
                pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
            for i in range(len(pts) - 1):
                d.line([pts[i], pts[i + 1]], fill=210, width=max(2, int(11 * (1 - i / len(pts)) + 2)))
            for i in range(10, 90, 26):            # leaves on the outer turn
                x, y = pts[i]; x2, y2 = pts[i + 1]
                t = math.atan2(y2 - y, x2 - x) - side * math.pi * 0.28
                tip = (x + math.cos(t) * 34, y + math.sin(t) * 34)
                l1 = (x + math.cos(t + .55) * 14, y + math.sin(t + .55) * 14)
                l2 = (x + math.cos(t - .55) * 14, y + math.sin(t - .55) * 14)
                d.polygon([(x, y), l1, tip, l2], fill=200)
                dot(tip[0] + math.cos(t) * 10, tip[1] + math.sin(t) * 10, 3.5)
            ex, ey = pts[-1]; d.ellipse([ex - 8, ey - 8, ex + 8, ey + 8], fill=230)
        # trefoil of white dots in the corner beyond the curl
        ox, oy = cx + math.cos(base) * 98, cy + math.sin(base) * 98
        for j in range(3):
            a = base + math.pi + (j - 1) * 0.7
            dot(ox + math.cos(a) * 11, oy + math.sin(a) * 11)
    return np.asarray(im) / 255.0, np.asarray(dots) / 255.0


def letter_mask(ch, font_path):
    font = ImageFont.truetype(font_path, 640)
    im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im)
    l, t, r, b = d.textbbox((0, 0), ch, font=font)
    d.text(((S - (r - l)) / 2 - l, (S - (b - t)) / 2 - t + 6), ch, font=font, fill=255)
    return np.asarray(im) / 255.0


def bake(ch, font_path, seed):
    yy, xx = np.mgrid[0:S, 0:S] / S
    out = np.zeros((S, S, 3)); alpha = np.zeros((S, S))
    # block
    m0, m1 = 18, S - 18
    block = np.zeros((S, S)); block[m0:m1, m0:m1] = 1
    n = fbm(S, seed)
    field = np.array([0.06, 0.17, 0.24]) * (1 - yy[..., None] * 0.45) + np.array([0.0, 0.03, 0.05]) * xx[..., None]
    field = field * (0.82 + 0.3 * n[..., None])
    vign = np.clip(1 - ((xx - 0.5) ** 2 + (yy - 0.5) ** 2) * 1.6, 0, 1)[..., None]
    field = field * (0.55 + 0.45 * vign)
    out = comp(out, field, block); alpha = np.maximum(alpha, block)
    # vines (behind the letter), muted gold with emboss
    vm, dots = vine_layer(seed + 1)
    vdiff, vspec = emboss(vm, 2, 22)
    vg = gold(vdiff, vspec * 0.4, n) * 0.72
    inside = np.zeros((S, S)); inside[52:S - 52, 52:S - 52] = 1
    # faint diaper lattice in the field
    lat = ((np.abs(((xx + yy) * 14) % 1 - 0.5) < 0.03) | (np.abs(((xx - yy) * 14) % 1 - 0.5) < 0.03)).astype(float)
    out = comp(out, np.array([0.16, 0.32, 0.40]), gblur(lat, 1) * inside * 0.35)
    out = comp(out, vg, np.clip(vm * 1.2, 0, 1) * inside)
    out = comp(out, np.array([0.93, 0.91, 0.84]), gblur(dots, 0.8) * inside * 0.95)
    # double gold rule
    rule = np.zeros((S, S))
    def frame(a, w):
        rule[a:S - a, a:a + w] = 1; rule[a:S - a, S - a - w:S - a] = 1
        rule[a:a + w, a:S - a] = 1; rule[S - a - w:S - a, a:S - a] = 1
    frame(18, 16); frame(46, 5)
    rd, rs = emboss(rule, 2.5, 30)
    out = comp(out, gold(rd, rs, n), rule)
    # thin dark line outside the outer rule for crispness
    edge = np.zeros((S, S)); edge[12:S - 12, 12:S - 12] = 1; edge[18:S - 18, 18:S - 18] = 0
    out = comp(out, np.array([0.08, 0.05, 0.02]), edge); alpha = np.maximum(alpha, edge)
    # letter: cast shadow, dark outline, burnished gold
    lm = letter_mask(ch, font_path)
    sh = gblur(np.roll(np.roll(lm, 14, 0), 10, 1), 10)
    out = comp(out, np.array([0.01, 0.02, 0.03]), sh * 0.85 * block)
    outline = gblur(lm, 7); outline = np.clip(outline * 3, 0, 1)
    out = comp(out, np.array([0.10, 0.05, 0.015]), outline)
    ld, ls = emboss(lm, 5, 34)
    lg = gold(ld, ls, n)
    # incised centre line: a darker inner bevel suggests a raised, punched gilt edge
    inner = np.clip(gblur(lm, 3) - gblur(lm, 14) * 0.15, 0, 1)
    out = comp(out, lg, lm)
    out = comp(out, np.array([0.45, 0.28, 0.08]), np.clip((lm - inner) * 1.5, 0, 1) * 0.5)
    alpha = np.maximum(alpha, outline)
    img = Image.fromarray(np.dstack([np.clip(out, 0, 1), alpha]).__mul__(255).astype(np.uint8), 'RGBA')
    return img.resize((FINAL, FINAL), Image.LANCZOS)


if __name__ == '__main__':
    letters = sys.argv[2] if len(sys.argv) > 2 else 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for i, ch in enumerate(letters):
        bake(ch, FONT, 11 + i).save(os.path.join(OUT, f'{ch}.webp'), quality=90, method=6)
        print('baked', ch)

"""Bake Brinewake's UI kit: lit raster materials (cast bronze, salt crust, dark slate) from analytic height fields.
Run: python3 tools/uikit/bake.py  -> writes PNGs to src/ui/kit/. Deterministic (fixed seeds)."""
import numpy as np
from PIL import Image
import os, math

OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'ui', 'kit')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)

# ---------------------------------------------------------------- noise
def blur(a, r):
    if r <= 0: return a
    k = int(r)
    out = a.copy()
    for _ in range(3):  # 3 box blurs ~ gaussian
        c = np.cumsum(np.pad(out, ((0, 0), (k + 1, k)), mode='wrap'), axis=1)
        out = (c[:, 2 * k + 1:] - c[:, :-2 * k - 1]) / (2 * k + 1)
        c = np.cumsum(np.pad(out, ((k + 1, k), (0, 0)), mode='wrap'), axis=0)
        out = (c[2 * k + 1:, :] - c[:-2 * k - 1, :]) / (2 * k + 1)
    return out

def fbm(h, w, octaves=5, base=4, seed=0):
    g = np.random.default_rng(seed)
    acc = np.zeros((h, w)); amp = 1.0; tot = 0
    for o in range(octaves):
        n = base * 2 ** o
        small = g.random((n, n))
        img = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += amp * (np.asarray(img) / 255.0); tot += amp; amp *= 0.5
    return acc / tot

def grain(h, w, seed=0, r=1):
    return blur(np.random.default_rng(seed).random((h, w)), r)

# ---------------------------------------------------------------- shading
L = np.array([-0.55, -0.65, 0.55]); L /= np.linalg.norm(L)
H = L + np.array([0, 0, 1.0]); H /= np.linalg.norm(H)

def shade(height, albedo, strength=6.0, spec=0.6, gloss=24, spec_col=(1.0, 0.92, 0.7), ao_r=6):
    gy, gx = np.gradient(height * strength)
    n = np.dstack([-gx, -gy, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    diff = np.clip((n * L).sum(2), 0, 1)
    sp = np.clip((n * H).sum(2), 0, 1) ** gloss * spec
    ao = np.clip(1 - (blur(height, ao_r) - height) * 2.2, 0.35, 1.0)
    lit = albedo * (0.28 + 0.9 * diff)[..., None] * ao[..., None] + sp[..., None] * np.array(spec_col)
    return np.clip(lit, 0, 1), ao

def ramp(t, stops):
    t = np.clip(t, 0, 1); out = np.zeros(t.shape + (3,))
    xs = [s[0] for s in stops]; cs = [np.array(s[1]) / 255.0 for s in stops]
    for c in range(3): out[..., c] = np.interp(t, xs, [cc[c] for cc in cs])
    return out

def save(name, rgb, alpha):
    a = np.dstack([rgb, alpha[..., None]])
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, name), optimize=True)
    print('wrote', name, a.shape)

def sd_round_rect(px, py, cx, cy, hw, hh, r):
    qx = np.abs(px - cx) - hw + r; qy = np.abs(py - cy) - hh + r
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r

def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)

BRONZE = [(0, (38, 24, 10)), (.35, (96, 64, 26)), (.6, (150, 108, 48)), (.8, (196, 152, 78)), (1, (236, 204, 140))]
VERDI = np.array([62, 108, 96]) / 255.0
SALT = np.array([236, 232, 220]) / 255.0

def bronze_albedo(h, w, height, seed):
    n = fbm(h, w, 5, 6, seed)
    pits = grain(h, w, seed + 1, 1)
    base = ramp(0.45 + (n - 0.5) * 0.5 + height * 0.25, BRONZE)
    # cavity tarnish: low local height relative to blur -> darker + verdigris
    cav = np.clip((blur(height, 4) - height) * 6, 0, 1)
    base = base * (1 - cav[..., None] * 0.55) + VERDI * (cav * smooth(.55, .8, n))[..., None] * 0.6
    base *= (0.88 + pits * 0.24)[..., None]
    return base

def salt_crust(h, w, mask, seed, amount=1.0):
    n = fbm(h, w, 5, 10, seed); g = grain(h, w, seed + 3, 0)
    m = mask * smooth(0.52, 0.66, n) * amount
    speck = (g > 0.985) * mask * 0.8
    return np.clip(m + speck, 0, 1)

# ---------------------------------------------------------------- frame (9-slice, 256, slice 72)
def frame(name, S=256, band=30, inner=8, corner=True, seed=1):
    y, x = np.mgrid[0:S, 0:S].astype(float) + 0.5
    d_out = sd_round_rect(x, y, S / 2, S / 2, S / 2 - 3, S / 2 - 3, 14)
    d_in = sd_round_rect(x, y, S / 2, S / 2, S / 2 - 3 - band, S / 2 - 3 - band, 6)
    t = np.clip(-d_out / band, 0, 1)                      # 0 at outer edge -> 1 at inner edge
    body = (d_out < 0) & (d_in > 0)
    prof = np.sin(np.clip(t, 0, 1) * math.pi) ** 0.6       # rounded bar
    prof += 0.35 * smooth(0.62, 0.7, t) * (1 - smooth(0.78, 0.86, t))  # raised inner bead
    prof -= 0.25 * np.exp(-((t - 0.3) / 0.05) ** 2)       # engraved groove
    height = np.where(body, prof, 0.0)
    if corner:
        for cx, cy in [(band * 0.95, band * 0.95), (S - band * 0.95, band * 0.95), (band * 0.95, S - band * 0.95), (S - band * 0.95, S - band * 0.95)]:
            r = np.hypot(x - cx, y - cy)
            boss = np.clip(1 - (r / (band * 0.95)) ** 2, 0, 1) ** 0.5 * 1.25
            ring = np.exp(-((r - band * 0.62) / 1.6) ** 2) * -0.25
            rivet = np.clip(1 - (r / 6.5) ** 2, 0, 1) ** 0.5 * 0.6
            height = np.maximum(height, boss + ring + rivet * (r < 7))
    height += (fbm(S, S, 4, 16, seed) - 0.5) * 0.12 * (height > 0)
    alpha = np.clip(0.5 - d_out, 0, 1) * np.clip(d_in + 0.5, 0, 1)
    alpha = np.maximum(alpha, (height > 0.02).astype(float) * np.clip(0.5 - d_out, 0, 1))
    alb = bronze_albedo(S, S, height, seed)
    sc = salt_crust(S, S, (height > 0.05).astype(float) * (1 - smooth(0.2, 0.6, height)), seed + 9, 0.8)
    rgb, ao = shade(height, alb, strength=7)
    rgb = rgb * (1 - sc[..., None]) + SALT * (0.75 + 0.25 * ao)[..., None] * sc[..., None]
    # dark inner lip shadow onto content
    lip = np.clip(1 - np.clip(d_in, 0, 9) / 9, 0, 1) * (d_in < 0) * 0 
    save(name, rgb, alpha)

# ---------------------------------------------------------------- slate panel fill (tileable 384)
def slate(name, S=384, seed=3):
    n = fbm(S, S, 6, 3, seed); n2 = fbm(S, S, 4, 12, seed + 1); g = grain(S, S, seed + 2, 0)
    height = n * 0.6 + n2 * 0.3 + g * 0.05
    alb = ramp(n * 0.7 + n2 * 0.3, [(0, (14, 20, 26)), (.5, (24, 33, 41)), (1, (40, 50, 58))])
    rgb, _ = shade(height, alb, strength=1.6, spec=0.08, gloss=10, spec_col=(.7, .8, .9))
    save(name, rgb, np.ones((S, S)))

# ---------------------------------------------------------------- plate button (9-slice 128, slice 30)
def plate(name, S=128, Hh=96, seed=5, tone=0.0, inset_col=(18, 22, 26)):
    y, x = np.mgrid[0:Hh, 0:S].astype(float) + 0.5
    d = sd_round_rect(x, y, S / 2, Hh / 2, S / 2 - 3, Hh / 2 - 3, 12)
    rim = 14
    t = np.clip(-d / rim, 0, 1)
    height = np.where(d < 0, np.sin(t * math.pi / 2) ** 0.7, 0)
    di = d + rim
    inner = di < 0
    height = np.where(inner, 0.55 - np.clip(-di / 30, 0, 0.12), height)
    height += (fbm(Hh, S, 4, 10, seed) - 0.5) * 0.08 * (d < 0)
    alb = bronze_albedo(Hh, S, height + tone, seed)
    rgb, ao = shade(height, alb, strength=6)
    fill = np.array(inset_col) / 255.0 * (0.85 + 0.3 * fbm(Hh, S, 4, 6, seed + 4))[..., None]
    rgb = np.where(inner[..., None], fill * (0.6 + 0.4 * smooth(-14, -2, -di))[..., None] if False else fill * np.clip(1 - np.exp(di / 4) * 0.7, 0.3, 1)[..., None], rgb)
    alpha = np.clip(0.5 - d, 0, 1)
    save(name, rgb, alpha)

# ---------------------------------------------------------------- end-turn medallion (256)
def medallion(name, S=256, seed=11):
    y, x = np.mgrid[0:S, 0:S].astype(float) + 0.5
    r = np.hypot(x - S / 2, y - S / 2); R = S / 2 - 4
    t = r / R
    height = np.zeros((S, S))
    rimz = (t > 0.78) & (t < 1)
    height += np.where(rimz, np.clip(np.sin((t - 0.78) / 0.22 * math.pi), 0, 1) ** 0.6, 0)
    # notches around the rim
    ang = np.arctan2(y - S / 2, x - S / 2)
    height -= rimz * 0.25 * (np.cos(ang * 24) > 0.85)
    lens = t <= 0.78
    height += np.where(lens, 0.55 * np.sqrt(np.clip(1 - (t / 0.78) ** 2, 0, 1)), 0)
    alb = bronze_albedo(S, S, height, seed)
    rgb, ao = shade(height, alb, strength=8)
    # amber glass lens with inner light
    glow = np.clip(1 - t / 0.78, 0, 1)
    glass = ramp(glow ** 0.8, [(0, (70, 30, 6)), (.4, (170, 92, 20)), (.75, (240, 176, 70)), (1, (255, 236, 180))])
    gy, gx = np.gradient(height * 8); n = np.dstack([-gx, -gy, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    sp = np.clip((n * H).sum(2), 0, 1) ** 60
    glass = np.clip(glass + sp[..., None] * 0.9, 0, 1)
    rgb = np.where(lens[..., None], glass, rgb)
    alpha = np.clip(R + 0.5 - r, 0, 1)
    save(name, rgb, alpha)

# ---------------------------------------------------------------- stat coins (96): hp salt-shield, ap tide drop, atk, def, cost
def coin(name, kind, S=96, seed=21):
    from PIL import ImageDraw
    m = Image.new('L', (S * 4, S * 4), 0); dr = ImageDraw.Draw(m); c = S * 2
    if kind == 'drop':
        pts = []
        for i in range(181):
            t = i / 180 * 2 * math.pi
            px = math.sin(t) * (math.sin(t / 2) ** 1.4) * 34 * 4; py = -math.cos(t) * 42 * 4
            pts.append((c + px, c + py + 10))
        dr.polygon(pts, fill=255)
    elif kind == 'shield':
        dr.polygon([(c - 128, c - 140), (c + 128, c - 140), (c + 128, c - 10), (c + 60, c + 110), (c, c + 150), (c - 60, c + 110), (c - 128, c - 10)], fill=255)
    else:
        dr.ellipse([c - 160, c - 160, c + 160, c + 160], fill=255)
    mask = np.asarray(m.resize((S, S), Image.LANCZOS)) / 255.0
    inner = blur(mask, 3) > 0.995
    hgt = np.clip(blur(mask, 3) * 1.6 - 0.2, 0, 1) ** 0.7 * 0.8 + inner * 0.15
    y, x = np.mgrid[0:S, 0:S].astype(float)
    rgb, ao = shade(hgt, bronze_albedo(S, S, hgt, seed), strength=5)
    cols = {'drop': [(0, (8, 40, 64)), (.6, (34, 120, 160)), (1, (170, 236, 252))],
            'shield': [(0, (60, 14, 10)), (.6, (150, 40, 28)), (1, (250, 150, 120))],
            'coin': [(0, (40, 26, 6)), (.6, (120, 80, 20)), (1, (230, 190, 110))]}[kind]
    g = np.clip(1 - np.hypot(x - S / 2 + 8, y - S / 2 + 10) / 50, 0, 1)
    fill = ramp(g, cols) * (0.75 + 0.25 * fbm(S, S, 3, 6, seed))[..., None]
    gy, gx = np.gradient(hgt * 5); n = np.dstack([-gx, -gy, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    fill = np.clip(fill + (np.clip((n * H).sum(2), 0, 1) ** 40 * 0.7)[..., None], 0, 1)
    rgb = np.where(inner[..., None], fill, rgb)
    save(name, rgb, mask)

def logo(name, text='BRINEWAKE', size=300, seed=31):
    from PIL import ImageDraw, ImageFont
    font = ImageFont.truetype(os.path.join(os.path.dirname(__file__), 'fonts', 'CormorantSC-Bold.ttf'), size * 4)
    tw = int(font.getlength(text) + size * 4 * 0.6) + 200; th = int(size * 4 * 1.25)
    m = Image.new('L', (tw, th), 0); dr = ImageDraw.Draw(m)
    spacing = size * 4 * 0.06; x = 100
    for ch in text:
        dr.text((x, size * 0.3), ch, font=font, fill=255); x += font.getlength(ch) + spacing
    bbox = m.getbbox(); m = m.crop((bbox[0] - 60, bbox[1] - 60, bbox[2] + 60, bbox[3] + 90))
    W, Hh = m.width // 4, m.height // 4
    mask = np.asarray(m.resize((W, Hh), Image.LANCZOS)) / 255.0
    hgt = np.clip(blur(mask, 4) * 1.5 - 0.25, 0, 1) ** 0.6
    hgt += (fbm(Hh, W, 5, 8, seed) - 0.5) * 0.07 * mask
    alb = bronze_albedo(Hh, W, hgt * 0.8 + 0.15, seed)
    rgb, ao = shade(hgt, alb, strength=9, spec=0.8, gloss=30)
    sc = salt_crust(Hh, W, mask * (1 - smooth(0.3, 0.8, hgt)), seed + 4, 0.9)
    rgb = rgb * (1 - sc[..., None] * 0.35) + SALT * sc[..., None] * 0.35
    # baked drop shadow + dark outline for legibility on any background
    sh = np.roll(np.roll(blur(mask, 5), 6, 0), 3, 1)
    outline = np.clip(blur(mask, 2) * 3, 0, 1)
    a = np.clip(np.maximum(mask, np.maximum(outline * 0.95, sh * 0.75)), 0, 1)
    rgb = np.where((mask > 0.5)[..., None], rgb, np.array([0.04, 0.03, 0.02]))
    save(name, rgb, a)

import sys
if len(sys.argv) > 1 and sys.argv[1] == 'logo':
    logo('logo.png'); sys.exit()
logo('logo.png')
frame('frame.png')
frame('frame_sm.png', S=128, band=16, seed=2)
slate('slate.png')
plate('plate.png')
plate('plate_gold.png', seed=6, tone=0.35, inset_col=(70, 46, 12))
medallion('endturn.png')
coin('coin_tide.png', 'drop'); coin('coin_hp.png', 'shield'); coin('coin_round.png', 'coin', seed=23)

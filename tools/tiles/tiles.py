#!/usr/bin/env python3
"""Brinewake painted isometric terrain tile generator.

Usage: python3 tools/tiles/tiles.py [terrain_id ...]   (no args = every terrain; ids = only those, so
existing tiles are left untouched). Env: EBB_CONTENT (content dir), EBB_PATCH (patch json path, "" = none).

Outputs (under content/tiles/):
  <id>_top_0..2.png   128x64 diamond tops, transparent outside, lit from top-left.
                      Painted natively at 2x (256x128) and downsampled for crispness.
                      For water-like terrains (brine_pool, brine_lake, lamp_oil) the three
                      tops are animation frames that loop.
  <id>_side.png       64x64 seamless cliff texture at neutral lighting.
  <id>_prop_N.png     optional small decals anchored bottom-centre.
and world/tiles_patch.json.

Everything is painted in a periodic square "ground space" (S x S pixels, G x G logical units) and
then projected onto the 2:1 diamond, so features are foreshortened correctly and the same terrain
tiles seamlessly. Variants of one terrain share the structure that touches the diamond edges, so
any two variants knit.
"""
import json, math, os, sys, colorsys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import map_coordinates, gaussian_filter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("EBB_CONTENT", os.path.normpath(os.path.join(HERE, "..", "..", "content")) + os.sep)
OUT = os.path.join(ROOT, "tiles/")
# tiles patch json (the "tiles" blocks for terrain.json). Set EBB_PATCH="" to skip writing it.
PATCH = os.environ.get("EBB_PATCH", os.path.join(HERE, "tiles_patch.json"))
G = 256           # logical ground units (all painting coordinates, widths, radii)
S = 512           # ground-space pixel resolution (2x painting)
K = S / G
SS = 2            # supersampling for the 2x diamond projection
TW, TH = 128, 64  # tile size at 1x (painted at 2x = 256x128)
SIDE = 64

TERRAIN = json.load(open(os.path.join(ROOT, "terrain.json")))
ANIMATED = {"brine_pool", "brine_lake", "lamp_oil", "shallows", "vent"}
SHARED_EDGE = {"wreck", "salt_wall", "living_reef"}   # variants share edge structure, no fade
UNDERLAY = {"brine_pool": "silt", "lamp_oil": "silt", "calcite": "silt", "living_reef": "silt",
            "shallows": "silt"}


# ----------------------------------------------------------------------------- helpers
def hx(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


def mix(a, b, t):
    t = np.asarray(t, np.float32)
    if t.ndim == 2:
        t = t[..., None]
    return a * (1 - t) + b * t


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def pnoise(rng, cells, size=S, cy=None):
    """Periodic value noise in [0,1]; cy gives anisotropic cells (rows)."""
    cy = cells if cy is None else cy
    g = rng.random((cy, cells)).astype(np.float32)
    big = np.tile(g, (3, 3))
    im = Image.fromarray(big, "F").resize((3 * size, 3 * size), Image.BICUBIC)
    return np.asarray(im)[size:2 * size, size:2 * size].copy()


def fbm(rng, base=4, octaves=5, pers=0.5, size=S, aniso=1):
    """aniso>1 stretches features along the column axis (a): rows get aniso x more cells."""
    acc = np.zeros((size, size), np.float32)
    amp, tot, c = 1.0, 0.0, base
    for _ in range(octaves):
        if c * aniso > size:
            break
        acc += amp * pnoise(rng, c, size, cy=int(c * aniso))
        tot += amp
        amp *= pers
        c *= 2
    acc /= tot
    lo, hi = np.percentile(acc, 1), np.percentile(acc, 99)
    return np.clip((acc - lo) / (hi - lo + 1e-6), 0, 1)


def pblur(a, r):
    """Periodic gaussian blur; r in logical units for ground-space arrays."""
    if a.shape[0] == S:
        r = r * K
    return gaussian_filter(a.astype(np.float32), r, mode="wrap")


def sample(arr, x, y):
    return map_coordinates(arr, [y, x], order=1, mode="grid-wrap")


def speckle(rng, p):
    """Sparse 1-logical-unit specks (so they survive the downsample)."""
    m = (rng.random((G, G)) > p).astype(np.float32)
    return np.kron(m, np.ones((int(K), int(K)), np.float32)) > 0


def warp(arr, rng, amt, cells=4):
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    dx = (fbm(rng, cells, 3) - 0.5) * 2 * amt * K
    dy = (fbm(rng, cells, 3) - 0.5) * 2 * amt * K
    return sample(arr, xx + dx, yy + dy)


def voronoi(rng, n, jitter_warp=0.0, size=S):
    """Periodic voronoi; distances returned in logical units."""
    sc = K if size == S else 1.0
    pts = rng.random((n, 2)) * size
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    if jitter_warp:
        xx = xx + (fbm(rng, 4, 3, size=size) - 0.5) * jitter_warp * sc
        yy = yy + (fbm(rng, 4, 3, size=size) - 0.5) * jitter_warp * sc
    f1 = np.full((size, size), 1e9, np.float32)
    f2 = np.full((size, size), 1e9, np.float32)
    idx = np.zeros((size, size), np.int32)
    for i, (px, py) in enumerate(pts):
        dx = np.abs(xx - px) % size
        dy = np.abs(yy - py) % size
        dx = np.minimum(dx, size - dx)
        dy = np.minimum(dy, size - dy)
        d = np.sqrt(dx * dx + dy * dy)
        closer = d < f1
        f2 = np.where(closer, f1, np.minimum(f2, d))
        idx = np.where(closer, i, idx)
        f1 = np.where(closer, d, f1)
    return f1 / sc, f2 / sc, idx, pts


class PCanvas:
    """Periodic drawing canvas (float32 grayscale) in logical coordinates; draws 9x with wrap."""

    def __init__(self, size=S, scale=2, logical=None):
        self.size = size
        self.L = logical if logical is not None else (G if size == S else size)
        self.k = scale * size / self.L
        self.im = Image.new("F", (size * scale, size * scale), 0.0)
        self.d = ImageDraw.Draw(self.im)

    def _offs(self):
        n = self.L * self.k
        return [(ox, oy) for ox in (-n, 0, n) for oy in (-n, 0, n)]

    def line(self, pts, width, val, caps=True):
        k = self.k
        for ox, oy in self._offs():
            p = [(x * k + ox, y * k + oy) for x, y in pts]
            self.d.line(p, fill=float(val), width=max(1, int(round(width * k))), joint="curve")
            if caps:
                r = width * k / 2
                for x, y in (p[0], p[-1]):
                    self.d.ellipse([x - r, y - r, x + r, y + r], fill=float(val))

    def ellipse(self, cx, cy, rx, ry, val):
        k = self.k
        for ox, oy in self._offs():
            x, y = cx * k + ox, cy * k + oy
            self.d.ellipse([x - rx * k, y - ry * k, x + rx * k, y + ry * k], fill=float(val))

    def polygon(self, pts, val):
        k = self.k
        for ox, oy in self._offs():
            self.d.polygon([(x * k + ox, y * k + oy) for x, y in pts], fill=float(val))

    def get(self):
        return np.asarray(self.im.resize((self.size, self.size), Image.BOX)).astype(np.float32)


def strokes(rng, n, length, width, angle=None, spread=math.pi, curve=0.3):
    """Brush-stroke texture in [-1,1]: light and dark dabs, optionally oriented."""
    out = np.zeros((S, S), np.float32)
    for sign in (1, -1):
        c = PCanvas(scale=1)
        for _ in range(n):
            x, y = rng.random() * G, rng.random() * G
            ang = (angle if angle is not None else 0) + (rng.random() - 0.5) * spread
            L = length * (0.5 + rng.random())
            pts = []
            for t in np.linspace(0, 1, 6):
                a2 = ang + curve * math.sin(t * 3)
                pts.append((x + math.cos(a2) * L * t, y + math.sin(a2) * L * t))
            c.line(pts, width * (0.6 + 0.8 * rng.random()), 0.4 + 0.6 * rng.random())
        out += sign * pblur(c.get(), 1.2)
    return np.clip(out, -1, 1)


LIGHT = np.array([-0.78, -0.38, 0.62], np.float32)
LIGHT /= np.linalg.norm(LIGHT)


def normals(h, k=1.0):
    if h.shape[0] == S:
        k = k * K   # gradients per logical unit
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * k
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * k
    n = np.stack([-gx, -gy, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n


def shade(h, k=1.0):
    n = normals(h, k)
    d = (n @ LIGHT) / LIGHT[2]
    return np.clip(d, 0.25, 1.8), n


def spec(n, power=40):
    v = np.array([0, 0, 1.0], np.float32)
    hv = LIGHT + v
    hv /= np.linalg.norm(hv)
    return np.clip(n @ hv, 0, 1) ** power


def pdelta(cx, cy):
    """Periodic offsets (pixels) from point (cx, cy) in pixel units."""
    dx = (VV - cx + S / 2) % S - S / 2
    dy = (UU - cy + S / 2) % S - S / 2
    return dx, dy


# ----------------------------------------------------------------------------- projection
TW2, TH2 = TW * 2, TH * 2
_ys, _xs = np.mgrid[0:TH2 * SS, 0:TW2 * SS].astype(np.float32)
_px, _py = (_xs + 0.5) / SS / 2, (_ys + 0.5) / SS / 2      # in 1x tile units
DA = ((_px - 64) / 64 + _py / 32) / 2   # along top->right edge  (map +x)
DB = (-(_px - 64) / 64 + _py / 32) / 2  # along top->left edge   (map +y)
INSIDE = ((DA >= 0) & (DA <= 1) & (DB >= 0) & (DB <= 1)).astype(np.float32)
EDGE_D = np.minimum(np.minimum(DA, 1 - DA), np.minimum(DB, 1 - DB))


def project(rgb, alpha=None, knit=0.0, grain=0.025, rng=None, ret2x=False):
    """Square ground-space RGB(A) -> 256x128 painted diamond -> 128x64 RGBA.

    Colour is sampled over the whole 2x canvas (ground space is periodic, so it is valid past the
    diamond), which lets the 2x->1x Lanczos + unsharp run without dark/bright rims at the edge."""
    sx, sy = DA * S - 0.5, DB * S - 0.5
    col = np.stack([sample(rgb[..., i], sx, sy) for i in range(3)], -1)
    a = INSIDE.copy()
    if alpha is not None:
        a *= np.clip(sample(alpha, sx, sy), 0, 1)
    if knit:
        col *= (1 - knit * np.exp(-EDGE_D / 0.018))[..., None]
    col = col.reshape(TH2, SS, TW2, SS, 3).mean(axis=(1, 3))         # 2x painted tile
    a2 = a.reshape(TH2, SS, TW2, SS).mean(axis=(1, 3))
    if grain and rng is not None:
        col = col * (1 + rng.normal(0, grain, (TH2, TW2, 1)).astype(np.float32))
    rgb2 = Image.fromarray((np.clip(col, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB")
    rgb1 = rgb2.resize((TW, TH), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=0.8, percent=35, threshold=1))
    a1 = a2.reshape(TH, 2, TW, 2).mean(axis=(1, 3))
    out = rgb1.copy()
    out.putalpha(Image.fromarray((np.clip(a1, 0, 1) * 255 + 0.5).astype(np.uint8), "L"))
    if ret2x:
        im2 = rgb2.copy()
        im2.putalpha(Image.fromarray((np.clip(a2, 0, 1) * 255 + 0.5).astype(np.uint8), "L"))
        return out, im2
    return out


# ----------------------------------------------------------------------------- shared grounds
UU, VV = np.mgrid[0:S, 0:S].astype(np.float32)  # VV = column (a), UU = row (b)
A_, B_ = VV / S, UU / S
DG = np.minimum(np.minimum(A_, 1 - A_), np.minimum(B_, 1 - B_))   # distance to diamond edge


def silt_ground(rng, base=None, ripple=1.0):
    base = hx(TERRAIN["silt"]["color"]) if base is None else base
    f = fbm(rng, 3, 6)
    fine = fbm(rng, 16, 3)
    w = fbm(rng, 3, 3)
    ph = (A_ * 3 + B_ * 1) * 2 * math.pi + w * 4.0
    rip = np.sin(ph) * (0.6 + 0.4 * fbm(rng, 2, 2))
    h = 0.32 * rip * ripple + 0.6 * f + 0.12 * fine
    col = mix(base * 0.86, base * 1.12, f[..., None] * 0.7 + 0.3 * fine[..., None])
    col = mix(col, col * np.array([1.06, 1.02, 0.94]), smooth(0.4, 1, rip)[..., None] * 0.6 * ripple)
    st = strokes(rng, 90, 26, 5, angle=math.atan2(1, -3) + math.pi / 2, spread=0.5)
    col *= (1 + 0.05 * st)[..., None]
    # specks / grit
    sp = speckle(rng, 0.992)
    col[sp] *= 0.7
    return col, h



def level_edges(col, width=0.05, step=0.005):
    """Equalise brightness along the diamond edges with the tile average. Every variant meets its
    neighbours through the same edge texture, so a dark or bright streak that happens to lie on
    the edge line would otherwise repeat around every tile of that terrain (and read as an outline
    against other terrains). The gain depends only on distance-to-edge, so tiling is unaffected."""
    L = col.mean(-1)
    g = L.mean()
    cs = np.arange(0, width, step) + step / 2
    r = np.array([g / max(1e-4, L[(DG >= c - step / 2) & (DG < c + step / 2)].mean()) for c in cs])
    gain = np.interp(DG, np.r_[cs, width + step], np.r_[r, 1.0])
    return col * gain[..., None]


# ----------------------------------------------------------------------------- terrains
def t_salt_flat(rng, v, frame):
    base = mix(hx(TERRAIN["salt_flat"]["color"]), hx("#e8e4d8"), 0.25)
    f = fbm(rng, 3, 5)
    f1, f2, idx, pts = voronoi(rng, 8 + 2 * v, jitter_warp=48)
    g1, g2, _, _ = voronoi(rng, 34, jitter_warp=24)
    edge = f2 - f1
    crack = 1 - smooth(0.2, 1.1, edge)
    fine = (1 - smooth(0.1, 0.7, g2 - g1)) * smooth(0.45, 0.8, fbm(rng, 4, 3))
    tone = rng.random(len(pts)).astype(np.float32)[idx]
    h = np.clip(edge, 0, 14) / 14 * 0.5 + 0.35 * f - crack * 0.35 - fine * 0.12
    s, n = shade(pblur(h, 0.8), 2.2)
    col = base * (0.95 + 0.06 * tone[..., None] + 0.12 * (f[..., None] - 0.5))
    st = strokes(rng, 120, 18, 4)
    col = col * (1 + 0.04 * st[..., None])
    col = col * s[..., None]
    crackcol = np.array([0.50, 0.55, 0.62], np.float32)
    col = mix(col, crackcol, crack * 0.7)
    col = mix(col, crackcol * 1.2, fine * 0.3)
    # faint sheen
    sh = smooth(0.55, 0.95, fbm(rng, 2, 3))
    col = col + (sh * 0.08)[..., None] * np.array([0.9, 0.95, 1.0]) + 0.1 * spec(n, 25)[..., None]
    return col, None


def t_silt(rng, v, frame):
    col, h = silt_ground(rng)
    s, _ = shade(pblur(h, 1.0), 3.5)
    return col * s[..., None], None


def branch_layer(rng, n, depth=3, length=30, width=4.5):
    c = PCanvas()

    def br(x, y, ang, L, w, d):
        pts = [(x, y)]
        for i in range(4):
            ang += (rng.random() - 0.5) * 0.5
            x += math.cos(ang) * L / 4
            y += math.sin(ang) * L / 4
            pts.append((x, y))
        c.line(pts, w, 1.0)
        if d > 0:
            for s_ in (-1, 1):
                if rng.random() < 0.85:
                    br(x, y, ang + s_ * (0.4 + rng.random() * 0.6), L * 0.7, w * 0.7, d - 1)
    for _ in range(n):
        br(rng.random() * G, rng.random() * G, rng.random() * 6.28, length * (0.7 + rng.random() * 0.6),
           width, depth)
    return c.get()


def t_dead_coral(rng, v, frame):
    coral = hx(TERRAIN["dead_coral"]["color"])
    g, h = silt_ground(rng, base=mix(hx(TERRAIN["silt"]["color"]), coral, 0.45), ripple=0.5)
    m = branch_layer(rng, 5 + v, depth=3, length=44, width=8)
    hb = pblur(m, 2.0)
    h = h * 0.4 + hb * 3.0
    s, n = shade(h, 4.0)
    tone = fbm(rng, 6, 3)
    ccol = mix(coral * 1.15, mix(coral, hx("#e2cfc8"), 0.7), tone[..., None])
    ao = pblur(m, 5)  # contact shadow under branches
    g = g * (1 - 0.35 * np.clip(ao * 1.5, 0, 1))[..., None]
    col = mix(g, ccol, np.clip(m * 1.2, 0, 1))
    col = col * s[..., None] + 0.08 * spec(n, 20)[..., None] * m[..., None]
    return col, None


def water_layers(rng, frame, nframes=3):
    th = 2 * math.pi * frame / nframes
    n1, n2 = fbm(rng, 6, 4), fbm(rng, 6, 4)
    m1, m2 = fbm(rng, 3, 3), fbm(rng, 3, 3)
    r = (n1 - 0.5) * math.cos(th) + (n2 - 0.5) * math.sin(th)
    big = (m1 - 0.5) * math.cos(th) + (m2 - 0.5) * math.sin(th)
    return r, big


def pool_mask(rng, inset=0.08, wob=0.07):
    p = 3.2
    d = (np.abs(A_ - 0.5) ** p + np.abs(B_ - 0.5) ** p) ** (1 / p)
    e = inset + wob * fbm(rng, 4, 3)
    return (0.5 - d) - e  # >0 inside water


def t_brine_pool(rng, v, frame):
    water = hx(TERRAIN["brine_pool"]["color"])
    st = np.random.default_rng(1234)  # shared shape across frames
    m = pool_mask(st, 0.03, 0.08)
    r, big = water_layers(np.random.default_rng(99), frame)
    depth = smooth(0.0, 0.22, m)
    inside = smooth(-0.004, 0.006, m)
    rim = smooth(-0.07, -0.0, m) * (1 - inside)
    col = mix(water * 1.15, water * np.array([0.45, 0.6, 0.65]), depth[..., None])
    h = r * 0.8 + big * 0.6
    s, n = shade(h, 10)
    col = col * (0.85 + 0.15 * s[..., None])
    caust = np.abs(np.sin((r * 6 + big * 3) * math.pi))
    caust = (1 - smooth(0.0, 0.12, caust)) * depth * 0.35
    col = col + caust[..., None] * hx("#9fe8df")
    col = col + 0.7 * spec(n, 60)[..., None] * inside[..., None]
    # bright lip just inside the edge
    lip = smooth(0.0, 0.01, m) * smooth(0.04, 0.012, m)
    col = mix(col, hx("#c9efe6"), lip * 0.55)
    wet = np.array([0.22, 0.2, 0.17], np.float32)
    col = np.where(inside[..., None] > 0.5, col, wet)
    alpha = np.maximum(inside * (0.8 + 0.15 * depth), rim * 0.55)
    return col, alpha


def t_trench(rng, v, frame):
    base = hx(TERRAIN["trench"]["color"])
    f = fbm(rng, 4, 4)
    col = base * (0.8 + 0.5 * f[..., None])
    low = np.maximum(A_, B_)  # 1 at the bottom edges
    glow = 0.25 * fbm(rng, 3, 2)
    col = col + glow[..., None] * hx("#3fd1c4") * 0.18
    sp = speckle(rng, 0.9993).astype(np.float32)
    col = col + pblur(sp, 1.0)[..., None] * hx("#3fd1c4") * 2.0
    return col, None


def t_bone_road(rng, v, frame):
    base = hx(TERRAIN["bone_road"]["color"])
    bone = hx("#d9d0b4")
    f = fbm(rng, 4, 5)
    nrib = 5
    curve = 0.10 * ((A_ - 0.5) * 2) ** 2
    t = (B_ + curve) * nrib
    u = t % 1.0
    rid = np.floor(t)
    gap = 1 - smooth(0.0, 0.12, u) * smooth(1.0, 0.88, u)
    # vertebra body in the middle of each rib
    vb = np.clip(1 - (((A_ - 0.5) / 0.13) ** 2 + ((u - 0.5) / 0.45) ** 2), 0, 1) ** 0.5
    h = (1 - gap) * np.sin(np.clip(u, 0, 1) * math.pi) * 0.8 + vb * 0.9 + 0.2 * f
    s, n = shade(pblur(h, 0.8), 4.0)
    rt = (np.sin(rid * 7.13 + v) * 999) % 1
    col = mix(base * 0.95, bone * 1.05, (0.5 * f + 0.3 * rt + 0.4 * vb)[..., None].clip(0, 1))
    cr = 1 - smooth(0.0, 0.08, np.abs(fbm(rng, 10, 3) - 0.5))
    col = mix(col, base * 0.6, cr * 0.35 * (1 - gap))
    under = hx(TERRAIN["silt"]["color"]) * 0.55
    col = mix(col, under * 0.7, gap)
    col = col * s[..., None] + 0.1 * spec(n, 25)[..., None]
    col *= (1 + 0.04 * strokes(rng, 80, 20, 4, angle=0, spread=0.6))[..., None]
    return col, None


def t_kelp_husk(rng, v, frame):
    base = hx(TERRAIN["kelp_husk"]["color"])
    pal = [base, base * 1.3, mix(base, hx("#7a6a3a"), 0.5), mix(base, hx("#8a7a4a"), 0.7), base * 0.8]
    g, gh = silt_ground(rng, base=mix(hx(TERRAIN["silt"]["color"]), base, 0.5) * 0.6, ripple=0.3)
    col = g.copy()
    h = gh * 0.2
    for layer in range(4):
        c = PCanvas()
        n = 18
        for _ in range(n):
            x, y = rng.random() * G, rng.random() * G
            ang = rng.random() * 6.28
            pts = [(x, y)]
            for i in range(8):
                ang += (rng.random() - 0.5) * 1.1
                x += math.cos(ang) * 9
                y += math.sin(ang) * 9
                pts.append((x, y))
            c.line(pts, 6 + rng.random() * 5, 1.0)
        m = c.get()
        lc = pal[rng.integers(len(pal))] * (0.9 + 0.2 * fbm(rng, 6, 2)[..., None])
        col = col * (1 - 0.35 * pblur(m, 3)[..., None])  # shadow from upper layer
        col = mix(col, lc, m)
        h = h + pblur(m, 1.0) * (0.8 + layer * 0.3)
    s, n = shade(h, 3.0)
    col = col * s[..., None] + 0.06 * spec(n, 15)[..., None]
    return col, None


def t_lighthouse_stone(rng, v, frame):
    base = mix(hx(TERRAIN["lighthouse_stone"]["color"]), hx("#a8b2b9"), 0.3)
    rows = 2
    r = B_ * rows
    ri = np.floor(r)
    off = (ri % 2) * 0.5
    c = A_ * 2 + off
    ci = np.floor(c)
    wob = (fbm(rng, 8, 3) - 0.5) * 0.06
    du = np.minimum(r % 1, 1 - r % 1) / rows + wob * 0.2
    dv = np.minimum(c % 1, 1 - c % 1) / 2 + wob * 0.2
    d = np.minimum(du, dv)
    mortar = 1 - smooth(0.006, 0.014, d)
    bevel = smooth(0.006, 0.04, d)
    bid = (np.sin(ri * 91.7 + (ci % 2) * 37.1 + v * 13) * 4375.5) % 1
    f = fbm(rng, 5, 5)
    h = bevel * 0.8 + 0.25 * f - mortar * 0.3
    s, n = shade(pblur(h, 0.6), 4.0)
    col = base * (0.88 + 0.18 * bid[..., None] + 0.14 * (f[..., None] - 0.5))
    col = mix(col, col * np.array([1.05, 1.0, 0.92]), smooth(0.6, 0.9, fbm(rng, 3, 3)) * 0.5)
    col = col * (1 + 0.05 * strokes(rng, 80, 16, 4))[..., None]
    col = col * s[..., None]
    col = mix(col, base * 0.35, mortar * 0.9)
    # chips
    chip = smooth(0.75, 0.85, fbm(rng, 12, 3)) * (1 - mortar)
    col = mix(col, base * 0.6, chip * 0.4)
    # brass fitting (one ring per tile, variant-placed)
    bx, by = [(0.3, 0.62), (0.7, 0.4), (0.5, 0.85)][v]
    rr = np.sqrt(((A_ - bx) * 1) ** 2 + ((B_ - by) * 1) ** 2)
    ring = smooth(0.045, 0.035, rr) * smooth(0.018, 0.026, rr)
    plate = smooth(0.03, 0.02, rr)
    brass = hx("#b08a3c")
    col = mix(col, brass * 0.55, plate * 0.8)
    col = mix(col, brass * (1.1 + 0.4 * (B_ < by)[..., None]), ring)
    # faint gold glow at the tile rim
    dd = np.minimum(np.minimum(A_, 1 - A_), np.minimum(B_, 1 - B_))
    col = col + (np.exp(-dd / 0.03) * 0.05)[..., None] * hx("#e3b04b")
    return col, None


def t_calcite(rng, v, frame):
    c0 = hx(TERRAIN["calcite"]["color"])
    c1 = hx("#f1e9df")
    dens = fbm(rng, 3, 3)
    hgt = np.zeros((S, S), np.float32)
    for i in range(260 + 60 * v):
        cx, cy = rng.random() * S, rng.random() * S
        if rng.random() > dens[int(cy) % S, int(cx) % S] * 1.3:
            continue
        rad = (1.5 + rng.random() ** 2 * 7) * K
        dx = (VV - cx + S / 2) % S - S / 2
        dy = (UU - cy + S / 2) % S - S / 2
        dome = np.clip(1 - (dx * dx + dy * dy) / (rad * rad), 0, 1) ** 0.5 * rad / K / 6
        hgt = np.maximum(hgt, dome)
    s, n = shade(pblur(hgt, 0.6), 8)
    col = mix(c0, c1, fbm(rng, 10, 3)[..., None]) * s[..., None]
    crumb = smooth(0.0, 0.06, hgt)
    dust = smooth(0.35, 0.9, dens) * 0.45
    col = np.where(crumb[..., None] > 0.05, col, mix(c0, c1, 0.5) * 0.95)
    alpha = np.maximum(crumb, dust * (0.6 + 0.4 * fbm(rng, 16, 2)))
    shadow = pblur(crumb, 2.0) * (1 - crumb)
    col = np.where((shadow[..., None] > 0.2) & (crumb[..., None] < 0.05), col * 0.55, col)
    return col, alpha


def _plank_layout(seed, NP):
    """Shared plank joints so every wreck variant knits: per plank, joints j1<j2 (or none)."""
    r = np.random.default_rng(seed)
    return [(0.12 + r.random() * 0.3, 0.58 + r.random() * 0.3) if r.random() < 0.5 else None
            for _ in range(NP)]


def t_wreck(rng, v, frame):
    base = hx(TERRAIN["wreck"]["color"])
    NP = 5                                     # planks per tile, all running along +a in every variant
    shared = np.random.default_rng(4242)       # structure touching the edges is shared by all variants
    wob = (fbm(shared, 3, 3) - 0.5) * 0.12 + (fbm(shared, 2, 2) - 0.5) * 0.08
    t = B_ * NP + wob                          # across planks (hand-shaped wavy edges)
    pid = np.floor(t).astype(int) % NP
    u = t % 1.0
    s = A_
    joints = _plank_layout(777 + v * 13, NP)
    jarr = np.array([j if j else (2.0, 2.0) for j in joints], np.float32)
    j1, j2 = jarr[pid, 0], jarr[pid, 1]
    jag = (fbm(rng, 12, 2) - 0.5) * 0.018      # splintered, hand-cut butt joints
    seg = ((s > j1 + jag) & (s < j2 + jag)).astype(np.int32)   # 0: edge-wrapping segment (shared tone)
    st_tone = np.random.default_rng(99).random(NP).astype(np.float32)
    var_tone = rng.random(NP).astype(np.float32)
    tone = np.where(seg == 1, var_tone[pid], st_tone[pid])
    # gaps between planks, varying width, and butt-joint gaps
    gw = 0.05 + 0.03 * fbm(shared, 6, 2)
    gap = 1 - smooth(0.0, gw, u) * smooth(1.0, 1 - gw, u)
    dj = np.minimum(np.abs(s - j1 - jag), np.abs(s - j2 - jag))
    jgap = 1 - smooth(0.002, 0.007, dj)
    # long grain along the plank, offset per segment, plus a couple of knots
    gn = fbm(shared if v == 0 else rng, 2, 4, aniso=12)
    grain = np.sin(2 * math.pi * (u * 2.5 + gn * 3.0 + tone * 5 + seg * 0.37)) * 0.5 + 0.5
    fine = fbm(shared, 4, 3, aniso=16)
    adze = np.abs(np.sin(math.pi * (s * 23 + tone * 7 + 0.3 * fbm(shared, 4, 2)))) ** 0.5
    # rounded, worn plank profile
    prof = np.clip(np.sin(np.clip(u, 0, 1) * math.pi), 0, 1) ** 0.35
    endround = smooth(0.0, 0.03, dj)
    h = prof * endround * 0.8 + 0.06 * grain + 0.05 * fine - 0.05 * adze
    wood = mix(base * 0.62, base * 1.32, (0.45 * tone + 0.3 * grain + 0.25 * fine)[..., None])
    weather = smooth(0.45, 0.85, fbm(shared, 3, 4))
    wood = mix(wood, mix(wood, hx("#8a8172"), 0.45), weather * 0.55)          # grey sea-bleach
    rot = smooth(0.62, 0.9, fbm(rng, 3, 4)) * (DG > 0.08)
    wood = mix(wood, np.array([0.16, 0.13, 0.10], np.float32), rot * 0.35)
    # treenails on the two (shared) frame lines + nails at butt joints
    pegs = np.zeros((S, S), np.float32)
    for fs in (0.25, 0.75):
        d = np.sqrt(((s - fs) * NP * 1.2) ** 2 + (u - 0.5) ** 2)
        pegs = np.maximum(pegs, smooth(0.13, 0.08, d))
    iron = np.zeros((S, S), np.float32)
    riv = np.zeros((S, S), np.float32)
    rustbleed = np.zeros((S, S), np.float32)
    hole = np.zeros((S, S), np.float32)
    if v >= 1:   # iron strap across the planks (stops short of the edges so variants still knit)
        b0 = [0, 0.47, 0.6][v]
        wv = (fbm(rng, 3, 2) - 0.5) * 0.01
        db = np.abs(s - b0 - wv)
        ends = smooth(0.1, 0.16, B_) * smooth(0.9, 0.84, B_)
        iron = smooth(0.05, 0.042, db) * ends
        for k_ in range(NP):
            bc = (k_ + 0.5) / NP
            for ds in (-0.024, 0.024):
                d = np.sqrt(((s - b0 - ds) * 1.0) ** 2 + ((B_ - bc) * 0.9) ** 2)
                riv = np.maximum(riv, smooth(0.013, 0.008, d) * ends)
        rustbleed = np.exp(-np.clip(s - b0, 0, 1) / 0.06) * (s > b0) * ends * (fbm(rng, 10, 3, aniso=6) * 1.2)
    if v == 2:   # one plank segment torn out: dark void with the frame timber below
        p = 1
        jj = joints[p] or (0.3, 0.7)
        jag2 = (fbm(rng, 24, 2) - 0.5) * 0.05
        hole = ((pid == p) & (s > jj[0] + 0.03 + jag2) & (s < jj[1] - 0.03 - jag2)).astype(np.float32)
    # barnacle crust along some gaps
    barn = speckle(rng, 0.985).astype(np.float32) * smooth(0.3, 0.9, gap + jgap) * (fbm(rng, 4, 2) > 0.5)
    barn = pblur(barn, 0.8) * 3
    rcol = hx("#2e2b2a")
    rust = hx("#a8552e")
    ironcol = mix(rcol * 1.3, rust * 0.9, (smooth(0.35, 0.9, fbm(rng, 8, 3)) * 0.8)[..., None])
    ironcol = ironcol * (0.85 + 0.3 * fbm(rng, 20, 2))[..., None]
    h = h * (1 - hole) + iron * (0.55 + 0.1 * fbm(rng, 16, 2)) + riv * 0.45 + pegs * 0.08 + barn * 0.2
    sh, n = shade(pblur(h, 0.45), 3.2)
    col = wood
    col = mix(col, mix(col, rust * 0.8, 0.6), np.clip(rustbleed, 0, 1) * 0.6)
    col = mix(col, base * 0.45, pegs * 0.7)
    col = mix(col, ironcol, iron)
    col = mix(col, rcol * 1.6, riv)
    col = mix(col, hx("#cfc6b4"), np.clip(barn, 0, 1) * 0.6)
    # the hole: frame timber under it running across (along b), void around it
    frame_ = smooth(0.06, 0.045, np.abs(s - 0.5 - 0.1 * (v == 2))) * hole
    silt = hx(TERRAIN["silt"]["color"]) * 0.32 * (0.8 + 0.4 * fbm(rng, 10, 2))[..., None]
    void = mix(silt, base * 0.55, frame_)
    void = void * (0.35 + 0.65 * smooth(0.0, 0.6, u))[..., None] * 0.8   # plank edge shadow
    col = col * sh[..., None]
    gapdark = np.clip(gap * 0.9 + jgap * 0.8, 0, 1)
    col = mix(col, np.array([0.05, 0.04, 0.035], np.float32), gapdark * (1 - hole))
    col = mix(col, void, hole)
    if v == 2:   # pale splintered lip where the plank tore
        lip = np.clip(pblur(hole, 0.9) * 2.5, 0, 1) * (1 - hole) * (1 - gapdark)
        col = mix(col, base * 1.6 * sh[..., None], lip * 0.7)
    col = col + (0.3 * spec(n, 20) * np.clip(iron + riv, 0, 1))[..., None]
    col = mix(col, col * 0.55, pblur(iron, 1.5) * (1 - iron) * 0.8)   # strap shadow
    col *= (1 + 0.04 * strokes(rng, 50, 30, 3, angle=0, spread=0.25))[..., None]
    return col, None


def _slick_field(seed):
    """Signed distance-ish field (>0 inside) of an irregular oil slick, kept off the tile edges."""
    r = np.random.default_rng(seed)
    w1, w2 = fbm(r, 3, 3) - 0.5, fbm(r, 3, 3) - 0.5
    ax, bx = A_ + w1 * 0.16, B_ + w2 * 0.16
    d = np.sqrt((ax - 0.5) ** 2 + (bx - 0.52) ** 2)
    lobes = (fbm(r, 5, 3) - 0.5) * 0.12
    m = 0.33 - d + lobes
    # satellite droplets
    for _ in range(5):
        cx, cy = 0.5 + (r.random() - 0.5) * 0.7, 0.5 + (r.random() - 0.5) * 0.7
        rr = 0.015 + r.random() * 0.025
        m = np.maximum(m, rr - np.sqrt((A_ - cx) ** 2 + (B_ - cy) ** 2))
    return np.minimum(m, DG - 0.05)


def _cyc(rng, frame, cells, oct_, n=3):
    th = 2 * math.pi * frame / n
    a, b = fbm(rng, cells, oct_), fbm(rng, cells, oct_)
    return (a - 0.5) * math.cos(th) + (b - 0.5) * math.sin(th)


def t_lamp_oil(rng, v, frame):
    amber = hx(TERRAIN["lamp_oil"]["color"])
    m = _slick_field(7071)
    inside = smooth(-0.002, 0.002, m)
    thick = smooth(0.0, 0.07, m)
    swell = _cyc(np.random.default_rng(55), frame, 3, 3)
    ripple = _cyc(np.random.default_rng(56), frame, 7, 3)
    dark = np.array([0.075, 0.045, 0.02], np.float32)
    col = mix(amber * 0.95, dark, thick[..., None] ** 0.7)
    col = mix(col, dark * 0.7, smooth(0.08, 0.2, m)[..., None])
    # surface: domed meniscus at the rim + slow swell -> broad amber gloss
    h = np.sqrt(np.clip(m, 0, 0.05) / 0.05) * 0.035 + swell * 0.012 + ripple * 0.003
    n = normals(pblur(h, 1.2), 60)
    gloss = spec(n, 14)
    sharp = spec(n, 160)
    # thin-film rainbow over the dark body, drifting gently per frame
    film = fbm(np.random.default_rng(57), 3, 4) + 0.35 * swell + frame * 0.035
    hue = (film * 1.6) % 1.0
    rb = np.stack(np.vectorize(lambda x: colorsys.hsv_to_rgb(x, 0.55, 1.0), otypes=[float] * 3)(hue), -1)
    bands = (0.5 + 0.5 * np.cos(film * 2 * math.pi * 4)) * smooth(0.25, 0.75, fbm(np.random.default_rng(58), 4, 3))
    col = col + rb.astype(np.float32) * (bands * thick * 0.17)[..., None]
    col = col + (gloss * 0.55)[..., None] * hx("#f0a640") + (sharp * 1.1)[..., None] * hx("#fff0c8")
    rim = smooth(0.0, 0.004, m) * smooth(0.016, 0.005, m)
    col = mix(col, hx("#f6b552"), rim * 0.65)
    # oily stain soaked into the silt around it
    stain = smooth(-0.03, -0.002, m) * (1 - inside) * (0.55 + 0.45 * fbm(np.random.default_rng(59), 12, 2))
    col = np.where(inside[..., None] > 0.5, col, np.array([0.11, 0.075, 0.04], np.float32))
    alpha = np.maximum(inside * 0.97, stain * 0.5)
    return col, alpha


def t_brine_lake(rng, v, frame):
    navy = hx(TERRAIN["brine_lake"]["color"])
    teal = hx("#0f3c43")
    deep = mix(navy, teal, 0.75) * 0.95
    st = np.random.default_rng(42)
    g = fbm(st, 2, 3)
    col = mix(deep * 0.72, deep * 1.12, g[..., None])
    # glowing specks far down: blurred, dim, slowly breathing across frames
    sp = np.zeros((S, S), np.float32)
    for (cx, cy, pw) in ((0.31, 0.63, 1.0), (0.72, 0.36, 0.6)):
        dx, dy = pdelta(cx * S, cy * S)
        r2 = (dx * dx + dy * dy) / (K * K)
        sp += pw * (np.exp(-r2 / 70) * 0.6 + np.exp(-r2 / 4) * 1.2)
    pulse = [1.0, 0.75, 0.88][frame]
    col = col + (sp * pulse * 0.3)[..., None] * hx("#3fd1c4")
    # murk layer over the specks
    col = mix(col, deep * 0.9, 0.15 * fbm(st, 4, 3)[..., None])
    # surface: gentle swell, soft glints and faint crest lines, moving per frame
    r = _cyc(np.random.default_rng(43), frame, 5, 4)
    big = _cyc(np.random.default_rng(44), frame, 2, 3)
    h = big * 0.5 + r * 0.18
    n = normals(pblur(h, 3), 9)
    col = col * (0.92 + 0.12 * ((n @ LIGHT) / LIGHT[2] - 1)[..., None] * 4)
    col = col + (spec(n, 90) * 0.32)[..., None] * hx("#bfe9e4")
    warpf = fbm(st, 3, 3)
    th = 2 * math.pi * frame / 3
    crest = np.sin(2 * math.pi * (A_ * 2 + B_ * 3) + warpf * 5 + th)
    crest = pblur(smooth(0.9, 1.0, crest), 1.5) * smooth(0.4, 0.9, fbm(st, 4, 2))
    col = col + (crest * 0.035)[..., None] * hx("#cfeee8")
    return col, None


def _facet_crystals(centres, H, base=0.75):
    """Truncated faceted pyramids (crisp planar faces) -> height field (max-combined)."""
    for (cx, cy, R, nf, rot, hgt, flat) in centres:
        dx, dy = pdelta(cx * S, cy * S)
        dx, dy = dx / K, dy / K
        if R * 1.6 < 1:
            continue
        sel = (np.abs(dx) < R * 1.4) & (np.abs(dy) < R * 1.4)
        best = np.full(dx.shape, -1e9, np.float32)
        for f in range(nf):
            a = rot + 2 * math.pi * f / nf
            best = np.maximum(best, dx * math.cos(a) + dy * math.sin(a))
        hh = base + np.minimum(hgt * (1 - best / R), hgt * flat)
        H = np.where(sel, np.maximum(H, hh), H)
    return H


def t_salt_wall(rng, v, frame):
    white = hx("#fbfaf6")
    shadowc = hx("#93a5ba")
    midc = hx("#d6dee8")
    shared = np.random.default_rng(31337)
    # crust plates shared by all variants (they reach the edges)
    f1, f2, idx, pts = voronoi(shared, 9, jitter_warp=14)
    nv = shared.normal(0, 1, (len(pts), 2)).astype(np.float32) * 0.035
    cx, cy = pts[idx, 0], pts[idx, 1]
    dx = ((VV - cx + S / 2) % S - S / 2) / K
    dy = ((UU - cy + S / 2) % S - S / 2) / K
    H = 0.6 + nv[idx, 0] * dx + nv[idx, 1] * dy
    crack = f2 - f1
    H = H - 1.2 * (1 - smooth(0.0, 1.6, crack))          # crisp V-cracks between plates
    H = H + 0.25 * fbm(shared, 16, 2)                     # micro crust texture
    # crystal clusters: edge-zone ones shared, interior ones per variant
    cs = []
    for src, n_, interior in ((shared, 12, False), (rng, 7 + 2 * v, True)):
        for _ in range(n_):
            x, y = src.random(), src.random()
            dg = min(x, 1 - x, y, 1 - y)
            if interior != (dg > 0.16):
                continue
            for _c in range(int(src.integers(2, 6))):
                R = 4 + src.random() ** 1.5 * (10 if interior else 6)
                xx_, yy_ = x + (src.random() - .5) * 0.07, y + (src.random() - .5) * 0.07
                if interior and min(xx_, 1 - xx_, yy_, 1 - yy_) < 0.1:
                    continue
                cs.append((xx_, yy_, R, int(src.integers(3, 6)), src.random() * 6.28, R * 1.7,
                           0.8 + src.random() * 0.2))
    Hp = H.copy()
    H = _facet_crystals(cs, H)
    cm = smooth(0.0, 0.04, H - Hp)                       # crystal mask
    n = normals(H, 1.0)
    d = (n @ LIGHT) / LIGHT[2]
    col = mix(shadowc, midc, smooth(0.15, 0.75, d)[..., None])
    plate_white = hx("#eceef0")
    col = mix(col, mix(plate_white, white, cm), smooth(0.72, 1.02, d)[..., None])
    col = col + (smooth(1.02, 1.35, d) * 0.06)[..., None]
    cr = 1 - smooth(0.0, 0.9, crack)
    col = mix(col, shadowc * 0.82, cr * 0.85)
    ao = pblur(cm, 2.0) * (1 - cm)
    col = col * (1 - 0.28 * ao)[..., None] * np.array([1.0, 1.0, 1.0])
    col = mix(col, col * np.array([0.86, 0.9, 0.97]), ao * 0.5)
    # crisp facet ridges: thin bright line where facet orientation changes
    rid = np.clip(np.abs(pblur(H, 0.4) - H) * 30, 0, 1) * cm
    col = col + (rid * 0.08)[..., None]
    col = col + (spec(n, 60) * 0.25)[..., None]
    col = col * (0.985 + 0.03 * fbm(shared, 5, 3))[..., None]
    return col, None


def _coral_colony(c, rng, cx, cy, kind, pal_i, tips, ids, scale=1.0):
    """Draw one branching colony into height canvas c (value = height) and id canvas ids."""
    if kind == "stag":
        nmain, L0, w0, depth, spread, fork = rng.integers(4, 6), 24, 6.5, 3, 0.55, 0.85
    elif kind == "fan":
        nmain, L0, w0, depth, spread, fork = rng.integers(2, 4), 20, 4.2, 4, 0.45, 0.95
    else:  # table / bushy acropora
        nmain, L0, w0, depth, spread, fork = rng.integers(8, 12), 15, 5.0, 2, 0.6, 0.9
    L0, w0 = L0 * scale, w0 * scale
    base_ang = rng.random() * 6.28
    fan_dir = rng.random() * 6.28

    def br(x, y, ang, L, w, d, hgt):
        pts = [(x, y)]
        for _ in range(3):
            ang += (rng.random() - 0.5) * 0.35
            x += math.cos(ang) * L / 3
            y += math.sin(ang) * L / 3
            pts.append((x, y))
        h2 = min(1.0, hgt + 0.18)
        c.line(pts, w, hgt)
        c.line(pts, w * 0.45, h2, caps=False)          # ridge -> rounded branch in the normal map
        ids.line(pts, w, pal_i + 1)
        if d > 0:
            for s_ in (-1, 1):
                if rng.random() < fork:
                    br(x, y, ang + s_ * spread * (0.6 + rng.random() * 0.8), L * 0.74, max(1.0, w * 0.7),
                       d - 1, h2)
        else:
            tips.append((x, y, w))
    for i in range(nmain):
        if kind == "fan":
            a = fan_dir + (i - nmain / 2) * 0.5
        else:
            a = base_ang + 2 * math.pi * i / nmain + (rng.random() - 0.5) * 0.4
        br(cx, cy, a, L0 * (0.75 + rng.random() * 0.5), w0, depth, 0.35)
    if kind == "table":
        c.ellipse(cx, cy, w0 * 1.3, w0 * 1.3, 0.45)
        ids.ellipse(cx, cy, w0 * 1.3, w0 * 1.3, pal_i + 1)


def t_living_reef(rng, v, frame):
    coral = hx(TERRAIN["living_reef"]["color"])
    pal = np.stack([coral, mix(coral, hx("#f0a060"), 0.55), mix(coral, hx("#c05a8a"), 0.55),
                    mix(coral, hx("#e8c070"), 0.45), coral * 0.82])
    tipc = hx("#fbe8d8")
    c, ids = PCanvas(), PCanvas()
    tips = []
    shared = np.random.default_rng(2024)
    # edge-zone colonies shared by all variants (so reef tiles knit), interior ones per variant
    for _ in range(14):
        x, y = shared.random(), shared.random()
        if min(x, 1 - x, y, 1 - y) < 0.07:
            _coral_colony(c, shared, x * G, y * G, "stag", int(shared.integers(5)), tips, ids, scale=0.8)
    kinds = [["stag", "stag", "table"], ["fan", "fan", "stag"], ["table", "table", "fan"]][v]
    placed = 0
    for _ in range(200):
        if placed >= 3 + v // 2:
            break
        x, y = rng.random(), rng.random()
        if min(x, 1 - x, y, 1 - y) < 0.3:
            continue
        _coral_colony(c, rng, x * G, y * G, kinds[placed % 3], int(rng.integers(5)), tips, ids)
        placed += 1
    hm = c.get()
    idm = np.asarray(ids.im.resize((S, S), Image.NEAREST)).astype(np.int32)
    tipm = PCanvas()
    for x, y, w in tips:
        tipm.ellipse(x, y, w * 0.9 + 0.4, w * 0.9 + 0.4, 1.0)
    tm = tipm.get()
    cover = smooth(0.05, 0.3, hm)
    n = normals(pblur(hm, 0.7), 3.5)
    sh = np.clip((n @ LIGHT) / LIGHT[2], 0.35, 1.5)
    P = pal[np.clip(idm - 1, 0, len(pal) - 1)]
    pol = fbm(rng, 30, 2)
    col = P * (0.8 + 0.25 * pol[..., None]) * (0.7 + 0.45 * hm[..., None])
    col = mix(col, tipc, np.clip(tm * 0.85 + smooth(0.8, 1.0, hm) * 0.4, 0, 1))
    col = col * sh[..., None] + 0.12 * spec(n, 25)[..., None] * cover[..., None]
    glow = speckle(rng, 0.9992).astype(np.float32) * (tm > 0.5)
    col = col + pblur(glow, 1.0)[..., None] * hx("#ffd9a0") * 2.5
    shadow = pblur(cover, 2.5) * (1 - cover)
    col = np.where(cover[..., None] > 0.02, col, np.array([0.11, 0.08, 0.07], np.float32))
    alpha = np.maximum(cover, shadow * 0.5)
    return col, alpha


# ----------------------------------------------------------------------------- new terrains
def _rect(c, cx, cy, w, h, ang, val):
    ca, sa = math.cos(ang), math.sin(ang)
    pts = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in
           ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    c.polygon(pts, val)


def _walk(rng, x, y, ang, steps, step, wander, curl=0.0):
    pts = [(x, y)]
    cv = 0.0
    for _ in range(steps):
        cv = cv * 0.8 + (rng.random() - 0.5) * wander + curl * (rng.random() - 0.5)
        ang += cv
        x += math.cos(ang) * step
        y += math.sin(ang) * step
        pts.append((x, y))
    return pts


def t_shallows(rng, v, frame):
    st = np.random.default_rng(2201)                 # silt bed is shared by all frames/variants
    bed, bh = silt_ground(st, base=hx(TERRAIN["silt"]["color"]) * 1.05, ripple=1.4)
    sb, _ = shade(pblur(bh, 1.0), 3.5)
    bed = bed * sb[..., None]
    # refraction: the bed wobbles slowly under the ripples
    r1 = _cyc(np.random.default_rng(2202), frame, 5, 4)
    r2 = _cyc(np.random.default_rng(2203), frame, 5, 4)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    bed = np.stack([sample(bed[..., i], xx + r1 * 14 * K, yy + r2 * 14 * K) for i in range(3)], -1)
    teal = hx("#4fb5b3")
    deep = hx("#2f8a90")
    dp = fbm(np.random.default_rng(2204), 3, 3)
    col = mix(bed, mix(teal, deep, dp[..., None] * 0.7), 0.42 + 0.15 * dp[..., None])
    col = col * (0.96 + 0.1 * dp[..., None])
    # surface ripples -> soft light/dark
    h = _cyc(np.random.default_rng(2205), frame, 6, 4) * 0.9 + _cyc(np.random.default_rng(2206), frame, 3, 3) * 0.5
    n = normals(pblur(h, 1.6), 8)
    col = col * (0.95 + 0.08 * ((n @ LIGHT) / LIGHT[2] - 1)[..., None] * 3)
    # caustics: bright web where two cyclic fields cross zero
    ca = _cyc(np.random.default_rng(2207), frame, 7, 3)
    cb = _cyc(np.random.default_rng(2208), frame, 9, 3)
    web = np.maximum(1 - smooth(0.0, 0.035, np.abs(ca)), 1 - smooth(0.0, 0.03, np.abs(cb)))
    web = pblur(web, 0.7) * (0.5 + 0.5 * smooth(0.3, 0.8, fbm(np.random.default_rng(2209), 4, 3)))
    col = col + (web * 0.16)[..., None] * hx("#bff0e6")
    # sun sparkle
    col = col + (spec(n, 90) * 0.6)[..., None] * hx("#f4fffb")
    sp = pblur(speckle(np.random.default_rng(2210 + frame), 0.9985).astype(np.float32), 0.7) * 3
    col = col + sp[..., None] * hx("#eafffa") * 0.4
    return col, None


def t_vent(rng, v, frame):
    st = np.random.default_rng(2301)                 # fissure structure shared by all frames
    base = hx(TERRAIN["vent"]["color"])
    f = fbm(st, 4, 5)
    fine = fbm(st, 14, 3)
    ground = mix(base * 0.2, base * 0.5, (0.6 * f + 0.4 * fine)[..., None])
    ground = mix(ground, hx("#3a3836"), smooth(0.4, 0.8, fbm(st, 3, 3))[..., None] * 0.7)   # ash drifts
    m = branch_layer(st, 3, depth=3, length=62, width=2.6)
    m = np.maximum(m, warp(branch_layer(st, 2, depth=2, length=70, width=1.4), st, 9, 3))
    m = np.clip(m, 0, 1) * smooth(0.07, 0.22, np.minimum(np.minimum(A_, 1 - A_), np.minimum(B_, 1 - B_)) * 0 + np.minimum(np.hypot(np.minimum(A_, 1 - A_), np.minimum(B_, 1 - B_)), 1))
    core = smooth(0.35, 0.9, pblur(m, 0.6))
    crack = smooth(0.1, 0.6, pblur(m, 0.9))
    halo = pblur(m, 7)
    band = np.clip(pblur(m, 3.6) * 3.0, 0, 1) * (1 - crack)
    hgt = f * 0.5 + fine * 0.1 + band * 0.9 - crack * 1.6
    s, n = shade(pblur(hgt, 0.7), 3.5)
    col = ground * s[..., None]
    # mineral crust: sulphur yellow bands with white bloom
    cn = fbm(st, 9, 4)
    sulph = hx("#d9bf3a") * (0.8 + 0.4 * cn[..., None])
    white = hx("#f0ead8")
    crust = band * smooth(0.25, 0.55, cn + 0.3 * band)
    col = mix(col, sulph * s[..., None], crust * 0.4)
    col = mix(col, white * np.clip(s[..., None], 0.7, 1.2), band * smooth(0.62, 0.82, fbm(st, 14, 3)) * 0.85)
    pulse = [1.0, 0.68, 0.86][frame]
    glow = np.array([1.0, 0.36, 0.08], np.float32)
    hot = np.array([1.0, 0.78, 0.3], np.float32)
    col = col + (halo * 0.55 * pulse)[..., None] * glow * 0.55
    col = mix(col, glow * (0.6 + 0.4 * pulse), crack[..., None] * 0.9)
    col = mix(col, hot * (0.85 + 0.3 * pulse), core[..., None] * 0.55 * pulse)
    col += spec(n, 30)[..., None] * 0.07
    return col, None


def t_tangleweed(rng, v, frame):
    base = hx(TERRAIN["tangleweed"]["color"])
    g, gh = silt_ground(rng, base=mix(hx(TERRAIN["silt"]["color"]), base, 0.45) * 0.55, ripple=0.3)
    col = g.copy()
    h = gh * 0.2
    pal = [(base * 0.85, 0.30), (base * 1.35, 0.22), (mix(base, hx("#5a4a2a"), 0.6) * 0.9, 0.2),
           (mix(base, hx("#2b3a22"), 0.55) * 0.9, 0.16), (hx("#b08a3a") * 0.85, 0.12)]   # last = dead ochre
    for layer in range(5):
        for pc, share in pal:
            c = PCanvas()
            n = int(30 * share * (1.0 + 0.15 * layer))
            for _ in range(n):
                x, y = rng.random() * G, rng.random() * G
                pts = _walk(rng, x, y, rng.random() * 6.28, int(9 + rng.random() * 9), 5.2, 1.3, 1.6)
                c.line(pts, 2.2 + rng.random() * 1.6, 1.0)
            m = c.get()
            m = np.clip(m * 1.3, 0, 1)
            lc = pc * (0.85 + 0.3 * fbm(rng, 8, 2)[..., None]) * (0.85 + 0.08 * layer)
            col = col * (1 - 0.4 * pblur(m, 1.6)[..., None])
            col = mix(col, lc, m)
            h = h + pblur(m, 0.7) * (0.5 + layer * 0.22)
    s, n = shade(pblur(h, 0.4), 3.0)
    col = col * s[..., None] + 0.05 * spec(n, 15)[..., None]
    return col, None


def t_scrap_field(rng, v, frame):
    base = hx(TERRAIN["scrap_field"]["color"])
    g, gh = silt_ground(rng, base=mix(hx(TERRAIN["silt"]["color"]), base, 0.35) * 0.75, ripple=0.35)
    hc, tc, rc = PCanvas(), PCanvas(), PCanvas()      # height, tone (0 = bare silt), rivet/bolt height
    link, gearm = PCanvas(), PCanvas()
    rivets = []
    for i in range(9 + v):
        cx, cy = rng.random() * G, rng.random() * G
        w, hh, ang = 30 + rng.random() * 36, 18 + rng.random() * 26, rng.random() * 3.14
        hv = 0.25 + 0.5 * rng.random()
        _rect(hc, cx, cy, w, hh, ang, hv)
        _rect(tc, cx, cy, w, hh, ang, 0.1 + 0.9 * rng.random())
        ca, sa = math.cos(ang), math.sin(ang)
        for ax in (-1, 1):
            for ay in (-1, 1):
                if rng.random() < 0.8:
                    x0, y0 = ax * (w / 2 - 2.6), ay * (hh / 2 - 2.6)
                    rivets.append((cx + x0 * ca - y0 * sa, cy + x0 * sa + y0 * ca))
        if w > 34 and rng.random() < 0.6:       # mid-edge rivet
            rivets.append((cx + 0.0 * ca, cy + 0.0 * sa))
    for x, y in rivets:
        rc.ellipse(x, y, 1.9, 1.9, 1.0)
    # chain run + loose links
    for _ in range(2):
        x, y = rng.random() * G, rng.random() * G
        pts = _walk(rng, x, y, rng.random() * 6.28, 9, 8.5, 0.7)
        for j in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[j], pts[j + 1]
            if j % 2 == 0:
                link.line([(x0, y0), (x1, y1)], 5.4, 1.0)
                link.line([(x0 + (x1 - x0) * 0.2, y0 + (y1 - y0) * 0.2), (x0 + (x1 - x0) * 0.8, y0 + (y1 - y0) * 0.8)],
                          2.2, 0.0, caps=True)
            else:
                link.ellipse((x0 + x1) / 2, (y0 + y1) / 2, 2.6, 2.6, 1.0)
    # gear (one broken)
    gx, gy = G * (0.3 + 0.4 * rng.random()), G * (0.3 + 0.4 * rng.random())
    teeth, R = 11, 12.0
    for broken in (False,):
        pts = []
        for k_ in range(teeth * 4):
            a = 2 * math.pi * k_ / (teeth * 4)
            r = R + (2.4 if (k_ % 4) in (0, 1) else 0)
            pts.append((gx + math.cos(a) * r, gy + math.sin(a) * r))
        gearm.polygon(pts, 1.0)
        gearm.ellipse(gx, gy, 2.8, 2.8, 0.0)
        # bite taken out of the rim
        ba = rng.random() * 6.28
        gearm.ellipse(gx + math.cos(ba) * R * 1.05, gy + math.sin(ba) * R * 1.05, 4.2, 4.2, 0.0)
    pm = np.clip(pblur(tc.get(), 0.3) * 4, 0, 1)
    tone = tc.get()
    lk, gm, rv = np.clip(link.get(), 0, 1), np.clip(gearm.get(), 0, 1), np.clip(rc.get(), 0, 1)
    cover = np.maximum(pm, np.maximum(lk, gm))
    h = gh * 0.2 + pblur(hc.get(), 0.5) * 1.6 + lk * 0.7 + gm * 0.9 + rv * pm * 0.5
    s, n = shade(pblur(h, 0.4), 3.4)
    rust_a, rust_b = hx("#b4602f"), hx("#6c3d24")
    iron = hx("#4a4540")
    rn = fbm(rng, 9, 4)
    rustc = mix(rust_b, rust_a, (0.5 * tone + 0.5 * rn)[..., None].clip(0, 1))
    rustc = mix(iron * 1.1, rustc, smooth(0.15, 0.55, rn + 0.3 * tone)[..., None])
    rustc = rustc * (0.85 + 0.3 * fbm(rng, 24, 2)[..., None])
    metal = mix(iron, hx("#8a8a86"), 0.5)
    col = g * (1 - 0.5 * pblur(cover, 1.6) * (1 - cover))[..., None]
    col = mix(col, rustc, pm)
    col = mix(col, mix(rustc, metal, 0.7) * 0.9, np.maximum(lk, gm))
    col = mix(col, hx("#d09060") * 1.1, rv * pm * 0.8)
    col = col * s[..., None]
    sharp = spec(n, 28) * cover
    col = col + (sharp * 0.9)[..., None] * hx("#e8e6dc")
    col = col * (1 + 0.05 * strokes(rng, 80, 14, 3))[..., None]
    return col, None


def t_beam_glass(rng, v, frame):
    base = hx(TERRAIN["beam_glass"]["color"])
    sand, sh0 = silt_ground(rng, base=mix(hx(TERRAIN["silt"]["color"]), hx("#cdbf9f"), 0.55), ripple=0.9)
    ss, _ = shade(pblur(sh0, 1.0), 3.0)
    sand = sand * ss[..., None]
    gm = 1 - smooth(0.66, 0.82, fbm(rng, 3, 4)) * smooth(0.14, 0.3, DG) * 0.95   # glass everywhere; sand only as inner patches
    dp = fbm(rng, 3, 4)
    glass = mix(base * 0.62, base * 1.0, dp[..., None])
    glass = mix(glass, hx("#5f9a86"), smooth(0.55, 0.9, fbm(rng, 4, 3))[..., None] * 0.4)
    # radial cracks from a fusion point
    cr = PCanvas()
    cx, cy = G * (0.38 + 0.24 * rng.random()), G * (0.38 + 0.24 * rng.random())
    for k_ in range(9 + v):
        a = 2 * math.pi * k_ / (9 + v) + (rng.random() - .5) * 0.5
        pts = _walk(rng, cx, cy, a, 9, 8.0, 0.35)
        cr.line(pts, 0.9 + rng.random() * 0.6, 1.0)
        if rng.random() < 0.6:
            j = int(3 + rng.random() * 4)
            px, py = pts[j]
            cr.line(_walk(rng, px, py, a + (0.7 if rng.random() < .5 else -0.7), 4, 6, 0.3), 0.7, 1.0)
    cm = cr.get()
    cm = pblur(np.clip(cm, 0, 1), 0.25)
    # smooth glossy surface with long swells; cracks dent it
    h = fbm(rng, 2, 3) * 0.9 + 0.12 * fbm(rng, 6, 2) - cm * 0.5
    n = normals(pblur(h, 1.5), 7)
    d = (n @ LIGHT) / LIGHT[2]
    glass = glass * (0.9 + 0.2 * (d[..., None] - 1) * 2.5 + 0.1)
    glass = mix(glass, hx("#2f5d4e"), (cm * 0.7)[..., None])
    glass = glass + (np.clip(pblur(cm, 0.8) - cm, 0, 1) * 0.5)[..., None] * hx("#e9fff4")   # bright lips on cracks
    # specular sweep streaks, all in one direction
    sw = fbm(rng, 2, 3, aniso=9)
    streak = smooth(0.58, 0.8, sw) * (0.6 + 0.4 * fbm(rng, 3, 2, aniso=9))
    streak2 = smooth(0.8, 0.95, fbm(rng, 3, 4, aniso=14))
    glass = glass + (streak * 0.18 + streak2 * 0.3)[..., None] * hx("#f2fff8")
    glass = glass + (spec(n, 55) * 0.35)[..., None] * hx("#ffffff")
    col = mix(sand, glass, gm[..., None])
    return col, None


def t_razor_oysters(rng, v, frame):
    base = hx(TERRAIN["razor_oysters"]["color"]) * np.array([1.0, 0.97, 1.04], np.float32)
    f1, f2, idx, pts = voronoi(rng, 30 + 2 * v, jitter_warp=40)
    N = len(pts)
    hv = rng.random(N).astype(np.float32)
    tone = hv[idx]
    openf = (rng.random(N) < 0.34)[idx]
    cx, cy = pts[idx, 0], pts[idx, 1]
    dx = ((VV - cx + S / 2) % S - S / 2) / K
    dy = ((UU - cy + S / 2) % S - S / 2) / K
    edge = f2 - f1
    dome = np.clip(edge / 7.0, 0, 1) ** 0.6
    ang = np.arctan2(dy, dx)
    ridge = np.sin(f1 * 2.1 + 2.5 * np.sin(ang * 3 + tone * 9)) * 0.5 + 0.5      # growth lamellae
    h = dome * 1.0 + 0.12 * ridge * dome + 0.05 * fbm(rng, 14, 2)
    # opened shells: the pearly cup sinks, with a raised lip
    cup = openf * (1 - smooth(0.0, 0.5, f1 / (np.maximum(f1 + edge * 0.5, 1e-3)))) * dome
    h = h - cup * 0.2
    s, n = shade(pblur(h, 0.5), 3.2)
    shell = mix(base * 0.5, base * 1.15, (0.55 * tone + 0.45 * ridge)[..., None].clip(0, 1))
    shell = mix(shell, shell * np.array([1.08, 0.97, 0.94]), smooth(0.5, 0.9, fbm(rng, 5, 3))[..., None] * 0.6)
    shell = mix(shell, hx("#5a5668"), smooth(0.55, 0.9, ridge)[..., None] * 0.4)
    col = shell * s[..., None]
    # pearly interior of opened shells: pearlescent hues
    pn = fbm(rng, 5, 3)
    pearl = mix(hx("#efe6ee"), hx("#b9dbd8"), pn[..., None])
    pearl = mix(pearl, hx("#e8c2d6"), (smooth(0.5, 0.9, fbm(rng, 4, 3)) * 0.6)[..., None])
    pm = openf * smooth(0.55, 0.3, f1 / (f1 + edge * 0.5 + 1e-3)) * smooth(2.0, 5.0, edge)
    col = mix(col, pearl * (0.85 + 0.25 * s[..., None]), pm[..., None] * 0.85)
    # wet water film between the shells
    gap = 1 - smooth(0.4, 3.2, edge)
    wet = mix(hx("#233c46"), hx("#3f6a70"), fbm(rng, 6, 3)[..., None])
    col = mix(col, wet, gap[..., None] * 0.85)
    sheen = spec(n, 20) * 0.35 + spec(n, 90) * 0.7
    col = col + sheen[..., None] * hx("#d6ecf0") * (0.4 + 0.6 * np.clip(pm + gap, 0, 1))[..., None]
    col = col + (smooth(0.7, 0.95, fbm(rng, 3, 3)) * 0.07)[..., None] * hx("#cfe6ea")
    return col, None


def t_glowmoss(rng, v, frame):
    base = hx(TERRAIN["glowmoss"]["color"])
    deep = hx("#1c3a24")
    f1, f2, idx, pts = voronoi(rng, 70, jitter_warp=18)
    f = fbm(rng, 3, 4)
    tuft = np.clip((f2 - f1) / 3.5, 0, 1) ** 0.5
    h = tuft * 0.8 + 0.3 * fbm(rng, 20, 3) + 0.3 * f
    s, n = shade(pblur(h, 0.5), 2.8)
    tone = fbm(rng, 6, 3)
    col = mix(deep * 0.7, base * 0.5, (0.5 * tone + 0.3 * f)[..., None].clip(0, 1))
    col = col * (0.75 + 0.45 * s[..., None])
    col = mix(col, deep * 0.4, ((1 - tuft) * 0.7)[..., None])         # shadowed seams
    col = col * (1 + 0.06 * strokes(rng, 100, 8, 3))[..., None]
    # bioluminescence: soft patches, dots, halos
    patch = smooth(0.7, 0.9, fbm(rng, 4, 4)) * 0.45
    dots = speckle(rng, 0.9965).astype(np.float32)
    dots2 = speckle(rng, 0.9985).astype(np.float32)
    em = patch * (0.5 + 0.5 * tuft)
    lum = hx("#d4f76a")
    col = col + (em * 0.5)[..., None] * hx("#a8e050")
    col = col + (pblur(dots, 2.4) * 2.8)[..., None] * hx("#9ee04a") * 0.45
    col = col + (pblur(dots, 0.7) * 3.0)[..., None] * lum
    col = col + (pblur(dots2, 1.2) * 4.0)[..., None] * hx("#f0ffa0")
    return col, None


def t_sinkmud(rng, v, frame):
    base = hx(TERRAIN["sinkmud"]["color"])
    f = fbm(rng, 3, 5)
    fine = fbm(rng, 12, 3)
    swirl = np.sin((A_ * 2 + B_ * 3) * 2 * math.pi + fbm(rng, 3, 3) * 6)
    h = 0.7 * f + 0.1 * fine + 0.12 * swirl
    # footprint dents + bubbles
    d = np.zeros((S, S), np.float32)
    fx, fy = G * (0.25 + 0.5 * rng.random()), G * (0.25 + 0.5 * rng.random())
    fa = rng.random() * 6.28
    dc, bc = PCanvas(), PCanvas()
    for i in range(3 if v != 1 else 2):
        a = fa + (i % 2 - 0.5) * 0.4
        px, py = fx + math.cos(fa) * 15 * i, fy + math.sin(fa) * 15 * i + (4 if i % 2 else -4)
        dc.ellipse(px, py, 6.0, 3.5, 1.0)
        dc.ellipse(px + math.cos(fa) * 7, py + math.sin(fa) * 7, 3.2, 2.6, 1.0)
    dm = pblur(dc.get(), 0.9)
    h = h - dm * 0.9 + pblur(dm, 2.0) * 0.2
    for _ in range(4 + v):
        bx, by, br = rng.random() * G, rng.random() * G, 1.8 + rng.random() * 3.2
        dxx, dyy = pdelta(bx * K, by * K)
        r = np.sqrt(dxx * dxx + dyy * dyy) / K
        dome = np.clip(1 - (r / br) ** 2, 0, 1) ** 0.5
        h = h + dome * 0.6 * (r < br)
        ring = smooth(br * 0.78, br, r) * smooth(br + 0.6, br, r)
        d = np.maximum(d, ring)
    s, n = shade(pblur(h, 0.6), 5.0)
    col = base * (0.4 + 0.8 * f[..., None]) * (0.6 + 0.5 * s[..., None])
    col = mix(col, base * 0.5, smooth(0.6, 0.9, fine)[..., None] * 0.3)
    col = col * (1 - 0.35 * dm)[..., None]
    col = col + (spec(n, 18) * 0.35)[..., None] * hx("#6a5a4c")                      # wide wet sheen
    col = col + (spec(n, 70) * 1.1)[..., None] * hx("#d9cfbe")
    col = col + (spec(n, 220) * 0.7)[..., None] * hx("#f3ead8")
    col = col + (d * 0.18)[..., None] * hx("#cfc4b4")
    return col, None


TOPS = {k[2:]: f for k, f in globals().items() if k.startswith("t_")}


# ----------------------------------------------------------------------------- sides
def side_texture(tid, rng):
    n = SIDE * 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    f = fbm(rng, 4, 5, size=n)
    w = fbm(rng, 2, 3, size=n)
    base = hx(TERRAIN[tid]["color"])
    rock = hx("#5c574f")
    if tid in ("brine_pool", "lamp_oil", "calcite", "living_reef", "shallows"):
        base = hx(TERRAIN["silt"]["color"])
    if tid == "salt_wall":
        tint, dark = base, 0.95
    elif tid == "trench":
        tint, dark = hx("#1a1c24"), 1.0
    elif tid in ("brine_lake",):
        tint, dark = mix(hx("#4a4d55"), base, 0.3), 0.75
    elif tid == "salt_flat":
        tint, dark = mix(base, rock, 0.35), 0.82
    elif tid == "vent":
        tint, dark = hx("#3a2c28"), 0.85
    elif tid == "sinkmud":
        tint, dark = mix(base, hx("#1c1816"), 0.3), 0.8
    elif tid == "beam_glass":
        tint, dark = mix(hx(TERRAIN["silt"]["color"]), base, 0.35), 0.82
    elif tid == "glowmoss":
        tint, dark = mix(hx("#3d3a2c"), base, 0.35), 0.78
    elif tid == "tangleweed":
        tint, dark = mix(hx("#4a4a34"), base, 0.4), 0.75
    else:
        tint, dark = mix(base, rock, 0.5), 0.8
    # strata: periodic bands (4 per tile height -> one per 16px level) with wobble
    ph = yy / n * 2 * math.pi * 4 + (w - 0.5) * 3.0
    bands = np.sin(ph) * 0.5 + 0.5
    thin = np.sin(ph * 3 + f * 2) * 0.5 + 0.5
    layer_id = np.floor((yy / n * 4 + (w - 0.5) * 0.5) * 2) % 8
    lt = (np.sin(layer_id * 3.7 + 1.3) * 0.5 + 0.5)
    col = tint * dark * (0.8 + 0.25 * lt[..., None] + 0.12 * (f[..., None] - 0.5))
    col = col * (0.9 + 0.12 * bands[..., None]) * (0.95 + 0.06 * thin[..., None])
    # seams between strata
    seam = smooth(0.06, 0.0, np.abs(((yy / n * 8 + (w - 0.5) * 1.0) % 1) - 0.0))
    col = col * (1 - 0.25 * seam[..., None])
    # vertical fracture strokes
    c = PCanvas(size=n, scale=1)
    for _ in range(10):
        x, y = rng.random() * n, rng.random() * n
        pts = [(x + (rng.random() - .5) * 3, y + i * 4) for i in range(int(4 + rng.random() * 6))]
        c.line(pts, 1.2, 1.0)
    fr = c.get()
    col = col * (1 - 0.35 * fr[..., None])
    if tid == "vent":
        col = mix(col, hx("#ff6a2a"), (fr * 0.55)[..., None])
    if tid == "scrap_field":
        rs = smooth(0.55, 0.85, fbm(rng, 5, 3, size=n))
        col = mix(col, hx("#a8552e") * 0.75, (rs * 0.45)[..., None])
    if tid == "salt_wall":
        cr = fbm(rng, 6, 3, size=n)
        col = mix(col, hx("#cfd8e2"), smooth(0.6, 0.9, cr)[..., None] * 0.4)
    if tid == "lighthouse_stone":
        r = yy / n * 4
        cidx = np.floor(xx / n * 2 + (np.floor(r) % 2) * 0.5)
        du = np.minimum(r % 1, 1 - r % 1)
        dv = np.minimum((xx / n * 2 + (np.floor(r) % 2) * 0.5) % 1, 1 - (xx / n * 2 + (np.floor(r) % 2) * 0.5) % 1)
        m = 1 - smooth(0.03, 0.07, np.minimum(du * 1.0, dv * 0.5))
        bt = (np.sin(np.floor(r) * 9.1 + cidx * 3.3) * 999) % 1
        col = base * 0.85 * (0.85 + 0.2 * bt[..., None] + 0.15 * (f[..., None] - .5))
        col = mix(col, base * 0.35, m * 0.85)
    if tid == "wreck":
        # timbers showing through
        t = (xx / n * 3) % 1
        tm = smooth(0.0, 0.05, t) * smooth(0.45, 0.4, t) * smooth(0.4, 0.6, fbm(rng, 3, 3, size=n))
        col = mix(col, base * 0.7 * (0.8 + 0.4 * f[..., None]), tm * 0.8)
    g = rng.normal(0, 0.03, (n, n, 1)).astype(np.float32)
    col = np.clip(col * (1 + g), 0, 1)
    img = Image.fromarray((col * 255).astype(np.uint8), "RGB").resize((SIDE, SIDE), Image.BOX)
    return img


# ----------------------------------------------------------------------------- props
def _shaded_line(d, pts, w, c_lit, c_dark, k):
    pts = [(x * k, y * k) for x, y in pts]
    d.line([(x + w * k * 0.25, y) for x, y in pts], fill=c_dark, width=int(w * k), joint="curve")
    d.line([(x - w * k * 0.15, y) for x, y in pts], fill=c_lit, width=max(1, int(w * k * 0.6)), joint="curve")


def _finish(im, k):
    w, h = im.size
    return im.resize((w // k, h // k), Image.LANCZOS)


def prop_coral(rng, vivid=False):
    k = 4
    W, H = 56, 56
    im = Image.new("RGBA", (W * k, H * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([(W / 2 - 17) * k, (H - 7) * k, (W / 2 + 17) * k, (H - 0.5) * k], fill=(10, 8, 12, 80))
    base = hx(TERRAIN["living_reef" if vivid else "dead_coral"]["color"])
    tips = []

    def br(x, y, ang, L, w, dpt):
        x2, y2 = x + math.cos(ang) * L, y + math.sin(ang) * L
        t = 1 - dpt / 4
        cl = mix(base * 1.15, hx("#f6dccd") if vivid else hx("#d8c6c0"), 0.25 + t * 0.5)
        lit = tuple(int(c * 255) for c in np.clip(cl, 0, 1)) + (255,)
        drk = tuple(int(c * 255) for c in np.clip(cl * 0.6, 0, 1)) + (255,)
        _shaded_line(d, [(x, y), ((x + x2) / 2 + (rng.random() - .5) * 2, (y + y2) / 2), (x2, y2)], w, lit, drk, k)
        if dpt > 0:
            for s_ in (-1, 1):
                if rng.random() < 0.8:
                    br(x2, y2, ang + s_ * (0.35 + rng.random() * 0.5), L * 0.72, max(1.2, w * 0.72), dpt - 1)
        else:
            tips.append((x2, y2))
    for i in range(3 if vivid else 2):
        br(W / 2 + (rng.random() - .5) * 16, H - 3, -math.pi / 2 + (rng.random() - .5) * 0.9, 13 + rng.random() * 5,
           4.2, 3)
    if vivid:
        for x, y in tips:
            r = 1.2
            d.ellipse([(x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k], fill=(255, 236, 214, 255))
    return _finish(im, k)


def prop_kelp(rng):
    k = 4
    W, H = 44, 64
    im = Image.new("RGBA", (W * k, H * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([(W / 2 - 16) * k, (H - 7) * k, (W / 2 + 16) * k, (H - 0.5) * k], fill=(5, 8, 6, 90))
    base = hx(TERRAIN["kelp_husk"]["color"])
    pal = [base * 0.8, base, base * 1.3, mix(base, hx("#8a7a4a"), 0.6), mix(base, hx("#6b5a36"), 0.6)]
    for i in range(22):
        x = W / 2 + (rng.random() - .5) * 26
        y = H - 3 - rng.random() * 3
        ang = -math.pi / 2 + (rng.random() - .5) * 0.7
        L = 30 + rng.random() * 26
        pts = [(x, y)]
        for j in range(7):
            ang += (rng.random() - .5) * 0.6
            x += math.cos(ang) * L / 7
            y += math.sin(ang) * L / 7
            pts.append((x, y))
        c = pal[rng.integers(len(pal))]
        sh = 0.7 + 0.5 * (i / 22)
        lit = tuple(int(v * 255) for v in np.clip(c * sh * 1.15, 0, 1)) + (255,)
        drk = tuple(int(v * 255) for v in np.clip(c * sh * 0.6, 0, 1)) + (255,)
        _shaded_line(d, pts, 2.6 - 1.2 * rng.random(), lit, drk, k)
    return _finish(im, k)


def _c255(c, a=255):
    return tuple(int(v * 255) for v in np.clip(c, 0, 1)) + (a,)


def _rib(d, k, pts_fn, w0, w1, wood, rng, n=24, broken=True):
    """Tapered, hand-shaped curved timber: flat lit face, dark side, grain, splintered tip."""
    P = [pts_fn(t) for t in np.linspace(0, 1, n)]
    L, Rr = [], []
    for i, (x, y) in enumerate(P):
        x2, y2 = P[min(i + 1, n - 1)]
        x1, y1 = P[max(i - 1, 0)]
        tx, ty = x2 - x1, y2 - y1
        l = math.hypot(tx, ty) + 1e-6
        nx, ny = -ty / l, tx / l
        t = i / (n - 1)
        w = (w0 + (w1 - w0) * t) * (1 + 0.08 * math.sin(t * 9 + rng.random()))
        L.append((x + nx * w / 2, y + ny * w / 2))
        Rr.append((x - nx * w / 2, y - ny * w / 2))
    # splintered top end
    tip = []
    if broken:
        xa, ya = L[-1]
        xb, yb = Rr[-1]
        for j in range(5):
            f = j / 4
            jx = xa + (xb - xa) * f
            jy = ya + (yb - ya) * f - (rng.random() * 3.0 if j % 2 else 0)
            tip.append((jx, jy))
    poly = L + tip + Rr[::-1]
    S_ = lambda pts: [(x * k, y * k) for x, y in pts]
    # which side is lit: the side whose normal points to the upper-left
    d.polygon(S_(poly), fill=_c255(wood * 0.45))
    mid = [((a[0] * 0.35 + b[0] * 0.65), (a[1] * 0.35 + b[1] * 0.65)) for a, b in zip(L, Rr)]
    lit_side = L if (L[n // 2][0] < Rr[n // 2][0]) else Rr
    face = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in zip(L, Rr)]
    d.polygon(S_(lit_side + face[::-1]), fill=_c255(wood * 1.0))
    # grain lines along the timber
    for off in (0.25, 0.6):
        g = [(a[0] * off + b[0] * (1 - off), a[1] * off + b[1] * (1 - off)) for a, b in zip(lit_side, face)]
        d.line(S_(g[2:-3]), fill=_c255(wood * 0.75), width=max(1, int(k * 0.4)))
    d.line(S_(lit_side[1:-1]), fill=_c255(mix(wood * 1.5, hx("#a39a88"), 0.4)), width=max(1, int(k * 0.8)))
    return P, L, Rr


def prop_wreck(rng, kind):
    k = 4
    W, H = 72, 72
    im = Image.new("RGBA", (W * k, H * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    wood = mix(hx(TERRAIN["wreck"]["color"]), hx("#7d6a55"), 0.3)
    rust = hx("#a8552e")
    iron = hx("#3a3633")
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    cx, base_y = W / 2, H - 9
    if kind == 0:
        # ship frame: keel timber lying in the silt with pairs of ribs curving up and in
        ds.ellipse([(cx - 28) * k, (base_y - 8) * k, (cx + 28) * k, (base_y + 8) * k], fill=(6, 5, 5, 110))
        kx0, ky0, kx1, ky1 = cx - 22, base_y + 4, cx + 20, base_y - 10
        stations = [0.15, 0.5, 0.85]
        items = []
        for si, f in enumerate(stations):
            bx, by = kx0 + (kx1 - kx0) * f, ky0 + (ky1 - ky0) * f
            for side in (-1, 1):
                hgt = 36 - si * 4 - rng.random() * 6 - (9 if (si + side) % 3 == 0 else 0)
                spread = 9 - si
                items.append((by, side, bx, by, hgt, spread))
        # keel
        d.polygon([(x * k, y * k) for x, y in [(kx0 - 2, ky0 + 1), (kx1 + 2, ky1 - 1.5), (kx1 + 2, ky1 + 2.5),
                                              (kx0 - 2, ky0 + 4.5)]], fill=_c255(wood * 0.5))
        d.line([((kx0 - 2) * k, (ky0 + 1) * k), ((kx1 + 2) * k, (ky1 - 1.5) * k)], fill=_c255(wood * 1.1), width=k)
        for by_, side, bx, by, hgt, spread in sorted(items, key=lambda q: (q[0], q[1])):
            fn = (lambda bx=bx, by=by, side=side, hgt=hgt, spread=spread:
                  lambda t: (bx + side * spread * (math.sin(t * math.pi * 0.9) - 0.55 * t), by - t * hgt))()
            _rib(d, k, fn, 5.4, 2.6, wood * (0.85 + 0.15 * rng.random()), rng)
            d.ellipse([(bx - 1.1) * k, (by - 1.6) * k, (bx + 1.1) * k, (by + 0.2) * k], fill=_c255(rust * 0.8))
    elif kind == 1:
        # two great curved ribs leaning together, one snapped short (whale-rib silhouette)
        ds.ellipse([(cx - 24) * k, (base_y - 6) * k, (cx + 24) * k, (base_y + 7) * k], fill=(6, 5, 5, 110))
        for side, hgt, bend, br in ((-1, 50, 9, True), (1, 33, 8, True)):
            bx = cx + side * 12
            fn = (lambda bx=bx, side=side, hgt=hgt, bend=bend:
                  lambda t: (bx + side * bend * (math.sin(t * math.pi * 0.8) * 0.6 - t * t * 1.3),
                             base_y - t * hgt))()
            _rib(d, k, fn, 6.5, 2.6, wood * (0.9 + 0.1 * rng.random()), rng)
            # iron strap near the foot
            y0 = base_y - 6
            d.rectangle([(bx - 4.2) * k, (y0 - 1.5) * k, (bx + 4.2) * k, (y0 + 1.5) * k], fill=_c255(iron))
            d.line([((bx - 4.2) * k, (y0 - 1.5) * k), ((bx + 4.2) * k, (y0 - 1.5) * k)], fill=_c255(rust), width=k)
            for rx in (-2.5, 2.5):
                d.ellipse([(bx + rx - .8) * k, (y0 - .8) * k, (bx + rx + .8) * k, (y0 + .8) * k], fill=_c255(rust * 1.2))
        # loose plank in the silt
        pts = [(cx - 14, base_y + 3), (cx + 10, base_y - 2), (cx + 11, base_y + 1), (cx - 13, base_y + 6)]
        d.polygon([(x * k, y * k) for x, y in pts], fill=_c255(wood * 0.7))
        d.line([(pts[0][0] * k, pts[0][1] * k), (pts[1][0] * k, pts[1][1] * k)], fill=_c255(wood * 1.2), width=k)
    else:
        # single frame with a strake plank still attached and an iron knee
        ds.ellipse([(cx - 26) * k, (base_y - 6) * k, (cx + 26) * k, (base_y + 7) * k], fill=(6, 5, 5, 110))
        bx = cx - 6
        fn = lambda t: (bx + math.sin(t * math.pi * 0.8) * 14 - t * 3, base_y - t * 40)
        P, L, Rr = _rib(d, k, fn, 6.0, 3.0, wood, rng)
        # strake: short plank crossing the rib at 40%
        x0, y0 = fn(0.38)
        plank = [(x0 - 18, y0 + 6), (x0 + 12, y0 - 6), (x0 + 12, y0 - 1), (x0 - 18, y0 + 11)]
        d.polygon([(x * k, y * k) for x, y in plank], fill=_c255(wood * 0.85))
        d.line([(plank[0][0] * k, plank[0][1] * k), (plank[1][0] * k, plank[1][1] * k)], fill=_c255(wood * 1.35), width=k)
        d.line([(plank[3][0] * k, plank[3][1] * k), (plank[2][0] * k, plank[2][1] * k)], fill=_c255(wood * 0.4), width=k)
        for f in (0.2, 0.75):
            px, py = plank[0][0] + (plank[1][0] - plank[0][0]) * f, plank[0][1] + (plank[1][1] - plank[0][1]) * f + 2.5
            d.ellipse([(px - .8) * k, (py - .8) * k, (px + .8) * k, (py + .8) * k], fill=_c255(rust))
        # iron knee at the foot
        kx, ky = bx + 2, base_y - 2
        knee = [(kx - 2, ky - 12), (kx + 1, ky - 12), (kx + 1, ky - 2), (kx + 11, ky - 2), (kx + 11, ky + 1), (kx - 2, ky + 1)]
        d.polygon([(x * k, y * k) for x, y in knee], fill=_c255(iron))
        d.line([((kx - 2) * k, (ky - 12) * k), ((kx - 2) * k, (ky + 1) * k)], fill=_c255(rust * 1.1), width=k)
        for (rx, ry) in ((kx - 0.5, ky - 9), (kx - 0.5, ky - 5), (kx + 5, ky - 0.5), (kx + 9, ky - 0.5)):
            d.ellipse([(rx - .7) * k, (ry - .7) * k, (rx + .7) * k, (ry + .7) * k], fill=_c255(rust * 1.25))
    sh = sh.filter(ImageFilter.GaussianBlur(2 * k))
    sh.alpha_composite(im)
    return _finish(sh, k)


def _flat(cx, cy, pts):
    """Ground-plane decal coordinates (a, b in px) -> iso screen offsets."""
    return [(cx + (a - b), cy + (a + b) * 0.5) for a, b in pts]


def prop_lantern(rng):
    """A tipped-over brass lantern with a cracked pane and a small dark oil spill."""
    k = 4
    W, H = 28, 22
    im = Image.new("RGBA", (W * k, H * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = W / 2, H - 6
    brass, dark = hx("#a07a38"), hx("#3b2a14")
    # spill + shadow
    d.ellipse([(cx - 3) * k, (cy - 1) * k, (cx + 11) * k, (cy + 4.5) * k], fill=(40, 26, 12, 120))
    d.ellipse([(cx - 9) * k, (cy - 2) * k, (cx + 5) * k, (cy + 3) * k], fill=(8, 6, 6, 110))
    # body lying on its side: cylinder seen from the side, leaning down-right
    body = [(cx - 7, cy - 6), (cx + 2, cy - 4), (cx + 2, cy + 1.5), (cx - 7, cy - 0.5)]
    d.polygon([(x * k, y * k) for x, y in body], fill=_c255(hx("#6d5a3a")))
    # glass panes with a dim amber glow, one cracked
    d.polygon([(x * k, y * k) for x, y in [(cx - 5.5, cy - 4.8), (cx + 0.5, cy - 3.4), (cx + 0.5, cy + 0.2), (cx - 5.5, cy - 1.2)]],
              fill=_c255(hx("#d99a3a") * 0.85))
    d.line([((cx - 4) * k, (cy - 4.2) * k), ((cx - 2) * k, (cy - 1.3) * k), ((cx - 0.5) * k, (cy - 2.5) * k)],
           fill=_c255(hx("#fff0c0")), width=max(1, k // 2))
    # brass caps
    for x0 in (cx - 7.5, cx + 2):
        d.ellipse([(x0 - 1.4) * k, (cy - 6.5 + (x0 - cx + 7.5) * 0.22) * k, (x0 + 1.4) * k, (cy + 1 + (x0 - cx + 7.5) * 0.22) * k],
                  fill=_c255(brass))
    d.line([((cx - 7.5) * k, (cy - 6) * k), ((cx + 2) * k, (cy - 4) * k)], fill=_c255(brass * 1.4), width=k)
    # handle ring
    d.arc([(cx - 12) * k, (cy - 6) * k, (cx - 6) * k, (cy - 1) * k], 60, 300, fill=_c255(dark * 1.6), width=k)
    return _finish(im, k)


def prop_tally(rng):
    """A flat slate shard with a chalk tally scratched on it."""
    k = 4
    W, H = 30, 18
    im = Image.new("RGBA", (W * k, H * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = W / 2, H / 2 - 1
    shard = _flat(cx, cy, [(-7, -3), (4, -6), (8, 0), (5, 6), (-4, 7), (-8, 2)])
    d.polygon([(x * k, y * k + 1.2 * k) for x, y in shard], fill=(30, 32, 38, 140))
    d.polygon([(x * k, y * k) for x, y in shard], fill=_c255(hx("#7d8590")))
    d.line([(x * k, y * k) for x, y in shard[:3]], fill=_c255(hx("#9aa2ac")), width=k)
    chalk = (236, 232, 222, 235)
    for i in range(4):
        a0, b0 = -4 + i * 2.2, -2.5
        p = _flat(cx, cy, [(a0, b0), (a0 + 0.6, b0 + 5.5)])
        d.line([(x * k, y * k) for x, y in p], fill=chalk, width=max(1, int(k * 0.55)))
    p = _flat(cx, cy, [(-5.5, 2.5), (4.5, -1.5)])
    d.line([(x * k, y * k) for x, y in p], fill=chalk, width=max(1, int(k * 0.55)))
    return _finish(im, k)


def prop_footprints(rng):
    """A short trail of booted footprints pressed into the silt."""
    k = 4
    W, H = 44, 26
    im = Image.new("RGBA", (W * k, H * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = W / 2, H / 2
    for i in range(5):
        a = -13 + i * 6.5
        b = (2.0 if i % 2 else -2.0) + (rng.random() - .5) * 0.8
        foot = []
        for t in np.linspace(0, 2 * math.pi, 14, endpoint=False):
            rr = 1.0 + 0.25 * math.cos(t)          # wider toe end
            foot.append((a + math.cos(t) * 2.6 * rr, b + math.sin(t) * 1.15 * rr))
        poly = _flat(cx, cy, foot)
        d.polygon([(x * k, y * k) for x, y in poly], fill=(38, 30, 22, 105))
        hi = _flat(cx, cy, [(a + 2.6 * math.cos(t), b + 1.3 * math.sin(t)) for t in np.linspace(3.6, 5.6, 6)])
        d.line([(x * k, y * k) for x, y in hi], fill=(196, 182, 156, 90), width=max(1, k // 2))
    return _finish(im.filter(ImageFilter.GaussianBlur(k * 0.25)), k)


def prop_oar(rng):
    """A broken oar, blade half buried in a little mound of silt."""
    k = 4
    W, H = 36, 40
    im = Image.new("RGBA", (W * k, H * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = W / 2, H - 6
    wood = hx("#8a6a48")
    silt = hx(TERRAIN["silt"]["color"])
    d.ellipse([(cx - 4) * k, (cy - 2) * k, (cx + 15) * k, (cy + 4) * k], fill=(8, 6, 5, 100))
    # shaft leaning up-left from the mound, snapped end
    x0, y0, x1, y1 = cx + 2, cy - 2, cx - 9, cy - 27
    d.line([(x0 * k, y0 * k), (x1 * k, y1 * k)], fill=_c255(wood * 0.55), width=int(2.6 * k))
    d.line([((x0 - 0.6) * k, y0 * k), ((x1 - 0.6) * k, y1 * k)], fill=_c255(wood * 1.15), width=int(1.2 * k))
    d.polygon([((x1 - 1.4) * k, (y1 + 0.5) * k), ((x1 - 0.2) * k, (y1 - 2.2) * k), ((x1 + 0.5) * k, (y1 - 0.6) * k),
               ((x1 + 1.4) * k, (y1 - 1.8) * k), ((x1 + 1.3) * k, (y1 + 1) * k)], fill=_c255(wood * 0.9))
    # blade emerging from the silt
    blade = [(cx - 1, cy - 4), (cx + 6, cy - 7), (cx + 8, cy - 2), (cx + 1, cy + 1)]
    d.polygon([(x * k, y * k) for x, y in blade], fill=_c255(wood * 0.8))
    d.line([(blade[0][0] * k, blade[0][1] * k), (blade[1][0] * k, blade[1][1] * k)], fill=_c255(wood * 1.3), width=k)
    # silt mound over the lower blade
    d.ellipse([(cx - 5) * k, (cy - 2.5) * k, (cx + 11) * k, (cy + 3) * k], fill=_c255(silt * 0.95))
    d.arc([(cx - 5) * k, (cy - 2.5) * k, (cx + 11) * k, (cy + 3) * k], 190, 300, fill=_c255(silt * 1.2), width=k)
    return _finish(im, k)


def prop_shells(rng):
    """A few pale shell fragments and pebbles (filler so the human touches stay rare)."""
    k = 4
    W, H = 26, 16
    im = Image.new("RGBA", (W * k, H * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i in range(6):
        x, y = W / 2 + (rng.random() - .5) * 16, H / 2 + (rng.random() - .5) * 7
        r = 0.7 + rng.random() * 1.3
        c = hx("#d8cbb4") if i % 2 else hx("#6e6556")
        d.ellipse([(x - r) * k, (y - r * 0.4 + 0.6) * k, (x + r) * k, (y + r * 0.6 + 0.6) * k], fill=(10, 8, 6, 90))
        d.ellipse([(x - r) * k, (y - r * 0.6) * k, (x + r) * k, (y + r * 0.5) * k], fill=_c255(c))
        d.arc([(x - r) * k, (y - r * 0.6) * k, (x + r) * k, (y + r * 0.5) * k], 180, 290, fill=_c255(c * 1.25), width=max(1, k // 2))
    return _finish(im, k)


def prop_salt(rng):
    k = 4
    W, H = 24, 24
    im = Image.new("RGBA", (W * k, H * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([(W / 2 - 8) * k, (H - 4) * k, (W / 2 + 8) * k, (H - .5) * k], fill=(60, 70, 90, 60))
    for i in range(5):
        x = W / 2 + (rng.random() - .5) * 10
        h = 5 + rng.random() * 9
        w = 1.6 + rng.random() * 1.6
        lean = (rng.random() - .5) * 3
        y = H - 2.5
        left = [(x - w, y), (x + lean, y - h), (x, y + 0.5)]
        right = [(x, y + 0.5), (x + lean, y - h), (x + w, y)]
        d.polygon([(a * k, b * k) for a, b in left], fill=(250, 250, 246, 255))
        d.polygon([(a * k, b * k) for a, b in right], fill=(178, 190, 204, 255))
    return _finish(im, k)


def _blank(W, H, k=4):
    im = Image.new("RGBA", (W * k, H * k), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def _shadow(d, cx, y, rx, k, a=90):
    d.ellipse([(cx - rx) * k, (y - 2.6) * k, (cx + rx) * k, (y + 2.6) * k], fill=(8, 6, 6, a))


def _poly(d, pts, c, k):
    d.polygon([(x * k, y * k) for x, y in pts], fill=_c255(c))


def prop_vent(rng, i):
    """Short mineral chimney stacks with a pale steam wisp."""
    k = 4
    W, H = 34, 56
    im, d = _blank(W, H, k)
    cx, by = W / 2, H - 5
    _shadow(d, cx, by + 1, 13, k, 100)
    rock, sulph, white = hx("#4a3a34"), hx("#d6bd3c"), hx("#eee8d6")
    stacks = [(0, 0, 15, 5.5), (-8, 3, 9, 3.6), (8, 2, 7, 3.2)][: 1 + i % 3 + (1 if i else 0)]
    for ox, oy, hgt, w in sorted(stacks, key=lambda q: q[1]):
        x, y = cx + ox, by + oy
        top = y - hgt
        lean = (rng.random() - 0.5) * 2
        body = [(x - w, y), (x - w * 0.55 + lean, top), (x + w * 0.55 + lean, top), (x + w, y)]
        _poly(d, body, rock * 0.8, k)
        _poly(d, [(x - w, y), (x - w * 0.55 + lean, top), (x - w * 0.1 + lean, top), (x + 0.0, y)], rock * 1.35, k)
        for j in range(4):    # sulphur / white crust bands
            t = 0.15 + 0.22 * j + rng.random() * 0.06
            yy = y - hgt * t
            ww = w * (1 - 0.45 * t)
            c = sulph if j % 2 == 0 else white
            d.ellipse([(x - ww * 0.9 + lean * t) * k, (yy - 1.0) * k, (x + ww * 0.9 + lean * t) * k, (yy + 1.2) * k],
                      fill=_c255(c * (0.85 + 0.2 * rng.random()), 235))
        # crater mouth with orange glow
        d.ellipse([(x - w * 0.55 + lean) * k, (top - 1.3) * k, (x + w * 0.55 + lean) * k, (top + 1.3) * k],
                  fill=_c255(white * 0.9))
        d.ellipse([(x - w * 0.38 + lean) * k, (top - 0.8) * k, (x + w * 0.38 + lean) * k, (top + 0.9) * k],
                  fill=_c255(hx("#ff6a22")))
        d.ellipse([(x - w * 0.2 + lean) * k, (top - 0.4) * k, (x + w * 0.2 + lean) * k, (top + 0.5) * k],
                  fill=_c255(hx("#ffd070")))
    # steam wisp
    st = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(st)
    x, y = cx, by - 17
    for j in range(9):
        r = 1.6 + j * 0.45
        x += math.sin(j * 0.9 + i) * 1.1
        y -= 2.9
        ds.ellipse([(x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k], fill=(240, 240, 235, int(150 * (1 - j / 10))))
    st = st.filter(ImageFilter.GaussianBlur(1.3 * k))
    im = Image.alpha_composite(im, st)
    return _finish(im, k)


def prop_weed(rng, i):
    """Upright tufts of wiry weed."""
    k = 4
    W, H = 36, 44
    im, d = _blank(W, H, k)
    _shadow(d, W / 2, H - 4, 11, k, 90)
    base = hx(TERRAIN["tangleweed"]["color"])
    pal = [base * 0.7, base, base * 1.25, mix(base, hx("#5a4a2a"), 0.6), hx("#a88438")]
    for j in range(26):
        x, y = W / 2 + (rng.random() - .5) * 14, H - 4 - rng.random() * 2
        ang = -math.pi / 2 + (rng.random() - .5) * 1.0
        L = 14 + rng.random() * (14 + 4 * i)
        pts = [(x, y)]
        for _ in range(6):
            ang += (rng.random() - .5) * 0.9
            x += math.cos(ang) * L / 6
            y += math.sin(ang) * L / 6
            pts.append((x, y))
        c = pal[rng.integers(len(pal))] * (0.75 + 0.4 * j / 26)
        _shaded_line(d, pts, 1.7 - 0.5 * rng.random(), _c255(c * 1.2), _c255(c * 0.55), k)
    return _finish(im, k)


def prop_chain(rng, i=0):
    k = 4
    W, H = 32, 20
    im, d = _blank(W, H, k)
    _shadow(d, W / 2, H - 4.5, 12, k, 100)
    rust, steel = hx("#8a4a2a"), hx("#6a6660")
    x, y = 7, H - 8
    for j in range(7):
        ox, oy = x + j * 2.6 + (rng.random() - .5), y + math.sin(j * 1.1) * 2.5 - (j % 3) * 0.6
        c = rust if j % 2 else steel
        if j % 2 == 0:
            d.ellipse([(ox - 3.6) * k, (oy - 2) * k, (ox + 3.6) * k, (oy + 2) * k], outline=_c255(c * 0.6), width=int(1.6 * k))
            d.arc([(ox - 3.6) * k, (oy - 2) * k, (ox + 3.6) * k, (oy + 2) * k], 180, 300, fill=_c255(c * 1.5), width=k)
        else:
            d.ellipse([(ox - 1.6) * k, (oy - 2.2) * k, (ox + 1.6) * k, (oy + 2.2) * k], fill=_c255(c * 0.7))
            d.arc([(ox - 1.6) * k, (oy - 2.2) * k, (ox + 1.6) * k, (oy + 2.2) * k], 180, 330, fill=_c255(c * 1.4), width=max(1, k // 2))
    return _finish(im, k)


def prop_anchor_fluke(rng, i=0):
    k = 4
    W, H = 34, 38
    im, d = _blank(W, H, k)
    cx, by = W / 2, H - 5
    _shadow(d, cx, by + 1, 13, k, 100)
    iron, rust = hx("#3e3a37"), hx("#8a4a2a")
    # shank sticking out of the silt, leaning
    d.line([(cx - 3) * k, (by) * k, (cx - 6) * k, (by - 24) * k], fill=_c255(iron), width=int(3.2 * k))
    d.line([(cx - 3.8) * k, (by) * k, (cx - 6.8) * k, (by - 24) * k], fill=_c255(rust * 1.2), width=int(1.2 * k))
    d.ellipse([(cx - 10.5) * k, (by - 30) * k, (cx - 2.5) * k, (by - 22) * k], outline=_c255(iron), width=int(2 * k))  # ring
    # fluke (triangular palm) half-buried
    _poly(d, [(cx + 1, by + 1), (cx + 14, by - 11), (cx + 10, by - 2), (cx + 4, by + 3)], iron * 1.1, k)
    _poly(d, [(cx + 1, by + 1), (cx + 14, by - 11), (cx + 11, by - 12.5), (cx - 2, by - 3)], rust * 0.9, k)
    d.line([(cx - 1.5) * k, (by - 3) * k, (cx + 11) * k, (by - 12.4) * k], fill=_c255(hx("#c8885a")), width=max(1, k // 2))
    d.ellipse([(cx - 7) * k, (by - 2.5) * k, (cx + 7) * k, (by + 3) * k], fill=(120, 104, 84, 255))   # silt mound
    d.arc([(cx - 7) * k, (by - 2.5) * k, (cx + 7) * k, (by + 3) * k], 190, 300, fill=_c255(hx("#a8977c")), width=k)
    return _finish(im, k)


def prop_gear(rng, i=0):
    k = 4
    W, H = 22, 18
    im, d = _blank(W, H, k)
    cx, cy = W / 2, H / 2 + 1
    _shadow(d, cx, cy + 4, 8, k, 90)
    rust = hx("#9a5230")
    # gear lying flat: ellipse-compressed polygon, teeth, hub hole
    def ring(r, n, tooth=0.0):
        pts = []
        for j in range(n * 4):
            a = 2 * math.pi * j / (n * 4)
            rr = r + (tooth if j % 4 in (0, 1) else 0)
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.55))
        return pts
    _poly(d, [(x, y + 1.2) for x, y in ring(7.2, 9, 1.8)], rust * 0.5, k)
    _poly(d, ring(7.2, 9, 1.8), rust, k)
    _poly(d, ring(5.0, 9, 0.0), rust * 1.25, k)
    d.ellipse([(cx - 2) * k, (cy - 1.1) * k, (cx + 2) * k, (cy + 1.1) * k], fill=(24, 18, 14, 255))
    d.arc([(cx - 7.2) * k, (cy - 4) * k, (cx + 7.2) * k, (cy + 4) * k], 190, 290, fill=_c255(hx("#e4b080")), width=max(1, k // 2))
    return _finish(im, k)


def prop_oysters(rng, i):
    k = 4
    W, H = 30, 20
    im, d = _blank(W, H, k)
    _shadow(d, W / 2, H - 5, 11, k, 80)
    base = hx(TERRAIN["razor_oysters"]["color"])
    for j in range(4 + i):
        x, y = W / 2 + (rng.random() - .5) * 16, H - 8 + (rng.random() - .5) * 5
        r = 2.6 + rng.random() * 2.0
        c = base * (0.75 + 0.4 * rng.random())
        d.ellipse([(x - r) * k, (y - r * 0.55 + 0.8) * k, (x + r) * k, (y + r * 0.6 + 0.8) * k], fill=_c255(c * 0.4))
        d.ellipse([(x - r) * k, (y - r * 0.7) * k, (x + r) * k, (y + r * 0.6) * k], fill=_c255(c))
        for q in (0.35, 0.65):     # growth ridges
            d.arc([(x - r * q) * k, (y - r * 0.7 * q) * k, (x + r * q) * k, (y + r * 0.6 * q) * k], 190, 340,
                  fill=_c255(c * 0.7), width=max(1, k // 3))
        d.arc([(x - r) * k, (y - r * 0.7) * k, (x + r) * k, (y + r * 0.6) * k], 180, 290, fill=_c255(c * 1.4), width=max(1, k // 2))
        if j % 2 == 0:   # pearly open shell
            d.ellipse([(x - r * 0.55) * k, (y - r * 0.4) * k, (x + r * 0.55) * k, (y + r * 0.3) * k], fill=_c255(hx("#eee4ee")))
            d.ellipse([(x - r * 0.25) * k, (y - r * 0.25) * k, (x + r * 0.1) * k, (y + r * 0.1) * k], fill=_c255(hx("#bfe0dc")))
    return _finish(im, k)


def prop_moss(rng, i):
    k = 4
    W, H = 26, 24
    im, d = _blank(W, H, k)
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dg = ImageDraw.Draw(glow)
    _shadow(d, W / 2, H - 4, 8, k, 80)
    base = hx(TERRAIN["glowmoss"]["color"])
    for j in range(7 + 2 * i):
        x = W / 2 + (rng.random() - .5) * 13
        y = H - 4 - rng.random() * 2
        hgt = 5 + rng.random() * 8
        lean = (rng.random() - .5) * 4
        c = base * (0.55 + 0.4 * rng.random())
        _shaded_line(d, [(x, y), (x + lean * 0.5, y - hgt * 0.5), (x + lean, y - hgt)], 1.3, _c255(c * 1.2), _c255(c * 0.55), k)
        tx, ty = x + lean, y - hgt
        r = 0.9 + rng.random() * 0.7
        dg.ellipse([(tx - r * 3) * k, (ty - r * 3) * k, (tx + r * 3) * k, (ty + r * 3) * k], fill=(190, 240, 90, 120))
        d.ellipse([(tx - r) * k, (ty - r) * k, (tx + r) * k, (ty + r) * k], fill=_c255(hx("#e4ff8a")))
    glow = glow.filter(ImageFilter.GaussianBlur(1.6 * k))
    im = Image.alpha_composite(glow, im)
    return _finish(im, k)


PROPS = {
    "dead_coral": [lambda r: prop_coral(r, False)] * 3,
    "living_reef": [lambda r: prop_coral(r, True)] * 3,
    "kelp_husk": [prop_kelp] * 3,
    "wreck": [lambda r: prop_wreck(r, 0), lambda r: prop_wreck(r, 1), lambda r: prop_wreck(r, 2)],
    # salt crystals (common) plus rare human touches
    "salt_flat": [prop_salt, prop_salt, prop_salt, prop_salt, prop_lantern, prop_tally],
    # silt: shell/pebble filler plus rare human touches
    "silt": [prop_shells, prop_shells, prop_shells, prop_footprints, prop_oar],
    "vent": [lambda r: prop_vent(r, 0), lambda r: prop_vent(r, 1), lambda r: prop_vent(r, 2)],
    "tangleweed": [lambda r: prop_weed(r, 0), lambda r: prop_weed(r, 1), lambda r: prop_weed(r, 2)],
    "scrap_field": [prop_chain, prop_anchor_fluke, prop_gear],
    "razor_oysters": [lambda r: prop_oysters(r, 0), lambda r: prop_oysters(r, 1), lambda r: prop_oysters(r, 2)],
    "glowmoss": [lambda r: prop_moss(r, 0), lambda r: prop_moss(r, 1), lambda r: prop_moss(r, 2)],
}


# ----------------------------------------------------------------------------- main
def main(only=None):
    os.makedirs(OUT, exist_ok=True)
    if only:
        bad = [t for t in only if t not in TERRAIN or t not in TOPS]
        if bad:
            sys.exit("unknown/unpainted terrain ids: " + ", ".join(bad))
    patch = {}
    count = 0
    for i, tid in enumerate(TERRAIN):
        if only and tid not in only:
            continue
        fn = TOPS[tid]
        tops = []
        for v in range(3):
            rng = np.random.default_rng(1000 * i + 17 * v + 3)
            frame = v if tid in ANIMATED else 0
            col, alpha = fn(rng, v, frame)
            if alpha is None and tid not in ("trench",):
                col = level_edges(col)
            # seam knitting: every variant fades into variant 0 at the diamond edges, and variant 0 is
            # periodic, so any two variants of the same terrain meet without a visible seam.
            if tid not in ANIMATED and tid not in SHARED_EDGE:
                if v == 0:
                    col0, alpha0 = col, alpha
                else:
                    dg = np.minimum(np.minimum(A_, 1 - A_), np.minimum(B_, 1 - B_))
                    wgt = smooth(0.1, 0.0, dg)
                    col = mix(col, col0, wgt)
                    if alpha is not None:
                        alpha = alpha * (1 - wgt) + alpha0 * wgt
            knit = 0.0   # no edge darkening: it read as a grid; neighbours blend in the renderer
            img = project(np.clip(col, 0, 1.2), alpha, knit=knit, rng=rng,
                          grain=0.012 if tid in ANIMATED else 0.025)
            p = f"tiles/{tid}_top_{v}.png"
            img.save(os.path.join(ROOT, p))
            tops.append(p)
            count += 1
        side = side_texture(tid, np.random.default_rng(500 + i))
        sp = f"tiles/{tid}_side.png"
        side.save(os.path.join(ROOT, sp))
        count += 1
        entry = {"tiles": {"top": tops, "side": sp}}
        if tid in PROPS:
            props = []
            for j, fnp in enumerate(PROPS[tid]):
                im = fnp(np.random.default_rng(9000 + 31 * i + j))
                pp = f"tiles/{tid}_prop_{j}.png"
                im.save(os.path.join(ROOT, pp))
                props.append(pp)
                count += 1
            entry["tiles"]["props"] = props
        if tid in ANIMATED:
            entry["tiles"]["animatedTop"] = True
        if tid in UNDERLAY:
            entry["underlay"] = UNDERLAY[tid]
        patch[tid] = entry
        print("done", tid, flush=True)
    if PATCH:
        with open(PATCH, "w") as fh:
            json.dump(patch, fh, indent=2)
    print("files", count)


if __name__ == "__main__":
    main(sys.argv[1:] or None)

"""Painterly sprite renderer.

Pipeline (all numpy, no GPU):
  1. Orthographic sphere-trace of the SDF figure at SS x supersampling, isometric 3/4 camera.
  2. Lighting: warm key from upper-left, wrong-sky ambient, ground bounce, cool rim, optional
     point lights (lamps), soft shadows and ambient occlusion from the SDF.
  3. Paint pass: softened light bands, world-space brush noise on albedo, cool shadow hue shift,
     then a Kuwahara filter at high resolution so the result reads as flat brush strokes.
  4. Emissive glow, downsample to 1x, light sharpen, soft ground shadow.

Output is an RGBA uint8 array of the requested canvas, feet anchored at `anchor`.
"""
from dataclasses import dataclass, field
from typing import Callable, Optional
import numpy as np

from sdf import smin, fbm, vnoise


@dataclass
class Material:
    albedo: object                      # rgb tuple 0..1, or fn(p, n) -> (N,3)
    spec: float = 0.05                  # specular strength
    gloss: float = 16.0                 # blinn exponent
    metal: float = 0.0                  # tints spec by albedo
    emissive: object = None             # rgb tuple 0..1 or None
    sss: float = 0.0                    # warm wrap for skin
    brush: float = 0.06                 # albedo brush-noise strength
    rim: float = 1.0


@dataclass
class Part:
    prim: object
    mat: str
    k: float = 0.0                      # smooth-union radius with what came before


@dataclass
class Light:
    pos: np.ndarray
    color: tuple
    intensity: float
    radius: float                       # falloff distance


@dataclass
class Scene:
    parts: list
    materials: dict
    lights: list = field(default_factory=list)
    ground_clip: bool = False           # cut everything below y=0 (sinking deaths, burrowing)


def _hex(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def srgb_to_lin(c):
    c = np.asarray(c, dtype=np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(c, 0, None)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


# --------------------------------------------------------------------------- scene eval

def _bounds(scene):
    bb = getattr(scene, '_bb', None)
    if bb is None:
        C = np.array([p.prim.bc for p in scene.parts], dtype=np.float64)
        R = np.array([p.prim.br for p in scene.parts], dtype=np.float64)
        bb = (C, R, (C * C).sum(1))
        scene._bb = bb
    return bb


def scene_eval(scene, p, want_mat=False):
    n = len(p)
    D = np.full(n, 1e3)
    raw = np.full(n, 1e3)
    mat = np.zeros(n, dtype=np.int32)
    C, R, C2 = _bounds(scene)
    # distances to every part's bounding sphere in one matmul
    d2 = (p * p).sum(1)[:, None] + C2[None, :] - 2.0 * (p @ C.T)
    BD = np.sqrt(np.maximum(d2, 0.0)) - R[None, :]
    for i, part in enumerate(scene.parts):
        bd = BD[:, i]
        m = bd < (D + part.k + 0.02)
        if not m.any():
            continue
        if m.all():
            d = part.prim(p)
        else:
            d = bd.copy()
            d[m] = part.prim(p[m])
        D = smin(D, d, part.k) if part.k > 0 else np.minimum(D, d)
        if want_mat:
            closer = d < raw
            raw = np.where(closer, d, raw)
            mat = np.where(closer, i, mat)
    if scene.ground_clip:
        D = np.maximum(D, -p[:, 1])
    return (D, mat) if want_mat else D


def calc_normal(scene, p, e=0.0015):
    k = np.array([[1, -1, -1], [-1, -1, 1], [-1, 1, -1], [1, 1, 1]], dtype=np.float64)
    nrm = np.zeros_like(p)
    for kk in k:
        nrm += kk[None, :] * scene_eval(scene, p + kk * e)[:, None]
    return nrm / np.linalg.norm(nrm, axis=1, keepdims=True)


def calc_ao(scene, p, n):
    occ, sca = 0.0, 1.0
    for i in range(5):
        h = 0.015 + 0.06 * i
        d = scene_eval(scene, p + n * h)
        occ = occ + (h - d) * sca
        sca *= 0.75
    return np.clip(1.0 - 2.2 * occ, 0.0, 1.0)


def soft_shadow(scene, ro, rd, k=10.0, tmax=2.5, steps=40):
    """Soft shadow factor (1 = lit). Rays drop out once fully shadowed or past tmax."""
    n = len(ro)
    res = np.ones(n)
    t = np.full(n, 0.02)
    alive = np.arange(n)
    for _ in range(steps):
        if len(alive) == 0:
            break
        h = scene_eval(scene, ro[alive] + rd[alive] * t[alive, None])
        res[alive] = np.minimum(res[alive], k * h / t[alive])
        t[alive] = t[alive] + np.clip(h, 0.01, 0.2)
        keep = (t[alive] < tmax) & (res[alive] > 0.002)
        alive = alive[keep]
    return np.clip(res, 0.0, 1.0)


# --------------------------------------------------------------------------- image ops

def box_blur(img, r):
    """Separable box blur on (H,W,...) using cumsum, edge-clamped."""
    if r <= 0:
        return img
    out = img
    for axis in (0, 1):
        pad = [(0, 0)] * out.ndim
        pad[axis] = (r + 1, r)
        a = np.pad(out, pad, mode='edge')
        c = np.cumsum(a, axis=axis)
        n = out.shape[axis]
        hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
        lo = np.take(c, np.arange(0, n), axis=axis)
        out = (hi - lo) / (2 * r + 1)
    return out


def gauss_blur(img, sigma):
    r = max(1, int(round(sigma * 0.9)))
    for _ in range(3):
        img = box_blur(img, r)
    return img


def kuwahara(rgb, mask, r):
    """Classic 4-quadrant Kuwahara on premultiplied rgb; keeps flat painted strokes."""
    H, W, _ = rgb.shape
    lum = rgb @ np.array([0.3, 0.59, 0.11])
    pad = r
    P = np.pad(rgb, ((pad, pad), (pad, pad), (0, 0)), mode='edge')
    L = np.pad(lum, ((pad, pad), (pad, pad)), mode='edge')

    def integral(a):
        s = np.cumsum(np.cumsum(a, axis=0), axis=1)
        return np.pad(s, ((1, 0), (1, 0)) + ((0, 0),) * (a.ndim - 2))

    I_rgb, I_l, I_l2 = integral(P), integral(L), integral(L * L)
    best_var = np.full((H, W), np.inf)
    out = rgb.copy()
    ys, xs = np.mgrid[0:H, 0:W]
    n = (r + 1) ** 2
    for oy, ox in ((0, 0), (0, r), (r, 0), (r, r)):
        y0, x0 = ys + oy, xs + ox
        y1, x1 = y0 + r + 1, x0 + r + 1

        def box(I):
            return I[y1, x1] - I[y0, x1] - I[y1, x0] + I[y0, x0]
        m = box(I_l) / n
        var = box(I_l2) / n - m * m
        mean = box(I_rgb) / n
        better = var < best_var
        best_var = np.where(better, var, best_var)
        out = np.where(better[..., None], mean, out)
    return np.where(mask[..., None], out, rgb)


# --------------------------------------------------------------------------- camera / render

@dataclass
class Camera:
    width: int = 96
    height: int = 112
    anchor: tuple = (48, 104)
    ppm: float = 52.0          # 1x pixels per metre
    azimuth: float = 38.0      # degrees; camera swings toward the figure's right side
    elevation: float = 30.0
    ss: int = 4                # supersampling

    def basis(self):
        az, el = np.radians(self.azimuth), np.radians(self.elevation)
        c = np.array([-np.sin(az) * np.cos(el), np.sin(el), np.cos(az) * np.cos(el)])
        fwd = -c
        right = np.cross(fwd, [0, 1, 0])
        right /= np.linalg.norm(right)
        up = np.cross(right, fwd)
        return fwd, right, up


@dataclass
class Look:
    """Global lighting and paint settings (one per faction or scene mood)."""
    key_dir_screen: tuple = (-0.55, 0.75, 0.55)  # (right, up, toward camera) in camera space
    key_color: tuple = (1.0, 0.95, 0.86)
    key_int: float = 1.35
    sky: tuple = (0.62, 0.66, 0.70)               # wrong-sky ambient (greenish lilac, dull)
    sky_int: float = 0.30
    bounce: tuple = (0.80, 0.74, 0.62)            # salt-flat bounce
    bounce_int: float = 0.22
    rim_dir_screen: tuple = (0.8, 0.35, -0.6)
    rim_color: tuple = (0.70, 0.86, 0.95)
    rim_int: float = 0.55
    shadow_tint: tuple = (0.70, 0.80, 1.0)
    bands: float = 0.35                           # 0 = smooth, 1 = hard light bands
    kuwahara: int = 2                             # radius at supersampled res, 0 = off
    exposure: float = 1.0
    ground_shadow: float = 0.55
    contrast: float = 0.3
    sharpen: float = 0.7
    edge_dark: float = 0.45
    edge_color: tuple = (0.07, 0.08, 0.12)
    flash: float = 0.0                            # hit flash toward white (figure only)
    toon: float = 0.0                             # 1 = cel shading: hard light/shadow, hard rim and spec


def render(scene: Scene, cam: Camera = Camera(), look: Look = Look(), debug=False):
    fwd, right, up = cam.basis()
    ss = cam.ss
    W, H = cam.width * ss, cam.height * ss
    xs = (np.arange(W) + 0.5) / ss - cam.anchor[0]
    ys = cam.anchor[1] - (np.arange(H) + 0.5) / ss
    U, V = np.meshgrid(xs, ys)
    U, V = U.ravel() / cam.ppm, V.ravel() / cam.ppm
    origin = -fwd * 6.0
    ro = origin[None, :] + U[:, None] * right[None, :] + V[:, None] * up[None, :]
    rd = np.broadcast_to(fwd, ro.shape)
    N = len(ro)

    # --- sphere trace with active-ray compaction
    t = np.zeros(N)
    hit = np.zeros(N, dtype=bool)
    alive = np.arange(N)
    # skip rays that miss the figure's overall bound
    lo = np.min([p.prim.bc - p.prim.br for p in scene.parts], axis=0)
    hi = np.max([p.prim.bc + p.prim.br for p in scene.parts], axis=0)
    bc, br = (lo + hi) / 2, np.linalg.norm(hi - lo) / 2
    oc = ro - bc
    b = oc @ fwd
    disc = b * b - (np.einsum('ij,ij->i', oc, oc) - br * br)
    alive = alive[disc > 0]
    t[alive] = np.maximum(-b[alive] - np.sqrt(disc[alive]), 0)
    tmax = 12.0
    for it in range(220):
        if len(alive) == 0:
            break
        p = ro[alive] + fwd * t[alive, None]
        d = scene_eval(scene, p)
        done = d < 0.0006
        hit[alive[done]] = True
        t[alive] += d * 0.9
        keep = (~done) & (t[alive] < tmax)
        alive = alive[keep]

    idx = np.nonzero(hit)[0]
    P = ro[idx] + fwd * t[idx, None]
    _, mat_i = scene_eval(scene, P, want_mat=True)
    Nrm = calc_normal(scene, P)
    AO = calc_ao(scene, P, Nrm)

    def cam_dir(v):
        v = np.asarray(v, dtype=np.float64)
        w = v[0] * right + v[1] * up - v[2] * fwd
        return w / np.linalg.norm(w)

    Lk = cam_dir(look.key_dir_screen)
    Lr = cam_dir(look.rim_dir_screen)
    Vd = -fwd
    shadow = soft_shadow(scene, P + Nrm * 0.004, np.broadcast_to(Lk, P.shape))

    mats = list(scene.materials.keys())
    part_mat = np.array([mats.index(p.mat) for p in scene.parts])
    mid = part_mat[mat_i]

    albedo = np.zeros((len(P), 3))
    spec_s = np.zeros(len(P)); gloss = np.ones(len(P)); metal = np.zeros(len(P))
    emis = np.zeros((len(P), 3)); sss = np.zeros(len(P)); brush = np.zeros(len(P))
    rimw = np.zeros(len(P))
    for j, name in enumerate(mats):
        m = mid == j
        if not m.any():
            continue
        M = scene.materials[name]
        a = M.albedo(P[m], Nrm[m]) if callable(M.albedo) else np.array(M.albedo)[None, :]
        albedo[m] = a
        spec_s[m], gloss[m], metal[m] = M.spec, M.gloss, M.metal
        sss[m], brush[m], rimw[m] = M.sss, M.brush, M.rim
        if M.emissive is not None:
            emis[m] = M.emissive(P[m], Nrm[m]) if callable(M.emissive) else np.array(M.emissive)[None, :]

    # brush noise: stretched world-space noise modulates albedo value
    bn = fbm(P * np.array([1.0, 0.35, 1.0]), 38.0, 3) - 0.5
    albedo = albedo * (1.0 + brush[:, None] * 2.0 * bn[:, None] * (1 - look.toon))
    alb = srgb_to_lin(np.clip(albedo, 0, 1))

    ndl = Nrm @ Lk
    wrap = (ndl + sss * 0.5) / (1 + sss * 0.5)
    diff = np.clip(wrap, 0, 1) * shadow
    # painterly banding of the key light
    banded = np.clip((np.floor(diff * 3.0 + 0.5) / 3.0), 0, 1)
    soft_b = diff + (banded - diff) * look.bands
    if look.toon:
        def _st(e0, e1, x):
            t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
        cel = 0.12 + 0.70 * _st(0.22, 0.26, diff) + 0.18 * _st(0.74, 0.77, diff)
        soft_b = soft_b + (cel - soft_b) * look.toon
        AO = AO + (np.where(AO > 0.55, 1.0, 0.7) - AO) * look.toon
    key = soft_b[:, None] * np.array(look.key_color) * look.key_int

    sky_w = 0.5 + 0.5 * Nrm[:, 1]
    amb = (np.array(look.sky)[None, :] * (sky_w[:, None] * look.sky_int)
           + np.array(look.bounce)[None, :] * ((1 - sky_w)[:, None] * look.bounce_int))
    amb = amb * AO[:, None]
    # cool hue shift where the key light does not reach
    tint = np.array(look.shadow_tint)[None, :]
    amb = amb * (tint + (1 - tint) * soft_b[:, None])

    fres = np.power(np.clip(1 - Nrm @ Vd, 0, 1), 2.5)
    rimt = fres * np.clip(Nrm @ Lr + 0.3, 0, 1)
    if look.toon:
        rimt = rimt + ((rimt > 0.30) * 0.75 - rimt) * look.toon
    rim = (rimt * rimw)[:, None] * np.array(look.rim_color) * look.rim_int

    color = alb * (key + amb) + alb * rim * 0.6 + rim * 0.25

    Hh = Lk + Vd
    Hh /= np.linalg.norm(Hh)
    sp = np.power(np.clip(Nrm @ Hh, 0, 1), gloss) * spec_s * shadow
    if look.toon:
        sp = sp + ((sp > 0.25 * np.maximum(spec_s, 1e-3)) * spec_s * 0.9 - sp) * look.toon
    spec_col = (1 - metal)[:, None] * np.array(look.key_color)[None, :] + metal[:, None] * alb
    color += sp[:, None] * spec_col * look.key_int

    for L in scene.lights:
        dv = L.pos[None, :] - P
        dist = np.linalg.norm(dv, axis=1)
        ld = dv / dist[:, None]
        att = L.intensity / (1 + (dist / L.radius) ** 2)
        nl = np.clip((Nrm * ld).sum(1) * 0.85 + 0.15, 0, 1)
        lc = srgb_to_lin(np.array(L.color))
        color += alb * (nl * att * (0.6 + 0.4 * AO))[:, None] * lc
        hl = ld + Vd
        hl /= np.linalg.norm(hl, axis=1, keepdims=True)
        sl = np.power(np.clip((Nrm * hl).sum(1), 0, 1), gloss) * spec_s * att * 2.0
        color += sl[:, None] * lc

    color = color * look.exposure + srgb_to_lin(np.clip(emis, 0, 1)) * 1.5

    # --- assemble hi-res buffers
    img = np.zeros((N, 3)); alpha = np.zeros(N); E = np.zeros((N, 3))
    img[idx] = color
    alpha[idx] = 1.0
    E[idx] = srgb_to_lin(np.clip(emis, 0, 1))
    img = img.reshape(H, W, 3); alpha = alpha.reshape(H, W); E = E.reshape(H, W, 3)

    # gentle tonemap then back to display space for the paint filter
    img = img / (1 + 0.25 * img)
    disp = lin_to_srgb(img)
    if look.flash > 0:
        disp = disp * (1 - look.flash) + look.flash
    if look.kuwahara > 0:
        disp = kuwahara(disp, alpha > 0.5, look.kuwahara)

    # --- ground shadow: soft ellipse plus key-light cast shadow on y=0
    gy = ro[:, 1] / -fwd[1]
    G = ro + fwd * gy[:, None]
    # cast shadow only matters near the feet; compute it at 1x on those pixels and upsample
    G1 = G.reshape(H, W, 3)[ss // 2::ss, ss // 2::ss].reshape(-1, 3)
    near = (G1[:, 0] ** 2 + G1[:, 2] ** 2) < 0.9 ** 2
    g1 = np.ones(len(G1))
    if near.any():
        g1[near] = soft_shadow(scene, G1[near] + np.array([0, 0.003, 0]),
                               np.broadcast_to(Lk, G1[near].shape), k=6.0, tmax=2.2, steps=36)
    g1 = g1.reshape(cam.height, cam.width)
    cast = 1 - np.repeat(np.repeat(g1, ss, 0), ss, 1)
    cast = box_blur(cast, ss // 2)
    ell = np.exp(-((G[:, 0] / 0.30) ** 2 + (G[:, 2] / 0.22) ** 2) * 2.2).reshape(H, W)
    feet = np.exp(-((G[:, 0] ** 2 + G[:, 2] ** 2) / 0.35 ** 2)).reshape(H, W)
    sh_a = np.clip(np.maximum(cast * 0.55 * feet, ell * 0.85), 0, 1) * look.ground_shadow
    sh_a = gauss_blur(sh_a, ss * 1.2)
    sh_rgb = np.array([0.10, 0.11, 0.16])

    # composite figure over shadow (premultiplied)
    prem = disp * alpha[..., None] + sh_rgb * (sh_a * (1 - alpha))[..., None]
    A = alpha + sh_a * (1 - alpha)

    # emissive bloom (adds light and a little alpha halo)
    glow = gauss_blur(E, ss * 2.5) * 0.9 + gauss_blur(E, ss * 6) * 0.5
    glow_s = lin_to_srgb(np.clip(glow, 0, 1))
    gl = glow_s.max(axis=2)
    prem = prem + glow_s * 0.55
    A = np.clip(A + gl * 0.45 * (1 - A), 0, 1)

    # --- downsample
    def down(a):
        sh = (cam.height, ss, cam.width, ss) + a.shape[2:]
        return a.reshape(sh).mean(axis=(1, 3))
    prem1, A1 = down(prem), down(A)
    rgb1 = prem1 / np.maximum(A1[..., None], 1e-6)
    # light unsharp mask for crisp 1x read
    blur = gauss_blur(rgb1, 1.0)
    rgb1 = np.clip(rgb1 + (rgb1 - blur) * look.sharpen, 0, 1)
    # value contrast: gentle S-curve around mid grey
    rgb1 = np.clip(rgb1 + look.contrast * (rgb1 - 0.5) * (1 - np.abs(2 * rgb1 - 1)), 0, 1)
    # silhouette darkening: figure pixels next to empty space get a soft ink edge
    F1 = down(alpha)
    nb = np.minimum.reduce([np.roll(F1, 1, 0), np.roll(F1, -1, 0), np.roll(F1, 1, 1), np.roll(F1, -1, 1)])
    edge = np.clip(F1 - nb, 0, 1) * (F1 > 0.3)
    rgb1 = rgb1 * (1 - look.edge_dark * edge[..., None]) + np.array(look.edge_color) * look.edge_dark * edge[..., None]
    out = np.dstack([rgb1, A1])
    out = (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
    if debug:
        return out, dict(hits=len(idx))
    return out

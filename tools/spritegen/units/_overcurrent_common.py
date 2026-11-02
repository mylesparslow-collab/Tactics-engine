"""Shared Overcurrent helpers: the faction Look (cel, lit from below), skin/jelly/tooth materials with
fake see-through organs, tube/ribbon sweeps, teeth rows, fish bodies, drips, ripples, placement
(hover, yaw, squash) and the dry-husk death.

Shape language: big pale soft shapes with too much mouth, a cyan lit underside, trailing threads.
Pure animals: nothing here is made, worn or carried.
"""
import dataclasses
import numpy as np
from render import Camera, Look, Material, Part, Light, Scene, _hex
from sdf import (v3, norm, basis_from, rot_y, rot_x, rot_z, Sphere, Ellipsoid, Capsule, RoundBox,
                 Cylinder, Torus, Func, Prim, Subtract, smax, smin, fbm, vnoise)
from kit.anim import creature_frames, CREATURE_DEFAULTS, ROWS
from kit.xform import Xform, Squash

FACTION = 'overcurrent'
CERU = _hex('#8cc7e8')
PEARL = _hex('#f4f0ff')
CYAN = _hex('#5fe0e6')
RED = _hex('#c4344a')
ABYSS = _hex('#0b1730')
PINK = _hex('#e8a0b0')
GREEN = _hex('#7fe08a')
HUSK = _hex('#d6cfba')
GOLD = _hex('#f0d890')

LOOK = dataclasses.replace(
    Look(), key_dir_screen=(-0.30, -0.45, 0.85), key_color=(0.80, 0.95, 1.0), key_int=0.80,
    sky=(0.80, 0.86, 1.0), sky_int=0.40, bounce=(0.55, 0.90, 0.95), bounce_int=0.26,
    rim_dir_screen=(0.6, 0.7, -0.5), rim_color=(0.62, 0.92, 1.0), rim_int=0.30,
    shadow_tint=(0.55, 0.68, 1.0), exposure=1.08, ground_shadow=0.7,
    toon=1.0, kuwahara=0, bands=0.0, contrast=0.12, sharpen=0.25, edge_dark=0.0)

_FWD = Camera().basis()[0]
DEFAULTS = dict(CREATURE_DEFAULTS)
DEFAULTS.update(ph=0.0, open=0.1, spit=0.0, ring=0.0, ext=0.0)


def pose(**kw):
    P = dict(DEFAULTS)
    P.update(kw)
    return P


# ------------------------------------------------------------------ parts plumbing

def new_parts():
    parts = []

    def add(prim, mat, k=0.0):
        parts.append(Part(prim, mat, k))
    return parts, add


def lerp(a, b, t):
    return a + (b - a) * t


def spline(pts, n):
    """Catmull-Rom through pts, n samples."""
    pts = [np.asarray(p, dtype=np.float64) for p in pts]
    if len(pts) < 3:
        return [pts[0] + (pts[-1] - pts[0]) * t for t in np.linspace(0, 1, n)]
    P = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    segs = len(pts) - 1
    for i in range(n):
        u = i / (n - 1) * segs
        s = min(int(u), segs - 1)
        t = u - s
        p0, p1, p2, p3 = P[s], P[s + 1], P[s + 2], P[s + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return out


def curve_r(radii, n):
    """Interpolate a short radii list to n samples."""
    x = np.linspace(0, 1, len(radii))
    return np.interp(np.linspace(0, 1, n), x, radii)


def tube(add, pts, radii, mat, n=14, k=0.03):
    """Round tapered tube through pts (spline) as chained capsules. Returns the sample points."""
    s = spline(pts, n)
    r = curve_r(radii, n)
    for i in range(n - 1):
        add(Capsule(s[i], s[i + 1], r[i], r[i + 1]), mat, k)
    return s


def ribbon(add, pts, widths, thick, mat, n=16, k=0.03, side=None):
    """Flat band through pts: each sample is an ellipsoid whose wide axis is `side` (default world up
    projected off the tangent) so the band can stand on edge. widths/thick are half-sizes."""
    s = spline(pts, n)
    w = curve_r(widths, n)
    th = curve_r(thick, n) if np.ndim(thick) else np.full(n, float(thick))
    for i in range(n - 1):
        a, b = s[i], s[i + 1]
        d = b - a
        L = np.linalg.norm(d)
        t = d / max(L, 1e-9)
        hint = v3(0, 1, 0) if side is None else np.asarray(side, dtype=np.float64)
        wide = hint - t * (hint @ t)
        if np.linalg.norm(wide) < 1e-6:
            wide = v3(1, 0, 0)
        wide = norm(wide)
        thin = np.cross(t, wide)
        R = np.stack([thin, t, wide], axis=1)      # local y = tangent, local z = wide
        add(Ellipsoid((a + b) / 2, (th[i], L * 0.75, w[i]), R), mat, k)
    return s


def tooth_arc(add, c, R, rad, a0, a1, n, length, r=0.014, drop=(0, -1, 0), mat='tooth', flat=1.0, wob=0.0, seed=1):
    """Row of needle teeth on an arc of an ellipse in local xz of frame R centred at c; teeth point along
    local `drop` (local coords). a in radians (0 = +z forward, positive toward +x)."""
    rng = np.random.default_rng(seed)
    dl = R @ norm(v3(*drop))
    for i in range(n):
        a = lerp(a0, a1, i / max(n - 1, 1))
        q = c + R @ v3(np.sin(a) * rad, 0, np.cos(a) * rad * flat)
        ln = length * (1 + wob * rng.uniform(-1, 1))
        tilt = R @ v3(np.sin(a) * 0.35, 0, np.cos(a) * 0.35 * flat)
        add(Capsule(q, q + norm(dl + tilt * 0.4) * ln, r, 0.004), mat, 0.0)


def eye(add, c, r, mat='eye', pupil='pupil', look=(0, 0, 1), pr=0.55):
    add(Sphere(c, r), mat, 0.0)
    d = norm(v3(*look))
    add(Sphere(c + d * r * 0.62, r * pr), pupil, 0.0)


def fin(add, root, tip, width, mat='fin', thick=0.012, n=6, k=0.02, curl=0.0, wide=None):
    """Leaf fin from root to tip: a flat ellipsoid pair (leaf)."""
    root, tip = np.asarray(root, dtype=np.float64), np.asarray(tip, dtype=np.float64)
    d = tip - root
    L = np.linalg.norm(d)
    t = d / L
    if wide is not None:
        w = norm(np.asarray(wide, dtype=np.float64) - t * (np.asarray(wide, dtype=np.float64) @ t))
    else:
        hint = v3(0, 1, 0)
        w = norm(hint - t * (hint @ t)) if abs(t[1]) < 0.95 else v3(1, 0, 0)
    wide = w
    thin = np.cross(t, wide)
    R = np.stack([thin, t, wide], axis=1)
    add(Ellipsoid(root + d * 0.5, (thick, L * 0.52, width), R), mat, k)


class Frame:
    """Local frame (origin o, rotation R, uniform scale s) so heads, jaws and limbs are built in their
    own coordinates and emitted straight into the parent frame (no nested transforms at render time)."""

    def __init__(self, o=(0, 0, 0), R=None, s=1.0):
        self.o, self.R, self.s = v3(*o), (np.eye(3) if R is None else R), s

    def p(self, v):
        return self.o + self.s * (self.R @ np.asarray(v, dtype=np.float64))

    def d(self, v):
        return self.R @ np.asarray(v, dtype=np.float64)

    def child(self, o=(0, 0, 0), R=None, s=1.0):
        return Frame(self.p(o), self.R if R is None else self.R @ R, self.s * s)

    def ell(self, add, c, rad, mat, k=0.0, R2=None):
        R = self.R if R2 is None else self.R @ R2
        add(Ellipsoid(self.p(c), tuple(np.asarray(rad) * self.s), R), mat, k)

    def cap(self, add, a, b, ra, rb=None, mat='skin', k=0.0):
        rb = ra if rb is None else rb
        add(Capsule(self.p(a), self.p(b), ra * self.s, rb * self.s), mat, k)

    def sph(self, add, c, r, mat, k=0.0):
        add(Sphere(self.p(c), r * self.s), mat, k)

    def tor(self, add, c, axis, R0, r, mat, k=0.0):
        add(Torus(self.p(c), self.d(axis), R0 * self.s, r * self.s), mat, k)

    def tooth(self, add, a, b, r=0.014, mat='tooth'):
        add(Capsule(self.p(a), self.p(b), r * self.s, 0.004), mat, 0.0)



def fish(F, add, ph=0.0, mouth=0.1, eye_look=(0, -0.3, 1.0), belly_eye=True, mat='skin', fin_mat='fin', big=1.0):
    """A small fish in frame F (nose +z, back +y, belly -y), about 0.34 long at F.s = 1.
    Belly eye: a wet pink eye set in the lit underside with a cyan ring and a pupil that tracks eye_look."""
    sw = np.sin(ph)
    F.ell(add, (0, 0, 0.0), (0.055, 0.085, 0.15), mat)
    F.ell(add, (0, -0.005, 0.12), (0.045, 0.058, 0.075), mat, 0.03)
    F.cap(add, (0, 0, -0.10), (0.012 * sw, 0, -0.20), 0.036, 0.016, mat, 0.03)
    fin(add, F.p((0.012 * sw, 0, -0.18)), F.p((0.05 * sw, 0, -0.34)), 0.095 * F.s, fin_mat, 0.008 * F.s, k=0.0)
    fin(add, F.p((0, 0.07, 0.04)), F.p((0, 0.18, -0.07)), 0.04 * F.s, fin_mat, 0.008 * F.s)
    for sx in (-1, 1):
        fin(add, F.p((sx * 0.05, -0.03, 0.07)), F.p((sx * 0.13 + 0.02 * sw * sx, -0.08, -0.03)), 0.035 * F.s, fin_mat, 0.007 * F.s)
        F.sph(add, (sx * 0.042, 0.02, 0.15), 0.018, 'eyeb')
    F.ell(add, (0, -0.02, 0.195), (0.026, 0.015 + 0.02 * mouth, 0.03), 'gum', 0.02)
    for sx in (-1, 1):
        F.tooth(add, (sx * 0.018, -0.03, 0.215), (sx * 0.016, -0.03 - 0.02 - 0.015 * mouth, 0.222), 0.005)
    if belly_eye:
        ec = v3(0, -0.07 * big, 0.03)
        F.sph(add, ec, 0.066 * big, 'eye', 0.02)
        F.tor(add, ec + v3(0, -0.005, 0), (0, -1, 0), 0.075 * big, 0.011, 'glow')
        d = norm(v3(*eye_look))
        F.sph(add, ec + d * 0.04 * big, 0.036 * big, 'iris')
        F.sph(add, ec + d * 0.062 * big, 0.019 * big, 'pupil')
    F.cap(add, (0.03, 0.0, 0.1), (0.045, -0.03, 0.12), 0.012, 0.008, 'finred')



def goblin(F, add, ph=0.0, ext=0.7, gape=0.4, tl=0.15, frills=5, bulk=1.0, ntooth=8, js=1.5, gold=False, tr=0.019, snout=1.0, reach=1.0, lig=False):
    """Goblin shark in frame F (nose +z, back +y): tapered body, blade snout, red gill frills, big soft fins and the
    sling-jaw cocked forward on a pink ligament. ext 0..1 jaw protrusion, gape 0..1 mouth opening.
    Returns the jaw frame (for drips and effects)."""
    sw = np.sin(ph)
    pts = [F.p((0, 0.06, -1.15)), F.p((0.03 * sw, 0.05, -0.80)), F.p((0.02 * sw, 0.03, -0.35)), F.p((0, 0.02, 0.05)), F.p((0, 0.0, 0.38))]
    tube(add, pts, [0.02 * F.s, 0.07 * F.s * bulk, 0.17 * F.s * bulk, 0.18 * F.s * bulk, 0.12 * F.s * bulk], 'skin', n=14, k=0.05)
    F.ell(add, (0, 0.0, 0.28), (0.15 * bulk, 0.15 * bulk, 0.20), 'skin', 0.06)
    # blade snout
    F.ell(add, (0, 0.09, 0.26 + 0.36 * snout), (0.10, 0.025, 0.36 * snout), 'snout', 0.04)
    F.ell(add, (0, 0.06, 0.40), (0.14, 0.05, 0.16), 'snout', 0.04)
    # tail: long upper lobe and short lower
    fin(add, F.p((0, 0.05 * 1, -1.05)), F.p((0.04 * sw, 0.52, -1.45)), 0.075 * F.s, 'fin', 0.012 * F.s, wide=(0, 0, 1))
    fin(add, F.p((0, 0.04, -1.1)), F.p((0.03 * sw, -0.22, -1.38)), 0.05 * F.s, 'fin', 0.012 * F.s, wide=(0, 0, 1))
    # dorsal, pectorals (huge, soft), pelvic
    fin(add, F.p((0, 0.15, -0.10)), F.p((0, 0.52, -0.42)), 0.13 * F.s, 'fin', 0.014 * F.s, wide=(0, 0, 1))
    fin(add, F.p((0, 0.10, -0.62)), F.p((0, 0.30, -0.78)), 0.06 * F.s, 'fin', 0.012 * F.s, wide=(0, 0, 1))
    for sx in (-1, 1):
        fin(add, F.p((sx * 0.13, -0.05, 0.12)), F.p((sx * 0.58, -0.22 + 0.05 * sw * sx, -0.30)), 0.17 * F.s, 'fin', 0.014 * F.s)
        fin(add, F.p((sx * 0.08, -0.10, -0.55)), F.p((sx * 0.30, -0.22, -0.78)), 0.08 * F.s, 'fin', 0.012 * F.s)
        # gill frills
        for i in range(frills):
            c = F.p((sx * 0.145, 0.0 + 0.02 * (i % 2), 0.20 - 0.065 * i))
            add(Ellipsoid(c, (0.015 * F.s, 0.085 * F.s, 0.018 * F.s), None), 'finred', 0.0)
            add(Ellipsoid(c + F.d((sx * 0.02, 0.06, 0.0)) * F.s, (0.012 * F.s, 0.04 * F.s, 0.02 * F.s), None), 'finred', 0.0)
        F.sph(add, (sx * 0.12, 0.10, 0.36), 0.032, 'eyeb')
    # the sling-jaw
    ex = (0.12 + 0.42 * ext) * reach
    F.cap(add, (0, -0.06, 0.26), (0, -0.07, 0.26 + ex), 0.07, 0.10, 'gum', 0.04)
    if lig:
        for sx in (-1, 1):
            F.cap(add, (sx * 0.06, -0.03, 0.22), (sx * 0.07, -0.07, 0.26 + ex), 0.018, 0.014, 'gum', 0.0)
    J = F.child((0, -0.06, 0.26 + ex), None, js)
    J.ell(add, (0, 0.03, 0.12), (0.11, 0.05, 0.20), 'skin', 0.03)
    J.ell(add, (0, -0.005, 0.12), (0.09, 0.03 + 0.04 * gape, 0.17), 'gum')
    for i in range(ntooth):
        z = 0.02 + i * 0.045
        for sx in (-1, 1):
            q = v3(sx * 0.095, 0.0, z)
            J.tooth(add, q, q + v3(sx * 0.014, -0.15 * (tl / 0.15), 0.07), tr, 'tooth')
            if gold:
                J.sph(add, q + v3(sx * 0.014, -0.15 * (tl / 0.15), 0.07), 0.011, 'gold')
    JL = J.child((0, -0.005, 0.0), rot_x(0.12 + 0.7 * gape))
    JL.ell(add, (0, -0.03, 0.12), (0.10, 0.04, 0.20), 'skin', 0.0)
    JL.ell(add, (0, 0.0, 0.12), (0.085, 0.02, 0.17), 'gum', 0.0)
    for i in range(ntooth):
        z = 0.03 + i * 0.045
        for sx in (-1, 1):
            q = v3(sx * 0.085, 0.0, z)
            JL.tooth(add, q, q + v3(sx * 0.01, 0.15 * (tl / 0.15), 0.07), tr, 'tooth')
            if gold:
                JL.sph(add, q + v3(sx * 0.01, 0.15 * (tl / 0.15), 0.07), 0.011, 'gold')
    return J


# ------------------------------------------------------------------ placement / end state

class Placer:
    """local -> world: squash about the ground, yaw/roll/pitch about the origin, then hover/bob.
    Death (P['end'] -> 1) flattens everything onto the salt. `.pt(v)` maps points, `.inv(p)` maps world
    points back to the body frame (so painted patterns stay glued to the body)."""

    def __init__(self, P, yaw=0.7, pitch=0.0, roll=0.0, hover=0.0, t=(0, 0, 0), scale=1.0, shift=0.0, back=0.0, R=None):
        e = P['end']
        self.e = e
        self.sy = max(P['squash'], 0.05) * (1 - 0.88 * e)
        self.sxz = (1 + (1 - P['squash']) * 0.5) * (1 + 0.20 * e)
        self.R = (rot_y(yaw) @ rot_z(roll) @ rot_x(pitch + P['lean'] * 0.6)) if R is None else R @ rot_x(P['lean'] * 0.6)
        h = hover * (1 - e) + P['bob']
        self.t = v3(*t) + v3(0, h, 0) + shift * v3(0.788, 0, 0.616) + back * v3(0.616, 0, -0.788)
        self.s = scale
        self.sc = np.array([self.sxz, self.sy, self.sxz])

    def pt(self, v):
        v = np.asarray(v, dtype=np.float64)
        return (self.R @ (v * self.s)) * self.sc + self.t

    def inv(self, p):
        q = (p - self.t) / self.sc
        return (q @ self.R) / self.s

    def parts(self, parts):
        return [Part(_Placed(pt.prim, self), pt.mat, pt.k) for pt in parts]


class _Placed(Prim):
    """One-matrix wrapper: evaluates prim in the body frame (inverse of the Placer transform)."""

    def __init__(self, prim, pl):
        self.prim, self.pl = prim, pl
        self.bc = pl.pt(prim.bc)
        self.br = prim.br * pl.s * float(pl.sc.max())
        self.f = pl.s * min(pl.sy, pl.sxz)

    def __call__(self, p):
        return self.prim(self.pl.inv(p)) * self.f


def R_from(y_dir, z_dir):
    """Rotation whose local y is y_dir and local z is as near z_dir as possible."""
    y = norm(y_dir)
    z = np.asarray(z_dir, dtype=np.float64)
    z = norm(z - y * (z @ y))
    return np.stack([np.cross(y, z), y, z], axis=1)


def drips(add, P, pts, mat='water', r=0.016, rise=0.20, phase=0.37):
    """Droplets that rise a little off the body, hang, then fall. World-space points."""
    if P['end'] > 0.3:
        return
    for i, q in enumerate(pts):
        t = (P['tell'] + i * phase) % 1.0
        h = rise * np.sin(np.pi * min(t / 0.55, 1.0)) if t < 0.55 else rise * 0.0 - (t - 0.55) * 0.9
        y = q[1] + h
        if y < 0.04:
            continue
        a = 1.0 if t < 0.55 else max(0.0, 1.0 - (t - 0.55) * 2.2)
        add(Sphere(v3(q[0], y, q[2]), r * (0.6 + 0.4 * a) * (1.2 if i % 2 else 0.9)), mat, 0.0)


def spray(add, P, origin, n=4, up=0.5, mat='water'):
    """A burst of droplets thrown upward (hit / attack)."""
    s = P['spit']
    if s <= 0:
        return
    rng = np.random.default_rng(5)
    for i in range(n):
        a = rng.uniform(0, 6.28)
        add(Sphere(origin + v3(np.cos(a) * 0.22 * s * rng.uniform(0.4, 1), up * s * rng.uniform(0.5, 1.1),
                               np.sin(a) * 0.2 * s * rng.uniform(0.4, 1)), 0.02 * (1.1 - 0.3 * s)), mat, 0.0)


def ripple(add, P, c=(0, 0.02, 0)):
    r = P['ring']
    if r <= 0:
        return
    add(Torus(v3(*c), v3(0, 1, 0), 0.25 + 0.95 * r, 0.018 + 0.012 * (1 - r)), 'ringmat', 0.0)


# ------------------------------------------------------------------ see-through organs

@dataclasses.dataclass
class Organ:
    c: np.ndarray
    r: tuple
    col: tuple
    glow: float = 0.0           # emissive strength (colour = col)
    op: float = 0.75            # how strongly it shows through the skin


def through(p, organs, depth=0.45):
    """For surface points p, march the camera ray straight into the body and report the first organ
    ellipsoid hit: (colour N3, strength N, emissive N3). Fakes a translucent body with plain albedo."""
    N = len(p)
    col = np.zeros((N, 3))
    amt = np.zeros(N)
    emi = np.zeros((N, 3))
    best = np.full(N, 1e9)
    for o in organs:
        r = np.asarray(o.r, dtype=np.float64)
        w = _FWD / r
        q = (p - o.c) / r
        a = w @ w
        b = q @ w
        c = (q * q).sum(1) - 1.0
        disc = b * b - a * c
        t = (-b - np.sqrt(np.maximum(disc, 0))) / a
        ok = (disc > 0) & (t > -0.02) & (t < depth) & (t < best)
        if not ok.any():
            continue
        dm2 = np.clip((q * q).sum(1) - b * b / a, 0, 1)
        shade = 0.55 + 0.45 * np.sqrt(1 - dm2)
        fade = np.clip(1.0 - t / depth, 0, 1) ** 0.7
        s = o.op * fade
        c3 = np.array(o.col)[None, :] * shade[:, None]
        col = np.where(ok[:, None], c3, col)
        amt = np.where(ok, s, amt)
        emi = np.where(ok[:, None], np.array(o.col)[None, :] * (o.glow * np.sqrt(1 - dm2))[:, None], emi)
        best = np.where(ok, t, best)
    return col, amt, emi


def _arr(c, n):
    return np.array(c)[None, :].repeat(n, 0)


def skin(top=None, under=None, organs=(), veins=0.0, vein_col=RED, vfreq=11.0, glow=0.55, spots=None,
         local=None, mottle=0.08, wet=40.0, sss=0.5, spec=0.35, depth=0.45, brush=0.0, belly_cut=(0.0, 0.7)):
    """Pale translucent animal skin. Top face is the cool dark one, the underside is pearl and glows cyan.
    organs: Organ list (world space, already posed) painted through the surface.
    local: fn(world p) -> body-frame p for patterns glued to the body.
    spots: fn(q, n) -> (mask N, colour N3) painted over the skin."""
    top = np.array(top if top is not None else tuple(np.array(CERU) * 0.66 + np.array(PEARL) * 0.06))
    under = np.array(under if under is not None else tuple(np.array(PEARL) * 0.62 + np.array(CERU) * 0.30))
    organs = list(organs)

    def albedo(p, n):
        q = local(p) if local is not None else p
        t = np.clip(0.5 + 0.55 * n[:, 1], 0, 1)[:, None]
        a = under[None, :] * (1 - t) + top[None, :] * t
        a = a * (1 - mottle + 2 * mottle * fbm(q, 9.0, 2)[:, None])
        if veins > 0:
            v = np.abs(vnoise(q + 3.3, vfreq) - 0.5) < 0.035
            v2 = np.abs(vnoise(q + 9.1, vfreq * 2.1) - 0.5) < 0.02
            vm = ((v | v2) * veins)[:, None]
            a = a * (1 - vm * 0.55) + np.array(vein_col)[None, :] * vm * 0.55
        if spots is not None:
            m, c = spots(q, n)
            a = np.where(m[:, None], c, a)
        if organs:
            c3, am, _ = through(p, organs, depth)
            a = a * (1 - am[:, None]) + c3 * am[:, None]
        return a

    def emissive(p, n):
        d = np.clip(-n[:, 1] * 1.25 - belly_cut[0], 0, 1)
        d = np.clip((d - 0.1) / 0.6, 0, 1) ** 1.2
        e = np.array(CYAN)[None, :] * (d * glow)[:, None]
        if organs:
            _, am, em = through(p, organs, depth)
            e = e + em * am[:, None]
        return e

    return Material(albedo, spec=spec, gloss=wet, emissive=emissive, sss=sss, brush=brush)


def jelly(organs=(), glow=0.5, tint=None, rim=True, depth=0.7, local=None, striate=0.0, spec=1.0):
    """Glassy bell: cerulean-pearl, see-through organs, faint cyan glow from below."""
    tint = np.array(tint if tint is not None else tuple(np.array(CERU) * 0.55 + np.array(PEARL) * 0.45))
    organs = list(organs)

    def albedo(p, n):
        q = local(p) if local is not None else p
        t = np.clip(0.5 + 0.5 * n[:, 1], 0, 1)[:, None]
        a = tint[None, :] * (0.85 + 0.25 * (1 - t)) * (1 + 0.0 * t)
        if striate > 0:
            ang = np.arctan2(q[:, 0], q[:, 2])
            m = (np.abs(np.mod(ang * 5 / np.pi, 1.0) - 0.5) < 0.07) * striate
            a = a * (1 - 0.25 * m[:, None])
        if organs:
            c3, am, _ = through(p, organs, depth)
            a = a * (1 - am[:, None]) + c3 * am[:, None]
        return a

    def emissive(p, n):
        d = np.clip((-n[:, 1] - 0.1) / 0.7, 0, 1)
        e = np.array(CYAN)[None, :] * (d * glow)[:, None]
        if organs:
            _, am, em = through(p, organs, depth)
            e = e + em * am[:, None]
        return e
    return Material(albedo, spec=spec, gloss=80, emissive=emissive, sss=0.4)


def std_mats(P, extra=None):
    g = max(P['glow'], 0.0)
    cy = tuple(np.array(CYAN) * 0.95 * g)
    m = {
        'tooth': Material(_hex('#f6efe6'), spec=0.5, gloss=60, sss=0.3),
        'gum': Material(_hex('#d85c78'), spec=0.7, gloss=40, sss=0.6),
        'throat': Material(_hex('#8c2440'), spec=0.5, gloss=30, sss=0.4, rim=0.2),
        'maw': Material(_hex('#4a1226'), spec=0.4, gloss=20, rim=0.1),
        'eye': Material(_hex('#f0b0c0'), spec=1.0, gloss=90, sss=0.3),
        'eyeb': Material(_hex('#161a2c'), spec=1.0, gloss=90),
        'iris': Material(_hex('#d0405a'), spec=0.8, gloss=70),
        'pupil': Material(_hex('#10121e'), spec=1.0, gloss=100, rim=0.0),
        'green': Material(GREEN, spec=1.0, gloss=80, emissive=tuple(np.array(GREEN) * 0.45 * g)),
        'fin': Material(lambda p, n: _arr(tuple(np.array(CERU) * 0.6 + np.array(PEARL) * 0.4), len(p)) *
                        (0.92 + 0.16 * (np.abs(vnoise(p, 14.0) - 0.5) < 0.12)[:, None]),
                        spec=0.6, gloss=50, sss=0.6),
        'finred': Material(_hex('#d04a5e'), spec=0.6, gloss=50, sss=0.6),
        'glow': Material(CYAN, emissive=cy, rim=0.0),
        'lure': Material(CYAN, emissive=tuple(np.array(_hex('#c8fcff')) * 1.1 * g), rim=0.0),
        'water': Material(_hex('#dff4ff'), spec=1.0, gloss=100, emissive=tuple(np.array(CYAN) * 0.35), rim=0.4),
        'slime': Material(_hex('#d8f2f4'), spec=1.0, gloss=90, emissive=tuple(np.array(CYAN) * 0.25), rim=0.3),
        'ringmat': Material(PEARL, emissive=tuple(np.array(CYAN) * 0.9 * max(P['ring'], 0)), rim=0.0),
        'snout': skin(top=_hex('#d8a8c0'), under=_hex('#f4d6e2'), glow=0.5, spec=0.4),
        'abyss': Material(ABYSS, spec=0.4, gloss=30, rim=0.2),
        'puddle': Material(_hex('#8fdde2'), spec=1.0, gloss=70, emissive=tuple(np.array(CYAN) * 0.18), rim=0.2),
        'gold': Material(GOLD, spec=0.9, gloss=60, emissive=tuple(np.array(GOLD) * 0.5), metal=0.4, rim=0.0),
        'bone': Material(_hex('#efe6d2'), spec=0.3, gloss=30),
    }
    if extra:
        m.update(extra)
    return m


def dry(mats, e):
    """Death: colours bleach to grey, then a pale cracked husk; glow and wet spec go out."""
    if e <= 0:
        return mats
    out = {}
    for name, m in mats.items():
        base = m.albedo

        def alb(p, n, base=base):
            a = base(p, n) if callable(base) else _arr(base, len(p))
            g = a @ np.array([0.3, 0.59, 0.11])
            grey = g[:, None] * np.array([1.0, 0.98, 0.92])[None, :]
            k = min(1.0, e * 1.6)
            a = a * (1 - k) + grey * k
            h = np.clip((e - 0.35) / 0.5, 0, 1)
            if h > 0:
                tone = np.array(HUSK)[None, :] * (0.88 + 0.2 * fbm(p, 14.0, 2)[:, None])
                a = a * (1 - h) + tone * h
                crack = (np.abs(vnoise(p, 7.0) - 0.5) < 0.028 * h) | (np.abs(vnoise(p + 5.5, 15.0) - 0.5) < 0.018 * h)
                a[crack] = a[crack] * 0.45
            return a
        m2 = dataclasses.replace(m, albedo=alb)
        m2.spec = m.spec * (1 - e) * 0.5
        m2.sss = m.sss * (1 - e)
        if m.emissive is not None:
            f = (1 - e) ** 2
            if callable(m.emissive):
                m2.emissive = (lambda p, n, fe=m.emissive, f=f: fe(p, n) * f)
            else:
                m2.emissive = tuple(np.array(m.emissive) * f)
        out[name] = m2
    return out


def finish(P, pl, parts, mats, lights=(), world=None, extra_drips=None, hover_lights=True):
    """Place the local-frame parts, add world-space extras (drops, ripples, puddle), apply the dry husk,
    and build the Scene."""
    placed = pl.parts(parts)
    sc_parts, add = new_parts()
    sc_parts.extend(placed)
    if world:
        world(add)
    e = P['end']
    if 0.05 < e < 0.95:
        r = 0.15 + 0.38 * np.sin(np.pi * min(e * 1.15, 1.0)) ** 0.8
        add(Ellipsoid(v3(0, 0.0, 0.05), (r, 0.012, r * 0.8)), 'puddle', 0.0)
    mats = dry(mats, e)
    lights = [Light(L.pos, L.color, L.intensity * (1 - e) ** 1.5, L.radius) for L in lights]
    return Scene(parts=sc_parts, materials=mats, lights=lights, ground_clip=True)


def under_light(P, c, strength=0.9, radius=0.9):
    """Cyan point light below the body: the sea is lit from beneath."""
    return Light(v3(*c), CYAN, strength * max(P['glow'], 0.0), radius)


# ------------------------------------------------------------------ animation rows

def oc_rows(base, atk_open=(0.5, 1.0, 0.0, 0.3), atk_strike=(0.0, 0.45, 1.0, 0.3), idle_amp=1.0, extra=None):
    """Standard Overcurrent rows over creature_frames. Channels used by builds: ph (wave phase), open (jaw 0..1),
    strike, spit, ring, tell, glow, end."""
    def ov(rows):
        for i, (P, o) in enumerate(rows['idle']):
            P['ph'] = 2 * np.pi * i / 4
            P['open'] = [0.12, 0.2, 0.12, 0.06][i]
            P['bob'] = [0.0, 0.025, 0.0, -0.02][i] * idle_amp
        for i, (P, o) in enumerate(rows['move']):
            P['ph'] = 2 * np.pi * i / 4
            P['open'] = 0.15
            P['bob'] = [0.0, 0.03, 0.0, 0.03][i]
        for i, (P, o) in enumerate(rows['attack']):
            P['open'] = atk_open[i]
            P['strike'] = atk_strike[i]
            P['ph'] = 0.8 * i
            P['spit'] = [0, 0, 0.5, 0.2][i]
        for i, (P, o) in enumerate(rows['hit']):
            P['open'] = 0.55 if i == 0 else 0.2
            P['spit'] = [1.0, 0.45][i]
            P['ph'] = 1.0 * i
        for i, (P, o) in enumerate(rows['death']):
            P['open'] = [0.5, 0.7, 0.4, 0.15][i]
            P['ph'] = 0.7 * i
            P['bob'] = [0.0, -0.04, 0, 0][i]
        for i, (P, o) in enumerate(rows['cast']):
            P['ring'] = [0.2, 0.6, 1.0][i]
            P['open'] = [0.3, 0.5, 0.2][i]
            P['ph'] = 1.1 * i
        if extra:
            extra(rows)
        return rows
    f = creature_frames(base, ov)
    return ROWS, f


__all__ = [n for n in dir() if not n.startswith('__')]

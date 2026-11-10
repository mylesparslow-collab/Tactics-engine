"""The Hermitage: shared hermit-crab rig, shell library and animation rows.

Shape language (world/factions/hermitage/ART.md): "a thing on legs with one claw out". A shelled unit is a
plainly human-made object (60-70% of the silhouette) carried tilted back, mouth forward-down toward the
camera, with ONE big violet orange-tipped claw (crab's right, -x), one small claw, two eyestalks with dark
bead eyes and orange tips, and FOUR thick banded walking legs set wide like a table. A bare (evicted) crab is
a raised violet claw over a fat pale spiral tail. Palette: VIOLET / ORANGE crab, TAIL pink-grey (bare only),
object colours RUST, VERDI, TAR, BONE, OAK; LAMP amber only for real lights.

Coordinates: metres, y up, the unit faces +z (lower right on screen), its right hand is -x.

API (everything below is exported by `from _hermitage_common import *`)
-------------------------------------------------------------------------
  SIZES / size_camera(size)  'small' | 'medium' | 'large' | 'great' -> crab scale s and Camera(ppm)
  hermit_pose(**channels)    neutral pose dict (all animation channels, see CHANNELS below)
  Shell(build=fn, ride=..., crab_at=..., ...)
                             how a crab wears an object. fn(add, P, F) adds parts in SHELL-LOCAL coords
                             (origin = object centre, +z = the mouth / forward, +y = up) using F.put(add,
                             prim, mat) or the F.ell/cap/cyl/... helpers, and returns a dict of materials
                             (F.inv(p) maps world->local inside material functions, see local_albedo()).
  shelled(P, size, SHELL, mats=None, lights=(), world=None) -> Scene      crab wearing the shell
  Bare(...) + bare(P, size, BARE, mats=None, world=None) -> Scene        evicted crab, spiral tail
  empty(P, SHELL, place=(o, R), rag=(local pt, local axis, radius), mats=None) -> Scene   vacant shell
  hermit_rows(neutral_pose, kind='shell'|'bare', extra=None) -> (ROWS, frames)
  structure_rows(neutral_pose) -> (ROWS, frames)   idle(2) / hit(2) / death(3, cracks) for empty shells
  Shell library (reuse these, do not redraw them): barrel_shell, diving_bell_shell, chapel_bell_shell,
  boiler_shell, long_gun_shell; helpers Frame, barnacles(), rag(), chela(), eyestalk(), cracked().
  world(add) callbacks add world-space extras: kit.fx emit(add, pos, 'steam'|'smoke'|'embers', s), flashes.

CHANNELS (pose dict, all floats, tween-safe): bob lean squash stride lift_a lift_b sway rock yaw slide recoil
  | eye_l eye_r dip_l dip_r (eyestalk swivel rad / dip 0..1) | raise cock snap drum limp spread open (claw)
  | duck (pull into shell) tip (shell falls on its side) fold (legs curl) flip (bare: on its back)
  | rear (bare: body pitched up) curl (tail tighter) drain (colour to grey) | fx end tell glow cast_glow
  | free unit channels: spin door fire ring ... (add with hermit_pose(spin=0.0)).

Worked example (a complete unit, see hermitage_barrel_squatter.py):

    from _hermitage_common import *
    UNIT_ID, SIZE = 'hermitage_barrel_squatter', 'small'
    CAMERA = size_camera(SIZE)
    SHELL = Shell(build=barrel_shell(length=0.86, r_mid=0.34), ride=0.50, crab_at=(0, -0.02, 0.30),
                  feet=((-0.40, 0.38), (0.40, 0.38), (-0.46, -0.20), (0.46, -0.20)), side_r=0.33)
    def neutral_pose(): return hermit_pose()
    def build(P): return shelled(P, SIZE, SHELL)
    ROWS, frames = hermit_rows(neutral_pose, 'shell')

Per-unit shell abilities go in `extra(rows)` (e.g. set rows['attack'][i][0]['recoil'] and 'fx') and are read
by your shell builder / world() callback. Keep the object nameable at 64 px, no combs (max 3 hoops, 3-5
rivet bosses, 4 posts), smoke only via kit.fx emit().
"""
import dataclasses
from dataclasses import dataclass, field
from typing import Callable, Optional
import numpy as np
from render import Camera, Look, Material, Part, Light, Scene, _hex
from sdf import (v3, norm, basis_from, rot_y, rot_x, rot_z, Sphere, Ellipsoid, Capsule, RoundBox, Cylinder,
                 Torus, Func, Prim, Subtract, Union, smax, smin, fbm, vnoise)
from kit.anim import CREATURE_DEFAULTS
from kit.xform import Xform, Squash, transform_parts, squash_parts
from kit.fx import emit
import rig

FACTION = 'hermitage'

# ------------------------------------------------------------------ palette
VIOLET = _hex('#7b4f8f')        # claws, legs, carapace
VIOLET_DK = _hex('#563466')
VIOLET_LT = _hex('#9a6aae')
ORANGE = _hex('#d9822b')        # tips, joints, eyestalk tips, rust blooms
ORANGE_DK = _hex('#b8621f')
TAIL = _hex('#c9a8a4')          # soft tail (bare only)
TAIL_DK = _hex('#a8827f')
BONE = _hex('#e3d9c6')          # barnacles, salt bloom
RUST = _hex('#6b3f26')          # iron shells
VERDI = _hex('#5f8f7c')         # bronze / copper gone green
TAR = _hex('#1f1a1d')           # tar, eyes, shell interiors
LAMP = _hex('#ffcf70')          # the 5% light
OAK = _hex('#5b4232')           # tarred oak
OAK_GREY = _hex('#8a8178')      # weathered timber
BRASS = _hex('#b08a45')
IRON = _hex('#3b3638')
GREY_VIOLET = _hex('#857c8e')   # drained colour (bare death)
RAG = _hex('#7a3a9e')

LOOK = dataclasses.replace(Look(), rim_color=(0.88, 0.80, 0.98), rim_int=0.6, sky=(0.64, 0.63, 0.70),
                           bounce=(0.84, 0.74, 0.62))

SIZES = {
    # s = crab scale (1.0 = pony-sized medium); ppm = camera pixels per metre (ART.md size table)
    'small': dict(s=0.80, ppm=52.0),
    'medium': dict(s=1.0, ppm=52.0),
    'large': dict(s=1.22, ppm=48.0),
    'great': dict(s=1.55, ppm=44.0),
}


def size_camera(size):
    return Camera(ppm=SIZES[size]['ppm'])


HERMIT_DEFAULTS = dict(CREATURE_DEFAULTS)
HERMIT_DEFAULTS.update(lift_a=0.0, lift_b=0.0, sway=0.0, rock=0.0, yaw=0.0, slide=0.0, recoil=0.0,
                       eye_l=0.0, eye_r=0.0, dip_l=0.0, dip_r=0.0,
                       raise_=0.0, cock=0.0, snap=0.0, drum=0.0, limp=0.0, spread=0.0, open=0.15,
                       duck=0.0, tip=0.0, fold=0.0, flip=0.0, rear=0.0, curl=0.0, drain=0.0, crack=0.0,
                       spin=0.0, door=0.0, fire=0.0, ring=0.0, shake=0.0)


def hermit_pose(**kw):
    """Fresh neutral pose with every rig channel. Pass rest values, e.g. hermit_pose(raise_=1.0, rear=0.2)."""
    P = dict(HERMIT_DEFAULTS)
    P.update(kw)
    return P


# ------------------------------------------------------------------ plumbing

def new_parts():
    parts = []

    def add(prim, mat, k=0.0):
        parts.append(Part(prim, mat, k))
    return parts, add


def lerp(a, b, t):
    return a + (b - a) * t


def R_from(z_dir, y_hint=(0, 1, 0)):
    """Rotation whose local z is z_dir and local y is as close to y_hint as possible."""
    z = norm(z_dir)
    y = np.asarray(y_hint, dtype=np.float64)
    y = y - z * (y @ z)
    if np.linalg.norm(y) < 1e-5:
        y = v3(0, 0, 1) - z * z[2] if abs(z[2]) < 0.9 else v3(1, 0, 0) - z * z[0]
    y = norm(y)
    return np.stack([np.cross(y, z), y, z], axis=1)


def axis_rot(axis, a):
    """Rodrigues rotation matrix about axis by angle a."""
    k = norm(axis)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * (K @ K)


class Frame:
    """A placed local frame: world = o + R @ (s * local). Shell builders get one (s = 1, metres); the crab
    is built in a child frame with s = crab scale. Helpers add primitives given in LOCAL coordinates."""

    def __init__(self, o=(0, 0, 0), R=None, s=1.0):
        self.o, self.R, self.s = v3(*o), (np.eye(3) if R is None else np.asarray(R, dtype=np.float64)), float(s)

    def p(self, q):
        return self.o + self.s * (self.R @ np.asarray(q, dtype=np.float64))

    def v(self, d):
        return self.R @ np.asarray(d, dtype=np.float64)

    def inv(self, pw):
        """World points (N,3) -> local (for material functions)."""
        return ((pw - self.o) @ self.R) / self.s

    def child(self, q=(0, 0, 0), R=None, s=1.0):
        return Frame(self.p(q), self.R if R is None else self.R @ R, self.s * s)

    def put(self, add, prim, mat, k=0.0):
        """Any sdf primitive built in local coordinates (Func, Subtract, ...) placed into the world."""
        add(Xform(prim, R=self.R, t=self.o, s=self.s), mat, k * self.s)

    def sph(self, add, c, r, mat, k=0.0):
        add(Sphere(self.p(c), r * self.s), mat, k * self.s)

    def ell(self, add, c, radii, mat, k=0.0, R=None):
        RR = self.R if R is None else self.R @ R
        add(Ellipsoid(self.p(c), tuple(np.asarray(radii, dtype=np.float64) * self.s), RR), mat, k * self.s)

    def cap(self, add, a, b, ra, rb=None, mat='claw', k=0.0):
        rb = ra if rb is None else rb
        add(Capsule(self.p(a), self.p(b), ra * self.s, rb * self.s), mat, k * self.s)

    def cyl(self, add, a, b, r, mat, k=0.0, e=0.0):
        add(Cylinder(self.p(a), self.p(b), r * self.s, e * self.s), mat, k * self.s)

    def box(self, add, c, hs, r, mat, k=0.0, R=None):
        RR = self.R if R is None else self.R @ R
        add(RoundBox(self.p(c), tuple(np.asarray(hs, dtype=np.float64) * self.s), r * self.s, RR), mat, k * self.s)

    def tor(self, add, c, axis, R0, r, mat, k=0.0):
        add(Torus(self.p(c), self.v(axis), R0 * self.s, r * self.s), mat, k * self.s)


def _arr(c, n):
    return np.array(c, dtype=np.float64)[None, :].repeat(n, 0)


def local_albedo(F, fn):
    """Material albedo from a function of SHELL-LOCAL points: fn(q_local (N,3), n_world) -> (N,3)."""
    return lambda p, n: fn(F.inv(p), n)


# ------------------------------------------------------------------ materials

def chitin(base, dark=None, speck=None, freq=9.0, amt=0.10):
    dark = VIOLET_DK if dark is None else dark

    def fn(p, n):
        a = _arr(base, len(p))
        m = fbm(p, freq, 2)[:, None]
        a = a * (1 - amt) + np.array(dark)[None, :] * amt + (m - 0.5) * 0.10
        if speck is not None:
            s = (vnoise(p + 3.1, freq * 2.6) > 0.80)[:, None]
            a = np.where(s, a * 0.4 + np.array(speck)[None, :] * 0.6, a)
        return np.clip(a, 0, 1)
    return fn


def crab_mats(P):
    return {
        'carapace': Material(chitin(VIOLET, speck=ORANGE), spec=0.3, gloss=24, brush=0.05),
        'claw': Material(chitin(VIOLET, amt=0.06), spec=0.55, gloss=34, brush=0.04),
        'leg': Material(chitin(_hex('#6f4583'), amt=0.08), spec=0.3, gloss=24, brush=0.05),
        'tip': Material(ORANGE, spec=0.45, gloss=30, brush=0.03),
        'joint': Material(ORANGE_DK, spec=0.35, gloss=24, brush=0.03),
        'eye': Material(TAR, spec=1.0, gloss=90, rim=0.6),
        'tail': Material(chitin(TAIL, dark=TAIL_DK, amt=0.12, freq=6.0), spec=0.35, gloss=30, sss=0.6, brush=0.04),
        'tailband': Material(TAIL_DK, spec=0.3, gloss=24, sss=0.4),
        'dark': Material(_hex('#140f12'), spec=0.05, gloss=8, rim=0.0, brush=0.0),
        'barn': Material(BONE, spec=0.1, gloss=10, brush=0.06),
        'rag': Material(RAG, spec=0.08, gloss=8, brush=0.06),
        'flash': Material(_hex('#fff2c0'), emissive=_hex('#fff2c0'), rim=0.0),
        'flame': Material(_hex('#ffb347'), emissive=_hex('#ffb347'), rim=0.0),
        'debris': Material(_hex('#4a3a30'), spec=0.1, gloss=10),
    }


CRAB_MATS = ('carapace', 'claw', 'leg', 'tip', 'joint', 'eye', 'tail', 'tailband')


def drained(mats, amt, names=CRAB_MATS, to=GREY_VIOLET):
    """Bare death: crab colours drain toward grey-violet."""
    if amt <= 0:
        return mats
    out = dict(mats)
    for nme in names:
        if nme not in mats:
            continue
        m = mats[nme]
        base = m.albedo

        def alb(p, n, base=base):
            a = base(p, n) if callable(base) else _arr(base, len(p))
            g = (a @ np.array([0.3, 0.59, 0.11]))[:, None]
            grey = np.array(to)[None, :] * (0.55 + 0.9 * g)
            return a * (1 - amt * 0.8) + grey * amt * 0.8
        out[nme] = dataclasses.replace(m, albedo=alb, spec=m.spec * (1 - 0.6 * amt), sss=m.sss * (1 - amt))
    return out


def cracked(mats, amt, names=None, freq=5.0, seed=0.0, color=TAR):
    """Destroyed shells: dark crack lines spread over the named materials (all if None)."""
    if amt <= 0:
        return mats
    out = dict(mats)
    for nme, m in mats.items():
        if names is not None and nme not in names:
            continue
        base = m.albedo

        def alb(p, n, base=base):
            a = base(p, n) if callable(base) else _arr(base, len(p))
            q = p + seed
            c1 = np.abs(vnoise(q, freq) - 0.5) < 0.035 * amt
            c2 = np.abs(vnoise(q + 7.7, freq * 1.9) - 0.5) < 0.02 * amt
            c = (c1 | c2)[:, None]
            return np.where(c, np.array(color)[None, :], a * (1 - 0.15 * amt))
        out[nme] = dataclasses.replace(m, albedo=alb)
    return out


# ------------------------------------------------------------------ small sculpt helpers

def tube(add, pts, radii, mat, k=0.02):
    """Chain of round cones through pts with per-point radii."""
    for i in range(len(pts) - 1):
        add(Capsule(pts[i], pts[i + 1], radii[i], radii[i + 1]), mat, k if i else 0.0)


def barnacles(add, center, normal, size=0.05, n=4, spread=None, seed=1, mat='barn', hole='dark'):
    """One cluster of 3-5 fat barnacle cones (never a speckle). World coords."""
    rng = np.random.default_rng(seed)
    nrm = norm(normal)
    R = R_from(nrm, (0, 1, 0.3))
    spread = size * 1.5 if spread is None else spread
    for i in range(n):
        a = rng.uniform(0, 2 * np.pi)
        rr = spread * (0.0 if i == 0 else rng.uniform(0.5, 1.0))
        q = center + R @ v3(np.cos(a) * rr, np.sin(a) * rr, 0)
        sz = size * (1.15 if i == 0 else rng.uniform(0.6, 0.95))
        top = q + nrm * sz * 1.1
        add(Capsule(q - nrm * sz * 0.3, top, sz, sz * 0.55), mat, 0.006)
        add(Sphere(top + nrm * sz * 0.25, sz * 0.38), hole, 0.0)


def rag(add, knot, axis, r, P, length=0.34, width=0.10, mat='rag'):
    """The violet 'Vacant' rag: a band tied round something (axis, radius r) with two tails that flutter."""
    axis = norm(axis)
    add(Torus(knot, axis, r + 0.02, 0.032), mat, 0.0)
    side = norm(np.cross(axis, v3(0, 1, 0))) if abs(axis[1]) < 0.9 else norm(v3(-0.55, 0, 0.83))   # knot faces the camera
    top = knot + v3(0, r + 0.02, 0) if abs(axis[1]) < 0.9 else knot + side * (r + 0.02)
    add(Sphere(top, 0.05), mat, 0.01)
    fl = 0.25 * np.sin(2 * np.pi * P.get('tell', 0.0))
    for j, sg in enumerate((-1, 1)):
        d = norm(v3(0, -1, 0) + side * sg * 0.55 + v3(0.25, 0, 0.35) * (fl + 0.3))
        seg = top + d * length * 0.5
        add(Ellipsoid(seg + side * sg * 0.01, (width * 0.5, 0.014, length * 0.55), R_from(d, np.cross(d, side))),
            mat, 0.01)


# ------------------------------------------------------------------ crab anatomy (crab-local units, s = 1 medium)

# claw key poses: (wrist, direction) with x OUTWARD (multiplied by the claw's side)
CLAW_KEYS = {
    'fwd': ((0.14, -0.06, 0.40), (0.12, 0.10, 1.0)),
    'up': ((0.24, 0.26, 0.44), (0.12, 0.62, 0.78)),
    'cock': ((0.26, 0.38, 0.04), (0.20, 0.80, -0.45)),
    'snap': ((0.10, 0.04, 0.50), (-0.08, -0.05, 1.0)),
    'drum': ((0.16, -0.02, 0.30), (0.08, -0.70, 0.60)),
    'tuck': ((0.09, -0.10, 0.22), (-0.15, -0.25, 1.0)),
    'limp': ((0.16, -0.22, 0.32), (0.10, -0.45, 1.0)),
    'spread': ((0.36, 0.06, 0.26), (0.65, 0.25, 0.75)),
}
SHOULDER = (0.13, -0.03, 0.15)


def _claw_target(P, big=True, guard=None):
    if big:
        w, d = [np.array(x, dtype=np.float64) for x in (guard or CLAW_KEYS['fwd'])]
        seq = (('up', P['raise_']), ('cock', P['cock']), ('snap', P['snap']), ('drum', P['drum']),
               ('tuck', max(P['duck'], P['fold'])), ('limp', P['limp']))
    else:
        w, d = [np.array(x, dtype=np.float64) for x in CLAW_KEYS['tuck']]
        seq = (('spread', P['spread']), ('fwd', 0.35 * P['snap']), ('up', 0.25 * P['cock']),
               ('tuck', max(P['duck'], P['fold'])))
    for key, t in seq:
        if t <= 0:
            continue
        kw, kd = CLAW_KEYS[key]
        w = lerp(w, np.array(kw), min(t, 1.2))
        d = lerp(norm(d), norm(kd), min(t, 1.0))
    return w, norm(d)


def chela(add, w, d, up, cs, open_, mat='claw', tip='tip', bumps=True):
    """A hermit-crab claw: thick wedge palm, lower fixed finger, hinged upper dactyl, orange tips.
    w wrist (world), d pointing direction, up = which way the dactyl opens, cs = size in metres-ish."""
    Rc = R_from(d, up)
    X, Y, Z = Rc[:, 0], Rc[:, 1], Rc[:, 2]
    palm = w + Z * 0.13 * cs
    add(Ellipsoid(palm, (0.090 * cs, 0.115 * cs, 0.155 * cs), Rc), mat, 0.03 * cs)
    add(Ellipsoid(palm + Z * 0.06 * cs - Y * 0.02 * cs, (0.075 * cs, 0.095 * cs, 0.11 * cs), Rc), mat, 0.02 * cs)
    if bumps:
        for j, (a, b) in enumerate(((0.06, 0.03), (0.02, -0.05), (0.07, -0.08))):
            add(Sphere(palm + Y * 0.10 * cs + X * a * cs * 0.6 + Z * b * cs, 0.024 * cs), 'tip' if j == 0 else mat,
                0.01 * cs)
    base = palm + Z * 0.12 * cs - Y * 0.04 * cs
    fd = norm(Z + Y * 0.10)
    Rf = R_from(fd, Y)
    add(Ellipsoid(base + fd * 0.08 * cs, (0.062 * cs, 0.048 * cs, 0.115 * cs), Rf), mat, 0.02 * cs)
    add(Ellipsoid(base + fd * 0.20 * cs + Y * 0.008 * cs, (0.042 * cs, 0.034 * cs, 0.07 * cs), Rf), tip, 0.012 * cs)
    a = 0.05 + 0.8 * open_
    h = palm + Z * 0.10 * cs + Y * 0.055 * cs
    dd = norm(Z * np.cos(a) + Y * np.sin(a))
    Rd = R_from(dd, Y)
    add(Ellipsoid(h + dd * 0.09 * cs, (0.058 * cs, 0.044 * cs, 0.115 * cs), Rd), mat, 0.015 * cs)
    add(Ellipsoid(h + dd * 0.205 * cs - Y * 0.006 * cs, (0.04 * cs, 0.032 * cs, 0.066 * cs), Rd), tip, 0.012 * cs)
    return palm, Rc


def cheliped(add, P, C, side, size, big=True, barn=0, seed=3, guard=None):
    """Arm + claw in crab frame C. side -1 = crab's right (the big claw). guard = rest (wrist, dir) key."""
    w, d = _claw_target(P, big, guard)
    w = w * v3(side, 1, 1)
    d = d * v3(side, 1, 1)
    sh = C.p(v3(SHOULDER[0] * side, SHOULDER[1], SHOULDER[2]))
    ww = C.p(w)
    s = C.s
    l1, l2 = 0.25 * s, 0.24 * s
    el = rig.two_bone(sh, ww, l1, l2, C.v((side * 1.0, -0.35, -0.2)))
    r0 = (0.062 if big else 0.042) * s * max(size, 0.6)
    add(Capsule(sh, el, r0, r0 * 0.9), 'claw', 0.0)
    add(Sphere(el, r0 * 0.95), 'joint', 0.01 * s)
    add(Capsule(el, ww, r0 * 0.9, r0 * 1.05), 'claw', 0.01 * s)
    dw = C.v(d)
    up = C.v((side * -0.35, 1.0, 0.0)) if big else C.v((side * -0.6, 1.0, 0.0))
    palm, Rc = chela(add, ww, dw, up, size * s, P['open'] if big else 0.3 + 0.3 * P['spread'], bumps=big)
    if barn:
        for i in range(barn):
            nrm = norm(Rc[:, 1] * 0.8 + Rc[:, 0] * side * (0.6 - 0.6 * i) + Rc[:, 2] * (0.2 * i - 0.2))
            barnacles(add, palm + nrm * 0.09 * size * s + Rc[:, 2] * (0.05 - 0.07 * i) * size * s, nrm,
                      size=0.028 * size * s, n=3 + (i % 2), seed=seed + i)
    return ww, dw


def eyestalk(add, base, d, L, s, bead=0.046, mat='claw', r=1.0):
    tip = base + d * L
    mid = base + d * L * 0.55
    add(Capsule(base, mid, 0.030 * s * r, 0.025 * s * r), mat, 0.0)
    add(Capsule(mid, tip, 0.025 * s * r, 0.024 * s * r), 'tip', 0.004 * s)
    add(Ellipsoid(tip + d * bead * 0.6 * s, (bead * s, bead * 1.15 * s, bead * s), R_from(v3(0, 0, 1) + d * 0.0, d)),
        'eye', 0.0)
    return tip


def _eye_dir(P, C, d_local, side, extra_dip=0.0):
    yaw = P['eye_r'] if side < 0 else P['eye_l']
    dip = max(P['dip_r'] if side < 0 else P['dip_l'], P['duck'], extra_dip)
    d = axis_rot(v3(0, 1, 0), yaw) @ norm(d_local)
    d = norm(lerp(d, v3(side * 0.1, -0.35, 1.0), min(dip, 1.0) * 0.75))
    return d, dip


def walking_leg(add, root, foot, s, outward, leg_len=1.0, r=1.0):
    """Thick banded walking leg from root (world) to foot (world): violet segments, orange joints."""
    l1, l2, l3 = 0.33 * s * leg_len, 0.34 * s * leg_len, 0.15 * s * leg_len
    out = norm(v3(outward[0], 0, outward[2])) if np.linalg.norm(v3(outward[0], 0, outward[2])) > 1e-6 else v3(1, 0, 0)
    ankle = foot + v3(0, l3 * 0.9, 0) + out * 0.035 * s
    knee = rig.two_bone(root, ankle, l1, l2, v3(0, 1.0, 0) + out * 0.7)
    rr = r * s
    add(Capsule(root, knee, 0.066 * rr, 0.056 * rr), 'leg', 0.0)
    add(Sphere(knee, 0.058 * rr), 'joint', 0.008 * s)
    mid = lerp(knee, ankle, 0.5)
    add(Capsule(knee, mid, 0.052 * rr, 0.048 * rr), 'leg', 0.006 * s)
    add(Capsule(mid, ankle, 0.048 * rr, 0.042 * rr), 'leg', 0.006 * s)
    add(Sphere(ankle, 0.045 * rr), 'joint', 0.006 * s)
    add(Capsule(ankle, foot + v3(0, 0.012 * s, 0), 0.040 * rr, 0.012 * rr), 'tip', 0.004 * s)


def carapace(add, C, s_big=1.0, antennae=True):
    """Shield-shaped violet front body in crab frame C (centre at origin)."""
    C.ell(add, (0, 0, 0), (0.21, 0.135, 0.23), 'carapace', 0.0)
    C.ell(add, (0, 0.035, 0.11), (0.165, 0.11, 0.13), 'carapace', 0.03)
    C.ell(add, (0, -0.07, 0.17), (0.09, 0.05, 0.05), 'joint', 0.01)          # mouthparts
    if antennae:
        for sx in (-1, 1):
            a = (sx * 0.035, 0.03, 0.20)
            b = (sx * 0.15, 0.20, 0.42)
            c = (sx * 0.30, 0.18, 0.62)
            C.cap(add, a, b, 0.016, 0.011, 'tip')
            C.cap(add, b, c, 0.011, 0.006, 'tip')


def spiral_tail(add, C, curl=0.0, size=1.0, center=(0, 0.30, -0.40), r0=0.27, r1=0.07, thick=(0.15, 0.035),
                turns=1.05, bounce=0.0, helix=-0.10, bands=3):
    """The bare crab's soft abdomen: a fat pink-grey spiral comma behind and above the body (crab-local)."""
    cz = v3(center[0], center[1] * size + bounce, center[2] * size)
    k = 1 - 0.20 * curl
    n = 22
    phi0 = np.radians(-62)
    span = 2 * np.pi * (turns + 0.10 * curl)
    pts, rad = [C.p((0, -0.01, -0.12))], [thick[0] * size * 0.95 * C.s]
    for i in range(n):
        t = i / (n - 1)
        phi = phi0 + span * t
        r = (r0 + (r1 - r0) * t ** 0.85) * size * k
        q = v3(helix * t * size, cz[1] + r * np.sin(phi), cz[2] + r * np.cos(phi))
        pts.append(C.p(q))
        rad.append((thick[0] + (thick[1] - thick[0]) * t ** 0.9) * size * C.s)
    tube(add, pts, rad, 'tail', 0.03 * C.s)
    # a few soft segment creases (painted rings, not ridges)
    for j in range(bands):
        i = 4 + j * 4
        if i + 1 < len(pts):
            ax = norm(pts[i + 1] - pts[i - 1])
            add(Torus(pts[i], ax, rad[i] * 0.93, 0.012 * C.s), 'tailband', 0.004 * C.s)
    # tail fan at the inner tip
    tipp = pts[-1]
    add(Sphere(tipp, rad[-1] * 1.2), 'tailband', 0.01 * C.s)
    return pts


def _gait_feet(P, feet, fwd, s, step=0.16):
    """feet: 4 world points (FR, FL, BR, BL); pairs A = FR+BL, B = FL+BR alternate."""
    out = []
    for i, f in enumerate(feet):
        a = i in (0, 3)
        dz = P['stride'] * step * s * (1 if a else -1)
        lift = (P['lift_a'] if a else P['lift_b']) * 0.13 * s
        out.append(f + fwd * dz + v3(0, lift, 0))
    return out


# ------------------------------------------------------------------ shelled crab

@dataclass
class Shell:
    """How a crab wears an object. All lengths in metres.

    build      fn(add, P, F) -> materials dict. Adds the object in shell-local coords (origin = object centre,
               +z = mouth/forward, +y = up). The rig places F; use F.put / F.cyl / F.ell / ... to add parts.
    ride       height of the shell origin above the ground when standing
    crab_at    shell-local point of the crab's carapace centre (just inside the mouth)
    feet       4 world (x, z) foot spots: front-right, front-left, back-right, back-left (right = -x)
    tilt       rest pitch (+ = back end raised, mouth toward the ground); ART asks for ~20 degrees
    crab_pitch extra pitch of the crab inside the shell (+ = nose down)
    leg_roots  optional 4 shell-local leg roots (FR, FL, BR, BL); default = on the carapace
    eyes       optional [(shell-local base, shell-local dir, length)]; default = two from the carapace
    eye_len    default eyestalk length (crab units) so the beads clear the rim
    big, small chela scales; barn = barnacle clusters on the big claw
    side_r     how high the origin sits when the object lies on its side (death); tip_dir +1/-1 roll side
    lie        rest pitch when lying (death); z0 world z of the origin; leg_len leg length factor
    """
    build: Callable
    ride: float
    crab_at: tuple
    feet: tuple = ((-0.40, 0.36), (0.40, 0.36), (-0.46, -0.18), (0.46, -0.18))
    tilt: float = 0.30
    crab_pitch: float = 0.0
    leg_roots: Optional[tuple] = None
    eyes: Optional[tuple] = None
    eye_len: float = 0.24
    big: float = 1.1
    small: float = 0.5
    barn: int = 0
    side_r: float = 0.35
    tip_dir: float = 1.0
    lie: float = 0.0
    z0: float = 0.0
    leg_len: float = 1.0
    leg_r: float = 1.0
    antennae: bool = True
    tip_angle: float = 1.35
    x0: float = 0.0
    eye_bead: float = 0.056
    guard: Optional[tuple] = ((0.14, 0.10, 0.42), (-0.55, 0.45, 0.70))   # claw rest: across the mouth, up
    yaw: float = 0.0           # turn the whole unit (+ = toward screen-right, side-on); feet turn with it


def shell_frame(P, sh):
    """World frame of the shell for this pose: ride height, tilt, rock, sway, duck, recoil and the death tip."""
    tip = P['tip']
    duck = P['duck']
    ride = sh.ride * (1 - 0.14 * duck - 0.25 * P['fold'] * (1 - tip)) + P['bob']
    y = lerp(ride, sh.side_r, tip)
    pitch = lerp(sh.tilt + P['lean'] + P['rock'], sh.lie, tip)
    roll = -sh.tip_dir * tip * sh.tip_angle + P['sway']
    R = rot_y(sh.yaw + P['yaw']) @ rot_z(roll) @ rot_x(pitch)
    o = v3(sh.x0 + P['slide'] + P['shake'] * 0.02, y, sh.z0) + rot_y(sh.yaw + P['yaw']) @ v3(0, 0, -P['recoil'])
    return Frame(o, R, 1.0)


def shelled(P, size, sh, mats=None, lights=(), world=None):
    """Scene: the crab wearing shell `sh`. mats override/extend materials; world(add) adds world extras."""
    s = SIZES[size]['s'] if isinstance(size, str) else float(size)
    parts, add = new_parts()
    F = shell_frame(P, sh)
    m = crab_mats(P)
    sm = sh.build(add, P, F)
    if sm:
        m.update(sm)
    C = F.child(v3(*sh.crab_at) + v3(0, -0.02 * P['duck'], -0.10 * P['duck'] * s), rot_x(sh.crab_pitch), s)
    carapace(add, C, antennae=sh.antennae and P['duck'] < 0.5)
    # claws (right = -x is the big one)
    cheliped(add, P, C, -1, sh.big, True, barn=sh.barn, guard=sh.guard)
    cheliped(add, P, C, 1, sh.small, False)
    # eyes
    if sh.eyes is None:
        eyes = [(C.p((-0.065, 0.08, 0.16)), C.v((-0.14, 1.0, 0.28)), sh.eye_len * s),
                (C.p((0.065, 0.08, 0.16)), C.v((0.14, 1.0, 0.28)), sh.eye_len * s)]
    else:
        eyes = [(F.p(b), F.v(d), L) for b, d, L in sh.eyes]
    droop = P['end'] * 0.8
    for i, (b, d, L) in enumerate(eyes):
        side = -1 if i % 2 == 0 else 1
        # swivel about the crab's up axis
        yaw = (P['eye_r'] if side < 0 else P['eye_l']) * (1.0 if i < 2 else -0.7)
        dip = max(P['dip_r'] if side < 0 else P['dip_l'], P['duck'], droop) if i < 2 else max(P['dip_r'], P['duck'], droop)
        dd = axis_rot(C.v((0, 1, 0)), yaw) @ norm(d)
        dd = norm(lerp(dd, C.v((side * 0.15, -0.30, 1.0)), min(dip, 1.0) * 0.7))
        eyestalk(add, b, dd, L * (1 - 0.6 * min(dip, 1.0)), s, bead=sh.eye_bead, r=1.3)
    # legs
    Ry = rot_y(sh.yaw + P['yaw'])
    fwd = Ry @ v3(0, 0, 1)
    base = [v3(sh.x0 + P['slide'], 0, sh.z0) + Ry @ v3(fx, 0, fz - P['recoil']) for fx, fz in sh.feet]
    feet = _gait_feet(P, base, fwd, s)
    if sh.leg_roots is None:
        roots = [C.p((-0.17, -0.07, 0.07)), C.p((0.17, -0.07, 0.07)), C.p((-0.18, -0.08, -0.06)),
                 C.p((0.18, -0.08, -0.06))]
    else:
        roots = [F.p(r) for r in sh.leg_roots]
    fold = max(P['fold'], P['tip'])
    for i, (rt, ft) in enumerate(zip(roots, feet)):
        side = -1 if i % 2 == 0 else 1
        tuck = C.p((side * 0.30, -0.16, 0.12 if i < 2 else -0.04))
        ft = lerp(ft, tuck, fold)
        walking_leg(add, rt, ft, s, v3(side, 0, 0.35 if i < 2 else -0.25), sh.leg_len * (1 - 0.25 * fold), sh.leg_r)
    if world:
        world(add)
    if abs(P['squash'] - 1) > 1e-3:
        parts[:] = squash_parts(parts, sy=P['squash'], sxz=1 + (1 - P['squash']) * 0.5)
    if mats:
        m.update(mats)
    m = drained(m, P['drain'])
    return Scene(parts=parts, materials=m, lights=list(lights), ground_clip=True)


# ------------------------------------------------------------------ bare crab

@dataclass
class Bare:
    """An evicted crab. Lengths in crab units (multiplied by the size's s).
    h        carapace centre height        feet   4 (x, z) foot spots FR, FL, BR, BL
    yaw      turn toward side-on (+ shows the left flank, - the right)
    tail     spiral_tail kwargs (size, center, r0, r1, thick, turns, helix)
    big/small chela scales; barn = barnacle clusters on the big claw; eye_len; leg_len"""
    h: float = 0.40
    feet: tuple = ((-0.48, 0.40), (0.56, 0.36), (-0.52, -0.30), (0.60, -0.26))
    yaw: float = 0.65
    tail: dict = field(default_factory=dict)
    big: float = 1.15
    small: float = 0.55
    barn: int = 0
    eye_len: float = 0.26
    leg_len: float = 1.0
    leg_r: float = 1.25
    z0: float = 0.0
    x0: float = 0.0


def bare_frame(P, b, s):
    fl = P['flip']
    h = lerp(b.h + P['bob'] / s, 0.15, fl)
    R = rot_y(b.yaw + P['yaw']) @ rot_z(-np.pi * 0.96 * fl + P['sway']) @ rot_x(P['lean'] - P['rear'] * (1 - fl))
    o = v3(b.x0 + P['slide'], h * s, b.z0 - P['recoil'])
    return Frame(o, R, s)


def bare(P, size, b, mats=None, lights=(), world=None):
    """Scene: the evicted crab (spiral tail, raised claw)."""
    s = SIZES[size]['s'] if isinstance(size, str) else float(size)
    parts, add = new_parts()
    C = bare_frame(P, b, s)
    carapace(add, C)
    tk = dict(b.tail)
    tk.setdefault('bounce', 0.0)
    tk['bounce'] = tk['bounce'] + P['ring'] * 0.0
    spiral_tail(add, C, curl=P['curl'], **tk)
    cheliped(add, P, C, -1, b.big, True, barn=b.barn)
    cheliped(add, P, C, 1, b.small, False)
    droop = P['end'] * 0.7
    for side in (-1, 1):
        d, dip = _eye_dir(P, C, (side * 0.22, 1.0, 0.05), side, droop)
        eyestalk(add, C.p((side * 0.065, 0.09, 0.16)), C.v(d), b.eye_len * s * (1 - 0.5 * dip), s)
    fwd = rot_y(b.yaw + P['yaw']) @ v3(0, 0, 1)
    Ry = rot_y(b.yaw + P['yaw'])
    base = [v3(b.x0 + P['slide'], 0, b.z0 - P['recoil']) + Ry @ v3(fx * s, 0, fz * s) for fx, fz in b.feet]
    feet = _gait_feet(P, base, fwd, s, step=0.20)
    roots = [C.p((-0.17, -0.06, 0.08)), C.p((0.17, -0.06, 0.08)), C.p((-0.18, -0.07, -0.06)),
             C.p((0.18, -0.07, -0.06))]
    fold = P['fold']
    for i, (rt, ft) in enumerate(zip(roots, feet)):
        side = -1 if i % 2 == 0 else 1
        tuck = C.p((side * 0.30, -0.24, 0.10 if i < 2 else -0.06))
        ft = lerp(ft, tuck, fold)
        walking_leg(add, rt, ft, s, C.v((side, 0, 0.35 if i < 2 else -0.3)), b.leg_len * (1 - 0.3 * fold), b.leg_r)
    if world:
        world(add)
    if abs(P['squash'] - 1) > 1e-3:
        parts[:] = squash_parts(parts, sy=P['squash'], sxz=1 + (1 - P['squash']) * 0.5)
    m = crab_mats(P)
    if mats:
        m.update(mats)
    m = drained(m, P['drain'])
    return Scene(parts=parts, materials=m, lights=list(lights), ground_clip=True)


# ------------------------------------------------------------------ empty shells (structures)

def empty(P, sh, place, rag_at=None, mats=None, lights=(), world=None, debris_mat='debris', seed=4):
    """Scene: a vacant shell lying where it was left. place = (origin, R) world placement of the shell frame.
    rag_at = (shell-local knot point, shell-local axis, radius) for the violet Vacant rag."""
    parts, add = new_parts()
    o, R = place
    sh_k = P['shake']
    F = Frame(v3(*o) + v3(0.025 * sh_k, -0.06 * P['crack'] ** 2, 0), rot_z(0.06 * P['crack']) @ np.asarray(R), 1.0)
    m = crab_mats(P)
    sm = sh.build(add, P, F)
    if sm:
        m.update(sm)
    if rag_at is not None:
        q, ax, r = rag_at
        rag(add, F.p(q), F.v(ax), r, P)
    c = P['crack']
    if c > 0:
        rng = np.random.default_rng(seed)
        for i in range(6):
            a = rng.uniform(0, 2 * np.pi)
            dist = (0.45 + 0.35 * rng.uniform()) * (0.5 + 0.5 * c)
            q = v3(np.cos(a) * dist, 0.03, np.sin(a) * dist * 0.8)
            hs = (0.05 * rng.uniform(0.7, 1.4), 0.025, 0.04 * rng.uniform(0.7, 1.3))
            add(RoundBox(q, hs, 0.01, rot_y(rng.uniform(0, 6.28)) @ rot_x(rng.uniform(-0.4, 0.4))), debris_mat, 0.0)
    if world:
        world(add)
    if mats:
        m.update(mats)
    m = cracked(m, c, names=[k for k in m if k not in CRAB_MATS and k not in ('rag', 'dark', 'flash', 'flame')])
    return Scene(parts=parts, materials=m, lights=list(lights), ground_clip=True)


# ------------------------------------------------------------------ shell library (shell-local builders)

def _bulge_cyl(L, r_mid, r_end):
    """Barrel body along z: |z| <= L/2, radius bulging from r_end to r_mid."""
    hl = L / 2

    def f(p):
        z = p[:, 2]
        r = r_end + (r_mid - r_end) * (1 - np.clip(z / hl, -1, 1) ** 2)
        d = np.sqrt(p[:, 0] ** 2 + p[:, 1] ** 2) - r
        return np.maximum(d * 0.96, np.abs(z) - hl)
    return Func(f, (0, 0, 0), np.hypot(hl, r_mid) + 0.02)


def barrel_shell(length=0.86, r_mid=0.34, r_end=0.28, bung=True, mouth=True, wood=None, hoops=(-0.36, 0.0, 0.36)):
    """Tarred oak hogshead lying along z, front head knocked out (the mouth, +z), three iron hoops and a
    knocked-out bung-hole on top (y+). Returns a Shell build fn."""
    wood = OAK if wood is None else wood

    def build(add, P, F):
        hl = length / 2
        body = _bulge_cyl(length, r_mid, r_end)
        if mouth:
            inner = _bulge_cyl(length - 0.07, r_mid - 0.045, r_end - 0.045)
            cut = Xform(inner, t=(0, 0, 0.08))
            F.put(add, Subtract(body, cut), 'stave')
            F.cyl(add, (0, 0, -hl + 0.10), (0, 0, -hl + 0.12), r_end + 0.03, 'dark')
        else:
            F.put(add, body, 'stave')
        for z in hoops:
            t = z / hl
            r = r_end + (r_mid - r_end) * (1 - t ** 2)
            F.put(add, Torus(v3(0, 0, z * 0.97), v3(0, 0, 1), r + 0.004, 0.022), 'hoop')
        if bung:
            F.cyl(add, (0, r_mid - 0.06, -0.02), (0, r_mid + 0.012, -0.02), 0.055, 'hoopdark', 0, 0.01)
            F.cyl(add, (0, r_mid - 0.10, -0.02), (0, r_mid + 0.03, -0.02), 0.038, 'dark')

        def alb(q, n):
            a = _arr(wood, len(q))
            ang = np.arctan2(q[:, 1], q[:, 0])
            st = np.abs(((ang / (2 * np.pi) * 14) % 1.0) - 0.5) > 0.46
            a = np.where(st[:, None], a * 0.62, a)
            g = fbm(q * v3(1, 1, 0.25), 7.0, 2)[:, None]
            a = a * (0.85 + 0.3 * g)
            tar = (vnoise(q * v3(1, 1, 0.5), 5.0) > 0.80)[:, None]
            a = np.where(tar, np.array(TAR)[None, :] * 1.3, a)
            inside = (np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2) < (r_end - 0.03 + (r_mid - r_end) * (1 - np.clip(q[:, 2] / hl, -1, 1) ** 2)))
            return np.where(inside[:, None], np.array(TAR)[None, :] * 0.8, a)

        def hoop_alb(q, n):
            a = _arr(RUST, len(q))
            rr = (vnoise(q, 14.0) > 0.62)[:, None]
            return np.where(rr, np.array(ORANGE)[None, :] * 0.85, a)
        return {'stave': Material(local_albedo(F, alb), spec=0.15, gloss=14, brush=0.08),
                'hoop': Material(local_albedo(F, hoop_alb), spec=0.45, gloss=26, metal=0.4),
                'hoopdark': Material(RUST, spec=0.3, gloss=20)}
    return build


def bell_port(h, r_bot, r_top, az, y):
    """Shell-local centre and outward normal of a diving-bell porthole (same profile as diving_bell_shell)."""
    hb, ht = -h / 2, h / 2
    t = np.clip((y - hb) / (ht - hb), 0, 1)
    rr = r_bot + (r_top - r_bot) * t ** 1.6
    return v3(np.sin(az) * rr, y, np.cos(az) * rr), norm(v3(np.sin(az), 0.18, np.cos(az)))


def diving_bell_shell(h=0.95, r_bot=0.48, r_top=0.30, ports=((0.0, 1.0), (-1.05, 1.0), (1.05, 1.0)), port_r=0.11,
                      port_y=0.08, hose=False, eyes_in=(0, 1)):
    """Brass diving bell, mouth down (-y). Shell-local origin at the middle of the bell's height.
    ports = (azimuth from +z in rad, scale); eyes_in = indices of ports that show the crab's eyes."""
    hb, ht = -h / 2, h / 2

    def bell_sdf(p):
        y = p[:, 1]
        t = np.clip((y - hb) / (ht - hb), 0, 1)
        r = r_bot + (r_top - r_bot) * t ** 1.6
        rr = np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2)
        side = (rr - r) * 0.92
        d = np.maximum(side, np.maximum(hb - y, y - ht))
        # rounded crown
        dome = np.sqrt(p[:, 0] ** 2 + ((y - ht + 0.02) / 0.75) ** 2 + p[:, 2] ** 2) - r_top
        d = np.minimum(d, np.maximum(dome * 0.75, ht - 0.05 - y))
        return d

    def build(add, P, F):
        outer = Func(bell_sdf, (0, 0, 0), h * 0.75 + r_bot)
        inner = Xform(Func(bell_sdf, (0, 0, 0), h * 0.75 + r_bot), t=(0, -0.06, 0), s=0.88)
        F.put(add, Subtract(outer, inner), 'brassb')
        F.cyl(add, (0, hb + 0.06, 0), (0, hb + 0.10, 0), r_bot * 0.93, 'dark')   # dark interior roof plug
        F.put(add, Torus(v3(0, hb + 0.03, 0), v3(0, 1, 0), r_bot + 0.012, 0.05), 'brassd')   # heavy skirt flange
        F.put(add, Torus(v3(0, ht - 0.03, 0), v3(0, 1, 0), r_top + 0.004, 0.035), 'brassd')    # crown band
        F.put(add, Torus(v3(0, ht + 0.33, 0), v3(1, 0, 0), 0.085, 0.034), 'brassd')         # lifting eye
        F.cyl(add, (0, ht + 0.16, 0), (0, ht + 0.26, 0), 0.07, 'brassd', 0.01)
        for j, (az, sc) in enumerate(ports):
            yy = port_y
            c, nrm = bell_port(h, r_bot, r_top, az, yy)
            pr = port_r * sc
            F.put(add, Torus(c + norm(nrm) * 0.015, nrm, pr + 0.01, 0.034), 'brassd')
            F.put(add, Cylinder(c - norm(nrm) * 0.03, c + norm(nrm) * 0.03, pr, 0.01), 'glass' if j in eyes_in else 'portdark')
        if hose:
            pts = [v3(-0.05, ht + 0.06, -0.08), v3(-0.25, ht + 0.02, -0.30), v3(-0.45, hb + 0.3, -0.35),
                   v3(-0.55, hb + 0.05, -0.1)]
            for a, b in zip(pts[:-1], pts[1:]):
                F.put(add, Capsule(a, b, 0.035), 'hose')

        def alb(q, n):
            a = _arr(_hex('#9a783c'), len(q))
            v = fbm(q, 5.0, 2)[:, None]
            v = fbm(q, 8.0, 2)[:, None]
            pat = np.clip((v - 0.60) * 6, 0, 1) * 0.8
            a = a * (1 - pat) + np.array(VERDI)[None, :] * pat
            low = np.clip((hb + 0.22 - q[:, 1]) / 0.22, 0, 1)[:, None] * 0.6
            return a * (1 - low) + np.array(VERDI)[None, :] * low
        return {'brassb': Material(local_albedo(F, alb), spec=0.55, gloss=70, metal=0.6, brush=0.05),
                'brassd': Material(_hex('#8f6e35'), spec=0.8, gloss=36, metal=0.7),
                'glass': Material(_hex('#a9c4c2'), spec=1.0, gloss=90, rim=0.8),
                'portdark': Material(_hex('#22282a'), spec=1.0, gloss=90),
                'hose': Material(_hex('#3a3230'), spec=0.2, gloss=14)}
    return build


def chapel_bell_shell(h=0.95, r_bot=0.50, r_top=0.26, crack=True, clapper_tied=True, rope=True):
    """Verdigris bronze chapel bell, mouth down (-y), flared lip, crown with a loop; one crack."""
    hb, ht = -h / 2, h / 2

    def bell_sdf(p):
        y = p[:, 1]
        t = np.clip((y - hb) / (ht - hb), 0, 1)
        # classic bell profile: flared lip, waist, shoulder
        r = r_top + (r_bot - r_top) * (1 - t) ** 2.2 + 0.05 * np.sin(np.pi * t) * 0.0
        rr = np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2)
        d = np.maximum((rr - r) * 0.85, np.maximum(hb - y, y - ht))
        dome = np.sqrt(p[:, 0] ** 2 + ((y - ht + 0.04) / 0.6) ** 2 + p[:, 2] ** 2) - r_top
        return np.minimum(d, np.maximum(dome * 0.6, ht - 0.06 - y))

    def build(add, P, F):
        outer = Func(bell_sdf, (0, 0, 0), h * 0.75 + r_bot)
        inner = Xform(Func(bell_sdf, (0, 0, 0), h * 0.75 + r_bot), t=(0, -0.07, 0), s=0.86)
        F.put(add, Subtract(outer, inner), 'bronze')
        F.put(add, Torus(v3(0, hb + 0.03, 0), v3(0, 1, 0), r_bot - 0.005, 0.04), 'bronze', 0.02)   # sound bow lip
        F.put(add, Torus(v3(0, hb + 0.30, 0), v3(0, 1, 0), r_top + (r_bot - r_top) * 0.35 + 0.012, 0.018), 'bronzed')
        F.cyl(add, (0, hb + 0.10, 0), (0, hb + 0.14, 0), r_bot * 0.80, 'dark')
        F.put(add, Torus(v3(0, ht + 0.10, 0), v3(1, 0, 0), 0.09, 0.03), 'bronzed')          # crown loop
        if clapper_tied:
            F.cyl(add, (0, hb + 0.12, 0), (0, hb + 0.0, 0.0), 0.02, 'iron')
            F.sph(add, (0, hb - 0.03, 0), 0.07, 'iron')
        if rope:
            F.put(add, Capsule(v3(0, ht + 0.18, 0), v3(0.10, ht + 0.32, -0.06), 0.025), 'rope')

        def alb(q, n):
            a = _arr(_hex('#4f7a6a'), len(q))
            v = fbm(q, 4.0, 2)[:, None]
            a = a * (0.8 + 0.3 * v)
            bronze = (vnoise(q, 6.0) > 0.68)[:, None]
            a = np.where(bronze, np.array(_hex('#8a6a3c'))[None, :], a)
            if crack:
                cx = np.abs(q[:, 0] + 0.05 * np.sin(q[:, 1] * 18) + 0.03) < 0.012
                cr = cx & (q[:, 2] > 0) & (q[:, 1] < hb + h * 0.7)
                a = np.where(cr[:, None], np.array(TAR)[None, :], a)
            return a
        return {'bronze': Material(local_albedo(F, alb), spec=0.7, gloss=30, metal=0.5, brush=0.05),
                'bronzed': Material(_hex('#4d7666'), spec=0.6, gloss=30, metal=0.5),
                'rope': Material(_hex('#a8834e'), spec=0.05, gloss=8, brush=0.1),
                'iron': Material(IRON, spec=0.6, gloss=30, metal=0.6)}
    return build


def boiler_shell(length=1.3, r=0.42, door=0.0, glow=1.0, funnel=True, bosses=4, funnel_h=0.20):
    """Rust-brown riveted ship's boiler (horizontal capsule along z), round firebox door on the front
    (+z end). door 0 shut .. 1 hanging open; glow = firebox amber (cooling embers when low)."""
    hl = length / 2 - r * 0.5

    def build(add, P, F):
        fz = hl + r * 0.55
        F.put(add, Subtract(Capsule(v3(0, 0, -hl), v3(0, 0, fz + r), r),
                            Cylinder(v3(0, 0, fz), v3(0, 0, fz + 3 * r), r * 1.5)), 'boil')     # flat front plate
        F.put(add, Torus(v3(0, 0, fz - 0.03), v3(0, 0, 1), r - 0.01, 0.03), 'boilband')
        for z in (-hl * 0.55, hl * 0.35):
            F.put(add, Torus(v3(0, 0, z), v3(0, 0, 1), r + 0.004, 0.02), 'boilband')
        # a few big rivet bosses, never a row
        for j, (a, z) in enumerate(((0.9, -hl * 0.2), (2.3, hl * 0.6), (-0.6, hl * 0.1), (1.6, -hl * 0.85))[:bosses]):
            c = v3(np.cos(a) * r, np.sin(a) * r, z)
            F.sph(add, c, 0.035, 'boilband')
        # firebox mouth and door
        F.cyl(add, (0, -0.06, fz - 0.10), (0, -0.06, fz + 0.012), 0.20, 'fire_in')
        F.put(add, Torus(v3(0, -0.06, fz + 0.01), v3(0, 0, 1), 0.21, 0.028), 'boilband')
        ang = door * 1.9
        hinge = v3(-0.22, -0.06, fz + 0.03)
        Rd = rot_y(-ang)
        dc = hinge + Rd @ v3(0.22, 0, 0.0)
        F.put(add, Cylinder(dc - Rd @ v3(0, 0, 0.02), dc + Rd @ v3(0, 0, 0.02), 0.20, 0.01), 'door')
        F.put(add, Sphere(dc + Rd @ v3(0.0, 0.10, 0.03), 0.03), 'boilband')
        if funnel:
            F.cyl(add, (0, r - 0.05, -hl * 0.5), (0, r + funnel_h, -hl * 0.5), 0.11, 'boil', 0.03, 0.02)
            F.put(add, Torus(v3(0, r + funnel_h, -hl * 0.5), v3(0, 1, 0), 0.11, 0.03), 'boilband')
            F.cyl(add, (0, r + funnel_h - 0.02, -hl * 0.5), (0, r + funnel_h + 0.01, -hl * 0.5), 0.085, 'dark')
        g = max(glow, 0.0)

        def alb(q, n):
            a = _arr(RUST, len(q))
            v = fbm(q, 4.0, 2)[:, None]
            a = a * (0.8 + 0.4 * v)
            bloom = (vnoise(q, 7.0) > 0.70)[:, None]
            return np.where(bloom, np.array(ORANGE)[None, :] * 0.8, a)
        return {'boil': Material(local_albedo(F, alb), spec=0.35, gloss=20, metal=0.3, brush=0.06),
                'boilband': Material(_hex('#4a2c1c'), spec=0.4, gloss=24, metal=0.4),
                'door': Material(_hex('#3e2a20'), spec=0.4, gloss=24, metal=0.4),
                'fire_in': Material(_hex('#7a2e14'), emissive=tuple(np.array(LAMP) * (0.08 + 0.9 * g)), rim=0.0)}
    return build


def long_gun_shell(length=2.0, r_breech=0.24, r_muzzle=0.15, open_breech=True, bore=0.07):
    """Cast-iron naval long gun along z, breech at -z, muzzle at +z with a muzzle swell ring, two
    reinforce rings and trunnions. open_breech knocks the cascabel end out (the crab's door)."""
    hl = length / 2

    def gun_sdf(p):
        z = p[:, 2]
        t = np.clip((z + hl) / length, 0, 1)
        r = r_breech + (r_muzzle - r_breech) * t
        r = r + 0.035 * np.exp(-((z - (hl - 0.10)) / 0.06) ** 2)     # muzzle swell
        d = np.sqrt(p[:, 0] ** 2 + p[:, 1] ** 2) - r
        return np.maximum(d * 0.95, np.abs(z) - hl)

    def build(add, P, F):
        g = Func(gun_sdf, (0, 0, 0), hl + 0.3)
        borec = Cylinder(v3(0, 0, -hl * 0.2), v3(0, 0, hl + 0.1), bore)
        body = Subtract(g, borec)
        if open_breech:
            body = Subtract(body, Cylinder(v3(0, 0, -hl - 0.1), v3(0, 0, -hl + 0.14), r_breech - 0.06))
        F.put(add, body, 'gun')
        F.cyl(add, (0, 0, hl - 0.2), (0, 0, hl - 0.14), bore + 0.004, 'dark')
        if open_breech:
            F.cyl(add, (0, 0, -hl + 0.12), (0, 0, -hl + 0.15), r_breech - 0.055, 'dark')
        for z in (-hl + 0.32, -hl * 0.15):
            t = (z + hl) / length
            rr = r_breech + (r_muzzle - r_breech) * t
            F.put(add, Torus(v3(0, 0, z), v3(0, 0, 1), rr + 0.006, 0.03), 'gunring')
        F.put(add, Torus(v3(0, 0, hl - 0.02), v3(0, 0, 1), r_muzzle + 0.015, 0.028), 'gunring')   # muzzle ring
        zt = -hl * 0.05
        rt = r_breech + (r_muzzle - r_breech) * ((zt + hl) / length)
        F.cyl(add, (-rt - 0.09, 0, zt), (rt + 0.09, 0, zt), 0.055, 'gunring', 0.0, 0.01)            # trunnions

        def alb(q, n):
            a = _arr(_hex('#2b2729'), len(q))
            v = fbm(q, 4.0, 2)[:, None]
            a = a * (0.85 + 0.35 * v)
            rr = (vnoise(q * v3(1, 1, 0.35), 5.0) > 0.74)[:, None]
            a = np.where(rr, np.array(RUST)[None, :] * 1.1, a)
            rr2 = (vnoise(q + 3.3, 9.0) > 0.90)[:, None]
            return np.where(rr2, np.array(ORANGE)[None, :] * 0.7, a)
        return {'gun': Material(local_albedo(F, alb), spec=0.45, gloss=26, metal=0.5, brush=0.05),
                'gunring': Material(_hex('#3a3234'), spec=0.6, gloss=30, metal=0.6)}
    return build


# ------------------------------------------------------------------ animation rows

ROWS = [
    ('idle', 4, True, {}),
    ('move', 6, True, {}),
    ('attack', 8, False, {'hitFrame': 2}),
    ('hit', 10, False, {}),
    ('death', 6, False, {'holdLast': True}),
    ('cast', 8, False, {}),
]


def _set(P, **kw):
    for k, v in kw.items():
        P[k] = v
    return P


def hermit_rows(base, kind='shell', extra=None):
    """Standard Hermitage rows. kind 'shell': eyestalk tell, slow lurch, claw snap, duck on hit, tip-over
    death with a limp claw, rear-and-drum cast. kind 'bare': twitchy shuffle, fast scuttle with tail bounce,
    flinch + tail clamp, flip-on-back death with colour drain. extra(rows) may edit the poses in place."""
    def frames():
        b = base
        R = {}
        if kind == 'shell':
            R['idle'] = [(_set(b(), rock=[0, .035, 0, -.03][i], sway=[0, .025, 0, -.02][i],
                               eye_l=[.25, .5, .15, -.2][i], eye_r=[-.2, -.05, -.4, -.15][i],
                               dip_l=[0, 0, 1, 0][i], dip_r=[0, 0, 0, .15][i], open=[.15, .25, .15, .1][i],
                               tell=i / 4), {}) for i in range(4)]
            R['move'] = [(_set(b(), stride=[1, 0, -1, 0][i], lift_a=[0, 0, 0, 1][i], lift_b=[0, 1, 0, 0][i],
                               sway=[.07, 0, -.07, 0][i], bob=[-.015, .02, -.015, .02][i],
                               rock=[.03, -.01, .03, -.01][i], eye_l=.2, eye_r=-.2, tell=i / 4), {})
                         for i in range(4)]
            R['attack'] = [(_set(b(), cock=[.7, 1, 0, 0][i], snap=[0, 0, 1, .35][i], open=[.6, .95, .0, .2][i],
                                 lean=[-.06, -.10, .08, .02][i], fx=[0, 0, 1, .2][i], strike=[0, .3, 1, .3][i]), {})
                           for i in range(4)]
            R['hit'] = [(_set(b(), duck=1.0, lean=-.12, sway=.05, shake=1), dict(exposure=1.25, flash=0.22)),
                        (_set(b(), duck=.45, lean=-.04, sway=-.02), {})]
            R['death'] = [(_set(b(), duck=.8, lean=-.12, sway=.06), {}),
                          (_set(b(), duck=.6, fold=.55, tip=.22, bob=-.04, end=.2), {}),
                          (_set(b(), tip=.92, fold=.9, squash=.94, limp=.6, end=.6), {}),
                          (_set(b(), tip=1.0, fold=1.0, limp=1.0, end=1.0, open=.35), {})]
            R['cast'] = [(_set(b(), lean=-.13, raise_=1.0, open=.3, eye_l=.3, eye_r=-.3, cast_glow=.5), {}),
                         (_set(b(), lean=-.04, drum=1.0, open=.1, bob=-.015, cast_glow=1.0), {}),
                         (_set(b(), lean=-.13, raise_=1.0, open=.3, cast_glow=.6), {}),
                         (_set(b(), lean=-.04, drum=1.0, open=.1, bob=-.015, cast_glow=.3), {})]
        else:
            def rel(P, **kw):
                for k, v in kw.items():
                    P[k] = P[k] + v
                return P
            R['idle'] = [(rel(_set(b(), tell=i / 4, curl=[0, .5, 1, .4][i], open=[.2, .35, .2, .1][i],
                                   eye_l=[.2, .45, .1, -.2][i], eye_r=[-.25, -.1, -.4, -.1][i],
                                   lift_a=[0, .7, 0, 0][i], lift_b=[0, 0, 0, .6][i]),
                              slide=[0, .05, .07, .02][i], bob=[0, .015, 0, .01][i]), {}) for i in range(4)]
            R['move'] = [(rel(_set(b(), stride=[1, 0, -1, 0][i], lift_a=[0, 0, 0, 1][i], lift_b=[0, 1, 0, 0][i],
                                   tell=i / 4, eye_l=.15, eye_r=-.15),
                              bob=[0, .035, 0, .035][i], sway=[.05, 0, -.05, 0][i], curl=[0, .5, 0, .5][i],
                              lean=[.04, .04, .04, .04][i]), {}) for i in range(4)]
            R['attack'] = [(rel(_set(b(), cock=[.75, 1, 0, 0][i], snap=[0, 0, 1, .35][i],
                                     open=[.6, .95, .0, .2][i], fx=[0, 0, 1, .2][i]),
                                lean=[-.08, -.12, .14, .04][i], rear=[.1, .15, -.1, 0][i]), {}) for i in range(4)]
            R['hit'] = [(rel(_set(b(), curl=1.0, open=.6, shake=1), lean=-.18, raise_=-.5, bob=-.02),
                         dict(exposure=1.25, flash=0.22)),
                        (rel(_set(b(), curl=.5), lean=-.06, raise_=-.2), {})]
            R['death'] = [(rel(_set(b(), curl=1.0, open=.7), lean=-.2, raise_=-.3), {}),
                          (_set(b(), flip=.35, fold=.45, curl=1.0, raise_=.3, drain=.3, end=.25), {}),
                          (_set(b(), flip=.85, fold=.85, curl=1.0, raise_=0.0, drain=.7, end=.6, squash=.95), {}),
                          (_set(b(), flip=1.0, fold=1.0, curl=1.0, raise_=0.0, drain=1.0, end=1.0, open=.1), {})]
            R['cast'] = [(rel(_set(b(), raise_=1.0, open=.35, cast_glow=.5), rear=.18, bob=.02), {}),
                         (rel(_set(b(), drum=1.0, open=.1, cast_glow=1.0), rear=-.05, bob=-.01), {}),
                         (rel(_set(b(), raise_=1.0, open=.35, cast_glow=.6), rear=.18, bob=.02), {}),
                         (rel(_set(b(), drum=1.0, open=.1, cast_glow=.3), rear=-.05, bob=-.01), {})]
        if extra:
            extra(R)
        return R
    return ROWS, frames


STRUCTURE_ROWS = [
    ('idle', 2, True, {}),
    ('hit', 10, False, {}),
    ('death', 6, False, {'holdLast': True}),
]


def structure_rows(base, extra=None):
    """Empty shells: idle (the rag stirs), hit (jolt + flash), death (cracks spread, debris, sag)."""
    def frames():
        R = {
            'idle': [(_set(base(), tell=0.0), {}), (_set(base(), tell=0.5), {})],
            'hit': [(_set(base(), shake=1.0, tell=.25), dict(exposure=1.25, flash=0.22)), (_set(base(), shake=-.4), {})],
            'death': [(_set(base(), shake=1.0, crack=.35), dict(exposure=1.15, flash=0.1)),
                      (_set(base(), crack=.75, end=.5), {}), (_set(base(), crack=1.0, end=1.0), {})],
        }
        if extra:
            extra(R)
        return R
    return STRUCTURE_ROWS, frames


__all__ = [n for n in dir() if not n.startswith('__')]

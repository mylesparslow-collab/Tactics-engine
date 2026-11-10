"""The Hermitage: shared hermit-crab rig, shell library and animation rows.

Shape language (world/factions/hermitage/ART.md): "a thing on legs with one claw out". A shelled unit is a
plainly human-made object (60-70% of the silhouette) WORN on the crab's rear half: tipped so its back end rests on
or near the salt, its mouth facing forward, and the crab's front spilling out of the mouth. The crab (rebuilt after
the owner's "a lot of the crabs look weird" review) must read as a crab at 48 px:
  * two PINCERS in a boxer's guard: fat rounded violet palms, a fixed lower finger and a hinged thumb in hot orange
    with pale tips, the right one (-x, toward the camera) much bigger. Brightest, most saturated shapes.
  * a HEAD: a domed pale-lilac shield with a darker rim, orange mouthparts, two thick pale-orange eyestalks ending
    in big glossy black eyes (pale cup + fixed highlight), short flicking antennae. Eyestalks are kept side-on to
    the camera so neither one vanishes end-on.
  * four short, thick, ARCHED walking legs (dark plum, ochre joint bands, pale pointed tips) growing from the crab's
    body and planted wide around it (auto_feet), splayed across the screen so every leg shows its arch.
  * bare (evicted) forms: a soft pink, segmented abdomen that droops and curls UNDER the body and off to one side
    (never a spiral shell). Each size class differs in proportion through Bare(...) fields, not only scale.
Palette roles: CLAW / FINGER / NAIL (claws), SHIELD (head), LEG / LEG_BAND (legs), STALK (eyestalks), FLESH (bare
abdomen); object colours RUST, VERDI, TAR, BONE, OAK; LAMP amber only for real lights.

Coordinates: metres, y up, the unit faces +z (lower right on screen), its right hand is -x. The crab is built in
its own frame C (origin = head-shield centre, scale s).

API (everything below is exported by `from _hermitage_common import *`)
-------------------------------------------------------------------------
  SIZES / size_camera(size)  'small' | 'medium' | 'large' | 'great' -> crab scale s and Camera(ppm). A unit may
                             pass a float scale as `size` (crab scale) and keep the class camera.
  hermit_pose(**channels)    neutral pose dict (all animation channels, see CHANNELS below)
  Shell(build=fn, ride=..., crab_at=..., ...)
                             how a crab wears an object. fn(add, P, F) adds parts in SHELL-LOCAL coords
                             (origin = object centre, +z = the mouth / forward, +y = up) using F.put(add,
                             prim, mat) or the F.ell/cap/cyl/... helpers, and returns a dict of materials
                             (F.inv(p) maps world->local inside material functions, see local_albedo()).
                             Key fit fields: ride, tilt (- = back end down), crab_at (head-shield centre, put it
                             a little OUTSIDE the mouth), crab_upright (1 = face stays level), span (leg reach),
                             eye_len / eye_bead, big / small, duck_dir / duck_depth, extra_eyes, yaw, x0 / z0.
  shelled(P, size, SHELL, mats=None, lights=(), world=None) -> Scene      crab wearing the shell
  crab_frame(P, SHELL, size) -> Frame C;  claw_grip(P, SHELL, size) -> (world point between the claw tips, dir)
  Bare(...) + bare(P, size, BARE, mats=None, world=None) -> Scene        evicted crab, soft abdomen
  empty(P, SHELL, place=(o, R), rag=(local pt, local axis, radius), mats=None) -> Scene   vacant shell
  hermit_rows(neutral_pose, kind='shell'|'bare', extra=None) -> (ROWS, frames)
  structure_rows(neutral_pose) -> (ROWS, frames)   idle(2) / hit(2) / death(3, cracks) for empty shells
  Shell library (reuse these, do not redraw them): barrel_shell, diving_bell_shell, chapel_bell_shell,
  boiler_shell, long_gun_shell; helpers Frame, barnacles(), rag(), chela(), cheliped_grip(), eyestalk(),
  crab_eyes(), walking_leg(), abdomen(), cracked().
  world(add) callbacks add world-space extras: kit.fx emit(add, pos, 'steam'|'smoke'|'embers', s), flashes.
  Legacy fields still accepted: Shell.feet / leg_roots (only with auto_feet=False), Shell.eyes (REPLACES the face's
  eyestalks: prefer extra_eyes), Bare.feet, spiral_tail() (now draws abdomen()).

CHANNELS (pose dict, all floats, tween-safe): bob lean squash stride lift_a lift_b sway rock yaw slide recoil
  | eye_l eye_r dip_l dip_r (eyestalk swivel rad / dip 0..1) | raise cock snap drum limp spread open (claw)
  | duck (pull into shell, claw across the mouth) tip (shell falls on its side) fold (legs curl)
  | flip (bare: on its back) rear (bare: body pitched up) curl (abdomen tighter) drain (colour to grey)
  | fx end tell (antenna flick phase) glow cast_glow | free unit channels: spin door fire ring stone ...

Worked example (a complete unit, see hermitage_barrel_squatter.py):

    from _hermitage_common import *
    UNIT_ID, SIZE = 'hermitage_barrel_squatter', 1.0
    CAMERA = size_camera('small')
    SHELL = Shell(build=barrel_shell(length=0.80, r_mid=0.32, r_end=0.265), ride=0.31, tilt=-0.06,
                  crab_at=(0, -0.10, 0.53), crab_upright=0.8, z0=-0.84, x0=0.32, yaw=0.15, span=0.46,
                  eye_len=0.32, big=1.35, small=0.70, side_r=0.30)
    def neutral_pose(): return hermit_pose(open=0.35)
    def build(P): return shelled(P, SIZE, SHELL)
    ROWS, frames = hermit_rows(neutral_pose, 'shell')

Per-unit shell abilities go in `extra(rows)` (e.g. set rows['attack'][i][0]['recoil'] and 'fx') and are read
by your shell builder / world() callback. Keep the object nameable at 64 px, no combs (max 3 hoops, 3-5
rivet bosses, 4 posts), smoke only via kit.fx emit(). Check every frame keeps 2 px clear of the frame edges.
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


# crab colour roles: claws are the brightest, most saturated shapes; the head shield is a lighter, duller mauve so
# the face separates from the claws; legs are a dark plum with ochre joint bands; the bare abdomen is soft pink.
CLAW = _hex('#9050b8')          # chela palm and arm: vivid violet
CLAW_DK = _hex('#5e2f7c')
FINGER = _hex('#ea8a2e')        # fingers: hot orange
NAIL = _hex('#f6e2c4')          # pale finger tips
SHIELD = _hex('#a99cc6')        # head shield: cool pale lilac, lighter and duller than the claw
SHIELD_DK = _hex('#6a5c8c')
STALK = _hex('#e8b36e')         # eyestalks and antennae: pale orange
LEG = _hex('#553a69')           # walking legs: dark plum
LEG_BAND = _hex('#d79a4a')      # leg joint bands: ochre
FLESH = _hex('#e6aaa2')         # bare abdomen: soft pink
FLESH_DK = _hex('#b4706f')


def crab_mats(P):
    return {
        'carapace': Material(chitin(SHIELD, dark=SHIELD_DK, speck=_hex('#cfc4e4'), freq=8.0, amt=0.12), spec=0.35,
                             gloss=26, brush=0.04),
        'shieldrim': Material(SHIELD_DK, spec=0.3, gloss=20, brush=0.02),
        'body': Material(chitin(_hex('#6a4a72'), dark=_hex('#3c2846'), amt=0.2), spec=0.15, gloss=14, brush=0.04),
        'mouth': Material(_hex('#c46a3a'), spec=0.3, gloss=20, brush=0.02),
        'claw': Material(chitin(CLAW, dark=CLAW_DK, amt=0.06, freq=6.0), spec=0.30, gloss=30, brush=0.02),
        'tip': Material(FINGER, spec=0.55, gloss=36, brush=0.02),
        'nail': Material(NAIL, spec=0.5, gloss=40, brush=0.0),
        'leg': Material(chitin(LEG, dark=_hex('#3a2448'), amt=0.10), spec=0.3, gloss=22, brush=0.04),
        'joint': Material(LEG_BAND, spec=0.35, gloss=24, brush=0.02),
        'legtip': Material(_hex('#f0c88c'), spec=0.4, gloss=30, brush=0.0),
        'stalk': Material(STALK, spec=0.35, gloss=26, brush=0.02),
        'eye': Material(_hex('#120c12'), spec=1.0, gloss=110, rim=0.4),
        'glint': Material(_hex('#ffffff'), emissive=(0.85, 0.85, 0.85), rim=0.0),
        'streak': Material(_hex('#fff6dc'), spec=0.0, rim=0.0, brush=0.0),
        'tail': Material(FLESH, spec=0.30, gloss=28, sss=0.6, brush=0.0),
        'tailband': Material(FLESH_DK, spec=0.3, gloss=24, sss=0.5),
        'dark': Material(_hex('#140f12'), spec=0.05, gloss=8, rim=0.0, brush=0.0),
        'barn': Material(BONE, spec=0.1, gloss=10, brush=0.06),
        'scar': Material(_hex('#d9c3c9'), spec=0.2, gloss=16, brush=0.0),
        'rag': Material(RAG, spec=0.08, gloss=8, brush=0.06),
        'flash': Material(_hex('#fff2c0'), emissive=_hex('#fff2c0'), rim=0.0),
        'flame': Material(_hex('#ffb347'), emissive=_hex('#ffb347'), rim=0.0),
        'debris': Material(_hex('#4a3a30'), spec=0.1, gloss=10),
    }


CRAB_MATS = ('carapace', 'shieldrim', 'body', 'mouth', 'claw', 'tip', 'nail', 'leg', 'joint', 'legtip', 'stalk',
             'eye', 'tail', 'tailband', 'scar')


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
#
# The crab is built in a frame C (origin = centre of the head shield, +z forward, +y up, right = -x, scale s).
# Reading order at board scale: two fat pincers in a boxer's guard (brightest), a mauve head shield with two thick
# orange eyestalks ending in big glossy black eyes, two pairs of short, arched, banded legs planted wide, and (bare
# only) a soft pink abdomen curled under and to the side.

# claw key poses: (wrist, pointing direction), x OUTWARD (multiplied by the claw's side)
CLAW_KEYS = {
    'fwd': ((0.20, -0.16, 0.18), (-0.50, 0.05, 0.86)),       # big claw rest: boxer's guard in front of the face
    'small': ((0.17, -0.12, 0.19), (-0.35, -0.15, 0.95)),     # small claw rest: tucked under the big one
    'up': ((0.27, 0.26, 0.14), (0.15, 0.95, 0.30)),          # held over the head (bare medium, cast)
    'cock': ((0.22, 0.20, -0.02), (0.10, 0.95, -0.25)),       # drawn up and back, wide open
    'snap': ((0.06, -0.05, 0.31), (-0.60, -0.12, 0.80)),       # thrown forward, shut
    'drum': ((0.16, -0.10, 0.26), (-0.10, -0.65, 0.75)),      # hammered down on the rim
    'tuck': ((0.03, -0.03, 0.14), (-1.0, -0.05, 0.30)),       # laid across the mouth like a door (duck)
    'limp': ((0.16, -0.26, 0.34), (0.10, -0.70, 1.0)),
    'spread': ((0.30, -0.04, 0.20), (0.60, -0.05, 0.85)),
}
SHOULDER = (0.11, -0.06, 0.10)


def _claw_target(P, big=True, guard=None):
    """Crab-local (wrist, direction) of a claw for this pose, x outward. guard = the big claw's rest key."""
    if big:
        w, d = [np.array(x, dtype=np.float64) for x in (guard or CLAW_KEYS['fwd'])]
        seq = (('up', P['raise_']), ('cock', P['cock']), ('snap', P['snap']), ('drum', P['drum']),
               ('tuck', max(P['duck'], P['fold'])), ('limp', P['limp']))
    else:
        w, d = [np.array(x, dtype=np.float64) for x in CLAW_KEYS['small']]
        seq = (('spread', P['spread']), ('fwd', 0.30 * P['snap']), ('up', 0.25 * P['cock']),
               ('tuck', 0.6 * max(P['duck'], P['fold'])))
    for key, t in seq:
        if t <= 0:
            continue
        kw, kd = CLAW_KEYS[key]
        w = lerp(w, np.array(kw), min(t, 1.2))
        d = lerp(norm(d), norm(kd), min(t, 1.0))
    return w, norm(d)


def chela(add, w, d, up, cs, open_, mat='claw', tip='tip', bumps=True, nail='nail', fat=1.0):
    """A pincer: fat rounded palm (violet), a fixed lower finger and a hinged upper thumb (orange, pale tips).
    w wrist (world), d pointing direction, up = the side the thumb opens toward, cs = size in metres.
    Returns (palm centre, frame, point between the finger tips)."""
    Rc = R_from(d, up)
    X, Y, Z = Rc[:, 0], Rc[:, 1], Rc[:, 2]
    f = fat
    add(Ellipsoid(w + Z * 0.02 * cs, (0.06 * cs * f, 0.07 * cs * f, 0.07 * cs), Rc), mat, 0.02 * cs)    # carpus knuckle
    palm = w + Z * 0.15 * cs
    add(Ellipsoid(palm, (0.090 * cs * f, 0.128 * cs * f, 0.135 * cs), Rc), mat, 0.03 * cs)
    add(Ellipsoid(palm + Y * 0.035 * cs - Z * 0.03 * cs, (0.078 * cs * f, 0.095 * cs * f, 0.105 * cs), Rc),
        mat, 0.03 * cs)                                                                             # meaty heel
    if bumps:
        for a, b, rr in ((0.02, 0.0, 0.026), (-0.03, 0.07, 0.020)):
            add(Sphere(palm + Y * 0.115 * cs * f + X * a * cs + Z * b * cs, rr * cs), tip, 0.012 * cs)
    # fixed finger: lower front of the palm, a tapering hook that curves up to meet the thumb
    f0 = palm + Z * 0.115 * cs - Y * 0.050 * cs * f
    f1 = f0 + Z * 0.095 * cs + Y * 0.004 * cs
    f2 = f1 + Z * 0.065 * cs + Y * 0.050 * cs
    add(Capsule(f0, f1, 0.058 * cs * f, 0.040 * cs), tip, 0.022 * cs)
    add(Capsule(f1, f2, 0.040 * cs, 0.011 * cs), nail, 0.008 * cs)
    # moving thumb (dactyl), hinged at the upper front, a heavier hook curving down onto the fixed finger
    a = 0.10 + 0.95 * float(np.clip(open_, 0, 1.2))
    h = palm + Z * 0.095 * cs + Y * 0.066 * cs * f
    dd = norm(Z * np.cos(a) + Y * np.sin(a))
    nd = norm(np.cross(X, dd))
    d1 = h + dd * 0.105 * cs + nd * 0.004 * cs
    d2 = d1 + dd * 0.065 * cs + nd * 0.058 * cs
    add(Sphere(h, 0.050 * cs * f), mat, 0.02 * cs)
    add(Capsule(h, d1, 0.052 * cs * f, 0.038 * cs), tip, 0.020 * cs)
    add(Capsule(d1, d2, 0.038 * cs, 0.011 * cs), nail, 0.008 * cs)
    mouth = (f2 + d2) * 0.5
    return palm, Rc, mouth


def _claw_up(C, d, side, P, big):
    """Which way the thumb opens: up in the guard, back when cocked, forward when drumming."""
    u0 = C.v((side * -0.25, 1.0, -0.05)) if big else C.v((side * -0.5, 1.0, 0.0))
    u1 = C.v((side * 0.10, 0.25, -1.0))
    t = min(1.0, max(P['cock'], P['raise_'] * 0.8)) if big else 0.0
    u = norm(lerp(u0, u1, t))
    if abs(float(u @ d)) > 0.92:
        u = C.v((0, 0, -1)) if d[1] > 0 else C.v((0, 0, 1))
    return u


def cheliped(add, P, C, side, size, big=True, barn=0, seed=3, guard=None, arm=1.0, scar=False, fat=1.0):
    """Arm + pincer in crab frame C. side -1 = crab's right (the big claw). guard = rest (wrist, dir) key.
    Returns (wrist, direction) in world; the gripping point is cheliped_grip()."""
    w, d = _claw_target(P, big, guard)
    w = w * v3(side, 1, 1)
    d = d * v3(side, 1, 1)
    s = C.s
    sh = C.p(v3(SHOULDER[0] * side, SHOULDER[1], SHOULDER[2]))
    ww = C.p(w)
    g = max(size, 0.6) ** 0.5
    l1, l2 = 0.15 * s * g, 0.13 * s * g
    el = rig.two_bone(sh, ww, l1, l2, C.v((side * 1.0, -0.6, 0.1)))
    r0 = (0.050 if big else 0.036) * s * max(size, 0.6) ** 0.7 * arm
    add(Capsule(sh, el, r0 * 0.9, r0), 'claw', 0.0)
    add(Sphere(el, r0 * 0.95), 'joint', 0.008 * s)
    add(Capsule(el, ww, r0, r0 * 1.12), 'claw', 0.01 * s)
    dw = norm(C.v(d))
    up = _claw_up(C, dw, side, P, big)
    op = P['open'] if big else 0.25 + 0.35 * P['spread'] + 0.15 * P['open']
    palm, Rc, mouth = chela(add, ww, dw, up, size * s, op, bumps=big, fat=fat)
    cs = size * s
    if scar:
        X, Y, Z = Rc[:, 0], Rc[:, 1], Rc[:, 2]
        out = X * (-side)
        for a, b in ((0.03, -0.02), (-0.04, 0.05)):
            c = palm + out * 0.082 * cs + Y * a * cs + Z * b * cs
            add(Capsule(c - Y * 0.045 * cs + Z * 0.03 * cs, c + Y * 0.045 * cs - Z * 0.03 * cs, 0.011 * cs),
                'scar', 0.0)
    if barn:
        for i in range(barn):
            nrm = norm(Rc[:, 1] * 0.8 + Rc[:, 0] * (-side) * (0.7 - 0.9 * i) + Rc[:, 2] * (0.2 * i - 0.25))
            barnacles(add, palm + nrm * 0.10 * cs + Rc[:, 2] * (0.03 - 0.08 * i) * cs, nrm,
                      size=0.026 * cs, n=3 + (i % 2), seed=seed + i)
    if big and P['fx'] > 0.5 and P['snap'] > 0.6:
        # snap accent: three short bright strokes off the shut tips (not a burst, not smoke)
        Z, Y = Rc[:, 2], Rc[:, 1]
        for k, (a, b) in enumerate(((0.35, 1.0), (0.8, 0.35), (0.45, -0.9))):
            dir_ = norm(Z * a + Y * b)
            p0 = mouth + dir_ * 0.05 * cs - Z * 0.03 * cs
            add(Capsule(p0, p0 + dir_ * 0.08 * cs, 0.014 * cs, 0.006 * cs), 'streak', 0.0)
    return ww, dw


def cheliped_grip(P, C, size, big=True, guard=None, side=None):
    """World point between the claw's finger tips and the claw direction, for units that hold props."""
    side = (-1 if big else 1) if side is None else side
    w, d = _claw_target(P, big, guard)
    ww = C.p(w * v3(side, 1, 1))
    dw = norm(C.v(d * v3(side, 1, 1)))
    up = _claw_up(C, dw, side, P, big)
    Rc = R_from(dw, up)
    cs = size * C.s
    return ww + Rc[:, 2] * 0.40 * cs + Rc[:, 1] * 0.02 * cs, dw


_CAM = Camera().basis()
_VIEW = norm(-_CAM[0])
_GLINT = norm(-_CAM[0] * 1.0 + _CAM[2] * 0.75 - _CAM[1] * 0.55)


def eyestalk(add, base, d, L, s, bead=0.056, mat='stalk', r=1.0, glint=True):
    """Thick pale-orange stalk ending in a big glossy black eye with a fixed highlight."""
    tip = base + d * L
    mid = base + d * L * 0.55
    add(Capsule(base, mid, 0.042 * s * r, 0.036 * s * r), mat, 0.0)
    add(Capsule(mid, tip, 0.036 * s * r, 0.033 * s * r), mat, 0.004 * s)
    rb = bead * s
    ec = tip + d * rb * 0.7
    add(Torus(tip + d * rb * 0.25, d, rb * 0.78, rb * 0.34), mat, 0.0)        # pale cup round the eye
    add(Ellipsoid(ec, (rb, rb, rb * 1.18), R_from(d)), 'eye', 0.0)
    if glint:
        add(Sphere(ec + _GLINT * rb * 0.80, rb * 0.34), 'glint', 0.0)
    return tip


def _eye_dir(P, C, d_local, side, extra_dip=0.0):
    yaw = P['eye_r'] if side < 0 else P['eye_l']
    dip = max(P['dip_r'] if side < 0 else P['dip_l'], P['duck'], extra_dip)
    d = axis_rot(v3(0, 1, 0), yaw) @ norm(d_local)
    d = norm(lerp(d, v3(side * 0.1, -0.35, 1.0), min(dip, 1.0) * 0.75))
    return d, dip


def walking_leg(add, root, foot, s, outward, leg_len=1.0, r=1.0, arch=1.0):
    """Short, thick, arched walking leg from root to foot (world): the thigh climbs up and out to a high knee,
    the shin drops steeply, and a dark pointed dactyl plants the tip. Plum segments, ochre joint bands."""
    o = v3(outward[0], 0, outward[2])
    out = norm(o) if np.linalg.norm(o) > 1e-6 else v3(1, 0, 0)
    hz = v3(foot[0] - root[0], 0, foot[2] - root[2])
    reach = float(np.linalg.norm(hz))
    hd = hz / reach if reach > 1e-6 else out
    rr = r * s
    # knee: 45% of the way out, raised above the root (the arch), never below it
    kh = (0.08 + 0.05 * leg_len) * s * arch
    knee = root + hd * reach * 0.42 + v3(0, kh, 0)
    # ankle: just inside and above the foot, so the dactyl stabs down and slightly out
    dl = 0.11 * s * leg_len
    ankle = foot - hd * dl * 0.35 + v3(0, dl * 0.95, 0)
    add(Capsule(root, knee, 0.060 * rr, 0.054 * rr), 'leg', 0.0)
    add(Sphere(knee, 0.058 * rr), 'joint', 0.006 * s)
    mid = lerp(knee, ankle, 0.50) + hd * 0.012 * s + v3(0, 0.01 * s, 0)
    add(Capsule(knee, mid, 0.050 * rr, 0.046 * rr), 'leg', 0.004 * s)
    add(Capsule(mid, ankle, 0.046 * rr, 0.038 * rr), 'leg', 0.004 * s)
    add(Sphere(ankle, 0.043 * rr), 'joint', 0.004 * s)
    tipm = lerp(ankle, foot, 0.55)
    add(Capsule(ankle, tipm, 0.036 * rr, 0.024 * rr), 'leg', 0.002 * s)
    add(Capsule(tipm, foot + v3(0, 0.006 * s, 0), 0.024 * rr, 0.006 * rr), 'legtip', 0.002 * s)
    return knee


def carapace(add, C, s_big=1.0, antennae=True, P=None, wide=1.0, thorax=True, rim=True):
    """Head and front body in crab frame C: a domed mauve shield with a darker rim, a short rostrum, orange
    mouthparts, the soft thorax running back into the shell, and two long flicking antennae."""
    w = s_big * wide
    if thorax:
        C.ell(add, (0, -0.035, -0.17), (0.145 * w, 0.105, 0.18), 'body', 0.0)
    if rim:
        C.ell(add, (0, -0.012, -0.005), (0.180 * w, 0.090, 0.172), 'shieldrim', 0.02)
    C.ell(add, (0, 0.006, 0.0), (0.172 * w, 0.102, 0.165), 'carapace', 0.02)
    C.ell(add, (0, 0.035, 0.07), (0.125 * w, 0.075, 0.095), 'carapace', 0.03)      # brow
    C.ell(add, (0, 0.035, 0.155), (0.034, 0.028, 0.045), 'carapace', 0.015)        # rostrum
    for sx in (-1, 1):
        C.ell(add, (sx * 0.042, -0.075, 0.13), (0.036, 0.055, 0.03), 'mouth', 0.012)   # mouthparts
    if antennae:
        ph = 0.0 if P is None else P.get('tell', 0.0)
        fl = 0.0 if P is None else (P.get('fx', 0.0) * 0.0)
        for sx in (-1, 1):
            sw = 0.22 * np.sin(2 * np.pi * (ph + (0.0 if sx < 0 else 0.37))) + fl
            a = v3(sx * 0.035, 0.0, 0.165)
            b = a + v3(sx * (0.06 + sw * 0.3), 0.08 + 0.04 * sw, 0.10)
            c = b + v3(sx * (0.10 + sw * 0.6), 0.03 - 0.06 * sw, 0.07)
            C.cap(add, a, b, 0.014, 0.011, 'stalk')
            C.cap(add, b, c, 0.011, 0.006, 'stalk')


def abdomen(add, C, curl=0.0, size=1.0, thick=(0.15, 0.05), side=-0.6, drop=0.0, sag=0.0, segs=4, start=None,
            **_ignored):
    """The bare crab's soft abdomen: a pale, segmented, slightly sagging sac that leaves the back of the thorax,
    droops and curls UNDER the body and off to one side (never a spiral shell above it). curl 0..1 tightens it.
    Extra spiral_tail kwargs (center, r0, turns, helix...) are accepted and ignored."""
    sz = size
    st = v3(0, -0.04, -0.24) if start is None else v3(*start)
    k = 1.0 - 0.22 * curl
    R0 = 0.20 * sz * k
    cz, cy = st[2] - 0.05 * sz, st[1] - R0 - drop
    phi0, phi1 = 0.15, np.pi * (1.10 + 0.22 * curl)
    n = segs * 2 + 1
    pts, rad = [], []
    for i in range(n):
        t = i / (n - 1)
        phi = phi0 + (phi1 - phi0) * t
        R = R0 * (1.0 - 0.45 * t)
        q = v3(side * 0.18 * sz * t ** 1.2, cy + R * np.cos(phi) - sag * np.sin(np.pi * t) * 0.10 * sz,
               cz - R * np.sin(phi) * 1.25)
        pts.append(C.p(q))
        bulge = np.sin(np.pi * min(t * 1.4, 1.0)) * 0.35 + 0.65
        rad.append((thick[0] * bulge * (1 - t) + thick[1] * t) * sz * C.s)
    # neck from the thorax into the sac
    add(Capsule(C.p(st), pts[0], 0.11 * sz * C.s, rad[0]), 'tail', 0.03 * C.s)
    for j in range(segs):
        a, b = pts[2 * j], pts[2 * j + 2]
        m = pts[2 * j + 1]
        ax = norm(b - a)
        ln = float(np.linalg.norm(b - a))
        r = rad[2 * j + 1]
        add(Ellipsoid(m, (r * 1.10, r, ln * 0.62), R_from(ax, C.v((0, 1, 0)))), 'tail', 0.035 * C.s)
        if j < segs - 1:
            add(Torus(b, ax, rad[2 * j + 2] * 0.90, 0.028 * C.s * sz), 'tailband', 0.0)
    tipp = pts[-1]
    tdir = norm(pts[-1] - pts[-2])
    add(Ellipsoid(tipp + tdir * rad[-1] * 0.8, (rad[-1] * 1.5, rad[-1] * 0.5, rad[-1] * 1.0),
                  R_from(tdir, C.v((0, 1, 0)))), 'tailband', 0.01 * C.s)
    return pts


def spiral_tail(add, C, curl=0.0, size=1.0, center=(0, 0.30, -0.40), r0=0.27, r1=0.07, thick=(0.15, 0.035),
                turns=1.05, bounce=0.0, helix=-0.10, bands=3):
    """Deprecated (it read as a snail shell). Kept so old unit files still run; it now draws abdomen()."""
    return abdomen(add, C, curl=curl, size=size, thick=(thick[0], max(thick[1], 0.045)))


def _gait_feet(P, feet, fwd, s, step=0.16):
    """feet: 4 world points (FR, FL, BR, BL); pairs A = FR+BL, B = FL+BR alternate."""
    out = []
    for i, f in enumerate(feet):
        a = i in (0, 3)
        dz = P['stride'] * step * s * (1 if a else -1)
        lift = (P['lift_a'] if a else P['lift_b']) * 0.11 * s
        out.append(f + fwd * dz + v3(0, lift, 0))
    return out


# leg roots on the crab body (FR, FL, BR, BL), crab-local; and the default splay of each foot
LEG_ROOTS = ((-0.14, -0.075, 0.05), (0.14, -0.075, 0.05), (-0.15, -0.085, -0.07), (0.15, -0.085, -0.07))
LEG_SPLAY = ((-1.0, 0.40), (1.0, 0.40), (-1.0, -0.50), (1.0, -0.50))


def _auto_feet(C, roots_w, span, s, spread=1.0):
    feet = []
    for i, rt in enumerate(roots_w):
        sx, sz = LEG_SPLAY[i]
        dv = C.v((sx * spread, 0, sz))
        dv = norm(v3(dv[0], 0, dv[2]))
        vh = norm(v3(_VIEW[0], 0, _VIEW[2]))
        dv = norm(dv - vh * (dv @ vh) * 0.55)          # splay across the screen, so every leg shows its arch
        reach = span * s * (1.0 if i < 2 else 0.92)
        feet.append(v3(rt[0], 0, rt[2]) + dv * reach)
    return feet


def crab_legs(add, P, C, roots_w, feet_w, s, leg_len=1.0, leg_r=1.0, fold=0.0, tuck_y=-0.16, skip=()):
    for i, (rt, ft) in enumerate(zip(roots_w, feet_w)):
        if i in skip:
            continue
        side = -1 if i % 2 == 0 else 1
        tuck = C.p((side * 0.24, tuck_y, 0.10 if i < 2 else -0.06))
        ft = lerp(ft, tuck, fold)
        o = C.v((side, 0, LEG_SPLAY[i][1]))
        walking_leg(add, rt, ft, s, o, leg_len * (1 - 0.25 * fold), leg_r)


def crab_eyes(add, P, C, s, eye_len=0.22, bead=0.056, droop=0.0, splay=0.36, base=(0.066, 0.05, 0.13), r=1.0,
              duck_keep=0.45, fwd=0.22):
    """Two eyestalks from the front of the shield. Swivel = eye_l / eye_r, dip_l / dip_r pull one down."""
    tips = []
    for side in (-1, 1):
        yaw = P['eye_r'] if side < 0 else P['eye_l']
        dip = max(P['dip_r'] if side < 0 else P['dip_l'], droop)
        dl = norm(v3(side * splay, 1.0, fwd))
        dl = axis_rot(v3(0, 1, 0), yaw) @ dl
        dl = norm(lerp(dl, v3(side * 0.25, -0.15, 1.0), min(dip, 1.0) * 0.8))
        if P.get('flip', 0.0) > 0:      # upside down: the stalks flop out sideways, never into the ground
            dl = norm(lerp(dl, v3(side * 0.8, 0.05, 0.6), min(P['flip'], 1.0)))
        L = eye_len * s * (1 - 0.45 * min(dip, 1.0)) * (1 - (1 - duck_keep) * P['duck'])
        dw = C.v(dl)
        dw = norm(dw - _VIEW * (dw @ _VIEW) * 0.6)      # keep both stalks side-on to the camera, never end-on
        tips.append(eyestalk(add, C.p(v3(side * base[0], base[1], base[2])), dw, L, s, bead=bead, r=r))
    return tips


# ------------------------------------------------------------------ shelled crab

@dataclass
class Shell:
    """How a crab wears an object. All lengths in metres.

    build      fn(add, P, F) -> materials dict. Adds the object in shell-local coords (origin = object centre,
               +z = mouth/forward, +y = up). The rig places F; use F.put / F.cyl / F.ell / ... to add parts.
    ride       height of the shell origin above the ground when standing
    crab_at    shell-local point of the crab's head-shield centre (at the mouth, so the face looks out of it)
    tilt       rest pitch (+ = back end raised, mouth toward the ground; - = back end down on the ground, the worn
               look: the object sits on the crab's rear half and drags)
    crab_pitch extra pitch of the crab inside the shell (+ = nose down); set it so the face looks level
    feet       legacy 4 world (x, z) foot spots; only used when auto_feet=False
    auto_feet  True: feet are planted wide around the crab's own leg roots (span, spread) - the default
    span       horizontal reach of each leg in crab units; spread = sideways bias of the splay
    leg_roots  legacy shell-local leg roots; ignored unless auto_feet=False (legs grow from the crab body)
    eyes       legacy eyestalk override [(shell-local base, shell-local dir, length)]: REPLACES the face's eyes.
               Prefer extra_eyes (added to the two face eyes, e.g. the barrel's bung-hole eye).
    eye_len    face eyestalk length (crab units); eye_bead = eye radius (crab units)
    big, small chela scales; barn = barnacle clusters on the big claw
    duck_dir   shell-local direction the crab pulls into on hit (default straight back into the mouth)
    duck_depth how far it pulls in (crab units)
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
    eye_len: float = 0.22
    big: float = 1.25
    small: float = 0.65
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
    guard: Optional[tuple] = None   # big claw rest (wrist, dir); None = CLAW_KEYS['fwd'] (boxer's guard)
    yaw: float = 0.0           # turn the whole unit (+ = toward screen-right, side-on); feet turn with it
    auto_feet: bool = True
    span: float = 0.40
    spread: float = 1.0
    extra_eyes: Optional[tuple] = None
    duck_dir: tuple = (0.0, 0.05, -1.0)
    duck_depth: float = 0.20
    crab_upright: float = 0.0  # 0..1: keep the crab's up axis toward world up regardless of the shell's tilt
    shield: float = 1.0        # head-shield width factor
    hide_legs: tuple = ()      # leg indices (FR, FL, BR, BL) that the object hides anyway


def shell_frame(P, sh):
    """World frame of the shell for this pose: ride height, tilt, rock, sway, duck, recoil and the death tip."""
    tip = P['tip']
    duck = P['duck']
    ride = sh.ride * (1 - 0.08 * duck - 0.20 * P['fold'] * (1 - tip)) + P['bob']
    y = lerp(ride, sh.side_r, tip)
    pitch = lerp(sh.tilt + P['lean'] + P['rock'], sh.lie, tip)
    roll = -sh.tip_dir * tip * sh.tip_angle + P['sway']
    R = rot_y(sh.yaw + P['yaw']) @ rot_z(roll) @ rot_x(pitch)
    o = v3(sh.x0 + P['slide'] + P['shake'] * 0.02, y, sh.z0) + rot_y(sh.yaw + P['yaw']) @ v3(0, 0, -P['recoil'])
    return Frame(o, R, 1.0)


def crab_frame(P, sh, size):
    """The crab's frame C inside shell sh for pose P (what shelled() builds the crab in)."""
    s = SIZES[size]['s'] if isinstance(size, str) else float(size)
    F = shell_frame(P, sh)
    dd = norm(v3(*sh.duck_dir)) * sh.duck_depth * s * P['duck']
    Rl = rot_x(sh.crab_pitch)
    if sh.crab_upright > 0:
        # partly undo the shell's tilt and rock so the face stays level
        Rl = rot_x(-(sh.tilt + P['rock']) * sh.crab_upright * (1 - P['tip'])) @ Rl
    return F.child(v3(*sh.crab_at) + dd, Rl, s)


def claw_grip(P, sh, size, big=True):
    """World point held between the claw tips (and the claw's direction) for a shelled crab."""
    C = crab_frame(P, sh, size)
    return cheliped_grip(P, C, sh.big if big else sh.small, big, sh.guard if big else None)


def shelled(P, size, sh, mats=None, lights=(), world=None):
    """Scene: the crab wearing shell `sh`. mats override/extend materials; world(add) adds world extras."""
    s = SIZES[size]['s'] if isinstance(size, str) else float(size)
    parts, add = new_parts()
    F = shell_frame(P, sh)
    m = crab_mats(P)
    sm = sh.build(add, P, F)
    if sm:
        m.update(sm)
    C = crab_frame(P, sh, size)
    carapace(add, C, antennae=sh.antennae and P['duck'] < 0.5, P=P, wide=sh.shield)
    # claws (right = -x is the big one, toward the camera)
    cheliped(add, P, C, -1, sh.big, True, barn=sh.barn, guard=sh.guard)
    cheliped(add, P, C, 1, sh.small, False)
    droop = P['end'] * 0.9
    if sh.eyes is None:
        crab_eyes(add, P, C, s, sh.eye_len, sh.eye_bead, droop=droop, r=1.0)
    else:
        for i, (b, d, L) in enumerate(sh.eyes):
            side = -1 if i % 2 == 0 else 1
            yaw = (P['eye_r'] if side < 0 else P['eye_l']) * (1.0 if i < 2 else -0.7)
            dip = max(P['dip_r'] if side < 0 else P['dip_l'], P['duck'], droop)
            dd = axis_rot(C.v((0, 1, 0)), yaw) @ norm(F.v(d))
            dd = norm(lerp(dd, C.v((side * 0.15, -0.30, 1.0)), min(dip, 1.0) * 0.7))
            eyestalk(add, F.p(b), dd, L * (1 - 0.6 * min(dip, 1.0)), s, bead=sh.eye_bead)
    for b, d, L in (sh.extra_eyes or ()):
        dip = max(P['dip_l'] * 0.5, P['duck'], droop)
        dd = axis_rot(F.v((0, 1, 0)), -0.7 * P['eye_l']) @ norm(F.v(d))
        dd = norm(lerp(dd, F.v((0.1, -0.2, 1.0)), min(dip, 1.0) * 0.6))
        eyestalk(add, F.p(b), dd, L * (1 - 0.6 * min(dip, 1.0)), s, bead=sh.eye_bead * 0.9)
    # legs
    Ry = rot_y(sh.yaw + P['yaw'])
    fwd = Ry @ v3(0, 0, 1)
    if sh.auto_feet or sh.leg_roots is None:
        roots = [C.p(r) for r in LEG_ROOTS]
    else:
        roots = [F.p(r) for r in sh.leg_roots]
    if sh.auto_feet:
        # plant from the standing pose so ducking and rocking do not drag the feet
        P0 = dict(P)
        P0.update(duck=0.0, rock=0.0, sway=0.0, bob=0.0, lean=0.0, recoil=0.0, slide=0.0, shake=0.0)
        C0 = crab_frame(P0, sh, size)
        base = _auto_feet(C0, [C0.p(r) for r in LEG_ROOTS], sh.span, s, sh.spread)
        base = [b + v3(P['slide'], 0, 0) - fwd * P['recoil'] for b in base]
    else:
        base = [v3(sh.x0 + P['slide'], 0, sh.z0) + Ry @ v3(fx, 0, fz - P['recoil']) for fx, fz in sh.feet]
    feet = _gait_feet(P, base, fwd, s)
    fold = max(P['fold'], P['tip'])
    crab_legs(add, P, C, roots, feet, s, sh.leg_len, sh.leg_r, fold, skip=sh.hide_legs)
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
    h        head-shield centre height      yaw   turn toward side-on (+ shows the left flank, - the right)
    tail     abdomen kwargs: size, thick (fat, tip), side (-x = toward the camera), drop, sag, segs
    big/small chela scales; barn = barnacle clusters on the big claw; scar = scarred big claw
    eye_len / eye_bead   eyestalk length and eye radius (small crabs: big eyes)
    span / spread        leg reach and sideways splay; leg_len / leg_r leg length and thickness
    shield   head-shield width factor; arm = claw-arm thickness factor; fat = pincer bulk factor
    pitch    rest pitch of the body (+ nose down); feet = legacy, ignored unless auto_feet=False"""
    h: float = 0.40
    feet: tuple = ((-0.48, 0.40), (0.56, 0.36), (-0.52, -0.30), (0.60, -0.26))
    yaw: float = 0.65
    tail: dict = field(default_factory=dict)
    big: float = 1.3
    small: float = 0.65
    barn: int = 0
    eye_len: float = 0.28
    leg_len: float = 1.0
    leg_r: float = 1.1
    z0: float = 0.0
    x0: float = 0.0
    eye_bead: float = 0.068
    span: float = 0.36
    spread: float = 1.0
    shield: float = 1.0
    arm: float = 1.0
    fat: float = 1.0
    scar: bool = False
    pitch: float = 0.0
    auto_feet: bool = True
    shield_barn: int = 0


def bare_frame(P, b, s):
    fl = P['flip']
    h = lerp(b.h + P['bob'] / s, 0.12 + 0.11 * b.big, fl)
    R = rot_y(b.yaw + P['yaw']) @ rot_z(-np.pi * 0.96 * fl + P['sway']) @ rot_x(b.pitch + P['lean'] - P['rear'] * (1 - fl))
    o = v3(b.x0 + P['slide'], h * s, b.z0 - P['recoil'])
    return Frame(o, R, s)


def bare(P, size, b, mats=None, lights=(), world=None):
    """Scene: the evicted crab (soft abdomen curled under, pincers up)."""
    s = SIZES[size]['s'] if isinstance(size, str) else float(size)
    parts, add = new_parts()
    C = bare_frame(P, b, s)
    carapace(add, C, P=P, wide=b.shield)
    if b.shield_barn:
        for i in range(b.shield_barn):
            nrm = norm(C.v((0.5 - 0.9 * i, 1.0, -0.4 + 0.2 * i)))
            barnacles(add, C.p((0.07 - 0.13 * i, 0.07, -0.06 + 0.03 * i)) + nrm * 0.03 * s, nrm, size=0.035 * s,
                      n=3 + i % 2, seed=11 + i)
    tk = dict(b.tail)
    if P['flip'] > 0:      # on its back the soft abdomen flops over sideways onto the salt
        tk['side'] = tk.get('side', -0.6) - 1.6 * P['flip']
        tk['drop'] = tk.get('drop', 0.0) - 0.10 * P['flip']
    abdomen(add, C, curl=P['curl'] * (1 - 0.6 * P['flip']), **tk)
    cheliped(add, P, C, -1, b.big, True, barn=b.barn, arm=b.arm, scar=b.scar, fat=b.fat)
    cheliped(add, P, C, 1, b.small, False, arm=b.arm)
    droop = P['end'] * 0.8 * (1 - P['flip'])
    crab_eyes(add, P, C, s, b.eye_len * (1 - 0.3 * P['flip']), b.eye_bead, droop=droop, duck_keep=1.0)
    fwd = rot_y(b.yaw + P['yaw']) @ v3(0, 0, 1)
    Ry = rot_y(b.yaw + P['yaw'])
    roots = [C.p(r) for r in LEG_ROOTS]
    if b.auto_feet:
        P0 = dict(P)
        P0.update(rear=0.0, lean=0.0, bob=0.0, sway=0.0, flip=0.0, recoil=0.0, slide=0.0)
        C0 = bare_frame(P0, b, s)
        base = _auto_feet(C0, [C0.p(r) for r in LEG_ROOTS], b.span, s, b.spread)
        base = [q + v3(P['slide'], 0, 0) - v3(0, 0, P['recoil']) for q in base]
    else:
        base = [v3(b.x0 + P['slide'], 0, b.z0 - P['recoil']) + Ry @ v3(fx * s, 0, fz * s) for fx, fz in b.feet]
    feet = _gait_feet(P, base, fwd, s, step=0.20)
    fold = max(P['fold'], P['flip'] * 0.6)
    if P['flip'] > 0:
        # on its back the legs paddle in the air: feet rise with the body
        feet = [lerp(f, C.p((LEG_ROOTS[i][0] * 1.9, -0.17, LEG_ROOTS[i][2] * 1.3 + 0.04)), min(P['flip'], 1.0))
                for i, f in enumerate(feet)]
    crab_legs(add, P, C, roots, feet, s, b.leg_len, b.leg_r, fold * 0.7, tuck_y=-0.22)
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
    """Standard Hermitage rows.
    kind 'shell': idle = eyestalks swivel on their own, one dips below the rim and pops back, claws work open and
    shut, antennae flick; move = alternating leg pairs with the object rocking and swaying; attack = the big claw
    cocks up and back wide open, then snaps forward shut (hitFrame 2, three bright strokes off the tips); hit = the
    crab yanks into the object, big claw laid across the mouth like a door, only eyes and claw tips out; death =
    slump, the object tips onto its side, one claw lolls out, eyestalks droop; cast = rear and drum the big claw
    twice on the rim.
    kind 'bare': twitchy sideways shuffle, fast scuttle with the abdomen bouncing, cock-and-snap from a rear,
    flinch with the abdomen clamped tight, flip onto its back with legs curling and colour draining, cast = rear
    and drum. extra(rows) may edit the poses in place."""
    def frames():
        b = base
        R = {}
        if kind == 'shell':
            R['idle'] = [(_set(b(), rock=[0, .03, 0, -.025][i], sway=[0, .02, 0, -.015][i],
                               eye_l=b()['eye_l'] + [.30, .55, .10, -.25][i],
                               eye_r=b()['eye_r'] + [-.25, -.05, -.45, -.20][i],
                               dip_l=[0, 0, 0, .0][i], dip_r=[0, 0, 1, .2][i],
                               open=b()['open'] + [0, .25, -.15, .1][i], spread=b()['spread'] + [0, .15, 0, .08][i],
                               tell=i / 4), {}) for i in range(4)]
            R['move'] = [(_set(b(), stride=[1, 0, -1, 0][i], lift_a=[0, 0, 0, 1][i], lift_b=[0, 1, 0, 0][i],
                               sway=[.06, 0, -.06, 0][i], bob=[-.012, .015, -.012, .015][i],
                               rock=[.035, -.01, .035, -.01][i], eye_l=b()['eye_l'] + .2, eye_r=b()['eye_r'] - .2,
                               tell=i / 4), {}) for i in range(4)]
            R['attack'] = [(_set(b(), cock=[.65, 1, 0, 0][i], snap=[0, 0, 1, .35][i], open=[.75, 1.05, .0, .25][i],
                                 lean=[-.05, -.09, .07, .02][i], fx=[0, 0, 1, .2][i], strike=[0, .3, 1, .3][i],
                                 eye_l=b()['eye_l'] + .15, eye_r=b()['eye_r'] - .15), {})
                           for i in range(4)]
            R['hit'] = [(_set(b(), duck=1.0, lean=-.10, sway=.05, shake=1, open=0.0), dict(exposure=1.25, flash=0.22)),
                        (_set(b(), duck=.55, lean=-.03, sway=-.02, open=.1), {})]
            R['death'] = [(_set(b(), duck=.6, lean=-.10, sway=.05, open=.1), {}),
                          (_set(b(), duck=.2, fold=.5, tip=.25, bob=-.03, end=.25, limp=.3), {}),
                          (_set(b(), tip=.92, fold=.9, squash=.95, limp=.8, end=.65, open=.5), {}),
                          (_set(b(), tip=1.0, fold=1.0, limp=1.0, end=1.0, open=.4), {})]
            R['cast'] = [(_set(b(), lean=-.14, raise_=1.0, open=.55, eye_l=.3, eye_r=-.3, cast_glow=.5), {}),
                         (_set(b(), lean=-.03, drum=1.0, open=.05, bob=-.015, cast_glow=1.0), {}),
                         (_set(b(), lean=-.14, raise_=1.0, open=.55, cast_glow=.6), {}),
                         (_set(b(), lean=-.03, drum=1.0, open=.05, bob=-.015, cast_glow=.3), {})]
        else:
            def rel(P, **kw):
                for k, v in kw.items():
                    P[k] = P[k] + v
                return P
            R['idle'] = [(rel(_set(b(), tell=i / 4, curl=[0, .5, 1, .4][i]),
                              open=[0, .25, -.1, .15][i], eye_l=[.25, .5, .05, -.25][i], eye_r=[-.25, -.05, -.45, -.1][i],
                              lift_a=[0, .7, 0, 0][i], lift_b=[0, 0, 0, .6][i],
                              slide=[0, .05, .07, .02][i], bob=[0, .012, 0, .008][i]), {}) for i in range(4)]
            R['move'] = [(rel(_set(b(), stride=[1, 0, -1, 0][i], lift_a=[0, 0, 0, 1][i], lift_b=[0, 1, 0, 0][i],
                                   tell=i / 4),
                              eye_l=.15, eye_r=-.15, bob=[0, .03, 0, .03][i], sway=[.05, 0, -.05, 0][i],
                              curl=[0, .5, 0, .5][i], lean=[.04, .04, .04, .04][i]), {}) for i in range(4)]
            R['attack'] = [(rel(_set(b(), cock=[.7, 1, 0, 0][i], snap=[0, 0, 1, .35][i],
                                     open=[.75, 1.05, .0, .25][i], fx=[0, 0, 1, .2][i]),
                                lean=[-.06, -.10, .10, .03][i], rear=[.1, .15, -.1, 0][i]), {}) for i in range(4)]
            R['hit'] = [(rel(_set(b(), curl=1.0, open=.0, shake=1, duck=.75), lean=-.16, bob=-.02),
                         dict(exposure=1.25, flash=0.22)),
                        (rel(_set(b(), curl=.6, duck=.35), lean=-.05), {})]
            R['death'] = [(rel(_set(b(), curl=1.0, open=.7, duck=.5), lean=-.2), {}),
                          (_set(b(), flip=.35, fold=.45, curl=1.0, raise_=.3, drain=.3, end=.25), {}),
                          (_set(b(), flip=.85, fold=.85, curl=1.0, raise_=0.0, drain=.55, end=.6, squash=.95), {}),
                          (_set(b(), flip=1.0, fold=1.0, curl=1.0, raise_=0.0, drain=.75, end=1.0, open=.1, duck=.6), {})]
            R['cast'] = [(rel(_set(b(), raise_=1.0, open=.55, cast_glow=.5), rear=.18, bob=.02), {}),
                         (rel(_set(b(), drum=1.0, open=.05, cast_glow=1.0), rear=-.05, bob=-.01), {}),
                         (rel(_set(b(), raise_=1.0, open=.55, cast_glow=.6), rear=.18, bob=.02), {}),
                         (rel(_set(b(), drum=1.0, open=.05, cast_glow=.3), rear=-.05, bob=-.01), {})]
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

"""Shared Lanternkeepers helpers: palette materials, lamps (with Light objects), hats, ghost
translucency and the faction animation tweaks (lamp-flicker idle, gutter death).

Shape language: tall, narrow, vertical; every silhouette is a tower with a bright top.
Gold appears only on real light sources (flame, lamp glass, beams). Brass is kept dull.
"""
import copy
import dataclasses
import numpy as np
from kit.humanoid import *          # noqa: F401,F403  (v3, norm, prims, Material, Light, ...)
from kit.anim import humanoid_rows
from kit.looks import LOOKS, PALETTES
from render import Camera, Part
from sdf import Prim
import rig

FACTION = 'lanternkeepers'
LK = PALETTES[FACTION]
GOLD = LK['gold']                   # #e3b04b  light only
SEA = LK['sea_grey']                # #8e9ba3
LENS = LK['lens_white']             # #fff6dc
SLATE = LK['slate']                 # #2b3239
OIL = LK['oilskin']                 # #c79a3a
FLAME = _hex('#ffc35a')
FLAME_CORE = _hex('#fff0c0')
LAMP_LIGHT = _hex('#ffb35c')
BRASS_DULL = _hex('#8a7448')


# ------------------------------------------------------------------ materials

def _tone(c, f):
    return tuple(np.clip(np.array(c) * f, 0, 1))


def _aged(c, k=0.22):
    """Pull a colour toward sea grey (faded, salt-bleached)."""
    return tuple(np.array(c) * (1 - k) + np.array(SEA) * k)


def oilskin_albedo(base=OIL, wear=0.25, freq=16.0):
    """Waxed oilskin: darker creases and paler worn patches by noise."""
    b = np.array(base)

    def fn(p, n):
        w = fbm(p * np.array([1.0, 0.45, 1.0]), freq, 3)
        crease = np.clip((0.42 - w) * 3.0, 0, 1)[:, None]
        pale = np.clip((w - 0.62) * 3.0, 0, 1)[:, None] * wear
        c = b[None, :] * (1 - 0.32 * crease) + np.array(LENS)[None, :] * pale * 0.35
        return np.clip(c, 0, 1)
    return fn


def noisy(base, amt=0.10, freq=24.0):
    b = np.array(base)
    return lambda p, n: np.clip(b[None, :] * (1 - amt + 2 * amt * fbm(p, freq, 2)[:, None]), 0, 1)


def keeper_mats(P, skin=None, hair=_hex('#5a4a40'), coat=OIL, eyes=_hex('#2a1d1a'), beard=None,
                lips=_hex('#a8584c')):
    """The faction's common material set. Emissives scale with P['glow'] (gutter at death)."""
    g = P['glow'] * (1 + 0.6 * P['cast_glow'])
    skin = skin if skin is not None else W['skin_light']
    return {
        'oilskin': Material(oilskin_albedo(_aged(coat)), spec=0.28, gloss=22, brush=0.08),
        'oilskin_dk': Material(oilskin_albedo(_tone(_aged(coat), 0.72)), spec=0.25, gloss=20, brush=0.08),
        'slate': Material(noisy(SLATE, 0.10), spec=0.06, gloss=10, brush=0.08),
        'seagrey': Material(noisy(SEA, 0.08), spec=0.04, gloss=8, brush=0.09),
        'coatgrey': Material(noisy(_hex('#6a767e'), 0.10), spec=0.05, gloss=8, brush=0.09),
        'wool': Material(noisy(_hex('#59636b'), 0.12), spec=0.02, gloss=6, brush=0.10),
        'canvas': Material(noisy(_hex('#b8b2a2'), 0.08), spec=0.03, brush=0.08),
        'whitewash': Material(noisy(_hex('#e4e0d4'), 0.06), spec=0.03, brush=0.06),
        'skin': Material(face_albedo(P, skin, hair, eyes=eyes, beard=beard, lips=lips), spec=0.06, gloss=12,
                         sss=0.6, brush=0.02),
        'hair': Material(hair, spec=0.2, gloss=16, brush=0.10),
        'brass': Material(BRASS_DULL, spec=0.8, gloss=36, metal=0.9, brush=0.05),
        'darkiron': Material(_hex('#3a3f46'), spec=0.6, gloss=30, metal=0.6, brush=0.05),
        'glove': Material(_hex('#3a2e26'), spec=0.15, gloss=18, brush=0.04),
        'lamp': Material(_hex('#ffd98a'), spec=0.3, gloss=30, emissive=_tone(_hex('#ffcf7a'), g), rim=0.0),
        'flame': Material(FLAME, emissive=_tone(FLAME, g), rim=0.0),
        'core': Material(FLAME_CORE, emissive=_tone(FLAME_CORE, g), rim=0.0),
        'lens': Material(LENS, spec=1.2, gloss=80, emissive=_tone(LENS, 0.25 + 0.75 * P['cast_glow']), rim=0.6,
                         brush=0.0),
        'beam': Material(GOLD, emissive=_tone(_hex('#ffe3a0'), 1.0), rim=0.0),
        'wax': Material(_hex('#ece2c6'), spec=0.2, gloss=20, sss=0.5, brush=0.03),
    }


# ------------------------------------------------------------------ lamps

def flame(add, c, P, size=1.0, mat='flame'):
    """Teardrop flame with a hot core; P['flick'] (0..3) and P['glow'] shape it."""
    f = P.get('flick', 0)
    s = size * (0.6 + 0.4 * min(P['glow'], 1.4))
    lean = [0.0, 0.006, -0.004, 0.003][int(f) % 4] * size
    hgt = [1.0, 0.8, 1.15, 0.9][int(f) % 4]
    if P['glow'] < 0.05:
        return
    add(Capsule(c, c + v3(lean, 0.045 * s * hgt, 0), 0.016 * s, 0.003), mat, 0.0)
    add(Sphere(c + v3(0, 0.008 * s, 0), 0.009 * s), 'core', 0.0)


def light_at(lights, P, c, intensity=1.5, radius=0.16, color=LAMP_LIGHT):
    g = P['glow'] * (1 + 0.8 * P['cast_glow'])
    lights.append(Light(pos=v3(*c), color=color, intensity=intensity * g, radius=radius))


def hurricane(add, lights, P, c, size=1.0, frame='brass', R=None, light=1.5):
    """Hurricane lantern: base, glowing glass globe with wire guards, cap and bail."""
    R = np.eye(3) if R is None else R
    s = size
    up = R[:, 1]
    add(Cylinder(c - up * 0.062 * s, c - up * 0.040 * s, 0.040 * s, 0.006), frame, 0.0)
    add(Ellipsoid(c, (0.034 * s, 0.048 * s, 0.034 * s), R), 'lamp', 0.0)
    for t in (-0.022, 0.016):
        add(Torus(c + up * t * s, up, 0.035 * s, 0.0035 * s), frame, 0.0)
    for k in range(4):
        a = k * np.pi / 2 + 0.4
        o = R @ v3(np.cos(a) * 0.037, 0, np.sin(a) * 0.037) * s
        add(Capsule(c + o - up * 0.042 * s, c + o + up * 0.040 * s, 0.003 * s), frame, 0.0)
    add(Cylinder(c + up * 0.042 * s, c + up * 0.062 * s, 0.030 * s, 0.006), frame, 0.0)
    add(Capsule(c + up * 0.062 * s, c + up * 0.078 * s, 0.012 * s, 0.006 * s), frame, 0.0)
    add(Torus(c + up * 0.075 * s, R[:, 2], 0.03 * s, 0.003 * s), frame, 0.0)
    light_at(lights, P, c + v3(0, 0, 0.03), light * s, 0.15 * s)
    return c + up * 0.10 * s       # bail top (hang point)


def box_lamp(add, lights, P, c, size=1.0, frame='brass', R=None, light=1.5):
    lantern(add, c, frame, 'lamp', size, R)
    light_at(lights, P, c + v3(0, 0, 0.03), light * size, 0.15 * size)
    return c + (np.eye(3) if R is None else R)[:, 1] * 0.085 * size


def pole_lamp(add, lights, P, a, b, kind='hurricane', size=1.0, shaft='wood', frame='brass', arm=0.07, light=1.6):
    """Straight pole a->b with an arm at the top and a lamp hanging from it. Returns the lamp centre."""
    add(Capsule(a, b, 0.017, 0.014), shaft, 0.0)
    ax = norm(b - a)
    side = norm(np.cross(ax, v3(0, 0, 1)) if abs(ax[2]) < 0.9 else v3(1, 0, 0))
    if side[0] < 0:
        side = -side
    tip = b + side * arm
    add(Capsule(b - ax * 0.02, tip, 0.008), frame, 0.0)
    add(Capsule(tip, tip - v3(0, 0.035, 0), 0.004), frame, 0.0)
    c = tip - v3(0, 0.035 + 0.08 * size, 0)
    if kind == 'hurricane':
        hurricane(add, lights, P, c, size, frame, light=light)
    else:
        box_lamp(add, lights, P, c, size, frame, light=light)
    return c


# ------------------------------------------------------------------ headgear

def sou_wester(add, P, mat='oilskin', brim=1.0, tilt=0.0):
    """Oilskin storm hat: round crown, wide brim, long sloping back flap."""
    H, R, h = P['head'], head_R(P) @ rot_x(tilt), P['height']
    add(Ellipsoid(H + R @ v3(0, 0.05, -0.012) * h, (0.090 * h, 0.072 * h, 0.098 * h), R), mat, 0.01)
    c = H + R @ v3(0, 0.035, -0.02) * h

    def f(p):
        q = (p - c) @ R / h
        r = np.sqrt(q[:, 0] ** 2 + (q[:, 2] / np.where(q[:, 2] < 0, 1.25, 1.0)) ** 2)
        droop = -0.25 * np.clip(r - 0.08, 0, None) - 0.12 * np.clip(-q[:, 2] - 0.05, 0, None)
        d = np.maximum(np.abs(q[:, 1] - droop) - 0.006, r - 0.16 * brim)
        return d * h
    add(Func(f, c, 0.22 * h * brim), mat, 0.012)


def keeper_cap(add, P, mat='slate', band='brass'):
    """Peaked keeper's cap (flat-topped, short visor)."""
    H, R, h = P['head'], head_R(P), P['height']
    add(Cylinder(H + R @ v3(0, 0.04, -0.01) * h, H + R @ v3(0, 0.10, -0.012) * h, 0.088 * h, 0.012), mat, 0.0)
    add(Torus(H + R @ v3(0, 0.05, -0.01) * h, R[:, 1], 0.088 * h, 0.006), band, 0.0)
    add(Ellipsoid(H + R @ v3(0, 0.045, 0.085) * h, (0.07 * h, 0.008 * h, 0.04 * h), R @ rot_x(0.3)), 'darkiron', 0.0)


def tall_hood(add, P, mat, peak=0.10):
    """Hood with a tall peak: the lighthouse-tower read."""
    add(hood_shell(P, size=1.05, peak=peak), mat, 0.0)


def mantle(add, P, mat, depth=0.17, width=0.16):
    """Round shoulder cape (oilskin storm cape)."""
    add(capelet_shell(P, depth=depth, width=width, sq=2.4), mat, 0.0)


# ------------------------------------------------------------------ ghosts

_BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


class Perforate(Prim):
    """Screen-door translucency: rays through 'pass' supersample cells skip the prim.

    Camera rays are parallel to the view axis, so a ray stays inside its own supersample cell; cells
    picked by an ordered 4x4 Bayer threshold against coverage(p) let the ray through. Each 1x pixel
    covers exactly a 4x4 block, so the result is true partial alpha after the downsample.
    """
    def __init__(self, prim, cam, coverage):
        self.prim, self.cov = prim, coverage
        self.bc, self.br = prim.bc, prim.br
        fwd, right, up = cam.basis()
        self.right, self.up = right, up
        self.cam = cam

    def __call__(self, p):
        d = self.prim(p)
        c = self.cam
        col = np.floor((p @ self.right * c.ppm + c.anchor[0]) * c.ss).astype(np.int64)
        row = np.floor((c.anchor[1] - p @ self.up * c.ppm) * c.ss).astype(np.int64)
        th = _BAYER[row % 4, col % 4]
        cov = self.cov(p) if callable(self.cov) else self.cov
        passing = th >= cov
        return np.where(passing, np.maximum(d, 0.06), d)


def ghostify(parts, cam, coverage):
    return [Part(Perforate(pt.prim, cam, coverage), pt.mat, pt.k) for pt in parts]


def ghost_mats(P, pale=_hex('#c9d0d3'), glow=0.35):
    """Pale grey ghost material set with a soft emissive (gold rim comes from the faction LOOK)."""
    g = glow * (0.4 + 0.6 * P['glow'])
    e = _tone(_hex('#b9c4c8'), g)

    def M(c, spec=0.1):
        return Material(noisy(c, 0.08, 18), spec=spec, gloss=14, emissive=e, rim=1.6, brush=0.06)
    return {
        'ghost': M(pale),
        'ghost_dk': M(_tone(pale, 0.72)),
        'ghost_lt': M(_hex('#e6ebea')),
        'ghost_skin': Material(face_albedo(P, _hex('#d4dbdc'), _hex('#7d8a8f'), eyes=_hex('#ffe9b0')),
                               spec=0.1, gloss=14, emissive=e, rim=1.6, brush=0.02),
    }


# ------------------------------------------------------------------ animation

def flicker_idle(frames_fn, amp=1.0):
    """Wrap a frames() so idle reads as a lamp flicker (stronger glow swing, flame shape steps)."""
    def frames():
        fr = frames_fn()
        out = {}
        for row, lst in fr.items():
            new = []
            for i, (P, o) in enumerate(lst):
                P = dict(P)
                P['flick'] = i
                if row == 'idle':
                    P['glow'] = P['glow'] / [1.0, 0.88, 1.08, 0.94][i] * (1 + amp * np.array([0, -0.38, 0.12, -0.2])[i])
                new.append((P, o))
            out[row] = new
        return out
    return frames


def pole_death(fr, side):
    """Long poles fall away to the side in death instead of spearing into the ground (keeps the lamp in frame)."""
    sx = -1 if side == 'r' else 1
    for i, (P, o) in enumerate(fr['death']):
        if i > 0 and P['item_' + side] is not None:
            P['item_' + side] = norm(v3(sx * [0, 0.45, 0.6, 0.65][i], [1, 0.8, 0.65, 0.6][i], 0.2))
    return fr


def keeper_rows(neutral_pose, attack_style='swing', weapon_side='r', cast_side='l', post=None, pole=None):
    ROWS, fr = humanoid_rows(neutral_pose, attack_style=attack_style, weapon_side=weapon_side, cast_side=cast_side)
    fr2 = flicker_idle(fr)
    if pole is not None:
        fr1 = fr2
        fr2 = lambda: pole_death(fr1(), pole)
    if post is None:
        return ROWS, fr2

    def frames():
        return post(fr2())
    return ROWS, frames


__all__ = [n for n in dir() if not n.startswith('__')]


class Waver(Prim):
    """Sideways sine ripple that grows toward the ground: a ghost's wavering outline."""
    def __init__(self, prim, amp=0.02, freq=9.0, phase=0.0, top=1.8):
        self.prim, self.amp, self.freq, self.phase, self.top = prim, amp, freq, phase, top
        self.bc, self.br = prim.bc, prim.br + amp

    def __call__(self, p):
        t = np.clip((self.top - p[:, 1]) / self.top, 0, 1)
        q = p.copy()
        q[:, 0] += self.amp * t * np.sin(p[:, 1] * self.freq + self.phase)
        q[:, 2] += 0.6 * self.amp * t * np.cos(p[:, 1] * self.freq * 0.7 + self.phase * 1.3)
        return self.prim(q) * 0.9


def ghost_body(parts, cam, P, coverage, amp=0.02):
    """Waver then perforate a list of parts (call on the ghost's own parts only)."""
    ph = P.get('tell', 0.0) * 2 * np.pi + P.get('flick', 0) * 0.0
    return [Part(Perforate(Waver(pt.prim, amp, 9.0, ph), cam, coverage), pt.mat, pt.k) for pt in parts]


__all__ = [n for n in dir() if not n.startswith('__')]


def lens_disc(add, c, axis, r, rim='brass', thick=0.012):
    """Ground-glass lens in a rim, facing along axis."""
    axis = norm(axis)
    add(Ellipsoid(c, (r, thick, r), basis_from(axis)), 'lens', 0.0)
    add(Torus(c, axis, r, 0.010 + r * 0.06), rim, 0.0)


def goggles(add, P, mat='brass', up=0.06):
    H, R, h = P['head'], head_R(P), P['height']
    for sx in (-1, 1):
        c = H + R @ v3(sx * 0.036, up, 0.078) * h
        add(Torus(c, R @ v3(0, 0.4, 1), 0.022, 0.007), mat, 0.0)
        add(Ellipsoid(c, (0.02, 0.02, 0.006), R), 'lens', 0.0)
    add(Torus(H + R @ v3(0, up, -0.005) * h, R @ v3(0, 1, -0.2), 0.088 * h, 0.006), 'leather', 0.0)


__all__ = [n for n in dir() if not n.startswith('__')]

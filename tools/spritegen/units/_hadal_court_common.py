"""Shared Hadal Court helpers: bell hulls, diving-bell helms, stalk lamps, segmented limbs,
cracked pressure-iron / brine-glaze materials, the teal pulse and the sink-into-the-dark death.

Shape language: huge, bottom-heavy bells, domed helms, dark masses with small teal lights.
Vent amber only for vents and the Vent-Priest line.
"""
import numpy as np
from kit.humanoid import *          # noqa: F401,F403  (re-exported for unit files)
from kit.humanoid import finish as _kit_finish
from kit.anim import humanoid_rows, creature_frames, CREATURE_DEFAULTS
from kit.looks import LOOKS, PALETTES
from kit.xform import Xform, Squash, transform_parts, squash_parts
from kit import endstates
from render import Camera, Material, Part, Light, Scene, _hex
from sdf import (v3, norm, basis_from, rot_y, rot_x, rot_z, Sphere, Ellipsoid, Capsule, RoundBox,
                 Cylinder, Torus, Func, smax, smin, fbm, vnoise)
import rig

FACTION = 'hadal_court'
HC = PALETTES[FACTION]
INDIGO = HC['indigo']
TEAL = HC['teal']
BLACK = HC['black']
PIRON = HC['iron']
AMBER = HC['amber']
BRONZE = _hex('#4d5e52')        # bronze-green bell-metal
VERDI = _hex('#5f8a7a')         # verdigris on old bells
BARN = _hex('#8e8c80')          # barnacle crust
HIDE = _hex('#454b66')          # brine-slick hide
FLESH = _hex('#7a7fa6')         # translucent pressure-flesh
ROBE = _hex('#34385c')          # abyss cloth
import dataclasses as _dc
LOOK = _dc.replace(LOOKS[FACTION], key_int=1.4, sky_int=0.36, exposure=1.12, contrast=0.35)

HADAL_DEFAULTS = dict(deflate=0.0, pulse_phase=0.0)


# ------------------------------------------------------------------ pulse

def pulse(P, phase=0.0):
    """Bioluminescent breathing 0.55..1.35, multiplied by the unit's glow and cast flare."""
    t = P.get('tell', 0.0) + phase
    return (0.95 + 0.4 * np.sin(2 * np.pi * t)) * P.get('glow', 1.0) + 0.8 * P.get('cast_glow', 0.0)


def teal_light(pos, P, strength=0.9, radius=0.7, phase=0.0, color=None):
    return Light(pos, color or TEAL, strength * max(pulse(P, phase), 0.0), radius)


# ------------------------------------------------------------------ materials

def _arr(c, n):
    return np.array(c)[None, :].repeat(n, 0)


def cracked_albedo(base, crack=BLACK, freq=9.0, width=0.035, seep=None, barn=0.0, mottle=0.14,
                   patina=None, patina_amt=0.0):
    """Base colour with pressure cracks (iso-lines of noise), optional teal seep in cracks,
    barnacle speckle, patina blotches."""
    def fn(p, n):
        a = _arr(base, len(p)) * (1 - mottle + 2 * mottle * fbm(p, 14.0, 2)[:, None])
        if patina is not None and patina_amt > 0:
            pm = np.clip((fbm(p + 3.1, 7.0, 3) - (1 - patina_amt)) * 5, 0, 1)[:, None]
            a = a * (1 - pm) + np.array(patina)[None, :] * pm
        r1 = np.abs(vnoise(p, freq) - 0.5)
        r2 = np.abs(vnoise(p + 7.7, freq * 2.3) - 0.5)
        cm = (r1 < width) | (r2 < width * 0.6)
        if seep is not None:
            edge = (r1 < width * 1.8) & ~cm
            a[edge] = a[edge] * 0.6 + np.array(seep)[None, :] * 0.4
        a[cm] = crack
        if barn > 0:
            b = fbm(p + 1.3, 38.0, 2) > (1 - 0.45 * barn)
            a[b] = BARN
        return a
    return fn


def banded_albedo(base, band, frame_c, frame_R, spacing=0.22, width=0.035, rivet=None, crack=BLACK,
                  freq=9.0, patina=None, patina_amt=0.0, barn=0.0):
    """Bell-metal with horizontal riveted bands in the bell's local frame (rings every `spacing`)."""
    inner = cracked_albedo(base, crack, freq, 0.012, seep=TEAL, barn=barn, patina=patina, patina_amt=patina_amt)

    def fn(p, n):
        a = inner(p, n)
        q = (p - frame_c) @ frame_R
        y = q[:, 1]
        f = np.mod(-y, spacing)
        m = f < width
        a[m] = np.array(band)[None, :] * (0.9 + 0.2 * fbm(p[m], 20, 1)[:, None])
        if rivet is not None:
            ang = np.arctan2(q[:, 0], q[:, 2])
            rv = m & (np.abs(np.mod(ang * 6, 1.0) - 0.5) < 0.12) & (np.abs(f - width / 2) < width * 0.35)
            a[rv] = rivet
        return a
    return fn


def hadal_mats(P, extra=None, lamp_gain=1.0, amber_gain=0.0):
    g = max(pulse(P), 0.0)
    m = {
        'iron': Material(cracked_albedo(PIRON, freq=8, seep=TEAL, barn=0.25), spec=0.55, gloss=28, metal=0.5, brush=0.05),
        'brine': Material(cracked_albedo(_hex('#363b78'), crack=_hex('#11132a'), freq=8, width=0.012, seep=TEAL), spec=0.9, gloss=55, brush=0.03),
        'hide': Material(cracked_albedo(HIDE, crack=_hex('#0f121c'), freq=6, width=0.02, mottle=0.2), spec=0.7, gloss=40, brush=0.05),
        'flesh': Material(cracked_albedo(FLESH, crack=_hex('#2b2d55'), freq=7, width=0.02, seep=TEAL), spec=0.5, gloss=30, sss=0.5, brush=0.04),
        'robe': Material(lambda p, n: _arr(ROBE, len(p)) * (0.85 + 0.3 * fbm(p, 16, 2)[:, None]), spec=0.04, brush=0.09),
        'chain': Material(_hex('#3c4152'), spec=0.8, gloss=40, metal=0.7),
        'barnacle': Material(cracked_albedo(BARN, crack=_hex('#4e4c45'), freq=30, width=0.06), spec=0.1, brush=0.1),
        'lamp': Material(TEAL, emissive=tuple(np.array(TEAL) * 1.5 * g * lamp_gain), rim=0.0),
        'port': Material(_hex('#1f6d6a'), spec=1.0, gloss=80, emissive=tuple(np.array(TEAL) * 0.55 * g * lamp_gain), rim=0.0),
        'speck': Material(TEAL, emissive=tuple(np.array(TEAL) * 1.1 * g * lamp_gain), rim=0.0),
        'vent': Material(AMBER, emissive=tuple(np.array(_hex('#ffb04a')) * (1.3 + 0.5 * P.get('cast_glow', 0)) * P.get('glow', 1) * max(amber_gain, 0)), rim=0.0),
        'abyss': Material(_hex('#07080d'), spec=0.6, gloss=50, brush=0.0, rim=0.2),
        'skin': Material(cracked_albedo(_hex('#5d628a'), crack=_hex('#2a2c4a'), freq=7, width=0.02), spec=0.4, gloss=25, sss=0.4, brush=0.03),
        'bone': Material(_hex('#a9a593'), spec=0.15, brush=0.06),
        'teeth': Material(_hex('#c9c3ad'), spec=0.4, gloss=30, brush=0.03),
        'maw': Material(_hex('#1a0f18'), spec=0.4, gloss=20),
    }
    if extra:
        m.update(extra)
    return m


def bell_metal(c, R, base=PIRON, band=_hex('#2f3347'), patina=VERDI, patina_amt=0.25, spacing=0.22, barn=0.3, **kw):
    return Material(banded_albedo(base, band, c, R, spacing=spacing, rivet=_hex('#8d93a8'), patina=patina,
                                  patina_amt=patina_amt, barn=barn), spec=0.65, gloss=32, metal=0.55, brush=0.05, **kw)


# ------------------------------------------------------------------ shapes

def bell_hull(c_top, height, r_top, r_bot, R=None, power=1.7, sz=0.82, lip=0.025, ribs=0.0, ribs_n=10,
              open_bottom=False, thick=0.03, crack=0.0):
    """Bell from c_top downward along -R[:,1]. r(t) = r_top + (r_bot - r_top) t^power, lip flare at the hem.
    ribs adds vertical flutes (bell-robe folds). Solid unless open_bottom (then a shell)."""
    R = np.eye(3) if R is None else R

    def f(p):
        q = (p - c_top) @ R
        y = -q[:, 1]
        t = np.clip(y / height, 0, 1)
        r = r_top + (r_bot - r_top) * t ** power
        r = r + lip * np.clip((t - 0.86) / 0.14, 0, 1) ** 2
        ang = np.arctan2(q[:, 0], q[:, 2])
        if ribs:
            r = r * (1 + ribs * t * np.sin(ang * ribs_n))
        if crack:
            r = r - crack * (np.abs(vnoise(p, 6.0) - 0.5) < 0.03)
        rad = np.sqrt(q[:, 0] ** 2 + (q[:, 2] / sz) ** 2)
        slope = (r_bot - r_top) / height * power
        d = (rad - r) / np.sqrt(1 + slope * slope * 0.5)
        if open_bottom:
            d = np.abs(d + thick) - thick
        d = smax(d, y - height, 0.012)
        d = smax(d, -y, 0.02)
        return d
    return Func(f, c_top - R[:, 1] * height * 0.5, np.hypot(height * 0.5, max(r_top, r_bot) + lip) + 0.03)


def frame_for(P, up=None):
    """Torso frame (columns x, y-up, z) following pelvis->neck."""
    up = norm(P['neck'] - P['pelvis']) if up is None else up
    return basis_from(up, (0, 0, 1))


def dome_helm(add, c, R, r=0.16, mat='helm', port='port', rim='iron', ports=1, crest=False, h=1.0, crack=False):
    """Diving-bell helm: dome, collar ring, front porthole(s) of dim teal glass with a brass-iron bezel."""
    up, fwd = R[:, 1], R[:, 2]
    add(Ellipsoid(c + up * 0.02 * h, (r, r * 1.08 * h, r * 0.98), R), mat, 0.0)
    add(Cylinder(c - up * (r * 0.75), c - up * (r * 0.45), r * 1.06, 0.012), rim, 0.02)
    offs = [0.0] if ports == 1 else [-0.42, 0.42] if ports == 2 else [-0.6, 0.0, 0.6]
    for o in offs:
        d = norm(fwd * np.cos(o) + R[:, 0] * np.sin(o) * 0.9 + up * 0.02)
        pc = c + d * (r * 0.92) + up * (0.0 if ports == 1 else 0.01)
        pr = r * (0.42 if ports == 1 else 0.27)
        add(Cylinder(pc - d * 0.015, pc + d * 0.02, pr, 0.008), port, 0.0)
        add(Torus(pc + d * 0.01, d, pr, 0.014), rim, 0.0)
        if ports == 1:
            add(Capsule(pc - R[:, 0] * pr + d * 0.02, pc + R[:, 0] * pr + d * 0.02, 0.008), rim, 0.0)
    if crest:
        add(Capsule(c + up * r * 1.05 - fwd * r * 0.7, c + up * r * 1.15 + fwd * r * 0.3, 0.02, 0.015), rim, 0.02)


def stalk_lamp(add, base, d1, d2, l1, l2, bulb=0.045, mat='hide', lamp='lamp', r0=0.02, r1=0.011):
    """Two-segment fleshy stalk ending in a bulb. Returns bulb centre."""
    a = base + norm(d1) * l1
    b = a + norm(d2) * l2
    add(Capsule(base, a, r0, (r0 + r1) / 2), mat, 0.01)
    add(Capsule(a, b, (r0 + r1) / 2, r1), mat, 0.01)
    add(Sphere(b + norm(d2) * bulb * 0.6 - v3(0, bulb * 0.7, 0), bulb), lamp, 0.0)
    return b + norm(d2) * bulb * 0.6 - v3(0, bulb * 0.7, 0)


def specks(add, pts, r=0.012, mat='speck'):
    for q in pts:
        add(Sphere(q, r), mat, 0.0)


def seg_limb(add, pts, radii, mat='hide', joint='iron', k=0.0, joint_scale=1.15):
    """Segmented limb through pts with knuckle balls at joints."""
    for i in range(len(pts) - 1):
        add(Capsule(pts[i], pts[i + 1], radii[i], radii[i + 1]), mat, k)
        if 0 < i + 1 < len(pts) - 1 and joint:
            add(Sphere(pts[i + 1], radii[i + 1] * joint_scale), joint, 0.0)


def barnacles(add, center, R, n=8, spread=0.2, size=0.022, seed=3, mat='barnacle', up_bias=0.5):
    rng = np.random.default_rng(seed)
    for i in range(n):
        a = rng.uniform(0, 2 * np.pi)
        q = center + R @ v3(np.cos(a) * spread * rng.uniform(0.6, 1), rng.uniform(-0.5, 0.5) * spread * up_bias,
                            np.sin(a) * spread * rng.uniform(0.6, 1))
        s = size * rng.uniform(0.6, 1.3)
        add(Cylinder(q - v3(0, s * 0.3, 0), q + v3(0, s * 0.6, 0), s, s * 0.4), mat, 0.004)


# ------------------------------------------------------------------ finish (deflate + sink into the dark)

def hadal_finish(P, parts, mats, lights=(), deflate_pivot=(0, 0, 0), add=None):
    """Applies P['deflate'] (collapsing bell squash) and P['sink'] (sinking into a black pool with
    teal motes rising) before the kit finish, which gutters every light as P['end'] -> 1."""
    df = P.get('deflate', 0.0)
    if df > 0:
        parts[:] = squash_parts(parts, sy=1 - 0.42 * df, sxz=1 + 0.18 * df, pivot=deflate_pivot)
    sink = P.get('sink', 0.0)
    e = P.get('end', 0.0)
    if sink > 0:
        parts[:] = endstates.sink_parts(parts, sink)
        lights = [Light(L.pos + v3(0, -sink, 0), L.color, L.intensity, L.radius) for L in lights]
    if e > 0:
        r = 0.25 + 0.4 * e
        parts.append(Part(Ellipsoid(v3(0, 0.0, 0.04), (r, 0.01, r * 0.85)), 'abyss', 0.0))
        rng = np.random.default_rng(7)
        if e < 1.0 or True:
            for i in range(5):
                a = rng.uniform(0, 6.28)
                rr = rng.uniform(0.1, 0.35)
                parts.append(Part(Sphere(v3(np.cos(a) * rr, 0.08 + rng.uniform(0, 0.5) * e + 0.2 * e, np.sin(a) * rr * 0.8),
                                         0.011 * (1.2 - 0.5 * e)), 'mote', 0.0))
        mats = dict(mats)
        mats['mote'] = Material(TEAL, emissive=tuple(np.array(TEAL) * (1.4 * (1 - 0.6 * e))), rim=0.0)
    P2 = dict(P)
    P2['sink'] = 0.0
    sc = _kit_finish(P2, FACTION, parts, mats, lights, end_style='sink')
    if sink > 0:
        sc.ground_clip = True
    return sc


def with_death(frames_fn, deflate=(0, 0, 0.35, 0.8), sink=None):
    """Wrap a frames() fn so death frames also deflate (and optionally override sink depths)."""
    def frames():
        fr = frames_fn()
        for i, (P, o) in enumerate(fr['death']):
            P['deflate'] = deflate[i]
            if sink is not None:
                P['sink'] = sink[i]
        return fr
    return frames


def hpose(height, build):
    P = base_pose(height, build)
    P.update(HADAL_DEFAULTS)
    return P


# ------------------------------------------------------------------ creatures

def creature_pose(**kw):
    P = dict(CREATURE_DEFAULTS)
    P.update(HADAL_DEFAULTS)
    P.update(kw)
    return P


def creature_place(parts, P, pivot=(0, 0, 0), lean_axis='x'):
    """Whole-body lean (about the ground pivot), bob and squash for creature channels."""
    out = squash_parts(parts, sy=P['squash'], sxz=1 + (1 - P['squash']) * 0.5, pivot=pivot)
    out = transform_parts(out, R=rot_x(P['lean'] * 0.6), t=(0, P['bob'], 0), pivot=pivot)
    return out


def creature_rows(base, sink=(0, 0, 0.12, 0.35), deflate=(0, 0, 0, 0), extra=None):
    """creature_frames with Hadal death (sink + lights out) and optional per-row tweaks."""
    def ov(rows):
        for i, (P, o) in enumerate(rows['death']):
            P['sink'] = sink[i]
            P['deflate'] = deflate[i]
        if extra:
            extra(rows)
        return rows
    f = creature_frames(base, ov)
    from kit.anim import ROWS
    return ROWS, f




def brute_limbs(P, add, mat='hide', arm=(0.08, 0.075, 0.07), fist=0.075, leg=(0.10, 0.08), hand_mat=None):
    """Thicker arms, fists and thighs over the kit body for heavy Court bodies."""
    for s in ('r', 'l'):
        sh, el, wr = P['sh_' + s], P['el_' + s], P['wr_' + s]
        add(Capsule(sh, el, arm[0], arm[1]), mat, 0.03)
        add(Capsule(el, wr, arm[1], arm[2]), mat, 0.03)
        add(Sphere(wr + norm(wr - el) * fist * 0.8, fist), hand_mat or mat, 0.02)
        if leg:
            add(Capsule(P['hip_' + s], P['kn_' + s], leg[0], leg[1]), mat, 0.03)


def chain_links(add, a, b, n=6, r=0.022, mat='chain', sag=0.0):
    for i in range(n):
        t = (i + 0.5) / n
        q = a + (b - a) * t - v3(0, sag * np.sin(np.pi * t), 0)
        d = norm(b - a)
        ax = norm(np.cross(d, v3(0, 1, 0))) if i % 2 else v3(0, 1, 0)
        add(Torus(q, ax, r, r * 0.32), mat, 0.0)


__all__ = [n for n in dir() if not n.startswith('__')]

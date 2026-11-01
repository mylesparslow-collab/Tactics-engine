"""Humanoid kit: a posable body, costume pieces, held props and the faction finish.

A unit file using the kit looks like:

    from kit.humanoid import *
    UNIT_ID = 'salt_concord_brineguard'; FACTION = 'salt_concord'; LOOK = LOOKS[FACTION]
    C = Costume(skirt='tabard', head='helm', ...)
    def neutral_pose(): P = base_pose(); P['item_r'] = ...; return P
    def build(P):
        parts, add = new_parts()
        body(P, add, C)
        held(P, add, 'r', 'spear', ...)
        mats = {...}
        return finish(P, FACTION, parts, mats, lights=[])
    ROWS, frames = rows_for(neutral_pose, style='thrust')        # from kit.anim

Conventions: metres, y up, figure faces +z, its RIGHT hand is -x (camera side), LEFT is +x.
An adult is ~1.7 m tall at height=1.0. The camera shows ~2.1 m of height in the 96x112 frame.
"""
from dataclasses import dataclass, field
import numpy as np
from sdf import (v3, norm, basis_from, rot_y, rot_x, rot_z, Sphere, Ellipsoid, Capsule, RoundBox,
                 Cylinder, Torus, Func, Subtract, Union, smax, smin, fbm, vnoise)
from render import Material, Part, Light, Scene, _hex
from kit.looks import LOOKS, PALETTES
from kit import endstates
import rig

W = PALETTES['world']


# ------------------------------------------------------------------ pose

def base_pose(height=1.0, build=1.0):
    """Relaxed standing pose. height scales vertically, build scales shoulder/hip width and girth."""
    h, b = height, build

    def J(x, y, z):
        return v3(x * b, y * h, z)
    P = dict(
        height=h, build=b,
        pelvis=J(0.0, 0.94, 0.0), chest=J(0.0, 1.27, -0.005), neck=J(0.0, 1.46, 0.0),
        head=J(0.0, 1.585, 0.015), head_yaw=np.radians(-10), head_pitch=np.radians(-2),
        sh_r=J(-0.185, 1.415, -0.01), el_r=J(-0.235, 1.15, -0.03), wr_r=J(-0.225, 0.93, 0.04),
        sh_l=J(0.185, 1.415, -0.01), el_l=J(0.235, 1.15, -0.03), wr_l=J(0.225, 0.93, 0.04),
        hip_r=J(-0.085, 0.92, 0.0), kn_r=J(-0.095, 0.50, 0.01), an_r=J(-0.10, 0.085, -0.02),
        hip_l=J(0.085, 0.92, 0.0), kn_l=J(0.12, 0.50, 0.07), an_l=J(0.135, 0.085, 0.07),
        foot_r_yaw=np.radians(-18), foot_l_yaw=np.radians(12),
        # held items: direction from the hand toward the item's business end, or None
        item_r=None, item_l=None,
        skirt_sway=0.0,     # hem swing -1..1
        breathe=0.0,
        tell=0.0,           # idle faction tell phase 0..1 (unit decides what it drives)
        glow=1.0,           # unit light / lamp strength multiplier
        cast_glow=0.0,      # 0..1 casting flare
        fx=0.0,             # attack effect (muzzle flash, spark) 0..1
        end=0.0,            # death end state 0..1 (see finish())
        sink=0.0,           # metres sunk into the ground (death)
    )
    return P


def head_R(P):
    return rot_y(P['head_yaw']) @ rot_x(-P['head_pitch'])


def hand_pos(P, s):
    d = norm(P['wr_' + s] - P['el_' + s])
    return P['wr_' + s] + d * 0.045


def new_parts():
    parts = []

    def add(prim, mat, k=0.0):
        parts.append(Part(prim, mat, k))
    return parts, add


# ------------------------------------------------------------------ costume

@dataclass
class Costume:
    """Material names refer to keys in the unit's materials dict."""
    top: str = 'top'            # torso
    sleeve: str = 'top'
    legs: str = 'legs'
    boot: str = 'boot'
    hand: str = 'glove'         # use 'skin' for bare hands
    skin: str = 'skin'
    hair: str = 'hair'
    skirt: str = 'coat'         # 'coat' (open front) | 'robe' (closed, long) | 'tabard' | None
    skirt_mat: str = 'top'
    hem: float = 0.30           # hem height in metres at height 1.0
    flare: float = 1.0          # skirt flare multiplier
    head: str = 'hair'          # 'hair' | 'hood' | 'helm' | 'cap' | 'bald' | 'none'
    head_mat: str = 'hair'      # material for hood / helm / cap
    hair_style: str = 'short'   # 'short' | 'bob' | 'tail' | 'long'
    belt: str = 'leather'       # or None
    boots_tall: bool = True
    girth: float = 1.0          # torso thickness
    neck_len: float = 1.0


def face_albedo(P, skin, hair, eyes=_hex('#2a1d1a'), lips=_hex('#a8584c'), brows=True, beard=None):
    """Material fn painting eyes, brows, lips, cheeks (and optional beard colour) in head space."""
    def fn(p, n):
        q = (p - P['head']) @ head_R(P)
        q = q / P['height']
        base = np.array(skin)[None, :].repeat(len(p), 0)
        front = q[:, 2] > 0.04
        for sx in (-1, 1):
            e = ((q[:, 0] - sx * 0.034) / 0.017) ** 2 + ((q[:, 1] - 0.005) / 0.009) ** 2
            base[(e < 1) & front] = eyes
            if brows:
                b = (((q[:, 0] - sx * 0.036) / 0.024) ** 2 + ((q[:, 1] - 0.030) / 0.006) ** 2 < 1) & front
                base[b] = hair
        cheek = np.exp(-(((np.abs(q[:, 0]) - 0.045) / 0.03) ** 2 + ((q[:, 1] + 0.03) / 0.03) ** 2))
        base = base * (1 - 0.15 * cheek[:, None]) + np.array(_hex('#d77a6a'))[None, :] * 0.15 * cheek[:, None]
        lip = ((q[:, 0] / 0.022) ** 2 + ((q[:, 1] + 0.058) / 0.007) ** 2 < 1) & front
        base[lip] = lips
        if beard is not None:
            bm = (q[:, 1] < -0.03) & (q[:, 2] > -0.01)
            base[bm & ~lip] = beard
        return base
    return fn


def skirt_shell(P, C, opening=0.52):
    """Flared cloth shell from the waist to the hem with folds. opening = front split (radians), 0 = closed."""
    pel = P['pelvis']
    h, b = P['height'], P['build']
    sway = P['skirt_sway']
    top = 1.02 * h
    hem0 = C.hem * h

    def f(p):
        dy = pel[1] - 0.94 * h
        x = (p[:, 0] - pel[0])
        z = (p[:, 2] - pel[2])
        y = p[:, 1] - dy
        t = np.clip((top - y) / (top - hem0), 0, 1.2)
        x = x - sway * 0.05 * t * t
        theta = np.arctan2(x, z)
        rx = (0.135 * b + 0.16 * C.flare * t ** 1.2) * C.girth ** 0.5
        rz = (0.100 * b + 0.12 * C.flare * t ** 1.2) * C.girth ** 0.5
        fold = 1 + 0.07 * t * np.sin(theta * 7 + 0.6) + 0.03 * t * np.sin(theta * 13 + 2.0)
        rad = np.sqrt((x / rx) ** 2 + (z / rz) ** 2)
        d = (rad - fold) * np.minimum(rx, rz) * 0.8
        hem = hem0 + 0.02 * np.sin(theta * 3 + 1.0)
        d = np.maximum(d, np.maximum(y - top, hem - y))
        d = np.maximum(d, 0.004 - p[:, 1])
        d = np.abs(d + 0.008) - 0.010
        if opening > 0:
            w = np.clip((top - 0.02 * h - y) / (0.70 * h), 0, 1) ** 0.8 * opening
            wedge = (np.abs(theta) - w) * np.sqrt(x * x + z * z)
            d = smax(d, -wedge, 0.01)
        return d
    return Func(f, (pel[0], pel[1] - 0.28 * h, pel[2]), 0.5 * h * max(1.0, C.flare))


def tabard_panels(P, C, width=0.15, mat=None):
    """Flat front and back panels hanging from the chest to below the knee (Concord tabard)."""
    pel, ch = P['pelvis'], P['chest']
    h = P['height']
    out = []
    for zs in (1, -1):
        top = ch + v3(0, 0.12 * h, zs * 0.10)
        bot = v3(pel[0], C.hem * h + 0.05, pel[2] + zs * (0.13 + 0.05 * P['skirt_sway'] * zs))
        mid = (top + bot) / 2
        R = basis_from(top - bot, (0, 0, 1))
        out.append(RoundBox(mid, (width * P['build'], np.linalg.norm(top - bot) / 2, 0.008), 0.006, R))
    return out


def capelet_shell(P, depth=0.19, width=0.215, sq=4.0):
    """Short shoulder cape. sq = superellipse power (4 = squared Concord, 2 = round)."""
    nk = P['neck']
    b = P['build']

    def f(p):
        q = p - (nk + v3(0, 0.0, -0.012))
        y = q[:, 1]
        t = np.clip(-y / depth, 0, 1)
        rx = (0.078 + width * t ** 0.55) * b
        rz = (0.068 + 0.095 * t ** 0.6) * b
        fold = 1 + 0.025 * t * np.sin(np.arctan2(q[:, 0], q[:, 2]) * 9)
        rad = ((np.abs(q[:, 0]) / rx) ** sq + (np.abs(q[:, 2]) / rz) ** sq) ** (1 / sq)
        d = (rad - fold) * np.minimum(rx, rz) * 0.7
        d = np.maximum(d, np.maximum(y, -depth - y))
        return np.abs(d + 0.007) - 0.009
    return Func(f, nk + v3(0, -0.09, 0), 0.32 * b)


def hood_shell(P, size=1.0, peak=0.04, droop=0.0):
    """Hood around the head, open at the face, falling onto the shoulders."""
    H = P['head']
    R = head_R(P)
    s = size * P['height']

    def f(p):
        q = (p - H) @ R / s
        q = q - np.array([0, 0.01, -0.012])
        # outer hood: ellipsoid stretched up into a soft peak at the back
        e = np.sqrt((q[:, 0] / 0.11) ** 2 + ((q[:, 1] - peak * np.clip(-q[:, 2] / 0.1, 0, 1)) / 0.13) ** 2
                    + (q[:, 2] / 0.12) ** 2)
        d = (e - 1.0) * 0.11
        d = np.abs(d + 0.006) - 0.008
        # face opening
        fo = np.sqrt((q[:, 0] / 0.07) ** 2 + ((q[:, 1] + 0.005) / 0.085) ** 2) - 1.0
        cut = np.maximum(fo * 0.07, 0.03 - q[:, 2])
        d = smax(d, -cut, 0.01)
        d = np.maximum(d, -0.17 - q[:, 1] - droop)
        return d * s
    return Func(f, H, 0.2 * s)


def body(P, add, C: Costume):
    """Legs, boots, torso, arms, hands, neck, head (hair / hood / helm) for a humanoid pose."""
    h, b, g = P['height'], P['build'], C.girth
    br = P['breathe']
    # legs and boots
    for s in ('r', 'l'):
        hip, kn, an = P['hip_' + s], P['kn_' + s], P['an_' + s]
        add(Capsule(hip, kn, 0.068 * b, 0.052 * b), C.legs, 0.02)
        if C.boots_tall:
            add(Capsule(kn + (an - kn) * 0.05, an, 0.050 * b, 0.044 * b), C.boot, 0.0)
            add(Capsule(kn + v3(0, 0.03, 0.0), kn + v3(0, -0.02, 0.01), 0.060 * b, 0.056 * b), C.boot, 0.01)
        else:
            add(Capsule(kn, an, 0.048 * b, 0.042 * b), C.legs, 0.01)
            add(Capsule(an + v3(0, 0.05, 0), an, 0.047 * b, 0.046 * b), C.boot, 0.0)
        fd = rot_y(P['foot_%s_yaw' % s]) @ v3(0, 0, 1)
        toe = an + fd * 0.15 * h + v3(0, -0.045, 0)
        add(Capsule(an + v3(0, -0.035, -0.03), toe, 0.048 * b, 0.036 * b), C.boot, 0.03)
    # torso
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    add(Ellipsoid(ch, ((0.165 + br * 0.004) * b * g ** 0.5, 0.19 * h, (0.105 + br * 0.006) * b * g)), C.top, 0.0)
    add(Ellipsoid(pel + v3(0, 0.12 * h, 0), (0.135 * b * g ** 0.5, 0.13 * h, 0.095 * b * g)), C.top, 0.06)
    if C.skirt == 'coat':
        add(skirt_shell(P, C, 0.52), C.skirt_mat, 0.0)
    elif C.skirt == 'robe':
        add(skirt_shell(P, C, 0.0), C.skirt_mat, 0.0)
    elif C.skirt == 'tabard':
        for pr in tabard_panels(P, C):
            add(pr, C.skirt_mat, 0.0)
    if C.belt:
        def belt(p, pel=pel):
            q = p - (pel + v3(0, 0.08 * h, 0.002))
            e = np.sqrt((q[:, 0] / (0.142 * b * g ** 0.5)) ** 2 + (q[:, 2] / (0.104 * b * g)) ** 2) - 1.0
            return np.maximum(np.abs(e * 0.104) - 0.006, np.abs(q[:, 1]) - 0.022)
        add(Func(belt, pel + v3(0, 0.08 * h, 0), 0.22 * b), C.belt, 0.0)
    # arms
    for s in ('r', 'l'):
        sh, el, wr = P['sh_' + s], P['el_' + s], P['wr_' + s]
        sx = -1 if s == 'r' else 1
        add(Capsule(sh + v3(-sx * 0.02, -0.04, 0), el, 0.056 * b, 0.048 * b), C.sleeve, 0.03)
        add(Capsule(el, wr, 0.048 * b, 0.040 * b), C.sleeve, 0.02)
        d = norm(wr - el)
        add(Ellipsoid(wr + d * 0.045, (0.034 * b, 0.045 * b, 0.030 * b), basis_from(d, (0, 0, 1))), C.hand, 0.01)
    # neck and head
    H = P['head']
    R = head_R(P)
    add(Capsule(nk + v3(0, -0.02, 0), H + v3(0, -0.07 * h, -0.01), 0.04 * b), C.skin, 0.0)
    if C.head != 'none':
        add(Ellipsoid(H, (0.078 * h, 0.097 * h, 0.088 * h), R), C.skin, 0.0)
        add(Ellipsoid(H + R @ v3(0, -0.05, 0.022) * h, (0.056 * h, 0.05 * h, 0.062 * h), R), C.skin, 0.03)
        add(Capsule(H + R @ v3(0, 0.0, 0.078) * h, H + R @ v3(0, -0.028, 0.092) * h, 0.010, 0.013), C.skin, 0.01)
    if C.head == 'hair' or C.head == 'cap':
        hair(P, add, C.hair, C.hair_style)
    if C.head == 'hood':
        add(hood_shell(P), C.head_mat, 0.0)
    elif C.head == 'helm':
        add(Ellipsoid(H + R @ v3(0, 0.035, -0.01) * h, (0.092 * h, 0.085 * h, 0.098 * h), R), C.head_mat, 0.0)
        add(Cylinder(H + R @ v3(0, 0.005, -0.01) * h, H + R @ v3(0, 0.02, -0.01) * h, 0.118 * h, 0.006), C.head_mat, 0.0)
    elif C.head == 'cap':
        add(Ellipsoid(H + R @ v3(0, 0.055, -0.01) * h, (0.088 * h, 0.05 * h, 0.094 * h), R), C.head_mat, 0.01)
        add(Cylinder(H + R @ v3(0, 0.03, 0.05) * h, H + R @ v3(0, 0.038, 0.07) * h, 0.07 * h, 0.004), C.head_mat, 0.0)


def hair(P, add, mat, style='short'):
    H, R, h = P['head'], head_R(P), P['height']
    add(Ellipsoid(H + R @ v3(0, 0.038, -0.03) * h, (0.080 * h, 0.074 * h, 0.080 * h), R), mat, 0.012)
    add(Ellipsoid(H + R @ v3(0, 0.062, 0.02) * h, (0.07 * h, 0.035 * h, 0.06 * h), R), mat, 0.02)
    if style in ('bob', 'long', 'tail'):
        for sx in (-1, 1):
            add(Ellipsoid(H + R @ v3(sx * 0.068, 0.0, 0.0) * h, (0.022 * h, 0.06 * h, 0.045 * h), R), mat, 0.02)
    if style == 'tail':
        a = H + R @ v3(0, 0.0, -0.085) * h
        add(Capsule(a, a + v3(0.02, -0.17, -0.05) * h, 0.030, 0.014), mat, 0.02)
        add(Sphere(a, 0.034), mat, 0.01)
    if style == 'long':
        a = H + R @ v3(0, 0.0, -0.06) * h
        add(Ellipsoid(a + v3(0, -0.12, -0.02) * h, (0.08 * h, 0.14 * h, 0.04 * h), R), mat, 0.03)


# ------------------------------------------------------------------ held props

def held(P, add, side, kind, shaft='wood', head='iron', below=0.0, above=None, glow_mat=None):
    """Attach a prop to a hand. P['item_<side>'] is the direction toward its business end.

    kinds: spear, pike, blade, knife, staff, club, hammer, axe, hook, pistol, long_gun, sling,
           lantern_pole, torch. `below`/`above` override how far the prop extends past the hand.
    Returns (butt, tip) world points so units can hang extra detail on the prop.
    """
    d = P['item_' + side]
    if d is None:
        return None
    d = norm(d)
    g = hand_pos(P, side)
    L = dict(spear=(0.85, 1.05), pike=(1.0, 1.5), blade=(0.08, 0.68), knife=(0.06, 0.30), staff=(1.0, 0.9),
             club=(0.08, 0.62), hammer=(0.15, 0.80), axe=(0.12, 0.75), hook=(0.6, 1.1), pistol=(0.04, 0.32),
             long_gun=(0.40, 0.85), sling=(0.0, 0.45), lantern_pole=(0.9, 0.95), torch=(0.10, 0.45))[kind]
    lb = below if below else L[0]
    la = above if above is not None else L[1]
    butt, tip = g - d * lb, g + d * la
    side_v = norm(np.cross(d, v3(0, 1, 0.2)))
    if kind in ('spear', 'pike'):
        add(Capsule(butt, tip - d * 0.14, 0.016), shaft, 0.0)
        add(Capsule(tip - d * 0.16, tip, 0.030, 0.003), head, 0.0)
        add(Cylinder(tip - d * 0.19, tip - d * 0.15, 0.022, 0.004), head, 0.0)
    elif kind in ('blade', 'knife'):
        r = 0.016 if kind == 'blade' else 0.012
        add(Capsule(g - d * lb, g + d * 0.06, 0.011), 'leather', 0.0)
        add(Sphere(g - d * (lb + 0.01), 0.016), head if head != 'steel' else 'iron', 0.0)
        add(Capsule(g + d * 0.065 - side_v * 0.055, g + d * 0.065 + side_v * 0.055, 0.010), head if head != 'steel' else 'iron', 0.0)
        add(Capsule(g + d * 0.08, tip, r, 0.004), 'steel', 0.0)
    elif kind == 'staff':
        add(Capsule(butt, tip, 0.018, 0.016), shaft, 0.0)
        add(Sphere(tip, 0.03), head, 0.0)
    elif kind == 'club':
        add(Capsule(butt, tip, 0.020, 0.045), shaft, 0.01)
    elif kind == 'hammer':
        add(Capsule(butt, tip, 0.016), shaft, 0.0)
        add(RoundBox(tip, (0.10, 0.05, 0.05), 0.01, basis_from(side_v, d)), head, 0.0)
    elif kind == 'axe':
        add(Capsule(butt, tip, 0.016), shaft, 0.0)
        add(RoundBox(tip - d * 0.05 + side_v * 0.06, (0.07, 0.06, 0.008), 0.006, basis_from(d, side_v)), head, 0.0)
    elif kind == 'hook':
        add(Capsule(butt, tip, 0.016), shaft, 0.0)
        c = tip + side_v * 0.06
        add(Torus(c, np.cross(d, side_v), 0.06, 0.012), head, 0.0)
    elif kind == 'pistol':
        add(Capsule(g - d * 0.02 - v3(0, 0.05, 0), g, 0.020), shaft, 0.01)
        add(Cylinder(g, tip, 0.018, 0.004), head, 0.0)
    elif kind == 'long_gun':
        add(Capsule(butt, g + d * 0.1, 0.028, 0.022), shaft, 0.01)
        add(Cylinder(g, tip, 0.020, 0.004), head, 0.0)
        add(Cylinder(tip - d * 0.03, tip + d * 0.01, 0.034, 0.006), head, 0.0)   # flared muzzle
    elif kind == 'sling':
        add(Capsule(g, tip, 0.006), 'leather', 0.0)
        add(Sphere(tip, 0.028), head, 0.0)
    elif kind == 'lantern_pole':
        add(Capsule(butt, tip, 0.016), shaft, 0.0)
        lc = tip + side_v * 0.05 - v3(0, 0.09, 0)
        add(Capsule(tip, tip + side_v * 0.06, 0.008), head, 0.0)
        lantern(add, lc, head, glow_mat or 'glass')
    elif kind == 'torch':
        add(Capsule(butt, tip, 0.020, 0.024), shaft, 0.0)
        add(Ellipsoid(tip + d * 0.04, (0.035, 0.06, 0.035)), glow_mat or 'flame', 0.0)
    if P['fx'] > 0 and kind in ('pistol', 'long_gun'):
        add(Ellipsoid(tip + d * 0.07, (0.05 * P['fx'], 0.05 * P['fx'], 0.05 * P['fx'])), 'flash', 0.0)
    return butt, tip


def lantern(add, c, frame='brass', glass='glass', size=1.0, R=None):
    """Box lantern: emissive glass block, frame caps and corner rods. Add a Light at c yourself."""
    R = np.eye(3) if R is None else R
    s = size
    add(RoundBox(c, (0.034 * s, 0.048 * s, 0.034 * s), 0.006, R), glass, 0.0)
    add(RoundBox(c + R[:, 1] * 0.055 * s, (0.040 * s, 0.010 * s, 0.040 * s), 0.006, R), frame, 0.0)
    add(RoundBox(c - R[:, 1] * 0.055 * s, (0.040 * s, 0.009 * s, 0.040 * s), 0.006, R), frame, 0.0)
    for cx in (-1, 1):
        for cz in (-1, 1):
            q = c + R @ v3(cx * 0.036, 0, cz * 0.036) * s
            add(Capsule(q - R[:, 1] * 0.05 * s, q + R[:, 1] * 0.05 * s, 0.0055 * s), frame, 0.0)
    add(Cylinder(c + R[:, 1] * 0.06 * s, c + R[:, 1] * 0.08 * s, 0.018 * s, 0.005), frame, 0.0)


def shield(P, add, side='l', shape='tower', mat='shield', rim='iron', size=1.0):
    """Shield strapped to a forearm, facing out and forward. shape: tower | round | kite."""
    el, wr = P['el_' + side], P['wr_' + side]
    sx = -1 if side == 'r' else 1
    c = (el + wr) / 2 + v3(sx * 0.06, 0, 0.05)
    up = norm(wr - el) * 0.3 + v3(0, 1, 0)
    out = norm(v3(sx * 0.6, 0, 1.0))
    R = basis_from(up, out)
    if shape == 'tower':
        add(RoundBox(c, (0.15 * size, 0.30 * size, 0.012), 0.012, R), mat, 0.0)
        add(RoundBox(c - R[:, 2] * 0.004, (0.165 * size, 0.315 * size, 0.008), 0.01, R), rim, 0.0)
    elif shape == 'round':
        add(Cylinder(c - out * 0.012, c + out * 0.012, 0.2 * size, 0.01), mat, 0.0)
        add(Torus(c, out, 0.2 * size, 0.012), rim, 0.0)
        add(Sphere(c + out * 0.015, 0.035), rim, 0.0)
    elif shape == 'kite':
        def f(p):
            q = (p - c) @ R
            y = q[:, 1] / size
            half = np.where(y > 0, 0.16, 0.16 * np.clip(1 + y / 0.36, 0, 1))
            d = np.maximum(np.abs(q[:, 0]) - half * size, np.maximum(y - 0.14, -0.36 - y) * size)
            return np.maximum(d, np.abs(q[:, 2]) - 0.012) - 0.004
        add(Func(f, c, 0.4 * size), mat, 0.0)


# ------------------------------------------------------------------ finishing

DEFAULT_MATS = lambda: {
    'leather': Material(W['leather'], spec=0.18, gloss=20, brush=0.06),
    'boot': Material(W['boot'], spec=0.25, gloss=24, brush=0.05),
    'glove': Material(_hex('#3e2c22'), spec=0.15, gloss=18, brush=0.04),
    'wood': Material(W['wood'], spec=0.1, gloss=12, brush=0.08),
    'iron': Material(W['iron'], spec=0.7, gloss=30, metal=0.7, brush=0.05),
    'steel': Material(W['steel'], spec=1.0, gloss=60, metal=0.6, brush=0.02),
    'brass': Material(_hex('#b8924a'), spec=0.9, gloss=40, metal=0.9, brush=0.04),
    'glass': Material(W['lamp'], spec=0.3, gloss=30, emissive=W['lamp'], rim=0.0),
    'flame': Material(_hex('#ffb347'), emissive=_hex('#ffb347'), rim=0.0),
    'flash': Material(_hex('#fff2c0'), emissive=_hex('#fff2c0'), rim=0.0),
    'brine': endstates.brine_material(),
    'scrap': Material(_hex('#8a4a2c'), spec=0.3, gloss=20, brush=0.1),
    'calcite': Material(_hex('#f1e9df'), spec=0.05, brush=0.06),
}

END_COLORS = {'salt_concord': _hex('#e2ddcf'), 'reef_ascendant': _hex('#f1e9df')}


def finish(P, faction, parts, mats, lights=(), add=None, end_style=None):
    """Merge default materials, apply glow/cast flare, the faction death end state, and build the Scene.

    end_style overrides the faction default: 'crust' | 'sink' | 'pool' | 'scrap' | 'gutter' | 'crumble'.
    The unit's own pose drives P['end'] (0..1) and P['sink'] (metres) through kit.anim death rows.
    """
    m = DEFAULT_MATS()
    m.update(mats)
    if add is None:
        def add(prim, mat, k=0.0):
            parts.append(Part(prim, mat, k))
    style = end_style or {'salt_concord': 'crust', 'hadal_court': 'sink', 'returning_tide': 'pool',
                          'salvage_compact': 'scrap', 'reef_ascendant': 'crumble',
                          'lanternkeepers': 'gutter'}[faction]
    e = P['end']
    ground_clip = False
    if P['sink'] > 0:
        parts[:] = endstates.sink_parts(parts, P['sink'])
        ground_clip = True
    if e > 0:
        if style == 'crust':
            m = endstates.crusted(m, END_COLORS['salt_concord'], e)
        elif style == 'crumble':
            m = endstates.crusted(m, END_COLORS['reef_ascendant'], e, freq=14.0)
            endstates.crumble_scatter(add, e)
        elif style == 'pool':
            endstates.brine_pool(add, e)
            m = endstates.gutter(m, e)
        elif style == 'scrap':
            endstates.scrap_scatter(add, e, seed=len(parts))
        elif style in ('gutter', 'sink'):
            m = endstates.gutter(m, e)
    lights = [Light(L.pos + v3(0, -P['sink'], 0), L.color, L.intensity * (1 - e if style in ('gutter', 'sink', 'pool') else 1), L.radius)
              for L in lights]
    return Scene(parts=parts, materials=m, lights=lights, ground_clip=ground_clip)


__all__ = [n for n in dir() if not n.startswith('__')]

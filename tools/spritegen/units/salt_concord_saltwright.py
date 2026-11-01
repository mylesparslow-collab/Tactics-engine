"""Saltwright (Salt Concord engineer / controller).

Salt-alchemist and mason in one. Long dark steel robe under a canvas mason's apron, a squared hood,
a mason's hod strapped to the back full of salt crystals that rise over the shoulders, and an oversized
triangular trowel. Cast: salt crystals grow out of the ground in front of the trowel.
Defining detail: the crystal-filled hod.
"""
import numpy as np
from kit.humanoid import *
from kit.anim import humanoid_rows
from kit.looks import LOOKS
from _salt_concord_common import *

UNIT_ID = 'salt_concord_saltwright'
FACTION = 'salt_concord'
LOOK = LOOKS[FACTION]

C = Costume(top='robe', sleeve='robe', legs='road', hand='glove', skirt='robe', skirt_mat='robe', hem=0.12,
            flare=0.75, head='none', belt='leather', girth=1.0)


def neutral_pose():
    P = base_pose(height=0.98, build=1.02)
    rig.lean(P, fwd=np.radians(4))
    rig.place_arm(P, 'r', v3(-0.25, 1.00, 0.14), (-1, -0.2, -0.5))
    P['item_r'] = norm(v3(-0.1, -0.35, 1.0))
    rig.place_arm(P, 'l', v3(0.20, 1.06, 0.18), (1, -0.3, -0.5))
    P['head_yaw'] = np.radians(-8)
    return P


def trowel(P, add, side='r'):
    d = P['item_' + side]
    if d is None:
        return
    d = norm(d)
    g = hand_pos(P, side)
    add(Capsule(g - d * 0.06, g + d * 0.06, 0.016), 'wood')
    add(Capsule(g + d * 0.06, g + d * 0.10 + v3(0, -0.06, 0), 0.008), 'iron')
    base = g + d * 0.10 + v3(0, -0.06, 0)
    sv = norm(np.cross(d, v3(0, 1, 0)))
    up = np.cross(sv, d)
    M = np.stack([sv, d, up], axis=1)

    def f(p):
        q = (p - base) @ M
        x, y, z = q[:, 0], q[:, 1], q[:, 2]
        L = 0.30
        half = 0.09 * np.clip(1 - y / L, 0, 1)
        d2 = np.maximum(np.maximum(-y, y - L), np.abs(x) - half)
        return np.maximum(d2 * 0.85, np.abs(z) - 0.006)
    add(Func(f, base + d * 0.15, 0.25), 'steel')


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    H, R, h = P['head'], head_R(P), P['height']
    add(Ellipsoid(H, (0.078 * h, 0.097 * h, 0.088 * h), R), 'skin')
    add(Ellipsoid(H + R @ v3(0, -0.05, 0.022) * h, (0.056 * h, 0.05 * h, 0.062 * h), R), 'skin', 0.03)
    add(Capsule(H + R @ v3(0, 0.0, 0.078) * h, H + R @ v3(0, -0.028, 0.092) * h, 0.010, 0.013), 'skin', 0.01)
    add(hood_shell(P, size=1.08, peak=0.02), 'hood')
    # squared canvas apron, front only, with a brass rule tucked in the belt
    tabard(P, add, 'apron', width=0.13, hem=0.30, top=0.24, zf=0.105, back=False)
    add(RoundBox(pel + v3(-0.10, 0.02, 0.13), (0.012, 0.10, 0.004), 0.002, rot_z(0.2)), 'brass')
    # the hod on the back: a squared frame box full of salt crystals
    hb = ch + v3(0, -0.02, -0.22)
    add(RoundBox(hb, (0.15, 0.17, 0.07), 0.012), 'wood')
    add(RoundBox(hb + v3(0, 0.0, -0.002), (0.135, 0.155, 0.074), 0.008), 'hodin')
    for s in (-1, 1):
        add(Capsule(P['sh_' + ('l' if s > 0 else 'r')] + v3(-s * 0.02, 0.02, 0.0), hb + v3(s * 0.11, 0.12, 0.06), 0.014), 'leather')
    rng = np.random.default_rng(4)
    for i, (x, hh, tz) in enumerate(((-0.08, 0.30, -0.25), (0.0, 0.42, 0.05), (0.08, 0.34, 0.3), (-0.03, 0.24, -0.5),
                                     (0.10, 0.22, 0.6))):
        crystal(add, hb + v3(x, 0.08, -0.005 * i), hh * 1.3, 0.042, 'crystal', tilt=v3(np.sin(tz) * 0.5, 1, -0.15))
    trowel(P, add, 'r')
    # cast: crystals grow out of the ground in front of the trowel
    cg = P['cast_glow']
    if cg > 0.05:
        for i, (x, z, hh) in enumerate(((-0.36, 0.22, 0.42), (-0.12, 0.34, 0.55), (0.30, 0.22, 0.40), (0.10, 0.36, 0.30))):
            crystal(add, v3(x, -0.02, z), hh * cg, 0.05, 'crystal_glow', tilt=v3(x * 0.6, 1, 0.1))
    mats = base_mats(P)
    mats.update({
        'robe': salted(STEEL_DK, 0.3, ground=0.8, gamt=1.0),
        'hood': salted(STEEL, 0.35),
        'apron': salted(CANVAS, 0.35, ground=0.8, gamt=1.0, vary=0.18),
        'hodin': salted(_hex('#4a3a2c'), 0.2),
        'skin': skin_mat(P, skin=W['skin_light'], hair=_hex('#6b5a4a')),
        'crystal_glow': crystal_mat(glow=0.35 * cg),
    })
    return finish(P, FACTION, parts, mats)


ROWS, frames = humanoid_rows(neutral_pose, attack_style='swing', weapon_side='r', cast_side='l')

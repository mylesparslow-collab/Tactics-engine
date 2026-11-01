"""Hullbreaker (Salvage Compact, big melee). A slab of a man in riveted hull plate on ONE side only:
a three-lame pauldron and a bolted chest plate on the left, bare patched canvas on the right. A
breaching maul made of a ship's capstan pin on a mast-spar haft, carried on the shoulder."""
import numpy as np
from _salvage_compact_common import *

UNIT_ID = 'salvage_compact_hullbreaker'
FACTION = 'salvage_compact'

C = Costume(top='coat', sleeve='coat', legs='trousers', hand='glove', skirt=None, head='bald',
            belt='leather', girth=1.45)


def neutral_pose():
    P = base_pose(height=1.10, build=1.32)
    rig.lean(P, fwd=np.radians(7), side=np.radians(-4))
    P['head_pitch'] = np.radians(-10)
    # maul over the right shoulder, both hands on the haft
    rig.place_arm(P, 'r', v3(-0.30, 1.30, 0.20), (-0.35, -0.5, -1), l1=0.30, l2=0.29)
    P['item_r'] = norm(v3(-0.25, 0.7, -0.65))
    rig.place_arm(P, 'l', v3(-0.06, 1.12, 0.32), (0.35, -0.6, -1), l1=0.30, l2=0.29)
    return P


def maul(P, add):
    d = P['item_r']
    if d is None:
        return
    d = norm(d)
    g = hand_pos(P, 'r')
    butt, tip = g - d * 0.45, g + d * 0.72
    add(Capsule(butt, tip, 0.024), 'wood', 0.0)
    lash(add, butt, tip, n=2, r=0.03, at=(0.05, 0.12))
    sv = norm(np.cross(d, v3(0, 1, 0.3)))
    # head: a squat capstan drum with iron bands, and a spike on the back face
    a, b = tip - sv * 0.15, tip + sv * 0.15
    add(Cylinder(a, b, 0.095, 0.015), 'plate', 0.0)
    for t in (0.1, 0.5, 0.9):
        add(Torus(a + (b - a) * t, sv, 0.095, 0.012), 'iron', 0.0)
    add(Capsule(b, b + sv * 0.10, 0.03, 0.004), 'iron', 0.0)
    if P['fx'] > 0:
        endstates.crumble_scatter(add, P['fx'], seed=4, n=8, radius=0.3, mat='spray', size=0.04)


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    add(ragged_coat(P, hem_lo=0.46, hem_hi=0.62, slope=1, opening=0.4, flare=0.7, girth=1.45), 'coat2', 0.0)
    pauldron(P, add, 'l', size=1.45, layers=3)
    ch, pel, h = P['chest'], P['pelvis'], P['height']
    # chest plate bolted on the left half only
    R = basis_from(v3(0.15, 1, 0.1), (0.3, 0, 1))
    c = ch + v3(0.08, 0.02, 0.15)
    add(RoundBox(c, (0.12, 0.17, 0.012), 0.012, R), 'plate', 0.0)
    for u, v in ((-0.09, 0.14), (0.09, 0.14), (-0.09, -0.14), (0.09, -0.14), (0.0, 0.0)):
        add(Sphere(c + R @ v3(u, v, 0.016), 0.013), 'tin', 0.0)
    # beard and big bald head; a chain across the belly
    H = P['head']
    Rh = head_R(P)
    add(Ellipsoid(H + Rh @ v3(0, -0.07, 0.04) * h, (0.07 * h, 0.06 * h, 0.05 * h), Rh), 'hair', 0.02)
    for k in range(6):
        t = k / 5
        add(Torus(pel + v3(-0.18 + 0.36 * t, 0.02 - 0.06 * np.sin(np.pi * t), 0.15), v3(0.3, 0, 1) if k % 2 else v3(1, 0, 0), 0.02, 0.006), 'iron', 0.0)
    maul(P, add)
    mats = sv_materials(P, skin='mid', hair=_hex('#3a2416'), beard=_hex('#3a2416'), coat_seed=13,
                        coat_colors=(CANVAS, SAILCLOTH, OCHRE, DRAB))
    mats.update(sled_materials())
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = sv_rows(neutral_pose, attack_style='slam', weapon_side='r', fidget='shoulder', flicker=False)

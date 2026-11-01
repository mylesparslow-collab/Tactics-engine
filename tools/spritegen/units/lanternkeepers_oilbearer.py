"""Oilbearer (Lanternkeepers line infantry). Carries lamp-oil up three hundred steps.

Sturdy, sou'wester and a long oilskin coat, cudgel in the right hand, a glass oil flask in the
left. Defining detail: a tall brass oil can on a pack-board, with the stair lamp hung from its
top, rising above the hat.
"""
import numpy as np
from _lanternkeepers_common import *

UNIT_ID = 'lanternkeepers_oilbearer'
FACTION = 'lanternkeepers'
LOOK = LOOKS[FACTION]

C = Costume(top='oilskin_dk', sleeve='oilskin_dk', legs='slate', boot='boot', hand='glove', skirt='coat',
            skirt_mat='oilskin_dk', hem=0.36, flare=0.7, head='bald', belt='leather', girth=1.15)


def neutral_pose():
    P = base_pose(height=0.98, build=1.1)
    h = P['height']
    rig.lean(P, fwd=np.radians(6))
    rig.place_arm(P, 'r', v3(-0.25, 1.02, 0.16), (-1, -0.3, -0.5), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(-0.05, 0.9, -0.25))
    rig.place_arm(P, 'l', v3(0.30, 1.00, 0.20), (1, -0.3, -0.6), l1=0.27 * h, l2=0.26 * h)
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    sou_wester(add, P, 'oilskin', brim=1.05, tilt=-0.28)
    # wool scarf
    nk = P['neck']
    add(Torus(nk + v3(0, -0.02, 0.0), v3(0, 1, 0.15), 0.07, 0.025), 'seagrey', 0.01)
    held(P, add, 'r', 'club', shaft='wood')
    # glass oil flask in the left hand
    g = hand_pos(P, 'l')
    fc = g + v3(0.0, -0.08, 0.01)
    add(Ellipsoid(fc, (0.055, 0.065, 0.055)), 'oilglass')
    add(Cylinder(fc + v3(0, 0.04, 0), fc + v3(0, 0.09, 0), 0.016, 0.004), 'oilglass')
    add(Cylinder(fc + v3(0, 0.085, 0), fc + v3(0, 0.105, 0), 0.019, 0.004), 'leather')
    # pack-board and tall oil can on the back
    ch = P['chest']
    back = ch + v3(0, 0.0, -0.17)
    up = norm(P['neck'] - P['pelvis'])
    for sx in (-1, 1):
        add(Capsule(back + v3(sx * 0.10, -0.30, 0.02), back + v3(sx * 0.10, 0.62, -0.04), 0.012), 'wood')
        add(Capsule(P['sh_' + ('r' if sx < 0 else 'l')] + v3(-sx * 0.04, 0.02, 0.0), back + v3(sx * 0.09, 0.10, 0.03), 0.014), 'leather')
    add(Capsule(back + v3(-0.11, -0.26, 0.0), back + v3(0.11, -0.26, 0.0), 0.012), 'wood')
    can_a = back + v3(0, -0.10, -0.05)
    can_b = can_a + up * 0.58
    add(Cylinder(can_a, can_b, 0.085, 0.012), 'brass')
    for t in (0.15, 0.85):
        add(Torus(can_a + (can_b - can_a) * t, up, 0.087, 0.008), 'darkiron')
    add(Capsule(can_b, can_b + up * 0.04, 0.05, 0.03), 'brass')
    add(Capsule(can_b + v3(0.05, -0.02, 0), can_b + v3(0.12, 0.07, 0.03), 0.010, 0.006), 'brass')   # spout
    # lamp hung from a hook over the top of the can
    hook = can_b + up * 0.05 + v3(-0.10, 0.16, 0.02)
    add(Capsule(can_b + up * 0.04, hook, 0.008), 'darkiron')
    hurricane(add, lights, P, hook - v3(0, 0.12, 0), size=1.3, frame='darkiron', light=1.9)
    mats = keeper_mats(P, hair=_hex('#3b2e25'), beard=_hex('#4a3a2e'), skin=W['skin_mid'])
    mats['oilglass'] = Material(_hex('#d08a2a'), spec=1.0, gloss=60, brush=0.0, emissive=(0.22, 0.12, 0.02), rim=1.5)
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = keeper_rows(neutral_pose, attack_style='swing', weapon_side='r', cast_side='l')

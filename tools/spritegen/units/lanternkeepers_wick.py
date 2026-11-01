"""Wick (Lanternkeepers scout, cheap). The youngest keeper, sent ahead with a taper.

Small, half-crouched, oilskin hood with a tall peak, a hand lantern held out in front and the right
hand cupped round it with a trimming knife. Defining detail: the lantern flame is the brightest
thing on screen.
"""
import numpy as np
from _lanternkeepers_common import *

UNIT_ID = 'lanternkeepers_wick'
FACTION = 'lanternkeepers'
LOOK = LOOKS[FACTION]

C = Costume(top='coatgrey', sleeve='coatgrey', legs='slate', boot='boot', hand='glove', skirt='coat',
            skirt_mat='coatgrey', hem=0.50, flare=0.55, head='hood', head_mat='oilskin', belt='leather', girth=0.85)


def neutral_pose():
    P = base_pose(height=0.82, build=0.84)
    h = P['height']
    # a real crouch: hips well down, wide stance, left foot forward, body bent over the lantern
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + rig.UPPER, v3(0, -0.15, 0.02))
    rig.place_leg(P, 'r', P['an_r'] + v3(-0.04, 0, -0.06), l1=0.43 * h, l2=0.42 * h)
    rig.place_leg(P, 'l', P['an_l'] + v3(0.03, 0, 0.10), l1=0.43 * h, l2=0.42 * h)
    rig.lean(P, fwd=np.radians(24))
    P['head_pitch'] = np.radians(-4)
    P['head_yaw'] = np.radians(-4)
    # lantern held out low in front in the left fist; the right hand cups round it (knife in that hand)
    ch = P['chest']
    rig.place_arm(P, 'l', ch + v3(0.10, -0.06, 0.30), (1, -0.6, -0.4), l1=0.27 * h, l2=0.26 * h)
    rig.place_arm(P, 'r', ch + v3(-0.05, -0.20, 0.32), (-1, -0.5, -0.3), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(-0.2, -0.8, 0.4))
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    tall_hood(add, P, 'oilskin_dk', peak=0.06)
    mantle(add, P, 'oilskin', depth=0.16, width=0.15)
    held(P, add, 'r', 'knife', head='brass')
    # hand lantern hanging from the left fist
    g = hand_pos(P, 'l')
    lc = g - v3(0, 0.12, 0)
    add(Capsule(g, g - v3(0, 0.03, 0), 0.004), 'brass')
    hurricane(add, lights, P, lc, size=1.5, light=3.4)
    # taper tucked in the belt
    pel = P['pelvis']
    add(Capsule(pel + v3(0.10, 0.06, 0.09), pel + v3(0.13, 0.22, 0.10), 0.008), 'wax')
    # satchel strap
    ch = P['chest']
    add(Capsule(ch + v3(-0.11, 0.12, 0.07), pel + v3(0.12, 0.08, 0.10), 0.010), 'leather')
    mats = keeper_mats(P, hair=_hex('#6b4a30'))
    mats['lamp'] = Material(_hex('#ffe2a0'), emissive=tuple(np.array(_hex('#ffd890')) * min(1.8, 1.6 * P['glow'] * (1 + 0.6 * P['cast_glow']))), rim=0.0)
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = keeper_rows(neutral_pose, attack_style='swing', weapon_side='r', cast_side='l')

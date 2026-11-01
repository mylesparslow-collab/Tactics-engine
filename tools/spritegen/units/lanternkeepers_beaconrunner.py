"""Beaconrunner (Lanternkeepers skirmisher). Steps along the beams between lamps.

Lean and quick, leaning into a run: short oilskin jacket, close hood with a long sea-grey scarf
streaming back, a runner's blade low in the right hand. Defining detail: a whip-thin lamp pole
strapped to the back, its lantern bobbing high above the head like a beacon on the move.
"""
import numpy as np
from _lanternkeepers_common import *

UNIT_ID = 'lanternkeepers_beaconrunner'
FACTION = 'lanternkeepers'
LOOK = LOOKS[FACTION]

C = Costume(top='oilskin', sleeve='slate', legs='slate', boot='boot', hand='glove', skirt='coat',
            skirt_mat='oilskin', hem=0.64, flare=0.45, head='hood', head_mat='coatgrey', belt='leather', girth=0.85)


def neutral_pose():
    P = base_pose(height=1.0, build=0.86)
    h = P['height']
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + rig.UPPER, v3(0, -0.03, 0.0))
    rig.place_leg(P, 'l', P['an_l'] + v3(0, 0, 0.08), l1=0.43 * h, l2=0.42 * h)
    rig.place_leg(P, 'r', P['an_r'] + v3(0, 0, -0.06), l1=0.43 * h, l2=0.42 * h)
    rig.lean(P, fwd=np.radians(12))
    P['head_pitch'] = np.radians(-10)
    rig.place_arm(P, 'r', v3(-0.27, 0.92, 0.18), (-1, -0.2, -0.5), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(-0.25, -0.35, 0.9))
    rig.place_arm(P, 'l', v3(0.24, 1.02, 0.10), (1, -0.3, -0.6), l1=0.27 * h, l2=0.26 * h)
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    held(P, add, 'r', 'blade', head='darkiron')
    # scarf: wrap and two tails streaming back
    nk = P['neck']
    add(Torus(nk + v3(0, -0.01, 0.0), v3(0, 1, 0.2), 0.065, 0.024), 'seagrey', 0.01)
    sw = P['skirt_sway']
    a = nk + v3(0.04, -0.02, -0.07)
    add(Capsule(a, a + v3(0.03 + 0.03 * sw, -0.22, -0.12), 0.022, 0.012), 'seagrey')
    add(Capsule(a + v3(-0.04, 0, 0), a + v3(-0.02 - 0.03 * sw, -0.30, -0.08), 0.020, 0.010), 'seagrey')
    # back pole with the beacon lamp
    pel, ch = P['pelvis'], P['chest']
    up = norm(P['neck'] - pel)
    b0 = pel + v3(-0.10, -0.02, -0.14)
    b1 = b0 + norm(up + v3(0.0, 0, -0.22)) * 1.06
    add(Capsule(ch + v3(-0.12, 0.12, 0.09), pel + v3(0.12, 0.06, 0.09), 0.010), 'leather')
    pole_lamp(add, lights, P, b0, b1, 'hurricane', size=1.15, shaft='wood', frame='darkiron', arm=0.08, light=1.8)
    mats = keeper_mats(P, hair=_hex('#7a5a3a'))
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = keeper_rows(neutral_pose, attack_style='swing', weapon_side='r', cast_side='l')

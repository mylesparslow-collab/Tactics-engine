"""Keeper Pell Auster, Last Keeper of Lantern Shoal (Lanternkeepers hero).

Small, elderly and bent: faded oilskin keeper's coat to the shins, a sea-grey shawl, grey hair in
a knot. She holds her staff across her body in both hands, its lantern hung from the top end
held high over her left shoulder. Wick trimmers and a key on her belt. Defining detail: clouded
pale eyes that still follow the light.
"""
import numpy as np
from _lanternkeepers_common import *

UNIT_ID = 'lanternkeepers_keeper_pell_auster'
FACTION = 'lanternkeepers'
LOOK = LOOKS[FACTION]

C = Costume(top='oilskin', sleeve='oilskin', legs='slate', boot='boot', hand='skin', skirt='coat',
            skirt_mat='oilskin', hem=0.20, flare=0.7, head='hair', hair='hair', hair_style='short',
            belt='leather', girth=1.0)


def neutral_pose():
    P = base_pose(height=0.88, build=0.92)
    h = P['height']
    rig.lean(P, fwd=np.radians(16))
    P['head_pitch'] = np.radians(-14)       # chin lifted toward the lamp
    P['head_yaw'] = np.radians(8)
    # staff across the body: right hand low at the right hip, left hand high in front of the chest
    rig.place_arm(P, 'r', v3(-0.20, 0.82, 0.20), (-1, -0.4, -0.5), l1=0.27 * h, l2=0.26 * h)
    rig.place_arm(P, 'l', v3(0.08, 1.10, 0.28), (1, -0.5, -0.3), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(hand_pos(P, 'l') - hand_pos(P, 'r'))
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    H, R, h = P['head'], head_R(P), P['height']
    add(Sphere(H + R @ v3(0, 0.06, -0.08) * h, 0.04), 'hair', 0.01)       # knot
    add(capelet_shell(P, depth=0.15, width=0.17, sq=2.2), 'seagrey')        # shawl
    res = held(P, add, 'r', 'staff', shaft='wood', head='brass', below=0.55, above=1.05)
    if res is not None:
        butt, tip = res
        d = norm(tip - butt)
        add(Capsule(tip, tip + v3(0, -0.04, 0), 0.005), 'darkiron')
        hurricane(add, lights, P, tip - v3(0, 0.04 + 0.10 * 1.25, 0), size=1.25, frame='brass', light=2.2)
    # belt: wick trimmers and a big key
    pel = P['pelvis']
    add(Capsule(pel + v3(0.13, 0.05, 0.08), pel + v3(0.15, -0.07, 0.10), 0.007), 'darkiron')
    add(Capsule(pel + v3(0.15, 0.05, 0.08), pel + v3(0.18, -0.06, 0.09), 0.007), 'darkiron')
    add(Torus(pel + v3(-0.13, 0.03, 0.09), v3(0, 0, 1), 0.02, 0.005), 'brass')
    add(Capsule(pel + v3(-0.13, 0.01, 0.09), pel + v3(-0.13, -0.10, 0.095), 0.007), 'brass')
    mats = keeper_mats(P, hair=_hex('#cfcac0'), skin=_hex('#d9a688'), eyes=_hex('#c7ccd0'),
                       coat=_hex('#b0904e'))
    return finish(P, FACTION, parts, mats, lights=lights)


def _post(fr):
    # she jabs the lamp end up and out at the foe, keeping the lantern in frame
    for i, (P, o) in enumerate(fr['attack']):
        P['item_r'] = norm(norm(P['item_r']) + v3(0.25, [0.9, 1.0, 0.75, 0.9][i], -0.2))
    return fr


ROWS, frames = keeper_rows(neutral_pose, attack_style='thrust', weapon_side='r', cast_side='l', post=_post, pole='r')

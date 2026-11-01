"""Salt Levy (Salt Concord, cheap body). Kit example: a short humanoid file.

Braced spear, slightly hunched. Oversize salt-crusted helm, undyed jerkin, road-tax tally tag on a
cord. Lean. Defining detail: a spear too good for him, new brass tip on an old pole.
"""
import numpy as np
from kit.humanoid import *
from kit.anim import humanoid_rows
from kit.looks import LOOKS, PALETTES

UNIT_ID = 'salt_concord_salt_levy'
FACTION = 'salt_concord'
LOOK = LOOKS[FACTION]
SC = PALETTES[FACTION]

C = Costume(top='jerkin', sleeve='shirt', legs='legs', hand='skin', skirt='robe', skirt_mat='jerkin',
            hem=0.62, flare=0.5, head='helm', head_mat='helm', belt='leather', girth=0.9)


def neutral_pose():
    P = base_pose(height=0.97, build=0.92)
    rig.lean(P, fwd=np.radians(7))               # slightly hunched
    P['head_pitch'] = np.radians(-6)
    # right hand braces the spear upright beside him, butt on the ground
    rig.place_arm(P, 'r', v3(-0.25, 0.96, 0.12), (-0.3, -0.2, -1))
    P['item_r'] = norm(v3(0.02, 1.0, 0.05))
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    held(P, add, 'r', 'spear', shaft='old_wood', head='brass', below=1.0, above=1.0)
    # tally tag on a cord around the neck
    nk = P['neck']
    add(Capsule(nk + v3(-0.05, -0.02, 0.07), nk + v3(-0.02, -0.12, 0.11), 0.004), 'leather')
    add(RoundBox(nk + v3(-0.02, -0.15, 0.115), (0.018, 0.026, 0.004), 0.003), 'tally')
    mats = {
        'jerkin': Material(lambda p, n: np.array(_hex('#b9ad94'))[None, :] * (0.92 + 0.12 * fbm(p, 20, 2)[:, None]),
                           spec=0.03, brush=0.10),
        'shirt': Material(_hex('#8d8f92'), spec=0.02, brush=0.08),
        'legs': Material(_hex('#6c6a66'), spec=0.02, brush=0.08),
        'skin': Material(face_albedo(P, W['skin_light'], _hex('#4a3426')), spec=0.06, gloss=12, sss=0.6, brush=0.02),
        'helm': Material(lambda p, n: np.where((fbm(p, 26, 3) > 0.52)[:, None], np.array(SC['salt'])[None, :],
                                               np.array(_hex('#6d737b'))[None, :]), spec=0.5, gloss=26, metal=0.5),
        'old_wood': Material(_hex('#5d4a38'), spec=0.05, brush=0.1),
        'tally': Material(_hex('#c9b27a'), spec=0.3),
    }
    return finish(P, FACTION, parts, mats)


ROWS, frames = humanoid_rows(neutral_pose, attack_style='thrust', weapon_side='r')

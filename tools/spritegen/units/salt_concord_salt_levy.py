"""Salt Levy (Salt Concord, cheap body). Kit example: a short humanoid file.

Braced spear, slightly hunched. Oversize salt-crusted kettle helm that sits too low, undyed jerkin
with salt crusted up the hem, a road-tax tally tag on a cord. Lean. Defining detail: a spear too
good for him, new brass tip on an old pole.
"""
import numpy as np
from kit.humanoid import *
from kit.anim import humanoid_rows
from kit.looks import LOOKS, PALETTES
from _salt_concord_common import *

UNIT_ID = 'salt_concord_salt_levy'
FACTION = 'salt_concord'
LOOK = LOOKS[FACTION]

C = Costume(top='jerkin', sleeve='shirt', legs='legs', hand='skin', skirt='robe', skirt_mat='jerkin',
            hem=0.58, flare=0.45, head='bald', belt='rope', girth=0.88, boots_tall=False)


def neutral_pose():
    P = base_pose(height=0.97, build=0.90)
    rig.lean(P, fwd=np.radians(8))               # slightly hunched
    P['head_pitch'] = np.radians(-4)
    # right hand braces the spear upright beside him, butt on the ground
    rig.place_arm(P, 'r', v3(-0.27, 0.98, 0.14), (-0.3, -0.2, -1))
    P['item_r'] = norm(v3(0.02, 1.0, 0.04))
    # left hand hangs, thumb in the rope belt
    rig.place_arm(P, 'l', v3(0.17, 0.93, 0.10), (1, -0.2, -0.6))
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    # oversize kettle helm, a size too big and riding low over the brows
    kettle_helm(P, add, 'helm', size=1.18, brim=1.08, tall=0.9)
    vert = P['item_r'] is not None and norm(P['item_r'])[1] > 0.8
    butt, tip = held(P, add, 'r', 'spear', shaft='old_wood', head='brass', below=1.0 if vert else 0.6, above=1.0)
    d = norm(tip - butt)
    add(Cylinder(tip - d * 0.22, tip - d * 0.19, 0.020, 0.004), 'brass')      # bright new ferrule
    for t in (0.35, 0.62):                                                    # old cord bindings
        add(Cylinder(butt + d * t * 2.0, butt + d * (t * 2.0 + 0.03), 0.019, 0.004), 'rope')
    add(Ellipsoid(tip - d * 0.09, (0.034, 0.12, 0.012), basis_from(d, (0, 0, 1))), 'brass')   # leaf blade, oversized
    # steel-blue levy scarf: the only colour he was issued
    nk0 = P['neck']
    add(Torus(nk0 + v3(0, -0.03, 0.0), v3(0, 1, 0.15), 0.07, 0.026), 'steelcloth', 0.01)
    add(Capsule(nk0 + v3(0.04, -0.05, 0.07), nk0 + v3(0.07, -0.16, 0.09), 0.022, 0.016), 'steelcloth', 0.01)
    # tally tag on a cord around the neck
    nk = P['neck']
    add(Capsule(nk + v3(-0.05, -0.02, 0.07), nk + v3(-0.02, -0.12, 0.11), 0.004), 'rope')
    add(RoundBox(nk + v3(-0.02, -0.15, 0.115), (0.022, 0.03, 0.005), 0.003), 'tally')
    # bedroll strapped across the back
    ch = P['chest']
    add(Cylinder(ch + v3(-0.16, 0.10, -0.15), ch + v3(0.16, 0.10, -0.15), 0.055, 0.02), 'canvas')
    mats = base_mats(P)
    mats.update({
        'jerkin': salted(CANVAS, 0.3, ground=0.75, gamt=0.9, vary=0.16, brush=0.10),
        'shirt': salted(_hex('#8d8f92'), 0.2),
        'legs': salted(_hex('#6c6a66'), 0.3, ground=0.5, gamt=1.0),
        'skin': skin_mat(P, hair=_hex('#3a2a1f')),
        'helm': salted_metal(_hex('#6d737b'), amount=0.75),
        'old_wood': Material(_hex('#5d4a38'), spec=0.05, brush=0.12),
        'rope': salted(_hex('#9a8a68'), 0.2, spec=0.02),
        'tally': Material(_hex('#c9b27a'), spec=0.3),
    })
    return finish(P, FACTION, parts, mats)


ROWS, frames = humanoid_rows(neutral_pose, attack_style='thrust', weapon_side='r')

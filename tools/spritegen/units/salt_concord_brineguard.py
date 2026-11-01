"""Brineguard (Salt Concord line infantry).

Salt-crusted iron kettle helm, pale tabard with a steel-blue border over a steel-blue gambeson, squared
pauldrons, a rectangular stair-marked pavise on the left arm and a long braced spear. Defining detail:
the pavise, part of a wall when he stands in rank.
"""
import numpy as np
from kit.humanoid import *
from kit.anim import humanoid_rows
from kit.looks import LOOKS
from _salt_concord_common import *

UNIT_ID = 'salt_concord_brineguard'
FACTION = 'salt_concord'
LOOK = LOOKS[FACTION]

C = Costume(top='tabard', sleeve='steelcloth', legs='road', hand='glove', skirt=None, head='none',
            belt='leather', girth=1.05)


def neutral_pose():
    P = base_pose(height=1.02, build=1.06)
    rig.place_arm(P, 'r', v3(-0.29, 0.98, 0.13), (-0.5, -0.2, -1))
    P['item_r'] = norm(v3(0.0, 1.0, 0.04))
    rig.place_arm(P, 'l', v3(0.22, 1.02, 0.16), (1, -0.3, -0.5))
    P['head_yaw'] = np.radians(-6)
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    # head (bare face under the helm)
    H, R, h = P['head'], head_R(P), P['height']
    add(Ellipsoid(H, (0.078 * h, 0.097 * h, 0.088 * h), R), 'skin')
    add(Ellipsoid(H + R @ v3(0, -0.05, 0.022) * h, (0.056 * h, 0.05 * h, 0.062 * h), R), 'skin', 0.03)
    add(Capsule(H + R @ v3(0, 0.0, 0.078) * h, H + R @ v3(0, -0.028, 0.092) * h, 0.010, 0.013), 'skin', 0.01)
    # aventail: mail drape from helm to shoulders
    add(Cylinder(P['neck'] + v3(0, -0.05, -0.015), P['neck'] + v3(0, 0.03, -0.02), 0.080, 0.02), 'iron')
    kettle_helm(P, add, 'helmiron', size=1.05, brim=0.85, comb=True)
    tabard(P, add, 'tabard', width=0.12, hem=0.40)
    square_pauldrons(P, add, 'iron', trim='salt')
    vert = P['item_r'] is not None and norm(P['item_r'])[1] > 0.8
    held(P, add, 'r', 'spear', shaft='wood', head='steel', below=0.95 if vert else 0.55, above=1.25 if vert else 1.05)
    cr = tower_shield(P, add, 'l', 'shield', 'brass', size=1.0)
    mats = base_mats(P)
    mats.update({
        'tabard': tabard_mat(P, width=0.12),
        'skin': skin_mat(P, skin=W['skin_light']),
        'shield': shield_mat(cr, kind='stair'),
        'glove': salted(_hex('#3e2c22'), 0.2),
    })
    return finish(P, FACTION, parts, mats)


ROWS, frames = humanoid_rows(neutral_pose, attack_style='thrust', weapon_side='r')

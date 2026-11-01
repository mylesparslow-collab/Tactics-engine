"""Stair-Warden (Salt Concord tank).

Broad and heavy. Closed squared helm with a T-slit, salt-crusted plate over a pale tabard bearing the
Greywater Stair, wide squared pauldrons, a door-sized steel-blue pavise and a flanged mace. Neighbours
stand taller beside them. Defining detail: the door-sized stair pavise.
"""
import numpy as np
from kit.humanoid import *
from kit.anim import humanoid_rows
from kit.looks import LOOKS
from _salt_concord_common import *

UNIT_ID = 'salt_concord_stair_warden'
FACTION = 'salt_concord'
LOOK = LOOKS[FACTION]

C = Costume(top='tabard', sleeve='mail', legs='road', hand='gauntlet', skirt=None, head='none', belt='leather',
            girth=1.25, boots_tall=True)


def neutral_pose():
    P = base_pose(height=1.08, build=1.2)
    rig.place_arm(P, 'r', v3(-0.30, 1.05, 0.10), (-1, -0.2, -0.5))
    P['item_r'] = norm(v3(-0.15, -0.2, 1.0))
    rig.place_arm(P, 'l', v3(0.25, 1.05, 0.20), (1, -0.3, -0.5))
    P['head_yaw'] = np.radians(-4)
    # wide stance
    rig.place_leg(P, 'r', v3(-0.15, 0.085, -0.03), l1=0.43 * 1.08, l2=0.42 * 1.08)
    rig.place_leg(P, 'l', v3(0.17, 0.085, 0.08), l1=0.43 * 1.08, l2=0.42 * 1.08)
    return P


def mace(P, add, side='r'):
    d = P['item_' + side]
    if d is None:
        return
    d = norm(d)
    g = hand_pos(P, side)
    add(Capsule(g - d * 0.10, g + d * 0.46, 0.018), 'iron')
    add(Sphere(g - d * 0.11, 0.024), 'brass')
    hc = g + d * 0.52
    R = basis_from(d, (0, 1, 0))
    add(Cylinder(hc - d * 0.09, hc + d * 0.09, 0.035, 0.01), 'iron')
    for i in range(6):
        a = i * np.pi / 3
        o = R[:, 0] * np.cos(a) + R[:, 2] * np.sin(a)
        Rf = np.stack([o, d, np.cross(o, d)], axis=1)
        add(RoundBox(hc + o * 0.045, (0.035, 0.075, 0.007), 0.004, Rf), 'iron')
    add(Sphere(hc + d * 0.10, 0.02), 'brass')


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    H, R, h = P['head'], head_R(P), P['height']
    add(Cylinder(nk + v3(0, -0.04, -0.01), nk + v3(0, 0.05, -0.01), 0.085, 0.02), 'mail')   # gorget
    barbute(P, add, 'visor', trim='helmiron', size=1.05)
    add(RoundBox(H + R @ v3(0, 0.13, -0.01) * h, (0.012, 0.03, 0.09), 0.008, R), 'brass')     # crest ridge
    tabard(P, add, 'tabard', width=0.14, hem=0.36, top=0.10)
    # breastplate over the tabard, upper chest only
    add(Ellipsoid(ch + v3(0, 0.07, 0.01), (0.17 * P['build'], 0.11, 0.115 * P['build'])), 'plate', 0.0)
    # plate fauld: squared lames over the hips
    for i in range(2):
        add(RoundBox(pel + v3(0, 0.02 - i * 0.06, 0.0), (0.18 * P['build'], 0.03, 0.125 * P['build']), 0.02), 'plate')
    square_pauldrons(P, add, 'plate', size=1.3, trim='salt')
    mace(P, add, 'r')
    cr = tower_shield(P, add, 'l', 'shield', 'brass', size=1.0, w=0.22, hgt=0.46, offset=v3(0.09, -0.06, 0.08))
    mats = base_mats(P)
    mats.update({
        'plate': salted_metal(_hex('#7a828c'), amount=0.5),
        'mail': salted_metal(IRON_DK, amount=0.35, spec=0.4),
        'visor': visor_mat(P, metal=_hex('#7a828c'), amount=0.45),
        'gauntlet': salted_metal(IRON, amount=0.3),
        'tabard': tabard_mat(P, width=0.14 * 1.2, stripe=None),
        'shield': shield_mat(cr, kind='stair', w=0.22, hgt=0.46),
        'skin': skin_mat(P),
    })
    return finish(P, FACTION, parts, mats)


ROWS, frames = humanoid_rows(neutral_pose, attack_style='swing', weapon_side='r')

"""Surveyor (Salt Concord ranged spotter).

Short steel-blue survey coat with salt trim, flat squared cap, a striped range pole slung across his
back that stands up over his shoulder like a spike, a light crossbow that shoots chalk-marked bolts,
a brass measuring chain at the hip and a chalk bag. Defining detail: the striped range pole.
"""
import numpy as np
from kit.humanoid import *
from kit.anim import humanoid_rows
from kit.looks import LOOKS
from _salt_concord_common import *

UNIT_ID = 'salt_concord_surveyor'
FACTION = 'salt_concord'
LOOK = LOOKS[FACTION]

C = Costume(top='coat', sleeve='coat', legs='road', hand='glove', skirt='coat', skirt_mat='coat', hem=0.56,
            flare=0.7, head='hair', hair='hair', hair_style='short', belt='leather', girth=0.92)


def neutral_pose():
    P = base_pose(height=1.0, build=0.95)
    rig.place_arm(P, 'r', v3(-0.18, 1.02, 0.18), (-1, -0.4, -0.5))
    P['item_r'] = norm(v3(0.35, -0.12, 1.0))
    rig.place_arm(P, 'l', v3(0.02, 1.00, 0.38), (1, -0.5, -0.3))
    P['head_yaw'] = np.radians(-4)
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    # flat squared survey cap with a short visor and a brass badge
    H, R, h = P['head'], head_R(P), P['height']
    add(RoundBox(H + R @ v3(0, 0.085, -0.01) * h, (0.084, 0.034, 0.090), 0.014, R), 'cap')
    add(RoundBox(H + R @ v3(0, 0.055, 0.09) * h, (0.07, 0.005, 0.035), 0.004, R @ rot_x(0.25)), 'cap')
    add(RoundBox(H + R @ v3(0, 0.09, 0.095) * h, (0.018, 0.016, 0.004), 0.003, R), 'brass')
    # squared salt collar and cuff trims
    nk, ch, pel = P['neck'], P['chest'], P['pelvis']
    add(Cylinder(nk + v3(0, -0.03, -0.005), nk + v3(0, 0.04, -0.012), 0.07, 0.012), 'salt')
    for s in ('r', 'l'):
        el, wr = P['el_' + s], P['wr_' + s]
        add(Capsule(el + (wr - el) * 0.72, wr - (wr - el) * 0.02, 0.047), 'salt')
    # range pole slung across the back, high over the left shoulder
    a = pel + v3(-0.22, -0.18, -0.16)
    b = ch + v3(0.46, 0.68, -0.14)
    P['_pa'], P['_pb'] = a, b
    add(Capsule(a, b, 0.018), 'rangepole')
    add(Sphere(b, 0.026), 'brass')
    add(Capsule(ch + v3(-0.12, 0.14, 0.09), pel + v3(0.13, 0.05, 0.10), 0.012), 'leather')     # sling strap
    # brass measuring chain looped at the right hip, chalk bag on the left
    chain(add, pel + v3(-0.14, 0.06, 0.06), pel + v3(-0.15, 0.06, -0.06), sag=0.08, n=6, r=0.012)
    add(Ellipsoid(pel + v3(0.16, -0.02, 0.06), (0.04, 0.05, 0.035)), 'canvas', 0.01)
    add(Sphere(pel + v3(0.16, 0.035, 0.06), 0.022), 'salt')
    crossbow(P, add, 'r')
    mats = base_mats(P)
    mats.update({
        'coat': salted(STEEL, 0.3, ground=0.7, gamt=0.9),
        'cap': salted(STEEL_DK, 0.2),
        'hair': Material(_hex('#3b2a20'), spec=0.2, brush=0.1),
        'skin': skin_mat(P, skin=W['skin_mid'], hair=_hex('#3b2a20')),
        'glove': salted(_hex('#3e2c22'), 0.2),
        'rangepole': rod_mat('_pa', '_pb', P, band=0.12),
        'chalk_puff': Material(SALT_HI, emissive=tuple(np.array(SALT_HI) * 0.6), rim=0.0),
    })
    return finish(P, FACTION, parts, mats)


ROWS, frames = humanoid_rows(neutral_pose, attack_style='shoot', weapon_side='r')

"""Brine Chirurgeon (Salt Concord healer).

Field surgeon in a long pale salt-canvas coat with a steel-blue surgeon's apron and squared cap, a
roll of lancets and a dressing satchel at the hip, a brass lancet in the right hand and a big
brass-caged flask of clear brine in the left. Cast: the brine flask lights and he sloshes it out.
Defining detail: the caged brine flask.
"""
import numpy as np
from kit.humanoid import *
from kit.anim import humanoid_rows
from kit.looks import LOOKS
from _salt_concord_common import *

UNIT_ID = 'salt_concord_brine_chirurgeon'
FACTION = 'salt_concord'
LOOK = LOOKS[FACTION]

C = Costume(top='coatpale', sleeve='coatpale', legs='road', hand='glove', skirt='coat', skirt_mat='coatpale',
            hem=0.22, flare=0.8, head='hair', hair='hair', hair_style='short', belt='leather', girth=0.95)
BRINE = _hex('#9fe3d8')


def neutral_pose():
    P = base_pose(height=1.0, build=0.95)
    rig.place_arm(P, 'r', v3(-0.24, 1.02, 0.14), (-1, -0.3, -0.5))
    P['item_r'] = norm(v3(-0.1, 0.4, 1.0))
    rig.place_arm(P, 'l', v3(0.24, 1.10, 0.18), (1, -0.4, -0.5))
    P['head_yaw'] = np.radians(-10)
    P['head_pitch'] = np.radians(4)
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    H, R, h = P['head'], head_R(P), P['height']
    # squared surgeon's cap and a mask pulled down round the neck
    add(RoundBox(H + R @ v3(0, 0.075, -0.01) * h, (0.082, 0.04, 0.088), 0.02, R), 'cap')
    add(Torus(nk + v3(0, 0.0, 0.01), v3(0, 1, 0.3), 0.06, 0.018), 'salt', 0.01)
    # steel-blue apron front and back, salt-stained
    tabard(P, add, 'apron', width=0.10, hem=0.36, top=0.30, zf=0.095, back=False)
    # lancet roll and dressing satchel
    add(RoundBox(pel + v3(0.17, -0.03, 0.05), (0.05, 0.07, 0.07), 0.015, rot_y(0.4)), 'leather')
    add(RoundBox(pel + v3(0.17, 0.035, 0.05), (0.054, 0.012, 0.074), 0.01, rot_y(0.4)), 'salt')
    add(Cylinder(pel + v3(-0.15, 0.04, 0.08), pel + v3(-0.15, -0.07, 0.10), 0.03, 0.01), 'leather')
    # lancet: short brass handle and a thin steel blade
    d = P['item_r']
    if d is not None:
        d = norm(d)
        g = hand_pos(P, 'r')
        add(Capsule(g - d * 0.05, g + d * 0.05, 0.011), 'brass')
        add(Capsule(g + d * 0.05, g + d * 0.22, 0.010, 0.002), 'steel')
    # caged brine flask in the left hand
    gl = hand_pos(P, 'l')
    fc = gl + v3(0.0, 0.13, 0.02)
    k = 1.35
    cg = P['cast_glow']
    add(Ellipsoid(fc, (0.06 * k, 0.075 * k, 0.06 * k)), 'flask')
    add(Cylinder(fc + v3(0, 0.06 * k, 0), fc + v3(0, 0.12 * k, 0), 0.022 * k, 0.005), 'flask')
    add(Cylinder(fc + v3(0, 0.115 * k, 0), fc + v3(0, 0.14 * k, 0), 0.026 * k, 0.006), 'brass')
    for a in range(4):
        ang = a * np.pi / 2 + 0.4
        o = v3(np.cos(ang), 0, np.sin(ang))
        add(Capsule(fc + o * 0.058 * k + v3(0, -0.06 * k, 0), fc + o * 0.058 * k + v3(0, 0.05 * k, 0), 0.006), 'brass')
    add(Torus(fc, v3(0, 1, 0), 0.062 * k, 0.008), 'brass')
    if cg > 0.3:
        for i in range(4):
            add(Sphere(fc + v3(-0.08 - 0.07 * i, 0.06 + 0.05 * i - 0.02 * i * i, 0.06 + 0.03 * i), 0.024 * cg), 'splash')
    mats = base_mats(P)
    mats.update({
        'coatpale': salted(_hex('#cfc8b6'), 0.25, ground=0.7, gamt=0.6, vary=0.12),
        'apron': salted(STEEL, 0.4, ground=0.8, gamt=1.0),
        'cap': salted(STEEL_DK, 0.2),
        'hair': Material(_hex('#8a8580'), spec=0.2, brush=0.1),
        'skin': skin_mat(P, skin=W['skin_light'], hair=_hex('#6a6560')),
        'flask': Material(BRINE, spec=0.9, gloss=60, brush=0.02, emissive=tuple(np.array(BRINE) * (0.25 + 0.6 * cg))),
        'splash': Material(BRINE, emissive=tuple(np.array(BRINE) * 0.6), rim=0.0),
    })
    lights = [Light(fc, _hex('#9fe3d8'), 0.6 + 1.2 * cg, 0.18)]
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = humanoid_rows(neutral_pose, attack_style='swing', weapon_side='r', cast_side='l')

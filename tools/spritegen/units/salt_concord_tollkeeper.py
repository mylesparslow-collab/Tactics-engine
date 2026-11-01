"""Tollkeeper (Salt Concord controller).

A heavy road-grey greatcoat with a steel-blue shoulder cape, a wide flat-brimmed toll hat, a strongbox
on the hip and a tall toll staff topped with a striped barrier bar from which a brass chain and hook
hang. Cast: the toll chain whips out and reels the target in. Defining detail: the barrier-bar staff.
"""
import numpy as np
from kit.humanoid import *
from kit.anim import humanoid_rows
from kit.looks import LOOKS
from _salt_concord_common import *

UNIT_ID = 'salt_concord_tollkeeper'
FACTION = 'salt_concord'
LOOK = LOOKS[FACTION]

C = Costume(top='greatcoat', sleeve='greatcoat', legs='road', hand='glove', skirt='coat', skirt_mat='greatcoat',
            hem=0.20, flare=0.95, head='hair', hair='hair', hair_style='bob', belt='leather', girth=1.15)


def neutral_pose():
    P = base_pose(height=1.0, build=1.08)
    rig.place_arm(P, 'r', v3(-0.27, 1.12, 0.16), (-1, -0.4, -0.5))
    P['item_r'] = norm(v3(-0.04, 1.0, 0.05))
    rig.place_arm(P, 'l', v3(0.16, 0.98, 0.14), (1, -0.2, -0.6))
    P['head_yaw'] = np.radians(-6)
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    H, R, h = P['head'], head_R(P), P['height']
    # wide flat toll hat (squared crown)
    add(RoundBox(H + R @ v3(0, 0.095, -0.01) * h, (0.072, 0.05, 0.078), 0.02, R), 'hat')
    add(RoundBox(H + R @ v3(0, 0.055, -0.005) * h, (0.17, 0.007, 0.16), 0.008, R @ rot_x(0.06)), 'hat')
    add(RoundBox(H + R @ v3(0, 0.072, -0.005) * h, (0.074, 0.012, 0.080), 0.006, R), 'brass')
    # steel-blue shoulder cape, squared
    add(capelet_shell(P, depth=0.20, width=0.24, sq=4.5), 'cape')
    # strongbox on the left hip, toll ledger on a strap
    add(RoundBox(pel + v3(0.20, -0.02, 0.04), (0.055, 0.065, 0.08), 0.01, rot_y(0.3)), 'iron')
    add(RoundBox(pel + v3(0.20, 0.045, 0.04), (0.058, 0.01, 0.083), 0.004, rot_y(0.3)), 'brass')
    add(RoundBox(pel + v3(0.24, -0.02, 0.095), (0.012, 0.016, 0.006), 0.003, rot_y(0.3)), 'brass')
    # toll staff with a striped barrier bar and a hanging chain + hook
    r = held(P, add, 'r', 'staff', shaft='wood', head='brass', below=1.1, above=1.02)
    if r is not None:
        butt, tip = r
        d = norm(tip - butt)
        sv = norm(np.cross(d, v3(0, 0, 1)))
        if sv[0] > 0:
            sv = -sv
        bar_a, bar_b = tip - d * 0.05 - sv * 0.04, tip - d * 0.05 + sv * 0.38
        P['_ba'], P['_bb'] = bar_a, bar_b
        add(RoundBox((bar_a + bar_b) / 2, (0.02, np.linalg.norm(bar_b - bar_a) / 2, 0.02), 0.006,
                     basis_from(bar_b - bar_a, (0, 0, 1))), 'barbar')
        add(Sphere(tip, 0.035), 'brass')
        cg = P['cast_glow']
        top = bar_b + v3(0, -0.02, 0)
        if cg > 0.05:
            end = top + v3(-0.25, -0.50, 1.05) * cg
            chain(add, top, end, sag=0.08 * (1 - cg) + 0.02, n=9, r=0.013)
            hk = end
        else:
            hk = top + v3(0, -0.30, 0.0)
            chain(add, top, hk, sag=0.0, n=6, r=0.013)
        add(Torus(hk + v3(0, -0.035, 0), v3(0, 0, 1), 0.035, 0.009), 'iron')
    mats = base_mats(P)
    mats.update({
        'greatcoat': salted(ROAD, 0.35, ground=0.7, gamt=0.9),
        'cape': salted(STEEL, 0.35),
        'hat': salted(INK, 0.4),
        'hair': Material(_hex('#4a3a2e'), spec=0.2, brush=0.1),
        'skin': skin_mat(P, skin=W['skin_mid'], hair=_hex('#4a3a2e'), beard=_hex('#6e5a48')),
        'barbar': rod_mat('_ba', '_bb', P, band=0.075),
    })
    return finish(P, FACTION, parts, mats)


ROWS, _frames = humanoid_rows(neutral_pose, attack_style='cast', weapon_side='r', cast_side='l')


def frames():
    # attack is a toll-chain lash: the staff hand jerks forward and the chain whips out from the bar
    f = _frames()
    att = []
    for i in range(4):
        P = neutral_pose()
        rig.lean(P, fwd=np.radians([-6, 2, 10, 4][i]))
        w = P['wr_r'] + v3(0, [0.0, 0.02, -0.02, 0.0][i], [-0.06, 0.06, 0.20, 0.10][i])
        rig.place_arm(P, 'r', w, (-1, -0.4, -0.5))
        P['item_r'] = norm(v3(-0.04, 1.0, [-0.15, 0.05, 0.30, 0.15][i]))
        P['cast_glow'] = [0.15, 0.45, 1.0, 0.55][i]
        P['head_pitch'] = np.radians([-6, 0, 8, 2][i])
        P['skirt_sway'] = [0.2, 0.0, -0.4, -0.2][i]
        att.append((P, {}))
    f['attack'] = att
    return f

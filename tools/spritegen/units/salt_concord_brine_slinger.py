"""Brine Slinger (Salt Concord ranged salt).

A miner turned skirmisher: bare scarred forearms, a squared leather apron over road-grey work clothes,
a steel-blue head-wrap, and a heavy satchel of cut brine pans (white salt slabs) on the hip. The sling
whirls a slab of salt-glass. Defining detail: the satchel of white salt pans.
"""
import numpy as np
from kit.humanoid import *
from kit.anim import humanoid_rows
from kit.looks import LOOKS
from _salt_concord_common import *
from kit.fx import emit

UNIT_ID = 'salt_concord_brine_slinger'
FACTION = 'salt_concord'
LOOK = LOOKS[FACTION]

C = Costume(top='work', sleeve='shirt', legs='road', hand='skin', skirt=None, head='hood', head_mat='wrap',
            belt='leather', girth=0.95, boots_tall=True)


def neutral_pose():
    P = base_pose(height=0.96, build=1.0)
    # weight back, sling hanging loaded from the right hand, left hand fishing in the satchel
    rig.place_arm(P, 'r', v3(-0.26, 0.98, 0.10), (-1, -0.2, -0.4))
    P['item_r'] = norm(v3(-0.5, -0.8, 0.45))
    rig.place_arm(P, 'l', v3(0.21, 0.97, 0.13), (0.35, -1.0, -0.35))   # elbow down, not akimbo
    P['head_yaw'] = np.radians(-14)
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    # squared leather apron (front panel only) and shoulder strap
    tabard(P, add, 'apron', width=0.12, hem=0.50, top=0.10, zf=0.085, back=False)
    add(Capsule(ch + v3(-0.12, 0.14, 0.09), pel + v3(0.15, 0.02, 0.06), 0.014), 'leather')
    # squared canvas shoulder cape (miner's dust cape), salt-crusted
    add(capelet_shell(P, depth=0.16, width=0.22, sq=4.5), 'canvas')
    # back rack of cut brine pans: three white slabs standing above the shoulder
    for i, (x, hh, tl) in enumerate(((-0.07, 0.20, 0.10), (0.02, 0.26, -0.04), (0.10, 0.18, -0.15))):
        add(RoundBox(ch + v3(x, 0.10 + hh * 0.5, -0.17 - 0.012 * i), (0.045, hh * 0.5 + 0.04, 0.013), 0.005, rot_z(tl)), 'crystal')
    add(RoundBox(ch + v3(0.01, 0.0, -0.16), (0.13, 0.06, 0.035), 0.01), 'leather')
    # steel-blue miner's sash tied at the hip
    add(Capsule(pel + v3(-0.14, 0.10, 0.07), pel + v3(-0.17, -0.12, 0.10), 0.03, 0.02), 'wrap', 0.01)
    # satchel of salt pans on the left hip
    sc = pel + v3(0.19, -0.02, 0.09)
    add(RoundBox(sc, (0.06, 0.09, 0.10), 0.02, rot_y(0.5)), 'leather', 0.0)
    for i, (dx, dz, tilt) in enumerate(((0.0, -0.04, 0.1), (0.005, 0.0, -0.08), (0.0, 0.045, 0.15))):
        add(RoundBox(sc + v3(dx, 0.125 + 0.012 * i, dz), (0.045, 0.045, 0.014), 0.004, rot_y(0.5) @ rot_z(tilt)), 'crystal')
    # wrist wraps and miner's knee pads
    for s in ('r', 'l'):
        el, wr = P['el_' + s], P['wr_' + s]
        add(Capsule(el + (wr - el) * 0.6, wr, 0.044), 'wraps', 0.01)
        add(RoundBox(P['kn_' + s] + v3(0, 0.0, 0.05), (0.05, 0.06, 0.02), 0.012), 'leather')
    # sling: two cords and a cut salt slab in the pouch
    d = P['item_r']
    if d is not None:
        d = norm(d)
        g = hand_pos(P, 'r')
        tip = g + d * 0.40
        sv = norm(np.cross(d, v3(0, 0, 1)) + 1e-6)
        add(Capsule(g, tip + sv * 0.03, 0.005), 'leather')
        add(Capsule(g, tip - sv * 0.03, 0.005), 'leather')
        add(RoundBox(tip + d * 0.02, (0.06, 0.055, 0.02), 0.006, basis_from(d, (0, 0, 1))), 'crystal')
        if P['fx'] > 0:
            emit(add, tip + d * 0.15, 'spray', 0.8 + 1.0 * P['fx'])
    mats = base_mats(P)
    mats.update({
        # pale salt and steel blue, like the rest of the line: rolled road-grey sleeves instead of bare
        # arms (bare skin and dark leather read as Compact at board scale)
        'work': salted(_hex('#c4bcaa'), 0.35, ground=0.6, gamt=0.9),
        'shirt': salted(ROAD, 0.3),
        'apron': salted(STEEL_DK, 0.45, ground=0.8, gamt=1.0, spec=0.15, gloss=16),
        'wrap': salted(STEEL, 0.3),
        'wraps': salted(CANVAS, 0.2),
        'skin': skin_mat(P, skin=W['skin_mid'], hair=_hex('#2c2018')),
    })
    return finish(P, FACTION, parts, mats)


ROWS, frames = humanoid_rows(neutral_pose, attack_style='swing', weapon_side='r')

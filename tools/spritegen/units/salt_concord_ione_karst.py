"""Magister Ione Karst, Assayer of the Saltpan Verge (Salt Concord hero).

Chief salt-alchemist: tall and spare, in a long ink-blue robe under a squared salt-white assayer's
scapular marked with brass assay stamps, a tall flat-topped assayer's cap with a brass band, round
brass spectacles, a bandolier of sample vials and a brass assay rod crowned with a hexagonal salt
crystal that glows cold white. Cast (Crystal Bulwark): salt prisms burst up around her.
Defining detail: the glowing crystal-tipped assay rod.
"""
import numpy as np
from kit.humanoid import *
from kit.anim import humanoid_rows
from kit.looks import LOOKS
from _salt_concord_common import *

UNIT_ID = 'salt_concord_ione_karst'
FACTION = 'salt_concord'
LOOK = LOOKS[FACTION]
GLOW = _hex('#e6f6ff')
VIAL = [_hex('#9fe3d8'), _hex('#e3c27a'), _hex('#d9e4ea'), _hex('#c98a7a'), _hex('#9fe3d8')]

C = Costume(top='robe', sleeve='robe', legs='road', hand='glove', skirt='robe', skirt_mat='robe', hem=0.07,
            flare=0.8, head='hair', hair='hair', hair_style='bob', belt='leather', girth=0.85, neck_len=1.05)


def neutral_pose():
    P = base_pose(height=1.06, build=0.9)
    rig.place_arm(P, 'r', v3(-0.34, 1.20, 0.16), (-1, -0.4, -0.5))
    P['item_r'] = norm(v3(-0.08, 1.0, 0.06))
    rig.place_arm(P, 'l', v3(0.12, 1.22, 0.24), (1, -0.4, -0.5))     # holds a sample up to the light
    P['head_yaw'] = np.radians(-4)
    P['head_pitch'] = np.radians(6)
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    H, R, h = P['head'], head_R(P), P['height']
    cg = P['cast_glow']
    # tall flat-topped assayer's cap
    add(RoundBox(H + R @ v3(0, 0.15, -0.015) * h, (0.078, 0.085, 0.084), 0.02, R), 'cap')
    add(RoundBox(H + R @ v3(0, 0.085, -0.015) * h, (0.083, 0.014, 0.089), 0.006, R), 'brass')
    # spectacles: two brass rings in front of the eyes
    for sx in (-1, 1):
        add(Torus(H + R @ v3(sx * 0.035, 0.005, 0.088) * h, R[:, 2], 0.019, 0.0045), 'brass')
    # salt-white scapular front and back with brass stamps
    tabard(P, add, 'scapular', width=0.095, hem=0.36, top=0.52, zf=0.10, zb=0.09)
    for i in range(3):
        add(Cylinder(ch + v3(0, -0.02 - 0.09 * i, 0.115), ch + v3(0, -0.02 - 0.09 * i, 0.125), 0.017, 0.004), 'brass')
    add(Torus(nk + v3(0, -0.03, 0.0), v3(0, 1, 0.1), 0.07, 0.02), 'scapular', 0.01)
    # bandolier of sample vials
    a, b = P['sh_l'] + v3(-0.04, 0.0, 0.08), pel + v3(-0.15, 0.08, 0.10)
    add(Capsule(a, b, 0.016), 'leather')
    for i in range(5):
        t = 0.25 + i * 0.14
        c = a * (1 - t) + b * t + v3(0, 0, 0.022)
        add(Capsule(c + v3(0, -0.025, 0), c + v3(0, 0.025, 0), 0.012), 'vial%d' % i)
        add(Cylinder(c + v3(0, 0.025, 0), c + v3(0, 0.035, 0), 0.010), 'brass')
    # sample held up in the left hand: a small salt prism
    gl = hand_pos(P, 'l')
    crystal(add, gl + v3(0, 0.02, 0.0), 0.15, 0.032, 'rodcrystal', tilt=v3(0.2, 1, 0.2))
    # assay rod: slim brass rod with a squared collar cage and a glowing hexagonal salt crystal
    d = P['item_r']
    tip = None
    if d is not None:
        d = norm(d)
        g = hand_pos(P, 'r')
        butt, top = g - d * 1.15, g + d * 0.74
        add(Capsule(butt, top, 0.014), 'brass')
        add(Cylinder(butt, butt + d * 0.05, 0.02, 0.004), 'iron')
        add(RoundBox(top, (0.04, 0.02, 0.04), 0.006, basis_from(d, (0, 0, 1))), 'brass')
        for k in range(4):
            ang = k * np.pi / 2 + 0.6
            o = basis_from(d, (0, 0, 1)) @ v3(np.cos(ang), 0, np.sin(ang))
            add(Capsule(top + o * 0.035, top + o * 0.05 + d * 0.16, 0.006), 'brass')
        crystal(add, top - d * 0.01, 0.27, 0.055, 'rodcrystal', tilt=d)
        tip = top + d * 0.12
    # crystal bulwark: prisms burst out of the ground around her when casting
    if cg > 0.05:
        for i, (x, z, hh) in enumerate(((-0.42, 0.18, 0.55), (-0.22, 0.32, 0.70), (0.10, 0.34, 0.5), (0.36, 0.20, 0.62),
                                        (0.45, -0.10, 0.45), (-0.45, -0.15, 0.40))):
            crystal(add, v3(x, -0.02, z), hh * cg, 0.06, 'bulwark', tilt=v3(x * 0.5, 1, z * 0.4))
    mats = base_mats(P)
    gl_amt = P['glow'] * (1 - P['end'])
    mats.update({
        'robe': salted(_hex('#2c3c52'), 0.3, ground=0.8, gamt=1.0),
        'scapular': tabard_mat(P, width=0.095 * 0.9 + 0.01, stripe=None, border=STEEL),
        'cap': salted(INK, 0.3),
        'hair': Material(_hex('#2a2220'), spec=0.25, brush=0.1),
        'skin': skin_mat(P, skin=_hex('#d9a888'), hair=_hex('#2a2220'), lips=_hex('#94505a')),
        'rodcrystal': crystal_mat(glow=0.8 * gl_amt + 0.6 * cg),
        'bulwark': crystal_mat(glow=0.25 * cg),
    })
    for i, c in enumerate(VIAL):
        mats['vial%d' % i] = Material(c, spec=0.9, gloss=60, brush=0.02, emissive=tuple(np.array(c) * 0.15))
    lights = [Light(tip, GLOW, 1.1 * gl_amt + 1.4 * cg, 0.35)] if tip is not None else []
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = humanoid_rows(neutral_pose, attack_style='swing', weapon_side='r', cast_side='l')

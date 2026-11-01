"""Snare-Tinker (Salvage Compact, controller). Hunched under a towering pack-frame of junk: a coiled
net, a slick barrel, a rope coil, bits of hull. Spanner in the right hand, goggles up, head wrap.
Defining detail: the overloaded junk pack. Tell: a small tin lantern on the pack flickers."""
import numpy as np
from _salvage_compact_common import *

UNIT_ID = 'salvage_compact_snare_tinker'
FACTION = 'salvage_compact'

C = Costume(top='coat', sleeve='coat2', legs='trousers', hand='glove', skirt=None, head='bald',
            belt='rope', girth=0.95)


def neutral_pose():
    P = base_pose(height=0.90, build=0.95)
    rig.lean(P, fwd=np.radians(16), side=np.radians(4))
    P['head_pitch'] = np.radians(-16)
    P['head_yaw'] = np.radians(-20)
    rig.place_arm(P, 'r', v3(-0.26, 0.92, 0.18), (-0.35, -0.3, -1))
    P['item_r'] = norm(v3(-0.1, 0.6, 0.8))
    rig.place_arm(P, 'l', v3(0.24, 0.90, 0.12), (0.35, -0.2, -1))
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    add(ragged_coat(P, hem_lo=0.42, hem_hi=0.60, slope=-1, opening=0.5, flare=0.7), 'coat', 0.0)
    wrap_head(P, add, 'coat2', knot_side=1)
    goggles(P, add, up=True)
    ch, nk = P['chest'], P['neck']
    # pack frame: two poles, a crossbar, all lashed
    back = ch + v3(0, 0, -0.17)
    fwd = norm(nk - P['pelvis'])
    a1, b1 = back + v3(-0.14, -0.3, -0.02), back + v3(-0.10, 0.45, -0.06)
    a2, b2 = back + v3(0.14, -0.3, -0.02), back + v3(0.18, 0.38, -0.04)
    add(Capsule(a1, b1, 0.016), 'wood', 0.0)
    add(Capsule(a2, b2, 0.016), 'wood', 0.0)
    add(Capsule(back + v3(-0.2, 0.2, -0.06), back + v3(0.24, 0.12, -0.05), 0.014), 'wood', 0.0)
    # slick barrel (oil) on the bottom, net bundle above, rope coil, hull scrap fan sticking out
    keg(add, back + v3(0.0, -0.12, -0.12), up=(1, 0.1, 0), r=0.10, hh=0.13, mat='plate', hoop='tin')
    add(Ellipsoid(back + v3(-0.02, 0.18, -0.14), (0.17, 0.12, 0.11)), 'net', 0.02)
    add(Torus(back + v3(0.10, 0.36, -0.10), v3(0.2, 0.3, 1), 0.08, 0.025), 'rope', 0.0)
    add(RoundBox(back + v3(-0.15, 0.36, -0.12), (0.06, 0.14, 0.008), 0.004, rot_z(0.5)), 'rust', 0.0)
    lc = b1 + v3(-0.06, -0.06, 0.02)
    add(Capsule(b1, lc + v3(0, 0.07, 0), 0.006), 'tin', 0.0)
    tin_lantern(add, lights, lc, P['glow'] * 0.6, size=0.8)
    # spanner
    d = P['item_r']
    if d is not None:
        d = norm(d)
        g = hand_pos(P, 'r')
        add(Capsule(g - d * 0.06, g + d * 0.38, 0.016), 'iron', 0.0)
        sv = norm(np.cross(d, v3(0, 1, 0.2)))
        jc = g + d * 0.43
        add(Torus(jc, np.cross(d, sv), 0.05, 0.02), 'iron', 0.0)
    if P['cast_glow'] > 0.05:
        g = hand_pos(P, 'l')
        add(Ellipsoid(g + v3(0.04, 0.06, 0.06), (0.08 + 0.08 * P['cast_glow'], 0.06, 0.08 + 0.06 * P['cast_glow'])), 'net', 0.02)
    mats = sv_materials(P, skin='weathered', hair=_hex('#3a2a1e'), coat_seed=9,
                        coat_colors=(DRAB, CANVAS, OCHRE, SAILCLOTH, MUTED_RUST))
    mats['net'] = Material(lambda p, n: np.where(((np.sin(p[:, 0] * 180 + p[:, 1] * 120) > 0.5) |
                                                  (np.sin(p[:, 2] * 180 - p[:, 1] * 120) > 0.5))[:, None],
                                                 _arr(_hex('#b39a6a'), len(p)), _arr(_hex('#4a3b2c'), len(p))),
                           spec=0.02, brush=0.04)
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = sv_rows(neutral_pose, attack_style='swing', weapon_side='r', fidget='look', cast_side='l')

"""Odo Brask, Fixer of the Kettle Market (Salvage Compact hero). A fat, cheerful broker in THREE coats,
each a different length and colour (long oilskin outer, rust middle, bone inner), flat cap, a knotted
cudgel, a fat coin purse and a dangling tin lantern. Wide, round, asymmetric."""
import numpy as np
from _salvage_compact_common import *

UNIT_ID = 'salvage_compact_odo_brask'
FACTION = 'salvage_compact'

C = Costume(top='coat3', sleeve='coat1', legs='trousers', hand='glove', skirt=None, head='cap',
            head_mat='cap', hair='hair', hair_style='short', belt='leather', girth=1.9)


def neutral_pose():
    P = base_pose(height=0.98, build=1.28)
    rig.lean(P, fwd=np.radians(-4), side=np.radians(3))           # leaning back, belly out
    P['head_yaw'] = np.radians(-14)
    rig.place_arm(P, 'r', v3(-0.36, 1.00, 0.16), (-0.35, -0.2, -1))
    P['item_r'] = norm(v3(-0.2, -0.2, 0.9))
    rig.place_arm(P, 'l', v3(0.30, 1.12, 0.22), (0.35, -0.5, -1))
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    g = 1.9
    pel, ch, h = P['pelvis'], P['chest'], P['height']
    # belly
    add(Ellipsoid(pel + v3(0, 0.18, 0.05), (0.21 * 1.28, 0.2, 0.19)), 'coat3', 0.05)
    # three coats, three hems: inner bone (longest at the left), middle rust, outer oilskin
    add(ragged_coat(P, hem_lo=0.22, hem_hi=0.34, slope=1, opening=0.25, flare=0.9, girth=g * 1.0), 'coat3', 0.0)
    add(ragged_coat(P, hem_lo=0.36, hem_hi=0.56, slope=-1, opening=0.45, flare=0.95, girth=g * 1.12, top=1.12), 'coat2', 0.0)
    add(ragged_coat(P, hem_lo=0.12, hem_hi=0.60, slope=1, opening=0.85, flare=1.1, girth=g * 1.24, top=1.24, notch=0.06), 'coat1', 0.0)
    # outer coat shoulders/collar
    nk = P['neck']
    add(Torus(nk + v3(0, -0.02, 0), v3(0, 1, 0.1), 0.085 * 1.28, 0.03), 'fur', 0.01)
    # face: jowls and a grin
    H, Rh = P['head'], head_R(P)
    add(Ellipsoid(H + Rh @ v3(0, -0.06, 0.02) * h, (0.075, 0.055, 0.065), Rh), 'skin', 0.03)
    # cudgel
    d = P['item_r']
    if d is not None:
        d = norm(d)
        gr = hand_pos(P, 'r')
        add(Capsule(gr - d * 0.08, gr + d * 0.55, 0.02, 0.05), 'wood', 0.01)
        for k in range(3):
            add(Sphere(gr + d * (0.35 + 0.08 * k) + v3(0.02 * (k - 1), 0.03, 0.02 * k), 0.025), 'wood', 0.01)
        add(Torus(gr + d * 0.5, d, 0.05, 0.008), 'iron', 0.0)
    # purse in the left hand, jingling
    gl = hand_pos(P, 'l')
    add(Capsule(gl, gl + v3(0, -0.07, 0.02), 0.005), 'iron', 0.0)
    tin_lantern(add, lights, gl + v3(0, -0.13, 0.03), P['glow'], size=1.0)
    pc = pel + v3(-0.10, 0.02, 0.30)
    add(Sphere(pc, 0.055), 'leather', 0.02)
    add(Cylinder(pc + v3(0, 0.04, 0), pc + v3(0, 0.06, 0), 0.022, 0.004), 'brass', 0.0)
    if P['cast_glow'] > 0.05:   # Buy Out: coins tossed up
        for k in range(5):
            c = gl + v3(0.04 * np.sin(k * 2.1), 0.08 + 0.05 * k * P['cast_glow'], 0.04 * np.cos(k * 2.1) + 0.05)
            add(Cylinder(c, c + v3(0.004, 0.005, 0.002), 0.018, 0.002), 'gold', 0.0)
        lights.append(Light(pos=gl + v3(0, 0.15, 0.05), color=_hex('#ffd27a'), intensity=1.0 * P['cast_glow'], radius=0.2))
    # tin lantern hanging off the outer coat's belt
    # ledger tags and a pocket watch chain across the belly
    for k in range(5):
        t = k / 4
        add(Sphere(pel + v3(-0.15 + 0.3 * t, 0.2 - 0.07 * np.sin(np.pi * t), 0.27), 0.009), 'brass', 0.0)
    mats = sv_materials(P, skin='light', hair=_hex('#6a4a30'), coat_seed=23)
    mats['coat1'] = Material(patchwork(lambda: P['pelvis'], (OILSKIN, DRAB, _hex('#3e382f'), MUTED_RUST), cell=0.12, seed=4, mute=0.6, rot=-0.7),
                             spec=0.25, gloss=18, brush=0.08)
    mats['coat2'] = Material(patchwork(lambda: P['pelvis'], (MUTED_RUST, RUST, OCHRE), cell=0.12, seed=6, mute=0.5),
                             spec=0.05, brush=0.1)
    mats['coat3'] = Material(patchwork(lambda: P['pelvis'], (SAILCLOTH, OCHRE, CANVAS), cell=0.1, seed=8, mute=0.3),
                             spec=0.03, brush=0.08)
    mats['cap'] = Material(_hex('#5a4c3a'), spec=0.05, brush=0.1)
    mats['fur'] = Material(_hex('#7a6a52'), spec=0.02, brush=0.14)
    mats['gold'] = Material(_hex('#d9b25a'), spec=1.0, gloss=50, metal=0.9)
    mats['skin'] = Material(face_albedo(P, SKINS['light'], _hex('#6a4a30'), lips=_hex('#9a4a40')), spec=0.1, gloss=14, sss=0.7, brush=0.02)
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = sv_rows(neutral_pose, attack_style='swing', weapon_side='r', fidget='sway', cast_side='l')

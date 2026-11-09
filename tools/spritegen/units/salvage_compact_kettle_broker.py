"""Kettle Broker (Salvage Compact economy).

Hunched pedlar of the Kettle Market under a towering lashed pack of tin kettles, rolled canvas and a
rope coil, a tin lantern swinging from the frame; sailcloth coat patched in ochre, rust scarf and a
slouch cap. One hand holds up a balance scale with a coin heap in a pan, the other offers a dented kettle
as a sales pitch. Defining detail: the kettle tower on his back.
"""
import numpy as np
from _salvage_compact_common import *
from _salvage_compact_w2 import *

UNIT_ID = 'salvage_compact_kettle_broker'
FACTION = 'salvage_compact'

C = Costume(top='coat', sleeve='coat', legs='trousers', hand='glove', skirt=None, head='cap', head_mat='coat2',
            hair='hair', hair_style='short', belt='leather', girth=1.1, boots_tall=False)


def neutral_pose():
    P = base_pose(height=0.94, build=0.98)
    rig.lean(P, fwd=np.radians(11))
    P['head_yaw'] = np.radians(-16)
    P['head_pitch'] = np.radians(-8)
    rig.place_arm(P, 'r', v3(-0.30, 1.16, 0.30), (-1, -0.3, -0.5))
    P['item_r'] = norm(v3(-0.2, 0.2, 1.0))
    rig.place_arm(P, 'l', v3(0.22, 1.24, 0.28), (0.5, -0.5, -0.6))
    P['pan_tip'] = 0.0
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    H, R, h, b = P['height'], None, P['height'], P['build']
    # short ragged coat tails and a wound scarf
    add(ragged_coat(P, hem_lo=0.38, hem_hi=0.58, slope=1, opening=0.5, flare=0.8, girth=1.1, top=1.0), 'coat', 0.0)
    scarf(P, add, 'rustcloth', tail=True, side=1)
    knit_cap(P, add, 'coat2', slouch=1.3)
    # the kettle tower: wooden carrying frame, lashed kettles stacked up past the head
    base = ch + v3(0, -0.04, -0.20)
    add(RoundBox(base + v3(0, 0.12, -0.20), (0.19, 0.40, 0.025), 0.015, rot_x(0.08)), 'wood', 0.0)
    add(Capsule(base + v3(-0.17, -0.28, 0.02), base + v3(-0.17, 0.45, -0.06), 0.018), 'wood', 0.0)
    add(Capsule(base + v3(0.17, -0.28, 0.02), base + v3(0.17, 0.45, -0.06), 0.018), 'wood', 0.0)
    ks = [((-0.10, 0.12, -0.12), 0.115, 'tin', (-1, 0.2, 0.3)), ((0.10, 0.40, -0.14), 0.105, 'tin', (1, 0.3, -0.4))]
    for off, r, m, sp in ks:
        kettle(add, base + v3(off[0], off[1], off[2] + 0.13), r=r, spout=sp, mat=m)
    add(Cylinder(base + v3(-0.14, -0.10, -0.04), base + v3(0.14, -0.10, -0.04), 0.06, 0.015), 'canvas', 0.0)  # rolled canvas
    lash(add, base + v3(-0.17, -0.2, -0.04), base + v3(-0.17, 0.4, -0.08), n=2, r=0.03, at=(0.3, 0.7, 0.85))
    lash(add, base + v3(0.17, -0.2, -0.04), base + v3(0.17, 0.4, -0.08), n=2, r=0.03, at=(0.3, 0.7, 0.85))
    # balance scale in the left hand
    g = hand_pos(P, 'l')
    balance(add, g + v3(0, 0.07, 0.0), norm(v3(0.7, 0.0, 0.7)) * 1.0, tip=P['pan_tip'], beam=0.19, drop=0.17)
    add(Capsule(g, g + v3(0, 0.07, 0), 0.008), 'brass', 0.0)
    # kettle on offer in the right hand (hangs from its bail)
    d = P['item_r']
    if d is not None:
        gr = hand_pos(P, 'r')
        sw = P.get('swing', v3(0, 0, 0))
        kc = gr + v3(0.0, -0.17, 0.0) + sw
        add(Torus(kc + v3(0, 0.07, 0), v3(0, 0, 1), 0.06, 0.008), 'iron', 0.0)
        kettle(add, kc, r=0.095, spout=(0.3, 0.2, 1.0), mat='copperk', handle=False)
    mats = sv_materials(P, skin='mid', hair=_hex('#4a3626'))
    mats.update({
        'coat': Material(_hex('#4a4038'), spec=0.03, brush=0.1),
        'rustcloth': Material(_hex('#b5583a'), spec=0.04, brush=0.1),
        'copperk': Material(_hex('#d28a50'), spec=0.7, gloss=30, metal=0.6, brush=0.06),
        'tin': Material(_hex('#a9aba2'), spec=0.7, gloss=34, metal=0.6, brush=0.06),
        'iron': Material(_hex('#4a4f56'), spec=0.5, gloss=24, metal=0.6, brush=0.05),
        'gold': Material(_hex('#e0b85a'), spec=1.0, gloss=50, metal=0.9),
    })
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, _frames = sv_rows(neutral_pose, attack_style='swing', weapon_side='r', fidget='shoulder', cast_side='l')


def frames():
    f = _frames()
    for row, fr in f.items():
        for i, (P, lo) in enumerate(fr):
            t = P['tell'] * 6.283
            if row == 'idle':
                P['pan_tip'] = np.sin(t)
                P['swing'] = v3(0.0, 0, 0.04 * np.sin(t))
            elif row == 'move':
                P['pan_tip'] = [0.5, 0, -0.5, 0][i]
                P['swing'] = v3(0, 0, [0.08, 0, -0.08, 0][i])
            elif row == 'attack':
                P['swing'] = [v3(0, 0, -0.12), v3(0, 0.0, 0.10), v3(0, 0.0, 0.26), v3(0, 0, 0.12)][i]
                P['pan_tip'] = [0, 0.5, 1, 0.3][i]
            elif row == 'cast':
                P['pan_tip'] = [0.4, -1, 0.3][i]
            else:
                P['pan_tip'] = 0.3
    return f

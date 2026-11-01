"""Glassgrinder (Lanternkeepers controller). Cuts and polishes the great lenses.

Leather apron over a sea-grey smock, goggles pushed up on the brow, rolled sleeves. Carries a
lens on a tall stand in the left hand, a little lamp behind the glass so the whole stand is a
projector. Defining detail: the hand lens in the right, flicked up on the attack in a dazzle flash.
"""
import numpy as np
from _lanternkeepers_common import *

UNIT_ID = 'lanternkeepers_glassgrinder'
FACTION = 'lanternkeepers'
LOOK = LOOKS[FACTION]

C = Costume(top='coatgrey', sleeve='canvas', legs='slate', boot='boot', hand='skin', skirt='coat',
            skirt_mat='coatgrey', hem=0.50, flare=0.5, head='hair', hair='hair', hair_style='bob', belt='leather', girth=0.95)


def neutral_pose():
    P = base_pose(height=0.95, build=0.95)
    h = P['height']
    P['head_pitch'] = np.radians(2)
    rig.place_arm(P, 'l', v3(0.27, 1.08, 0.18), (1, -0.4, -0.4), l1=0.27 * h, l2=0.26 * h)
    P['item_l'] = norm(v3(0.0, 1.0, 0.02))
    rig.place_arm(P, 'r', v3(-0.20, 1.02, 0.22), (-1, -0.4, -0.5), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(-0.1, 0.7, 0.7))
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    goggles(add, P)
    # lens stand: pole, lamp, and the big lens in front of it
    d = P['item_l']
    if d is not None:
        d = norm(d)
        g = hand_pos(P, 'l')
        butt, top = g - d * 1.02, g + d * 0.80
        add(Capsule(butt, top, 0.016, 0.014), 'wood')
        for k in (-1, 1):   # tripod feet at the bottom
            add(Capsule(butt + d * 0.18, butt + v3(k * 0.08, 0.0, -0.06), 0.008), 'darkiron')
        fwd = norm(v3(-0.35, 0, 1.0))
        add(Capsule(top - d * 0.06, top + fwd * 0.06 - d * 0.06, 0.008), 'brass')
        lens_disc(add, top + fwd * 0.10 - d * 0.02, fwd, 0.095, rim='brass')
        box_lamp(add, lights, P, top - fwd * 0.07 + d * 0.07, size=0.75, frame='darkiron', light=1.6)
    # leather apron, front only
    pel, ch = P['pelvis'], P['chest']
    a_top, a_mid = ch + v3(0, 0.08, 0.105), pel + v3(0, 0.08, 0.125)
    a_bot = pel + v3(0, -0.42, 0.15 + 0.03 * P['skirt_sway'])
    add(RoundBox((a_top + a_mid) / 2, (0.07, np.linalg.norm(a_top - a_mid) / 2, 0.008), 0.006,
                 basis_from(a_top - a_mid, (0, 0, 1))), 'apron')
    def skirt(p, a=a_mid, b=a_bot):
        ax = norm(a - b)
        R = basis_from(ax, (0, 0, 1))
        q = (p - (a + b) / 2) @ R
        L = np.linalg.norm(a - b) / 2
        t = np.clip((L - q[:, 1]) / (2 * L), 0, 1)
        w = 0.10 + 0.05 * t
        return np.maximum(np.maximum(np.abs(q[:, 0]) - w, np.abs(q[:, 1]) - L), np.abs(q[:, 2]) - 0.008) - 0.004
    add(Func(skirt, (a_mid + a_bot) / 2, 0.35), 'apron')
    add(Capsule(a_top + v3(-0.06, 0, -0.02), P['neck'] + v3(0, 0.0, -0.03), 0.007), 'leather')
    add(Capsule(a_top + v3(0.06, 0, -0.02), P['neck'] + v3(0, 0.0, -0.03), 0.007), 'leather')
    # hand lens in the right hand
    gr = hand_pos(P, 'r')
    dr = norm(P['item_r']) if P['item_r'] is not None else v3(0, 1, 0)
    add(Capsule(gr - dr * 0.03, gr + dr * 0.07, 0.009), 'wood')
    lc = gr + dr * 0.13
    lens_disc(add, lc, dr * 0.3 + v3(-0.3, 0, 1), 0.05, rim='brass')
    if P['fx'] > 0:
        add(Sphere(lc + v3(-0.03, 0, 0.06), 0.06 * P['fx']), 'flash')
        light_at(lights, P, lc + v3(0, 0, 0.08), 2.5 * P['fx'], 0.2, color=_hex('#fff2c0'))
    mats = keeper_mats(P, hair=_hex('#9a6a3e'), skin=W['skin_light'])
    mats['apron'] = Material(noisy(_hex('#6e5440'), 0.12), spec=0.2, gloss=20, brush=0.08)
    mats['lens']  = Material(LENS, spec=1.4, gloss=90, emissive=tuple(np.array(LENS) * (0.35 + 0.65 * max(P['cast_glow'], P['fx']))), rim=0.8, brush=0.0)
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = keeper_rows(neutral_pose, attack_style='shoot', weapon_side='r', cast_side='r', pole='l')

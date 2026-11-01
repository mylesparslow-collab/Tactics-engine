"""Signalman (Lanternkeepers ranged marker). Flashes shutter-codes between lighthouses.

Keeper's cap, sea-grey coat with an oilskin storm cape, a shuttered signal lamp in the right hand
that he aims like a gun, and a signal mast on his back with two lamps stacked at the top.
Defining detail: the shutter slats snap open on the hit frame and the flash lands.
"""
import numpy as np
from _lanternkeepers_common import *

UNIT_ID = 'lanternkeepers_signalman'
FACTION = 'lanternkeepers'
LOOK = LOOKS[FACTION]

C = Costume(top='coatgrey', sleeve='coatgrey', legs='slate', boot='boot', hand='glove', skirt='coat',
            skirt_mat='coatgrey', hem=0.40, flare=0.6, head='hair', hair='hair', hair_style='short',
            belt='leather', girth=0.95)


def neutral_pose():
    P = base_pose(height=1.0, build=0.95)
    h = P['height']
    rig.place_arm(P, 'r', v3(-0.24, 1.02, 0.16), (-1, -0.3, -0.5), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(-0.2, -0.1, 1.0))
    return P


def signal_lamp(add, lights, P):
    d = P['item_r']
    if d is None:
        return
    d = norm(d)
    g = hand_pos(P, 'r')
    R = basis_from(d, (0, 1, 0))
    up = R[:, 2] if R[:, 2][1] > 0 else -R[:, 2]
    c = g + up * 0.07 + d * 0.06
    add(Cylinder(c - d * 0.10, c + d * 0.10, 0.068, 0.012), 'darkiron')
    add(Cylinder(c + d * 0.095, c + d * 0.112, 0.060, 0.004), 'lamp')
    add(Torus(c + d * 0.11, d, 0.066, 0.008), 'darkiron')
    add(Cylinder(c + up * 0.05, c + up * 0.11, 0.022, 0.006), 'darkiron')            # chimney
    add(Capsule(g, c - up * 0.05, 0.012), 'darkiron')                                 # grip
    fx = P['fx']
    side = norm(np.cross(d, up))
    for k in (-1, 0, 1):
        sc = c + d * 0.125 + up * (k * 0.038)
        # slats: closed = flat across the lens, open = turned edge-on
        Rs = np.stack([side, up * (1 - fx) + d * fx, np.cross(side, up * (1 - fx) + d * fx)], axis=1)
        add(RoundBox(sc, (0.064, 0.017, 0.004), 0.002, Rs), 'darkiron')
    light_at(lights, P, c + d * 0.2, 1.2 + 2.5 * fx, 0.2)
    if fx > 0:
        add(Capsule(c + d * 0.14, c + d * (0.14 + 0.32 * fx), 0.05 * fx, 0.02 * fx), 'flash')


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    keeper_cap(add, P, 'slate')
    mantle(add, P, 'oilskin', depth=0.20, width=0.17)
    signal_lamp(add, lights, P)
    # signal mast on the back: tower with two stacked lamps
    ch, pel = P['chest'], P['pelvis']
    up = norm(P['neck'] - pel)
    base = pel + v3(0.06, 0.05, -0.16)
    top = base + up * 1.0
    add(Capsule(base, top, 0.016, 0.013), 'wood')
    add(Capsule(ch + v3(0.10, 0.10, -0.11), ch + v3(-0.12, -0.15, 0.10), 0.011), 'leather')
    add(Capsule(top - up * 0.03 + v3(-0.06, 0, 0), top - up * 0.03 + v3(0.06, 0, 0), 0.007), 'darkiron')
    box_lamp(add, lights, P, top - up * 0.10 + v3(0.0, 0, 0.0), size=0.85, frame='darkiron', light=1.3)
    box_lamp(add, lights, P, top - up * 0.28 + v3(0.0, 0, 0.0), size=0.75, frame='darkiron', light=1.0)
    add(Capsule(top + v3(0.0, 0.0, 0), top + v3(0.0, 0.05, 0), 0.01), 'darkiron')
    # flag pennant
    add(RoundBox(top + v3(0.07, -0.02, 0.0), (0.06, 0.03, 0.003), 0.002), 'whitewash')
    mats = keeper_mats(P, hair=_hex('#2e2620'), skin=W['skin_dark'])
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = keeper_rows(neutral_pose, attack_style='shoot', weapon_side='r', cast_side='l')

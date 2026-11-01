"""Keeper of the Long Watch (Lanternkeepers commander). Has not slept a full night in forty years.

Tall and upright: a long night-slate greatcoat to the ankles with brass buttons and an oilskin
storm cape, grey beard, keeper's cap. Defining detail: the watch-staff, taller than he is, crowned
with a caged lamp (a lighthouse lantern room in miniature), and a ring of tower keys at the belt.
"""
import numpy as np
from _lanternkeepers_common import *

UNIT_ID = 'lanternkeepers_keeper_of_the_long_watch'
FACTION = 'lanternkeepers'
LOOK = LOOKS[FACTION]

C = Costume(top='wool', sleeve='wool', legs='slate', boot='boot', hand='glove', skirt='coat',
            skirt_mat='wool', hem=0.10, flare=0.6, head='bald', belt='leather', girth=1.1)


def neutral_pose():
    P = base_pose(height=1.1, build=1.06)
    h = P['height']
    P['head_yaw'] = np.radians(-16)
    rig.place_arm(P, 'l', v3(0.29, 1.22, 0.18), (1, -0.5, -0.4), l1=0.27 * h, l2=0.26 * h)
    P['item_l'] = norm(v3(0.03, 1.0, 0.02))
    rig.place_arm(P, 'r', v3(-0.22, 1.00, 0.10), (-1, -0.3, -0.5), l1=0.27 * h, l2=0.26 * h)
    return P


def lamp_room(add, lights, P, c, s=1.0):
    """Caged lamp: gallery ring, glass drum, six bars, domed cap with a finial."""
    add(Cylinder(c - v3(0, 0.075, 0) * s, c - v3(0, 0.06, 0) * s, 0.075 * s, 0.006), 'brass')
    add(Cylinder(c - v3(0, 0.055, 0) * s, c + v3(0, 0.05, 0) * s, 0.048 * s, 0.01), 'lamp')
    for k in range(6):
        a = k * np.pi / 3
        o = v3(np.cos(a), 0, np.sin(a)) * 0.056 * s
        add(Capsule(c + o - v3(0, 0.06, 0) * s, c + o + v3(0, 0.06, 0) * s, 0.0055 * s), 'darkiron')
    add(Capsule(c + v3(0, 0.065, 0) * s, c + v3(0, 0.085, 0) * s, 0.06 * s, 0.02 * s), 'darkiron')
    add(Capsule(c + v3(0, 0.09, 0) * s, c + v3(0, 0.13, 0) * s, 0.008 * s, 0.003), 'brass')
    flame(add, c - v3(0, 0.02, 0) * s + v3(0, 0, 0.0), P, 1.4 * s)
    light_at(lights, P, c + v3(0, 0, 0.06), 2.2 * s, 0.2)


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    keeper_cap(add, P, 'slate')
    mantle(add, P, 'oilskin', depth=0.22, width=0.19)
    # brass buttons down the coat front and lapels
    pel, nk = P['pelvis'], P['neck']
    for sx in (-1, 1):
        add(Capsule(nk + v3(sx * 0.05, -0.20, 0.10), pel + v3(sx * 0.02, 0.13, 0.10), 0.014, 0.010), 'whitewash')
    for i in range(4):
        t = 0.25 + i * 0.2
        add(Sphere((nk + v3(-0.075, -0.22, 0.105)) * (1 - t) + (pel + v3(-0.05, 0.14, 0.10)) * t, 0.011), 'brass')
    # key ring at the belt
    kc = pel + v3(-0.14, 0.02, 0.10)
    add(Torus(kc, v3(0, 0, 1), 0.03, 0.005), 'brass')
    for k in range(3):
        add(Capsule(kc + v3(-0.02 + k * 0.02, -0.02, 0.01), kc + v3(-0.03 + k * 0.025, -0.09, 0.012), 0.006), 'darkiron')
    # watch staff
    d = P['item_l']
    if d is not None:
        d = norm(d)
        g = hand_pos(P, 'l')
        butt, top = g - d * 1.30, g + d * 0.56
        add(Capsule(butt, top, 0.019, 0.016), 'wood')
        add(Cylinder(top - d * 0.03, top + d * 0.02, 0.03, 0.005), 'brass')
        lamp_room(add, lights, P, top + d * 0.10, 1.05)
    mats = keeper_mats(P, hair=_hex('#b9b4aa'), beard=_hex('#c4bfb5'), skin=W['skin_light'])
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = keeper_rows(neutral_pose, attack_style='cast', weapon_side='r', cast_side='r', pole='l')

"""Lantern Warden (Lanternkeepers support / healer). Tends the flame that tends the keepers.

Long closed sea-grey coat to the ankles, oilskin hood and storm cape, a shepherd's crook in the
left hand with a lantern hanging from the crook. Defining detail: the crook lantern, the warmest
light in the line; on the cast the right hand opens toward an ally and the lamp swells.
"""
import numpy as np
from _lanternkeepers_common import *

UNIT_ID = 'lanternkeepers_lantern_warden'
FACTION = 'lanternkeepers'
LOOK = LOOKS[FACTION]

C = Costume(top='seagrey', sleeve='seagrey', legs='slate', boot='boot', hand='skin', skirt='robe',
            skirt_mat='seagrey', hem=0.06, flare=0.55, head='hood', head_mat='oilskin', belt='leather', girth=0.95)


def neutral_pose():
    P = base_pose(height=1.0, build=0.92)
    h = P['height']
    P['head_pitch'] = np.radians(4)
    rig.place_arm(P, 'l', v3(0.26, 1.16, 0.16), (1, -0.5, -0.4), l1=0.27 * h, l2=0.26 * h)
    P['item_l'] = norm(v3(0.02, 1.0, 0.02))
    rig.place_arm(P, 'r', v3(-0.18, 1.00, 0.18), (-1, -0.4, -0.5), l1=0.27 * h, l2=0.26 * h)
    return P


def crook(add, lights, P):
    d = P['item_l']
    if d is None:
        return
    d = norm(d)
    g = hand_pos(P, 'l')
    butt, top = g - d * 1.12, g + d * 0.72
    add(Capsule(butt, top, 0.016, 0.014), 'wood')
    # crook hook curling forward-out
    side = norm(np.cross(d, v3(0, 0, 1)))
    if side[0] < 0:
        side = -side
    c = top + side * 0.075
    ax = norm(np.cross(d, side))
    def f(p, c=c, ax=ax, side=side, d=d):
        q = p - c
        y = q @ ax
        u, w = q @ side, q @ d
        r = np.sqrt(u * u + w * w)
        ring = np.sqrt((r - 0.075) ** 2 + y * y) - 0.013
        return np.maximum(ring, -w)            # upper half only
    add(Func(f, c, 0.1), 'wood', 0.0)
    tip = c + side * 0.075
    add(Capsule(tip, tip - v3(0, 0.05, 0), 0.006), 'darkiron')
    hurricane(add, lights, P, tip - v3(0, 0.05 + 0.10 * 1.2, 0), size=1.25, frame='brass', light=2.2)


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    mantle(add, P, 'oilskin', depth=0.21, width=0.17)
    crook(add, lights, P)
    # satchel of wicks and lint at the hip
    pel = P['pelvis']
    add(RoundBox(pel + v3(-0.17, 0.02, 0.04), (0.035, 0.06, 0.07), 0.015), 'leather')
    add(Capsule(P['chest'] + v3(0.11, 0.12, 0.08), pel + v3(-0.15, 0.08, 0.06), 0.010), 'leather')
    # cast: a warm glow gathered in the open right hand
    if P['cast_glow'] > 0.05:
        g = hand_pos(P, 'r') + v3(0, 0.05, 0.04)
        add(Sphere(g, 0.035 * P['cast_glow']), 'core')
        light_at(lights, P, g, 1.6 * P['cast_glow'], 0.2)
    mats = keeper_mats(P, hair=_hex('#8c8378'), skin=W['skin_light'])
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = keeper_rows(neutral_pose, attack_style='cast', weapon_side='r', cast_side='r', pole='l')

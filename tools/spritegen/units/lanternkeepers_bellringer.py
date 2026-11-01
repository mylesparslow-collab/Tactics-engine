"""Bellringer (Lanternkeepers summoner / controller). Rings the fog-bell that wakes the Lamplit.

Knit cap, slate coat under an oilskin storm cape, a bell mallet in the right hand. Defining
detail: a tall bell-post in the left hand, a gallows top with a dark iron fog-bell on one side
and its lamp on the other; on the cast the bell swings and the lamp flares.
"""
import numpy as np
from _lanternkeepers_common import *

UNIT_ID = 'lanternkeepers_bellringer'
FACTION = 'lanternkeepers'
LOOK = LOOKS[FACTION]

C = Costume(top='slate', sleeve='coatgrey', legs='slate', boot='boot', hand='glove', skirt='coat',
            skirt_mat='slate', hem=0.30, flare=0.65, head='cap', head_mat='knit', hair='hair', belt='leather',
            girth=1.0)


def neutral_pose():
    P = base_pose(height=1.0, build=1.0)
    h = P['height']
    rig.place_arm(P, 'l', v3(0.27, 1.12, 0.16), (1, -0.4, -0.4), l1=0.27 * h, l2=0.26 * h)
    P['item_l'] = norm(v3(0.03, 1.0, 0.0))
    rig.place_arm(P, 'r', v3(-0.25, 0.94, 0.12), (-1, -0.3, -0.5), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(-0.1, -0.4, 0.8))
    P['bell_swing'] = 0.0
    return P


def bell_post(add, lights, P):
    d = P['item_l']
    if d is None:
        return
    d = norm(d)
    g = hand_pos(P, 'l')
    butt, top = g - d * 1.08, g + d * 0.84
    add(Capsule(butt, top, 0.018, 0.015), 'wood')
    # gallows bar across the top
    bar = norm(v3(1.0, 0, 0.2))
    a, b = top - bar * 0.12, top + bar * 0.20
    add(Capsule(a, b, 0.012), 'wood')
    add(Capsule(top - d * 0.12, top + bar * 0.10, 0.008), 'darkiron')     # brace
    # fog-bell hanging from the outer end, swinging with P['bell_swing']
    sw = P.get('bell_swing', 0.0)
    hang = norm(v3(np.sin(sw) * 0.8, -1, np.sin(sw) * 0.3))
    bc = b + hang * 0.14
    add(Capsule(b, b + hang * 0.03, 0.006), 'darkiron')
    Rb = basis_from(-hang, (0, 0, 1))
    def bell(p, c=bc, R=Rb):
        q = (p - c) @ R
        y = q[:, 1]
        t = np.clip((0.09 - y) / 0.20, 0, 1)
        r = 0.045 + 0.075 * t ** 1.6
        rad = np.sqrt(q[:, 0] ** 2 + q[:, 2] ** 2)
        d0 = np.maximum(rad - r, np.maximum(y - 0.09, -0.11 - y))
        return np.maximum(d0, -(np.maximum(rad - (r - 0.01), -0.07 - y)))    # hollow mouth
    add(Func(bell, bc, 0.17), 'bell')
    add(Sphere(bc - Rb[:, 1] * 0.11, 0.018), 'darkiron')        # clapper
    # lamp from the inner end
    lc = a - v3(0, 0.13, 0)
    add(Capsule(a, a - v3(0, 0.04, 0), 0.005), 'darkiron')
    hurricane(add, lights, P, lc, size=1.05, frame='darkiron', light=1.7)


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    mantle(add, P, 'oilskin', depth=0.18, width=0.16)
    held(P, add, 'r', 'hammer', shaft='wood', head='mallet', below=0.12, above=0.42)
    bell_post(add, lights, P)
    mats = keeper_mats(P, hair=_hex('#4d3a2c'), beard=_hex('#6b5a4a'), skin=W['skin_light'])
    mats['knit'] = Material(noisy(_hex('#7a3f33'), 0.12, 40), spec=0.02, brush=0.12)
    mats['mallet'] = Material(_hex('#4a3a30'), spec=0.1, brush=0.1)
    mats['bell'] = Material(_hex('#6a6866'), spec=0.7, gloss=32, metal=0.7, brush=0.05)
    return finish(P, FACTION, parts, mats, lights=lights)


def _post(fr):
    for i, (P, o) in enumerate(fr['cast']):
        P['bell_swing'] = [0.3, -0.5, 0.25][i]
    for i, (P, o) in enumerate(fr['attack']):
        P['bell_swing'] = [0.0, 0.1, -0.2, 0.1][i]
    for i, (P, o) in enumerate(fr['idle']):
        P['bell_swing'] = [0.0, 0.04, 0.0, -0.04][i]
    return fr


ROWS, frames = keeper_rows(neutral_pose, attack_style='swing', weapon_side='r', cast_side='r', post=_post, pole='l')

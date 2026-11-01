"""Stairkeeper (Lanternkeepers tank). Sworn to one staircase and the door at its top.

Big and square-built: heavy dark oilskin greatcoat, iron keeper's helm, a long iron-shod stair
pole. Defining detail: the stair door itself carried as a shield, oak planks and iron straps,
with its little door-lamp still burning on the top rail.
"""
import numpy as np
from _lanternkeepers_common import *

UNIT_ID = 'lanternkeepers_stairkeeper'
FACTION = 'lanternkeepers'
LOOK = LOOKS[FACTION]

C = Costume(top='wool', sleeve='oilskin_dk', legs='slate', boot='boot', hand='glove', skirt='coat',
            skirt_mat='wool', hem=0.22, flare=0.8, head='helm', head_mat='darkiron', belt='leather',
            girth=1.35)


def neutral_pose():
    P = base_pose(height=1.08, build=1.22)
    h = P['height']
    rig.place_arm(P, 'r', v3(-0.30, 1.05, 0.14), (-1, -0.3, -0.5), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(0.0, 1.0, 0.05))
    rig.place_arm(P, 'l', v3(0.27, 1.06, 0.20), (1, -0.4, -0.3), l1=0.27 * h, l2=0.26 * h)
    return P


def door(add, lights, P):
    el, wr = P['el_l'], P['wr_l']
    c = (el + wr) / 2 + v3(0.06, -0.08, 0.10)
    out = norm(v3(-0.15, 0, 1.0))
    R = basis_from(v3(0, 1, 0), out)
    add(RoundBox(c, (0.19, 0.42, 0.018), 0.008, R), 'oak')
    for t in (-0.27, 0.0, 0.27):
        add(RoundBox(c + R[:, 1] * t + R[:, 2] * 0.02, (0.195, 0.022, 0.006), 0.004, R), 'darkiron')
    for k in (-1, 1):
        add(Sphere(c + R[:, 1] * 0.0 + R[:, 0] * (0.12 * k) + R[:, 2] * 0.028, 0.012), 'darkiron')
    # ring handle and the door-lamp on the top rail
    add(Torus(c + R[:, 2] * 0.03 + R[:, 0] * 0.08, R[:, 2], 0.03, 0.006), 'darkiron')
    top = c + R[:, 1] * 0.40
    add(Capsule(top, top + R[:, 1] * 0.06, 0.008), 'darkiron')
    box_lamp(add, lights, P, top + R[:, 1] * 0.13, size=0.95, frame='darkiron', light=1.6)


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    mantle(add, P, 'oilskin', depth=0.20, width=0.21)
    # helm brim and nape guard
    H, R, h = P['head'], head_R(P), P['height']
    add(Cylinder(H + R @ v3(0, 0.055, -0.02) * h, H + R @ v3(0, 0.065, -0.02) * h, 0.12 * h, 0.005), 'darkiron')
    held(P, add, 'r', 'staff', shaft='wood', head='darkiron', below=1.15, above=0.85)
    door(add, lights, P)
    mats = keeper_mats(P, hair=_hex('#3a3029'), beard=_hex('#55493f'), skin=W['skin_mid'])
    mats['oak'] = Material(noisy(_hex('#5a4330'), 0.14, 30), spec=0.06, brush=0.12)
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = keeper_rows(neutral_pose, attack_style='thrust', weapon_side='r', cast_side='l', pole='r')

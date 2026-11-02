"""Roost-Runner (Gyre scout, flying). A freckled roost kid crouched low on a pony-sized grey gull, leaning
into the launch. Patched oilskin coat, bone-and-cord harness with a tiny brass bell, beak-orange scarf.
Defining detail: a stolen purse held up high in the free hand."""
from _gyre_common import *

UNIT_ID = 'gyre_roost_runner'
LOOK = LOOK_AIR
CAMERA = Camera(ppm=48)
S = species('gull', half=0.9)


def hands(P, Q, S):
    k = S['k']
    h = 0.72
    sh = Q['sh_r']
    up = P['arm']
    tgt = sh + v3(-0.12, 0.22 + 0.10 * up, 0.30 + 0.20 * P['strike'])
    rig.place_arm(Q, 'r', tgt, (-1, 0.2, -0.4), l1=0.27 * h, l2=0.26 * h)


R = rider_cfg(h=0.72, b=0.88, lean=0.72, head='scarf', hair=hx('#9a5a2e'), skin=hx('#d9a27e'), hands=hands,
              sash=False, tail_len=0.36)


def neutral_pose():
    return fly_pose(fl=0.35, pitch=0.05, neckx=0.2, arm=0.5)


def extra(c):
    W, add, S_ = c['W'], c['add'], c['S']
    # the stolen purse, held up high with cord ties
    hp = hand_pos(W, 'r')
    pc = hp + v3(0, 0.05, 0.0)
    add(Ellipsoid(pc + v3(0, 0.02, 0), (0.05, 0.055, 0.045)), 'leather', 0.0)
    add(Capsule(hp + v3(0, 0.03, 0), pc + v3(0, 0.05, 0), 0.008, 0.007), 'cord', 0.0)
    add(Sphere(pc + v3(0.0, 0.08, 0.0), 0.012), 'gold', 0.0)
    # the tiny bell on the harness
    F = c['F']
    add(Sphere(F.pt(v3(-0.20, -0.05, 0.12)), 0.020), 'brass', 0.0)


def build(P):
    return flier_build(P, S, R, extra)


ROWS, frames = fly_rows(neutral_pose)

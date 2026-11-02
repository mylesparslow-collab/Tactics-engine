"""Skua Lancer (Gyre skirmisher, flying). A lean rider flat along a hook-beaked brown skua in a steep stoop,
wings swept to a dart shape, bone lance lowered, coat tails streaming, beak-orange saddle cord.
Defining detail: the skua's folded-back arrowhead wings and the long bone lance."""
from _gyre_common import *

UNIT_ID = 'gyre_skua_lancer'
LOOK = LOOK_AIR
CAMERA = Camera(ppm=48)
S = species('skua', half=0.9)


def hands(P, Q, S):
    h = 0.82
    sh = Q['sh_r']
    rig.place_arm(Q, 'r', sh + v3(-0.10, -0.16, 0.30 + 0.14 * P['strike']), (-1, -0.4, -0.2), l1=0.27 * h, l2=0.26 * h)


R = rider_cfg(h=0.82, b=0.90, lean=0.98, head='mask', skin=hx('#b98462'), hands=hands, sash=True, tail_len=0.5,
              mats=dict(coat=hx('#6b6455')))


def neutral_pose():
    return fly_pose(fl=0.10, fold=0.35, pitch=0.20, neckx=0.7, dip=0.3, legs=0.25)


def extra(c):
    W, add, F, P = c['W'], c['add'], c['F'], c['P']
    g = hand_pos(W, 'r')
    d = norm(F.R @ v3(-0.06, -0.02 - 0.12 * P['strike'], 1.0))
    butt, tip = g - d * 0.40, g + d * 0.85
    add(Capsule(butt, tip - d * 0.25, 0.026, 0.020), 'bone', 0.0)
    add(Capsule(tip - d * 0.28, tip, 0.042, 0.004), 'bone', 0.0)
    for t in (0.0, 0.07, 0.14):
        add(Cylinder(tip - d * (0.32 + t), tip - d * (0.30 + t), 0.020, 0.004), 'cord', 0.0)
    add(Sphere(butt, 0.024), 'bone', 0.0)


def build(P):
    return flier_build(P, S, R, extra, y0=0.66)


ROWS, frames = fly_rows(neutral_pose, idle_amp=0.60)

"""Frigate Thief (Gyre disruptor, flying). A grinning thief in a hooded oilskin coat on a red-throated frigatebird
in a banking turn: long forked tail, very long bent wings, throat pouch inflated red. Clutching a stolen
glowing drip-flask. Defining detail: the inflated red throat pouch and the stolen flask."""
from _gyre_common import *

UNIT_ID = 'gyre_frigate_thief'
LOOK = LOOK_AIR
CAMERA = Camera(ppm=46)
S = species('frigate', bend=-0.20, dihedral=0.30, half=0.95)


def hands(P, Q, S):
    h = 0.80
    sh = Q['sh_r']
    rig.place_arm(Q, 'r', sh + v3(-0.14, 0.12, 0.26 + 0.12 * P['snatch']), (-1, 0.2, -0.4), l1=0.27 * h, l2=0.26 * h)


R = rider_cfg(h=0.80, b=0.88, lean=0.66, head='hood', skin=hx('#c08f6c'), hands=hands, tail_len=0.5,
              mats=dict(coat=hx('#6a6c66')))


def neutral_pose():
    return fly_pose(fl=0.35, roll=0.22, pitch=0.04, neckx=0.2, pouch=1.0, snatch=0.5)


def extra(c):
    W, add = c['W'], c['add']
    g = hand_pos(W, 'r')
    # stolen drip-flask: glass with a glowing teal drip, brass cap
    add(Capsule(g + v3(0, 0.02, 0), g + v3(0, 0.12, 0.0), 0.030, 0.030), 'glass', 0.0)
    add(Cylinder(g + v3(0, 0.12, 0), g + v3(0, 0.15, 0), 0.016, 0.004), 'brass', 0.0)
    add(Sphere(g + v3(0.03, -0.02, 0.0), 0.010), 'glass', 0.0)
    return [Light(g + v3(0, 0.08, 0.05), hx('#7fd6c8'), 0.6, 0.5)]


def build(P):
    return flier_build(P, S, R, extra, y0=0.55)


ROWS, frames = fly_rows(neutral_pose, idle_amp=0.60)

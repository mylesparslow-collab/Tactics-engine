"""Wheel-Captain (Gyre commander, flying). A hard-faced captain on a big black-backed gull, wings spread,
long black oilskin coat with a beak-orange sash, bone horn at the belt, one arm pointing the dive.
Defining detail: the bone signal horn and the orange sash."""
from _gyre_common import *

UNIT_ID = 'gyre_wheel_captain'
LOOK = LOOK_AIR
CAMERA = Camera(ppm=46)
S = species('blackback', half=0.92)


def hands(P, Q, S):
    h = 0.86
    sh = Q['sh_r']
    # right arm points forward and down toward the target
    rig.place_arm(Q, 'r', sh + v3(-0.10, -0.05 - 0.10 * P['arm'], 0.46), (-1, 0.5, -0.2), l1=0.27 * h, l2=0.26 * h)


R = rider_cfg(h=0.86, b=0.95, lean=0.45, head='hood', skin=hx('#b88a6c'), hands=hands, tail_len=0.78,
              mats=dict(coat=hx('#2f3236'), skin=hx('#b88a6c')))


def neutral_pose():
    return fly_pose(fl=0.40, pitch=0.03, neckx=0.3, arm=0.4)


def extra(c):
    W, add, F = c['W'], c['add'], c['F']
    # bone horn at the belt, with a cord
    pel = W['pelvis']
    side = F.R @ v3(-1, 0, 0)
    a = pel + side * 0.13 + F.R @ v3(0, 0.0, 0.07)
    b = a + F.R @ v3(-0.03, -0.10, 0.12)
    add(Capsule(a, b, 0.032, 0.012), 'bone', 0.02)
    add(Sphere(a, 0.036), 'bone', 0.0)
    add(Cylinder(a + (b - a) * 0.15, a + (b - a) * 0.3, 0.030, 0.004), 'cord', 0.0)
    # sash hanging orange tail
    ch = W['chest']
    add(Capsule(pel + side * 0.08 + F.R @ v3(0, 0.02, -0.02), pel + side * 0.12 + F.R @ v3(0, -0.28, -0.10), 0.030, 0.022), 'cord', 0.0)
    # cutlass at the hip (reversed side)
    h0 = pel - side * 0.12
    add(Capsule(h0, h0 + F.R @ v3(0.0, -0.08, -0.46), 0.010, 0.006), 'steel', 0.0)


def build(P):
    return flier_build(P, S, R, extra, y0=0.55)


ROWS, frames = fly_rows(neutral_pose, idle_amp=0.60)

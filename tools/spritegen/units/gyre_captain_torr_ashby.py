"""Captain Torr Ashby of the Black Wheel (Gyre hero, flying). A scarred mercenary on a vast bald vulture descending,
neck hunched, wings wide. Dark oilskin coat with a thin gold company badge, bone hook at the belt, beak-orange sash,
a half-eaten loaf of bread in his teeth. Grim and patient."""
from _gyre_common import *

UNIT_ID = 'gyre_captain_torr_ashby'
LOOK = LOOK_AIR
CAMERA = Camera(ppm=46)
S = species('vulture', half=0.92)


def hands(P, Q, S):
    h = 0.90
    sh = Q['sh_r']
    rig.place_arm(Q, 'r', sh + v3(-0.12, -0.14, 0.22), (-1, -0.3, -0.2), l1=0.27 * h, l2=0.26 * h)


R = rider_cfg(h=0.90, b=1.06, girth=1.1, lean=0.50, head='bald', skin=hx('#b88562'), hands=hands, tail_len=0.6,
              beard=hx('#3a342f'), mats=dict(coat=hx('#4d4e52'), skin=hx('#b88562')))
R['hair'] = hx('#3a342f')


def neutral_pose():
    return fly_pose(fl=0.30, pitch=0.12, neckx=0.0, dip=0.2, legs=0.3)


def extra(c):
    W, add, F, P = c['W'], c['add'], c['F'], c['P']
    H = W['head']
    Rh = head_R(W)
    # half-eaten loaf in his teeth
    m = H + Rh @ v3(0.0, -0.03, 0.085) * 0.9
    add(Ellipsoid(m + Rh @ v3(0.0, 0.0, 0.05), (0.075, 0.032, 0.038), Rh @ rot_z(0.2)), 'bread', 0.0)
    add(Sphere(m + Rh @ v3(0.07, -0.01, 0.08), 0.022), 'skin_in', 0.0)
    c['mats']['skin_in'] = Material(hx('#e6d2a8'), spec=0.02, brush=0.04)
    # gold company badge on the chest
    ch = W['chest']
    add(Cylinder(ch + F.R @ v3(-0.08, 0.06, 0.12), ch + F.R @ v3(-0.08, 0.06, 0.135), 0.024, 0.004), 'gold', 0.0)
    # bone hook at the belt
    pel = W['pelvis']
    side = F.R @ v3(-1, 0, 0)
    a = pel + side * 0.15 + F.R @ v3(0, 0.0, 0.0)
    b = a + F.R @ v3(-0.02, -0.12, 0.10)
    add(Capsule(a, b, 0.016, 0.012), 'bone', 0.0)
    add(Capsule(b, b + F.R @ v3(-0.03, -0.02, 0.07), 0.012, 0.004), 'bone', 0.0)
    add(Capsule(pel + side * 0.0, pel + side * 0.18, 0.02, 0.02), 'cord', 0.0)


def build(P):
    return flier_build(P, S, R, extra, y0=0.55)


ROWS, frames = fly_rows(neutral_pose, idle_amp=0.60)

"""Shrike Harrier (Gyre controller, flying). A rider on a masked grey-and-black shrike with spread wings and
a hooked beak, holding a salt-spike down. Larder of salt-spikes lashed to the harness with prey on them.
Defining detail: the impaled larder on the bird's flank and the beak-orange mask bar."""
from _gyre_common import *

UNIT_ID = 'gyre_shrike_harrier'
LOOK = LOOK_AIR
CAMERA = Camera(ppm=48)
S = species('shrike', k=1.2, half=0.88)


def hands(P, Q, S):
    h = 0.82
    sh = Q['sh_r']
    rig.place_arm(Q, 'r', sh + v3(-0.12, -0.20, 0.22 + 0.2 * P['strike']), (-1, -0.2, -0.2), l1=0.27 * h, l2=0.26 * h)


R = rider_cfg(h=0.82, b=0.90, lean=0.60, head='hood', goggles=True, skin=hx('#b78662'), hands=hands,
              mats=dict(coat=hx('#6a6a60')))


def neutral_pose():
    return fly_pose(fl=0.45, pitch=0.04, neckx=0.2, legs=0.3)


def spike(add, a, d, L=0.7, r=0.020):
    add(Capsule(a, a + d * L, r, 0.004), 'feather_g', 0.0)


def extra(c):
    W, add, F, P, S_ = c['W'], c['add'], c['F'], c['P'], c['S']
    g = hand_pos(W, 'r')
    d = norm(F.R @ v3(-0.05, -0.45 - 0.2 * P['strike'], 1.0))
    spike(add, g - d * 0.12, d, 0.6, 0.022)
    add(Cylinder(g - d * 0.06, g + d * 0.02, 0.03, 0.006), 'tar', 0.0)
    add(Cylinder(g + d * 0.10, g + d * 0.14, 0.028, 0.005), 'cord', 0.0)
    # the larder: salt-spikes lashed along the right flank, each with something on it
    k = S_['k']
    for j, (z, dz) in enumerate(((0.05, 0.0), (-0.12, 0.0), (0.22, 0.0))):
        a = F.pt(v3(-0.22 * k, -0.02, z * k))
        dd = norm(F.R @ v3(-0.5, -0.4 - 0.15 * j, 0.1 - 0.15 * j))
        spike(add, a, dd, 0.38, 0.012)
        add(Ellipsoid(a + dd * (0.22 + 0.05 * j), (0.03, 0.03, 0.04)), 'feather_i' if j != 1 else 'leather', 0.0)
    # mask bar painted beak orange across the bird's eyes
    H = c['info']['head']
    add(Capsule(H + F.R @ v3(-0.065, 0.015, 0.05), H + F.R @ v3(-0.045, 0.02, 0.09), 0.012, 0.010), 'beak', 0.0)


def build(P):
    return flier_build(P, S, R, extra)


ROWS, frames = fly_rows(neutral_pose, idle_amp=0.60)

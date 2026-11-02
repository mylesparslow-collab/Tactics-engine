"""Pelican Hauler (Gyre controller, flying). An enormous pelican in flight with broad wings and a sagging
pouch bulging with an indignant marksman's boots and elbows, rider crouched on its shoulders hauling
the reins. Defining detail: a kicking boot sticking out of the pouch."""
from _gyre_common import *

UNIT_ID = 'gyre_pelican_hauler'
LOOK = LOOK_AIR
CAMERA = Camera(ppm=46)
S = species('pelican', k=1.08, half=0.90, ch_root=0.40, ch_wrist=0.30)
R = rider_cfg(h=0.84, b=0.95, lean=0.55, head='hood', skin=hx('#c08a68'), mats=dict(coat=hx('#7d7766')))


def neutral_pose():
    return fly_pose(fl=0.30, pitch=0.02, neckx=0.0, pouch=0.85, kick=0.5)


def extra(c):
    P, add, F, S_ = c['P'], c['add'], c['F'], c['S']
    # elbow poking out of the pouch the other side
    k = S_['k']
    pc = c['info']['beak'] - F.R @ v3(0, 0, 0.14 * k)
    add(Sphere(pc + F.R @ v3(-0.07 * k, -0.17 * k, -0.02), 0.045), 'oil_dk', 0.02)


def build(P):
    return flier_build(P, S, R, extra, y0=0.55)


def tweak(rows):
    for nm in rows:
        for i, (P, o) in enumerate(rows[nm]):
            P['kick'] = 0.3 + 0.5 * (i % 2)
            P['pouch'] = 0.85 + 0.1 * (i % 2)


ROWS, frames = fly_rows(neutral_pose, tweak=tweak, idle_amp=0.60)

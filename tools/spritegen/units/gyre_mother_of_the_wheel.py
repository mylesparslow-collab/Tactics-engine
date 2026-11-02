"""Mother of the Wheel (Gyre exotic commander, flying giant). An albatross the size of a sail-barge gliding on
full wingspan with three small riders and lanterns strung along her back, cord-and-bone harness trailing.
Defining detail: the strung lanterns (the only warm light) and the sheer span."""
from _gyre_common import *

UNIT_ID = 'gyre_mother_of_the_wheel'
LOOK = LOOK_AIR
CAMERA = Camera(ppm=44)
S = species('albatross', k=1.5, half=1.02, ch_root=0.25, ch_wrist=0.19, saddle=(0.21, 0.0))
R = rider_cfg(h=0.62, b=0.9, lean=0.55, head='hood', skin=hx('#b88a6c'), z=0.42, tail_len=0.4,
              mats=dict(coat=hx('#6b6a60')))
R2 = rider_cfg(h=0.60, b=0.9, lean=0.30, head='mask', skin=hx('#b88a6c'), z=-0.08, x=0.0, tail_len=0.36,
               skin_mat='skin_plain')
R3 = rider_cfg(h=0.58, b=0.9, lean=0.45, head='scarf', skin=hx('#b88a6c'), z=-0.52, tail_len=0.32,
               skin_mat='skin_plain', hair=hx('#d8d4c8'))


def neutral_pose():
    return fly_pose(fl=0.18, pitch=0.0, neckx=0.2, legs=0.0)


def extra(c):
    add, F, P, S_, mats = c['add'], c['F'], c['P'], c['S'], c['mats']
    mats['skin_plain'] = Material(noisy(hx('#b88a6c'), 0.06), spec=0.05, sss=0.4, brush=0.02)
    mats['hair'] = Material(hx('#40372f'), spec=0.2, gloss=16, brush=0.1)
    lights = []
    for Rx in (R2, R3):
        W2 = world_rider(P, S_, F, Rx)
        rider_body(W2, add, Rx, S_)
    k = S_['k']
    # lanterns strung along the back on a cord, and hanging at the flanks
    zs = (0.42, 0.17, -0.08, -0.30, -0.52)
    pts = [F.pt(v3(0, (S_['body'][1] + 0.05) * k, z)) for z in zs]
    for a, b in zip(pts[:-1], pts[1:]):
        add(Capsule(a + v3(0, 0.02, 0), b + v3(0, 0.02, 0), 0.007, 0.007), 'tar', 0.0)
    for j, (z, sx) in enumerate(((0.3, -1), (-0.18, 1), (-0.45, -1), (0.1, 1))):
        a = F.pt(v3(sx * S_['body'][0] * k * 0.95, S_['body'][1] * k * 0.2, z))
        cl = a + F.R @ v3(sx * 0.06, -0.10, 0.0)
        add(Capsule(a, cl + F.R @ v3(0, 0.06, 0), 0.006, 0.006), 'cord', 0.0)
        lantern(add, cl, 'brass', 'lamp', size=0.8, R=F.R)
        lights.append(Light(cl, hx('#ffb35c'), 0.7 * P['glow'], 0.55))
    return lights


def build(P):
    return flier_build(P, S, R, extra, y0=0.58)


ROWS, frames = fly_rows(neutral_pose, idle_amp=0.60)

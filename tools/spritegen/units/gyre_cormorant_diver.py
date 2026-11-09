"""Cormorant Diver (Gyre ambusher, flying). A sleek rider pressed flat along a glossy black cormorant in a vertical-ish
dive, wings swept back like a dart, long snaking neck stretched out and hooked bone beak ahead, yellow-orange throat
skin. Rider in a tarred black-grey diving coat and brass goggles with a belt of lead weights; salt grit and spray
streaming off the tail. Defining detail: the steep dive pose, with salt flecks peeling off the feathers.
Distinct from the Skua Lancer: black not brown, neck-led, near vertical, spray, no lance."""
from _gyre_w2 import *

UNIT_ID = 'gyre_cormorant_diver'
LOOK = LOOK_AIR
CAMERA = Camera(ppm=48)
S = species('cormorant', half=0.88)


def hands(P, Q, S_):
    h = 0.84
    sh = Q['sh_r']
    rig.place_arm(Q, 'r', sh + v3(-0.07, -0.20, 0.17), (-1, -0.4, -0.1), l1=0.27 * h, l2=0.26 * h)


R = rider_cfg(h=0.84, b=0.88, lean=0.45, head='hood', goggles=True, skin=hx('#b98e6e'), hands=hands,
              tail_len=0.32, sash=False, mats=dict(coat=hx('#d9d6c8')))


def neutral_pose():
    return fly_pose(fl=0.0, fl2=-0.1, fold=0.78, pitch=0.62, neckx=1.0, dip=0.5, legs=0.0, look=-0.2, tailsp=-0.3)


def extra(c):
    W, add, F, P, mats, S_ = c['W'], c['add'], c['F'], c['P'], c['mats'], c['S']
    extra_mats(mats)
    k = S_['k']
    # throat skin patch: yellow-orange gular pouch on the neck/beak base
    H = c['info']['head']
    add(Ellipsoid(H + F.R @ v3(0, -0.035, 0.05), (0.035, 0.030, 0.06), F.R), 'beak', 0.02)
    # lead-weight belt at the rider's waist
    pel = W['pelvis']
    for j in range(5):
        a = (j - 2) * 0.40
        add(Cylinder(pel + F.R @ v3(np.sin(a) * 0.13, 0.04, np.cos(a) * 0.08 - 0.0), pel + F.R @ v3(np.sin(a) * 0.13, 0.085, np.cos(a) * 0.08), 0.021, 0.004), 'iron', 0.0)
    # white thigh patch on the bird, dive trail: spray and salt grit streaming up-back
    back = norm(F.R @ v3(0, 0.3, -1.0))
    spray(add, F.t + F.R @ v3(0, 0.1, -0.5) * k, back, n=9, amt=1.0, seed=4, length=0.7, mat='salt', size=0.024, spread=0.16)
    spray(add, F.t + F.R @ v3(0.15, 0.12, -0.1) * k, back, n=5, amt=1.0, seed=8, length=0.5, mat='spray', size=0.018, spread=0.12)
    return []


def build(P):
    return flier_build(P, S, R, extra, y0=0.78)


def tweak(rows):
    for i, (P, o) in enumerate(rows['idle']):
        P['pitch'] = 0.62 + 0.04 * np.sin(i * 1.57)
        P['fold'] = 0.78 - 0.1 * np.sin(i * 1.57)
    for i, (P, o) in enumerate(rows['move']):
        P['pitch'] = 0.5
        P['fold'] = 0.5


ROWS, frames = fly_rows(neutral_pose, tweak=tweak, idle_amp=0.35)

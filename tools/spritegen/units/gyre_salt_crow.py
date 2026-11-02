"""Salt Crow (Gyre cheap body, flying). A crow the size of a hunting dog, wings half open and fingered,
beak-orange eye ring, a notch in the beak where something once fought back, a scrap of rope-end in its beak.
No rider: just the bird, with a torn tarred-cord harness stub."""
from _gyre_common import *

UNIT_ID = 'gyre_salt_crow'
LOOK = LOOK_AIR
CAMERA = Camera(ppm=52)
S = species('crow', k=1.2, half=0.92)


def neutral_pose():
    return fly_pose(fl=0.40, pitch=0.06, neckx=0.3, legs=0.15)


def extra(c):
    add, info, F = c['add'], c['info'], c['F']
    b1 = info['beak']
    P = c['P']
    sw = np.sin(P['tell'] * 6.283) * 0.03
    # a scrap of rope-end hanging from the beak
    a = b1 + F.R @ v3(0, -0.03, -0.04)
    b = a + F.R @ v3(0.0 + sw, -0.10, -0.03)
    cc = b + F.R @ v3(0.02, -0.07, -0.01)
    c['add'](Capsule(a, b, 0.010, 0.009), 'cord', 0.0)
    c['add'](Capsule(b, cc, 0.009, 0.006), 'tar', 0.0)
    # tuft of ragged neck feathers
    H = info['head']
    for sx in (-1, 1):
        add(Ellipsoid(H + F.R @ v3(sx * 0.07, -0.03, -0.12), (0.045, 0.03, 0.08), F.R @ rot_y(sx * 0.3)), 'b_neck', 0.04)


def build(P):
    return flier_build(P, S, None, extra, y0=0.48, rider=False)


ROWS, frames = fly_rows(neutral_pose, idle_amp=0.60)

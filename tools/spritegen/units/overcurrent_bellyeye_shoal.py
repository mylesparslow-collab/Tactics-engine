"""Bellyeye Shoal (Overcurrent cheap body). Five hand-sized pale fish hanging in a tight knot, rolled belly-out so
a wet pink eye sits in every lit belly, every pupil swung to the same point. Defining detail: the belly eyes,
each a different size, all looking at you. Tell: the cyan eye-rings breathe and the whole knot turns as one."""
from _overcurrent_common import *

UNIT_ID = 'overcurrent_bellyeye_shoal'
CAMERA = Camera(ppm=56)

_C = v3(-0.53, 0.5, 0.68)
_B0 = norm(v3(-0.30, -0.50, 0.80))            # belly direction: toward the viewer
_N0 = v3(0.788, 0.12, 0.616)
# (x, y, z, roll about belly axis, size, eye size)
FISH = [(0.02, 0.98, 0.0, 0.0, 1.45, 1.8), (-0.36, 0.60, -0.10, 0.3, 1.2, 1.5), (0.30, 1.36, -0.2, -0.30, 1.2, 1.2),
        (-0.30, 1.30, 0.10, 0.5, 1.1, 1.7), (0.36, 0.62, 0.20, -0.45, 1.15, 1.35)]


def neutral_pose():
    return pose()


def frame_for(roll):
    b = _B0
    n = _N0 - b * (_N0 @ b)
    n = norm(n)
    c, s = np.cos(roll), np.sin(roll)
    n2 = n * c + np.cross(b, n) * s
    y = -b
    x = np.cross(y, n2)
    return np.stack([x, y, n2], axis=1)


def build(P):
    parts, add = new_parts()
    st, op = P['strike'], P['open']
    pl = Placer(P, yaw=0.0, hover=0.0, shift=-0.02)
    centers = []
    for i, (x, y, z, roll, sz, es) in enumerate(FISH):
        bob = 0.03 * np.sin(P['ph'] + i * 1.3)
        c = v3(x, y + bob, z) + norm(_N0) * 0.30 * st * (1.0 if i == 0 else 0.8)
        F = Frame(c, frame_for(roll + 0.15 * np.sin(P['ph'] * 0.5 + i)), 1.0 * sz)
        look = F.R.T @ norm(v3(0.2, 0.0, 0.3) * 0 + _C * 0.8 + v3(0.5, 0.1, 0.35))
        fish(F, add, ph=P['ph'] * 1.5 + i * 1.7, mouth=op + 0.5 * st, eye_look=look, big=es)
        centers.append(c)
    mats = std_mats(P, {'skin': skin(glow=0.8, veins=0.25, local=pl.inv, organs=[])})
    lights = [under_light(P, v3(0, 0.15, 0.1), 1.0, 1.2)]
    dp = [pl.pt(c + v3(0, -0.05, 0)) for c in centers[1:4]]

    def world(add2):
        drips(add2, P, dp)
        spray(add2, P, pl.pt(v3(0.2, 1.0, 0.4)))
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.3, 0.8, 0.0, 0.2), atk_strike=(0.0, 0.5, 1.0, 0.3))

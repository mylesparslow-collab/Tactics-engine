"""Gulper (Overcurrent melee). An eel that is mostly mouth: pale body reared in an S out of its own coil,
the unhinged jaw bigger than the whole animal, pink throat hooked with teeth, a cyan lure at the tail tip,
a stomach stretched tight and visible under the skin.
Defining detail: the gape. Tell: belly-light breathing and a slow wave down the body."""
from _overcurrent_common import *

UNIT_ID = 'overcurrent_gulper'
CAMERA = Camera(ppm=46)
YAW = 0.85


def neutral_pose():
    return pose()


def spine(P):
    ph, st = P['ph'], P['strike']
    w = lambda y, a: a * np.sin(ph + y * 3.2)
    return [v3(0.30, 0.24, -0.72), v3(0.20, 0.07, -0.66), v3(0.04 + w(0.1, 0.05), 0.10, -0.52),
            v3(-0.20 + w(0.2, 0.05), 0.15, -0.34), v3(-0.10, 0.40, -0.30 - 0.05 * st),
            v3(0.02 + w(0.6, 0.04), 0.84, -0.32 + 0.06 * st), v3(0.04, 1.26, -0.26 + 0.2 * st),
            v3(0.0, 1.50, -0.10 + 0.18 * st)]


def build(P):
    parts, add = new_parts()
    op, st = P['open'], P['strike']
    pts = spine(P)
    s = tube(add, pts, [0.012, 0.035, 0.07, 0.115, 0.15, 0.15, 0.13, 0.11], 'skin', n=22, k=0.05)
    tip = pts[0]
    add(Capsule(tip, tip + v3(0.04, 0.13, 0.05), 0.012, 0.009), 'skin', 0.0)
    lure_c = tip + v3(0.04, 0.18, 0.05)
    add(Sphere(lure_c, 0.055), 'lure', 0.0)
    for i in range(3, 20, 3):
        a = s[i]
        add(Capsule(a + v3(0, 0.12, 0), a + v3(0, 0.20, -0.03), 0.007, 0.003), 'fin', 0.0)
    # head frame at the neck, pitched by the animation, 1.45x so the mouth dwarfs the body
    pitch = 0.55 + 0.30 * st - 0.30 * op
    H = Frame(pts[-1] + v3(0, 0.02, 0.0), rot_x(pitch), 1.45)
    gape = 0.45 + 0.95 * op
    H.ell(add, (0, 0.07, 0.34), (0.23, 0.075, 0.40), 'skin', 0.0)
    H.ell(add, (0, 0.02, 0.06), (0.20, 0.17, 0.20), 'skin', 0.06)
    H.ell(add, (0, -0.06, 0.26), (0.17, 0.09 + 0.18 * op, 0.27), 'throat', 0.0)
    for sx in (-1, 1):
        H.sph(add, (sx * 0.15, 0.09, 0.24), 0.034, 'eyeb')
    for k in range(14):
        z = 0.12 + k * 0.056
        for sx in (-1, 1):
            q = v3(sx * 0.215, 0.0, z)
            H.tooth(add, q, q + v3(-sx * 0.02, -0.17 - 0.04 * (k % 2), 0.0), 0.019)
    J = H.child((0, -0.02, 0.0), rot_x(gape))
    J.ell(add, (0, -0.05, 0.42), (0.21, 0.05, 0.48), 'skin', 0.0)
    J.ell(add, (0, -0.14, 0.32), (0.16, 0.10 + 0.07 * op, 0.36), 'skin', 0.05)
    J.ell(add, (0, 0.0, 0.34), (0.15, 0.035, 0.38), 'gum', 0.0)
    for k in range(14):
        z = 0.12 + k * 0.056
        for sx in (-1, 1):
            q = v3(sx * 0.19, 0.0, z)
            J.tooth(add, q, q + v3(-sx * 0.02, 0.16 + 0.04 * (k % 2), 0.01), 0.019)
    pl = Placer(P, yaw=YAW, hover=0.05, shift=-0.12)
    organs = [Organ(pl.pt(s[8] + v3(-0.02, 0.0, 0.0)), (0.11, 0.26, 0.10), _hex('#e08aa0'), 0.0, 0.75),
              Organ(pl.pt(s[14]), (0.075, 0.10, 0.07), _hex('#c4344a'), 0.0, 0.7)]
    mats = std_mats(P, {'skin': skin(organs=organs, veins=0.5, local=pl.inv, glow=0.6, depth=0.5)})
    lights = [under_light(P, pl.pt(s[10]) * v3(1, 0, 1) + v3(0, 0.1, 0), 1.0, 1.0),
              Light(pl.pt(lure_c), CYAN, 0.8 * P['glow'], 0.5)]
    dp = [pl.pt(H.p((0.0, 0.1, 0.9))), pl.pt(s[10] + v3(0.1, 0, 0))]

    def world(add2):
        drips(add2, P, dp)
        spray(add2, P, pl.pt(H.p((0, 0.3, 0.8))))
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.6, 1.0, 0.0, 0.3), atk_strike=(0.0, 0.4, 1.0, 0.3))

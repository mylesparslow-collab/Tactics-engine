"""Lure-Mother (Overcurrent controller). A squat round pearl anglerfish dragging herself along the salt, a
yawning split jaw of needle teeth, and a living stalk arching over it that ends in a tiny lighthouse: tower,
lamp and a beam of cyan light thrown out ahead of the mouth. Things walk toward it weeping with relief.
Defining detail: the lure is a perfect small copy of a lighthouse beam. Tell: the beam flickers."""
from _overcurrent_common import *

UNIT_ID = 'overcurrent_lure_mother'
CAMERA = Camera(ppm=50)


def neutral_pose():
    return pose()


def build(P):
    parts, add = new_parts()
    ph, st, op = P['ph'], P['strike'], P['open']
    flick = 0.8 + 0.25 * np.sin(2 * np.pi * P['tell'] * 2) + 0.2 * P['cast_glow']
    z0 = 0.30 * st
    B = Frame((0, 0.52, -0.10 + z0), rot_x(0.05 * st), 1.0)
    B.ell(add, (0, 0, 0), (0.50, 0.46, 0.55), 'skin')
    B.ell(add, (0, 0.05, 0.30), (0.42, 0.40, 0.42), 'skin', 0.1)
    # dorsal warts
    for (x, y, z) in [(0.2, 0.40, -0.1), (-0.15, 0.44, -0.25), (0.0, 0.46, 0.05), (-0.3, 0.3, 0.1), (0.3, 0.3, -0.25)]:
        B.sph(add, (x, y, z), 0.05, 'skin', 0.03)
    # tail fan
    fin(add, B.p((0, 0.0, -0.45)), B.p((0.1 * np.sin(ph), 0.05, -0.95)), 0.20, 'fin', 0.012)
    for sx in (-1, 1):
        # thick pectoral "arms" dragging her along
        a = B.p((sx * 0.42, -0.18, 0.12))
        b = B.p((sx * 0.62, -0.34 + 0.05 * np.sin(ph + sx), 0.34))
        add(Capsule(a, b, 0.09, 0.06), 'skin', 0.03)
        fin(add, b, b + v3(sx * 0.12, -0.04, 0.16), 0.11, 'fin', 0.01)
        B.sph(add, (sx * 0.28, 0.28, 0.50), 0.045, 'eyeb')
        B.sph(add, (sx * 0.31, 0.30, 0.53), 0.018, 'tooth')
    # the mouth: a wide upturned gape across the front
    M = B.child((0, -0.02, 0.30), rot_x(-0.22), 1.35)
    gape = 0.35 + 0.75 * op
    M.ell(add, (0, 0.06, 0.16), (0.44, 0.09, 0.34), 'skin', 0.05)
    M.ell(add, (0, -0.06, 0.04), (0.38, 0.14 + 0.15 * op, 0.30), 'throat')
    for k in range(16):
        a = -1.3 + k * 0.173
        q = v3(np.sin(a) * 0.42, 0.0, 0.05 + np.cos(a) * 0.40)
        M.tooth(add, q + v3(0, 0.02, 0), q + v3(-np.sin(a) * 0.03, -0.28 - 0.05 * (k % 2), -0.04), 0.021)
    J = M.child((0, -0.02, -0.05), rot_x(gape))
    J.ell(add, (0, -0.07, 0.30), (0.40, 0.08, 0.46), 'skin', 0.0)
    J.ell(add, (0, 0.0, 0.30), (0.34, 0.03, 0.40), 'gum', 0.0)
    for k in range(16):
        a = -1.35 + k * 0.18
        q = v3(np.sin(a) * 0.38, 0.0, 0.08 + np.cos(a) * 0.46)
        J.tooth(add, q, q + v3(np.sin(a) * 0.02, 0.32 + 0.06 * (k % 2), 0.05), 0.024)
    # the lure: a living stalk ending in a little lighthouse and its beam
    sw = 0.06 * np.sin(ph)
    pts = [B.p((0, 0.40, 0.25)), B.p((0.0, 0.88, 0.22)), B.p((sw, 1.02, 0.60)), B.p((sw, 0.78, 0.98))]
    sp = tube(add, pts, [0.035, 0.028, 0.02, 0.018], 'skin', n=12, k=0.02)
    top = sp[-1]
    add(Capsule(top, top + v3(0, -0.10, 0), 0.06, 0.036), 'bone', 0.0)             # tower
    add(Cylinder(top + v3(0, -0.10, 0), top + v3(0, -0.085, 0), 0.058, 0.005), 'bone', 0.0)
    lamp = top + v3(0, -0.14, 0)
    add(Sphere(lamp, 0.052 * (0.9 + 0.2 * flick)), 'lure', 0.0)
    add(Cylinder(lamp + v3(0, -0.055, 0), lamp + v3(0, -0.045, 0), 0.05, 0.004), 'bone', 0.0)
    beam_d = norm(v3(0.2, -0.6, 1.0))
    bs = lamp + beam_d * 0.05
    add(Capsule(bs, bs + beam_d * (0.38 + 0.12 * flick), 0.03, 0.10 + 0.04 * flick), 'beam', 0.0)
    pl = Placer(P, yaw=0.5, hover=0.18, shift=-0.10, back=0.6, scale=0.76)
    organs = [Organ(pl.pt(B.p((0.0, -0.02, 0.0))), (0.28, 0.20, 0.32), _hex('#e08ca0'), 0.0, 0.8),
              Organ(pl.pt(B.p((0.0, -0.0, -0.04))), (0.06, 0.04, 0.26), _hex('#f4f0e6'), 0.0, 0.85),
              Organ(pl.pt(B.p((0.15, 0.1, -0.2))), (0.09, 0.08, 0.09), _hex('#c4344a'), 0.0, 0.8)]
    mats = std_mats(P, {'skin': skin(organs=organs, veins=0.45, glow=0.7, depth=0.6, local=pl.inv, spec=0.4),
                        'beam': Material(CYAN, emissive=tuple(np.array(_hex('#9eeef2')) * 0.7 * flick), rim=0.0)})
    lights = [under_light(P, v3(0, 0.1, 0), 1.0, 1.1), Light(pl.pt(lamp), CYAN, 1.1 * flick, 0.9)]
    dp = [pl.pt(J.p((0.2, -0.1, 0.5))), pl.pt(B.p((-0.3, -0.2, 0.2)))]

    def world(add2):
        drips(add2, P, dp)
        spray(add2, P, pl.pt(M.p((0, 0.2, 0.5))))
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.5, 1.0, 0.0, 0.3), atk_strike=(0.0, 0.5, 1.0, 0.3))

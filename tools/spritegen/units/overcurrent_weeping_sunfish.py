"""Weeping Sunfish (Overcurrent support / healer). A vast, slow, flat moon of a fish standing on its fins, its flank
bruised with parasite scars and pale lice, a small gentle eye weeping brine in a rope down its side and a lip of
tiny teeth under the beak. The others crowd under it to be rained on.
Defining detail: the tears, which climb a few pixels before they fall. Tell: the tear-stream and the belly pearls pulse."""
from _overcurrent_common import *

UNIT_ID = 'overcurrent_weeping_sunfish'
CAMERA = Camera(ppm=44)


def neutral_pose():
    return pose()


def scars(q, n):
    f = fbm(q + 2.2, 5.0, 3)
    bruise = f > 0.60
    pale = (fbm(q + 7.7, 16.0, 2) > 0.74) & ~bruise
    col = np.where(bruise[:, None], np.array(_hex('#8a5f86'))[None, :] * (0.8 + 0.4 * f[:, None]),
                   np.array(_hex('#f0e6ee'))[None, :].repeat(len(q), 0))
    return bruise | pale, col


def build(P):
    parts, add = new_parts()
    ph, st, op = P['ph'], P['strike'], P['open']
    z0 = 0.18 * st
    B = Frame((0, 1.02, z0), rot_x(0.03 * st), 1.0)
    B.ell(add, (0, 0, 0), (0.18, 0.72, 0.78), 'skin')
    B.ell(add, (0, -0.02, -0.40), (0.14, 0.55, 0.28), 'skin', 0.12)
    for j in range(7):                                            # scalloped clavus edge
        y = -0.46 + j * 0.155
        B.sph(add, (0, y, -0.66 - 0.02 * np.sin(ph + j)), 0.075, 'fin', 0.05)
    fin(add, B.p((0, 0.58, -0.18)), B.p((0, 1.00, -0.50 + 0.06 * np.sin(ph))), 0.17, 'fin', 0.014, wide=(0, 0, 1))
    fin(add, B.p((0, -0.58, -0.18)), B.p((0, -0.98, -0.52 + 0.06 * np.sin(ph + 1))), 0.17, 'fin', 0.014, wide=(0, 0, 1))
    # beaked little mouth
    B.ell(add, (0, -0.06, 0.70), (0.09, 0.075 + 0.04 * op, 0.07), 'gum', 0.04)
    B.ell(add, (0, 0.0, 0.73), (0.07, 0.025, 0.04), 'tooth')
    B.ell(add, (0, -0.12 - 0.05 * op, 0.72), (0.06, 0.02, 0.04), 'tooth')
    # eye with a heavy lid, tears
    ec = B.p((-0.15, 0.16, 0.46))
    add(Sphere(ec, 0.085), 'eye', 0.03)
    add(Sphere(ec + v3(-0.03, -0.02, 0.05), 0.050), 'iris', 0.0)
    add(Sphere(ec + v3(-0.04, -0.03, 0.07), 0.027), 'pupil', 0.0)
    add(Capsule(ec + v3(-0.0, 0.07, -0.04), ec + v3(-0.02, 0.05, 0.08), 0.02, 0.02), 'skin', 0.02)
    B.cap(add, (-0.17, 0.05, 0.58), (-0.17, -0.1, 0.62), 0.0, 0.0, 'water')
    tw = 1.0 + 0.9 * P['cast_glow']
    path = [ec + v3(-0.02, -0.07, 0.04), B.p((-0.25, -0.05, 0.62)), B.p((-0.30, -0.5, 0.66)), v3(-0.40, 0.55 * 0 + 0.12, B.p((0, 0, 0.70))[2] + 0.06), v3(-0.46, 0.02, B.p((0, 0, 0.78))[2] + 0.08)]
    sp = spline(path, 9)
    for i in range(8):
        add(Capsule(sp[i], sp[i + 1], 0.020 * tw, 0.020 * tw), 'water', 0.01)
    add(Ellipsoid(v3(sp[-1][0], 0.012, sp[-1][2]), (0.30 * (1 + 0.2 * P['cast_glow']), 0.012, 0.22), None), 'puddle', 0.0)
    # side fin, lice, belly pearls
    fin(add, B.p((-0.18, -0.10, 0.22)), B.p((-0.34, -0.35 + 0.08 * np.sin(ph), -0.05)), 0.11, 'fin', 0.012)
    for (y, z) in [(0.30, -0.1), (0.05, 0.20), (-0.30, -0.25), (0.45, 0.25), (-0.12, 0.0)]:
        c = B.p((-0.205, y, z))
        add(Ellipsoid(c, (0.03, 0.05, 0.075), None), 'louse', 0.0)
        for sx in (-1, 1):
            add(Capsule(c + v3(-0.02, sx * 0.03, 0), c + v3(-0.05, sx * 0.07, 0.02), 0.008, 0.004), 'louse', 0.0)
    for j in range(9):
        a = -2.4 + j * 0.42
        q = B.p((-0.15, np.cos(a) * -0.62 - 0.0, np.sin(a) * 0.62))
        if q[1] < 0.9:
            add(Sphere(q + v3(-0.03, 0, 0), 0.032), 'glow', 0.0)
    pl = Placer(P, yaw=0.9, hover=0.0, shift=-0.18, back=0.4, scale=0.92)
    organs = [Organ(pl.pt(B.p((0.0, -0.1, 0.0))), (0.12, 0.34, 0.34), _hex('#c88aa8'), 0.0, 0.5),
              Organ(pl.pt(B.p((0.0, 0.0, 0.30))), (0.1, 0.12, 0.10), _hex('#c4344a'), 0.0, 0.55)]
    mats = std_mats(P, {'skin': skin(top=tuple(np.array(CERU) * 0.72 + np.array(PEARL) * 0.14), spots=scars, organs=organs,
                                     veins=0.3, glow=0.7, local=pl.inv, depth=0.5, spec=0.45, mottle=0.06),
                        'louse': Material(_hex('#f2e4ea'), spec=0.4, gloss=40)})
    lights = [under_light(P, v3(0, 0.15, 0.1), 0.9, 1.3)]
    dp = [sp[2], sp[4]]

    def world(add2):
        drips(add2, P, dp, rise=0.25, r=0.02)
        spray(add2, P, v3(-0.4, 0.1, 0.6), n=5)
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.2, 0.6, 0.0, 0.2), atk_strike=(0.0, 0.4, 1.0, 0.3))

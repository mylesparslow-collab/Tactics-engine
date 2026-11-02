"""Barrelgaze (Overcurrent commander). A pale round fish standing upright on its tail fan, with a clear dome for a
head: the brain lies visible inside and two green tubular eyes roll upward through its own skull to track the
beam. Where it stares, the shoal strikes.
Defining detail: green eyes rotating inside a glass skull. Tell: the eyes sweep up to the beam and the dome pulses."""
from _overcurrent_common import *

LOOK = dataclasses.replace(LOOK, sky_int=0.20, key_int=0.7, exposure=0.95)
UNIT_ID = 'overcurrent_barrelgaze'
CAMERA = Camera(ppm=46)


def neutral_pose():
    return pose()


def build(P):
    parts, add = new_parts()
    ph, st, op = P['ph'], P['strike'], P['open']
    z0 = 0.12 * st
    lean = 0.06 + 0.12 * st
    B = Frame((0, 0.0, z0), rot_x(lean), 1.0)
    sw = np.sin(ph)
    # upright body on a tail fan that rests just off the ground
    B.ell(add, (0, 0.92, 0), (0.46, 0.54, 0.42), 'skin')
    B.ell(add, (0, 0.50, -0.02), (0.34, 0.32, 0.30), 'skin', 0.12)
    B.cap(add, (0, 0.28, -0.04), (0.04 * sw, 0.12, -0.10), 0.14, 0.07, 'skin', 0.08)
    fin(add, B.p((0.04 * sw, 0.14, -0.10)), B.p((0.12 * sw, 0.02, -0.34)), 0.30, 'fin', 0.014, wide=(1, 0, 0))
    fin(add, B.p((0.04 * sw, 0.14, -0.10)), B.p((0.12 * sw, 0.0, 0.12)), 0.27, 'fin', 0.014, wide=(1, 0, 0))
    for sx in (-1, 1):
        fin(add, B.p((sx * 0.42, 0.86, 0.04)), B.p((sx * 0.80, 0.70 + 0.10 * np.sin(ph + sx), 0.12)), 0.17, 'fin', 0.014, wide=(0, 1, 0))
        fin(add, B.p((sx * 0.22, 0.45, -0.02)), B.p((sx * 0.42, 0.22, -0.16)), 0.10, 'fin', 0.012)
    fin(add, B.p((0, 1.20, -0.26)), B.p((0.02 * sw, 1.50, -0.52)), 0.12, 'fin', 0.014, wide=(0, 0, 1))
    # the clear dome head with a small low mouth beneath it
    hc = B.p((0, 1.30, 0.10))
    add(Ellipsoid(hc, (0.38, 0.32, 0.40), None), 'glass', 0.08)
    mc = B.p((0, 1.04, 0.36))
    add(Ellipsoid(mc, (0.09, 0.05 + 0.05 * op, 0.07), None), 'gum', 0.04)
    add(Capsule(mc + v3(-0.05, 0.02, 0.04), mc + v3(-0.045, -0.06 - 0.03 * op, 0.07), 0.012, 0.004), 'tooth')
    add(Capsule(mc + v3(0.05, 0.02, 0.04), mc + v3(0.045, -0.06 - 0.03 * op, 0.07), 0.012, 0.004), 'tooth')
    pl = Placer(P, yaw=0.55, hover=0.12, shift=-0.0, back=0.0)
    look_up = 0.4 + 0.5 * np.sin(2 * np.pi * P['tell'] * 1.0) * 0.3 + 0.3 * st
    organs = [Organ(pl.pt(B.p((0, 1.36, 0.0))), (0.15, 0.10, 0.18), _hex('#f0a0c0'), 0.05, 0.95),
              Organ(pl.pt(B.p((0, 1.40, -0.10))), (0.10, 0.06, 0.12), _hex('#e07898'), 0.0, 0.95)]
    eye_glow = 0.35 + 0.35 * np.sin(2 * np.pi * P['tell'] * 1.0) ** 2 + 0.4 * P['cast_glow']
    for sx in (-1, 1):
        # tubular eyes pointing up and slightly forward, roughly where the beam is
        ec = B.p((sx * 0.17, 1.28, 0.20))
        organs.append(Organ(pl.pt(ec), (0.135, 0.14, 0.135), _hex('#5fdc78'), eye_glow, 0.98))
        organs.append(Organ(pl.pt(ec + v3(sx * 0.0, 0.06, 0.02)), (0.05, 0.05, 0.05), _hex('#e6fff0'), 0.5, 0.98))
    mats = std_mats(P, {'skin': skin(top=_hex('#3c5c88'), organs=[Organ(pl.pt(B.p((0, 0.9, 0.0))), (0.2, 0.30, 0.2), _hex('#e08ca4'), 0.0, 0.6)],
                                     veins=0.3, glow=0.8, local=pl.inv, depth=0.5, spec=0.4),
                        'glass': jelly(organs, glow=0.5, depth=0.55, tint=tuple(np.array(CERU) * 0.5 + np.array(PEARL) * 0.5), spec=1.0)})
    lights = [under_light(P, v3(0, 0.1, 0.1), 1.0, 1.2), Light(pl.pt(hc + v3(0, 0.05, 0.1)), GREEN, 0.5 * eye_glow * P['glow'], 0.5)]
    dp = [pl.pt(B.p((0.3, 0.4, 0.1))), pl.pt(B.p((-0.3, 0.8, 0.2)))]

    def world(add2):
        drips(add2, P, dp)
        spray(add2, P, pl.pt(B.p((0, 1.0, 0.5))))
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.3, 1.0, 0.0, 0.3), atk_strike=(0.0, 0.5, 1.0, 0.3))

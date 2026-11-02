"""Tongue-Louse (Overcurrent skirmisher). A dog-sized parasitic isopod: glassy overlapping back plates with the
blood-gorged gut and a red dorsal vessel showing through, seven pairs of hooked legs, black bead eyes,
long feelers and a hooked mouth cone that fits a mouth exactly. Defining detail: red blood under glass plates.
Tell: the gut pulses and the swimmerets under the belly glow cyan."""
from _overcurrent_common import *

UNIT_ID = 'overcurrent_tongue_louse'
CAMERA = Camera(ppm=50)
S = 1.2


def neutral_pose():
    return pose()


def build(P):
    parts, add = new_parts()
    ph, st, op = P['ph'], P['strike'], P['open']
    z0 = 0.14 * st
    F = Frame((0, 0.0, z0), rot_x(-0.05 + 0.12 * st), S)
    pulse = 0.5 + 0.5 * np.sin(2 * np.pi * P['tell'])
    # back plates, head to tail
    n = 8
    zs = np.linspace(0.30, -0.50, n)
    for i, z in enumerate(zs):
        u = i / (n - 1)
        wx = 0.26 * (1 - 0.30 * abs(u - 0.35) ** 1.4) * (1 - 0.45 * max(u - 0.6, 0) / 0.4)
        hy = 0.10 * (1 - 0.30 * u)
        F.ell(add, (0, 0.24 - 0.012 * i + 0.02 * np.sin(ph + i * 0.7), z), (wx, hy, 0.105), 'chitin', 0.02)
    # head shield + eyes + feelers
    F.ell(add, (0, 0.24, 0.42), (0.20, 0.10, 0.12), 'chitin', 0.02)
    for sx in (-1, 1):
        F.sph(add, (sx * 0.15, 0.27, 0.46), 0.050, 'eyeb')
        pts = [v3(sx * 0.10, 0.25, 0.50), v3(sx * 0.24, 0.34, 0.66), v3(sx * 0.42, 0.42 + 0.03 * np.sin(ph + sx), 0.74),
               v3(sx * 0.58, 0.34, 0.78)]
        sp = spline(pts, 8)
        for a, b, r in zip(sp[:-1], sp[1:], np.linspace(0.016, 0.005, 7)):
            F.cap(add, a, b, r, r * 0.9, 'chitin')
    # mouth cone with hooked fangs (opens on attack)
    F.ell(add, (0, 0.12, 0.54), (0.09, 0.06 + 0.03 * op, 0.09), 'gum', 0.02)
    for sx in (-1, 1):
        a = v3(sx * 0.06, 0.12, 0.60)
        F.cap(add, a, a + v3(sx * (0.03 + 0.07 * op), -0.06 - 0.02 * op, 0.10), 0.02, 0.006, 'tooth')
        F.cap(add, a + v3(sx * (0.03 + 0.07 * op), -0.06 - 0.02 * op, 0.10), a + v3(-sx * 0.01, -0.10, 0.17), 0.006, 0.004, 'tooth')
    # tail fan
    F.ell(add, (0, 0.14, -0.62), (0.14, 0.06, 0.10), 'chitin', 0.02)
    for sx in (-1, 1):
        F.ell(add, (sx * 0.12, 0.11, -0.74), (0.045, 0.02, 0.10), 'fin', 0.0, R2=rot_y(sx * 0.35))
    # legs: seven pairs, alternating gait
    feet = []
    for i in range(7):
        z = lerp(0.28, -0.40, i / 6)
        for sx in (-1, 1):
            g = ph * 1.0 + i * 0.9 + (0 if sx > 0 else np.pi)
            lift = max(0.0, np.sin(g)) * (0.10 if abs(P['stride']) > 0 or st > 0 else 0.03)
            sw = 0.05 * np.cos(g) * (1 if P['stride'] != 0 else 0.3)
            root = v3(sx * 0.18, 0.15, z)
            knee = v3(sx * 0.33, 0.22, z + 0.03 + sw * 0.5)
            foot = v3(sx * 0.37, lift, z + sw - 0.04)
            hook = foot + v3(-sx * 0.02, 0.0, 0.05)
            F.cap(add, root, knee, 0.032, 0.024, 'chitin', 0.01)
            F.cap(add, knee, foot + v3(0, 0.02, 0), 0.024, 0.014, 'chitin')
            F.cap(add, foot + v3(0, 0.02, 0), hook, 0.012, 0.004, 'tooth')
            feet.append(F.p(foot))
        F.sph(add, (0, 0.04, z), 0.034 + 0.01 * pulse, 'glow')       # glowing swimmerets under the belly
    pl = Placer(P, yaw=0.30, hover=0.02, shift=0.16, back=0.5)
    organs = [Organ(pl.pt(F.p((0, 0.20, -0.05))), (0.17, 0.09, 0.30), _hex('#d83a50'), 0.2 * pulse, 0.85),
              Organ(pl.pt(F.p((0, 0.25, 0.1))), (0.04, 0.04, 0.38), _hex('#ff5a6e'), 0.3 * pulse, 0.8),
              Organ(pl.pt(F.p((0.0, 0.2, 0.34))), (0.08, 0.06, 0.07), _hex('#e87a90'), 0.0, 0.7)]
    mats = std_mats(P, {'chitin': skin(under=tuple(np.array(PEARL) * 0.62 + np.array(CERU) * 0.2),
                                       top=tuple(np.array(CERU) * 0.70 + np.array(PEARL) * 0.15),
                                       organs=organs, glow=0.5, depth=0.5, spec=0.5, wet=60, mottle=0.04, local=pl.inv)})
    lights = [under_light(P, v3(0, 0.05, 0.0), 0.9, 0.8)]
    dp = [pl.pt(F.p((0.1, 0.35, 0.6)))]

    def world(add2):
        drips(add2, P, dp)
        spray(add2, P, pl.pt(F.p((0, 0.3, 0.6))), n=3)
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


def _extra(rows):
    for i, (P, o) in enumerate(rows['move']):
        P['stride'] = 1.0
        P['ph'] = 2 * np.pi * i / 4 * 1.0


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.3, 1.0, 0.0, 0.3), atk_strike=(0.0, 0.5, 1.0, 0.3), extra=_extra)

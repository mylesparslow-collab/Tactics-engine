"""Ribbon King (Overcurrent mobile). An oarfish thirty feet long, silver and boneless, rearing in a tall S, a crest
of red filaments streaming from its crown like blood in water, a red-edged fin along the whole back, and two long
oar-fins hanging below the throat. The body shows no motion; the crest does all the moving.
Defining detail: the red crest. Tell: crest and fin ripple while the body hangs still."""
from _overcurrent_common import *

UNIT_ID = 'overcurrent_ribbon_king'
CAMERA = Camera(ppm=46)


def neutral_pose():
    return pose()


def spine(P):
    ph, st = P['ph'], P['strike']
    w = lambda a, t: a * np.sin(ph - t * 4.0)
    return [v3(-0.80, 0.22, -0.1), v3(-0.40 + w(0.05, 0.0), 0.12, 0.0), v3(0.15 + w(0.06, 0.2), 0.20, 0.0),
            v3(0.58 + w(0.06, 0.4), 0.55, 0.0), v3(0.50 + w(0.05, 0.6), 1.00, 0.0),
            v3(0.05 + w(0.04, 0.8), 1.38, 0.0 + 0.2 * st), v3(-0.35, 1.62, 0.05 + 0.2 * st), v3(-0.05, 1.85, 0.10 + 0.4 * st)]


def build(P):
    parts, add = new_parts()
    ph, st, op = P['ph'], P['strike'], P['open']
    pts = spine(P)
    n = 32
    s = ribbon(add, pts, [0.02, 0.10, 0.13, 0.14, 0.14, 0.13, 0.12, 0.11, 0.09], [0.02, 0.04, 0.05, 0.055, 0.055, 0.055, 0.05, 0.05, 0.045],
               'skin', n=n, k=0.04, side=v3(0.35, 1.0, 0.0))
    # red-edged dorsal fin: a comb of fine rays along the whole outer curve, rippling
    for i in range(3, n - 3):
        t = norm(s[i + 1] - s[i - 1])
        nrm = norm(np.cross(v3(0, 0, 1), t))
        nrm = -nrm
        wd = 0.13 * (1 - 0.3 * abs(i / n - 0.5))
        L = 0.20 + 0.05 * np.sin(ph + i * 0.7)
        add(Capsule(s[i] + nrm * wd, s[i] + nrm * (wd + L), 0.012, 0.006), 'finred', 0.012)
    H = Frame(s[-1], basis_from(norm(s[-1] - s[-4]), v3(0, 0, 1)), 1.0)
    H.ell(add, (0, 0.05, 0), (0.095, 0.17, 0.085), 'skin', 0.04)
    mo = 0.05 + 0.10 * op
    H.ell(add, (0.0, 0.22, 0.0), (0.045, 0.04 + mo, 0.05), 'gum', 0.03)
    H.cap(add, (0.0, 0.24, 0.0), (0.0, 0.36 + 0.2 * op, 0.0), 0.02, 0.01, 'tooth')
    H.sph(add, (0.0, 0.12, 0.075), 0.062, 'eyeb')
    H.sph(add, (0.0, 0.14, 0.12), 0.026, 'tooth')
    # crest: long red filaments streaming back from the crown like blood in water
    cb = H.p((0, 0.0, 0.0)) + v3(0, 0.08, 0)
    for j in range(11):
        base = cb + v3(0.02 * j * 0.1, 0.0, (j - 5) * 0.012)
        L = 1.0 + 0.15 * (j % 3)
        prev = base
        for m in range(1, 7):
            h = m / 6
            cur = base + v3(-0.62 * L * h, 0.05 + 0.20 * np.sin(h * 2.6) - 0.28 * h * h * 0 + 0.05 * np.sin(ph - h * 4 + j) - 0.1 * h * h,
                            (j - 5) * 0.03 * h + 0.03 * np.sin(ph - h * 5 + j * 0.7))
            add(Capsule(prev, cur, 0.016 * (1 - 0.6 * h), 0.016 * (1 - 0.6 * (h + 0.17))), 'finred', 0.012)
            prev = cur
    for sx in (-1, 1):
        a = s[-4] + v3(0.0, -0.10, sx * 0.05)
        pts2 = [a, a + v3(0.06, -0.30, sx * 0.04), a + v3(0.20 + 0.05 * np.sin(ph), -0.58, sx * 0.06)]
        tube(add, pts2, [0.014, 0.011, 0.008], 'finred', n=5, k=0.0)
        add(Ellipsoid(pts2[-1] + v3(0.02, -0.04, 0), (0.03, 0.065, 0.02), None), 'finred', 0.0)
    pl = Placer(P, yaw=-0.05, hover=0.12, shift=-0.02, back=0.1)
    organs = [Organ(pl.pt(s[18]), (0.07, 0.12, 0.12), _hex('#d78ca2'), 0.0, 0.5)]
    mats = std_mats(P, {'skin': skin(top=_hex('#8aa8c4'), under=_hex('#e8eef8'), organs=organs, veins=0.0, glow=0.9,
                                     local=pl.inv, depth=0.3, spec=1.0, wet=70, mottle=0.12)})
    lights = [under_light(P, v3(0, 0.3, 0.1), 1.0, 1.3)]
    dp = [pl.pt(s[10] + v3(0.1, 0, 0.1)), pl.pt(s[22] + v3(0.1, 0, 0.1))]

    def world(add2):
        drips(add2, P, dp)
        spray(add2, P, pl.pt(pts[-1]))
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.2, 0.6, 1.0, 0.3), atk_strike=(0.0, 0.5, 1.0, 0.3), idle_amp=0.6)

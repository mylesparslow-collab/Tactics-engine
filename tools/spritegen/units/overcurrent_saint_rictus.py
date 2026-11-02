"""Saint Rictus, the Jaw That Prays (Overcurrent hero). A large pale-pink goblin shark mid-lunge, the sling-jaw flung
out on a ligament longer than its body, three rows of needle teeth bared, a collar of oversized red gill frills
fanned like a vestment, old bite scars across the flank, cyan underside. A thin gold-pearl glint on every tooth tip.
Defining detail: the jaw thrown out at full stretch, and the gold-tipped teeth. Tell: frills flutter, drops stream up."""
from _overcurrent_common import *

UNIT_ID = 'overcurrent_saint_rictus'
CAMERA = Camera(ppm=44)


def neutral_pose():
    return pose(open=0.45)


def bites(q, n):
    f = fbm(q + 4.4, 7.0, 3)
    m = f > 0.66
    return m, np.array(_hex('#a0607c'))[None, :] * (0.85 + 0.3 * f[:, None]).repeat(3, 1)


def build(P):
    parts, add = new_parts()
    ph, st, op = P['ph'], P['strike'], P['open']
    F = Frame((0, 0, 0), None, 1.0)
    J = goblin(F, add, ph=ph, ext=0.9 + 0.1 * st, gape=0.3 + 0.7 * op, bulk=1.5, ntooth=10, js=1.8, frills=6, tl=0.26, gold=True, tr=0.03, snout=1.45, reach=1.6, lig=True)
    # collar of oversized frills fanned behind the gills
    for sx in (-1, 1):
        for i in range(4):
            base = F.p((sx * 0.17, 0.02 + 0.03 * i, 0.10 - 0.07 * i))
            tip = base + v3(sx * 0.16, 0.10 - 0.03 * i + 0.03 * np.sin(ph + i), -0.05 - 0.02 * i)
            add(Capsule(base, tip, 0.016, 0.005), 'finred', 0.01)
            add(Ellipsoid((base + tip) / 2, (0.012, 0.09, 0.05), None), 'finred', 0.0)
    pl = Placer(P, yaw=0.10, pitch=0.12 + 0.10 * st, hover=0.85, shift=-0.05, back=0.55, scale=0.70)
    organs = [Organ(pl.pt(v3(0, -0.02, -0.15)), (0.14, 0.12, 0.30), _hex('#e08aa0'), 0.0, 0.6),
              Organ(pl.pt(v3(0, 0.0, 0.15)), (0.07, 0.08, 0.08), _hex('#c4344a'), 0.0, 0.6)]
    mats = std_mats(P, {'skin': skin(top=_hex('#a8929e'), under=_hex('#e6ccd2'), organs=organs, veins=0.35, glow=0.8, spots=bites,
                                     local=pl.inv, depth=0.4, spec=0.4, mottle=0.06)})
    lights = [under_light(P, v3(0, 0.2, 0), 1.1, 1.6)]
    streams = [pl.pt(v3(sx * 0.2, 0.2 + 0.1 * i, -0.4 - 0.25 * i)) for i, sx in enumerate((-1, 1, -1, 1))]

    def world(add2):
        for i, q in enumerate(streams):
            if P['end'] > 0.3:
                break
            t = (P['tell'] + i * 0.27) % 1.0
            add2(Sphere(q + v3(0, 0.15 + 0.7 * t, 0), 0.028 * (1.2 - 0.6 * t)), 'water', 0.0)
        spray(add2, P, pl.pt(J.p((0, 0, 0.3))))
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.4, 1.0, 0.0, 0.3), atk_strike=(0.0, 0.5, 1.0, 0.3), idle_amp=0.7)

"""Saint Rictus, the Jaw That Prays (Overcurrent hero). A large pale-pink goblin shark mid-lunge, the sling-jaw flung
out on a ligament longer than its body, three rows of needle teeth bared, a collar of oversized red gill frills
fanned like a vestment, old bite scars across the flank, cyan underside. A thin gold-pearl glint on every tooth tip.
Defining detail: the jaw thrown out at full stretch, and the gold-tipped teeth. Tell: frills flutter, drops stream up."""
from _overcurrent_common import *

UNIT_ID = 'overcurrent_saint_rictus'
CAMERA = Camera(ppm=44)
YAW, PITCH, SHIFT = 0.80, 0.16, -0.08


def neutral_pose():
    return pose(open=0.45)


def bites(q, n):
    f = fbm(q + 4.4, 7.0, 3)
    m = f > 0.66
    return m, np.array(_hex('#a0607c'))[None, :] * (0.85 + 0.3 * f[:, None]).repeat(3, 1)


def jitter(i, a=1.0):
    return a * (np.sin(i * 12.9898 + 4.1) * 0.5 + np.sin(i * 7.3 + 1.7) * 0.5)


def shark(F, add, ph=0.0, ext=0.7, gape=0.5, ntooth=6):
    """Heavy goblin shark in frame F (nose +z, back +y): thick body, blade snout, jaw slung on a pink ligament,
    dark red maw, short irregular curved needle teeth."""
    sw = np.sin(ph)
    pts = [F.p((0, 0.08, -1.10)), F.p((0.03 * sw, 0.06, -0.75)), F.p((0.02 * sw, 0.03, -0.30)), F.p((0, 0.02, 0.08)), F.p((0, 0.0, 0.40))]
    tube(add, pts, [0.035, 0.13, 0.27, 0.29, 0.20], 'skin', n=14, k=0.07)
    F.ell(add, (0, 0.0, 0.30), (0.24, 0.23, 0.26), 'skin', 0.08)
    # belly keel (glowing underside edge)
    F.ell(add, (0, -0.19, -0.05), (0.14, 0.05, 0.55), 'glow', 0.05)
    # blade snout
    F.ell(add, (0, 0.10, 0.62), (0.11, 0.03, 0.40), 'snout', 0.04)
    F.ell(add, (0, 0.06, 0.45), (0.17, 0.07, 0.18), 'snout', 0.04)
    # tail (kept short enough to stay in frame)
    fin(add, F.p((0, 0.05, -0.95)), F.p((0.04 * sw, 0.46, -1.28)), 0.09, 'fin', 0.014, wide=(0, 0, 1))
    fin(add, F.p((0, 0.04, -1.0)), F.p((0.03 * sw, -0.24, -1.25)), 0.06, 'fin', 0.014, wide=(0, 0, 1))
    fin(add, F.p((0, 0.22, -0.10)), F.p((0, 0.58, -0.40)), 0.15, 'fin', 0.016, wide=(0, 0, 1))
    fin(add, F.p((0, 0.10, -0.62)), F.p((0, 0.28, -0.76)), 0.07, 'fin', 0.012, wide=(0, 0, 1))
    for sx in (-1, 1):
        fin(add, F.p((sx * 0.20, -0.08, 0.10)), F.p((sx * 0.60, -0.26 + 0.05 * sw * sx, -0.30)), 0.18, 'fin', 0.015)
        fin(add, F.p((sx * 0.10, -0.12, -0.55)), F.p((sx * 0.30, -0.24, -0.78)), 0.08, 'fin', 0.012)
        F.sph(add, (sx * 0.17, 0.12, 0.40), 0.04, 'eyeb')
        F.sph(add, (sx * 0.185, 0.125, 0.42), 0.014, 'tooth')
    # red gill-frill collar: a fan of broad frills behind the head
    n = 9
    for sx in (-1, 1):
        for i in range(n):
            a = -0.9 + 1.8 * i / (n - 1)            # angle around the neck, bottom to top
            rt = 0.20
            base = F.p((sx * 0.20 * np.cos(a), 0.2 * np.sin(a) + 0.03, 0.12))
            ln = 0.36 + 0.06 * np.cos(a * 1.5) + 0.02 * np.sin(ph + i)
            tip = base + F.d((sx * 0.20 * np.cos(a) + 0.0, 0.34 * np.sin(a), -ln))
            fin(add, base, tip, 0.07, 'finred', 0.012, wide=(sx * 0.5, 0, 0.0) if False else None)
            add(Sphere(tip, 0.02), 'finred', 0.0)
    # sling-jaw on a visible pink ligament
    ex = 0.12 + 0.50 * ext
    A = v3(0, -0.12, 0.26)
    Bj = v3(0, -0.16, 0.26 + ex)
    for sx in (-1, 1):
        F.cap(add, (sx * 0.10, -0.08, 0.22), (sx * 0.09, -0.16, 0.26 + ex), 0.032, 0.025, 'lig', 0.0)
    F.cap(add, (0, -0.12, 0.22), (0, -0.16, 0.30 + ex), 0.08, 0.06, 'lig', 0.04)
    J = F.child((0, -0.16, 0.26 + ex), None, 2.1)
    # upper jaw block
    J.ell(add, (0, 0.04, 0.12), (0.12, 0.055, 0.21), 'skin', 0.03)
    # dark red maw cavity
    J.ell(add, (0, -0.03, 0.12), (0.095, 0.06 + 0.05 * gape, 0.17), 'maw', 0.0)
    for i in range(ntooth):
        z = 0.03 + i * 0.052
        for sx in (-1, 1):
            j = jitter(i * 2 + (sx > 0))
            L = 0.075 + 0.025 * j
            q = v3(sx * 0.098, 0.0, z)
            m = q + v3(-sx * 0.006, -L * 0.6, 0.012 * j)
            t = m + v3(-sx * 0.014, -L * 0.45, -0.018)
            J.tooth(add, q, m, 0.013, 'tooth'); J.tooth(add, m, t, 0.009, 'tooth')
            J.sph(add, t, 0.0085, 'gold')
    JL = J.child((0, -0.01, 0.0), rot_x(0.25 + 0.80 * gape))
    JL.ell(add, (0, -0.045, 0.12), (0.105, 0.045, 0.21), 'skin', 0.0)
    JL.ell(add, (0, -0.005, 0.12), (0.085, 0.025, 0.17), 'maw', 0.0)
    for i in range(ntooth - 1):
        z = 0.04 + i * 0.055
        for sx in (-1, 1):
            j = jitter(i * 3 + 5 + (sx > 0))
            L = 0.065 + 0.025 * j
            q = v3(sx * 0.088, 0.0, z)
            m = q + v3(-sx * 0.005, L * 0.6, 0.012 * j)
            t = m + v3(-sx * 0.012, L * 0.45, -0.016)
            JL.tooth(add, q, m, 0.012, 'tooth'); JL.tooth(add, m, t, 0.008, 'tooth')
            JL.sph(add, t, 0.0085, 'gold')
    return J


def build(P):
    parts, add = new_parts()
    ph, st, op = P['ph'], P['strike'], P['open']
    F = Frame((0, 0, 0), None, 1.0)
    J = shark(F, add, ph=ph, ext=0.75 + 0.25 * st, gape=0.55 + 0.55 * op)
    pl = Placer(P, yaw=YAW, pitch=PITCH + 0.10 * st, hover=0.75, shift=SHIFT, back=0.0, scale=0.72)
    organs = [Organ(pl.pt(v3(0, -0.02, -0.15)), (0.14, 0.12, 0.30), _hex('#e08aa0'), 0.0, 0.3)]
    mats = std_mats(P, {
        'skin': skin(top=_hex('#b49aa8'), under=_hex('#ecd0d8'), organs=organs, veins=0.2, glow=1.0, spots=bites,
                     local=pl.inv, depth=0.4, spec=0.4, mottle=0.06),
        'lig': Material(_hex('#e888a4'), spec=0.7, gloss=40, sss=0.6),
        'maw': Material(_hex('#7a1a30'), spec=0.3, gloss=20, emissive=(0.05, 0.0, 0.02), rim=0.0),
        'finred': Material(_hex('#d8283f'), spec=0.5, gloss=40, sss=0.5, emissive=(0.10, 0.0, 0.02)),
        'tooth': Material(_hex('#f4f0ff'), spec=0.5, gloss=60, sss=0.3),
    })
    lights = [under_light(P, v3(0, 0.1, 0), 1.2, 1.8)]
    streams = [pl.pt(v3(sx * 0.25, 0.3 + 0.1 * i, -0.3 - 0.2 * i)) for i, sx in enumerate((-1, 1, -1, 1))]

    def world(add2):
        for i, q in enumerate(streams):
            if P['end'] > 0.3:
                break
            t = (P['tell'] + i * 0.27) % 1.0
            add2(Sphere(q + v3(0, 0.15 + 0.6 * t, 0), 0.028 * (1.2 - 0.6 * t)), 'water', 0.0)
        spray(add2, P, pl.pt(J.p((0, 0, 0.3))))
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.4, 1.0, 0.0, 0.3), atk_strike=(0.0, 0.5, 1.0, 0.3), idle_amp=0.7)

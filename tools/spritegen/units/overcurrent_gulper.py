"""Gulper (Overcurrent melee). An eel that is mostly mouth: pale body reared in an S out of its own coil,
the unhinged jaw bigger than the whole animal, pink throat hooked with teeth, a cyan lure at the tail tip,
a stomach stretched tight and visible under the skin.
Defining detail: the gape. Tell: belly-light breathing and a slow wave down the body."""
from _overcurrent_common import *
from kit.fx import emit

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
    s = tube(add, pts, [0.012, 0.035, 0.07, 0.105, 0.13, 0.12, 0.10, 0.085], 'skin', n=22, k=0.05)
    tip = pts[0]
    add(Capsule(tip, tip + v3(0.04, 0.13, 0.05), 0.012, 0.009), 'skin', 0.0)
    lure_c = tip + v3(0.04, 0.18, 0.05)
    add(Sphere(lure_c, 0.055), 'lure', 0.0)
    for i in range(3, 20, 3):
        a = s[i]
        add(Capsule(a + v3(0, 0.12, 0), a + v3(0, 0.20, -0.03), 0.007, 0.003), 'fin', 0.0)
    # head frame at the neck, pitched by the animation; small skull, the pouch of a mouth dominates
    pitch = 0.45 + 0.30 * st - 0.25 * op
    H = Frame(pts[-1] + v3(0, 0.02, 0.0), rot_x(pitch), 1.30)
    gape = 0.70 + 0.70 * op
    # skull + thin upper jaw
    H.ell(add, (0, 0.06, 0.04), (0.17, 0.14, 0.17), 'skin', 0.06)
    H.ell(add, (0, 0.05, 0.30), (0.19, 0.05, 0.34), 'skin', 0.0)
    H.ell(add, (0, 0.005, 0.30), (0.17, 0.022, 0.31), 'gum', 0.0)
    for sx in (-1, 1):
        H.sph(add, (sx * 0.13, 0.11, 0.10), 0.03, 'eyeb')
        H.sph(add, (sx * 0.14, 0.12, 0.11), 0.011, 'tooth')
    # irregular small hooked teeth, upper (hang down, hook inward)
    for sx in (-1, 1):
        rng = np.random.default_rng(3 + (sx > 0))
        for i in range(6):
            z = 0.12 + i * 0.085 + rng.uniform(-0.02, 0.02)
            L = 0.055 + rng.uniform(-0.02, 0.035)
            q = v3(sx * (0.165 - 0.01 * i / 5), 0.0, z)
            m = q + v3(-sx * 0.004, -L * 0.65, 0.0)
            t = m + v3(-sx * 0.022, -L * 0.40, 0.012)
            H.tooth(add, q, m, 0.015, 'tooth'); H.tooth(add, m, t, 0.009, 'tooth')
    J = H.child((0, -0.01, 0.02), rot_x(gape))
    # slack lower jaw: thin bone rim with a stretchy dark pouch hanging beneath it
    J.ell(add, (0, -0.05, 0.34), (0.16, 0.035, 0.38), 'skin', 0.0)
    J.ell(add, (0, -0.02, 0.34), (0.15, 0.02, 0.34), 'gum', 0.0)
    J.ell(add, (0, -0.13 - 0.05 * op, 0.30), (0.21, 0.10 + 0.06 * op, 0.34), 'pouch', 0.05)
    for sx in (-1, 1):
        rng = np.random.default_rng(9 + (sx > 0))
        for i in range(5):
            z = 0.16 + i * 0.09 + rng.uniform(-0.025, 0.025)
            L = 0.05 + rng.uniform(-0.015, 0.035)
            q = v3(sx * 0.15, 0.0, z)
            m = q + v3(-sx * 0.004, L * 0.65, 0.0)
            t = m + v3(-sx * 0.02, L * 0.40, 0.014)
            J.tooth(add, q, m, 0.014, 'tooth'); J.tooth(add, m, t, 0.008, 'tooth')
    # stretchy membrane between the jaws: a dark cavity that spans the gape
    mid = rot_x(gape * 0.5)
    H.ell(add, (0, -0.012 - 0.12 * np.sin(gape * 0.5), 0.02 + 0.30 * np.cos(gape * 0.5)),
          (0.19, 0.05 + 0.24 * np.sin(gape * 0.5), 0.34 * (0.6 + 0.4 * np.cos(gape * 0.5))), 'abyss', 0.0, R2=mid)
    H.ell(add, (0, -0.02 - 0.17 * np.sin(gape * 0.5), 0.10 + 0.30 * np.cos(gape * 0.5)),
          (0.20, 0.03 + 0.15 * np.sin(gape * 0.5), 0.24), 'membrane', 0.04, R2=mid)
    pl = Placer(P, yaw=YAW, hover=0.05, shift=-0.12)
    organs = [Organ(pl.pt(s[8] + v3(-0.02, 0.0, 0.0)), (0.11, 0.26, 0.10), _hex('#e08aa0'), 0.0, 0.75),
              Organ(pl.pt(s[14]), (0.075, 0.10, 0.07), _hex('#c4344a'), 0.0, 0.7)]
    mats = std_mats(P, {
        'skin': skin(top=_hex('#3a6488'), under=_hex('#eee8fa'), organs=organs, veins=0.35, local=pl.inv, glow=0.9,
                     depth=0.55, mottle=0.10),
        'abyss': Material(ABYSS, spec=0.1, gloss=10, rim=0.0),
        'membrane': Material(_hex('#3a1430'), spec=0.5, gloss=30, sss=0.5, emissive=(0.10, 0.01, 0.03), rim=0.1),
        'pouch': Material(_hex('#2c1030'), spec=0.4, gloss=30, sss=0.4, emissive=(0.04, 0.0, 0.03), rim=0.1),
        'gum': Material(_hex('#c4344a'), spec=0.7, gloss=40, sss=0.6),
        'tooth': Material(_hex('#f4f0ff'), spec=0.5, gloss=60, sss=0.3),
        'fin': Material(_hex('#6fa8cc'), spec=0.5, gloss=40, sss=0.6)})
    lights = [under_light(P, pl.pt(s[10]) * v3(1, 0, 1) + v3(0, 0.1, 0), 1.0, 1.0),
              Light(pl.pt(lure_c), CYAN, 1.4 * P['glow'], 0.7)]
    dp = [pl.pt(H.p((0.0, 0.1, 0.9))), pl.pt(s[10] + v3(0.1, 0, 0))]

    def world(add2):
        drips(add2, P, dp)
        if P['strike'] > 0.15:
            emit(add2, pl.pt(H.p((0, -0.1, 0.8))), 'spray', 0.6 + 1.2 * P['strike'])
        emit(add2, pl.pt(lure_c) + v3(0, 0.05, 0), 'mist', 0.25 * max(P['glow'], 0.0) * (1 - P['end']))
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.6, 1.0, 0.0, 0.3), atk_strike=(0.0, 0.4, 1.0, 0.3))

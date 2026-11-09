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
            v3(-0.20 + w(0.2, 0.05), 0.15, -0.34), v3(-0.24, 0.42, -0.36 - 0.05 * st),
            v3(0.10 + w(0.6, 0.04), 0.82, -0.18 + 0.06 * st), v3(-0.06, 1.18, -0.30 + 0.2 * st),
            v3(-0.02, 1.40, -0.12 + 0.18 * st)]


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
    # head: a small skull hinged to two long jaws that open into one dark maw (no extra layers)
    pitch = 0.35 + 0.30 * st - 0.15 * op
    H = Frame(pts[-1] + v3(0, 0.02, 0.0), rot_x(pitch), 1.30)
    g = 0.85 + 0.45 * op            # total gape angle
    H.ell(add, (0, 0.03, -0.02), (0.15, 0.15, 0.17), 'skin', 0.06)
    for sx in (-1, 1):
        H.sph(add, (sx * 0.12, 0.10, 0.04), 0.036, 'eyeb')
        H.sph(add, (sx * 0.13, 0.11, 0.05), 0.010, 'tooth')
    U = H.child((0, 0.03, 0.04), rot_x(-0.35 * g))
    Lw = H.child((0, -0.03, 0.04), rot_x(0.65 * g))
    L_JAW = 0.62
    # the maw: a fan of thin dark plates filling the V, darkest at the hinge
    for i, t in enumerate(np.linspace(0.06, 0.94, 12)):
        ang = -0.35 * g + t * g
        M = H.child((0, 0.03 - 0.06 * t, 0.04), rot_x(ang))
        M.ell(add, (0, 0.0, L_JAW * 0.42), (0.10, 0.03, L_JAW * 0.44), 'maw', 0.06)
    H.ell(add, (0, -0.02, 0.10), (0.11, 0.09, 0.09), 'abyss', 0.0)
    # jaws: skin outside, a red gum lip on the inner edge
    U.ell(add, (0, 0.035, L_JAW * 0.48), (0.15, 0.045, L_JAW * 0.52), 'skin', 0.03)
    U.ell(add, (0, -0.005, L_JAW * 0.46), (0.13, 0.018, L_JAW * 0.47), 'gum', 0.0)
    Lw.ell(add, (0, -0.05, L_JAW * 0.50), (0.15, 0.07, L_JAW * 0.54), 'skin', 0.03)
    Lw.ell(add, (0, 0.005, L_JAW * 0.48), (0.13, 0.018, L_JAW * 0.49), 'gum', 0.0)
    # few small hooked teeth, mostly toward the front of each jaw, curling inward
    for J, sgn, seed in ((U, -1, 3), (Lw, 1, 9)):
        for sx in (-1, 1):
            rng = np.random.default_rng(seed + (sx > 0))
            for i in range(3):
                z = L_JAW * (0.42 + 0.22 * i) + rng.uniform(-0.02, 0.02)
                ln = 0.11 + 0.025 * i + rng.uniform(-0.01, 0.015)
                q = v3(sx * 0.125, 0.0, z)
                m = q + v3(-sx * 0.01, sgn * ln * 0.6, 0.0)
                t_ = m + v3(-sx * 0.015, sgn * ln * 0.4, -0.02)
                J.tooth(add, q, m, 0.024, 'tooth'); J.tooth(add, m, t_, 0.013, 'tooth')
    pl = Placer(P, yaw=YAW, hover=0.05, shift=-0.12)
    organs = [Organ(pl.pt(s[8] + v3(-0.02, 0.0, 0.0)), (0.11, 0.26, 0.10), _hex('#e08aa0'), 0.0, 0.35),
              Organ(pl.pt(s[14]), (0.075, 0.10, 0.07), _hex('#c4344a'), 0.0, 0.3)]
    mats = std_mats(P, {
        'skin': skin(top=_hex('#3a6488'), under=_hex('#eee8fa'), organs=organs, veins=0.35, local=pl.inv, glow=0.9,
                     depth=0.55, mottle=0.10),
        'abyss': Material(ABYSS, spec=0.1, gloss=10, rim=0.0),
        'maw': Material(_hex('#6a1830'), spec=0.6, gloss=40, sss=0.3, rim=0.0),
        'gum': Material(_hex('#c4344a'), spec=0.7, gloss=40, sss=0.6),
        'tooth': Material(_hex('#f4f0ff'), spec=0.5, gloss=60, sss=0.3),
        'fin': Material(_hex('#6fa8cc'), spec=0.5, gloss=40, sss=0.6)})
    lights = [under_light(P, pl.pt(s[10]) * v3(1, 0, 1) + v3(0, 0.1, 0), 1.0, 1.0),
              Light(pl.pt(lure_c), CYAN, 1.4 * P['glow'], 0.7)]
    dp = [pl.pt(H.p((0.0, 0.0, 0.7))), pl.pt(s[10] + v3(0.1, 0, 0))]

    def world(add2):
        drips(add2, P, dp)
        if P['strike'] > 0.15:
            emit(add2, pl.pt(H.p((0, 0.0, 0.7))), 'spray', 0.6 + 1.2 * P['strike'])
        emit(add2, pl.pt(lure_c) + v3(0, 0.05, 0), 'mist', 0.25 * max(P['glow'], 0.0) * (1 - P['end']))
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.6, 1.0, 0.0, 0.3), atk_strike=(0.0, 0.4, 1.0, 0.3))

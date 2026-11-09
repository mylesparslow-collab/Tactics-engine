"""Rainmoth Cloud (Overcurrent, cheap ranged). A shoal of five grey moths clotted into one low raincloud: fat
fuzzy bodies, broad scalloped patterned wings beating out of step, plumed antennae, each lit cyan underneath,
and a veil of rain falling from the knot to the ground. Defining detail: the eyespotted wings and the rain
curtain. Tell: wings beat, drops rise off the bodies then fall."""
from _overcurrent_common import *

UNIT_ID = 'overcurrent_rainmoth_cloud'
CAMERA = Camera(ppm=56)

# x, y, z, yaw, size
MOTHS0 = [(0.00, 0.78, 0.20, 0.15, 0.95, 0.10), (-0.50, 0.95, -0.15, 0.95, 0.75, -0.35), (0.50, 1.00, -0.10, -0.75, 0.80, 0.30),
         (-0.12, 1.30, -0.30, 0.45, 0.62, 0.45), (0.28, 0.55, 0.60, -0.3, 0.55, -0.20), (-0.42, 0.58, 0.40, 1.4, 0.55, 0.25),
         (0.12, 1.08, -0.45, 2.4, 0.60, -0.4)]


MOTHS = [(x * 0.78, 0.30 + (y - 0.30) * 0.8, z * 0.78, yw, sz * 0.78, tl) for (x, y, z, yw, sz, tl) in MOTHS0]


def neutral_pose():
    return pose()


def wing_func(o, R, s, L, sz, flip):
    """Moth wing pair-half in frame (o, R): spans +x*s from the root, chord along z. Scalloped moth outline."""
    o = np.asarray(o)

    def f(p):
        q = ((p - o) @ R) / sz
        u = q[:, 0] * s
        w = q[:, 2]
        y = q[:, 1]
        # forewing and hindwing lobes (2D ellipses in u,w), scalloped
        a = np.sqrt(((u - 0.52 * L) / (0.52 * L)) ** 2 + ((w - 0.04) / 0.30) ** 2) - 1.0
        b = np.sqrt(((u - 0.36 * L) / (0.38 * L)) ** 2 + ((w + 0.22) / 0.22) ** 2) - 1.0
        d2 = smin(a * 0.15, b * 0.15, 0.05)
        th = np.arctan2(w - 0.0, u - 0.05)
        d2 = d2 + 0.006 * np.cos(11 * th)
        d2 = np.maximum(d2, -u + 0.0)
        d = smax(d2, np.abs(y) - 0.011, 0.01)
        return d * sz * 0.8
    return Func(f, o + R @ v3(s * L * 0.5 * sz, 0, -0.05 * sz), (L + 0.2) * sz)


def moth(add, mats, P, idx, c, yaw, sz, ph, pl, tilt=0.0):
    R = rot_y(yaw) @ rot_x(tilt)
    F = Frame(c, R, sz)
    fl = 0.40 * np.sin(ph) + 0.62
    F.ell(add, (0, 0, 0.16), (0.05, 0.05, 0.055), 'fuzz', 0.02)
    F.ell(add, (0, 0, 0.04), (0.07, 0.07, 0.09), 'fuzz', 0.03)
    F.ell(add, (0, -0.01, -0.13), (0.05, 0.05, 0.16), 'fuzz', 0.03)
    for s in (-1, 1):
        F.sph(add, (s * 0.036, 0.015, 0.20), 0.022, 'eyeb')
        a, b = np.array((s * 0.02, 0.04, 0.2)), np.array((s * 0.13, 0.19, 0.34))
        F.cap(add, a, b, 0.010, 0.006, 'fuzz')
        for j in range(7):
            t = 0.2 + 0.11 * j
            q = a + (b - a) * t
            F.cap(add, q, q + np.array((s * 0.06, 0.03, 0.05)), 0.007, 0.003, 'fuzz')
            F.cap(add, q, q + np.array((-s * 0.01, 0.03, 0.065)), 0.007, 0.003, 'fuzz')
        Rw = R @ rot_z(-s * fl)
        wo = F.p((s * 0.04, 0.05, 0.03))
        add(wing_func(wo, Rw, s, 0.40, sz, 1), 'wing%d' % idx, 0.0)


def wing_mat(local_fn, glow):
    def spots(q, n):
        u = np.abs(q[:, 0])
        w = q[:, 2]
        top = n[:, 1] > 0.1
        eye = np.sqrt((u - 0.30) ** 2 + (w - 0.03) ** 2)
        ring = (eye < 0.085) & top
        core = (eye < 0.042) & top
        band = (np.abs(u - 0.18 - 0.4 * (w + 0.1)) < 0.03) & top
        col = np.zeros((len(q), 3))
        col[:] = _hex('#eef2f8')
        col[core] = _hex('#2a3248')
        col[ring & ~core] = _hex('#dfe6f2')
        m = ring | band
        col[band & ~ring] = _hex('#58627c')
        return m, col
    return skin(top=_hex('#b4bccb'), under=_hex('#f2f5fa'), glow=glow, mottle=0.1, spec=0.15, wet=14, local=local_fn,
                spots=spots, veins=0.5, vein_col=_hex('#464f68'), vfreq=16.0, belly_cut=(0.0, 0.5))


def build(P):
    parts, add = new_parts()
    ph = P['ph']
    st = P['strike']
    pl = Placer(P, yaw=0.0, hover=0.0)
    mats = std_mats(P, {
        'fuzz': skin(top=_hex('#7d889e'), under=_hex('#e2e7f0'), glow=0.6, mottle=0.14, spec=0.05, wet=8),
        'rain': Material(_hex('#e4f6ff'), spec=0.3, gloss=40, emissive=tuple(np.array(CYAN) * 1.6), rim=0.1),
        'mist': skin(top=_hex('#a8b4c8'), under=_hex('#dce4f0'), glow=0.4, mottle=0.2, spec=0.0, wet=5)})
    frames = []
    for i, (x, y, z, yw, sz, tl) in enumerate(MOTHS):
        c = v3(x, y + 0.05 * np.sin(ph + i * 1.7), z + 0.18 * st * (1 if i % 2 else 0.5))
        R = rot_y(yw + 0.18 * np.sin(ph * 0.5 + i)) @ rot_x(tl)
        fl_ph = ph * 1.3 + i * 1.9
        fl = 0.40 * np.sin(fl_ph) + 0.62

        def loc(p, c=c, R=R, sz=sz):
            return ((p - c) @ R) / sz
        mats['wing%d' % i] = wing_mat(loc, 0.9)
        moth(add, mats, P, i, c, yw + 0.18 * np.sin(ph * 0.5 + i), sz, fl_ph, pl, tl)
        frames.append(c)
    # small mist knot under the shoal
    for (x, y, z, r) in [(0.0, 0.48, 0.0, 0.14), (-0.2, 0.46, 0.1, 0.10)]:
        add(Sphere(v3(x, y, z), r), 'mist', 0.08)
    rain = []
    for k in range(6):
        a = k * 2.4
        x, z = np.cos(a) * (0.08 + 0.55 * ((k * 5) % 7) / 7), np.sin(a) * (0.08 + 0.5 * ((k * 3) % 5) / 5)
        tt = (P['tell'] + k * 0.31) % 1.0
        y1 = 0.56 - tt * 0.34
        L = (0.22 + 0.06 * (k % 3)) * (1 + 0.5 * st)
        if y1 > 0.07:
            add(Capsule(v3(x, y1, z), v3(x, max(y1 - L, 0.03), z), 0.013, 0.008), 'rain', 0.0)
    lights = [under_light(P, v3(0, 0.15, 0.1), 1.0, 1.5)]
    dp = [pl.pt(v3(0.2, 0.8, 0.1)), pl.pt(v3(-0.4, 0.9, 0.0)), pl.pt(v3(0.5, 0.9, 0.0))]

    def world(add2):
        drips(add2, P, dp, rise=0.3)
        spray(add2, P, v3(0, 0.9, 0.2))
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.2, 0.5, 1.0, 0.3), atk_strike=(0.0, 0.4, 1.0, 0.3))

"""Wave-2 Lanternkeeper helpers (append-only; new file)."""
import numpy as np
from _lanternkeepers_common import *


def dust_albedo(base, dust=_hex('#e9f0f2'), density=0.09, freq=48.0, glint=_hex('#ffffff')):
    """Fabric with sparkling glass-dust specks (cells of a high-frequency noise)."""
    b = np.array(base)

    def fn(p, n):
        w = fbm(p, 16.0, 3)
        c = b[None, :] * (0.88 + 0.24 * w[:, None])
        s = vnoise(p, freq)
        m = np.clip((s - (1 - density)) / density, 0, 1)[:, None]
        s2 = vnoise(p + 7.0, freq * 0.37)
        m2 = np.clip((s2 - 0.93) / 0.07, 0, 1)[:, None]
        c = c * (1 - m) + np.array(dust)[None, :] * m
        c = c * (1 - m2) + np.array(glint)[None, :] * m2
        # lower hem gets dustier
        t = np.clip((1.0 - p[:, 1]) * 0.8, 0, 0.5)[:, None]
        c = c * (1 - 0.25 * t) + np.array(dust)[None, :] * 0.25 * t
        return np.clip(c, 0, 1)
    return fn


def cracked_lens(add, c, axis, r, rim='brass', cracks=((0.0, 0.8), (0.9, 0.6), (-1.1, 0.55)), chip=True):
    """Lens disc with dark crack lines across its face and a missing chip."""
    axis = norm(axis)
    lens_disc(add, c, axis, r, rim=rim)
    up = norm(np.cross(axis, v3(0, 1, 0))) if abs(axis[1]) < 0.95 else v3(1, 0, 0)
    up2 = norm(np.cross(up, axis))
    for a, ln in cracks:
        d = np.cos(a) * up + np.sin(a) * up2
        o = (np.sin(a * 2.3) * 0.25) * r * up2 + axis * 0.012
        add(Capsule(c + o - d * r * ln, c + o + d * r * ln, 0.0055, 0.0055), 'crack', 0.0)
    if chip:
        add(Ellipsoid(c + (up * 0.7 + up2 * 0.45) * r, (r * 0.28, 0.018, r * 0.28), basis_from(axis)), 'crack', 0.0)


__all__ = [n for n in dir() if not n.startswith('__')]


FALSE_LIGHT = _hex('#bfeee0')


def false_lamp(add, lights, P, c, size=1.0, swing=0.0, glow=None):
    """A lure lamp: hurricane lantern with a cold sea-green light (the one wrong colour among the keepers)."""
    g = P['glow'] * (1 + 0.8 * P['cast_glow']) if glow is None else glow
    up = norm(v3(swing, 1.0, 0.0))
    R = basis_from(up, (0, 0, 1))
    s = size
    add(Cylinder(c - up * 0.062 * s, c - up * 0.040 * s, 0.040 * s, 0.006), 'darkiron', 0.0)
    add(Ellipsoid(c, (0.036 * s, 0.050 * s, 0.036 * s), R), 'falselamp', 0.0)
    for t in (-0.022, 0.018):
        add(Torus(c + up * t * s, up, 0.037 * s, 0.0035 * s), 'darkiron', 0.0)
    for k in range(4):
        a = k * np.pi / 2 + 0.4
        o = R @ v3(np.cos(a) * 0.039, 0, np.sin(a) * 0.039) * s
        add(Capsule(c + o - up * 0.042 * s, c + o + up * 0.040 * s, 0.003 * s), 'darkiron', 0.0)
    add(Cylinder(c + up * 0.044 * s, c + up * 0.064 * s, 0.030 * s, 0.006), 'darkiron', 0.0)
    lights.append(Light(pos=c + v3(0, 0, 0.04), color=_hex('#9fe8d4'), intensity=1.7 * s * g, radius=0.18 * s))
    return c + up * 0.08 * s


def razor_oysters(add, c, n=5, seed=4, scale=1.0, mat='oyster'):
    """A cluster of razor oysters (ridged grey shells with white edges) on the ground."""
    rng = np.random.default_rng(seed)
    for i in range(n):
        a = rng.uniform(0, 6.28)
        r = rng.uniform(0.0, 0.11) * scale
        p = c + v3(np.cos(a) * r, 0.02 * scale, np.sin(a) * r)
        tilt = rng.uniform(0.2, 0.9)
        Rb = rot_y(a) @ rot_x(-tilt)
        add(Ellipsoid(p, (0.05 * scale, 0.018 * scale, 0.07 * scale), Rb), mat, 0.01)
        add(Ellipsoid(p + Rb @ v3(0, 0.012, 0.012) * scale, (0.040 * scale, 0.010 * scale, 0.058 * scale), Rb), 'oyster_edge', 0.0)


__all__ = [n for n in dir() if not n.startswith('__')]


def book_stack(add, c, yaw=0.0, n=5, seed=3, size=1.0, mats=('book_a', 'book_b', 'book_c', 'book_d'), ribbons=True):
    """Stack of logbooks (cloth covers, cream page-edges on the open side), centred on c (bottom of the stack)."""
    rng = np.random.default_rng(seed)
    y = 0.0
    for i in range(n):
        t = rng.uniform(0.030, 0.050) * size
        w = rng.uniform(0.085, 0.115) * size
        d = rng.uniform(0.115, 0.15) * size
        ya = yaw + rng.uniform(-0.25, 0.25)
        R = rot_y(ya)
        cc = c + v3(rng.uniform(-0.01, 0.01), y + t, rng.uniform(-0.01, 0.01))
        cm = mats[i % len(mats)]
        add(RoundBox(cc + R @ v3(w * 0.03, 0, d * 0.02), (w * 0.94, t * 0.80, d * 0.96), 0.004, R), 'wax', 0.0)   # pages
        add(RoundBox(cc + R @ v3(0, t * 0.88, 0), (w, t * 0.16, d), 0.004, R), cm, 0.0)                         # top board
        add(RoundBox(cc + R @ v3(0, -t * 0.88, 0), (w, t * 0.16, d), 0.004, R), cm, 0.0)                        # bottom board
        add(RoundBox(cc + R @ v3(-w * 0.93, 0, 0), (w * 0.09, t, d), 0.005, R), cm, 0.0)                         # spine
        if ribbons and i % 2 == 0:
            add(Capsule(cc + R @ v3(w * 0.3, 0, d), cc + R @ v3(w * 0.3 + 0.01, -t * 2.0 - 0.03, d + 0.025), 0.005, 0.004), 'ribbon', 0.0)
        y += 2 * t
    return c + v3(0, y, 0)


def spectacles(add, P, mat='brass'):
    H, R, h = P['head'], head_R(P), P['height']
    for sx in (-1, 1):
        c = H + R @ v3(sx * 0.034, 0.004, 0.083) * h
        add(Torus(c, R @ v3(0, 0, 1), 0.022, 0.0035), mat, 0.0)
        add(Ellipsoid(c, (0.020, 0.020, 0.004), R), 'lens', 0.0)
    add(Capsule(H + R @ v3(-0.012, 0.008, 0.086) * h, H + R @ v3(0.012, 0.008, 0.086) * h, 0.003), mat, 0.0)


def dome_lamp(add, lights, P, c, size=1.0, tilt=(0, 0, 0), light=2.0, frame='brass'):
    """Brass-hooded reading lamp: a dome shade over a glowing flame, hanging at c (c = centre of the flame)."""
    s = size
    up = v3(0, 1, 0)
    add(Ellipsoid(c + up * 0.075 * s, (0.075 * s, 0.050 * s, 0.075 * s)), frame, 0.0)
    add(Torus(c + up * 0.028 * s, up, 0.080 * s, 0.006 * s), frame, 0.0)
    add(Sphere(c + up * 0.126 * s, 0.014 * s), frame, 0.0)
    add(Ellipsoid(c, (0.040 * s, 0.040 * s, 0.040 * s)), 'lamp', 0.0)
    add(Capsule(c - up * 0.04 * s, c - up * 0.03 * s, 0.03 * s, 0.03 * s), frame, 0.0)
    flame(add, c - up * 0.005, P, size=1.3 * s)
    light_at(lights, P, c + v3(0, -0.04, 0.03), light * s, 0.22 * s)


__all__ = [n for n in dir() if not n.startswith('__')]

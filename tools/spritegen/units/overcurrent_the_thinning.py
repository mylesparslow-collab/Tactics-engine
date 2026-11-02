"""The Thinning (Overcurrent exotic big body). A ray so vast its shadow lands a turn before it does: a pale diamond of
wing swept toward the viewer, the whole belly a field of watching eyes of every size, a wall-wide mouth slot lined
with pearl plates under the nose, gill slits in gill red, a cyan-lit edge, a long thin tail trailing off.
Defining detail: the field of eyes on the belly. Tell: wings undulate, eyes blink in waves, cyan edge breathes."""
from _overcurrent_common import *

UNIT_ID = 'overcurrent_the_thinning'
CAMERA = Camera(ppm=44)
W, ZF, ZB = 1.18, 0.92, 0.78


def neutral_pose():
    return pose()


def _basis():
    fwd, right, up = Camera().basis()
    b = norm(v3(-0.50, -0.20, 0.80))
    return R_from(-b, -up + right * 0.25)


def ray_sdf(P, c):
    amp = 0.22 * np.sin(P['ph'])
    st = P['strike']

    def f(p):
        q = p - c
        x = np.abs(q[:, 0])
        z = q[:, 2]
        y = q[:, 1] - amp * x * (0.6 + 0.4 * np.sin(z * 2 + P['ph']))
        zn = np.where(z > 0, z / (ZF + 0.15 * st), -z / ZB)
        r = x / W + zn
        d2 = (r - 1.0) * 0.50
        rr = np.clip(r, 0, 1)
        th = 0.05 + 0.20 * (1 - rr ** 1.4) ** 1.2 * np.clip(1 - 0.5 * x / W, 0, 1)
        dy = np.abs(y) - th
        return smax(d2, dy, 0.10)
    return Func(f, c, 1.5)


def eyes_pattern(q, n):
    cell = 0.23
    ix = np.floor(q[:, 0] / cell); iz = np.floor(q[:, 2] / cell)
    h = lambda a, b, k: np.abs(np.sin(a * 12.9898 + b * 78.233 + k * 37.719) * 43758.5453) % 1.0
    has = h(ix, iz, 1) > 0.16
    cx = (ix + 0.30 + 0.4 * h(ix, iz, 2)) * cell
    cz = (iz + 0.30 + 0.4 * h(ix, iz, 3)) * cell
    rad = cell * (0.24 + 0.26 * h(ix, iz, 4))
    d = np.hypot(q[:, 0] - cx, q[:, 2] - cz)
    belly = (q[:, 1] < -0.02) & (np.abs(q[:, 0]) / W + np.where(q[:, 2] > 0, q[:, 2] / ZF, -q[:, 2] / ZB) < 0.86)
    m = has & belly & (d < rad)
    col = np.zeros((len(q), 3))
    col[:] = np.array(_hex('#f6e4ec'))
    iris = d < rad * 0.62
    col[iris] = np.array(_hex('#d04a66'))
    col[d < rad * 0.30] = np.array(_hex('#161a2a'))
    return m, col


def build(P):
    parts, add = new_parts()
    ph, st, op = P['ph'], P['strike'], P['open']
    c = v3(0, 0, 0)
    add(ray_sdf(P, c), 'skin', 0.0)
    add(Ellipsoid(v3(0, -0.10, 0.10), (0.62, 0.20, 0.58), None), 'skin', 0.25)
    # snout bump and the wall-wide mouth slot under it
    add(Ellipsoid(v3(0, 0.0, 0.70), (0.34, 0.15, 0.28), None), 'skin', 0.08)
    mw = 0.50
    add(Ellipsoid(v3(0, -0.13, 0.68), (mw, 0.05 + 0.08 * op, 0.09), None), 'throat', 0.0)
    for i in range(15):
        a = -1.0 + i * 0.143
        add(Sphere(v3(a * mw, -0.14, 0.76 - 0.1 * a * a), 0.030), 'tooth', 0.0)
        add(Sphere(v3(a * mw, -0.14 - 0.03 * op, 0.60 + 0.1 * a * a), 0.026), 'tooth', 0.0)
    # gill slits
    for sx in (-1, 1):
        for i in range(5):
            add(Ellipsoid(v3(sx * (0.26 + 0.05 * i), -0.20, 0.30 - 0.12 * i), (0.075, 0.018, 0.016), rot_y(sx * 0.5)), 'finred', 0.0)
        add(Sphere(v3(sx * 0.15, 0.07, 0.62), 0.035), 'eyeb', 0.0)
    # tail: long and thin, curling away
    tl = tube(add, [v3(0, -0.02, -0.65), v3(0.04, -0.03, -1.0), v3(0.20 + 0.1 * np.sin(ph), -0.04, -1.35), v3(0.45, -0.02, -1.55)],
              [0.11, 0.065, 0.035, 0.012], 'skin', n=10, k=0.03)
    add(Capsule(v3(0.0, -0.04, -0.95), v3(0.02, -0.14, -1.05), 0.02, 0.005), 'tooth', 0.0)
    R = _basis()
    pl = Placer(P, yaw=0.0, hover=1.12, R=R, scale=0.98, shift=0.10, back=0.1)
    organs = [Organ(pl.pt(v3(0, -0.02, 0.1)), (0.34, 0.1, 0.34), _hex('#e0a0b8'), 0.0, 0.35)]

    def glow_em(p, n):
        q = pl.inv(p)
        r = np.abs(q[:, 0]) / W + np.where(q[:, 2] > 0, q[:, 2] / ZF, -q[:, 2] / ZB)
        e = np.clip((r - 0.62) / 0.38, 0, 1) ** 1.3 * (0.55 + 0.35 * np.sin(2 * np.pi * P['tell']))
        belly = (q[:, 1] < 0.0)
        return np.array(CYAN)[None, :] * (e * belly * 0.9 * P['glow'])[:, None]
    sk = skin(top=tuple(np.array(CERU) * 0.7 + np.array(PEARL) * 0.1), under=tuple(np.array(PEARL) * 0.6 + np.array(CERU) * 0.35),
              organs=organs, veins=0.25, glow=0.8, spots=eyes_pattern, local=pl.inv, depth=0.4, spec=0.4, mottle=0.05)
    sk.emissive = glow_em
    mats = std_mats(P, {'skin': sk})
    lights = [under_light(P, v3(0, 0.2, 0.2), 1.1, 1.8)]

    def world(add2):
        spray(add2, P, v3(0, 1.0, 0.5), n=6)
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.4, 1.0, 0.0, 0.3), atk_strike=(0.0, 0.5, 1.0, 0.3), idle_amp=0.8)

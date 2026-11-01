"""Coralspire, the Mind of Coralspire (Reef Ascendant hero). The eldest colony: a vast fluted tower of
pink calcite that branches like a candelabrum into lesser spires, its oldest branches crumbling at the
tips. Drones cluster at its base, joined to it by fine synapse lines of light; light runs up the
grooves of the trunk. Motionless; the spires sway slightly."""
from _reef_ascendant_common import *
from render import Camera

UNIT_ID = 'reef_ascendant_coralspire'
CAMERA = Camera(ppm=44)
BRANCHES = [  # start height on trunk, angle, length, radius, outward bend
    (0.7, 0.3, 0.95, 0.13, 0.85), (0.9, 2.7, 0.9, 0.12, 0.9), (1.1, 4.3, 0.75, 0.1, 0.8),
    (1.3, 1.4, 0.6, 0.08, 0.7), (0.55, 5.5, 0.6, 0.09, 1.0), (1.45, 3.5, 0.45, 0.06, 0.6),
]
DRONES = [(0.62, 0.45, 0.3), (-0.62, 0.4, 0.9), (0.05, 0.78, 0.1)]


def neutral_pose():
    return base()


def groove_glow(P, n, twist, L, base_alb, k=1.0):
    """Synapse light running up the trunk grooves."""
    g = np.clip(k * (0.35 + 0.35 * P['glow'] + 1.0 * P['cast_glow']), 0, 1.6)
    ph = P['tell']

    def mask(p):
        t = np.clip(p[:, 1] / L, 0, 1)
        th = np.arctan2(p[:, 0], p[:, 2]) + twist * t
        groove = np.clip((-np.cos(n * th) - 0.82) * 8, 0, 1)
        travel = 0.5 + 0.5 * np.sin(p[:, 1] * 9.0 - 6.28 * ph)
        return groove * (0.4 + 0.6 * travel)

    def alb(p, nn):
        a = base_alb(p, nn)
        m = mask(p)[:, None]
        return a * (1 - m * 0.6) + np.array(GLOW)[None, :] * m * 0.6

    def em(p, nn):
        return np.array(GLOW)[None, :] * (mask(p) * g)[:, None]
    return Material(alb, spec=0.06, gloss=10, brush=0.07, emissive=em)


def mini_drone(add, c, yaw, P, i):
    R = rot_y(yaw) * 1.0
    c = c * 1.0
    add(ribbed(c + v3(0, 0.1, 0), (0.08, 0.06, 0.1), n=10, depth=0.01, R=R), 'calcite_b', 0)
    for j, (x, h) in enumerate(((-0.03, 0.14), (0.03, 0.17))):
        a = c + R @ v3(x, 0.12, -0.04)
        b = c + R @ v3(x * 1.4, 0.12 + h, -0.08) + v3(0, 0.01 * np.sin(6.28 * P['tell'] + i + j), 0)
        tube(add, a, b, 0.022, 'coral', open_=0.5, k=0.015)
    add(Sphere(c + R @ v3(0, 0.09, 0.1), 0.03), 'flesh', 0.02)
    for s in (-1, 1):
        for zz in (-0.05, 0.05):
            a = c + R @ v3(0.05 * s, 0.07, zz)
            add(Capsule(a, c + R @ v3(0.1 * s, 0.01, zz * 1.3), 0.01, 0.006), 'calcite_b', 0.006)


def build(P):
    parts, add = new_parts()
    rng = np.random.default_rng(51)
    st = P['strike']
    sw = wave(P, 0.0, strike=0.0)
    L = 2.05
    ground_root(add, v3(0, 0.05, 0), 9, 0.7, 0.06, 'calcite_b', rng, k=0.04)
    bx, bz = 0.015 * sw, 0.02 + 0.04 * st
    add(spire(v3(0, 0, 0), L, 0.32, 0.07, n=11, flute=0.22, twist=1.2, bulge=0.06, bulge_at=0.08,
              bend=(bx, bz)), 'trunk', 0.06)

    def on_trunk(y):
        t = y / L
        return v3(bx * L * t * t, y, bz * L * t * t), 0.32 + (0.07 - 0.32) * t
    for j, (y, ang, ln, r, ob) in enumerate(BRANCHES):
        c, tr = on_trunk(y)
        out = v3(np.cos(ang), 0, np.sin(ang))
        s = wave(P, j * 1.3, strike=0.0)
        start = c + out * tr * 0.4
        bend = (out[0] * ob + 0.03 * s, out[2] * ob + 0.03 * s * 0.5)
        add(spire(start, ln, r, r * 0.35, n=7, flute=0.25, twist=0.5, bend=bend), 'branch', 0.05)
        tip = start + v3(bend[0] * ln, ln, bend[1] * ln)
        # crumbling old tips: a broken calcite stub with chalk flecks
        add(Sphere(tip + v3(0, -0.01, 0), r * 0.45), 'calcite_b', 0.02)
    # lashing spire root on the attack (spire lash)
    a = v3(0.2, 0.06, 0.25)
    e = a + v3(0.05 * sw, 0.2 + 0.4 * st, 0.2 + 0.6 * st)
    chain(add, bez(a, a + v3(0.1, 0.35, 0.1), e, 5), 0.06, 0.012, 'coral', k=0.03)
    # drones at the base, joined by synapse lines
    for i, (x, z, yaw) in enumerate(DRONES):
        c = v3(x, 0.0, z)
        sub_parts, sub_add = new_parts()
        mini_drone(sub_add, v3(0, 0, 0), yaw, P, i)
        parts.extend(transform_parts(sub_parts, t=tuple(c), s=1.8))
        add(Capsule(v3(x * 0.35, 0.05, z * 0.35), c + v3(0, 0.12, 0), 0.006), 'synapse', 0.0)
    parts = body_pose(parts, P, lean_scale=0.25)
    m = reef_mats(P, glow=0.5)
    pink_calc = calcite_mat(flush=0.5, flush_col=_hex('#eea596'), low_col=_hex('#c79a86'))
    m['trunk'] = groove_glow(P, 11, 1.2, L, pink_calc.albedo)
    m['branch'] = calcite_mat(flush=0.6, flush_col=_hex('#eea596'))
    g = np.clip(0.5 + 0.4 * P['glow'] + 1.0 * P['cast_glow'], 0, 1.6)
    m['synapse'] = Material(GLOW, emissive=tuple(np.clip(np.array(GLOW) * g, 0, 1)), rim=0.0, brush=0.0)
    lights = [Light(v3(0, 0.6, 0.4), GLOW, 0.25 * g, 0.7)]
    return finish(P, FACTION, parts, m, lights=lights)


ROWS, frames = reef_rows(neutral_pose, sink=0.35, tilt=0.07)

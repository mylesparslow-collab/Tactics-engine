"""The Bleached (Reef Ascendant hero). A mind-coral that turned white in the sun and is starving: a great
brain-coral head on a cracked fluted trunk, bone-white and chalk-dead, antler branches arching out (some
snapped), a lens-eye gone milky, a ragged hunger-mouth in the trunk, and withered pale polyps hanging in
rags. Only a few cracks still pulse a thin, guttering pink. Defining detail: the white skeleton with its
last pink light running in the cracks. Tell: the cracks gutter, withered polyps twitch."""
from _reef_ascendant_common import *
from render import Camera

UNIT_ID = 'reef_ascendant_the_bleached'
CAMERA = Camera(ppm=44)
B_BONE = _hex('#f6efe4')
B_ASH = _hex('#cfc6b4')


def neutral_pose():
    return base()


def build(P):
    parts, add = new_parts()
    ph = 2 * np.pi * P['tell']
    st, op, tw = P['strike'], P['open'], P['twitch']
    w = lambda a: wave(P, a)
    rng = np.random.default_rng(21)
    # roots and buttresses spreading over the ground
    ground_root(add, v3(0, 0.15, 0), 8, 0.85, 0.075, 'bone', rng)
    add(Ellipsoid(v3(0, 0.16, 0), (0.50, 0.20, 0.46), None), 'bone_dk', 0.06)
    # trunk: fluted, bulging, leaning a little, with a hunger-mouth hollowed out of the front
    trunk = spire(v3(0, 0.05, 0), 1.0, 0.42, 0.33, n=7, flute=0.2, bulge=0.07, bulge_at=0.3, porous=0.012, bend=(0.03, 0.0))
    hollow = Ellipsoid(v3(0.05, 0.55, 0.40), (0.21 + 0.05 * op, 0.27 + 0.06 * op, 0.20), rot_y(0.2))
    add(Subtract(trunk, hollow, 0.03), 'bone', 0.04)
    add(Ellipsoid(v3(0.05, 0.55, 0.30), (0.17, 0.23, 0.10), rot_y(0.2)), 'maw', 0.0)
    # ragged "teeth" of broken calcite around the hunger-mouth
    for i in range(9):
        a = i / 8 * np.pi * 2
        c = v3(0.05, 0.55, 0.40) + rot_y(0.2) @ v3(np.cos(a) * 0.21, np.sin(a) * 0.27, 0.12)
        d = rot_y(0.2) @ v3(-np.cos(a) * 0.35, -np.sin(a) * 0.5, 0.7)
        add(Capsule(c, c + norm(d) * (0.07 + 0.03 * (i % 3)), 0.02, 0.004), 'bone', 0.0)
    # the brain: a huge cracked dome
    hc = v3(0.03, 1.42, 0.0)
    brn = brain(hc, (0.68, 0.40, 0.56), groove=0.04, freq=15.0)
    for a0, a1 in (((0.35, 1.9, 0.38), (0.10, 1.4, 0.55)), ((-0.1, 2.05, 0.4), (0.25, 1.52, 0.5)), ((0.52, 1.62, 0.0), (0.48, 1.35, 0.3))):
        pass
    cracks = [[(0.42, 1.68, 0.30), (0.34, 1.50, 0.38), (0.40, 1.32, 0.33), (0.28, 1.18, 0.42)],
              [(-0.10, 1.80, 0.30), (-0.02, 1.65, 0.38), (-0.12, 1.52, 0.44), (0.0, 1.32, 0.45)],
              [(0.60, 1.48, -0.05), (0.66, 1.30, 0.10), (0.58, 1.16, 0.2)]]
    cl = []
    for cr in cracks:
        for a, b in zip(cr[:-1], cr[1:]):
            g = Capsule(v3(*a), v3(*b), 0.014, 0.014)
            cl.append(g)
    crk = Union(cl, 0.0)
    add(Subtract(brn, crk, 0.01), 'bone_brain', 0.0)
    # the milky lens-eye set in the brain's face
    ec = v3(-0.10, 1.38, 0.54)
    add(Sphere(ec, 0.13), 'lens_dead', 0.04)
    add(Torus(ec + v3(0, 0, 0.06), v3(0, 0.1, 1), 0.10, 0.018), 'bone', 0.01)
    # antler branches: dead, bone white, a few snapped
    for i, (x, z, dx, dz, L) in enumerate([(0.18, -0.12, 0.9, -0.1, 0.55), (-0.2, -0.1, -0.9, 0.0, 0.5), (0.3, 0.1, 0.75, 0.65, 0.42), (-0.25, 0.1, -0.7, 0.7, 0.34)]):
        root = v3(x, 0.78 + 0.12 * i, z)
        d = norm(v3(dx, 0.55, dz) + v3(0.06 * w(i), 0.04 * w(i + 1), 0.0))
        branches(add, root, d, L, 0.065, 2 if i < 2 else 1, 'bone', rng, k=0.03, spread=0.6, kids=(2, 2), up_bias=0.45,
                 tip=(lambda a, e, dd, r: a(Capsule(e, e + dd * 0.05, r, r * 0.3), 'bone_dk', 0.0)))
    # antler on top of the brain
    branches(add, hc + v3(-0.25, 0.28, -0.05), (-0.5, 1, -0.2), 0.30, 0.055, 2, 'bone', rng, k=0.03, kids=(2, 2), up_bias=0.5)
    add(Capsule(hc + v3(0.3, 0.26, -0.1), hc + v3(0.4, 0.5, -0.12), 0.06, 0.04), 'bone', 0.03)
    # withered polyps hanging from the brain rim like rags
    for i in range(10):
        a = 2 * np.pi * i / 10 + 0.3
        rx, rz = np.cos(a) * 0.52, np.sin(a) * 0.46
        pts = []
        for j in range(5):
            h = j / 4
            sw = 0.05 * h * np.sin(ph + i * 1.1 - h * 2) + 0.04 * tw * h * (i % 2)
            pts.append(hc + v3(rx * (1 + 0.1 * h) + sw, -0.20 - 0.55 * h * (1 + 0.5 * (i % 3) / 2), rz * (1 + 0.1 * h)))
        chain(add, pts, 0.026, 0.006, 'wither', k=0.004)
        add(Sphere(pts[-1], 0.02), 'wither', 0.0)
    # a few desiccated drone husks at the foot
    for i, (x, z) in enumerate([(-0.55, 0.45), (0.5, 0.52), (-0.2, 0.7)]):
        add(Ellipsoid(v3(x, 0.09, z), (0.13, 0.08, 0.15), rot_y(i)), 'bone_dk', 0.03)
        add(Capsule(v3(x, 0.10, z), v3(x + 0.02, 0.30, z - 0.03), 0.025, 0.018), 'bone', 0.01)
    parts = body_pose(parts, P, lunge=0.1)
    parts = scaled(transform_parts(parts, R=rot_y(0.2), pivot=(0, 0, 0)), 1.0)
    m = reef_mats(P, glow=0.3)
    pulse = 0.25 + 0.2 * np.sin(ph) + 0.5 * P['glow'] * 0.4 + 0.7 * P['cast_glow']

    def bone_alb(p, n):
        f = fbm(p, 9.0, 3)[:, None]
        a = np.array(B_BONE)[None, :] * (0.9 + 0.15 * f) + 0 * p
        crack = (np.abs(vnoise(p, 6.0) - 0.5) < 0.018) | (np.abs(vnoise(p + 4.4, 12.0) - 0.5) < 0.012)
        a = np.where(crack[:, None], np.array(B_ASH)[None, :] * 0.55, a)
        low = np.clip(0.5 - p[:, 1], 0, 0.5)[:, None] / 0.5
        a = a * (1 - low * 0.25) + np.array(B_ASH)[None, :] * low * 0.25
        return a

    def bone_em(p, n):
        c = (np.abs(vnoise(p, 6.0) - 0.5) < 0.018)
        return np.array(GLOW)[None, :] * (c * pulse * 0.5)[:, None]
    m['bone'] = Material(bone_alb, spec=0.05, gloss=10, brush=0.08, emissive=bone_em)
    m['bone_dk'] = Material(lambda p, n: bone_alb(p, n) * np.array([0.82, 0.78, 0.74])[None, :], spec=0.04, gloss=10, brush=0.08)

    def brain_alb(p, n):
        a = bone_alb(p, n)
        gr = np.abs(vnoise(p, 16.0) - 0.5) < 0.05
        return np.where(gr[:, None], a * np.array([0.72, 0.68, 0.7])[None, :], a)
    m['bone_brain'] = Material(brain_alb, spec=0.05, gloss=10, brush=0.08, emissive=bone_em)
    m['wither'] = Material(_hex('#dcd2bf'), spec=0.1, gloss=14, sss=0.3, brush=0.04)
    m['maw'] = Material(_hex('#3a1c22'), emissive=tuple(np.array(GLOW) * 0.12 * (1 + P['open'])), rim=0.0)
    m['lens_dead'] = Material(_hex('#cfe2de'), spec=0.9, gloss=60, emissive=tuple(np.array(LENS) * (0.18 + 0.22 * pulse + 0.4 * P['fx'])), rim=0.5, brush=0.0)
    lights = [Light(v3(0.0, 1.0, 0.5), GLOW, 0.25 * pulse * (1 - P['end']), 1.4)]
    return finish(P, FACTION, parts, m, lights)


ROWS, frames = reef_rows(neutral_pose, sink=0.35, tilt=0.06)

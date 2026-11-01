"""Glasswake, the Lensmind of the Glass Shallows (Reef Ascendant hero). A young colony grown in clear
stone: a coral foot pushing up a cluster of glass-calcite crystal spires and three round lenses that
bend sunlight into sight. Light gathers in the lenses; a glass spike fires on the hit frame."""
from _reef_ascendant_common import *
from kit.xform import Xform
from render import Camera

UNIT_ID = 'reef_ascendant_glasswake'
CAMERA = Camera(ppm=48)
CRYS = [  # (x, z, length, radius, tilt_x, tilt_z)
    (0.0, -0.05, 1.35, 0.12, 0.05, 0.0), (-0.2, 0.0, 0.95, 0.09, 0.15, 0.35), (0.22, -0.08, 1.05, 0.1, -0.05, -0.35),
    (-0.08, -0.25, 1.1, 0.085, -0.3, 0.15), (0.14, -0.28, 0.8, 0.075, -0.35, -0.25), (-0.32, -0.15, 0.6, 0.065, -0.1, 0.6),
    (0.34, 0.12, 0.55, 0.06, 0.25, -0.6),
]
LENSES = [(0.0, 0.95, 0.16, 0.13), (-0.22, 0.6, 0.18, 0.09), (0.24, 0.72, 0.12, 0.08)]


def neutral_pose():
    return base()


def build(P):
    parts, add = new_parts()
    rng = np.random.default_rng(71)
    st = P['strike']
    ground_root(add, v3(0, 0.04, 0), 7, 0.45, 0.04, 'coral', rng)
    add(ribbed(v3(0, 0.16, -0.05), (0.32, 0.18, 0.28), n=16, depth=0.02, R=rot_x(np.pi / 2)), 'calcite_p', 0)
    for j, (x, z, L, r, tx, tz) in enumerate(CRYS):
        s = wave(P, j * 1.1, strike=0.0)
        R = rot_z(tz + 0.03 * s) @ rot_x(tx + 0.02 * s)
        base_pt = v3(x, 0.1, z)
        pr = spire(base_pt, L, r, 0.005, n=6, flute=0.08, top_round=0.0)
        add(Xform(pr, R=R, pivot=base_pt), 'glass', 0.0)
        # coral collar where each crystal grows out
        add(Torus(base_pt + R @ v3(0, 0.08, 0), R @ v3(0, 1, 0), r * 1.05, 0.03), 'coral', 0.03)
    for i, (x, y, z, r) in enumerate(LENSES):
        c = v3(x, y, z + 0.05)
        Rl = rot_y(-0.35 + 0.1 * np.sin(6.28 * P['tell'] + i)) @ rot_x(np.pi / 2 - 0.25 - 0.3 * st)
        add(Torus(c, Rl @ v3(0, 1, 0), r * 1.02, 0.022), 'coral', 0.0)
        add(Ellipsoid(c, (r, 0.03, r), Rl), 'lens', 0.0)
    if P['fx'] > 0.5 or st > 0.35:
        d = norm(v3(-0.2, -0.15, 1.0))
        a = v3(0.0, 0.95, 0.25) + d * (0.1 + 0.6 * st)
        add(Capsule(a, a + d * 0.3, 0.035, 0.004), 'glass', 0.0)
    parts = body_pose(parts, P, lean_scale=0.4, lunge=0.05)
    m = reef_mats(P, glow=0.4)
    m['glass'] = glass_mat(P)
    m['lens'] = lens_mat(P)
    g = 0.5 + 0.4 * P['glow'] + 1.2 * P['cast_glow'] + 1.2 * P['fx']
    lights = [Light(v3(0, 0.9, 0.35), LENS, 0.3 * g, 0.6)]
    return finish(P, FACTION, parts, m, lights=lights)


ROWS, frames = reef_rows(neutral_pose, sink=0.25, tilt=0.08)

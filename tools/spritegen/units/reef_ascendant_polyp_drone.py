"""Polyp Drone (Reef Ascendant, cheap body). Knee-high scuttling bundle of fused calcite tubes,
two small clawed fans, six spine legs. Defining detail: one soft pink mouth that gapes as it lunges."""
from _reef_ascendant_common import *

UNIT_ID = 'reef_ascendant_polyp_drone'


def neutral_pose():
    return base()


def build(P):
    parts, add = new_parts()
    rng = np.random.default_rng(11)
    op = P['open']
    w0 = wave(P, 0.0)
    w1 = wave(P, 1.7)
    # body: squat calcite shell, slightly nose-down toward the front
    by = 0.17
    add(ribbed(v3(0, by, -0.01), (0.12, 0.09, 0.145), n=14, depth=0.014), 'calcite_b', 0)
    # fused tubes on the back, raked backward like a bundle
    tubes = [(-0.06, -0.06, 0.25, -0.25, 0.034), (0.05, -0.07, 0.26, 0.2, 0.032), (0.0, -0.1, 0.32, 0.0, 0.038),
             (-0.08, 0.0, 0.21, -0.5, 0.028), (0.08, 0.0, 0.2, 0.5, 0.027)]
    for i, (x, z, top, lean_x, r) in enumerate(tubes):
        a = v3(x, by, z)
        sw = 0.012 * wave(P, i * 1.3) + 0.03 * P['twitch'] * (i == 2)
        b = v3(x + lean_x * 0.06 + sw, top + 0.02 * P['twitch'] * (i == 2), z - 0.06)
        tube(add, a, b, r, 'coral' if i % 2 else 'calcite_p', open_=0.5, k=0.02)
        # polyp flower in the tube mouth
        d = norm(b - a)
        add(Sphere(b + d * 0.006 * (1 + P['twitch']), r * 0.45), 'flesh', 0.0)
    # mouth: soft pink lip at the front that gapes with P['open']
    mz = 0.13 + 0.03 * op
    my = by - 0.005
    lip_R = 0.05 + 0.018 * op
    add(Ellipsoid(v3(0, my, mz - 0.03), (0.07, 0.06 + 0.012 * op, 0.04)), 'flesh', 0.03)
    add(Torus(v3(0, my, mz + 0.0), v3(0, 0.15, 1), lip_R * 0.75, 0.016), 'flesh', 0.01)
    # ring of short feeding tentacles around the mouth, flaring as it opens
    add(crown(v3(0, my, mz - 0.005), 9, lip_R * 0.8, 0.03 + 0.03 * op, 0.035 + 0.02 * op, 0.009, 0.004,
              sway=lambda i: (0.0, 0.008 * np.sin(i * 2.1 + 6.28 * P['tell']), 0.006 * np.sin(i)),
              curl=-0.01, R=rot_x(np.pi / 2 - 0.15)), 'flesh', 0.006)
    add(Ellipsoid(v3(0, my, mz + 0.012), (lip_R * 0.62, lip_R * (0.25 + 0.5 * op) + 0.008, 0.02)), 'mouth', 0)
    # clawed fans on the shoulders
    for s in (-1, 1):
        piv = v3(0.085 * s, by + 0.03, 0.06)
        ang = 0.35 + 0.25 * w0 * s * 0.5 + 0.4 * P['strike']
        R = rot_y(s * 0.5) @ rot_z(-s * (0.9 - 0.2 * w1)) @ rot_x(ang)
        add(fan(piv, R, 0.11, 0.55, ribs=5, thick=0.007, scallop=0.25), 'coral', 0.0)
        add(Capsule(piv, piv + R @ v3(0, 0.1, 0), 0.008, 0.004), 'calcite_b', 0.004)
    legs(add, P, v3(0, 0.12, -0.0), 0.10, 0.11, n=6, h=0.09, r=0.014, mat='calcite_b')
    parts = scaled(body_pose(parts, P, pivot=(0, 0.0, 0), lunge=0.07), 1.3)
    return finish(P, FACTION, parts, reef_mats(P, glow=0.3))


ROWS, frames = reef_rows(neutral_pose, sink=0.05)

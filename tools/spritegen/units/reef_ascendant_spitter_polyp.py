"""Spitter Polyp (Reef Ascendant, ranged skirmisher). A bulbous slurry sac on spine legs with one long
fluted spitting tube arched over its back. Defining detail: the flared muzzle that lobs a glob of
caustic calcite slurry (fx on the hit frame)."""
from _reef_ascendant_common import *

UNIT_ID = 'reef_ascendant_spitter_polyp'


def neutral_pose():
    return base()


def build(P):
    parts, add = new_parts()
    op, st = P['open'], P['strike']
    sw = wave(P, 0.4, strike=0.0)
    by = 0.2
    # slurry sac: ribbed shell behind, translucent pink sac swelling on the belly
    add(ribbed(v3(0, by + 0.02, -0.04), (0.13, 0.11, 0.15), n=12, depth=0.016, R=rot_x(-0.25)), 'calcite_b', 0)
    add(Ellipsoid(v3(0, by - 0.02, 0.02), (0.11 + 0.01 * op, 0.09, 0.11)), 'flesh', 0.04)
    # neck: rises from the back and arches forward; recoils on the windup, snaps forward on the spit
    back = [-0.05, -0.02, 0.06, 0.0][0] if False else 0.0
    pull = -0.08 * (P['lean'] < 0) * abs(P['lean']) * 4 + 0.06 * st
    a = v3(0, by + 0.08, -0.08)
    b = v3(0.02 * sw, 0.62 + 0.03 * sw, -0.12 + pull * 0.5)
    c = v3(0.03 * sw, 0.58 - 0.08 * st, 0.12 + pull)
    pts = bez(a, b, c, n=6)
    chain(add, pts, 0.055, 0.04, 'coral', k=0.02, first_k=0.05)
    # neck ridges (calcite rings)
    for i in (2, 3, 4):
        d = norm(pts[i + 1] - pts[i - 1])
        add(Torus(pts[i], d, 0.05 - 0.003 * i, 0.011), 'calcite_b', 0.01)
    # muzzle: a flared trumpet with a fringe of short fronds
    d = norm(pts[-1] - pts[-2])
    m = pts[-1] + d * 0.03
    add(Capsule(pts[-1], m, 0.042, 0.055 + 0.012 * op), 'calcite_p', 0.015)
    add(Sphere(m + d * 0.012, 0.035 + 0.01 * op), 'mouth', 0)
    add(crown(m, 10, 0.05, 0.035 + 0.02 * op, 0.025, 0.009, 0.004, R=basis_from(d),
              sway=lambda i: (0.0, 0.006 * np.sin(i * 1.9 + 6.28 * P['tell']), 0.0), curl=0.01), 'flesh', 0.008)
    if P['fx'] > 0:
        g = m + d * (0.09 + 0.12 * P['fx'])
        add(Sphere(g, 0.045 * P['fx']), 'slurry', 0)
        add(Sphere(g - d * 0.06, 0.025 * P['fx']), 'slurry', 0.02)
    legs(add, P, v3(0, 0.15, 0.0), 0.11, 0.12, n=6, h=0.10, r=0.015, mat='calcite_b')
    parts = scaled(body_pose(parts, P, lunge=0.0), 1.15)
    m = reef_mats(P, glow=0.3)
    m['slurry'] = Material(_hex('#efe6d6'), spec=0.4, gloss=20, emissive=tuple(np.array(GLOW) * 0.45), brush=0.02)
    return finish(P, FACTION, parts, m)


ROWS, frames = reef_rows(neutral_pose, sink=0.05)

"""Lensbearer (Reef Ascendant, ranged artillery). A colony grown around a lens of clear calcite: a thicket
of short branching coral at the foot, one tall fluted stalk curving up to a coral cradle that holds a
great glass lens turned to the sky. Defining detail: the cyan light gathering in the lens; it tips
toward the target and fires a beam on the hit frame."""
from _reef_ascendant_common import *
from kit.xform import Xform
from render import Camera

UNIT_ID = 'reef_ascendant_lensbearer'
CAMERA = Camera(ppm=46)


def neutral_pose():
    return base()


def build(P):
    parts, add = new_parts()
    rng = np.random.default_rng(31)
    sw = wave(P, 0.0, strike=0.0)
    st = P['strike']
    # foot thicket: short branching coral around the base
    ground_root(add, v3(0, 0.04, 0), 7, 0.4, 0.04, 'calcite_b', rng)
    for i, ang in enumerate((0.5, 2.0, 3.4, 4.9)):
        r0 = v3(np.cos(ang) * 0.16, 0.0, np.sin(ang) * 0.14)
        branches(add, r0, (np.cos(ang) * 0.4, 1.0, np.sin(ang) * 0.4), 0.22, 0.045, 2, 'coral', rng,
                 k=0.02, spread=0.6, sway=(0.02 * wave(P, i), 0), kids=(2, 2), up_bias=0.4)
    # lesser spires of the colony grown up around the stalk
    for j, (x, z, h, r) in enumerate([(-0.2, 0.1, 0.75, 0.08), (0.2, -0.12, 0.6, 0.07), (0.06, 0.22, 0.45, 0.06)]):
        s = wave(P, j * 1.9, strike=0.0)
        add(spire(v3(x, 0, z), h, r, r * 0.3, n=7, flute=0.25, twist=0.6,
                  bend=(np.sign(x) * 0.2 + 0.03 * s, np.sign(z) * 0.1)), 'calcite_p', 0.04)
        tip = v3(x + (np.sign(x) * 0.2 + 0.03 * s) * h, h, z + np.sign(z) * 0.1 * h)
        add(crown(tip - v3(0, 0.02, 0), 6, r * 0.25, 0.05, 0.06, 0.01, 0.004, curl=0.02,
                  sway=lambda i, j=j: (0.0, 0.012 * np.sin(i * 1.7 + j + 6.28 * P['tell']) + 0.015 * P['twitch'] * (i % 2), 0.0)),
            'flesh', 0.008)
    # main stalk: fluted, curving forward at the top
    L = 1.55
    bx, bz = 0.02 * sw, 0.10 + 0.06 * st
    add(spire(v3(0, 0, -0.05), L, 0.2, 0.09, n=9, flute=0.2, twist=0.8, bulge=0.03, bulge_at=0.1,
              bend=(bx, bz)), 'stalk', 0.05)
    top = v3(bx * L, L, -0.05 + bz * L)
    # cradle: a ring of coral fingers around the lens; lens tips toward the target on the attack
    tilt = 0.55 - 0.15 * np.sin(2 * np.pi * P['tell']) * 0.2 + 0.55 * st
    Rl = rot_x(-(np.pi / 2) + tilt) @ rot_z(0.05 * sw)          # local y = lens axis
    ax = Rl @ v3(0, 1, 0)
    lc = top + v3(0, 0.1, 0) + ax * 0.05
    add(Torus(lc, ax, 0.27, 0.04), 'coral', 0.0)
    add(Capsule(top - v3(0, 0.04, 0), lc - ax * 0.05, 0.08, 0.06), 'coral', 0.04)
    for i in range(7):
        a = i * 2 * np.pi / 7 + 0.2
        u = Rl @ v3(np.cos(a), 0, np.sin(a))
        p0 = lc + u * 0.26 - ax * 0.02
        add(Capsule(p0, p0 + u * 0.06 + ax * (0.1 + 0.02 * np.sin(i * 2 + 6.28 * P['tell'])), 0.022, 0.007), 'calcite_b', 0.01)
    add(Ellipsoid(lc, (0.25, 0.055, 0.25), Rl), 'lens', 0.0)
    # beam on the hit frame
    if P['fx'] > 0.5:
        d = norm(ax * 0.3 + v3(0, -0.35, 1.0))
        add(Capsule(lc + d * 0.1, lc + d * 1.1, 0.05, 0.02), 'beam', 0.0)
    parts = body_pose(parts, P, lean_scale=0.4)
    m = reef_mats(P, glow=0.3)
    m['stalk'] = calcite_mat(flush=0.35, low_col=_hex('#c79a86'))
    m['lens'] = lens_mat(P)
    m['beam'] = Material(LENS, emissive=tuple(np.array(_hex('#d8fbf8')) * 1.0), rim=0.0, brush=0.0)
    g = 0.5 + 0.4 * P['glow'] + 1.2 * P['cast_glow'] + 1.5 * P['fx']
    lights = [Light(lc + v3(0, 0.05, 0.1), LENS, 0.35 * g, 0.55)]
    return finish(P, FACTION, parts, m, lights=lights)


ROWS, frames = reef_rows(neutral_pose, sink=0.3, tilt=0.15)

"""Mantis Striker (Reef Ascendant, burst). A living-calcite mantis shrimp: segmented ribbed tail ending in a
fan, a carapace with cyan lens-eyes on stalks, and two folded raptorial arms ending in huge pink clubs that
smash on the hit frame. Defining detail: the oversized clubs. Tell: the clubs twitch, antennae flick."""
from _reef_ascendant_common import *

UNIT_ID = 'reef_ascendant_mantis_striker'
YAW = -0.3
TAILPITCH = -0.9


def neutral_pose():
    return base()


def build(P):
    parts, add = new_parts()
    st = P['strike']
    tw = P['twitch']
    w = lambda ph: wave(P, ph)
    by = 0.30
    # abdomen: six overlapping ribbed segments arching back and down, then the tail fan
    for i in range(6):
        z = -0.10 - 0.105 * i
        y = by + 0.03 + 0.032 * i ** 1.45 + 0.01 * w(i * 0.7)
        rx, ry = 0.175 - 0.017 * i, 0.125 - 0.012 * i
        add(Ellipsoid(v3(0, y, z), (rx, ry, 0.095), None), 'coral' if i % 2 else 'calcite_p', 0.012)
        add(Ellipsoid(v3(0, y, z + 0.052), (rx * 1.0, ry * 1.0, 0.016), None), 'reefred', 0.0)
        add(Capsule(v3(0, y + ry * 0.8, z - 0.03), v3(0, y + ry * 1.25, z + 0.04), 0.012, 0.004), 'coral', 0.0)   # dorsal spine
        for s in (-1, 1):   # swimmerets
            add(Capsule(v3(s * rx * 0.8, y - ry * 0.6, z), v3(s * (rx + 0.06), y - ry - 0.06, z - 0.03), 0.014, 0.006), 'flesh', 0.008)
    ty = by + 0.03 + 0.032 * 5.8 ** 1.45 - 0.02
    tz = -0.10 - 0.105 * 6
    for s, ang in ((-1, 0.55), (1, -0.55), (0, 0.0)):
        R = rot_y(-ang) @ rot_x(TAILPITCH) @ np.stack([v3(1, 0, 0), v3(0, 0, -1), v3(0, 1, 0)], 1)
        add(fan(v3(0, ty + 0.01, tz + 0.05), R, 0.22 if s else 0.26, 0.42, ribs=5, thick=0.012, scallop=0.15), 'coral' if s else 'calcite_p', 0.0)
    # carapace
    add(ribbed(v3(0, by + 0.03, 0.12), (0.20, 0.16, 0.24), n=10, depth=0.018, R=None), 'coral', 0.02)
    add(Ellipsoid(v3(0, by + 0.01, 0.34), (0.15, 0.12, 0.12), None), 'calcite_p', 0.03)
    add(Capsule(v3(0, by + 0.14, 0.30), v3(0, by + 0.19, 0.44), 0.02, 0.006), 'coral', 0.0)               # rostrum
    # lens-eyes on stalks
    for s in (-1, 1):
        a, b = v3(s * 0.08, by + 0.10, 0.40), v3(s * 0.16, by + 0.22, 0.46)
        add(Capsule(a, b, 0.032, 0.026), 'flesh', 0.01)
        add(Sphere(b + v3(0, 0.02, 0.01), 0.075), 'lens', 0.01)
        add(Sphere(b + v3(s * 0.01, 0.025, 0.05), 0.022), 'mouth', 0.0)
    # antennae
    for s in (-1, 1):
        pts = [v3(s * 0.05, by + 0.07, 0.44), v3(s * 0.12, by + 0.16, 0.62), v3(s * 0.22 + 0.03 * w(s + 1), by + 0.10, 0.84), v3(s * 0.34 + 0.05 * w(s), by - 0.02 + 0.03 * tw, 1.0)]
        chain(add, pts, 0.012, 0.004, 'coral', k=0.004)
        add(Ellipsoid(v3(s * 0.11, by + 0.04, 0.5), (0.012, 0.03, 0.10), None), 'flesh', 0.01)          # antennal scale
    add(Ellipsoid(v3(0, by - 0.07, 0.40), (0.07, 0.05, 0.07), None), 'mouth', 0.02)
    # raptorial arms with club
    for s in (-1, 1):
        sh = v3(s * 0.16, by - 0.02, 0.28)
        el = v3(s * (0.40 - 0.18 * st), by + 0.14 - 0.05 * st, 0.42 + 0.22 * st)
        # strike: forearm swings from folded (back toward body, club cocked high) to out and down
        wr_rest = v3(s * 0.36, by + 0.04, 0.66)
        wr_hit = v3(s * 0.14, by - 0.12, 0.96)
        wr = wr_rest + (wr_hit - wr_rest) * st + v3(0, 0.03 * tw * (s > 0), 0)
        d = norm(wr - el) if np.linalg.norm(wr - el) > 1e-3 else v3(0, 0, 1)
        add(Capsule(sh, el, 0.05, 0.042), 'calcite_p', 0.02)
        add(Capsule(el, wr, 0.042, 0.036), 'calcite_b', 0.02)
        for j in range(4):   # raptorial spines
            q = el + (wr - el) * (0.2 + 0.2 * j)
            add(Capsule(q, q + v3(s * 0.04, -0.05, 0.03), 0.012, 0.003), 'coral', 0.0)
        cd = norm(d + v3(0, -0.5 * (1 - st), 0.3 * (1 - st)))
        club = wr + cd * 0.12
        add(Capsule(wr, wr + cd * 0.12, 0.05, 0.07), 'calcite_b', 0.03)
        add(Ellipsoid(wr + cd * 0.2, (0.105, 0.14, 0.105), basis_from(cd)), 'club', 0.03)
        add(Sphere(wr + cd * 0.31, 0.06), 'reefred', 0.02)
        add(Capsule(wr + cd * 0.1 + v3(0, 0.07, 0), wr + cd * 0.26 + v3(0, 0.11, 0), 0.02, 0.01), 'calcite_b', 0.01)
    # walking legs
    legs(add, P, v3(0, 0.20, 0.10), 0.15, 0.20, n=8, h=0.10, r=0.020, mat='coral_dk', reach=0.07)
    parts = transform_parts(parts, t=(0, 0, -0.55))
    parts = body_pose(parts, P, lunge=0.18)
    parts = transform_parts(parts, R=rot_y(YAW), t=(0.0, 0.0, 0.0), pivot=(0, 0, 0))
    parts = scaled(parts, 1.0)
    m = reef_mats(P, glow=0.4)
    m['lens'] = lens_mat(P)
    m['club'] = coral_mat(deep=0.5, base_col=_hex('#f0988a'), deep_col=RED)
    return finish(P, FACTION, parts, m)


ROWS, frames = reef_rows(neutral_pose, sink=0.05)

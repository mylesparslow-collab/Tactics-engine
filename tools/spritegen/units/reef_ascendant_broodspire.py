"""Broodspire (Reef Ascendant, spawner). A tall spiral-fluted cone of coral that buds fresh drones:
swollen polyp buds with pink mouths stud its flanks. Buds swell on the cast (spawn brood); spines
jet from the front bud on the attack."""
from _reef_ascendant_common import *

UNIT_ID = 'reef_ascendant_broodspire'
BUDS = [(0.9, 0.38, 0.13), (2.3, 0.6, 0.11), (4.2, 0.32, 0.12), (1.5, 0.95, 0.09), (3.3, 1.1, 0.075),
        (5.4, 0.75, 0.095), (0.4, 1.32, 0.065), (-0.2, 0.62, 0.1)]


def neutral_pose():
    return base()


def build(P):
    parts, add = new_parts()
    rng = np.random.default_rng(5)
    sw = wave(P, 0.0, strike=0.0)
    op = P['open']
    L = 1.85

    def R_at(y):
        return 0.36 * (1 - y / L) ** 0.9 + 0.02
    bx = 0.02 * sw
    ground_root(add, v3(0, 0.04, 0), 7, 0.42, 0.04, 'calcite_b', rng)
    add(spire(v3(0, 0, 0), L, 0.38, 0.02, n=9, flute=0.28, twist=5.5, bend=(bx, 0.0)), 'coral', 0.04)
    # calcite growth rings
    # chalky calcite crust patches low on the spire (old growth), not rings
    for j in range(7):
        ang = j * 0.9 + 0.4
        y = 0.12 + 0.11 * j
        add(Ellipsoid(v3(np.cos(ang) * R_at(y) * 0.85, y, np.sin(ang) * R_at(y) * 0.85), (0.11, 0.07, 0.11)),
            'calcite_b', 0.05)
    # budding drones
    for i, (ang, y, r) in enumerate(BUDS):
        s = 1.0 + 0.35 * P['cast_glow'] + 0.1 * P['twitch'] * (i % 2)
        rr = r * s
        rad = R_at(y) * 0.9
        c = v3(np.cos(ang) * (rad + rr * 0.5) + bx * L * (y / L) ** 2, y, np.sin(ang) * (rad + rr * 0.5))
        out = norm(v3(np.cos(ang), 0.5, np.sin(ang)))
        add(ribbed(c, (rr, rr * 1.15, rr), n=8, depth=rr * 0.12, R=basis_from(out)), 'calcite_p', 0.03)
        add(Torus(c + out * rr * 1.0, out, rr * 0.38, rr * 0.16), 'flesh', 0.01)
        add(Sphere(c + out * rr * 1.0, rr * (0.25 + 0.15 * op)), 'mouth', 0)
    # spine jet from the front bud
    if P['fx'] > 0 or P['strike'] > 0.3:
        ang, y, r = BUDS[0]
        c0 = v3(np.cos(ang) * (R_at(y) + r), y, np.sin(ang) * (R_at(y) + r))
        for j in range(3):
            d = norm(v3(np.cos(ang) * 0.6 + 0.1 * (j - 1), 0.15 + 0.08 * j, 1.0))
            a = c0 + d * (0.02 + 0.2 * P['strike'])
            add(Capsule(a, a + d * 0.26, 0.022, 0.004), 'calcite_b', 0)
    # crown tip
    tip = v3(bx * L, L, 0)
    add(crown(tip + v3(0, -0.05, 0), 7, 0.02, 0.08, 0.1, 0.012, 0.005, curl=0.03,
              sway=lambda i: (0, 0.02 * np.sin(i * 2 + 6.28 * P['tell']), 0.01 * np.sin(i))), 'flesh', 0.01)
    parts = body_pose(parts, P, lean_scale=0.4)
    m = reef_mats(P, glow=0.4)
    m['coral'] = pore_glow_mat(P, coral_mat().albedo, freq=40.0, thresh=0.8, k=0.6)
    return finish(P, FACTION, parts, m)


ROWS, frames = reef_rows(neutral_pose, sink=0.3, tilt=0.15)

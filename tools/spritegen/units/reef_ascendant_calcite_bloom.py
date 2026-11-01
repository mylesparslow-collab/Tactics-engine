"""Calcite Bloom (Reef Ascendant, terrain spreader). A flower the size of a house: a thick fluted stalk
on spreading root runners that turn rock to reef, carrying a great cup of fluted calcite petals around
a glowing stamen crown. Petals open wide on the cast (spread reef); a thorn whip lashes on the attack."""
from _reef_ascendant_common import *
from render import Camera

UNIT_ID = 'reef_ascendant_calcite_bloom'
CAMERA = Camera(ppm=46)


def neutral_pose():
    return base()


def build(P):
    parts, add = new_parts()
    rng = np.random.default_rng(17)
    sw = wave(P, 0.0, strike=0.0)
    op = 0.35 + 0.5 * P['cast_glow'] + 0.15 * P['open']
    st = P['strike']
    # root runners and a living-reef skirt at the foot
    ground_root(add, v3(0, 0.05, 0), 9, 0.62, 0.045, 'coral', rng, k=0.03)
    for i in range(6):
        ang = i * 1.05 + 0.3
        add(Sphere(v3(np.cos(ang) * 0.32, 0.0, np.sin(ang) * 0.28), 0.06), 'calcite_b', 0.04)
    L = 1.05
    bx = 0.04 * sw
    add(spire(v3(0, 0, 0), L, 0.17, 0.11, n=9, flute=0.2, twist=1.2, bulge=0.04, bulge_at=0.1,
              bend=(bx, 0.03)), 'stalk', 0.05)
    # thorn leaves on the stalk
    for i, (y, ang) in enumerate([(0.35, 0.8), (0.6, 3.6), (0.8, 5.5)]):
        a = v3(np.cos(ang) * 0.12 + bx * (y / L) ** 2 * L, y, np.sin(ang) * 0.12)
        d = norm(v3(np.cos(ang), 0.7, np.sin(ang)))
        add(Capsule(a, a + d * 0.22, 0.035, 0.006), 'coral', 0.03)
    top = v3(bx * L, L, 0.03 * L)
    # calyx
    add(Ellipsoid(top + v3(0, 0.05, 0), (0.2, 0.1, 0.2)), 'coral_dk', 0.05)
    # petals: two rings of cupped fluted calcite blades
    for ring, (n, ln, wd, tilt0, mat, ph0) in enumerate([(9, 0.55, 0.17, 0.55, 'petal', 0.0),
                                                        (7, 0.42, 0.13, 0.25, 'petal2', 0.35)]):
        for i in range(n):
            ang = ph0 + i * 2 * np.pi / n
            tilt = tilt0 + 0.7 * op + 0.05 * np.sin(2 * np.pi * P['tell'] + i)
            out = v3(np.cos(ang), 0, np.sin(ang))
            d = norm(out * np.sin(tilt) + v3(0, np.cos(tilt), 0))
            c = top + v3(0, 0.08, 0) + out * 0.09 + d * ln * 0.5
            side = norm(np.cross(d, out))
            nrm = np.cross(side, d)
            R = np.stack([side, d, nrm], axis=1)
            add(ribbed(c, (wd, ln * 0.5, 0.035), n=6, depth=0.01, R=R @ rot_x(np.pi / 2) @ rot_x(-np.pi / 2)), mat, 0.0)
    # stamen crown with glowing beads
    sc = top + v3(0, 0.13, 0)
    add(crown(sc, 11, 0.02, 0.07, 0.22, 0.012, 0.006, curl=0.02,
              sway=lambda i: (0.02 * np.sin(i + 6.28 * P['tell']), 0.0, 0.02 * np.cos(i * 1.7))), 'flesh', 0.01)
    for i in range(11):
        ang = i * 2 * np.pi / 11
        add(Sphere(sc + v3(np.cos(ang) * 0.09, 0.235, np.sin(ang) * 0.09), 0.018), 'glow', 0.0)
    # thorn whip: a runner that rears and lashes forward on the attack
    a = v3(0.25, 0.04, 0.2)
    m_ = a + v3(0.05, 0.25 + 0.3 * st, 0.15 + 0.2 * st)
    e = a + v3(-0.05 + 0.03 * sw, 0.15 + 0.2 * st, 0.15 + 0.65 * st)
    chain(add, bez(a, m_, e, 5), 0.035, 0.008, 'coral', k=0.015)
    parts = body_pose(parts, P, lean_scale=0.4)
    m = reef_mats(P, glow=0.5)
    m['stalk'] = calcite_mat(flush=0.3, low_col=_hex('#c79a86'))
    m['petal'] = calcite_mat(flush=0.55, flush_col=_hex('#f0a493'), pores=False, brush=0.05)
    m['petal2'] = calcite_mat(flush=0.7, flush_col=CORAL, pores=False, brush=0.05)
    lights = [Light(sc + v3(0, 0.2, 0), GLOW, 0.3 * (P['glow'] + P['cast_glow']), 0.6)]
    return finish(P, FACTION, parts, m, lights=lights)


ROWS, frames = reef_rows(neutral_pose, sink=0.25, tilt=0.12)

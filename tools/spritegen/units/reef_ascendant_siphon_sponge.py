"""Siphon Sponge (Reef Ascendant, drain). A pulsing mound of three fused barrel-sponges: a tall central barrel
with a dark open mouth, flanking barrels, osculum holes pocking every wall and root-runners over the ground.
Defining detail: the oscula, which breathe pink light as it filters. Tell: the whole mound swells and sags,
and filaments reach out from the mouths on the attack."""
from _reef_ascendant_common import *

UNIT_ID = 'reef_ascendant_siphon_sponge'


def neutral_pose():
    return base()


def barrel(c, h, r0, r1, nflute=9, flute=0.12, hole_depth=0.5, wall=0.30, bulge=0.04, tilt=(0.0, 0.0), holes=()):
    """Barrel sponge: fluted vertical wall, widening to the lip, hollow top, optional side oscula (centre, radius)."""
    c = v3(*c)
    holes = [(v3(*hc), hr) for hc, hr in holes]

    def f(p):
        q = p - c
        t = np.clip(q[:, 1] / h, 0, 1)
        x = q[:, 0] - tilt[0] * h * t * t
        z = q[:, 2] - tilt[1] * h * t * t
        th = np.arctan2(x, z)
        r = r0 + (r1 - r0) * t ** 0.8 + bulge * np.sin(np.pi * t)
        rr = r * (1 - flute * (0.5 - 0.5 * np.cos(nflute * th)) ** 1.3)
        d = np.sqrt(x * x + z * z) - rr
        d = smax(d, np.maximum(-q[:, 1], q[:, 1] - h), 0.03)
        rim = np.sqrt(x * x + z * z) - rr * (1 - wall)
        d = smax(d, -smax(rim, -(q[:, 1] - h * (1 - hole_depth)), 0.02), 0.02)
        for hc, hr in holes:
            d = smax(d, -(np.linalg.norm(p - hc, axis=1) - hr), 0.02)
        return d * 0.8
    return Func(f, c + v3(tilt[0] * h * 0.5, h * 0.5, tilt[1] * h * 0.5), h * 0.6 + r1 + 0.2)


def build(P):
    parts, add = new_parts()
    st = P['strike']
    ph = 2 * np.pi * P['tell']
    sw = 1.0 + 0.045 * np.sin(ph) + 0.05 * st
    # base mound with roots
    add(Ellipsoid(v3(0, 0.10, 0), (0.62, 0.17, 0.55), None), 'sponge_dk', 0.05)
    rng = np.random.default_rng(8)
    ground_root(add, v3(0, 0.1, 0), 7, 0.78, 0.045, 'sponge', rng)
    # three barrels: (x, z, height, r0, r1, tilt)
    specs = [(0.0, 0.0, 0.92, 0.25, 0.34, (0.0, 0.0)),
             (-0.40, 0.18, 0.58, 0.19, 0.25, (-0.05, 0.12)),
             (0.34, 0.22, 0.45, 0.17, 0.22, (0.08, 0.10)),
             (0.14, -0.38, 0.62, 0.17, 0.23, (0.05, -0.1)),
             (-0.30, -0.28, 0.36, 0.13, 0.17, (-0.04, -0.06))]
    mouths = []
    for i, (x, z, h, r0, r1, tl) in enumerate(specs):
        hh = h * (sw if i == 0 else 1.0 + 0.5 * (sw - 1) * (1 if i % 2 else -1))
        holes = []
        for j in range(6 if i == 0 else 3):
            a = 0.9 + j * 1.05 + i
            y = hh * (0.25 + 0.14 * ((j * 3) % 5))
            rr = r0 + (r1 - r0) * (y / hh) ** 0.8
            holes.append(((x + np.sin(a) * rr, y, z + np.cos(a) * rr), 0.045 + 0.012 * (j % 2)))
        add(barrel((x, 0.08, z), hh, r0, r1, nflute=8 + i, tilt=tl, holes=holes), 'sponge' if i % 2 == 0 else 'sponge_lt', 0.04)
        top = v3(x + tl[0] * hh, 0.08 + hh - 0.14, z + tl[1] * hh)
        add(Ellipsoid(top, (r1 * 0.72, 0.05, r1 * 0.72), None), 'mouth', 0.0)
        mouths.append((top, r1))
        for hc, hr in holes:
            add(Sphere(v3(*hc) * 0.99 + v3(0, 0, 0) - norm(v3(hc[0] - x, 0, hc[2] - z)) * 0.01, hr * 0.8), 'osc', 0.0)
    # small pores / buds on mound
    for i in range(7):
        a = i * 0.9
        add(Sphere(v3(np.cos(a) * 0.5, 0.12, np.sin(a) * 0.45), 0.05), 'sponge_lt', 0.03)
    # spore plume rising out of the big mouth (filtering) and filaments reaching out on attack
    t0 = mouths[0][0]
    for i in range(5):
        t = (P['tell'] + i * 0.2) % 1.0
        add(Sphere(t0 + v3(0.05 * np.sin(i * 2 + ph), 0.04 + 0.5 * t, 0.05 * np.cos(i * 2)), 0.032 * (1 - 0.6 * t)), 'glow', 0.0)
    for i, (mp, mr) in enumerate(mouths):
        for k in range(3):
            a = k * 2.1 + i
            L = 0.25 + 0.9 * st * (1 if i < 3 else 0.6)
            d = norm(v3(np.sin(a) * 0.6, 0.35 * (1 - st), np.cos(a) * 0.6 + 0.8 * st))
            pts = [mp + v3(np.sin(a) * mr * 0.4, 0, np.cos(a) * mr * 0.4)]
            for j in range(1, 4):
                pts.append(pts[0] + d * L * j / 3 + v3(0.03 * np.sin(ph + j + k), 0.18 * (j / 3) * (1 - st) - 0.15 * (j / 3) ** 2 * st, 0))
            chain(add, pts, 0.026, 0.008, 'flesh', k=0.01)
            add(Sphere(pts[-1], 0.022), 'glow', 0.0)
    parts = body_pose(parts, P, lunge=0.0)
    parts = scaled(transform_parts(parts, t=(0.1, 0, -0.1)), 0.78)
    m = reef_mats(P, glow=0.8)
    m['sponge'] = pore_glow_mat(P, calcite_mat(flush=0.55, base_col=_hex('#e9c9b8'), flush_col=_hex('#f0a89a')).albedo, freq=40.0, thresh=0.78, k=0.9)
    m['sponge_lt'] = calcite_mat(flush=0.4, base_col=_hex('#f4e4d6'), flush_col=PINK)
    m['sponge_dk'] = coral_mat(deep=0.5, base_col=_hex('#c98778'))
    m['osc'] = Material(_hex('#5a2630'), emissive=tuple(np.array(GLOW) * 0.35 * (0.5 + 0.5 * np.sin(ph) + 0.5 * P['glow'])), rim=0.0, brush=0.0)
    m['mouth'] = Material(_hex('#4a1a24'), emissive=tuple(np.array(GLOW) * 0.22), rim=0.0)
    return finish(P, FACTION, parts, m)


def _extra(rows):
    for P, o in rows['move']:
        P['stride'] = 0.0
    for P, o in rows['idle']:
        P['squash'] = 1.0


ROWS, frames = reef_rows(neutral_pose, sink=0.2, tilt=0.05, extra=_extra)

"""Reef Tender (Reef Ascendant, support / healer). A stilt-legged drone carrying a branching coral
crown hung with glowing feeding sacs: the colony's stores, carried to the many. Sacs glow brighter on
the cast (mend growth); a feeding tendril lashes on the attack."""
from _reef_ascendant_common import *

UNIT_ID = 'reef_ascendant_reef_tender'


def neutral_pose():
    return base()


def build(P):
    parts, add = new_parts()
    sw = wave(P, 0.0, strike=0.0)
    st = P['strike']
    by = 0.5
    # body: ribbed calcite carapace with a pink underbelly
    add(ribbed(v3(0, by, 0), (0.15, 0.12, 0.2), n=12, depth=0.015, R=rot_x(0.1)), 'calcite_b', 0)
    add(Ellipsoid(v3(0, by - 0.06, 0.03), (0.12, 0.07, 0.15)), 'flesh', 0.04)
    # head-end: a short snout with a feeding mouth
    add(Capsule(v3(0, by, 0.16), v3(0, by - 0.05, 0.27), 0.065, 0.04), 'coral', 0.03)
    add(Sphere(v3(0, by - 0.06, 0.3), 0.025), 'mouth', 0)
    # four stilt legs
    legs(add, P, v3(0, by - 0.05, 0), 0.12, 0.16, n=4, h=0.2, r=0.022, mat='calcite_b', reach=0.08, lift=0.05)
    # branching crown on the back with feeding sacs at every tip
    rng = np.random.default_rng(21)
    sacs = []

    def tip(add, e, d, r):
        sacs.append(e)
    branches(add, v3(0, by + 0.08, -0.04), (0.0, 1.0, -0.2), 0.2, 0.045, 2, 'coral', rng,
             k=0.025, spread=1.0, sway=(0.03 * sw, 0.0), taper=0.72, kids=(3, 3), up_bias=0.1, tip=tip)
    pulse = 1.0 + 0.15 * np.sin(2 * np.pi * P['tell']) + 0.4 * P['cast_glow']
    for i, e in enumerate(sacs):
        r = 0.045 * (0.85 + 0.3 * ((i * 7) % 3) / 2) * pulse
        hang = e + v3(0.01 * sw, -r * 0.9, 0)
        add(Capsule(e, hang, 0.008), 'coral', 0.006)
        add(Sphere(hang + v3(0, -r * 0.4, 0), r), 'sac', 0.0)
    # feeding tendrils at the snout
    for s in (-1, 1):
        a = v3(0.04 * s, by - 0.05, 0.26)
        lash = st if s < 0 else 0.3 * st
        m = a + v3(0.05 * s, -0.12 + 0.15 * lash, 0.08 + 0.2 * lash)
        e = a + v3(0.07 * s + 0.02 * wave(P, s), -0.2 + 0.28 * lash, 0.08 + 0.4 * lash)
        chain(add, bez(a, m, e, 4), 0.014, 0.005, 'flesh', k=0.01)
    parts = body_pose(parts, P, lunge=0.04)
    m = reef_mats(P, glow=0.4)
    g = np.clip(0.45 + 0.25 * P['glow'] + 0.9 * P['cast_glow'], 0, 1.5)
    m['sac'] = Material(_hex('#f7c3b4'), spec=0.6, gloss=40, sss=0.8, brush=0.02,
                        emissive=tuple(np.array(_hex('#ffb4a0')) * 0.55 * g))
    lights = [Light(v3(0, by + 0.35, 0.1), GLOW, 0.2 * g, 0.4)]
    return finish(P, FACTION, parts, m, lights=lights)


ROWS, frames = reef_rows(neutral_pose, sink=0.1)

"""Brainstalk (Reef Ascendant, mind / aura). A tall fluted stalk of living calcite topped by a
brain-coral head whose grooves glow with the synapse pulse, trailing lash tendrils. Tall mind among
small drones; the light breathes in its grooves (idle tell)."""
from _reef_ascendant_common import *

UNIT_ID = 'reef_ascendant_brainstalk'


def neutral_pose():
    return base()


def build(P):
    parts, add = new_parts()
    rng = np.random.default_rng(3)
    st = P['strike']
    sw = wave(P, 0.0, strike=0.0)
    L = 1.22
    bx, bz = 0.03 * sw, 0.02 + 0.05 * st
    # root flare and runners
    ground_root(add, v3(0, 0.04, 0), 6, 0.3, 0.035, 'calcite_b', rng)
    add(spire(v3(0, 0.0, 0), L, 0.17, 0.085, n=10, flute=0.22, bulge=0.03, bulge_at=0.15, twist=0.6,
              bend=(bx, bz)), 'stalk', 0.05)
    top = v3(bx * L, L, bz * L)
    # a collar of short fronds where the head sits
    add(crown(top + v3(0, -0.03, 0), 9, 0.08, 0.1, 0.02, 0.016, 0.006, curl=0.03,
              sway=lambda i: (0, 0.015 * np.sin(i + 6.28 * P['tell']), 0)), 'coral', 0.02)
    # brain head: grooves cut to a glowing core
    hc = top + v3(0, 0.2, 0.02)
    Rh = rot_x(0.25 + 0.15 * st) @ rot_z(0.05 * sw)
    add(Ellipsoid(hc, (0.215, 0.18, 0.2), Rh), 'glow', 0)
    add(brain(hc, (0.25, 0.21, 0.235), groove=0.045, freq=30.0, R=Rh), 'calcite_p', 0.0)
    # lash tendrils hanging from under the head; the front one lashes out on the strike
    for i, (ang, ln) in enumerate([(0.4, 0.55), (2.2, 0.45), (3.9, 0.5), (5.2, 0.42)]):
        a = hc + v3(np.cos(ang) * 0.14, -0.13, np.sin(ang) * 0.14)
        lash = st if i == 0 else 0.15 * st
        ph = wave(P, i * 1.7, strike=0.0)
        mid = a + v3(np.cos(ang) * 0.12 + 0.04 * ph, -ln * 0.5 + 0.35 * lash, np.sin(ang) * 0.12 + 0.35 * lash)
        end = a + v3(np.cos(ang) * 0.1 + 0.08 * ph, -ln + 0.75 * lash, np.sin(ang) * 0.1 + 0.6 * lash)
        chain(add, bez(a, mid, end, n=4), 0.026, 0.008, 'flesh', k=0.012, first_k=0.03)
    parts = body_pose(parts, P, lean_scale=0.5)
    m = reef_mats(P, glow=0.5)
    m['stalk'] = calcite_mat(flush=0.32, low_col=_hex('#c79a86'))
    m['glow'] = glow_mat(P, k=0.9 + 0.3 * P['twitch'])
    lights = [Light(hc + v3(0, 0.05, 0.25), GLOW, 0.25 * (P['glow'] + P['cast_glow']), 0.5)]
    return finish(P, FACTION, parts, m, lights=lights)


ROWS, frames = reef_rows(neutral_pose, sink=0.25, tilt=0.2)

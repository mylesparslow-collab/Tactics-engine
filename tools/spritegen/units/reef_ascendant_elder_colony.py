"""Elder Colony (Reef Ascendant, exotic mind / summoner). Three centuries of slow growth: a massive
porous calcite mound fused from many fluted spires of different heights, polyp crowns on their tips,
a brain-coral lobe nestled in the middle, and pores that breathe light (the synapse pulse)."""
from _reef_ascendant_common import *
from render import Camera

UNIT_ID = 'reef_ascendant_elder_colony'
CAMERA = Camera(ppm=44)
SPIRES = [  # x, z, height, r0, bend phase
    (0.0, -0.1, 1.75, 0.22, 0.0), (-0.3, 0.05, 1.2, 0.16, 1.1), (0.32, -0.02, 1.35, 0.17, 2.3),
    (-0.16, -0.32, 1.45, 0.15, 3.0), (0.2, -0.36, 1.05, 0.13, 4.2), (-0.45, -0.2, 0.8, 0.11, 5.0),
    (0.48, 0.2, 0.75, 0.1, 0.7),
]


def neutral_pose():
    return base()


def build(P):
    parts, add = new_parts()
    rng = np.random.default_rng(41)
    st = P['strike']
    ground_root(add, v3(0, 0.05, 0), 10, 0.75, 0.05, 'calcite_b', rng, k=0.03)
    # the mound
    add(ribbed(v3(0, 0.22, -0.05), (0.62, 0.5, 0.3), n=26, depth=0.03, R=rot_x(np.pi / 2)), 'mound', 0)
    for j, (x, z, h, r0, ph) in enumerate(SPIRES):
        s = wave(P, ph, strike=0.0)
        out = norm(v3(x + 1e-3, 0, z + 1e-3))
        bend = (out[0] * 0.08 + 0.03 * s, out[2] * 0.08 + 0.06 * st * (j == 0))
        add(spire(v3(x, 0.15, z), h, r0, r0 * 0.4, n=8 + j % 3, flute=0.24, twist=0.7 + 0.3 * j, bulge=0.025,
                  bulge_at=0.7, bend=bend), 'mound' if j % 2 else 'spire', 0.06)
        tip = v3(x + bend[0] * h, 0.15 + h, z + bend[1] * h)
        add(crown(tip - v3(0, 0.02, 0), 8, r0 * 0.3, 0.06 + 0.04 * P['open'], 0.08, 0.012, 0.005, curl=0.03,
                  sway=lambda i, ph=ph: (0.0, 0.015 * np.sin(i * 1.7 + ph + 6.28 * P['tell']) + 0.02 * P['twitch'] * (i % 3 == 0), 0.0)),
            'flesh', 0.01)
    # brain lobe nested at the front
    bc = v3(0.08, 0.55, 0.3)
    add(Ellipsoid(bc, (0.21, 0.15, 0.16)), 'glow', 0)
    add(brain(bc, (0.25, 0.18, 0.2), groove=0.04, freq=28.0), 'calcite_p', 0.0)
    # crushing growth: a thick coral arm that heaves forward on the attack
    a = v3(-0.35, 0.3, 0.25)
    e = a + v3(-0.1, 0.15 + 0.2 * (1 - st), 0.25 + 0.45 * st)
    chain(add, bez(a, a + v3(-0.1, 0.35, 0.15), e, 4), 0.09, 0.035, 'coral', k=0.04, first_k=0.08)
    parts = body_pose(parts, P, lean_scale=0.3)
    m = reef_mats(P, glow=0.6)
    m['mound'] = pore_glow_mat(P, calcite_mat(flush=0.3).albedo, freq=34.0, thresh=0.78, k=0.8)
    m['spire'] = pore_glow_mat(P, coral_mat(base_col=_hex('#e58c7c')).albedo, freq=40.0, thresh=0.8, k=0.7)
    lights = [Light(bc + v3(0, 0.1, 0.3), GLOW, 0.3 * (P['glow'] + P['cast_glow']), 0.7)]
    return finish(P, FACTION, parts, m, lights=lights)


ROWS, frames = reef_rows(neutral_pose, sink=0.3, tilt=0.06)

"""Shard Urchin (Reef Ascendant, spiked body). A coral-red globe bristling with long calcite shards on
short tube feet. Defining detail: the shards bristle outward (lengthen) when it attacks or is hit."""
from _reef_ascendant_common import *

UNIT_ID = 'reef_ascendant_shard_urchin'
DIRS = fib_dirs(46, seed=4, jitter=0.12, ymin=-0.45)
RNG = np.random.default_rng(9)
LENS_ = RNG.uniform(0.7, 1.25, len(DIRS))


def neutral_pose():
    return base()


def build(P):
    parts, add = new_parts()
    bristle = 1.0 + 0.45 * P['strike'] + 0.25 * P['twitch'] + 0.5 * P['cast_glow']
    c = v3(0, 0.22, 0)
    add(ribbed(c, (0.16, 0.14, 0.16), n=16, depth=0.012, R=rot_x(np.pi / 2)), 'coral_dk', 0)
    add(spike_ball(c, 0.15, DIRS, 0.17 * bristle, 0.016, lens=LENS_), 'shard', 0.01)
    # pink mouth ring on the front
    add(Torus(c + v3(0, -0.02, 0.15), v3(0, 0, 1), 0.03, 0.012), 'flesh', 0.01)
    add(Sphere(c + v3(0, -0.02, 0.155), 0.022 + 0.01 * P['open']), 'mouth', 0)
    # tube feet
    s = P['stride']
    for i in range(8):
        ang = i * 2 * np.pi / 8
        ph = 1 if i % 2 else -1
        a = c + v3(np.cos(ang) * 0.09, -0.11, np.sin(ang) * 0.09)
        b = v3(np.cos(ang) * 0.14, 0.012 + max(0, 0.03 * s * ph), np.sin(ang) * 0.14 + 0.04 * s * ph)
        add(Capsule(a, b, 0.016, 0.01), 'flesh', 0.01)
    parts = scaled(body_pose(parts, P, lunge=0.05), 1.75)
    m = reef_mats(P, glow=0.2)
    m['shard'] = calcite_mat(flush=0.08, base_col=_hex('#f5efe6'), pores=False)
    return finish(P, FACTION, parts, m)


ROWS, frames = reef_rows(neutral_pose, sink=0.06)

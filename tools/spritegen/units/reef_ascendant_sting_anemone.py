"""Sting Anemone (Reef Ascendant, controller drone). A squat fluted column on a creeping foot, crowned
with a thicket of swaying pink stinging tentacles. Rooted-looking, but it glides. Tentacles reach
forward on the sting; tips glow faintly (numbing touch)."""
from _reef_ascendant_common import *

UNIT_ID = 'reef_ascendant_sting_anemone'


def neutral_pose():
    return base()


def build(P):
    parts, add = new_parts()
    st, op = P['strike'], P['open']
    t = P['tell']
    # creeping pedal foot and the fluted column
    add(Ellipsoid(v3(0, 0.035, 0), (0.17, 0.045, 0.16)), 'calcite_b', 0)
    add(spire(v3(0, 0.02, 0), 0.32, 0.14, 0.16, n=14, flute=0.1, bulge=-0.02, bulge_at=0.45,
              bend=(0.02 * wave(P, 0), 0.04 * st)), 'calcite_p', 0.04)
    top = v3(0.02 * wave(P, 0) * 0.32, 0.34, 0.04 * st * 0.32)
    add(Ellipsoid(top, (0.15, 0.04, 0.15)), 'coral_dk', 0.03)
    add(Sphere(top + v3(0, 0.02, 0), 0.04 + 0.01 * op), 'mouth', 0)
    n = 16

    def sw(i, ring):
        ang = i * 2 * np.pi / n
        front = max(0.0, np.sin(ang))           # +z side of the ring
        rad = 0.05 * np.sin(2 * np.pi * t + i * 1.3) + st * 0.16 * front
        up = 0.04 * np.cos(2 * np.pi * t + i * 0.9) - st * 0.12 * front + 0.03 * P['twitch'] * (i % 3 == 0)
        tan = 0.05 * np.sin(i * 2.7 + 6.28 * t) + 0.08 * P['stride'] * np.cos(ang)
        return (rad, up, tan)
    add(crown(top, n, 0.09, 0.2, 0.18, 0.022, 0.006, sway=lambda i: sw(i, 0), curl=0.06), 'flesh', 0.02)
    add(crown(top + v3(0, 0.02, 0), 10, 0.04, 0.12, 0.2, 0.018, 0.006, sway=lambda i: sw(i * 1.6, 1),
              curl=0.05, twist_phase=0.3), 'pinkflesh', 0.01)
    # numbing tips: glowing beads at the inner tentacle tips
    for i in range(10):
        ang = i * 2 * np.pi / 10 + 0.3
        o = sw(i * 1.6, 1)
        r = 0.04 + 0.12 + o[0] - 0.025
        p = top + v3(np.cos(ang) * r, 0.02 + 0.2 + o[1] + 0.05, np.sin(ang) * r)
        add(Sphere(p, 0.011), 'glow', 0)
    parts = scaled(body_pose(parts, P, lunge=0.03), 1.2)
    m = reef_mats(P, glow=0.5)
    m['pinkflesh'] = flesh_mat(col=_hex('#f6c9bd'), P=P, glow=0.3)
    return finish(P, FACTION, parts, m)


ROWS, frames = reef_rows(neutral_pose, sink=0.05)

"""Spireguard (Reef Ascendant, tank). A drone that never stops growing: tier on tier of ribbed calcite
shelves stacked into a squat stepped wall, crowned by a thick fluted spire, on stumpy pillar legs.
Rams forward on the attack; the growth rings have a faint pink seam that pulses."""
from _reef_ascendant_common import *

UNIT_ID = 'reef_ascendant_spireguard'
CAMERA = None


def neutral_pose():
    return base()


def build(P):
    parts, add = new_parts()
    sw = wave(P, 0.0, strike=0.0)
    rng = np.random.default_rng(8)
    # stumpy legs
    s = P['stride']
    for i, (x, z) in enumerate([(-0.24, 0.18), (0.24, 0.18), (-0.24, -0.2), (0.24, -0.2)]):
        ph = 1 if (i in (0, 3)) else -1
        lift = max(0, 0.05 * s * ph)
        add(spire(v3(x, lift, z + 0.05 * s * ph), 0.36, 0.085, 0.11, n=8, flute=0.15), 'calcite_b', 0.03)
    # stacked shelves, each a ribbed lens of calcite, stepping in as they rise
    tiers = [(0.38, 0.54, 0.46, 0.10), (0.58, 0.47, 0.40, 0.095), (0.77, 0.39, 0.33, 0.09), (0.94, 0.31, 0.27, 0.085),
             (1.09, 0.23, 0.2, 0.08)]
    # inner core that the shelves grow from
    add(spire(v3(0, 0.3, 0), 0.85, 0.36, 0.16, n=12, flute=0.2), 'calcite_p', 0.0)
    for i, (y, rx, rz, ry) in enumerate(tiers):
        # shelves grow unevenly (offset and tilted per tier) so the stack reads as grown, not as ladder rungs
        jx, jz, tz, tx = rng.uniform(-0.05, 0.05), rng.uniform(-0.03, 0.05), rng.uniform(-0.12, 0.12), rng.uniform(-0.1, 0.1)
        c = v3(0.01 * sw * i + jx, y, 0.02 * i + jz)
        Rt = rot_z(tz) @ rot_x(tx)
        add(ribbed(c, (rx, rz, ry * 1.25), n=22, depth=0.03, R=Rt @ rot_x(np.pi / 2), porous=0.015),
            'calcite_b' if i % 2 else 'shelf', 0.035)
        add(Ellipsoid(c + v3(0, -ry * 0.75, 0), (rx * 0.8, 0.02, rz * 0.8), Rt), 'seam', 0.0)
    # crown: thick fluted spire and two side horns, with a ram boss on the front
    add(spire(v3(0.05 * sw, 1.08, 0.08), 0.62, 0.16, 0.02, n=7, flute=0.25, twist=1.5, bend=(0.03 * sw, 0.04)), 'coral', 0.04)
    for sx in (-1, 1):
        add(Capsule(v3(0.18 * sx, 0.95, 0.12), v3(0.36 * sx, 1.28, 0.2), 0.06, 0.012), 'coral', 0.04)
    add(ribbed(v3(0, 0.62, 0.42), (0.18, 0.16, 0.1), n=10, depth=0.02), 'coral_dk', 0.06)
    add(Sphere(v3(0, 0.62, 0.5), 0.035 + 0.02 * P['open']), 'mouth', 0.0)
    parts = body_pose(parts, P, lean_scale=0.6, lunge=0.16)
    m = reef_mats(P, glow=0.4)
    g = np.clip(0.4 + 0.3 * P['glow'] + 0.8 * P['cast_glow'], 0, 1.4)
    m['shelf'] = calcite_mat(flush=0.4)
    m['seam'] = Material(CORAL, spec=0.2, emissive=tuple(np.array(GLOW) * 0.25 * g), brush=0.03)
    return finish(P, FACTION, parts, m)


del CAMERA
ROWS, frames = reef_rows(neutral_pose, sink=0.15, tilt=0.06)

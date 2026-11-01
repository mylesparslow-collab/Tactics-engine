"""Fanblade (Reef Ascendant, fast melee skirmisher). A lean drone grown around one great sea fan of
razored calcite, carried raised like a sail and swept down to cut. White calcite razor edge on a
coral fan; low fast body on long spine legs."""
from _reef_ascendant_common import *

UNIT_ID = 'reef_ascendant_fanblade'


def neutral_pose():
    return base(lean=0.08)


def build(P):
    parts, add = new_parts()
    st = P['strike']
    sw = wave(P, 0.0, strike=0.0)
    by = 0.26
    add(ribbed(v3(0, by, 0.0), (0.09, 0.075, 0.17), n=10, depth=0.012, R=rot_x(0.15)), 'calcite_b', 0)
    # head: a small fluted snout with a pink mouth
    add(spire(v3(0, by - 0.01, 0.12), 0.0001 + 0.1, 0.05, 0.03, n=6, flute=0.2), 'calcite_b', 0) if False else None
    add(Capsule(v3(0, by + 0.01, 0.12), v3(0, by - 0.02, 0.22), 0.05, 0.032), 'coral', 0.03)
    add(Sphere(v3(0, by - 0.025, 0.245), 0.022), 'mouth', 0)
    # the great fan: pivot on the back, raised behind; swept forward and down on the strike
    piv = v3(0.0, by + 0.05, -0.04)
    sweep = [0.0, -0.45, 1.25, 0.7][0]
    a = -0.35 - 0.6 * P['strike'] * 0 + np.radians(8) * sw
    # strike maps 0 -> 0.4 (windup back) -> 1 (cut forward)
    # the cut is a diagonal sweep across the body (yaw + roll), not a straight chop forward, so the fan
    # never folds flat onto the ground and its face stays toward the camera on the hit frame
    cut = np.interp(st, [0, 0.4, 1.0], [0.0, -0.4, 0.55])
    yaw = np.interp(st, [0, 0.4, 1.0], [0.0, 0.2, -0.6])
    roll = np.interp(st, [0, 0.4, 1.0], [0.0, 0.0, 0.5])
    R = rot_y(-0.35 + yaw) @ rot_x(-0.25 + cut + np.radians(6) * sw) @ rot_z(0.15 + roll + 0.06 * sw)
    add(fan(piv, R, 0.50, 0.62, ribs=11, thick=0.010, scallop=0.10, rib_k=0.006), 'razor', 0)
    add(fan(piv + R @ v3(0, 0, 0.002), R, 0.465, 0.6, ribs=11, thick=0.014, scallop=0.10, rib_k=0.008), 'fanbody', 0)
    add(Capsule(piv - R @ v3(0, 0.02, 0), piv + R @ v3(0, 0.12, 0), 0.03, 0.018), 'calcite_p', 0.02)
    # two small fins behind the head
    for s in (-1, 1):
        q = v3(0.07 * s, by + 0.03, 0.08)
        Rf = rot_y(s * 0.9) @ rot_z(-s * 1.0) @ rot_x(0.3 + 0.3 * sw * s)
        add(fan(q, Rf, 0.10, 0.5, ribs=5, thick=0.006, scallop=0.2), 'coral', 0)
    legs(add, P, v3(0, 0.2, 0.0), 0.08, 0.15, n=6, h=0.16, r=0.014, mat='calcite_b', reach=0.1, lift=0.05)
    parts = scaled(body_pose(parts, P, lunge=0.12), 1.15)
    m = reef_mats(P, glow=0.2)
    m['fanbody'] = coral_mat(deep=0.15, base_col=_hex('#e8907e'), hi_col=CALC)
    m['razor'] = Material(_hex('#fbf6ee'), spec=0.5, gloss=40, brush=0.03)
    return finish(P, FACTION, parts, m)


ROWS, frames = reef_rows(neutral_pose, sink=0.05)

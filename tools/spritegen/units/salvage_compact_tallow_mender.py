"""Tallow-Mender (Salvage Compact, support). Stout hull-doctor in a greasy leather apron, sleeves
rolled, head wrap, a tin pot of rendered tallow with a candle stuck in it held in the left hand and
a big ladle-spoon in the right. Defining detail: the candle-lit tallow pot. Tell: candle flicker."""
import numpy as np
from _salvage_compact_common import *

UNIT_ID = 'salvage_compact_tallow_mender'
FACTION = 'salvage_compact'

C = Costume(top='coat', sleeve='coat', legs='trousers', hand='skin', skirt=None, head='bald',
            belt='leather', girth=1.35)


def neutral_pose():
    P = base_pose(height=0.92, build=1.12)
    rig.lean(P, fwd=np.radians(4), side=np.radians(3))
    P['head_yaw'] = np.radians(-6)
    rig.place_arm(P, 'r', v3(-0.30, 0.98, 0.14), (-0.35, -0.3, -1))
    P['item_r'] = norm(v3(-0.15, 0.85, 0.4))
    rig.place_arm(P, 'l', v3(0.20, 1.05, 0.26), (0.35, -0.5, -1))
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    add(ragged_coat(P, hem_lo=0.36, hem_hi=0.50, slope=1, opening=0.7, flare=0.9, girth=1.35), 'coat', 0.0)
    wrap_head(P, add, 'canvas', knot_side=-1, size=1.03)
    pel, ch = P['pelvis'], P['chest']
    # leather apron over the belly
    def apron(p):
        q = p - (pel + v3(0, 0.05, 0.0))
        e = np.sqrt((q[:, 0] / 0.2) ** 2 + (q[:, 2] / 0.15) ** 2) - 1.0
        d = np.abs(e * 0.15) - 0.008
        d = np.maximum(d, np.maximum(q[:, 1] - 0.32, -0.42 - q[:, 1]))
        return np.maximum(d, 0.02 - q[:, 2])
    add(Func(apron, pel + v3(0, 0, 0.1), 0.45), 'apron', 0.0)
    for sx in (-1, 1):   # rolled sleeves
        add(Capsule(P['el_' + ('r' if sx < 0 else 'l')], P['el_' + ('r' if sx < 0 else 'l')] * 0.7 + P['wr_' + ('r' if sx < 0 else 'l')] * 0.3, 0.056), 'canvas', 0.0)
    # ladle-spoon
    d = P['item_r']
    if d is not None:
        d = norm(d)
        g = hand_pos(P, 'r')
        add(Capsule(g - d * 0.1, g + d * 0.42, 0.014), 'wood', 0.0)
        add(Ellipsoid(g + d * 0.48, (0.06, 0.03, 0.07), basis_from(np.cross(d, v3(1, 0, 0)) + v3(0, 0.001, 0), d)), 'tin', 0.0)
    # tallow pot with a candle in the left hand
    g = hand_pos(P, 'l') + v3(0.0, 0.02, 0.05)
    tin_cylinder(add, g - v3(0, 0.07, 0), g + v3(0, 0.04, 0), 0.06, mat='tin')
    add(Cylinder(g + v3(0, 0.02, 0), g + v3(0, 0.045, 0), 0.054, 0.004), 'tallow', 0.0)
    add(Torus(g + v3(0, 0.05, 0), v3(0.3, 0.2, 1), 0.07, 0.006), 'tin', 0.0)   # bail handle
    P2 = dict(P)
    P2['glow'] = P['glow'] * (1 + 1.5 * P['cast_glow'])
    candle(add, lights, g + v3(0.015, 0.04, 0), P2, height=0.07)
    if P['cast_glow'] > 0.05:
        lights.append(Light(pos=g + v3(0, 0.15, 0.05), color=_hex('#ffd27a'), intensity=1.6 * P['cast_glow'], radius=0.3))
    # rag and jars on the belt
    for k, x in enumerate((-0.15, 0.17)):
        add(Capsule(pel + v3(x, 0.02, 0.1), pel + v3(x, -0.06, 0.11), 0.03, 0.03), 'bone' if k else 'tin', 0.0)
    mats = sv_materials(P, skin='light', hair=_hex('#5a3a28'), coat_seed=5,
                        coat_colors=(SAILCLOTH, CANVAS, OCHRE, BONE))
    mats['apron'] = Material(lambda p, n: np.where((fbm(p, 14, 3) > 0.68)[:, None], _arr(TALLOW, len(p)) * 0.8,
                                                   _arr(_hex('#5e412c'), len(p))), spec=0.35, gloss=22, brush=0.08)
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = sv_rows(neutral_pose, attack_style='swing', weapon_side='r', fidget='sway', cast_side='l')

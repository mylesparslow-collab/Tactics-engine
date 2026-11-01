"""Rivet-Slinger (Salvage Compact, ranged). A pneumatic rivet gun built from a ship's bilge pump:
long tin barrel, pump cylinder and handle, hose running to a tank on the back. Goggles down,
knit cap, bandolier of bent nails. Defining detail: the bilge-pump gun."""
import numpy as np
from _salvage_compact_common import *

UNIT_ID = 'salvage_compact_rivet_slinger'
FACTION = 'salvage_compact'

C = Costume(top='coat', sleeve='coat2', legs='trousers', hand='glove', skirt=None, head='bald',
            belt='leather', girth=1.0)


def neutral_pose():
    P = base_pose(height=0.96, build=1.0)
    rig.lean(P, fwd=np.radians(6), side=np.radians(-3))
    rig.place_arm(P, 'r', v3(-0.20, 1.02, 0.14), (-0.35, -0.5, -1))
    P['item_r'] = norm(v3(0.15, 0.45, 1.0))
    rig.place_arm(P, 'l', P['wr_r'] + norm(v3(0.15, 0.45, 1.0)) * 0.26 + v3(0, -0.03, 0), (0.35, -0.6, -1))
    P['head_pitch'] = np.radians(-4)
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    add(ragged_coat(P, hem_lo=0.40, hem_hi=0.62, slope=-1, opening=0.5, flare=0.8), 'coat', 0.0)
    knit_cap(P, add, 'coat2', slouch=0.7)
    goggles(P, add, up=False)
    pauldron(P, add, 'r', size=0.8, layers=1)
    ch, pel = P['chest'], P['pelvis']
    # tank on the back (a pressure canister lashed to a frame)
    tc = ch + v3(0.05, 0.0, -0.19)
    tin_cylinder(add, tc + v3(0, -0.17, 0), tc + v3(0, 0.15, 0), 0.08, mat='brass')
    add(Sphere(tc + v3(0, 0.16, 0), 0.05), 'brass', 0.0)
    # the gun
    d = P['item_r']
    if d is not None:
        d = norm(d)
        g = hand_pos(P, 'r')
        sv = norm(np.cross(d, v3(0, 1, 0)))
        up = np.cross(sv, d)
        add(Capsule(g - d * 0.30 + up * 0.0, g + d * 0.05, 0.03, 0.025), 'wood', 0.01)      # stock
        tin_cylinder(add, g + d * 0.02 + up * 0.04, g + d * 0.40 + up * 0.04, 0.05, mat='tin')   # pump chamber
        add(Cylinder(g + d * 0.38 + up * 0.04, g + d * 0.78 + up * 0.04, 0.020, 0.004), 'iron', 0.0)  # barrel
        add(Cylinder(g + d * 0.74 + up * 0.04, g + d * 0.80 + up * 0.04, 0.032, 0.005), 'brass', 0.0)  # muzzle
        add(Capsule(g + d * 0.15 + up * 0.09, g + d * 0.05 + up * 0.20 - sv * 0.05, 0.010), 'iron', 0.0)  # pump handle
        add(Sphere(g + d * 0.05 + up * 0.20 - sv * 0.05, 0.02), 'wood', 0.0)
        # nail hopper
        add(RoundBox(g + d * 0.25 + up * 0.11, (0.04, 0.035, 0.05), 0.006, basis_from(up, d)), 'rust', 0.0)
        # hose from the tank to the chamber
        a, b = tc + v3(-0.05, -0.12, 0.06), g + d * 0.04 + up * 0.0 - sv * 0.03
        mid = (a + b) / 2 + v3(-0.08, -0.12, 0)
        add(Capsule(a, mid, 0.016), 'oilskin', 0.01)
        add(Capsule(mid, b, 0.016), 'oilskin', 0.01)
        if P['fx'] > 0:
            m = g + d * 0.86 + up * 0.04
            add(Ellipsoid(m, (0.05 * P['fx'], 0.05 * P['fx'], 0.05 * P['fx'])), 'flash', 0.0)
            for k in range(3):
                add(Capsule(m + d * (0.12 + 0.1 * k) + sv * (k - 1) * 0.04,
                            m + d * (0.17 + 0.1 * k) + sv * (k - 1) * 0.05, 0.007), 'iron', 0.0)
    # nail bandolier
    add(Capsule(pel + v3(0.13, 0.12, 0.08), ch + v3(-0.1, 0.12, 0.10), 0.016), 'leather', 0.0)
    mats = sv_materials(P, skin='dark', hair=_hex('#15100c'), coat_seed=11,
                        coat_colors=(CANVAS, SAILCLOTH, OCHRE, MUTED_RUST))
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = sv_rows(neutral_pose, attack_style='shoot', weapon_side='r', fidget='look', flicker=False)

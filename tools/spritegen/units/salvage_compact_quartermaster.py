"""Quartermaster (Salvage Compact, commander). Keeper of the ledger and the cutlass: a long patched
greatcoat with a diagonal tail, a bone-plate pauldron on the right shoulder only, a fat ledger under
the left arm, a tin lantern on the hip and a tallow-yellow sash. Head scarf, no hat."""
import numpy as np
from _salvage_compact_common import *

UNIT_ID = 'salvage_compact_quartermaster'
FACTION = 'salvage_compact'

C = Costume(top='coat2', sleeve='coat', legs='trousers', hand='glove', skirt=None, head='bald',
            belt='sash', girth=1.1)


def neutral_pose():
    P = base_pose(height=1.02, build=1.02)
    rig.lean(P, fwd=np.radians(3), side=np.radians(-3))
    P['head_yaw'] = np.radians(-20)
    P['head_pitch'] = np.radians(-6)
    rig.place_arm(P, 'r', v3(-0.27, 0.98, 0.16), (-0.35, -0.3, -1))
    P['item_r'] = norm(v3(-0.25, -0.35, 0.7))          # cutlass point down and out
    rig.place_arm(P, 'l', v3(0.20, 1.12, 0.18), (0.35, -0.6, -1))
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    add(ragged_coat(P, hem_lo=0.14, hem_hi=0.46, slope=-1, opening=0.55, flare=1.1, notch=0.06), 'coat', 0.0)
    scarf(P, add, 'canvas', tail=False)
    wrap_head(P, add, 'bonecloth', knot_side=-1)
    pauldron(P, add, 'r', size=0.8, mat='plate', layers=2)
    held(P, add, 'r', 'blade', head='brass', above=0.62)
    pel, ch = P['pelvis'], P['chest']
    # ledger: a fat book held against the chest, with a strap and loose pages
    g = hand_pos(P, 'l')
    R = basis_from(v3(0.1, 1, 0.2), (0.5, 0, 1))
    bc = g + v3(-0.03, 0.06, 0.04)
    add(RoundBox(bc, (0.10, 0.13, 0.04), 0.01, R), 'ledger', 0.0)
    add(RoundBox(bc + R @ v3(0.008, 0, 0), (0.095, 0.125, 0.034), 0.004, R), 'canvas', 0.0)
    # tin lantern on the right hip
    hook = pel + v3(-0.16, 0.06, 0.06)
    add(Capsule(hook, hook + v3(0, -0.06, 0), 0.006), 'tin', 0.0)
    tin_lantern(add, lights, hook + v3(-0.01, -0.13, 0.01), P['glow'], size=0.9)
    # key ring and coin purse
    add(Torus(pel + v3(0.14, 0.0, 0.1), v3(0.4, 0, 1), 0.035, 0.006), 'brass', 0.0)
    add(Sphere(pel + v3(0.1, -0.06, 0.12), 0.04), 'leather', 0.02)
    mats = sv_materials(P, skin='weathered', hair=_hex('#7d7468'), beard=_hex('#8a8175'), coat_seed=17,
                        coat_colors=(OILSKIN, DRAB, MUTED_RUST, CANVAS))
    mats['sash'] = Material(TALLOW, spec=0.08, brush=0.08)
    mats['bonecloth'] = Material(BONE, spec=0.03, brush=0.08)
    mats['ledger'] = Material(_hex('#5a3524'), spec=0.2, gloss=18, brush=0.06)
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = sv_rows(neutral_pose, attack_style='swing', weapon_side='r', fidget='look', cast_side='l')

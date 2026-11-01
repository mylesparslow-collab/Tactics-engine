"""Lamplighter (Salvage Compact, scout). A hulk-kid running ahead with a tin lantern on a long pole,
oil can on the hip, flares in the belt. Small, thin, knit cap. Tell: the lantern flickers."""
import numpy as np
from _salvage_compact_common import *

UNIT_ID = 'salvage_compact_lamplighter'
FACTION = 'salvage_compact'

C = Costume(top='coat', sleeve='canvas', legs='trousers', hand='skin', skirt=None, head='bald',
            belt='rope', girth=0.85, boots_tall=False)


def neutral_pose():
    P = base_pose(height=0.80, build=0.82)
    rig.lean(P, fwd=np.radians(8), side=np.radians(4))
    P['head_yaw'] = np.radians(-18)
    rig.place_arm(P, 'r', v3(-0.17, 0.98 * 0.8 + 0.14, 0.24), (-0.35, -0.4, -1), l1=0.22, l2=0.21)
    P['item_r'] = norm(v3(0.0, 1.0, 0.75))           # pole leaning forward on a diagonal
    rig.place_arm(P, 'l', v3(0.20, 0.80, 0.06), (0.35, 0, -1), l1=0.22, l2=0.21)
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    add(ragged_coat(P, hem_lo=0.48, hem_hi=0.66, slope=1, opening=0.6, flare=0.7), 'coat', 0.0)
    knit_cap(P, add, 'coat2', slouch=1.4)
    scarf(P, add, 'coat2', tail=True, side=-1)
    r = None
    if P['item_r'] is not None:
        d = norm(P['item_r'])
        g = hand_pos(P, 'r')
        reach = 0.55 + 0.4 * np.clip(d @ norm(v3(0, 0.8, 0.6)), 0, 1)
        butt, tip = g - d * 0.45, g + d * reach
        r = (butt, tip)
        add(Capsule(butt, tip, 0.017), 'wood', 0.0)
        sv = norm(np.cross(d, v3(0, 1, 0.2)))
        arm = tip + v3(0, 0.02, 0) + sv * 0.0 + norm(v3(d[0], 0, d[2])) * 0.12
        add(Capsule(tip, arm, 0.009), 'tin', 0.0)
        lc = arm - v3(0, 0.12, 0)
        add(Capsule(arm, lc + v3(0, 0.07, 0), 0.004), 'iron', 0.0)
        tin_lantern(add, lights, lc, P['glow'], size=1.25)
        add(Capsule(tip, tip - sv * 0.03 + v3(0, 0.05, 0), 0.008), 'rust', 0.0)   # little hook on the tip
        lash(add, butt, tip, n=2, r=0.02, at=(0.42, 0.47))
    pel = P['pelvis']
    # oil can on the left hip
    tin_cylinder(add, pel + v3(0.16, -0.12, 0.02), pel + v3(0.17, 0.0, 0.02), 0.045)
    add(Capsule(pel + v3(0.17, -0.01, 0.05), pel + v3(0.2, 0.06, 0.12), 0.008), 'tin', 0.0)
    flare_belt(P, add, n=3)
    hand_flare(P, add, lights, 'l')
    mats = sv_materials(P, skin='light', hair=_hex('#6a3b22'), coat_seed=4,
                        coat_colors=(OCHRE, CANVAS, MUTED_RUST, SAILCLOTH))
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = sv_rows(neutral_pose, attack_style='swing', weapon_side='r', fidget='look')

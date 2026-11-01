"""Wringer (Returning Tide, bruiser). A priest of the oldest rite, who draws water out of living things.

Broad, hooded, heavy planted stance in black and green wet robes, a linen cloth slung over one
shoulder. Defining detail: both hands twisting a rope of water upward between them.
"""
from _returning_tide_common import *

UNIT_ID = 'returning_tide_wringer'

C = Costume(top='robe', sleeve='robe', legs='robe', boot='skin', hand='skin', skin='skin',
            skirt=None, head='bald', belt=None, boots_tall=False, girth=1.25)


def neutral_pose():
    P = base_pose(height=1.0, build=1.2)
    rig.place_leg(P, 'l', (0.19, 0.085, 0.08))
    rig.place_leg(P, 'r', (-0.19, 0.085, -0.04))
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + rig.UPPER, v3(0, -0.04, 0))
    rig.lean(P, fwd=np.radians(9))
    P['head_pitch'] = np.radians(8)
    rig.place_arm(P, 'r', v3(-0.10, 1.00, 0.30), (-1, -0.4, -0.3))
    rig.place_arm(P, 'l', v3(0.06, 1.34, 0.32), (1, -0.6, -0.3))
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    add(ragged_robe(P, hem=0.06, flare=1.0, rag=1.0, seed=4.0, droop=0.04, girth=1.15), 'robe', 0.0)
    add(shawl(P, depth=0.24, width=0.26, rag=1.0, seed=1.3, front_drop=0.08), 'black', 0.0)
    deep_hood(P, add, 'black', size=1.14, peak=0.10, tail=0.26, droop=0.03)
    # wide sleeves
    for s in ('r', 'l'):
        sleeve_flare(P, add, s, 'robe', length=0.10, width=0.07)
    # linen cloth slung over the left shoulder, hanging front and back
    sh = P['sh_l']
    add(RoundBox(sh + v3(-0.02, -0.16, 0.10), (0.06, 0.18, 0.012), 0.01, basis_from(v3(0.15, 1, 0.25), (0, 0, 1))), 'linen', 0.01)
    add(RoundBox(sh + v3(-0.02, -0.20, -0.11), (0.06, 0.22, 0.012), 0.01, basis_from(v3(0.15, 1, -0.2), (0, 0, 1))), 'linen', 0.01)
    add(Capsule(sh + v3(-0.02, 0.03, 0.08), sh + v3(-0.02, 0.03, -0.09), 0.03), 'linen', 0.02)
    # the rope of water twisting up between the hands
    a, b = hand_pos(P, 'r'), hand_pos(P, 'l')
    if np.linalg.norm(b - a) > 0.08:
        water_rope(add, a, b, phase=P['tell'] + P['cast_glow'], r=0.020, amp=0.03, twist=1.5, n=8)
    drips(P, add, [a + v3(0, -0.04, 0), P['pelvis'] + v3(0.2, -0.82, 0.05), P['pelvis'] + v3(-0.22, -0.85, -0.02)])
    puddle(P, add, r=0.34)
    mats = {
        'robe': wet_cloth(_hex('#36423d'), wet=0.9, low_dark=0.2),
        'black': wet_cloth(_hex('#3f7a5c'), wet=0.8, low_dark=0.1),
        'skin': wet_skin(P, SKIN_PALE, hair=BLACK, sunken=0.3),
        'water': Material(GLINT, spec=1.2, gloss=70, emissive=tuple(np.array(BRINE) * (0.35 + 0.5 * P['cast_glow'])), brush=0.0),
    }
    return tide_finish(P, parts, mats, add)


ROWS, frames = tide_rows(neutral_pose, attack_style='cast', weapon_side='r', cast_side='l')

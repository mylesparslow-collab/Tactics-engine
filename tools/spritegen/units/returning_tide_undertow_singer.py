"""Undertow Singer (Returning Tide, controller). A voice that tugs at ankles.

Barefoot woman in flowing green-black robes, long wet hair, mouth open in song, one arm hooking toward
her chest as if hauling a line. Defining detail: a line of water running from her fist down to the
ground ahead, and ripples spreading at her feet.
"""
from _returning_tide_common import *

UNIT_ID = 'returning_tide_undertow_singer'

C = Costume(top='robe', sleeve='robe', legs='robe', boot='skin', hand='skin', skin='skin',
            skirt=None, head='bald', belt=None, boots_tall=False, girth=0.85)


def neutral_pose():
    P = base_pose(height=0.99, build=0.88)
    rig.place_leg(P, 'r', (-0.12, 0.085, -0.12))
    rig.lean(P, fwd=np.radians(-6), side=np.radians(3))
    P['head_pitch'] = np.radians(-14)
    P['head_yaw'] = np.radians(-4)
    rig.place_arm(P, 'r', v3(-0.10, 1.30, 0.20), (-1, -0.6, -0.2))
    rig.place_arm(P, 'l', v3(0.34, 1.02, 0.12), (1, 0, -0.5))
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    wet_hair(P, add, 'hair', style='long')
    add(ragged_robe(P, hem=0.02, flare=1.05, top=1.06, rag=1.3, seed=9.2, droop=0.10, girth=0.9), 'robe', 0.0)
    add(shawl(P, depth=0.26, width=0.20, rag=1.4, seed=5.5, front_drop=0.12), 'black', 0.0)
    for s in ('r', 'l'):
        sleeve_flare(P, add, s, 'robe', length=0.14, width=0.07)
    # the hauled line of water: from her fist out and down to the ground ahead
    hr = hand_pos(P, 'r')
    pull = P['cast_glow']
    far = v3(-0.62 - 0.1 * pull, 0.02, 0.18)
    water_rope(add, hr, far, phase=P['tell'], r=0.013, amp=0.012, twist=3, n=10, sag=0.12)
    ripples(P, add, n=2, r0=0.12, center=far)
    ripples(P, add, n=2, r0=0.30, center=(0.0, 0.0, 0.05))
    drips(P, add, [hr + v3(0, -0.05, 0), P['wr_l'] + v3(0, -0.12, 0), P['head'] + v3(0.05, -0.30, -0.1)])
    puddle(P, add, r=0.32)
    mats = {
        'robe': wet_cloth(_hex('#2e4a3d'), wet=0.8, low_dark=0.3),
        'black': wet_cloth(_hex('#5f8f74'), wet=0.8, low_dark=0.1),
        'hair': Material(_hex('#1c1a18'), spec=0.8, gloss=40, brush=0.05),
        'skin': wet_skin(P, SKIN_PALE, hair=_hex('#1c1a18'), mouth=1.0),
        'water': Material(GLINT, spec=1.2, gloss=70, emissive=tuple(np.array(BRINE) * (0.35 + 0.5 * pull)), brush=0.0),
    }
    return tide_finish(P, parts, mats, add)


ROWS, frames = tide_rows(neutral_pose, attack_style='cast', weapon_side='r', cast_side='l')

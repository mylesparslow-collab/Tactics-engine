"""Shroud-Mender (Returning Tide, healer). A midwife of the Drowned who wraps wounds in wet cloth.

Hunched woman in sodden green-grey shawls, hood raised, a black sash, a bone needle at the belt.
Defining detail: a bundle of wet linen cradled in her arm, trailing a long dripping strip.
"""
from _returning_tide_common import *

UNIT_ID = 'returning_tide_shroud_mender'

C = Costume(top='shawls', sleeve='shawls', legs='shawls', boot='skin', hand='skin', skin='skin',
            skirt=None, head='bald', belt=None, boots_tall=False, girth=1.0)


def neutral_pose():
    P = base_pose(height=0.93, build=0.95)
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + rig.UPPER, v3(0, -0.03, 0))
    rig.place_leg(P, 'l', (0.13, 0.085, 0.10))
    rig.lean(P, fwd=np.radians(20))
    P['head_pitch'] = np.radians(-4)
    P['head_yaw'] = np.radians(-14)
    rig.place_arm(P, 'l', v3(0.07, 1.04, 0.30), (1, -0.3, -0.5))
    rig.place_arm(P, 'r', v3(-0.16, 1.00, 0.28), (-1, -0.4, -0.4))
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    add(ragged_robe(P, hem=0.05, flare=0.85, rag=1.2, seed=6.2, droop=0.03, girth=1.05), 'shawls', 0.0)
    add(shawl(P, depth=0.34, width=0.20, rag=1.4, seed=0.9, front_drop=0.06), 'shawl2', 0.0)
    add(shawl(P, depth=0.18, width=0.20, rag=1.0, seed=2.4, front_drop=0.03), 'shawls', 0.0)
    deep_hood(P, add, 'shawl2', size=1.12, peak=0.04, tail=0.0, droop=0.04)
    for s in ('r', 'l'):
        sleeve_flare(P, add, s, 'shawls', length=0.08, width=0.06)
    # black sash and the bone needle
    pel = P['pelvis']

    def sash(p, c=pel + v3(0, 0.10, 0)):
        q = p - c
        e = np.sqrt((q[:, 0] / 0.17) ** 2 + (q[:, 2] / 0.13) ** 2) - 1.0
        return np.maximum(np.abs(e * 0.13) - 0.008, np.abs(q[:, 1]) - 0.04)
    add(Func(sash, pel + v3(0, 0.10, 0), 0.26), 'black', 0.0)
    add(Capsule(pel + v3(0.14, 0.14, 0.09), pel + v3(0.17, -0.06, 0.12), 0.007, 0.004), 'bone', 0.0)
    # the bundle of wet linen in the crook of her left arm, with a long trailing strip
    hl = hand_pos(P, 'l')
    bc = hl + v3(-0.10, 0.05, 0.06)
    R = basis_from(v3(1.0, 0.35, 0.25), (0, 0, 1))
    add(Ellipsoid(bc, (0.085, 0.15, 0.08), R), 'linen', 0.0)
    add(Torus(bc, R[:, 1], 0.055, 0.016), 'linen', 0.0)
    tail = bc + v3(-0.05, -0.55, 0.06 + 0.03 * P['skirt_sway'])
    add(Capsule(bc + v3(-0.02, -0.04, 0.05), (bc + tail) / 2 + v3(-0.03, 0, 0.04), 0.022, 0.02), 'linen', 0.01)
    add(Capsule((bc + tail) / 2 + v3(-0.03, 0, 0.04), tail, 0.02, 0.012), 'linen', 0.01)
    drips(P, add, [tail, bc + v3(0.04, -0.08, 0.02), pel + v3(-0.18, -0.85, 0.04)])
    puddle(P, add, r=0.30)
    mats = {
        'shawls': wet_cloth(_hex('#7d8580'), wet=0.7, low_dark=0.35),
        'shawl2': wet_cloth(_hex('#47705a'), wet=0.8, low_dark=0.3),
        'bone': Material(_hex('#ddd4bc'), spec=0.2, gloss=20),
        'linen': Material(lambda p, n: np.array(LINEN)[None, :] * (0.88 + 0.16 * fbm(p, 24, 2)[:, None]),
                          spec=0.45, gloss=30, brush=0.06,
                          emissive=tuple(np.array(BRINE) * 0.35 * P['cast_glow']) if P['cast_glow'] > 0 else None),
        'skin': wet_skin(P, SKIN_WARM, hair=_hex('#4a4038')),
    }
    return tide_finish(P, parts, mats, add)


ROWS, frames = tide_rows(neutral_pose, attack_style='cast', weapon_side='r', cast_side='r')

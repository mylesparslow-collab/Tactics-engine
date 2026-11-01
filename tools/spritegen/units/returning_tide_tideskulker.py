"""Tideskulker (Returning Tide, skirmisher). A gutter-child who learned the shallows on the Weeping Shelf.

Small and wiry, crouched low, a hooked gutter-knife held back behind the hip, bare feet, black and
green rags, a short wet hood, silt-smeared face. Defining detail: the low crouch and the hooked knife.
"""
from _returning_tide_common import *

UNIT_ID = 'returning_tide_tideskulker'

C = Costume(top='rags', sleeve='rags', legs='skin', boot='skin', hand='skin', skin='skin',
            skirt=None, head='bald', belt=None, boots_tall=False, girth=0.85)


def neutral_pose():
    h = 0.78
    P = base_pose(height=h, build=0.82)
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + rig.UPPER, v3(0, -0.13 * h, -0.04))
    rig.place_leg(P, 'l', (0.16 * 0.82, 0.085, 0.17), l1=0.43 * h, l2=0.42 * h)
    rig.place_leg(P, 'r', (-0.14 * 0.82, 0.085, -0.14), l1=0.43 * h, l2=0.42 * h)
    rig.lean(P, fwd=np.radians(24))
    P['head_pitch'] = np.radians(-14)
    P['head_yaw'] = np.radians(-18)
    rig.place_arm(P, 'r', P['pelvis'] + v3(-0.20, 0.0, -0.14), (-0.4, 0.2, -1), l1=0.27 * h, l2=0.26 * h)
    rig.place_arm(P, 'l', P['pelvis'] + v3(0.14, 0.12, 0.26), (0.6, -0.6, -0.2), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(-0.2, -0.25, -1.0))
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    add(ragged_robe(P, hem=0.52, flare=0.5, top=1.0, rag=1.6, seed=3.3, droop=0.0, opening=0.25), 'rags', 0.0)
    add(shawl(P, depth=0.16, width=0.17, rag=1.4, seed=2.2, front_drop=0.0), 'black', 0.0)
    deep_hood(P, add, 'black', size=1.12, peak=0.08, tail=0.14, droop=0.02)
    # wrapped shins (rags) and a hooked knife
    for s in ('r', 'l'):
        kn, an = P['kn_' + s], P['an_' + s]
        add(Capsule(kn + (an - kn) * 0.35, an + v3(0, 0.03, 0), 0.046, 0.046), 'wrap', 0.01)
    r = held(P, add, 'r', 'knife', head='iron')
    if r is not None:
        butt, tip = r
        d = norm(tip - butt)
        side = norm(np.cross(d, v3(0, 1, 0)))
        c = tip + side * 0.04
        add(Torus(c, np.cross(d, side), 0.04, 0.008), 'steel', 0.0)
        # cut the inner half of the hook so it reads as a curve, not a ring
    rag_strips(add, P['pelvis'] + v3(0.02, -0.25, -0.10), 3, 0.18, 'rags', spread=0.06, seed=9, sway=P['skirt_sway'])
    drips(P, add, [P['pelvis'] + v3(-0.10, -0.38, 0.06), P['wr_l'] + v3(0, -0.05, 0)])
    puddle(P, add, r=0.22)
    mats = {
        'rags': wet_cloth(_hex('#3e5f4c'), wet=0.7, low_dark=0.3, streak=0.2, top=1.1),
        'wrap': wet_cloth(LINEN_DK, wet=0.5, low_dark=0.3, top=0.6),
        'skin': wet_skin(P, SKIN_WARM, hair=BLACK, brows=True),
    }
    # silt smear across the face
    sk = mats['skin'].albedo

    def smeared(p, n):
        a = sk(p, n)
        q = (p - P['head']) @ head_R(P)
        m = (np.abs(q[:, 1] + 0.02 + 0.3 * q[:, 0]) < 0.018) & (q[:, 2] > 0.03)
        a[m] = a[m] * 0.55 + np.array(_hex('#6b6656')) * 0.45
        return a
    mats['skin'].albedo = smeared
    return tide_finish(P, parts, mats, add)


ROWS, frames = tide_rows(neutral_pose, attack_style='swing', weapon_side='r', sink=0.25)

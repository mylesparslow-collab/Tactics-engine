"""Rainsayer (Returning Tide, caster). A prophet who calls rain from clear sky.

Gaunt, hooded dark-green robe, bare feet, a staff hung with tarnished bells in one hand, the other
arm raised to the sky. Defining detail: a small rain cloud hanging over the raised hand, raining.
"""
from _returning_tide_common import *

UNIT_ID = 'returning_tide_rainsayer'

C = Costume(top='robe', sleeve='robe', legs='robe', boot='skin', hand='skin', skin='skin',
            skirt=None, head='bald', belt=None, boots_tall=False, girth=0.8)


def neutral_pose():
    P = base_pose(height=1.02, build=0.85)
    rig.lean(P, fwd=np.radians(-2))
    P['head_pitch'] = np.radians(-12)
    rig.place_arm(P, 'r', v3(-0.26, 1.00, 0.16), (-0.6, -0.2, -1))
    rig.place_arm(P, 'l', v3(0.22, 1.86, 0.10), (1, 0, -0.3))
    P['item_r'] = norm(v3(-0.02, 1.0, 0.04))
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    add(ragged_robe(P, hem=0.10, flare=0.6, rag=1.3, seed=5.1, droop=0.05, girth=0.85), 'robe', 0.0)
    add(shawl(P, depth=0.22, width=0.19, rag=1.2, seed=3.0), 'hood', 0.0)
    deep_hood(P, add, 'hood', size=1.08, peak=0.05, tail=0.30)
    knotted_cord(add, P, girth=0.85)
    for s in ('r', 'l'):
        sleeve_flare(P, add, s, 'robe', length=0.10, width=0.065)
    # staff with a crossbar of tarnished bells
    r = held(P, add, 'r', 'staff', shaft='driftwood', head='bronze', below=1.0, above=0.9)
    if r is not None:
        butt, tip = r
        d = norm(tip - butt)
        side = norm(np.cross(d, v3(0, 0, 1)))
        cb = tip - d * 0.06
        add(Capsule(cb - side * 0.10, cb + side * 0.10, 0.009), 'driftwood', 0.0)
        for k, o in enumerate((-0.09, 0.0, 0.09)):
            sw = 0.012 * np.sin(P['tell'] * 6.28 + k * 2)
            top = cb + side * o
            bc = top - d * 0.075 + side * sw
            add(Capsule(top, bc, 0.003), 'cord', 0.0)
            add(Capsule(bc + d * 0.01, bc - d * 0.03, 0.012, 0.024), 'bronze', 0.0)
    # the rain cloud over the raised left hand
    hl = hand_pos(P, 'l')
    cg = P['cast_glow']
    if hl[1] > 1.4:
        cc = hl + v3(0.02, 0.13, 0.0)
        s = 1.35 + 0.35 * cg
        for o, r_ in ((v3(0, 0, 0), 0.075), (v3(0.07, -0.01, 0.02), 0.06), (v3(-0.07, -0.015, -0.01), 0.055),
                      (v3(0.02, 0.04, -0.02), 0.05), (v3(-0.03, -0.02, 0.06), 0.045)):
            add(Sphere(cc + o * s, r_ * s), 'cloud', 0.03)
        rain(add, cc + v3(0, -0.06, 0), w=0.09 * s, n=10, length=0.10, phase=P['tell'] + cg, top=0.0,
             bottom=-0.45, seed=4)
    drips(P, add, [P['wr_r'] + v3(0, -0.07, 0), P['pelvis'] + v3(0.12, -0.80, 0.06)])
    puddle(P, add, r=0.26)
    mats = {
        'robe': wet_cloth(WET_GREY, wet=0.8, low_dark=0.35),
        'hood': wet_cloth(_hex('#3f7a5c'), wet=0.8, low_dark=0.2),
        'skin': wet_skin(P, SKIN_PALE, hair=BLACK, sunken=0.5),
        'driftwood': Material(_hex('#6e6252'), spec=0.2, gloss=18, brush=0.12),
        'bronze': Material(_hex('#7d7a52'), spec=0.6, gloss=30, metal=0.7, brush=0.06),
        'cloud': Material(_hex('#8e9a98'), spec=0.05, brush=0.10,
                          emissive=tuple(np.array(BRINE) * 0.3 * cg) if cg > 0 else None),
    }
    return tide_finish(P, parts, mats, add)


def _post(fr):
    # keep the raised arm (and its cloud) up through walking
    for i, (P, lk) in enumerate(fr['move']):
        rig.place_arm(P, 'l', P['sh_l'] + v3(0.04, 0.42, 0.10 + 0.02 * i), (1, 0, -0.3))
    return fr


ROWS, frames = tide_rows(neutral_pose, attack_style='cast', weapon_side='l', cast_side='l', post=_post)

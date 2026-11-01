"""Choirmaster (Returning Tide, commander). A conductor whose hymns keep a thousand throats in time.

Tall and upright in a long drowned-green robe with a high stiff black collar and a linen stole, damp
hair. Defining detail: a long thin choir staff raised high in one hand, the other hand open, with
drips shaken off the staff tip.
"""
from _returning_tide_common import *

UNIT_ID = 'returning_tide_choirmaster'

C = Costume(top='robe', sleeve='robe', legs='robe', boot='boot', hand='skin', skin='skin',
            skirt=None, head='bald', belt=None, boots_tall=False, girth=0.95)


def neutral_pose():
    P = base_pose(height=1.08, build=0.95)
    rig.lean(P, fwd=np.radians(-3))
    P['head_pitch'] = np.radians(-8)
    # staff arm raised out to the side (not over the head, which hid the face behind the forearm)
    rig.place_arm(P, 'r', v3(-0.44, 1.64, 0.20), (-1, -0.7, -0.3), l1=0.29, l2=0.28)
    rig.place_arm(P, 'l', v3(0.34, 1.22, 0.30), (1, -0.8, -0.2), l1=0.29, l2=0.28)
    P['item_r'] = norm(v3(-0.40, 1.0, 0.05))
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    wet_hair(P, add, 'hair', style='bob')
    add(ragged_robe(P, hem=0.03, flare=0.75, top=1.05, rag=0.9, seed=8.1, droop=0.05), 'robe', 0.0)
    hood_down(P, add, 'robe', size=0.9)
    # high stiff black collar
    nk = P['neck']
    up = norm(P['neck'] - P['chest'])
    add(Cylinder(nk + up * -0.02, nk + up * 0.09, 0.080 * P['build'], 0.012), 'black', 0.0)
    # linen stole hanging down the front
    for sx in (-1, 1):
        a = nk + v3(sx * 0.06, -0.05, 0.07)
        b = P['pelvis'] + v3(sx * 0.07 + P['skirt_sway'] * 0.02, -0.40, 0.17)
        add(RoundBox((a + b) / 2, (0.03, np.linalg.norm(b - a) / 2, 0.008), 0.005, basis_from(a - b, (0, 0, 1))), 'linen', 0.0)
    for s in ('r', 'l'):
        sleeve_flare(P, add, s, 'robe', length=0.08, width=0.06)
    r = held(P, add, 'r', 'staff', shaft='black', head='bronze', below=0.12, above=0.75)
    ends = []
    if r is not None:
        butt, tip = r
        add(Torus(tip, norm(tip - butt), 0.035, 0.006), 'bronze', 0.0)
        ends.append(tip - v3(0, 0.03, 0))
    drips(P, add, ends + [P['wr_l'] + v3(0, -0.07, 0), P['pelvis'] + v3(-0.2, -0.86, 0.02)], fall=0.4)
    puddle(P, add, r=0.28)
    mats = {
        'robe': wet_cloth(_hex('#3f7a5c'), wet=0.7, low_dark=0.42),
        'hair': Material(_hex('#2a2620'), spec=0.7, gloss=40, brush=0.06),
        'bronze': Material(_hex('#8a8458'), spec=0.7, gloss=34, metal=0.7, brush=0.05),
        'skin': wet_skin(P, SKIN_PALE, hair=_hex('#2a2620'), mouth=0.6),
    }
    return tide_finish(P, parts, mats, add)


ROWS, frames = tide_rows(neutral_pose, attack_style='swing', weapon_side='r')

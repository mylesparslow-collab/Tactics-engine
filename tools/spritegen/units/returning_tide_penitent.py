"""Penitent (Returning Tide, cheap body). Shaven pilgrim walking into the surf to be forgiven.

Thin, arms spread, head tilted up mid-prayer. Damp green-grey sackcloth shift with a ragged hem,
knotted cord at the waist, black cord at the neck, bare feet, a club held loosely.
Defining detail: ropes of seawater trailing from both sleeves.
"""
from _returning_tide_common import *

UNIT_ID = 'returning_tide_penitent'

C = Costume(top='shift', sleeve='skin', legs='skin', boot='skin', hand='skin', skin='skin',
            skirt=None, head='bald', belt=None, boots_tall=False, girth=0.85)


def neutral_pose():
    P = base_pose(height=0.97, build=0.88)
    rig.lean(P, fwd=np.radians(-3))
    P['head_pitch'] = np.radians(-16)
    P['head_yaw'] = np.radians(-6)
    rig.place_arm(P, 'r', v3(-0.36, 1.02, 0.18), (-0.6, -0.6, -0.6))
    # open arm offered forward and bent, palm up, instead of a stiff straight-out T
    rig.place_arm(P, 'l', v3(0.32, 1.24, 0.30), (1, -1, 0))
    P['item_r'] = norm(v3(-0.25, -0.9, 0.25))
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    add(ragged_robe(P, hem=0.26, flare=0.55, rag=1.2, seed=0.7, girth=0.9), 'shift', 0.0)
    held(P, add, 'r', 'club', shaft='driftwood')
    # a sodden hood pushed back off the shaven head: reads as Tide at 1x without hiding the prayer
    hood_down(P, add, 'shift', size=1.0)
    knotted_cord(add, P, girth=0.95)
    # black cord at the neck with a small knot
    nk = P['neck']
    add(Torus(nk + v3(0, -0.03, 0.005), v3(0, 1, 0.25), 0.062, 0.007), 'cord', 0.0)
    add(Sphere(nk + v3(0, -0.07, 0.07), 0.014), 'cord', 0.0)
    # wide wet sleeves; seawater ropes trail from them
    ends = []
    for s in ('r', 'l'):
        sx = -1 if s == 'r' else 1
        sh, el = P['sh_' + s], P['el_' + s]
        add(Capsule(sh + v3(-sx * 0.02, -0.03, 0), el, 0.066, 0.064), 'shift', 0.03)
        add(Capsule(el, el + v3(sx * 0.01, -0.11, -0.02), 0.068, 0.045), 'shift', 0.02)
        e = el + v3(sx * 0.01, -0.15, -0.02)
        tail = e + v3(sx * 0.10, -0.42 + 0.04 * np.sin(P['tell'] * 6.28), -0.16)
        water_rope(add, e, tail, phase=P['tell'], r=0.012, amp=0.012, twist=1.5, n=6, sag=-0.04)
        ends.append(tail)
    drips(P, add, ends + [P['pelvis'] + v3(-0.12, -0.62, 0.05), P['pelvis'] + v3(0.10, -0.66, -0.06)])
    puddle(P, add, r=0.26)
    mats = {
        'shift': wet_cloth(_hex('#6c7b6a'), wet=0.7, low_dark=0.42),
        'skin': wet_skin(P, SKIN_PALE, hair=_hex('#5a4a3e'), mouth=0.5),
        'driftwood': Material(_hex('#7a6c5c'), spec=0.2, gloss=18, brush=0.12),
    }
    return tide_finish(P, parts, mats, add)


ROWS, frames = tide_rows(neutral_pose, attack_style='swing', weapon_side='r')

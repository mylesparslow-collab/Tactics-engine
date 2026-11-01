"""Tear-Slinger (Returning Tide, ranged). A mourner who hurls brine from a bag of collected grief.

Veiled woman in a dark-green wet cloak and a black veil, wide throwing stance, a leather brine-bag
swinging from a sling, tear vials on the belt. Defining detail: the heavy dripping grief-bag.
"""
from _returning_tide_common import *

UNIT_ID = 'returning_tide_tear_slinger'

C = Costume(top='under', sleeve='cloak', legs='under', boot='skin', hand='skin', skin='skin',
            skirt=None, head='bald', belt='leather', boots_tall=False, girth=0.88)


def neutral_pose():
    P = base_pose(height=0.96, build=0.9)
    rig.place_leg(P, 'l', (0.19, 0.085, 0.16))
    rig.place_leg(P, 'r', (-0.17, 0.085, -0.10))
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + rig.UPPER, v3(0, -0.03, 0))
    rig.lean(P, fwd=np.radians(6), side=np.radians(-3))
    P['head_pitch'] = np.radians(2)
    # sling arm hangs loose and a little out; the old backward elbow made a hard triangle
    rig.place_arm(P, 'r', v3(-0.32, 1.02, 0.12), (-1, -0.2, 0.2))
    rig.place_arm(P, 'l', v3(0.21, 1.16, 0.30), (0.6, -0.8, -0.3))
    P['item_r'] = norm(v3(-0.40, -1.0, 0.20))
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    add(ragged_robe(P, hem=0.14, flare=0.9, rag=1.4, seed=1.1, droop=0.08, opening=0.35), 'cloak', 0.0)
    add(shawl(P, depth=0.30, width=0.22, rag=1.2, seed=0.4, front_drop=0.04), 'cloak', 0.0)
    deep_hood(P, add, 'cloak', size=1.1, peak=0.05, tail=0.0)
    # black veil hanging over the lower face and chin
    H, R, h = P['head'], head_R(P), P['height']
    add(Ellipsoid(H + R @ v3(0, -0.06, 0.05) * h, (0.074 * h, 0.058 * h, 0.06 * h), R), 'veil', 0.01)
    add(Ellipsoid(H + R @ v3(0, -0.11, 0.05) * h, (0.07 * h, 0.06 * h, 0.05 * h), R), 'veil', 0.03)
    # sling and the grief-bag
    r = held(P, add, 'r', 'sling', head='cord')
    if r is not None:
        butt, tip = r
        d = norm(tip - butt)
        add(Ellipsoid(tip + d * 0.03, (0.065, 0.075, 0.06), basis_from(d, (0, 0, 1))), 'bag', 0.0)
        add(Cylinder(tip - d * 0.03, tip + d * 0.0, 0.02, 0.004), 'cord', 0.0)
        drips(P, add, [tip + d * 0.10, tip + d * 0.07 + v3(0.03, 0, 0)], speed=2.0)
    # tear vials on the belt
    pel = P['pelvis']
    for k, a in enumerate((-0.9, -0.45, 0.2, 0.65)):
        c = pel + v3(np.sin(a) * 0.15, 0.03, np.cos(a) * 0.115)
        add(Capsule(c, c + v3(0, -0.06, 0), 0.016), 'vial', 0.0)
        add(Sphere(c + v3(0, 0.012, 0), 0.011), 'cord', 0.0)
    drips(P, add, [pel + v3(0.18, -0.74, -0.10), pel + v3(-0.20, -0.70, 0.02)])
    puddle(P, add, r=0.28)
    mats = {
        'cloak': wet_cloth(_hex('#365a48'), wet=0.8, low_dark=0.35),
        'under': wet_cloth(GREY_DK, wet=0.6),
        'veil': wet_cloth(BLACK, wet=0.9, low_dark=0.0),
        'bag': Material(_hex('#4a3a2c'), spec=0.55, gloss=30, brush=0.08),
        'vial': Material(GLINT, spec=1.0, gloss=60, emissive=tuple(np.array(BRINE) * 0.5), brush=0.0),
        'skin': wet_skin(P, SKIN_PALE, hair=BLACK),
    }
    return tide_finish(P, parts, mats, add)


ROWS, frames = tide_rows(neutral_pose, attack_style='swing', weapon_side='r')

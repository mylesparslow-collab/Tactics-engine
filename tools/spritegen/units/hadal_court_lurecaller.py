"""Lurecaller (Hadal Court controller). Lean, stooped, in a long bell-robe; a fleshy lamp-stalk grown
from its own skull arches forward over its face, and it swings it to draw prey in.
Defining detail: the skull lure, the brightest point on the board for the Court.
"""
from _hadal_court_common import *

UNIT_ID = 'hadal_court_lurecaller'
CAMERA = Camera(ppm=50)

C = Costume(top='robe', sleeve='robe', legs='hide', boot='hide', hand='skin', skirt='robe', skirt_mat='robe',
            hem=0.03, flare=1.5, head='bald', belt='chain', girth=0.85)


def neutral_pose():
    P = hpose(1.10, 0.95)
    h = 1.10
    rig.lean(P, fwd=np.radians(12))
    P['head_pitch'] = np.radians(8)
    # left hand raised, palm out, beckoning; right holds a lure-dart low
    rig.place_arm(P, 'l', P['chest'] + v3(0.26, 0.05, 0.25), (1, -0.6, -0.3), l1=0.27 * h, l2=0.26 * h)
    rig.place_arm(P, 'r', P['pelvis'] + v3(-0.22, 0.0, 0.14), (-1, -0.3, -0.4), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(-0.1, -0.4, 1.0))
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    R = frame_for(P)
    # bell cowl on the shoulders
    add(bell_hull(P['neck'] + v3(0, 0.03, -0.02), 0.26, 0.09, 0.27, R=R, power=0.8, sz=0.8, lip=0.02, ribs=0.05,
                  ribs_n=8, open_bottom=True, thick=0.015), 'robe', 0.0)
    H, Rh = P['head'], rot_y(P['head_yaw']) @ rot_x(-P['head_pitch'])
    # ridged skull crest
    for i in range(3):
        add(Ellipsoid(H + Rh @ v3(0, 0.07 - 0.0 * i, -0.03 - 0.035 * i), (0.03, 0.045, 0.04), Rh), 'skin', 0.03)
    sw = np.sin(2 * np.pi * P.get('tell', 0)) * 0.25 + P.get('strike', 0) * 0.0
    swing = rot_y(sw)
    bulb = stalk_lamp(add, H + Rh @ v3(0, 0.08, -0.06), Rh @ v3(0, 1, -0.5),
                      swing @ (Rh @ v3(0, 0.15, 1.0)), 0.26, 0.30, bulb=0.07, mat='skin', r0=0.045, r1=0.018)
    # hanging second stalk segment to the bulb (droop)
    held(P, add, 'r', 'knife', head='iron')
    mats = hadal_mats(P, {
        'skin': Material(face_albedo(P, _hex('#7d82a8'), _hex('#2a2c4a'), eyes=TEAL, lips=_hex('#3a3b5c'), brows=False),
                         spec=0.4, gloss=25, sss=0.5, brush=0.03),
        'robe': Material(cracked_albedo(_hex('#3c4066'), crack=_hex('#1b1d33'), freq=5, width=0.01, mottle=0.2,
                                        patina=_hex('#555a73'), patina_amt=0.3), spec=0.05, brush=0.1),
    }, lamp_gain=1.3)
    lights = [teal_light(bulb, P, 1.3, 0.9)]
    return hadal_finish(P, parts, mats, lights)


ROWS, _fr = humanoid_rows(neutral_pose, attack_style='shoot', weapon_side='r', sink_depth=0.6, cast_side='l')
frames = with_death(_fr, deflate=(0, 0, 0.1, 0.3))

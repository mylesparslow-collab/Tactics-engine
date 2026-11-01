"""Maelis Quell, Hearth-Mother of the Warm Vents (Hadal Court hero). Eldest Vent-Priest: stooped and
broad in a layered bell-robe with a kelp-brown shawl, an old pale face under a domed cowl, a tall
ember-staff topped with a pierced vent-bell brazier, and a small vent-flame cradled in her left hand.
Defining detail: the cradled flame held against the cold (vent amber), one teal bead at her brow.
"""
from _hadal_court_common import *
from sdf import Subtract

UNIT_ID = 'hadal_court_maelis_quell'
CAMERA = Camera(ppm=48)
H_ = 1.08

C = Costume(top='robe', sleeve='robe', legs='hide', boot='hide', hand='skin', skirt='robe', skirt_mat='robe',
            hem=0.02, flare=2.1, head='bald', belt='chain', girth=1.35)


def neutral_pose():
    P = hpose(H_, 1.3)
    rig.lean(P, fwd=np.radians(10))
    P['head_pitch'] = np.radians(10)
    rig.place_arm(P, 'r', P['pelvis'] + v3(-0.36, 0.30, 0.18), (-1, -0.6, -0.4), l1=0.27 * H_, l2=0.26 * H_)
    P['item_r'] = norm(v3(-0.03, 1.0, 0.04))
    rig.place_arm(P, 'l', P['chest'] + v3(0.06, -0.14, 0.26), (1, -0.6, -0.3), l1=0.27 * H_, l2=0.26 * H_)
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    R = frame_for(P)
    nk = P['neck']
    # shawl bell over the shoulders
    add(bell_hull(nk + v3(0, 0.03, -0.02), 0.34, 0.11, 0.36, R=R, power=0.8, sz=0.85, lip=0.02, ribs=0.06, ribs_n=11,
                  open_bottom=True, thick=0.016), 'shawl', 0.0)
    H, Rh = P['head'], rot_y(P['head_yaw']) @ rot_x(-P['head_pitch'])
    add(Subtract(bell_hull(H + Rh[:, 1] * 0.15, 0.27, 0.08, 0.15, R=Rh, power=0.6, open_bottom=True, thick=0.014, lip=0.02),
                 Ellipsoid(H + Rh @ v3(0, -0.03, 0.13), (0.085, 0.12, 0.10), Rh), 0.01), 'robe', 0.0)
    add(Sphere(H + Rh @ v3(0, 0.07, 0.10), 0.016), 'lamp', 0.0)
    # cradled flame in the left hand
    g = hand_pos(P, 'l')
    fl = g + v3(0, 0.08, 0.02)
    flick = 1 + 0.15 * np.sin(2 * np.pi * P.get('tell', 0) * 2)
    add(Ellipsoid(fl, (0.045 * flick, 0.07 * flick, 0.045 * flick)), 'vent', 0.0)
    add(Cylinder(g + v3(0, 0.0, 0.01), g + v3(0, 0.03, 0.01), 0.06, 0.008), 'iron', 0.0)
    # ember staff with a pierced vent-bell brazier
    bt = held(P, add, 'r', 'staff', shaft='wood', head='iron', below=0.95, above=0.62)
    braz = None
    if bt:
        butt, tip = bt
        d = norm(tip - butt)
        braz = tip + d * 0.06
        add(bell_hull(braz + v3(0, 0.13, 0), 0.20, 0.04, 0.10, power=0.9, lip=0.015), 'brazier', 0.0)
        add(Sphere(braz + v3(0, -0.07, 0), 0.075), 'vent', 0.0)
        add(Cylinder(tip - d * 0.02, tip + d * 0.03, 0.05, 0.006), 'iron', 0.0)
    if P['cast_glow'] > 0:
        add(Sphere(fl + v3(0, 0.06, 0), 0.04 + 0.06 * P['cast_glow']), 'vent', 0.0)
    pierce = lambda p, n: np.where((np.abs(np.sin(p[:, 0] * 90) * np.sin(p[:, 1] * 90)) > 0.6)[:, None],
                                   np.array(_hex('#ffb04a'))[None, :], np.array(_hex('#3b3f55'))[None, :])
    mats = hadal_mats(P, {
        'robe': Material(cracked_albedo(_hex('#32365a'), crack=_hex('#1a1c33'), freq=5, width=0.008, mottle=0.2,
                                        patina=_hex('#5c4a3e'), patina_amt=0.3), spec=0.05, brush=0.1),
        'shawl': Material(cracked_albedo(_hex('#4a4536'), crack=_hex('#24221b'), freq=6, width=0.01, mottle=0.25), spec=0.08, brush=0.12),
        'skin': Material(face_albedo(P, _hex('#b9b3bf'), _hex('#d9d6dc'), eyes=_hex('#2a2a3a'), lips=_hex('#8a6f78')),
                         spec=0.15, sss=0.6, brush=0.03),
        'brazier': Material(pierce, spec=0.5, gloss=30, metal=0.4,
                            emissive=lambda p, n: (np.abs(np.sin(p[:, 0] * 90) * np.sin(p[:, 1] * 90)) > 0.6)[:, None]
                            * np.array(_hex('#ffa040'))[None, :] * P['glow'] * (1 - P['end'])),
        'wood': Material(_hex('#3d3a3a'), spec=0.1, brush=0.08),
    }, amber_gain=1.0)
    lights = [Light(fl, _hex('#ffa040'), 1.0 * P['glow'] * flick, 0.6)]
    if braz is not None:
        lights.append(Light(braz, _hex('#ff9a3a'), 1.0 * P['glow'], 0.7))
    lights.append(teal_light(H + Rh[:, 2] * 0.15, P, 0.2, 0.25))
    return hadal_finish(P, parts, mats, lights)


ROWS, _fr = humanoid_rows(neutral_pose, attack_style='swing', weapon_side='r', sink_depth=0.55, cast_side='l')


def frames():
    fr = _fr()
    for i, (P, o) in enumerate(fr['death']):
        P['deflate'] = [0, 0, 0.2, 0.5][i]
    return fr

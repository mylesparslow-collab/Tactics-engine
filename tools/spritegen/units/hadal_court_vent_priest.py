"""Vent-Priest (Hadal Court support). Squat, wide bell-robed priest under a heavy hood, carrying a
portable vent-flame: an iron cage on a crook-staff holding a glowing amber vent stone.
Defining detail: the only warm light in the Court (vent amber), with one teal bead at the throat.
"""
from _hadal_court_common import *

UNIT_ID = 'hadal_court_vent_priest'
CAMERA = Camera(ppm=50)

C = Costume(top='robe', sleeve='robe', legs='hide', boot='hide', hand='skin', skirt='robe', skirt_mat='robe',
            hem=0.02, flare=2.0, head='hood', head_mat='hood', belt='chain', girth=1.3)


def neutral_pose():
    P = hpose(1.05, 1.25)
    h = 1.05
    rig.lean(P, fwd=np.radians(6))
    rig.place_arm(P, 'l', P['pelvis'] + v3(0.30, 0.28, 0.20), (1, -0.6, -0.4), l1=0.27 * h, l2=0.26 * h)
    P['item_l'] = norm(v3(0.02, 1.0, 0.05))
    rig.place_arm(P, 'r', P['chest'] + v3(-0.08, -0.08, 0.22), (-1, -0.5, -0.3), l1=0.27 * h, l2=0.26 * h)
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    R = frame_for(P)
    add(bell_hull(P['neck'] + v3(0, 0.02, -0.02), 0.32, 0.10, 0.33, R=R, power=0.9, sz=0.85, lip=0.02, ribs=0.04,
                  open_bottom=True, thick=0.016), 'hood', 0.0)
    H, Rh = P['head'], rot_y(P['head_yaw']) @ rot_x(-P['head_pitch'])
    add(Ellipsoid(H + Rh @ v3(0, -0.01, 0.06), (0.06, 0.07, 0.03), Rh), 'abyss', 0.0)    # shadowed face
    # crook staff with the vent cage
    bt = held(P, add, 'l', 'staff', shaft='iron', head='iron', below=0.95, above=0.75)
    vent = None
    if bt:
        butt, tip = bt
        d = norm(tip - butt)
        side = norm(np.cross(d, v3(0, 0, 1))) * -1
        hook = tip + side * 0.10 + d * 0.06
        add(Capsule(tip, hook, 0.016), 'iron', 0.0)
        vent = hook - v3(0, 0.15, 0)
        add(Capsule(hook, vent + v3(0, 0.09, 0), 0.008), 'chain', 0.0)
        add(Ellipsoid(vent, (0.05, 0.06, 0.05)), 'vent', 0.0)
        for a in range(4):
            q = vent + rot_y(a * np.pi / 2 + 0.4) @ v3(0.065, 0, 0)
            add(Capsule(q + v3(0, -0.07, 0), q + v3(0, 0.08, 0), 0.008), 'iron', 0.0)
        add(Cylinder(vent + v3(0, 0.075, 0), vent + v3(0, 0.095, 0), 0.075, 0.006), 'iron', 0.0)
        add(Cylinder(vent + v3(0, -0.095, 0), vent + v3(0, -0.07, 0), 0.07, 0.006), 'iron', 0.0)
    if P['cast_glow'] > 0:
        g = hand_pos(P, 'r')
        add(Sphere(g + v3(0, 0.05, 0.03), 0.03 + 0.05 * P['cast_glow']), 'vent', 0.0)
    add(Sphere(P['neck'] + R @ v3(0, -0.05, 0.13), 0.022), 'lamp', 0.0)
    mats = hadal_mats(P, {
        'hood': Material(cracked_albedo(_hex('#3a3e62'), crack=_hex('#1c1e33'), freq=5, width=0.01, mottle=0.2,
                                        patina=_hex('#5a4a40'), patina_amt=0.2), spec=0.05, brush=0.1),
        'robe': Material(cracked_albedo(_hex('#33375a'), crack=_hex('#1c1e33'), freq=5, width=0.01, mottle=0.2,
                                        patina=_hex('#6b5440'), patina_amt=0.25), spec=0.05, brush=0.1),
        'skin': Material(_hex('#7a7fa6'), spec=0.3, sss=0.5),
    }, amber_gain=1.0)
    lights = [teal_light(P['neck'] + v3(0, 0, 0.2), P, 0.3, 0.3)]
    if vent is not None:
        lights.append(Light(vent, _hex('#ffa040'), 1.3 * P['glow'] * (1 + 0.3 * np.sin(6.28 * P.get('tell', 0))), 0.8))
    if P['cast_glow'] > 0:
        lights.append(Light(hand_pos(P, 'r') + v3(0, 0.05, 0.05), _hex('#ffa040'), 1.2 * P['cast_glow'], 0.6))
    return hadal_finish(P, parts, mats, lights)


ROWS, _fr = humanoid_rows(neutral_pose, attack_style='cast', weapon_side='r', sink_depth=0.55, cast_side='r')
frames = with_death(_fr, deflate=(0, 0, 0.2, 0.5))

"""Deep Herald (Hadal Court debuffer). Tall, narrow singer in a tiered bell-cowl robe whose face is a
black void with two teal eyes; carries a herald staff hung with a small bell-lamp. Sings the dark.
Defining detail: the stacked bell-cowl (three nested bells) and the hanging bell-lamp.
"""
from _hadal_court_common import *
from sdf import Subtract

UNIT_ID = 'hadal_court_deep_herald'
CAMERA = Camera(ppm=46)

C = Costume(top='robe', sleeve='robe', legs='robe', boot='hide', hand='skin', skirt='robe', skirt_mat='robe',
            hem=0.02, flare=1.3, head='none', belt=None, girth=0.95)


def neutral_pose():
    P = hpose(1.27, 0.95)
    h = 1.27
    P['head_pitch'] = np.radians(10)
    rig.place_arm(P, 'r', P['pelvis'] + v3(-0.40, 0.22, 0.14), (-1, -0.6, -0.4), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(-0.03, 1.0, 0.06))
    rig.place_arm(P, 'l', P['pelvis'] + v3(0.10, 0.18, 0.22), (1, -0.4, -0.4), l1=0.27 * h, l2=0.26 * h)
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    R = frame_for(P)
    H, Rh = P['head'], rot_y(P['head_yaw']) @ rot_x(-P['head_pitch'])
    # three nested bells: hood, mantle, cape
    add(Subtract(bell_hull(H + Rh[:, 1] * 0.17, 0.30, 0.06, 0.15, R=Rh, power=0.6, sz=0.95, lip=0.015, open_bottom=True, thick=0.014),
                 Ellipsoid(H + Rh @ v3(0, -0.02, 0.13), (0.075, 0.10, 0.08), Rh), 0.01), 'cowl', 0.0)
    add(bell_hull(P['neck'] + v3(0, 0.0, -0.01), 0.20, 0.12, 0.40, R=R, power=0.55, sz=0.85, lip=0.03, open_bottom=True, thick=0.015), 'cowl', 0.0)
    for k in range(7):
        a = -1.6 + k * 0.53
        q = P['neck'] + R @ v3(np.sin(a) * 0.40, -0.24, np.cos(a) * 0.34)
        add(Capsule(q, q - v3(0, 0.06, 0), 0.004), 'chain', 0.0)
        add(bell_hull(q - v3(0, 0.05, 0), 0.05, 0.012, 0.024, power=0.8, lip=0.004), 'bellm', 0.0)
    add(bell_hull(P['chest'] + R[:, 1] * 0.0, 0.32, 0.20, 0.33, R=R, power=0.8, sz=0.85, lip=0.02, ribs=0.05, open_bottom=True, thick=0.015), 'robe', 0.0)
    # void face + teal eyes
    add(Ellipsoid(H + Rh @ v3(0, -0.01, 0.03), (0.075, 0.095, 0.08), Rh), 'abyss', 0.0)
    eyes = [H + Rh @ v3(sx * 0.03, 0.01, 0.10) for sx in (-1, 1)]
    specks(add, eyes, 0.014)
    bt = held(P, add, 'r', 'staff', shaft='iron', head='iron', below=0.95, above=0.85)
    lamp = None
    if bt:
        butt, tip = bt
        d = norm(tip - butt)
        side = norm(np.cross(d, v3(0, 0, 1))) * -1
        arm = tip - d * 0.04 + side * 0.16
        add(Capsule(tip - d * 0.04, arm, 0.013), 'iron', 0.0)
        lamp = arm - v3(0, 0.16, 0) + v3(np.sin(6.28 * P.get('tell', 0)) * 0.02, 0, 0)
        add(Capsule(arm, lamp + v3(0, 0.08, 0), 0.006), 'chain', 0.0)
        add(bell_hull(lamp + v3(0, 0.09, 0), 0.13, 0.035, 0.075, power=0.8, lip=0.01), 'bellm', 0.0)
        add(Sphere(lamp - v3(0, 0.085, 0), 0.045), 'lamp', 0.0)
    # sung darkness: rings around the head during cast
    if P['cast_glow'] > 0:
        for k in range(2):
            add(Torus(H + v3(0, -0.05 - 0.1 * k, 0.0), v3(0, 1, 0.2), 0.18 + 0.12 * k + 0.1 * P['cast_glow'], 0.008), 'speck', 0.0)
    mats = hadal_mats(P, {
        'cowl': Material(cracked_albedo(_hex('#2f3360'), crack=_hex('#14162b'), freq=5, width=0.008, mottle=0.2), spec=0.08, brush=0.1),
        'robe': Material(cracked_albedo(_hex('#272a4e'), crack=_hex('#14162b'), freq=5, width=0.008, mottle=0.2,
                                        patina=_hex('#41465e'), patina_amt=0.3), spec=0.05, brush=0.1),
        'bellm': bell_metal(lamp if lamp is not None else H, np.eye(3), base=_hex('#4d5e52'), spacing=0.05),
        'skin': Material(_hex('#6b6f96'), spec=0.3, sss=0.5),
    })
    lights = [teal_light(H + Rh[:, 2] * 0.15, P, 0.35, 0.35)]
    if lamp is not None:
        lights.append(teal_light(lamp - v3(0, 0.07, 0), P, 1.2, 0.8))
    return hadal_finish(P, parts, mats, lights)


ROWS, _fr = humanoid_rows(neutral_pose, attack_style='swing', weapon_side='r', sink_depth=0.7, cast_side='l')
frames = with_death(_fr, deflate=(0, 0, 0.25, 0.6))

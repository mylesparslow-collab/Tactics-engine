"""Pressure Lancer (Hadal Court ranged). Armoured gunner with a long bored brine-lance braced at the hip,
fed by a pressure tank on its back; twin-port diving helm. Fires shafts of compressed brine.
Defining detail: the long lance barrel and the round tank, teal gauge glowing.
"""
from _hadal_court_common import *

UNIT_ID = 'hadal_court_pressure_lancer'
CAMERA = Camera(ppm=48)

C = Costume(top='brine', sleeve='iron', legs='hide', boot='iron', hand='iron', skirt='robe', skirt_mat='brine',
            hem=0.42, flare=1.0, head='none', belt='chain', girth=1.2)


def neutral_pose():
    P = hpose(1.12, 1.3)
    h = 1.12
    rig.lean(P, fwd=np.radians(4))
    g = P['pelvis'] + v3(-0.22, 0.10, 0.18)
    rig.place_arm(P, 'r', g, (-1, -0.4, -0.5), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(0.45, 0.30, 1.0))
    rig.place_arm(P, 'l', g + P['item_r'] * 0.32, (1, -0.6, -0.2), l1=0.27 * h, l2=0.26 * h)
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    brute_limbs(P, add, 'iron', arm=(0.07, 0.065, 0.06), fist=0.06, leg=None)
    R = frame_for(P)
    add(bell_hull(P['neck'] + R[:, 1] * 0.01, 0.42, 0.16, 0.30, R=R, power=1.2, sz=0.85, lip=0.03), 'bell', 0.04)
    # back tank
    tc = P['chest'] + R @ v3(0, 0.0, -0.26)
    add(Capsule(tc - R[:, 1] * 0.14, tc + R[:, 1] * 0.14, 0.15), 'tank', 0.0)
    add(Torus(tc, R[:, 1], 0.15, 0.014), 'iron', 0.0)
    add(Cylinder(tc + R @ v3(0.12, 0.06, -0.05), tc + R @ v3(0.15, 0.08, -0.06), 0.04, 0.005), 'port', 0.0)
    H, Rh = P['head'] + v3(0, -0.01, 0), rot_y(P['head_yaw']) @ rot_x(-P['head_pitch'])
    dome_helm(add, H, Rh, r=0.15, mat='helm', ports=2)
    # the lance: long bored barrel
    d = P['item_r']
    if d is not None:
        d = norm(d)
        g = hand_pos(P, 'r')
        a, b = g - d * 0.35, g + d * 1.05
        add(Cylinder(a, b, 0.045, 0.01), 'iron', 0.0)
        for t in (0.05, 0.45, 0.85):
            q = a + (b - a) * t
            add(Torus(q, d, 0.05, 0.014), 'band', 0.0)
        add(Cylinder(b - d * 0.02, b + d * 0.04, 0.065, 0.01), 'band', 0.0)
        add(Cylinder(b, b + d * 0.045, 0.035, 0.0), 'abyss', 0.0)
        # hose from tank to breech
        hose_a = tc + R @ v3(-0.12, -0.12, 0.05)
        add(Capsule(hose_a, (hose_a + a) / 2 + v3(0, -0.12, 0), 0.02), 'hide', 0.01)
        add(Capsule((hose_a + a) / 2 + v3(0, -0.12, 0), a, 0.02), 'hide', 0.01)
        if P['fx'] > 0:
            for k in range(3):
                add(Ellipsoid(b + d * (0.12 + 0.18 * k), (0.06 * P['fx'] * (1 - 0.2 * k),) * 3), 'lamp', 0.0)
    mats = hadal_mats(P, {
        'bell': bell_metal(P['neck'], R, base=_hex('#4d5474'), spacing=0.16, patina_amt=0.2),
        'helm': bell_metal(H, Rh, base=_hex('#555c7c'), spacing=0.3, patina_amt=0.3, barn=0),
        'tank': bell_metal(tc, R, base=_hex('#4d5e52'), spacing=0.12, patina=VERDI, patina_amt=0.4),
        'band': Material(_hex('#6a7090'), spec=0.8, gloss=40, metal=0.6),
    })
    lights = [teal_light(H + Rh[:, 2] * 0.2, P, 0.5, 0.45)]
    if P['fx'] > 0 and d is not None:
        lights.append(Light(hand_pos(P, 'r') + norm(P['item_r']) * 1.2, TEAL, 1.5 * P['fx'], 0.9))
    return hadal_finish(P, parts, mats, lights)


ROWS, _fr = humanoid_rows(neutral_pose, attack_style='shoot', weapon_side='r', sink_depth=0.65)
frames = with_death(_fr, deflate=(0, 0, 0.2, 0.5))

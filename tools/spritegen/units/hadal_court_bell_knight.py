"""Bell-Knight (Hadal Court tank). A knight sealed in a brass pressure-bell: the body IS the bell,
domed diving-bell helm with one porthole, teal stalk lamp, a bell-headed maul. Toll crushes adjacent.
Defining detail: the riveted bell hull, wider at the hem than the shoulders.
"""
from _hadal_court_common import *

UNIT_ID = 'hadal_court_bell_knight'
CAMERA = Camera(ppm=44)

C = Costume(top='brine', sleeve='iron', legs='iron', boot='iron', hand='iron', skirt=None, head='none',
            belt=None, girth=1.2)


def neutral_pose():
    P = hpose(1.25, 1.55)
    rig.lean(P, fwd=np.radians(5))
    # maul held low across the body, head resting by the right foot
    rig.place_arm(P, 'r', P['pelvis'] + v3(-0.36, 0.22, 0.26), (-1, -0.5, -0.3), l1=0.27 * 1.25, l2=0.26 * 1.25)
    rig.place_arm(P, 'l', P['pelvis'] + v3(0.30, 0.02, 0.18), (1, -0.4, -0.3), l1=0.27 * 1.25, l2=0.26 * 1.25)
    P['item_r'] = norm(v3(-0.12, 0.85, -0.35))
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    R = frame_for(P)
    top = P['neck'] + R[:, 1] * 0.02
    add(bell_hull(top, P['neck'][1] - 0.42, 0.22, 0.52, R=R, power=1.6, sz=0.85, lip=0.05), 'bell', 0.04)
    # pauldron bells on the shoulders
    for s in ('r', 'l'):
        sx = -1 if s == 'r' else 1
        sh = P['sh_' + s]
        Rs = basis_from(norm(v3(sx * 0.5, 1, 0)), (0, 0, 1))
        add(bell_hull(sh + v3(0, 0.12, 0), 0.24, 0.06, 0.17, R=Rs, power=0.8, sz=1.0, lip=0.025), 'bell', 0.02)
        el, wr = P['el_' + s], P['wr_' + s]
        add(Capsule(el, wr, 0.075, 0.07), 'iron', 0.02)
        add(Sphere(wr + norm(wr - el) * 0.06, 0.07), 'iron', 0.01)
    # helm
    H = P['head'] + v3(0, -0.02, 0)
    Rh = rot_y(P['head_yaw']) @ rot_x(-P['head_pitch'])
    dome_helm(add, H, Rh, r=0.16, mat='helm', ports=1, rim='iron')
    bulb = stalk_lamp(add, H + Rh[:, 1] * 0.13 - Rh[:, 2] * 0.10, Rh[:, 1] - Rh[:, 2] * 0.3, Rh[:, 2] + v3(0, 0.25, 0),
                      0.20, 0.20, bulb=0.05, mat='iron', r0=0.022, r1=0.012)
    # toll chain across the bell
    ch = P['chest']
    for i in range(6):
        t = i / 5
        a = ch + R @ v3(-0.20 + 0.40 * t, -0.08 - 0.16 * np.sin(np.pi * t), 0.24)
        add(Torus(a, v3(1, 0, 0) if i % 2 else v3(0, 0, 1), 0.022, 0.007), 'chain', 0.0)
    # maul: iron haft with a small cast bell as head
    bt = held(P, add, 'r', 'club', shaft='iron', head='iron', below=0.30, above=0.85)
    if bt:
        butt, tip = bt
        d = norm(tip - butt)
        add(bell_hull(tip - d * 0.06, 0.26, 0.08, 0.15, R=basis_from(-d, (0, 0, 1)), power=1.2, lip=0.02), 'iron', 0.0)
        if P['fx'] > 0:
            add(Torus(tip + d * 0.16, v3(0, 1, 0), 0.25 * P['fx'] + 0.1, 0.012), 'speck', 0.0)
    mats = hadal_mats(P, {
        'bell': bell_metal(top, R, base=_hex('#4d5474'), patina_amt=0.3),
        'helm': bell_metal(H, Rh, base=_hex('#555c7c'), spacing=0.09, patina_amt=0.35),
    })
    lights = [teal_light(bulb, P, 1.0, 0.8), teal_light(H + Rh[:, 2] * 0.2, P, 0.3, 0.4)]
    return hadal_finish(P, parts, mats, lights)


ROWS, _fr = humanoid_rows(neutral_pose, attack_style='slam', weapon_side='r', sink_depth=0.75)
frames = with_death(_fr)

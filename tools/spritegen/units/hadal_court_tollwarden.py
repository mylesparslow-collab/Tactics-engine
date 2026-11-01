"""Tollwarden (Hadal Court commander). Magistrate in a heavy bell-robe of plated pressure-iron, a tall
bell-crown helm with a single teal port, chain of office with a toll-seal, and the tollrod: an iron
mace-staff topped with a hanging bell. Defining detail: the bell-crown and the chain of office.
"""
from _hadal_court_common import *

UNIT_ID = 'hadal_court_tollwarden'
CAMERA = Camera(ppm=46)

C = Costume(top='brine', sleeve='robe', legs='hide', boot='iron', hand='iron', skirt='robe', skirt_mat='robe',
            hem=0.30, flare=1.2, head='none', belt='chain', girth=1.3)


def neutral_pose():
    P = hpose(1.15, 1.5)
    h = 1.15
    P['head_pitch'] = np.radians(-4)
    rig.place_arm(P, 'r', P['pelvis'] + v3(-0.44, 0.14, 0.12), (-1, -0.5, -0.4), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(-0.08, 1.0, 0.12))
    rig.place_arm(P, 'l', P['pelvis'] + v3(0.20, 0.12, 0.20), (1, -0.4, -0.4), l1=0.27 * h, l2=0.26 * h)
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    brute_limbs(P, add, 'robe', arm=(0.075, 0.07, 0.06), fist=0.055, leg=None, hand_mat='iron')
    R = frame_for(P)
    add(bell_hull(P['neck'] + R[:, 1] * 0.0, 0.62, 0.24, 0.44, R=R, power=0.9, sz=0.85, lip=0.03), 'bell', 0.03)
    for s_ in ('r', 'l'):
        sx = -1 if s_ == 'r' else 1
        Rs = basis_from(norm(v3(sx * 0.6, 1, 0)), (0, 0, 1))
        add(bell_hull(P['sh_' + s_] + v3(0, 0.12, 0), 0.22, 0.06, 0.17, R=Rs, power=0.8, lip=0.02), 'bellg', 0.02)
    # chain of office with toll-seal
    nk = P['neck']
    for i in range(7):
        t = i / 6
        q = nk + R @ v3(-0.17 + 0.34 * t, -0.06 - 0.17 * np.sin(np.pi * t), 0.17 + 0.05 * np.sin(np.pi * t))
        add(Torus(q, v3(1, 0, 0) if i % 2 else v3(0, 0, 1), 0.02, 0.007), 'brass', 0.0)
    seal = nk + R @ v3(0, -0.28, 0.24)
    add(Cylinder(seal - R[:, 2] * 0.01, seal + R[:, 2] * 0.015, 0.05, 0.006), 'bellg', 0.0)
    add(Sphere(seal + R[:, 2] * 0.02, 0.016), 'lamp', 0.0)
    # bell-crown helm
    H, Rh = P['head'], rot_y(P['head_yaw']) @ rot_x(-P['head_pitch'])
    dome_helm(add, H, Rh, r=0.14, mat='helm', ports=1)
    add(bell_hull(H + Rh[:, 1] * 0.40, 0.28, 0.05, 0.16, R=Rh, power=1.3, sz=1.0, lip=0.02), 'bellg', 0.0)
    add(Sphere(H + Rh[:, 1] * 0.42, 0.03), 'lamp', 0.0)
    # tollrod
    bt = held(P, add, 'r', 'staff', shaft='iron', head='iron', below=0.9, above=0.62)
    if bt:
        butt, tip = bt
        d = norm(tip - butt)
        add(Sphere(tip, 0.045), 'iron', 0.0)
        add(bell_hull(tip - d * 0.03, 0.15, 0.04, 0.09, R=basis_from(d, (0, 0, 1)), power=1.0, lip=0.015), 'bellg', 0.0)
        add(Sphere(tip - d * 0.17, 0.022), 'lamp', 0.0)
    mats = hadal_mats(P, {
        'bell': bell_metal(nk, R, base=_hex('#4a5070'), spacing=0.12, patina_amt=0.2),
        'helm': bell_metal(H, Rh, base=_hex('#555c7c'), spacing=0.3, barn=0),
        'bellg': bell_metal(H, Rh, base=BRONZE, band=_hex('#36443c'), spacing=0.07, patina_amt=0.45, barn=0),
        'brass': Material(_hex('#6f7a6a'), spec=0.8, gloss=40, metal=0.8),
        'robe': Material(cracked_albedo(_hex('#2c3058'), crack=_hex('#14162b'), freq=5, width=0.008, mottle=0.2), spec=0.06, brush=0.1),
    })
    lights = [teal_light(H + Rh[:, 2] * 0.2, P, 0.4, 0.4), teal_light(seal + R[:, 2] * 0.1, P, 0.4, 0.4, phase=0.3)]
    if bt:
        lights.append(teal_light(bt[1], P, 0.6, 0.5, phase=0.6))
    return hadal_finish(P, parts, mats, lights)


ROWS, _fr = humanoid_rows(neutral_pose, attack_style='swing', weapon_side='r', sink_depth=0.7)
frames = with_death(_fr, deflate=(0, 0, 0.3, 0.7))

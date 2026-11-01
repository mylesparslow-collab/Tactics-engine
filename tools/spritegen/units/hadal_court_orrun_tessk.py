"""Orrun Tessk, Knight-Unrelieved of the Seventh Watch (Hadal Court hero). A Bell-Knight who never left
his post: heavier, older bell hull split by a great crack leaking teal light, a ragged watch-cloak, a
watch lamp hung from the shoulder and a long hookblade planted beside him in anchor stance.
Defining detail: the cracked, still-tolling bell glowing from inside.
"""
from _hadal_court_common import *

UNIT_ID = 'hadal_court_orrun_tessk'
CAMERA = Camera(ppm=44)
H_ = 1.27

C = Costume(top='brine', sleeve='iron', legs='iron', boot='iron', hand='iron', skirt=None, head='none',
            belt=None, girth=1.2)


def neutral_pose():
    P = hpose(H_, 1.6)
    rig.lean(P, fwd=np.radians(3))
    # anchor stance: wide feet, blade planted at his right, both hands on the pommel
    rig.place_leg(P, 'r', P['an_r'] + v3(-0.08, 0, -0.04), l1=0.43 * H_, l2=0.42 * H_)
    rig.place_leg(P, 'l', P['an_l'] + v3(0.08, 0, 0.04), l1=0.43 * H_, l2=0.42 * H_)
    g = P['pelvis'] + v3(-0.42, 0.18, 0.30)
    rig.place_arm(P, 'r', g, (-1, -0.4, -0.3), l1=0.27 * H_, l2=0.26 * H_)
    rig.place_arm(P, 'l', g + v3(0.06, 0.08, 0.0), (1, -0.5, -0.4), l1=0.27 * H_, l2=0.26 * H_)
    P['item_r'] = norm(v3(-0.05, -1.0, 0.08))
    return P


def crack_fn(R, top):
    """Emissive along one big jagged crack running down the bell front-left."""
    def emis(p, n):
        q = (p - top) @ R
        y = -q[:, 1]
        ang = np.arctan2(q[:, 0], q[:, 2])
        path = 0.35 + 0.12 * np.sin(y * 9.0) + 0.05 * np.sin(y * 23.0)
        w = np.exp(-((ang - path) / 0.05) ** 2) * (y > 0.08) * (y < 1.15)
        return np.array(TEAL)[None, :] * (w * 1.4 * GLOW[0])[:, None]
    return emis


GLOW = [1.0]


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    R = frame_for(P)
    top = P['neck'] + R[:, 1] * 0.03
    GLOW[0] = max(pulse(P), 0) * (1 - P['end'])
    add(bell_hull(top, P['neck'][1] - 0.36, 0.24, 0.56, R=R, power=1.5, sz=0.85, lip=0.06), 'bell', 0.04)
    for s in ('r', 'l'):
        sx = -1 if s == 'r' else 1
        sh = P['sh_' + s]
        Rs = basis_from(norm(v3(sx * 0.5, 1, 0)), (0, 0, 1))
        add(bell_hull(sh + v3(0, 0.13, 0), 0.25, 0.06, 0.18, R=Rs, power=0.8, sz=1.0, lip=0.025), 'bell', 0.02)
        el, wr = P['el_' + s], P['wr_' + s]
        add(Capsule(el, wr, 0.075, 0.07), 'iron', 0.02)
        add(Sphere(wr + norm(wr - el) * 0.06, 0.07), 'iron', 0.01)
    # ragged watch cloak down the back
    def cloak(p, top=top, R=R):
        q = (p - top) @ R
        y = -q[:, 1]
        t = np.clip(y / 1.2, 0, 1)
        r = 0.30 + 0.32 * t ** 1.3
        rad = np.sqrt(q[:, 0] ** 2 + (q[:, 2] / 0.85) ** 2)
        d = np.abs(rad - r - 0.03) - 0.012
        d = np.maximum(d, q[:, 2] + 0.05)                 # back half only
        hem = 1.05 + 0.08 * np.sin(np.arctan2(q[:, 0], q[:, 2]) * 11) + 0.04 * np.sin(q[:, 0] * 37)
        return np.maximum(d, np.maximum(-y + 0.02, y - hem))
    add(Func(cloak, top - R[:, 1] * 0.6, 0.95), 'cloak', 0.0)
    # helm with crest, single port
    H = P['head'] + v3(0, -0.02, 0)
    Rh = rot_y(P['head_yaw']) @ rot_x(-P['head_pitch'])
    dome_helm(add, H, Rh, r=0.165, mat='helm', ports=1, rim='iron', crest=True)
    # watch lamp hanging from the left pauldron
    lamp = P['sh_l'] + v3(0.12, -0.18, 0.12) + v3(np.sin(6.28 * P.get('tell', 0)) * 0.01, 0, 0)
    add(Capsule(P['sh_l'] + v3(0.10, 0.0, 0.08), lamp + v3(0, 0.07, 0), 0.006), 'chain', 0.0)
    lantern(add, lamp, frame='iron', glass='lamp', size=1.1)
    # hookblade
    bt = held(P, add, 'r', 'blade', head='iron', below=0.2, above=1.0)
    if bt:
        butt, tip = bt
        d = norm(tip - butt)
        side = norm(np.cross(d, v3(0, 1, 0.3)))
        c = tip - d * 0.06 + side * 0.08
        add(Torus(c, np.cross(d, side), 0.08, 0.016), 'steel', 0.0)
        add(Capsule(tip - d * 0.75, tip - d * 0.1, 0.03, 0.02), 'steel', 0.01)
        if P['fx'] > 0:
            add(Torus(tip, v3(0, 1, 0), 0.15 + 0.2 * P['fx'], 0.012), 'speck', 0.0)
    m_bell = bell_metal(top, R, base=_hex('#4a5070'), patina_amt=0.35, barn=0.4)
    m_bell.emissive = crack_fn(R, top)
    mats = hadal_mats(P, {
        'bell': m_bell,
        'helm': bell_metal(H, Rh, base=_hex('#555c7c'), spacing=0.09, patina_amt=0.4),
        'cloak': Material(cracked_albedo(_hex('#2a2d4c'), crack=_hex('#12142a'), freq=5, width=0.01, mottle=0.25,
                                         patina=_hex('#3e5058'), patina_amt=0.3), spec=0.04, brush=0.12),
        'steel': Material(_hex('#8a93a6'), spec=0.9, gloss=50, metal=0.6),
    })
    lights = [teal_light(lamp, P, 1.0, 0.8), teal_light(top + R @ v3(0.15, -0.5, 0.45), P, 0.5, 0.6, phase=0.3)]
    return hadal_finish(P, parts, mats, lights)


ROWS, _fr = humanoid_rows(neutral_pose, attack_style='swing', weapon_side='r', sink_depth=0.75)
frames = with_death(_fr, deflate=(0, 0, 0.35, 0.8))

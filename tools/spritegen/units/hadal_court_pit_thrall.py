"""Pit Thrall (Hadal Court cheap body). Brine-grown labourer: slouched forward dragging a pressure-weight
on a chain, crude open bell-helm with an eye-slit, brine-slick hide. One and a half humans.
Defining detail: one dim teal lamp bulb on its helm, flickering.
"""
from _hadal_court_common import *

UNIT_ID = 'hadal_court_pit_thrall'
CAMERA = Camera(ppm=48)

C = Costume(top='hide', sleeve='hide', legs='hide', boot='hide', hand='hide', skin='hide', skirt='robe',
            skirt_mat='robe', hem=0.52, flare=0.7, head='none', belt='chain', boots_tall=False, girth=1.3)


def neutral_pose():
    P = hpose(1.12, 1.45)
    h = 1.12
    dn = v3(0, -0.10, 0)
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + rig.UPPER, dn)
    rig.place_leg(P, 'r', P['an_r'] + v3(-0.04, 0, -0.04), l1=0.43 * h, l2=0.42 * h, pole=(-0.4, 0, 1))
    rig.place_leg(P, 'l', P['an_l'] + v3(0.05, 0, 0.0), l1=0.43 * h, l2=0.42 * h, pole=(0.4, 0, 1))
    rig.lean(P, fwd=np.radians(22))
    P['head_pitch'] = np.radians(-14)
    rig.place_arm(P, 'r', P['pelvis'] + v3(-0.36, -0.22, 0.12), (-1, 0, -0.5), l1=0.27 * h * 1.1, l2=0.26 * h * 1.1)
    rig.place_arm(P, 'l', P['pelvis'] + v3(0.30, -0.18, 0.28), (1, 0, -0.5), l1=0.27 * h * 1.1, l2=0.26 * h * 1.1)
    P['item_r'] = norm(v3(-0.25, -0.55, -0.6))      # chain trailing behind to the weight
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    brute_limbs(P, add, 'hide', arm=(0.09, 0.075, 0.07), fist=0.08, leg=(0.10, 0.075))
    R = frame_for(P)
    # hunched back mass
    add(Ellipsoid(P['chest'] + R @ v3(0, -0.02, -0.07), (0.30, 0.20, 0.20), R), 'hide', 0.06)
    # crude bell-helm (open bottom, sits over the head down to the neck)
    H = P['head']
    Rh = rot_y(P['head_yaw']) @ rot_x(-P['head_pitch'])
    add(bell_hull(H + Rh[:, 1] * 0.16, 0.30, 0.11, 0.19, R=Rh, power=0.7, sz=0.95, lip=0.025), 'helm', 0.0)
    add(RoundBox(H + Rh @ v3(0, -0.01, 0.165), (0.09, 0.012, 0.02), 0.006, Rh), 'abyss', 0.0)
    bulb = stalk_lamp(add, H + Rh[:, 1] * 0.16, Rh[:, 1] + Rh[:, 2] * 0.6, Rh[:, 2] + v3(0, -0.1, 0),
                      0.07, 0.07, bulb=0.035, mat='iron', r0=0.014, r1=0.009)
    # chain from the right fist to a dragged pressure-weight
    if P['item_r'] is not None:
        g = hand_pos(P, 'r')
        w = g + norm(P['item_r']) * 0.62
        w[1] = max(w[1], 0.11)
        chain_links(add, g, w, n=7, r=0.024)
        add(bell_hull(w + v3(0, 0.11, 0), 0.2, 0.05, 0.12, power=0.8, lip=0.015), 'iron', 0.0)
    if P['fx'] > 0:
        add(Torus(v3(0, 0.02, 0.45), v3(0, 1, 0), 0.15 + 0.2 * P['fx'], 0.014), 'speck', 0.0)
    flick = [1.0, 0.45, 1.1, 0.7][int(P.get('tell', 0) * 4) % 4]
    mats = hadal_mats(P, {
        'helm': bell_metal(H, Rh, base=_hex('#5d6584'), spacing=0.15, patina_amt=0.4, barn=0.0),
        'lamp': Material(TEAL, emissive=tuple(np.array(TEAL) * 1.0 * flick * max(pulse(P), 0)), rim=0.0),
    })
    lights = [teal_light(bulb, P, 0.6 * flick, 0.5)]
    return hadal_finish(P, parts, mats, lights)


ROWS, _fr = humanoid_rows(neutral_pose, attack_style='slam', weapon_side='r', sink_depth=0.7)


def frames():
    fr = _fr()
    for i, (P, o) in enumerate(fr['attack']):
        P['item_r'] = None          # drops the chain to slam with both fists
    for i, (P, o) in enumerate(fr['death']):
        P['deflate'] = [0, 0, 0.1, 0.3][i]
    return fr

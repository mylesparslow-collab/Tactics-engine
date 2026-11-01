"""Herald Vhaal, the Third Bell (Hadal Court hero). A giant envoy wearing a brass-green bell as robe
and crown: cracked glaze, teal light seeping through the cracks, a heavy clapper hanging on a chain at
her front. Perfectly still, hands folded, head inclined, polite. A lamp-lure on a stalk from her crown
hangs before her face. Defining detail: the lure lamp in front of a calm, pale face.
"""
from _hadal_court_common import *
from sdf import Subtract

UNIT_ID = 'hadal_court_herald_vhaal'
CAMERA = Camera(ppm=44)

C = Costume(top='robe', sleeve='robe', legs='robe', boot='hide', hand='skin', skirt=None, head='bald',
            belt=None, girth=1.0)
H_ = 1.28


def neutral_pose():
    P = hpose(H_, 1.15)
    P['head_pitch'] = np.radians(14)       # head inclined
    P['head_yaw'] = np.radians(-6)
    c = P['chest'] + v3(0, -0.12, 0.24)
    rig.place_arm(P, 'r', c + v3(-0.04, 0, 0), (-1, -0.5, -0.4), l1=0.27 * H_, l2=0.26 * H_)
    rig.place_arm(P, 'l', c + v3(0.04, 0.02, 0.01), (1, -0.5, -0.4), l1=0.27 * H_, l2=0.26 * H_)
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    R = frame_for(P)
    nk = P['neck']
    # the great bell robe, flared collar
    add(bell_hull(nk + R[:, 1] * 0.02, nk[1] + 0.02, 0.18, 0.62, R=R, power=1.9, sz=0.85, lip=0.07, ribs=0.02, ribs_n=12),
        'bell', 0.02)
    add(Torus(nk + R[:, 1] * 0.0, R[:, 1], 0.17, 0.035), 'bellg', 0.02)
    add(bell_hull(nk + R[:, 1] * 0.05, 0.22, 0.15, 0.33, R=R, power=0.7, sz=0.85, lip=0.03, open_bottom=True, thick=0.018), 'bellg', 0.0)
    # sleeves as small bells over the folded arms
    for s in ('r', 'l'):
        el, wr = P['el_' + s], P['wr_' + s]
        add(bell_hull(el + norm(el - wr) * 0.06, np.linalg.norm(wr - el) * 0.85, 0.06, 0.12, R=basis_from(norm(el - wr), (0, 1, 0)),
                      power=1.0, lip=0.015, open_bottom=True, thick=0.012), 'bellg', 0.0)
    # clapper on its chain from the folded hands
    g = (hand_pos(P, 'r') + hand_pos(P, 'l')) / 2
    clap = v3(0.0, 0.62 * H_, 0.42)
    chain_links(add, g, clap + v3(0, 0.08, 0), n=7, r=0.02)
    add(Sphere(clap, 0.09), 'iron', 0.0)
    add(Capsule(clap, clap + v3(0, 0.10, 0), 0.04), 'iron', 0.0)
    # head, crown bell, lure
    H, Rh = P['head'], rot_y(P['head_yaw']) @ rot_x(-P['head_pitch'])
    add(bell_hull(H + Rh[:, 1] * 0.25, 0.24, 0.05, 0.13, R=Rh, power=0.9, lip=0.02), 'bellg', 0.0)
    add(Subtract(bell_hull(H + Rh[:, 1] * 0.12, 0.26, 0.09, 0.15, R=Rh, power=0.7, open_bottom=True, thick=0.012, lip=0.02),
                 Ellipsoid(H + Rh @ v3(0, -0.03, 0.14), (0.095, 0.14, 0.11), Rh), 0.01), 'bellg', 0.0)
    sw = np.sin(2 * np.pi * P.get('tell', 0)) * 0.015
    base = H + Rh[:, 1] * 0.27
    a = base + Rh @ v3(0, 0.12, 0.12)
    b = H + Rh @ v3(0, 0.10, 0.30)
    seg_limb(add, [base, a, b], [0.018, 0.014, 0.01], 'bellg', joint=None)
    lure = b + v3(sw, -0.16, 0)
    add(Capsule(b, lure + v3(0, 0.04, 0), 0.005), 'chain', 0.0)
    add(Sphere(lure, 0.04), 'lamp', 0.0)
    if P['cast_glow'] > 0:
        add(Torus(P['chest'] + v3(0, 0, 0.1), v3(0, 1, 0.3), 0.5 + 0.2 * P['cast_glow'], 0.012), 'speck', 0.0)
    mats = hadal_mats(P, {
        'bell': bell_metal(nk, R, base=_hex('#46574c'), band=_hex('#2e3b34'), spacing=0.28, patina=VERDI, patina_amt=0.4, barn=0.15),
        'bellg': bell_metal(H, Rh, base=_hex('#52665a'), band=_hex('#344239'), spacing=0.16, patina=VERDI, patina_amt=0.4, barn=0),
        'skin': Material(face_albedo(P, _hex('#c5c8d8'), _hex('#4a4d68'), eyes=_hex('#1d2a3a'), lips=_hex('#6f6a86')),
                         spec=0.2, gloss=20, sss=0.6, brush=0.02),
        'robe': Material(_hex('#2c3058'), spec=0.05),
    }, lamp_gain=1.3)
    lights = [teal_light(lure, P, 1.3, 0.8), teal_light(P['chest'] + v3(0, -0.3, 0.6), P, 0.25, 0.7, phase=0.5)]
    return hadal_finish(P, parts, mats, lights)


ROWS, _fr = humanoid_rows(neutral_pose, attack_style='cast', weapon_side='r', sink_depth=0.8, cast_side='l')


def frames():
    fr = _fr()
    for i, (P, o) in enumerate(fr['move']):
        pass
    for i, (P, o) in enumerate(fr['death']):
        P['deflate'] = [0, 0.05, 0.35, 0.75][i]
    return fr

"""Silt-Weaver (Hadal Court, terrain controller). A tall, slight Court weaver in a plain abyss robe and a
small domed helm with gill-slits; from the helm and shoulders long translucent gill-veils stream down and
out behind, trailing trench silt that puffs up around her feet. Defining detail: the long gill-veils
dragging silt.
"""
from _hadal_court_w2 import *

UNIT_ID = 'hadal_court_silt_weaver'
CAMERA = Camera(ppm=46)

C = Costume(top='robe', sleeve='robe', legs='hide', boot='hide', hand='skin', skin='skin', skirt='robe',
            skirt_mat='robe', hem=0.08, flare=1.5, head='none', belt='cord', boots_tall=False, girth=0.88)


def neutral_pose():
    P = hpose(1.18, 0.86)
    h = 1.18
    rig.lean(P, fwd=np.radians(4))
    P['head_pitch'] = np.radians(8)
    # hands open at the waist, as if drawing thread
    rig.place_arm(P, 'r', P['pelvis'] + v3(-0.30, 0.20, 0.26), (-1, -0.5, -0.4), l1=0.27 * h, l2=0.26 * h)
    rig.place_arm(P, 'l', P['pelvis'] + v3(0.30, 0.22, 0.26), (1, -0.5, -0.4), l1=0.27 * h, l2=0.26 * h)
    P['veil'] = 0.0
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    R = frame_for(P)
    h = P['height']
    tl = P['tell']
    nk, H = P['neck'], P['head']
    Rh = rot_y(P['head_yaw']) @ rot_x(-P['head_pitch'])
    lift = 0.35 * P['cast_glow'] + 0.2 * P['veil']
    # shoulder yoke of layered robe cloth, narrow and drooping (not a bell)
    add(Ellipsoid(nk + v3(0, -0.07, -0.01), (0.25, 0.07, 0.15), R), 'robe', 0.03)
    add(Torus(nk + v3(0, -0.03, 0.0), R[:, 1], 0.095, 0.03), 'robe', 0.02)
    # sleeves: long hanging sleeve-mouths
    for s in ('r', 'l'):
        el, wr = P['el_' + s], P['wr_' + s]
        a = el + (wr - el) * 0.4
        b = wr + v3(0, -0.15, 0.02)
        add(Capsule(a, b, 0.052, 0.08), 'robe', 0.03)
    # helm: small dome with gill slits and a bell-metal collar
    add(Ellipsoid(H + Rh[:, 1] * 0.01, (0.115, 0.135, 0.12), Rh), 'helm', 0.0)
    add(Cylinder(H - Rh[:, 1] * 0.09, H - Rh[:, 1] * 0.05, 0.12, 0.012), 'iron', 0.02)
    add(RoundBox(H + Rh @ v3(0, 0.0, 0.112), (0.065, 0.018, 0.018), 0.01, Rh), 'abyss', 0.0)
    specks(add, [H + Rh @ v3(sx * 0.035, 0.0, 0.122) for sx in (-1, 1)], 0.011)
    for sx in (-1, 1):
        for k in range(3):
            add(RoundBox(H + Rh @ v3(sx * 0.108, -0.035 + k * 0.032, 0.02), (0.012, 0.010, 0.05), 0.004, Rh), 'abyss', 0.0)
    add(Capsule(H + Rh[:, 1] * 0.11, H + Rh @ v3(0, 0.12, -0.12), 0.012, 0.008), 'iron', 0.01)
    # gill-veils: a fan of ribbons from the helm sides and shoulders, trailing behind and to the ground
    tips = []
    veils = [(-1.0, 0.62, 0), (-0.65, 0.85, 1), (-0.3, 1.05, 2), (0.0, 0.9, 3), (0.3, 1.05, 4), (0.65, 0.85, 5), (1.0, 0.62, 6)]
    lat = v3(0.8, 0, 0.6)
    for ln, L, k in veils:
        root = H + Rh @ v3(np.sign(ln) * 0.10, -0.02, -0.05) + lat * ln * 0.05
        d0 = norm(v3(0, -1.0, -0.12 + 0.5 * lift) + lat * ln * 0.8)
        tip = ribbon(add, root, d0, L * 1.3 * h, tl + k * 0.31, 'veil' if k % 2 else 'veil2', n=9, w0=0.075, w1=0.05, thick=0.016,
                     sway=0.22, drift=(0, -1.0, -0.15), k=0.012)
        tips.append(tip)
    # long shoulder-veils dragging on the floor
    for sx, k in ((-1, 7), (1, 8)):
        root = P['sh_' + ('r' if sx < 0 else 'l')] + v3(sx * 0.02, 0.02, -0.08)
        tip = ribbon(add, root, norm(v3(sx * 0.5, -0.8, -0.8)), 1.1 * h, tl + k * 0.27, 'veil', n=9, w0=0.085, w1=0.08,
                     thick=0.014, sway=0.09, drift=(0, -1.0, -0.3), k=0.012)
        tips.append(tip)
    # silt: dust the veil tips drag through
    for j, tp in enumerate(tips):
        q = v3(tp[0], 0.03, tp[2])
        silt_puff(add, q, 0.06 + 0.02 * (j % 3) + 0.04 * P['cast_glow'], 'silt', n=3, seed=j, lift=0.02 + 0.05 * P['cast_glow'])
    for k in range(7):
        a = (k * 0.9 + tl * 6.28) % 6.28
        r_ = 0.35 + 0.1 * (k % 3)
        q = v3(np.cos(a) * r_, 0.10 + 0.4 * ((tl + k * 0.17) % 1.0), -0.2 + np.sin(a) * r_ * 0.8)
        add(Sphere(q, 0.014), 'silt', 0.0)
    # silt cloud swelling underfoot on cast
    if P['cast_glow'] > 0:
        cg = P['cast_glow']
        for k in range(8):
            a = k * 0.785
            q = v3(np.cos(a) * 0.5 * cg, 0.05 + 0.02 * (k % 3), 0.2 + np.sin(a) * 0.45 * cg)
            add(Ellipsoid(q, (0.10 + 0.03 * cg, 0.05, 0.10 + 0.03 * cg)), 'silt', 0.04)
    # fingerless thread-drawing hands: hair-fine teal threads between them
    a, b = hand_pos(P, 'r'), hand_pos(P, 'l')
    if np.linalg.norm(b - a) > 0.12:
        for j in range(3):
            m = (a + b) / 2 + v3(0, -0.04 * (j - 1) * 1.5 + 0.02 * np.sin(tl * 6.28 + j), 0.0)
            add(Capsule(a, m, 0.005), 'speck', 0.0)
            add(Capsule(m, b, 0.005), 'speck', 0.0)
    if P['fx'] > 0:
        add(Torus(v3(0, 0.03, 0.5), v3(0, 1, 0), 0.2 + 0.3 * P['fx'], 0.02), 'silt', 0.0)
    mats = hadal_mats(P, {
        'robe': Material(cracked_albedo(_hex('#2c3058'), crack=_hex('#14162b'), freq=5, width=0.008, mottle=0.2), spec=0.06, brush=0.1),
        'helm': bell_metal(H, Rh, base=_hex('#5a6280'), spacing=0.12, patina_amt=0.4, barn=0.0),
        'veil': Material(lambda p, n: np.array(_hex('#8f93c4'))[None, :] * (0.78 + 0.35 * fbm(p, 20, 2)[:, None])
                         + np.array(TEAL)[None, :] * 0.10 * (fbm(p + 4, 30, 1)[:, None] > 0.6), spec=0.3, gloss=26, sss=0.6, brush=0.06,
                         emissive=tuple(np.array(TEAL) * 0.05 * max(pulse(P), 0))),
        'veil2': Material(lambda p, n: np.array(_hex('#5d5f9a'))[None, :] * (0.8 + 0.3 * fbm(p, 20, 2)[:, None]), spec=0.3, gloss=26, sss=0.5, brush=0.06),
        'silt': silt_mat(),
        'skin': Material(cracked_albedo(_hex('#7b80ac'), crack=_hex('#2a2c4a'), freq=7, width=0.02), spec=0.4, gloss=25, sss=0.4, brush=0.03),
        'cord': Material(_hex('#a9a593'), spec=0.1, brush=0.08),
    })
    lights = [teal_light(H + Rh[:, 2] * 0.18, P, 0.4, 0.4)]
    if P['cast_glow'] > 0:
        lights.append(Light(hand_pos(P, 'r') + v3(0, 0.05, 0.1), TEAL, 0.9 * P['cast_glow'], 0.4))
    return hadal_finish(P, parts, mats, lights)


def _post(fr):
    for i, (P, o) in enumerate(fr['attack']):
        P['veil'] = [0, 0.4, 1.0, 0.4][i]
    for i, (P, o) in enumerate(fr['death']):
        P['deflate'] = 0.0
    return fr


ROWS, _fr = humanoid_rows(neutral_pose, attack_style='cast', weapon_side='r', sink_depth=0.7, cast_side='l')


def frames():
    return _post(_fr())

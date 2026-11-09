"""Salt-Drinker (Returning Tide, sacrifice fodder). A penitent who swallowed brine until it killed him and
kept walking: head thrown back, a salt-crusted tin cup at his mouth with brine running down his chin, a
belly swollen taut and glossy as a waterskin, salt crystals blooming over shoulders, belly and knees.
Defining detail: the white salt-crusted belly about to burst, and the cup.
"""
from _returning_tide_w2 import *
from render import Camera

UNIT_ID = 'returning_tide_salt_drinker'
CAMERA = Camera(ppm=54)

C = Costume(top='shift', sleeve='shift', legs='skin', boot='skin', hand='skin', skin='skin',
            skirt=None, head='bald', belt=None, boots_tall=False, girth=1.05)


def neutral_pose():
    P = base_pose(height=0.97, build=0.95)
    h = 0.97
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + rig.UPPER, v3(0, -0.03, 0))
    rig.place_leg(P, 'l', (0.20, 0.085, 0.08), l1=0.43 * h, l2=0.42 * h, pole=(0.5, 0, 1))
    rig.place_leg(P, 'r', (-0.20, 0.085, -0.04), l1=0.43 * h, l2=0.42 * h, pole=(-0.5, 0, 1))
    rig.lean(P, fwd=np.radians(-4))
    P['head_pitch'] = np.radians(-12)
    rig.shift(P, ('head',), v3(0, 0.04, 0.05))
    rig.place_arm(P, 'r', P['head'] + v3(-0.10, -0.12, 0.20), (-1, -0.7, 0.2), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(0.1, 0.9, 0.2))
    rig.place_arm(P, 'l', P['pelvis'] + v3(0.26, 0.10, 0.22), (1, -0.4, -0.3), l1=0.27 * h, l2=0.26 * h)
    P['belly'] = 1.0
    return P


def build(P):
    parts, add = new_parts()
    pel, ch, nk, H = P['pelvis'], P['chest'], P['neck'], P['head']
    h = P['height']
    R = frame_for(P)
    Rh = head_R(P)
    tl = P['tell']
    bl = P['belly']
    body(P, add, C)
    # the swollen belly: a taut glossy jug of a paunch, slosh driven by the tell
    slosh = 1 + 0.025 * np.sin(2 * np.pi * tl * 2) + 0.03 * P['breathe']
    bc = pel + R @ v3(0, 0.05, 0.13 * bl ** 0.5)
    rb = 0.195 * bl ** 0.55 * slosh
    add(Ellipsoid(bc, (rb * 1.08, rb * 1.12, rb * 1.0), R), 'belly', 0.07)
    add(Ellipsoid(ch + R @ v3(0, -0.03, 0.03), (0.20, 0.17, 0.15), R), 'skin', 0.06)
    # rope tied under the belly, cutting in
    add(Torus(bc + R @ v3(0, -0.15 * bl ** 0.4, -0.02), R[:, 1], rb * 0.92, 0.014), 'cord', 0.0)
    # rags: short salt-stiff shift hanging from the shoulders over the back and hips
    add(ragged_robe(P, hem=0.46, flare=0.5, top=0.90, rag=1.6, seed=7.1, droop=0.1, girth=1.15, depth=1.25), 'shift', 0.0)
    for sx in (-1, 1):
        add(Capsule(nk + v3(sx * 0.10, -0.01, -0.01), pel + v3(sx * 0.15, 0.04, -0.12), 0.026), 'shift', 0.02)
    # thick forearms: bare, swollen, crusted
    for s in ('r', 'l'):
        add(Capsule(P['sh_' + s], P['el_' + s], 0.062, 0.054), 'skin', 0.03)
        add(Capsule(P['el_' + s], P['wr_' + s], 0.054, 0.046), 'skin', 0.03)
    # the tin cup at the mouth and the streams from it and from the lips
    g = hand_pos(P, 'r')
    cup = g + v3(0.0, 0.05, 0.03)
    Rcup = basis_from(norm(H + Rh @ v3(0, -0.05, 0.1) - cup) + v3(0, 0.6, 0), (0, 0, 1))
    add(Cylinder(cup - Rcup[:, 1] * 0.045, cup + Rcup[:, 1] * 0.05, 0.042, 0.01), 'tin', 0.0)
    add(Torus(cup + Rcup[:, 1] * 0.05, Rcup[:, 1], 0.040, 0.007), 'tin', 0.0)
    lips = H + Rh @ v3(0, -0.063, 0.092) * h
    for k in range(3):
        t = k / 3
        q = lips + v3(-0.01 * k, -0.05 * (k + 1) - 0.03 * np.sin(2 * np.pi * (tl + k * 0.3)), 0.03 + 0.015 * k)
        add(Capsule(lips if k == 0 else q + v3(0, 0.05, 0), q, 0.011, 0.009), 'water', 0.01)
    stream(add, lips + v3(0.0, -0.10, 0.04), ground_y=max(bc[1] - 0.05, 0.1), phase=tl, r=0.011, n=3, splash=False) if False else None
    drips(P, add, [lips + v3(0.02, -0.12, 0.06), bc + R @ v3(0.15, -0.10, 0.2), P['kn_l'] + v3(0.02, -0.04, 0.08),
                   P['sh_l'] + v3(0.02, -0.2, 0.05), P['an_r'] + v3(0, 0.2, 0.1)], fall=0.4, speed=1.1)
    # salt: crystal clusters on shoulders, belly, knees, chin, hands
    sc = lambda c, n_, nn, sp, sz, sd: salt_crystals(add, c, nn, n=n_, spread=sp, size=sz, seed=sd)
    sc(P['sh_r'] + v3(-0.02, 0.07, -0.02), 7, v3(-0.4, 1, 0), 0.06, 0.028, 1)
    sc(P['sh_l'] + v3(0.02, 0.07, -0.02), 7, v3(0.4, 1, 0), 0.06, 0.026, 2)
    sc(bc + R @ v3(0.14, 0.08, 0.22), 9, R @ v3(0.4, 0.3, 1), 0.10, 0.032 * bl ** 0.4, 3)
    sc(bc + R @ v3(-0.16, 0.0, 0.17), 6, R @ v3(-0.6, 0.1, 1), 0.07, 0.026 * bl ** 0.4, 4)
    sc(P['kn_l'] + v3(0.04, 0.0, 0.05), 4, v3(0.5, 0.2, 1), 0.035, 0.02, 5)
    sc(P['kn_r'] + v3(-0.04, 0.0, 0.05), 4, v3(-0.5, 0.2, 1), 0.035, 0.02, 6)
    sc(H + Rh @ v3(0, -0.085, 0.05) * h, 6, Rh @ v3(0, -0.5, 1), 0.04, 0.016, 7)
    sc(g + v3(0.0, 0.0, 0.0), 3, v3(0, 1, 0.5), 0.03, 0.014, 8)
    sc(nk + v3(0, -0.04, -0.08), 6, v3(0, 0.5, -1), 0.07, 0.024, 9)
    # burst: spray of brine and salt shards
    fx = P['fx']
    if fx > 0:
        rng = np.random.default_rng(5)
        for k in range(14):
            a = rng.uniform(0, 6.28)
            r_ = (0.25 + 0.5 * fx) * rng.uniform(0.6, 1.0)
            c = bc + v3(np.cos(a) * r_, rng.uniform(-0.05, 0.3) * fx, np.sin(a) * r_ * 0.9)
            if k % 3 == 0:
                add(RoundBox(c, (0.02, 0.03, 0.02), 0.004, rot_y(a)), 'salt', 0.0)
            else:
                add(Sphere(c, 0.026), 'water', 0.0)
        add(Torus(v3(0, 0.03, 0.05), v3(0, 1, 0), 0.25 + 0.45 * fx, 0.02), 'water', 0.0)
    puddle(P, add, r=0.36 + 0.1 * max(bl - 1, 0), seed=5.0)
    ripples(P, add, n=2, r0=0.30)

    skin_base = _hex('#a9b3a6')

    def skin_fn(p, n):
        a = tide_face(P, skin_base, BLACK, milky=True, sunken=0.55, brows=False, mouth=1.0, lips=_hex('#6a6e68'))(p, n)
        body_m = p[:, 1] < nk[1] - 0.04
        crust = (fbm(p + 2.0, 11.0, 3) > 0.54) | (fbm(p + 5.0, 26.0, 2) > 0.68)
        m = crust & body_m
        sc_ = np.array(SALT)[None, :] * (0.85 + 0.25 * fbm(p, 40, 1)[:, None])
        a[m] = sc_[m]
        q = (p - H) @ Rh
        chin = (q[:, 1] < -0.045 * h) & (q[:, 2] > -0.02) & (fbm(p, 30, 2) > 0.45)
        a[chin] = sc_[chin]
        return a * (0.95 + 0.1 * fbm(p, 9, 2)[:, None])

    def belly_fn(p, n):
        q = (p - bc) @ R
        base = np.array(_hex('#9fb0a8'))[None, :].repeat(len(p), 0) * (0.9 + 0.2 * fbm(p, 12, 2)[:, None])
        # brine showing through the stretched skin: blue-green veins and a lower tint
        base = base * (1 - 0.25 * np.clip(-q[:, 1] / rb, 0, 1)[:, None]) + np.array(BRINE)[None, :] * (0.25 * np.clip(-q[:, 1] / rb, 0, 1))[:, None]
        v = np.abs(vnoise(p, 14.0) - 0.5) < 0.02
        base[v] = base[v] * 0.6 + np.array(_hex('#4a7a80'))[None, :] * 0.4
        m = (fbm(p + 1.0, 10.0, 3) > 0.60) & (q[:, 2] > -0.05)
        base[m] = np.array(SALT)[None, :]
        return base
    mats = {
        'skin': Material(skin_fn, spec=0.45, gloss=30, sss=0.4, brush=0.04),
        'belly': Material(belly_fn, spec=0.9, gloss=62, sss=0.5, brush=0.03),
        'shift': wet_cloth(_hex('#8f9a92'), wet=0.5, low_dark=0.12, streak=0.18),
        'tin': Material(lambda p, n: np.array(_hex('#8a9190'))[None, :] * (0.8 + 0.3 * fbm(p, 26, 2)[:, None]), spec=0.7, gloss=40, metal=0.6),
        'salt': salt_mat(),
    }
    return tide_finish(P, parts, mats, add, pool_r=0.7)


ROWS, _fr = tide_rows(neutral_pose, attack_style='swing', weapon_side='l', cast_side='l', sink=0.2)


def frames():
    fr = _fr()
    h = 0.97
    for i, (P, o) in enumerate(fr['idle']):
        P['belly'] = 1.0 + 0.03 * P['breathe']
    for i, (P, o) in enumerate(fr['move']):
        P['belly'] = 1.0
    for i, (P, o) in enumerate(fr['attack']):
        P['belly'] = [1.0, 1.25, 1.65, 0.5][i]
        P['item_r'] = None
        rig.place_arm(P, 'r', P['pelvis'] + v3(-0.30, [0.2, 0.3, 0.1, -0.1][i], 0.2), (-1, -0.4, -0.3), l1=0.27 * h, l2=0.26 * h)
        rig.place_arm(P, 'l', P['pelvis'] + v3(0.30, [0.2, 0.3, 0.1, -0.1][i], 0.2), (1, -0.4, -0.3), l1=0.27 * h, l2=0.26 * h)
        P['head_pitch'] = np.radians([-20, -30, -4, 5][i])
        P['fx'] = [0, 0, 1, 0.5][i]
    for i, (P, o) in enumerate(fr['hit']):
        P['belly'] = 1.1
    for i, (P, o) in enumerate(fr['cast']):
        P['belly'] = [1.05, 1.18, 1.1][i]
    for i, (P, o) in enumerate(fr['death']):
        P['belly'] = [1.2, 0.7, 0.45, 0.35][i]
        P['fx'] = [0.4, 0.8, 0.2, 0.0][i]
        P['item_r'] = None
    return fr

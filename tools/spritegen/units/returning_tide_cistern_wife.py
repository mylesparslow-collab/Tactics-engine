"""Cistern-Wife (Returning Tide, flood engine). A thin woman bent double under a cracked stoneware
cistern strapped to her back that never empties: water sheets from its fissures, spills over the rim and
runs down her in streams. Wet hair plastered flat, a long wooden dipper in one fist.
Defining detail: the tall cracked cistern on her back, always dripping, and the pool around her.
"""
from _returning_tide_w2 import *

UNIT_ID = 'returning_tide_cistern_wife'

C = Costume(top='robe', sleeve='robe', legs='robe', boot='skin', hand='skin', skin='skin',
            skirt=None, head='bald', belt=None, boots_tall=False, girth=1.0)


def neutral_pose():
    P = base_pose(height=0.98, build=0.95)
    h = 0.98
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + rig.UPPER, v3(0, -0.05, 0))
    rig.place_leg(P, 'l', (0.16, 0.085, 0.10), l1=0.43 * h, l2=0.42 * h)
    rig.place_leg(P, 'r', (-0.16, 0.085, -0.06), l1=0.43 * h, l2=0.42 * h)
    rig.lean(P, fwd=np.radians(15))
    P['head_pitch'] = np.radians(-10)
    rig.shift(P, ('head',), v3(0, 0.0, 0.04))
    # left hand grips the strap at the collarbone, right hand the dipper low at her side
    rig.place_arm(P, 'l', P['chest'] + v3(0.10, 0.14, 0.16), (1, -0.5, -0.3), l1=0.27 * h, l2=0.26 * h)
    rig.place_arm(P, 'r', v3(-0.26, 0.82, 0.22), (-1, -0.4, -0.3), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(0.05, -0.6, 0.8))
    P['item_l'] = v3(0, 0, 1)
    P['gush'] = 0.0
    return P


def ladle(P, add, g, d, cup=0.05):
    add(Capsule(g - d * 0.15, g + d * 0.62, 0.015, 0.012), 'wood', 0.0)
    c = g + d * 0.66
    R = basis_from(d, (0, 1, 0))
    add(Ellipsoid(c, (cup, cup * 0.55, cup), R), 'wood', 0.01)
    add(Ellipsoid(c + R[:, 1] * 0.012, (cup * 0.8, cup * 0.3, cup * 0.8), R), 'water', 0.0)
    return c


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    h, b = P['height'], P['build']
    R = frame_for(P)
    ch, nk, pel = P['chest'], P['neck'], P['pelvis']
    tl, cg = P['tell'], P['cast_glow']
    # ragged wet robe, shawl across the shoulders
    add(ragged_robe(P, hem=0.07, flare=0.9, rag=1.1, seed=2.0, droop=0.05, girth=1.0), 'robe', 0.0)
    add(shawl(P, depth=0.20, width=0.18, rag=1.0, seed=3.1, front_drop=0.05), 'shawl', 0.0)
    wet_hair(P, add, 'hair', 'long')
    # the cistern: tall stoneware vat on her back, leaning with her spine
    cc = ch + R @ v3(0, -0.03, -0.34)
    Rc = R @ rot_x(np.radians(-6))
    crack_a = (0.55, 0.04, 0.22)
    add(barrel(cc, Rc, 0.23, 0.30, bulge=0.12, crack=crack_a), 'cistern', 0.0)
    add(barrel(cc + Rc[:, 1] * 0.30, Rc, 0.20, 0.03, bulge=0.0), 'cistern_dk', 0.01)          # lid rim
    for dy in (-0.19, -0.03, 0.15):
        add(Torus(cc + Rc[:, 1] * dy, Rc[:, 1], 0.23 * (1 + 0.12 * (1 - (dy / 0.30) ** 2)) - 0.004, 0.013), 'iron', 0.0)
    # strap harness over her shoulders and across the chest
    for sx, s in ((-1, 'r'), (1, 'l')):
        a = cc + Rc @ v3(sx * 0.12, 0.20, 0.20)
        bq = P['sh_' + s] + v3(0, 0.05, -0.02)
        cq = P['chest'] + R @ v3(sx * 0.12, -0.14, 0.14)
        add(Capsule(a, bq, 0.016), 'cord', 0.01)
        add(Capsule(bq, cq, 0.016), 'cord', 0.01)
        add(Capsule(cq, cc + Rc @ v3(sx * 0.25, -0.20, 0.12), 0.016), 'cord', 0.01)
    # water: cracked fissure streams, rim spill, a sheet down the back of her robe
    ang = crack_a[0]
    fx = cc + Rc @ v3(np.sin(ang) * 0.26, crack_a[1], np.cos(ang) * 0.26)
    gush = 1.0 + 1.8 * P['gush'] + 1.2 * cg
    stream(add, fx + v3(0, 0, 0.0), ground_y=0.0, phase=tl, r=0.020 * gush, out=(0.04 + 0.2 * cg, 0.05 + 0.3 * cg), n=7)
    for j, (sa, sy) in enumerate(((-0.4, -0.28), (2.3, 0.0), (3.6, -0.15))):
        q = cc + Rc @ v3(np.sin(sa) * 0.26, sy, np.cos(sa) * 0.26)
        stream(add, q, ground_y=0.0, phase=tl + 0.3 * j, r=0.011 * (1 + 0.6 * P['gush']), out=(0.0, -0.04), n=6)
        add(Sphere(q, 0.016), 'water', 0.0)
    rim_pts = []
    for j, sa in enumerate((0.8, 2.0, 4.3)):
        q = cc + Rc[:, 1] * 0.33 + Rc @ v3(np.sin(sa) * 0.2, 0, np.cos(sa) * 0.2)
        rim_pts.append(q)
        add(Ellipsoid(q + v3(0, -0.03, 0), (0.02, 0.05, 0.02)), 'water', 0.01)
    # wet cascade over her shoulders back: drips from hem and fingers
    hand_l, hand_r = hand_pos(P, 'l'), hand_pos(P, 'r')
    drips(P, add, rim_pts + [hand_l + v3(0, -0.05, 0), pel + v3(0.18, -0.74, 0.1), pel + v3(-0.2, -0.76, -0.1),
                             nk + v3(0.0, -0.1, 0.2), P['head'] + v3(0.0, -0.1, 0.1)], fall=0.55, speed=1.3)
    # dipper
    if P['item_r'] is not None:
        d = norm(P['item_r'])
        c = ladle(P, add, hand_r, d)
        if P['fx'] > 0:
            for k in range(6):
                a = k / 6 * 6.28
                add(Sphere(c + d * 0.2 + v3(np.cos(a) * 0.12 * P['fx'], 0.05 * (k % 2) - 0.06, np.sin(a) * 0.12 * P['fx']), 0.022), 'water', 0.0)
    # open-the-cistern pour: arc of water thrown forward over her shoulder
    if cg > 0.2:
        top = cc + Rc[:, 1] * 0.30
        for k in range(10):
            t = k / 9
            q = top + v3(0, 0.12 * np.sin(np.pi * t * 0.9) - 0.9 * t * t, 0.10 + 1.0 * cg * t)
            if q[1] > 0.02:
                add(Sphere(q, 0.03 * (1.2 - 0.5 * t) * cg), 'water', 0.03)
    puddle(P, add, r=0.46 + 0.20 * cg + 0.06 * P['gush'], center=(0.0, 0.0, -0.1), seed=3.3)
    ripples(P, add, n=3, r0=0.40, center=(0.0, 0.0, -0.1))
    mats = {
        'robe': wet_cloth(_hex('#3f5a4c'), wet=0.9, low_dark=0.25),
        'shawl': wet_cloth(_hex('#7fa88c'), wet=0.8, low_dark=0.05),
        'hair': Material(_hex('#2c2f2a'), spec=0.8, gloss=40, brush=0.05),
        'skin': wet_skin(P, SKIN_PALE, hair=_hex('#2c2f2a'), sunken=0.3),
        'wood': Material(_hex('#5a4a38'), spec=0.4, gloss=22, brush=0.1),
        'iron': Material(_hex('#35383a'), spec=0.5, gloss=28, metal=0.4, brush=0.08),
        'cistern': Material(cistern_albedo(cc, Rc, crack_a), spec=0.6, gloss=44, brush=0.07),
        'cistern_dk': Material(_hex('#4f5a56'), spec=0.4, gloss=26, brush=0.08),
    }
    return tide_finish(P, parts, mats, add, pool_r=0.62)


def cistern_albedo(cc, Rc, crack_a):
    base = np.array(_hex('#9aa8a0'))
    dark = np.array(_hex('#2e3736'))
    glint = np.array(GLINT)

    def fn(p, n):
        q = (p - cc) @ Rc
        a = base[None, :] * (0.78 + 0.34 * fbm(p, 16, 3)[:, None])
        y = q[:, 1]
        a = a * (1 - 0.35 * np.clip((0.45 - y) / 0.9, 0, 1))[:, None]      # lower half darker (soaked)
        # hairline cracks
        r1 = np.abs(vnoise(p, 9.0) - 0.5) < 0.014
        a[r1] = dark
        # wet streaks
        st = fbm(p * np.array([1.0, 0.1, 1.0]), 30, 2) > 0.62
        a[st] = a[st] * 0.8 + glint[None, :] * 0.2
        ang = np.arctan2(q[:, 0], q[:, 2])
        fis = (np.abs(ang - crack_a[0]) * 0.3 < 0.05) & (np.abs(y - crack_a[1]) < crack_a[2] + 0.03)
        a[fis] = a[fis] * 0.3 + glint[None, :] * 0.5
        return a
    return fn


ROWS, _fr = tide_rows(neutral_pose, attack_style='swing', weapon_side='r', cast_side='l')


def frames():
    fr = _fr()
    for i, (P, o) in enumerate(fr['idle']):
        P['gush'] = 0.0
    for i, (P, o) in enumerate(fr['move']):
        P['gush'] = 0.3
    for i, (P, o) in enumerate(fr['attack']):
        P['gush'] = 0.2
        P['item_l'] = v3(0, 0, 1)
        h = 0.98
        rig.place_arm(P, 'l', P['chest'] + v3(0.10, 0.12, 0.16), (1, -0.5, -0.3), l1=0.27 * h, l2=0.26 * h)
    for i, (P, o) in enumerate(fr['cast']):
        P['gush'] = [0.3, 0.8, 1.0][i]
        P['item_l'] = None
        rig.place_arm(P, 'l', v3(0.30, [1.15, 1.5, 1.35][i], [0.20, 0.28, 0.40][i]), (1, -0.5, -0.3), l1=0.27 * 0.98, l2=0.26 * 0.98)
    for i, (P, o) in enumerate(fr['death']):
        P['item_r'] = None
        P['gush'] = 0.5
    return fr

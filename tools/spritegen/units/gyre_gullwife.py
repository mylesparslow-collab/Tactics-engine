"""Gullwife (Gyre ranged, ground). A stout cliff-woman in a headscarf and feathered oilskin apron, planted wide, a
flock of screaming gulls in her apron that she throws at whatever she dislikes. Defining detail: gull heads
poking from the apron, and the dozen birds leaving her hands at once."""
from _gyre_common import *

UNIT_ID = 'gyre_gullwife'
LOOK = LOOK
C = Costume(top='oil_pale', sleeve='oil', legs='oil_dk', boot='boot', hand='skin', skirt='robe', skirt_mat='oil_dk',
            hem=0.15, flare=0.95, head='cap', head_mat='wool', belt='cord', girth=1.30, boots_tall=False)


def neutral_pose():
    P = ground_pose(base_pose(height=0.93, build=1.22))
    rig.lean(P, fwd=np.radians(4))
    rig.place_arm(P, 'r', v3(-0.26, 0.98, 0.20), (-1, -0.2, -0.6), l1=0.25, l2=0.24)
    rig.place_arm(P, 'l', v3(0.26, 0.98, 0.20), (1, -0.2, -0.6), l1=0.25, l2=0.24)
    return P


def gull_heads(P, add, n=4):
    h, b = P['height'], P['build']
    base = P['pelvis'] + v3(0, 0.22 * h, 0.20)
    for j in range(n):
        a = (j - (n - 1) / 2) * 0.17 * b
        top = base + v3(a, 0.07 + 0.03 * ((j * 7) % 3), 0.04 - 0.02 * abs(a) * 3)
        sway = 0.02 * np.sin(P['tellp'] * 6.283 + j)
        top = top + v3(sway, 0, 0)
        add(Capsule(top - v3(0, 0.08, 0), top, 0.036, 0.030), 'feather_g', 0.0)
        add(Sphere(top + v3(0, 0.02, 0.01), 0.040), 'feather_g', 0.02)
        add(Capsule(top + v3(0, 0.015, 0.04), top + v3(0.0, 0.0, 0.11), 0.016, 0.007), 'beak', 0.0)
        add(Sphere(top + v3(-0.025, 0.035, 0.03), 0.009), 'eye', 0.0)


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    h, b = P['height'], P['build']
    pel = P['pelvis']
    # feathered apron: front panel and a bulging pouch full of gulls
    add(RoundBox(pel + v3(0, -0.12 * h, 0.155 * b), (0.19 * b, 0.30 * h, 0.012), 0.008,
                 rot_x(0.10)), 'oil_pale', 0.0)
    add(Ellipsoid(pel + v3(0, 0.15 * h, 0.15 * b), (0.21 * b, 0.12 * h, 0.12 * b)), 'oil_pale', 0.04)
    for i in range(9):
        a = -0.8 + i * 0.2
        add(Ellipsoid(pel + v3(np.sin(a) * 0.20 * b, -0.40 * h, 0.17 * b + np.cos(a) * 0.0),
                      (0.032, 0.07 * h, 0.012), rot_z(a * 0.3)), ('feather_s', 'feather_g')[i % 2], 0.0)
    add(Cylinder(pel + v3(0, 0.07 * h, 0.0), pel + v3(0, 0.10 * h, 0.0), 0.15 * b * 1.15, 0.01), 'cord', 0.0)
    flk = P['flock']
    if flk < 0.12:
        gull_heads(P, add, 4)
    # headscarf knot at the back
    H = P['head']
    Rh = head_R(P)
    add(Sphere(H + Rh @ v3(0, 0.02, -0.11) * h, 0.036), 'wool', 0.0)
    # the flock leaving her hands (throw) or wheeling above her (cast)
    if flk > 0.05:
        rng = np.random.default_rng(5)
        hands = (hand_pos(P, 'r') + hand_pos(P, 'l')) / 2
        for j in range(6):
            sx = (j - 2.5) / 2.5
            t = min(flk, 1.3)
            pos = hands + v3(sx * (0.15 + 0.55 * t), 0.15 * t + 0.1 * np.sin(j * 1.7), 0.10 + 0.85 * t * (0.6 + 0.1 * j % 3))
            fl = np.sin(P['tellp'] * 6.283 * 2 + j * 1.3)
            mini_bird(add, pos, yaw=sx * 0.35, flap=fl, k=0.30, pitch=0.1, back='feather_g', belly='feather_g')
    ob = P['orbit']
    if ob > 0.05:
        c0 = P['head'] + v3(0, 0.22, 0.0)
        for j in range(6):
            th = P['tellp'] * 6.283 + j * 1.05
            pos = c0 + v3(np.cos(th) * 0.55, 0.15 * np.sin(j * 2.0) + 0.1, np.sin(th) * 0.5)
            mini_bird(add, pos, yaw=-th + 1.57, flap=np.sin(th * 2 + j), k=0.30, back='feather_g', belly='feather_g')
    mats = gyre_mats(P, skin=hx('#c88f6b'), hair=hx('#7c6a58'), coat=hx('#7d7a6e'), eyes=hx('#2a1d1a'))
    mats['skin'] = Material(face_albedo(P, hx('#c88f6b'), hx('#7c6a58'), lips=hx('#a85a4c')), spec=0.06, gloss=12, sss=0.5, brush=0.02)
    return ground_finish(P, parts, mats)


def tweak(rows):
    for i, (P, o) in enumerate(rows['attack']):
        h = P['height']
        # both arms heave the flock forward and up
        tg = [v3(0.0, 1.05, -0.10), v3(0.0, 1.30, 0.20), v3(0.0, 1.50, 0.62), v3(0.0, 1.30, 0.45)][i]
        for s, sx in (('r', -1), ('l', 1)):
            rig.place_arm(P, s, v3(sx * (0.20 - 0.04 * i * 0.5), tg[1], tg[2]), (sx, -0.3, -0.5), l1=0.25, l2=0.24)
        P['flock'] = [0.0, 0.15, 0.55, 1.15][i]
        P['tellp'] = i / 4
    for i, (P, o) in enumerate(rows['cast']):
        for s, sx in (('r', -1), ('l', 1)):
            rig.place_arm(P, s, v3(sx * 0.22, [1.4, 1.62, 1.55][i], 0.10), (sx, -0.3, -0.5), l1=0.25, l2=0.24)
        P['orbit'] = [0.4, 1.0, 1.0][i]
        P['tellp'] = [0.0, 0.2, 0.4][i]
    for i, (P, o) in enumerate(rows['idle']):
        P['tellp'] = i / 4
    for i, (P, o) in enumerate(rows['move']):
        P['tellp'] = i / 4


ROWS, frames = ground_rows(neutral_pose, attack='cast', tweak=tweak)

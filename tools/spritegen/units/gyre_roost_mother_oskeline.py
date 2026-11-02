"""Roost-Mother Oskeline, Keeper of the High Nests (Gyre hero, ground). An ancient bent woman in a long
feather-woven shawl and oilskin skirt, driftwood crook with a thin gold nest-ring in one hand, the other arm
raised calling, a pair of crows perched on her shoulders, beak-orange knots in the shawl."""
from _gyre_common import *

UNIT_ID = 'gyre_roost_mother_oskeline'
LOOK = LOOK
C = Costume(top='oil', sleeve='oil', legs='oil_dk', boot='boot', hand='skin', skirt='robe', skirt_mat='oil_dk',
            hem=0.05, flare=0.9, head='hair', hair_style='long', belt='cord', girth=1.0, boots_tall=False)
WHITE = hx('#d8d4c8')


def neutral_pose():
    P = ground_pose(base_pose(height=0.86, build=0.92))
    rig.lean(P, fwd=np.radians(15))
    P['head_pitch'] = np.radians(-14)
    rig.place_arm(P, 'r', v3(-0.24, 0.96, 0.22), (-1, -0.3, -0.5), l1=0.25, l2=0.24)
    P['item_r'] = norm(v3(0.05, 1.0, 0.10))
    rig.place_arm(P, 'l', v3(0.33, 1.52, 0.18), (1, -0.3, -0.4), l1=0.25, l2=0.24)
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    h, b = P['height'], P['build']
    feather_mantle(P, add, rings=((0.16, 0.0, 0.10, 12), (0.225, -0.05, 0.13, 15), (0.285, -0.11, 0.14, 17)),
                   scale=1.0, seed=7, mats=('feather_s', 'feather_g', 'feather_i', 'feather_g'))
    # beak-orange knots in the shawl
    nk = P['neck']
    for j in range(5):
        a = -0.9 + j * 0.45
        add(Sphere(nk + v3(np.sin(a) * 0.20 * b, -0.10 * h, np.cos(a) * 0.17 * b), 0.016), 'cord', 0.0)
    # driftwood crook with a gold nest-ring
    butt, tip = held(P, add, 'r', 'staff', shaft='drift', head='drift', below=0.9, above=0.78)
    d = norm(tip - butt)
    side = norm(np.cross(d, v3(0, 0, 1)))
    add(Capsule(tip, tip + d * 0.05 + side * 0.08, 0.020, 0.018), 'drift', 0.0)
    add(Capsule(tip + d * 0.05 + side * 0.08, tip + side * 0.17 - d * 0.02, 0.018, 0.014), 'drift', 0.0)
    add(Capsule(tip + side * 0.17 - d * 0.02, tip + side * 0.15 - d * 0.10, 0.014, 0.010), 'drift', 0.0)
    add(Torus(tip + side * 0.10 + d * 0.0, np.cross(d, side), 0.040, 0.007), 'gold', 0.0)
    add(Cylinder(butt + d * 0.6, butt + d * 0.64, 0.024, 0.004), 'cord', 0.0)
    # crows on her shoulders
    perched_crow(add, P['sh_r'] + v3(-0.02, 0.07, 0.0), yaw=0.5, k=0.34)
    perched_crow(add, P['sh_l'] + v3(0.02, 0.07, -0.02), yaw=-0.2, k=0.30)
    # cast: crows wheeling above her head
    ob = P['orbit']
    if ob > 0.05:
        c0 = P['head'] + v3(0, 0.30, 0.0)
        for j in range(5):
            th = P['tellp'] * 6.283 + j * 1.25
            pos = c0 + v3(np.cos(th) * 0.58, 0.18 * np.sin(j * 2.0), np.sin(th) * 0.5)
            mini_bird(add, pos, yaw=-th + 1.57, flap=np.sin(th * 2 + j), k=0.28, back='feather_i', belly='feather_i', beak='beak_ink')
    mats = gyre_mats(P, skin=hx('#b88a6a'), hair=WHITE, coat=hx('#76736a'), eyes=hx('#2a1d1a'))
    mats['skin'] = Material(face_albedo(P, hx('#b88a6a'), WHITE, lips=hx('#9a5a4c')), spec=0.06, gloss=12, sss=0.5, brush=0.02)
    return ground_finish(P, parts, mats)


def tweak(rows):
    for i, (P, o) in enumerate(rows['cast']):
        for s, sx in (('l', 1),):
            rig.place_arm(P, s, v3(sx * 0.30, [1.5, 1.7, 1.62][i], 0.15), (sx, -0.3, -0.4), l1=0.25, l2=0.24)
        P['orbit'] = [0.4, 1.0, 1.0][i]
        P['tellp'] = [0.0, 0.2, 0.4][i]
    for nm in ('idle', 'move', 'attack'):
        for i, (P, o) in enumerate(rows[nm]):
            P['tellp'] = i / 4


ROWS, frames = ground_rows(neutral_pose, attack='swing', tweak=tweak)

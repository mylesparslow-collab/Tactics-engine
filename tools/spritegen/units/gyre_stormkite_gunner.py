"""Stormkite Gunner (Gyre long ranged, ground). A gunner kneeling on a small canvas-and-bone kite platform that
sits on its skids on the ground, held by taut cables to iron stakes, wind bellying the canvas. A harpoon-bolt
thrower at the shoulder, oilskin coat, beak-orange pennant on the mast. NOT flying: platform and cables
clearly grounded. Defining detail: tether cables straight as bowstrings."""
from _gyre_common import *
from kit.anim import kneel

UNIT_ID = 'gyre_stormkite_gunner'
LOOK = LOOK
C = Costume(top='oil', sleeve='oil', legs='oil_dk', boot='boot', hand='glove', skirt='coat', skirt_mat='oil_dk',
            hem=0.45, flare=0.7, head='hood', head_mat='oil_dk', belt='tar', girth=1.05, boots_tall=True)
LIFT = 0.16
OFF = v3(0.05, 0.0, 0.02)


def neutral_pose():
    P = ground_pose(base_pose(height=0.95, build=1.0))
    kneel(P, 0.85)
    d = v3(0, LIFT, 0.0) + OFF
    rig.shift(P, rig.UPPER + ('pelvis', 'hip_r', 'hip_l', 'kn_r', 'kn_l', 'an_r', 'an_l'), d)
    rig.lean(P, fwd=np.radians(12))
    aim = norm(v3(-0.12, -0.14, 1.0))
    sh = P['sh_r']
    g = P['pelvis'] + v3(-0.10, 0.40, 0.30)
    rig.place_arm(P, 'r', g, (-1, -0.5, -0.3), l1=0.27, l2=0.26)
    rig.place_arm(P, 'l', g + aim * 0.34 + v3(0, -0.04, 0.0), (1, -0.5, -0.3), l1=0.27, l2=0.26)
    P['item_r'] = aim
    P['head_pitch'] = np.radians(8)
    P['wind'] = 0.0
    return P


def build(P):
    parts, add = new_parts()
    wind = P.get('wind', 0.0)
    # --- platform: deck, skids, rails (sits on the ground)
    Ry = rot_y(0.0)
    add(RoundBox(v3(0.05, 0.075 + 0.0, 0.0) + OFF, (0.52, 0.035, 0.44), 0.01, Ry), 'wood', 0.0)
    for sx in (-1, 1):
        add(Capsule(v3(sx * 0.40, 0.03, -0.55) + OFF, v3(sx * 0.40, 0.04, 0.58) + OFF, 0.032, 0.026), 'drift', 0.0)
        add(Capsule(v3(sx * 0.40, 0.045, 0.58) + OFF, v3(sx * 0.40, 0.12, 0.66) + OFF, 0.026, 0.020), 'drift', 0.0)
        add(Capsule(v3(sx * 0.46, 0.09, -0.40) + OFF, v3(sx * 0.46, 0.34, -0.40) + OFF, 0.016, 0.016), 'bone', 0.0)
        add(Capsule(v3(sx * 0.46, 0.34, -0.40) + OFF, v3(sx * 0.46, 0.34, 0.30) + OFF, 0.013, 0.013), 'bone', 0.0)
    add(Cylinder(v3(0.05, 0.10, 0.20) + OFF, v3(0.05, 0.11, 0.20) + OFF, 0.0, 0.0) if False else Sphere(v3(0, -5, 0), 0.001), 'wood', 0.0)
    # --- mast and the belly of the kite sail behind the gunner
    m0 = v3(0.05, 0.10, -0.38) + OFF
    m1 = v3(0.12, 1.08, -0.55) + OFF
    add(Capsule(m0, m1, 0.028, 0.016), 'drift', 0.0)
    me = norm(m1 - m0)
    sc = v3(1, 0, 0)
    sn = norm(np.cross(sc, me))
    sn = sn if sn[2] > 0 else -sn
    ang = 0.10 * np.sin(wind * 6.283)
    sail = Blade(m0 + me * 0.12, me, sc, sn, 0.92, lead=(0.46, 0.015), trail=(0.46, 0.015), th=(0.014, 0.010), gs=1.5)
    mats_sail = Material(noisy(CANVAS, 0.06, 18.0), spec=0.02, brush=0.06)
    add(sail, 'canvas', 0.0)
    # cross-spar and stripe
    sp = m0 + me * 0.55
    add(Capsule(sp - sc * 0.50, sp + sc * 0.50, 0.012, 0.012), 'bone', 0.0)
    add(Capsule(m0 + me * 0.12 - sc * 0.50, m0 + me * 0.12 + sc * 0.50, 0.016, 0.016), 'cord', 0.0)
    # pennant at the mast top
    for s_ in range(5):
        a = m1 + v3(0.02 * s_, 0.0 - 0.01 * s_, -0.07 * s_ - 0.02 + 0.02 * np.sin(P['tell'] * 6.283 + s_))
        add(Capsule(a, a + v3(0.02, 0, -0.07), 0.016 - 0.002 * s_, 0.014 - 0.002 * s_), 'cord', 0.0)
    # --- taut cables from the sail spar ends and mast top to iron stakes in the ground
    stakes = [v3(-0.55, 0.0, -0.85), v3(0.75, 0.0, -0.95), v3(1.05, 0.0, -0.20), v3(0.2, 0.0, -1.25)]
    ends = [sp - sc * 0.50, sp + sc * 0.50, m1 + v3(0, -0.12, 0), m1 + v3(0, -0.05, 0)]
    for st, en in zip(stakes, ends):
        st = st + OFF
        add(Capsule(en, st + v3(0, 0.06, 0), 0.011, 0.011), 'tar', 0.0)
        add(Capsule(st + v3(0, 0.0, 0), st + v3(0, 0.15, 0), 0.020, 0.016), 'iron', 0.0)
        add(Torus(st + v3(0, 0.15, 0), v3(1, 0, 0.3), 0.032, 0.008), 'iron', 0.0)
    # winch drum on the deck
    add(Cylinder(v3(-0.30, 0.12, 0.05) + OFF, v3(-0.30, 0.12, 0.25) + OFF, 0.05, 0.01), 'iron', 0.0)
    body(P, add, C)
    # harpoon-bolt thrower: stock, prod, harpoon bolt with a line to the winch
    if P['item_r'] is not None:
        d = norm(P['item_r'])
        g = hand_pos(P, 'r')
        side = norm(np.cross(d, v3(0, 1, 0)))
        butt = g - d * 0.38
        tip = g + d * 0.85
        add(Capsule(butt, g + d * 0.15, 0.034, 0.028), 'wood', 0.01)
        add(Capsule(g + d * 0.1, tip - d * 0.1, 0.022, 0.020), 'iron', 0.0)
        pr = g + d * 0.44
        add(Capsule(pr - side * 0.34 + d * (-0.10), pr + side * 0.34 + d * (-0.10), 0.016, 0.016), 'bone', 0.0)
        add(Capsule(pr - side * 0.34 + d * (-0.10), pr, 0.006, 0.006), 'tar', 0.0)
        add(Capsule(pr + side * 0.34 + d * (-0.10), pr, 0.006, 0.006), 'tar', 0.0)
        add(Capsule(g - d * 0.1, tip + d * 0.25, 0.014, 0.010), 'bone', 0.0)
        add(Capsule(tip + d * 0.22, tip + d * 0.45, 0.034, 0.004), 'steel', 0.0)
        add(Cylinder(tip + d * 0.14, tip + d * 0.17, 0.020, 0.004), 'cord', 0.0)
        add(Capsule(butt, v3(-0.30, 0.17, 0.15) + OFF, 0.006, 0.006), 'cord', 0.0)
        if P['fx'] > 0:
            add(Ellipsoid(tip + d * 0.5, (0.07 * P['fx'],) * 3), 'flash', 0.0)
    mats = gyre_mats(P, skin=hx('#c08f6c'), coat=hx('#6e6b60'), eyes=hx('#2a1d1a'))
    return ground_finish(P, parts, mats)


def tweak(rows):
    for nm in rows:
        for i, (P, o) in enumerate(rows[nm]):
            P['wind'] = (i % 4) / 4
    for i, (P, o) in enumerate(rows['attack']):
        aim = norm(v3(-0.12, [-0.10, -0.12, -0.10, -0.16][i], 1.0))
        rig.place_arm(P, 'r', P['pelvis'] + v3(-0.10, 0.40, 0.30 - [0.0, 0.04, 0.10, 0.04][i] * 0.0), (-1, -0.5, -0.3), l1=0.27, l2=0.26)
        P['item_r'] = aim


ROWS, frames = ground_rows(neutral_pose, attack='shoot', tweak=tweak)

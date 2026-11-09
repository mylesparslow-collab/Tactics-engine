"""Kite-Rigger (Gyre terrain, ground). A thick-set roost-rigger in a quilted oilskin coat, knit cap and pushed-up
goggles, hung about with the tools of his trade: a fan of three diamond kites on a bone frame rising behind his
shoulders (canvas halves in slate and white, orange cord bridles, ribbon tails), a block-and-tackle pulley and cord
coil on the belt, and in his left hand a tall driftwood perch pole with a T-bar and a tern sitting on it. The attack
plants the pole; the cast raises the kite fan. Defining detail: the kite fan silhouette behind him."""
from _gyre_w2 import *

UNIT_ID = 'gyre_kite_rigger'
LOOK = LOOK
C = Costume(top='oil', sleeve='oil', legs='oil_dk', boot='boot', hand='glove', skirt='coat', skirt_mat='oil_dk',
            hem=0.46, flare=0.75, head='cap', head_mat='knit', belt='cord', girth=1.18, boots_tall=True)


def neutral_pose():
    P = ground_pose(base_pose(height=0.98, build=1.12))
    h = P['height']
    rig.lean(P, fwd=np.radians(3))
    P['head_yaw'] = np.radians(-14)
    rig.place_arm(P, 'l', v3(0.30, 1.02, 0.14), (1, -0.4, -0.4), l1=0.27 * h, l2=0.26 * h)
    P['item_l'] = norm(v3(0.02, 1.0, 0.03))
    rig.place_arm(P, 'r', v3(-0.26, 0.98, 0.18), (-1, -0.4, -0.5), l1=0.27 * h, l2=0.26 * h)
    P['fan'] = 0.0
    return P


def kite_fan(add, mats, P):
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    h, b = P['height'], P['build']
    lift = P['fan']
    base = ch + v3(0, 0.02, -0.12)
    # bone frame: backpack rack and a fan hub
    add(RoundBox(ch + v3(0, -0.02, -0.12), (0.12 * b, 0.17, 0.028), 0.01, rot_x(0.0)), 'leather', 0.0)
    add(Capsule(pel + v3(0, 0.0, -0.13), ch + v3(0, 0.38 + 0.0, -0.20), 0.016, 0.014), 'bone', 0.0)
    wob = 0.04 * np.sin(P['tellp'] * 6.283)
    sets = [(0.0, 0.0, 0.00, 1.0, 'kite_c', 0.30, 0.46), (-0.62, 0.26, -0.20, 0.8, 'kite_l', 0.24, 0.38),
            (0.62, -0.26, -0.18, 0.8, 'kite_r', 0.24, 0.38)]
    for roll, yaw, dz, sc, nm, hw, ht in sets:
        roll = roll * (1.0 + 0.35 * lift)
        R = rot_y(yaw) @ rot_z(roll) @ rot_x(-0.55 - 0.15 * lift + wob)
        ctr = base + v3(0.0, 0.55 + 0.05 * lift, -0.30) + v3(roll * 0.30, 0.0, dz)
        ctr = ctr + R @ v3(0, 0.12, 0)
        ctr[1] = min(ctr[1], 1.50)
        anchor = base + v3(0, 0.20, -0.14)
        kite(add, mats, nm, ctr, R, hw * sc * 0.9, ht * sc * 0.9, tail=0.30 * sc, phase=P['tellp'] + roll, bridle_to=anchor,
             a=CANVAS if nm != 'kite_r' else mix(SLATE, GUANO, 0.25), b=mix(SLATE, GUANO, 0.25) if nm != 'kite_r' else CANVAS)


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    mats = gyre_mats(P, skin=hx('#c28b68'), hair=hx('#6a5a46'), coat=hx('#7c7867'), eyes=hx('#2a1d1a'))
    extra_mats(mats)
    mats['knit'] = Material(noisy(hx('#5d6a74'), 0.14, 44.0), spec=0.02, brush=0.1)
    mats['skin'] = Material(face_albedo(P, hx('#c28b68'), hx('#6a5a46'), lips=hx('#a85a4c')), spec=0.06, gloss=12, sss=0.5, brush=0.02)
    h, b = P['height'], P['build']
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    H, R = P['head'], head_R(P)
    # goggles pushed up on the cap
    for sx in (-1, 1):
        c = H + R @ v3(sx * 0.036, 0.062, 0.070) * h
        add(Torus(c, R @ v3(0, 0.5, 1), 0.022, 0.007), 'brass', 0.0)
        add(Ellipsoid(c, (0.019, 0.019, 0.006), R), 'glass', 0.0)
    add(Torus(H + R @ v3(0, 0.055, -0.005) * h, R @ v3(0, 1, -0.3), 0.088 * h, 0.006), 'leather', 0.0)
    kite_fan(add, mats, P)
    # belt gear: pulley block, cord coil, fid
    for sx in (1,):
        c = pel + v3(0.20 * b, -0.02, 0.06)
        add(RoundBox(c, (0.03, 0.055, 0.03), 0.01), 'wood', 0.0)
        add(Cylinder(c + v3(0.03, 0, 0), c + v3(0.045, 0, 0), 0.028, 0.004), 'iron', 0.0)
        add(Capsule(c + v3(0, -0.05, 0), c + v3(0.0, -0.17, 0.02), 0.006, 0.006), 'cord', 0.0)
    for k in range(3):
        add(Torus(pel + v3(-0.20 * b, 0.0 + 0.016 * k, 0.04), v3(1, 0, 0.2), 0.07, 0.011), 'cord', 0.0)
    # perch pole in the left hand
    if P['item_l'] is not None:
        d = norm(P['item_l'])
        g = hand_pos(P, 'l')
        base = g - d * 0.82
        perch_pole(add, base, d, length=1.58, bar=0.30, bird=True, flap=P['fan'], tell=P['tellp'])
    # right hand: bone fid mallet
    held(P, add, 'r', 'hammer', shaft='wood', head='iron') if P['item_r'] is not None else None
    return ground_finish(P, parts, mats)


def tweak(rows):
    for nm in rows:
        for i, (P, o) in enumerate(rows[nm]):
            P.setdefault('fan', 0.0)
            P['tellp'] = i / 4
    for i, (P, o) in enumerate(rows['attack']):
        P['fan'] = [0, 0.2, 0.6, 0.3][i]
        P['item_l'] = norm(v3([0.05, 0.1, 0.0, 0.05][i], [1.0, 0.8, -0.6, -0.2][i], [0.1, 0.5, 0.9, 0.5][i])) if False else P['item_l']
    for i, (P, o) in enumerate(rows['cast']):
        P['fan'] = [0.4, 1.0, 0.6][i]
        P['cast_glow'] = 0.0
    for i, (P, o) in enumerate(rows['death']):
        P['fan'] = 0.0
        P['item_l'] = norm(v3(0.5 * [0, 0.4, 0.7, 0.9][i], [1, 0.7, 0.5, 0.2][i], 0.2)) if P['item_l'] is not None else None


ROWS, frames = ground_rows(neutral_pose, attack='thrust', weapon_side='l', cast_side='r', tweak=tweak)

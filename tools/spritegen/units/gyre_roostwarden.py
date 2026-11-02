"""Roostwarden (Gyre tank, ground). A heavy cliff-guard in layered feathered oilskin and an albatross-skull
beak-mask helm, bracing a long hooked nest-pike with both hands, wide immovable stance, beak-orange cord
lashings. Defining detail: the pike's hook is a curved albatross bone, worn smooth."""
from _gyre_common import *

UNIT_ID = 'gyre_roostwarden'
LOOK = LOOK
C = Costume(top='oil', sleeve='oil', legs='oil_dk', boot='boot', hand='glove', skirt='coat', skirt_mat='oil_dk',
            hem=0.34, flare=0.8, head='none', belt='tar', girth=1.38, boots_tall=True)


def neutral_pose():
    P = ground_pose(base_pose(height=1.0, build=1.32))
    rig.lean(P, fwd=np.radians(5))
    P['an_r'] = v3(-0.26, 0.085, 0.02)
    P['an_l'] = v3(0.26, 0.085, 0.12)
    rig.place_leg(P, 'r', P['an_r'], l1=0.43, l2=0.42)
    rig.place_leg(P, 'l', P['an_l'], l1=0.43, l2=0.42)
    # two hands on the pike, braced forward
    rig.place_arm(P, 'r', v3(-0.22, 1.12, 0.22), (-1, -0.5, -0.3), l1=0.27, l2=0.26)
    rig.place_arm(P, 'l', v3(0.12, 1.28, 0.40), (1, -0.5, -0.3), l1=0.27, l2=0.26)
    P['item_r'] = norm(v3(0.14, 0.80, 1.0))
    P['item_l'] = None
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    h, b = P['height'], P['build']
    feather_mantle(P, add, rings=((0.19, 0.0, 0.10, 14), (0.26, -0.06, 0.13, 16), (0.31, -0.13, 0.12, 16)), scale=1.1)
    H = P['head']
    R = head_R(P)
    # albatross-skull beak-mask helm
    add(Ellipsoid(H + R @ v3(0, 0.035, -0.008) * h, (0.098 * h, 0.092 * h, 0.108 * h), R), 'bone', 0.0)
    add(Ellipsoid(H + R @ v3(0, 0.010, 0.060) * h, (0.080 * h, 0.060 * h, 0.065 * h), R), 'bone', 0.03)
    a = H + R @ v3(0, 0.0, 0.10) * h
    bb = H + R @ v3(0, -0.06, 0.30) * h
    add(Capsule(a, bb, 0.040 * h, 0.012 * h), 'bone', 0.02)
    add(Capsule(bb - (bb - a) * 0.10, bb + R @ v3(0, -0.035, 0.03) * h, 0.014 * h, 0.006 * h), 'beak', 0.0)
    for sx in (-1, 1):
        add(Sphere(H + R @ v3(sx * 0.055, 0.020, 0.088) * h, 0.022 * h), 'beak_ink', 0.0)
    add(Torus(H + R @ v3(0, 0.03, -0.01) * h, R[:, 1], 0.098 * h, 0.007 * h), 'cord', 0.0)
    add(Sphere(H + R @ v3(0, -0.07, -0.02) * h, 0.001), 'skin', 0.0)
    # the nest-pike with albatross-bone hook
    if P['item_r'] is not None:
        butt, tip = held(P, add, 'r', 'pike', shaft='drift', head='bone', below=1.15, above=1.0)
        d = norm(tip - butt)
        side = norm(np.cross(d, v3(0, 1, 0.1)))
        add(Capsule(tip - d * 0.18, tip + d * 0.00, 0.020, 0.020), 'bone', 0.0)
        pts = [tip - d * 0.14, tip - d * 0.02 + side * 0.07, tip + d * 0.04 + side * 0.16, tip - d * 0.06 + side * 0.20]
        rad = (0.026, 0.024, 0.020, 0.008)
        for u, v, r0, r1 in zip(pts[:-1], pts[1:], rad[:-1], rad[1:]):
            add(Capsule(u, v, r0, r1), 'bone', 0.0)
        for t in (0.0, 0.07, 0.14):
            add(Cylinder(tip - d * (0.24 + t), tip - d * (0.22 + t), 0.024, 0.004), 'cord', 0.0)
        add(Cylinder(butt + d * 0.3, butt + d * 0.33, 0.022, 0.004), 'cord', 0.0)
    mats = gyre_mats(P, skin=hx('#b88562'), coat=hx('#76736a'), eyes=hx('#2a1d1a'))
    return ground_finish(P, parts, mats)


ROWS, frames = ground_rows(neutral_pose, attack='thrust')

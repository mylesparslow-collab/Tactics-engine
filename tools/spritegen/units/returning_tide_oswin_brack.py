"""Captain Oswin Brack, the Unsunk (Returning Tide hero).

A Hulk captain who went down with his ship three hundred years ago and refused to stay down. Bearded,
pale and calm, in a sea-rotted green-black long coat with tarnished gold braid on the shoulders and
cuffs, a peaked captain's cap and a ship's-bell badge. A barnacled cutlass in his right hand, a brass
spyglass in his left. Defining detail: seaweed hanging in his beard and from the coat hem.
"""
from _returning_tide_common import *

UNIT_ID = 'returning_tide_oswin_brack'

C = Costume(top='coat', sleeve='coat', legs='trousers', boot='boot', hand='skin', skin='skin',
            skirt='coat', skirt_mat='coat', hem=0.22, flare=0.9, head='bald', belt='leather',
            boots_tall=True, girth=1.15)


def neutral_pose():
    P = base_pose(height=1.02, build=1.1)
    rig.place_leg(P, 'l', (0.17, 0.085, 0.12))
    rig.place_leg(P, 'r', (-0.15, 0.085, -0.06))
    P['head_pitch'] = np.radians(-3)
    P['head_yaw'] = np.radians(-10)
    rig.place_arm(P, 'r', v3(-0.31, 0.98, 0.18), (-1, -0.3, -0.6))
    rig.place_arm(P, 'l', v3(0.27, 1.06, 0.22), (1, -0.4, -0.4))
    P['item_r'] = norm(v3(-0.25, -0.35, 0.9))
    P['item_l'] = norm(v3(0.1, 0.5, 0.85))
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    H, R, h = P['head'], head_R(P), P['height']
    # beard with seaweed
    add(Ellipsoid(H + R @ v3(0, -0.075, 0.045) * h, (0.07 * h, 0.07 * h, 0.06 * h), R), 'beard', 0.02)
    rag_strips(add, H + R @ v3(0.01, -0.12, 0.06) * h, 3, 0.12, 'kelp', spread=0.03, seed=31, r=0.010)
    # peaked captain's cap
    add(Ellipsoid(H + R @ v3(0, 0.06, -0.01) * h, (0.092 * h, 0.05 * h, 0.098 * h), R), 'cap', 0.01)
    add(Cylinder(H + R @ v3(0, 0.08, -0.01) * h, H + R @ v3(0, 0.115, -0.015) * h, 0.105 * h, 0.01), 'cap', 0.0)
    add(Ellipsoid(H + R @ v3(0, 0.05, 0.085) * h, (0.07 * h, 0.010 * h, 0.04 * h), R), 'black', 0.0)
    add(Torus(H + R @ v3(0, 0.072, -0.01) * h, R[:, 1], 0.094 * h, 0.006), 'gold', 0.0)
    # gold braid: epaulettes, coat edges, cuffs, bell badge
    for s in ('r', 'l'):
        sx = -1 if s == 'r' else 1
        sh = P['sh_' + s]
        add(Ellipsoid(sh + v3(sx * 0.02, 0.035, 0), (0.07, 0.022, 0.06)), 'gold', 0.01)
        for k in range(3):
            add(Capsule(sh + v3(sx * (0.05 + 0.02 * k), 0.02, -0.04 + 0.04 * k),
                        sh + v3(sx * (0.07 + 0.02 * k), -0.06, -0.04 + 0.04 * k), 0.006), 'gold', 0.0)
        el, wr = P['el_' + s], P['wr_' + s]
        add(Capsule(el + (wr - el) * 0.70, wr, 0.050), 'gold', 0.0)
    nk = P['neck']
    for sx in (-1, 1):
        add(Capsule(nk + v3(sx * 0.05, -0.04, 0.09), P['pelvis'] + v3(sx * 0.03, 0.12, 0.11), 0.010), 'gold', 0.0)
    add(Capsule(nk + v3(0, -0.12, 0.13), nk + v3(0, -0.15, 0.135), 0.022, 0.032), 'gold', 0.0)   # bell badge
    # cutlass (barnacled) and spyglass
    r = held(P, add, 'r', 'blade', head='gold', above=0.62)
    if r is not None:
        butt, tip = r
        g = hand_pos(P, 'r')
        barnacles(add, g + (tip - g) * 0.55, v3(0, 1, 0.2), n=4, spread=0.025, size=0.010, seed=32)
        d = norm(tip - butt)
        add(Torus(g + d * 0.01, d, 0.04, 0.006), 'gold', 0.0)   # knuckle guard
    d = P['item_l']
    if d is not None:
        g = hand_pos(P, 'l')
        d = norm(d)
        add(Cylinder(g - d * 0.10, g + d * 0.05, 0.020, 0.004), 'leather', 0.0)
        add(Cylinder(g + d * 0.05, g + d * 0.16, 0.024, 0.004), 'brass', 0.0)
        add(Cylinder(g + d * 0.16, g + d * 0.24, 0.028, 0.004), 'brass', 0.0)
    # seaweed hanging from the coat hem and barnacles on the shoulder
    for k, a in enumerate(np.radians([-140, -60, 20, 150])):
        pel = P['pelvis']
        anc = v3(pel[0] + np.sin(a) * 0.27, 0.30, pel[2] + np.cos(a) * 0.22)
        rag_strips(add, anc, 2, 0.16, 'kelp', spread=0.03, seed=40 + k, sway=P['skirt_sway'], r=0.011)
    barnacles(add, P['sh_l'] + v3(0.02, 0.0, -0.08), v3(0.3, 0.4, -1), n=6, spread=0.05, seed=33)
    drips(P, add, [P['pelvis'] + v3(-0.25, -0.70, 0.08), P['pelvis'] + v3(0.22, -0.74, -0.04),
                   H + R @ v3(0, -0.17, 0.07) * h])
    puddle(P, add, r=0.32)
    mats = {
        'coat': wet_cloth(_hex('#24352e'), wet=0.8, low_dark=0.2, streak=0.2),
        'trousers': wet_cloth(_hex('#3a403c'), wet=0.7),
        'cap': wet_cloth(_hex('#1a2220'), wet=0.8, low_dark=0.0),
        'gold': Material(_hex('#9a8448'), spec=0.7, gloss=30, metal=0.8, brush=0.08),
        'beard': Material(_hex('#8c8a7e'), spec=0.5, gloss=30, brush=0.10),
        'skin': wet_skin(P, _hex('#b8b4a2'), hair=_hex('#8c8a7e'), sunken=0.35),
    }
    return tide_finish(P, parts, mats, add)


ROWS, frames = tide_rows(neutral_pose, attack_style='swing', weapon_side='r', cast_side='l')

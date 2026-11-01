"""Prophet Imre Dunnock, the Wet Saint (Returning Tide hero).

A former Concord tax clerk, ordinary and thin, calmly reading from a waterlogged ledger. His old clerk's
coat is soaked dark, its Concord cut sagging; spectacles, wet hair flat on his skull, the Wet Saint's
rod planted in his right hand. Defining details: the open ledger with gold-edged, ruined pages
dripping, and a puddle that gently spreads around his shoes.
"""
from _returning_tide_common import *

UNIT_ID = 'returning_tide_imre_dunnock'

C = Costume(top='coat', sleeve='coat', legs='trousers', boot='boot', hand='skin', skin='skin',
            skirt='coat', skirt_mat='coat', hem=0.24, flare=0.75, head='bald', belt=None,
            boots_tall=False, girth=0.85)


def neutral_pose():
    P = base_pose(height=1.0, build=0.88)
    rig.lean(P, fwd=np.radians(5))
    P['head_pitch'] = np.radians(22)
    P['head_yaw'] = np.radians(4)
    rig.place_arm(P, 'r', v3(-0.27, 1.12, 0.16), (-1, -0.5, -0.4))
    rig.place_arm(P, 'l', v3(0.06, 1.18, 0.33), (1, -0.6, -0.3))
    P['item_r'] = norm(v3(-0.03, 1.0, 0.06))
    P['item_l'] = v3(0, 0, 1)        # marks the left hand as busy (ledger), so walks keep it up
    P['ledger_open'] = 1.0
    return P


def ledger(P, add, g, open_=1.0):
    """Open ledger held in the left hand, tilted up toward the face."""
    hd = P['head']
    up = norm(v3(0, 0.8, 0) + norm(hd - g) * 0.6)
    R = basis_from(up, (0, 0, 1)) @ rot_y(np.radians(-25))
    c = g + R @ v3(-0.04, 0.03, 0.02)
    ang = np.radians(18 * open_ + 4)
    pages = []
    for sx in (-1, 1):
        Rr = R @ rot_y(-sx * ang)
        pc = c + R @ v3(sx * 0.075 * np.cos(ang), 0, 0.0)
        add(RoundBox(pc, (0.075, 0.10, 0.006), 0.003, Rr), 'cover', 0.0)
        add(RoundBox(pc + Rr[:, 2] * 0.010, (0.068, 0.094, 0.006), 0.002, Rr), 'pages', 0.0)
        pages.append(pc + Rr @ v3(sx * 0.07, -0.09, 0.0))
    add(Cylinder(c - R[:, 1] * 0.10, c + R[:, 1] * 0.10, 0.012, 0.002), 'cover', 0.0)
    return pages


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    wet_hair(P, add, 'hair')
    # Concord clerk's collar and cuffs, soaked
    nk = P['neck']
    up = norm(P['neck'] - P['chest'])
    add(Cylinder(nk - up * 0.03, nk + up * 0.045, 0.068, 0.012), 'coat_trim', 0.0)
    for sx in (-1, 1):
        add(Capsule(nk + v3(sx * 0.045, -0.04, 0.08), P['pelvis'] + v3(sx * 0.012, 0.13, 0.095), 0.014, 0.010), 'coat_trim', 0.0)
    for s in ('r', 'l'):
        el, wr = P['el_' + s], P['wr_' + s]
        add(Capsule(el + (wr - el) * 0.75, wr, 0.046), 'coat_trim', 0.0)
    for i in range(3):
        t = 0.25 + i * 0.25
        c = (nk + v3(-0.065, -0.05, 0.092)) * (1 - t) + (P['pelvis'] + v3(-0.04, 0.14, 0.096)) * t
        add(Sphere(c, 0.009), 'button', 0.0)
    # spectacles: thin rims around the painted lenses
    H, R, h = P['head'], head_R(P), P['height']
    for sx in (-1, 1):
        add(Torus(H + R @ v3(sx * 0.035, 0.004, 0.088) * h, R[:, 2], 0.024, 0.0035), 'gold', 0.0)
    # the Wet Saint's rod
    if P.get('rod_fwd'):
        r = held(P, add, 'r', 'staff', shaft='rod', head='gold', below=0.35, above=1.25)
    else:
        r = held(P, add, 'r', 'staff', shaft='rod', head='gold', below=1.12, above=0.62)
    # the ledger
    pages = ledger(P, add, hand_pos(P, 'l'), P.get('ledger_open', 1.0))
    drips(P, add, pages + [P['pelvis'] + v3(-0.2, -0.66, 0.05), P['pelvis'] + v3(0.21, -0.68, -0.04)], fall=0.5)
    # the gently spreading puddle
    grow = 1.0 + 0.10 * P['tell'] + 0.25 * P['cast_glow']
    puddle(P, add, r=0.34, grow=grow, seed=2.0)
    ripples(P, add, n=2, r0=0.30 * grow)
    mats = {
        'coat': wet_cloth(_hex('#47595e'), wet=0.8, low_dark=0.40),
        'coat_trim': wet_cloth(_hex('#a9aa9c'), wet=0.6, low_dark=0.2),
        'trousers': wet_cloth(_hex('#3d4443'), wet=0.7),
        'button': Material(_hex('#7e7350'), spec=0.6, gloss=30, metal=0.6),
        'hair': Material(_hex('#3a3128'), spec=0.8, gloss=40, brush=0.05),
        'rod': Material(_hex('#3f3a30'), spec=0.4, gloss=26, brush=0.06),
        'cover': Material(_hex('#3a4a40'), spec=0.5, gloss=30, brush=0.06),
        'pages': Material(lambda p, n: np.array(_hex('#d8d3bd'))[None, :] * (0.82 + 0.25 * fbm(p, 40, 2)[:, None]),
                          spec=0.4, gloss=26, brush=0.04,
                          emissive=tuple(np.array(BRINE) * 0.4 * P['cast_glow']) if P['cast_glow'] > 0 else None),
        'skin': wet_skin(P, _hex('#d4b5a0'), hair=_hex('#3a3128'), spectacles=GOLD, eyes=_hex('#30383a')),
    }
    lights = []
    if P['cast_glow'] > 0:
        lights.append(Light(hand_pos(P, 'l') + v3(0, 0.1, 0.05), BRINE, 1.2 * P['cast_glow'], 0.2))
    return tide_finish(P, parts, mats, add, lights=lights, pool_r=0.6)


def _post(fr):
    # attack: points the rod at the target. cast: lifts the ledger high and reads aloud.
    for i, (P, lk) in enumerate(fr['attack']):
        P['item_l'] = v3(0, 0, 1)
        P['rod_fwd'] = True
    for i, (P, lk) in enumerate(fr['cast']):
        g = [v3(0.10, 1.30, 0.30), v3(0.12, 1.55, 0.30), v3(0.08, 1.30, 0.32)][i]
        rig.place_arm(P, 'l', g, (1, -0.6, -0.3))
        P['head_pitch'] = np.radians([0, -10, 10][i])
    for P, lk in fr['death']:
        P['ledger_open'] = 0.0
    return fr


ROWS, frames = tide_rows(neutral_pose, attack_style='thrust', weapon_side='r', cast_side='l', post=_post)

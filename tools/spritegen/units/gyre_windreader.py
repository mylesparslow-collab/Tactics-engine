"""Windreader (Gyre support healer, ground). An old roost-reader in a long grey oilskin and a feather shawl, a tall
kite-staff trailing beak-orange ribbons that all lean the wrong way, one hand raised to test the air.
Defining detail: the bells, feathers and tails on the kite-staff pointing against the wind."""
from _gyre_common import *

UNIT_ID = 'gyre_windreader'
LOOK = LOOK
C = Costume(top='oil', sleeve='oil', legs='oil_dk', boot='boot', hand='skin', skirt='robe', skirt_mat='oil_dk',
            hem=0.07, flare=0.75, head='hood', head_mat='wool', belt='cord', girth=0.92, boots_tall=False)


def neutral_pose():
    P = ground_pose(base_pose(height=0.90, build=0.86))
    rig.lean(P, fwd=np.radians(5))
    P['head_pitch'] = np.radians(-10)
    rig.place_arm(P, 'r', v3(-0.20, 0.98, 0.16), (-1, -0.3, -0.5), l1=0.25, l2=0.24)
    P['item_r'] = norm(v3(0.05, 1.0, 0.03))
    rig.place_arm(P, 'l', v3(0.30, 1.48, 0.16), (1, -0.3, -0.4), l1=0.25, l2=0.24)
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    h, b = P['height'], P['build']
    feather_mantle(P, add, rings=((0.17, 0.0, 0.09, 12), (0.23, -0.06, 0.12, 14)), scale=0.95, seed=4)
    add(capelet_shell(P, depth=0.14, width=0.17, sq=2.4), 'wool', 0.0)
    # kite-staff
    butt, tip = held(P, add, 'r', 'staff', shaft='drift', head='cord', below=0.9, above=0.62)
    d = norm(tip - butt)
    tell = P['tell']
    n_k = norm(v3(-0.5, 0.15, 0.85))
    Rk = basis_from(n_k, v3(0, 1, 0)) @ rot_y(0.785)
    kc = tip + d * 0.04 + v3(0, 0.10, 0)
    add(RoundBox(kc, (0.095, 0.006, 0.150), 0.003, Rk), 'canvas', 0.0)
    add(Capsule(kc - Rk[:, 2] * 0.15, kc + Rk[:, 2] * 0.15, 0.006, 0.006), 'wood', 0.0)
    add(Capsule(kc - Rk[:, 0] * 0.095, kc + Rk[:, 0] * 0.095, 0.005, 0.005), 'wood', 0.0)
    add(Sphere(kc, 0.016), 'cord', 0.0)
    # ribbon tails leaning the wrong way (into -z / +x), fluttering with the tell
    root = kc - Rk[:, 2] * 0.15
    wind = norm(v3(0.35, -0.2, -0.9))
    for j, (off, mat) in enumerate(((-0.02, 'cord'), (0.02, 'bone'), (0.0, 'cord'))):
        pt = root + v3(off, 0, 0)
        L0 = 0.20 + 0.06 * j
        for s_ in range(6):
            fl = np.sin(tell * 6.283 + s_ * 0.9 + j) * 0.04
            d2 = norm(wind + v3(fl, -0.15 - 0.05 * s_, fl * 0.5))
            nxt = pt + d2 * (L0 / 6)
            add(Capsule(pt, nxt, 0.007, 0.006), mat, 0.0)
            pt = nxt
    # bells and feathers on the staff
    for t, m in ((0.65, 'brass'), (0.78, 'brass')):
        add(Sphere(butt + d * (t * (np.linalg.norm(tip - butt))), 0.016), m, 0.0)
    for t in (0.0, 1.0):
        add(Capsule(tip - d * 0.25, tip - d * 0.25 + v3(0.12, -0.02, -0.10), 0.006, 0.004), 'feather_g', 0.0)
    if P['cast_glow'] > 0:
        add(Torus(kc, n_k, 0.12 + 0.12 * P['cast_glow'], 0.008), 'cord', 0.0)
    mats = gyre_mats(P, skin=hx('#c08f6c'), hair=hx('#d4d0c4'), coat=hx('#7b7869'), eyes=hx('#2a1d1a'))
    mats['skin'] = Material(face_albedo(P, hx('#c08f6c'), hx('#d4d0c4'), lips=hx('#a85a4c')), spec=0.06, gloss=12, sss=0.5, brush=0.02)
    return ground_finish(P, parts, mats)


ROWS, frames = ground_rows(neutral_pose, attack='swing', cast_side='l')

"""Guano Bombardier (Gyre flying siege). A heavy-set rider in leather helm and brass goggles perched aft on a big
cream-headed gannet, wings wide and level for a bombing run. Slung beneath the bird in a rope net cradle: a rack of
fat clay jars, wax-sealed and streaked with guano, one with a hissing fuse. The rider holds a lit jar over the side
on the attack and lets go. Defining detail: the clay jars swinging under the belly."""
from _gyre_w2 import *

UNIT_ID = 'gyre_guano_bombardier'
LOOK = LOOK_AIR
CAMERA = Camera(ppm=46)
S = species('gannet', half=0.94)


def hands(P, Q, S_):
    h = 0.88
    sh = Q['sh_r']
    a = P['arm']
    rig.place_arm(Q, 'r', sh + v3(-0.20 - 0.05 * a, -0.10 + 0.06 * a, 0.14 + 0.10 * a), (-1, -0.3, -0.2), l1=0.27 * h, l2=0.26 * h)


R = rider_cfg(h=0.95, b=1.0, girth=1.1, lean=0.05, head='cap', goggles=True, skin=hx('#c18d6a'), hands=hands,
              tail_len=0.36, mats=dict(coat=hx('#e2d6b6')))
R['look'] = -0.3


def neutral_pose():
    return fly_pose(fl=0.30, pitch=0.0, neckx=0.2, legs=0.5)


def jars(c, ph):
    W, add, F, P, S_ = c['W'], c['add'], c['F'], c['P'], c['S']
    k = S_['k']
    sw = P['swing'] * 0.5 + 0.06 * np.sin(P['tell'] * 6.283)
    n_hang = int(P['jars'])
    # cradle: two rails under the keel with a rope net, jars hang in two columns of two
    rail_a, rail_b = F.pt(v3(0, -0.15, 0.22) * k), F.pt(v3(0, -0.15, -0.26) * k)
    add(Capsule(rail_a, rail_b, 0.018, 0.018), 'wood', 0.0)
    slots = [(-1, 0.14), (1, 0.14), (-1, -0.12), (1, -0.12)]
    for j, (sx, z) in enumerate(slots):
        if j >= n_hang:
            break
        top = F.pt(v3(sx * 0.12, -0.14, z) * k)
        cen = top + v3(sx * 0.03 + sw * (1 + 0.3 * j) * 0.1, -0.20, 0.0)
        add(Capsule(top, cen + v3(0, 0.1, 0), 0.007, 0.006), 'net', 0.0)
        add(Capsule(top + v3(sx * -0.02, 0, 0.02), cen + v3(sx * 0.05, 0.05, 0.05), 0.005, 0.005), 'net', 0.0)
        add(Capsule(top + v3(sx * -0.02, 0, -0.02), cen + v3(sx * 0.05, 0.05, -0.05), 0.005, 0.005), 'net', 0.0)
        bomb_jar(add, cen, rot_z(-sx * sw * 0.8), size=1.15, fuse=1.0 if j == 0 else 0.0, seed=j)
        add(Torus(cen + v3(0, 0.02, 0), v3(0, 1, 0), 0.09, 0.006), 'net', 0.0)


def extra(c):
    W, add, F, P, mats = c['W'], c['add'], c['F'], c['P'], c['mats']
    extra_mats(mats)
    jars(c, 0)
    lights = []
    # the jar in the rider's hand (attack: raised then flung)
    g = hand_pos(W, 'r')
    if P['hold'] > 0:
        cj = g + v3(0, 0.07, 0.04) + P['throw'] * v3(-0.25, -0.35, 0.55)
        bomb_jar(add, cj, rot_z(0.3 * P['throw']), size=1.05, fuse=1.0, seed=7)
        lights.append(Light(cj + v3(0, 0.14, 0), hx('#ffb35c'), 0.9, 0.12))
    # dropped jars fall away below (attack)
    if P['drop'] > 0:
        for j in range(3):
            pc = F.t + v3(-0.30 + 0.30 * j, -0.2 - 0.55 * P['drop'] - 0.1 * j, 0.1 - 0.05 * j)
            bomb_jar(add, pc, rot_x(0.8 * P['drop'] + j), size=1.0, fuse=1.0 if j == 1 else 0.0, seed=j + 3)
        add(Ellipsoid(F.t + v3(-0.10, -1.0 * P['drop'] - 0.4, 0.1), (0.16 * P['drop'], 0.05, 0.14 * P['drop']), np.eye(3)), 'flash', 0.0) if P['drop'] > 0.9 else None
    # strap bandolier and a guano-stained rump on the rider's coat
    ch = W['chest']
    add(Capsule(ch + F.R @ v3(-0.13, 0.12, 0.07), ch + F.R @ v3(0.13, -0.12, 0.08), 0.014, 0.014), 'leather', 0.0)
    return lights


def build(P):
    return flier_build(P, S, R, extra, y0=0.78)


def neutral_extra(P):
    P.update(dict(jars=4, swing=0.0, hold=0.0, throw=0.0, drop=0.0, arm=0.0))
    return P


def tweak(rows):
    for nm in rows:
        for i, (P, o) in enumerate(rows[nm]):
            neutral_extra(P)
            P['swing'] = np.sin(i * 1.7) * 0.4
    for i, (P, o) in enumerate(rows['attack']):
        P['hold'] = [1, 1, 1, 0][i]
        P['arm'] = [0.2, 0.8, 1.0, 0.3][i]
        P['throw'] = [0.0, 0.0, 1.0, 0.0][i]
        P['drop'] = [0, 0.15, 0.55, 1.0][i]
        P['jars'] = 4 if i < 2 else 2
    for i, (P, o) in enumerate(rows['death']):
        P['jars'] = [4, 3, 1, 0][i]
    for i, (P, o) in enumerate(rows['cast']):
        P['hold'] = 1
        P['arm'] = [0.3, 0.9, 0.5][i]


_neutral0 = neutral_pose


def neutral_pose():       # noqa: F811
    return neutral_extra(_neutral0())


ROWS, frames = fly_rows(neutral_pose, tweak=tweak, idle_amp=0.5)

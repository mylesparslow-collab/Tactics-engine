"""Causeway Outrider (Salt Concord skirmisher).

Mounted courier of the salt roads: a lean salt-dun causeway pony in a squared steel-blue saddle cloth
and a brass-edged face plate, salt crusted to the hocks; the rider in a short steel-blue coat and low
kettle helm, a courier's dispatch tube on the back and a light lance flying a swallow-tailed pennant.
Defining detail: the lance pennant over a mounted silhouette.
"""
import numpy as np
from kit.humanoid import *
from kit.looks import LOOKS
from kit.xform import transform_parts
from render import Camera
from _salt_concord_common import *

UNIT_ID = 'salt_concord_causeway_outrider'
FACTION = 'salt_concord'
LOOK = LOOKS[FACTION]
CAMERA = Camera(ppm=46)

C = Costume(top='coat', sleeve='coat', legs='road', hand='glove', skirt=None, head='hair', hair='hair',
            hair_style='short', belt='leather', girth=0.92)
SEAT = 1.24
ZS = -0.18     # whole group shifted back so the pony's head stays in frame


def neutral_pose():
    P = base_pose(height=0.86, build=0.92)
    dy = v3(0, SEAT - P['pelvis'][1], -0.10)
    for k in list(P):
        if isinstance(P[k], np.ndarray) and P[k].shape == (3,):
            P[k] = P[k] + dy
    rig.place_leg(P, 'r', v3(-0.31, SEAT - 0.50, 0.04), l1=0.37, l2=0.36, pole=(-1, 0, 1))
    rig.place_leg(P, 'l', v3(0.31, SEAT - 0.50, 0.04), l1=0.37, l2=0.36, pole=(1, 0, 1))
    rig.place_arm(P, 'r', v3(-0.26, SEAT + 0.12, 0.08), (-1, -0.3, -0.4))
    P['item_r'] = norm(v3(-0.16, 1.0, 0.10))
    rig.place_arm(P, 'l', v3(0.08, SEAT + 0.10, 0.30), (1, -0.3, -0.4))
    P['foot_r_yaw'] = 0.0
    P['foot_l_yaw'] = 0.0
    P.update(gait=None, hbob=0.0, hpitch=0.0, neck=0.0, fold=0.0, tail=0.0)
    return P


def horse(P, add):
    fold = P['fold']
    by = 0.88 - 0.46 * fold
    add(Ellipsoid(v3(0, by, 0), (0.25, 0.28, 0.56)), 'coat_h', 0.0)
    add(Ellipsoid(v3(0, by + 0.04, 0.40), (0.24, 0.29, 0.26)), 'coat_h', 0.08)
    add(Ellipsoid(v3(0, by + 0.04, -0.40), (0.25, 0.29, 0.28)), 'coat_h', 0.08)
    # neck and head
    na = v3(0, by + 0.12, 0.50)
    nd = norm(v3(0, 0.80 - 0.5 * P['neck'] - 0.4 * fold, 0.60))
    nb = na + nd * 0.52
    add(Capsule(na, nb, 0.15, 0.095), 'coat_h', 0.06)
    hd = norm(v3(0, -0.75, 0.66) + v3(0, 0, 0.3 * P['neck']))
    hb = nb + hd * 0.34
    add(Capsule(nb, hb, 0.095, 0.062), 'coat_h', 0.04)
    for sx in (-1, 1):
        add(Capsule(nb + v3(sx * 0.04, 0.04, -0.02), nb + v3(sx * 0.055, 0.14, -0.04), 0.022, 0.006), 'coat_h', 0.01)
        add(Sphere(nb + hd * 0.12 + v3(sx * 0.07, 0.02, 0), 0.014), 'ink')                   # eyes
    # mane (squared, cropped) and brass-edged face plate
    add(RoundBox((na + nb) / 2 + v3(0, 0.10, -0.05), (0.025, 0.28, 0.05), 0.012, basis_from(nd, (0, 0, 1))), 'mane')
    add(RoundBox(nb + hd * 0.18 + norm(np.cross(v3(1, 0, 0), hd)) * -0.055, (0.06, 0.13, 0.012), 0.006,
                 basis_from(hd, np.cross(v3(1, 0, 0), hd) * -1)), 'faceplate')
    # tail
    ta = v3(0, by + 0.12, -0.62)
    add(Capsule(ta, ta + v3(0.05 * P['tail'], -0.50 + 0.2 * fold, -0.14), 0.05, 0.035), 'mane', 0.02)
    # squared saddle cloth with salt border, saddle
    add(RoundBox(v3(0, by + 0.10, -0.05), (0.265, 0.15, 0.24), 0.03), 'cloth', 0.0)
    add(RoundBox(v3(0, by + 0.27, -0.05), (0.15, 0.04, 0.16), 0.03), 'leather', 0.0)
    # legs
    g = P['gait']
    for (sx, zz, fr) in ((-1, 0.40, True), (1, 0.40, True), (-1, -0.40, False), (1, -0.40, False)):
        top = v3(sx * 0.12, by - 0.08, zz)
        if fold > 0:
            hoof = v3(sx * 0.16, 0.05, zz + (0.30 if fr else -0.15) * fold)
        else:
            ph = 0.0 if g is None else g + (0.0 if (sx > 0) == fr else 0.5)
            sw = np.sin(ph * 2 * np.pi) if g is not None else 0.0
            lift = max(0.0, np.cos(ph * 2 * np.pi)) * 0.16 if g is not None else 0.0
            hoof = v3(sx * 0.13, 0.05 + lift, zz + 0.18 * sw + (0.03 if fr else -0.02))
        L1, L2 = 0.42, 0.42
        knee = rig.two_bone(top, hoof, L1, L2, (0, 0, 1) if fr else (0, 0, -1))
        add(Capsule(top, knee, 0.09, 0.05), 'coat_h', 0.04)
        add(Capsule(knee, hoof, 0.045, 0.036), 'leg_h', 0.01)
        add(Cylinder(hoof + v3(0, -0.045, 0.01), hoof + v3(0, 0.0, 0.01), 0.045, 0.01), 'hoof')


def build(P):
    parts, add = new_parts()
    horse(P, add)
    hparts = list(parts)
    parts.clear()
    body(P, add, C)
    kettle_helm(P, add, 'helmiron', size=1.0, brim=0.85, tall=0.85)
    nk, ch = P['neck'], P['chest']
    add(Cylinder(nk + v3(0, -0.03, -0.005), nk + v3(0, 0.03, -0.012), 0.068, 0.01), 'salt')
    # scarf streaming back
    add(Capsule(nk + v3(0.02, -0.02, -0.06), nk + v3(0.08, -0.10, -0.30), 0.03, 0.012), 'salt', 0.01)
    # dispatch tube on the back
    add(Cylinder(ch + v3(-0.12, -0.12, -0.13), ch + v3(0.14, 0.20, -0.13), 0.04, 0.008), 'leather')
    add(Cylinder(ch + v3(0.13, 0.19, -0.13), ch + v3(0.155, 0.225, -0.13), 0.046, 0.006), 'brass')
    for s in ('r', 'l'):
        el, wr = P['el_' + s], P['wr_' + s]
        add(Capsule(el + (wr - el) * 0.72, wr - (wr - el) * 0.02, 0.047), 'salt')
    # reins from the left hand to the bit
    r = held(P, add, 'r', 'pike', shaft='wood', head='steel', below=0.55, above=1.30)
    if r is not None:
        butt, tip = r
        d = norm(tip - butt)
        pennant(add, tip - d * 0.17, length=0.40, height=0.15, sway=np.sin(P['tell'] * 6.28),
                direction=norm(v3(0.35, -0.1, -1.0) - d * 0.3), phase=P['tell'] * 6.28, swallow=True)
    rparts = list(parts)
    parts.clear()
    # whole group: horse pitch/bob; rider rides along
    R = rot_x(-P['hpitch'])
    hp = transform_parts(hparts, R=R, t=(0, P['hbob'], ZS), pivot=(0, 0.9, -0.3))
    rp = transform_parts(rparts, R=R, t=(0, P['hbob'], ZS), pivot=(0, 0.9, -0.3))
    parts.extend(hp + rp)
    mats = base_mats(P)

    def cloth(p, n):
        a = np.array(STEEL)[None, :].repeat(len(p), 0) * (0.93 + 0.1 * fbm(p, 20, 2)[:, None])
        y = p[:, 1] - P['hbob']
        edge = y < (0.88 - 0.46 * P['fold'] + 0.10 - 0.11)
        a[edge] = SALT
        return salt_seams(a, p, 0.3, 26, 0.0, 0.0)
    mats.update({
        'coat': salted(STEEL, 0.3),
        'coat_h': salted(_hex('#b3a68e'), 0.3, ground=0.55, gamt=1.0, vary=0.12, spec=0.12, gloss=16),
        'leg_h': salted(_hex('#8a7d68'), 0.5, ground=0.6, gamt=1.2),
        'mane': Material(_hex('#3a3029'), spec=0.15, brush=0.12),
        'hoof': Material(_hex('#2b2622'), spec=0.2),
        'cloth': Material(cloth, spec=0.04, brush=0.07),
        'faceplate': salted_metal(_hex('#8c939c'), amount=0.4),
        'hair': Material(_hex('#3b2a20'), spec=0.2, brush=0.1),
        'skin': skin_mat(P, skin=W['skin_mid'], hair=_hex('#3b2a20')),
    })
    return finish(P, FACTION, parts, mats)


ROWS = [
    ('idle', 4, True, {}),
    ('move', 8, True, {}),
    ('attack', 10, False, {'hitFrame': 2}),
    ('hit', 10, False, {}),
    ('death', 6, False, {'holdLast': True}),
    ('cast', 8, False, {}),
]


def _idle(i):
    P = neutral_pose()
    b = [0, 1, 0, -1][i]
    P['breathe'] = b
    P['hbob'] = 0.006 * b
    rig.shift(P, rig.UPPER, v3(0, 0.006 * b, 0))
    P['neck'] = [0.0, 0.08, 0.15, 0.06][i]
    P['tail'] = [0, 0.6, 0, -0.6][i]
    P['tell'] = i / 4
    return P, {}


def _move(i):
    P = neutral_pose()
    P['gait'] = i / 4
    P['hbob'] = [0.03, -0.01, 0.03, -0.01][i]
    P['hpitch'] = [0.03, -0.02, 0.03, -0.02][i]
    rig.shift(P, rig.UPPER, v3(0, -0.01 * [1, -1, 1, -1][i], 0.02))
    P['neck'] = [-0.1, 0.1, -0.1, 0.1][i]
    P['tail'] = [1, 0.5, 1, 0.5][i]
    P['tell'] = i / 4
    return P, {}


def _attack(i):
    P = neutral_pose()
    d = [norm(v3(-0.1, 1.0, -0.5)), norm(v3(-0.2, 0.3, 1.0)), norm(v3(-0.15, -0.12, 1.0)), norm(v3(-0.15, 0.1, 1.0))][i]
    w = [v3(-0.26, SEAT + 0.30, -0.12), v3(-0.26, SEAT + 0.16, 0.0), v3(-0.24, SEAT + 0.12, 0.22),
         v3(-0.25, SEAT + 0.12, 0.10)][i]
    rig.lean(P, fwd=np.radians([-6, 4, 14, 6][i]))
    rig.place_arm(P, 'r', w, (-1, -0.3, -0.6))
    P['item_r'] = d
    P['hpitch'] = [0.06, 0.0, -0.06, -0.02][i]
    P['hbob'] = [0.02, 0.0, -0.02, 0.0][i]
    P['gait'] = [None, 0.25, 0.5, None][i]
    P['neck'] = [0.1, -0.1, -0.2, 0][i]
    return P, {}


def _hit(i):
    P = neutral_pose()
    rig.lean(P, fwd=np.radians([-12, -4][i]))
    P['hpitch'] = [0.06, 0.02][i]
    P['neck'] = [0.3, 0.1][i]
    return P, (dict(exposure=1.25, flash=0.22) if i == 0 else {})


def _death(i):
    P = neutral_pose()
    f = [0.0, 0.35, 0.8, 0.85][i]
    P['fold'] = f
    dy = -0.46 * f
    rig.shift(P, tuple(k for k in P if isinstance(P[k], np.ndarray) and P[k].shape == (3,)), v3(0, dy, 0))
    rig.lean(P, fwd=np.radians([-12, 15, 35, 40][i]))
    rig.place_arm(P, 'r', P['pelvis'] + v3(-0.20, 0.0, 0.25), (-1, 0, -0.5))
    rig.place_arm(P, 'l', P['pelvis'] + v3(0.20, 0.0, 0.25), (1, 0, -0.5))
    P['item_r'] = norm(v3(-0.6, -0.15, 0.8)) if i > 0 else P['item_r']
    P['head_pitch'] = np.radians([12, 20, 35, 35][i])
    P['neck'] = [0.3, 0.6, 1.0, 1.1][i]
    P['hpitch'] = [0.08, -0.05, -0.08, -0.08][i]
    P['end'] = [0, 0.15, 0.5, 1.0][i]
    return P, {}


def _cast(i):
    P = neutral_pose()
    # causeway dash: the pony rears a little, the rider raises the lance high and points
    P['hpitch'] = [0.08, 0.16, 0.04][i]
    P['neck'] = [0.2, 0.35, 0.0][i]
    rig.place_arm(P, 'r', v3(-0.26, SEAT + [0.20, 0.32, 0.16][i], 0.06), (-1, -0.3, -0.4))
    rig.place_arm(P, 'l', v3(0.20, SEAT + [0.30, 0.52, 0.25][i], 0.32), (1, -0.4, -0.3))
    rig.lean(P, fwd=np.radians([-4, -8, 2][i]))
    P['tail'] = [0.5, 1.0, 0.3][i]
    return P, {}


def frames():
    return {
        'idle': [_idle(i) for i in range(4)],
        'move': [_move(i) for i in range(4)],
        'attack': [_attack(i) for i in range(4)],
        'hit': [_hit(i) for i in range(2)],
        'death': [_death(i) for i in range(4)],
        'cast': [_cast(i) for i in range(3)],
    }

"""Rainwatch Inquisitor (Salt Concord anti-caster).

Tall, narrow, white oilcloth hooded coat with a steel-blue stole, a pale salt-cloth mask over the
mouth, brass rain-lens on the hood and a heavy brass salt censer on a chain that swings and pours
white smoke. A brass rain-gauge funnel on the back. Defining detail: the swinging censer.
"""
import numpy as np
from kit.humanoid import *
from kit.anim import humanoid_rows
from kit.looks import LOOKS
from _salt_concord_common import *

UNIT_ID = 'salt_concord_rainwatch_inquisitor'
FACTION = 'salt_concord'
LOOK = LOOKS[FACTION]

C = Costume(top='oil', sleeve='oil', legs='dark', hand='glove', skirt='robe', skirt_mat='oil',
            hem=0.07, flare=0.75, head='hood', head_mat='hoodm', belt='leather', girth=0.92, boots_tall=True)


def neutral_pose():
    P = base_pose(height=1.07, build=0.88)
    rig.lean(P, fwd=np.radians(2))
    P['head_yaw'] = np.radians(-8)
    rig.place_arm(P, 'r', v3(-0.44, 1.12, 0.16), (-1, -0.3, -0.3))
    P['item_r'] = norm(v3(0.0, -1.0, 0.0))
    rig.place_arm(P, 'l', v3(0.17, 1.10, 0.20), (0.3, -0.5, -1))
    P['swing'] = v3(0, 0, 0)
    return P


def censer(add, lights, P):
    g = hand_pos(P, 'r')
    sw = P.get('swing', v3(0, 0, 0))
    top = g + v3(0, 0.02, 0)
    c = g + v3(sw[0], -0.34, sw[2])
    chain(add, top, c + v3(0, 0.07, 0), sag=0.0, n=6, r=0.014)
    # squared brass censer: lidded box with pierced-glow slits, finial and hanging salt-pouch
    d = norm(c + v3(0, 0.07, 0) - top)
    R = basis_from(d * -1, (0, 0, 1))
    add(RoundBox(c, (0.095, 0.095, 0.095), 0.02, R), 'brass', 0.0)
    add(RoundBox(c + R[:, 1] * 0.085, (0.060, 0.034, 0.060), 0.014, R), 'brass', 0.0)
    add(Sphere(c + R[:, 1] * 0.14, 0.020), 'brass', 0.0)
    for sx in (-1, 1):
        add(RoundBox(c + R[:, 0] * sx * 0.058 + R[:, 2] * 0.01, (0.006, 0.040, 0.030), 0.003, R), 'ember', 0.0)
        add(RoundBox(c + R[:, 2] * sx * 0.058, (0.030, 0.040, 0.006), 0.003, R), 'ember', 0.0)
    add(Torus(c - R[:, 1] * 0.02, R[:, 1], 0.063, 0.008), 'iron', 0.0)
    lights.append(Light(pos=c + v3(0, 0, 0.05), color=_hex('#ffd9a0'), intensity=0.9 * P['glow'], radius=0.14))
    # white salt smoke
    smoke_amt = 0.8 + 0.4 * P['cast_glow']
    t = P['tell'] * 6.283
    for k in range(5):
        off = v3(0.025 * np.sin(t + k * 1.7) * (k + 1) * 0.5, 0.10 + 0.075 * k, 0.025 * np.cos(t + k * 1.3) * (k + 1) * 0.5)
        add(Sphere(c + R[:, 1] * 0.15 + (off + v3(0.05, 0, 0.04)) * 1.3, (.050 + 0.020 * k) * smoke_amt), 'smoke', 0.02)


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    H, R, h = P['head'], head_R(P), P['height']
    # steel-blue stole front and back, squared shoulder cape in oilcloth
    tabard(P, add, 'stole', width=0.065, hem=0.20, top=0.30, zf=0.125, zb=0.13)
    add(capelet_shell(P, depth=0.17, width=0.20, sq=4.5), 'oil2')
    add(Torus(nk + v3(0, -0.01, 0), v3(0, 1, 0), 0.085, 0.014), 'stole', 0.0)
    # salt-cloth mask under the hood, brass rain-lens on the brow
    add(RoundBox(H + R @ v3(0, -0.045, 0.07) * h, (0.055, 0.034, 0.030), 0.014, R), 'mask', 0.0)
    add(Cylinder(H + R @ v3(0.0, 0.082, 0.090) * h, H + R @ v3(0.0, 0.082, 0.108) * h, 0.026, 0.006), 'brass', 0.0)
    add(Cylinder(H + R @ v3(0.0, 0.082, 0.104) * h, H + R @ v3(0.0, 0.082, 0.114) * h, 0.019, 0.003), 'glass', 0.0)
    add(Torus(H + R @ v3(0, 0.0, 0.0) * h, R[:, 1], 0.115 * h, 0.012), 'stole', 0.0)
    add(Torus(pel + v3(0, 0.07, 0), v3(0, 1, 0), 0.155, 0.022), 'stole', 0.0)
    # rain-gauge funnel on the back and a wooden frame
    add(Cylinder(ch + v3(0.0, 0.0, -0.13), ch + v3(0.0, 0.26, -0.15), 0.035, 0.008), 'brass', 0.0)
    add(Func(lambda p, a=ch + v3(0.0, 0.26, -0.15): np.maximum(
        np.sqrt((p[:, 0] - a[0]) ** 2 + (p[:, 2] - a[2]) ** 2) - (0.03 + 0.07 * np.clip((p[:, 1] - a[1]) / 0.11, 0, 1)),
        np.maximum(a[1] - p[:, 1], p[:, 1] - a[1] - 0.11)), ch + v3(0, 0.32, -0.15), 0.18), 'brass', 0.0)
    # censer
    censer(add, lights, P)
    # gloves: pale gauntlet cuffs
    for s in ('r', 'l'):
        el, wr = P['el_' + s], P['wr_' + s]
        add(Capsule(el + (wr - el) * 0.72, wr - (wr - el) * 0.02, 0.048), 'oil2')
    mats = base_mats(P)
    oil = _hex('#dcd8c9')
    mats.update({
        'oil': salted(_hex('#4b6784'), 0.18, ground=0.5, gamt=0.7, vary=0.07, spec=0.30, gloss=22, brush=0.07),
        'hoodm': salted(_hex('#b9c4cc'), 0.15, ground=0.0, gamt=0.0, vary=0.07, spec=0.3, gloss=22, brush=0.07),
        'boot': Material(_hex('#1e222a'), spec=0.25, gloss=24, brush=0.05),
        'dark': Material(_hex('#262d38'), spec=0.2, gloss=16, brush=0.05),
        'oil2': salted(_hex('#34485f'), 0.2, ground=0.0, gamt=0.0, vary=0.08, spec=0.3, gloss=22),
        'stole': salted(_hex('#1f2a3d'), 0.12, ground=0.0, gamt=0.0, spec=0.2, gloss=16),
        'mask': salted(_hex('#e8e3d4'), 0.1, ground=0.0, gamt=0.0, spec=0.02),
        'glove': Material(_hex('#2a2622'), spec=0.2, gloss=16, brush=0.05),
        'ember': Material(_hex('#ffb866'), emissive=tuple(np.array(_hex('#ff9a40')) * min(P['glow'] + P['cast_glow'], 2.0)), rim=0.0),
        'smoke': Material(_hex('#f2f0e8'), spec=0.0, brush=0.1, rim=0.5),
        'skin': skin_mat(P, skin=W['skin_light'], hair=_hex('#d9d4c8')),
        'hair': Material(_hex('#d9d4c8'), spec=0.2),
    })
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, _frames = humanoid_rows(neutral_pose, attack_style='swing', weapon_side='r', cast_side='l')


def frames():
    f = _frames()
    for row, fr in f.items():
        for i, (P, lo) in enumerate(fr):
            t = P['tell'] * 6.283
            if row == 'idle':
                P['swing'] = v3(0.05 * np.sin(t), 0, 0.07 * np.cos(t))
            elif row == 'move':
                P['swing'] = v3(0.0, 0, [0.10, 0.0, -0.10, 0.0][i])
            elif row == 'attack':
                P['swing'] = [v3(0.0, 0, -0.14), v3(0.05, 0, 0.18), v3(0.0, 0.0, 0.34), v3(0, 0, 0.18)][i]
                P['swing'] = P['swing'] + v3(0, 0.0, 0)
                P['cast_glow'] = [0.0, 0.2, 0.8, 0.3][i]
            elif row == 'cast':
                P['swing'] = v3(0, 0, 0.08)
            elif row == 'hit':
                P['swing'] = v3(0, 0, [-0.18, -0.06][i])
    return f

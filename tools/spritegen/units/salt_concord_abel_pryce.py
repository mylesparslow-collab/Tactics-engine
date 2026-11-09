"""Surveyor-Royal Abel Pryce (Salt Concord hero).

The Concord's chief cartographer: tall, stooped, wild white hair and round brass spectacles, a long ink-navy
greatcoat with a salt-white hem and squared steel-blue shoulder cape, a brass chain of office, a leather map
case across the back with scrolls sticking out, a satchel of rolled charts, a brass theodolite carried in the
left hand (it lights up when he casts) and a bundled survey tripod used as a walking staff with a plumb bob.
Defining detail: the brass theodolite and the map case.
"""
import numpy as np
from kit.humanoid import *
from kit.anim import humanoid_rows
from kit.looks import LOOKS
from _salt_concord_common import *

UNIT_ID = 'salt_concord_abel_pryce'
FACTION = 'salt_concord'
LOOK = LOOKS[FACTION]

NAVY = _hex('#2d3d55')
C = Costume(top='coat', sleeve='coat', legs='road', hand='glove', skirt='coat', skirt_mat='coat', hem=0.26,
            flare=1.05, head='hair', hair='hair', hair_style='short', belt='leather', girth=1.05)


def neutral_pose():
    P = base_pose(height=1.08, build=0.92)
    rig.lean(P, fwd=np.radians(5))
    P['head_yaw'] = np.radians(-4)
    P['head_pitch'] = np.radians(-2)
    rig.place_arm(P, 'r', v3(-0.27, 1.02, 0.18), (-1, -0.4, -0.5))
    P['item_r'] = norm(v3(0.0, 1.0, 0.08))
    rig.place_arm(P, 'l', v3(0.15, 1.18, 0.30), (0.5, -0.5, -0.5))
    P['item_l'] = norm(v3(-0.2, 0.15, 1.0))      # theodolite telescope direction
    return P


def theodolite(P, add, lights, size=1.25):
    g = hand_pos(P, 'l') + v3(0, 0.02, 0.01)
    s = size
    cg = P['cast_glow']
    # tripod head plate, standards, telescope, graduated circle
    add(Cylinder(g + v3(0, 0.0, 0), g + v3(0, 0.025 * s, 0), 0.050 * s, 0.006), 'brass', 0.0)
    for k in range(3):
        a = k * 2.094
        add(Capsule(g, g + v3(0.04 * np.sin(a), -0.06, 0.04 * np.cos(a)) * s, 0.012), 'wood', 0.0)
    c = g + v3(0, 0.12 * s, 0)
    d = norm(P['item_l'])
    sv = norm(np.cross(d, v3(0, 1, 0)))
    for sg in (-1, 1):
        add(Capsule(g + v3(0, 0.02 * s, 0) + sv * sg * 0.05 * s, c + sv * sg * 0.052 * s, 0.012 * s), 'brass', 0.0)
    add(Capsule(c - d * 0.09 * s, c + d * 0.13 * s, 0.026 * s, 0.020 * s), 'brass', 0.0)         # telescope
    add(Cylinder(c + d * 0.12 * s, c + d * 0.17 * s, 0.034 * s, 0.006), 'brass', 0.0)             # objective hood
    add(Cylinder(c + d * 0.165 * s, c + d * 0.175 * s, 0.026 * s, 0.003), 'lens', 0.0)
    add(Torus(g + v3(0, 0.05 * s, 0), v3(0, 1, 0), 0.056 * s, 0.007), 'brass', 0.0)               # horizontal circle
    add(Torus(c + sv * 0.055 * s, sv, 0.040 * s, 0.006), 'brass', 0.0)                            # vertical circle
    add(Sphere(c - d * 0.095 * s + v3(0, 0.02, 0), 0.012), 'brass', 0.0)                          # eyepiece
    lights.append(Light(pos=c + d * 0.2, color=_hex('#ffd9a0'), intensity=0.4 + 1.2 * cg, radius=0.16))
    if cg > 0.05:      # cast: a pale surveyor's beam streams out of the objective
        for k in range(1, 6):
            add(Sphere(c + d * (0.18 + 0.12 * k * cg), 0.016 * cg), 'beam', 0.0)


def tripod_staff(P, add):
    d = P['item_r']
    if d is None:
        return None
    d = norm(d)
    g = hand_pos(P, 'r')
    butt, tip = g - d * 0.62, g + d * 0.42
    sv = norm(np.cross(d, v3(0, 0, 1)))
    ov = norm(np.cross(d, sv))
    for k in range(3):
        a = k * 2.094 + 0.5
        off = (sv * np.cos(a) + ov * np.sin(a))
        add(Capsule(butt + off * 0.04, tip + off * 0.012, 0.021, 0.018), 'wood', 0.0)
        add(Capsule(butt + off * 0.04, butt + off * 0.04 + d * 0.07, 0.024), 'brass', 0.0)
    add(Torus(tip - d * 0.06, d, 0.026, 0.010), 'brass', 0.0)
    add(Torus(g + d * 0.14, d, 0.030, 0.008), 'leather', 0.0)
    add(Cylinder(tip, tip + d * 0.05, 0.030, 0.006), 'brass', 0.0)
    # plumb bob on a chain
    chain(add, tip + d * 0.03, tip + d * 0.03 + v3(0.02, -0.25, 0.07), sag=0.0, n=4, r=0.008)
    add(Capsule(tip + d * 0.03 + v3(0.02, -0.26, 0.07), tip + d * 0.03 + v3(0.02, -0.33, 0.07), 0.022, 0.004), 'brass', 0.0)
    return butt, tip


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    H, R, h = P['head'], head_R(P), P['height']
    # squared steel-blue cape with a salt edge, high stiff collar
    add(capelet_shell(P, depth=0.19, width=0.22, sq=4.6), 'cape')
    add(Cylinder(nk + v3(0, -0.035, -0.005), nk + v3(0, 0.035, -0.012), 0.072, 0.012), 'salt')
    # hand-sewn salt cuffs and a salt-white hem band
    for s in ('r', 'l'):
        el, wr = P['el_' + s], P['wr_' + s]
        add(Capsule(el + (wr - el) * 0.70, wr - (wr - el) * 0.02, 0.049), 'salt')
    # brass chain of office with a medallion, and brass buttons down the coat
    for k in range(7):
        t = k / 6
        a = np.pi * (0.1 + 0.8 * t)
        add(Sphere(nk + v3(-np.cos(a) * 0.10, -0.045 - 0.12 * np.sin(a), 0.07 * np.sin(a) + 0.02), 0.010), 'brass', 0.0)
    add(Cylinder(ch + v3(0.0, 0.10, 0.108), ch + v3(0.0, 0.10, 0.118), 0.030, 0.004), 'brass', 0.0)
    for k in range(4):
        add(Sphere(ch + v3(0.0, 0.06 - 0.075 * k, 0.108 + 0.002 * k), 0.0105), 'brass', 0.0)
    # round brass spectacles, white eyebrow and long grey beard
    for sx in (-1, 1):
        c = H + R @ v3(sx * 0.034, 0.008, 0.088) * h
        add(Torus(c, R @ v3(0, 0, 1), 0.024, 0.0045), 'brass', 0.0)
        add(Cylinder(c + R @ v3(0, 0, 0.0), c + R @ v3(0, 0, 0.003), 0.021, 0.002), 'specs', 0.0)
    add(Capsule(H + R @ v3(-0.034, 0.008, 0.088) * h, H + R @ v3(0.034, 0.008, 0.088) * h, 0.0035), 'brass', 0.0)
    # map case across the back, scrolls poking out of both caps
    a = pel + v3(-0.20, -0.24, -0.16)
    b = ch + v3(0.22, -0.10, -0.16)
    d = norm(b - a)
    add(Capsule(a, b, 0.048), 'case', 0.0)
    for end, sg in ((a, -1), (b, 1)):
        add(Cylinder(end, end + d * sg * 0.03, 0.054, 0.008), 'brass', 0.0)
    for t in (0.25, 0.55, 0.8):
        add(Torus(a + (b - a) * t, d, 0.049, 0.007), 'brass', 0.0)
    add(Capsule(b + d * 0.02, b + d * 0.08 + v3(0.02, -0.02, -0.02), 0.020), 'paper', 0.0)
    add(Capsule(ch + v3(-0.12, 0.17, 0.09), pel + v3(0.15, 0.02, 0.11), 0.014), 'leather')   # case sling
    # satchel of rolled charts on the right hip
    add(RoundBox(pel + v3(-0.21, -0.03, 0.02), (0.055, 0.075, 0.095), 0.022), 'leather')
    add(Capsule(pel + v3(-0.21, 0.04, -0.07), pel + v3(-0.21, 0.20, -0.02), 0.020), 'paper', 0.0)
    add(Capsule(pel + v3(-0.25, 0.04, -0.04), pel + v3(-0.28, 0.18, 0.0), 0.017), 'paper', 0.0)
    # brass dividers tucked in the belt
    add(Capsule(pel + v3(0.13, 0.04, 0.10), pel + v3(0.16, -0.10, 0.12), 0.007), 'brass', 0.0)
    add(Capsule(pel + v3(0.15, 0.04, 0.10), pel + v3(0.19, -0.10, 0.13), 0.007), 'brass', 0.0)
    tripod_staff(P, add)
    theodolite(P, add, lights)
    mats = base_mats(P)
    mats.update({
        'coat': salted(NAVY, 0.3, ground=0.55, gamt=1.2, vary=0.10, brush=0.08),
        'cape': salted(STEEL, 0.35, ground=0.0, gamt=0.0),
        'road': salted(_hex('#6c6e72'), 0.3, ground=0.5, gamt=1.0),
        'hair': Material(_hex('#e8e4da'), spec=0.2, brush=0.1),
        'skin': skin_mat(P, skin=W['skin_light'], hair=_hex('#cfcabd'), beard=None),
        'case': Material(_hex('#5a4030'), spec=0.22, gloss=20, brush=0.08),
        'paper': Material(_hex('#d9cfae'), spec=0.04, brush=0.06),
        'specs': Material(_hex('#cfe3ee'), spec=0.9, gloss=60, emissive=tuple(np.array(_hex('#cfe3ee')) * 0.15), rim=0.0),
        'lens': Material(_hex('#9fd2e8'), spec=1.0, gloss=60, emissive=tuple(np.array(_hex('#bfe6f5')) * (0.5 + 1.5 * P['cast_glow'])), rim=0.0),
        'beam': Material(_hex('#e9f6ff'), emissive=tuple(np.array(_hex('#cfeaff')) * 1.6), rim=0.0),
    })
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, _frames = humanoid_rows(neutral_pose, attack_style='swing', weapon_side='r', cast_side='l')


def frames():
    f = _frames()
    # theodolite hand: keep it lifted at chest in every row except death; the cast raises it to the eye
    for row, fr in f.items():
        for i, (P, lo) in enumerate(fr):
            if row == 'cast':
                P['item_l'] = norm(v3(-0.2, [0.1, 0.2, 0.05][i], 1.0))
                g = [v3(0.12, 1.30, 0.28), v3(0.06, 1.46, 0.34), v3(0.10, 1.34, 0.44)][i]
                rig.place_arm(P, 'l', g * v3(1, 1.0, 1) * 1.0, (0.4, -0.5, -0.6))
            elif row in ('idle', 'move', 'hit', 'attack'):
                P['item_l'] = norm(v3(-0.2, 0.15, 1.0))
                if P['item_l'] is not None and row != 'death':
                    base = neutral_pose()
                    dp = P['pelvis'] - base['pelvis']
                    if row in ('move', 'idle'):
                        rig.place_arm(P, 'l', base['wr_l'] + dp * 0.9, (0.4, -0.5, -0.6))
                    else:
                        rig.place_arm(P, 'l', P['sh_l'] + v3(-0.03, -0.30, 0.30), (0.4, -0.5, -0.6))
            else:
                P['item_l'] = norm(v3(0, -0.5, 1.0))
    return f

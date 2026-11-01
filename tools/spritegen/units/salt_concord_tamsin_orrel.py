"""Commander Tamsin Orrel, Surveyor-Commander of Lantern Shoal (Salt Concord hero).

Art direction: one hand on a surveying staff, looking past the viewer. Long steel-blue coat,
Survey Blade, rolled chart case, a lit night lamp on her belt. Young and thin. Salt crust
on every seam.

The figure is built from a pose (a dict of joint positions and a few scalars) so the same
sculpt drives every animation frame.
"""
import numpy as np
from sdf import (v3, norm, basis_from, rot_y, rot_x, Sphere, Ellipsoid, Capsule, RoundBox,
                 Cylinder, Torus, Func, Subtract, Union, smax, smin, fbm, vnoise)
from render import Material, Part, Light, Scene, _hex

UNIT_ID = "salt_concord_tamsin_orrel"

# ---------------------------------------------------------------- palette (Concord sheet)
STEEL = _hex('#56728f')
STEEL_DK = _hex('#3d546c')
SALT = _hex('#e2ddcf')
ROAD = _hex('#7b7d80')
INK = _hex('#1d2a3a')
BRASS = _hex('#b8924a')
LEATHER = _hex('#4d3526')
BOOT = _hex('#33261d')
SKIN = _hex('#e0ad8c')
HAIR = _hex('#5b3020')
WOOD = _hex('#6e4c31')
LAMP = _hex('#ffcf7a')


def neutral_pose():
    """Standing still: weight on the right leg, left hand on the staff."""
    P = dict(
        pelvis=v3(0.0, 0.94, 0.0),
        chest=v3(0.0, 1.27, -0.005),
        neck=v3(0.0, 1.46, 0.0),
        head=v3(0.0, 1.585, 0.015),
        head_yaw=np.radians(-12),     # turn toward her right (camera side): looking past the viewer
        head_pitch=np.radians(-2),
        sh_r=v3(-0.185, 1.415, -0.01), el_r=v3(-0.235, 1.15, -0.03), wr_r=v3(-0.215, 0.93, 0.03),
        sh_l=v3(0.185, 1.415, -0.01), el_l=v3(0.29, 1.19, 0.03), wr_l=v3(0.285, 1.19, 0.20),
        hip_r=v3(-0.085, 0.92, 0.0), kn_r=v3(-0.095, 0.50, 0.01), an_r=v3(-0.10, 0.085, -0.02),
        hip_l=v3(0.085, 0.92, 0.0), kn_l=v3(0.12, 0.50, 0.07), an_l=v3(0.135, 0.085, 0.07),
        foot_r_yaw=np.radians(-18), foot_l_yaw=np.radians(12),
        staff_base=v3(0.30, 0.0, 0.28), staff_top=v3(0.285, 2.06, 0.19),
        coat_sway=0.0,                # hem swing (-1..1)
        lamp_swing=0.0,               # radians
        lamp_glow=1.0,
        breathe=0.0,
        crust=0.0,
        ring_glow=0.0,
        blade=None,                   # direction of the drawn Survey Blade, None = sheathed                # cast tell: the brass sighting ring lights up                    # death end state: salt crust over everything (0..1)
    )
    return P


# ---------------------------------------------------------------- material functions

def coat_albedo(p, n, P):
    """Steel-blue coat, pale salt trim on the front edges and hem, salt bloom low down."""
    base = np.array(STEEL)[None, :].repeat(len(p), 0)
    x, y, z = p[:, 0] - P['pelvis'][0], p[:, 1] - (P['pelvis'][1] - 0.94), p[:, 2] - P['pelvis'][2]
    theta = np.arctan2(x, z)
    w = coat_open_angle(y)
    trim = (np.abs(theta) - w < 0.16) & (y < 1.02) & (z > 0)
    hem = y < hem_y(theta, P) + 0.045
    t = (trim | hem)
    base[t] = SALT
    # darker steel lining visible inside the opening
    inner = (np.abs(theta) < w + 0.02) & (y < 1.0)
    base[inner] = np.array(STEEL_DK)
    # salt bloom: white crust creeping up from the hem with noise
    crust = np.clip((0.62 - y) / 0.30, 0, 1) * fbm(p, 22.0, 3)
    c = np.clip((crust - 0.28) * 3.0, 0, 1)[:, None]
    base = base * (1 - c) + np.array(SALT)[None, :] * c
    return base


def hem_y(theta, P):
    return 0.30 + 0.02 * np.sin(theta * 3 + 1.0)


def coat_open_angle(y):
    return np.clip((1.0 - y) / 0.70, 0, 1) ** 0.8 * 0.52


def skin_albedo(p, n, P):
    """Face paint: eyes, brows, lips and warm cheeks placed in head-local coordinates."""
    R = head_R(P)
    q = (p - P['head']) @ R
    base = np.array(SKIN)[None, :].repeat(len(p), 0)
    front = q[:, 2] > 0.04
    # eyes: dark almond spots
    for sx in (-1, 1):
        e = ((q[:, 0] - sx * 0.034) / 0.017) ** 2 + ((q[:, 1] - 0.005) / 0.009) ** 2
        m = (e < 1) & front
        base[m] = _hex('#2a1d1a')
        b = (((q[:, 0] - sx * 0.036) / 0.024) ** 2 + ((q[:, 1] - 0.030) / 0.006) ** 2 < 1) & front
        base[b] = HAIR
    cheek = np.exp(-(((np.abs(q[:, 0]) - 0.045) / 0.03) ** 2 + ((q[:, 1] + 0.03) / 0.03) ** 2))
    base = base * (1 - 0.18 * cheek[:, None]) + np.array(_hex('#d77a6a'))[None, :] * 0.18 * cheek[:, None]
    lip = ((q[:, 0] / 0.022) ** 2 + ((q[:, 1] + 0.058) / 0.007) ** 2 < 1) & front
    base[lip] = _hex('#a8584c')
    return base


def rod_albedo(p, n, P):
    """Surveying rod: alternating salt and ink bands every 10 cm over waxed wood."""
    a, b = P['staff_base'], P['staff_top']
    ax = norm(b - a)
    s = (p - a) @ ax
    band = (np.floor(s / 0.10) % 2) == 0
    out = np.where(band[:, None], np.array(SALT)[None, :], np.array(INK)[None, :])
    low = s < 0.35
    out[low] = WOOD
    return out


def salt_crusted(m, amount):
    """Death end state: white salt blooms over a material, driven by noise."""
    import copy
    base = m.albedo
    def alb(p, n):
        a = base(p, n) if callable(base) else np.array(base)[None, :].repeat(len(p), 0)
        c = np.clip((fbm(p, 18.0, 3) - (1 - amount)) * 4.0 + (amount - 0.5) * 2, 0, 1)[:, None]
        return a * (1 - c) + np.array(SALT)[None, :] * c
    m2 = copy.copy(m)
    m2.albedo = alb
    m2.spec = m.spec * (1 - amount) + 0.03 * amount
    m2.metal = m.metal * (1 - amount)
    if m.emissive is not None:
        m2.emissive = tuple(np.array(m.emissive) * (1 - amount))
    return m2


def head_R(P):
    return rot_y(P['head_yaw']) @ rot_x(-P['head_pitch'])


# ---------------------------------------------------------------- build

def build(P):
    parts = []
    add = lambda prim, mat, k=0.0: parts.append(Part(prim, mat, k))
    br = P['breathe']

    # --- legs and boots
    for s in ('r', 'l'):
        hip, kn, an = P['hip_' + s], P['kn_' + s], P['an_' + s]
        add(Capsule(hip, kn, 0.068, 0.052), 'trousers', 0.02)
        add(Capsule(kn + (an - kn) * 0.05, an, 0.050, 0.044), 'boot', 0.0)
        add(Capsule(kn + v3(0, 0.03, 0.0), kn + v3(0, -0.02, 0.01), 0.060, 0.056), 'boot', 0.01)   # boot cuff
        yaw = P['foot_%s_yaw' % s]
        fd = rot_y(yaw) @ v3(0, 0, 1)
        toe = an + fd * 0.15 + v3(0, -0.045, 0)
        add(Capsule(an + v3(0, -0.035, -0.03), toe, 0.048, 0.036), 'boot', 0.03)

    # --- torso (coat), squared salt mantle on the shoulders
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    add(Ellipsoid(ch + v3(0, 0, 0.0), (0.165 + br * 0.004, 0.19, 0.105 + br * 0.006)), 'coat', 0.0)
    add(Ellipsoid(pel + v3(0, 0.12, 0), (0.135, 0.13, 0.095)), 'coat', 0.06)

    # coat skirt: flared shell with folds, split at the front
    sway = P['coat_sway']

    def skirt(p):
        x = p[:, 0] - pel[0]
        z = p[:, 2] - pel[2]
        y = p[:, 1] - (pel[1] - 0.94)
        t = np.clip((1.02 - y) / 0.72, 0, 1)
        x = x - sway * 0.05 * t * t
        theta = np.arctan2(x, z)
        rx = 0.135 + 0.16 * t ** 1.2
        rz = 0.100 + 0.12 * t ** 1.2
        fold = 1 + 0.07 * t * np.sin(theta * 7 + 0.6) + 0.03 * t * np.sin(theta * 13 + 2.0)
        rad = np.sqrt((x / rx) ** 2 + (z / rz) ** 2)
        d = (rad - fold) * np.minimum(rx, rz) * 0.8
        hem = hem_y(theta, P)
        d = np.maximum(d, np.maximum(y - 1.02, hem - y))
        d = np.maximum(d, 0.004 - p[:, 1])   # coat pools on the ground when she kneels
        d = np.abs(d + 0.008) - 0.010
        w = coat_open_angle(y)
        wedge = (np.abs(theta) - w) * np.sqrt(x * x + z * z)
        return smax(d, -wedge, 0.01)
    add(Func(skirt, (pel[0], pel[1] - 0.28, pel[2]), 0.45), 'coat', 0.0)

    # squared salt capelet over the shoulders (superellipse shell = Concord rectangles)
    def capelet(p):
        q = p - (nk + v3(0, 0.0, -0.012))
        y = q[:, 1]
        t = np.clip(-y / 0.19, 0, 1)
        rx = 0.078 + 0.215 * t ** 0.55
        rz = 0.068 + 0.095 * t ** 0.6
        fold = 1 + 0.025 * t * np.sin(np.arctan2(q[:, 0], q[:, 2]) * 9)
        rad = ((np.abs(q[:, 0]) / rx) ** 4 + (np.abs(q[:, 2]) / rz) ** 4) ** 0.25
        d = (rad - fold) * np.minimum(rx, rz) * 0.7
        d = np.maximum(d, np.maximum(y + 0.0, -0.19 - y))
        return np.abs(d + 0.007) - 0.009
    add(Func(capelet, nk + v3(0, -0.09, 0), 0.3), 'capelet', 0.0)
    # high collar
    add(Cylinder(nk + v3(0, -0.03, -0.005), nk + v3(0, 0.05, -0.012), 0.072, 0.012), 'salt', 0.0)

    # lapels: pale V on the chest
    for sx in (-1, 1):
        a = nk + v3(sx * 0.045, -0.04, 0.085)
        b = pel + v3(sx * 0.012, 0.13, 0.098)
        add(Capsule(a, b, 0.016, 0.010), 'salt', 0.0)
    # brass buttons down the right lapel
    for i in range(4):
        tt = 0.2 + i * 0.2
        c = (nk + v3(-0.07, -0.05, 0.095)) * (1 - tt) + (pel + v3(-0.04, 0.14, 0.098)) * tt
        add(Sphere(c, 0.011), 'brass', 0.0)

    # belt with buckle
    def belt(p):
        q = p - (pel + v3(0, 0.08, 0.002))
        e = np.sqrt((q[:, 0] / 0.142) ** 2 + (q[:, 2] / 0.104) ** 2) - 1.0
        return np.sqrt((e * 0.1) ** 2 + 0) * 0 + np.maximum(np.abs(e * 0.104) - 0.006, np.abs(q[:, 1]) - 0.022)
    add(Func(belt, pel + v3(0, 0.08, 0), 0.2), 'leather', 0.0)
    add(RoundBox(pel + v3(0, 0.08, 0.108), (0.024, 0.024, 0.008), 0.004), 'brass', 0.0)

    # bandolier strap: right hip to left shoulder, carries the chart case
    add(Capsule(pel + v3(-0.12, 0.10, 0.085), ch + v3(0.06, 0.10, 0.10), 0.013), 'leather', 0.0)
    add(Capsule(ch + v3(0.06, 0.10, 0.10), P['sh_l'] + v3(-0.03, 0.03, 0.0), 0.013), 'leather', 0.0)

    # chart case on her back, poking over the left shoulder
    cb = ch + v3(-0.16, -0.22, -0.13)
    ct = ch + v3(0.25, 0.15, -0.13)
    add(Cylinder(cb, ct, 0.042, 0.008), 'leather', 0.0)
    add(Cylinder(ct - norm(ct - cb) * 0.04, ct + norm(ct - cb) * 0.012, 0.048, 0.006), 'brass', 0.0)
    add(Cylinder(cb - norm(ct - cb) * 0.012, cb + norm(ct - cb) * 0.04, 0.048, 0.006), 'brass', 0.0)
    # rolled chart sticking out of the top
    add(Cylinder(ct, ct + norm(ct - cb) * 0.07, 0.026, 0.004), 'paper', 0.0)

    # --- arms (sleeves) and gloved hands
    for s in ('r', 'l'):
        sh, el, wr = P['sh_' + s], P['el_' + s], P['wr_' + s]
        sxx = -1 if s == 'r' else 1
        add(Capsule(sh + v3(-sxx * 0.02, -0.06, 0), el, 0.056, 0.048), 'coat', 0.03)
        add(Capsule(el, wr, 0.048, 0.040), 'coat', 0.02)
        cuff_a = el + (wr - el) * 0.72
        add(Capsule(cuff_a, wr - (wr - el) * 0.02, 0.047, 0.047), 'salt', 0.0)
        d = norm(wr - el)
        add(Ellipsoid(wr + d * 0.045, (0.034, 0.045, 0.030), basis_from(d, (0, 0, 1))), 'glove', 0.01)

    # --- neck and head
    add(Capsule(nk + v3(0, -0.02, 0), P['head'] + v3(0, -0.07, -0.01), 0.04), 'skin', 0.0)
    R = head_R(P)
    H = P['head']
    add(Ellipsoid(H, (0.078, 0.097, 0.088), R), 'skin', 0.0)
    add(Ellipsoid(H + R @ v3(0, -0.05, 0.022), (0.056, 0.05, 0.062), R), 'skin', 0.03)       # jaw
    add(Capsule(H + R @ v3(0, 0.0, 0.078), H + R @ v3(0, -0.028, 0.092), 0.010, 0.013), 'skin', 0.01)  # nose
    # hair: swept cap, side locks, tied tail
    add(Ellipsoid(H + R @ v3(0, 0.038, -0.03), (0.080, 0.074, 0.080), R), 'hair', 0.012)
    add(Ellipsoid(H + R @ v3(0, 0.062, 0.02), (0.07, 0.035, 0.06), R), 'hair', 0.02)   # swept fringe
    add(Ellipsoid(H + R @ v3(-0.068, 0.0, 0.0), (0.022, 0.06, 0.045), R), 'hair', 0.02)   # side lock
    add(Ellipsoid(H + R @ v3(0.068, 0.0, 0.0), (0.022, 0.06, 0.045), R), 'hair', 0.02)
    tail_a = H + R @ v3(0, 0.0, -0.085)
    add(Capsule(tail_a, tail_a + v3(0.02, -0.17, -0.05), 0.030, 0.014), 'hair', 0.02)
    add(Sphere(tail_a + v3(0.0, 0.0, 0.0), 0.034), 'hair', 0.01)

    # --- survey staff in her left hand
    a, b = P['staff_base'], P['staff_top']
    add(Capsule(a, b, 0.016, 0.014), 'rod', 0.0)
    ax = norm(b - a)
    add(Cylinder(a, a + ax * 0.06, 0.02, 0.004), 'brass', 0.0)  # shoe
    # head of the staff: brass sighting ring and crossbar with a hanging plumb bob
    ring_c = b + ax * 0.065
    add(Torus(ring_c, v3(1, 0, 0), 0.05, 0.009), 'sight', 0.0)
    add(Capsule(b - v3(0.09, 0, 0.03), b + v3(0.09, 0, 0.03), 0.010), 'brass', 0.0)
    add(Sphere(b + ax * 0.005, 0.02), 'brass', 0.0)
    bob_top = b + v3(0.085, 0, 0.027)
    add(Capsule(bob_top, bob_top + v3(0, -0.12, 0), 0.003), 'ink', 0.0)
    add(Capsule(bob_top + v3(0, -0.115, 0), bob_top + v3(0, -0.16, 0), 0.014, 0.002), 'brass', 0.0)

    # --- Survey Blade sheathed at the left hip
    hilt = pel + v3(0.15, 0.04, 0.09)
    tip = pel + v3(0.24, -0.52, -0.22)
    sd = norm(tip - hilt)
    add(Capsule(hilt + sd * 0.03, tip, 0.020, 0.014), 'scabbard', 0.0)
    add(Cylinder(tip - sd * 0.07, tip + sd * 0.005, 0.018, 0.004), 'brass', 0.0)
    if P['blade'] is None:
        add(Capsule(hilt, hilt - sd * 0.15, 0.011), 'leather', 0.0)
        add(Capsule(hilt + v3(-0.0, 0.0, -0.05), hilt + v3(0.0, 0.0, 0.05), 0.009), 'brass', 0.0)  # guard
        add(Sphere(hilt - sd * 0.16, 0.017), 'brass', 0.0)
    else:
        # drawn: held in the right fist, P['blade'] is the blade direction
        bd = norm(P['blade'])
        g = P['wr_r'] + norm(P['wr_r'] - P['el_r']) * 0.045
        add(Capsule(g - bd * 0.07, g + bd * 0.06, 0.011), 'leather', 0.0)
        add(Sphere(g - bd * 0.08, 0.017), 'brass', 0.0)
        gx = norm(np.cross(bd, v3(0, 1, 0.3)))
        add(Capsule(g + bd * 0.065 - gx * 0.055, g + bd * 0.065 + gx * 0.055, 0.010), 'brass', 0.0)
        add(Capsule(g + bd * 0.08, g + bd * 0.66, 0.016, 0.004), 'steel', 0.0)

    # --- the night lamp, hanging from the belt on her right hip
    hook = pel + v3(-0.125, 0.06, 0.08)
    sw = P['lamp_swing']
    down = norm(v3(np.sin(sw) * 0.6, -1, np.sin(sw) * 0.3))
    lc = hook + down * 0.105
    LR = basis_from(-down, (0, 0, 1)) @ rot_y(np.radians(20))
    add(Capsule(hook, hook + down * 0.04, 0.005), 'brass', 0.0)
    add(Torus(hook + down * 0.045, LR[:, 2], 0.014, 0.0045), 'brass', 0.0)
    add(RoundBox(lc, (0.034, 0.048, 0.034), 0.006, LR), 'glass', 0.0)
    add(RoundBox(lc + LR[:, 1] * 0.055, (0.040, 0.010, 0.040), 0.006, LR), 'brass', 0.0)   # cap
    add(RoundBox(lc - LR[:, 1] * 0.055, (0.040, 0.009, 0.040), 0.006, LR), 'brass', 0.0)  # base
    for cx in (-1, 1):
        for cz in (-1, 1):
            c = lc + LR @ v3(cx * 0.036, 0, cz * 0.036)
            add(Capsule(c - LR[:, 1] * 0.05, c + LR[:, 1] * 0.05, 0.0055), 'brass', 0.0)
    add(Cylinder(lc + LR[:, 1] * 0.06, lc + LR[:, 1] * 0.08, 0.018, 0.005), 'brass', 0.0)  # chimney

    glow = P['lamp_glow']
    materials = {
        'coat': Material(lambda p, n: coat_albedo(p, n, P), spec=0.04, gloss=8, brush=0.08),
        'salt': Material(lambda p, n: np.array(SALT)[None, :] * (0.94 + 0.08 * fbm(p, 30, 2)[:, None]),
                         spec=0.05, gloss=10, brush=0.05),
        'capelet': Material(lambda p, n: np.where((p[:, 1] < nk[1] - 0.165)[:, None], np.array(STEEL_DK)[None, :],
                                                  np.array(SALT)[None, :] * (0.94 + 0.08 * fbm(p, 30, 2)[:, None])),
                            spec=0.05, gloss=10, brush=0.05),
        'trousers': Material(ROAD, spec=0.02, brush=0.08),
        'boot': Material(BOOT, spec=0.25, gloss=24, brush=0.05),
        'leather': Material(LEATHER, spec=0.18, gloss=20, brush=0.06),
        'scabbard': Material(_hex('#2d2a33'), spec=0.3, gloss=30, brush=0.04),
        'glove': Material(_hex('#3e2c22'), spec=0.15, gloss=18, brush=0.04),
        'brass': Material(BRASS, spec=0.9, gloss=40, metal=0.9, brush=0.04),
        'ink': Material(INK, spec=0.1),
        'steel': Material(_hex('#c9d2d8'), spec=1.0, gloss=60, metal=0.6, brush=0.02),
        'sight': Material(BRASS, spec=0.9, gloss=40, metal=0.9, brush=0.04,
                          emissive=tuple(np.array(LAMP) * P['ring_glow']) if P['ring_glow'] > 0 else None),
        'paper': Material(_hex('#efe6cf'), spec=0.02, brush=0.04),
        'skin': Material(lambda p, n: skin_albedo(p, n, P), spec=0.06, gloss=12, sss=0.6, brush=0.02),
        'hair': Material(HAIR, spec=0.25, gloss=18, brush=0.10),
        'rod': Material(lambda p, n: rod_albedo(p, n, P), spec=0.15, gloss=20, brush=0.03),
        'glass': Material(LAMP, spec=0.3, gloss=30, emissive=tuple(np.array(LAMP) * glow), rim=0.0),
    }
    if P['crust'] > 0:
        materials = {k: salt_crusted(m, P['crust']) for k, m in materials.items()}
    lights = [Light(pos=lc + v3(0, 0, 0.02), color=_hex('#ffb35c'), intensity=1.5 * glow, radius=0.13)]
    return Scene(parts=parts, materials=materials, lights=lights)


# ---------------------------------------------------------------- animation

import rig
from sdf import rot_x as _rx

ROWS = [  # name, fps, loop, extra manifest fields
    ('idle', 4, True, {}),
    ('move', 8, True, {}),
    ('attack', 10, False, {'hitFrame': 2}),
    ('hit', 10, False, {}),
    ('death', 6, False, {'holdLast': True}),
    ('cast', 8, False, {}),
]


def _walk(i):
    P = neutral_pose()
    # contact / passing / contact / passing
    stride = 0.17
    keys = [
        dict(l=(0.13, 0.085, 0.07 + stride), r=(-0.10, 0.085, -0.05 - stride * 0.6), dy=-0.025),
        dict(l=(0.12, 0.085, 0.02), r=(-0.10, 0.17, 0.05), dy=0.01),
        dict(l=(0.13, 0.085, 0.02 - stride * 0.8), r=(-0.10, 0.085, 0.05 + stride), dy=-0.025),
        dict(l=(0.12, 0.17, 0.10), r=(-0.10, 0.085, 0.0), dy=0.01),
    ][i]
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + rig.UPPER, v3(0, keys['dy'], 0.03))
    rig.place_leg(P, 'l', keys['l'])
    rig.place_leg(P, 'r', keys['r'])
    rig.lean(P, fwd=np.radians(4))
    # staff carried, swinging slightly with the stride
    sw = [0.05, 0.0, -0.05, 0.0][i]
    P['staff_base'] = v3(0.30, 0.16, 0.30 + sw)
    P['staff_top'] = v3(0.27, 2.18, 0.15 + sw * 0.4)
    rig.place_arm(P, 'l', P['staff_base'] + norm(P['staff_top'] - P['staff_base']) * 1.06, (1, -0.4, -0.6))
    rig.place_arm(P, 'r', v3(-0.22, 0.95, 0.03 - sw * 1.6), (-0.4, 0, -1))
    P['coat_sway'] = [0.7, 0.0, -0.7, 0.0][i]
    P['lamp_swing'] = [0.25, 0.05, -0.25, -0.05][i]
    return P, {}


def _attack(i):
    P = neutral_pose()
    # the staff stays planted in her left hand; she cuts with the Survey Blade in her right
    k = [
        dict(w=(-0.20, 1.62, -0.10), bl=(0.15, 0.55, -0.8), lean=-5, step=0.0, pole=(-1, -0.2, -0.6)),
        dict(w=(-0.12, 1.52, 0.18), bl=(0.25, 0.85, 0.45), lean=3, step=0.05, pole=(-1, -0.4, -0.2)),
        dict(w=(-0.02, 1.08, 0.40), bl=(0.35, -0.35, 0.85), lean=12, step=0.12, pole=(-1, -0.3, 0.0)),
        dict(w=(-0.14, 1.04, 0.24), bl=(0.15, -0.6, 0.75), lean=5, step=0.06, pole=(-1, -0.5, -0.2)),
    ][i]
    d = v3(0, -0.02 * (k['step'] > 0.1), k['step'] * 0.5)
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + rig.UPPER, d)
    rig.place_leg(P, 'l', (0.14, 0.085, 0.07 + k['step'] * 1.4))
    rig.place_leg(P, 'r', (-0.10, 0.085, -0.04))
    rig.lean(P, fwd=np.radians(k['lean']))
    # left hand keeps hold of the staff, which tilts with her
    P['staff_top'] = P['staff_top'] + v3(0, 0, k['step'] * 0.6)
    ax = norm(P['staff_top'] - P['staff_base'])
    rig.place_arm(P, 'l', P['staff_base'] + ax * 1.18, (1, -0.5, -0.4))
    rig.place_arm(P, 'r', v3(*k['w']) + d, k['pole'])
    P['blade'] = v3(*k['bl'])
    P['head_pitch'] = np.radians([-6, 0, 8, 2][i])
    P['coat_sway'] = [0.2, 0.0, -0.4, -0.2][i]
    P['lamp_swing'] = [-0.15, 0.1, 0.35, 0.1][i]
    return P, {}


def _hit(i):
    P = neutral_pose()
    a = [-11, -4][i]
    rig.lean(P, fwd=np.radians(a), extra=('staff_top',))
    P['head_pitch'] = np.radians([10, 3][i])
    P['lamp_swing'] = [-0.35, -0.1][i]
    P['coat_sway'] = [0.3, 0.1][i]
    look = dict(exposure=1.25, flash=0.22) if i == 0 else {}
    return P, look


def _kneel(P, depth):
    """Drop toward one knee: right knee to the ground, left foot planted forward."""
    py = 0.94 - 0.36 * depth
    d = v3(0, py - P['pelvis'][1], -0.03 * depth)
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + rig.UPPER, d)
    rig.place_leg(P, 'l', (0.14, 0.085, 0.07 + 0.25 * depth))
    rig.place_leg(P, 'r', (-0.10, 0.085 + 0.0 * depth, -0.02 - 0.32 * depth), pole=(0, -0.2 * depth, 1))
    if depth > 0.7:
        P['kn_r'] = v3(-0.10, 0.075, 0.10)
        P['an_r'] = v3(-0.10, 0.08, -0.32)


def _death(i):
    P = neutral_pose()
    if i == 0:
        rig.lean(P, fwd=np.radians(-12), extra=('staff_top',))
        P['staff_top'] = P['staff_top'] + v3(0.12, -0.04, 0.0)
        rig.place_arm(P, 'l', P['wr_l'] + v3(0.03, 0.0, -0.02), (1, -0.5, -0.3))
        P['head_pitch'] = np.radians(16)
        P['lamp_glow'] = 0.8
        P['lamp_swing'] = -0.3
        return P, {}
    depth = [0, 0.75, 1.0, 1.0][i]
    _kneel(P, depth)
    lean = [0, 14, 24, 24][i]
    rig.lean(P, fwd=np.radians(lean))
    # the staff stays planted, leaning away; her left hand still on it
    P['staff_base'] = v3(0.34, 0.0, 0.42)
    P['staff_top'] = P['staff_base'] + norm(v3(0.35, 1.0, 0.12)) * 2.06
    ax = norm(P['staff_top'] - P['staff_base'])
    rig.place_arm(P, 'l', P['staff_base'] + ax * (0.86 if i == 1 else 0.72), (1, -0.6, -0.3))
    rig.place_arm(P, 'r', P['pelvis'] + v3(-0.16, 0.0 if i == 1 else -0.06, 0.14), (-1, 0, -0.5))
    P['head_pitch'] = np.radians([0, 18, 34, 34][i])
    P['lamp_glow'] = [1, 0.6, 0.25, 0.0][i]
    P['crust'] = [0, 0.15, 0.5, 1.0][i]
    P['lamp_swing'] = [0, 0.2, 0.05, 0.0][i]
    return P, {}


def _cast(i):
    P = neutral_pose()
    # she tips the sighting ring toward the target, the ring and lamp flare
    tilt = [0.25, 0.45, 0.0][i]
    hand = P['wr_l'] + v3(0, [0.06, 0.10, 0.0][i], 0)
    ax = norm(v3(0.05 * tilt, 1.0, 0.0) + v3(0, 0, 1.0) * tilt)
    rel = 1.18
    P['staff_base'] = hand - ax * rel
    P['staff_top'] = P['staff_base'] + ax * 2.06
    rig.place_arm(P, 'l', hand, (1, -0.4, -0.5))
    rig.place_arm(P, 'r', [v3(-0.24, 1.10, 0.12), v3(-0.22, 1.30, 0.20), v3(-0.215, 0.93, 0.03)][i], (-1, -0.6, -0.3))
    rig.lean(P, fwd=np.radians([2, 5, 1][i]))
    P['head_pitch'] = np.radians([-6, -4, 0][i])
    P['lamp_glow'] = [1.3, 2.0, 1.3][i]
    P['ring_glow'] = [0.5, 1.0, 0.4][i]
    P['coat_sway'] = [0.2, 0.4, -0.2][i]
    return P, {}


def frames():
    """{row name: [(pose, look overrides), ...]} in ROWS order."""
    return {
        'idle': [_idle(i) for i in range(4)],
        'move': [_walk(i) for i in range(4)],
        'attack': [_attack(i) for i in range(4)],
        'hit': [_hit(i) for i in range(2)],
        'death': [_death(i) for i in range(4)],
        'cast': [_cast(i) for i in range(3)],
    }


def _idle(i):
    P = neutral_pose()
    b = [0.0, 1.0, 0.0, -1.0][i]
    P['breathe'] = b
    rig.shift(P, ('chest', 'neck', 'head', 'sh_r', 'sh_l', 'el_r'), v3(0, 0.006 * b, 0))
    P['lamp_glow'] = [1.0, 0.86, 1.08, 0.93][i]
    P['lamp_swing'] = [0.0, 0.08, 0.0, -0.08][i]
    P['coat_sway'] = 0.12 * b
    P['head_yaw'] = P['head_yaw'] + np.radians([0, 2, 3, 1][i])
    return P, {}

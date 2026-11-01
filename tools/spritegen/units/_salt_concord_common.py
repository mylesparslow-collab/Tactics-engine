"""Shared Salt Concord helpers: palette, salt-seamed materials, squared helms, tabards, tower shields,
pennants, spoked wheels, measuring chains and salt crystals.

Shape language: rectangles and triangles, squared shoulders, long spears, wheeled engines.
Palette: pale salt + steel blue + brass, road grey, ink navy. Salt crust on every seam.
"""
import numpy as np
from sdf import (v3, norm, basis_from, rot_y, rot_x, rot_z, Sphere, Ellipsoid, Capsule, RoundBox,
                 Cylinder, Torus, Func, smax, smin, fbm, vnoise)
from render import Material, _hex
from kit.humanoid import head_R, hand_pos, face_albedo, W
from kit.looks import PALETTES

SC = PALETTES['salt_concord']
SALT = _hex('#e2ddcf')
SALT_HI = _hex('#f1ede2')
STEEL = _hex('#56728f')
STEEL_DK = _hex('#3d546c')
STEEL_LT = _hex('#7d97b0')
ROAD = _hex('#7b7d80')
ROAD_DK = _hex('#5d6064')
INK = _hex('#1d2a3a')
BRASS = _hex('#b8924a')
CANVAS = _hex('#b9ad94')
CANVAS_DK = _hex('#8f846e')
IRON = _hex('#5f656e')
IRON_DK = _hex('#40454d')
LEATHER = _hex('#4d3526')
WOOD = _hex('#6e4c31')
LAMP = _hex('#ffcf7a')


def _arr(c, n):
    return np.array(c, dtype=np.float64)[None, :].repeat(n, 0)


def salt_seams(a, p, amount=0.35, freq=24.0, ground=0.55, gamt=0.6):
    """Blend salt bloom into albedo array a: noisy speckle everywhere plus a crust creeping up from the ground."""
    n = fbm(p, freq, 3)
    speck = np.clip((n - (1 - amount * 0.6)) * 5.0, 0, 1)
    creep = np.clip((ground - p[:, 1]) / max(ground, 1e-6), 0, 1) * gamt
    c = np.clip(speck + np.clip((n * creep - 0.12) * 3.0, 0, 1), 0, 1)[:, None]
    return a * (1 - c) + np.array(SALT)[None, :] * c


def salted(color, amount=0.35, freq=24.0, ground=0.55, gamt=0.6, vary=0.10, **kw):
    """Material: flat colour with brush variation and salt crust in the seams and low down."""
    col = np.array(color)

    def alb(p, n):
        a = col[None, :] * (1 - vary / 2 + vary * fbm(p, 14, 2)[:, None])
        return salt_seams(a, p, amount, freq, ground, gamt)
    kw.setdefault('spec', 0.05)
    kw.setdefault('brush', 0.07)
    return Material(alb, **kw)


def salted_metal(color=IRON, amount=0.45, **kw):
    kw.setdefault('spec', 0.55)
    kw.setdefault('gloss', 28)
    kw.setdefault('metal', 0.55)
    kw.setdefault('brush', 0.05)
    return salted(color, amount=amount, freq=30.0, **kw)


def tabard_mat(P, field=SALT, border=STEEL, stripe=STEEL_DK, width=0.15, stripe_w=0.035, hem_band=0.05,
               emblem=None):
    """Pale tabard with steel-blue borders, a centre stripe and a hem band. Painted in pelvis-local x."""
    def alb(p, n):
        x = p[:, 0] - P['pelvis'][0]
        y = p[:, 1] - (P['pelvis'][1] - 0.94 * P['height'])
        a = _arr(field, len(p)) * (0.94 + 0.08 * fbm(p, 26, 2)[:, None])
        w = width * P['build']
        edge = np.abs(x) > w - 0.022
        a[edge] = border
        if stripe is not None:
            a[np.abs(x) < stripe_w / 2] = stripe
        hem = y < (P['height'] * 0.30 + hem_band)
        if emblem is not None:
            emblem(a, x, y)
        return salt_seams(a, p, 0.25, 26, 0.55, 0.9)
    return Material(alb, spec=0.03, brush=0.08)


def tabard(P, add, mat, width=0.12, hem=0.42, top=0.10, zf=0.10, zb=0.10, thick=0.008, back=True):
    """Front and back squared panels hanging from the belt to the hem (sway with skirt_sway).
    Paint the chest with the same tabard material so it reads as one garment."""
    pel = P['pelvis']
    h = P['height']
    sw = P['skirt_sway']
    for zs, z0 in (((1, zf), (-1, zb)) if back else ((1, zf),)):
        t = pel + v3(0, top * h, zs * z0 * P['build'])
        b = v3(pel[0] + sw * 0.05, hem * h, pel[2] + zs * (z0 * P['build'] + 0.04) - abs(sw) * 0.02 * zs + sw * 0.03)
        mid = (t + b) / 2
        R = basis_from(t - b, (0, 0, 1))
        L = np.linalg.norm(t - b) / 2
        add(RoundBox(mid, (width * P['build'], L, thick), 0.006, R), mat, 0.0)


def square_pauldrons(P, add, mat, size=1.0, trim=None, drop=0.0):
    """Squared, layered shoulder plates (Concord shape language) that follow the upper arm."""
    for s in ('r', 'l'):
        sx = -1 if s == 'r' else 1
        sh = P['sh_' + s]
        down = norm(P['el_' + s] - sh)
        R = basis_from(norm(-down * 0.6 + v3(sx * 0.5, 1, 0)), (0, 0, 1))
        c = sh + v3(sx * 0.015, 0.01 - drop, -0.005) + down * 0.01
        add(RoundBox(c, (0.060 * size, 0.026 * size, 0.070 * size), 0.016, R), mat, 0.01)
        add(RoundBox(c + down * 0.05 + R[:, 0] * 0.008, (0.056 * size, 0.016 * size, 0.066 * size), 0.012, R),
            trim or mat, 0.0)


def kettle_helm(P, add, mat, brim_mat=None, size=1.0, brim=1.0, tall=1.0, crest=None, comb=False):
    """Squared Concord kettle helm: boxy bowl with a flat, slightly drooping rectangular brim."""
    H, R, h = P['head'], head_R(P), P['height']
    s = size * h
    add(RoundBox(H + R @ v3(0, 0.080 * tall, -0.008) * s, (0.070, 0.038 * tall, 0.078), 0.042 * s, R), mat, 0.0)
    if brim:
        add(RoundBox(H + R @ v3(0, 0.048, -0.004) * s, (0.125 * brim, 0.006, 0.130 * brim), 0.008, R @ rot_x(0.05)),
            brim_mat or mat, 0.0)
    if comb:
        add(RoundBox(H + R @ v3(0, 0.14 * tall, -0.01) * s, (0.010, 0.022, 0.080), 0.008, R), brim_mat or mat, 0.0)
    if crest is not None:
        add(Capsule(H + R @ v3(0, 0.12 * tall, -0.01) * s, H + R @ v3(0, 0.20 * tall, -0.05) * s, 0.012, 0.006),
            crest, 0.0)


def barbute(P, add, mat, trim=None, size=1.0, slit=True):
    """Closed squared helm with a T face opening painted dark (Stair-Warden)."""
    H, R, h = P['head'], head_R(P), P['height']
    s = size * h
    add(RoundBox(H + R @ v3(0, 0.015, -0.005) * s, (0.085, 0.105, 0.092), 0.04 * s, R), mat, 0.0)
    add(RoundBox(H + R @ v3(0, -0.085, -0.01) * s, (0.098, 0.022, 0.100), 0.012, R), trim or mat, 0.0)


def visor_mat(P, metal=IRON, slit=INK, amount=0.4):
    """Helm material with a dark T-shaped eye/mouth slit painted on the front."""
    def alb(p, n):
        q = (p - P['head']) @ head_R(P) / P['height']
        a = _arr(metal, len(p)) * (0.95 + 0.1 * fbm(p, 18, 2)[:, None])
        front = q[:, 2] > 0.05
        eye = (np.abs(q[:, 1] - 0.005) < 0.011) & (np.abs(q[:, 0]) < 0.065) & front
        mouth = (np.abs(q[:, 0]) < 0.012) & (q[:, 1] < 0.0) & (q[:, 1] > -0.07) & front
        a[eye | mouth] = slit
        return salt_seams(a, p, amount, 30, 0.5, 0.5)
    return Material(alb, spec=0.6, gloss=30, metal=0.55, brush=0.05)


def tower_shield(P, add, side='l', mat='shield', rim='brass', size=1.0, w=0.17, hgt=0.34, out_dir=None,
                 offset=None):
    """Rectangular Concord pavise strapped to the forearm. Returns (centre, R) for painting an emblem."""
    el, wr = P['el_' + side], P['wr_' + side]
    sx = -1 if side == 'r' else 1
    c = (el + wr) / 2 + (offset if offset is not None else v3(sx * 0.07, 0, 0.06))
    up = v3(0, 1, 0) + norm(wr - el) * 0.15
    out = norm(out_dir if out_dir is not None else v3(sx * 0.55, 0, 1.0))
    R = basis_from(up, out)
    add(RoundBox(c, (w * size, hgt * size, 0.014), 0.008, R), mat, 0.0)
    add(RoundBox(c - R[:, 2] * 0.006, (w * size + 0.014, hgt * size + 0.014, 0.009), 0.008, R), rim, 0.0)
    add(Sphere(c + R[:, 2] * 0.018, 0.026 * size), rim, 0.0)
    return c, R


def shield_mat(c_R, size=1.0, field=STEEL, mark=SALT, kind='stair', w=0.17, hgt=0.34):
    """Shield face: steel-blue field with a pale emblem (stair steps, chevron or bar), salt-seamed."""
    def alb(p, n):
        c, R = c_R[0], c_R[1]
        q = (p - c) @ R / size
        x, y = q[:, 0], q[:, 1]
        a = _arr(field, len(p)) * (0.93 + 0.1 * fbm(p, 20, 2)[:, None])
        if kind == 'stair':
            # three bold steps rising to the right, and a lintel bar above
            u, v = x / w, y / hgt
            for i in range(3):
                m = (u > -0.62 + i * 0.42) & (u < 0.66) & (v > -0.70 + i * 0.30) & (v < -0.40 + i * 0.30)
                a[m] = mark
            a[(np.abs(u) < 0.66) & (np.abs(v - 0.52) < 0.09)] = mark
        elif kind == 'chevron':
            m = np.abs(y - 0.05 + np.abs(x) * 0.9) < 0.035
            a[m & (np.abs(x) < w - 0.02)] = mark
        elif kind == 'bar':
            a[np.abs(x) < 0.03] = mark
            a[np.abs(y - 0.08) < 0.03] = mark
        edge = (np.abs(x) > w - 0.02) | (np.abs(y) > hgt - 0.02)
        a[edge] = SALT
        return salt_seams(a, p, 0.3, 24, 0.6, 0.6)
    return Material(alb, spec=0.12, gloss=16, brush=0.06)


def pennant(add, root, length=0.32, height=0.14, sway=0.0, mat='pennant', direction=None, phase=0.0,
            swallow=False, thick=0.006):
    """Triangular (or swallow-tailed) pennant hanging from a pole at `root`, streaming along `direction`."""
    d = norm(direction if direction is not None else v3(0.6, -0.05, -0.8))
    up = v3(0, 1, 0)
    side = norm(np.cross(d, up))
    up = np.cross(side, d)
    M = np.stack([d, up, side], axis=1)

    def f(p):
        q = (p - root) @ M
        x, y, z = q[:, 0], q[:, 1], q[:, 2]
        t = np.clip(x / length, 0, 1)
        y = y + (0.03 * t * t + 0.02 * sway * t) * length * 2 * 0 + height * 0.5 * 0 - 0.0
        y = y + t * t * 0.25 * height       # droops at the tail
        wave = (0.020 + 0.02 * abs(sway)) * t * np.sin(x * 16 + phase + sway * 2.0)
        half = height * 0.5 * (1 - t)
        if swallow:
            half = np.where(t > 0.6, height * 0.5 * (1 - 0.6) * 1.0, half)
        dy = np.abs(y + height * 0.5) - np.maximum(half, 0)
        if swallow:
            notch = 0.45 * (t - 0.6) / 0.4 * height
            dy = np.where(t > 0.6, np.maximum(dy, -(np.abs(y + height * 0.5) - np.maximum(notch, 0))), dy)
        dx = np.maximum(-x, x - length)
        d2 = np.maximum(dx, dy * 0.8)
        return np.maximum(d2, np.abs(z - wave) - thick)
    add(Func(f, root + d * length * 0.5 - up * height * 0.5, length * 0.7 + height), mat, 0.0)


def pennant_mat(color=STEEL, edge=SALT):
    def alb(p, n):
        a = _arr(color, len(p)) * (0.92 + 0.12 * fbm(p, 20, 2)[:, None])
        return salt_seams(a, p, 0.25, 30, 0.0, 0.0)
    return Material(alb, spec=0.03, brush=0.08)


def wheel(add, c, axis, r, angle=0.0, rim_mat='iron', spoke_mat='wood', hub_mat='brass', spokes=6, width=0.06,
          tyre=0.03):
    """Spoked wheel. axis is the axle direction. angle rotates the spokes (rolling)."""
    ax = norm(axis)
    B = basis_from(ax, (0, 1, 0))
    u, w = B[:, 0], B[:, 2]
    add(Torus(c, ax, r - tyre * 0.5, tyre), rim_mat, 0.0)
    for i in range(spokes):
        a = angle + i * 2 * np.pi / spokes
        dvec = u * np.cos(a) + w * np.sin(a)
        add(Capsule(c + dvec * 0.03, c + dvec * (r - tyre), 0.014), spoke_mat, 0.0)
    add(Cylinder(c - ax * width * 0.6, c + ax * width * 0.6, r * 0.18, 0.01), hub_mat, 0.0)
    # tread blocks: squared studs around the rim (wheels read as engine parts at 1x)
    for i in range(10):
        a = angle * 1.0 + i * 2 * np.pi / 10
        dvec = u * np.cos(a) + w * np.sin(a)
        Rb = np.stack([dvec, ax, np.cross(dvec, ax)], axis=1)
        add(RoundBox(c + dvec * (r + tyre * 0.2), (tyre * 0.6, width * 0.45, tyre * 0.9), 0.004, Rb), rim_mat, 0.0)


def chain(add, a, b, sag=0.06, n=7, r=0.010, mat='brass'):
    """Measuring chain: little links strung between a and b with a sag."""
    for i in range(n + 1):
        t = i / n
        p = a * (1 - t) + b * t + v3(0, -sag * 4 * t * (1 - t), 0)
        add(Sphere(p, r), mat, 0.0)
        if i < n:
            t2 = (i + 1) / n
            p2 = a * (1 - t2) + b * t2 + v3(0, -sag * 4 * t2 * (1 - t2), 0)
            add(Capsule(p, p2, r * 0.45), mat, 0.0)


def crystal(add, base, height, r, mat='crystal', tilt=None):
    """Hexagonal salt prism with a pointed top (Concord triangles)."""
    d = norm(tilt if tilt is not None else v3(0, 1, 0))
    R = basis_from(d, (0, 0, 1))

    def f(p):
        q = (p - base) @ R
        x, y, z = q[:, 0], q[:, 1], q[:, 2]
        # hexagon in xz
        k = np.array([-0.8660254, 0.5, 0.57735])
        ax, az = np.abs(x), np.abs(z)
        ax2 = ax - 2 * np.minimum(k[0] * ax + k[1] * az, 0) * k[0]
        az2 = az - 2 * np.minimum(k[0] * ax + k[1] * az, 0) * k[1]
        dh = np.sqrt((ax2 - np.clip(ax2, -k[2] * r, k[2] * r)) ** 2 + (az2 - r) ** 2) * np.sign(az2 - r)
        tip = (y - height) + np.sqrt(ax * ax + az * az) * (height * 0.35 / r) * 0.6
        return np.maximum(np.maximum(dh, tip * 0.7), -y)
    add(Func(f, base + d * height * 0.5, height * 0.6 + r), mat, 0.0)


def crystal_mat(glow=0.0, color=SALT_HI, tint=_hex('#cfe3ee')):
    e = tuple(np.array(_hex('#dff3ff')) * glow) if glow > 0 else None
    return Material(lambda p, n: _arr(color, len(p)) * 0.8 + np.array(tint)[None, :] * 0.2 * (0.7 + 0.6 * fbm(p, 12, 2)[:, None]),
                    spec=0.8, gloss=50, brush=0.03, emissive=e, rim=1.2)


def skin_mat(P, skin=None, hair=_hex('#4a3426'), beard=None, eyes=_hex('#2a1d1a'), lips=_hex('#a8584c')):
    return Material(face_albedo(P, skin or W['skin_light'], hair, eyes=eyes, lips=lips, beard=beard),
                    spec=0.06, gloss=12, sss=0.6, brush=0.02)


def base_mats(P):
    """Common Concord materials. Units add or override."""
    return {
        'salt': Material(lambda p, n: np.array(SALT)[None, :] * (0.94 + 0.08 * fbm(p, 30, 2)[:, None]),
                         spec=0.05, gloss=10, brush=0.05),
        'steelcloth': salted(STEEL, 0.3, gamt=0.8),
        'steelcloth_dk': salted(STEEL_DK, 0.3, gamt=0.8),
        'road': salted(ROAD, 0.25),
        'canvas': salted(CANVAS, 0.25, vary=0.14, brush=0.1),
        'ink': Material(INK, spec=0.1),
        'iron': salted_metal(IRON),
        'helmiron': salted_metal(_hex('#6d737b'), amount=0.55),
        'brass': Material(BRASS, spec=0.9, gloss=40, metal=0.9, brush=0.04),
        'pennant': pennant_mat(),
        'boot': salted(W['boot'], 0.2, ground=0.3, gamt=1.0, spec=0.25, gloss=24, brush=0.05),
        'leather': salted(LEATHER, 0.15, ground=0.2, spec=0.18, gloss=20, brush=0.06),
        'crystal': crystal_mat(),
    }


def rod_mat(a_key, b_key, P, band=0.10, low=0.0):
    """Survey-rod banding (salt / ink) between pose points P[a_key] and P[b_key]."""
    def alb(p, n):
        a, b = P[a_key], P[b_key]
        ax = norm(b - a)
        s = (p - a) @ ax
        bnd = (np.floor(s / band) % 2) == 0
        out = np.where(bnd[:, None], np.array(SALT)[None, :], np.array(INK)[None, :])
        out[s < low] = WOOD
        return out
    return Material(alb, spec=0.15, gloss=20, brush=0.03)


def crossbow(P, add, side='r', size=1.0, stock='wood', prod='iron', string='ink', bolt='salt'):
    """Light Concord crossbow held at the hand along P['item_<side>'] (squared stock, steel prod, chalk bolt)."""
    d = P['item_' + side]
    if d is None:
        return None
    d = norm(d)
    g = hand_pos(P, side)
    sv = norm(np.cross(d, v3(0, 1, 0)))
    up = np.cross(sv, d)
    R = np.stack([sv, d, up], axis=1)
    s = size
    add(RoundBox(g + d * 0.10 * s - up * 0.01, (0.022, 0.26 * s, 0.026), 0.008, R), stock)       # stock
    add(RoundBox(g - d * 0.14 * s - up * 0.03, (0.026, 0.06 * s, 0.045), 0.01, R), stock)        # butt
    front = g + d * 0.34 * s
    for sg in (-1, 1):
        a = front + sv * sg * 0.20 * s - d * 0.05 * s
        add(Capsule(front, a, 0.013, 0.008), prod)
        add(Capsule(a, g + d * 0.12 * s + up * 0.012, 0.0028), string)
    add(Capsule(g + d * 0.12 * s + up * 0.02, front + d * 0.06, 0.008), bolt)                   # chalk bolt
    add(RoundBox(g + d * 0.02 * s + up * 0.04, (0.012, 0.03, 0.012), 0.004, R), 'brass')         # brass sight
    if P['fx'] > 0:
        add(Sphere(front + d * 0.12, 0.05 * P['fx']), 'chalk_puff')
    return g, front

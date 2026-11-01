"""Caustic Lantern (Salt Concord siege engine).

A wheeled brazier: a squared, salt-crusted timber cart on four spoked iron-shod wheels, carrying a
brass-framed lantern furnace with glowing salt-glass panes, and a throwing arm whose cup holds a lump
of burning salt-glass that it hurls in long arcs. Steel-blue pennants fly from the rear corners.
Idle tell: the furnace flickers and the pennants stir. Death: an axle gives, the furnace gutters and
the whole engine crusts over with salt.
"""
import numpy as np
from sdf import (v3, norm, basis_from, rot_y, rot_x, rot_z, Sphere, Ellipsoid, Capsule, RoundBox, Cylinder,
                 Torus, fbm)
from render import Material, Light, _hex, Part
from kit.humanoid import finish, new_parts
from kit.anim import creature_frames, CREATURE_DEFAULTS, ROWS
from kit.xform import transform_parts
from kit.looks import LOOKS
from _salt_concord_common import *

UNIT_ID = 'salt_concord_caustic_lantern'
FACTION = 'salt_concord'
LOOK = LOOKS[FACTION]
FIRE = _hex('#ffd98a')
FIRE_CORE = _hex('#f4ffd8')


def neutral_pose():
    P = dict(CREATURE_DEFAULTS)
    P.update(roll=0.0, arm=0.0, tilt=0.0)
    return P


def build(P):
    parts, add = new_parts()
    g = P['glow'] * (1 - P['end'])
    cg = P['cast_glow']
    WR = 0.21
    # chassis: squared timber bed with iron straps
    bed_c = v3(0, 0.40, 0.0)
    add(RoundBox(bed_c, (0.30, 0.07, 0.52), 0.02), 'timber')
    for z in (-0.40, 0.0, 0.40):
        add(RoundBox(bed_c + v3(0, 0.0, z), (0.315, 0.075, 0.03), 0.01), 'iron')
    # trail / tongue reaching forward
    add(RoundBox(v3(0, 0.30, 0.68), (0.05, 0.04, 0.20), 0.01, rot_x(0.25)), 'timber')
    add(Torus(v3(0, 0.25, 0.88), v3(1, 0, 0), 0.04, 0.012), 'iron')
    # wheels
    for x in (-0.36, 0.36):
        for z in (-0.33, 0.33):
            wheel(add, v3(x, WR, z), v3(1, 0, 0), WR, angle=P['roll'] + (0.3 if z > 0 else 0),
                  rim_mat='iron', spoke_mat='timber', hub_mat='brass', spokes=6, width=0.06, tyre=0.025)
    add(Cylinder(v3(-0.38, WR, 0.33), v3(0.38, WR, 0.33), 0.022), 'iron')
    add(Cylinder(v3(-0.38, WR, -0.33), v3(0.38, WR, -0.33), 0.022), 'iron')
    # lantern furnace: brass-framed box with glowing panes, squared pyramid hood and chimney
    fcen = v3(0, 0.74, -0.14)
    add(RoundBox(fcen + v3(0, -0.24, 0), (0.22, 0.03, 0.22), 0.01), 'iron')
    add(RoundBox(fcen, (0.18, 0.21, 0.18), 0.01), 'panes')
    for cx in (-1, 1):
        for cz in (-1, 1):
            q = fcen + v3(cx * 0.185, 0, cz * 0.185)
            add(Capsule(q + v3(0, -0.22, 0), q + v3(0, 0.22, 0), 0.018), 'brass')
    for y in (-0.21, 0.0, 0.21):
        add(RoundBox(fcen + v3(0, y, 0), (0.195, 0.012, 0.195), 0.004), 'brass')
    for t in (-0.06, 0.06):     # mullions: squared panes
        add(RoundBox(fcen + v3(t, 0, 0), (0.008, 0.21, 0.19), 0.003), 'iron')
        add(RoundBox(fcen + v3(0, 0, t), (0.19, 0.21, 0.008), 0.003), 'iron')
    # pyramid hood (Concord triangles)
    def hood(p, c=fcen + v3(0, 0.23, 0)):
        q = p - c
        h = 0.20
        r = 0.21 * np.clip(1 - q[:, 1] / h, 0, 1)
        d = np.maximum(np.maximum(np.abs(q[:, 0]), np.abs(q[:, 2])) - r, np.maximum(-q[:, 1], q[:, 1] - h))
        return d * 0.7
    from sdf import Func
    add(Func(hood, fcen + v3(0, 0.33, 0), 0.32), 'hood')
    add(Cylinder(fcen + v3(0, 0.38, 0), fcen + v3(0, 0.52, 0), 0.04, 0.008), 'iron')
    add(Cylinder(fcen + v3(0, 0.50, 0), fcen + v3(0, 0.53, 0), 0.055, 0.008), 'brass')
    # throwing arm: pivots at the front of the furnace, swings from back (arm=0) over to front (arm=1)
    piv = v3(0, 0.80, 0.16)
    add(Cylinder(piv + v3(-0.20, 0, 0), piv + v3(0.20, 0, 0), 0.03), 'iron')
    for x in (-0.18, 0.18):
        add(RoundBox(v3(x, 0.60, 0.16), (0.025, 0.20, 0.04), 0.008), 'timber')
    a = np.radians(-60 + 150 * P['arm'])     # -60 deg = cocked back, 90 = thrown forward
    ad = norm(v3(0, np.cos(np.radians(90) - a) * 0 + np.cos(a), np.sin(a)))
    ad = norm(v3(0, np.cos(a - np.radians(90)) * 0 + np.sin(np.radians(90) - a + np.radians(0)) * 0 + np.cos(a), np.sin(a)))
    tipp = piv + ad * 0.62
    add(Capsule(piv - ad * 0.12, tipp, 0.03, 0.022), 'timber')
    add(Cylinder(piv + ad * 0.25, piv + ad * 0.28, 0.035), 'iron')
    cup = tipp + v3(0, 0.03, 0)
    add(Torus(cup, v3(0, 1, 0), 0.06, 0.018), 'iron')
    add(Ellipsoid(cup + v3(0, -0.01, 0), (0.07, 0.025, 0.07)), 'iron')
    if P['arm'] < 0.8 or cg > 0:
        add(Ellipsoid(cup + v3(0, 0.035, 0), (0.05, 0.045, 0.05)), 'fireglass')
    if P['fx'] > 0:
        # released lump arcing away, trailing caustic sparks
        for i in range(4):
            add(Sphere(tipp + v3(0, 0.15 + 0.05 * i, 0.20 + 0.14 * i), (0.06 - 0.01 * i) * P['fx']), 'fireglass')
    # pennants on the rear corners
    for x in (-0.28, 0.28):
        root = v3(x, 0.47, -0.50)
        add(Capsule(root, root + v3(0, 0.95, 0), 0.012), 'timber')
        add(Sphere(root + v3(0, 0.96, 0), 0.02), 'brass')
        pennant(add, root + v3(0, 0.92, 0), length=0.34, height=0.13, sway=np.sin(P['tell'] * 6.28 + x * 3),
                direction=v3(0.25 * np.sign(x), -0.05, -1.0), phase=P['tell'] * 6.28 + x * 4, swallow=True)
    # salt crust heaped on the bed and axles (always present)
    for (x, z, r) in ((-0.22, 0.38, 0.06), (0.20, -0.42, 0.05), (0.24, 0.30, 0.045)):
        add(Ellipsoid(v3(x, 0.47, z), (r, r * 0.5, r)), 'saltcrust')
    # whole-body motion: lean (pitch), bob, death tilt (axle gives on the right)
    tilt = P['tilt']
    R = rot_x(P['lean'] * 0.35) @ rot_z(-tilt)
    parts[:] = transform_parts(parts, R=R, t=(0, P['bob'], -0.12), pivot=(0, 0, 0.3 * np.sign(P['lean'] + 1e-6)))
    flick = 0.85 + 0.3 * abs(np.sin(P['tell'] * 9.0))
    mats = base_mats(P)
    gl = g * flick + 1.2 * cg
    mats.update({
        'timber': salted(_hex('#6b5440'), 0.4, ground=0.6, gamt=0.9, spec=0.06, brush=0.1),
        'iron': salted_metal(IRON, amount=0.55),
        'hood': salted_metal(STEEL_DK, amount=0.5),
        'panes': Material(lambda p, n: np.array(_hex('#c99a4a'))[None, :] * (0.75 + 0.25 * fbm(p, 16, 2)[:, None]),
                          spec=0.6, gloss=40, emissive=tuple(np.array(FIRE) * 0.45 * gl), rim=0.0, brush=0.02),
        'fireglass': Material(FIRE_CORE, emissive=tuple(np.array(FIRE_CORE) * (0.9 * g + 0.3)), rim=0.0),
        'saltcrust': Material(SALT_HI, spec=0.05, brush=0.08),
    })
    L = Light(R @ fcen + v3(0.0, P['bob'], 0.2), _hex('#ffcf7a'), 1.6 * gl, 0.45)
    return finish(P, FACTION, parts, mats, lights=[L])


def _over(rows):
    for i, (P, lk) in enumerate(rows['move']):
        P['roll'] = i * (2 * np.pi / 6) / 2
    for i, (P, lk) in enumerate(rows['attack']):
        P['arm'] = [0.0, -0.1, 1.0, 0.7][i]
        P['lean'] = [-0.05, -0.1, 0.12, 0.04][i]
    for i, (P, lk) in enumerate(rows['death']):
        P['tilt'] = [0.0, 0.08, 0.16, 0.18][i]
        P['arm'] = [0.0, 0.3, 0.75, 0.8][i]
        P['lean'] = [-0.1, 0.1, 0.2, 0.2][i]
    for i, (P, lk) in enumerate(rows['cast']):
        P['arm'] = [0.0, 0.15, 0.4][i]
    for name in rows:
        for P, lk in rows[name]:
            P['squash'] = 1.0
    return rows


frames = creature_frames(neutral_pose, _over)

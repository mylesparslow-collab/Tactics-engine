"""Saltmill Juggernaut (Salt Concord exotic siege engine).

A salt-grinding mill bolted to iron treads: two long tread units with road wheels, a squared riveted
hull, a huge ribbed grinding drum across the front, a pyramid hopper on top heaped with salt, a
stack, steel-blue pennants on twin masts, and the defining detail: a white plume of ground salt
pouring from the drum. "The Concord's proof that a road can walk."
"""
import numpy as np
from sdf import (v3, norm, basis_from, rot_y, rot_x, rot_z, Sphere, Ellipsoid, Capsule, RoundBox, Cylinder,
                 Torus, Func, fbm, smin)
from render import Material, Light, Camera, _hex
from kit.humanoid import finish, new_parts
from kit.anim import creature_frames, CREATURE_DEFAULTS, ROWS
from kit.xform import transform_parts
from kit.looks import LOOKS
from _salt_concord_common import *

UNIT_ID = 'salt_concord_saltmill_juggernaut'
FACTION = 'salt_concord'
LOOK = LOOKS[FACTION]
CAMERA = Camera(ppm=44)


def neutral_pose():
    P = dict(CREATURE_DEFAULTS)
    P.update(roll=0.0, drum=0.0, plume=1.0, tilt=0.0)
    return P


def tread(add, x, roll, L=0.80, r=0.22, w=0.20):
    """Stadium-shaped track unit along z at side x, with cleats that creep with `roll` (metres)."""
    c = v3(x, r, 0.0)

    def f(p, c=c):
        q = p - c
        z = np.clip(q[:, 2], -L, L)
        d2 = np.sqrt((q[:, 2] - z) ** 2 + q[:, 1] ** 2) - r
        return np.maximum(d2, np.abs(q[:, 0]) - w / 2)
    add(Func(f, c, L + r), 'track', 0.0)
    for zz in np.linspace(-L + 0.18, L - 0.18, 4):
        add(Cylinder(c + v3(-w * 0.56, 0, zz), c + v3(w * 0.56, 0, zz), r * 0.62, 0.01), 'iron')
        add(Cylinder(c + v3(-w * 0.6, 0, zz), c + v3(w * 0.6, 0, zz), r * 0.22, 0.01), 'brass')
    # cleats around the loop
    per = 2 * (2 * L) + 2 * np.pi * r
    n = 22
    for i in range(n):
        s = (i * per / n + roll) % per
        if s < 2 * L:                                     # top run, moving back
            pos, nrm = c + v3(0, r, L - s), v3(0, 1, 0)
        elif s < 2 * L + np.pi * r:                       # back curve
            a = (s - 2 * L) / r
            pos, nrm = c + v3(0, r * np.cos(a), -L - r * np.sin(a)), v3(0, np.cos(a), -np.sin(a))
        elif s < 4 * L + np.pi * r:                       # bottom run
            pos, nrm = c + v3(0, -r, -L + (s - 2 * L - np.pi * r)), v3(0, -1, 0)
        else:
            a = (s - 4 * L - np.pi * r) / r
            pos, nrm = c + v3(0, -r * np.cos(a), L + r * np.sin(a)), v3(0, -np.cos(a), np.sin(a))
        Rb = basis_from(nrm, (1, 0, 0))
        add(RoundBox(pos + nrm * 0.012, (w * 0.56, 0.018, 0.035), 0.006, Rb), 'iron')


def build(P):
    parts, add = new_parts()
    pl = P['plume'] * (1 - P['end'])
    # treads
    for x in (-0.46, 0.46):
        tread(add, x, P['roll'])
    # hull: squared riveted box with sloped front glacis
    add(RoundBox(v3(0, 0.62, -0.10), (0.38, 0.20, 0.70), 0.03), 'hull')
    add(RoundBox(v3(0, 0.44, 0), (0.58, 0.035, 0.86), 0.015), 'iron')            # track guards
    for z in np.linspace(-0.7, 0.55, 6):
        for x in (-0.575, 0.575):
            add(Sphere(v3(x, 0.46, z), 0.018), 'brass')
    add(RoundBox(v3(0, 0.83, -0.12), (0.40, 0.025, 0.72), 0.01), 'iron')
    # the mill drum: big ribbed cylinder across the front, turning
    dc = v3(0, 0.58, 0.82)
    add(Cylinder(dc + v3(-0.50, 0, 0), dc + v3(0.50, 0, 0), 0.30, 0.03), 'drum')
    for i in range(10):
        a = P['drum'] + i * 2 * np.pi / 10
        o = v3(0, np.cos(a), np.sin(a))
        Rr = basis_from(o, (1, 0, 0))
        add(RoundBox(dc + o * 0.30, (0.47, 0.03, 0.025), 0.008, np.stack([v3(1, 0, 0), o, np.cross(v3(1, 0, 0), o)], 1)),
            'iron')
    for x in (-0.53, 0.53):
        add(Cylinder(dc + v3(x - 0.03, 0, 0), dc + v3(x + 0.03, 0, 0), 0.33, 0.01), 'iron')
        add(Cylinder(dc + v3(x * 1.06, 0, 0), dc + v3(x * 1.12, 0, 0), 0.08, 0.01), 'brass')
    # arms holding the drum
    for x in (-0.56, 0.56):
        add(RoundBox(v3(x, 0.66, 0.50), (0.035, 0.07, 0.34), 0.01, rot_x(0.12)), 'iron')
    # hopper: inverted squared pyramid on top, heaped with salt
    hc = v3(0, 0.86, 0.12)

    def hop(p, c=hc):
        q = p - c
        h = 0.48
        r = 0.16 + 0.22 * np.clip(q[:, 1] / h, 0, 1)
        d = np.maximum(np.maximum(np.abs(q[:, 0]), np.abs(q[:, 2])) - r, np.maximum(-q[:, 1], q[:, 1] - h))
        return np.abs(d * 0.7 + 0.01) - 0.018
    add(Func(hop, hc + v3(0, 0.25, 0), 0.6), 'hopper')
    add(Ellipsoid(hc + v3(0, 0.44, 0), (0.34, 0.10, 0.34)), 'saltheap')
    for (x, z) in ((-0.12, 0.05), (0.1, -0.08), (0.02, 0.14)):
        add(Ellipsoid(hc + v3(x, 0.51, z), (0.10, 0.07, 0.10)), 'saltheap')
    # chute from hopper down into the drum
    add(RoundBox(v3(0, 0.80, 0.55), (0.12, 0.05, 0.16), 0.01, rot_x(-0.5)), 'iron')
    # stack at the rear and two masts with pennants
    add(Cylinder(v3(0.22, 0.85, -0.55), v3(0.22, 1.45, -0.55), 0.06, 0.01), 'iron')
    add(Cylinder(v3(0.22, 1.42, -0.55), v3(0.22, 1.48, -0.55), 0.085, 0.01), 'brass')
    for x in (-0.30, 0.30):
        root = v3(x, 0.85, -0.72)
        add(Capsule(root, root + v3(0, 1.75, 0), 0.022), 'timber')
        add(Sphere(root + v3(0, 1.76, 0), 0.035), 'brass')
        pennant(add, root + v3(0, 1.70, 0), length=0.62, height=0.24, sway=np.sin(P['tell'] * 6.28 + x * 3),
                direction=v3(0.2 * np.sign(x), -0.05, -1.0), phase=P['tell'] * 6.28 + x * 5, swallow=True,
                thick=0.008)
    # salt crust heaped on the guards
    for (x, z, r) in ((-0.45, 0.6, 0.07), (0.48, -0.5, 0.06), (0.40, 0.3, 0.05), (-0.42, -0.6, 0.06)):
        add(Ellipsoid(v3(x, 0.48, z), (r, r * 0.45, r * 1.4)), 'saltheap')
    # the white salt plume: pours from under the drum and billows up in front
    if pl > 0.02:
        ph = P['tell'] * 2 * np.pi + P['drum']
        # salt pouring off the drum face in a sheet down to the ground
        for i in range(5):
            t = i / 4
            add(Ellipsoid(dc + v3(-0.25 + 0.12 * i, -0.30 - 0.12 * t * 0, 0.30 + 0.03 * np.sin(ph + i)),
                          (0.07 * pl, 0.10 * pl, 0.05 * pl)), 'plume', 0.03)
        for i in range(6):
            add(Ellipsoid(v3(-0.45 + 0.18 * i, 0.06, dc[2] + 0.30 + 0.05 * np.sin(i * 1.7)),
                          (0.11 * pl, 0.06 * pl, 0.10 * pl)), 'plume', 0.05)
        # plume of ground salt billowing up past the drum on the far side
        cs, rs = [], []
        for i in range(12):
            t = i / 11
            cs.append(v3(0.40 + 0.14 * np.sin(i * 1.9 + ph) + 0.25 * t, 0.30 + 1.35 * t, dc[2] + 0.15 - 0.65 * t
                         + 0.08 * np.cos(i * 2.3 + ph)))
            rs.append((0.06 + 0.15 * t) * pl)
        cs, rs = np.array(cs), np.array(rs)

        def puffs(p, cs=cs, rs=rs, ph=ph):
            d = np.full(len(p), 1e3)
            for c, r in zip(cs, rs):
                d = smin(d, np.linalg.norm(p - c, axis=1) - r, 0.06)
            return d - 0.05 * (fbm(p + v3(0, -ph * 0.05, 0), 9.0, 3) - 0.5)
        lo, hi = cs.min(0) - 0.3, cs.max(0) + 0.3
        add(Func(puffs, (lo + hi) / 2, float(np.linalg.norm(hi - lo) / 2)), 'plume', 0.05)
    R = rot_x(P['lean'] * 0.3) @ rot_z(-P['tilt'])
    parts[:] = transform_parts(parts, R=R, t=(0.0, P['bob'], -0.45), s=0.70, pivot=(0, 0, 0))
    mats = base_mats(P)
    mats.update({
        'hull': salted_metal(STEEL_DK, amount=0.55, spec=0.35),
        'drum': salted_metal(_hex('#8c939c'), amount=0.65),
        'track': salted_metal(IRON_DK, amount=0.4, spec=0.3),
        'iron': salted_metal(IRON, amount=0.5),
        'hopper': salted_metal(STEEL, amount=0.6, spec=0.3),
        'timber': salted(_hex('#6b5440'), 0.4),
        'saltheap': Material(lambda p, n: np.array(SALT_HI)[None, :] * (0.9 + 0.12 * fbm(p, 20, 2)[:, None]),
                             spec=0.05, brush=0.08),
        'plume': Material(lambda p, n: np.array(SALT_HI)[None, :] * (0.93 + 0.1 * fbm(p, 10, 2)[:, None]),
                          spec=0.0, brush=0.05, emissive=tuple(np.array(SALT_HI) * 0.18), rim=1.4),
    })
    return finish(P, FACTION, parts, mats)


def _over(rows):
    for i, (P, lk) in enumerate(rows['idle']):
        P['drum'] = i * 0.15
    for i, (P, lk) in enumerate(rows['move']):
        P['roll'] = i * 0.09
        P['drum'] = i * 0.31
    for i, (P, lk) in enumerate(rows['attack']):
        P['drum'] = i * 0.5
        P['plume'] = [0.8, 1.0, 1.5, 1.2][i]
        P['lean'] = [-0.12, -0.05, 0.22, 0.08][i]
    for i, (P, lk) in enumerate(rows['hit']):
        P['plume'] = 0.6
    for i, (P, lk) in enumerate(rows['death']):
        P['tilt'] = [0.0, 0.05, 0.10, 0.11][i]
        P['plume'] = [0.8, 0.5, 0.2, 0.0][i]
        P['lean'] = [-0.12, 0.08, 0.18, 0.18][i]
    for i, (P, lk) in enumerate(rows['cast']):
        P['plume'] = [1.2, 1.7, 1.3][i]
        P['drum'] = i * 0.5
    for name in rows:
        for P, lk in rows[name]:
            P['squash'] = 1.0
    return rows


frames = creature_frames(neutral_pose, _over)

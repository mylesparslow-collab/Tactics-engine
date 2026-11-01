"""First Flame (Lanternkeepers exotic beam engine). The flame that was lit on the night of the Long Ebb.

A real machine, not a spirit: an iron carriage on two spoked wheels, a tapering keeper's frame of
four posts and banded rings rising off it like a lighthouse tower, a clockwork drive drum and gear
low down, a lens at its heart in front of the flame chamber, and a lantern room at the top.
Defining detail: the perfectly straight gold beam that leaves the heart lens on the hit frame.
"""
import numpy as np
from _lanternkeepers_common import *
from kit.anim import creature_frames, CREATURE_DEFAULTS
from kit.xform import transform_parts, squash_parts
from render import Camera

UNIT_ID = 'lanternkeepers_first_flame'
FACTION = 'lanternkeepers'
LOOK = LOOKS[FACTION]
CAMERA = Camera(ppm=44)

FWD = norm(v3(-0.25, 0, 1.0))       # the engine faces lower-right on screen


def neutral_pose():
    P = base_pose()
    P.update(CREATURE_DEFAULTS)
    P['wheel'] = 0.0
    P['drum'] = 0.0
    return P


def wheel(add, c, axis, ang, r=0.26):
    add(Torus(c, axis, r, 0.028), 'darkiron')
    add(Torus(c, axis, r - 0.035, 0.012), 'darkiron')
    add(Cylinder(c - axis * 0.04, c + axis * 0.04, 0.045, 0.01), 'brass')
    R = basis_from(axis)
    for k in range(6):
        a = ang + k * np.pi / 3
        o = R @ v3(np.cos(a), 0, np.sin(a))
        add(Capsule(c + o * 0.04, c + o * (r - 0.03), 0.011), 'darkiron')


def gear(add, c, axis, r, ang, teeth=12, mat='brass'):
    add(Cylinder(c - axis * 0.018, c + axis * 0.018, r, 0.005), mat)
    R = basis_from(axis)
    for k in range(teeth):
        a = ang + k * 2 * np.pi / teeth
        o = R @ v3(np.cos(a), 0, np.sin(a))
        add(RoundBox(c + o * (r + 0.012), (0.012, 0.016, 0.012), 0.003, basis_from(axis, o)), mat)
    add(Cylinder(c - axis * 0.03, c + axis * 0.03, r * 0.3, 0.004), 'darkiron')


def build(P):
    parts, add = new_parts()
    lights = []
    side = norm(np.cross(v3(0, 1, 0), FWD))       # engine's left
    # --- carriage: plinth between two big wheels
    axle_y = 0.26
    for sx in (-1, 1):
        wheel(add, v3(0, axle_y, 0) + side * sx * 0.33, side, P['wheel'] * sx)
    add(Capsule(v3(0, axle_y, 0) - side * 0.33, v3(0, axle_y, 0) + side * 0.33, 0.03), 'darkiron')
    plinth = v3(0, 0.36, 0)
    add(Cylinder(plinth - v3(0, 0.08, 0), plinth + v3(0, 0.08, 0), 0.27, 0.02), 'stone')
    add(Torus(plinth + v3(0, 0.08, 0), v3(0, 1, 0), 0.27, 0.015), 'brass')
    # trail/prop leg at the back keeps it standing
    add(Capsule(plinth - FWD * 0.2, v3(0, 0.04, 0) - FWD * 0.48, 0.022), 'darkiron')
    add(Sphere(v3(0, 0.04, 0) - FWD * 0.48, 0.035), 'darkiron')
    # --- keeper's frame: four tapering posts with rings
    base_y, top_y = 0.44, 1.78
    R0, R1 = 0.22, 0.13
    posts = []
    for k in range(4):
        a = np.pi / 4 + k * np.pi / 2
        dvec = norm(FWD * np.cos(a) + side * np.sin(a))
        p0 = v3(0, base_y, 0) + dvec * R0
        p1 = v3(0, top_y, 0) + dvec * R1
        add(Capsule(p0, p1, 0.018, 0.014), 'darkiron')
        posts.append((p0, p1))
    for y, r in ((0.62, 0.205), (1.02, 0.18), (1.48, 0.15), (1.76, 0.132)):
        add(Torus(v3(0, y, 0), v3(0, 1, 0), r * 1.41 * 0.72, 0.012), 'brass')
    # diagonal braces on the back faces
    for k in (1, 2):
        add(Capsule(posts[k][0], posts[(k + 1) % 4][0] + (posts[(k + 1) % 4][1] - posts[(k + 1) % 4][0]) * 0.4, 0.008), 'darkiron')
    # --- clockwork drive: drum on the central column, side gear
    add(Capsule(v3(0, 0.44, 0), v3(0, 1.80, 0), 0.03), 'darkiron')
    dc = v3(0, 0.80, 0)
    add(Cylinder(dc - v3(0, 0.12, 0), dc + v3(0, 0.12, 0), 0.10, 0.015), 'brass')
    for t in (-0.08, 0.0, 0.08):
        add(Torus(dc + v3(0, t, 0), v3(0, 1, 0), 0.102, 0.006), 'darkiron')
    gear(add, dc + side * 0.19 + FWD * 0.02, side, 0.075, P['drum'])
    gear(add, dc + side * 0.19 + v3(0, 0.15, 0) - FWD * 0.06, side, 0.045, -P['drum'] * 1.6, teeth=8)
    # weights on chains
    for s in (-1, 1):
        w = dc - FWD * 0.12 + side * 0.06 * s + v3(0, -0.12 - 0.05 * np.sin(P['drum'] + s), 0)
        add(Capsule(w, dc - FWD * 0.10 + side * 0.06 * s + v3(0, 0.1, 0), 0.004), 'darkiron')
        add(Cylinder(w - v3(0, 0.06, 0), w, 0.026, 0.006), 'darkiron')
    # --- heart: flame chamber and the lens
    hc = v3(0, 1.24, 0)
    add(Cylinder(hc - v3(0, 0.13, 0), hc + v3(0, 0.13, 0), 0.10, 0.02), 'lamp')
    add(Cylinder(hc + v3(0, 0.12, 0), hc + v3(0, 0.16, 0), 0.12, 0.01), 'brass')
    add(Cylinder(hc - v3(0, 0.16, 0), hc - v3(0, 0.12, 0), 0.12, 0.01), 'brass')
    flame(add, hc - v3(0, 0.05, 0) + FWD * 0.0, P, 2.4)
    lc = hc + FWD * 0.16
    add(Cylinder(hc + FWD * 0.06, lc, 0.11, 0.01), 'brass')          # lens barrel
    lens_disc(add, lc, FWD, 0.12, rim='brass', thick=0.02)
    for r in (0.04, 0.08):
        add(Torus(lc + FWD * 0.012, FWD, r, 0.005), 'lens')             # fresnel rings
    light_at(lights, P, hc + FWD * 0.3, 2.6, 0.3)
    # beam
    s = P['strike']
    if P['fx'] > 0 or s > 0.5:
        L = 2.2 * max(P['fx'], 0.0)
        if L > 0:
            add(Capsule(lc + FWD * 0.03, lc + FWD * (0.03 + L), 0.045, 0.03), 'beam')
            light_at(lights, P, lc + FWD * 0.5, 3.0 * P['fx'], 0.4, color=_hex('#ffd27a'))
    # --- lantern room at the top
    tc = v3(0, 1.94, 0)
    add(Cylinder(tc - v3(0, 0.17, 0), tc - v3(0, 0.14, 0), 0.19, 0.01), 'brass')            # gallery
    add(Torus(tc - v3(0, 0.10, 0), v3(0, 1, 0), 0.18, 0.008), 'darkiron')                    # rail
    add(Cylinder(tc - v3(0, 0.14, 0), tc + v3(0, 0.10, 0), 0.11, 0.02), 'lamp')
    for k in range(8):
        a = k * np.pi / 4 + P['drum'] * 0.3
        o = v3(np.cos(a), 0, np.sin(a)) * 0.115
        add(Capsule(tc + o - v3(0, 0.14, 0), tc + o + v3(0, 0.10, 0), 0.008), 'darkiron')
    add(Capsule(tc + v3(0, 0.12, 0), tc + v3(0, 0.17, 0), 0.13, 0.04), 'darkiron')        # dome
    add(Sphere(tc + v3(0, 0.25, 0), 0.03), 'brass')
    add(Capsule(tc + v3(0, 0.27, 0), tc + v3(0, 0.33, 0), 0.007, 0.003), 'brass')
    light_at(lights, P, tc + FWD * 0.2, 2.4, 0.3)
    # --- whole-body motion
    parts[:] = squash_parts(parts, sy=P['squash'], sxz=1.0 / np.sqrt(P['squash']), pivot=(0, 0, 0))
    R = rot_x(P['lean'] * 0.5) if True else None
    Rl = basis_from(v3(0, 1, 0))
    ax = norm(np.cross(v3(0, 1, 0), FWD))
    th = P['lean'] * 0.45
    Rm = (np.cos(th) * np.eye(3) + np.sin(th) * np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
          + (1 - np.cos(th)) * np.outer(ax, ax))
    parts[:] = transform_parts(parts, R=Rm, t=(0, P['bob'], 0), pivot=(0, 0, 0))
    lights = [Light(Rm @ L.pos + v3(0, P['bob'], 0), L.color, L.intensity, L.radius) for L in lights]
    mats = keeper_mats(P)
    mats['stone'] = Material(noisy(_hex('#a8b2b9'), 0.10, 20), spec=0.05, brush=0.10)
    return finish(P, FACTION, parts, mats, lights=lights)


def _over(rows):
    for i, (P, o) in enumerate(rows['idle']):
        P['drum'] = i * 0.25
        P['flick'] = i
        P['glow'] = [1.0, 0.7, 1.12, 0.82][i]
    for i, (P, o) in enumerate(rows['move']):
        P['wheel'] = i * np.pi / 6
        P['drum'] = i * 0.4
    for i, (P, o) in enumerate(rows['attack']):
        P['drum'] = i * 0.5
        P['glow'] = [1.2, 1.5, 1.8, 1.2][i]
    for i, (P, o) in enumerate(rows['cast']):
        P['drum'] = i * 0.6
    for i, (P, o) in enumerate(rows['death']):
        P['lean'] = [-0.10, 0.08, 0.16, 0.18][i]
        P['squash'] = [1, 0.97, 0.94, 0.93][i]
    return rows


frames = creature_frames(neutral_pose, _over)
ROWS = [
    ('idle', 4, True, {}),
    ('move', 8, True, {}),
    ('attack', 10, False, {'hitFrame': 2}),
    ('hit', 10, False, {}),
    ('death', 6, False, {'holdLast': True}),
    ('cast', 8, False, {}),
]

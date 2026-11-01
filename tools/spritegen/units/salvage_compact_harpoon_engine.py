"""Harpoon Engine (Salvage Compact, exotic engine). A whaling harpoon the size of a mast on a cut-down
hull cart: rusted hull-plate chassis on four spoked wheels, an A-frame of leviathan-bone spars carrying
the launcher rail, bone bow-arms with a rope string, a chain winch drum with a crank at the back, and
a tin lantern on a hook. Defining detail: the barbed harpoon head trailing a bright chain.

Rows: idle (lantern flicker, ratchet tick), move (wheels turn, cart bobs), attack (draw, loose: the
harpoon flies out on its chain, recover), hit, death (frame collapses, scrap scatters, lantern out),
cast (Harpoon Haul: the winch spins and the chain hauls taut)."""
import numpy as np
from _salvage_compact_common import *
from render import Camera
from kit.xform import transform_parts

UNIT_ID = 'salvage_compact_harpoon_engine'
FACTION = 'salvage_compact'
CAMERA = Camera(ppm=44)

DEF = dict(bob=0.0, pitch=0.0, wheel=0.0, draw=0.0, shot=0.0, haul=0.0, crank=0.0, glow=1.0,
           cast_glow=0.0, fx=0.0, end=0.0, sink=0.0, collapse=0.0, tell=0.0)


def neutral_pose():
    return dict(DEF)


def wheel(add, c, r, axis, ang, brk=0.0):
    add(Torus(c, axis, r, 0.022), 'iron', 0.0)
    add(Torus(c, axis, r - 0.03, 0.018), 'wood', 0.0)
    add(Cylinder(c - axis * 0.04, c + axis * 0.04, 0.035, 0.008), 'rust', 0.0)
    u = norm(np.cross(axis, v3(0, 1, 0)))
    w = np.cross(axis, u)
    for k in range(6):
        a = ang + k * np.pi / 3
        dvec = u * np.cos(a) + w * np.sin(a)
        add(Capsule(c + dvec * 0.03, c + dvec * (r - 0.03), 0.011), 'wood', 0.0)


def build(P):
    parts, add = new_parts()
    lights = []
    col = P['collapse']
    L = 1.5          # chassis length (z)
    Wd = 0.62
    ch_y = 0.42 - 0.18 * col
    # ---- hull chassis: a cut boat hull, keel down, rusted plate with rivets
    def hull(p):
        q = p - v3(0, ch_y, 0)
        x, y, z = q[:, 0], q[:, 1], q[:, 2]
        t = np.clip(np.abs(z) / (L * 0.5), 0, 1)
        half = Wd * 0.5 * (1 - 0.55 * t ** 3)
        depth = 0.20 * (1 - 0.4 * t ** 2)
        e = np.sqrt((x / half) ** 2 + (np.minimum(y, 0) / depth) ** 2) - 1
        d = e * np.minimum(half, depth) * 0.7
        d = np.maximum(d, np.abs(z) - L * 0.5)
        d = np.maximum(d, y - 0.05)
        return d
    add(Func(hull, v3(0, ch_y - 0.05, 0), L * 0.6), 'hull', 0.0)
    # deck rim
    for sx in (-1, 1):
        add(Capsule(v3(sx * Wd * 0.47, ch_y + 0.05, -L * 0.45), v3(sx * Wd * 0.3, ch_y + 0.05, L * 0.45), 0.022), 'wood', 0.0)
        for k in range(5):
            z = -L * 0.4 + k * L * 0.2
            add(Sphere(v3(sx * Wd * 0.5 * (1 - 0.4 * (abs(z) / (L * 0.5)) ** 3), ch_y - 0.04, z), 0.014), 'tin', 0.0)
    # ---- wheels
    for sx in (-1, 1):
        for zz in (-L * 0.32, L * 0.30):
            r = 0.21
            c = v3(sx * (Wd * 0.5 + 0.05 + 0.1 * col * (zz > 0)), r - 0.06 * col * (zz > 0), zz)
            ax = norm(rot_z(sx * 0.4 * col * (zz > 0)) @ v3(1, 0, 0))
            wheel(add, c, r, ax, P['wheel'] + sx * 0.3)
        add(Capsule(v3(-Wd * 0.55, 0.21, -L * 0.32), v3(Wd * 0.55, 0.21, -L * 0.32), 0.02), 'iron', 0.0)
    # ---- bone A-frame and the launcher, pivoting at the top of the frame
    piv = v3(0, ch_y + 0.62 - 0.35 * col, 0.05)
    elev = np.radians(12) - np.radians(25) * col
    aim = norm(v3(0, np.sin(elev), np.cos(elev)))
    for sx in (-1, 1):
        for zz in (-0.25, 0.30):
            foot = v3(sx * Wd * 0.38, ch_y + 0.04, zz)
            add(Capsule(foot, piv + v3(sx * 0.07, 0, 0) + v3(sx * 0.2 * col, -0.1 * col, 0), 0.03, 0.022), 'bone', 0.01)
        lash(add, v3(sx * Wd * 0.38, ch_y + 0.04, -0.25), piv, n=1, r=0.035, at=(0.85,))
    add(Capsule(piv - v3(0.12, 0, 0), piv + v3(0.12, 0, 0), 0.03), 'rust', 0.0)
    # launcher rail (stock)
    rb, rf = piv - aim * 0.75, piv + aim * 0.65
    add(RoundBox((rb + rf) / 2, (0.05, 0.04, 0.72), 0.01, basis_from(v3(0, 1, 0) - aim * aim[1], aim)), 'wood', 0.0)
    # bow arms of bone + rope string (drawn back by `draw`)
    side = v3(1, 0, 0)
    bow_c = piv + aim * 0.48
    draw = P['draw'] * (1 - P['shot'])
    for sx in (-1, 1):
        tip = bow_c + side * sx * 0.60 - aim * (0.26 + 0.12 * draw) + v3(0, 0.05, 0)
        mid = bow_c + side * sx * 0.32 - aim * 0.03 + v3(0, 0.03, 0)
        add(Capsule(bow_c, mid, 0.045, 0.038), 'bone', 0.01)
        add(Capsule(mid, tip, 0.038, 0.020), 'bone', 0.01)
        add(Sphere(tip, 0.03), 'bone', 0.0)
        nock = bow_c - aim * (0.25 + 0.38 * draw)
        add(Capsule(tip, nock, 0.006), 'rope', 0.0)
    add(Torus(bow_c, aim, 0.055, 0.014), 'rope', 0.0)
    # the harpoon: mast-sized shaft with an iron barbed head; flies out on `shot`
    fly = P['shot'] * 0.75 - P['haul'] * 0.05
    hb = bow_c - aim * (0.25 + 0.38 * draw) + aim * fly
    ht = hb + aim * 1.05
    add(Capsule(hb, ht, 0.026), 'wood', 0.0)
    for t in (0.2, 0.5):
        add(Torus(hb + (ht - hb) * t, aim, 0.028, 0.008), 'iron', 0.0)
    add(Capsule(ht, ht + aim * 0.26, 0.065, 0.004), 'steel', 0.0)
    for sx in (-1, 1):   # barbs
        add(Capsule(ht + aim * 0.08, ht - aim * 0.08 + side * sx * 0.10, 0.02, 0.004), 'steel', 0.0)
        add(Capsule(ht + aim * 0.06, ht - aim * 0.05 + v3(0, sx * 0.065, 0), 0.014, 0.004), 'steel', 0.0)
    # ---- chain from the harpoon head back to the winch drum, bright links
    drum = v3(0, ch_y + 0.22 - 0.1 * col, -L * 0.36)
    add(Cylinder(drum - side * 0.2, drum + side * 0.2, 0.11, 0.01), 'wood', 0.0)
    for t in np.linspace(-0.16, 0.16, 5):
        add(Torus(drum + side * t, side, 0.115, 0.014), 'chain', 0.0)
    for sx in (-1, 1):   # drum posts
        add(Capsule(drum + side * sx * 0.23 + v3(0, -0.22, 0), drum + side * sx * 0.23, 0.03), 'rust', 0.0)
    ca = P['crank']
    crank_end = drum - side * 0.30 + v3(0, np.cos(ca) * 0.14, np.sin(ca) * 0.14)
    add(Capsule(drum - side * 0.26, drum - side * 0.30, 0.02), 'iron', 0.0)
    add(Capsule(drum - side * 0.30, crank_end, 0.016), 'iron', 0.0)
    add(Capsule(crank_end, crank_end - side * 0.1, 0.02), 'wood', 0.0)
    a = ht + aim * 0.0 - aim * 1.0 + v3(0, 0.0, 0)
    a = hb + aim * 0.06
    b = drum + v3(0, 0.11, 0)
    n = 16
    sag = 0.05 + 0.12 * (1 - P['shot']) * (1 - P['haul'])
    prev = None
    for k in range(n + 1):
        t = k / n
        p = a * (1 - t) + b * t + v3(0.03, -sag * np.sin(np.pi * t), 0)
        if prev is not None:
            dd = norm(p - prev)
            ax = np.cross(dd, v3(0, 1, 0)) if k % 2 else v3(0, 1, 0) - dd * dd[1]
            add(Torus((p + prev) / 2, norm(ax), 0.022, 0.008), 'chain', 0.0)
        prev = p
    # ---- lantern on a hooked bone post at the front left, a powder keg and a rope coil
    post_b = v3(Wd * 0.35, ch_y + 0.04, L * 0.38)
    post_t = post_b + v3(0.06 + 0.3 * col, 0.55 - 0.3 * col, 0.02)
    add(Capsule(post_b, post_t, 0.022, 0.016), 'bone', 0.0)
    add(Capsule(post_t, post_t + v3(0.0, -0.01, 0.12), 0.012), 'iron', 0.0)
    lc = post_t + v3(0, -0.10, 0.12)
    add(Capsule(post_t + v3(0, -0.01, 0.12), lc + v3(0, 0.055, 0), 0.004), 'iron', 0.0)
    tin_lantern(add, lights, lc, P['glow'], size=1.0)
    keg(add, v3(-Wd * 0.22, ch_y + 0.15, L * 0.22), up=(0, 1, 0), r=0.08, hh=0.1)
    add(Torus(v3(Wd * 0.18, ch_y + 0.08, -L * 0.12), v3(0, 1, 0), 0.08, 0.025), 'rope', 0.0)
    # a painted trade mark stripe on the hull
    if P['fx'] > 0:
        smoke_puffs(add, bow_c + v3(0, 0.05, 0), P['fx'], n=4, seed=4, spread=0.15, size=0.06)
    # whole-machine bob / pitch
    R = rot_x(-P['pitch'])
    t = v3(0, P['bob'], -0.28)
    parts[:] = transform_parts(parts, R=R, t=t, pivot=(0, 0, 0))
    for Lt in lights:
        Lt.pos = R @ Lt.pos + t
    mats = sv_materials(P)
    mats['hull'] = Material(painted_plate(lambda: v3(Wd * 0.5, ch_y - 0.05, 0.25), lambda: basis_from(v3(0, 1, 0), v3(1, 0, 0)) @ rot_y(np.pi / 2),
                                          letters_col=BONE, base=_hex('#7a4630')), spec=0.35, gloss=18, metal=0.3, brush=0.08)
    mats['chain'] = Material(_hex('#dfe4e6'), spec=1.0, gloss=70, metal=0.7, brush=0.02)
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS = [
    ('idle', 4, True, {}),
    ('move', 6, True, {}),
    ('attack', 10, False, {'hitFrame': 2}),
    ('hit', 10, False, {}),
    ('death', 6, False, {'holdLast': True}),
    ('cast', 8, False, {}),
]


def _f(**kw):
    P = dict(DEF)
    P.update(kw)
    return P


def frames():
    return {
        'idle': [(_f(glow=g, crank=c, bob=b), {}) for g, c, b in
                 zip([1.0, 0.6, 1.2, 0.8], [0.0, 0.25, 0.5, 0.25], [0, -0.006, 0, -0.003])],
        'move': [(_f(wheel=i * np.pi / 6, bob=[0, 0.02, 0, 0.015][i], pitch=[0.02, -0.01, 0.015, -0.015][i],
                     glow=[1, 0.85, 1.1, 0.9][i]), {}) for i in range(4)],
        'attack': [(_f(draw=[0.5, 1.0, 1.0, 0.0][i], shot=[0, 0, 1, 0.55][i], fx=[0, 0, 1, 0.3][i],
                       pitch=[0.0, -0.015, 0.03, 0.01][i], crank=[0.0, 0.9, 0.9, 0.4][i]), {}) for i in range(4)],
        'hit': [(_f(pitch=-0.04, bob=0.01), dict(exposure=1.25, flash=0.22)), (_f(pitch=-0.015), {})],
        'death': [(_f(pitch=-0.03, glow=0.8), {}),
                  (_f(collapse=0.3, glow=0.5, end=0.15, pitch=0.02), {}),
                  (_f(collapse=0.7, glow=0.2, end=0.5, pitch=0.05), {}),
                  (_f(collapse=1.0, glow=0.0, end=1.0, pitch=0.06), {})],
        'cast': [(_f(shot=0.6, haul=0.3, crank=-0.8, glow=1.2, pitch=-0.01), {}),
                 (_f(shot=0.35, haul=0.7, crank=-2.0, glow=1.4, pitch=-0.03), {}),
                 (_f(shot=0.0, haul=1.0, crank=-3.2, glow=1.1, pitch=-0.01), {})],
    }

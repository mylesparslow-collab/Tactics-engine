"""The Beacon (keystone objective): a stranded lighthouse on the drained seabed, still lit.

Rows: idle (the lens turns, a bright face sweeps round), hit (shudder and flash), death (the lamp
gutters, the tower cracks and leans, ending dark).
"""
import numpy as np
from kit.humanoid import *
from kit.xform import transform_parts
from render import Camera
from sdf import rot_z

UNIT_ID = 'keystone'
FACTION = 'lanternkeepers'
LOOK = LOOKS['lanternkeepers']
CAMERA = Camera(ppm=30.0)

STONE = _hex('#a8b2b9')
STONE_DK = _hex('#7c858d')
SALT = _hex('#e8e4d8')
BRASS = _hex('#b8924a')
SLATE = _hex('#2b3239')
LAMP = _hex('#ffd98a')

ROWS = [
    ('idle', 4, True, {}),
    ('hit', 10, False, {}),
    ('death', 6, False, {'holdLast': True}),
]


def neutral_pose():
    return dict(spin=0.0, glow=1.0, crack=0.0, lean=0.0, shake=0.0)


def _octagon(p, c, r_bot, r_top, y0, y1):
    """Tapered octagonal prism."""
    q = p - c
    y = q[:, 1]
    t = np.clip((y - y0) / (y1 - y0), 0, 1)
    r = r_bot + (r_top - r_bot) * t
    ang = np.arctan2(q[:, 2], q[:, 0])
    k = np.pi / 8
    a = np.mod(ang + k, 2 * k) - k
    rad = np.sqrt(q[:, 0] ** 2 + q[:, 2] ** 2) * np.cos(a)
    d = (rad - r) * 0.95
    return np.maximum(d, np.maximum(y0 - y, y - y1))


def build(P):
    parts, add = new_parts()
    sh = P['shake']
    o = v3(sh * 0.02, 0, 0)

    # rock plinth crusted with salt and barnacles
    def plinth(p):
        q = p - o
        d = np.sqrt((q[:, 0] / 0.62) ** 2 + (q[:, 2] / 0.55) ** 2) * 0.55 - 0.55
        d = np.maximum(d, q[:, 1] - 0.16 - 0.06 * fbm(q, 4.0, 2))
        return d + 0.03 * (fbm(q, 9.0, 2) - 0.5)
    add(Func(plinth, o + v3(0, 0.08, 0), 0.75), 'rock')
    for i, (x, z, r) in enumerate([(0.35, 0.28, 0.06), (-0.42, 0.18, 0.05), (0.15, 0.45, 0.045),
                                   (-0.2, 0.42, 0.04), (0.48, -0.05, 0.05)]):
        add(Sphere(o + v3(x, 0.16, z), r), 'barnacle', 0.02)

    # tower
    add(Func(lambda p: _octagon(p, o, 0.36, 0.25, 0.12, 2.55), o + v3(0, 1.3, 0), 1.35), 'tower')
    # door on the camera side
    dr = basis_from(v3(0, 1, 0), v3(-0.6, 0, 0.8))
    add(RoundBox(o + v3(-0.20, 0.42, 0.27), (0.09, 0.17, 0.03), 0.02, dr), 'door')
    # small windows up the tower
    for y, sx in ((1.05, -1), (1.65, 1), (2.1, -1)):
        r = 0.36 - 0.11 * (y - 0.12) / 2.43
        n = norm(v3(sx * 0.55, 0, 0.8))
        add(RoundBox(o + n * r + v3(0, y, 0), (0.035, 0.06, 0.03), 0.01, basis_from(v3(0, 1, 0), n)), 'window')

    # gallery: platform, rail ring and posts
    add(Cylinder(o + v3(0, 2.52, 0), o + v3(0, 2.6, 0), 0.38, 0.02), 'tower_dk')
    add(Torus(o + v3(0, 2.76, 0), v3(0, 1, 0), 0.37, 0.012), 'iron')
    for k in range(10):
        a = k / 10 * 2 * np.pi
        add(Capsule(o + v3(np.cos(a) * 0.37, 2.6, np.sin(a) * 0.37), o + v3(np.cos(a) * 0.37, 2.76, np.sin(a) * 0.37), 0.008), 'iron')
    # lantern room: glazed drum with brass mullions, domed cap, finial
    add(Cylinder(o + v3(0, 2.60, 0), o + v3(0, 2.98, 0), 0.20, 0.01), 'lens')
    for k in range(8):
        a = k / 8 * 2 * np.pi + np.pi / 8
        add(Capsule(o + v3(np.cos(a) * 0.205, 2.60, np.sin(a) * 0.205), o + v3(np.cos(a) * 0.205, 2.98, np.sin(a) * 0.205), 0.012), 'brass')
    add(Cylinder(o + v3(0, 2.97, 0), o + v3(0, 3.01, 0), 0.24, 0.01), 'brass')
    add(Ellipsoid(o + v3(0, 3.01, 0), (0.22, 0.16, 0.22)), 'cap', 0.0)
    add(Capsule(o + v3(0, 3.15, 0), o + v3(0, 3.30, 0), 0.012), 'brass')
    add(Sphere(o + v3(0, 3.31, 0), 0.03), 'brass')

    if P['lean'] != 0:
        parts[:] = transform_parts(parts, R=rot_z(-P['lean']), pivot=(0, 0.1, 0))

    g = P['glow']
    spin = P['spin']
    crack = P['crack']

    def lens_emis(p, n):
        # a bright beam face sweeping round the lens, plus the steady lamp behind the glass
        ang = np.arctan2(p[:, 2], p[:, 0])
        beam = np.exp(-((np.mod(ang - spin + np.pi, 2 * np.pi) - np.pi) / 0.45) ** 2)
        e = np.array(LAMP)[None, :] * (0.55 + 0.6 * beam[:, None]) * g
        return np.clip(e, 0, 1)

    def tower_alb(p, n):
        q = p - o
        y = q[:, 1]
        course = np.mod(y, 0.16) < 0.012                       # mortar lines between courses
        base = np.where(course[:, None], np.array(STONE_DK)[None, :], np.array(STONE)[None, :])
        base = base * (0.92 + 0.12 * fbm(p, 14, 2)[:, None])
        # salt tide-line: crust on the lower tower
        c = np.clip((0.75 - y) / 0.5, 0, 1) * fbm(p, 18, 3)
        cm = np.clip((c - 0.25) * 3, 0, 1)[:, None]
        base = base * (1 - cm) + np.array(SALT)[None, :] * cm
        if crack > 0:
            ang = np.arctan2(q[:, 2], q[:, 0])
            cr = np.abs(np.sin(ang * 3 + y * 6.0 + 1.3 * np.sin(y * 11))) < 0.12 * crack
            base[cr & (y > 0.4) & (y < 0.4 + 2.2 * crack)] = SLATE
        return base

    mats = {
        'rock': Material(lambda p, n: np.array(_hex('#9a9282'))[None, :] * (0.85 + 0.3 * fbm(p, 10, 3)[:, None]), spec=0.05, brush=0.1),
        'barnacle': Material(_hex('#d9d0b4'), spec=0.1, brush=0.1),
        'tower': Material(tower_alb, spec=0.06, gloss=10, brush=0.06),
        'tower_dk': Material(STONE_DK, spec=0.05),
        'door': Material(_hex('#4a3a2c'), spec=0.1),
        'window': Material(np.array(LAMP) * 0.8 * min(g, 1) + np.array(SLATE) * (1 - min(g, 1)), emissive=tuple(np.array(LAMP) * 0.55 * g)),
        'lens': Material(np.array(LAMP) * min(g, 1) + np.array(_hex('#46535a')) * (1 - min(g, 1)), spec=0.8, gloss=60, emissive=lens_emis, rim=0.0),
        'brass': Material(BRASS, spec=0.9, gloss=40, metal=0.9),
        'cap': Material(_hex('#3c4a4f'), spec=0.4, gloss=20, metal=0.4),
    }
    lights = [Light(pos=o + v3(0, 2.8, 0.3), color=_hex('#ffc46a'), intensity=1.4 * g, radius=0.5)]
    m = DEFAULT_MATS()
    m.update(mats)
    return Scene(parts=parts, materials=m, lights=lights)


def frames():
    def mk(**kw):
        P = neutral_pose()
        P.update(kw)
        return P
    return {
        'idle': [(mk(spin=i * np.pi / 2, glow=[1, .92, 1.05, .96][i]), {}) for i in range(4)],
        'hit': [(mk(shake=1.0, glow=1.2), dict(exposure=1.2, flash=0.2)), (mk(shake=-0.5), {})],
        'death': [(mk(glow=[0.7, 0.4, 0.15, 0.0][i], crack=[0.3, 0.6, 0.9, 1.0][i],
                      lean=[0.0, 0.03, 0.06, 0.08][i], shake=[1, -0.6, 0.3, 0][i]), {}) for i in range(4)],
    }

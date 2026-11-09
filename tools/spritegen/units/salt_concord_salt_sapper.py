"""Salt Sapper (Salt Concord demolition).

Stocky mine-crew sapper: leather apron over a patched canvas smock, a squared mining cap with a
brass lamp, goggles pushed up, a rock pick-hammer in the right hand and, pushed with the left, a
wheelbarrow stacked with bundled white salt charges and a lit fuse. Defining detail: the barrow of
salt charges with the sparking fuse.
"""
import numpy as np
from kit.humanoid import *
from kit.anim import humanoid_rows
from kit.looks import LOOKS
from render import Camera
from _salt_concord_common import *

UNIT_ID = 'salt_concord_salt_sapper'
FACTION = 'salt_concord'
LOOK = LOOKS[FACTION]
CAMERA = Camera(ppm=48)

C = Costume(top='smock', sleeve='smock', legs='road', hand='glove', skirt=None, head='none', belt='leather',
            girth=1.3, boots_tall=True)


def neutral_pose():
    P = base_pose(height=0.92, build=1.18)
    rig.lean(P, fwd=np.radians(10))
    P['head_yaw'] = np.radians(-8)
    P['head_pitch'] = np.radians(-6)
    rig.place_arm(P, 'r', v3(-0.30, 0.96, 0.20), (-1, -0.4, -0.4))
    P['item_r'] = norm(v3(-0.1, 0.9, 0.35))
    rig.place_arm(P, 'l', v3(0.28, 0.86, 0.26), (0.5, -0.5, -1))
    P['barrow_roll'] = 0.0
    dz = v3(0, 0, -0.30)
    for k in list(P):
        if isinstance(P[k], np.ndarray) and P[k].shape == (3,) and not k.startswith('item'):
            P[k] = P[k] + dz
    return P


def barrow(add, lights, P):
    g = P['wr_l'] + v3(0.0, 0.0, 0.0)
    # handles from the hand forward along z; tray body ahead; wheel at the nose
    ph = v3(g[0], g[1] - 0.02, g[2] - 0.12)
    nose = v3(g[0], 0.17, g[2] + 0.40)
    add(Capsule(ph, v3(g[0], g[1] - 0.12, g[2] + 0.40), 0.020), 'wood', 0.0)
    add(Capsule(v3(g[0] - 0.24, g[1] - 0.02, g[2] - 0.12), v3(g[0] - 0.22, g[1] - 0.12, g[2] + 0.40), 0.020), 'wood', 0.0)
    add(Capsule(v3(g[0] - 0.03, 0.02, g[2] + 0.12), v3(g[0] - 0.03, g[1] - 0.05, g[2] + 0.12), 0.015), 'wood', 0.0)  # stand leg
    c = v3(g[0] - 0.11, g[1] - 0.13, g[2] + 0.16)
    # tray: open box, tapered
    add(RoundBox(c + v3(0, 0.0, 0.0), (0.24, 0.016, 0.24), 0.01), 'iron', 0.0)
    add(RoundBox(c + v3(-0.255, 0.10, 0.0), (0.014, 0.10, 0.24), 0.008), 'iron', 0.0)
    add(RoundBox(c + v3(0.255, 0.10, 0.0), (0.014, 0.10, 0.24), 0.008), 'iron', 0.0)
    add(RoundBox(c + v3(0, 0.10, 0.235), (0.24, 0.10, 0.014), 0.008), 'iron', 0.0)
    add(RoundBox(c + v3(0, 0.10, -0.235), (0.24, 0.10, 0.014), 0.008), 'iron', 0.0)
    # white salt charges: bundled blocks and crystals, tied with rope
    spark = None
    for k, (x, z) in enumerate(((-0.12, -0.12), (0.11, -0.12), (-0.12, 0.07), (0.12, 0.08), (0.0, 0.17), (0.0, -0.02))):
        top = c + v3(x, 0.19 + 0.02 * (k % 2), z)
        add(Cylinder(top - v3(0, 0.20, 0), top, 0.065, 0.012), 'charge', 0.0)
        add(Torus(top - v3(0, 0.07, 0), v3(0, 1, 0), 0.066, 0.008), 'rope', 0.0)
        add(Cylinder(top + v3(0, 0.0, 0), top + v3(0, 0.025, 0), 0.020, 0.006), 'ink', 0.0)
        if k == 5:
            spark = top + v3(0, 0.12, 0.0)
            add(Capsule(top + v3(0, 0.02, 0), spark, 0.006), 'rope', 0.0)
    crystal(add, c + v3(-0.17, 0.17, 0.22), 0.16, 0.04, tilt=v3(-0.3, 1, 0.2))
    # fuse spark
    sg = 0.6 + 0.8 * P['glow'] * (0.5 + 0.5 * np.sin(P['tell'] * 6.283 * 2))
    add(Sphere(spark + v3(0, 0.012, 0), 0.018), 'fuse', 0.0)
    for j in range(3):
        a = P['tell'] * 6.283 + j * 2.1
        add(Sphere(spark + v3(0.03 * np.sin(a), 0.03 + 0.02 * j, 0.03 * np.cos(a)), 0.008), 'fuse', 0.0)
    lights.append(Light(pos=spark + v3(0, 0.03, 0.04), color=_hex('#ffb35a'), intensity=1.4 * sg, radius=0.20))
    # wheel at the nose, rolling with the move row
    wheel(add, v3(g[0] - 0.11, 0.17, g[2] + 0.40), v3(1, 0, 0), 0.17, angle=P['barrow_roll'], rim_mat='iron', spokes=6,
          width=0.05, tyre=0.03)
    add(Capsule(v3(g[0] - 0.11 - 0.07, 0.17, g[2] + 0.40), v3(g[0] - 0.11 - 0.07, g[1] - 0.14, g[2] + 0.30), 0.012), 'iron', 0.0)
    add(Capsule(v3(g[0] - 0.11 + 0.07, 0.17, g[2] + 0.40), v3(g[0] - 0.11 + 0.07, g[1] - 0.14, g[2] + 0.30), 0.012), 'iron', 0.0)


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    H, R, h = P['head'], head_R(P), P['height']
    # head: skin, squared mining cap, goggles up, lamp
    add(Ellipsoid(H, (0.078 * h, 0.097 * h, 0.088 * h), R), 'skin', 0.0)
    add(Ellipsoid(H + R @ v3(0, -0.05, 0.022) * h, (0.060 * h, 0.05 * h, 0.064 * h), R), 'skin', 0.03)
    add(Capsule(H + R @ v3(0, 0.0, 0.078) * h, H + R @ v3(0, -0.028, 0.092) * h, 0.010, 0.013), 'skin', 0.01)
    kettle_helm(P, add, 'cap', size=1.05, brim=0.7, tall=0.8)
    goggles(P, add, up=True) if False else None
    for sx in (-1, 1):
        c = H + R @ v3(sx * 0.036, 0.062, 0.088) * h
        add(Cylinder(c - R @ v3(0, 0, 0.012), c + R @ v3(0, 0, 0.012), 0.024, 0.005), 'brass', 0.0)
        add(Cylinder(c + R @ v3(0, 0, 0.008), c + R @ v3(0, 0, 0.016), 0.017, 0.003), 'glass', 0.0)
    lamp = H + R @ v3(0, 0.092, 0.085) * h
    add(RoundBox(lamp, (0.032, 0.03, 0.03), 0.01, R), 'brass', 0.0)
    add(Cylinder(lamp + R @ v3(0, 0, 0.03), lamp + R @ v3(0, 0, 0.042), 0.022, 0.004), 'glass', 0.0)
    lights.append(Light(pos=lamp + R @ v3(0, 0.0, 0.08), color=_hex('#ffcf7a'), intensity=1.0 * P['glow'], radius=0.14))
    # leather apron over the smock, squared bib; neck scarf
    tabard(P, add, 'apron', width=0.15, hem=0.36, top=0.20, zf=0.125, zb=0.12, back=False)
    add(RoundBox(ch + v3(0, 0.02, 0.105), (0.115 * P['build'], 0.15, 0.010), 0.008), 'apron', 0.0)
    add(Torus(nk + v3(0, -0.02, 0), v3(0, 1, 0.1), 0.085, 0.024), 'steelcloth', 0.01)
    square_pauldrons(P, add, 'iron', size=0.9, trim='leather')
    # tool bandolier: little fuse spools on the hip
    for k in range(3):
        add(Cylinder(pel + v3(0.17, 0.0 + 0.0 * k, 0.0) + v3(0.0, -0.01, 0.05 * (k - 1)),
                     pel + v3(0.23, -0.01, 0.05 * (k - 1)), 0.026, 0.006), 'rope', 0.0)
    # pick-hammer in the right hand
    r = held(P, add, 'r', 'hammer', shaft='wood', head='iron', below=0.12, above=0.58)
    if r is not None:
        butt, tip = r
        d = norm(tip - butt)
        add(Capsule(tip - d * 0.01, tip - d * 0.01 + norm(np.cross(d, v3(0, 1, 0.1))) * -0.15, 0.014, 0.003), 'iron', 0.0)
    barrow(add, lights, P)
    mats = base_mats(P)
    mats.update({
        'smock': salted(_hex('#a69c86'), 0.3, ground=0.7, gamt=0.9, vary=0.16, brush=0.1),
        'apron': salted(_hex('#5a3f2c'), 0.2, ground=0.4, gamt=0.7, spec=0.2, gloss=18),
        'road': salted(_hex('#6d6c68'), 0.3, ground=0.5, gamt=1.0),
        'cap': salted_metal(_hex('#7a8088'), amount=0.55),
        'glass': Material(_hex('#ffcf7a'), spec=0.3, gloss=30, emissive=tuple(np.array(_hex('#ffcf7a')) * 1.0), rim=0.0),
        'charge': Material(lambda p, n: np.array(SALT_HI)[None, :].repeat(len(p), 0) * (0.9 + 0.12 * fbm(p, 24, 2)[:, None]), spec=0.1, brush=0.05),
        'rope': salted(_hex('#9a8a68'), 0.2, spec=0.02),
        'fuse': Material(_hex('#ffd48a'), emissive=tuple(np.array(_hex('#ffb347')) * 1.3), rim=0.0),
        'glove': Material(_hex('#4a382a'), spec=0.12, gloss=14, brush=0.05),
        'skin': skin_mat(P, skin=W['skin_mid'], hair=_hex('#3a2a20'), beard=_hex('#4a382c')),
    })
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, _frames = humanoid_rows(neutral_pose, attack_style='swing', weapon_side='r', cast_side='r')


def frames():
    f = _frames()
    for row, fr in f.items():
        for i, (P, lo) in enumerate(fr):
            # left hand stays on the barrow handle; right arm does the work
            base = neutral_pose()
            P['barrow_roll'] = {'idle': 0.0, 'move': i * 0.9}.get(row, 0.0)
            if row != 'death':
                drop = P['pelvis'] - base['pelvis']
                rig.place_arm(P, 'l', base['wr_l'] + v3(0, drop[1] * 0.6, 0.0), (0.5, -0.5, -1))
            if row == 'move':
                P['barrow_roll'] = i * 0.9
    return f

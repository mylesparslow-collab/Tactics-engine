"""Hesk Varrow, the Forger (Salvage Compact hero).

Thin, sharp and tall: the direct opposite of Odo Brask's bulk. A long narrow soot-black frock coat with a
high collar and a rust-red lining, a tall brimless soot-felt cap, slicked hair and a pencil moustache,
round tinted goggles pushed up. Hanging across the chest on a ribbon: a row of red wax seals; a brass-
cornered ledger under the left arm; a stylus-quill in the right hand and a fan of thin paper blades at
the belt. Papers trail from his pockets. Defining detail: the strings of wax seals and the ledger.
"""
import numpy as np
from _salvage_compact_common import *
from _salvage_compact_w2 import *

UNIT_ID = 'salvage_compact_hesk_varrow'
FACTION = 'salvage_compact'

C = Costume(top='frock', sleeve='frock', legs='trousers', hand='glove', skirt='coat', skirt_mat='frock', hem=0.12,
            flare=0.55, head='hair', hair='hair', hair_style='short', belt='leather', girth=0.80, boots_tall=True)


def neutral_pose():
    P = base_pose(height=1.10, build=0.78)
    rig.lean(P, fwd=np.radians(-2))
    P['head_yaw'] = np.radians(-12)
    P['head_pitch'] = np.radians(-3)
    rig.place_arm(P, 'r', v3(-0.20, 1.20, 0.22), (-1, -0.2, -0.6))
    P['item_r'] = norm(v3(-0.15, 0.7, 0.6))
    rig.place_arm(P, 'l', v3(0.11, 1.05, 0.20), (0.6, -0.5, -0.6))
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    H, R, h, b = P['head'], head_R(P), P['height'], P['build']
    # coat details: tall stiff collar, rust lining showing at the open front, tails
    add(Cylinder(nk + v3(0, -0.04, -0.004), nk + v3(0, 0.05, -0.012), 0.062, 0.012), 'frock', 0.0)
    add(Cylinder(nk + v3(0, -0.01, 0.0), nk + v3(0, 0.0, 0.0), 0.066, 0.006), 'lining', 0.0)
    for sx in (-1, 1):
        add(RoundBox(ch + v3(sx * 0.055, -0.02, 0.098), (0.014, 0.17, 0.007), 0.004, rot_z(sx * 0.08)), 'lining', 0.0)
    add(Cylinder(nk + v3(0, -0.05, 0.02), nk + v3(0, -0.035, 0.02), 0.058, 0.004), 'bone', 0.0)    # cravat
    add(Capsule(nk + v3(0.0, -0.045, 0.07), nk + v3(0.01, -0.16, 0.085), 0.020, 0.012), 'bone', 0.0)
    # tall brimless cap of soot felt
    add(Cylinder(H + R @ v3(0, 0.05, -0.01) * h, H + R @ v3(0, 0.15, -0.015) * h, 0.074 * h, 0.012), 'felt', 0.0)
    add(Cylinder(H + R @ v3(0, 0.15, -0.015) * h, H + R @ v3(0, 0.158, -0.015) * h, 0.070 * h, 0.006), 'felt', 0.0)
    add(Cylinder(H + R @ v3(0, 0.055, -0.01) * h, H + R @ v3(0, 0.075, -0.01) * h, 0.080 * h, 0.006), 'rust', 0.0)  # band
    add(RoundBox(H + R @ v3(0.0, 0.12, 0.062) * h, (0.014, 0.020, 0.004), 0.003, R), 'seal', 0.0)          # a seal as cap badge
    # pencil moustache and round tinted goggles pushed up under the cap
    for sx in (-1, 1):
        c = H + R @ v3(sx * 0.038, 0.062, 0.078) * h
        add(Cylinder(c, c + R @ v3(0, 0.0, 0.01), 0.020, 0.004), 'brass', 0.0)
        add(Cylinder(c + R @ v3(0, 0, 0.007), c + R @ v3(0, 0, 0.013), 0.014, 0.003), 'goggle', 0.0)
    # chest: a ribbon of red wax seals and keys
    a0 = nk + v3(-0.07, -0.04, 0.08)
    a1 = pel + v3(0.12, 0.17, 0.12)
    add(Capsule(a0, a1, 0.009), 'rust', 0.0)
    for k in range(6):
        t = (k + 0.5) / 6
        pt = a0 * (1 - t) + a1 * t
        add(Capsule(pt, pt + v3(0, -0.04, 0.012), 0.006), 'rope', 0.0)
        add(Cylinder(pt + v3(0, -0.04, 0.012), pt + v3(0, -0.04, 0.026), 0.032, 0.008), 'seal', 0.0)
        if k % 2 == 0:
            add(Cylinder(pt + v3(0, -0.04, 0.026), pt + v3(0, -0.04, 0.030), 0.012, 0.002), 'gold', 0.0)
    # ledger (brass corners) clamped under the left arm / held at the left hand
    g = hand_pos(P, 'l')
    Lc = g + v3(0.02, 0.01, 0.02)
    add(RoundBox(Lc, (0.085, 0.115, 0.024), 0.008, rot_x(0.35) @ rot_z(0.12)), 'ledger', 0.0)
    add(RoundBox(Lc + v3(0, 0.0, 0.0), (0.087, 0.026, 0.026), 0.006, rot_x(0.35) @ rot_z(0.12)), 'bone', 0.0)   # page edge band
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        add(Sphere(Lc + v3(dx * 0.080, dy * 0.108, 0.02), 0.011), 'brass', 0.0)
    # papers stuffed in the coat pocket
    pp = pel + v3(-0.16, 0.05, 0.07)
    for k in range(3):
        add(RoundBox(pp + v3(-0.01 * k, 0.07 + 0.012 * k, 0.0), (0.020, 0.06, 0.004), 0.002, rot_z(0.15 * (k - 1))), 'paper', 0.0)
    # fan of thin blades at the belt (Thirty Knives)
    for k in range(5):
        a = np.radians(-28 + 14 * k)
        c = pel + v3(0.15, 0.00, 0.07)
        dv = v3(np.sin(a) * 0.6 + 0.4, -0.9 * np.cos(a), 0.18)
        add(Capsule(c, c + norm(dv) * 0.19, 0.008, 0.002), 'steel', 0.0)
    add(Sphere(pel + v3(0.15, 0.01, 0.07), 0.016), 'brass', 0.0)
    # quill-stylus in the right hand
    d = P['item_r']
    if d is not None:
        d = norm(d)
        gr = hand_pos(P, 'r')
        add(Capsule(gr - d * 0.04, gr + d * 0.26, 0.008, 0.003), 'steel', 0.0)
        sv = norm(np.cross(d, v3(0, 0, 1)))
        add(Capsule(gr + d * 0.18, gr + d * 0.30 + sv * 0.06 + v3(0, 0.06, 0), 0.013, 0.002), 'paper', 0.0)   # quill vane
        if P['cast_glow'] > 0.05:                  # cast: papers flutter out
            for k in range(5):
                a = k * 1.3 + P['tell'] * 6.28
                pc = gr + d * (0.20 + 0.10 * k * P['cast_glow']) + v3(0.05 * np.sin(a), 0.03 * k * P['cast_glow'], 0.05 * np.cos(a))
                add(RoundBox(pc, (0.030, 0.002, 0.040), 0.002, rot_y(a)), 'paper', 0.0)
    mats = sv_materials(P, skin='light', hair=_hex('#2a2018'), beard=None)
    mats['skin'] = Material(face_albedo(P, _hex('#e1b797'), _hex('#241a14'), lips=_hex('#9a4a40'),
                                        eyes=_hex('#1f1612')), spec=0.08, gloss=14, sss=0.6, brush=0.02)
    mats.update({
        'frock': Material(lambda p, n: np.array(_hex('#46423c'))[None, :] * (0.9 + 0.22 * fbm(p, 14, 2)[:, None]) + np.array(BONE)[None, :] * 0.10 * (fbm(p, 26, 2) > 0.7)[:, None],
                          spec=0.25, gloss=18, brush=0.08),
        'lining': Material(_hex('#a8402c'), spec=0.1, gloss=12, brush=0.06),
        'felt': Material(_hex('#363230'), spec=0.04, brush=0.1),
        'trousers': Material(_hex('#4e4a44'), spec=0.04, brush=0.08),
        'seal': Material(_hex('#b02f22'), spec=0.5, gloss=30, brush=0.04),
        'gold': Material(_hex('#d9b25a'), spec=1.0, gloss=50, metal=0.9),
        'paper': Material(_hex('#e4dcc2'), spec=0.04, brush=0.06),
        'ledger': Material(_hex('#4a2a22'), spec=0.3, gloss=20, brush=0.06),
        'steel': Material(_hex('#c9ced3'), spec=1.0, gloss=60, metal=0.6),
        'goggle': Material(_hex('#d0b27a'), spec=1.0, gloss=60, emissive=tuple(np.array(_hex('#b08a4a')) * 0.2), rim=0.0),
        'hair': Material(_hex('#2a2018'), spec=0.3, gloss=20, brush=0.08),
    })
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = sv_rows(neutral_pose, attack_style='swing', weapon_side='r', fidget='look', cast_side='r')

"""Rim Marshal (Salt Concord commander).

Officer of the Rim Wardens: long steel-blue greatcoat with salt trim, a squared salt mantle, brass
gorget and sash, a crested kettle helm, a drawn marshal's blade and a tall back-standard (a squared
steel-blue banner with the salt stair) that marks where the line forms. Idle tell: the standard stirs.
Defining detail: the back-standard.
"""
import numpy as np
from kit.humanoid import *
from kit.anim import humanoid_rows
from kit.looks import LOOKS
from _salt_concord_common import *

UNIT_ID = 'salt_concord_rim_marshal'
FACTION = 'salt_concord'
LOOK = LOOKS[FACTION]

C = Costume(top='coat', sleeve='coat', legs='road', hand='glove', skirt='coat', skirt_mat='coat', hem=0.26,
            flare=0.9, head='bald', belt='leather', girth=1.05)


def neutral_pose():
    P = base_pose(height=1.03, build=1.08)
    rig.place_arm(P, 'r', v3(-0.26, 1.0, 0.16), (-1, -0.3, -0.5))
    P['item_r'] = norm(v3(-0.15, -0.55, 1.0))
    rig.place_arm(P, 'l', v3(0.20, 1.02, 0.02), (1, -0.1, 0.3))      # fist on hip
    P['head_yaw'] = np.radians(-14)
    P['head_pitch'] = np.radians(-4)
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    kettle_helm(P, add, 'helmiron', brim_mat='brass', size=1.04, brim=0.9, comb=True)
    add(capelet_shell(P, depth=0.17, width=0.23, sq=5.0), 'salt')
    add(Cylinder(nk + v3(0, -0.04, -0.005), nk + v3(0, 0.03, -0.01), 0.078, 0.01), 'brass')        # gorget
    add(Capsule(P['sh_r'] + v3(0.03, -0.06, 0.08), pel + v3(0.13, 0.08, 0.10), 0.02), 'sash')      # sash
    add(RoundBox(pel + v3(0, 0.08, 0.11), (0.026, 0.026, 0.008), 0.004), 'brass')
    for s in ('r', 'l'):
        el, wr = P['el_' + s], P['wr_' + s]
        add(Capsule(el + (wr - el) * 0.70, wr - (wr - el) * 0.02, 0.049), 'salt')
    # back standard: pole from between the shoulder blades, squared banner on a crossbar
    sw = 0.5 * np.sin(P['tell'] * 2 * np.pi) + P['skirt_sway'] * 0.4
    base = ch + v3(0.05, -0.10, -0.15)
    top = base + v3(0.04, 0.92, -0.02)
    add(Capsule(base, top, 0.014), 'wood')
    add(RoundBox(base + v3(0, 0.12, 0.02), (0.03, 0.06, 0.02), 0.006), 'leather')
    add(Sphere(top + v3(0, 0.02, 0), 0.026), 'brass')
    bar = top + v3(0, -0.05, 0)
    add(Capsule(bar + v3(-0.02, 0, 0.02), bar + v3(0.02, 0, -0.30), 0.010), 'wood')
    fc = bar + v3(0.0, -0.20, -0.15) + v3(0.015 * sw, 0, 0)
    FR = rot_y(np.radians(-6) + 0.12 * sw) @ rot_x(0.02 * sw)
    P['_fc'], P['_FR'] = fc, FR
    add(RoundBox(fc, (0.008, 0.19, 0.15), 0.004, FR), 'banner')
    mats = base_mats(P)

    def banner(p, n):
        q = (p - P['_fc']) @ P['_FR']
        y, z = q[:, 1], q[:, 2]
        a = np.array(STEEL)[None, :].repeat(len(p), 0) * (0.92 + 0.12 * fbm(p, 20, 2)[:, None])
        edge = (np.abs(z) > 0.125) | (np.abs(y) > 0.165)
        a[edge] = SALT
        for i in range(3):
            m = (z > -0.09 + i * 0.06) & (z < 0.09) & (y > -0.12 + i * 0.06) & (y < -0.06 + i * 0.06)
            a[m] = SALT
        return salt_seams(a, p, 0.25, 30, 0.0, 0.0)
    mats.update({
        'coat': salted(STEEL, 0.3, ground=0.7, gamt=0.9),
        'sash': salted(INK, 0.2),
        'banner': Material(banner, spec=0.03, brush=0.07),
        'skin': skin_mat(P, skin=W['skin_light'], hair=_hex('#9a948a'), beard=_hex('#a8a296')),
    })
    held(P, add, 'r', 'blade', head='brass', above=0.72)
    return finish(P, FACTION, parts, mats)


ROWS, frames = humanoid_rows(neutral_pose, attack_style='swing', weapon_side='r', cast_side='l')

"""Warden-General Hesper Vael, Marshal of the Greywater Stair (Salt Concord hero).

The oldest living Stair-Warden: broad, weathered, grey hair cropped square, bare-headed with a scar.
A salt-crusted steel cuirass and squared pauldrons over a long steel-blue surcoat with the Stair
in salt-white down the front, a heavy salt-white mantle pinned with brass, and the Stair Halberd:
a squared axe blade and spike on a long haft, a steel-blue banner with the Stair hanging from the
crossbar. Defining detail: the planted halberd and its stair banner, held like a gate.
"""
import numpy as np
from kit.humanoid import *
from kit.anim import humanoid_rows
from kit.looks import LOOKS
from _salt_concord_common import *

UNIT_ID = 'salt_concord_hesper_vael'
FACTION = 'salt_concord'
LOOK = LOOKS[FACTION]

C = Costume(top='surcoat', sleeve='mail', legs='road', hand='gauntlet', skirt='coat', skirt_mat='surcoat', hem=0.20,
            flare=0.85, head='hair', hair='hair', hair_style='short', belt='leather', girth=1.25)


def neutral_pose():
    P = base_pose(height=1.02, build=1.18)
    rig.place_arm(P, 'r', v3(-0.37, 1.24, 0.16), (-1, -0.3, -0.5))
    P['item_r'] = norm(v3(-0.10, 1.0, 0.05))
    rig.place_arm(P, 'l', v3(0.17, 0.97, 0.15), (0.3, -0.2, -1))     # gauntlet resting on the belt
    P['head_yaw'] = np.radians(-16)
    P['head_pitch'] = np.radians(-3)
    rig.place_leg(P, 'r', v3(-0.15, 0.085, -0.03), l1=0.43 * 1.02, l2=0.42 * 1.02)
    rig.place_leg(P, 'l', v3(0.16, 0.085, 0.09), l1=0.43 * 1.02, l2=0.42 * 1.02)
    return P


def halberd(P, add):
    d = P['item_r']
    if d is None:
        return
    d = norm(d)
    g = hand_pos(P, 'r')
    vert = d[1] > 0.85 and g[1] < 1.4
    # in the overhead slam the hands choke up toward the head so the blade stays in frame
    above = 0.92 if g[1] < 1.45 else 0.62
    butt, tip = g - d * (1.22 if vert else 0.75), g + d * above
    add(Capsule(butt, tip, 0.019), 'haft')
    add(Cylinder(butt, butt + d * 0.06, 0.024, 0.004), 'brass')
    for t in (0.55, 0.62):
        add(Cylinder(g + d * (t - 0.6), g + d * (t - 0.57), 0.024, 0.004), 'brass')
    side = norm(np.cross(d, v3(0, 0, 1)))
    if side[0] > 0:
        side = -side           # blade toward the camera side
    fwd = np.cross(side, d)
    R = np.stack([side, d, fwd], axis=1)
    hc = tip - d * 0.18
    # squared axe blade (a trapezoid) and back spike
    R2 = np.stack([fwd, d, -side], axis=1)

    def blade(p, c=hc):
        q = (p - c) @ R2
        x, y, z = q[:, 0], q[:, 1], q[:, 2]
        hy = 0.07 + 0.08 * np.clip(x / 0.20, 0, 1)
        dd = np.maximum(np.maximum(-x, x - 0.20), np.abs(y) - hy)
        return np.maximum(dd * 0.9, np.abs(z) - 0.008)
    add(Func(blade, hc + fwd * 0.10, 0.22), 'steel')
    add(Capsule(hc - fwd * 0.02, hc - fwd * 0.15 + d * 0.02, 0.016, 0.003), 'steel')
    add(Capsule(tip - d * 0.06, tip + d * 0.16, 0.022, 0.002), 'steel')                 # top spike
    add(RoundBox(hc, (0.03, 0.06, 0.03), 0.008, R), 'brass')
    # crossbar under the head and a hanging stair banner
    cb = tip - d * 0.27
    add(Capsule(cb - side * 0.04, cb + side * 0.26, 0.011), 'brass')
    sw = 0.4 * np.sin(P['tell'] * 2 * np.pi) + P['skirt_sway'] * 0.3
    fc = cb + side * 0.15 + v3(0, -0.14, 0) + fwd * (0.01 * sw)
    FR = basis_from(v3(0, 1, 0), fwd) @ rot_y(0.1 * sw)
    P['_fc'], P['_FR'] = fc, FR
    add(RoundBox(fc, (0.10, 0.13, 0.006), 0.004, FR), 'banner')
    # swallow tails
    for sx in (-1, 1):
        a = fc + FR[:, 0] * sx * 0.055 - FR[:, 1] * 0.12
        add(Capsule(a, a - FR[:, 1] * 0.07 + FR[:, 0] * sx * 0.01, 0.03, 0.008), 'banner_t')


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    b = P['build']
    # cuirass and fauld, salt crusted
    add(Ellipsoid(ch + v3(0, 0.03, 0.012), (0.16 * b, 0.15, 0.118 * b)), 'plate', 0.02)
    for i in range(2):
        add(RoundBox(pel + v3(0, 0.03 - i * 0.055, 0.0), (0.15 * b, 0.026, 0.11 * b), 0.02), 'plate')
    square_pauldrons(P, add, 'plate', size=0.95, trim='brass')
    # heavy salt mantle with brass clasps
    add(capelet_shell(P, depth=0.24, width=0.25, sq=5.0), 'mantle')
    for sx in (-1, 1):
        add(Cylinder(nk + v3(sx * 0.07, -0.06, 0.07), nk + v3(sx * 0.07, -0.06, 0.09), 0.024, 0.005), 'brass')
    add(Capsule(nk + v3(-0.07, -0.06, 0.09), nk + v3(0.07, -0.06, 0.09), 0.005), 'brass')
    # gorget
    add(Cylinder(nk + v3(0, -0.04, -0.005), nk + v3(0, 0.02, -0.01), 0.075, 0.01), 'plate')
    # cropped grey hair (squared) and a scar painted via the skin mat
    halberd(P, add)
    mats = base_mats(P)

    def surcoat(p, n):
        x = p[:, 0] - P['pelvis'][0]
        y = p[:, 1] - (P['pelvis'][1] - 0.94 * P['height'])
        a = np.array(STEEL)[None, :].repeat(len(p), 0) * (0.93 + 0.1 * fbm(p, 20, 2)[:, None])
        front = (p[:, 2] - P['pelvis'][2]) > 0.05
        # stair steps in salt down the front of the skirt
        for i in range(4):
            m = front & (y > 0.30 + i * 0.09) & (y < 0.37 + i * 0.09) & (x > -0.10 + i * 0.035) & (x < 0.10)
            a[m] = SALT
        a[y < 0.28] = SALT
        return salt_seams(a, p, 0.3, 24, 0.7, 1.0)

    def banner(p, n):
        q = (p - P['_fc']) @ P['_FR']
        x, y = q[:, 0], q[:, 1]
        a = np.array(STEEL)[None, :].repeat(len(p), 0) * (0.93 + 0.1 * fbm(p, 20, 2)[:, None])
        a[(np.abs(x) > 0.08) | (y > 0.11)] = SALT
        for i in range(3):
            m = (x > -0.07 + i * 0.045) & (x < 0.07) & (y > -0.10 + i * 0.05) & (y < -0.055 + i * 0.05)
            a[m] = SALT
        return salt_seams(a, p, 0.2, 30, 0.0, 0.0)

    def skin(p, n, base=face_albedo(P, _hex('#cf9d80'), _hex('#b8b2a8'), lips=_hex('#9a5a4e'))):
        a = base(p, n)
        q = (p - P['head']) @ head_R(P) / P['height']
        scar = (np.abs(q[:, 0] + 0.03 - 0.25 * (q[:, 1] - 0.0)) < 0.005) & (q[:, 1] > -0.04) & (q[:, 1] < 0.05) & (q[:, 2] > 0.04)
        a[scar] = _hex('#e8c8b6')
        return a
    mats.update({
        'surcoat': Material(surcoat, spec=0.04, brush=0.08),
        'plate': salted_metal(_hex('#8a929c'), amount=0.5),
        'mail': salted_metal(IRON_DK, amount=0.35, spec=0.4),
        'gauntlet': salted_metal(IRON, amount=0.3),
        'mantle': salted(SALT, 0.15, vary=0.08),
        'hair': Material(_hex('#b8b2a8'), spec=0.15, brush=0.12),
        'skin': Material(skin, spec=0.06, gloss=12, sss=0.5, brush=0.02),
        'haft': salted(_hex('#4e3a2a'), 0.25),
        'banner': Material(banner, spec=0.03, brush=0.07),
        'banner_t': pennant_mat(),
    })
    return finish(P, FACTION, parts, mats)


ROWS, frames = humanoid_rows(neutral_pose, attack_style='slam', weapon_side='r', cast_side='l')

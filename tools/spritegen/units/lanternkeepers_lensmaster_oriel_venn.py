"""Lensmaster Oriel Venn, Mistress of the Seventh Lens (Lanternkeepers hero).

Tall and lean, a long night-slate coat with a high collar and oilskin lining, dark hair pinned
up, a brass loupe at one eye. Defining detail: the Seventh Lens staff, a great lens in a brass
ring at the top with seven small lenses set round it and a lamp burning behind; on the attack she
levels it and folds the beam into a blade of light.
"""
import numpy as np
from _lanternkeepers_common import *

UNIT_ID = 'lanternkeepers_lensmaster_oriel_venn'
FACTION = 'lanternkeepers'
LOOK = LOOKS[FACTION]

C = Costume(top='slate', sleeve='slate', legs='slate', boot='boot', hand='glove', skirt='coat',
            skirt_mat='venncoat', hem=0.12, flare=0.55, head='hair', hair='hair', hair_style='tail',
            belt='leather', girth=0.88)


def neutral_pose():
    P = base_pose(height=1.06, build=0.88)
    h = P['height']
    P['head_yaw'] = np.radians(-18)
    rig.place_arm(P, 'r', v3(-0.33, 1.02, 0.14), (-1, -0.5, -0.4), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(-0.17, 1.0, 0.04))
    rig.place_arm(P, 'l', v3(0.20, 0.98, 0.14), (1, -0.3, -0.5), l1=0.27 * h, l2=0.26 * h)
    return P


def lens_staff(add, lights, P):
    d = P['item_r']
    if d is None:
        return
    d = norm(d)
    g = hand_pos(P, 'r')
    butt, top = g - d * 1.08, g + d * 0.78
    add(Capsule(butt, top, 0.016, 0.014), 'wood')
    add(Cylinder(top - d * 0.04, top + d * 0.01, 0.026, 0.005), 'brass')
    # lens faces "forward" relative to the staff
    fwd = norm(v3(-0.35, 0, 1.0) - d * (v3(-0.35, 0, 1.0) @ d))
    up = d
    c = top + up * 0.13
    add(Torus(c, fwd, 0.13, 0.012), 'brass')
    add(Ellipsoid(c, (0.115, 0.014, 0.115), basis_from(fwd)), 'lens')
    side = norm(np.cross(up, fwd))
    for k in range(7):   # the seven lenses: a rack in a shallow arc under the great lens
        lc = c - up * (0.17 + 0.03 * abs(k - 3) ** 1.3 * 0.4) + side * (k - 3) * 0.052
        add(Torus(lc, fwd, 0.022, 0.006), 'brass')
        add(Ellipsoid(lc, (0.019, 0.006, 0.019), basis_from(fwd)), 'lens')
    add(Capsule(c - up * 0.17 - side * 0.16, c - up * 0.17 + side * 0.16, 0.007), 'brass')
    lamp_c = c - fwd * 0.07
    add(Sphere(lamp_c, 0.04), 'lamp')
    light_at(lights, P, c + fwd * 0.08, 2.4, 0.24)
    fx = P['fx']
    if fx > 0:
        add(Capsule(c + fwd * 0.03, c + fwd * (0.05 + 1.7 * fx), 0.035 * fx + 0.005, 0.008), 'beam')
        light_at(lights, P, c + fwd * 0.5, 3.0 * fx, 0.4, color=_hex('#ffd27a'))


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    # high collar
    nk = P['neck']
    add(Cylinder(nk + v3(0, -0.04, -0.01), nk + v3(0, 0.06, -0.02), 0.075, 0.012), 'slate')
    # loupe on the right eye
    H, R, h = P['head'], head_R(P), P['height']
    add(Cylinder(H + R @ v3(-0.035, 0.005, 0.075) * h, H + R @ v3(-0.035, 0.005, 0.10) * h, 0.018, 0.004), 'brass')
    lens_staff(add, lights, P)
    # lens case and ground-glass pouch
    pel = P['pelvis']
    add(RoundBox(pel + v3(0.15, 0.0, 0.06), (0.03, 0.05, 0.05), 0.012), 'leather')
    mats = keeper_mats(P, hair=_hex('#24201f'), skin=W['skin_light'])
    mats['venncoat'] = Material(lambda p, n: np.where(((p[:, 2] - P['pelvis'][2]) > 0.06)[:, None] &
                                                      (np.abs(p[:, 0] - P['pelvis'][0]) < 0.06)[:, None],
                                                      np.array(_hex('#a88a4a'))[None, :], np.array(SLATE)[None, :] * 1.35),
                                spec=0.12, gloss=14, brush=0.08)
    mats['lens'] = Material(LENS, spec=1.4, gloss=90, emissive=tuple(np.array(LENS) * min(1.0, 0.18 + 0.82 * max(P['cast_glow'], P['fx']))), rim=0.6, brush=0.0)
    return finish(P, FACTION, parts, mats, lights=lights)


def _post(fr):
    for i, (P, o) in enumerate(fr['attack']):
        P['fx'] = [0, 0, 1, 0.25][i]
    return fr


ROWS, frames = keeper_rows(neutral_pose, attack_style='thrust', weapon_side='r', cast_side='l', post=_post, pole='r')

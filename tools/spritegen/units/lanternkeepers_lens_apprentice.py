"""Lens-Apprentice (Lanternkeepers cheap body, ranged). A young keeper, smaller than the line troops, in a
too-big sea-grey smock under a canvas apron glittering with glass-dust, hair in a short tail, a knit cap pushed
back. Defining detail: the cracked lens held out at arm's length like a shield, a web of cracks and a chipped
edge, a bright point of light caught in it; on the attack it spits a bolt through the crack."""
import numpy as np
from _lanternkeepers_w2 import *

UNIT_ID = 'lanternkeepers_lens_apprentice'
FACTION = 'lanternkeepers'
LOOK = LOOKS[FACTION]

C = Costume(top='coatgrey', sleeve='coatgrey', legs='slate', boot='boot', hand='skin', skirt='coat',
            skirt_mat='coatgrey', hem=0.55, flare=0.6, head='hair', hair='hair', hair_style='tail', belt='leather',
            girth=0.98)


def neutral_pose():
    P = base_pose(height=0.80, build=0.88)
    h = P['height']
    P['head_pitch'] = np.radians(2)
    P['head_yaw'] = np.radians(-14)
    # lens arm out in front, free hand clutching the apron strap
    rig.place_arm(P, 'r', v3(-0.20, 1.12 * h + 0.06, 0.34), (-1, -0.5, -0.2), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(-0.30, 0.15, 0.95))
    rig.place_arm(P, 'l', v3(0.12, 1.00 * h, 0.12), (1, -0.4, -0.5), l1=0.27 * h, l2=0.26 * h)
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    h, b = P['height'], P['build']
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    # knit cap pushed back on the head
    H, R = P['head'], head_R(P)
    add(Ellipsoid(H + R @ v3(0, 0.078, -0.045) * h, (0.080 * h, 0.040 * h, 0.075 * h), R @ rot_x(-0.35)), 'knit', 0.01)
    add(Torus(H + R @ v3(0, 0.060, -0.02) * h, R @ v3(0, 1, 0.5), 0.078 * h, 0.012), 'knit', 0.0)
    # dust apron: curved shell with a bib, to the knee
    a_top, a_bot = ch + v3(0, 0.09, 0.095), pel + v3(0, -0.36 * h, 0.15 + 0.03 * P['skirt_sway'])
    ab_c, ab_h = (a_top + a_bot) / 2, np.linalg.norm(a_top - a_bot) / 2
    Ra = basis_from(a_top - a_bot, (0, 0, 1))

    def apron_f(p, c=ab_c, R=Ra, hh=ab_h):
        q = (p - c) @ R
        t = np.clip((q[:, 1] + hh) / (2 * hh), 0, 1)
        w = 0.075 + 0.075 * (1 - t) ** 1.2
        bow = 0.05 * (q[:, 0] / 0.13) ** 2
        dz = np.abs(q[:, 2] + bow) - 0.008
        dx = np.abs(q[:, 0]) - w
        dy = np.abs(q[:, 1]) - hh
        return np.maximum(np.maximum(dz, dx), dy) - 0.004
    add(Func(apron_f, ab_c, ab_h + 0.2), 'apron')
    add(Capsule(a_top + v3(-0.07, 0, -0.01), nk + v3(0, 0.0, -0.03), 0.007), 'leather')
    add(Capsule(a_top + v3(0.07, 0, -0.01), nk + v3(0, 0.0, -0.03), 0.007), 'leather')
    # apron pocket with spare lens glass poking out
    pc = pel + v3(0.0, -0.10 * h, 0.17)
    add(RoundBox(pc, (0.06, 0.04, 0.010), 0.006, rot_x(0.12)), 'apron_dk')
    for k in range(3):
        add(Ellipsoid(pc + v3(-0.03 + 0.03 * k, 0.05, 0.0), (0.012, 0.022, 0.004), rot_z(0.3 * (k - 1))), 'lens')
    # the cracked lens
    g = hand_pos(P, 'r')
    d = norm(P['item_r']) if P['item_r'] is not None else v3(0, 0, 1)
    lc = g + d * 0.07
    add(Capsule(g - d * 0.03, lc, 0.010), 'wood')
    cracked_lens(add, lc + d * 0.06 + v3(0, 0.02, 0), norm(v3(-0.50, 0.30, 0.82)) * 0.6 + d * 0.4, 0.125, rim='brass')
    glow = max(P['cast_glow'], P['fx'])
    sp = lc + d * 0.12 + v3(-0.02, 0.03, 0.0)
    if glow > 0.05:
        add(Sphere(sp, 0.012 + 0.03 * glow), 'flash')
    light_at(lights, P, sp + d * 0.05, 0.35 + 2.4 * glow, 0.16, color=_hex('#fff2c0'))
    if P['fx'] > 0:
        add(Capsule(sp, sp + d * (0.1 + 1.0 * P['fx']), 0.022 * P['fx'] + 0.004, 0.006), 'beam')
    mats = keeper_mats(P, hair=_hex('#6a3f2c'), skin=_hex('#d1a07c'), coat=_hex('#a9b4ba'))
    mats['apron'] = Material(dust_albedo(_hex('#8a8272'), density=0.10), spec=0.25, gloss=20, brush=0.06)
    mats['apron_dk'] = Material(noisy(_hex('#4e4338'), 0.1), spec=0.15, gloss=14, brush=0.06)
    mats['knit'] = Material(noisy(_hex('#4f6e70'), 0.14, 40.0), spec=0.02, brush=0.1)
    mats['crack'] = Material(_hex('#2a2a2e'), spec=0.0, brush=0.0)
    mats['lens'] = Material(LENS, spec=1.4, gloss=90, emissive=tuple(np.array(LENS) * (0.10 + 0.9 * glow)), rim=0.8, brush=0.0)
    return finish(P, FACTION, parts, mats, lights=lights)


def _post(fr):
    for i, (P, o) in enumerate(fr['attack']):
        P['fx'] = [0, 0, 1, 0.2][i]
    return fr


ROWS, frames = keeper_rows(neutral_pose, attack_style='shoot', weapon_side='r', cast_side='l', post=_post, pole=None)

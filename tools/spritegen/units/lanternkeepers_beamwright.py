"""Beamwright (Lanternkeepers ranged line damage). Trims a lens until the light is a blade.

Goggles, oilskin apron-coat over sea grey, a long brass-and-iron beam tube carried upright like
a lighthouse in miniature, lens glowing at the top. Defining detail: on the hit frame it levels
the tube and a perfectly straight gold beam leaves the lens.
"""
import numpy as np
from _lanternkeepers_common import *

UNIT_ID = 'lanternkeepers_beamwright'
FACTION = 'lanternkeepers'
LOOK = LOOKS[FACTION]

C = Costume(top='coatgrey', sleeve='coatgrey', legs='slate', boot='boot', hand='glove', skirt='coat',
            skirt_mat='oilskin', hem=0.32, flare=0.6, head='hair', hair='hair', hair_style='tail',
            belt='leather', girth=0.95)


def neutral_pose():
    P = base_pose(height=1.02, build=0.95)
    h = P['height']
    rig.place_arm(P, 'r', v3(-0.31, 0.98, 0.14), (-1, -0.4, -0.5), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(-0.16, 1.0, 0.06))
    rig.place_arm(P, 'l', v3(-0.27, 1.24, 0.14), (1, -0.4, -0.5), l1=0.27 * h, l2=0.26 * h)
    return P


def beam_tube(add, lights, P):
    d = P['item_r']
    if d is None:
        return
    d = norm(d)
    g = hand_pos(P, 'r')
    a, b = g - d * 0.22, g + d * 0.80
    add(Cylinder(a, b, 0.055, 0.010), 'tube')
    for t in (0.1, 0.45, 0.8):
        add(Torus(a + (b - a) * t, d, 0.052, 0.007), 'brass')
    # lamp housing at the back with a chimney
    side = norm(np.cross(d, v3(0, 0, 1)) if abs(d[2]) < 0.9 else v3(1, 0, 0))
    hc = a + d * 0.10
    add(RoundBox(hc, (0.07, 0.07, 0.07), 0.012, basis_from(d, (0, 0, 1))), 'brass')
    add(Cylinder(hc + side * 0.06, hc + side * 0.12, 0.018, 0.005), 'darkiron')
    light_at(lights, P, hc + v3(0, 0, 0.08), 0.9, 0.12)
    # lens at the mouth
    lens_disc(add, b + d * 0.005, d, 0.050, rim='brass', thick=0.014)
    add(Cylinder(b - d * 0.01, b + d * 0.02, 0.060, 0.006), 'brass')
    light_at(lights, P, b + d * 0.06, 1.6, 0.18)
    fx = P['fx']
    if fx > 0:
        add(Capsule(b + d * 0.03, b + d * (0.03 + 1.6 * fx), 0.020 * fx + 0.004, 0.012 * fx + 0.003), 'beam')
        light_at(lights, P, b + d * 0.4, 3.0 * fx, 0.3, color=_hex('#ffd27a'))
    # grip for the left hand
    add(Capsule(g + d * 0.22 + side * 0.0, g + d * 0.22 - v3(0, 0.0, 0) + side * 0.05, 0.010), 'darkiron')


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    goggles(add, P, up=0.055)
    beam_tube(add, lights, P)
    # spare lens case on the hip
    pel = P['pelvis']
    add(Cylinder(pel + v3(0.15, 0.0, 0.02), pel + v3(0.15, 0.10, 0.02), 0.04, 0.008), 'leather')
    mats = keeper_mats(P, hair=_hex('#2e2a28'), skin=W['skin_mid'])
    mats['lens'] = Material(LENS, spec=1.4, gloss=90, emissive=tuple(np.array(_hex('#ffe8b0')) * min(1.0, 0.75 * P['glow'] + P['fx'])), rim=0.6, brush=0.0)
    mats['tube'] = Material(noisy(_hex('#59606a'), 0.08), spec=0.7, gloss=34, metal=0.6, brush=0.05)
    return finish(P, FACTION, parts, mats, lights=lights)


def _post(fr):
    # second hand steadies the tube on the attack (level aim)
    for i, (P, o) in enumerate(fr['attack']):
        if P['item_r'] is not None:
            d = norm(P['item_r'])
            P['item_r'] = norm(v3(d[0], d[1] * 0.3, d[2]))
    return fr


ROWS, frames = keeper_rows(neutral_pose, attack_style='shoot', weapon_side='r', cast_side='l', post=_post)

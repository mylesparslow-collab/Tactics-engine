"""Wren Halloway, the Rimfall Thief (Gyre hero, flying). A lean young woman on a frigatebird with its red throat
pouch inflated, wings wide, short oilskin jacket, beak-orange scarf, a stolen Lanternkeeper lens at her hip
(thin gold rim) and a Concord ledger in her coat, grinning over her shoulder as she banks away."""
from _gyre_common import *

UNIT_ID = 'gyre_wren_halloway'
LOOK = LOOK_AIR
CAMERA = Camera(ppm=46)
S = species('frigate', bend=-0.20, dihedral=0.30, half=0.95)


def hands(P, Q, S):
    h = 0.78
    sh = Q['sh_r']
    rig.place_arm(Q, 'r', sh + v3(-0.12, 0.02, 0.30), (-1, -0.2, -0.3), l1=0.27 * h, l2=0.26 * h)


R = rider_cfg(h=0.78, b=0.86, lean=0.60, head='scarf', hair=hx('#7a3b22'), skin=hx('#d3a07e'), hands=hands,
              tail_len=0.30, mats=dict(coat=hx('#7d7566'), lips=hx('#b2564a')))
R['look'] = 0.0


def neutral_pose():
    return fly_pose(fl=0.35, roll=0.26, pitch=0.05, neckx=0.2, pouch=1.0, look=-0.85)


def extra(c):
    W, add, F, P = c['W'], c['add'], c['F'], c['P']
    pel = W['pelvis']
    side = F.R @ v3(-1, 0, 0)
    # the stolen lens at the hip: glass disc, thin gold rim
    lc = pel + side * 0.14 + F.R @ v3(0, -0.10, 0.02)
    ax = norm(side + F.R @ v3(0, 0, 0.6))
    add(Cylinder(lc - ax * 0.012, lc + ax * 0.012, 0.062, 0.006), 'glass', 0.0)
    add(Torus(lc, ax, 0.064, 0.007), 'gold', 0.0)
    add(Capsule(pel + side * 0.05, lc, 0.008, 0.008), 'tar', 0.0)
    # Concord ledger tucked into the coat at the chest
    ch = W['chest']
    add(RoundBox(ch + F.R @ v3(0.07, 0.02, 0.10), (0.032, 0.045, 0.014), 0.006, F.R), 'bone', 0.0)
    return [Light(lc, hx('#9fe0d4'), 0.35, 0.4)]


def build(P):
    return flier_build(P, S, R, extra, y0=0.55)


ROWS, frames = fly_rows(neutral_pose, idle_amp=0.60)

"""Lamplit Sailor (Lanternkeepers summon). A drowned sailor the beam revealed and the lamp bound.

Tall wavering pale outline, half see-through, long sea-coat fading out below the knee, watch cap,
boathook held upright. Defining detail: a small hand lamp chained to its left wrist (bound to the
lamp), the only solid, warm thing about it.
"""
import numpy as np
from _lanternkeepers_common import *

UNIT_ID = 'lanternkeepers_lamplit_sailor'
FACTION = 'lanternkeepers'
LOOK = dataclasses.replace(LOOKS[FACTION], rim_int=1.3)
CAM = Camera()

C = Costume(top='ghost', sleeve='ghost', legs='ghost_dk', boot='ghost_dk', hand='ghost_skin', skin='ghost_skin',
            hair='ghost_dk', skirt='coat', skirt_mat='ghost', hem=0.16, flare=0.75, head='cap', head_mat='ghost_dk',
            belt='ghost_dk', girth=0.9)


def neutral_pose():
    P = base_pose(height=1.06, build=0.9)
    h = P['height']
    rig.lean(P, fwd=np.radians(8))
    P['head_pitch'] = np.radians(10)
    rig.place_arm(P, 'r', v3(-0.27, 1.05, 0.14), (-1, -0.3, -0.6), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(0.02, 1.0, 0.04))
    rig.place_arm(P, 'l', v3(0.24, 0.98, 0.10), (1, -0.2, -0.6), l1=0.27 * h, l2=0.26 * h)
    return P


def make_coverage(P):
    # solid-ish at the head and shoulders, thinning toward the hem; fades away in death
    fade = 1.0 - 0.8 * P['end']

    def cov(p):
        return np.clip(0.30 + 0.42 * (p[:, 1] - 0.25) / 1.3, 0.12, 0.78) * fade
    return cov


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    held(P, add, 'r', 'hook', shaft='ghost_lt', head='ghost_lt', below=0.85, above=1.0)
    ghost = ghost_body(parts, CAM, P, make_coverage(P), amp=0.025)
    parts[:] = []
    # the chained hand lamp: solid and warm
    g = hand_pos(P, 'l')
    lc = g + v3(0.02, -0.21, 0.04)
    for k in range(4):
        a = g + (lc + v3(0, 0.1, 0) - g) * (k / 4)
        add(Torus(a, v3(1, 0, 0) if k % 2 else v3(0, 0, 1), 0.012, 0.0035), 'darkiron')
    box_lamp(add, lights, P, lc, size=1.25, frame='darkiron', light=2.0)
    parts[:] = ghost + parts
    mats = keeper_mats(P)
    mats.update(ghost_mats(P))
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = keeper_rows(neutral_pose, attack_style='thrust', weapon_side='r', cast_side='l', pole='r')

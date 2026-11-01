"""Captain Hollis Drenn, First of the Drowned Watch (Lanternkeepers hero, ghost).

Big and broad, a ship's captain's long coat and a bicorne, heavy beard, a great boathook. He
is Lamplit: pale, wavering and partly see-through, more solid than the sailors he commands.
Defining detail: a heavy chain from his belt to a solid ship's lantern he carries in his left
hand, the only warm thing about him, the lamp he is bound to.
"""
import numpy as np
from _lanternkeepers_common import *

UNIT_ID = 'lanternkeepers_captain_hollis_drenn'
FACTION = 'lanternkeepers'
LOOK = dataclasses.replace(LOOKS[FACTION], rim_int=1.25)
CAM = Camera()

C = Costume(top='ghost', sleeve='ghost', legs='ghost_dk', boot='ghost_dk', hand='ghost_skin', skin='ghost_skin',
            hair='ghost_dk', skirt='coat', skirt_mat='ghost', hem=0.18, flare=0.85, head='bald', belt='ghost_dk',
            girth=1.25)


def neutral_pose():
    P = base_pose(height=1.08, build=1.18)
    h = P['height']
    P['head_pitch'] = np.radians(-4)
    rig.place_arm(P, 'r', v3(-0.33, 1.10, 0.14), (-1, -0.3, -0.6), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(-0.06, 1.0, 0.05))
    rig.place_arm(P, 'l', v3(0.30, 1.02, 0.16), (1, -0.2, -0.6), l1=0.27 * h, l2=0.26 * h)
    return P


def make_coverage(P):
    fade = 1.0 - 0.8 * P['end']

    def cov(p):
        return np.clip(0.42 + 0.45 * (p[:, 1] - 0.25) / 1.3, 0.18, 0.9) * fade
    return cov


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    H, R, h = P['head'], head_R(P), P['height']
    # beard and bicorne
    add(Ellipsoid(H + R @ v3(0, -0.07, 0.04) * h, (0.07 * h, 0.07 * h, 0.06 * h), R), 'ghost_lt', 0.02)
    hat_c = H + R @ v3(0, 0.08, -0.01) * h
    add(Ellipsoid(hat_c, (0.20 * h, 0.06 * h, 0.07 * h), R), 'ghost_dk', 0.01)
    add(Ellipsoid(hat_c + R @ v3(0, 0.02, 0) * h, (0.09 * h, 0.06 * h, 0.08 * h), R), 'ghost_dk', 0.0)
    # coat lapels and cuffs
    pel, nk = P['pelvis'], P['neck']
    for sx in (-1, 1):
        add(Capsule(nk + v3(sx * 0.06, -0.06, 0.10), pel + v3(sx * 0.03, 0.12, 0.12), 0.02, 0.012), 'ghost_lt')
    mantle(add, P, 'ghost_dk', depth=0.15, width=0.20)
    held(P, add, 'r', 'hook', shaft='ghost_lt', head='ghost_lt', below=1.0, above=1.0)
    ghost = ghost_body(parts, CAM, P, make_coverage(P), amp=0.02)
    parts[:] = []
    # solid: belt chain to the ship's lantern in his left hand
    g = hand_pos(P, 'l')
    lc = g - v3(0, 0.16, 0)
    belt = pel + v3(0.10, 0.07, 0.11)
    for k in range(6):
        t = k / 5
        a = belt * (1 - t) + (lc - v3(0, 0.07, 0)) * t - v3(0, 0.06 * np.sin(np.pi * t), 0)
        add(Torus(a, v3(1, 0, 0) if k % 2 else v3(0, 0, 1), 0.013, 0.004), 'darkiron')
    add(Capsule(g, g - v3(0, 0.04, 0), 0.005), 'darkiron')
    hurricane(add, lights, P, lc, size=1.45, frame='darkiron', light=2.4)
    parts[:] = ghost + parts
    mats = keeper_mats(P)
    mats.update(ghost_mats(P, pale=_hex('#bfc8cc'), glow=0.4))
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = keeper_rows(neutral_pose, attack_style='swing', weapon_side='r', cast_side='l', pole='r')

"""Silt-Slider (Slough rare, mobile duelist). Long and glossy, reared low (1.8 m) and leaning far forward like a
sledder, the coil stretched out behind into a long flat S ending in a chartreuse-banded paddle. A hooked sabre in
each hand, both swept back along the body. Deep glossy black with thin bone bands, gold belly.
Defining detail: the long flat body and the two swept-back sabres."""
from _slough_common import *

UNIT_ID = 'slough_silt_slider'
N = Naga(height=1.8, girth=0.86, tube=0.135, coil_r=0.64, loops=1.3, coil_depth=0.42, coil_back=0.36,
         hood='flat', hood_w=1.1, lean=0.34, accent=('tail',), band_len=0.2, band_dark=0.80, gloss=1.9,
         pattern='edged', hood_mark='bars', trim=BRONZE,
         dark=_hex('#141c28'), light=_hex('#d4dcd2'), belly=_hex('#e0b440'), mantle=_hex('#141c28'),
         hood_face=_hex('#4a5666'), hood_rim=_hex('#e6ecdf'), lip=_hex('#e6ecdf'), skin=_hex('#3c4656'),
         paddle=1.5, fang=1.1, head_len=1.4,
         tail_side=1)
CAMERA = naga_camera(N)


def neutral_pose():
    P = naga_pose(N)
    s = P['s']
    reach(P, 'r', scr(-0.36, 1.00 * s, 0.30))
    reach(P, 'l', scr(0.38, 1.12 * s, -0.20))
    aim(P, 'r', sdir(-0.55, 0.30, -0.65))
    aim(P, 'l', sdir(-0.55, 0.25, -0.50))
    return P


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    blade(add, P, 'r', 'sabre', length=0.52, below=0.10)
    blade(add, P, 'l', 'sabre', length=0.52, below=0.10)
    return naga_finish(P, N, parts)


def _both(row, i, P):
    """The left sabre follows the right in the attack so both are seen cutting."""
    if row == 'attack' and 'item_l' in P and P['item_l'] is not None:
        R = {0: rot_x(-1.2), 1: rot_x(-0.7), 2: rot_x(0.25), 3: rot_x(0.1)}[i]
        sh = P['sh_l']
        P['hd_l'] = sh + R @ (P['hd_l'] - sh)
        P['item_l'] = R @ P['item_l']
    if row == 'attack':      # the flat hood rides ahead of the cut: keep it inside the frame
        P['hood'] = min(P['hood'], 1.0)
        P['head'] = P['head'] - E1 * [0, 0.06, 0.14, 0.08][i] * P['s']


ROWS, frames = naga_rows(neutral_pose, attack='swing', hook=_both)

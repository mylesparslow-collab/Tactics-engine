"""Hundredcoat (Slough exotic, four-armed long giant). Rears to the top of a ppm-44 frame; the torso and the top
of the coil covered in overlapping layers of lacquered amber shed skin like roof tiles, edges lighter. Upper
arms raise two fang-glaives out to the sides, lower arms hold two more low and forward; chartreuse glaze on all
four blades. Bone bands only show on the coil. Defining detail: the shingled amber skin-armour."""
from _slough_common import *

UNIT_ID = 'slough_hundredcoat'
N = Naga(height=2.6, arms=4, girth=1.30, tube=0.21, coil_r=0.56, loops=1.75, coil_back=0.27, hood='broad',
         hood_w=1.05, band_len=0.30, accent=(), body_r=0.19, head_len=1.15,
         skin=_hex('#6a5a44'), belly=_hex('#8a6a3a'))
CAMERA = naga_camera(N)


def neutral_pose():
    P = naga_pose(N)
    s = P['s']
    reach(P, 'r', scr(-0.54, 1.62, 0.12))
    reach(P, 'l', scr(0.52, 1.64, -0.05))
    aim(P, 'r', sdir(-0.24, 1.0, 0.05))
    aim(P, 'l', sdir(0.24, 1.0, -0.05))
    reach(P, 'r2', scr(-0.62, 1.18, 0.30))
    reach(P, 'l2', scr(0.64, 1.16, 0.0))
    aim(P, 'r2', sdir(-0.30, -0.70, 0.55))
    aim(P, 'l2', sdir(0.35, -0.75, 0.45))
    return P


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    lacquer_coat(add, P, B, N, rows=4, per_row=5, coil=True)
    for sd, L, bl in (('r', 0.80, 0.30), ('l', 0.80, 0.30), ('r2', 0.62, 0.22), ('l2', 0.62, 0.22)):
        blade(add, P, sd, 'glaive', length=L, below=bl)
    return naga_finish(P, N, parts)


ROWS, frames = naga_rows(neutral_pose, attack='quad')

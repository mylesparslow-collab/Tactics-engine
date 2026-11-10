"""Hundredcoat (Slough exotic, four-armed long giant). Rears to the top of a ppm-44 frame; the torso and the top
of the coil covered in overlapping layers of lacquered amber shed skin like roof tiles, edges lighter. Upper
arms raise two fang-glaives out to the sides, lower arms hold two more low and forward; chartreuse glaze on all
four blades. Bone bands only show on the coil. Defining detail: the shingled amber skin-armour."""
from _slough_common import *

UNIT_ID = 'slough_hundredcoat'
N = Naga(height=2.6, arms=4, girth=1.30, tube=0.21, coil_r=0.56, loops=1.75, coil_back=0.27, hood='broad',
         hood_w=1.08, hood_h=0.86, band_len=0.30, accent=(), body_r=0.19, head_len=1.15,
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


def _fit(row, i, P):
    """Giant in a ppm-44 frame: keep the raised glaives under the top edge and the coil off the bottom."""
    s = P['s']
    if row == 'cast':            # spread the upper arms out instead of up
        up = [0.12, 0.28, 0.10][i] * s
        P['hd_r'] = P['hd_r'] + v3(0, -up, 0) + E1 * -0.06 * (i == 1)
        P['hd_l'] = P['hd_l'] + v3(0, -up, 0) + E1 * 0.06 * (i == 1)
        P['hd_r2'] = P['hd_r2'] + v3(0, -up * 0.5, 0)
        P['hd_l2'] = P['hd_l2'] + v3(0, -up * 0.5, 0)
    if row == 'cast':
        slide(P, v3(0, -[0.03, 0.06, 0.0][i] * s, 0))
        bend(P, fwd=np.radians([3, 7, 0][i]))
        P['hood'] = min(P['hood'], 1.25)
    if row == 'attack' and i == 0:
        move_hands(P, v3(0, -0.10 * s, 0), ('r', 'l'))
    P['coil_sq'] = max(P['coil_sq'], 0.95)
    P['coil_w'] = min(P['coil_w'], 1.0)


ROWS, frames = naga_rows(neutral_pose, attack='quad', hook=_fit)

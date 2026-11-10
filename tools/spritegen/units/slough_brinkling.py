"""Brinkling (Slough common, cheap body). A thin young krait-folk a few sheddings old, reared to the height of a
man (head at 1.9 m) on a narrow two-loop coil it has not grown into, a little unsteady. A reed gaff held in both
hands like a boat-pole; on the left forearm a buckler cut from its own first skin, pale and still translucent,
stretched on a reed hoop. Defining detail: the buckler. Chartreuse band at the neck. Bites head-first."""
from _slough_common import *

UNIT_ID = 'slough_brinkling'
N = Naga(height=1.9, girth=0.74, tube=0.12, coil_r=0.40, loops=1.5, coil_back=0.18, hood='narrow', hood_w=1.1,
         accent=('neck',), arm_len=0.95, lean=-0.06, band_len=0.20, band_dark=0.36, fang=1.1,
         belly=_hex('#e8cf7c'), skin=_hex('#7a6638'), hood_face=_hex('#8a7a52'))   # young: paler, more bone than black
CAMERA = naga_camera(N)


def neutral_pose():
    P = naga_pose(N)
    s = P['s']
    hold_pole(P, 'r', 'l', grip=v3(-0.34, 0.95, 0.22) * v3(1, s, 1), direction=v3(0.40, 0.84, 0.36), spacing=0.36)
    return P


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    pole(add, P, 'r', 'l', 'gaff', below=0.55, above=0.62)
    buckler(add, P, 'l', size=1.0)
    return naga_finish(P, N, parts)


ROWS, frames = naga_rows(neutral_pose, attack='bite')

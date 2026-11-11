"""Reedrunner (Slough common, skirmisher). Slim and long, reared only to 1.9 m and leaning hard forward, the coil
pulled out into a long low trailing S with a big paddle tail, as if caught mid-slide. A hook-knife held forward
in the right hand, the left swept back; a rolled message-skin tied across the chest with chartreuse cord.
Yellow lip and chin, narrow pale hood. Defining detail: the forward lean and the long trailing tail."""
from _slough_common import *

UNIT_ID = 'slough_reedrunner'
YEL = _hex('#e8c24a')
N = Naga(height=1.9, girth=0.78, tube=0.125, coil_r=0.72, loops=1.3, coil_depth=0.36, coil_back=0.30,
         hood='narrow', hood_w=1.2, hood_h=1.1, lean=0.22, accent=(), band_len=0.16, band_dark=0.40, paddle=1.6,
         pattern='rings', band_grow=0.6, hood_mark='stripe', hood_mark_col=YEL,
         dark=_hex('#1c2a38'), light=_hex('#a8c2cc'), belly=_hex('#e2d9a6'), mantle=_hex('#18222c'),
         lip=YEL, hood_face=_hex('#4e6a7a'), hood_rim=YEL, skin=_hex('#4a6270'), fang=1.15, arm_len=1.05,
         head_len=1.45)
CAMERA = naga_camera(N)


def neutral_pose():
    P = naga_pose(N)
    s = P['s']
    reach(P, 'r', scr(0.18, 1.36 * s, 0.46))
    aim(P, 'r', sdir(0.85, 0.38, 0.28))
    reach(P, 'l', scr(-0.42, 1.10 * s, -0.35))
    return P


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    blade(add, P, 'r', 'sabre', length=0.60, below=0.10)
    # rolled message-skin across the chest, tied with chartreuse cord
    s = P['s']
    Rt = B['chest_R']
    C = P['chest']
    rt, up, fw = Rt[:, 0], Rt[:, 1], Rt[:, 2]
    a = C + rt * 0.20 * s + up * 0.14 * s + fw * 0.10 * s
    b = C - rt * 0.20 * s - up * 0.12 * s + fw * 0.10 * s
    add(Capsule(a, b, 0.052 * s), 'reed', 0.0)
    for t in (0.18, 0.5, 0.82):
        q = lerp(a, b, t)
        add(Sphere(q, 0.060 * s), 'glaze', 0.0)
    return naga_finish(P, N, parts)


def _fit(row, i, P):
    if row == 'attack':
        h = [scr(-0.12, 1.45, 0.25), scr(0.05, 1.50, 0.32), scr(0.12, 1.22, 0.62), scr(0.15, 1.32, 0.50)][i]
        d = [sdir(0.25, 0.80, -0.1), sdir(0.70, 0.60, 0.0), sdir(0.95, -0.12, 0.35), sdir(0.85, 0.20, 0.3)][i]
        P['hd_r'] = h
        P['item_r'] = d


ROWS, frames = naga_rows(neutral_pose, attack='swing', hook=_fit)

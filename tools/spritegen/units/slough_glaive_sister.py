"""Glaive-Sister (Slough uncommon, duellist). Lean and very upright, reared to 2.2 m on a tidy tight coil. A long
fang-glaive held in a formal two-handed guard slanting across the body, a lacquered amber skin sash crossing the
chest, a chartreuse band at the waist. High-contrast crisp black-and-bone. Defining detail: the formal upright
guard and the long glaive."""
from _slough_common import *

UNIT_ID = 'slough_glaive_sister'
N = Naga(**dict(SKINS['krait'], hood_face=_hex('#9a978a')), height=2.2, girth=0.86, tube=0.135, coil_r=0.42, coil_back=0.32, loops=1.7, hood='spade',
         hood_w=0.95, hood_h=1.1, hood_mark='chevron', hood_mark_col=CHART, pattern='checker',
         accent=('neck',), band_len=0.26, band_dark=0.5, head_len=1.25, tail_side=1, lean=-0.03, bracer=_hex('#d6a35e'))
CAMERA = naga_camera(N)


def neutral_pose():
    P = naga_pose(N)
    s = P['s']
    hold_pole(P, 'r', 'l', grip=scr(-0.40, 1.00, 0.30), direction=sdir(0.62, 0.78, 0.0), spacing=0.46)
    return P


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    s = P['s']
    pole(add, P, 'r', 'l', 'glaive', below=0.40, above=0.92)
    # amber lacquered sash across the chest, shoulder to hip
    Rt = B['chest_R']
    rt, up, fw = Rt[:, 0], Rt[:, 1], Rt[:, 2]
    C = P['chest']
    a = C + (rt * 0.17 + up * 0.15 + fw * 0.03) * s
    b = P['waist'] + (-rt * 0.14 + up * 0.04 + fw * 0.03) * s
    add(Capsule(a, b, 0.052 * s, 0.05 * s), 'lacquer', 0.0)
    add(Capsule(a + fw * 0.012 * s, b + fw * 0.012 * s, 0.020 * s), 'lacquer_lt', 0.0)
    return naga_finish(P, N, parts)


def _fit(row, i, P):
    if row == 'attack':
        g, dr = [(scr(-0.46, 0.95, 0.26), sdir(0.40, 0.90, 0.0)),
                 (scr(-0.44, 1.00, 0.28), sdir(0.55, 0.80, 0.1)),
                 (scr(-0.42, 1.08, 0.50), sdir(0.72, -0.05, 0.55)),
                 (scr(-0.34, 1.02, 0.36), sdir(0.70, 0.55, 0.2))][i]
        P['hd_r'] = g
        P['hd_l'] = g + dr * 0.46


ROWS, frames = naga_rows(neutral_pose, attack='thrust', hook=_fit)

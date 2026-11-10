"""Siltcoil Ambusher (Slough uncommon, ambusher). Mud-coloured marsh olive and silt grey, reared only to 1.6 m,
the rest sunk in a low wide coil half buried under a flat silt mound, hunched. A fang-glaive stands straight up
out of the coil beside the head like a reed, its blade tip well above the hood, chartreuse glaze on the tip.
Very faint bands, gold eyes. Defining detail: the low hunched ambush pose with the glaive standing up."""
from _slough_common import *

UNIT_ID = 'slough_siltcoil'
MUD = _hex('#6a6a40')
N = Naga(height=1.6, girth=1.15, tube=0.17, coil_r=0.66, loops=1.9, coil_depth=0.78, coil_back=0.20,
         hood='broad', hood_w=1.2, hood_h=1.1, lean=0.22, dark=_hex('#464a2c'), light=_hex('#8a8764'), band_fade=0.8,
         band_len=0.30, accent=(), skin=_hex('#6e7040'), belly=_hex('#a89a58'), mantle=_hex('#3c4026'),
         hood_face=_hex('#a9a672'), hood_rim=_hex('#c9c498'), lip=_hex('#c9b870'), head_len=1.55, fang=1.2,
         eye=_hex('#ffd23a'), tail_side=-1)
CAMERA = naga_camera(N)


def neutral_pose():
    P = naga_pose(N)
    s = P['s']
    hold_pole(P, 'r', 'l', grip=scr(-0.36, 0.95, 0.20), direction=sdir(0.08, 1.0, 0.0), spacing=0.36)
    return P


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    s = P['s']
    pole(add, P, 'r', 'l', 'glaive', below=0.40, above=0.70)
    # flat silt mound over the lower coil, with a ragged lip
    c = P['coil_c'] + v3(0, -0.02, 0) + E2 * 0.0
    k = 1.0 - 0.9 * P['flat']
    add(Ellipsoid(c + v3(0, 0.0, 0.0), (0.74, 0.11 * k, 0.60), np.eye(3)), 'silt', 0.05)
    add(Ellipsoid(c + E1 * 0.55 + E2 * 0.28, (0.26, 0.07 * k, 0.20), np.eye(3)), 'silt', 0.05)
    add(Ellipsoid(c - E1 * 0.50 + E2 * 0.35, (0.24, 0.07 * k, 0.18), np.eye(3)), 'silt', 0.05)
    mats = {'silt': Material(lambda p, n: _arr(_hex('#6e6a4c'), len(p)) * (0.86 + 0.26 * fbm(p, 7.0, 3)[:, None]),
                             spec=0.05, gloss=8, brush=0.1)}
    return naga_finish(P, N, parts, mats)


def _fit(row, i, P):
    P['coil_sq'] = min(P['coil_sq'], 0.80)
    if row == 'attack':
        # the glaive tips over forward in a strike and comes back up
        ang = [-0.05, 0.10, 1.10, 0.45][i]
        d = sdir(np.sin(ang), np.cos(ang), 0.25 * np.sin(ang))
        P['hd_r'] = scr(-0.36, 0.95, 0.20)
        P['hd_l'] = P['hd_r'] + d * 0.36
        if i == 2:
            P['hd_r'] = P['hd_r'] + sdir(0.5, 0, 0.1) * 0.12
            P['hd_l'] = P['hd_r'] + d * 0.36


ROWS, frames = naga_rows(neutral_pose, attack='thrust', hook=_fit)

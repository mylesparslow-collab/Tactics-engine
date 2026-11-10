"""Scaleshield (Slough common, tank). A heavy, thick-bodied krait (body radius 0.2 m) reared to 2.0 m but wide,
behind one huge leviathan scale held in front with both hands: a curved grey-green plate 1.2 m tall with three
ridges and a lacquer-amber rim, covering most of the torso. Band black dominant. Defining detail: the scale."""
from _slough_common import *

UNIT_ID = 'slough_scaleshield'
N = Naga(palette='krait', hood_face=_hex('#8f8a78'), skin=_hex('#4a4a44'),
         height=2.0, girth=1.40, tube=0.215, coil_r=0.52, loops=1.6, coil_depth=0.64, coil_back=0.30,
         hood='broad', hood_w=1.0, hood_h=0.9, hood_mark='chevron', band_dark=0.68, band_len=0.36, pattern='edged',
         accent=('tail',), body_r=0.18, tail_side=-1, shoulders=1.12, head_w=1.15, lean=0.05)
CAMERA = naga_camera(N)


def neutral_pose():
    P = naga_pose(N, v_shield=norm(v3(-0.30, 0.10, 1.0)))
    s = P['s']
    reach(P, 'r', v3(-0.38, 0.94 * s, 0.30))
    reach(P, 'l', v3(0.24, 0.98 * s, 0.36))
    return P


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    s = P['s']
    nz = norm(P['v_shield'])
    c = (P['hd_r'] + P['hd_l']) / 2 + nz * 0.07 * s + v3(0, 0.06, 0) * s
    up = norm(v3(0, 1, 0) - nz * nz[1])
    if P['drop'] > 0:      # death: the scale falls flat in front of the coil
        k = min(1.0, P['drop'] * 2.5)
        c = lerp(c, scr(0.02, 0.10, -0.50), k)
        nz = norm(lerp(nz, v3(0, 1, 0.05), k))
        up = norm(lerp(up, E1, k))
    scale_shield(add, c, nz, up, w=0.42 * s, h=0.56 * s)
    pauldron(add, P, B, N, 'r', plates=3, size=1.1)
    pauldron(add, P, B, N, 'l', plates=2, size=1.1)
    return naga_finish(P, N, parts)


def _fit(row, i, P):
    """The bash drives the door-sized scale forward: keep its leading edge inside the frame."""
    if row == 'attack':
        move_hands(P, -E1 * 0.07 * P['s'] * (i == 2))


ROWS, frames = naga_rows(neutral_pose, attack='bash', hook=_fit)

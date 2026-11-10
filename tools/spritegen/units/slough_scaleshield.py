"""Scaleshield (Slough common, tank). A heavy, thick-bodied krait (body radius 0.2 m) reared to 2.0 m but wide,
behind one huge leviathan scale held in front with both hands: a curved grey-green plate 1.2 m tall with three
ridges and a lacquer-amber rim, covering most of the torso. Band black dominant. Defining detail: the scale."""
from _slough_common import *

UNIT_ID = 'slough_scaleshield'
N = Naga(height=2.0, girth=1.28, tube=0.20, coil_r=0.50, loops=1.6, coil_depth=0.64, coil_back=0.30,
         hood='broad', hood_w=1.08, band_dark=0.64, band_len=0.30, accent=(), body_r=0.17, tail_side=-1)
CAMERA = naga_camera(N)


def neutral_pose():
    P = naga_pose(N, v_shield=norm(v3(-0.30, 0.10, 1.0)))
    s = P['s']
    reach(P, 'r', v3(-0.36, 1.06 * s, 0.30))
    reach(P, 'l', v3(0.26, 1.10 * s, 0.36))
    return P


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    s = P['s']
    nz = norm(P['v_shield'])
    c = (P['hd_r'] + P['hd_l']) / 2 + nz * 0.07 * s + v3(0, 0.06, 0) * s
    up = norm(v3(0, 1, 0) - nz * nz[1])
    if P['drop'] > 0:      # death: the scale falls flat in front of the coil
        k = P['drop']
        c = lerp(c, v3(-0.10, 0.05, -0.05), k)
        nz = norm(lerp(nz, v3(0, 1, 0.05), k))
        up = norm(lerp(up, norm(v3(0.2, 0, -1)), k))
    scale_shield(add, c, nz, up, w=0.40 * s, h=0.60 * s)
    return naga_finish(P, N, parts)


ROWS, frames = naga_rows(neutral_pose, attack='bash')

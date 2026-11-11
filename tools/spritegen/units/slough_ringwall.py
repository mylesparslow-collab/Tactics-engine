"""Ringwall (Slough rare, long tank). Four-armed giant in a ppm-44 frame on a massive two-loop ring of thick grey
and bone banded coil, torso reared to ~2.7 m. The upper arms each hold a leviathan-scale shield out to the side
like a wall; the lower arms hold short rusted hooked tridents forward. Defining detail: the two shields."""
from _slough_common import *

UNIT_ID = 'slough_ringwall'
N = Naga(height=2.62, arms=4, girth=1.35, tube=0.235, coil_r=0.62, loops=2.0, coil_back=0.38, coil_depth=0.62,
         hood='broad', hood_w=1.0, hood_h=0.95, head_len=1.4, band_len=0.34, band_dark=0.62, accent=(),
         body_r=0.20, dark=_hex('#2c3a2a'), light=_hex('#c6ccae'), skin=_hex('#55604a'), belly=_hex('#a89a4e'),
         mantle=_hex('#22301f'), hood_face=_hex('#5f6e56'), hood_rim=_hex('#e0e4cc'), lip=_hex('#dfe2c8'),
         pattern='edged', hood_mark='chevron', trim=_hex('#5e6f6a'), tail_side=-1)
CAMERA = naga_camera(N)


def neutral_pose():
    P = naga_pose(N, v_sr=norm(sdir(-0.45, 0.0, 1.0)), v_sl=norm(sdir(0.55, 0.0, 0.8)))
    s = P['s']
    reach(P, 'r', scr(-0.50, 1.62, 0.18))
    reach(P, 'l', scr(0.52, 1.64, -0.02))
    reach(P, 'r2', scr(-0.52, 1.10, 0.52))
    reach(P, 'l2', scr(0.50, 1.12, 0.30))
    aim(P, 'r2', sdir(-0.10, 0.10, 1.0))
    aim(P, 'l2', sdir(0.30, 0.10, 0.9))
    return P


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    s = P['s']
    dr = P['drop']
    for sd, key, k in (('r', 'v_sr', 0), ('l', 'v_sl', 1)):
        nz = norm(P[key])
        c = P['hd_' + sd] + nz * 0.07 + v3(0, 0.04, 0)
        up = norm(v3(0, 1, 0) - nz * nz[1])
        if dr > 0:
            kk = min(1.0, dr * 2.5)
            c = lerp(c, scr(-0.30 + 0.62 * k, 0.05, -0.28 - 0.1 * k), kk)
            nz = norm(lerp(nz, v3(0, 1, 0.05), kk))
            up = norm(lerp(up, E1, kk))
        scale_shield(add, c, nz, up, w=0.33, h=0.52, ridges=3, curve=0.10)
    pauldron(add, P, B, N, 'r', plates=2, size=1.3)
    pauldron(add, P, B, N, 'l', plates=2, size=1.3)
    blade(add, P, 'r2', 'trident', length=0.95, below=0.40)
    blade(add, P, 'l2', 'trident', length=0.95, below=0.40)
    return naga_finish(P, N, parts)


def _fit(row, i, P):
    s = P['s']
    P0 = neutral_pose()
    if row == 'attack':          # shields hold the wall and shove; the tridents do the stabbing
        for sd in ('r', 'l'):
            P['hd_' + sd] = P0['hd_' + sd] + v3(0, [-0.02, 0, 0.0, 0.0][i], 0) * s + E2 * [-0.04, 0, 0.08, 0.03][i] - E1 * [0, 0, 0.05, 0.02][i]
        k = [-0.10, 0.0, 0.18, 0.05][i]
        for sd in ('r2', 'l2'):
            P['hd_' + sd] = P0['hd_' + sd] + (E2 - E1 * 0.25) * k
    if row == 'cast':            # shields swing wide, tridents stay low
        for sd, sx in (('r', -1), ('l', 1)):
            P['hd_' + sd] = P0['hd_' + sd] + E1 * sx * [0.02, 0.08, 0.03][i] + v3(0, [0.0, 0.08, 0.0][i], 0) * s
        for sd in ('r2', 'l2'):
            P['hd_' + sd] = P0['hd_' + sd]
        slide(P, v3(0, -[0.03, 0.06, 0.0][i] * s, 0))
        P['hood'] = min(P['hood'], 1.25)
    # the reared giant fills the frame: keep the hood under the top edge when the head snaps back
    if row == 'hit' or (row == 'death' and i == 0) or row == 'cast':
        slide(P, v3(0, -0.07 * s, 0))
    P['hood'] = min(P['hood'], 1.05 if row in ('attack', 'cast', 'hit') else 1.12)
    P['coil_sq'] = max(P['coil_sq'], 0.95)
    P['coil_w'] = min(P['coil_w'], 1.0)


ROWS, frames = naga_rows(neutral_pose, attack='quad', hook=_fit)

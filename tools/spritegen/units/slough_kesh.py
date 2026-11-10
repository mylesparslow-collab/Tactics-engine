"""Kesh, the Four-Handed (Slough hero, four-armed giant, ppm 44). Low, wide and thick-torsoed, a flat wide hood,
a vast crisp black-and-bone coil with a big paddle tail, four hands open as if to catch and a short fang-glaive
loose in each. One bright chartreuse champion band high on the neck. Defining detail: the four open arms."""
from _slough_common import *

UNIT_ID = 'slough_kesh'
N = Naga(palette='krait', trim=LACQUER_RED, hood_face=_hex('#8c8676'), hood_mark_col=_hex('#f1ead0'),
         skin=_hex('#6e6a5e'), dark=_hex('#1c1f21'), light=_hex('#efe8d0'), belly=_hex('#e6b238'),
         height=2.54, arms=4, girth=1.65, tube=0.27, coil_r=0.66, loops=1.8, coil_back=0.38, coil_depth=0.62,
         hood='cobra', hood_w=1.05, hood_h=1.05, hood_mark='chevron', head_len=1.35, head_w=1.2, band_len=0.42,
         band_dark=0.5, accent=('neck',), body_r=0.22, paddle=1.5, lean=0.10, tail_side=-1, shoulders=1.12)
CAMERA = Camera(ppm=44.0)

# (side, hand, glaive direction, glaive length)
ARMS = (('r', scr(-0.44, 1.30, 0.14), sdir(-0.35, 0.9, 0.25), 0.9),
        ('l', scr(0.42, 1.34, -0.04), sdir(0.35, 0.9, -0.05), 0.9),
        ('r2', scr(-0.46, 0.88, 0.50), sdir(-0.32, 0.25, 0.85), 0.85),
        ('l2', scr(0.44, 0.90, 0.30), sdir(0.30, 0.25, 0.80), 0.85))


def neutral_pose():
    P = naga_pose(N)
    for sd, h, d, L in ARMS:
        reach(P, sd, h)
        aim(P, sd, d)
    return P


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    s = P['s']
    pauldron(add, P, B, N, 'r', plates=3, size=1.1)      # red-lacquered champion's shoulder skins
    pauldron(add, P, B, N, 'l', plates=3, size=1.1)
    for sd, h, d, L in ARMS:
        blade(add, P, sd, 'glaive', length=L, below=0.30)
        # open fingers (catching)
        hd = P['hd_' + sd]
        a = norm(hd - P['sh_' + sd])
        sv = _side(a)
        for k in range(3):
            f = k - 1
            add(Capsule(hd + a * 0.03, hd + (a + sv * f * 0.5) * 0.12 * s, 0.020 * s, 0.007), 'hand', 0.0)
    return naga_finish(P, N, parts)


def _fit(row, i, P):
    s = P['s']
    P0 = neutral_pose()
    if row == 'attack':          # the four arms close in on the target: a catch
        k = [-0.5, 0.0, 1.0, 0.45][i]
        for sd, h, d, L in ARMS:
            sx = -1 if sd[0] == 'r' else 1
            P['hd_' + sd] = P0['hd_' + sd] + E1 * sx * (-0.18 * k + (0.06 if k < 0 else 0)) * 1.0 + E2 * (0.26 * k) + v3(0, -0.04 * k, 0)
            fwd = sdir(-0.25 * sx, 0.25, 1.0)
            P['item_' + sd] = norm(lerp(d, fwd, max(k, 0) * 0.9))
        slide(P, v3(0, 0, 0.0))
    if row == 'cast':            # arms flung open wide, glaives up
        for sd, h, d, L in ARMS:
            sx = -1 if sd[0] == 'r' else 1
            kk = [0.3, 1.0, 0.4][i]
            P['hd_' + sd] = P0['hd_' + sd] + E1 * sx * -0.02 * kk + v3(0, 0.06 * kk, 0)
            P['item_' + sd] = norm(lerp(d, sdir(sx * 0.2, 1.0, 0.0), kk * 0.7))
        slide(P, v3(0, -[0.06, 0.12, 0.04][i] * s, 0))
        P['hood'] = min(P['hood'], 1.05)
    P['coil_sq'] = max(P['coil_sq'], 0.95)
    P['coil_w'] = min(P['coil_w'], 1.0)


ROWS, frames = naga_rows(neutral_pose, attack='quad', hook=_fit)

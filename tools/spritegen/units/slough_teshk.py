"""Teshk, Who Bites Last (Slough hero). Lean slate-grey-and-bone duellist, 2.2 m, one tight loop of coil, an
unscarred glossy hide, a curved fang-sabre in the right hand (chartreuse tip, thin gold line along the fang), the
left hand empty and held behind the back. Spade-shaped hood with a gold rim, an amber lacquered shoulder-guard and
sash. Defining detail: the economical one-handed stance and the clean glossy skin."""
from _slough_common import *

UNIT_ID = 'slough_teshk'
SLATE_D = _hex('#3a3f43')
N = Naga(height=2.2, girth=0.92, tube=0.145, coil_r=0.42, loops=1.5, coil_back=0.22, coil_depth=0.78, hood='spade',
         hood_w=1.2, hood_h=1.2, head_len=1.5, band_len=0.24, band_dark=0.5, accent=(), gloss=1.7, body_r=0.125,
         dark=_hex('#4a4f52'), light=_hex('#e9e4d0'), belly=_hex('#e0b440'), skin=_hex('#8a8f86'),
         mantle=_hex('#33383b'), hood_face=_hex('#c8cdc2'), hood_rim=_hex('#e8c860'), lip=_hex('#f2e6b0'),
         tail_side=1, lean=0.06)
CAMERA = naga_camera(N)


def neutral_pose():
    P = naga_pose(N)
    s = P['s']
    reach(P, 'r', scr(-0.50, 1.34 * s, 0.30))
    aim(P, 'r', sdir(-0.15, -0.25, 1.0))
    P['hd_l'] = P['waist'] + v3(0.06, 0.12, -0.20) * s
    return P


def sabre_fang(add, P, side='r', length=0.95):
    s = P['s']
    d = P['item_' + side]
    if d is None:
        return
    # long curved sabre made from one fang: slim, bowed in the camera plane; chartreuse tip, gold line
    res = blade(add, P, side, 'sabre', length=length * s, below=0.12 * s)
    if res is None:
        return
    butt, tip = res
    dd = norm(tip - butt)
    add(Capsule(butt + dd * 0.15 * s, butt + dd * 0.20 * s, 0.040 * s), 'amber', 0.0)   # guard
    add(Capsule(tip - dd * 0.20 * s, tip, 0.020 * s, 0.006), 'glaze', 0.0)            # chartreuse tip


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    s = P['s']
    Rt = B['chest_R']
    up, fw, rt = Rt[:, 1], Rt[:, 2], Rt[:, 0]
    C = P['chest']
    # amber lacquer shoulder-guard on the sword shoulder + sash across the chest
    sh = P['sh_r']
    add(Ellipsoid(sh + up * 0.045 * s - rt * 0.02 * s, (0.125 * s, 0.07 * s, 0.11 * s), Rt), 'amber', 0.04)
    add(Ellipsoid(sh + up * 0.07 * s, (0.09 * s, 0.03 * s, 0.085 * s), Rt), 'amber_lt', 0.02)
    a = P['sh_r'] + up * 0.02 * s + fw * 0.07 * s
    b = P['waist'] + rt * 0.17 * s + fw * 0.10 * s - up * 0.03 * s
    add(Capsule(a, b, 0.032 * s), 'amber', 0.0)
    add(Capsule(a + fw * 0.012 * s, b + fw * 0.012 * s, 0.012 * s), 'amber_lt', 0.0)
    sabre_fang(add, P)
    mats = {'amber': Material(lambda p, n: _arr(LACQUER, len(p)) * (0.88 + 0.25 * fbm(p, 9.0, 2)[:, None]), spec=0.8, gloss=60, sss=0.3),
            'amber_lt': Material(LACQUER_LT, spec=0.8, gloss=60)}
    return naga_finish(P, N, parts, mats)


def _fit(row, i, P):
    s = P['s']
    P0 = neutral_pose()
    if row == 'attack':           # draw back low, then one clean lunging cut across
        k = [-0.5, 0.0, 1.0, 0.3][i]
        P['hd_r'] = P0['hd_r'] + E2 * 0.22 * k + E1 * (-0.06 * k) + v3(0, 0.12 * (1 if i == 1 else 0) + 0.04 * k, 0) * s
        P['item_r'] = [sdir(-0.55, 0.25, 0.25), sdir(-0.4, 0.8, 0.2), sdir(0.35, 0.05, 1.0), sdir(0.1, -0.3, 1.0)][i]
    if row == 'cast':
        P['hd_r'] = P0['hd_r'] + v3(0, [0.1, 0.3, 0.1][i], 0) * s
        P['item_r'] = sdir(-0.3, 0.9, 0.3)
    if row in ('idle', 'move', 'hit'):
        P['item_r'] = norm(P['item_r'] if P['item_r'] is not None else P0['item_r'])
    P['hd_l'] = P['waist'] + v3(0.06, 0.12, -0.20) * s if row != 'death' else P['hd_l']


ROWS, frames = naga_rows(neutral_pose, attack='bite', cast='raise', hook=_fit)

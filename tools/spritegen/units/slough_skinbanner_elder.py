"""Skinbanner Elder (Slough rare, commander). Standard build in a ppm-48 frame, tall narrow hood, wide faded bone
bands. A tall banner pole is held upright in the right hand: banner-hook on top, a chartreuse-trimmed crossbar and
three long pale shed skins (faint ghost bands) hanging from it. Left hand raised, fingers spread.
Defining detail: the hanging skins of the dead."""
from _slough_common import *

UNIT_ID = 'slough_skinbanner_elder'
N = Naga(height=2.1, girth=1.05, tube=0.16, coil_r=0.50, loops=1.8, hood='narrow', hood_w=1.05, hood_h=1.3,
         head_len=1.75, band_len=0.30, band_dark=0.45, band_fade=0.18, grey=0.35, accent=(), tail_side=-1,
         belly=_hex('#cfa23c'), hood_face=_hex('#d8cf9c'), hood_rim=_hex('#f2ecd0'))
CAMERA = Camera(ppm=48.0)

BAR_Y = 1.95         # crossbar height above the hand's pole point (m above ground when upright)


def neutral_pose():
    P = naga_pose(N)
    s = P['s']
    reach(P, 'r', scr(-0.40, 1.22 * s, 0.22))
    aim(P, 'r', v3(0, 1, 0))
    reach(P, 'l', scr(0.52, 1.78 * s, 0.05))
    return P


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    s = P['s']
    g = P['hd_r']
    d = norm(P['item_r'])
    drop = P['drop']
    butt, tip = blade(add, P, 'r', 'gaff', length=0.98, below=1.10)
    d = norm(tip - butt)
    bar = lerp(butt + d * 1.95 * s, butt + d * 0.5 * s, drop)
    sv = E1
    add(Capsule(bar - sv * 0.31, bar + sv * 0.31, 0.022 * s), 'haft', 0.0)
    for k in (-1, 1):
        add(Sphere(bar + sv * 0.32 * k, 0.034 * s), 'glaze', 0.0)
    add(Capsule(bar - sv * 0.30, bar + sv * 0.30, 0.014 * s, 0.014 * s), 'glaze', 0.0)
    sw = np.sin(2 * np.pi * P['tell']) * 0.12 + 0.06 * P['breathe']
    for off, ln in ((-0.25, 0.95), (0.0, 1.20), (0.25, 0.85)):
        top = bar + sv * off * s - d * 0.02 * s
        dn = norm(v3(0, -1, 0) + sv * (sw + 0.15 * off))
        if drop > 0:
            dn = norm(lerp(dn, E2 + E1 * off, drop))
            top = lerp(top, v3(top[0] * 0.5, 0.08, -0.1) + E1 * off * 0.5, drop)
        c = top + dn * ln * 0.5 * s
        add(Ellipsoid(c, (0.115 * s, ln * 0.5 * s, 0.014 * s), R_from(dn, E2 + v3(0, 0.2, 0))), 'banner', 0.0)
        add(Capsule(top + dn * 0.02, top + dn * 0.07 * s, 0.015 * s), 'glaze', 0.0)
    # raised left hand: spread fingers
    h = P['hd_l']
    a = norm(h - P['sh_l'])
    sv2 = _side(a)
    for k in range(4):
        f = k - 1.5
        add(Capsule(h + a * 0.02, h + (a + sv2 * f * 0.40) * 0.12 * s, 0.014 * s, 0.006), 'hand', 0.0)

    def banner_alb(p, n):
        base = _arr(HUSK, len(p))
        y = p[:, 1]
        stripe = (np.mod(y / 0.22, 1.0) < 0.35)
        base[stripe] = base[stripe] * 0.78
        return base * (0.94 + 0.12 * fbm(p, 9.0, 2)[:, None])
    mats = {'banner': Material(banner_alb, spec=0.05, gloss=10, sss=0.7, brush=0.04)}
    return naga_finish(P, N, parts, mats)


def _fit(row, i, P):
    s = P['s']
    if row == 'cast':               # only the free hand rises; the pole stays planted
        P['hd_r'] = P['hd_r'] - v3(0, [0.12, 0.28, 0.10][i], [0.02, 0.06, 0.12][i]) * s
        P['hd_l'] = P['hd_l'] + v3(0, 0.0, 0.0)
    if row == 'attack':             # the pole dips forward on the strike (hook toward the enemy)
        a = [-0.10, 0.0, 0.62, 0.22][i]
        P['item_r'] = norm(rot_x(a) @ v3(0, 1, 0))
        P['hd_r'] = P['hd_r'] + v3(0, 0, [-0.02, 0.0, 0.12, 0.05][i]) * s
    if row in ('idle', 'move', 'hit', 'death'):
        P['item_r'] = norm(v3(0, 1, 0) + v3(0, 0, 0.0))


ROWS, frames = naga_rows(neutral_pose, attack='bite', cast='raise', hook=_fit)

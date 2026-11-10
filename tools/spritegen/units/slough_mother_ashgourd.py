"""Mother Ashgourd (Slough hero). Older, heavy-bodied, 2.1 m, grey around the hood, grey-black and bone bands.
A big gourd on a strap at each hip and a sling in the right hand; her left holds one gourd up to the light, its
mouth open, a thin glowing stream of venom pouring from it. Defining detail: the open gourd and its stream."""
from _slough_common import *

UNIT_ID = 'slough_mother_ashgourd'
N = Naga(height=2.1, girth=1.30, tube=0.195, coil_r=0.54, loops=1.7, coil_back=0.28, hood='broad', hood_w=1.35,
         hood_h=1.1, head_len=1.5, band_len=0.28, band_dark=0.55, band_fade=0.1, grey=0.6, accent=(), body_r=0.17,
         dark=_hex('#33383a'), light=_hex('#d6d2bc'), belly=_hex('#c9a444'), skin=_hex('#8c8a66'),
         mantle=_hex('#555a58'), hood_face=_hex('#b4b8a8'), hood_rim=_hex('#e8e6d4'), lip=_hex('#e6dca0'),
         tail_side=-1)
CAMERA = naga_camera(N)
POUR = 0.5


def neutral_pose():
    P = naga_pose(N)
    s = P['s']
    reach(P, 'r', scr(-0.50, 1.28 * s, 0.30))
    aim(P, 'r', sdir(-0.55, -0.35, 0.45))
    reach(P, 'l', scr(0.52, 1.80 * s, 0.12))
    return P


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    s = P['s']
    Rt = B['chest_R']
    up, fw, rt = Rt[:, 1], Rt[:, 2], Rt[:, 0]
    W = P['waist']
    dr = P['drop']
    alive = 1.0 - min(1.0, P['end'] * 2.0)
    # --- hip gourds on reed straps, bandolier across the chest
    for sx in (-1, 1):
        hip = W + rt * sx * 0.24 * N.girth * s + fw * 0.02 * s - up * 0.02 * s
        gc = hip + rt * sx * 0.06 * s - up * 0.10 * s + fw * 0.06 * s
        gourd(add, gc, r=0.17 * s, neck=norm(v3(sx * 0.4, 1.0, 0.0)))
        sh = P['sh_r' if sx < 0 else 'sh_l']
        a = lerp(sh, P['chest'], 0.55) + fw * 0.12 * s
        add(Capsule(a, hip + fw * 0.04 * s, 0.018 * s), 'lash', 0.0)
    # --- sling in the right hand
    hd = P['hd_r']
    d = norm(P['item_r'])
    cord = 0.40 * s
    end = hd + d * cord
    throw = P['throw']
    add(Capsule(hd, end, 0.008 * s), 'lash', 0.0)
    add(Capsule(hd, end + sv_off(d) * 0.05 * s, 0.006 * s), 'lash', 0.0)
    add(Ellipsoid(end, (0.05 * s, 0.035 * s, 0.05 * s), R_from(d, E2)), 'lash', 0.0)
    if True:
        gp = end + d * 0.04 * s + d * throw * 1.1 * s - v3(0, 0.2 * throw * throw, 0)
        add(Sphere(gp, 0.11 * s), 'gourd', 0.0)
        add(Sphere(gp + v3(0, 0.10, 0) * s, 0.05 * s), 'glaze', 0.0)
    # --- raised gourd, mouth open, pouring a thin venom stream
    h = P['hd_l']
    nk = norm(sdir(0.80, -0.30, 0.10) if dr == 0 else v3(0, 1, 0))
    gc = h + v3(0, 0.05 * s, 0) - nk * 0.10 * s
    gt = gourd_open(add, gc, 0.15 * s, nk)
    lights = []
    if alive > 0.25:
        d2 = norm(v3(0.10, -1.0, 0.06))
        strength = 0.6 + 0.8 * P['cast_glow']
        L = (0.55 + 0.35 * P['cast_glow']) * s * alive
        n = 12
        for i in range(n):
            t = (i + 0.5) / n
            q = gt + d2 * L * t + v3(0.02 * t * t, -0.05 * t * t, 0) * s
            add(Sphere(q, 0.021 * s * (1.0 - 0.35 * t)), 'venom', 0.0)
        emit(add, gt + d2 * L, 'spray', 0.7)
        lights = [Light(gt + v3(0, -0.1, 0.1), CHART, 0.4 + 0.5 * P['cast_glow'], 0.4)]
    return naga_finish(P, N, parts, {}, lights)


def sv_off(d):
    return _side(d)


def gourd_open(add, c, r, nk):
    c = v3(*c)
    add(Sphere(c, r), 'gourd', 0.0)
    add(Sphere(c + nk * r * 1.0, r * 0.62), 'gourd', 0.04)
    mouth = c + nk * r * 1.5
    add(Cylinder(c + nk * r * 1.25, mouth, r * 0.30, 0.01), 'gourd', 0.0)
    add(Sphere(mouth, r * 0.24), 'venom', 0.0)
    return mouth


def _fit(row, i, P):
    s = P['s']
    P0 = neutral_pose()
    if row == 'attack':          # sling whirled overhead, gourd released on the strike
        dirs = [sdir(-0.6, 0.8, -0.4), sdir(-0.2, 1.0, 0.0), sdir(0.3, 0.1, 1.0), sdir(0.0, -0.6, 0.6)]
        P['item_r'] = dirs[i]
        P['hd_r'] = P0['hd_r'] + v3(0, [0.12, 0.28, 0.12, 0.0][i], 0) * s + E2 * [-0.05, 0, 0.12, 0.05][i]
        P['throw'] = [0, 0, 0.9, 1.0][i]
        if i == 3:
            P['throw'] = 1.6
    if row == 'cast':            # the held gourd tips and pours hard; hood flares
        P['hd_l'] = P0['hd_l'] + v3(0, [0.0, 0.05, 0.0][i], 0) * s
        P['hd_r'] = P0['hd_r']
        P['item_r'] = P0['item_r']
        P['throw'] = 0.0
    if row in ('idle', 'move', 'hit', 'death'):
        P['item_r'] = sdir(-0.55, -0.35, 0.45) if row != 'death' else sdir(-0.3, -0.9, 0.2)
        if row in ('idle', 'move'):
            P['throw'] = 0.0
    P['hood'] = min(P['hood'], 1.3)


ROWS, frames = naga_rows(neutral_pose, attack='swing', cast='raise', hook=_fit)

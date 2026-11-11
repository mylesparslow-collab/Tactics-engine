"""Gourdslinger (Slough uncommon, ranged area). Standard 2.1 m build with a rack of four big dried marsh-gourds
strapped across its back above the shoulders (a lumpy crown behind the hood, chartreuse wax stoppers), a sling
whirling in the right hand with a gourd in the pouch, a spare gourd held up in the left. Black-and-bone coil.
Defining detail: the gourd rack behind the head."""
from _slough_common import *

UNIT_ID = 'slough_gourdslinger'
N = Naga(height=2.1, girth=1.0, tube=0.15, coil_r=0.50, loops=1.75, hood='broad', hood_w=0.8, accent=(),
         band_len=0.26, band_dark=0.66, head_len=1.4, tail_side=-1, pattern='saddles', hood_mark='ocelli',
         dark=_hex('#3b2c20'), light=_hex('#d8c49c'), belly=_hex('#d9a94a'), mantle=_hex('#2e231a'),
         hood_face=_hex('#8a7356'), hood_rim=_hex('#efe0b8'), lip=_hex('#ecdcb4'), skin=_hex('#6e5640'),
         bracer=_hex('#7a6a3a'))
CAMERA = naga_camera(N)


def neutral_pose():
    P = naga_pose(N)
    s = P['s']
    reach(P, 'r', scr(-0.52, 1.50, 0.12))
    aim(P, 'r', sdir(-0.2, 1.0, 0.0))        # direction the sling hangs / whirls from the hand
    reach(P, 'l', scr(0.45, 1.34, 0.45))
    return P


def _rack(P, B):
    Rt = B['chest_R']
    rt, up, fw = Rt[:, 0], Rt[:, 1], Rt[:, 2]
    C = P['chest']
    s = P['s']
    out = []
    for (x, y, r) in ((-0.27, 0.22, 0.125), (0.27, 0.24, 0.13), (-0.13, 0.46, 0.115), (0.14, 0.48, 0.11)):
        out.append((C + (rt * x + up * y - fw * 0.12) * s, r * s, up))
    return out


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    s = P['s']
    Rt = B['chest_R']
    C = P['chest']
    rt, up, fw = Rt[:, 0], Rt[:, 1], Rt[:, 2]
    # gourd rack: a reed yoke strapped across the shoulders, four gourds above it
    add(Capsule(C + (-rt * 0.24 + up * 0.14 - fw * 0.10) * s, C + (rt * 0.24 + up * 0.14 - fw * 0.10) * s, 0.018 * s), 'lash', 0.0)
    add(Capsule(C + (-rt * 0.20 + up * 0.16 - fw * 0.12) * s, C + (rt * 0.20 + up * 0.46 - fw * 0.20) * s, 0.012 * s), 'lash', 0.0)
    for c, r, u in _rack(P, B):
        gourd(add, c, r, neck=norm(u + fw * 0.0 + v3(0, 0.3, 0)))
    # sling in the right hand, mid-whirl; the pouch gourd leaves it on the throw
    h = P['hd_r']
    th = P['throw']
    ph = P['tell'] * 2 * np.pi
    d = norm(P['item_r'])
    side = norm(np.cross(d, v3(0.3, 0, 1)))
    a = norm(d * np.cos(ph) + side * np.sin(ph) * 0.9 + v3(0, 0.1, 0))
    L = 0.55 * s
    pouch = h + a * L
    tgt = h + sdir(0.8, -0.1, 0.3) * 0.75
    if th > 0.01:
        pouch = lerp(h + sdir(0.9, 0.3, 0.2) * L, tgt, th)
        a = norm(pouch - h)
    # cord: two thin strands from the hand to the pouch + a pouch
    n = 5
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        sag = v3(0, -0.04, 0) * s
        add(Capsule(lerp(h, pouch, t0) + sag * np.sin(np.pi * t0), lerp(h, pouch, t1) + sag * np.sin(np.pi * t1),
                    0.009 * s), 'lash', 0.0)
    if P['drop'] < 0.5:
        gourd(add, pouch, 0.085 * s, neck=norm(h - pouch))
    # left hand: spare gourd held up
    if P['drop'] < 0.1 or True:
        hl = P['hd_l']
        gc = hl + v3(0, 0.10, 0.02) * s
        gl = lerp(gc, scr(0.2, 0.12, -0.35), min(1.0, P['drop'] * 1.5)) if P['drop'] > 0 else gc
        add(Sphere(gl, 0.088 * s), 'gourd', 0.0)
        add(Sphere(gl + v3(0, 0.10, 0) * s, 0.055 * s), 'gourd', 0.04)
        add(Cylinder(gl + v3(0, 0.17, 0) * s, gl + v3(0, 0.21, 0) * s, 0.028 * s, 0.01), 'glaze', 0.0)
    lights = []

    def world(add2):
        if P['venom'] > 0.4 and P['drop'] < 0.1:
            venom_drip(add2, P, gl + v3(0, 0.2, 0) * s, P['venom'] * 0.6)
    return naga_finish(P, N, parts, world=world)


def _fit(row, i, P):
    s = P['s']
    if row == 'attack':
        # wind the sling up behind the head, whirl it, then let go forward
        P['hd_r'] = [scr(-0.55, 1.55, -0.05), scr(-0.50, 1.70, 0.0), scr(-0.30, 1.45, 0.45), scr(-0.45, 1.40, 0.30)][i]
        P['item_r'] = [sdir(-0.5, 0.8, -0.3), sdir(-0.1, 1.0, -0.2), sdir(0.9, 0.3, 0.2), sdir(0.3, -0.5, 0.2)][i]
        P['tell'] = [0.0, 0.25, 0.5, 0.75][i]
        P['throw'] = [0, 0, 0.25, 1.0][i] if i < 3 else 1.0
    elif row == 'cast':
        P['hd_r'] = P['hd_r'] + v3(0, 0.0, 0.0)
        P['throw'] = [0.0, 0.5, 1.0][i]
        P['item_r'] = sdir(0.6, 0.6, 0.3)
        P['hd_l'] = scr(0.40, 1.30, 0.42) + v3(0, [0.0, 0.25, 0.10][i], 0)
    elif row == 'idle':
        P['tell'] = [0.0, 0.25, 0.5, 0.75][i]
    elif row == 'move':
        P['tell'] = [0.0, 0.25, 0.5, 0.75][i]
    elif row == 'hit':
        P['throw'] = 0.0


ROWS, frames = naga_rows(neutral_pose, attack='swing', cast='throw', hook=_fit)

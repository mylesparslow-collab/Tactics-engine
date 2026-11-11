"""Hookfang Wrangler (Slough uncommon, controller). Standard 2.1 m build, the body coiled over to one side to
brace. An oversized rust-headed barbed trident (three tines, the outer two barbed back) held across the body,
a thick reed-green line coiled over the left shoulder and trailing to the coil. Black-and-bone banding.
Defining detail: the barbed trident."""
from _slough_common import *

UNIT_ID = 'slough_hookfang_wrangler'
N = Naga(height=2.1, girth=1.08, tube=0.16, coil_r=0.50, loops=1.75, hood='cobra', hood_w=1.0, accent=(),
         band_len=0.30, band_dark=0.48, head_len=1.4, tail_side=1, lean=0.06, coil_back=0.30, pattern='rings', hood_mark='chevron',
         dark=_hex('#233a2c'), light=_hex('#c9d2a2'), belly=_hex('#d8c070'), mantle=_hex('#1c2e22'),
         hood_face=_hex('#5f7a5c'), hood_rim=_hex('#e2e8c4'), lip=_hex('#e2e8c4'), skin=_hex('#46604a'))
CAMERA = naga_camera(N)


def neutral_pose():
    P = naga_pose(N)
    s = P['s']
    bend(P, side=np.radians(-9), fwd=0.0)          # braced over to its right (screen-left)
    P['coil_c'] = P['coil_c'] + E1 * 0.06
    hold_pole(P, 'r', 'l', grip=scr(-0.40, 1.00, 0.34), direction=sdir(0.55, 0.65, 0.30), spacing=0.40)
    return P


def big_trident(add, butt, tip, d, s, spread=1.0):
    s0 = s
    s = s * spread
    """Oversized rust trident: shaft to tip, crossbar head, three long tines, outer two barbed back."""
    cam = v3(-0.53, 0.5, 0.68)
    bn = cam - d * (cam @ d)
    bn = norm(np.cross(d, norm(bn)))
    base = tip - d * 0.30 * s
    add(Capsule(butt, base, 0.026 * s0), 'haft', 0.0)
    add(Capsule(base - d * 0.04 * s, base + d * 0.06 * s, 0.034 * s), 'lash', 0.0)
    wd = 0.20 * s
    add(Capsule(base - bn * wd, base + bn * wd, 0.024 * s), 'rust', 0.02)
    for k in (-1, 0, 1):
        a = base + bn * wd * k
        t = a + d * (0.46 if k == 0 else 0.38) * s
        add(Capsule(a, t, 0.026 * s, 0.006 * s), 'rust', 0.01)
        if k:
            m = a + d * 0.24 * s
            add(Capsule(m, m - d * 0.12 * s + bn * 0.10 * k * s, 0.018 * s, 0.004 * s), 'rust', 0.0)
            # outer tine curves in a little
    add(Sphere(tip + d * 0.16 * s, 0.001), 'rust', 0.0)


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    s = P['s']
    ha, hb = P['hd_r'], P['hd_l']
    d = norm(hb - ha)
    butt, tip = ha - d * 0.30 * s, hb + d * 0.80 * s
    butt, tip = _drop(P, butt, tip)
    if P['drop'] > 0:           # lying on the ground it would span the tile: the fallen haft sinks into the silt
        m = (butt + tip) / 2
        k = 1.0 - 0.30 * min(1.0, P['drop'] * 2)
        butt, tip = m + (butt - m) * k, m + (tip - m) * k
    d = norm(tip - butt)
    big_trident(add, butt, tip, d, s, 1.25)
    # line coiled over the left shoulder: three loops round the shoulder/upper chest, a tail trailing to the coil
    Rt = B['chest_R']
    rt, up, fw = Rt[:, 0], Rt[:, 1], Rt[:, 2]
    sh = P['sh_l']
    ctr = sh + up * 0.02 * s
    for k in range(3):
        rr = (0.17 - 0.025 * k) * s
        ax = norm(up * 0.4 + rt * 0.9)
        add(Torus(ctr - rt * (0.02 * k) * s + up * (-0.04 * k) * s, ax, rr, 0.030 * s), 'line', 0.0)
    end = P['waist'] + (rt * 0.20 - up * 0.10 + fw * 0.06) * s
    add(Capsule(ctr - up * 0.1 * s - fw * 0.1 * s, end, 0.026 * s), 'line', 0.0)
    add(Capsule(end, scr(0.35, 0.05, -0.20), 0.026 * s), 'line', 0.0)
    mats = {'line': Material(_hex('#6f7a3c'), spec=0.1, gloss=10, brush=0.08)}
    mats['rust'] = Material(_hex('#a35a30'), spec=0.4, gloss=28, metal=0.25, brush=0.08)
    return naga_finish(P, N, parts, mats)


def _fit(row, i, P):
    """The oversized trident is the widest thing in the frame: keep the thrust and the raise inside it."""
    s = P['s']
    if row == 'attack':
        move_hands(P, -E1 * [0.0, 0.03, 0.08, 0.04][i] * s)
    if row == 'cast':
        move_hands(P, v3(0, -[0.10, 0.18, 0.10][i] * s, 0))
    if row == 'hit':
        move_hands(P, E1 * 0.04 * s)
    P['hood'] = min(P['hood'], 1.12)


ROWS, frames = naga_rows(neutral_pose, attack='thrust', hook=_fit)

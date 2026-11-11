"""Skin-Reader (Slough uncommon, healer). Old and thin, reared to 2.0 m with a stoop, the hood edge ragged and
pale. A tall hook-staff in the right hand with one long pale shed skin hanging from the hook like a scroll, a
chartreuse knot on the shaft; the left hand open, fingers spread, as if reading by touch. Faded low-contrast
bands, husk-pale skin, gold belly. Defining detail: the hanging skin on the hook-staff."""
from _slough_common import *

UNIT_ID = 'slough_skin_reader'
GREY_D = _hex('#4b4d44')
N = Naga(height=2.0, girth=0.80, tube=0.135, coil_r=0.48, loops=1.7, hood='ragged', hood_w=1.2, hood_h=1.1,
         lean=0.10, dark=GREY_D, light=_hex('#cfc8aa'), band_fade=0.55, band_len=0.27, band_dark=0.45, accent=(),
         skin=_hex('#857c5c'), mantle=_hex('#34352d'), hood_face=_hex('#8c8670'), hood_rim=_hex('#f2ecd2'),
         pattern='rings', hood_mark='plain',
         belly=_hex('#d3a94c'), grey=0.4, head_len=1.4, arm_len=1.0, tail_side=-1)
CAMERA = naga_camera(N)


def neutral_pose():
    P = naga_pose(N)
    s = P['s']
    reach(P, 'r', scr(-0.46, 1.05, 0.22))
    P['item_r'] = norm(v3(0.0, 1.0, 0.0))
    reach(P, 'l', scr(0.38, 1.22, 0.38))
    return P


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    s = P['s']
    d = P['item_r']
    g = P['hd_r']
    # tall hook-staff: shaft 2.15 m, hook at the top
    L = 1.05
    butt, tip = blade(add, P, 'r', 'gaff', length=L, below=0.85 - 0.45 * min(1.0, P['drop'] * 3))   # butt stays off the frame bottom as it falls
    dd = norm(tip - butt)
    # chartreuse knot below the hook
    add(Sphere(tip - dd * 0.12, 0.045), 'glaze', 0.0)
    # the shed skin hangs from the hook, a long pale flat scroll (cream, brighter than the body)
    top = tip - dd * 0.02 + E1 * 0.06 + E2 * 0.06
    sw = 0.04 * np.sin(P['tell'] * 2 * np.pi)
    ln = 0.85 * (1 - 0.8 * P['flat'])
    Rs = np.stack([E1, v3(0, 1, 0), E2], axis=1)
    for k, (t, wd) in enumerate(((0.28, 0.115), (0.62, 0.105), (0.93, 0.065))):
        add(Ellipsoid(top + v3(sw * t, -ln * t, 0), (wd, 0.21, 0.022), Rs), 'skinpale', 0.04)
    # open left hand: spread fingers
    h = P['hd_l']
    sh = P['sh_l']
    fd = norm(h - sh)
    for k in (-1.5, -0.5, 0.5, 1.5):
        f = norm(fd + v3(0, 0, 0) + _hang_off(fd) * 0.32 * k * 0.5 + v3(0, 0.1 * (abs(k) < 1), 0))
        add(Capsule(h, h + f * 0.10 * s, 0.014 * s, 0.009 * s), 'hand', 0.0)
    mats = {'skinpale': Material(lambda p, n: _arr(_hex('#f4efd6'), len(p)) * (0.92 + 0.12 * fbm(p, 12.0, 2)[:, None]),
                                 spec=0.05, gloss=10, sss=0.6, brush=0.03)}
    return naga_finish(P, N, parts, mats)


def _hang_off(d):
    return _side(d)


def _fit(row, i, P):
    if row == 'attack':      # staff: raise, then bring the hook down and forward
        P['hd_r'] = [scr(-0.42, 1.00, 0.24), scr(-0.40, 1.04, 0.26), scr(-0.20, 1.25, 0.45), scr(-0.30, 1.10, 0.35)][i]
        slide(P, -E1 * [0, 0.02, 0.08, 0.04][i] * P['s'])
        P['hood'] = min(P['hood'], 1.05)
        P['item_r'] = [sdir(0.05, 1.0, 0.05), sdir(0.15, 1.0, 0.15), sdir(0.45, 0.85, 0.25), sdir(0.3, 1.0, 0.2)][i]


def _fit2(row, i, P):
    _fit(row, i, P)
    if row == 'cast':      # staff stays put; only the reading hand rises, hood flares
        P['hd_r'] = scr(-0.46, 1.05, 0.22)
        P['hd_l'] = scr(0.38, 1.22 + [0.0, 0.2, 0.1][i], 0.38)
        P['item_r'] = norm(v3(0, 1, 0))
    if row == 'death' and i >= 1:   # keep the slumping S off the bottom edge
        P['mid'] = P['mid'] - E2 * 0.22 * [0, 0.6, 1.0, 1.0][i]


ROWS, frames = naga_rows(neutral_pose, attack='swing', cast='raise', hook=_fit2)

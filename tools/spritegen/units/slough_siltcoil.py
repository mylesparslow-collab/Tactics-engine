"""Siltcoil Ambusher (Slough uncommon, ambusher). A serpent-folk lying in wait, sunk in a low pale silt mound: three
banded coils (mud-black and silt-bone rings) break the surface in separate arches, the last one ending in the flat
paddle tail. Out of the middle rises a hunched, hooded body (marsh olive, gold-olive belly, dark mantle and hood with a
pale rim) and both arms, holding a bold hooked glaive: a black haft, one great pale fang blade with a back-hook and a
chartreuse-glazed tip. Defining detail: the hooded head and the glaive rising out of the silt."""
from _slough_common import *

UNIT_ID = 'slough_siltcoil'
N = Naga(height=1.72, girth=1.08, tube=0.09, coil_r=0.28, loops=1.4, coil_depth=0.62, coil_back=0.36, coil_lift=0.3,
         hood='broad', hood_w=1.25, hood_h=1.05, lean=0.20, dark=_hex('#2c3020'), light=_hex('#b3ad86'), band_fade=0.15,
         band_len=0.24, accent=(), skin=_hex('#6a7040'), belly=_hex('#b9a65a'), mantle=_hex('#2f341f'),
         hood_face=_hex('#5f5c3a'), hood_rim=_hex('#ddd6ac'), lip=_hex('#cdbd74'), head_len=1.55, fang=1.2,
         pattern='rings', hood_mark='stripe', hood_mark_col=CHART,
         eye=_hex('#ffd23a'), tail_side=-1)
CAMERA = naga_camera(N)

SILT_C = _hex('#8a816b')
SILT_WET = _hex('#625a49')
HUMP_DK = _hex('#2c3020')
HUMP_LT = _hex('#b9b38c')
HAFT_DK = _hex('#1d1e18')
MOUND = (0.70, 0.24, 0.40)        # mound radii along screen-right, up, toward camera

# coils breaking the surface: (centre in screen terms x, d), arch radius, tube radius, arch direction (screen x, d),
# taper toward the far end (the tail)
HUMPS = (((-0.50, -0.02), 0.20, 0.120, (1.0, 0.35), 0.0),
         ((0.44, -0.10), 0.17, 0.105, (1.0, -0.45), 0.0),
         ((0.10, 0.20), 0.13, 0.085, (1.0, 0.15), 0.75))


def neutral_pose():
    P = naga_pose(N)
    hold_pole(P, 'r', 'l', grip=scr(-0.46, 0.80, 0.24), direction=sdir(-0.10, 1.0, 0.0), spacing=0.38)
    return P


def _mound_c(P):
    return P['coil_c'] + v3(0, -0.03, 0)


def _hump_frames(P):
    c0 = _mound_c(P)
    out = []
    for (x, d), R, r, ax, taper in HUMPS:
        a = norm(E1 * ax[0] + E2 * ax[1])
        c = c0 + E1 * x + E2 * d + v3(0, MOUND[1] * 0.55 * (1 - 0.6 * (x / MOUND[0]) ** 2), 0)
        out.append((c, a, R, r, taper))
    return out


def glaive(add, P, butt, tip, s):
    """Bold hooked glaive: black haft, chartreuse lashing, one big pale fang blade bowed to the camera-visible side
    with a back-hook at its root, tip glazed chartreuse."""
    d = norm(tip - butt)
    L = np.linalg.norm(tip - butt)
    cam = v3(-0.53, 0.5, 0.68)
    bn = norm(np.cross(d, norm(cam - d * (cam @ d))))
    if bn @ E1 < 0:
        bn = -bn                                 # blade edge bows toward screen-right (away from the body)
    bl = 0.56 * s
    base = tip - d * bl
    add(Capsule(butt, base + d * 0.02, 0.030 * s), 'haftdk', 0.0)
    add(Capsule(base - d * 0.09 * s, base + d * 0.01 * s, 0.036 * s), 'glaze', 0.0)
    add(Sphere(butt, 0.032 * s), 'glaze', 0.0)
    n = 7
    prev = base
    for i in range(1, n + 1):
        t = i / n
        q = base + d * bl * t + bn * 0.15 * s * np.sin(np.pi * t * 0.85)
        ra = 0.080 * s * (1 - (i - 1) / n) ** 0.7 + 0.006
        rb = 0.080 * s * (1 - i / n) ** 0.7 + 0.004
        add(Capsule(prev, q, ra, rb), 'blade' if t < 0.62 else 'glaze', 0.012)
        prev = q
    # the hook: a curved spur off the back of the blade root, curling down
    h0 = base + d * 0.07 * s
    h1 = h0 - bn * 0.09 * s + d * 0.02 * s
    h2 = h0 - bn * 0.15 * s - d * 0.05 * s
    add(Capsule(h0, h1, 0.032 * s, 0.024 * s), 'blade', 0.01)
    add(Capsule(h1, h2, 0.024 * s, 0.008 * s), 'blade', 0.008)


def _hump_alb(c, a, R):
    up = v3(0, 1, 0)

    def fn(p, n):
        q = p - c
        ang = np.arctan2(q @ up, q @ a)               # 0 .. pi along the arch
        k = np.floor(ang / (np.pi / 5.0)).astype(int)
        col = np.where((k % 2 == 0)[:, None], np.array(HUMP_DK)[None, :], np.array(HUMP_LT)[None, :])
        return col
    return fn


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    s = P['s']
    # --- the glaive through both hands
    ha, hb = P['hd_r'], P['hd_l']
    d = norm(hb - ha)
    butt, tip = _drop(P, ha - d * 0.40 * s, hb + d * 1.05 * s)
    glaive(add, P, butt, tip, s)
    # --- low pale silt mound with a ragged lip (added after the husk flatten: dead, it slumps to a low dark patch)
    mound = []
    madd = lambda prim, mat, k=0.0: mound.append(Part(prim, mat, k))
    fl = P['flat']
    c = _mound_c(P)
    Rm = np.stack([E1, v3(0, 1, 0), E2], axis=1)
    kw = 1.0 - 0.15 * fl
    k = 1.0 - 0.62 * fl
    madd(Ellipsoid(c, (MOUND[0] * kw, MOUND[1] * k, MOUND[2] * kw), Rm), 'silt', 0.0)
    for (x, dd, rx, ry, rz) in ((-0.42, 0.18, 0.26, 0.09, 0.18), (0.40, 0.14, 0.24, 0.08, 0.17), (0.0, -0.22, 0.34, 0.10, 0.2)):
        madd(Ellipsoid(c + (E1 * x + E2 * dd) * kw, (rx * kw, ry * k, rz * kw), Rm), 'silt', 0.06)
    # --- coils arching out of the silt (each banded, ends sunk below the surface)
    mats = {}
    for j, (hc, a, R, r, taper) in enumerate(_hump_frames(P)):
        sink = 0.9 * P['flat']
        cc = hc - v3(0, R * sink, 0)
        pts = [cc + a * np.cos(t) * R * 1.1 + v3(0, np.sin(t) * R, 0) for t in np.linspace(-0.25, np.pi + 0.25, 10)]
        rads = [r * (1 - taper * (i / 9) ** 1.5) for i in range(10)]
        for i in range(9):
            add(Capsule(pts[i], pts[i + 1], rads[i], rads[i + 1]), 'hump%d' % j, 0.02)
        if taper > 0:                                  # the last coil ends in the flat paddle tail
            tg = norm(pts[-1] - pts[-3])
            side = norm(np.cross(tg, v3(0, 1, 0)))
            pc = pts[-1] + v3(0, 0.07, 0) + tg * 0.02
            add(Ellipsoid(pc, (0.02, 0.09, 0.13), np.stack([side, v3(0, 1, 0), norm(tg - v3(0, tg[1], 0))], axis=1)),
                'hump%d' % j, 0.02)
        mats['hump%d' % j] = Material(_hump_alb(cc, a, R), spec=0.45, gloss=46, brush=0.03)


    def silt_alb(p, n):
        a = _arr(SILT_C, len(p)) * (1 - 0.4 * fl) * (0.88 + 0.22 * fbm(p, 6.0, 3)[:, None])
        wet = (vnoise(p * v3(1, 2, 1), 4.0) > 0.66)[:, None]
        return np.where(wet, np.array(SILT_WET)[None, :] * 1.05, a)
    silt = Material(silt_alb, spec=0.05, gloss=8, brush=0.1)
    mats['silt'] = silt
    mats['blade'] = Material(FANG, spec=0.55, gloss=50, brush=0.02)
    mats['haftdk'] = Material(HAFT_DK, spec=0.3, gloss=24, brush=0.02)
    sc = naga_finish(P, N, parts, mats)
    sc.materials['silt'] = silt                       # the silt stays silt; only the snake dies into a husk
    sc.parts.extend(mound)
    return sc


def _fit(row, i, P):
    P['coil_sq'] = min(P['coil_sq'], 0.85)
    s = P['s']
    C = P['chest']
    if row == 'attack':
        # wind: glaive cocked back over the shoulder; strike: driven forward-down in a long lunge, blade in front
        g, dr, sp = [(C + scr(-0.36, -0.14, -0.05), sdir(-0.40, 1.0, -0.10), 0.34),
                     (C + scr(-0.36, -0.10, 0.0), sdir(-0.15, 1.0, 0.0), 0.34),
                     (C + scr(-0.42, -0.34, 0.26), sdir(0.88, 0.36, 0.20), 0.30),
                     (C + scr(-0.40, -0.26, 0.18), sdir(-0.05, 1.0, 0.10), 0.34)][i]
        P['hd_r'] = g
        P['hd_l'] = g + dr * sp
    if row == 'cast':
        P['hd_r'] = C + scr(-0.30, -0.18 + 0.05 * i, 0.15)
        P['hd_l'] = P['hd_r'] + sdir(0.12, 1.0, 0.0) * 0.36


ROWS, frames = naga_rows(neutral_pose, attack='thrust', hook=_fit)

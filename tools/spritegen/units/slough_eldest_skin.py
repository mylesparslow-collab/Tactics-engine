"""The Eldest Skin (Slough hero). Old, very large for a non-giant (2.4 m, ppm 48), a stooped body with an enormous
ragged hood and faded grey-and-bone bands, a single chartreuse ring at the throat. A skin-staff hung with a dozen
small pale skins in the right hand, a cape of many shed skins heaped over the coil behind her so she reads as a
heap of paper with a hood. Defining detail: the cape of skins."""
from _slough_common import *

UNIT_ID = 'slough_eldest_skin'
N = Naga(height=2.3, girth=1.15, tube=0.185, coil_r=0.56, loops=1.8, coil_back=0.30, hood='ragged', hood_w=1.4,
         hood_h=1.15, head_len=1.85, band_len=0.30, band_dark=0.5, band_fade=0.35, grey=0.55, accent=('neck',),
         dark=_hex('#3c4040'), light=_hex('#d9d4bc'), belly=_hex('#d6c58e'), skin=_hex('#6a6248'),
         mantle=_hex('#34383a'), hood_face=_hex('#cfc7a0'), hood_rim=_hex('#f4efdc'), lip=_hex('#efe6bd'),
         lean=0.10, tail_side=-1)
CAMERA = naga_camera(N)


def neutral_pose():
    P = naga_pose(N)
    s = P['s']
    reach(P, 'r', scr(-0.40, 1.30 * s, 0.26))
    aim(P, 'r', v3(0, 1, 0))
    reach(P, 'l', scr(0.50, 1.55 * s, 0.22))
    return P


def lying_pole(P, below, length):
    """Staff through the right hand, or (death) lying on the ground beside the coil, kept inside the frame."""
    g, d = P['hd_r'], norm(P['item_r'])
    b0, t0 = g - d * below, g + d * length
    k = P['drop']
    if k <= 0:
        return b0, t0
    b2 = scr(-0.50, 0.05, -0.10)
    t2 = b2 + E1 * 1.0
    return lerp(b0, b2, k), lerp(t0, t2, k)


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    s = P['s']
    dr = P['drop']
    # --- cape of shed skins over the coil, behind her
    rng = np.random.default_rng(11)
    c0 = P['coil_c']
    back = norm(v3(0.25, 0, -1.0))
    rt = v3(back[2], 0, -back[0])
    for ri, (R, y, n) in enumerate(((0.66, 0.30, 12), (0.54, 0.52, 10), (0.42, 0.74, 8))):
        for j in range(n):
            a = np.radians(-118 + 236 * (j + 0.5 * (ri % 2)) / n)
            out = norm(back * np.cos(a) + rt * np.sin(a))
            q = c0 + out * R * (1.0 + 0.1 * rng.uniform(-1, 1)) + v3(0, y * s, 0) * 0.9
            nrm = norm(out + v3(0, 0.35, 0))
            dn = norm(-v3(0, 1, 0) * 0.9 + out * 0.3)
            ln = 0.20 + 0.06 * rng.uniform(0, 1)
            add(Ellipsoid(q, (0.13 * s, ln * s, 0.016 * s), R_from(dn, nrm)), 'cape', 0.0)
    # --- staff hung with a dozen small skins
    butt, tip = lying_pole(P, 1.3, 0.80)
    d = norm(tip - butt)
    _shaft(add, butt, tip, 'staff', d, P, 'haft', 'fang', 'glaze')
    add(Torus(tip - d * 0.05, d, 0.07 * s, 0.014 * s), 'lash', 0.0)
    add(Sphere(tip + d * 0.03, 0.04 * s), 'glaze', 0.0)
    sw = np.sin(2 * np.pi * P['tell']) * 0.15
    sv = _side(d)
    for j in range(12):
        a = 2 * np.pi * j / 12
        o = (sv * np.cos(a) + np.cross(d, sv) * np.sin(a))
        top = tip - d * (0.06 + 0.03 * (j % 3)) * s + o * 0.05 * s
        dn = norm(v3(0, -1, 0) + o * 0.30 + E1 * sw)
        ln = (0.30 + 0.12 * ((j * 5) % 3)) * s
        if dr > 0:
            top = lerp(top, v3(top[0] * 0.6, 0.06, -0.15) + E1 * (j - 6) * 0.04, dr)
            dn = norm(lerp(dn, E1 * (1 if j % 2 else -1) + v3(0, 0.05, 0), dr))
        add(Ellipsoid(top + dn * ln * 0.5, (0.04 * s, ln * 0.5, 0.010 * s), R_from(dn, E2)), 'cape', 0.0)
    # --- free hand: fingers spread, raised as if reading
    h = P['hd_l']
    a = norm(h - P['sh_l'])
    sv2 = _side(a)
    for k in range(4):
        f = k - 1.5
        add(Capsule(h + a * 0.02, h + (a + sv2 * f * 0.40) * 0.13 * s, 0.015 * s, 0.006), 'hand', 0.0)
    # --- skin sash: pale first skin over the shoulder
    Rt = B['chest_R']
    return naga_finish(P, N, parts, {'cape': Material(lambda p, n: _arr(HUSK, len(p)) * (0.97 + 0.08 * fbm(p, 8.0, 2)[:, None])
                                                       * (0.95 + 0.05 * np.sin(p[:, 1] * 38.0)[:, None]),
                                                       spec=0.05, gloss=10, sss=0.7, brush=0.05)})


def _fit(row, i, P):
    s = P['s']
    P0 = neutral_pose()
    if row == 'cast':
        P['hd_r'] = P0['hd_r']
        P['item_r'] = v3(0, 1, 0)
        P['hd_l'] = P0['hd_l'] + v3(0, [0.1, 0.30, 0.1][i], 0.0) * s
        P['hood'] = min(P['hood'], 1.2)
    if row == 'attack':
        P['hd_r'] = P0['hd_r'] + E2 * [-0.04, 0, 0.12, 0.04][i]
        a = [-0.10, 0.0, 0.50, 0.15][i]
        P['item_r'] = norm(rot_x(a) @ v3(0, 1, 0))
        P['hood'] = min(P['hood'], 1.2)
    if row in ('idle', 'move', 'hit', 'death'):
        P['item_r'] = v3(0, 1, 0) if row != 'death' else norm(lerp(v3(0, 1, 0), E1, [0, 0.3, 1, 1][i]))
        if row != 'death':
            P['hd_r'] = P0['hd_r'] + (P['waist'] - P0['waist']) * 0.8
    P['hood'] = min(P['hood'], 1.0 if row in ('attack', 'cast') else 1.1)


ROWS, frames = naga_rows(neutral_pose, attack='bite', cast='raise', hook=_fit)

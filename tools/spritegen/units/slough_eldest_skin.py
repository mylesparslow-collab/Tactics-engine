"""The Eldest Skin (Slough hero). The oldest of the serpent-folk, shed ninety times; 2.35 m, ppm 48. The living snake
reads first: a crisp banded coil (old grey-black and bone), a dark scaled torso with a muted gold front, a huge ragged
dark hood with a pale rim, and a bright chartreuse ring at the throat. Her old skins are worn as a layered cape of
long pale strips hanging from behind the shoulders down to the coil, framing (never covering) the dark body, with a
short second tier over the upper arms. Signature prop: a tall crook-staff in her right hand hung with three long
skins, a thin gold ring on the oldest. Left hand raised, fingers spread. Defining detail: the skin cape and staff."""
from _slough_common import *

UNIT_ID = 'slough_eldest_skin'
N = Naga(palette='violet', trim=LACQUER_RED, height=2.32, girth=1.12, tube=0.19, coil_r=0.56, loops=1.8, coil_back=0.30, hood='ragged',
         hood_w=1.35, hood_h=1.25, hood_mark='ocelli', hood_mark_col=_hex('#e8e2c8'), head_len=1.35, band_len=0.24,
         band_dark=0.32, band_fade=0.0, grey=0.0, accent=(), lean=0.08, tail_side=-1)
CAMERA = naga_camera(N)

GOLD_HERO = _hex('#e0b84a')
SKIN_OLD = _hex('#eee7cc')
SKIN_OLDER = _hex('#d9d0ae')

# cape strips behind the shoulders: (x across the back -1..1, length m, width m, outward splay, tier, shade)
CAPE = ((-1.20, 0.96, 0.22, 0.80, 0, 0), (-0.60, 1.14, 0.24, 0.70, 0, 1), (0.10, 1.05, 0.24, 0.20, 0, 0),
        (0.70, 1.10, 0.22, 0.75, 0, 1), (1.20, 0.92, 0.20, 0.95, 0, 0),
        (-1.00, 0.58, 0.20, 0.55, 1, 1), (1.00, 0.52, 0.19, 0.55, 1, 1))
STAFF_SKINS = ((-0.17, 0.78, 0.12), (0.03, 0.98, 0.14), (0.20, 0.66, 0.11))


def neutral_pose():
    P = naga_pose(N)
    s = P['s']
    reach(P, 'r', scr(-0.46, 1.22 * s, 0.24))
    aim(P, 'r', v3(0, 1, 0))
    reach(P, 'l', scr(0.46, 1.60 * s, 0.20))
    return P


def lying_pole(P, below, length):
    """Staff through the right hand, or (death) lying on the ground beside the coil, kept inside the frame."""
    g, d = P['hd_r'], norm(P['item_r'])
    b0, t0 = g - d * below, g + d * length
    k = P['drop']
    if k <= 0:
        return b0, t0
    b2 = scr(-0.48, 0.05, -0.12)
    t2 = b2 + E1 * 0.95
    return lerp(b0, b2, k), lerp(t0, t2, k)


def strip(add, top, dn, out, ln, w, mat, sway=0.0):
    """A hanging shed skin: two overlapping flat ribbons with a slight bend, ragged narrower lower end."""
    fl = norm(np.cross(dn, out))                      # ribbon face normal
    mid = top + dn * ln * 0.5
    d2 = norm(dn + out * (0.12 + sway) + fl * 0.05)
    a_c = top + dn * ln * 0.27
    b_c = mid + d2 * ln * 0.23
    add(Ellipsoid(a_c, (w * 0.5, ln * 0.29, 0.012), R_from(dn, fl)), mat, 0.01)
    add(Ellipsoid(b_c, (w * 0.40, ln * 0.27, 0.011), R_from(d2, fl)), mat, 0.01)
    return b_c + d2 * ln * 0.25


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    s = P['s']
    dr = P['drop']
    Rt = B['chest_R']
    rt, up, fw = Rt[:, 0], Rt[:, 1], Rt[:, 2]
    C = P['chest']
    sw = np.sin(2 * np.pi * P['tell']) * 0.06 + 0.03 * P['breathe']
    # --- cape of old skins: long strips from behind the shoulders, a short tier over the upper arms
    fall = P['fall'] + dr
    for j, (x, ln, w, spl, tier, shade) in enumerate(CAPE):
        mat = 'skin_a' if shade == 0 else 'skin_b'
        if tier == 0:
            top = C + (rt * x * 0.19 + up * 0.15 - fw * (0.08 + 0.02 * abs(x))) * s
            dn = norm(-up * 1.0 - fw * 0.30 + rt * x * spl * 0.45)
        else:      # short skins draped over the shoulder caps, in front of the long ones
            top = C + (rt * x * 0.21 + up * 0.17 + fw * 0.04) * s
            dn = norm(-up * 1.0 + fw * 0.05 + rt * np.sign(x) * spl)
        out = rt * np.sign(x) if abs(x) > 0.05 else -fw
        L = ln * s * (1 - 0.55 * min(dr, 1.0))
        if dr > 0:   # death: the strips spill flat over the coil
            dn = norm(lerp(dn, rt * np.sign(x + 1e-3) * 0.45 - fw * 0.6 + v3(0, -0.25, 0), min(dr, 1.0)))
        strip(add, top, dn, out, L, w * s * 1.05, mat, sway=sw * (1 if j % 2 else -1))
    # --- the crook-staff hung with three long skins
    butt, tip = lying_pole(P, 1.20, 0.90)
    d = norm(tip - butt)
    add(Capsule(butt, tip, 0.026 * s), 'staffwood', 0.0)
    sv = norm(E1 - d * (E1 @ d))
    hook_c = tip + d * 0.07 * s - sv * 0.07 * s
    ax = norm(np.cross(d, sv))
    add(Torus(hook_c, ax, 0.075 * s, 0.022 * s), 'staffwood', 0.0)               # the crook
    add(Capsule(hook_c - sv * 0.075 * s, hook_c - sv * 0.075 * s - d * 0.07 * s, 0.022 * s, 0.012 * s), 'staffwood', 0.0)
    bar = tip - d * 0.10 * s
    add(Capsule(bar - sv * 0.22 * s, bar + sv * 0.22 * s, 0.020 * s), 'staffwood', 0.0)
    add(Capsule(bar - d * 0.05 * s, bar + d * 0.02 * s, 0.034 * s), 'glaze', 0.0)  # chartreuse knot
    for j, (off, ln, w) in enumerate(STAFF_SKINS):
        top = bar + sv * off * s * 1.2
        dn = norm(v3(0, -1, 0) + sv * (sw * 1.5 + 0.12 * off))
        L = ln * s
        if dr > 0:
            dn = norm(lerp(dn, E1 * (1 if off >= 0 else -1) + v3(0, 0.05, 0), dr))
            top = lerp(top, scr(-0.20 + off * 1.2, 0.05, -0.14), dr)
            L = L * (1 - 0.6 * dr)
        strip(add, top, dn, E1, L, w * s, 'skin_a' if j != 1 else 'skin_b', sway=0.0)
        add(Capsule(top - dn * 0.01, top + dn * 0.05 * s, 0.017 * s), 'glaze' if j != 1 else 'goldring', 0.0)
    add(Torus(bar + sv * 0.02 * s + v3(0, -0.07, 0) * s, v3(0, 1, 0), 0.05 * s, 0.010 * s), 'goldring', 0.0)
    # --- bright chartreuse throat ring
    nk0 = C + up * 0.15 * s
    hd = P['head'] - up * 0.05 * s
    ring_c = lerp(nk0, hd, 0.42)
    add(Torus(ring_c, norm(hd - nk0), 0.090 * s, 0.036 * s), 'throatring', 0.0)
    # --- free hand raised, fingers spread
    h = P['hd_l']
    a = norm(h - P['sh_l'])
    sv2 = _side(a)
    for k in range(4):
        f = k - 1.5
        add(Capsule(h + a * 0.02, h + (a + sv2 * f * 0.40) * 0.13 * s, 0.016 * s, 0.006), 'hand', 0.0)

    def skin_alb(base):
        def fn(p, n):
            a = _arr(base, len(p)) * (0.95 + 0.08 * fbm(p, 9.0, 2)[:, None])
            ghost = np.mod(p[:, 1] / 0.20 + 0.3 * p[:, 0], 1.0) < 0.30
            return np.where(ghost[:, None], a * 0.82, a)
        return fn
    glow_k = 0.16 * (1 - P['end'])            # thin old skin lets the light through: stays pale even in shadow
    mats = {'skin_a': Material(skin_alb(SKIN_OLD), spec=0.05, gloss=10, sss=0.9, brush=0.04,
                               emissive=tuple(np.array(SKIN_OLD) * glow_k)),
            'skin_b': Material(skin_alb(SKIN_OLDER), spec=0.05, gloss=10, sss=0.9, brush=0.04,
                               emissive=tuple(np.array(SKIN_OLDER) * glow_k)),
            'staffwood': Material(_hex('#4a3b2a'), spec=0.2, gloss=20, brush=0.05),
            'goldring': Material(GOLD_HERO, spec=0.9, gloss=60, metal=0.7),
            'throatring': Material(CHART, spec=0.7, gloss=50, emissive=tuple(np.array(CHART) * 0.55 * max(P['glow'], 0.6) * (1 - P['end'])))}
    return naga_finish(P, N, parts, mats)


def _fit(row, i, P):
    s = P['s']
    P0 = neutral_pose()
    if row == 'cast':
        P['hd_r'] = P0['hd_r']
        P['item_r'] = v3(0, 1, 0)
        P['hd_l'] = P0['hd_l'] + v3(0, [0.1, 0.24, 0.1][i], 0.0) * s
        P['hood'] = min(P['hood'], 1.15)
        slide(P, v3(0, -0.07, 0) * s)
    if row == 'attack':
        P['hd_r'] = P0['hd_r'] + E2 * [-0.04, 0, 0.12, 0.04][i]
        a = [-0.10, 0.0, 0.40, 0.15][i]
        P['item_r'] = norm(rot_x(a) @ v3(0, 1, 0))
        P['hood'] = min(P['hood'], 1.25)
        if i == 2:
            slide(P, -E1 * 0.10 * s - E2 * 0.04 * s)
        if i >= 1:               # the ragged hood is huge: the bite stays inside the frame
            P['head'] = P['head'] - E1 * 0.12 * s
    if row in ('idle', 'move', 'hit', 'death'):
        P['item_r'] = v3(0, 1, 0) if row != 'death' else norm(lerp(v3(0, 1, 0), E1, [0, 0.3, 1, 1][i]))
        if row != 'death':
            P['hd_r'] = P0['hd_r'] + (P['waist'] - P0['waist']) * 0.8
    P['hood'] = min(P['hood'], 1.1 if row in ('attack', 'cast') else 1.15)


ROWS, frames = naga_rows(neutral_pose, attack='bite', cast='raise', hook=_fit)

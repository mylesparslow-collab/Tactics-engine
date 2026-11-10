"""Yellowbelly Matriarch (Slough rare, venom burst). Big heavy brood-mother reared to 2.3 m, black back and a
whole gold front, a girdle of small pale first skins hanging round her waist. No weapon: both hands forward with
clawed fingers open, mouth open on two big fangs that glow with venom. Defining detail: the gold front + fanged mouth."""
from _slough_common import *

UNIT_ID = 'slough_yellowbelly_matriarch'
N = Naga(height=2.3, girth=1.25, tube=0.215, coil_r=0.56, loops=1.7, coil_back=0.28, hood='broad', hood_w=1.45,
         hood_h=1.25, head_len=1.7, band_len=0.30, band_dark=0.58, accent=(), body_r=0.18,
         skin=_hex('#b08a34'), belly=_hex('#ecb83e'), mantle=_hex('#1e2124'), hood_face=_hex('#e2c565'),
         hood_rim=_hex('#f2ecd0'), lip=_hex('#f0d27a'), tail_side=-1)
CAMERA = naga_camera(N)


def neutral_pose():
    P = naga_pose(N)
    s = P['s']
    reach(P, 'r', scr(-0.52, 1.30 * s, 0.50))
    reach(P, 'l', scr(0.50, 1.36 * s, 0.34))
    P['jaw'] = 0.55
    P['venom'] = 0.45
    return P


def claws(add, P, sd, n=3, L=0.10):
    s = P['s']
    d = norm(P['hd_' + sd] - P['sh_' + sd])
    sv = _side(d)
    up = norm(np.cross(sv, d))
    for k in range(n):
        f = (k - (n - 1) / 2)
        a = P['hd_' + sd] + d * 0.03 * s + sv * f * 0.035 * s
        b = a + (d + sv * f * 0.45) * L * s
        add(Capsule(a, b, 0.017 * s, 0.004), 'bone', 0.0)


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    s = P['s']
    g = N.girth
    Rt = B['chest_R']
    up, fw, rt = Rt[:, 1], Rt[:, 2], Rt[:, 0]
    W = P['waist']
    # girdle of first skins
    add(Torus(W + up * 0.01 * s, up, 0.17 * g * s, 0.016 * s), 'lash', 0.0)
    for row in range(2):
        n = 11
        for j in range(n):
            a = np.radians(-135 + 270 * (j + 0.5 * row) / n)
            rx, rz = 0.175 * g * s, 0.135 * g * s
            nrm = norm(rt * np.sin(a) / rx + fw * np.cos(a) / rz)
            q = W + rt * np.sin(a) * rx + fw * np.cos(a) * rz - up * (0.02 + 0.06 * row) * s
            R = R_from(-up, nrm)
            add(Ellipsoid(q + nrm * 0.02 * s - up * 0.075 * s, (0.055 * s, 0.115 * s, 0.016 * s), R_from(up, nrm)), 'husk', 0.0)
    for sd in ('r', 'l'):
        claws(add, P, sd)
    sp = P['spit']

    def world(a2):
        if sp > 0.25:
            F = B['head']
            d = norm(F.d((0, -0.15, 1.0)) + v3(0, 0, 0.15))
            spit_stream(a2, P, B['mouth'] + d * 0.04, d, length=0.5 * sp, n=6)
        if P['venom'] > 0.5:
            venom_drip(a2, P, B['fang_tips'][0], 0.5 * P['venom'])
    return naga_finish(P, N, parts, world=world)


ROWS, frames = naga_rows(neutral_pose, attack='bite', cast='spit')

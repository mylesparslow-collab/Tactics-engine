"""Shell-Broker (Hermitage champion, support). A pony-sized BARE crab (pale spiral tail showing) harnessed with tar
rope to a net-sledge hauling its stock: two barrels and a sheet of rust plate under three bands of tar net. Pose:
leaning forward into the traces, the big claw raised to haggle. ~1.4 m crab, sledge trails behind to the upper left.
Defining detail: the sledge of stock (three big objects only)."""
from _hermitage_common import *

UNIT_ID = 'hermitage_shell_broker'
SIZE = 1.10
CAMERA = Camera(ppm=48)
YAW = 0.12
BARE = Bare(h=0.40, yaw=YAW, leg_len=1.0, leg_r=1.05, z0=-0.30, x0=0.50, big=1.40, small=0.70, eye_len=0.32,
            eye_bead=0.068, span=0.40, tail=dict(size=1.0, thick=(0.15, 0.05), side=-0.6, drop=0.02))
YS = 0.02               # the sledge trails along its own heading, a little off the crab's


def _wood_alb(base):
    def fn(p, n):
        a = np.array(base, dtype=np.float64)[None, :].repeat(len(p), 0)
        v = fbm(p * v3(1, 6, 1), 7.0, 2)[:, None]
        return a * (0.80 + 0.35 * v)
    return fn


def _stave_alb(p, n):
    a = np.array(OAK, dtype=np.float64)[None, :].repeat(len(p), 0)
    ang = np.arctan2(p[:, 0] - 0.0, p[:, 2])
    st = np.abs(((ang / (2 * np.pi) * 12) % 1.0) - 0.5) > 0.44
    a = np.where(st[:, None], a * 0.6, a)
    v = fbm(p, 8.0, 2)[:, None]
    return a * (0.85 + 0.3 * v)


def _plate_alb(p, n):
    a = np.array(_hex('#6c4a38'), dtype=np.float64)[None, :].repeat(len(p), 0)
    b = (vnoise(p, 9.0) > 0.58)[:, None]
    a = np.where(b, np.array(ORANGE)[None, :] * 0.78, a)
    return a * (0.85 + 0.3 * fbm(p, 6.0, 2)[:, None])


MATS = {
    'sled': Material(_wood_alb(_hex('#6b5744')), spec=0.08, gloss=10, brush=0.1),
    'stave': Material(_stave_alb, spec=0.12, gloss=12, brush=0.08),
    'hoop': Material(_hex('#7a4a2a'), spec=0.4, gloss=24, metal=0.4),
    'plate': Material(_plate_alb, spec=0.4, gloss=24, metal=0.4, brush=0.05),
    'net': Material(_hex('#2a2226'), spec=0.05, gloss=8, brush=0.06),
    'rope': Material(_hex('#b99a62'), spec=0.05, gloss=8, brush=0.1),
}


def sledge(add, P, D):
    """Everything in the sledge frame D (origin at the crab's ground spot, -z = back along the trail)."""
    s = 1.0
    bob = 0.015 * np.sin(2 * np.pi * P['tell'] * 2) * (1 if P['stride'] != 0 or P['lift_a'] or P['lift_b'] else 0)
    for sx in (-1, 1):
        pts = [v3(sx * 0.27, 0.15 + bob, -0.55), v3(sx * 0.27, 0.08, -0.66), v3(sx * 0.27, 0.045, -0.9),
               v3(sx * 0.27, 0.045, -1.2), v3(sx * 0.27, 0.05, -1.34)]
        for a, b in zip(pts[:-1], pts[1:]):
            D.put(add, Capsule(a, b, 0.038), 'sled')
    for z in (-0.62, -0.95, -1.28):
        D.box(add, (0, 0.105, z), (0.30, 0.022, 0.04), 0.008, 'sled')
    D.box(add, (0, 0.14, -0.95), (0.29, 0.016, 0.40), 0.008, 'sled')
    # stock 1: an upright tarred barrel, back left
    c = v3(-0.08, 0.16, -1.02)
    D.cyl(add, tuple(c), tuple(c + v3(0, 0.40, 0)), 0.16, 'stave', 0.0, 0.03)
    D.ell(add, tuple(c + v3(0, 0.20, 0)), (0.18, 0.21, 0.18), 'stave', 0.0)
    for y in (0.06, 0.34):
        D.put(add, Torus(c + v3(0, y, 0), v3(0, 1, 0), 0.16 + 0.012 * (1 - abs(y - 0.2) * 3), 0.020), 'hoop')
    D.cyl(add, tuple(c + v3(0, 0.395, 0)), tuple(c + v3(0, 0.415, 0)), 0.115, 'stave', 0.0, 0.008)
    # stock 2: a barrel lying across the front of the load
    c2 = v3(0.04, 0.15 + 0.15, -0.70)
    R2 = rot_y(0.35) @ rot_z(np.pi / 2)
    D.ell(add, tuple(c2), (0.15, 0.17, 0.15), 'stave', 0.0, R=R2)
    D.put(add, Torus(c2 + rot_y(0.35) @ v3(0.13, 0, 0), rot_y(0.35) @ v3(1, 0, 0), 0.14, 0.02), 'hoop')
    D.put(add, Torus(c2 + rot_y(0.35) @ v3(-0.13, 0, 0), rot_y(0.35) @ v3(1, 0, 0), 0.14, 0.02), 'hoop')
    # stock 3: a sheet of iron plate leaning against the barrel, three big bolts
    Rp = rot_y(0.12) @ rot_x(-0.32)
    D.box(add, (0.12, 0.40, -1.23), (0.27, 0.25, 0.022), 0.012, 'plate', R=Rp)
    for (px, py) in ((-0.13, 0.15), (0.13, 0.18), (0.0, -0.16)):
        D.sph(add, tuple(v3(0.12, 0.40, -1.23) + Rp @ v3(px, py, 0.034)), 0.034, 'hoop')
    # net: three thick tar bands over the load, lashed at the runners
    for z, hh in ((-0.78, 0.30), (-0.97, 0.52), (-1.14, 0.50)):
        pts = [v3(-0.30, 0.12, z), v3(-0.20, 0.12 + hh * 0.8, z), v3(0.0, 0.14 + hh, z), v3(0.22, 0.12 + hh * 0.7, z),
               v3(0.30, 0.12, z)]
        for a, b in zip(pts[:-1], pts[1:]):
            D.put(add, Capsule(a, b, 0.016), 'net')
    D.put(add, Capsule(v3(-0.28, 0.12, -0.7), v3(0.24, 0.12, -1.26), 0.014), 'net')
    return D


def build(P):
    s = SIZE
    b = BARE
    C = bare_frame(P, b, s)

    def world(add):
        # the sledge frame: crab ground spot, own heading
        Ry = rot_y(b.yaw + P['yaw'] + YS)
        o = v3(b.x0 + P['slide'], 0, b.z0 - P['recoil'])
        D = Frame(o, Ry @ rot_x(0.05 * P['flip']), 0.86)
        sledge(add, P, D)
        # harness: two traces from the shoulders to the sledge bar, a chest strap over the carapace
        for sx in (-1, 1):
            a = C.p((sx * 0.20, -0.04, 0.04))
            bb = D.p((sx * 0.27, 0.13, -0.58))
            mid = (a + bb) / 2 + v3(0, -0.03, 0)
            add(Capsule(a, mid, 0.016, 0.014), 'net', 0.0)
            add(Capsule(mid, bb, 0.014, 0.016), 'net', 0.0)
        pts = [C.p((-0.20, -0.04, 0.05)), C.p((-0.12, 0.13, 0.04)), C.p((0.12, 0.13, 0.04)), C.p((0.20, -0.04, 0.05))]
        for a, c in zip(pts[:-1], pts[1:]):
            add(Capsule(a, c, 0.018 * s, 0.018 * s), 'rope', 0.0)
    return bare(P, s, b, mats=MATS, world=world)


def neutral_pose():
    return hermit_pose(raise_=1.15, lean=0.10, open=0.5)


def _rows(R):
    for i, (P, o) in enumerate(R['idle']):          # haggling: the claw bobs and opens
        P['raise_'] = [1.15, 0.8, 1.25, 0.9][i]
        P['open'] = [0.6, 0.15, 0.8, 0.3][i]
        P['curl'] *= 0.5
    for P, o in R['move']:
        P['lean'] += 0.06
        P['raise_'] = 0.9
    for row in ('attack', 'hit', 'cast', 'death'):
        for P, o in R[row]:
            P['snap'] *= 0.7
    for P, o in R['death']:
        P['raise_'] = max(P['raise_'], 0.0) * 0.5
    return R


ROWS, frames = hermit_rows(neutral_pose, 'bare', extra=_rows)

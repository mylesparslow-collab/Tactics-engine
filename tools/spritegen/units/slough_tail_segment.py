"""Coil (Slough token: tail segment of the long giants Ringwall, Hundredcoat, Kesh). One tile's worth of fat
krait body lying in a loop on the ground: it comes in from the upper-left tile edge, swings round in front and
leaves by the upper-right edge, so whatever direction the tail runs, the ends of two or three segments on
neighbouring tiles behind a giant line up into one banded body. Black-and-bone with the gold underside showing.
The engine always draws segments unmirrored and 150/112 larger, so ppm is 44 / 1.34 (giant scale).
Idle: a slow peristaltic ripple. Hit: a jolt and flakes. Death: dulls to an empty flat skin."""
from _slough_common import *

UNIT_ID = 'slough_tail_segment'
CAMERA = Camera(ppm=33.0)
N = Naga(tube=0.21, band_len=0.36, accent=())
R0 = 0.20


def _ground(dx, dy):
    """Ground point that projects dx px right and dy px down from the anchor (sprite px at CAMERA.ppm)."""
    ppm = CAMERA.ppm
    return E1 * (dx / ppm) + E2 * (dy / (0.5 * ppm))


def neutral_pose():
    return dict(s=1.0, tell=0.0, shake=0.0, flakes=0.0, end=0.0, flat=0.0, gone=0.0, band_rot=v3(1.0, 0, 0))


def path(P):
    L = _ground(-25, -12.5)
    Rr = _ground(25, -12.5)
    ctrl = [L + _ground(-6, -3), L, _ground(-17, 0.5), _ground(0, 3.0), _ground(17, 0.5), Rr, Rr + _ground(6, -3)]
    pts = spline(ctrl, 40)
    out = []
    for i, q in enumerate(pts):
        t = i / (len(pts) - 1)
        y = R0 * 0.88 + 0.06 * np.sin(np.pi * t) ** 2 - 0.30 * (1 - smooth(0.0, 0.22, min(t, 1 - t)))
        out.append(v3(q[0], y, q[2]))
    return np.array(out)


def build(P):
    parts, add = new_parts()
    pts = path(P)
    sh = P['shake']
    pts = pts + v3(0.03 * sh, 0, 0)
    seglen = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    sv = np.concatenate([[0], np.cumsum(seglen)])
    n = len(pts)
    ph = P['tell']
    rad = []
    for i in range(n):
        t = i / (n - 1)
        rip = 1 + 0.035 * np.exp(-((t - (0.15 + 0.7 * ph)) / 0.12) ** 2)
        taper = 0.86 + 0.14 * np.sin(np.pi * min(1, t * 1.2 + 0.0)) if t < 0.1 or t > 0.9 else 1.0
        rad.append(R0 * rip * (0.9 + 0.1 * np.sin(np.pi * t)))
    for i in range(n - 1):
        add(Capsule(pts[i], pts[i + 1], rad[i], rad[i + 1]), 'band', 0.04)
    bel = np.array([v3(0, -1, 0)] * n)
    Pm = dict(band_rot=P['band_rot'])
    mats = {'band': Material(band_albedo(N, pts, sv, bel, Pm, []), spec=0.45, gloss=46, brush=0.03),
            'flake': Material(HUSK, spec=0.1, sss=0.5)}
    if P['flakes'] > 0.02:
        rng = np.random.default_rng(3)
        for i in range(4):
            q = pts[rng.integers(5, n - 5)]
            o = q + v3(rng.uniform(-0.2, 0.2), 0.25 + 0.25 * P['flakes'] * rng.uniform(0.5, 1), rng.uniform(-0.2, 0.2))
            add(Ellipsoid(o, (0.04, 0.01, 0.03), rot_y(rng.uniform(0, 3)) @ rot_x(rng.uniform(-1, 1))), 'flake', 0.0)
    fl = P['flat']
    if fl > 0:
        parts[:] = [Part(Squash(pt.prim, 1 - 0.7 * fl, 1 + 0.05 * fl, (0, 0, 0)), pt.mat, pt.k) for pt in parts]
    mats = husked(mats, P['end'])
    return Scene(parts=parts, materials=mats, lights=[], ground_clip=True)


ROWS, frames = token_rows(neutral_pose)

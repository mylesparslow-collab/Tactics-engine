"""Lifeboat Skimmer (Hermitage mobile). A pony-sized crab wearing an upturned clinker lifeboat, keel up like a fin: three
broad lapped strakes of weathered white and blue-grey paint, the hull longer than the crab, legs out under the gunwales
and the big claw and eyestalks out past the bow. Low and long. ~1.4 m. Defining detail: the keel line on top."""
from _hermitage_common import *
from _hermitage_common import _arr

UNIT_ID = 'hermitage_lifeboat_skimmer'
SIZE = 'medium'
CAMERA = size_camera(SIZE)
L, B, D = 0.62, 0.34, 0.34          # half length, half beam, keel height over the gunwale plane
WHITE = _hex('#d6d3c6')
BLUEG = _hex('#6f8798')


def _y0(z):
    return -0.15 * (z / L) ** 2


def _dims(z):
    t = np.clip(z / L, -1, 1)
    bow = np.where(t > 0, 0.82, 1.0)                    # a sharper bow
    k = np.clip(1 - np.abs(t) ** (1.7 * bow + 0.3), 0.0, 1)
    return np.maximum(B * k ** 0.6, 0.03), np.maximum(D * k ** 0.5, 0.03)


def _hull(wall, drop):
    def f(p):
        z = p[:, 2]
        b, d = _dims(z)
        y = p[:, 1] - _y0(z)
        u, v = p[:, 0] / (b - wall), y / (d - wall)
        e = (np.sqrt(u ** 2 + v ** 2) - 1.0) * np.minimum(b - wall, d - wall) * 0.8
        if wall == 0:
            phi = np.arctan2(np.abs(p[:, 0]), np.maximum(y, 1e-3)) / (np.pi / 2)
            saw = (np.clip(phi, 0, 0.999) * 3.0) % 1.0
            e = e - 0.022 * saw                         # clinker laps: each strake overhangs the one below
        return np.maximum(e, np.maximum(-(y + drop), np.abs(z) - L))
    return Func(f, (0, 0, 0), L + 0.4)


def boat_shell():
    def build(add, P, F):
        F.put(add, Subtract(_hull(0.0, 0.0), _hull(0.05, 0.12)), 'paint')
        # the keel line on top, standing up like a fin, and stem and stern posts
        kp, kr = [], []
        for z in np.linspace(-0.56, 0.52, 11):
            b, d = _dims(np.array([z]))
            kp.append(F.p((0, _y0(z) + float(d[0]) + 0.012, z)))
            kr.append(0.036 * F.s)
        tube(add, kp, kr, 'keel', 0.01)
        zb = 0.54
        F.cap(add, (0, _y0(zb) + 0.10, zb), (0, _y0(zb) + 0.0, zb + 0.13), 0.04, 0.03, 'keel')
        F.cap(add, (0, _y0(-0.55) + 0.10, -0.55), (0, _y0(-0.55) + 0.08, -0.69), 0.04, 0.03, 'keel')
        # one rope grab-line looped along the gunwale at the stern (solid band, not a row of things)
        F.put(add, Torus(v3(0.0, -0.02, -0.40), v3(0, 0, 1), 0.27, 0.022), 'rope0')

        def alb(q, n):
            z = q[:, 2]
            b, d = _dims(z)
            y = q[:, 1] - _y0(z)
            phi = np.arctan2(np.abs(q[:, 0]), np.maximum(y, 1e-3)) / (np.pi / 2)
            strake = np.clip((phi * 3.0).astype(int), 0, 2)
            a = np.where((strake % 2 == 0)[:, None], _arr(BLUEG, len(q)), _arr(WHITE, len(q)))
            frac = (np.clip(phi, 0, 0.999) * 3.0) % 1.0
            a = np.where((frac > 0.88)[:, None], a * 0.62, a)                 # shadowed lap line
            w = fbm(q * v3(1, 1, 0.5), 5.0, 2)[:, None]
            flake = (vnoise(q, 8.0) > 0.74)[:, None]                          # flaked paint down to grey wood
            a = np.where(flake, _arr(_hex('#6e6458'), len(q)), a * (0.84 + 0.3 * w))
            inside = (np.sqrt((q[:, 0] / np.maximum(b - 0.03, 0.02)) ** 2 + (y / np.maximum(d - 0.03, 0.02)) ** 2) < 1.0)
            return np.where(inside[:, None], np.array(TAR)[None, :] * 0.9, a)
        return {'paint': Material(local_albedo(F, alb), spec=0.22, gloss=18, brush=0.08),
                'keel': Material(_hex('#3f4a55'), spec=0.2, gloss=14, brush=0.06),
                'rope0': Material(_hex('#a8834e'), spec=0.05, gloss=8, brush=0.1)}
    return build


SHELL = Shell(
    build=boat_shell(),
    ride=0.72, tilt=-0.20, crab_at=(0, -0.28, 0.24), crab_pitch=0.0, z0=-0.20, x0=0.04, yaw=0.30,
    feet=((-0.40, 0.34), (0.42, 0.32), (-0.48, -0.28), (0.48, -0.32)),
    leg_roots=((-0.20, -0.30, 0.28), (0.20, -0.30, 0.28), (-0.28, -0.28, -0.08), (0.28, -0.28, -0.08)),
    eyes=(((-0.10, -0.28, 0.48), (-0.20, 0.55, 0.85), 0.50), ((0.10, -0.28, 0.48), (0.20, 0.55, 0.85), 0.50)),
    eye_bead=0.058, big=1.25, small=0.55, side_r=0.42, tip_angle=1.30, lie=0.0, leg_len=1.12, leg_r=1.1,
    guard=((0.12, 0.02, 0.40), (-0.45, 0.30, 0.85)))


def neutral_pose():
    return hermit_pose(open=0.3)


def build(P):
    return shelled(P, SIZE, SHELL)


def _rows(R):
    # move = skid: the boat glides, legs paddling off the ground
    for i, (P, o) in enumerate(R['move']):
        P['lift_a'] = [0.7, 0.3, 0.7, 0.3][i]
        P['lift_b'] = [0.3, 0.7, 0.3, 0.7][i]
        P['stride'] *= 0.6
        P['bob'] = [0.03, 0.05, 0.03, 0.05][i]
        P['lean'] = -0.05
    return R


ROWS, frames = hermit_rows(neutral_pose, 'shell', extra=_rows)

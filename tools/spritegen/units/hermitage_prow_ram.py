"""Prow Ram (Hermitage champion, melee charger). A horse-sized crab wearing the bow section of a wrecked ship: grey
timber hull in three broad strakes with a faded paint band, a flat deck with a hatch the eyestalks climb out of, an
iron-shod ram low on the cutwater and a carved figurehead (a woman's bust, arms crossed, blank white eyes) high on
the stem. Head-down charge stance, the big claw out under the ram. ~1.8 m, ppm 48.
Defining detail: the figurehead's stare."""
from _hermitage_common import *

UNIT_ID = 'hermitage_prow_ram'
SIZE = 'large'
CAMERA = size_camera(SIZE)

HL = 0.52          # half length of the bow section (stern cut at -z, stem at +z)
W0 = 0.33          # half beam at the cut stern
HK = 0.74          # depth of the hull below the deck at the stern
CUT = 0.56         # the planking is smashed out below this depth under the deck


def _deck_y(u):
    return 0.18 + 0.42 * u ** 2.6


def _half_w(u):
    return W0 * (1.0 - u ** 1.45) + 0.03


def _depth(u):
    return HK * (1.0 - 0.45 * u ** 2.0)


def _hull_d(p):
    z, x, y = p[:, 2], p[:, 0], p[:, 1]
    u = np.clip((z + HL) / (2 * HL), 0, 1)
    w, yd, hk = _half_w(u), _deck_y(u), _depth(u)
    e = np.sqrt((x / w) ** 2 + ((y - yd) / hk) ** 2)
    d = (e - 1.0) * np.minimum(w, hk) * 0.8
    d = np.maximum(d, y - yd)
    d = np.maximum(d, np.abs(z) - HL - 0.02 + 0.02)
    return d, yd, hk


def prow_shell():
    def build(add, P, F):
        def outer(p):
            d, yd, hk = _hull_d(p)
            return np.maximum(d, (yd - CUT) - p[:, 1])

        def inner(p):
            d, yd, hk = _hull_d(p)
            d = d + 0.05
            d = np.maximum(d, p[:, 1] - (yd - 0.05))
            return np.maximum(d, -(p[:, 2] + HL) - 0.2)      # the stern is open, the cut runs through

        def shell(p):
            o = outer(p)
            i = inner(p)
            # hatch in the deck
            r = np.sqrt((p[:, 0]) ** 2 + (p[:, 2] - 0.18) ** 2) - 0.12
            return np.maximum(np.maximum(o, -i), -r + 0.0 * o)
        F.put(add, Func(shell, (0, 0.1, 0), 1.2), 'timber')
        # hatch coaming
        F.put(add, Torus(v3(0, _deck_y((0.18 + HL) / (2 * HL)) + 0.005, 0.18), v3(0, 1, 0), 0.125, 0.026), 'timberd')
        # solid gunwale rail band along the sheer: a rounded capsule line each side
        for sx in (-1, 1):
            pts = []
            for u in np.linspace(0.0, 0.93, 7):
                pts.append(v3(sx * (_half_w(u) - 0.01), _deck_y(u) + 0.01, -HL + 2 * HL * u))
            for a, b in zip(pts[:-1], pts[1:]):
                F.put(add, Capsule(a, b, 0.028), 'timberd')
        # stem post, a heavy timber curve up to the figurehead
        sz = HL - 0.03
        F.put(add, Capsule(v3(0, _deck_y(1.0) - 0.30, sz + 0.02), v3(0, _deck_y(1.0) + 0.30, sz + 0.14), 0.052, 0.04),
              'timberd')
        # iron-shod ram: a tapered snout low on the cutwater, two collars
        ry = _deck_y(1.0) - 0.30
        F.put(add, Capsule(v3(0, ry + 0.02, HL - 0.35), v3(0, ry - 0.04, HL + 0.40), 0.11, 0.022), 'ram')
        F.sph(add, (0, ry - 0.04, HL + 0.41), 0.034, 'ramtip')
        F.put(add, Torus(v3(0, ry + 0.00, HL - 0.20), v3(0, 0.05, 1), 0.08, 0.028), 'ramband')
        F.put(add, Torus(v3(0, ry - 0.01, HL - 0.02), v3(0, 0.05, 1), 0.062, 0.024), 'ramband')
        # three big rust bosses on the hull sides
        for sx, uu, vv in ((-1, 0.45, -0.22), (1, 0.30, -0.24), (-1, 0.12, -0.20)):
            z = -HL + 2 * HL * uu
            w, yd, hk = _half_w(uu), _deck_y(uu), _depth(uu)
            a = np.arcsin(-vv)
            F.sph(add, (sx * w * np.cos(a) * 1.0, yd + vv * hk, z), 0.032, 'ramband')
        for sx in (-1, 1):
            uu = 0.78
            w, yd, hk = _half_w(uu), _deck_y(uu), _depth(uu)
            c = v3(sx * w * 0.93, yd - 0.17 * hk, -HL + 2 * HL * uu)
            F.put(add, Torus(c, v3(sx, 0.0, 0.5), 0.045, 0.014), 'ramband')
            F.put(add, Cylinder(c - v3(sx, 0, 0.5) * 0.02, c + v3(sx, 0, 0.5) * 0.02, 0.04, 0.0), 'dark')
        # figurehead: a bust leaning out over the stem, arms crossed, blank stare
        G = F.child((0, _deck_y(1.0) + 0.22, HL + 0.12), rot_y(-0.75) @ rot_x(0.12), 1.45)
        fy, fz = 0.0, 0.0
        G.ell(add, (0, fy + 0.04, fz - 0.02), (0.115, 0.15, 0.09), 'gown', 0.03, R=rot_x(0.35))
        G.ell(add, (0, fy - 0.04, fz - 0.06), (0.10, 0.10, 0.10), 'gown', 0.03)
        G.cap(add, (0, fy + 0.15, fz + 0.01), (0, fy + 0.19, fz + 0.03), 0.045, 0.05, 'figure')   # neck
        G.ell(add, (0, fy + 0.27, fz + 0.045), (0.074, 0.09, 0.08), 'figure', 0.02)               # head
        G.ell(add, (0, fy + 0.31, fz - 0.015), (0.080, 0.07, 0.07), 'hair', 0.02)                # hair mass behind
        G.ell(add, (0, fy + 0.23, fz - 0.03), (0.075, 0.17, 0.065), 'hair', 0.02)
        for sx in (-1, 1):
            G.ell(add, (sx * 0.030, fy + 0.285, fz + 0.115), (0.021, 0.014, 0.010), 'blank', 0.0)  # blank staring eyes
            G.ell(add, (sx * 0.032, fy + 0.318, fz + 0.108), (0.030, 0.007, 0.008), 'hair', 0.0, R=rot_z(-sx * 0.2))
        G.cap(add, (-0.09, fy + 0.0, fz + 0.04), (0.08, fy + 0.07, fz + 0.075), 0.035, 0.03, 'gown', 0.02)
        G.cap(add, (0.09, fy + 0.0, fz + 0.045), (-0.07, fy + 0.07, fz + 0.08), 0.035, 0.03, 'gown', 0.02)
        G.sph(add, (-0.075, fy + 0.07, fz + 0.085), 0.034, 'figure')
        G.sph(add, (0.085, fy + 0.07, fz + 0.085), 0.034, 'figure')

        def alb(q, n):
            a = _arr(OAK_GREY, len(q))
            v = fbm(q * v3(1, 3, 1), 6.0, 2)[:, None]
            a = a * (0.80 + 0.32 * v)
            u = np.clip((q[:, 2] + HL) / (2 * HL), 0, 1)
            yd, hk = _deck_y(u), _depth(u)
            vv = (q[:, 1] - yd) / hk
            # plank seams (three broad strakes) and a faded paint band under the gunwale
            seam = (np.abs(vv + 0.20) < 0.016) | (np.abs(vv + 0.40) < 0.016) | (np.abs(vv + 0.60) < 0.016)
            top = vv > -0.035
            paint = (vv > -0.20) & (vv <= -0.035)
            pc = _arr(_hex('#7e8f86'), len(q)) * (0.85 + 0.2 * fbm(q, 9.0, 2)[:, None])
            flake = (vnoise(q, 11.0) > 0.60)[:, None]
            a = np.where(paint[:, None], np.where(flake, a, pc), a)
            a = np.where(seam[:, None], np.array(TAR)[None, :] * 1.5, a)
            deck = _arr(_hex('#6a5d4e'), len(q)) * (0.85 + 0.3 * fbm(q * v3(5, 1, 1), 8.0, 2)[:, None])
            a = np.where(top[:, None], deck, a)
            d, _, _ = _hull_d(q)
            inside = (d < -0.025) & (q[:, 1] < yd - 0.045)
            a = np.where(inside[:, None], np.array(TAR)[None, :] * 0.9, a)
            return a

        def rust(q, n):
            a = _arr(_hex('#82482a'), len(q))
            b = (vnoise(q, 12.0) > 0.55)[:, None]
            return np.where(b, np.array(ORANGE)[None, :] * 0.8, a)
        return {'timber': Material(local_albedo(F, alb), spec=0.08, gloss=10, brush=0.10),
                'timberd': Material(_hex('#5f574f'), spec=0.1, gloss=12, brush=0.08),
                'ram': Material(local_albedo(F, rust), spec=0.4, gloss=24, metal=0.4),
                'ramtip': Material(_hex('#8a4a28'), spec=0.5, gloss=28, metal=0.5),
                'ramband': Material(_hex('#4a2c1c'), spec=0.45, gloss=24, metal=0.4),
                'gown': Material(_hex('#8a5f55'), spec=0.1, gloss=12, brush=0.08),
                'figure': Material(_hex('#b8a88c'), spec=0.12, gloss=14, brush=0.06),
                'hair': Material(_hex('#3c3434'), spec=0.1, gloss=12),
                'blank': Material(_hex('#f2ecdc'), spec=0.3, gloss=20, rim=0.0)}
    return build


def _eyes():
    out = []
    for sx in (-1, 1):
        base = v3(sx * 0.07, -0.20, 0.18)
        d = norm(v3(sx * 0.25, 1.0, 0.25))
        out.append((tuple(base), tuple(d), 0.78))
    return tuple(out)


SHELL = Shell(
    build=prow_shell(),
    ride=1.02, tilt=0.12, crab_at=(0, -0.32, 0.12), crab_pitch=0.05, z0=-0.30, x0=-0.10, yaw=0.78,
    feet=((-0.46, 0.40), (0.50, 0.36), (-0.50, -0.36), (0.54, -0.40)),
    leg_roots=((-0.20, -0.38, 0.18), (0.20, -0.38, 0.18), (-0.28, -0.38, -0.12), (0.28, -0.38, -0.12)),
    eyes=_eyes(), eye_bead=0.055, antennae=False,
    guard=((0.12, -0.04, 0.44), (-0.45, 0.20, 0.80)),
    big=1.25, small=0.55, side_r=0.42, tip_angle=1.25, leg_len=1.12, leg_r=1.15)


def neutral_pose():
    return hermit_pose(open=0.3, spread=0.3)


def build(P):
    return shelled(P, SIZE, SHELL)


def _rows(R):
    # attack: the prow dips and lunges, the claw snaps under the ram
    for i, (P, o) in enumerate(R['attack']):
        P['lean'] = [-0.10, -0.16, 0.12, 0.03][i]
        P['slide'] = [0.0, -0.03, 0.10, 0.04][i]
        P['snap'] *= 0.6
    for row in ('hit', 'death', 'cast'):
        for P, o in R[row]:
            P['snap'] *= 0.6
            P['drum'] *= 0.6
    return R


ROWS, frames = hermit_rows(neutral_pose, 'shell', extra=_rows)

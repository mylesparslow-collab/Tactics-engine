"""Lobster-Pot Lurker (Hermitage controller). A pony-ish dog of a crab living in a giant D-section lobster pot:
withy body bound by three thick rust-iron hoops, a coil of orange rope on top, the funnel mouth at the front where the
crab crouches and peers out. The big claw holds the free end of the rope, which runs back over the shoulder to the coil
(Haul In: the claw whips the rope end out). ~1.1 m. Defining detail: the rope trailing from claw to pot."""
from _hermitage_common import *
from _hermitage_common import _claw_target, _arr

UNIT_ID = 'hermitage_lobster_pot_lurker'
SIZE = 'small'
CAMERA = size_camera(SIZE)
RX, RY, Y0 = 0.46, 0.44, -0.20      # D profile: half-ellipse on a flat floor at y = Y0
HL = 0.44                           # half length
ROPE = _hex('#e8892a')


def _prof(p, sx=1.0, sy=1.0):
    """2D signed distance of the D profile in the xy plane (negative inside)."""
    x, y = p[:, 0], p[:, 1] - Y0
    e = (np.sqrt((x / (RX * sx)) ** 2 + (y / (RY * sy)) ** 2) - 1.0) * min(RX * sx, RY * sy)
    return np.maximum(e, -y)


def pot_shell(rope_coil=True):
    def solid(p):
        return np.maximum(_prof(p) * 0.9, np.abs(p[:, 2]) - HL)

    def inner(p):
        return np.maximum(_prof(p, 0.90, 0.90) * 0.9 + 0.0, np.abs(p[:, 2]) - HL - 0.2) + 0.0

    def hoop(z0, r):
        def f(p):
            return np.sqrt(_prof(p) ** 2 + (p[:, 2] - z0) ** 2) - r
        return f

    def build(add, P, F):
        body = Subtract(Func(solid, (0, 0, 0), 1.0), Func(lambda p: np.maximum(_prof(p, 0.90, 0.90), np.abs(p[:, 2]) - HL - 0.3) * 0.9,
                                                      (0, 0, 0), 1.2))
        F.put(add, body, 'withy')
        # floor slab inside reads dark
        F.box(add, (0, Y0 + 0.02, 0), (RX * 0.88, 0.012, HL * 0.95), 0.0, 'dark')
        for z, r in ((-HL + 0.03, 0.036), (0.0, 0.034), (HL - 0.02, 0.042)):
            F.put(add, Func(hoop(z, r), (0, 0, z), 1.0), 'iron')
        # two ridge bars along the top corners so the frame reads as iron + withy
        for sx in (-1, 1):
            F.cyl(add, (sx * 0.47, Y0 + 0.03, -HL + 0.03), (sx * 0.47, Y0 + 0.03, HL - 0.02), 0.028, 'iron')
        # the rope coil on top: three stacked turns, not a puff
        if rope_coil:
            top = Y0 + RY
            for j, (rr, yy) in enumerate(((0.15, 0.015), (0.13, 0.065), (0.10, 0.11))):
                F.put(add, Torus(v3(0.0, top + yy - 0.01, -0.14), v3(0, 1, 0), rr, 0.032), 'rope')
        # iron lifting loop at the back
        F.put(add, Torus(v3(0, Y0 + RY * 0.62, -HL - 0.02), v3(1, 0, 0), 0.085, 0.026), 'iron')

        def alb(q, n):
            ang = np.arctan2(q[:, 0], q[:, 1] - Y0)
            a = _arr(_hex('#ad8248'), len(q))
            v = fbm(q * v3(1, 1, 2.2), 6.0, 2)[:, None]
            a = a * (0.78 + 0.45 * v)
            rib = (np.sin(ang * 7.0 + q[:, 2] * 2.0) > 0.15)[:, None]          # a few broad withy runs, not a lattice
            a = np.where(rib, a * 0.50, a)
            inside = (_prof(q, 0.945, 0.945) < 0.0)
            return np.where(inside[:, None], np.array(TAR)[None, :] * 0.8, a)

        def iron_alb(q, n):
            a = _arr(RUST, len(q))
            bl = (vnoise(q, 12.0) > 0.66)[:, None]
            return np.where(bl, np.array(ORANGE)[None, :] * 0.8, a)
        return {'withy': Material(local_albedo(F, alb), spec=0.12, gloss=10, brush=0.1),
                'iron': Material(local_albedo(F, iron_alb), spec=0.45, gloss=26, metal=0.4),
                'rope': Material(ROPE, spec=0.08, gloss=8, brush=0.1)}
    return build


SHELL = Shell(
    build=pot_shell(),
    ride=0.74, tilt=0.16, crab_at=(0, -0.22, 0.24), crab_pitch=-0.10, z0=-0.22, x0=0.20,
    feet=((-0.44, 0.30), (0.44, 0.28), (-0.52, -0.22), (0.50, -0.24)),
    leg_roots=((-0.20, -0.22, 0.28), (0.20, -0.22, 0.28), (-0.32, -0.20, -0.08), (0.32, -0.20, -0.08)),
    eye_len=0.52, eye_bead=0.068, big=1.3, small=0.5, side_r=0.50, tip_angle=1.30, leg_len=1.12, leg_r=1.2,
    guard=((0.16, 0.06, 0.46), (-0.45, 0.40, 0.8)))


def neutral_pose():
    return hermit_pose(open=0.5, throw=0.0, drop=0.0)


def build(P):
    F = shell_frame(P, SHELL)
    s = SIZES[SIZE]['s']
    C = F.child(v3(*SHELL.crab_at) + v3(0, -0.02 * P['duck'], -0.10 * P['duck'] * s), rot_x(SHELL.crab_pitch), s)

    def world(add):
        w, d = _claw_target(P, True, SHELL.guard)
        ww, dw = C.p(w * v3(-1, 1, 1)), C.v(d * v3(-1, 1, 1))
        cs = SHELL.big * s
        t = P['throw']
        end = ww + dw * 0.44 * cs + F.v((0.0, 0.05, 1.0)) * 0.55 * min(t, 1.0) * (1.0 if t < 1.5 else 0.6)
        end = lerp(end, v3(end[0] - 0.05, 0.05, end[2]), min(P['drop'], 1.0))
        start = F.p((0.10, Y0 + RY + 0.09, -0.12))
        ctrl = F.p((-0.66, 0.10, 0.02)) + v3(0, -0.12, 0)
        n = 9
        pts = []
        for i in range(n + 1):
            u = i / n
            pts.append((1 - u) ** 2 * start + 2 * u * (1 - u) * ctrl + u ** 2 * end)
        for a, b in zip(pts[:-1], pts[1:]):
            add(Capsule(a, b, 0.032, 0.032), 'rope', 0.006)
        add(Sphere(end, 0.04), 'rope', 0.01)
    return shelled(P, SIZE, SHELL, world=world)


def _rows(R):
    for i, (P, o) in enumerate(R['attack']):
        P['throw'] = [0, 0, 1, 1][i]
        P['open'] = [0.45, 0.35, 0.8, 0.5][i]
    for i, (P, o) in enumerate(R['death']):
        P['drop'] = [0, 0.3, 1, 1][i]
    return R


ROWS, frames = hermit_rows(neutral_pose, 'shell', extra=_rows)

"""Jug Lobber (Hermitage ranged). A big-dog crab living in a salt-glazed stoneware cistern jug: round belly with a
chunk broken out of the front (the crab's door), a short flared neck pointing back and up, one loop handle, brown
glaze drips on grey-cream. The big claw holds a round ballast stone; the attack winds it back and throws it overhand.
~1.1 m. Defining detail: the stone in the claw."""
from _hermitage_common import *
from _hermitage_common import _arr

UNIT_ID = 'hermitage_jug_lobber'
SIZE = 0.95            # 'small' class, crab scaled so its front fills the broken door
CAMERA = size_camera('small')
RX, RY, RZ = 0.40, 0.38, 0.42          # belly radii
WALL = 0.045
STONE_R = 0.115


def _ell_sdf(rx, ry, rz):
    rr = np.array([rx, ry, rz])
    m = min(rx, ry, rz)

    def f(p):
        return (np.linalg.norm(p / rr, axis=1) - 1.0) * m * 0.9
    return f


def jug_shell():
    outer = Func(_ell_sdf(RX, RY, RZ), (0, 0, 0), 0.6)
    inner = Func(_ell_sdf(RX - WALL, RY - WALL, RZ - WALL), (0, 0, 0), 0.6)
    door = Sphere(v3(0.0, -0.07, 0.56), 0.33)

    def build(add, P, F):
        body = Subtract(Subtract(outer, inner), door)
        F.put(add, body, 'glaze')
        # short neck, pointing back and up, with a rolled lip and a dark throat
        n0, n1 = v3(0, 0.12, -0.30), v3(0, 0.30, -0.62)
        F.cyl(add, tuple(n0), tuple(n1), 0.135, 'glaze', 0.05)
        F.put(add, Torus(n1 + v3(0, 0.005, -0.005), norm(n1 - n0), 0.145, 0.045), 'glaze', 0.01)
        F.put(add, Cylinder(n1 - norm(n1 - n0) * 0.01, n1 + norm(n1 - n0) * 0.03, 0.10, 0.01), 'dark')
        # one throwing ring on the belly and the loop handle from neck to shoulder
        F.put(add, Torus(v3(0, 0.0, 0.10), v3(0, 0, 1), 0.372, 0.022), 'glazed')
        F.put(add, Torus(v3(0.0, 0.40, -0.40), v3(1, 0, 0), 0.155, 0.04), 'glaze')
        barnacles(add, F.p((-0.36, -0.12, -0.10)), F.v((-1, -0.1, -0.1)), size=0.032, n=4, seed=2)

        def alb(q, n):
            a = _arr(_hex('#c9bfa6'), len(q))
            v = fbm(q * 1.3, 5.0, 2)[:, None]
            a = a * (0.88 + 0.22 * v)
            ang = np.arctan2(q[:, 0], q[:, 1])
            tg = vnoise(np.stack([ang * 1.6, ang * 0, ang * 0 + 1.3], 1), 2.2)
            thr = 0.38 - 0.62 * tg ** 1.4
            drip = (q[:, 1] > thr)[:, None]
            a = np.where(drip, _arr(_hex('#6a4a34'), len(q)) * (0.85 + 0.3 * v), a)
            inside = (np.linalg.norm(q / np.array([RX - 0.01, RY - 0.01, RZ - 0.01]), axis=1) < 0.96)
            inside &= ~((q[:, 1] > 0.22) & (q[:, 2] < -0.30))
            return np.where(inside[:, None], np.array(TAR)[None, :] * 0.9, a)
        return {'glaze': Material(local_albedo(F, alb), spec=0.55, gloss=46, brush=0.05),
                'glazed': Material(_hex('#8c6a4c'), spec=0.4, gloss=30, brush=0.05),
                'stone': Material(chitin(_hex('#7d7a78'), dark=_hex('#4a4745'), freq=7.0, amt=0.35), spec=0.1, gloss=10,
                                  brush=0.1)}
    return build


SHELL = Shell(
    build=jug_shell(),
    ride=0.40, tilt=-0.12, crab_at=(0, -0.14, 0.40), crab_upright=1.0, z0=-0.70, x0=0.34, yaw=0.15,
    eye_len=0.32, eye_bead=0.066, span=0.46, big=1.35, small=0.65, side_r=0.40, tip_angle=1.35, tip_dir=-1.0,
    guard=((0.20, -0.02, 0.17), (-0.40, 0.25, 0.85)))


def neutral_pose():
    return hermit_pose(open=0.55, stone=1.0, throw=0.0, drop=0.0)


def build(P):
    s = SIZES[SIZE]['s'] if isinstance(SIZE, str) else float(SIZE)

    def world(add):
        if P['stone'] <= 0.02:
            return
        held, dw = claw_grip(P, SHELL, SIZE, True)
        F = shell_frame(P, SHELL)
        t = P['throw']
        fly = held + F.v((0.0, 0.10, 1.0)) * 0.55 * t + v3(0, -0.10 * max(t - 1, 0), 0)
        ground = v3(held[0], STONE_R * s, held[2]) + v3(0.1, 0, 0.06)
        pos = lerp(fly, ground, min(P['drop'], 1.0))
        r = STONE_R * (1.0 + 0.25 * (SHELL.big - 1)) * P['stone']
        add(Ellipsoid(pos, (r, r * 0.92, r * 0.97), rot_y(0.6)), 'stone', 0.0)
        for j, (a, b, c) in enumerate(((0.6, 0.5, 0.3), (-0.5, 0.2, 0.7), (0.1, -0.6, 0.6))):
            add(Sphere(pos + v3(a, b, c) * r * 0.78, r * 0.42), 'stone', 0.012)
    return shelled(P, SIZE, SHELL, world=world)


def _rows(R):
    # attack = overhand throw: the stone is drawn back (cock), released on the hit frame, gone after
    for i, (P, o) in enumerate(R['attack']):
        P['throw'] = [0, 0, 1, 2][i]
        P['stone'] = 1.0
        P['open'] = [0.45, 0.35, 0.8, 0.5][i]
    # death: the stone falls out of the claw and stays on the salt
    for i, (P, o) in enumerate(R['death']):
        P['drop'] = [0, 0.4, 1, 1][i]
        P['slide'] = [0, 0.0, -0.02, -0.02][i]
        P['limp'] *= 0.5
    return R


ROWS, frames = hermit_rows(neutral_pose, 'shell', extra=_rows)

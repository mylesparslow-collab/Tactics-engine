"""Bell Tenant (Hermitage controller). A pony-sized crab wearing a verdigris bronze chapel bell like a hood: the bell
lies tilted mouth-forward over its back, the old rope still tied to the crown, one long crack down the bronze. The
crab's small claw holds the clapper out by the lip. Clang: the bell swings forward and one clean ring-line expands.
~1.4 m. Defining detail: the crack, and the clapper in the small claw."""
from _hermitage_common import *
from _hermitage_common import _claw_target, _arr

UNIT_ID = 'hermitage_bell_tenant'
SIZE = 'medium'
CAMERA = size_camera(SIZE)
H, RB, RT = 0.90, 0.46, 0.25
TH = -1.12                      # bell axis swung from vertical to nearly horizontal, mouth forward


def bell_on_side():
    inner = chapel_bell_shell(h=H, r_bot=RB, r_top=RT, crack=True, clapper_tied=False, rope=False)

    def build(add, P, F):
        F2 = Frame(F.o, F.R @ rot_x(TH), 1.0)
        mats = inner(add, P, F2)
        # the crown rope: a thick tail hanging off the back
        crown = F2.p((0, H / 2 + 0.09, 0))
        pts = [crown, crown + F.v((0.0, 0.02, -0.14)), crown + F.v((0.05, -0.12, -0.26)), crown + F.v((0.10, -0.38, -0.30)),
               crown + F.v((0.12, -0.55, -0.26))]
        for a, b in zip(pts[:-1], pts[1:]):
            add(Capsule(a, b, 0.038, 0.034), 'rope', 0.01)
        # the long crack: a dark zig-zag from the lip nearly to the shoulder (also drawn as a groove so it reads at 1x)
        hb = -H / 2
        pts = []
        for k, (yy, da) in enumerate(((0.02, 0.0), (0.16, 0.06), (0.28, -0.04), (0.42, 0.05), (0.54, -0.02), (0.66, 0.04))):
            t = np.clip(yy / H, 0, 1)
            rr = RT + (RB - RT) * (1 - t) ** 2.2 + 0.012
            az = -0.75 + da
            pts.append(F2.p((np.sin(az) * rr, hb + yy, np.cos(az) * rr)))
        for a, b in zip(pts[:-1], pts[1:]):
            add(Capsule(a, b, 0.016, 0.013), 'dark', 0.0)
        return mats
    return build


SHELL = Shell(
    build=bell_on_side(),
    ride=0.80, tilt=0.0, crab_at=(0, -0.20, 0.30), crab_pitch=0.0, z0=-0.30, x0=0.14,
    feet=((-0.52, 0.34), (0.54, 0.32), (-0.58, -0.24), (0.58, -0.26)),
    leg_roots=((-0.20, -0.24, 0.30), (0.20, -0.24, 0.30), (-0.30, -0.26, -0.05), (0.30, -0.26, -0.05)),
    eyes=(((-0.10, -0.12, 0.40), (-0.18, 1.0, 0.30), 0.56), ((0.10, -0.12, 0.40), (0.18, 1.0, 0.30), 0.56)),
    eye_bead=0.058, big=1.25, small=0.6, side_r=0.46, tip_angle=1.30, tip_dir=-1.0,
    guard=((0.14, 0.00, 0.44), (-0.50, 0.35, 0.8)), leg_len=1.05)


def neutral_pose():
    return hermit_pose(open=0.35, spread=0.0, ring=0.0)


def build(P):
    F = shell_frame(P, SHELL)
    s = SIZES[SIZE]['s']
    C = F.child(v3(*SHELL.crab_at) + v3(0, -0.02 * P['duck'], -0.10 * P['duck'] * s), rot_x(SHELL.crab_pitch), s)
    F2 = Frame(F.o, F.R @ rot_x(TH), 1.0)
    mouth = F2.p((0, -H / 2, 0))
    axis = F2.v((0, -1, 0))

    def world(add):
        # clapper: iron ball held in the small claw, rod running back inside the bell
        w, d = _claw_target(P, False)
        ww, dw = C.p(w * v3(1, 1, 1)), C.v(d)
        cs = SHELL.small * s
        ball = ww + dw * 0.40 * cs + F.v((0, 0.02, 0))
        add(Sphere(ball, 0.075), 'iron', 0.0)
        add(Capsule(ball, mouth - axis * 0.18 + F.v((0.05, 0.05, 0)), 0.02, 0.02), 'iron', 0.0)
        r = P['ring']
        if r > 0.02:                         # one clean ring-line expanding off the lip
            add(Torus(mouth + axis * (0.10 + 0.25 * r), axis, 0.40 + 0.28 * r, 0.014 * (1.2 - 0.6 * r)), 'ringline', 0.0)
    return shelled(P, SIZE, SHELL, world=world,
                   mats={'ringline': Material(_hex('#e8efe6'), emissive=_hex('#c9d8d0'), rim=0.0)})


def _rows(R):
    # attack = Clang: the bell rocks back, swings forward on the hit frame and rings
    for i, (P, o) in enumerate(R['attack']):
        P['cock'] = 0.0
        P['snap'] = [0, 0, 0.5, 0.2][i]
        P['lean'] = [0.0, 0.10, -0.22, -0.06][i]
        P['recoil'] = [0, 0, -0.06, 0][i]
        P['ring'] = [0, 0, 0.5, 1.0][i]
        P['open'] = [0.35, 0.3, 0.7, 0.4][i]
    for i, (P, o) in enumerate(R['cast']):
        P['ring'] = [0, 0.4, 0.2, 0.9][i]
    return R


ROWS, frames = hermit_rows(neutral_pose, 'shell', extra=_rows)

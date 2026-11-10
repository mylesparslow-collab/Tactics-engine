"""Tool-Chest Tinker (Hermitage support / healer). A big-dog crab sitting up in a ship's carpenter's chest of grey oak
with brass corners: open at the front, the lid propped up forward like an awning on a chisel stood on the ground. The
big claw holds a wooden mallet (the only crab holding a tool); the eyestalks peer out under the lid. ~1.0 m.
Defining detail: the mallet."""
from _hermitage_common import *
from _hermitage_common import _claw_target, _arr

UNIT_ID = 'hermitage_tool_chest_tinker'
SIZE = 'small'
CAMERA = size_camera(SIZE)
HX, HY, HZ = 0.42, 0.23, 0.33         # chest half extents
LID_A = 0.62                          # lid raised about the back hinge (rad)
HINGE = v3(0, HY, -HZ)
GREY_OAK = _hex('#7d7870')
BRASS_L = _hex('#c29a4a')


def _lid_R():
    return rot_x(-LID_A)


def chest_shell():
    def build(add, P, F):
        outer = RoundBox(v3(0, 0, 0), (HX, HY, HZ), 0.03)
        inner = RoundBox(v3(0, 0.07, 0.10), (HX - 0.045, HY, HZ - 0.03), 0.02)      # open on top and at the front
        F.put(add, Subtract(outer, inner), 'oak')
        # brass corners (front) and base straps
        for sx in (-1, 1):
            F.box(add, (sx * (HX - 0.01), HY - 0.05, HZ - 0.02), (0.045, 0.07, 0.045), 0.012, 'brass')
            F.box(add, (sx * (HX - 0.01), -HY + 0.05, HZ - 0.02), (0.045, 0.06, 0.045), 0.012, 'brass')
            F.box(add, (sx * (HX - 0.01), -HY + 0.05, -HZ + 0.03), (0.045, 0.06, 0.045), 0.012, 'brass')
            F.put(add, Torus(v3(sx * (HX + 0.01), 0.04, 0.0), v3(1, 0, 0), 0.07, 0.016), 'iron')      # becket rings
        # lid on the back hinge, propped open
        R = _lid_R()
        c = HINGE + R @ v3(0, 0.03, HZ + 0.04)
        F.box(add, tuple(c), (HX + 0.01, 0.028, HZ + 0.04), 0.012, 'oak', 0.0, R)
        for sx in (-1, 1):
            cc = HINGE + R @ v3(sx * (HX - 0.04), 0.035, 2 * HZ + 0.02)
            F.box(add, tuple(cc), (0.05, 0.04, 0.05), 0.012, 'brass', 0.0, R)
            cb = HINGE + R @ v3(sx * (HX - 0.07), 0.04, 0.04)
            F.box(add, tuple(cb), (0.07, 0.035, 0.05), 0.012, 'brass', 0.0, R)
        # the chisel prop under the lid's front-right corner, standing on the ground (world)
        top = F.p(HINGE + R @ v3(-HX + 0.07, -0.01, 2 * HZ + 0.02))
        t = P['tip']
        bot = v3(top[0] - 0.05, 0.03, top[2] + 0.14)
        bot = lerp(bot, v3(top[0] - 0.30, 0.03, top[2] + 0.30), t)
        top = lerp(top, v3(top[0] - 0.05, 0.03, top[2] + 0.45), t)
        mid = lerp(bot, top, 0.45)
        add(Capsule(bot, mid, 0.036, 0.032), 'oakh', 0.0)                 # handle (wood)
        add(Capsule(mid, top, 0.022, 0.016), 'iron', 0.004)               # blade
        add(Sphere(bot, 0.04), 'oakh', 0.01)

        def alb(q, n):
            a = _arr(GREY_OAK, len(q))
            g = fbm(q * v3(1, 0.15, 1.5), 6.0, 2)[:, None]
            a = a * (0.80 + 0.40 * g)
            plank = (np.abs(((q[:, 1] + HY) / (2 * HY) * 3.0 % 1.0) - 0.5) > 0.47)[:, None]      # three planks
            a = np.where(plank, a * 0.55, a)
            inside = ((np.abs(q[:, 0]) < HX - 0.05) & (q[:, 1] < HY - 0.02) & (q[:, 2] < HZ - 0.02)
                      & (np.abs(q[:, 0]) < HX - 0.05)) & (q[:, 2] > -HZ + 0.02) & (q[:, 1] > -HY + 0.05)
            return np.where(inside[:, None], np.array(TAR)[None, :] * 0.8, a)
        return {'oak': Material(local_albedo(F, alb), spec=0.12, gloss=10, brush=0.1),
                'oakh': Material(_hex('#8a5e3a'), spec=0.15, gloss=14, brush=0.08),
                'brass': Material(BRASS_L, spec=0.75, gloss=40, metal=0.7),
                'iron': Material(_hex('#58585c'), spec=0.6, gloss=30, metal=0.6),
                'mallet': Material(_hex('#8a5e3a'), spec=0.15, gloss=14, brush=0.08)}
    return build


SHELL = Shell(
    build=chest_shell(),
    ride=0.50, tilt=0.20, crab_at=(0, -0.08, 0.16), crab_pitch=-0.45, z0=-0.30, x0=0.10,
    feet=((-0.44, 0.30), (0.44, 0.28), (-0.52, -0.20), (0.50, -0.22)),
    leg_roots=((-0.16, -0.17, 0.22), (0.16, -0.17, 0.22), (-0.26, -0.18, -0.06), (0.26, -0.18, -0.06)),
    eye_len=0.46, eye_bead=0.064, big=1.25, small=0.5, side_r=0.34, tip_angle=1.30,
    guard=((0.14, 0.18, 0.42), (-0.30, 0.65, 0.65)))


def neutral_pose():
    return hermit_pose(open=0.2)


def build(P):
    F = shell_frame(P, SHELL)
    s = SIZES[SIZE]['s']
    C = F.child(v3(*SHELL.crab_at) + v3(0, -0.02 * P['duck'], -0.10 * P['duck'] * s), rot_x(SHELL.crab_pitch), s)

    def world(add):
        w, d = _claw_target(P, True, SHELL.guard)
        ww, dw = C.p(w * v3(-1, 1, 1)), C.v(d * v3(-1, 1, 1))
        cs = SHELL.big * s
        grip = ww + dw * 0.40 * cs
        hd = norm(dw * 0.35 + v3(0, 1.0, 0) * 0.95 + F.v((0, 0, 0.1)))      # the handle stands up out of the grip
        a, b = grip - hd * 0.12, grip + hd * 0.50
        add(Capsule(a, b, 0.032, 0.028), 'mallet', 0.0)
        side = norm(np.cross(hd, v3(0.7, 0.0, 0.7)))
        Rm = R_from(side, hd)                                                   # head: a cylinder lying across the handle top
        hc = b + hd * 0.03
        add(Cylinder(hc - side * 0.13, hc + side * 0.13, 0.085, 0.02), 'mallet', 0.0)
        for sg in (-1, 1):
            add(Torus(hc + side * 0.10 * sg, side, 0.088, 0.016), 'iron', 0.0)
    return shelled(P, SIZE, SHELL, world=world)


def _rows(R):
    # attack = a hard mallet blow: raise (cock) then snap forward-down
    for i, (P, o) in enumerate(R['attack']):
        P['snap'] *= 0.8
    return R


ROWS, frames = hermit_rows(neutral_pose, 'shell', extra=_rows)

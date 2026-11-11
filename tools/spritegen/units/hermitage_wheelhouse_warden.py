"""Wheelhouse Warden (Hermitage commander). A horse-sized crab living under a coaster's timber wheelhouse: square grey
planked box, flat overhanging roof, one big front window with a brass ship's wheel (six thick spokes) in it and the
crab's two eyes peering out either side of the wheel, the side door swung open and the big claw pointing out of it
like a harbourmaster. ~1.8 m, ppm 48. Defining detail: the wheel turns when it walks."""
from _hermitage_common import *

UNIT_ID = 'hermitage_wheelhouse_warden'
SIZE = 'large'
CAMERA = size_camera(SIZE)

HX, HY, HZ = 0.46, 0.40, 0.40       # half extents of the wheelhouse box
WIN = (0.0, 0.08, 0.34, 0.21)        # window centre x, y, half width, half height (front wall, +z)
DOOR = (0.04, -0.06, 0.19, 0.28)     # door centre z, y, half width, half height (right wall, -x)


def _box(p, c, h):
    q = np.abs(p - np.asarray(c)[None, :]) - np.asarray(h)[None, :]
    return np.maximum(np.maximum(q[:, 0], q[:, 1]), q[:, 2])


def wheelhouse():
    def build(add, P, F):
        def shell(p):
            outer = _box(p, (0, 0, 0), (HX, HY, HZ))
            inner = _box(p, (0, -0.2, 0), (HX - 0.05, HY - 0.05 + 0.2, HZ - 0.05))
            d = np.maximum(outer, -inner)
            win = _box(p, (WIN[0], WIN[1], HZ), (WIN[2], WIN[3], 0.12))
            door = _box(p, (-HX, DOOR[1], DOOR[0]), (0.12, DOOR[3], DOOR[2]))
            return np.maximum(np.maximum(d, -win), -door)
        F.put(add, Func(shell, (0, 0, 0), 1.0), 'timber', 0.0)
        # corner posts, sill and window frame (heavy, darker timber)
        for sx in (-1, 1):
            for sz in (-1, 1):
                F.box(add, (sx * (HX - 0.01), 0, sz * (HZ - 0.01)), (0.035, HY, 0.035), 0.01, 'trim')
        F.box(add, (0, WIN[1] - WIN[3] - 0.03, HZ + 0.005), (WIN[2] + 0.06, 0.03, 0.02), 0.01, 'trim')
        F.box(add, (0, WIN[1] + WIN[3] + 0.03, HZ + 0.005), (WIN[2] + 0.06, 0.03, 0.02), 0.01, 'trim')
        for sx in (-1, 1):
            F.box(add, (sx * (WIN[2] + 0.03), WIN[1], HZ + 0.005), (0.03, WIN[3] + 0.06, 0.02), 0.01, 'trim')
        # flat roof with a deep overhang, a low coaming and a ventilator cowl
        F.box(add, (0, HY + 0.03, 0.02), (HX + 0.05, 0.024, HZ + 0.05), 0.015, 'roof')
        F.box(add, (0, HY + 0.075, 0.02), (HX + 0.0, 0.02, HZ + 0.01), 0.012, 'trim')
        F.cyl(add, (-0.18, HY + 0.10, -0.20), (-0.18, HY + 0.24, -0.20), 0.055, 'iron', 0.02, 0.01)
        F.sph(add, (-0.18, HY + 0.26, -0.20), 0.07, 'iron')
        # the open door leaf, swung back against the wall
        F.box(add, (-HX - 0.20, DOOR[1], DOOR[0] + DOOR[2] + 0.03), (0.20, DOOR[3], 0.016), 0.012, 'trim', R=rot_y(0.25))
        F.box(add, (-HX - 0.20, DOOR[1], DOOR[0] + DOOR[2] + 0.03), (0.13, 0.11, 0.02), 0.012, 'timber', R=rot_y(0.25))
        F.box(add, (0, WIN[1], HZ - 0.22), (WIN[2] + 0.05, WIN[3] + 0.05, 0.02), 0.01, 'dark')
        # the brass wheel, set back in the window: six thick spokes with handles, turns with P['spin']
        a0 = P['spin']
        wc = v3(WIN[0], WIN[1] - 0.005, HZ - 0.13)
        F.put(add, Torus(wc, v3(0, 0, 1), 0.150, 0.022), 'brass')
        F.sph(add, tuple(wc), 0.045, 'brass')
        F.cyl(add, tuple(wc - v3(0, 0, 0.03)), tuple(wc + v3(0, 0, 0.04)), 0.032, 'brassd', 0.0, 0.01)
        for k in range(6):
            a = a0 + k * np.pi / 3
            d = v3(np.sin(a), np.cos(a), 0)
            F.put(add, Capsule(wc, wc + d * 0.20, 0.022, 0.017), 'brass')
            F.sph(add, tuple(wc + d * 0.22), 0.030, 'brassd')

        def alb(q, n):
            a = _arr(_hex('#a39d90'), len(q))
            v = fbm(q * v3(1, 4, 1), 6.0, 2)[:, None]
            a = a * (0.78 + 0.34 * v)
            # horizontal plank seams
            pl = np.abs(((q[:, 1] + 0.5) / 0.115) % 1.0 - 0.5) > 0.465
            a = np.where(pl[:, None], a * 0.55, a)
            # faded cream paint on the upper planks, flaking away
            paint = (q[:, 1] > 0.02)
            flake = (vnoise(q, 8.0) > 0.52)
            pc = _arr(_hex('#c4bca4'), len(q)) * (0.88 + 0.2 * fbm(q, 9.0, 2)[:, None])
            a = np.where((paint & flake)[:, None], np.where(pl[:, None], pc * 0.6, pc), a)
            # inside is tar-dark
            inside = (np.abs(q[:, 0]) < HX - 0.03) & (np.abs(q[:, 2]) < HZ - 0.03) & (q[:, 1] < HY - 0.03)
            return np.where(inside[:, None], np.array(TAR)[None, :] * 0.9, a)

        def brass(q, n):
            a = _arr(_hex('#d0a752'), len(q))
            g = (vnoise(q, 14.0) > 0.66)[:, None]
            return np.where(g, np.array(VERDI)[None, :] * 0.9, a)
        return {'timber': Material(local_albedo(F, alb), spec=0.08, gloss=10, brush=0.10),
                'trim': Material(_hex('#6e655a'), spec=0.1, gloss=12, brush=0.08),
                'roof': Material(_hex('#34302f'), spec=0.12, gloss=14, brush=0.08),
                'iron': Material(_hex('#4a2c1c'), spec=0.4, gloss=24, metal=0.4),
                'brass': Material(local_albedo(F, brass), spec=0.8, gloss=48, metal=0.7),
                'brassd': Material(_hex('#8f6e35'), spec=0.8, gloss=36, metal=0.7)}
    return build


def _eyes():
    out = []
    for sx in (-1, 1):
        base = v3(sx * 0.27, -0.16, 0.10)
        tgt = v3(sx * 0.27, 0.17, HZ - 0.08)
        d = tgt - base
        out.append((tuple(base), tuple(norm(d)), float(np.linalg.norm(d))))
    return tuple(out)


SHELL = Shell(
    build=wheelhouse(),
    ride=0.78, tilt=0.0, crab_at=(0, -0.40, 0.70), crab_upright=1.0, eye_lean=(1.3, -0.2, 0.35), z0=-1.00, x0=0.62, yaw=-0.30,
    eye_len=0.34, eye_bead=0.062, span=0.44, duck_dir=(0, 0.35, -1.0), duck_depth=0.24,
    big=1.45, small=0.70, side_r=0.42, tip_angle=1.25, leg_len=1.15, leg_r=1.15)


def neutral_pose():
    return hermit_pose(open=0.3, spread=0.3)


def build(P):
    return shelled(P, SIZE, SHELL)


def _rows(R):
    for i, (P, o) in enumerate(R['move']):
        P['spin'] = i * np.pi / 6
    for i, (P, o) in enumerate(R['idle']):
        P['spin'] = [0.0, 0.10, 0.0, -0.10][i]
    for i, (P, o) in enumerate(R['cast']):
        P['spin'] = i * 0.9
    for i, (P, o) in enumerate(R['attack']):
        P['spin'] = [0.0, -0.5, 0.8, 0.8][i]
        P['snap'] *= 0.6
    for row in ('hit', 'death', 'cast'):
        for P, o in R[row]:
            P['snap'] *= 0.6
            P['drum'] *= 0.6
    for P, o in R['death']:
        P['recoil'] = 0.60 * P['tip']
        P['limp'] *= 0.5
    fit_rows(R, snap=0.7, drum=0.5, death_back=0.0, death_slide=0.22, cast_back=0.20)   # keep claws and the death topple inside the frame
    return R


ROWS, frames = hermit_rows(neutral_pose, 'shell', extra=_rows)

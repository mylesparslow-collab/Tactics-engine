"""Strongbox Bailiff (Hermitage disruptor). A pony-sized crab inside a dark iron-banded Compact pay-chest, the lid raised
like a visor, the eyestalks peering out under it and the big claw out of the open front. An orange padlock swings
from the hasp on a short chain. Serve Notice: the lid slams down on the hit frame. ~1.4 m.
Defining detail: the swinging padlock."""
from _hermitage_common import *
from _hermitage_common import _arr

UNIT_ID = 'hermitage_strongbox_bailiff'
SIZE = 'medium'
CAMERA = size_camera(SIZE)
HX, HY, HZ = 0.40, 0.29, 0.34
HINGE = v3(0, HY, -HZ)
LID0 = 0.85
IRON_DK = _hex('#37333a')
PADLOCK = _hex('#e48a22')


def _lid_angle(P):
    return max(LID0 + 0.35 * P['door'], 0.04)


def _swing(P):
    return 0.40 * np.sin(2 * np.pi * P['tell']) + 0.5 * P['sway'] * 4 + 0.15 * P['shake'] + 0.8 * P['stride'] * 0.2


def chest_shell():
    def build(add, P, F):
        outer = RoundBox(v3(0, 0, 0), (HX, HY, HZ), 0.03)
        cav = RoundBox(v3(0, 0.07, 0.10), (HX - 0.05, HY - 0.02, HZ - 0.03), 0.02)    # open on top and the whole front
        F.put(add, Subtract(outer, cav), 'iron')
        for z in (-0.19, 0.20):
            ring = Subtract(RoundBox(v3(0, 0, z), (HX + 0.016, HY + 0.016, 0.04), 0.015),
                            RoundBox(v3(0, 0.06, z), (HX - 0.03, HY - 0.025, 0.2), 0.0))
            F.put(add, ring, 'band')
        for sx, sz in ((-1, 0.20), (1, 0.20), (-1, -0.19), (1, -0.19)):
            F.sph(add, (sx * (HX + 0.02), 0.0, sz), 0.038, 'boss')
        # lid on the back hinge, raised like a visor
        a = _lid_angle(P)
        R = rot_x(-a)
        lc = HINGE + R @ v3(0, 0.04, HZ + 0.04)
        F.box(add, tuple(lc), (HX + 0.01, 0.04, HZ + 0.04), 0.02, 'iron', 0.0, R)
        for sx in (-1, 1):
            F.box(add, tuple(HINGE + R @ v3(sx * 0.24, 0.06, HZ + 0.04)), (0.045, 0.05, HZ + 0.05), 0.015, 'band', 0.0, R)
        F.box(add, tuple(HINGE + R @ v3(0, 0.08, 0.03)), (HX - 0.03, 0.05, 0.05), 0.015, 'band', 0.0, R)
        F.sph(add, tuple(HINGE + R @ v3(-0.24, 0.12, HZ + 0.18)), 0.034, 'boss')
        F.sph(add, tuple(HINGE + R @ v3(0.24, 0.12, HZ + 0.18)), 0.034, 'boss')
        # hasp on the lid's front edge and the padlock swinging from it on a short chain
        edge = HINGE + R @ v3(0, 0.0, 2 * HZ + 0.06)
        F.box(add, tuple(edge + R @ v3(0, 0.02, -0.06)), (0.05, 0.03, 0.08), 0.012, 'band', 0.0, R)
        top = F.p(edge)
        sw = _swing(P)
        g = norm(v3(np.sin(sw), -1.0, np.cos(sw) * 0.0 + 0.15 * np.sin(sw)))
        # chain: 3 short links, then the lock body
        pts = [top]
        for k in range(1, 4):
            pts.append(top + g * 0.06 * k)
        for a_, b_ in zip(pts[:-1], pts[1:]):
            add(Capsule(a_, b_, 0.014, 0.014), 'chain', 0.004)
        lk = pts[-1] + g * 0.09
        Rl = R_from(v3(0, 0, 1) + g * 0.0, -g)
        add(RoundBox(lk, (0.075, 0.09, 0.05), 0.022, Rl), 'lock', 0.0)
        add(Torus(lk - g * 0.10, Rl[:, 2], 0.045, 0.016), 'chain', 0.0)
        add(Sphere(lk + F.v((0, 0, 0.05)), 0.022), 'dark', 0.0)

        def alb(q, n):
            a = _arr(IRON_DK, len(q))
            v = fbm(q, 5.0, 2)[:, None]
            a = a * (0.8 + 0.5 * v)
            rr = (vnoise(q * 1.2, 6.0) > 0.84)[:, None]
            a = np.where(rr, _arr(RUST, len(q)), a)
            inside = ((np.abs(q[:, 0]) < HX - 0.04) & (q[:, 1] < HY - 0.01) & (q[:, 2] > -HZ + 0.02) & (q[:, 1] > -HY + 0.12))
            return np.where(inside[:, None], np.array(TAR)[None, :] * 0.8, a)

        def band_alb(q, n):
            a = _arr(RUST, len(q))
            bl = (vnoise(q, 11.0) > 0.78)[:, None]
            return np.where(bl, np.array(ORANGE)[None, :] * 0.8, a)
        return {'iron': Material(local_albedo(F, alb), spec=0.45, gloss=24, metal=0.4, brush=0.05),
                'band': Material(local_albedo(F, band_alb), spec=0.35, gloss=22, metal=0.4),
                'boss': Material(_hex('#4a2c1c'), spec=0.5, gloss=26, metal=0.5),
                'chain': Material(_hex('#4b484c'), spec=0.6, gloss=30, metal=0.6),
                'lock': Material(PADLOCK, spec=0.6, gloss=34, metal=0.4)}
    return build


SHELL = Shell(
    build=chest_shell(),
    ride=0.42, tilt=-0.08, crab_at=(0, -0.08, 0.40), crab_upright=1.0, z0=-0.62, x0=0.26,
    eye_len=0.32, eye_bead=0.064, span=0.46, duck_dir=(0, 0.2, -1.0), duck_depth=0.26,
    big=1.40, small=0.70, side_r=0.46, tip_angle=1.30, tip_dir=-1.0)


def neutral_pose():
    return hermit_pose(open=0.3, door=0.0)


def build(P):
    return shelled(P, SIZE, SHELL)


def _rows(R):
    # attack = Serve Notice: the lid rears up, then slams down on the hit frame while the claw snaps out
    for i, (P, o) in enumerate(R['attack']):
        P['door'] = [0.3, 0.8, -1.9, -0.6][i]
    # hit: the lid drops to shield the stalks
    for P, o in R['hit']:
        P['door'] = -1.4
    for i, (P, o) in enumerate(R['death']):
        P['door'] = [-0.8, -1.2, -1.5, -1.6][i]
    fit_rows(R, snap=0.6, drum=0.45, limp=0.5, death_yaw=-0.5, cast_back=0.06)   # keep claws and the death topple inside the frame
    return R


ROWS, frames = hermit_rows(neutral_pose, 'shell', extra=_rows)

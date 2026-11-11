"""Sixpence (Hermitage hero, mobile queue-jumper). An ex-Compact crab in a squat black-powder keg (smaller than a
hogshead, three iron hoops, a scorched band round the mouth end, a fuse-hole on top), pony-sized (~1.3 m) and
sitting high on long legs. Jaunty, leaning forward, the big claw up like a hand raised in a queue, and an orange
fuse cord held in the small claw (a few sparks at the fuse-hole). Defining detail: the fuse cord in the small claw."""
from _hermitage_common import *

UNIT_ID = 'hermitage_sixpence'
SIZE = 'medium'
CAMERA = size_camera(SIZE)
KEG_L, KEG_R = 0.66, 0.31

_keg = barrel_shell(length=KEG_L, r_mid=KEG_R, r_end=0.255, hoops=(-0.24, 0.0, 0.24))


def keg(add, P, F):
    m = _keg(add, P, F)
    st = m['stave']
    a0 = st.albedo

    def alb(p, n):
        a = a0(p, n)
        q = F.inv(p)
        edge = (vnoise(q * 3.0, 6.0) - 0.5) * 0.10
        band = (q[:, 2] + edge > -0.02) & (q[:, 2] + edge < 0.30)
        soot = (q[:, 2] < 0.02) & (vnoise(q * v3(2, 1, 0.5) + 4.0, 9.0) > 0.72) & (q[:, 2] > -0.12)
        a = a * 0.82
        a = np.where(band[:, None], np.array(TAR)[None, :] * 0.9, a)
        ember = band & (vnoise(q * 2.5 + 7.0, 9.0) > 0.80)
        a = np.where(ember[:, None], np.array(ORANGE)[None, :] * 0.8, a)
        return np.where(soot[:, None], a * 0.5, a)
    m['stave'] = dataclasses.replace(st, albedo=alb)
    m['hoop'] = dataclasses.replace(m['hoop'])
    return m


SHELL = Shell(
    build=keg, ride=0.60, tilt=-0.06, crab_at=(0, -0.08, 0.42), crab_upright=1.0, z0=-0.66, x0=0.27, yaw=0.30,
    eye_len=0.34, eye_bead=0.066, span=0.46, duck_dir=(0, 0.1, -1.0), duck_depth=0.24,
    big=1.40, small=0.72, side_r=0.33, leg_len=1.25, leg_r=1.0)


def neutral_pose():
    return hermit_pose(raise_=1.15, lean=-0.04, open=0.4, spread=0.85)


def build(P):
    F = shell_frame(P, SHELL)

    def world(add):
        tip, dw = claw_grip(P, SHELL, SIZE, big=False)
        hole = F.p((0.0, KEG_R + 0.02, -0.02))
        mid = (hole + tip) / 2 + v3(0.0, 0.16, 0.10)
        n = 12
        pts = []
        for i in range(n + 1):
            t = i / n
            pts.append((1 - t) ** 2 * hole + 2 * t * (1 - t) * mid + t ** 2 * tip)
        for a, b in zip(pts[:-1], pts[1:]):
            add(Capsule(a, b, 0.024, 0.024), 'fuse', 0.0)
        add(Sphere(hole + v3(0, 0.03, 0), 0.03), 'fuse', 0.0)
        add(Sphere(tip, 0.034), 'tip', 0.0)
        emit(add, hole + v3(0, 0.05, 0), 'embers', 0.55 + 0.4 * P['fx'] + 0.3 * P['cast_glow'])
    return shelled(P, SIZE, SHELL, world=world,
                   mats={'fuse': Material(_hex('#e8892b'), spec=0.1, gloss=10, emissive=tuple(np.array(ORANGE) * 0.25))})


def _rows(R):
    for i, (P, o) in enumerate(R['idle']):          # the raised claw waves for attention
        P['raise_'] = [1.15, 0.95, 1.25, 1.05][i]
        P['open'] = [0.4, 0.2, 0.5, 0.25][i]
    for P, o in R['move']:
        P['lean'] -= 0.04
        P['raise_'] = 1.1
    for row in ('attack', 'death', 'cast', 'hit'):
        for P, o in R[row]:
            P['snap'] *= 0.35
    fit_rows(R, death_back=0.07)   # keep claws and the death topple inside the frame
    return R


ROWS, frames = hermit_rows(neutral_pose, 'shell', extra=_rows)

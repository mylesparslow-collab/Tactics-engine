"""Duchess Abaft, the Stern Tenant (Hermitage hero, commander). A wagon-sized crab (2.5 m, ppm 44) wearing the carved
stern-castle of a ship-of-the-line: dark oak, a stepped poop with three gilt finials, two tiers of three lit amber
gallery windows, a projecting gallery with a solid rail band, one thin gold-leaf scroll between the tiers, and the
smashed lower bulkhead the big claw and eyestalks come out of. The rudder hangs off the stern post and drags
behind like a tail. Defining detail: the lit gallery windows and the single gold-leaf scroll (the hero accent)."""
from _hermitage_common import *

UNIT_ID = 'hermitage_duchess_abaft'
SIZE = 1.40              # 'great' class crab, trimmed so the claw clears the frame beside the stern
CAMERA = size_camera('great')

HZ = 0.42                 # half depth of the stern castle
YB, YT = -0.34, 0.66      # bottom / top of the main castle
HOLE = (0.0, -0.17, 0.30, 0.16)   # smashed bulkhead: centre x, y, half width, half height
ROWS_Y = (0.10, 0.47)     # window tiers
WX = (-0.31, 0.0, 0.31)   # window columns


def _wx(y):
    return 0.52 - 0.10 * (y - YB) / (YT - YB)


def _box(p, c, h):
    q = np.abs(p - np.asarray(c)[None, :]) - np.asarray(h)[None, :]
    return np.maximum(np.maximum(q[:, 0], q[:, 1]), q[:, 2])


def stern(add, P, F):
    def castle(p):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        d1 = np.maximum(np.maximum(np.abs(x) - _wx(y), np.abs(z) - HZ), np.maximum(YB - y, y - YT))
        d2 = _box(p, (0, YT + 0.11, -0.05), (0.40, 0.12, 0.33))                      # stepped poop
        d = np.minimum(d1, d2)
        hole = np.maximum(np.sqrt(((x - HOLE[0]) / HOLE[2]) ** 2 + ((y - HOLE[1]) / HOLE[3]) ** 2) - 1.0, -(z - (HZ - 0.5)))
        return np.maximum(d, -(hole * 0.16))
    F.put(add, Func(castle, (0, 0.2, 0), 1.2), 'oak', 0.0)
    # a heavy wale and base sill (solid bands, not rows of anything)
    F.box(add, (0, YB + 0.03, 0.0), (_wx(YB) + 0.03, 0.04, HZ + 0.03), 0.015, 'oakd')
    F.box(add, (0, YT + 0.005, 0.0), (_wx(YT) + 0.04, 0.03, HZ + 0.04), 0.012, 'oakd')
    # projecting gallery: ledge + solid rail band + four posts
    F.box(add, (0, -0.045, HZ + 0.09), (_wx(0.0) + 0.05, 0.028, 0.10), 0.012, 'oakd')
    F.box(add, (0, 0.015, HZ + 0.185), (_wx(0.0) + 0.05, 0.055, 0.016), 0.01, 'redband')
    for px in (-0.55, -0.19, 0.19, 0.55):
        F.cyl(add, (px, -0.04, HZ + 0.18), (px, 0.085, HZ + 0.18), 0.022, 'gold', 0.0, 0.006)
    # two tiers of three lit windows, framed in faded red
    for ry in ROWS_Y:
        for cx in WX:
            F.box(add, (cx, ry, HZ - 0.005), (0.105, 0.115, 0.022), 0.02, 'redband')
            F.box(add, (cx, ry, HZ + 0.006), (0.078, 0.088, 0.02), 0.025, 'glass')
            F.box(add, (cx, ry, HZ + 0.026), (0.006, 0.09, 0.006), 0.003, 'oakd')       # mullions
            F.box(add, (cx, ry + 0.01, HZ + 0.026), (0.08, 0.006, 0.006), 0.003, 'oakd')
    # the single thin gold-leaf scroll between the tiers (a sine run with a curl at each end and a cartouche)
    ys = 0.29
    pts = [v3(x, ys + 0.03 * np.sin(x * 11), HZ + 0.016) for x in np.linspace(-0.40, 0.40, 18)]
    for a, b in zip(pts[:-1], pts[1:]):
        F.put(add, Capsule(a, b, 0.016), 'gold')
    for sx in (-1, 1):
        cx = sx * 0.46
        sp = []
        for i in range(14):
            t = i / 13
            ang = sx * (np.pi * 0.15 + 2 * np.pi * 1.15 * t)
            r = 0.062 * (1 - 0.78 * t)
            sp.append(v3(cx + r * np.cos(ang) * 1.0, ys + 0.02 + r * np.sin(ang), HZ + 0.016))
        for a, b in zip(sp[:-1], sp[1:]):
            F.put(add, Capsule(a, b, 0.015), 'gold')
    F.ell(add, (0, ys + 0.03, HZ + 0.018), (0.052, 0.038, 0.014), 'gold')
    # three gilt finials on the poop rail (no combs)
    for px in (-0.36, 0.0, 0.36):
        F.cyl(add, (px, YT + 0.22, -0.05 + (0.25 if abs(px) < 0.1 else 0.18)), (px, YT + 0.36, -0.05 + (0.25 if abs(px) < 0.1 else 0.18)),
              0.026, 'oakd', 0.0, 0.006)
        F.sph(add, (px, YT + 0.385, -0.05 + (0.25 if abs(px) < 0.1 else 0.18)), 0.048, 'gold')
    # broken planks round the smashed bulkhead: three big splinters
    for (sx, sy, ang, ln) in ((-0.29, -0.06, 0.5, 0.28), (0.27, -0.30, -0.6, 0.24), (0.10, -0.015, 0.1, 0.22)):
        a = v3(sx, sy, HZ - 0.02)
        d = norm(v3(np.sin(ang) * 0.4, np.cos(ang) * 0.5, 0.9))
        F.put(add, Capsule(a, a + d * ln, 0.035, 0.012), 'oakd')
    # the rudder: off the stern post, trailing back down to the salt like a tail
    a = v3(-0.10, 0.12, -HZ + 0.02)
    b = v3(-0.28, -0.82, -0.56)
    b = a + (b - a) * (1 - 0.45 * P['tip'])
    d = norm(b - a)
    L = float(np.linalg.norm(b - a))
    Rr = R_from(d, (1, 0, 0.0))
    F.box(add, tuple((a + b) / 2), (0.075, 0.30, L / 2), 0.02, 'oakd', R=Rr)
    for t in (0.18, 0.55, 0.88):
        c = a + (b - a) * t
        F.box(add, tuple(c), (0.085, 0.31, 0.034), 0.01, 'iron', R=Rr)
    F.cyl(add, tuple(a + d * 0.05), tuple(a + d * 0.12 + v3(0, 0.1, 0.1)), 0.04, 'iron', 0.0, 0.01)

    em = P['cast_glow']
    fl = 0.9 + 0.1 * np.sin(2 * np.pi * P['tell'] * 2)
    glow = fl * (1 + 0.45 * em) * (1 - 0.9 * P['end'])

    def alb(q, n):
        a = _arr(_hex('#5a3d2f'), len(q))
        v = fbm(q * v3(1, 4, 1), 6.0, 2)[:, None]
        a = a * (0.78 + 0.36 * v)
        pl = np.abs(((q[:, 1] + 0.5) / 0.10) % 1.0 - 0.5) > 0.46
        a = np.where(pl[:, None], a * 0.6, a)
        hx = ((q[:, 0] - HOLE[0]) / HOLE[2]) ** 2 + ((q[:, 1] - HOLE[1]) / HOLE[3]) ** 2
        inside = (hx < 1.08) & (q[:, 2] < HZ - 0.015)
        a = np.where(inside[:, None], np.array(TAR)[None, :] * 0.9, a)
        # salt bloom creeping up the lower planks
        bl = (q[:, 1] < YB + 0.20) & (vnoise(q, 7.0) > 0.55)
        return np.where(bl[:, None], a * 0.55 + np.array(BONE)[None, :] * 0.45, a)

    def red(q, n):
        a = _arr(_hex('#7e3731'), len(q))
        f = (vnoise(q, 12.0) > 0.60)[:, None]
        return np.where(f, a * 0.65 + np.array(OAK_GREY)[None, :] * 0.35, a)
    return {'oak': Material(local_albedo(F, alb), spec=0.1, gloss=12, brush=0.10),
            'oakd': Material(_hex('#35261f'), spec=0.12, gloss=14, brush=0.08),
            'redband': Material(local_albedo(F, red), spec=0.12, gloss=14, brush=0.08),
            'gold': Material(_hex('#d9b250'), spec=0.9, gloss=50, metal=0.8, brush=0.02),
            'iron': Material(_hex('#3b3638'), spec=0.4, gloss=24, metal=0.5),
            'glass': Material(_hex('#f0d89a'), spec=1.0, gloss=80, emissive=tuple(np.array(LAMP) * 1.05 * glow), rim=0.2)}


def _eyes():
    out = []
    for sx in (-1, 1):
        base = v3(sx * 0.13, -0.26, 0.20)
        tgt = v3(sx * 0.22, 0.26, HZ + 0.27)
        d = tgt - base
        out.append((tuple(base), tuple(norm(d)), float(np.linalg.norm(d)) + 0.04))
    return tuple(out)


SHELL = Shell(
    build=stern, ride=0.86, tilt=-0.04, crab_at=(0, -0.26, 0.64), crab_upright=1.0, eye_lean=(1.25, -0.1, 0.35), z0=-0.76, x0=0.405, yaw=0.02,
    eye_len=0.30, eye_bead=0.060, span=0.38, duck_dir=(0, 0.1, -1.0), duck_depth=0.26,
    big=1.20, small=0.60, side_r=0.55, tip_angle=1.15, leg_len=0.80, leg_r=1.35)


def neutral_pose():
    return hermit_pose(open=0.3, spread=0.3)


def build(P):
    F = shell_frame(P, SHELL)
    lights = [Light(F.p((0, 0.3, 0.9)), LAMP, 0.55 * (1 - P['end']) * (1 + 0.5 * P['cast_glow']), 0.9)]
    return shelled(P, SIZE, SHELL, lights=lights)


def _rows(R):
    for row in ('attack', 'death', 'cast', 'hit'):
        for P, o in R[row]:
            P['snap'] *= 0.25
            P['drum'] *= 0.3
            P['limp'] *= 0.4
    for P, o in R['death']:
        P['slide'] -= 0.20 * P['tip']; P['limp'] *= 0.4
    R['death'][1][0]['slide'] += 0.11      # the half-fallen frame swings wide: nudge it in
    fit_rows(R, snap=0.7, death_back=0.35, death_slide=0.28, death_yaw=-0.3, stride=0.5)   # keep claws and the death topple inside the frame
    return R


ROWS, frames = hermit_rows(neutral_pose, 'shell', extra=_rows)

"""Old Knell (Hermitage hero, control). A big crab (large, 1.9 m, ppm 48) living in a stolen Hadal Court pressure-bell:
tall, heavy, dark indigo-bronze with verdigris at the lip, a thick stepped skirt, a band of five fat studs, one
round viewport with a gold hairline on its rim (the hero accent), a great lifting-eye on the crown, and one orange
rust streak running down from the viewport. Worn like a cowl, mouth forward-down; the big claw is barnacled.
Defining detail: the Court's cold bronze with a single orange rust streak and the gold-rimmed viewport."""
from _hermitage_common import *

UNIT_ID = 'hermitage_old_knell'
SIZE = 'large'
CAMERA = size_camera(SIZE)
H, RB, RT = 1.22, 0.58, 0.27
HB, HT = -H / 2, H / 2
VP_T, VP_AZ = 0.60, -0.95          # viewport height fraction and azimuth from +z
STUD_AZ = (-1.95, -1.45, -0.85, -0.30, 0.30)
STUD_T = 0.30


def _r(t):
    return RT + (RB - RT) * (1 - t) ** 1.9


def _at(t, az, out=0.0):
    r = _r(t) + out
    y = HB + t * H
    return v3(np.sin(az) * r, y, np.cos(az) * r), norm(v3(np.sin(az), 0.22, np.cos(az)))


def pressure_bell(add, P, F):
    def bell(p):
        y = p[:, 1]
        t = np.clip((y - HB) / H, 0, 1)
        rr = np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2)
        d = np.maximum((rr - _r(t)) * 0.85, np.maximum(HB - y, y - HT))
        dome = np.sqrt(p[:, 0] ** 2 + ((y - HT + 0.06) / 0.62) ** 2 + p[:, 2] ** 2) - RT
        return np.minimum(d, np.maximum(dome * 0.6, HT - 0.07 - y))
    outer = Func(bell, (0, 0, 0), H * 0.8 + RB)
    inner = Xform(Func(bell, (0, 0, 0), H * 0.8 + RB), t=(0, -0.08, 0), s=0.88)
    F.put(add, Subtract(outer, inner), 'bronze')
    # heavy stepped skirt: two thick rings, the lower one fat
    F.put(add, Torus(v3(0, HB + 0.05, 0), v3(0, 1, 0), RB - 0.01, 0.075), 'bronzed', 0.02)
    F.put(add, Torus(v3(0, HB + 0.19, 0), v3(0, 1, 0), _r(0.15) + 0.005, 0.040), 'bronzed')
    # stud band: one flat ring and five fat studs on the front arc
    F.put(add, Torus(v3(0, HB + STUD_T * H, 0), v3(0, 1, 0), _r(STUD_T) + 0.012, 0.030), 'bronzed')
    for az in STUD_AZ:
        c, nrm = _at(STUD_T, az, 0.03)
        F.sph(add, tuple(c), 0.052, 'stud')
    # crown: collar, big lifting eye with two gussets
    F.cyl(add, (0, HT - 0.02, 0), (0, HT + 0.07, 0), 0.15, 'bronzed', 0.02, 0.02)
    F.put(add, Torus(v3(0, HT + 0.20, 0), v3(1, 0, 0), 0.115, 0.042), 'bronzed')
    F.put(add, Capsule(v3(0.0, HT + 0.04, 0.09), v3(0.0, HT + 0.12, 0.0), 0.028), 'bronzed')
    # the one round viewport: bronze ring, gold hairline on the rim, dark glass
    c, nrm = _at(VP_T, VP_AZ, 0.0)
    F.put(add, Torus(c + nrm * 0.02, nrm, 0.125, 0.036), 'bronzed')
    F.put(add, Torus(c + nrm * 0.045, nrm, 0.108, 0.0085), 'gold')
    F.put(add, Cylinder(c - nrm * 0.03, c + nrm * 0.02, 0.105, 0.01), 'glass')
    F.cyl(add, (0, HB + 0.12, 0), (0, HB + 0.16, 0), RB * 0.82, 'dark')

    def alb(q, n):
        a = _arr(_hex('#55527a'), len(q))                      # indigo bronze
        v = fbm(q, 4.0, 2)[:, None]
        a = a * (0.75 + 0.40 * v)
        t = np.clip((q[:, 1] - HB) / H, 0, 1)
        verd = ((vnoise(q, 6.0) > 0.62) & (t < 0.45)) | ((vnoise(q + 5.0, 9.0) > 0.78) & (t < 0.75))
        a = np.where(verd[:, None], np.array(VERDI)[None, :] * 0.62, a)
        # the single orange rust streak, down from the viewport
        az = np.arctan2(q[:, 0], q[:, 2])
        wob = 0.05 * np.sin(q[:, 1] * 9.0) + (vnoise(q * 2.0, 5.0) - 0.5) * 0.08
        streak = (np.abs(az - (VP_AZ + 0.04) - wob) < 0.065) & (t < VP_T - 0.04) & (t > 0.04)
        a = np.where(streak[:, None], np.array(ORANGE)[None, :] * 0.72, a)
        inside = np.sqrt(q[:, 0] ** 2 + q[:, 2] ** 2) < _r(t) - 0.035
        return np.where((inside & (q[:, 1] < HT - 0.1))[:, None], np.array(TAR)[None, :] * 0.9, a)
    return {'bronze': Material(local_albedo(F, alb), spec=0.4, gloss=30, metal=0.3, brush=0.06),
            'bronzed': Material(_hex('#2f2c3c'), spec=0.6, gloss=30, metal=0.55),
            'stud': Material(_hex('#4b4658'), spec=0.7, gloss=40, metal=0.6),
            'gold': Material(_hex('#e0b44c'), spec=0.9, gloss=60, metal=0.8),
            'glass': Material(_hex('#0f1624'), spec=1.0, gloss=90, rim=0.8)}


def _eyes():
    out = []
    for sx in (-1, 1):
        base = v3(sx * 0.10, -0.46, 0.34)
        d = norm(v3(sx * 0.28, 1.0, 0.55))
        out.append((tuple(base), tuple(d), 0.52))
    return tuple(out)


SHELL = Shell(
    build=pressure_bell, ride=1.00, tilt=0.42, crab_at=(0, -0.42, 0.22), crab_pitch=0.30, z0=-0.15, x0=0.22, yaw=-0.12,
    feet=((-0.52, 0.34), (0.56, 0.30), (-0.58, -0.30), (0.62, -0.34)),
    leg_roots=((-0.22, -0.52, 0.26), (0.22, -0.52, 0.26), (-0.30, -0.52, -0.06), (0.30, -0.52, -0.06)),
    eyes=_eyes(), eye_bead=0.055, antennae=False, barn=3,
    guard=((0.14, -0.04, 0.44), (-0.55, 0.30, 0.75)),
    big=1.35, small=0.55, side_r=0.55, tip_angle=1.25, tip_dir=-1.0, leg_len=1.2, leg_r=1.2)


def neutral_pose():
    return hermit_pose(open=0.3, spread=0.2)


def build(P):
    return shelled(P, SIZE, SHELL)


def _rows(R):
    for row in ('attack', 'death', 'cast', 'hit'):
        for P, o in R[row]:
            P['snap'] *= 0.6
            P['drum'] *= 0.6
            P['limp'] *= 0.5
    return R


ROWS, frames = hermit_rows(neutral_pose, 'shell', extra=_rows)

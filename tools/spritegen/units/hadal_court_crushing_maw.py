"""Crushing Maw (Hadal Court heavy melee). A walking mouth, thousands of years old, kept in a tomb of
brine: a squat bell of cracked hide strapped in pressure-iron bands, almost all jaw, on four stump legs.
Defining detail: the huge horizontal maw with a double row of bone teeth; a row of small teal eyes above.
"""
from _hadal_court_common import *

UNIT_ID = 'hadal_court_crushing_maw'
CAMERA = Camera(ppm=44)


def neutral_pose():
    return creature_pose()


def build(P):
    parts, add = new_parts()
    e, st, sk = P['end'], P['stride'], P['strike']
    opn = 0.10 + 0.04 * np.sin(2 * np.pi * P['tell']) + 0.55 * sk * (1 - 0.6 * max(sk - 0.8, 0) / 0.2) \
        + 0.25 * P['cast_glow'] + 0.2 * e
    if sk >= 1.0:
        opn = 0.05          # the bite snaps shut on the hit frame
    hinge = v3(0, 0.80, -0.30)
    # upper skull-bell
    top = v3(0, 1.72, -0.08)
    Rb = rot_x(0.12)
    add(bell_hull(top, 0.92, 0.26, 0.70, R=Rb, power=1.1, sz=0.82, lip=0.06, ribs=0.03, ribs_n=7), 'bellhide', 0.0)
    add(Ellipsoid(top + v3(0, -0.02, 0), (0.27, 0.10, 0.23)), 'hide', 0.06)
    barnacles(add, v3(0, 1.45, -0.25), np.eye(3), n=10, spread=0.38, size=0.04, seed=11)
    # eye row above the lip
    eyes = []
    for k in range(5):
        a = -0.6 + k * 0.3
        q = v3(np.sin(a) * 0.62, 1.12 + 0.03 * np.cos(a * 3), np.cos(a) * 0.50)
        add(Sphere(q, 0.028 if k != 2 else 0.036), 'lamp', 0.0)
        eyes.append(q)
    # upper teeth along the lip
    for k in range(9):
        a = -1.0 + k * 0.25
        q = v3(np.sin(a) * 0.60, 0.86, np.cos(a) * 0.52 - 0.02)
        add(Capsule(q + v3(0, 0.04, 0), q + v3(0, -0.15 - 0.04 * (k % 2), 0.02), 0.042, 0.006), 'teeth', 0.0)
    # maw interior
    add(Ellipsoid(v3(0, 0.82, 0.08), (0.56, 0.08 + 0.35 * opn, 0.44)), 'maw', 0.0)
    # lower jaw (rotates about the hinge)
    jaw = []
    jadd = lambda prim, mat, k=0.0: jaw.append(Part(prim, mat, k))
    jadd(Ellipsoid(v3(0, 0.66, 0.05), (0.66, 0.18, 0.55)), 'hide', 0.0)
    jadd(Torus(v3(0, 0.64, 0.04), v3(0, 1, 0), 0.62, 0.025), 'band', 0.02)
    for k in range(8):
        a = -0.9 + k * 0.257
        q = v3(np.sin(a) * 0.58, 0.76, np.cos(a) * 0.50)
        jadd(Capsule(q - v3(0, 0.04, 0), q + v3(0, 0.14 + 0.04 * (k % 2), 0.0), 0.04, 0.006), 'teeth', 0.0)
    parts.extend(transform_parts(jaw, R=rot_x(opn), pivot=hinge))
    # four stump legs with toe plates
    for sx in (-1, 1):
        for sz_, ph in ((1, 1), (-1, -1)):
            g = ph * sx * st
            hip = v3(sx * 0.42, 0.62, sz_ * 0.26 - 0.08)
            ft = v3(sx * (0.52 + 0.15 * e), 0.0 + 0.10 * max(g, 0), sz_ * 0.30 - 0.06 + 0.10 * g)
            kn = (hip + ft) / 2 + v3(sx * 0.06, 0.02, 0.06)
            seg_limb(add, [hip, kn, ft + v3(0, 0.08, 0)], [0.15, 0.13, 0.12], 'hide', joint='band', k=0.03)
            add(Ellipsoid(ft + v3(0, 0.06, 0.04), (0.14, 0.07, 0.15)), 'band', 0.02)
    if P['fx'] > 0:
        add(Torus(v3(0, 0.03, 0.75), v3(0, 1, 0), 0.15 + 0.25 * P['fx'], 0.016), 'speck', 0.0)
    parts[:] = transform_parts(creature_place(parts, P), t=(0, 0, -0.1))
    mats = hadal_mats(P, {
        'bellhide': Material(banded_albedo(_hex('#4a4e70'), PIRON, top, Rb, spacing=0.30, width=0.05, rivet=_hex('#8d93a8'),
                                           barn=0.3), spec=0.3, gloss=20, brush=0.07),
        'hide': Material(cracked_albedo(_hex('#4a4e70'), crack=_hex('#1b1d33'), freq=6, width=0.02, seep=TEAL, barn=0.3,
                                        patina=_hex('#5e5f78'), patina_amt=0.3), spec=0.3, gloss=20, sss=0.2, brush=0.07),
        'band': Material(cracked_albedo(PIRON, crack=BLACK, freq=12, width=0.01), spec=0.6, gloss=30, metal=0.5),
    })
    lights = [teal_light(eyes[2] + v3(0, P['bob'], 0.1), P, 0.4, 0.45)]
    return hadal_finish(P, parts, mats, lights)


ROWS, frames = creature_rows(neutral_pose, sink=(0, 0, 0.12, 0.45), deflate=(0, 0.05, 0.2, 0.45))

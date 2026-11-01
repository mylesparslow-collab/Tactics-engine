"""Trench Crab (Hadal Court bruiser). A barnacled, house-sized hunter-beast: domed pressure-iron carapace
with a bell-rim lip, six segmented walking legs, two great clamp-claws (one bigger), teal eye-stalks.
Defining detail: the oversized clamp claw and the barnacle-crusted dome.
"""
from _hadal_court_common import *

UNIT_ID = 'hadal_court_trench_crab'
CAMERA = Camera(ppm=44)


def neutral_pose():
    return creature_pose()


def leg(add, root, foot, s, lift, P, mat='shell'):
    foot = foot + v3(0, lift, 0)
    mid = (root + foot) / 2
    knee = root + v3(s * 0.24, 0.24 + 0.5 * lift, 0) * (1 - 0.5 * P['end'])
    seg_limb(add, [root, knee, foot + v3(0, 0.10, 0), foot], [0.09, 0.075, 0.05, 0.015], mat, joint='joint')


def build(P):
    parts, add = new_parts()
    e, st, sk = P['end'], P['stride'], P['strike']
    by = 0.78 - 0.4 * e
    c = v3(0, by, 0)
    # carapace: flattened dome with bell lip, plus a ridge plate
    add(Ellipsoid(c + v3(0, 0.05, 0), (0.58, 0.30, 0.48)), 'shell', 0.0)
    for k in range(7):
        a = -0.9 + k * 0.3
        q = c + v3(np.sin(a) * 0.55, -0.04, np.cos(a) * 0.45)
        add(Capsule(q, q + v3(np.sin(a) * 0.12, 0.05, np.cos(a) * 0.10), 0.035, 0.006), 'shell', 0.02)
    add(Torus(c + v3(0, -0.10, 0), v3(0, 1, 0), 0.52, 0.07), 'shell', 0.08)
    add(Ellipsoid(c + v3(0, 0.26, -0.08), (0.26, 0.14, 0.30)), 'shell', 0.1)
    add(Ellipsoid(c + v3(0, -0.14, 0.05), (0.48, 0.18, 0.42)), 'hide', 0.05)
    barnacles(add, c + v3(0, 0.27, -0.1), np.eye(3), n=12, spread=0.36, size=0.05, up_bias=0.5, seed=5)
    # eye stalks and teal eyes
    eyes = []
    for sx in (-1, 1):
        a = c + v3(sx * 0.12, 0.12, 0.44)
        b = a + v3(sx * 0.04, 0.20, 0.06)
        add(Capsule(a, b, 0.025, 0.018), 'hide', 0.01)
        add(Sphere(b, 0.035), 'lamp', 0.0)
        eyes.append(b)
    # mouthparts
    add(Ellipsoid(c + v3(0, -0.10, 0.46), (0.16, 0.08, 0.06)), 'maw', 0.02)
    # walking legs: 3 per side, alternating tripod gait
    for s in (-1, 1):
        for i, z in enumerate((0.22, -0.05, -0.32)):
            root = c + v3(s * 0.48, -0.08, z)
            grp = (i + (s > 0)) % 2
            ph = st if grp == 0 else -st
            foot = v3(s * (0.68 + 0.2 * e), 0.0, z * 1.3 + 0.12 * ph)
            leg(add, root, foot, s, 0.12 * max(ph, 0) * (1 - e), P)
    # claws: right (-x) is the big clamp
    for s, size in ((-1, 1.5), (1, 1.0)):
        reach = sk if s == -1 else 0.3 * sk
        raise_ = 0.2 * P['cast_glow']
        sh = c + v3(s * 0.36, -0.06, 0.38)
        el = sh + v3(s * 0.22, 0.12 + raise_, 0.12 + 0.12 * reach)
        wr = el + v3(-s * 0.10, 0.0 + raise_, 0.18 + 0.30 * reach)
        seg_limb(add, [sh, el, wr], [0.07 * size, 0.07 * size, 0.08 * size], 'shell', joint='joint')
        d = norm(wr - el)
        Rc = basis_from(d, v3(0, 1, 0))
        open_ = 0.35 * (1 - abs(2 * reach - 1)) + 0.1
        palm = wr + d * 0.12 * size
        add(Ellipsoid(palm, (0.10 * size, 0.16 * size, 0.08 * size), Rc), 'shell', 0.03)
        for j, sg in ((0, 1), (1, -1)):
            Rf = basis_from(norm(d + Rc[:, 2] * sg * open_ * 1.2 + Rc[:, 0] * 0.0), v3(0, 1, 0))
            add(Ellipsoid(palm + d * 0.20 * size + Rc[:, 2] * sg * 0.04 * size, (0.045 * size, 0.17 * size, 0.04 * size), Rf), 'claw', 0.01)
    if P['fx'] > 0:
        add(Torus(v3(-0.4, 0.03, 1.0), v3(0, 1, 0), 0.12 + 0.2 * P['fx'], 0.014), 'speck', 0.0)
    parts[:] = transform_parts(creature_place(parts, P), t=(0.25, 0, -0.45))
    mats = hadal_mats(P, {
        'shell': Material(cracked_albedo(_hex('#3e4466'), crack=_hex('#1a1c30'), freq=6, width=0.02, seep=TEAL, barn=0.35,
                                         patina=_hex('#5b6a6a'), patina_amt=0.25), spec=0.2, gloss=18, brush=0.08),
        'claw': Material(cracked_albedo(_hex('#5d6488'), crack=_hex('#1a1c30'), freq=9, width=0.01), spec=0.4, gloss=30),
        'joint': Material(_hex('#2b2f4a'), spec=0.5, gloss=30),
    })
    lights = [teal_light(q + v3(0, P['bob'], 0.05), P, 0.5, 0.5) for q in eyes]
    return hadal_finish(P, parts, mats, lights)


ROWS, frames = creature_rows(neutral_pose, sink=(0, 0, 0.1, 0.3))

"""Anglet (Hadal Court, cheap ranged). A small lantern-jawed pressure-born: hunched, translucent
brine-flesh, an oversize jaw lit from inside by glowing bile, a thimble of bell-metal for a cap and a
bait-lamp on a stalk. Spits glowing bile. Defining detail: the lit jaw and the bile globule.
"""
from _hadal_court_w2 import *

UNIT_ID = 'hadal_court_anglet'
CAMERA = Camera(ppm=60)


def neutral_pose():
    return creature_pose()


def build(P):
    parts, add = new_parts()
    e, st, sk, tl = P['end'], P['stride'], P['strike'], P['tell']
    opn = 0.34 + 0.06 * np.sin(2 * np.pi * tl) + 0.50 * min(sk * 1.4, 1.0) + 0.22 * P['cast_glow'] + 0.25 * e
    if sk >= 1.0:
        opn = 0.62
    # legs: short bowed stumps with webbed iron-toed feet
    for sx in (-1, 1):
        g = sx * st
        hip = v3(sx * 0.12, 0.40, -0.02)
        ft = v3(sx * 0.15, 0.03 + 0.07 * max(g, 0), 0.05 + 0.10 * g)
        kn = (hip + ft) / 2 + v3(sx * 0.05, 0.0, 0.09)
        seg_limb(add, [hip, kn, ft + v3(0, 0.05, 0)], [0.085, 0.07, 0.06], 'hide', joint='iron', k=0.03)
        add(Ellipsoid(ft + v3(0, 0.03, 0.06), (0.085, 0.045, 0.12)), 'hide', 0.02)
        for tx in (-0.04, 0.0, 0.04):
            add(Sphere(ft + v3(tx + sx * 0.0, 0.03, 0.17), 0.026), 'teeth', 0.0)
    # pot body, hunched forward
    bc = v3(0, 0.62, -0.03)
    add(Ellipsoid(bc, (0.20, 0.28, 0.19), rot_x(0.25)), 'flesh', 0.05)
    add(Torus(bc + v3(0, -0.12, 0.0), v3(0, 1, 0.1), 0.205, 0.026), 'iron', 0.0)
    for k in range(5):
        a = 2.7 + k * 0.42
        add(Cone(bc + v3(np.cos(a) * 0.0, 0.14 - k * 0.0, -0.20), v3(0, 0.3, -1), 0.0), 'bone', 0.0) if False else None
    # dorsal pressure plates down the spine
    for k in range(5):
        y = 0.80 - k * 0.095
        add(Ellipsoid(v3(0, y, -0.19 - 0.015 * (4 - k) + 0.0), (0.07 - 0.006 * k, 0.04, 0.03), rot_x(-0.3)), 'iron', 0.01)
    barnacles(add, v3(0.10, 0.62, -0.18), np.eye(3), n=4, spread=0.08, size=0.02, seed=4)
    # arms: thin, clutching the belly; the strike throws them out
    for sx in (-1, 1):
        sh = v3(sx * 0.21, 0.72, 0.02)
        wr = v3(sx * 0.15, 0.50 + 0.05 * sk, 0.20 + 0.12 * sk)
        el = v3(sx * 0.30, 0.56, 0.06)
        seg_limb(add, [sh, el, wr], [0.05, 0.04, 0.034], 'hide', joint='iron', k=0.02)
        for f in (-1, 0, 1):
            add(Capsule(wr, wr + v3(f * 0.02, -0.02, 0.06), 0.012, 0.007), 'teeth', 0.0)
    # head: big, set forward; bell-metal thimble cap
    hc = v3(0, 1.04 + 0.02 * np.sin(2 * np.pi * tl), 0.15)
    Rh = rot_x(-0.05 - 0.12 * sk + 0.1 * e)
    add(Ellipsoid(hc, (0.27, 0.19, 0.25), Rh), 'flesh', 0.05)
    add(Ellipsoid(hc + Rh @ v3(0, 0.09, -0.02), (0.20, 0.12, 0.20), Rh), 'hide', 0.04)
    add(bell_hull(hc + Rh @ v3(0.03, 0.30, -0.03), 0.17, 0.02, 0.11, R=Rh @ rot_z(-0.25), power=1.1, lip=0.015), 'iron', 0.0)
    add(Sphere(hc + Rh @ v3(0.03, 0.31, -0.03) + v3(0.01, 0, 0), 0.02), 'lamp', 0.0)
    # eyes: big milky pits with teal pupil
    for sx in (-1, 1):
        ec = hc + Rh @ v3(sx * 0.14, 0.05, 0.14)
        add(Sphere(ec, 0.040), 'eye', 0.0)
        add(Sphere(ec + Rh @ v3(sx * 0.0, 0.0, 0.028), 0.020), 'speck', 0.0)
        add(Torus(ec + Rh @ v3(0, 0, 0.01), Rh[:, 2], 0.042, 0.011), 'iron', 0.0)
    # upper jaw / snout shelf and teeth
    uj = hc + Rh @ v3(0, -0.08, 0.17)
    add(Ellipsoid(uj, (0.20, 0.06, 0.16), Rh), 'hide', 0.03)
    for k in range(7):
        x = -0.15 + k * 0.05
        q = hc + Rh @ v3(x, -0.12, 0.28 - 0.04 * abs(x) * 3)
        add(Capsule(q, q + Rh @ v3(0, -0.08 - 0.02 * (k % 2), 0.0), 0.012, 0.003), 'teeth', 0.0)
    # mouth glow + lower jaw (hinged)
    hinge = hc + Rh @ v3(0, -0.12, 0.02)
    add(Ellipsoid(hc + Rh @ v3(0, -0.12, 0.13), (0.16, 0.03 + 0.18 * opn, 0.12), Rh), 'bile', 0.0)
    jaw = []
    jadd = lambda prim, mat, k=0.0: jaw.append(Part(prim, mat, k))
    jadd(Ellipsoid(hc + Rh @ v3(0, -0.17, 0.15), (0.21, 0.075, 0.19), Rh), 'hide', 0.03)       # the heavy lantern jaw
    jadd(Ellipsoid(hc + Rh @ v3(0, -0.20, 0.30), (0.12, 0.05, 0.08), Rh), 'hide', 0.02)         # chin lump
    for k in range(7):
        x = -0.14 + k * 0.047
        q = hc + Rh @ v3(x, -0.14, 0.27 - 0.05 * abs(x) * 3)
        jadd(Capsule(q, q + Rh @ v3(0, 0.09 + 0.02 * (k % 2), 0.0), 0.012, 0.003), 'teeth', 0.0)
    jadd(Torus(hc + Rh @ v3(0, -0.21, 0.14), Rh[:, 1], 0.17, 0.014), 'iron', 0.0)
    parts.extend(transform_parts(jaw, R=rot_x(opn * 1.1), pivot=hinge))
    # bait lamp on a short stalk over the snout
    s0 = hc + Rh @ v3(0.0, 0.17, 0.08)
    s1 = s0 + Rh @ v3(0.0, 0.14, 0.12)
    s2 = s1 + Rh @ v3(0.0, -0.02, 0.17 + 0.03 * np.sin(2 * np.pi * tl))
    add(Capsule(s0, s1, 0.018, 0.012), 'hide', 0.01)
    add(Capsule(s1, s2, 0.012, 0.008), 'hide', 0.01)
    bulb = s2 + Rh @ v3(0, -0.05, 0.0)
    add(Sphere(bulb, 0.055), 'lamp', 0.0)
    # bile globule in flight
    if sk > 0.3:
        f = min(sk, 1.0)
        mp = hc + Rh @ v3(0, -0.14, 0.28)
        for j in range(4):
            t = f * (0.2 + 0.28 * j)
            q = mp + v3(0, 0.05 * t - 0.12 * t * t, 0.9 * t * (1 if sk >= 1.0 else 0.5))
            add(Sphere(q, 0.06 * (1 - 0.12 * j)), 'bile', 0.04)
    if P['fx'] > 0:
        add(Torus(v3(0, 0.02, 0.55), v3(0, 1, 0), 0.10 + 0.22 * P['fx'], 0.014), 'bile', 0.0)
    parts[:] = transform_parts(creature_place(parts, P), t=(0, 0, 0))
    mats = hadal_mats(P, {
        'hide': Material(cracked_albedo(_hex('#444a7a'), crack=_hex('#14162e'), freq=7, width=0.02, mottle=0.2), spec=0.5, gloss=34, brush=0.05),
        'flesh': Material(cracked_albedo(_hex('#6a70a8'), crack=_hex('#2b2d55'), freq=8, width=0.016, seep=TEAL, mottle=0.18), spec=0.6, gloss=34, sss=0.5, brush=0.04),
        'bile': bile_mat(P),
        'eye': Material(_hex('#d5ddd6'), spec=0.8, gloss=60, emissive=tuple(np.array(TEAL) * 0.12), rim=0.0),
    })
    lights = [teal_light(bulb, P, 0.8, 0.5), Light(hc + Rh @ v3(0, -0.12, 0.30), _hex('#6fe8cf'), 0.9 * (0.4 + opn) * max(pulse(P), 0.2), 0.55)]
    return hadal_finish(P, parts, mats, lights)


ROWS, frames = creature_rows(neutral_pose, sink=(0, 0, 0.10, 0.30), deflate=(0, 0.05, 0.2, 0.5))

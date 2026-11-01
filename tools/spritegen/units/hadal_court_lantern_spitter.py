"""Lantern Spitter (Hadal Court ranged). A glass-skinned gulper: a pale, glossy sac of a body with
glowing veins showing through the skin, a huge hinged gulper jaw, four spindly jointed legs and a whip
tail ending in a lure. Spits luminous brine. Defining detail: the lit veins inside the glass skin.
"""
from _hadal_court_common import *

UNIT_ID = 'hadal_court_lantern_spitter'
CAMERA = Camera(ppm=50)


def neutral_pose():
    return creature_pose()


def glass_material(P):
    g = max(pulse(P), 0) * (1 - P['end'])

    def alb(p, n):
        a = _arr(_hex('#5a6190'), len(p)) * (0.85 + 0.3 * fbm(p, 9, 2)[:, None])
        return a

    def emis(p, n):
        v = np.abs(vnoise(p, 11.0) - 0.5) < 0.025
        w = np.abs(vnoise(p + 4.0, 23.0) - 0.5) < 0.018
        m = (v | w).astype(float) * 0.8
        return np.array(TEAL)[None, :] * (m * g)[:, None]
    return Material(alb, spec=0.6, gloss=60, sss=0.3, emissive=emis, brush=0.02)


def build(P):
    parts, add = new_parts()
    e, st, sk = P['end'], P['stride'], P['strike']
    c = v3(0, 0.78 - 0.25 * e, 0)
    add(Ellipsoid(c, (0.38, 0.38, 0.44)), 'glass', 0.0)
    add(Ellipsoid(c + v3(0, -0.05, -0.30), (0.22, 0.22, 0.25)), 'glass', 0.08)
    # dorsal ridge spines
    for k in range(4):
        q = c + v3(0, 0.33 - 0.04 * k, 0.10 - 0.12 * k)
        add(Capsule(q, q + v3(0, 0.10, -0.05), 0.02, 0.004), 'hide', 0.01)
    # gulper jaw: upper lip plate and big hinged lower pouch
    opn = 0.12 + 0.7 * [0, 0.6, 1.0, 0.4][min(int(sk * 3 + 0.01), 3)] * (sk > 0) + 0.3 * P['cast_glow']
    hinge = c + v3(0, -0.02, 0.10)
    add(Ellipsoid(c + v3(0, 0.02, 0.32), (0.26, 0.10, 0.20)), 'hide', 0.05)
    add(Sphere(c + v3(0, 0.0, 0.33), 0.11), 'maw', 0.0)
    jaw = []
    jadd = lambda prim, mat, k=0.0: jaw.append(Part(prim, mat, k))
    jadd(Ellipsoid(c + v3(0, -0.12, 0.30), (0.30, 0.13, 0.30)), 'glass', 0.0)
    for k in range(7):
        a = -0.8 + k * 0.27
        q = c + v3(np.sin(a) * 0.22, -0.04, 0.30 + np.cos(a) * 0.22)
        jadd(Capsule(q - v3(0, 0.02, 0), q + v3(0, 0.07, 0), 0.016, 0.003), 'teeth', 0.0)
    parts.extend(transform_parts(jaw, R=rot_x(opn), pivot=hinge))
    # eyes: two tiny milky-teal points
    eyes = [c + v3(sx * 0.17, 0.12, 0.30) for sx in (-1, 1)]
    specks(add, eyes, 0.024)
    # legs
    for sx in (-1, 1):
        for sz_, ph in ((1, 1), (-1, -1)):
            g = ph * sx * st
            root = c + v3(sx * 0.22, -0.22, sz_ * 0.14)
            ft = v3(sx * (0.36 + 0.1 * e), 0.10 * max(g, 0), sz_ * 0.26 + 0.12 * g)
            kn = root + v3(sx * 0.20, 0.10, sz_ * 0.04)
            seg_limb(add, [root, kn, ft + v3(0, 0.05, 0), ft], [0.055, 0.045, 0.028, 0.01], 'hide', joint='hide', k=0.01)
    # whip tail with lure
    t0 = c + v3(0, -0.05, -0.45)
    sw = np.sin(2 * np.pi * P['tell']) * 0.12
    pts = [t0, t0 + v3(0.05 + sw, -0.15, -0.25), t0 + v3(0.12 + sw, 0.0, -0.45), t0 + v3(0.10 + sw * 1.5, 0.40, -0.45),
           t0 + v3(0.02 + sw * 2, 0.62, -0.30)]
    seg_limb(add, pts, [0.10, 0.06, 0.035, 0.02, 0.012], 'hide', joint=None, k=0.02)
    lure = pts[-1] + v3(0, -0.04, 0.06)
    add(Sphere(lure, 0.045), 'lamp', 0.0)
    # spit
    if P['fx'] > 0:
        d = norm(v3(0.0, 0.08, 1.0))
        for k in range(4):
            add(Sphere(c + v3(0, 0.0, 0.5) + d * (0.15 + 0.17 * k), 0.06 * P['fx'] * (1 - 0.18 * k)), 'lamp', 0.0)
    parts[:] = transform_parts(creature_place(parts, P), t=(0, 0, 0.05))
    mats = hadal_mats(P, {'glass': glass_material(P),
                          'hide': Material(cracked_albedo(_hex('#4a4f72'), crack=_hex('#1b1d33'), freq=8, width=0.015), spec=0.5, gloss=30)})
    lights = [teal_light(lure + v3(0, P['bob'], 0.05), P, 0.9, 0.6), teal_light(c + v3(0, P['bob'], 0.45), P, 0.25, 0.4)]
    if P['fx'] > 0:
        lights.append(Light(c + v3(0, 0, 0.9), TEAL, 1.3 * P['fx'], 0.8))
    return hadal_finish(P, parts, mats, lights)


ROWS, frames = creature_rows(neutral_pose, sink=(0, 0, 0.1, 0.3))

"""Lantern Spitter (Hadal Court ranged). A glass-skinned gulper: a pale, glossy sac of a body with
glowing veins showing through the skin, a huge hinged gulper jaw, four spindly jointed legs and a whip
tail ending in a lure. Spits luminous brine. Defining detail: the lit veins inside the glass skin.
"""
from _hadal_court_common import *

UNIT_ID = 'hadal_court_lantern_spitter'
CAMERA = Camera(ppm=48)


def neutral_pose():
    return creature_pose()


def glass_material(P):
    g = max(pulse(P), 0) * (1 - P['end'])

    def alb(p, n):
        a = _arr(_hex('#2c3164'), len(p)) * (0.8 + 0.35 * fbm(p, 9, 2)[:, None])
        return a

    def emis(p, n):
        v = np.abs(vnoise(p, 11.0) - 0.5) < 0.025
        w = np.abs(vnoise(p + 4.0, 23.0) - 0.5) < 0.018
        m = (v | w).astype(float) * 0.65
        return np.array(TEAL)[None, :] * (m * g)[:, None]
    return Material(alb, spec=0.9, gloss=70, sss=0.2, emissive=emis, brush=0.02)


def build(P):
    parts, add = new_parts()
    e, st, sk = P['end'], P['stride'], P['strike']
    # Squat and bottom-heavy: a low glass sac slung between splayed legs, capped by a riveted
    # bell-iron dorsal dome (Court shape language), with the gulper jaw hanging forward.
    c = v3(0, 0.50 - 0.22 * e, 0)
    add(Ellipsoid(c + v3(0, -0.04, 0), (0.42, 0.34, 0.46)), 'glass', 0.0)
    add(Ellipsoid(c + v3(0, -0.10, -0.30), (0.28, 0.24, 0.26)), 'glass', 0.08)
    # dorsal dome plate with a riveted rim band and a cracked crown
    add(Ellipsoid(c + v3(0, 0.10, -0.04), (0.40, 0.24, 0.44)), 'shell', 0.02)
    add(Torus(c + v3(0, 0.06, -0.04), (0, 1, 0), 0.40, 0.034), 'shell', 0.02)
    for k in range(3):
        q = c + v3(0, 0.33 - 0.03 * k, 0.04 - 0.14 * k)
        add(Capsule(q, q + v3(0, 0.07, -0.05), 0.025, 0.006), 'hide', 0.01)
    # gulper jaw: upper lip plate and big hinged lower pouch
    opn = 0.12 + 0.7 * [0, 0.6, 1.0, 0.4][min(int(sk * 3 + 0.01), 3)] * (sk > 0) + 0.3 * P['cast_glow']
    hinge = c + v3(0, -0.02, 0.14)
    add(Ellipsoid(c + v3(0, 0.04, 0.36), (0.30, 0.12, 0.22)), 'shell', 0.05)
    add(Sphere(c + v3(0, -0.02, 0.38), 0.13), 'maw', 0.0)
    jaw = []
    jadd = lambda prim, mat, k=0.0: jaw.append(Part(prim, mat, k))
    jadd(Ellipsoid(c + v3(0, -0.16, 0.34), (0.34, 0.16, 0.34)), 'glass', 0.0)
    for k in range(9):
        a = -0.95 + k * 0.24
        q = c + v3(np.sin(a) * 0.27, -0.06, 0.34 + np.cos(a) * 0.27)
        jadd(Capsule(q - v3(0, 0.02, 0), q + v3(0, 0.09, 0), 0.02, 0.004), 'teeth', 0.0)
    parts.extend(transform_parts(jaw, R=rot_x(opn), pivot=hinge))
    # eyes: two tiny milky-teal points on the lip plate
    eyes = [c + v3(sx * 0.19, 0.14, 0.36) for sx in (-1, 1)]
    specks(add, eyes, 0.026)
    # legs: short, thick and bowed out, knees above the body line, feet planted wide
    for sx in (-1, 1):
        for sz_, ph in ((1, 1), (-1, -1)):
            g = ph * sx * st
            root = c + v3(sx * 0.30, -0.02, sz_ * 0.18)
            kn = root + v3(sx * 0.27, 0.12, sz_ * 0.07)
            ft = v3(sx * (0.55 + 0.08 * e), 0.08 * max(g, 0), sz_ * (0.08 if sz_ > 0 else 0.24) + 0.10 * g)
            seg_limb(add, [root, kn, ft + v3(0, 0.08, 0), ft], [0.085, 0.07, 0.05, 0.03], 'hide', joint='shell', k=0.02)
    # whip tail with lure
    t0 = c + v3(0, 0.0, -0.48)
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
    parts[:] = transform_parts(squash_parts(creature_place(parts, P), sy=1.10, sxz=1.10), t=(0.12, 0, -0.30))
    mats = hadal_mats(P, {'glass': glass_material(P),
                          'shell': bell_metal(c, np.eye(3), base=_hex('#363a52'), spacing=0.16, barn=0.35),
                          'hide': Material(cracked_albedo(_hex('#4a4f72'), crack=_hex('#1b1d33'), freq=8, width=0.015), spec=0.5, gloss=30)})
    lights = [teal_light(lure + v3(0, P['bob'], 0.05), P, 0.9, 0.6), teal_light(c + v3(0, P['bob'], 0.45), P, 0.25, 0.4)]
    if P['fx'] > 0:
        lights.append(Light(c + v3(0, 0, 0.9), TEAL, 1.3 * P['fx'], 0.8))
    # lights follow the 1.10x body scale and offset applied to the parts above
    for L in lights:
        L.pos = v3(*(np.array(L.pos) * 1.10)) + v3(0.12, 0, -0.30)
    return hadal_finish(P, parts, mats, lights)


ROWS, frames = creature_rows(neutral_pose, sink=(0, 0, 0.1, 0.3))

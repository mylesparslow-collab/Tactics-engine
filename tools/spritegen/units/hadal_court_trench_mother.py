"""Trench Mother (Hadal Court exotic summoner). Brood-mother of the trench floors rising out of her
pressure-bell: a vast ribbed bell shell, a pale flesh torso and small domed head emerging from its crown,
long arms spread to birth spawn, tendrils spilling from the rim, small Pit Thrall brood clinging on.
Defining detail: a teal pulse ripple travelling down the shell (the idle tell).
"""
from _hadal_court_common import *

UNIT_ID = 'hadal_court_trench_mother'
CAMERA = Camera(ppm=44)


def neutral_pose():
    return creature_pose()


def shell_material(P, top, R):
    base = banded_albedo(_hex('#3d4266'), _hex('#2a2e4a'), top, R, spacing=0.26, width=0.04, rivet=_hex('#7d84a0'),
                         barn=0.12, patina=VERDI, patina_amt=0.2)
    ph = P.get('tell', 0.0)
    amp = max(pulse(P), 0) * (1 - P['end'])

    def emis(p, n):
        q = (p - top) @ R
        y = -q[:, 1] / 1.75
        w = np.exp(-((y - (ph % 1.0)) / 0.06) ** 2) + 0.5 * np.exp(-((y - ((ph + 0.5) % 1.0)) / 0.05) ** 2)
        crack = np.abs(vnoise(p, 7.0) - 0.5) < 0.05
        return np.array(TEAL)[None, :] * (w * (0.25 + 0.9 * crack) * amp)[:, None]
    return Material(base, spec=0.5, gloss=28, metal=0.3, emissive=emis, brush=0.05)


def build(P):
    parts, add = new_parts()
    e, sk, cg = P['end'], P['strike'], P['cast_glow']
    top = v3(0, 1.80, -0.12)
    R = rot_x(0.10)
    add(bell_hull(top, 1.70, 0.32, 0.86, R=R, power=1.25, sz=0.85, lip=0.08, ribs=0.05, ribs_n=9), 'shell', 0.0)
    # crown opening collar and the emerging body
    add(Torus(top + v3(0, -0.02, 0), R[:, 1], 0.30, 0.05), 'iron', 0.02)
    ch = top + v3(0, 0.18, 0.08)
    add(Ellipsoid(ch, (0.22, 0.24, 0.17)), 'flesh', 0.0)
    hd = ch + v3(0, 0.30, 0.06)
    add(Capsule(ch, hd, 0.07), 'flesh', 0.04)
    dome_helm(add, hd, rot_x(0.2), r=0.12, mat='helm', ports=3, rim='iron')
    # arms spread wide (lash on strike, raise on cast)
    for sx in (-1, 1):
        sh = ch + v3(sx * 0.20, 0.10, 0)
        lash = sk if sx == -1 else 0.2 * sk
        el = sh + v3(sx * 0.28, -0.04 + 0.25 * cg, 0.10 + 0.25 * lash)
        wr = el + v3(sx * (0.20 - 0.18 * lash), -0.02 + 0.25 * cg - 0.2 * lash, 0.12 + 0.45 * lash)
        seg_limb(add, [sh, el, wr], [0.075, 0.06, 0.045], 'flesh', joint='iron', k=0.02)
        for f in (-1, 0, 1):
            add(Capsule(wr, wr + norm(wr - el) * 0.14 + v3(0, f * 0.05, f * 0.04), 0.018, 0.006), 'flesh', 0.01)
        if cg > 0:
            add(Sphere(wr + v3(0, 0.1, 0), 0.05 * cg), 'lamp', 0.0)
    # tendrils from the rim
    for k in range(7):
        a = -2.4 + k * 0.8
        if k in (1, 2):
            continue
        r0 = v3(np.sin(a) * 0.80, 0.18, np.cos(a) * 0.68 - 0.12)
        dirn = v3(np.sin(a), 0, np.cos(a))
        w = np.sin(2 * np.pi * P['tell'] + k) * 0.06
        pts = [r0, r0 + dirn * 0.12 + v3(w, -0.12, 0), r0 + dirn * 0.22 + v3(-w, -0.15, w), r0 + dirn * 0.30 + v3(w, -0.14, 0)]
        seg_limb(add, pts, [0.06, 0.045, 0.03, 0.012], 'flesh', joint=None, k=0.02)
    # brood: small thralls clinging on the shell
    brood = [(-0.48, 0.95, 0.52), (0.50, 0.70, 0.55), (0.12, 1.30, 0.46), (-0.30, 0.40, 0.78)]
    tips = []
    for i, (x, y, z) in enumerate(brood):
        c = v3(x, y, z)
        add(Ellipsoid(c, (0.08, 0.10, 0.07)), 'hide', 0.02)
        add(bell_hull(c + v3(0, 0.15, 0.02), 0.11, 0.035, 0.06, power=0.7, lip=0.01), 'iron', 0.0)
        add(Sphere(c + v3(0, 0.16, 0.03), 0.017), 'lamp', 0.0)
        tips.append(c)
    # vent at her base
    add(Ellipsoid(v3(0, 0.02, 0.10), (0.62, 0.04, 0.5)), 'barnacle', 0.05)
    parts[:] = transform_parts(creature_place(parts, P), t=(0.27, 0, -0.30), s=0.88)
    mats = hadal_mats(P, {
        'shell': shell_material(P, top, R),
        'helm': bell_metal(hd, np.eye(3), base=_hex('#58607f'), spacing=0.3, barn=0),
    })
    lights = [teal_light(hd + v3(0, P['bob'], 0.18), P, 0.5, 0.5),
              teal_light(v3(0, 1.0 + P['bob'], 0.75), P, 0.4, 0.8, phase=0.25)]
    if cg > 0:
        lights.append(Light(v3(0, 1.8, 0.4), TEAL, 1.2 * cg, 1.0))
    return hadal_finish(P, parts, mats, lights)


ROWS, frames = creature_rows(neutral_pose, sink=(0, 0, 0.15, 0.45), deflate=(0, 0.05, 0.3, 0.7))

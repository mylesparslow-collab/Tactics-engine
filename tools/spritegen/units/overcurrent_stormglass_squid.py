"""Stormglass Squid (Overcurrent, burst ranged). A squid with a glass-clear mantle and a live lightning bolt
forked inside it: ringed glass cartilage bands, arrowhead fins, a hooded head with two big cyan-ringed eyes, eight
short arms and two long club tentacles that spark. Defining detail: the caged lightning in the glass mantle.
Tell: the bolt flickers and re-forks; the tentacles coil and snap on the attack, arcing to the target."""
from _overcurrent_common import *

UNIT_ID = 'overcurrent_stormglass_squid'
CAMERA = Camera(ppm=50)
BOLT = _hex('#e6fcff')


def neutral_pose():
    return pose()


def bolt_pts(ph, flick):
    """Forked bolt zig-zag along the mantle axis (local coords): list of (point) main + fork."""
    base = [(0.0, 0.0), (0.06, 0.16), (-0.05, 0.30), (0.07, 0.46), (-0.04, 0.62), (0.05, 0.80)]
    sh = 0.03 * np.sin(ph * 3 + np.arange(6) * 1.7) * (0.4 + flick)
    return [(x + s, h) for (x, h), s in zip(base, sh)]


def build(P):
    parts, add = new_parts()
    ph, st, op = P['ph'], P['strike'], P['open']
    flick = 0.5 + 0.5 * np.sin(2 * np.pi * P['tell'] * 2 + 0.6)
    # mantle axis: from head (0, 0.72, 0.05) rising up and back
    A = v3(0, 0.78, 0.0)
    D = norm(v3(-0.22, 1.0, -0.38))
    side = norm(np.cross(D, v3(0, 0, 1)))
    up2 = np.cross(side, D)
    n = 14
    axis = [A + D * (1.05 * i / (n - 1)) for i in range(n)]
    rad = [0.22 * (0.55 + 0.45 * np.sin(np.pi * (0.15 + 0.85 * i / (n - 1)) ** 0.8)) if i < n - 1 else 0.02 for i in range(n)]
    rad = [r * (1.0 + 0.04 * np.sin(ph + i * 0.7)) for i, r in enumerate(rad)]
    for i in range(n - 1):
        add(Capsule(axis[i], axis[i + 1], rad[i], rad[i + 1]), 'glass', 0.05)
    # glass cartilage rings and a ridge spine
    for i in (2, 4, 6, 8, 10):
        add(Torus(axis[i], D, rad[i] * 1.02, 0.012), 'ring', 0.0)
    for i in range(1, n - 2):
        add(Capsule(axis[i] + up2 * rad[i] * 0.98, axis[i + 1] + up2 * rad[i + 1] * 0.98, 0.014, 0.014), 'ring', 0.0)
    # arrowhead fins
    for s in (-1, 1):
        r0, r1 = axis[8], axis[12 if n > 12 else n - 1]
        tipf = axis[7] + side * s * 0.5 + D * 0.05
        fin(add, axis[10] - D * 0.1, tipf + D * 0.08, 0.26, 'fin', 0.016, wide=D)
        fin(add, axis[10] + D * 0.15, axis[n - 1] + side * s * 0.3 - D * 0.1, 0.12, 'fin', 0.016, wide=D)
    # head and funnel
    add(Ellipsoid(A + v3(0, -0.04, 0.10), (0.17, 0.15, 0.17), None), 'skin', 0.08)
    for s in (-1, 1):
        ec = A + v3(s * 0.15, -0.0, 0.14)
        add(Sphere(ec, 0.11), 'eyeball', 0.04)
        d = norm(v3(s * 0.7, -0.05, 0.7))
        add(Torus(ec + d * 0.065, d, 0.075, 0.018), 'glow', 0.0)
        add(Sphere(ec + d * 0.085, 0.055), 'pupil', 0.0)
    # arms: eight short, curling down and forward; two long club tentacles
    tips = []
    for i in range(8):
        u = (i - 3.5) / 3.5
        a = u * 1.15
        base = A + v3(np.sin(a) * 0.12, -0.12, 0.16 + np.cos(a) * 0.04)
        out = norm(v3(np.sin(a) * 0.9, -0.55, np.cos(a) * 0.6 + 0.2))
        sw = 0.05 * np.sin(ph + i * 1.3)
        p1 = base + out * 0.22 + v3(sw, 0, 0)
        p2 = base + out * 0.44 + v3(sw * 1.6, -0.06, 0.04)
        p3 = base + out * 0.60 + v3(sw * 2, 0, 0.12 * (1 - abs(u)))
        p2 = v3(p2[0], max(p2[1], 0.10), p2[2])
        p3 = v3(p3[0], max(p3[1], 0.08), p3[2])
        tube(add, [base, p1, p2, p3], [0.05, 0.042, 0.03, 0.008], 'skin', n=8, k=0.02)
        tips.append(p3)
    tent = []
    for s in (-1, 1):
        base = A + v3(s * 0.05, -0.14, 0.2)
        reach = 0.55 + 0.9 * st
        end = base + norm(v3(s * 0.25, -0.35 + 0.25 * st, 0.9)) * reach * 1.0
        end = v3(end[0], max(end[1], 0.14), end[2])
        mid = (base + end) / 2 + v3(s * 0.12 * (1 - st), -0.1, 0.0) + v3(0.06 * np.sin(ph + s), 0.08 * np.cos(ph), 0)
        mid = v3(mid[0], max(mid[1], 0.12), mid[2])
        tube(add, [base, mid, end], [0.03, 0.022, 0.02], 'skin', n=9, k=0.02)
        add(Ellipsoid(end + v3(0, 0, 0.04), (0.06, 0.06, 0.09), None), 'club', 0.03)
        for j in range(4):
            q = end + v3(s * 0.04 * np.cos(j * 1.6), 0.04 * np.sin(j * 1.6), 0.06)
            add(Sphere(q, 0.016), 'bolt', 0.0)
        tent.append(end)
    # spark arcs off the club tips (stronger on attack/cast)
    sp = 0.25 + 0.75 * max(st, P['cast_glow'], P['fx'])
    rng = np.random.default_rng(int(ph * 10) % 7 + 1)
    for s_i, e in enumerate(tent):
        prev = e + v3(0, 0.0, 0.1)
        for j in range(4):
            nxt = prev + v3(rng.normal(0, 0.07), rng.normal(0, 0.06) + 0.02, 0.12 * sp + 0.05)
            add(Capsule(prev, nxt, 0.009 * (1 + sp), 0.007), 'bolt', 0.0)
            prev = nxt
    # inside the mantle: the lightning, painted through the glass as hot organs
    pl = Placer(P, yaw=0.15, hover=0.30, shift=0.0, back=0.0)
    organs = []
    bp = bolt_pts(ph, flick)
    dense = []
    for (a, b) in zip(bp[:-1], bp[1:]):
        for t in np.linspace(0, 1, 5, endpoint=False):
            dense.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    for (x, h) in dense:
        c = A + D * (0.08 + h * 0.95 * 0.9) + side * x * 3.0
        organs.append(Organ(pl.pt(c), (0.024, 0.032, 0.024), BOLT, 1.6 + 0.9 * flick + 0.8 * P['cast_glow'], 1.0))
    for (x, h), sg in ((bp[2], 1), (bp[4], -1)):
        c = A + D * (0.08 + h * 0.95 * 0.9) + side * (x + sg * 0.05) * 3.0
        organs.append(Organ(pl.pt(c), (0.02, 0.03, 0.02), BOLT, 1.2 + 0.7 * flick, 0.95))
    organs.append(Organ(pl.pt(A + D * 0.22 + side * 0.01), (0.11, 0.1, 0.11), _hex('#7fe8ee'), 0.5, 0.7))      # ink-gland glow
    organs.append(Organ(pl.pt(A + D * 0.35 + up2 * 0.06), (0.05, 0.12, 0.05), _hex('#d8506a'), 0.1, 0.8))
    mats = std_mats(P, {
        'glass': jelly(organs, glow=0.2, tint=_hex('#6fa3d0'), depth=0.8, local=pl.inv, spec=1.0),
        'ring': Material(_hex('#d6ecf8'), spec=0.9, gloss=70, emissive=tuple(np.array(CYAN) * 0.22), sss=0.3),
        'fin': skin(top=_hex('#a8d6ec'), under=_hex('#e8f4fc'), glow=0.8, mottle=0.05, spec=0.5, wet=60, local=pl.inv, veins=0.3, vein_col=_hex('#6aa8d0')),
        'skin': skin(top=_hex('#a8c6de'), under=_hex('#f2eeff'), glow=0.9, mottle=0.08, local=pl.inv, veins=0.3, vein_col=_hex('#c4344a'), spec=0.35, wet=50),
        'eyeball': Material(_hex('#e6f0f8'), spec=1.0, gloss=90, sss=0.2),
        'club': Material(_hex('#d6ecf8'), spec=0.8, gloss=60, emissive=tuple(np.array(CYAN) * 0.35)),
        'bolt': Material(BOLT, emissive=tuple(np.array(BOLT) * (1.2 + 0.8 * st + 0.7 * flick) * max(P['glow'], 0.1)), rim=0.0)})
    lights = [under_light(P, v3(0, 0.15, 0.2), 1.0, 1.6),
              Light(pl.pt(A + D * 0.5), BOLT, (0.9 + 0.7 * flick + 0.8 * P['cast_glow']) * max(P['glow'], 0.0), 1.1)]
    dp = [pl.pt(tips[1] + v3(0, 0.1, 0)), pl.pt(tips[6] + v3(0, 0.1, 0))]

    def world(add2):
        drips(add2, P, dp, rise=0.25)
        spray(add2, P, pl.pt(v3(0, 1.0, 0.5)))
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.2, 0.6, 1.0, 0.3), atk_strike=(0.0, 0.5, 1.0, 0.3))

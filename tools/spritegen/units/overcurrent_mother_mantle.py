"""Mother Mantle, the Hook-Armed Deep (Overcurrent hero). A colossal squid reared up out of the sky-sea: a pale
translucent mantle like a sail with its organs showing, a door-sized never-blinking eye ringed in gold-pearl,
eight spread arms whose suckers turned out to be rotating hooks, and a beak that works behind them. Ink curls from
the funnel. Defining detail: the great eye with its thin gold-pearl ring. Tell: arms curl, ink drifts, eye holds still."""
from _overcurrent_common import *

UNIT_ID = 'overcurrent_mother_mantle'
CAMERA = Camera(ppm=44)


def neutral_pose():
    return pose()


def build(P):
    parts, add = new_parts()
    ph, st, op = P['ph'], P['strike'], P['open']
    # mantle: tall translucent torpedo leaning back, with rhomboid fins at the tip
    mp = [v3(0, 1.00, 0.0), v3(0, 1.45, -0.20), v3(0, 1.85, -0.42), v3(0, 2.18, -0.68)]
    ms = tube(add, mp, [0.30, 0.36, 0.28, 0.04], 'skin', n=12, k=0.05)
    for sx in (-1, 1):
        add(Ellipsoid(v3(sx * 0.27, 1.98 + 0.02 * np.sin(ph), -0.60), (0.30, 0.025, 0.20), rot_y(sx * 0.1) @ rot_z(sx * 0.35 * np.sin(ph * 0.7 + 1) * 0.3)), 'fin', 0.03)
    # head and the door-sized eye
    add(Ellipsoid(v3(0, 0.92, 0.12), (0.33, 0.28, 0.30), None), 'skin', 0.1)
    ec = v3(-0.30, 0.98, 0.20)
    add(Sphere(ec, 0.21), 'eyeball', 0.05)
    d = norm(v3(-0.55, 0.0, 0.85))
    add(Torus(ec + d * 0.165, d, 0.115, 0.018), 'gold', 0.0)
    add(Sphere(ec + d * 0.16, 0.085), 'pupil', 0.0)
    add(Ellipsoid(ec + v3(0.0, 0.18, 0.0), (0.2, 0.05, 0.2), None), 'skin', 0.05)
    add(Sphere(v3(0.25, 0.98, 0.26), 0.12), 'eyeball', 0.04)
    # funnel, beak
    add(Capsule(v3(0.12, 0.82, 0.28), v3(0.30, 0.70, 0.42), 0.06, 0.04), 'skin', 0.03)
    bk = v3(0.0, 0.70, 0.40)
    add(Ellipsoid(bk, (0.06, 0.07 + 0.05 * op, 0.09), None), 'beak', 0.0)
    add(Capsule(bk + v3(0, 0.0, 0.05), bk + v3(0, -0.12 - 0.08 * op, 0.14), 0.04, 0.008), 'beak', 0.0)
    add(Capsule(bk + v3(0, 0.03, 0.05), bk + v3(0, 0.09, 0.15 + 0.04 * op), 0.035, 0.008), 'beak', 0.0)
    # eight arms spreading forward and down, hooks along the camera-side
    hooks = 0
    tips = []
    for i in range(8):
        u = (i - 3.5) / 3.5                       # -1 .. 1 across the spread
        a = u * 1.25
        base = v3(np.sin(a) * 0.22, 0.78 - 0.04 * abs(u), 0.28 + np.cos(a) * 0.08)
        out = norm(v3(np.sin(a) * 1.0, -0.15, np.cos(a) * 0.55 + 0.25))
        L = 1.05 + 0.20 * (1 - abs(u))
        reach = 1.0 + 0.45 * st * (1 - abs(u) * 0.5)
        sw = 0.12 * np.sin(ph + i * 1.1)
        p1 = base + out * 0.35 * reach + v3(0, -0.10, 0)
        p2 = base + out * 0.70 * reach + v3(sw, -0.38, 0.04 * i % 3 * 0.1)
        p3 = base + out * 1.0 * reach * (L / 1.2) + v3(sw * 1.5, -0.52, 0.0)
        p3 = v3(p3[0], max(p3[1], 0.06), p3[2])
        p2 = v3(p2[0], max(p2[1], 0.10), p2[2])
        tip = p3 + v3(-np.sign(u + 1e-3) * 0.10 * np.sin(ph + i), 0.16 + 0.1 * np.sin(ph * 1.3 + i), 0.10)
        sp = tube(add, [base, p1, p2, p3, tip], [0.085, 0.075, 0.06, 0.04, 0.012], 'skin', n=8, k=0.03)
        tips.append(tip)
        for j in range(1, 7):
            q = sp[j]
            t = norm(sp[j + 1] - sp[j - 1])
            o = norm(np.cross(t, v3(0, 1, 0)))
            o = o if o[2] > 0 else -o
            r = 0.07 - 0.008 * j
            add(Capsule(q + o * r * 0.7, q + o * (r + 0.12), 0.022, 0.007), 'hook', 0.0)
            add(Capsule(q + o * (r + 0.12), q + o * (r + 0.10) + t * 0.08 - v3(0, 0.04, 0), 0.011, 0.004), 'hookred', 0.0)
    pl = Placer(P, yaw=0.40, hover=0.06, shift=-0.10, back=0.55, scale=0.80)
    organs = [Organ(pl.pt(v3(0, 1.40, -0.18)), (0.15, 0.30, 0.14), _hex('#e08aa0'), 0.0, 0.8),
              Organ(pl.pt(v3(0, 1.80, -0.38)), (0.10, 0.20, 0.10), _hex('#101428'), 0.0, 0.85),
              Organ(pl.pt(v3(0.09, 1.20, -0.08)), (0.07, 0.10, 0.07), _hex('#c4344a'), 0.0, 0.9),
              Organ(pl.pt(v3(-0.12, 1.55, -0.28)), (0.06, 0.12, 0.06), _hex('#7fe8ee'), 0.5, 0.9)]
    mats = std_mats(P, {'skin': skin(organs=organs, veins=0.45, glow=0.8, local=pl.inv, depth=0.6, spec=0.4, mottle=0.06),
                        'eyeball': Material(_hex('#f0e6d2'), spec=1.0, gloss=90, sss=0.3),
                        'hook': Material(_hex('#f2e8e4'), spec=0.7, gloss=70, emissive=tuple(np.array(RED) * 0.12)),
                        'hookred': Material(RED, spec=0.6, gloss=50, emissive=tuple(np.array(RED) * 0.2)),
                        'beak': Material(_hex('#3a1426'), spec=0.7, gloss=50)})
    lights = [under_light(P, v3(0, 0.2, 0.2), 1.1, 1.8)]
    dp = [pl.pt(tips[1] + v3(0, 0.1, 0)), pl.pt(tips[6] + v3(0, 0.1, 0))]

    def world(add2):
        drips(add2, P, dp, rise=0.2)
        # ink curling from the funnel
        if P['end'] < 0.7:
            for k, (dx, dy, dz, r) in enumerate([(0.0, 0.0, 0.0, 0.10), (0.18, 0.08, 0.10, 0.13), (0.34, 0.20, 0.06, 0.16), (0.52, 0.34, 0.12, 0.13), (0.68, 0.52, 0.10, 0.10)]):
                q = pl.pt(v3(0.34 + dx * 0.8, 0.70 + dy, 0.44 + dz))
                add2(Sphere(q + v3(0.04 * np.sin(ph + k), 0.03 * np.cos(ph + k), 0), r * (1 + 0.5 * P['cast_glow'])), 'ink', 0.05)
        spray(add2, P, pl.pt(v3(0, 1.0, 0.7)))
        ripple(add2, P)
    mats['ink'] = Material(_hex('#14224a'), spec=0.3, gloss=20, rim=0.6, emissive=tuple(np.array(CYAN) * 0.04))
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.3, 1.0, 0.0, 0.3), atk_strike=(0.0, 0.5, 1.0, 0.3), idle_amp=0.7)

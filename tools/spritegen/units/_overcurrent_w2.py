"""Wave-2 Overcurrent helpers: a structured cloud-whale sculpt shared by the Calf and Old Sounding."""
from _overcurrent_common import *


def whale(add, P, L=1.0, head=1.0, y0=0.95, scars=False, barn=0, flip=1.0, fluke=1.0, mouth=0.3, rainy=0, jaw_open=0.0, seed=3, tail_lift=0.0):
    """Cloud-whale in local space (+z forward, y up), body length about 2.3*L, centred near (0, y0, 0).
    Returns dict of anchor points: head, belly points for rain, flukes."""
    rng = np.random.default_rng(seed)
    ph, st = P['ph'], P['strike']
    sw = np.sin(ph)
    # spine: tail -> head, with an undulation travelling down the body
    zs = np.array([-1.25, -0.95, -0.55, -0.1, 0.35, 0.78, 1.10]) * L
    ys = np.array([0.10, 0.06, 0.0, -0.02, -0.01, 0.0, -0.04])
    for i, z in enumerate(zs):
        ys[i] += 0.07 * L * np.sin(ph - z * 2.2) * (1.0 - 0.6 * (z > 0))
    ys = ys + tail_lift * np.clip(-zs / 1.25 / L, 0, 1) ** 1.6 * L
    rad = np.array([0.04, 0.10, 0.21, 0.31, 0.35, 0.33, 0.27]) * L
    rad = rad * np.array([1, 1, 1, 1.0, 1.0, 1.0 * head, 1.0 * head ** 0.8])
    pts = [v3(0.0, y0 + ys[i], zs[i]) for i in range(len(zs))]
    sp = tube(add, pts, list(rad), 'skin', n=24, k=0.10)
    # big blunt head: upper skull dome and lower jaw
    hc = v3(0, y0 + 0.02 * L, 0.98 * L)
    add(Ellipsoid(hc + v3(0, 0.05 * L, 0.06 * L), (0.34 * L * head, 0.28 * L * head, 0.40 * L * head), None), 'skin', 0.12)
    jo = 0.10 * jaw_open * L
    jc = v3(0, y0 - 0.14 * L - jo, 1.02 * L)
    add(Ellipsoid(jc, (0.31 * L * head, 0.16 * L * head, 0.38 * L * head), rot_x(0.10 * jaw_open)), 'skin', 0.08)
    # mouth line: dark gum slit between jaws, with a pearl baleen comb hanging from the upper jaw
    mz = 1.12 * L
    add(Ellipsoid(v3(0, y0 - 0.07 * L - 0.5 * jo, mz - 0.02), (0.30 * L * head, 0.025 * L + 0.4 * jo, 0.33 * L * head), None), 'maw', 0.02)
    for s in (-1, 1):
        for j in range(11):
            t = j / 10
            z = lerp(0.80, 1.36, t) * L
            x = s * 0.30 * L * head * np.sqrt(max(0.0, 1 - ((z - 1.05 * L) / (0.38 * L)) ** 2)) * 0.94
            q = v3(x, y0 - 0.06 * L - 0.4 * jo, z)
            add(Capsule(q, q + v3(0, -(0.075 + 0.05 * jaw_open) * L, 0.005), 0.012 * L, 0.004), 'baleen', 0.0)
    # eyes: small, dark, deep, with a pale socket
    for s in (-1, 1):
        ec = v3(s * 0.335 * L * head, y0 + 0.02 * L, 0.80 * L)
        add(Sphere(ec, 0.075 * L), 'eyesock', 0.04)
        add(Sphere(ec + v3(s * 0.035, 0.0, 0.03) * L, 0.050 * L), 'eyeb', 0.0)
        add(Sphere(ec + v3(s * 0.062, 0.025, 0.05) * L, 0.014 * L), 'bonef', 0.0)
    # blowhole
    add(Ellipsoid(v3(0, y0 + 0.30 * L * head, 0.55 * L), (0.07 * L, 0.02 * L, 0.04 * L), None), 'maw', 0.02)
    # ventral pleats: glowing ridges from chin to navel
    for k in range(-3, 4):
        a = k * 0.17
        prev = None
        for j in range(10):
            z = lerp(1.2, -0.1, j / 9) * L
            yb = np.interp(z, zs, ys) + y0
            rr = np.interp(z, zs, rad) * (0.99 if abs(k) < 3 else 0.97)
            q = v3(np.sin(a) * rr, yb - np.cos(a) * rr, z)
            if prev is not None:
                add(Capsule(prev, q, 0.014 * L, 0.014 * L), 'pleat', 0.0)
            prev = q
    # flippers: long, curved, with finger ridges
    for s in (-1, 1):
        root = v3(s * 0.28 * L, y0 - 0.17 * L, 0.45 * L)
        fl = 0.12 * np.sin(ph + (0 if s > 0 else 1.5)) + 0.35 * st
        tip = root + v3(s * 0.55 * L * flip, -0.52 * L * flip + fl * L * 0.4, -0.30 * L * flip)
        fin(add, root, tip, 0.19 * L * flip, 'fin', 0.03 * L, wide=(0, 0.2, 1.0))
        for j in range(3):
            tt = 0.35 + 0.25 * j
            q = root + (tip - root) * tt
            add(Capsule(q + v3(0, 0.02, 0.0), q + v3(s * 0.08, -0.12, -0.14) * L * 0.5 * flip, 0.014 * L, 0.006 * L), 'bonef', 0.0)
    # tail stock to flukes: two big leaves, undulating
    tail = pts[0]
    for s in (-1, 1):
        tip = tail + v3(s * 0.75 * L * fluke, 0.10 * L * np.sin(ph - 1.2) + 0.05 * L, -0.34 * L * fluke)
        fin(add, tail + v3(0, 0, 0.1 * L), tip, 0.24 * L * fluke, 'fin', 0.03 * L, wide=(0, 0.1, 1.0))
    # dorsal hump
    add(Ellipsoid(v3(0, y0 + 0.30 * L + 0.04 * L, -0.55 * L), (0.045 * L, 0.10 * L, 0.14 * L), rot_x(-0.5)), 'skin', 0.04)
    # barnacles: little pale cones in rough clusters (head, jaw line, flipper roots)
    bpos = []
    for i in range(barn):
        c0 = [(-0.2, 0.28, 0.9), (0.22, 0.30, 0.95), (0.0, 0.34, 0.72), (-0.30, 0.0, 1.15), (0.30, -0.02, 1.2), (-0.33, 0.1, 0.3), (0.33, 0.12, 0.1), (0.0, 0.34, 0.05)][i % 8]
        o = v3(*c0) * L + v3(rng.normal(0, 0.05), rng.normal(0, 0.03), rng.normal(0, 0.05)) * L
        o = v3(o[0], y0 + o[1], o[2])
        n = norm(v3(o[0], (o[1] - y0) * 1.3 + 0.1, 0.2))
        for dd in ((0, 0, 0), (0.05, 0.0, 0.03), (-0.03, 0.02, 0.05)):
            o2 = o + v3(*dd) * L
            add(Capsule(o2, o2 + n * 0.07 * L, 0.036 * L, 0.02 * L), 'barn', 0.01)
            add(Sphere(o2 + n * 0.075 * L, 0.018 * L), 'bonef', 0.0)
        bpos.append(o)
    return dict(zs=zs, ys=ys, rad=rad, y0=y0, tail=tail, head=hc)


def cloud_mantle(add, P, L, y0, n=9, seed=5, big=1.0, trail=0.0, info=None):
    """Cloud puffs clinging along the back, shredding rearward."""
    rng = np.random.default_rng(seed)
    ph = P['ph']
    out = []
    for i in range(n):
        t = i / (n - 1)
        z = lerp(0.65, -1.1, t) * L
        x = rng.normal(0, 0.12) * L
        y = y0 + (0.33 - 0.12 * t) * L + 0.03 * np.sin(ph + i)
        if info is not None:
            y = y0 + np.interp(z, info['zs'], info['ys']) + np.interp(z, info['zs'], info['rad']) * 0.95 + 0.03 * np.sin(ph + i)
        r = (0.17 - 0.06 * t + 0.03 * rng.random()) * L * big
        add(Sphere(v3(x, y, z), r), 'cloud', 0.10)
        out.append(v3(x, y, z))
    return out


def rain_curtain(add, P, anchors, ground=0.04, n_each=2, L=0.7, thick=0.011, seed=9):
    rng = np.random.default_rng(seed)
    if P['end'] > 0.5:
        return
    for i, a in enumerate(anchors):
        for k in range(n_each):
            tt = (P['tell'] + i * 0.23 + k * 0.5) % 1.0
            off = v3(rng.normal(0, 0.07), 0, rng.normal(0, 0.07))
            top = a[1] - tt * 0.35
            ln = L * (0.6 + 0.5 * rng.random())
            bot = max(top - ln, ground)
            if top - bot > 0.05:
                add(Capsule(v3(a[0], top, a[2]) + off, v3(a[0], bot, a[2]) + off, thick, thick * 0.4), 'rain', 0.0)


def whale_mats(P, pl, scars=False, organs=(), old=False):
    top = _hex('#9fb8d4') if not old else _hex('#8fa6c0')
    under = _hex('#f1eeff')

    def spots(q, n):
        col = np.zeros((len(q), 3))
        m = np.zeros(len(q), dtype=bool)
        if scars:
            sc = (np.abs(np.sin(q[:, 2] * 7.0 + q[:, 1] * 11.0 + q[:, 0] * 3.0)) > 0.975) & (fbm(q + 7.0, 3.0, 2) > 0.48)
            sc2 = np.abs(np.sin(q[:, 2] * 5.0 - q[:, 1] * 9.0 + 2.0)) > 0.985
            sc2 &= (q[:, 0] > 0.0) & (q[:, 2] > 0.2)
            m = sc | sc2
            col[:] = _hex('#f4f6ff')
        return m, col
    sk = skin(top=top, under=under, organs=list(organs), veins=0.25 if not old else 0.35, vein_col=_hex('#6f86ae'), glow=0.95, spots=spots,
              local=pl.inv, mottle=0.07, spec=0.3, wet=50, depth=0.5, brush=0.0)
    return sk

__all__ = [n for n in dir() if not n.startswith('__')]

"""Wave-2 Gyre helpers (append-only): new bird species (tern, cormorant, gannet), oilcloth pouch, letter,
clay bomb jars with a sling net, spray/salt trail, kite and perch props."""
from _gyre_common import *
from _gyre_common import _sp, _arr

# ---------------------------------------------------------------- species

SPECIES['tern'] = _sp(
    k=0.98, body=(0.115, 0.115, 0.37), neck=0.26, neck_th=0.055, headr=(0.066, 0.062, 0.088),
    beak_len=0.20, beak_d=0.030, hook=0.012, beak_mat='beak',
    L_in=0.36, L_out=0.68, ch_root=0.22, ch_wrist=0.15, ch_tip=0.028, lead=0.04, th=0.022,
    dihedral=0.16, amp_in=0.40, amp_out=0.55, sweep_in=0.12, sweep_out=0.52, teeth=(8, 0.03, 0.5),
    tail_len=0.50, tail_w=(0.035, 0.16), tail_notch=0.34, tail_th=0.012,
    col=dict(mantle=mix(SLATE, GUANO, 0.42), covert=mix(SLATE, GUANO, 0.52), flight=mix(SLATE, GUANO, 0.15),
             tip=INK, spot=None),
    back=mix(SLATE, GUANO, 0.45), belly=GUANO, head=INK, neckc=GUANO, tailc=GUANO,
    saddle=(0.20, -0.03), nf=10, cov=0.38, tip_t=0.82)

SPECIES['cormorant'] = _sp(
    k=1.10, body=(0.150, 0.140, 0.42), neck=0.40, neck_th=0.052, headr=(0.060, 0.058, 0.095),
    beak_len=0.22, beak_d=0.034, hook=0.045, beak_mat='beak_bone', tip_mat='beak_ink', gloss=True,
    L_in=0.44, L_out=0.52, ch_root=0.30, ch_wrist=0.24, ch_tip=0.05, lead=0.05, th=0.028,
    dihedral=0.14, amp_in=0.45, amp_out=0.5, sweep_in=0.14, sweep_out=0.40, teeth=(8, 0.05, 0.5),
    tail_len=0.34, tail_w=(0.05, 0.12), tail_notch=0.0,
    col=dict(mantle=mix(INK, SLATE, 0.22), covert=mix(INK, hx('#3e5a5c'), 0.35), flight=INK, tip=None, spot=None),
    back=mix(INK, SLATE, 0.18), belly=mix(INK, SLATE, 0.10), head=INK, neckc=mix(INK, SLATE, 0.12), tailc=INK,
    saddle=(0.20, -0.02), eye_ring=True, nf=8, cov=0.4, tip_t=0.99)

SPECIES['gannet'] = _sp(
    k=1.32, body=(0.190, 0.170, 0.46), neck=0.24, neck_th=0.075, headr=(0.078, 0.072, 0.105),
    beak_len=0.30, beak_d=0.044, hook=0.020, beak_mat='beak_blue',
    L_in=0.50, L_out=0.62, ch_root=0.31, ch_wrist=0.21, ch_tip=0.04, lead=0.05, th=0.030,
    dihedral=0.12, amp_in=0.40, amp_out=0.50, sweep_in=0.10, sweep_out=0.34, teeth=(9, 0.04, 0.5),
    tail_len=0.38, tail_w=(0.05, 0.12), tail_notch=-0.10,
    col=dict(mantle=GUANO, covert=GUANO, flight=mix(GUANO, SLATE, 0.2), tip=INK, spot=None),
    back=GUANO, belly=GUANO, head=hx('#e3cf94'), neckc=hx('#e8dcae'), tailc=GUANO,
    saddle=(0.21, -0.14), eye_ring=False, nf=11, cov=0.34, tip_t=0.70)


def extra_mats(m, P=None):
    m['beak_blue'] = Material(noisy(hx('#8aa0ae'), 0.06), spec=0.3, gloss=26, brush=0.03)
    m['clay'] = Material(noisy(hx('#a5643f'), 0.14, 26.0), spec=0.12, gloss=14, brush=0.08)
    m['clay_dk'] = Material(noisy(hx('#6e3f2b'), 0.12, 26.0), spec=0.12, gloss=14, brush=0.08)
    m['guano'] = Material(noisy(GUANO, 0.05, 30.0), spec=0.1, gloss=14, brush=0.06)
    m['wax'] = Material(hx('#b4382f'), spec=0.3, gloss=26, brush=0.03)
    m['net'] = Material(noisy(hx('#8c7c5a'), 0.12, 50.0), spec=0.02, brush=0.06)
    m['oilcloth'] = Material(noisy(hx('#c2ab5f'), 0.10, 30.0), spec=0.35, gloss=26, brush=0.05)
    m['oilcloth_dk'] = Material(noisy(hx('#8a7536'), 0.10, 30.0), spec=0.30, gloss=24, brush=0.05)
    m['paper'] = Material(noisy(hx('#efe6cf'), 0.05, 40.0), spec=0.05, brush=0.04)
    m['spray'] = Material(hx('#e8f1f4'), spec=0.4, gloss=20, brush=0.02)
    m['salt'] = Material(noisy(hx('#f1efe6'), 0.05, 50.0), spec=0.3, gloss=20, brush=0.03)
    return m


def finish_w2(c_mats_fn=None):
    pass


# ---------------------------------------------------------------- props

def pouch(add, c, R, size=1.0, flap=True, open_=0.0):
    """Oilcloth letter pouch with a buckled flap and a red wax seal. R = orientation (columns x,y,z)."""
    s = size
    add(RoundBox(c, (0.055 * s, 0.065 * s, 0.030 * s), 0.012 * s, R), 'oilcloth', 0.02)
    if flap:
        add(RoundBox(c + R @ v3(0, 0.040 * s, 0.012 * s), (0.058 * s, 0.032 * s, 0.014 * s), 0.008 * s, R @ rot_x(0.25 + open_)), 'oilcloth_dk', 0.0)
        add(Sphere(c + R @ v3(0, 0.012 * s, 0.040 * s), 0.013 * s), 'wax', 0.0)
        add(Capsule(c + R @ v3(0, 0.02 * s, 0.036 * s), c + R @ v3(0, -0.05 * s, 0.034 * s), 0.0045 * s, 0.0045 * s), 'cord', 0.0)
    # corners tied with cord
    for sx in (-1, 1):
        add(Sphere(c + R @ v3(sx * 0.055 * s, -0.04 * s, 0.0), 0.012 * s), 'cord', 0.0)


def letter(add, c, R, size=1.0, glow=0.0, lights=None):
    """Sealed letter: folded paper with a red wax seal; glow adds a pale aura."""
    s = size
    add(RoundBox(c, (0.050 * s, 0.003 * s, 0.036 * s), 0.002, R), 'paper', 0.0)
    add(RoundBox(c + R @ v3(0, 0.003 * s, 0), (0.050 * s, 0.002 * s, 0.002 * s), 0.001, R), 'wax', 0.0)
    add(Sphere(c + R @ v3(0, 0.005 * s, 0), 0.010 * s), 'wax', 0.0)
    if glow > 0.02:
        add(Ellipsoid(c + R @ v3(0, 0.02, 0), (0.07 * glow, 0.02 * glow, 0.05 * glow), R), 'flash', 0.0)
        if lights is not None:
            lights.append(Light(c + v3(0, 0.08, 0.05), hx('#fff1c8'), 2.0 * glow, 0.25))


def bomb_jar(add, c, R, size=1.0, fuse=0.0, seed=0):
    """Clay bomb jar: round belly, narrow neck, wax-sealed bung, guano drip streaks; optional lit fuse."""
    s = size
    add(Ellipsoid(c, (0.075 * s, 0.085 * s, 0.075 * s), R), 'clay', 0.0)
    add(Ellipsoid(c + R @ v3(0, 0.07 * s, 0), (0.045 * s, 0.045 * s, 0.045 * s), R), 'clay', 0.03)
    add(Cylinder(c + R @ v3(0, 0.095 * s, 0), c + R @ v3(0, 0.115 * s, 0), 0.034 * s, 0.006), 'clay_dk', 0.0)
    add(Sphere(c + R @ v3(0, 0.118 * s, 0), 0.024 * s), 'wax', 0.0)
    add(Torus(c + R @ v3(0, 0.035 * s, 0), R[:, 1], 0.070 * s, 0.006 * s), 'cord', 0.0)
    for j in range(3):
        a = seed + j * 2.1
        add(Capsule(c + R @ v3(np.cos(a) * 0.06 * s, 0.04 * s, np.sin(a) * 0.06 * s),
                    c + R @ v3(np.cos(a) * 0.072 * s, -0.04 * s - 0.01 * j, np.sin(a) * 0.072 * s), 0.011 * s, 0.006 * s), 'guano', 0.0)
    if fuse > 0:
        a0 = c + R @ v3(0, 0.12 * s, 0)
        add(Capsule(a0, a0 + R @ v3(0.02, 0.05 * s, 0.01), 0.004, 0.003), 'cord', 0.0)
        add(Sphere(a0 + R @ v3(0.02, 0.055 * s, 0.01), 0.011 * fuse), 'flame', 0.0)


def spray(add, c, d, n=7, amt=1.0, seed=2, spread=0.12, length=0.5, mat='spray', size=0.022):
    """Droplets / salt flecks streaming from c along d (trailing a dive)."""
    if amt <= 0:
        return
    rng = np.random.default_rng(seed)
    d = norm(d)
    for i in range(n):
        t = rng.uniform(0.1, 1.0) * length * amt
        o = v3(*rng.normal(0, spread, 3)) * (0.3 + t)
        p = c + d * t + o
        r = size * rng.uniform(0.6, 1.2) * (1.1 - 0.5 * t / max(length, 1e-3))
        add(Ellipsoid(p, (r * 0.8, r * 1.3, r * 0.8), basis_from(d, v3(0, 1, 0))), mat, 0.0)


__all__ = [n for n in dir() if not n.startswith('__')]


# ---------------------------------------------------------------- kites and perches

def kite_mat(frame_R, c, hw, ht, hb, a=None, b=None, stripe=None):
    """Two-tone diamond kite canvas (left half a, right half b) with a centre stripe, in the kite's local frame."""
    a = np.array(a if a is not None else CANVAS)
    b = np.array(b if b is not None else mix(SLATE, GUANO, 0.25))
    st = np.array(stripe if stripe is not None else ORANGE)

    def fn(p, n):
        q = (p - c) @ frame_R
        out = np.where((q[:, 0] > 0)[:, None], b[None, :], a[None, :]) * np.ones((len(p), 1))
        s = np.abs(q[:, 1] - 0.10 * ht) < 0.014
        out[s] = st
        sp = np.abs(q[:, 0]) < 0.010
        out[sp] = np.array(BONE)
        out = out * (0.92 + 0.16 * fbm(p, 24.0, 2))[:, None]
        return np.clip(out, 0, 1)
    return Material(fn, spec=0.03, brush=0.07)


class DiamondKite(Prim):
    """Flat diamond (kite) plate, local x = width, y = up, z = normal."""
    def __init__(self, c, R, hw, ht, hb, th=0.007):
        self.c, self.R, self.hw, self.ht, self.hb, self.th = v3(*c), R, hw, ht, hb, th
        self.bc = self.c
        self.br = max(hw, ht, hb) + 0.05

    def __call__(self, p):
        q = (p - self.c) @ self.R
        y = q[:, 1]
        f = np.abs(q[:, 0]) / self.hw + np.where(y > 0, y / self.ht, -y / self.hb) - 1.0
        d2 = f * min(self.hw, self.ht) * 0.62
        return np.maximum(d2, np.abs(q[:, 2]) - self.th)


def kite(add, mats, name, c, R, hw, ht, hb=None, tail=0.0, phase=0.0, a=None, b=None, bridle_to=None):
    """Diamond kite with bone spars, ribbon tail (orange/canvas bows) and an optional bridle line to a point."""
    hb = hb if hb is not None else ht * 0.55
    c = v3(*c)
    mats[name] = kite_mat(R, c, hw, ht, hb, a, b)
    add(DiamondKite(c, R, hw, ht, hb), name, 0.0)
    up, side = R[:, 1], R[:, 0]
    add(Capsule(c - up * hb, c + up * ht, 0.007, 0.006), 'bone', 0.0)
    add(Capsule(c - side * hw, c + side * hw, 0.007, 0.006), 'bone', 0.0)
    if tail > 0:
        p = c - up * hb
        for j in range(5):
            q = p - up * tail / 5 + side * 0.025 * np.sin(phase * 6.283 + j * 1.4)
            add(Capsule(p, q, 0.005, 0.004), 'tar', 0.0)
            add(Ellipsoid(q, (0.030, 0.012, 0.014), R), 'cord' if j % 2 == 0 else 'canvas', 0.0)
            p = q
    if bridle_to is not None:
        bt = v3(*bridle_to)
        add(Capsule(c + up * 0.15 * ht, bt, 0.004, 0.004), 'cord', 0.0)
        add(Capsule(c - up * 0.3 * hb, bt, 0.004, 0.004), 'cord', 0.0)


def perch_pole(add, base, d, length=1.4, bar=0.34, bird=True, flap=0.0, tell=0.0):
    """Perch pole: drift-wood pole with a T-bar and cord lashings, tern perched on it."""
    d = norm(d)
    top = base + d * length
    add(Capsule(base, top, 0.020, 0.015), 'drift', 0.0)
    side = norm(np.cross(d, v3(0, 0, 1))) if abs(d[2]) < 0.9 else v3(1, 0, 0)
    a, b = top + side * bar - d * 0.04, top - side * bar - d * 0.04
    add(Capsule(a, b, 0.016, 0.016), 'drift', 0.0)
    for t in (-0.05, 0.0):
        add(Cylinder(top + d * t - d * 0.005, top + d * t + d * 0.005, 0.026, 0.004), 'cord', 0.0)
    add(Sphere(a, 0.02), 'cord', 0.0)
    add(Sphere(b, 0.02), 'cord', 0.0)
    for k in range(3):
        add(Torus(base + d * (0.25 + 0.08 * k), d, 0.024, 0.006), 'tar', 0.0)
    if bird:
        perched_tern(add, top - d * 0.02 + side * bar * 0.45, k=0.34, yaw=0.5, flap=flap, tell=tell)
    return top


def perched_tern(add, c, yaw=0.0, k=0.30, flap=0.0, tell=0.0):
    """A small tern perched with folded wings, tail cocked, orange beak."""
    R = rot_y(yaw)
    p = lambda q: c + R @ (v3(*q) * k)
    bob = 0.02 * np.sin(tell * 6.283)
    add(Ellipsoid(p((0, 0.17 + bob, 0)), (0.17 * k, 0.19 * k, 0.36 * k), R @ rot_x(-0.45)), 'feather_g', 0.0)
    add(Ellipsoid(p((0, 0.22 + bob, -0.06)), (0.15 * k, 0.15 * k, 0.32 * k), R @ rot_x(-0.45)), 'feather_s', 0.04)
    add(Sphere(p((0, 0.44 + bob, 0.20)), 0.115 * k), 'feather_i', 0.03)
    add(Sphere(p((0, 0.38 + bob, 0.18)), 0.10 * k), 'feather_g', 0.03)
    add(Capsule(p((0, 0.43 + bob, 0.29)), p((0, 0.40 + bob, 0.52)), 0.040 * k, 0.012 * k), 'beak', 0.0)
    add(Capsule(p((0, 0.10, -0.2)), p((0, -0.05, -0.70 - 0.2 * flap)), 0.07 * k, 0.12 * k), 'feather_g', 0.0)
    add(Capsule(p((0.07, 0.10, -0.2)), p((0.12, -0.02, -0.78 - 0.2 * flap)), 0.03 * k, 0.02 * k), 'feather_g', 0.0)
    for sx in (-1, 1):
        add(Sphere(p((sx * 0.085, 0.47 + bob, 0.23)), 0.020 * k), 'eye', 0.0)


__all__ = [n for n in dir() if not n.startswith('__')]

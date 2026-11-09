"""Wave-2 Hadal Court helpers (append-only; existing units do not import this)."""
from _hadal_court_common import *


def bile_mat(P, gain=1.0):
    g = max(pulse(P), 0.0) * gain
    return Material(_hex('#7ff0d4'), emissive=tuple(np.array(_hex('#6fe8cf')) * (2.0 + 0.8 * P.get('fx', 0)) * g), rim=0.0)


def ribbon(add, root, d0, length, phase, mat, n=7, w0=0.07, w1=0.02, thick=0.012, sway=0.07, drift=(0, 0, 0), flat=(1, 0, 0), k=0.01):
    """A flat flowing ribbon (veil) from root along d0, wavy in the plane spanned by `flat`.
    Built of overlapping flattened ellipsoids. Returns the tip."""
    d0 = norm(np.asarray(d0, dtype=np.float64))
    cam = norm(np.array([-0.6, 0.45, 0.8]))
    p = np.asarray(root, dtype=np.float64).copy()
    seg = length / n
    dr = np.asarray(drift, dtype=np.float64)
    d = d0
    for i in range(n):
        t = (i + 0.5) / n
        w = w0 + (w1 - w0) * t
        wob = np.sin(phase * 2 * np.pi + t * 4.5) * sway * t
        side = norm(np.cross(d0, cam))
        dd = norm(d0 + side * wob * 3 + dr * t * 1.5)
        fl = norm(np.cross(dd, cam))
        q = p + dd * seg
        c = (p + q) / 2
        Rb = basis_from(dd, fl)
        add(Ellipsoid(c, (thick, seg * 0.62, w), Rb), mat, k)
        p = q
    return p


def silt_puff(add, c, r, mat='silt', n=5, seed=0, lift=0.0):
    rng = np.random.default_rng(seed)
    add(Ellipsoid(c, (r, r * 0.30, r * 0.8)), mat, 0.04)
    for i in range(n):
        a = rng.uniform(0, 6.28)
        rr = r * rng.uniform(0.4, 0.9)
        q = c + v3(np.cos(a) * rr, rng.uniform(0, 0.05) + lift, np.sin(a) * rr * 0.8)
        add(Ellipsoid(q, (r * 0.3, r * 0.17, r * 0.3)), mat, 0.03)


def silt_mat(alpha_dark=0.0):
    return Material(lambda p, n: np.array(_hex('#5b5c78'))[None, :] * (0.8 + 0.4 * fbm(p, 22, 2)[:, None]), spec=0.04, brush=0.14)


def vchain(add, a, b, n=3, r=0.03, mat='chain'):
    """Chain between two points that may be vertical (links alternate between two perpendicular planes)."""
    d = b - a
    L = np.linalg.norm(d)
    u = d / max(L, 1e-6)
    s1 = norm(np.cross(u, v3(1, 0, 0))) if abs(u[0]) < 0.9 else norm(np.cross(u, v3(0, 0, 1)))
    s2 = np.cross(u, s1)
    for i in range(n):
        q = a + d * (i + 0.5) / n
        add(Torus(q, s1 if i % 2 else s2, r, r * 0.32), mat, 0.0)


__all__ = [n for n in dir() if not n.startswith('__')]

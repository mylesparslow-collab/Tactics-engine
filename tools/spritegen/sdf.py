"""Signed-distance primitives for the sprite sculptor.

Every primitive works on an (N, 3) float array of points and returns (N,) distances.
Each one also carries a bounding sphere so the renderer can skip it for points
that are far away (this keeps a 60-part figure fast enough in plain numpy).

World units are metres. y is up, the figure faces +z, its left hand is +x.
"""
import numpy as np


def v3(*a):
    return np.array(a, dtype=np.float64)


def norm(v):
    v = np.asarray(v, dtype=np.float64)
    return v / np.linalg.norm(v)


def basis_from(axis_y, hint=(0, 0, 1)):
    """Rotation matrix whose local y axis points along axis_y."""
    y = norm(axis_y)
    h = norm(hint)
    if abs(np.dot(h, y)) > 0.95:
        h = norm((1, 0, 0))
    x = norm(np.cross(y, h))
    z = np.cross(x, y)
    return np.stack([x, y, z], axis=1)  # columns are local axes


def rot_y(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_z(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


class Prim:
    """Base primitive. Subclasses set self.bc (bound centre) and self.br (bound radius)."""
    bc = np.zeros(3)
    br = 1.0

    def __call__(self, p):
        raise NotImplementedError


class Sphere(Prim):
    def __init__(self, c, r):
        self.c, self.r = v3(*c), r
        self.bc, self.br = self.c, r

    def __call__(self, p):
        return np.linalg.norm(p - self.c, axis=1) - self.r


class Ellipsoid(Prim):
    """Axis radii in a local frame given by rotation matrix R (columns = local axes)."""
    def __init__(self, c, radii, R=None):
        self.c = v3(*c)
        self.r = v3(*radii)
        self.R = np.eye(3) if R is None else R
        self.bc, self.br = self.c, float(max(radii))

    def __call__(self, p):
        q = (p - self.c) @ self.R
        k0 = np.linalg.norm(q / self.r, axis=1)
        k1 = np.linalg.norm(q / (self.r * self.r), axis=1)
        return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


class Capsule(Prim):
    """Round cone from a (radius ra) to b (radius rb)."""
    def __init__(self, a, b, ra, rb=None):
        self.a, self.b = v3(*a), v3(*b)
        self.ra = ra
        self.rb = ra if rb is None else rb
        self.bc = (self.a + self.b) / 2
        self.br = np.linalg.norm(self.b - self.a) / 2 + max(self.ra, self.rb)

    def __call__(self, p):
        pa = p - self.a
        ba = self.b - self.a
        L2 = ba @ ba
        h = np.clip((pa @ ba) / L2, 0.0, 1.0)
        r = self.ra + (self.rb - self.ra) * h
        return np.linalg.norm(pa - h[:, None] * ba, axis=1) - r


class RoundBox(Prim):
    """Box with half-size hs and rounding r, centred at c, rotated by R."""
    def __init__(self, c, hs, r=0.0, R=None):
        self.c, self.hs, self.r = v3(*c), v3(*hs), r
        self.R = np.eye(3) if R is None else R
        self.bc, self.br = self.c, float(np.linalg.norm(self.hs)) + r

    def __call__(self, p):
        q = np.abs((p - self.c) @ self.R) - self.hs
        out = np.linalg.norm(np.maximum(q, 0.0), axis=1)
        inside = np.minimum(np.max(q, axis=1), 0.0)
        return out + inside - self.r


class Cylinder(Prim):
    """Capped cylinder along local y, from a to b, radius r, edge rounding e."""
    def __init__(self, a, b, r, e=0.0):
        self.a, self.b, self.r, self.e = v3(*a), v3(*b), r, e
        self.bc = (self.a + self.b) / 2
        self.h = np.linalg.norm(self.b - self.a) / 2
        self.R = basis_from(self.b - self.a)
        self.br = self.h + r

    def __call__(self, p):
        q = (p - self.bc) @ self.R
        dx = np.sqrt(q[:, 0] ** 2 + q[:, 2] ** 2) - self.r + self.e
        dy = np.abs(q[:, 1]) - self.h + self.e
        return (np.minimum(np.maximum(dx, dy), 0.0)
                + np.sqrt(np.maximum(dx, 0) ** 2 + np.maximum(dy, 0) ** 2) - self.e)


class Torus(Prim):
    """Torus around local y axis (axis given), major R0, minor r."""
    def __init__(self, c, axis, R0, r):
        self.c, self.R0, self.r = v3(*c), R0, r
        self.R = basis_from(axis)
        self.bc, self.br = self.c, R0 + r

    def __call__(self, p):
        q = (p - self.c) @ self.R
        a = np.sqrt(q[:, 0] ** 2 + q[:, 2] ** 2) - self.R0
        return np.sqrt(a * a + q[:, 1] ** 2) - self.r


class Func(Prim):
    """Arbitrary SDF function with an explicit bound."""
    def __init__(self, fn, bc, br):
        self.fn, self.bc, self.br = fn, v3(*bc), br

    def __call__(self, p):
        return self.fn(p)


class Subtract(Prim):
    """a minus b, with optional smoothing k."""
    def __init__(self, a, b, k=0.0):
        self.a, self.b, self.k = a, b, k
        self.bc, self.br = a.bc, a.br

    def __call__(self, p):
        return smax(self.a(p), -self.b(p), self.k)


class Union(Prim):
    def __init__(self, prims, k=0.0):
        self.prims, self.k = prims, k
        lo = np.min([q.bc - q.br for q in prims], axis=0)
        hi = np.max([q.bc + q.br for q in prims], axis=0)
        self.bc = (lo + hi) / 2
        self.br = float(np.linalg.norm(hi - lo) / 2)

    def __call__(self, p):
        d = self.prims[0](p)
        for q in self.prims[1:]:
            d = smin(d, q(p), self.k)
        return d


def smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b + (a - b) * h - k * h * (1.0 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


# --- hash noise usable inside SDFs and material functions -------------------

def hash3(i):
    i = i.astype(np.int64)
    h = (i[..., 0] * 374761393 + i[..., 1] * 668265263 + i[..., 2] * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return (h & 0xFFFF) / 65535.0


def vnoise(p, freq):
    """Smooth value noise in [0,1], p is (N,3)."""
    q = p * freq
    i = np.floor(q)
    f = q - i
    f = f * f * (3 - 2 * f)
    out = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = ((f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1])
                     * (f[:, 2] if dz else 1 - f[:, 2]))
                out = out + w * hash3(i + np.array([dx, dy, dz]))
    return out


def fbm(p, freq, octaves=3):
    s, a, tot = 0.0, 1.0, 0.0
    for o in range(octaves):
        s = s + a * vnoise(p + o * 17.3, freq * (2 ** o))
        tot += a
        a *= 0.5
    return s / tot

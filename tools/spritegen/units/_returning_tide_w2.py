"""Wave-2 Returning Tide helpers (append-only; existing units do not import this)."""
from _returning_tide_common import *
from sdf import Func, smax, smin
import numpy as _np

def frame_for(P, up=None):
    up = norm(P['neck'] - P['pelvis']) if up is None else up
    return basis_from(up, (0, 0, 1))


SALT = _hex('#e8e6dc')
SALT_DK = _hex('#b9bbb0')


def stream(add, a, ground_y=0.0, phase=0.0, r=0.014, mat='water', wob=0.012, n=6, out=(0.0, 0.0), splash=True):
    """A thin falling stream from a point to the ground (slightly wavering, with a little splash)."""
    top = _np.asarray(a, dtype=_np.float64)
    prev = top
    H = top[1] - ground_y
    for k in range(1, n + 1):
        t = k / n
        q = top + v3(out[0] * t * t + wob * _np.sin(phase * 6.28 + t * 5), -H * t, out[1] * t * t)
        add(Capsule(prev, q, r * (1.0 - 0.15 * t), r * (1.0 - 0.15 * (t + 1 / n))), mat, 0.01)
        prev = q
    if splash:
        add(Ellipsoid(v3(prev[0], ground_y + 0.01, prev[2]), (r * 3.0, 0.012, r * 2.4)), 'drip', 0.0)
    return prev


def barrel(c, R, rad, half, bulge=0.10, crack=None, lip=0.02):
    """Bulging cask/cistern axis along R's y. Optional crack = (x, z) local anchor of a vertical-ish fissure notch."""
    def f(p):
        q = (p - c) @ R
        y = q[:, 1]
        u = _np.clip(y / half, -1, 1)
        r = rad * (1 + bulge * (1 - u * u)) - lip * (_np.abs(u) > 0.92) * 0
        rr = _np.sqrt(q[:, 0] ** 2 + q[:, 2] ** 2)
        d = (rr - r)
        d = smax(d, _np.abs(y) - half, 0.03)
        if crack is not None:
            ang = _np.arctan2(q[:, 0], q[:, 2])
            cx = crack[0]
            w = 0.012 + 0.012 * _np.abs(_np.sin(y * 18))
            dd = _np.abs(ang - cx) * rad - w
            dd = _np.maximum(dd, _np.abs(y - crack[1]) - crack[2])
            d = smax(d, -dd, 0.004)
        return d
    return Func(f, c, _np.hypot(half, rad * (1 + bulge)) + 0.05)


def salt_crystals(add, center, normal, n=6, spread=0.05, size=0.02, seed=0, mat='salt'):
    """Cluster of little blocky salt crystals standing out of a surface."""
    rng = _np.random.default_rng(seed)
    nn = norm(normal)
    t1 = norm(_np.cross(nn, v3(0, 1, 0.3)))
    t2 = _np.cross(nn, t1)
    for i in range(n):
        o = center + t1 * rng.uniform(-spread, spread) + t2 * rng.uniform(-spread, spread)
        s = size * rng.uniform(0.6, 1.3)
        d = norm(nn + t1 * rng.uniform(-0.5, 0.5) + t2 * rng.uniform(-0.5, 0.5))
        add(RoundBox(o + d * s * 0.7, (s * 0.55, s * 1.2, s * 0.55), s * 0.12, basis_from(d, t1)), mat, 0.0)


def salt_mat(P=None):
    return Material(lambda p, n: _np.array(SALT)[None, :] * (0.82 + 0.3 * fbm(p, 44, 2)[:, None]), spec=0.75, gloss=48, brush=0.06)


__all__ = [n for n in dir() if not n.startswith("__")]

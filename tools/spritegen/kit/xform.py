"""Rigid transforms of whole parts: move, rotate, scale a primitive (or a whole creature).

Use for non-humanoid bodies (crabs, polyps, engines) whose animation is mostly whole-body motion:
    parts = [Part(Xform(prim, R=rot_x(0.2), t=v3(0,0.1,0), s=1.1, pivot=v3(0,0,0)), mat, k) ...]
or wrap a finished part list with transform_parts().
"""
import numpy as np
from sdf import Prim, v3
from render import Part


class Xform(Prim):
    """prim moved by: p' = pivot + s * R @ (p - pivot) + t   (R rotation, s uniform scale)."""
    def __init__(self, prim, R=None, t=(0, 0, 0), s=1.0, pivot=(0, 0, 0)):
        self.prim = prim
        self.R = np.eye(3) if R is None else np.asarray(R, dtype=np.float64)
        self.t = v3(*t)
        self.s = float(s)
        self.pivot = v3(*pivot)
        self.bc = self.pivot + self.s * (self.R @ (prim.bc - self.pivot)) + self.t
        self.br = prim.br * self.s

    def __call__(self, p):
        q = ((p - self.t - self.pivot) @ self.R) / self.s + self.pivot   # inverse transform
        return self.prim(q) * self.s


class Squash(Prim):
    """Non-uniform scale (squash and stretch) about a pivot, e.g. sy=0.9, sxz=1.05 for a landing."""
    def __init__(self, prim, sy=1.0, sxz=1.0, pivot=(0, 0, 0)):
        self.prim, self.sy, self.sxz, self.pivot = prim, sy, sxz, v3(*pivot)
        sc = np.array([sxz, sy, sxz])
        self.sc = sc
        self.bc = self.pivot + (prim.bc - self.pivot) * sc
        self.br = prim.br * max(sy, sxz)

    def __call__(self, p):
        q = (p - self.pivot) / self.sc + self.pivot
        return self.prim(q) * min(self.sy, self.sxz)


def transform_parts(parts, R=None, t=(0, 0, 0), s=1.0, pivot=(0, 0, 0)):
    return [Part(Xform(pt.prim, R, t, s, pivot), pt.mat, pt.k) for pt in parts]


def squash_parts(parts, sy=1.0, sxz=1.0, pivot=(0, 0, 0)):
    return [Part(Squash(pt.prim, sy, sxz, pivot), pt.mat, pt.k) for pt in parts]

"""Wave-2 Salvage Compact helpers (append-only): tin kettles, balance scales, ledger books."""
import numpy as np
from _salvage_compact_common import *


def kettle(add, c, r=0.07, spout=(1, 0.3, 0), up=(0, 1, 0), mat='tin', handle=True, lid=True):
    """Squat tin kettle: dome body, lid knob, curved spout, bail handle."""
    up = norm(v3(*up))
    sp = norm(v3(*spout))
    add(Ellipsoid(c, (r, r * 0.80, r), basis_from(up, (0, 0, 1))), mat, 0.0)
    if lid:
        add(Cylinder(c + up * r * 0.72, c + up * r * 0.84, r * 0.55, 0.006), mat, 0.0)
        add(Sphere(c + up * r * 0.98, r * 0.17), 'brass', 0.0)
    a = c + sp * r * 0.85 + up * r * 0.0
    add(Capsule(a, c + sp * r * 1.75 + up * r * 0.55, r * 0.22, r * 0.12), mat, 0.0)
    if handle:
        hax = norm(np.cross(up, sp))
        add(Torus(c + up * r * 0.55, hax, r * 0.78, r * 0.10), 'iron', 0.0)


def balance(add, top, sv, tip=0.0, beam=0.15, drop=0.15):
    """Hand-held balance scale: beam, centre ring and two pans on chains. tip>0 lowers the +sv pan."""
    add(Torus(top + v3(0, 0.03, 0), v3(0, 0, 1), 0.022, 0.006), 'brass', 0.0)
    add(Capsule(top - sv * beam, top + sv * beam, 0.011), 'brass', 0.0)
    for sg in (-1, 1):
        e = top + sv * sg * beam
        pan = e + v3(0, -drop - 0.035 * tip * sg, 0)
        add(Capsule(e, pan + v3(0.02, 0.0, 0.0), 0.004), 'brass', 0.0)
        add(Capsule(e, pan + v3(-0.02, 0.0, 0.0), 0.004), 'brass', 0.0)
        add(Capsule(e, pan + v3(0.0, 0.0, 0.02), 0.004), 'brass', 0.0)
        add(Cylinder(pan + v3(0, -0.012, 0), pan + v3(0, 0.0, 0), 0.058, 0.006), 'tin', 0.0)
        if sg < 0:
            add(Sphere(pan + v3(0, 0.020, 0), 0.020), 'gold', 0.0)      # a coin heap on one pan
            add(Sphere(pan + v3(0.025, 0.015, 0.01), 0.014), 'gold', 0.0)

"""Faction death end states (art_direction.md section 10) as reusable helpers.

  Concord   salt crust          crusted(materials, SALT, amount)
  Hadal     deflating bell /    sink_parts(...) + Scene(ground_clip=True), lights out, teal motes
            sinking into dark
  Tide      pool of brine       brine_pool(add, amount, radius) + sink_parts
  Compact   scattering scrap    scrap_scatter(add, amount, seed)
  Reef      crumbling calcite   crusted(materials, CALCITE, amount) + crumble_scatter + sink
  Keepers   flame gutters out   gutter(materials, amount) and dim the unit's Light objects
"""
import copy
import numpy as np
from sdf import v3, Ellipsoid, RoundBox, Sphere, Cylinder, fbm, rot_y, rot_x
from render import Material, Part, _hex
from kit.xform import transform_parts


def crusted(materials, color, amount, freq=18.0):
    """Return a new materials dict where `color` blooms over every surface by noise (0..1)."""
    if amount <= 0:
        return materials
    out = {}
    for name, m in materials.items():
        base = m.albedo

        def alb(p, n, base=base):
            a = base(p, n) if callable(base) else np.array(base)[None, :].repeat(len(p), 0)
            c = np.clip((fbm(p, freq, 3) - (1 - amount)) * 4.0 + (amount - 0.5) * 2, 0, 1)[:, None]
            return a * (1 - c) + np.array(color)[None, :] * c
        m2 = copy.copy(m)
        m2.albedo = alb
        m2.spec = m.spec * (1 - amount) + 0.03 * amount
        m2.metal = m.metal * (1 - amount)
        if m.emissive is not None and not callable(m.emissive):
            m2.emissive = tuple(np.array(m.emissive) * (1 - amount))
        out[name] = m2
    return out


def gutter(materials, amount):
    """Fade every emissive material toward off (amount 1 = dark)."""
    out = {}
    for name, m in materials.items():
        m2 = copy.copy(m)
        if m.emissive is not None and not callable(m.emissive):
            m2.emissive = tuple(np.array(m.emissive) * (1 - amount))
        out[name] = m2
    return out


def sink_parts(parts, depth, tilt=0.0):
    """Lower the whole body into the ground (use with Scene(ground_clip=True))."""
    from sdf import rot_z
    return transform_parts(parts, R=rot_z(tilt), t=(0, -depth, 0))


def brine_pool(add, amount, radius=0.42, center=(0.0, 0.0, 0.05), mat='brine'):
    """A flat spreading pool on the ground. Add a 'brine' material (teal, glossy) to the scene."""
    if amount <= 0:
        return
    r = radius * (0.35 + 0.65 * amount)
    add(Ellipsoid(v3(*center) + v3(0, 0.0, 0), (r, 0.012, r * 0.8)), mat, 0.0)


def brine_material(color=_hex('#2f6f6a')):
    return Material(color, spec=1.0, gloss=60, brush=0.03)


def scrap_scatter(add, amount, seed=1, n=9, radius=0.45, mat='scrap', size=0.035):
    """Bits of rust and bone flung around the feet (amount 0..1 = how far they've flown)."""
    rng = np.random.default_rng(seed)
    for i in range(n):
        ang = rng.uniform(0, 2 * np.pi)
        dist = radius * (0.25 + 0.75 * amount) * rng.uniform(0.4, 1.0)
        c = v3(np.cos(ang) * dist, size * 0.6, np.sin(ang) * dist * 0.8)
        R = rot_y(rng.uniform(0, 6.28)) @ rot_x(rng.uniform(-0.6, 0.6))
        hs = (size * rng.uniform(0.6, 1.4), size * 0.4, size * rng.uniform(0.5, 1.2))
        add(RoundBox(c, hs, size * 0.15, R), mat, 0.0)


def crumble_scatter(add, amount, seed=2, n=12, radius=0.35, mat='calcite', size=0.03):
    """Chalky lumps falling around the base (Reef calcite, or salt chunks)."""
    if amount <= 0:
        return
    rng = np.random.default_rng(seed)
    for i in range(n):
        ang = rng.uniform(0, 2 * np.pi)
        dist = radius * rng.uniform(0.2, 1.0) * (0.5 + 0.5 * amount)
        r = size * rng.uniform(0.6, 1.3) * amount
        add(Sphere(v3(np.cos(ang) * dist, r * 0.5, np.sin(ang) * dist * 0.8), r), mat, 0.0)

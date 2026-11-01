"""Reef Ascendant shared sculpting helpers: grown calcite forms, not built ones.

Everything here is a numpy SDF (sdf.Func) so a unit file can assemble a thicket from a few calls:

  spire(...)        fluted tower with grooves (polar cosine flutes), bend for sway, optional porosity
  crown(...)        polar-repeated ring of tentacles / petals / fronds (each with its own sway phase)
  fan(...)          a ribbed, scallop-edged sea fan blade in an arbitrary plane
  spike_ball(...)   urchin: sphere with radial spikes (Fibonacci directions)
  brain(...)        brain-coral head with meandering grooves
  branches(...)     recursive branching capsules (smooth union), bends with sway
  tube(...)         an open polyp tube (capsule with a mouth hollow)
  legs(...)         short spine legs that scuttle with the stride channel

Animation: units use kit.anim.creature_frames; reef_rows() adds the Reef death (crumble + sink + tilt)
and a polyp-twitch idle. wave(P, ph) gives a per-part sway value from the tell/stride/strike channels.
Pose: build parts in rest space, then body_pose(parts, P) applies lean / squash / bob.
"""
import numpy as np
from sdf import (v3, norm, basis_from, rot_y, rot_x, rot_z, Sphere, Ellipsoid, Capsule, RoundBox,
                 Cylinder, Torus, Func, Subtract, Union, smax, smin, fbm, vnoise)
from render import Material, Part, Light, Scene, _hex
from kit.looks import LOOKS, PALETTES
from kit.anim import creature_frames, CREATURE_DEFAULTS, ROWS
from kit.xform import transform_parts, squash_parts
from kit.humanoid import new_parts, finish

FACTION = 'reef_ascendant'
import dataclasses
# chalky forms: lift the ambient/bounce a touch so calcite stays white in the shadow side
LOOK = dataclasses.replace(LOOKS[FACTION], sky_int=0.48, bounce_int=0.36, exposure=1.06)
RA = PALETTES[FACTION]
CORAL, CALC, PINK, RED, LENS = RA['coral'], RA['calcite'], RA['pink'], RA['reef_red'], RA['lens']
BONE = _hex('#d9d0b4')
DUSK = _hex('#b79a92')          # muted pink-grey for pores/crevices
GLOW = _hex('#ffc2b0')          # warm synapse pulse (not teal: that belongs to the Court)


# ------------------------------------------------------------------ pose / rows

def base(**kw):
    P = dict(CREATURE_DEFAULTS)
    P.update(twitch=0.0, open=0.0)
    P.update(kw)
    return P


def wave(P, ph=0.0, idle=1.0, move=1.0, strike=1.0):
    """Per-part sway (-1..1ish) from tell (idle/move phase), stride and strike, offset by phase ph."""
    return (0.5 * idle * np.sin(2 * np.pi * P['tell'] + ph) + 0.6 * move * P['stride'] * np.cos(ph)
            + 0.9 * strike * P['strike'] - 1.5 * P['lean'] * 0.5)


def reef_rows(base_fn, sink=0.12, tilt=0.12, extra=None):
    """creature_frames with the Reef idle tell (polyp twitch) and death (crumble, sink, slight topple)."""
    def ov(rows):
        for i, (P, _) in enumerate(rows['idle']):
            P['twitch'] = [0.0, 0.0, 1.0, 0.3][i]
        for i, (P, _) in enumerate(rows['attack']):
            P['open'] = [0.2, 0.5, 1.0, 0.4][i]
        for i, (P, _) in enumerate(rows['cast']):
            P['open'] = [0.5, 1.0, 0.6][i]
        for i, (P, _) in enumerate(rows['death']):
            P['sink'] = [0, 0, 0.35, 1.0][i] * sink
            P['topple'] = [0, 0.3, 0.7, 1.0][i] * tilt
            P['open'] = [0.6, 0.3, 0.0, 0.0][i]
        for i, (P, _) in enumerate(rows['hit']):
            P['twitch'] = [1.0, 0.4][i]
        if extra:
            extra(rows)
        return rows
    return ROWS, creature_frames(base_fn, ov)


def body_pose(parts, P, pivot=(0, 0, 0), lean_scale=1.0, lunge=0.0):
    """Apply lean (about the base), squash (about the ground), bob and an attack lunge (metres
    forward at strike=1) to a rest-space part list."""
    a = P['lean'] * lean_scale
    R = rot_x(a) @ rot_z(P.get('topple', 0.0))
    if abs(P['squash'] - 1) > 1e-4:
        parts = squash_parts(parts, sy=P['squash'], sxz=1.0 / np.sqrt(P['squash']), pivot=pivot)
    tz = lunge * P['strike']
    if abs(a) > 1e-5 or abs(P.get('topple', 0)) > 1e-5 or abs(P['bob']) > 1e-5 or tz:
        parts = transform_parts(parts, R=R, t=(0, P['bob'], tz), pivot=pivot)
    return parts


# ------------------------------------------------------------------ materials

def _arr(c, n):
    return np.array(c)[None, :].repeat(n, 0)


def calcite_mat(flush=0.25, flush_col=PINK, pores=True, base_col=CALC, low_col=None, brush=0.08):
    """Chalky porous calcite. flush blooms pink through it; pores dot the surface."""
    def alb(p, n):
        a = _arr(base_col, len(p))
        f = np.clip((fbm(p, 9.0, 3) - (0.62 - flush)) * 3.0, 0, 1)[:, None]
        a = a * (1 - f) + np.array(flush_col)[None, :] * f
        if low_col is not None:
            g = np.clip(0.35 - p[:, 1], 0, 0.35)[:, None] / 0.35
            a = a * (1 - g * 0.6) + np.array(low_col)[None, :] * g * 0.6
        if pores:
            pr = vnoise(p, 120.0)
            a = np.where((pr > 0.72)[:, None], a * 0.72 + np.array(DUSK)[None, :] * 0.18, a)
        return a
    return Material(alb, spec=0.05, gloss=10, brush=brush)


def coral_mat(deep=0.18, base_col=CORAL, deep_col=RED, hi_col=PINK, freq=11.0, brush=0.07):
    def alb(p, n):
        a = _arr(base_col, len(p))
        f = fbm(p, freq, 3)
        d = np.clip((0.45 - f) * 3.0 * deep * 2, 0, 0.7)[:, None]
        h = np.clip((f - 0.6) * 4.0, 0, 1)[:, None] * np.clip(n[:, 1], 0, 1)[:, None]
        a = a * (1 - d) + np.array(deep_col)[None, :] * d
        a = a * (1 - h * 0.5) + np.array(hi_col)[None, :] * h * 0.5
        pr = vnoise(p, 110.0)
        a = np.where((pr > 0.74)[:, None], a * 0.8, a)
        return a
    return Material(alb, spec=0.08, gloss=12, brush=brush)


def flesh_mat(col=PINK, inner=RED, P=None, glow=0.0):
    """Soft translucent polyp flesh. glow > 0 adds a faint pulse under the skin."""
    em = None
    if glow > 0 and P is not None:
        g = glow * P['glow']
        em = tuple(np.array(GLOW) * min(g, 1.0) * 0.35)
    def alb(p, n):
        f = fbm(p, 24.0, 2)[:, None]
        return _arr(col, len(p)) * (0.85 + 0.25 * f) * 0.9 + _arr(inner, len(p)) * 0.1
    return Material(alb, spec=0.35, gloss=28, sss=0.7, brush=0.03, emissive=em)


def mouth_mat():
    return Material(_hex('#5e2128'), spec=0.4, gloss=30, sss=0.3, brush=0.02, rim=0.3)


def glow_mat(P, col=GLOW, k=1.0):
    g = np.clip(k * (0.55 + 0.45 * P['glow'] + 0.8 * P['cast_glow']), 0, 1.6)
    c = tuple(np.clip(np.array(col) * g, 0, 1))
    return Material(col, spec=0.2, emissive=c, rim=0.0, brush=0.0)


def pore_glow_mat(P, base_mat_alb, col=GLOW, freq=55.0, thresh=0.74, k=1.0):
    """Calcite whose pores breathe light (Reef tell)."""
    g = np.clip(k * (0.35 + 0.45 * P['glow'] + 0.9 * P['cast_glow']), 0, 1.6)
    def em(p, n):
        pr = vnoise(p, freq)
        m = np.clip((pr - thresh) * 10, 0, 1)[:, None]
        return np.array(col)[None, :] * m * g
    def alb(p, n):
        a = base_mat_alb(p, n)
        pr = vnoise(p, freq)
        m = np.clip((pr - thresh) * 10, 0, 1)[:, None]
        return a * (1 - m) + np.array(col)[None, :] * m
    return Material(alb, spec=0.06, gloss=10, brush=0.07, emissive=em)


def lens_mat(P, k=1.0):
    g = np.clip(k * (0.5 + 0.4 * P['glow'] + 0.9 * P['cast_glow'] + 0.6 * P['fx']), 0, 1.8)
    def em(p, n):
        # bright core, glassy rim: brighter where the surface faces the viewer/sky
        f = 0.55 + 0.45 * np.clip(n[:, 1], 0, 1)
        return np.array(LENS)[None, :] * (f * g * 0.85)[:, None]
    return Material(_hex('#d6f6f3'), spec=1.0, gloss=80, emissive=em, rim=0.6, brush=0.0)


def reef_mats(P, glow=0.6):
    return {
        'calcite_b': calcite_mat(flush=0.18),
        'calcite_p': calcite_mat(flush=0.45),
        'coral': coral_mat(),
        'coral_dk': coral_mat(deep=0.4, base_col=_hex('#cf6b5f')),
        'flesh': flesh_mat(P=P, glow=glow),
        'mouth': mouth_mat(),
        'glow': glow_mat(P),
        'reefred': Material(RED, spec=0.1, gloss=14, brush=0.08),
    }


# ------------------------------------------------------------------ SDF helpers

def seg(q, a, b, ra, rb):
    """Round-cone distance with per-point (N,3) or (3,) endpoints and radii."""
    ba = b - a
    pa = q - a
    L2 = np.maximum((ba * ba).sum(-1), 1e-9)
    h = np.clip((pa * ba).sum(-1) / L2, 0, 1)
    r = ra + (rb - ra) * h
    return np.linalg.norm(pa - h[..., None] * ba, axis=-1) - r


def spire(base_pt, L, r0, r1=0.0, n=8, flute=0.14, bend=(0.0, 0.0), twist=0.0, bulge=0.0,
          bulge_at=0.5, porous=0.0, top_round=0.02, neck=0.0):
    """Fluted tower from base_pt straight up L metres. r0 base radius, r1 top radius.
    bend=(bx,bz): the tip moves bx*L, bz*L sideways (quadratic bend, for sway).
    bulge adds a swelling at bulge_at; flute is groove depth as a fraction of radius."""
    b = v3(*base_pt)
    bx, bz = bend

    def rad(t):
        r = r0 + (r1 - r0) * t
        r = r + bulge * np.exp(-((t - bulge_at) / 0.18) ** 2)
        if neck:
            r = r * (1 - neck * np.exp(-((t - 0.82) / 0.08) ** 2))
        return np.maximum(r, 0.004)

    def f(p):
        q = p - b
        t = np.clip(q[:, 1] / L, 0, 1)
        x = q[:, 0] - bx * L * t * t
        z = q[:, 2] - bz * L * t * t
        th = np.arctan2(x, z) + twist * t
        r = rad(t)
        rr = r * (1 - flute * (0.5 - 0.5 * np.cos(n * th)) ** 1.5)
        d = np.sqrt(x * x + z * z) - rr
        if porous:
            d = d + porous * (fbm(p, 34.0, 2) - 0.5)
        dy = np.maximum(-q[:, 1], q[:, 1] - L)
        return smax(d, dy, top_round) * 0.7

    rm = max(r0, r1) + abs(bulge)
    return Func(f, b + v3(bx * L * 0.5, L * 0.5, bz * L * 0.5), L * 0.55 + rm + (abs(bx) + abs(bz)) * L)


def crown(c, n, r_start, length, rise, rad0, rad1, sway=None, curl=0.0, droop=0.0, R=None,
          twist_phase=0.0, tangential=0.4):
    """Polar ring of n tapered 3-segment fronds starting at radius r_start around centre c.
    Each frond goes out (length) and up (rise), curling up by curl at the tip (or drooping).
    sway(i) -> (radial, up, tangential) offsets in metres for frond i (per-frond animation)."""
    c = v3(*c)
    Rm = np.eye(3) if R is None else R
    sec = 2 * np.pi / n
    offs = np.array([sway(i) if sway else (0.0, 0.0, 0.0) for i in range(n)], dtype=np.float64)

    def frond(qx, qy, qz, i):
        o = offs[i % n]
        rad_o, up_o, tan_o = o[:, 0], o[:, 1], o[:, 2] * tangential
        z0 = np.zeros_like(qx)
        a = np.stack([z0 + r_start, z0, z0], -1)
        m1 = np.stack([z0 + r_start + length * 0.45 + rad_o * 0.3, z0 + rise * 0.5 + up_o * 0.3, tan_o * 0.3], -1)
        m2 = np.stack([z0 + r_start + length * 0.85 + rad_o * 0.7, z0 + rise * 0.85 + up_o * 0.7 - droop * 0.4, tan_o * 0.7], -1)
        tip = np.stack([z0 + r_start + length + rad_o - curl * 0.5, z0 + rise + up_o + curl - droop, tan_o], -1)
        q = np.stack([qx, qy, qz], -1)
        rm1 = rad0 + (rad1 - rad0) * 0.45
        rm2 = rad0 + (rad1 - rad0) * 0.85
        d = seg(q, a, m1, rad0, rm1)
        d = np.minimum(d, seg(q, m1, m2, rm1, rm2))
        d = np.minimum(d, seg(q, m2, tip, rm2, rad1))
        return d

    def f(p):
        q = (p - c) @ Rm
        ang = np.arctan2(q[:, 2], q[:, 0]) - twist_phase
        rad = np.sqrt(q[:, 0] ** 2 + q[:, 2] ** 2)
        best = np.full(len(p), 1e3)
        i0 = np.floor(ang / sec + 0.5).astype(np.int64)
        for di in (-1, 0, 1):
            i = i0 + di
            a2 = ang - i * sec
            best = np.minimum(best, frond(rad * np.cos(a2), q[:, 1], rad * np.sin(a2), np.mod(i, n)))
        return best

    ext = r_start + length + abs(rise) + abs(curl) + rad0 + 0.1
    return Func(f, c + Rm @ v3(0, rise * 0.5, 0), ext)


def fan(pivot, R, radius, half_angle, ribs=9, thick=0.012, scallop=0.08, holes=0.0, rib_k=0.006):
    """A ribbed sea-fan blade. Local frame R: columns (u, v, w); the fan opens in the u-v plane,
    centred on +v from the pivot, spanning +-half_angle. holes>0 punches a lattice."""
    pv = v3(*pivot)

    def f(p):
        q = (p - pv) @ R
        u, v, w = q[:, 0], q[:, 1], q[:, 2]
        rad = np.sqrt(u * u + v * v)
        th = np.arctan2(u, v)
        edge = radius * (1 - scallop * (0.5 - 0.5 * np.cos(ribs * 2 * np.pi * th / (2 * half_angle))) ** 0.7)
        d_r = rad - edge
        d_a = (np.abs(th) - half_angle) * np.maximum(rad, 0.02)
        rib = 0.5 + 0.5 * np.cos(ribs * 2 * np.pi * th / (2 * half_angle))
        tk = thick * (0.55 + 0.45 * (1 - rad / radius)) + rib_k * rib ** 4
        d_w = np.abs(w) - tk
        d = np.maximum(np.maximum(d_r, d_a), d_w)
        if holes:
            cell = np.sin(rad * holes) * np.sin(th * holes * 0.35 * radius)
            d = np.maximum(d, -(np.abs(cell) - 0.55) * 0.01 - (rib > 0.85) * 1.0)
        return d * 0.8

    return Func(f, pv + R @ v3(0, radius * 0.5, 0), radius * 0.6 + 0.05)


def fib_dirs(n, seed=0, jitter=0.15, ymin=-1.0):
    rng = np.random.default_rng(seed)
    out = []
    g = np.pi * (3 - np.sqrt(5))
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        r = np.sqrt(1 - y * y)
        a = g * i
        d = v3(np.cos(a) * r, y, np.sin(a) * r) + rng.normal(0, jitter, 3)
        d = norm(d)
        if d[1] >= ymin:
            out.append(d)
    return out


def spike_ball(c, r_body, dirs, length, r_base, r_tip=0.003, lens=None):
    """Urchin: a body sphere plus tapered spikes along dirs (lens: per-spike length multipliers)."""
    c = v3(*c)
    D = np.array(dirs)
    Ls = np.ones(len(D)) if lens is None else np.asarray(lens)

    cmin = np.cos(np.arcsin(min(0.99, (r_base * 2.5) / max(r_body, 1e-3))) + 0.35)

    def f(p):
        q = p - c
        ln = np.linalg.norm(q, axis=1)
        d = ln - r_body
        cosang = (q / np.maximum(ln, 1e-6)[:, None]) @ D.T          # (N, K)
        near = (cosang > cmin) | (ln < r_body * 1.1)[:, None]
        for k in range(len(D)):
            m = near[:, k]
            if not m.any():
                continue
            a = D[k] * r_body * 0.6
            b = D[k] * (r_body + length * Ls[k])
            d[m] = np.minimum(d[m], seg(q[m], a, b, r_base, r_tip))
        return d
    return Func(f, c, r_body + length * Ls.max() + r_base)


def brain(c, radii, groove=0.012, freq=38.0, R=None):
    """Brain-coral head: ellipsoid with meandering grooves."""
    c = v3(*c)
    Rm = np.eye(3) if R is None else R
    rr = v3(*radii)

    def f(p):
        q = (p - c) @ Rm
        k0 = np.linalg.norm(q / rr, axis=1)
        k1 = np.linalg.norm(q / (rr * rr), axis=1)
        d = k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)
        m = np.sin(freq * q[:, 0] + 2.2 * np.sin(freq * 0.7 * q[:, 2]) + 1.5 * np.sin(freq * 0.6 * q[:, 1]))
        m = m + np.sin(freq * 0.9 * q[:, 2] + 2.0 * np.sin(freq * 0.8 * q[:, 1]))
        d = d + groove * (1 - np.abs(np.tanh(1.6 * m)))
        return d * 0.75
    return Func(f, c, float(rr.max()) + groove)


def branches(add, root, direction, L, r, depth, mat, rng, k=0.02, spread=0.55, sway=(0.0, 0.0),
             taper=0.68, kids=(2, 3), up_bias=0.35, tip=None, level=0):
    """Recursive branching capsules. sway=(sx, sz) bends each level a little more toward (sx,0,sz).
    tip(add, end_point, direction, radius) is called at every terminal branch."""
    d = norm(v3(*direction) + v3(sway[0], 0, sway[1]) * (level + 1) * 0.5)
    a = v3(*root)
    b = a + d * L
    add(Capsule(a, b, r, r * taper), mat, k)
    if depth <= 0:
        if tip:
            tip(add, b, d, r * taper)
        return
    nk = rng.integers(kids[0], kids[1] + 1)
    for j in range(nk):
        ang = rng.uniform(0, 2 * np.pi) + j * 2 * np.pi / nk
        side = norm(np.cross(d, v3(np.cos(ang), 0.1, np.sin(ang))) + 1e-6)
        nd = norm(d + side * spread * rng.uniform(0.7, 1.3) + v3(0, up_bias, 0))
        branches(add, b, nd, L * rng.uniform(0.6, 0.8), r * taper, depth - 1, mat, rng, k * 0.8, spread,
                 sway, taper, kids, up_bias, tip, level + 1)


def tube(add, a, b, r, mat, mouth_mat='mouth', lip_mat=None, k=0.015, open_=0.6):
    """Open polyp tube from a to b. The mouth is a dark hollow at b, with a soft lip."""
    a, b = v3(*a), v3(*b)
    d = norm(b - a)
    body = Capsule(a, b, r * 1.05, r)
    hole = Capsule(b - d * r * 0.4, b + d * r * 2, r * (0.35 + 0.35 * open_))
    add(Subtract(body, hole, 0.008), mat, k)
    add(Sphere(b - d * r * (0.7 + 0.4 * (1 - open_)), r * 0.6), mouth_mat, 0.0)
    if lip_mat:
        add(Torus(b - d * r * 0.25, d, r * 0.82, r * 0.22), lip_mat, 0.006)


def legs(add, P, centre, rx, rz, n=6, h=0.12, r=0.018, mat='calcite_b', k=0.012, lift=0.03, reach=0.06):
    """Scuttling spine legs around an oval body; alternate pairs step with the stride channel."""
    c = v3(*centre)
    s = P['stride']
    for i in range(n):
        ang = np.pi * 0.5 + (i + 0.5) * 2 * np.pi / n
        ph = 1 if i % 2 == 0 else -1
        x, z = np.cos(ang) * rx, np.sin(ang) * rz
        hip = c + v3(x * 0.6, 0, z * 0.6)
        footz = z * 1.25 + s * ph * reach
        foot = v3(x * 1.35, max(0.0, lift * s * ph) + 0.012, footz)
        knee = (hip + foot) / 2 + v3(x * 0.35, h * 0.5, z * 0.15)
        add(Capsule(hip, knee, r, r * 0.8), mat, k)
        add(Capsule(knee, foot, r * 0.8, r * 0.35), mat, 0.004)


def ground_root(add, c, n, length, r, mat, rng, k=0.02, y=0.015):
    """Root runners spreading over the ground from c."""
    c = v3(*c)
    for i in range(n):
        ang = i * 2 * np.pi / n + rng.uniform(-0.3, 0.3)
        e = c + v3(np.cos(ang) * length * rng.uniform(0.7, 1.1), y - c[1], np.sin(ang) * length * rng.uniform(0.7, 1.1))
        m = (c + e) / 2 + v3(0, 0.02, 0)
        add(Capsule(c + v3(0, 0.03, 0), m, r, r * 0.7), mat, k)
        add(Capsule(m, e, r * 0.7, r * 0.25), mat, k * 0.5)




def ribbed(c, radii, n=12, depth=0.012, R=None, porous=0.0):
    """Ellipsoid shell with n longitudinal ridges running along its local z axis (shell / carapace)."""
    c = v3(*c)
    Rm = np.eye(3) if R is None else R
    rr = v3(*radii)

    def f(p):
        q = (p - c) @ Rm
        k0 = np.linalg.norm(q / rr, axis=1)
        k1 = np.linalg.norm(q / (rr * rr), axis=1)
        d = k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)
        th = np.arctan2(q[:, 0], q[:, 1])
        d = d + depth * (0.5 - 0.5 * np.cos(n * th)) ** 1.5
        if porous:
            d = d + porous * (fbm(p, 40.0, 2) - 0.5)
        return d * 0.75
    return Func(f, c, float(rr.max()) + depth)


def scaled(parts, s, pivot=(0, 0, 0)):
    return transform_parts(parts, s=s, pivot=pivot)


def chain(add, pts, r0, r1, mat, k=0.01, first_k=None):
    """Tapered capsule chain through pts (a stalk, neck, tentacle)."""
    pts = [v3(*q) for q in pts]
    n = len(pts) - 1
    for i in range(n):
        ra = r0 + (r1 - r0) * i / n
        rb = r0 + (r1 - r0) * (i + 1) / n
        add(Capsule(pts[i], pts[i + 1], ra, rb), mat, (first_k if (i == 0 and first_k is not None) else k))


def bez(a, b, c, n=5, d=None):
    """Points along a quadratic (or cubic, with d) Bezier."""
    a, b, c = v3(*a), v3(*b), v3(*c)
    out = []
    for i in range(n + 1):
        t = i / n
        if d is None:
            out.append((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t * t * c)
        else:
            dd = v3(*d)
            out.append((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t * t * c + t ** 3 * dd)
    return out


def glass_mat(P, k=0.5):
    g = np.clip(k * (0.6 + 0.4 * P['glow'] + 1.2 * P['cast_glow'] + 0.8 * P['fx']), 0, 1.2)
    def alb(p, n):
        f = fbm(p, 16.0, 2)[:, None]
        return _arr(_hex('#d4f3f0'), len(p)) * (0.85 + 0.25 * f)
    def em(p, n):
        f = np.clip(0.5 - n[:, 2] * 0.3 + 0.5 * n[:, 1], 0, 1)
        return np.array(LENS)[None, :] * (f * g)[:, None]
    return Material(alb, spec=1.2, gloss=90, emissive=em, rim=1.3, brush=0.01)


__all__ = [n for n in dir() if not n.startswith('__')]

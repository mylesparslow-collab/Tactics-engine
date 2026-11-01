"""Shared helpers for the Returning Tide (drowned green, black, wet grey, bleached linen, brine glint).

Shape language: ragged vertical shapes, hooded, soaked, slumped yet upright, wavy drooping hems.
Everything is wet: cloth has a high specular sheen and darkens toward the hem, drips fall from
hems and sleeves (the idle tell, driven by P['tell']), and most units stand in a small puddle.
Death: collapse, a slight sink and the kit brine pool (finish(..., 'pool') + humanoid_rows sink).
"""
import numpy as np
from kit.humanoid import *          # noqa: F401,F403  (v3, norm, prims, Material, finish, ...)
from kit.anim import humanoid_rows
from kit.looks import LOOKS, PALETTES
import rig

FACTION = 'returning_tide'
LOOK = LOOKS[FACTION]
T = PALETTES[FACTION]

GREEN = _hex('#3f7a5c')
GREEN_DK = _hex('#2a4f3f')
GREEN_BK = _hex('#1b2a25')
BLACK = _hex('#14181a')
WET_GREY = _hex('#6d7a78')
GREY_DK = _hex('#4a5554')
LINEN = _hex('#cfd2c4')
LINEN_DK = _hex('#a9ad9f')
BRINE = _hex('#4fa3a0')
GLINT = _hex('#8fe0d8')
SKIN_PALE = _hex('#c9b6a2')      # pale, damp, faintly green
SKIN_DROWNED = _hex('#9aa898')    # risen dead: grey-green
SKIN_WARM = _hex('#c49a80')
BARNACLE = _hex('#c2bca8')
GOLD = _hex('#b8954a')
KELP = _hex('#5a6a3a')


# ------------------------------------------------------------------ materials

def wet_cloth(color, wet=0.7, low_dark=0.38, streak=0.10, spec=None, gloss=None, brush=0.08, top=1.5):
    """Sodden cloth: darkens toward the ground (water wicks up), vertical wet streaks, glossy sheen."""
    col = np.array(color)

    def fn(p, n):
        y = p[:, 1]
        dark = 1 - low_dark * np.clip((top - y) / top, 0, 1) ** 1.4
        st = fbm(p * np.array([1.0, 0.12, 1.0]), 26.0, 2)
        v = (0.92 + 0.12 * fbm(p, 18, 2)) * dark * (1 - streak * (st > 0.55))
        return col[None, :] * v[:, None]
    return Material(fn, spec=spec if spec is not None else 0.10 + 0.22 * wet,
                    gloss=gloss if gloss is not None else 10 + 10 * wet, brush=brush)


def wet_skin(P, color, hair=BLACK, **face_kw):
    return Material(tide_face(P, color, hair, **face_kw), spec=0.30, gloss=26, sss=0.45, brush=0.03)


def tide_face(P, skin, hair, eyes=_hex('#1e2224'), lips=_hex('#7e5a54'), brows=True, mouth=0.0,
              spectacles=None, beard=None, milky=False, sunken=0.0):
    """Head-space face paint. mouth 0..1 opens a dark singing mouth; spectacles=rgb paints round rims;
    milky=True gives the risen dead pale clouded eyes (solemn, not gory); sunken darkens sockets."""
    def fn(p, n):
        q = (p - P['head']) @ head_R(P)
        q = q / P['height']
        base = np.array(skin)[None, :].repeat(len(p), 0)
        front = q[:, 2] > 0.035
        if sunken > 0:
            for sx in (-1, 1):
                s = np.exp(-(((q[:, 0] - sx * 0.034) / 0.03) ** 2 + ((q[:, 1] - 0.003) / 0.02) ** 2))
                base = base * (1 - sunken * 0.45 * s[:, None])
        for sx in (-1, 1):
            e = ((q[:, 0] - sx * 0.034) / 0.017) ** 2 + ((q[:, 1] - 0.005) / 0.009) ** 2
            base[(e < 1) & front] = _hex('#c9d3cc') if milky else eyes
            if milky:
                base[(e < 0.25) & front] = _hex('#8a9a94')
            if brows:
                b = (((q[:, 0] - sx * 0.036) / 0.024) ** 2 + ((q[:, 1] - 0.030) / 0.006) ** 2 < 1) & front
                base[b] = hair
            if spectacles is not None:
                r = np.sqrt(((q[:, 0] - sx * 0.035) / 0.026) ** 2 + ((q[:, 1] - 0.004) / 0.021) ** 2)
                base[(np.abs(r - 1) < 0.22) & front] = spectacles
        if spectacles is not None:
            br = (np.abs(q[:, 0]) < 0.012) & (np.abs(q[:, 1] - 0.010) < 0.004) & front
            base[br] = spectacles
        cheek = np.exp(-(((np.abs(q[:, 0]) - 0.045) / 0.03) ** 2 + ((q[:, 1] + 0.03) / 0.03) ** 2))
        base = base * (1 - 0.10 * cheek[:, None]) + np.array(_hex('#b98a7c'))[None, :] * 0.10 * cheek[:, None]
        if beard is not None:
            bm = (q[:, 1] < -0.02) & (q[:, 2] > -0.02)
            base[bm] = beard
        if mouth > 0:
            m = ((q[:, 0] / 0.020) ** 2 + ((q[:, 1] + 0.060) / (0.006 + 0.016 * mouth)) ** 2 < 1) & front
            base[m] = _hex('#2a1616')
        else:
            lip = ((q[:, 0] / 0.022) ** 2 + ((q[:, 1] + 0.058) / 0.006) ** 2 < 1) & front
            base[lip] = lips
        return base
    return fn


def base_mats(P):
    """Materials every Tide unit shares."""
    return {
        'drip': Material(GLINT, spec=1.2, gloss=80, emissive=tuple(np.array(BRINE) * 0.35), rim=1.0, brush=0.0),
        'water': Material(lambda p, n: np.array(BRINE)[None, :] * (0.85 + 0.3 * fbm(p, 30, 2)[:, None]),
                          spec=1.2, gloss=70, emissive=tuple(np.array(BRINE) * 0.30), brush=0.02),
        'puddle': Material(lambda p, n: np.array(_hex('#2f4a4a'))[None, :] * (0.85 + 0.3 * fbm(p, 14, 2)[:, None]),
                           spec=1.4, gloss=90, brush=0.0),
        'barnacle': Material(lambda p, n: np.where((fbm(p, 60, 2) > 0.55)[:, None], np.array(_hex('#6f7468'))[None, :],
                                                   np.array(BARNACLE)[None, :]), spec=0.2, gloss=14, brush=0.08),
        'cord': Material(_hex('#2a2622'), spec=0.3, gloss=24, brush=0.05),
        'kelp': Material(KELP, spec=0.6, gloss=40, brush=0.06),
        'rust': Material(_hex('#6e4636'), spec=0.3, gloss=18, brush=0.12),
        'gold': Material(GOLD, spec=0.8, gloss=36, metal=0.8, brush=0.05),
        'linen': wet_cloth(LINEN, wet=0.5, low_dark=0.2),
        'black': wet_cloth(BLACK, wet=0.9, low_dark=0.0),
    }


# ------------------------------------------------------------------ cloth shells

def ragged_robe(P, hem=0.10, flare=0.8, top=1.02, opening=0.0, rag=1.0, seed=0.0, droop=0.03,
                girth=1.0, depth=1.0):
    """Closed (or split) robe from the waist to a wavy, tattered, drooping hem.
    hem: base hem height (m at height 1). rag: tatter amount. droop: back hangs lower than the front."""
    pel = P['pelvis']
    h, b = P['height'], P['build']
    sway = P['skirt_sway']
    top_y = top * h
    hem0 = hem * h

    def f(p):
        dy = pel[1] - 0.94 * h
        x = p[:, 0] - pel[0]
        z = p[:, 2] - pel[2]
        y = p[:, 1] - dy
        t = np.clip((top_y - y) / max(top_y - hem0, 0.2), 0, 1.25)
        x = x - sway * 0.06 * t * t
        z = z - abs(sway) * 0.015 * t * t
        theta = np.arctan2(x, z)
        rx = (0.140 * b + 0.13 * flare * t ** 1.3) * girth
        rz = (0.105 * b * depth + 0.10 * flare * t ** 1.3) * girth
        fold = 1 + 0.085 * t ** 0.8 * np.sin(theta * 7 + 0.6 + seed) + 0.04 * t * np.sin(theta * 13 + 2.0 + seed)
        rad = np.sqrt((x / rx) ** 2 + (z / rz) ** 2)
        d = (rad - fold) * np.minimum(rx, rz) * 0.8
        hy = (hem0 + rag * (0.035 * np.sin(theta * 5 + 1.0 + seed) + 0.02 * np.sin(theta * 11 + 2.3 + seed * 1.3)
                            + 0.04 * np.clip((np.sin(theta * 17 + seed * 1.7) - 0.45) * 2.5, 0, 1))
              - droop * (0.5 - 0.5 * np.cos(theta)) * h)
        d = np.maximum(d, np.maximum(y - top_y, hy - y))
        d = np.maximum(d, 0.004 - p[:, 1])
        d = np.abs(d + 0.008) - 0.010
        if opening > 0:
            w = np.clip((top_y - 0.02 * h - y) / (0.70 * h), 0, 1) ** 0.8 * opening
            wedge = (np.abs(theta) - w) * np.sqrt(x * x + z * z)
            d = smax(d, -wedge, 0.01)
        return d
    return Func(f, (pel[0], pel[1] - 0.30 * h, pel[2]), 0.62 * h * max(1.0, flare * girth))


def shawl(P, depth=0.26, width=0.21, rag=1.0, seed=0.0, sq=2.2, front_drop=0.06, thick=0.010):
    """Rounded shoulder shawl with a wavy, dripping lower edge (soft superellipse, not the Concord's square)."""
    nk = P['neck']
    b = P['build']
    lean = P['chest'] - P['pelvis']
    up = norm(lean)
    R = basis_from(up, (0, 0, 1))

    def f(p):
        q = (p - (nk + v3(0, 0.01, -0.012))) @ R
        y = q[:, 1]
        theta = np.arctan2(q[:, 0], q[:, 2])
        lim = depth + front_drop * np.clip(np.cos(theta), 0, 1) + rag * (0.025 * np.sin(theta * 6 + seed)
                                                                         + 0.035 * np.clip((np.sin(theta * 13 + seed * 2) - 0.4) * 2.5, 0, 1))
        t = np.clip(-y / depth, 0, 1.3)
        rx = (0.080 + width * t ** 0.55) * b
        rz = (0.072 + 0.10 * t ** 0.6) * b
        fold = 1 + 0.04 * t * np.sin(theta * 9 + seed)
        rad = ((np.abs(q[:, 0]) / rx) ** sq + (np.abs(q[:, 2]) / rz) ** sq) ** (1 / sq)
        d = (rad - fold) * np.minimum(rx, rz) * 0.7
        d = np.maximum(d, np.maximum(y, -lim - y))
        return np.abs(d + thick * 0.7) - thick
    return Func(f, nk + v3(0, -0.12, 0), 0.40 * b)


def deep_hood(P, add, mat, size=1.08, peak=0.06, tail=0.30, droop=0.02):
    """Kit hood plus a sodden liripipe tail hanging down the back (ragged vertical line)."""
    add(hood_shell(P, size=size, peak=peak, droop=droop), mat, 0.0)
    if tail > 0:
        H, R, h = P['head'], head_R(P), P['height']
        a = H + R @ v3(0, 0.07, -0.10) * h * size
        b = a + v3(0.0, -tail, -0.05) * h
        add(Capsule(a, (a + b) / 2 + v3(0, 0, -0.02), 0.045 * size, 0.035), mat, 0.03)
        add(Capsule((a + b) / 2 + v3(0, 0, -0.02), b, 0.035, 0.018), mat, 0.02)
        return b
    return None


def rag_strips(add, anchor, n, length, mat, spread=0.05, seed=0, sway=0.0, r=0.012):
    """Dangling wet rags (or kelp) from a point: thin tapered capsules that hang and sway."""
    rng = np.random.default_rng(seed)
    ends = []
    for i in range(n):
        off = v3(rng.uniform(-spread, spread), 0, rng.uniform(-spread, spread))
        L = length * rng.uniform(0.6, 1.0)
        a = anchor + off
        b = a + v3(sway * 0.05 + rng.uniform(-0.02, 0.02), -L, rng.uniform(-0.02, 0.02))
        add(Capsule(a, b, r, r * 0.45), mat, 0.0)
        ends.append(b)
    return ends


def sleeve_flare(P, add, s, mat, length=0.16, width=0.075):
    """A wide wet sleeve mouth drooping below the wrist."""
    el, wr = P['el_' + s], P['wr_' + s]
    d = norm(wr - el)
    a = el + (wr - el) * 0.45
    b = wr + v3(0, -length * 0.5, 0) + d * 0.01
    add(Capsule(a, b, 0.055, width), mat, 0.03)
    return b + v3(0, -width * 0.6, 0)


# ------------------------------------------------------------------ water

def drips(P, add, anchors, mat='drip', size=0.013, fall=0.30, speed=1.0):
    """Droplets dropping from anchor points, phase from P['tell'] (idle/move tell)."""
    ph = P.get('tell', 0.0)
    for i, a in enumerate(anchors):
        f = (ph * speed + i * 0.37 + 0.11 * i * i) % 1.0
        dy = fall * f * f
        c = a - v3(0, dy + size, 0)
        if c[1] < 0.02:
            continue
        st = 1.0 + 1.6 * f
        add(Ellipsoid(c, (size * 0.8, size * st, size * 0.8)), mat, 0.0)


def puddle(P, add, r=0.30, center=None, mat='puddle', seed=0.0, grow=1.0):
    """Flat irregular puddle under the feet (thin, glossy, slightly wavy edge)."""
    c = v3(0.0, 0.0, 0.04) if center is None else v3(*center)
    R = r * grow

    def f(p):
        q = p - c
        th = np.arctan2(q[:, 2], q[:, 0])
        rr = R * (1 + 0.10 * np.sin(3 * th + seed) + 0.06 * np.sin(5 * th + 1.3 + seed) + 0.04 * np.sin(9 * th + seed))
        rad = np.sqrt(q[:, 0] ** 2 + (q[:, 2] / 0.85) ** 2)
        return np.maximum(rad - rr, np.abs(q[:, 1] - 0.002) - 0.004)
    add(Func(f, c, R * 1.25), mat, 0.0)


def water_rope(add, a, b, phase=0.0, r=0.017, twist=2.5, amp=0.025, n=10, mat='water', sag=0.0):
    """Two strands of water twisting around each other between two points."""
    d = b - a
    L = np.linalg.norm(d)
    u = norm(d)
    s1 = norm(np.cross(u, v3(0, 0, 1)) if abs(u[2]) < 0.9 else np.cross(u, v3(1, 0, 0)))
    s2 = np.cross(u, s1)
    for strand in (0, np.pi):
        prev = None
        for k in range(n + 1):
            t = k / n
            ang = phase * 2 * np.pi + strand + t * twist * 2 * np.pi
            env = np.sin(np.pi * t) ** 0.5
            p = a + d * t + (s1 * np.cos(ang) + s2 * np.sin(ang)) * amp * env - v3(0, sag * 4 * t * (1 - t), 0)
            if prev is not None:
                add(Capsule(prev, p, r * (0.6 + 0.4 * env)), mat, 0.012)
            prev = p
    return L


def barnacles(add, center, normal, n=6, spread=0.05, size=0.012, seed=0, mat='barnacle'):
    """A cluster of little conical barnacles on a surface."""
    rng = np.random.default_rng(seed)
    nn = norm(normal)
    t1 = norm(np.cross(nn, v3(0, 1, 0.3)))
    t2 = np.cross(nn, t1)
    for i in range(n):
        o = center + t1 * rng.uniform(-spread, spread) + t2 * rng.uniform(-spread, spread)
        s = size * rng.uniform(0.6, 1.3)
        add(Capsule(o - nn * s * 0.3, o + nn * s * 0.9, s, s * 0.55), mat, 0.0)


def knotted_cord(add, P, y_off=0.08, mat='cord', tails=True, girth=1.0):
    """Knotted cord at the waist with two hanging tails ending in knots."""
    pel, h, b = P['pelvis'], P['height'], P['build']
    c = pel + v3(0, y_off * h, 0)

    def belt(p):
        q = p - c
        e = np.sqrt((q[:, 0] / (0.150 * b * girth)) ** 2 + (q[:, 2] / (0.112 * b * girth)) ** 2) - 1.0
        return np.sqrt((e * 0.11) ** 2 + q[:, 1] ** 2) - 0.012
    add(Func(belt, c, 0.24 * b * girth), mat, 0.0)
    if tails:
        k = c + v3(-0.04 * b, -0.01, 0.105 * b * girth)
        add(Sphere(k, 0.022), mat, 0.0)
        for sx, L in ((-1, 0.30), (1, 0.24)):
            e = k + v3(sx * 0.03 + P['skirt_sway'] * 0.03, -L * h, 0.02)
            add(Capsule(k, e, 0.010, 0.008), mat, 0.0)
            add(Sphere(e, 0.016), mat, 0.0)


def rain(add, center, w=0.28, n=9, length=0.12, phase=0.0, mat='drip', top=0.0, bottom=-0.9, seed=3):
    """Short falling streaks below a point (rain from clear sky), looping with phase."""
    rng = np.random.default_rng(seed)
    span = top - bottom
    for i in range(n):
        x = rng.uniform(-w, w)
        z = rng.uniform(-w * 0.7, w * 0.7)
        f = (rng.uniform(0, 1) + phase) % 1.0
        y = top - f * span
        a = center + v3(x, y, z)
        add(Capsule(a, a + v3(0.004, -length, 0), 0.0055, 0.003), mat, 0.0)


def tide_rows(neutral_pose, attack_style='swing', weapon_side='r', sink=0.35, cast_side='l', post=None):
    """Kit humanoid rows with the Tide death (slight sink into a spreading brine pool)."""
    ROWS, fr0 = humanoid_rows(neutral_pose, attack_style=attack_style, weapon_side=weapon_side,
                              sink_depth=sink, cast_side=cast_side)

    def fr():
        out = fr0()
        # The kit kneel throws the back foot far behind the body. Under a Tide robe that bare pale
        # foot pokes out alone and reads as a detached bone at 1x, so tuck it in under the hem.
        for i in (1, 2):
            P = out['death'][i][0]
            h = P['height']
            back = v3(P['an_r'][0] * 0.7, 0.07, P['pelvis'][2] - 0.13 * h)
            rig.place_leg(P, 'r', back, l1=0.43 * h, l2=0.42 * h, pole=(0, -0.3, 1))
        return out
    if post is None:
        return ROWS, fr

    def frames():
        return post(fr())
    return ROWS, frames


def tide_finish(P, parts, mats, add, lights=(), pool_r=0.5):
    """finish() with a larger, rimmed end pool than the kit default."""
    from kit import endstates
    m = base_mats(P)
    m.update(mats)
    e, sink = P['end'], P['sink']
    if sink > 0:
        parts[:] = endstates.sink_parts(parts, sink)
        lights = [Light(L.pos + v3(0, -sink, 0), L.color, L.intensity, L.radius) for L in lights]
    if e > 0:
        puddle(P, add, r=pool_r * (0.4 + 0.6 * e), center=(0.0, 0.0, 0.10), mat='brine', seed=1.7)
    P2 = dict(P)
    P2['sink'] = 0.0
    sc = finish(P2, FACTION, parts, m, lights=lights, add=add)
    sc.ground_clip = sink > 0
    return sc



def hood_down(P, add, mat, size=1.0):
    """A sodden hood fallen back onto the shoulders: a heavy roll of cloth behind the neck."""
    nk, h, b = P['neck'], P['height'], P['build']
    up = norm(P['neck'] - P['chest'])
    R = basis_from(up, (0, 0, 1))
    c = nk + R @ v3(0, -0.02, -0.075) * size
    add(Ellipsoid(c, (0.11 * b * size, 0.06 * size, 0.07 * size), R), mat, 0.02)
    add(Ellipsoid(c + R @ v3(0, -0.07, -0.03) * size, (0.085 * b * size, 0.08 * size, 0.045 * size), R), mat, 0.03)
    add(Torus(nk + v3(0, -0.035, -0.005), up, 0.075 * b * size, 0.022 * size), mat, 0.02)


def wet_hair(P, add, mat, style='short', flat=1.0):
    """Hair plastered flat by water (kit hair, pulled closer to the skull)."""
    H, R, h = P['head'], head_R(P), P['height']
    add(Ellipsoid(H + R @ v3(0, 0.03, -0.022) * h, (0.083 * h, 0.08 * h, 0.088 * h), R), mat, 0.01)
    if style in ('long', 'bob'):
        for sx in (-1, 1):
            add(Ellipsoid(H + R @ v3(sx * 0.07, -0.03, -0.01) * h, (0.022 * h, 0.08 * h, 0.05 * h), R), mat, 0.02)
    if style == 'long':
        a = H + R @ v3(0, -0.02, -0.07) * h
        add(Capsule(a, a + v3(0, -0.24, -0.05) * h, 0.07 * h, 0.035 * h), mat, 0.03)
    if style == 'bun':
        add(Sphere(H + R @ v3(0, 0.03, -0.10) * h, 0.042 * h), mat, 0.01)


def ripples(P, add, n=2, r0=0.22, center=(0.0, 0.0, 0.04), mat='drip', phase=None):
    """Expanding rings on the puddle, phase from P['tell']."""
    ph = P.get('tell', 0.0) if phase is None else phase
    for i in range(n):
        f = (ph + i / n) % 1.0
        r = r0 * (0.4 + 0.8 * f)
        add(Torus(v3(*center) + v3(0, 0.006, 0), v3(0, 1, 0), r, 0.0045 * (1.2 - f)), mat, 0.0)


__all__ = [n for n in dir() if not n.startswith("__")]

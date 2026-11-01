"""Salvage Compact shared helpers: palette, materials, patchwork cloth, ragged diagonal coats,
mismatched hull-plate pauldrons, rope lashings, tin lanterns, kegs, flare belts, goggles,
bone sleds, and the faction idle tell (fidget + lantern/fuse flicker).

Shape language: asymmetric, lashed together, angled. Rust, bone white, tallow yellow, soot;
signal red only for flares. Light comes from powder and tin lanterns, never magic.
"""
import copy
import numpy as np
from kit.humanoid import *
from kit.anim import humanoid_rows
from kit.looks import LOOKS, PALETTES
from sdf import hash3

FACTION = 'salvage_compact'
SV = PALETTES[FACTION]
RUST, BONE, TALLOW, SOOT, FLARE = SV['rust'], SV['bone'], SV['tallow'], SV['soot'], SV['flare']
LAMP_LIGHT = _hex('#ffb05a')
import dataclasses as _dc
LOOK = _dc.replace(LOOKS[FACTION], exposure=1.1, sky_int=0.36)

# muted neutrals for cloth (70%), faction colours used as accents (25%)
CANVAS = _hex('#9a8f78')
OCHRE = _hex('#8f6a3a')
DRAB = _hex('#6e6857')
SAILCLOTH = _hex('#b9ad92')
OILSKIN = _hex('#4a4033')
MUTED_RUST = _hex('#8a5038')
SKINS = dict(light=W['skin_light'], mid=W['skin_mid'], dark=W['skin_dark'], weathered=_hex('#b78262'))


def _arr(c, n):
    return np.array(c)[None, :].repeat(n, 0)


# ------------------------------------------------------------------ material fns

def patchwork(origin_fn, colors, cell=0.085, seed=0, stitch=SOOT, rot=0.5, mute=0.4):
    """Patchwork cloth: angled rectangular patches of different colours with dark stitch seams.
    origin_fn() returns the anchor point (pelvis) so patches ride with the body."""
    cols = np.array(colors)
    c, s = np.cos(rot), np.sin(rot)

    def fn(p, n):
        q = p - origin_fn()
        # rotate the patch grid so seams run on diagonals
        x = q[:, 0] * c - q[:, 1] * s
        y = q[:, 0] * s + q[:, 1] * c
        g = np.stack([x / cell, y / (cell * 1.3), q[:, 2] / cell], 1)
        i = np.floor(g)
        hsh = hash3(i + seed * 7)
        base = cols[(hsh * len(cols)).astype(int) % len(cols)]
        base = base * (1 - mute) + cols[0][None, :] * mute
        f = g - i
        seam = (np.minimum(f[:, 0], 1 - f[:, 0]) < 0.04) | (np.minimum(f[:, 1], 1 - f[:, 1]) < 0.03)
        base = base * (0.9 + 0.16 * fbm(p, 24, 2)[:, None])
        base[seam] = base[seam] * 0.7 + np.array(stitch) * 0.3
        return base
    return fn


def rusty(base=RUST, streak=SOOT, bone_chips=True):
    """Rusted hull plate: rust with dark vertical streaks and pale paint chips."""
    def fn(p, n):
        a = _arr(base, len(p)) * (0.85 + 0.25 * fbm(p, 14, 3)[:, None])
        st = np.clip((fbm(p * np.array([5, 0.4, 5]), 9, 2) - 0.55) * 4, 0, 1)[:, None]
        a = a * (1 - 0.5 * st) + np.array(streak) * 0.5 * st
        if bone_chips:
            ch = (fbm(p, 30, 2) > 0.68)
            a[ch] = np.array(BONE) * 0.8
        return a
    return fn


def painted_plate(origin_fn, R_fn, letters_col=BONE, base=RUST, band=None):
    """Hull plate with half a painted ship's name: blocky letter strokes in plate-local space."""
    rf = rusty(base)

    def fn(p, n):
        a = rf(p, n)
        q = (p - origin_fn()) @ R_fn()
        u, v = q[:, 0], q[:, 1]
        # letters: a row of block glyphs, cut off on one side (half a name)
        lx = (u + 0.2) / 0.07
        li = np.floor(lx)
        lf = lx - li
        row = (v > 0.02) & (v < 0.13) & (li >= 0) & (li < 4)
        h = hash3(np.stack([li, li * 3, li * 5], 1))
        vert = (lf < 0.25) | ((lf > 0.6) & (lf < 0.82) & (h > 0.4))
        horiz = (np.abs(v - 0.125) < 0.016) | ((np.abs(v - 0.075) < 0.014) & (h > 0.3)) | ((np.abs(v - 0.03) < 0.014) & (h < 0.7))
        stroke = row & (lf < 0.82) & (vert | horiz)
        wear = fbm(p, 40, 2) > 0.35
        a[stroke & wear] = np.array(letters_col)
        if band is not None:
            b = np.abs(v + 0.08) < 0.03
            a[b & wear] = np.array(band)
        return a
    return fn


def rope_albedo(p, n):
    t = np.sin((p[:, 0] + p[:, 1] * 1.3 + p[:, 2]) * 260)
    return _arr(_hex('#a3895e'), len(p)) * (0.82 + 0.16 * t[:, None])


def bone_albedo(p, n):
    a = _arr(BONE, len(p)) * (0.86 + 0.16 * fbm(p, 18, 3)[:, None])
    pits = fbm(p, 45, 2) > 0.66
    a[pits] = a[pits] * 0.78
    return a


def sv_materials(P, skin='weathered', hair=_hex('#3a2a20'), beard=None, eyes=_hex('#1f1612'),
                 coat_colors=(CANVAS, MUTED_RUST, OCHRE, SAILCLOTH, DRAB), coat_seed=0, coat_cell=0.085):
    """The faction material set. Keys: skin hair coat coat2 rust plate bone tallow soot rope tin
    canvas oilskin trousers leather boot glove wood lamp flare fuse scrap."""
    g = P['glow']
    pel = lambda: P['pelvis']
    sk = SKINS.get(skin, skin) if isinstance(skin, str) else skin
    fl = FLARE
    m = {
        'skin': Material(face_albedo(P, sk, hair, eyes=eyes, beard=beard), spec=0.06, gloss=12, sss=0.6, brush=0.02),
        'hair': Material(hair, spec=0.2, gloss=16, brush=0.1),
        'coat': Material(patchwork(pel, coat_colors, cell=coat_cell, seed=coat_seed), spec=0.03, brush=0.1),
        'coat2': Material(patchwork(pel, (OILSKIN, DRAB, MUTED_RUST, _hex('#3a332c')), cell=coat_cell * 1.2, seed=coat_seed + 3, rot=-0.6),
                          spec=0.05, brush=0.1),
        'canvas': Material(lambda p, n: _arr(SAILCLOTH, len(p)) * (0.85 + 0.2 * fbm(p, 20, 2)[:, None]), spec=0.02, brush=0.1),
        'oilskin': Material(OILSKIN, spec=0.35, gloss=22, brush=0.06),
        'trousers': Material(lambda p, n: _arr(_hex('#7d725f'), len(p)) * (0.85 + 0.2 * fbm(p, 16, 2)[:, None]), spec=0.02, brush=0.09),
        'rust': Material(rusty(), spec=0.3, gloss=18, metal=0.3, brush=0.1),
        'plate': Material(rusty(_hex('#7d4a30')), spec=0.35, gloss=20, metal=0.35, brush=0.08),
        'bone': Material(bone_albedo, spec=0.12, gloss=14, brush=0.06),
        'tallow': Material(TALLOW, spec=0.25, gloss=20, sss=0.3, brush=0.05),
        'soot': Material(SOOT, spec=0.1, gloss=10, brush=0.06),
        'rope': Material(rope_albedo, spec=0.03, brush=0.05),
        'tin': Material(_hex('#8b8a82'), spec=0.7, gloss=34, metal=0.6, brush=0.06),
        'lamp': Material(_hex('#ffcf7a'), spec=0.3, gloss=30, emissive=tuple(np.array(_hex('#ffc46a')) * min(g, 1.6)), rim=0.0),
        'flare': Material(fl, spec=0.2, gloss=16, brush=0.05),
        'flare_lit': Material(_hex('#ff6a45'), emissive=tuple(np.array(_hex('#ff5a3a')) * 1.2), rim=0.0),
        'fuse': Material(_hex('#ffd48a'), emissive=tuple(np.array(_hex('#ffb347')) * np.clip(g, 0.2, 2.0)), rim=0.0),
        'smoke': Material(_hex('#5c5650'), spec=0.0, brush=0.12, rim=0.4),
        'brass': Material(_hex('#a78a4e'), spec=0.8, gloss=36, metal=0.8, brush=0.06),
        'goggle': Material(_hex('#c9b07a'), spec=1.0, gloss=60, metal=0.2, brush=0.02),
        'scrap': Material(lambda p, n: np.where((hash3(np.floor(p * 30)) > 0.55)[:, None], _arr(BONE, len(p)) * 0.9,
                                                rusty()(p, n)), spec=0.3, gloss=18, brush=0.08),
        'wood': Material(_hex('#5f4430'), spec=0.08, gloss=12, brush=0.1),
        'glove': Material(_hex('#3b2b20'), spec=0.12, gloss=16, brush=0.05),
    }
    return m


# ------------------------------------------------------------------ cloth

def ragged_coat(P, hem_lo=0.30, hem_hi=0.62, slope=1.0, opening=0.5, flare=1.0, girth=1.0, notch=0.05,
                top=1.02):
    """Open coat skirt with a DIAGONAL, ragged hem: low on one side, high on the other.
    slope=+1 puts the long tail on the figure's right (camera side), -1 on its left."""
    pel = P['pelvis']
    h, b = P['height'], P['build']
    sway = P['skirt_sway']
    top_y = top * h

    def f(p):
        dy = pel[1] - 0.94 * h
        x = (p[:, 0] - pel[0])
        z = (p[:, 2] - pel[2])
        y = p[:, 1] - dy
        hem_mid = 0.5 * (hem_lo + hem_hi) * h
        t = np.clip((top_y - y) / (top_y - hem_lo * h), 0, 1.3)
        x = x - sway * 0.05 * t * t
        theta = np.arctan2(x, z)
        rx = (0.135 * b + 0.15 * flare * t ** 1.2) * girth ** 0.5
        rz = (0.100 * b + 0.11 * flare * t ** 1.2) * girth ** 0.5
        fold = 1 + 0.06 * t * np.sin(theta * 6 + 0.6) + 0.035 * t * np.sin(theta * 11 + 2.0)
        rad = np.sqrt((x / rx) ** 2 + (z / rz) ** 2)
        d = (rad - fold) * np.minimum(rx, rz) * 0.8
        # diagonal hem: sin(theta) is +1 at the figure's left (+x)
        hem = hem_mid + slope * np.sin(theta) * 0.5 * (hem_hi - hem_lo) * h
        hem = hem + notch * np.abs(np.sin(theta * 5 + 0.7)) ** 3 - 0.01 * np.sin(theta * 17)
        d = np.maximum(d, np.maximum(y - top_y, hem - y))
        d = np.maximum(d, 0.004 - p[:, 1])
        d = np.abs(d + 0.008) - 0.010
        if opening > 0:
            w = np.clip((top_y - 0.02 * h - y) / (0.70 * h), 0, 1) ** 0.8 * opening
            wedge = (np.abs(theta) - w) * np.sqrt(x * x + z * z)
            d = smax(d, -wedge, 0.01)
        return d
    return Func(f, (pel[0], pel[1] - 0.25 * h, pel[2]), 0.55 * h * max(1.0, flare) * girth ** 0.5)


def scarf(P, add, mat='coat2', tail=True, side=1):
    """Wound neck scarf with a hanging tail over one shoulder."""
    nk = P['neck']
    add(Torus(nk + v3(0, -0.02, 0.005), v3(0.12 * side, 1, 0.05), 0.06 * P['build'], 0.028), mat, 0.02)
    if tail:
        a = nk + v3(side * 0.05, -0.03, 0.07)
        add(Capsule(a, a + v3(side * 0.04, -0.2, 0.03 - 0.05 * P['skirt_sway']), 0.025, 0.018), mat, 0.01)


def wrap_head(P, add, mat='coat2', knot_side=1, size=1.0):
    """Head wrap / bandana: a cloth cap and a knot with two short tails at the back."""
    H, R, h = P['head'], head_R(P), P['height']
    add(Ellipsoid(H + R @ v3(0, 0.04, -0.012) * h, (0.087 * size * h, 0.072 * h, 0.093 * size * h), R), mat, 0.012)
    k = H + R @ v3(knot_side * 0.05, 0.02, -0.085) * h
    add(Sphere(k, 0.024), mat, 0.01)
    add(Capsule(k, k + v3(knot_side * 0.05, -0.1, -0.04), 0.017, 0.008), mat, 0.0)
    add(Capsule(k, k + v3(knot_side * 0.01, -0.12, -0.06), 0.015, 0.007), mat, 0.0)


def tin_cap(P, add, mat='tin', tilt=0.25):
    """Dented tin pot cap worn askew (no tricorns)."""
    H, h = P['head'], P['height']
    R = head_R(P) @ rot_z(tilt)
    add(Ellipsoid(H + R @ v3(0, 0.05, -0.01) * h, (0.094 * h, 0.06 * h, 0.10 * h), R), mat, 0.0)
    add(Cylinder(H + R @ v3(0, 0.022, -0.01) * h, H + R @ v3(0, 0.03, -0.01) * h, 0.11 * h, 0.004), mat, 0.0)


def knit_cap(P, add, mat='coat2', slouch=1.0):
    H, R, h = P['head'], head_R(P), P['height']
    add(Ellipsoid(H + R @ v3(0, 0.05, -0.02) * h, (0.088 * h, 0.07 * h, 0.093 * h), R), mat, 0.01)
    add(Ellipsoid(H + R @ v3(0.02, 0.10, -0.07) * h, (0.05 * h, 0.04 * slouch * h, 0.055 * h), R), mat, 0.03)
    add(Torus(H + R @ v3(0, 0.02, -0.01) * h, R[:, 1], 0.086 * h, 0.016), mat, 0.0)


def goggles(P, add, up=False, lens='goggle', strap='leather'):
    """Brass-rimmed salt goggles over the eyes, or pushed up onto the brow."""
    H, R, h = P['head'], head_R(P), P['height']
    yy = 0.055 if up else 0.008
    zz = 0.07 if up else 0.08
    for sx in (-1, 1):
        c = H + R @ v3(sx * 0.036, yy, zz) * h
        ax = R @ norm(v3(sx * 0.25, 0.2 if up else 0, 1))
        add(Cylinder(c - ax * 0.012, c + ax * 0.012, 0.024, 0.005), 'brass', 0.0)
        add(Cylinder(c + ax * 0.008, c + ax * 0.016, 0.017, 0.003), lens, 0.0)
    add(Torus(H + R @ v3(0, yy, -0.005) * h, R[:, 1], 0.086 * h, 0.009), strap, 0.0)


# ------------------------------------------------------------------ armour, lashings, gear

def pauldron(P, add, side='l', size=1.0, mat='plate', layers=2, rivets=True):
    """One curved hull-plate shoulder (mismatched: only one side), stacked lames, rivets, rope strap."""
    sh = P['sh_' + side]
    sx = -1 if side == 'r' else 1
    up = norm(v3(sx * 0.55, 1.0, 0.0))
    for i in range(layers):
        c = sh + v3(sx * (0.035 + 0.03 * i), 0.035 - 0.055 * i, 0.0) * size
        R = basis_from(up, (0, 0, 1)) @ rot_z(sx * 0.1 * i)

        def f(p, c=c, R=R, s=size * (1 - 0.12 * i)):
            q = (p - c) @ R
            # dome shell clipped to a band: a bent plate
            e = np.sqrt((q[:, 0] / (0.12 * s)) ** 2 + (q[:, 1] / (0.07 * s)) ** 2 + (q[:, 2] / (0.11 * s)) ** 2) - 1
            d = np.abs(e * 0.07 * s) - 0.009
            return np.maximum(d, -q[:, 1] - 0.005)
        add(Func(f, c, 0.16 * size), mat, 0.0)
        if rivets:
            for k in (-1, 0, 1):
                rp = c + R @ v3(k * 0.06 * size, 0.045 * size, 0.07 * size)
                add(Sphere(rp, 0.011), 'tin', 0.0)
    # rope strap across the chest to the other armpit
    o = 'r' if side == 'l' else 'l'
    a = sh + v3(-sx * 0.02, -0.05, 0.07)
    b = P['sh_' + o] + v3(sx * 0.07, -0.16, 0.08)
    add(Capsule(a, b, 0.011), 'rope', 0.0)


def lash(add, a, b, n=3, r=0.022, mat='rope', at=(0.3, 0.5, 0.7)):
    """Rope wraps around the segment a-b at fractions `at`."""
    d = norm(b - a)
    for t in at[:n]:
        add(Torus(a + (b - a) * t, d, r, 0.007), mat, 0.0)


def keg(add, c, up=(0, 1, 0), r=0.09, hh=0.12, mat='wood', hoop='rust', R=None):
    up = norm(v3(*up))
    a, b = c - up * hh, c + up * hh

    def f(p):
        # bulged barrel
        ab = b - a
        t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
        q = p - (a + np.outer(t, ab))
        rr = r * (0.86 + 0.14 * np.sin(np.pi * t))
        return np.maximum(np.linalg.norm(q, axis=1) - rr, np.abs(((p - c) @ up)) - hh)
    add(Func(f, c, max(r, hh) * 1.5), mat, 0.0)
    for t in (-0.75, 0.75):
        add(Torus(c + up * hh * t, up, r * 0.93, 0.008), hoop, 0.0)


def flare_belt(P, add, n=5, lit=-1, mat='flare'):
    """Bandolier of signal flares across the hips (red tubes with tallow caps). lit = index burning."""
    pel, h, b = P['pelvis'], P['height'], P['build']
    for i in range(n):
        ang = np.radians(-60 + i * 22)
        c = pel + v3(np.sin(ang) * 0.15 * b, 0.09 * h, np.cos(ang) * 0.115 * b)
        a, e = c + v3(0, -0.055, 0), c + v3(0, 0.035, 0)
        add(Capsule(a, e, 0.014), mat if i != lit else 'flare', 0.0)
        add(Sphere(e, 0.013), 'tallow', 0.0)


def tin_lantern(add, lights, c, glow, size=1.0, R=None, frame='tin'):
    lantern(add, c, frame, 'lamp', size=size, R=R)
    lights.append(Light(pos=c + v3(0, 0, 0.03), color=LAMP_LIGHT, intensity=1.5 * glow, radius=0.16 * size))


def candle(add, lights, base, P, height=0.08, r=0.016, lit=True):
    """Tallow candle with a fat-flame flicker driven by P['glow']."""
    top = base + v3(0, height, 0)
    add(Capsule(base, top, r, r * 0.9), 'tallow', 0.0)
    add(Ellipsoid(top + v3(0, 0.012, 0), (r * 1.3, r * 1.3, r * 1.3)), 'tallow', 0.01)   # drips
    if lit and P['glow'] > 0.05:
        g = P['glow']
        add(Ellipsoid(top + v3(0, 0.035 * min(g, 1.5), 0), (0.011, 0.026 * min(g, 1.6), 0.011)), 'fuse', 0.0)
        lights.append(Light(pos=top + v3(0, 0.04, 0.02), color=LAMP_LIGHT, intensity=0.6 * g, radius=0.08))


def smoke_puffs(add, c, amount, n=4, seed=3, spread=0.12, size=0.05):
    if amount <= 0:
        return
    rng = np.random.default_rng(seed)
    for i in range(n):
        o = v3(rng.uniform(-1, 1) * spread, i * size * 1.3 + 0.02, rng.uniform(-1, 1) * spread * 0.6)
        add(Sphere(c + o * amount, size * (0.6 + 0.6 * amount) * rng.uniform(0.8, 1.2)), 'smoke', 0.02)


# ------------------------------------------------------------------ rows

def sv_rows(neutral_pose, attack_style='swing', weapon_side='r', cast_side='l', fidget='shoulder', flicker=True):
    """Kit humanoid rows plus the Compact idle tell: a fidget (shoulder hitch, head check, weight
    shift) and a lantern / fuse flicker. Never a static pose: move leans harder, idle shifts weight."""
    ROWS, base_frames = humanoid_rows(neutral_pose, attack_style=attack_style, weapon_side=weapon_side,
                                      cast_side=cast_side)

    def frames():
        fr = base_frames()
        idle = []
        for i, (P, lo) in enumerate(fr['idle']):
            import rig as _rig
            if fidget == 'shoulder':
                _rig.shift(P, ('sh_r', 'el_r', 'wr_r') if weapon_side == 'l' else ('sh_l', 'el_l', 'wr_l'),
                           v3(0, [0, 0.012, 0.022, 0.008][i], 0))
                P['head_yaw'] += np.radians([0, -6, -10, -3][i])
            elif fidget == 'look':
                P['head_yaw'] += np.radians([0, 10, 16, 4][i])
                P['head_pitch'] += np.radians([0, -3, -4, 0][i])
            elif fidget == 'sway':
                _rig.lean(P, side=np.radians([0, 1.5, 2.5, 1.0][i]))
            if flicker:
                P['glow'] = [1.0, 0.62, 1.2, 0.8][i]
            idle.append((P, lo))
        fr['idle'] = idle
        return fr
    return ROWS, frames




# ------------------------------------------------------------------ more gear

def hand_flare(P, add, lights, side='l', amount=None, length=0.16):
    """A lit signal flare held in a hand (cast). The only saturated red in the faction."""
    a = P['cast_glow'] if amount is None else amount
    if a <= 0.05:
        return
    g = hand_pos(P, side)
    d = norm(v3(0.1 if side == 'l' else -0.1, 1, 0.25))
    tip = g + d * length
    add(Capsule(g - d * 0.04, tip, 0.017), 'flare', 0.0)
    add(Ellipsoid(tip + d * 0.03, (0.03 * (0.6 + a), 0.05 * (0.6 + a), 0.03 * (0.6 + a))), 'flare_lit', 0.0)
    lights.append(Light(pos=tip + v3(0, 0.05, 0.03), color=_hex('#ff6040'), intensity=1.6 * a, radius=0.22))
    smoke_puffs(add, tip + v3(0, 0.06, 0), a, n=3, seed=5, spread=0.05, size=0.035)


def tin_cylinder(add, a, b, r, mat='tin', bands=True):
    add(Cylinder(a, b, r, 0.006), mat, 0.0)
    if bands:
        d = norm(b - a)
        L = np.linalg.norm(b - a)
        for t in (0.15, 0.85):
            add(Torus(a + d * L * t, d, r, 0.005), 'rust', 0.0)


def bone_lance(add, g, d, below=0.45, above=1.25):
    """Leviathan-bone lance: tapering pale shaft, rope grip, a jagged bone point."""
    butt, tip = g - d * below, g + d * above
    add(Capsule(butt, tip - d * 0.2, 0.024, 0.016), 'bone', 0.0)
    add(Capsule(tip - d * 0.24, tip, 0.034, 0.004), 'bone', 0.0)
    side = norm(np.cross(d, v3(0, 1, 0.1)))
    add(Capsule(tip - d * 0.18, tip - d * 0.30 + side * 0.06, 0.012, 0.004), 'bone', 0.0)   # barb
    lash(add, g - d * 0.1, g + d * 0.12, n=3, r=0.026, at=(0.1, 0.5, 0.9))
    return butt, tip


# ------------------------------------------------------------------ the bone sled

def bone_sled(add, P, length=1.5, width=0.5, deck=0.17, sail=False, rich=False):
    """Sled of leviathan ribs, centred at origin, pointing +z. P['sled_tilt'] pitches the nose,
    P['spray'] (0..1) throws salt off the runners, P['sled_break'] (0..1) splays the ribs (death)."""
    L, Wd = length, width
    brk = P.get('sled_break', 0.0)
    # runners: long bones that curl up at the front
    for sx in (-1, 1):
        x = sx * Wd * 0.5 + sx * brk * 0.12
        pts = [v3(x, 0.03, -L * 0.5), v3(x, 0.025, L * 0.15), v3(x, 0.06, L * 0.38), v3(x, 0.17, L * 0.5),
               v3(x * 0.92, 0.28, L * 0.5 - 0.02)]
        for a, b in zip(pts[:-1], pts[1:]):
            add(Capsule(a, b + v3(0, -brk * 0.02, 0), 0.026, 0.022), 'bone', 0.015)
        add(Sphere(pts[-1], 0.034), 'bone', 0.0)   # knuckle at the curl
    # rib arches spanning the runners (support the deck)
    for i, zz in enumerate(np.linspace(-L * 0.38, L * 0.26, 4)):
        c = v3(0, 0.03, zz)
        rot = np.radians(8 * brk * (1 if i % 2 else -1))

        def rib(p, c=c, rot=rot):
            q = (p - c) @ rot_z(rot)
            r = np.sqrt(q[:, 0] ** 2 + (q[:, 1] / 0.55) ** 2)
            d = np.abs(r - Wd * 0.5) * 0.55
            d = np.sqrt(d ** 2 + q[:, 2] ** 2) - 0.02
            return np.maximum(d, -q[:, 1])
        add(Func(rib, c + v3(0, 0.08, 0), Wd * 0.6), 'bone', 0.0)
    # deck: lashed hull planks on top of the ribs, a bit askew
    for i in range(5):
        z = -L * 0.40 + i * L * 0.15
        R = rot_y(np.radians([-4, 3, -2, 5, -6][i] + brk * [20, -15, 30, -25, 10][i]))
        add(RoundBox(v3(0.01 * (i % 2), deck + brk * (-0.08), z), (Wd * 0.47, 0.012, L * 0.065), 0.006, R),
            'plank' if i % 3 else 'rust', 0.0)
    # rope lashings where the deck meets the runners
    for sx in (-1, 1):
        for zz in (-L * 0.3, L * 0.1):
            add(Torus(v3(sx * Wd * 0.5, 0.09, zz), v3(0, 0, 1), 0.05, 0.008), 'rope', 0.0)
    # rear cargo: a lashed keg and a coil of rope
    keg(add, v3(0.1, deck + 0.1, -L * 0.42), up=(0, 1, 0), r=0.075, hh=0.09)
    add(Torus(v3(-0.13, deck + 0.03, -L * 0.42), v3(0, 1, 0), 0.07, 0.022), 'rope', 0.0)
    # salt spray off the runners
    sp = P.get('spray', 0.0)
    if sp > 0:
        rng = np.random.default_rng(int(P.get('spray_seed', 1)))
        for sx in (-1, 1):
            for k in range(7):
                t = k / 6
                c = v3(sx * (Wd * 0.5 + 0.06 + t * 0.25 * sp), 0.04 + t * 0.22 * sp + rng.uniform(0, 0.04),
                       -L * 0.5 + 0.1 - t * 0.35 * sp + rng.uniform(-0.05, 0.05))
                add(Sphere(c, (0.045 - 0.025 * t) * (0.6 + 0.6 * sp)), 'spray', 0.03)
    if rich:
        # bone figurehead: a jaw bone at the prow
        add(Capsule(v3(-Wd * 0.46, 0.28, L * 0.48), v3(0, 0.36, L * 0.56), 0.02, 0.012), 'bone', 0.01)
        add(Capsule(v3(Wd * 0.46, 0.28, L * 0.48), v3(0, 0.36, L * 0.56), 0.02, 0.012), 'bone', 0.01)
        for k in range(4):
            t = (k + 1) / 5
            a = v3(-Wd * 0.46, 0.28, L * 0.48) * (1 - t) + v3(0, 0.36, L * 0.56) * t
            add(Capsule(a, a + v3(0, -0.04, 0.01), 0.008, 0.003), 'bone', 0.0)
    return deck


def sled_materials():
    return {
        'plank': Material(lambda p, n: _arr(_hex('#6b5440'), len(p)) * (0.8 + 0.3 * fbm(p * np.array([1, 1, 0.2]), 30, 2)[:, None]),
                          spec=0.06, brush=0.1),
        'spray': Material(_hex('#efeadc'), spec=0.0, brush=0.04, rim=0.6),
    }


def rider_pose(height=1.0, build=1.0, deck=0.17, crouch=0.62, lean_fwd=18, wide=0.2):
    """Crouched rider standing on the sled deck: front foot forward, back foot braced."""
    P = base_pose(height, build)
    h = height
    py = deck + crouch * h
    d = v3(0, py - P['pelvis'][1], 0)
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + rig.UPPER, d)
    rig.place_leg(P, 'l', (0.16 * build, deck + 0.085, 0.24), l1=0.43 * h, l2=0.42 * h, pole=(0.3, 0, 1))
    rig.place_leg(P, 'r', (-0.15 * build, deck + 0.085, -0.22), l1=0.43 * h, l2=0.42 * h, pole=(-0.3, 0, 1))
    P['foot_l_yaw'] = np.radians(25)
    P['foot_r_yaw'] = np.radians(-35)
    rig.lean(P, fwd=np.radians(lean_fwd))
    P.update(sled_tilt=0.0, spray=0.0, spray_seed=1, sled_break=0.0, deck=deck, pitch=0.0, roll=0.0, lift=0.0, coat_fly=0.3)
    return P


def tilt_scene(parts, P, pitch=0.0, roll=0.0, lift=0.0):
    from kit.xform import transform_parts
    if pitch == 0 and roll == 0 and lift == 0:
        return parts
    return transform_parts(parts, R=rot_x(-pitch) @ rot_z(roll), t=(0, lift, 0), pivot=(0, 0, -0.4))


# ------------------------------------------------------------------ sled rider rows

SLED_ROWS = [
    ('idle', 4, True, {}),
    ('move', 4, True, {}),
    ('attack', 10, False, {'hitFrame': 2}),
    ('hit', 10, False, {}),
    ('death', 6, False, {'holdLast': True}),
    ('cast', 8, False, {}),
]


def sled_rows(neutral_pose, attack='thrust', side='r'):
    """Rows for a rider on a bone sled. Pose scalars read by the unit: pitch, roll, lift (whole-scene
    tilt), spray, sled_break, end, glow, cast_glow, fx, coat_fly."""
    sx = -1 if side == 'r' else 1
    UP = ('pelvis', 'hip_r', 'hip_l') + rig.UPPER

    def P0():
        P = neutral_pose()
        P.update(pitch=0.0, roll=0.0, lift=0.0, coat_fly=0.3)
        return P

    def idle(i):
        P = P0()
        b = [0, 1, 0, -1][i]
        rig.shift(P, UP, v3(0, -0.012 * b, 0))
        P['head_yaw'] += np.radians([0, -12, -18, -6][i])
        P['glow'] = [1.0, 0.62, 1.2, 0.8][i]
        P['coat_fly'] = 0.3 + 0.05 * b
        return P, {}

    def move(i):
        P = P0()
        P['pitch'] = np.radians([3, -2, 3, -1][i])
        P['roll'] = np.radians([2, -1, -2, 1][i])
        P['lift'] = [0.0, 0.03, 0.0, 0.02][i]
        P['spray'] = [1.0, 0.7, 0.9, 0.6][i]
        P['spray_seed'] = i + 1
        P['coat_fly'] = 1.0
        rig.lean(P, fwd=np.radians(8))
        rig.shift(P, UP, v3(0, [-0.03, 0, -0.03, 0][i], 0))
        return P, {}

    def atk(i):
        P = P0()
        h = P['height']
        k = [-0.18, -0.08, 0.30, 0.12][i]
        rig.lean(P, fwd=np.radians([-8, -2, 18, 8][i]))
        rig.shift(P, UP, v3(0, 0, k * 0.4))
        w = P['wr_' + side] + v3(0, [0.04, 0.06, 0.0, 0.0][i], k)
        rig.place_arm(P, side, w, (sx * 0.4, -0.4, -1), l1=0.27 * h, l2=0.26 * h)
        if attack == 'swing':
            P['item_' + side] = [norm(v3(sx * 0.3, 0.9, -0.4)), norm(v3(sx * 0.2, 0.9, 0.4)),
                                 norm(v3(-sx * 0.3, -0.3, 0.9)), norm(v3(-sx * 0.1, -0.5, 0.8))][i]
            rig.place_arm(P, side, P['sh_' + side] + [v3(sx * 0.1, 0.12, -0.1), v3(sx * 0.05, 0.15, 0.2),
                                                      v3(sx * 0.0, -0.15, 0.42), v3(sx * 0.05, -0.25, 0.3)][i],
                          (sx * 0.4, -0.3, -1), l1=0.27 * h, l2=0.26 * h)
        P['pitch'] = np.radians([-3, -1, 5, 2][i])
        P['spray'] = [0.3, 0.5, 1.0, 0.6][i]
        P['coat_fly'] = 0.7
        P['fx'] = [0, 0, 1, 0.2][i]
        return P, {}

    def hit(i):
        P = P0()
        rig.lean(P, fwd=np.radians([-14, -5][i]), side=np.radians([4, 1][i]))
        P['head_pitch'] = np.radians([12, 4][i])
        P['roll'] = np.radians([-4, -1][i])
        return P, (dict(exposure=1.25, flash=0.22) if i == 0 else {})

    def death(i):
        P = P0()
        h = P['height']
        rig.shift(P, UP, v3(0, [0, -0.08, -0.18, -0.22][i], 0))
        rig.lean(P, fwd=np.radians([-14, 20, 38, 44][i]), side=np.radians([0, -6, -12, -14][i]))
        P['head_pitch'] = np.radians([16, 24, 36, 40][i])
        for s in ('r', 'l'):
            ss = -1 if s == 'r' else 1
            if i > 0:
                rig.place_arm(P, s, P['pelvis'] + v3(ss * 0.2, -0.12 * i, 0.22), (ss * 0.4, 0, -1), l1=0.27 * h, l2=0.26 * h)
                if P['item_' + s] is not None:
                    P['item_' + s] = norm(v3(ss * 0.5, -0.5, 0.6))
        P['glow'] = [0.8, 0.5, 0.2, 0.0][i]
        P['sled_break'] = [0, 0.2, 0.6, 1.0][i]
        P['roll'] = np.radians([0, -3, -6, -8][i])
        P['end'] = [0, 0.15, 0.5, 1.0][i]
        return P, {}

    def cast(i):
        P = P0()
        h = P['height']
        o = 'l' if side == 'r' else 'r'
        so = -sx
        g = [v3(so * 0.24, 0.0, 0.14), v3(so * 0.22, 0.38, 0.22), v3(so * 0.18, 0.2, 0.36)][i]
        rig.place_arm(P, o, P['sh_' + o] + g, (so * 0.4, -0.5, -1), l1=0.27 * h, l2=0.26 * h)
        P['cast_glow'] = [0.5, 1.0, 0.5][i]
        P['spray'] = [0.6, 1.0, 1.0][i]
        P['spray_seed'] = 7 + i
        P['pitch'] = np.radians([2, -4, 6][i])
        P['lift'] = [0.0, 0.06, 0.02][i]
        P['coat_fly'] = 1.0
        rig.lean(P, fwd=np.radians([4, 10, 16][i]))
        return P, {}

    def frames():
        return {'idle': [idle(i) for i in range(4)], 'move': [move(i) for i in range(4)],
                'attack': [atk(i) for i in range(4)], 'hit': [hit(i) for i in range(2)],
                'death': [death(i) for i in range(4)], 'cast': [cast(i) for i in range(3)]}
    return SLED_ROWS, frames


def coat_tail(P, add, mat='coat', length=0.45, width=0.12):
    """A flying coat tail streaming behind (-z) from the back of the waist."""
    pel = P['pelvis']
    f = P.get('coat_fly', 0.3)
    a = pel + v3(0.0, 0.1, -0.1)
    pts = [a]
    for k in range(1, 4):
        t = k / 3
        pts.append(a + v3(0.04 * np.sin(k * 1.7), -0.25 * t * (1 - f) + 0.04 * f * np.sin(k * 2.2), -length * t * (0.4 + 0.6 * f)))
    for k, (p, q) in enumerate(zip(pts[:-1], pts[1:])):
        L = np.linalg.norm(q - p)
        add(RoundBox((p + q) / 2, (width * (1 - 0.15 * k), L * 0.55, 0.012), 0.01, basis_from(q - p, v3(0, 1, 0))), mat, 0.02)


def place_sled(parts, lights, P, dz=-0.3, yaw=0.0, heel=0.0):
    """Whole sled scene: drift yaw/heel, the row's pitch/roll/lift, then pull it back by dz so the prow
    stays inside the 96x112 frame. Lights are moved with the parts."""
    from kit.xform import transform_parts
    R = rot_x(-P['pitch']) @ rot_z(P['roll']) @ rot_y(yaw) @ rot_z(heel)
    piv = v3(0, 0, -0.4)
    t = v3(0, P['lift'], dz)
    parts[:] = transform_parts(parts, R=R, t=t, pivot=piv)
    for L in lights:
        L.pos = piv + R @ (L.pos - piv) + t


# ------------------------------------------------------------------ death: scattering scrap

from kit.humanoid import finish as _kit_finish


def finish(P, faction, parts, mats, lights=(), add=None, end_style=None):
    """kit finish() plus a louder Compact end state: as P['end'] rises, a wider spray of rust plate,
    bone chips and rope ends is flung out around the body (on top of the kit's scrap scatter)."""
    e = P.get('end', 0.0)
    if e > 0:
        rng = np.random.default_rng(len(parts) + 11)
        n = 16
        for i in range(n):
            ang = rng.uniform(0, 2 * np.pi)
            dist = (0.18 + 0.5 * e) * rng.uniform(0.35, 1.0)
            sz = 0.03 + 0.03 * rng.uniform()
            c = v3(np.cos(ang) * dist, sz * 0.35 + 0.12 * (1 - e) * rng.uniform(), np.sin(ang) * dist * 0.8)
            R = rot_y(rng.uniform(0, 6.28)) @ rot_x(rng.uniform(-0.5, 0.5))
            kind = i % 3
            if kind == 0:
                parts.append(Part(RoundBox(c, (sz * 1.3, sz * 0.25, sz * 0.9), sz * 0.1, R), 'rust', 0.0))
            elif kind == 1:
                parts.append(Part(Capsule(c - R[:, 0] * sz, c + R[:, 0] * sz, sz * 0.35), 'bone', 0.0))
            else:
                parts.append(Part(Torus(c, R[:, 1], sz * 0.6, sz * 0.18), 'rope' if i % 2 else 'tin', 0.0))
    return _kit_finish(P, faction, parts, mats, lights=lights, add=add, end_style=end_style)



__all__ = [n for n in dir() if not n.startswith('__')]

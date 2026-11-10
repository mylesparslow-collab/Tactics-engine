"""The Slough: shared serpent-folk rig (a parametric naga) for every Slough unit.

Body plan (ART.md part A): a wide low COIL of banded krait body on the ground (1.5-2 loops, black-and-bone
rings, gold underside, ending in a flat vertical paddle tail), a RISING S-curve that leaves the coil and becomes
a scaled human torso with 2 or 4 ARMS, and a cobra HOOD behind a snake head with TWO big fangs.
Bands run round the body and tail only (never across torso or arms); the torso is belly colour with a band-black
mantle that continues into the hood.

Units are metres, y up, the figure faces +z (lower-right on screen), its RIGHT hand is -x (camera side).
The coil centre sits a little behind the anchor so the front loop is not cut by the frame bottom.

------------------------------------------------------------------------------------------- API
Spec (static, per unit)
  N = Naga(height=2.1, girth=1.0, arms=2|4, tube=0.15, coil_r=0.50, loops=1.75, hood='cobra', hood_w=1.0,
           dark=BLACK, light=BONE, belly=GOLD, skin=None, accent=('neck',), band_fade=0.0, ...)
      height = top of the reared head (m). 1.9 thin young, 2.1 standard, 2.3-2.4 big, 2.7-2.8 giant (CAMERA ppm 44).
      hood: 'cobra' | 'broad' | 'flat' (wide + short) | 'narrow' (tall) | 'ragged' (torn edge) | 'spade'
      accent: where the chartreuse band(s) go: 'neck' | 'waist' | 'tail' | a float 0..1 along the coil.
  naga_camera(N) -> Camera  (52 ppm up to 2.2 m, 48 to 2.45 m, 44 for giants)

Pose (a dict; numbers / numpy arrays only, so tween.py can in-between it)
  P = naga_pose(N)                           neutral reared pose
  joints: waist, mid (S bend), chest, neck, head, sh_<s>, hd_<s> (hand = grip point) for s in r, l (+ r2, l2)
          item_<s> = direction a one-handed weapon points (or None)
          any key 'u_*' is a point riding the upper body, 'v_*' a direction riding it (rotated by bend/turn)
  scalars: hood (0 shut, 1 normal, 1.35 full flare), jaw (0..1), tongue (0..1), venom (mouth/fang glow 0..1),
           coil_sq (coil y-squash), band_rot (bands sliding along the body: unit vector, angle = phase), tail_sw (paddle sweep -1..1),
           breathe, tell, glow, cast_glow, fx, spit, flakes (hit), fall (death slump 0..1), drop (weapons fall
           0..1), end (husk colour 0..1), flat (squash to a flat skin 0..1)
  posing: bend(P, fwd, side, twist)  rotate the upper body about the waist
          slide(P, d)                 move upper body + waist (the S stretches)
          move_hands(P, d, sides)     shift grips; hold_pole(P, 'r', 'l', grip, direction, spacing)
          aim(P, side, direction)     set item_<side>
          scr(x, y, d) / sdir(x, y, d)  points / directions authored in screen terms (x right, y up, d to camera)

Build (inside build(P))
  parts, add = new_parts()
  B = naga_body(P, add, N)          coil, paddle, rising body, torso, mantle, arms + hands, head, fangs, hood
        -> dict: B['mouth'], B['throat'], B['head'] (Frame), B['hood_c'], B['chest_R'], B['hand'][s], B['s']
  props: pole(add, P, 'r', 'l', kind, below, above)   two-handed: through both hands, tip beyond the 2nd hand
             kinds: lance | glaive | gaff | trident | staff
         blade(add, P, 'r', kind, length)               one-handed along item_r: glaive | sabre | knife | trident
         buckler(add, P, 'l'), scale_shield(add, c, normal, up, w, h), gourd(add, c, r), lacquer_coat(add, P, B, N)
  return naga_finish(P, N, parts, mats={...extra unit materials...}, lights=[])
         (merges the faction materials, adds hit flakes, applies the death husk colour + flatten to a skin;
          pass world=fn(add) for extras such as spit_stream(add, P, B['mouth'], dir) or venom_drip(add, P, at))

Rows
  ROWS, frames = naga_rows(neutral_pose, attack='thrust'|'swing'|'bite'|'spit'|'bash'|'quad', cast='raise'|'spit'|'throw',
                           hook=None)
  hook(row, i, P) may adjust any frame (e.g. a gourd leaving the hand). Rows: idle 4 (sway + hood flare, tongue
  flick), move 4 (bands slide, coil rolls, paddle sweeps, torso level), attack 4 (draw back into coil, lunge,
  hitFrame 2), hit 2, death 4 (slump, hood folds, bands dull, flat empty skin), cast 3.  Tween-friendly.
  token_rows(neutral_pose) for husks and tail segments (idle 2, hit 2, death 3).

Gotchas
  * Keep everything inside the 96x112 frame in EVERY row (styles.py cel outline wraps across frame edges, so a
    weapon touching the right edge leaves a stray pixel on the left). Check attack strike + death frames.
  * The figure's left (+x) projects up-right on screen; author wide arm poses with scr()/sdir().
  * Structures (husks, tail segments) are drawn 150/112 larger by the engine: their ppm is the unit ppm / 1.34.
  * Below ~0.9 m the coil fills the background, so the rising S shows mainly through its gold front.

------------------------------------------------------------------------------------------- example
    from _slough_common import *
    UNIT_ID = 'slough_banded_lancer'
    N = Naga(height=2.1, tube=0.155, loops=1.85, accent=())
    CAMERA = naga_camera(N)

    def neutral_pose():
        P = naga_pose(N)
        hold_pole(P, 'r', 'l', grip=v3(-0.22, 1.18, 0.10), direction=v3(0.62, -0.30, 0.55), spacing=0.42)
        return P

    def build(P):
        parts, add = new_parts()
        B = naga_body(P, add, N)
        pole(add, P, 'r', 'l', 'lance', below=0.45, above=0.60)
        return naga_finish(P, N, parts)

    ROWS, frames = naga_rows(neutral_pose, attack='thrust')
"""
import copy
import dataclasses
import numpy as np
from sdf import (v3, norm, basis_from, rot_y, rot_x, rot_z, Sphere, Ellipsoid, Capsule, RoundBox, Cylinder,
                 Torus, Func, Prim, smax, smin, fbm, vnoise)
from render import Camera, Look, Material, Part, Light, Scene, _hex
from kit.xform import Squash
from kit.fx import emit
import rig

FACTION = 'slough'

# ------------------------------------------------------------------ palette (ART.md)
CHART = _hex('#b5c934')       # venom chartreuse: one band, seals, glaze, trim
BLACK = _hex('#262a2e')       # band black (#16181a lifted a touch so cel shading still reads on it)
INK = _hex('#16181a')
BONE = _hex('#e6dfc8')
GOLD = _hex('#d9a93a')        # yellowbelly gold: bellies, throats, coil undersides
OLIVE = _hex('#5c6a31')
LACQUER = _hex('#a8743a')     # lacquered shed-skin armour
LACQUER_LT = _hex('#d6a35e')
HUSK = _hex('#d8d1ae')
VENOM = _hex('#e4ff5a')       # the 5% light: fang tips, open mouth, gourd mouths, drips
SCALE_GREY = _hex('#7d8a72')  # leviathan scale
RUST = _hex('#8a4b2a')
REED = _hex('#8a8550')
REED_GREEN = _hex('#6f7a3c')
GOURD = _hex('#b89a5e')
SLATE = _hex('#4a4f52')
TONGUE = _hex('#e8607e')
FANG = _hex('#f4eedc')
EYE = _hex('#efc94a')
MOUTH = _hex('#6e2632')
SILT = _hex('#6f6a58')

LOOK = dataclasses.replace(
    Look(), sky=(0.63, 0.66, 0.62), sky_int=0.34, bounce=(0.80, 0.76, 0.58), bounce_int=0.22,
    rim_color=(0.80, 0.90, 0.66), rim_int=0.6, shadow_tint=(0.70, 0.82, 0.86))

E1 = v3(0.788, 0.0, 0.616)     # screen-right along the ground
E2 = v3(-0.616, 0.0, 0.788)    # toward the camera along the ground (down on screen)
GRID = norm(v3(0.12, 0.0, 0.99))  # a board grid axis (screen slope 1:2 down-right)


def scr(x, y, d=0.0):
    """World point authored in screen terms: x metres to screen-right, y metres high, d metres toward the camera
    (which moves it down the screen by d/2). The figure's left (+x) runs screen-right AND up, so author wide
    poses with this instead of raw world x/z."""
    return E1 * x + E2 * d + v3(0, y, 0)


def sdir(x, y, d=0.0):
    """Unit direction in screen terms (see scr)."""
    return norm(E1 * x + E2 * d + v3(0, y, 0))


def _arr(c, n):
    return np.array(c, dtype=np.float64)[None, :].repeat(n, 0)


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def new_parts():
    parts = []

    def add(prim, mat, k=0.0):
        parts.append(Part(prim, mat, k))
    return parts, add


class Frame:
    """Local frame (origin o, rotation R with columns = local x,y,z, scale s)."""

    def __init__(self, o=(0, 0, 0), R=None, s=1.0):
        self.o, self.R, self.s = v3(*o), (np.eye(3) if R is None else R), s

    def p(self, v):
        return self.o + self.s * (self.R @ np.asarray(v, dtype=np.float64))

    def d(self, v):
        return self.R @ np.asarray(v, dtype=np.float64)

    def child(self, o=(0, 0, 0), R=None, s=1.0):
        return Frame(self.p(o), self.R if R is None else self.R @ R, self.s * s)

    def ell(self, add, c, rad, mat, k=0.0, R2=None):
        R = self.R if R2 is None else self.R @ R2
        add(Ellipsoid(self.p(c), tuple(np.asarray(rad) * self.s), R), mat, k)

    def cap(self, add, a, b, ra, rb=None, mat='skin', k=0.0):
        rb = ra if rb is None else rb
        add(Capsule(self.p(a), self.p(b), ra * self.s, rb * self.s), mat, k)

    def sph(self, add, c, r, mat, k=0.0):
        add(Sphere(self.p(c), r * self.s), mat, k)


def R_from(y_dir, z_dir):
    """Rotation whose local y is y_dir and local z is as near z_dir as possible."""
    y = norm(y_dir)
    z = np.asarray(z_dir, dtype=np.float64)
    z = z - y * (z @ y)
    if np.linalg.norm(z) < 1e-6:
        z = v3(1, 0, 0) - y * y[0]
    z = norm(z)
    return np.stack([np.cross(y, z), y, z], axis=1)


def spline(pts, n):
    """Catmull-Rom through pts, n samples."""
    pts = [np.asarray(p, dtype=np.float64) for p in pts]
    Q = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    segs = len(pts) - 1
    for i in range(n):
        u = i / (n - 1) * segs
        k = min(int(u), segs - 1)
        t = u - k
        p0, p1, p2, p3 = Q[k], Q[k + 1], Q[k + 2], Q[k + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return out


# ------------------------------------------------------------------ spec

@dataclasses.dataclass
class Naga:
    height: float = 2.1          # reared head top (m)
    girth: float = 1.0           # torso / arm thickness
    arms: int = 2                # 2 or 4 (the lower pair sits lower on the torso, held wider)
    tube: float = 0.15           # body radius in the coil
    coil_r: float = 0.50         # centreline radius of the outer loop (along screen-right)
    loops: float = 1.75          # 1.5 .. 2.0 readable loops
    coil_depth: float = 0.72     # ellipse ratio toward the camera (keeps the front loop in frame)
    coil_back: float = 0.22      # coil centre pushed back from the anchor
    coil_lift: float = 1.0       # how high the inner loop climbs on the outer one
    tail_side: int = 1           # 1: paddle tail at screen-left, -1: at screen-right
    paddle: float = 1.0          # paddle tail size
    hood: str = 'cobra'          # cobra | broad | flat | narrow | ragged | spade
    hood_w: float = 1.0
    hood_h: float = 1.0
    head_len: float = 1.2
    hood_yaw: float = -0.40      # hood fan turned toward the camera (rad)
    lean: float = 0.0            # forward lean of the reared body (rad)
    dark: tuple = BLACK          # krait band colours
    light: tuple = BONE
    band_len: float = 0.25       # one dark + light period (m)
    band_dark: float = 0.5       # dark fraction of a period
    band_fade: float = 0.0       # 0 crisp .. 1 no bands (old, mud-coloured)
    accent: tuple = ('neck',)    # chartreuse band places
    accent_col: tuple = CHART
    belly: tuple = GOLD          # torso front, throat, coil underside
    skin: tuple = None           # arms / torso sides (None = belly toned down)
    mantle: tuple = BLACK        # shoulders, hood back, head top
    hood_face: tuple = None      # hood front (None = mantle)
    hood_rim: tuple = BONE       # pale edge of the hood front
    lip: tuple = BONE            # lips / chin
    eye: tuple = EYE
    fang: float = 1.0
    gloss: float = 1.0           # scale wetness (Teshk is glossier than anyone)
    grey: float = 0.0            # greying (old): mixes grey into the dark bands and mantle
    arm_len: float = 1.0
    body_r: float = None         # rising-body radius at the waist (None = from girth)


def _phase(P):
    """Band slide / coil roll phase 0..1, stored as a unit vector so tween.py interpolates it round the loop."""
    b = P['band_rot']
    return float(np.mod(np.arctan2(b[1], b[0]) / (2 * np.pi), 1.0))


def naga_scale(N):
    return N.height / 2.1


def naga_camera(N):
    if N.height >= 2.55:
        return Camera(ppm=44.0)
    if N.height > 2.25:
        return Camera(ppm=48.0)
    return Camera()


def _skin(N):
    return N.skin if N.skin is not None else tuple(np.array(N.belly) * 0.62 + np.array(N.mantle) * 0.28)


# ------------------------------------------------------------------ pose

UPPER = ('chest', 'neck', 'head', 'sh_r', 'sh_l', 'sh_r2', 'sh_l2', 'hd_r', 'hd_l', 'hd_r2', 'hd_l2')
SIDES = ('r', 'l', 'r2', 'l2')


def naga_pose(N, **kw):
    """Neutral reared pose for spec N. Hands rest low in front; units place them with hold_pole / reach."""
    s = naga_scale(N)
    g = N.girth
    h = lambda y: y * s
    P = dict(
        s=s,
        coil_c=v3(0, 0, 0) - E2 * N.coil_back * max(1.0, N.coil_r / 0.5),
        coil_sq=1.0, coil_w=1.0, band_rot=v3(1.0, 0.0, 0.0), tail_sw=0.0,
        mid=v3(-0.10, 0.62 * max(s, 0.95), 0.36),
        waist=v3(0.0, h(1.02), 0.08),
        chest=v3(0.0, h(1.38), 0.03),
        neck=v3(0.0, h(1.68), 0.05),
        head=v3(0.0, h(1.93), 0.12),
        head_yaw=np.radians(22), head_pitch=np.radians(4), head_roll=0.0,
        hood=1.0, jaw=0.0, tongue=0.0, venom=0.0,
        sh_r=v3(-0.20 * g * s, h(1.54), 0.0), sh_l=v3(0.20 * g * s, h(1.54), 0.0),
        hd_r=v3(-0.28 * s, h(1.08), 0.20), hd_l=v3(0.28 * s, h(1.08), 0.20),
        item_r=None, item_l=None,
        breathe=0.0, tell=0.0, glow=1.0, cast_glow=0.0, fx=0.0, spit=0.0, flakes=0.0,
        fall=0.0, drop=0.0, end=0.0, flat=0.0, sink=0.0, throw=0.0,
    )
    if N.arms == 4:
        P.update(sh_r2=v3(-0.19 * g * s, h(1.30), 0.02), sh_l2=v3(0.19 * g * s, h(1.30), 0.02),
                 hd_r2=v3(-0.45 * s, h(1.0), 0.15), hd_l2=v3(0.45 * s, h(1.0), 0.15), item_r2=None, item_l2=None)
    if N.lean:
        bend(P, N.lean)
    P.update(kw)
    return P


def upper_keys(P):
    return [k for k in UPPER if k in P] + [k for k in P if k.startswith('u_')]


def dir_keys(P):
    return [k for k in P if (k.startswith('item_') or k.startswith('v_')) and P[k] is not None]


def turn(P, R, pivot=None):
    """Rotate the upper body (and held directions) by R about pivot (default: the waist)."""
    pv = P['waist'] if pivot is None else pivot
    for k in upper_keys(P):
        P[k] = pv + R @ (P[k] - pv)
    for k in dir_keys(P):
        P[k] = R @ np.asarray(P[k], dtype=np.float64)
    return P


def bend(P, fwd=0.0, side=0.0, twist=0.0):
    """Tilt the upper body about the waist: fwd > 0 toward +z, side > 0 toward +x (its left), twist about y.
    The S control point follows a third of the way the other way, so the body curls instead of hinging."""
    R = rot_y(twist) @ rot_z(-side) @ rot_x(fwd)
    turn(P, R)
    P['mid'] = P['mid'] + v3(-side * 0.10, 0, -fwd * 0.10)
    return P


def slide(P, d, waist=True, mid=0.5):
    """Move the upper body by d (and the waist, and the S point by `mid` of it): lunges, recoils, drops."""
    d = np.asarray(d, dtype=np.float64)
    for k in upper_keys(P):
        P[k] = P[k] + d
    if waist:
        P['waist'] = P['waist'] + d
    P['mid'] = P['mid'] + d * mid
    return P


def move_hands(P, d, sides=None):
    for s in (sides or SIDES):
        if 'hd_' + s in P:
            P['hd_' + s] = P['hd_' + s] + np.asarray(d, dtype=np.float64)
    return P


def reach(P, side, target):
    P['hd_' + side] = v3(*target)
    return P


def aim(P, side, direction):
    P['item_' + side] = norm(direction)
    return P


def hold_pole(P, a, b, grip, direction, spacing=0.45):
    """Both hands on one shaft: hand a at grip, hand b `spacing` further along `direction` (toward the tip)."""
    d = norm(direction)
    P['hd_' + a] = v3(*grip)
    P['hd_' + b] = v3(*grip) + d * spacing
    return P


def arm_lengths(P, N):
    s = P['s'] * N.arm_len
    return 0.31 * s, 0.30 * s


# ------------------------------------------------------------------ body path (coil + rising S)

def body_path(P, N):
    """Centreline from the paddle tail through the coil and up the rising S to the waist.
    Returns (pts (M,3), radii (M,), belly dirs (M,3), n_coil)."""
    s = P['s']
    r = N.tube
    c = P['coil_c']
    L = N.loops
    sq = P['coil_sq']
    w = P['coil_w']
    R0 = N.coil_r * w
    R1 = max(R0 - 1.05 * r, 1.3 * r)
    th_e = np.pi / 2                          # exit toward the camera
    sgn = N.tail_side
    th0 = th_e - sgn * 2 * np.pi * L
    nc = int(28 * L) + 4
    pts, rad, bel = [], [], []
    roll = _phase(P)
    for i in range(nc):
        u = i / (nc - 1)
        th = th0 + sgn * 2 * np.pi * L * u
        R = lerp(R0, R1, smooth(0.25, 0.95, u))
        wob = 1.0 + 0.04 * np.sin(th * 2 + roll * 2 * np.pi)
        y = r * (0.93 + 1.25 * N.coil_lift * smooth(0.40, 0.85, u)) * sq
        p = c + E1 * np.cos(th) * R * wob + E2 * np.sin(th) * R * N.coil_depth * wob + v3(0, y, 0)
        pts.append(p)
        rad.append(r * (0.42 + 0.58 * smooth(0.0, 0.30, u)) * (1 + (1 - sq) * 0.5))
        bel.append(v3(0, -1, 0))
    # exit tangent
    tg = norm(pts[-1] - pts[-2])
    E = pts[-1]
    wr = N.body_r if N.body_r else 0.13 * N.girth * s
    ctrl = [pts[-2], E, E + tg * 0.10 + v3(0, 0.10, 0), P['mid'], P['waist']]
    up = spline(ctrl, 17)[5:]
    rr = np.interp(np.linspace(0, 1, len(up)), [0, 0.45, 1.0], [r, (r + wr) * 0.5 * 1.04, wr])
    for i, q in enumerate(up):
        # keep the S off the frame bottom: limit how far toward the camera a low point may sit
        dep = q @ E2 - P['coil_c'] @ E2 * 0.0
        lim = (0.866 * q[1] + 0.10 - rr[i]) / 0.5
        if dep > lim:
            q = q - E2 * (dep - lim)
        pts.append(q)
        rad.append(rr[i])
        t = i / (len(up) - 1)
        fw = norm(v3(-0.15, 0, 1)) * smooth(0.0, 0.35, t) + v3(0, -1, 0) * (1 - smooth(0.0, 0.35, t))
        bel.append(norm(fw))
    return np.array(pts), np.array(rad), np.array(bel), nc


def _nearest(pts, p, chunk=40000):
    """Nearest point on polyline pts for each p: (segment index, t, closest point)."""
    A = pts[:-1]
    D = pts[1:] - A
    L2 = (D * D).sum(1) + 1e-12
    n = len(p)
    seg = np.zeros(n, dtype=np.int64)
    tt = np.zeros(n)
    for a in range(0, n, chunk):
        q = p[a:a + chunk]
        rel = q[:, None, :] - A[None, :, :]
        t = np.clip((rel * D[None]).sum(2) / L2[None], 0, 1)
        d2 = ((rel - t[..., None] * D[None]) ** 2).sum(2)
        j = np.argmin(d2, 1)
        seg[a:a + chunk] = j
        tt[a:a + chunk] = t[np.arange(len(q)), j]
    cl = A[seg] + D[seg] * tt[:, None]
    return seg, tt, cl


def band_albedo(N, path, svals, bel, P, accents, husk=False):
    """Krait rings by arc length, gold belly where the surface faces the belly direction."""
    dark = np.array(N.dark) * (1 - N.grey) + np.array(_hex('#7a7c7a')) * N.grey
    light = np.array(N.light)
    fade = N.band_fade
    period = N.band_len
    ph = _phase(P) * period
    belly = np.array(N.belly)

    def fn(p, n):
        seg, t, cl = _nearest(path, p)
        sv = svals[seg] + (svals[seg + 1] - svals[seg]) * t
        u = np.mod((sv - ph) / period, 1.0)
        dk = u < N.band_dark
        col = np.where(dk[:, None], dark[None, :], light[None, :])
        mixc = dark * (1 - 0.5) + light * 0.5
        col = col * (1 - fade) + mixc[None, :] * fade
        for a in accents:
            m = np.abs(sv - a) < period * 0.32
            col[m] = accent_band
        b = bel[seg]
        off = p - cl
        off = off / (np.linalg.norm(off, axis=1, keepdims=True) + 1e-9)
        bm = (off * b).sum(1)
        th = bth[seg]
        bw = smooth(th, th + 0.12, bm)[:, None]
        col = col * (1 - bw) + belly[None, :] * bw
        return col
    accent_band = np.array(N.accent_col)
    # narrow gold underside on the coil, a broad gold front on the rising S so it reads as the torso's stem
    nb = len(bel)
    bth = np.where(np.abs(bel[:, 1]) > 0.5, 0.80, 0.30)
    return fn


def accent_positions(N, svals, nc):
    total_coil = svals[nc - 1]
    total = svals[-1]
    out = []
    for a in N.accent:
        if a == 'neck':
            out.append(total - 0.06)
        elif a == 'waist':
            out.append(total - 0.42)
        elif a == 'tail':
            out.append(0.32)
        else:
            out.append(float(a) * total_coil)
    return out


# ------------------------------------------------------------------ hood

def hood_sdf(P, N, F):
    """Cobra hood: a thin curved fan in frame F (x across, y up, z = facing). Width flares with P['hood']."""
    s = P['s']
    fl = P['hood']
    shape = N.hood
    W = 0.27 * s * N.hood_w * (0.35 + 0.65 * fl)
    H = 0.22 * s * N.hood_h
    yc = 0.0
    if shape == 'broad':
        W *= 1.15
    elif shape == 'flat':
        W *= 1.30
        H *= 0.78
    elif shape == 'narrow':
        W *= 0.78
        H *= 1.18
    elif shape == 'spade':
        W *= 1.05
    th = 0.018 * s
    bendk = 1.1 / max(W, 0.05) * (0.5 + 0.5 * fl)

    def f(p):
        q = (p - F.o) @ F.R
        x, y, z = q[:, 0], q[:, 1], q[:, 2]
        yy = (y - yc) / H                    # -1 bottom .. 1 top
        # half-width profile: pinched at the neck, widest above the middle, round top
        prof = np.sqrt(np.clip(1 - np.clip(yy - 0.15, 0, None) ** 2 / 0.85 ** 2, 0, 1))
        pinch = 0.32 + 0.68 * smooth(-1.05, 0.1, yy)
        if shape == 'spade':
            prof = prof * (1 - 0.25 * smooth(0.4, 1.0, yy))
        wy = W * prof * pinch
        if shape == 'ragged':
            ang = np.arctan2(y, x)
            wy = wy * (1 - 0.13 * (np.sin(ang * 9 + 1.3) > 0.3) - 0.06 * np.sin(ang * 23))
        dx = np.abs(x) - wy
        dy = np.maximum(-1.0 - yy, yy - 1.0) * H
        d2 = np.maximum(dx, dy)
        zc = -bendk * x * x * 0.5 - 0.02 * s * yy
        dz = np.abs(z - zc) - th * (1.0 - 0.4 * np.clip(np.abs(x) / (W + 1e-6), 0, 1))
        return np.maximum(d2 * 0.9, dz)
    return Func(f, F.o, max(W, H) * 1.15 + 0.05)


# ------------------------------------------------------------------ the body

def _arm(add, sh, hd, l1, l2, pole, r_up, r_lo, mat, hand_mat, hand_r):
    el = rig.two_bone(sh, hd, l1, l2, pole)
    d = hd - el
    ln = np.linalg.norm(d)
    # if the hand is out of reach the forearm stretches (never detaches)
    wr = hd - norm(d) * min(hand_r * 0.9, ln * 0.4)
    add(Capsule(sh, el, r_up, r_lo * 1.05), mat, 0.03)
    add(Capsule(el, wr, r_lo, r_lo * 0.82), mat, 0.02)
    Rh = basis_from(norm(d), (0, 1, 0))
    add(Ellipsoid(hd, (hand_r * 0.95, hand_r * 1.15, hand_r * 0.85), Rh), hand_mat, 0.015)
    return el


def head_frame(P, N):
    s = P['s']
    R = rot_y(P['head_yaw']) @ rot_x(P['head_pitch']) @ rot_z(P['head_roll'])
    return Frame(P['head'], R, s * N.head_len)


def naga_body(P, add, N, arms=True, head=True):
    """Sculpt the whole serpent body for pose P. Returns B (anchors for props, fx and materials)."""
    s = P['s']
    g = N.girth
    B = {}
    # --- coil + rising body
    pts, rad, bel, nc = body_path(P, N)
    seglen = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    svals = np.concatenate([[0], np.cumsum(seglen)])
    for i in range(len(pts) - 1):
        add(Capsule(pts[i], pts[i + 1], rad[i], rad[i + 1]), 'band', 0.035 if i < nc else 0.05)
    B.update(path=pts, svals=svals, bel=bel, nc=nc, rad=rad)
    B['accents'] = accent_positions(N, svals, nc)
    # --- paddle tail: a tall flat oar at the tail tip, sweeping
    t0 = pts[0]
    tg = norm(pts[0] - pts[2])
    sw = P['tail_sw']
    tg = norm(rot_y(sw * 0.6) @ tg)
    side = norm(np.cross(tg, v3(0, 1, 0)))
    pc = t0 + tg * 0.13 * N.paddle * s + v3(0, 0.10 * N.paddle * s, 0)
    Rp = np.stack([side, v3(0, 1, 0), tg], axis=1)
    add(Ellipsoid(pc, (0.024 * s, 0.15 * N.paddle * s, 0.21 * N.paddle * s), Rp), 'paddle', 0.03)
    B['tail'] = pc
    # --- torso
    W, C, Nk = P['waist'], P['chest'], P['neck']
    up = norm(Nk - W)
    fwd = norm(v3(0, 0, 1) - up * up[2])
    Rt = R_from(up, fwd)
    B['chest_R'] = Rt
    ab = (W + C) * 0.5
    add(Ellipsoid(ab, (0.15 * g * s, 0.24 * s, 0.12 * g * s), R_from(norm(C - W), fwd)), 'torso', 0.07)
    add(Ellipsoid(C, (0.205 * g * s, 0.20 * s, 0.135 * g * s), Rt), 'torso', 0.06)
    # shoulder mantle (band black, continues into the hood)
    add(Ellipsoid(C + up * 0.13 * s - fwd * 0.03 * s, (0.215 * g * s, 0.10 * s, 0.135 * g * s), Rt), 'mantle', 0.05)
    # neck
    add(Capsule(C + up * 0.15 * s, P['head'] - up * 0.05 * s, 0.085 * s * g ** 0.5, 0.068 * s), 'neck', 0.05)
    B['throat'] = lerp(Nk, P['head'], 0.35) + fwd * 0.07 * s
    # --- arms
    l1, l2 = arm_lengths(P, N)
    B['hand'] = {}
    if arms:
        for sd in SIDES:
            if 'sh_' + sd not in P:
                continue
            sx = -1 if sd[0] == 'r' else 1
            lower = sd.endswith('2')
            sh = P['sh_' + sd]
            add(Sphere(sh, 0.085 * g * s * (0.85 if lower else 1.0)), 'mantle' if not lower else 'torso', 0.05)
            pole_v = v3(sx * 1.0, -0.6, -0.7) if not lower else v3(sx * 1.0, -0.2, -0.4)
            ru = 0.068 * g * s * (0.9 if lower else 1.0)
            _arm(add, sh, P['hd_' + sd], l1, l2, pole_v, ru, ru * 0.82, 'limb', 'hand', 0.05 * s * g ** 0.5)
            B['hand'][sd] = P['hd_' + sd]
    # --- head
    if head:
        F = head_frame(P, N)
        B['head'] = F
        _snake_head(P, add, N, F)
        B['mouth'] = F.p((0, -0.035, 0.17))
        B['fang_tips'] = [F.p((sx * 0.032, -0.10 * N.fang - 0.02 * P['jaw'], 0.14)) for sx in (-1, 1)]
        # hood: centred behind the head, facing forward (follows the head yaw half way)
        yaw = N.hood_yaw + P['head_yaw'] * 0.3      # turned toward the camera so the fan reads open
        Rh = R_from(up, rot_y(yaw) @ fwd)
        hc = P['head'] - Rh[:, 2] * 0.10 * s - up * 0.07 * s
        HF = Frame(hc, Rh, 1.0)
        B['hood_c'] = hc
        B['hood_F'] = HF
        add(hood_sdf(P, N, HF), 'hood', 0.03)
    B['N'] = N
    return B


def _snake_head(P, add, N, F):
    """Wedge-shaped krait head: flat skull, blunt snout, hinged lower jaw, two big fangs, gold eyes."""
    j = P['jaw']
    F.ell(add, (0, 0.010, -0.01), (0.076, 0.056, 0.115), 'head', 0.0)
    F.ell(add, (0, -0.002, 0.10), (0.052, 0.040, 0.115), 'head', 0.035)
    # brow scales (give the head a hard, mean read)
    for sx in (-1, 1):
        F.ell(add, (sx * 0.048, 0.043, 0.045), (0.032, 0.017, 0.05), 'head', 0.02)
    # lower jaw hinged at the back of the head
    J = F.child((0, -0.03, -0.06), rot_x(0.55 * j))
    J.ell(add, (0, -0.012, 0.115), (0.066, 0.026, 0.115), 'jaw', 0.02)
    if j > 0.05:
        # open mouth: dark pink inside, lit with venom when P['venom']
        M = F.child((0, -0.035, -0.06), rot_x(0.27 * j))
        M.ell(add, (0, 0.0, 0.11), (0.055, 0.02 + 0.02 * j, 0.10), 'mouth', 0.0)
    # eyes
    for sx in (-1, 1):
        F.sph(add, (sx * 0.058, 0.022, 0.060), 0.024, 'eye')
        F.sph(add, (sx * 0.068, 0.022, 0.070), 0.011, 'pupil')
    # two big fangs at the front of the upper jaw, slightly uneven, curving back
    fl = 0.090 * N.fang
    for sx, k in ((-1, 1.0), (1, 0.86)):
        a = (sx * 0.032, -0.030, 0.150)
        m = (sx * 0.031, -0.030 - fl * k * 0.6, 0.152)
        b = (sx * 0.028, -0.030 - fl * k, 0.135)
        F.cap(add, a, m, 0.016, 0.011, 'fang')
        F.cap(add, m, b, 0.011, 0.003, 'fang')
    # forked tongue
    t = P['tongue']
    if t > 0.05:
        a = (0, -0.035, 0.16)
        b = (0, -0.05 - 0.03 * t, 0.16 + 0.12 * t)
        F.cap(add, a, b, 0.009, 0.007, 'tongue')
        for sx in (-1, 1):
            F.cap(add, b, (sx * 0.025 * t, -0.07 - 0.04 * t, 0.17 + 0.17 * t), 0.006, 0.003, 'tongue')


# ------------------------------------------------------------------ props

def pole(add, P, a, b, kind='lance', below=0.7, above=0.9, shaft='haft', head='fang', glaze='glaze'):
    """Two-handed weapon running through hand a then hand b; the business end is beyond hand b.
    kinds: lance (one great curved fang lashed on) | glaive (long curved fang blade) | gaff (hook)
           | trident (rusted, outer tines barbed back) | staff. Returns (butt, tip)."""
    ha, hb = P['hd_' + a], P['hd_' + b]
    d = norm(hb - ha)
    butt, tip = ha - d * below, hb + d * above
    butt, tip = _drop(P, butt, tip)
    d = norm(tip - butt)
    _shaft(add, butt, tip, kind, d, P, shaft, head, glaze)
    return butt, tip


def blade(add, P, side, kind='sabre', length=0.7, below=0.12, shaft='haft', head='fang', glaze='glaze'):
    """One-handed weapon along P['item_<side>'] from hand <side>. kinds: sabre | glaive | knife | trident | lance."""
    d = P['item_' + side]
    if d is None:
        return None
    d = norm(d)
    g = P['hd_' + side]
    butt, tip = g - d * below, g + d * length
    butt, tip = _drop(P, butt, tip)
    d = norm(tip - butt)
    _shaft(add, butt, tip, kind, d, P, shaft, head, glaze)
    return butt, tip


def _drop(P, butt, tip):
    """Death: the weapon falls out of the hands and lies flat on the ground."""
    k = P['drop']
    if k <= 0:
        return butt, tip
    mid = (butt + tip) / 2
    L = np.linalg.norm(tip - butt)
    hd = tip - butt
    hd[1] = 0
    hd = norm(hd) if np.linalg.norm(hd) > 1e-3 else v3(1, 0, 0)
    gm = v3(mid[0] * 0.4, 0.03, -0.12)        # lies across the coil, back from the frame bottom
    Lg = min(L, 1.2)
    hd = norm(hd * 0.3 + E1)
    b2, t2 = gm - hd * Lg / 2, gm + hd * Lg / 2
    return lerp(butt, b2, k), lerp(tip, t2, k)


def _side(d):
    c = np.cross(d, v3(0, 1, 0.2))
    if np.linalg.norm(c) < 0.2:
        c = np.cross(d, v3(1, 0, 0))
    return norm(c)


def _shaft(add, butt, tip, kind, d, P, shaft, head, glaze):
    L = np.linalg.norm(tip - butt)
    sv = _side(d)
    # blades curve in the plane most visible to the camera
    cam = v3(-0.53, 0.5, 0.68)
    bn = cam - d * (cam @ d)
    bn = norm(np.cross(d, norm(bn)))       # in-screen perpendicular to the shaft
    s = P['s']
    if kind in ('lance', 'glaive', 'staff', 'gaff', 'trident'):
        hl = dict(lance=0.40, glaive=0.34, staff=0.0, gaff=0.0, trident=0.14)[kind] * s
        add(Capsule(butt, tip - d * hl * 0.85, 0.023 * s), shaft, 0.0)
    if kind in ('lance', 'glaive'):
        base = tip - d * dict(lance=0.40, glaive=0.34)[kind] * s
        # reed lashing (chartreuse cord)
        add(Capsule(base - d * 0.06 * s, base + d * 0.03 * s, 0.028 * s), glaze if kind == 'lance' else 'lash', 0.0)
        # one great curved fang: a tapered crescent
        n = 6
        w0 = 0.050 if kind == 'glaive' else 0.046
        bow = 0.10 if kind == 'glaive' else 0.06
        prev = None
        for i in range(n + 1):
            t = i / n
            q = base + d * (((tip - base) @ d) * t) + bn * bow * s * np.sin(np.pi * t * 0.9) * (1 if kind == 'glaive' else 0.7)
            if prev is not None:
                ra = w0 * s * (1 - (i - 1) / n) ** 0.8 + 0.004
                rb = w0 * s * (1 - i / n) ** 0.8 + 0.003
                add(Capsule(prev, q, ra, rb), head if t < (0.7 if kind == 'lance' else 0.45) else glaze, 0.012)
            prev = q
    elif kind == 'gaff':
        add(Capsule(tip - d * 0.03 * s, tip + d * 0.05 * s, 0.026 * s), 'lash', 0.0)
        c = tip + d * 0.03 * s + bn * 0.075 * s
        ax = norm(np.cross(d, bn))
        add(Torus(c, ax, 0.075 * s, 0.014 * s), 'hook', 0.0)
        # cut the hook ring open on the far side with a small barb
        add(Capsule(c + bn * 0.075 * s, c + bn * 0.075 * s - d * 0.06 * s, 0.013 * s, 0.004), 'hook', 0.0)
    elif kind == 'trident':
        base = tip - d * 0.16 * s
        add(Capsule(base - bn * 0.13 * s, base + bn * 0.13 * s, 0.017 * s), 'rust', 0.01)
        for k in (-1, 0, 1):
            a = base + bn * 0.12 * k * s
            t = a + d * (0.26 if k == 0 else 0.20) * s
            add(Capsule(a, t, 0.015 * s, 0.004), 'rust', 0.0)
            if k:
                add(Capsule(t, t - d * 0.07 * s - bn * 0.04 * k * s, 0.010 * s, 0.003), 'rust', 0.0)
    elif kind == 'staff':
        add(Sphere(tip, 0.03 * s), 'lash', 0.0)
    elif kind in ('sabre', 'knife'):
        r = (0.030 if kind == 'sabre' else 0.022) * s
        add(Capsule(butt, butt + d * 0.14 * s, 0.017 * s), shaft, 0.0)
        add(Capsule(butt + d * 0.12 * s - bn * 0.05 * s, butt + d * 0.12 * s + bn * 0.05 * s, 0.012 * s), 'lash', 0.0)
        base = butt + d * 0.14 * s
        n = 6
        prev = base
        for i in range(1, n + 1):
            t = i / n
            q = base + (tip - base) * t - bn * 0.09 * s * t * t
            add(Capsule(prev, q, r * (1 - (i - 1) / n * 0.8), r * (1 - i / n * 0.8) + 0.002), head if t < 0.75 else glaze, 0.01)
            prev = q
    return butt, tip


def buckler(add, P, side='l', mat='buckler', rim='reed', size=1.0):
    """Small round skin buckler on a reed hoop, strapped to the forearm of <side>."""
    s = P['s']
    sh, hd = P['sh_' + side], P['hd_' + side]
    sx = -1 if side[0] == 'r' else 1
    c = lerp(sh, hd, 0.68) + v3(sx * 0.07, 0, 0.06) * s
    out = norm(v3(sx * 0.35, 0.1, 1.0) + E2 * 0.6)
    r = 0.19 * size * s
    add(Cylinder(c - out * 0.008, c + out * 0.008, r, 0.006), mat, 0.0)
    add(Torus(c, out, r, 0.016 * s), rim, 0.0)
    add(Capsule(c - E1 * r * 0.9, c + E1 * r * 0.9, 0.006 * s), rim, 0.0)
    return c


def scale_shield(add, c, normal, up, w=0.42, h=0.62, mat='scale', rim='lacquer', ridges=3, curve=0.08):
    """One huge leviathan scale: a curved rounded plate with ridges and a lacquer rim (w, h = half sizes)."""
    nz = norm(normal)
    R = R_from(up, nz)
    th = 0.03

    def f(p):
        q = (p - c) @ R
        x, y, z = q[:, 0], q[:, 1], q[:, 2]
        # scale outline: rounded top, tapering slightly to a blunt point at the bottom
        yy = y / h
        wy = w * np.sqrt(np.clip(1 - np.clip(yy, 0, None) ** 2, 0, 1)) * (1 - 0.35 * np.clip(-yy, 0, 1) ** 1.5)
        d2 = np.maximum(np.abs(x) - wy, np.abs(y) - h)
        zc = -curve * (x / w) ** 2 - 0.03 * (yy) ** 2
        rid = 0.0
        for k in range(ridges):
            xk = (k - (ridges - 1) / 2) * w * 0.5
            rid = rid + 0.018 * np.exp(-((x - xk) / 0.03) ** 2) * (1 - 0.6 * np.abs(yy))
        dz = np.abs(z - zc - rid * 0.5) - th - rid * 0.5
        return np.maximum(d2 * 0.9, dz)
    add(Func(f, c, max(w, h) + 0.08), mat, 0.0)

    def frim(p):
        q = (p - c) @ R
        x, y, z = q[:, 0], q[:, 1], q[:, 2]
        yy = y / h
        wy = w * np.sqrt(np.clip(1 - np.clip(yy, 0, None) ** 2, 0, 1)) * (1 - 0.35 * np.clip(-yy, 0, 1) ** 1.5)
        d2 = np.maximum(np.abs(x) - wy, np.abs(y) - h)
        zc = -curve * (x / w) ** 2 - 0.03 * yy ** 2
        return np.maximum(np.abs(d2 + 0.012) - 0.014, np.abs(z - zc + 0.004) - th * 1.25)
    add(Func(frim, c, max(w, h) + 0.08), rim, 0.0)
    return R


def gourd(add, c, r=0.11, mat='gourd', seal='glaze', neck=v3(0, 1, 0)):
    """Dried marsh gourd: a fat bulb, a smaller top lobe and a chartreuse wax stopper."""
    c = v3(*c)
    nk = norm(neck)
    add(Sphere(c, r), mat, 0.0)
    add(Sphere(c + nk * r * 1.05, r * 0.6), mat, 0.04)
    add(Cylinder(c + nk * r * 1.5, c + nk * r * 1.85, r * 0.26, 0.01), seal, 0.0)
    return c + nk * r * 1.85


def lacquer_coat(add, P, B, N, rows=4, per_row=7, coil=True, mat='lacquer', edge='lacquer_lt'):
    """Shingled armour of lacquered shed skins: rows of overlapping amber plates (roof tiles) over the torso
    front and sides, each plate showing a lighter edge below it; with coil=True a run of plates on the top loop."""
    s = P['s']
    g = N.girth
    W, C = P['waist'], P['chest']
    Rt = B['chest_R']
    up, fw = Rt[:, 1], Rt[:, 2]
    rt = Rt[:, 0]
    top = C + up * 0.17 * s
    bot = W - up * 0.02 * s
    for i in range(rows):
        t = i / max(rows - 1, 1)
        c = lerp(top, bot, t)
        rx = 0.215 * g * s * (1.0 - 0.18 * t)
        rz = 0.142 * g * s * (1.0 - 0.10 * t)
        off = 0.5 * (i % 2)
        for j in range(per_row):
            a = np.radians(-112 + 224 * (j + off) / per_row)
            if abs(a) > np.radians(118):
                continue
            nrm = norm(rt * np.sin(a) / rx + fw * np.cos(a) / rz)
            q = c + rt * np.sin(a) * rx + fw * np.cos(a) * rz
            # plate tilted out at the bottom: local y runs down-and-out along the surface
            dn = norm(-up + nrm * 0.35)
            R = R_from(dn, nrm)
            pc = q + nrm * 0.012 * s + dn * 0.04 * s
            add(Ellipsoid(pc + dn * 0.020 * s - nrm * 0.006 * s, (0.095 * s * g, 0.088 * s, 0.014 * s), R), edge, 0.0)
            add(Ellipsoid(pc, (0.090 * s * g, 0.080 * s, 0.017 * s), R), mat, 0.0)
    if coil:
        pts, rad, nc = B['path'], B['rad'], B['nc']
        for i in range(int(nc * 0.50), nc - 1, 2):
            a, b = pts[i], pts[min(i + 2, len(pts) - 1)]
            tg = norm(b - a)
            for side in (-1, 1):
                sd = norm(np.cross(tg, v3(0, 1, 0))) * side
                nrm = norm(v3(0, 1, 0) + sd * 0.8)
                q = a + nrm * rad[i] * 0.95
                R = R_from(norm(-tg * 0.3 + sd - v3(0, 0.6, 0)), nrm)
                add(Ellipsoid(q + nrm * 0.004, (rad[i] * 0.55, rad[i] * 0.55, 0.016 * s), R), edge, 0.0)
                add(Ellipsoid(q + nrm * 0.012 - R[:, 1] * 0.02, (rad[i] * 0.5, rad[i] * 0.48, 0.016 * s), R), mat, 0.0)


# ------------------------------------------------------------------ materials

def naga_mats(P, N, B):
    s = P['s']
    gl = N.gloss
    mats = {}
    mats['band'] = Material(band_albedo(N, B['path'], B['svals'], B['bel'], P, B['accents']),
                            spec=0.45 * gl, gloss=46, brush=0.03)
    mats['paddle'] = mats['band']
    skin = np.array(_skin(N))
    belly = np.array(N.belly)
    mantle = np.array(N.mantle) * (1 - N.grey) + np.array(_hex('#8a8c88')) * N.grey
    W, C = P['waist'], P['chest']
    Rt = B['chest_R']

    def torso_alb(p, n):
        q = (p - C) @ Rt / s
        col = _arr(skin, len(p))
        front = (q[:, 2] > 0.02) & (np.abs(q[:, 0]) < 0.115 + 0.03 * np.clip(-q[:, 1] / 0.3, 0, 1))
        plate = np.mod(q[:, 1] / 0.075, 1.0) < 0.16
        col[front] = belly
        col[front & plate] = belly * 0.78
        back = q[:, 2] < -0.06
        col[back] = mantle * 0.9 + skin * 0.1
        return col
    mats['torso'] = Material(torso_alb, spec=0.30 * gl, gloss=30, brush=0.04)
    mats['mantle'] = Material(tuple(mantle), spec=0.4 * gl, gloss=40, brush=0.03)
    Rn = Rt

    def neck_alb(p, n):
        q = (p - C) @ Rn
        col = _arr(mantle, len(p))
        fr = q[:, 2] > 0.01
        col[fr] = belly
        return col
    mats['neck'] = Material(neck_alb, spec=0.35 * gl, gloss=36, brush=0.03)
    mats['limb'] = Material(tuple(skin), spec=0.25 * gl, gloss=26, brush=0.04)
    mats['hand'] = Material(tuple(skin * 0.82), spec=0.2, gloss=20, brush=0.03)
    if 'head' in B:
        F = B['head']
        lip = np.array(N.lip)

        def head_alb(p, n):
            q = (p - F.o) @ F.R / F.s
            col = _arr(mantle, len(p))
            low = q[:, 1] < -0.012 + 0.12 * np.clip(q[:, 2] - 0.13, 0, 1)
            col[low] = lip
            return col
        mats['head'] = Material(head_alb, spec=0.45 * gl, gloss=44, brush=0.03)
        mats['jaw'] = Material(tuple(lip), spec=0.3, gloss=30, brush=0.02)
        HF = B['hood_F']
        hface = np.array(N.hood_face if N.hood_face is not None else mantle * 0.45 + belly * 0.35 + np.array(N.light) * 0.2)
        rimc = np.array(N.hood_rim)

        def hood_alb(p, n):
            q = (p - HF.o) @ HF.R / s
            col = _arr(mantle, len(p))
            front = (n @ HF.R[:, 2]) > 0.0
            col[front] = hface
            # pale rim round the front edge, and the gold throat stripe up the middle
            r2 = np.sqrt((q[:, 0] / 0.2) ** 2 + ((q[:, 1] - 0.03) / 0.25) ** 2)
            rim_m = front & (r2 > 0.86 - 0.12 * (1 - P['hood']))
            col[rim_m] = rimc
            mid = front & (np.abs(q[:, 0]) < 0.035) & (q[:, 1] < 0.02)
            col[mid] = belly
            return col
        mats['hood'] = Material(hood_alb, spec=0.35 * gl, gloss=36, brush=0.03)
    v = max(P['venom'], 0.0)
    mats['fang'] = Material(FANG, spec=0.6, gloss=60, emissive=tuple(np.array(VENOM) * 0.9 * v) if v > 0.05 else None)
    mats['mouth'] = Material(MOUTH, spec=0.4, gloss=30, emissive=tuple(np.array(VENOM) * 0.55 * v) if v > 0.05 else None,
                             rim=0.2)
    mats['tongue'] = Material(TONGUE, spec=0.5, gloss=40, emissive=tuple(np.array(TONGUE) * 0.25))
    mats['eye'] = Material(N.eye, spec=0.9, gloss=80, emissive=tuple(np.array(N.eye) * 0.25))
    mats['pupil'] = Material(INK, spec=0.9, gloss=90, rim=0.0)
    # props
    mats['haft'] = Material(_hex('#6b5638'), spec=0.2, gloss=20, brush=0.05)
    mats['fang_w'] = Material(FANG, spec=0.5, gloss=50)
    mats['bone'] = Material(_hex('#e9e1c9'), spec=0.4, gloss=40, brush=0.03)
    mats['glaze'] = Material(CHART, spec=0.8, gloss=60, emissive=tuple(np.array(CHART) * (0.18 + 0.5 * v)))
    mats['lash'] = Material(REED, spec=0.1, gloss=10, brush=0.06)
    mats['reed'] = Material(REED, spec=0.1, gloss=10, brush=0.06)
    mats['hook'] = Material(_hex('#d9d0b4'), spec=0.4, gloss=40)
    mats['rust'] = Material(RUST, spec=0.35, gloss=24, metal=0.3, brush=0.08)
    mats['buckler'] = Material(lambda p, n: _arr(HUSK, len(p)) * (0.92 + 0.12 * fbm(p, 14.0, 2)[:, None]),
                               spec=0.25, gloss=30, sss=0.5, brush=0.03)
    mats['scale'] = Material(lambda p, n: _arr(SCALE_GREY, len(p)) * (0.88 + 0.2 * fbm(p, 6.0, 2)[:, None]),
                             spec=0.5, gloss=40, brush=0.04)
    mats['lacquer'] = Material(lambda p, n: _arr(LACQUER, len(p)) * (0.85 + 0.3 * fbm(p, 9.0, 2)[:, None]),
                               spec=0.7, gloss=50, sss=0.3, brush=0.03)
    mats['lacquer_lt'] = Material(_hex('#e8c27a'), spec=0.7, gloss=50, sss=0.3)
    mats['gourd'] = Material(lambda p, n: _arr(GOURD, len(p)) * (0.85 + 0.25 * fbm(p, 10.0, 2)[:, None]),
                             spec=0.25, gloss=24, brush=0.05)
    mats['venom'] = Material(VENOM, spec=0.8, gloss=70, emissive=tuple(np.array(VENOM) * 0.85), rim=0.3)
    mats['husk'] = Material(lambda p, n: _arr(HUSK, len(p)) * (0.9 + 0.15 * fbm(p, 12.0, 2)[:, None]),
                            spec=0.05, gloss=10, sss=0.6, brush=0.03)
    mats['flake'] = Material(HUSK, spec=0.1, sss=0.5)
    return mats


def husked(mats, e, keep=('venom',)):
    """Death colour: everything lerps to husk pale with ghost bands (some of the old value kept), no gloss, no glow."""
    if e <= 0:
        return mats
    out = {}
    hk = np.array(HUSK)
    for name, m in mats.items():
        base = m.albedo

        def alb(p, n, base=base):
            a = base(p, n) if callable(base) else _arr(base, len(p))
            lum = a @ np.array([0.3, 0.59, 0.11])
            grey = lum[:, None] * np.array([1.0, 0.98, 0.92])[None, :]
            k1 = min(1.0, e * 1.7)
            a = a * (1 - k1) + grey * k1
            k2 = np.clip((e - 0.3) / 0.6, 0, 1)
            ghost = hk[None, :] * (0.78 + 0.30 * np.clip(lum, 0, 1)[:, None])
            return a * (1 - k2) + ghost * k2
        m2 = dataclasses.replace(m, albedo=alb)
        m2.spec = m.spec * (1 - e)
        m2.sss = m.sss * (1 - e) + 0.4 * e
        if m.emissive is not None:
            f = (1 - e) ** 2
            m2.emissive = (lambda p, n, fe=m.emissive, f=f: fe(p, n) * f) if callable(m.emissive) else tuple(np.array(m.emissive) * f)
        out[name] = m2
    return out


def naga_finish(P, N, parts, mats=None, lights=(), B=None, world=None):
    """Merge the faction materials with the unit's, add hit flakes / venom drips, apply the death
    (husk colour + flatten to a skin), and return the Scene. B is found automatically from naga_body."""
    B = B if B is not None else _LAST_B.get('B')
    m = naga_mats(P, N, B)
    if mats:
        m.update(mats)
    add = lambda prim, mat, k=0.0: parts.append(Part(prim, mat, k))
    s = P['s']
    # hit: a few pale skin flakes come off
    fk = P['flakes']
    if fk > 0.02 and 'path' in B:
        rng = np.random.default_rng(7)
        pts = B['path']
        for i in range(4):
            q = pts[rng.integers(len(pts) // 2, len(pts))]
            o = q + v3(rng.uniform(-0.25, 0.25), 0.15 + 0.25 * fk * rng.uniform(0.5, 1), rng.uniform(-0.2, 0.2)) * s
            add(Ellipsoid(o, (0.035 * s, 0.008 * s, 0.025 * s), rot_y(rng.uniform(0, 3)) @ rot_x(rng.uniform(-1, 1))), 'flake', 0.0)
    if world:
        world(add)
    e = P['end']
    fl = P['flat']
    if fl > 0:
        parts[:] = [Part(Squash(pt.prim, 1 - 0.75 * fl, 1 - 0.15 * fl, tuple(-E2 * 0.8)), pt.mat, pt.k) for pt in parts]
    m = husked(m, e)
    lights = [Light(L.pos, L.color, L.intensity * (1 - e), L.radius) for L in lights]
    return Scene(parts=parts, materials=m, lights=lights, ground_clip=True)


_LAST_B = {}
_naga_body = naga_body


def naga_body(P, add, N, arms=True, head=True):  # noqa: F811  (records B for naga_finish)
    B = _naga_body(P, add, N, arms, head)
    _LAST_B['B'] = B
    return B


naga_body.__doc__ = _naga_body.__doc__


def venom_drip(add, P, at, strength=1.0):
    """Venom drops falling from a fang / gourd mouth (live fx 'spray' emitter + one sculpted bright drop)."""
    if strength <= 0.02:
        return
    add(Sphere(at - v3(0, 0.04 * P['s'], 0), 0.013 * P['s']), 'venom', 0.0)
    emit(add, at, 'spray', min(2.0, 0.4 * strength))


def spit_stream(add, P, a, d, length=0.6, n=7, r=0.018):
    """A thin bright stream of venom drops from a, along d (no clouds)."""
    d = norm(d)
    s = P['s']
    for i in range(n):
        t = (i + 0.5) / n
        q = a + d * length * t + v3(0, -0.10 * t * t, 0) * s
        add(Sphere(q, r * s * (1.1 - 0.5 * t)), 'venom', 0.0)
    emit(add, a + d * length, 'spray', 0.8)


# ------------------------------------------------------------------ animation rows

ROWS = [
    ('idle', 4, True, {}),
    ('move', 8, True, {}),
    ('attack', 10, False, {'hitFrame': 2}),
    ('hit', 10, False, {}),
    ('death', 6, False, {'holdLast': True}),
    ('cast', 8, False, {}),
]


def _fwd_of(P):
    return v3(0, 0, 1)


def idle_pose(base, i):
    """Sway left/right with the hood flaring on the outward swing; head dips and the tongue flicks once."""
    P = base()
    sw = [0.0, 1.0, 0.0, -1.0][i]
    bend(P, side=np.radians(3.0) * sw, fwd=np.radians([0, 0.5, 1.5, 0.5][i]))
    P['hood'] = P['hood'] * [1.0, 1.14, 0.96, 1.08][i]
    P['coil_sq'] = [1.0, 1.02, 1.0, 0.985][i]
    P['breathe'] = sw
    P['tell'] = i / 4
    P['tail_sw'] = [0.0, 0.25, 0.0, -0.25][i]
    if i == 2:
        P['head_pitch'] = P['head_pitch'] + np.radians(9)
        P['tongue'] = 1.0
    P['glow'] = [1.0, 0.9, 1.08, 0.95][i]
    return P, {}


def move_pose(base, i):
    """No steps: bands slide along the body (the coil rolls), coil translates, paddle sweeps, torso level."""
    P = base()
    a = 2 * np.pi * i / 4                 # one band period / one coil roll over the loop
    P['band_rot'] = v3(np.cos(a), np.sin(a), 0.0)
    dz = [0.0, 0.04, 0.0, -0.03][i]
    P['coil_c'] = P['coil_c'] + v3(0, 0, dz)
    P['coil_w'] = [1.0, 0.97, 1.0, 1.03][i]
    P['tail_sw'] = [1.0, 0.0, -1.0, 0.0][i]
    bend(P, fwd=np.radians(5), side=np.radians([1.5, 0, -1.5, 0][i]))
    slide(P, v3(0, [0.0, 0.02, 0.0, 0.02][i], 0.03))
    P['hood'] *= 0.92
    return P, {}


def _attack_pose(base, i, style):
    P = base()
    s = P['s']
    ph = ['wind', 'rise', 'strike', 'recover'][i]
    if ph == 'wind':          # draw back and down into the coil, hood flat
        slide(P, v3(0, -0.14, -0.10) * s, mid=0.8)
        bend(P, fwd=np.radians(-8))
        P['coil_sq'] = 0.88
        P['coil_w'] = 1.04
        P['hood'] = 0.55
    elif ph == 'rise':
        slide(P, v3(0, -0.04, 0.02) * s, mid=0.6)
        bend(P, fwd=np.radians(4))
        P['coil_sq'] = 0.95
        P['hood'] = 1.0
        P['jaw'] = 0.3
    elif ph == 'strike':      # fast forward lunge, hood full, fangs bared
        slide(P, v3(0.0, -0.06, 0.30) * s, mid=0.7)
        bend(P, fwd=np.radians(14))
        P['coil_sq'] = 1.04
        P['hood'] = 1.35
        P['jaw'] = 1.0
        P['venom'] = 1.0
        P['fx'] = 1.0
        P['tail_sw'] = -0.8
    else:
        slide(P, v3(0, -0.02, 0.10) * s, mid=0.6)
        bend(P, fwd=np.radians(5))
        P['hood'] = 1.1
        P['jaw'] = 0.3
        P['venom'] = 0.3
        P['tail_sw'] = -0.3
    sides = [k[3:] for k in P if k.startswith('hd_')]
    if style == 'thrust':      # two-handed pole: pull back along the shaft, then drive it forward
        d = _pole_dir(P)
        k = {'wind': -0.22, 'rise': -0.05, 'strike': 0.14, 'recover': 0.06}[ph] * s
        move_hands(P, d * k + v3(0, 0.0, 0), sides)
        if ph == 'strike':
            slide(P, v3(-0.06, 0.0, -0.12) * s, mid=0.5)   # the weapon does the reaching
    elif style == 'swing':     # one-handed weapon in the right hand: raise high back, cut down across
        R = {'wind': rot_x(-1.9) @ rot_z(-0.2), 'rise': rot_x(-1.3), 'strike': rot_x(0.35) @ rot_z(0.15),
             'recover': rot_x(0.12)}[ph]
        sh = P['sh_r']
        hd = P['hd_r'] - sh
        P['hd_r'] = sh + R @ hd + v3(0, 0.0, 0.0)
        if P.get('item_r') is not None:
            P['item_r'] = R @ P['item_r']
    elif style == 'bash':      # shield driven forward with both hands
        k = {'wind': -0.10, 'rise': 0.0, 'strike': 0.22, 'recover': 0.06}[ph] * s
        move_hands(P, v3(0, 0.02, 1) * k, sides)
    elif style == 'quad':      # four-armed: upper pair chops down, lower pair thrusts
        Ru = {'wind': rot_x(-0.9), 'rise': rot_x(-0.5), 'strike': rot_x(0.6), 'recover': rot_x(0.2)}[ph]
        for sd in ('r', 'l'):
            sh = P['sh_' + sd]
            P['hd_' + sd] = sh + Ru @ (P['hd_' + sd] - sh)
            if P.get('item_' + sd) is not None:
                P['item_' + sd] = Ru @ P['item_' + sd]
        k = {'wind': -0.12, 'rise': 0.0, 'strike': 0.10, 'recover': 0.04}[ph] * s
        move_hands(P, v3(-0.3, 0, 1) * k, ('r2', 'l2'))
        if ph == 'strike':
            slide(P, v3(-0.10, 0, -0.12) * s, mid=0.5)   # giants lunge less: keep the blades in frame
    elif style in ('bite', 'spit'):   # head-first: neck and head reach further than the body
        k = {'wind': -0.06, 'rise': 0.0, 'strike': 0.16, 'recover': 0.04}[ph] * s
        P['head'] = P['head'] + v3(0, -0.4 * k, 1) * k
        if style == 'spit':
            P['spit'] = {'wind': 0.0, 'rise': 0.2, 'strike': 1.0, 'recover': 0.3}[ph]
    return P, {}


def _pole_dir(P):
    if 'hd_r' in P and 'hd_l' in P:
        d = P['hd_l'] - P['hd_r']
        if np.linalg.norm(d) > 1e-3:
            return norm(d)
    return v3(0, 0, 1)


def hit_pose(base, i):
    P = base()
    s = P['s']
    if i == 0:
        slide(P, v3(0, -0.04, -0.10) * s, mid=0.7)
        bend(P, fwd=np.radians(-10), side=np.radians(-3))
        P['hood'] = 0.2
        P['coil_sq'] = 0.9
        P['coil_w'] = 1.04
        P['flakes'] = 1.0
        P['jaw'] = 0.5
        P['tail_sw'] = 0.8
        return P, dict(exposure=1.25, flash=0.22)
    slide(P, v3(0, -0.01, -0.04) * s, mid=0.7)
    bend(P, fwd=np.radians(-4))
    P['hood'] = 0.8
    P['flakes'] = 0.4
    return P, {}


def death_pose(base, i):
    """Slump sideways into the coils, hood folds, bands dull, ends as a flat empty skin in a ring."""
    P = base()
    s = P['s']
    if i == 0:      # recoil, hood shut
        slide(P, v3(0, -0.03, -0.08) * s, mid=0.6)
        bend(P, fwd=np.radians(-12), side=np.radians(-4))
        P['hood'] = 0.35
        P['jaw'] = 0.6
        P['coil_sq'] = 0.92
        return P, dict(exposure=1.15, flash=0.12)
    f = [0, 0.55, 1.0, 1.0][i]
    # sink the waist toward the top of the coil and fall toward the figure's left (screen right)
    slide(P, v3(-0.02, -0.50 * f, -0.06) * s, mid=0.75)
    bend(P, side=np.radians(28) * f, fwd=np.radians(-72) * f)
    P['mid'] = P['mid'] + v3(0.05, -0.12, -0.32) * f * s
    P['head_pitch'] = P['head_pitch'] + np.radians(30) * f
    P['head_roll'] = np.radians(-40) * f
    P['hood'] = [0.35, 0.3, 0.15, 0.1][i]
    P['jaw'] = [0.6, 0.4, 0.1, 0.0][i]
    P['coil_sq'] = [0.94, 0.95, 0.97, 0.97][i]
    P['coil_w'] = [1.0, 1.02, 1.03, 1.03][i]
    P['drop'] = [0, 0.3, 1.0, 1.0][i]
    P['end'] = [0, 0.3, 0.65, 1.0][i]
    P['flat'] = [0, 0, 0.25, 1.0][i]
    P['glow'] = [1, 0.5, 0.2, 0][i]
    # hands go limp, lying on the ground beside the body
    for k, sd in enumerate([x[3:] for x in P if x.startswith('hd_')]):
        sx = -1 if sd[0] == 'r' else 1
        lim = P['waist'] + v3(sx * 0.28 + 0.10, -0.25, 0.02 + 0.05 * k) * s
        lim[1] = max(lim[1], 0.12 * s)
        P['hd_' + sd] = lerp(P['hd_' + sd], lim, min(1.0, f * 1.2))
    return P, {}


def cast_pose(base, i, style='raise'):
    """Hood flares, arms raise, venom glow brightens at the mouth; 'spit' and 'throw' add a stream / throw."""
    P = base()
    s = P['s']
    bend(P, fwd=np.radians([-4, -7, 6][i]))
    slide(P, v3(0, [0.03, 0.06, 0.0][i], [0.0, -0.02, 0.08][i]) * s)
    P['hood'] = [1.2, 1.4, 1.1][i]
    P['venom'] = [0.4, 1.0, 0.6][i]
    P['jaw'] = [0.3, 0.6, 0.4][i]
    P['cast_glow'] = [0.5, 1.0, 0.4][i]
    P['glow'] = [1.3, 2.0, 1.3][i]
    if style == 'raise':
        for sd in [x[3:] for x in P if x.startswith('hd_')]:
            P['hd_' + sd] = P['hd_' + sd] + v3(0, [0.12, 0.28, 0.10][i], [0.02, 0.06, 0.12][i]) * s
    elif style == 'spit':
        P['spit'] = [0.2, 1.0, 0.4][i]
        P['head'] = P['head'] + v3(0, 0, [0.0, 0.10, 0.04][i]) * s
    elif style == 'throw':
        P['throw'] = [0.0, 0.5, 1.0][i]
    return P, {}


def naga_rows(base, attack='thrust', cast='raise', hook=None):
    """(ROWS, frames) for a Slough unit. base() must return a fresh neutral pose. hook(row, i, P) tweaks frames."""
    def frames():
        out = {
            'idle': [idle_pose(base, i) for i in range(4)],
            'move': [move_pose(base, i) for i in range(4)],
            'attack': [_attack_pose(base, i, attack) for i in range(4)],
            'hit': [hit_pose(base, i) for i in range(2)],
            'death': [death_pose(base, i) for i in range(4)],
            'cast': [cast_pose(base, i, cast) for i in range(3)],
        }
        if hook:
            for row, fr in out.items():
                for i, (P, o) in enumerate(fr):
                    hook(row, i, P)
        return out
    return ROWS, frames


TOKEN_ROWS = [
    ('idle', 2, True, {}),
    ('hit', 10, False, {}),
    ('death', 6, False, {'holdLast': True}),
]


def token_rows(base, hook=None):
    """Husks and tail segments: idle (flutter / peristaltic ripple), hit (jolt + flash), death (collapse flat,
    fade). Channels: tell (0..1 phase), flakes, end, flat, gone (0..1 blown away)."""
    def frames():
        def mk(**kw):
            P = base()
            P.update(kw)
            return P
        out = {
            'idle': [(mk(tell=0.0), {}), (mk(tell=0.5), {})],
            'hit': [(mk(tell=0.25, flakes=1.0, shake=1.0), dict(exposure=1.25, flash=0.22)), (mk(tell=0.4, flakes=0.4, shake=-0.4), {})],
            'death': [(mk(flat=0.35, end=0.3, flakes=0.8), dict(exposure=1.1, flash=0.1)),
                      (mk(flat=0.85, end=0.7, gone=0.5), {}), (mk(flat=1.0, end=1.0, gone=1.0), {})],
        }
        if hook:
            for row, fr in out.items():
                for i, (P, o) in enumerate(fr):
                    hook(row, i, P)
        return out
    return TOKEN_ROWS, frames


__all__ = [n for n in dir() if not n.startswith('__')]

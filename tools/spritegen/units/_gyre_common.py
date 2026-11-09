"""Shared Gyre helpers: palette, GyreLook, the flying-bird sculptor (wings built from feathered
SDF blades), the seated rider, the feather-heap death, ground-folk costume pieces and the
animation rows for fliers.

Shape language: wings first. Birds are drawn in flight on a hover (no baked ground shadow while
airborne, the engine draws it). Rider is small, hunched, secondary. Ground roost-folk are thick,
hooked and feathered. Beak orange only on beaks, cord, sashes and one strap.
"""
import copy
import dataclasses as _dc
import numpy as np
from kit.humanoid import *          # noqa: F401,F403  (v3, prims, Material, Part, Light, Costume, ...)
from kit.humanoid import finish as _kit_finish
from kit.anim import humanoid_rows, ROWS as KIT_ROWS
from kit.looks import LOOKS
from kit.xform import transform_parts, squash_parts
from render import Camera, Look
from sdf import Prim, hash3
import rig

hx = _hex
FACTION = 'gyre'

SLATE = _hex('#5a6470')
ORANGE = _hex('#e8892f')
GUANO = _hex('#ece9e1')
INK = _hex('#1c1f26')
FRIGATE = _hex('#b5362f')
BONE = _hex('#d9d0b4')
OIL = _hex('#7a7566')          # weathered flight-coat oilskin (slate pulled paler)
OIL_DK = _hex('#4d4a42')
TAR = _hex('#2a2926')
STRAW = _hex('#a8946a')
CANVAS = _hex('#b9b3a0')
SKIN_W = _hex('#c9926f')       # wind-weathered
GOLD = _hex('#d9b14a')


# ------------------------------------------------------------------ look

@_dc.dataclass
class GyreLook(Look):
    """Look that drops the baked ground shadow when `air` is set (the engine draws the flier's)."""
    air: bool = False

    def __post_init__(self):
        if self.air:
            self.ground_shadow = 0.0


def _mk_look(air):
    base = LOOKS['salt_concord']
    kw = {f.name: getattr(base, f.name) for f in _dc.fields(Look)}
    kw.update(sky=(0.60, 0.65, 0.72), sky_int=0.34, rim_color=(0.78, 0.88, 1.0), rim_int=0.6,
              bounce=(0.78, 0.76, 0.70), shadow_tint=(0.66, 0.76, 1.0), exposure=1.04, toon=1.0)
    return GyreLook(air=air, **kw)


LOOK = _mk_look(False)          # ground units
LOOK_AIR = _mk_look(True)       # fliers
GROUND_OVER = dict(air=False, ground_shadow=0.45)     # look override for frames that rest on the ground


# ------------------------------------------------------------------ small colour helpers

def _arr(c, n):
    return np.array(c)[None, :].repeat(n, 0)


def mix(a, b, t):
    return tuple(np.array(a) * (1 - t) + np.array(b) * t)


def tone(c, f):
    return tuple(np.clip(np.array(c) * f, 0, 1))


def noisy(base, amt=0.10, freq=24.0):
    b = np.array(base)
    return lambda p, n: np.clip(b[None, :] * (1 - amt + 2 * amt * fbm(p, freq, 2)[:, None]), 0, 1)


def oil_albedo(base=OIL, wear=0.25, freq=16.0, salt=0.0):
    """Waxed oilskin stiff with salt: darker creases, pale worn patches and salt bloom."""
    b = np.array(base)

    def fn(p, n):
        w = fbm(p * np.array([1.0, 0.45, 1.0]), freq, 3)
        crease = np.clip((0.42 - w) * 3.0, 0, 1)[:, None]
        pale = np.clip((w - 0.60) * 3.0, 0, 1)[:, None] * wear
        c = b[None, :] * (1 - 0.30 * crease) + np.array(GUANO)[None, :] * pale * 0.5
        if salt > 0:
            s = np.clip((fbm(p + 4.1, 9.0, 3) - (1 - salt)) * 5, 0, 1)[:, None]
            c = c * (1 - s * 0.6) + np.array(GUANO)[None, :] * s * 0.6
        return np.clip(c, 0, 1)
    return fn


def gyre_mats(P, skin=SKIN_W, hair=_hex('#3f3730'), coat=OIL, eyes=_hex('#241c19'), lips=_hex('#9a5a4c'),
              beard=None, coat_salt=0.25):
    m = {
        'oil': Material(oil_albedo(coat, salt=coat_salt), spec=0.30, gloss=22, brush=0.06),
        'oil_dk': Material(oil_albedo(tone(coat, 0.62), salt=coat_salt * 0.6), spec=0.28, gloss=20, brush=0.06),
        'oil_pale': Material(oil_albedo(mix(coat, GUANO, 0.35), salt=0.1), spec=0.25, gloss=20, brush=0.06),
        'wool': Material(noisy(_hex('#7b7770'), 0.12), spec=0.02, brush=0.08),
        'canvas': Material(noisy(CANVAS, 0.08), spec=0.03, brush=0.08),
        'straw': Material(noisy(STRAW, 0.14, 40.0), spec=0.03, brush=0.08),
        'bone': Material(noisy(BONE, 0.07), spec=0.2, gloss=24, brush=0.04),
        'cord': Material(ORANGE, spec=0.1, gloss=12, brush=0.04),
        'tar': Material(TAR, spec=0.1, gloss=12, brush=0.04),
        'leather': Material(_hex('#4a3626'), spec=0.18, gloss=20, brush=0.06),
        'boot': Material(_hex('#33291f'), spec=0.22, gloss=22, brush=0.05),
        'glove': Material(_hex('#4c3a2c'), spec=0.15, gloss=18, brush=0.04),
        'wood': Material(noisy(_hex('#7a6a58'), 0.12, 30.0), spec=0.08, gloss=10, brush=0.08),
        'drift': Material(noisy(_hex('#8d8579'), 0.14, 28.0), spec=0.05, gloss=8, brush=0.08),
        'iron': Material(_hex('#4f545c'), spec=0.7, gloss=30, metal=0.7, brush=0.05),
        'steel': Material(_hex('#b9c2c8'), spec=1.0, gloss=60, metal=0.6, brush=0.02),
        'brass': Material(_hex('#a98a4c'), spec=0.8, gloss=36, metal=0.9, brush=0.05),
        'gold': Material(GOLD, spec=0.9, gloss=40, metal=0.9, brush=0.03),
        'beak': Material(ORANGE, spec=0.25, gloss=26, brush=0.03),
        'beak_ink': Material(tone(INK, 1.2), spec=0.3, gloss=26, brush=0.03),
        'beak_bone': Material(noisy(BONE, 0.05), spec=0.3, gloss=26, brush=0.03),
        'eye': Material(_hex('#14161b'), spec=0.9, gloss=60, brush=0.0),
        'eye_ring': Material(ORANGE, spec=0.1, brush=0.0),
        'red': Material(FRIGATE, spec=0.3, gloss=24, sss=0.4, brush=0.04),
        'leg': Material(noisy(_hex('#7d6a60'), 0.1), spec=0.1, brush=0.04),
        'feather_s': Material(noisy(SLATE, 0.10, 40.0), spec=0.05, brush=0.06),
        'feather_g': Material(noisy(GUANO, 0.05, 40.0), spec=0.04, brush=0.06),
        'feather_i': Material(noisy(INK, 0.10, 40.0), spec=0.12, gloss=20, brush=0.06),
        'glass': Material(_hex('#9fd8cf'), spec=0.5, gloss=40, emissive=tone(_hex('#7fd6c8'), 0.55), rim=0.0),
        'lamp': Material(_hex('#ffcf7a'), spec=0.3, gloss=30, emissive=_hex('#ffcf7a'), rim=0.0),
        'flash': Material(_hex('#fff2c0'), emissive=_hex('#fff2c0'), rim=0.0),
        'skin': Material(face_albedo(P, skin, hair, eyes=eyes, beard=beard, lips=lips), spec=0.06, gloss=12,
                         sss=0.5, brush=0.02),
        'hair': Material(hair, spec=0.2, gloss=16, brush=0.10),
        'bread': Material(noisy(_hex('#b98a4f'), 0.12, 30.0), spec=0.05, brush=0.06),
    }
    return m


# ------------------------------------------------------------------ frames and local builders

def rot_zx(roll, pitch):
    return rot_x(pitch) @ rot_z(roll)


class Frame:
    """Rigid frame: world = t + R @ local."""
    def __init__(self, R=None, t=(0, 0, 0)):
        self.R = np.eye(3) if R is None else R
        self.t = v3(*t)

    def pt(self, q):
        return self.t + self.R @ np.asarray(q, dtype=np.float64)

    def inv(self, p):
        return (p - self.t) @ self.R


class Loc:
    """Builder that places primitives given in a local frame (with uniform scale k)."""
    def __init__(self, add, F, k=1.0):
        self.add, self.F, self.k = add, F, k

    def p(self, *q):
        if len(q) == 1:
            q = q[0]
        return self.F.t + self.F.R @ (np.asarray(q, dtype=np.float64) * self.k)

    def d(self, *q):
        if len(q) == 1:
            q = q[0]
        return self.F.R @ np.asarray(q, dtype=np.float64)

    def ell(self, c, r, mat, k=0.0, R=None):
        RR = self.F.R if R is None else self.F.R @ R
        self.add(Ellipsoid(self.p(c), [x * self.k for x in r], RR), mat, k)

    def cap(self, a, b, ra, rb, mat, k=0.0):
        self.add(Capsule(self.p(a), self.p(b), ra * self.k, ra * self.k if rb is None else rb * self.k), mat, k)

    def sph(self, c, r, mat, k=0.0):
        self.add(Sphere(self.p(c), r * self.k), mat, k)

    def along(self, a, b, rx, rz, mat, k=0.0, hint=(0, 1, 0)):
        """Ellipsoid whose long axis runs a -> b (local coordinates), cross radii rx, rz."""
        a, b = v3(*a), v3(*b)
        axis = self.F.R @ (b - a)
        hn = self.F.R @ v3(*hint)
        R = basis_from(axis, hn)
        L = np.linalg.norm(b - a) * 0.5 * self.k
        self.add(Ellipsoid(self.p((a + b) / 2), (rx * self.k, L, rz * self.k), R), mat, k)


# ------------------------------------------------------------------ the feathered blade (wings, tails, kites)

class Blade(Prim):
    """Thin tapered slab with a scalloped/toothed trailing edge. Local axes: e (span), c (chord toward
    the trailing edge), n (normal). lead/trail/th are (root, tip) pairs."""
    def __init__(self, A, e, c, n, L, lead=(0.05, 0.03), trail=(0.30, 0.08), th=(0.03, 0.012),
                 teeth=None, notch=0.0, gs=1.25):
        self.A, self.e, self.c, self.n = v3(*A), v3(*e), v3(*c), v3(*n)
        self.L, self.lead, self.trail, self.th = L, lead, trail, th
        self.teeth, self.notch = teeth, notch
        self.gs = gs * (1.0 + (0.9 * teeth[1] * teeth[0] / L if teeth else 0.0))
        tm, lm = max(trail), max(lead)
        self.bc = self.A + self.e * L / 2 + self.c * (tm - lm) / 2
        self.br = float(np.hypot(L / 2, (tm + lm) / 2) + max(th) + 0.03)

    def coords(self, p):
        rel = p - self.A
        a = rel @ self.e
        b = rel @ self.c
        w = rel @ self.n
        t = np.clip(a / self.L, 0, 1)
        ld = self.lead[0] + (self.lead[1] - self.lead[0]) * t
        tr = self.trail[0] + (self.trail[1] - self.trail[0]) * t
        th = self.th[0] + (self.th[1] - self.th[0]) * t
        if self.teeth:
            nt, dp, t0 = self.teeth
            f = (a / self.L * nt) % 1.0
            k = np.clip((t - t0) / 0.1, 0, 1)
            tr = tr - dp * f * k
        return a, b, w, t, ld, tr, th

    def __call__(self, p):
        a, b, w, t, ld, tr, th = self.coords(p)
        Le = self.L
        if self.notch:
            Le = self.L - self.notch * np.clip(1 - np.abs(b) / np.maximum(tr, 1e-3), 0, 1)
        return np.maximum.reduce([np.abs(w) - th, (b - tr) / self.gs, -ld - b, -a, a - Le])


def wing_paint(bl, col, seg, nf=9, cov=0.36, tip_t=0.62):
    """Feather albedo for a wing blade: coverts, flight-feather streaks, ink tip, optional white spot."""
    base, covert, flight, tip, spot = (np.array(col[k]) if col.get(k) is not None else None
                                       for k in ('mantle', 'covert', 'flight', 'tip', 'spot'))

    def fn(p, n):
        a, b, w, t, ld, tr, th = bl.coords(p)
        N = len(p)
        u = np.clip((b + ld) / np.maximum(tr + ld, 1e-4), 0, 1)
        c = _arr(flight if seg == 'o' else base, N)
        edge = 0.04 * np.sin(a * 60.0)
        iscov = u < cov + edge
        c[iscov] = (covert if seg == 'o' else covert)[None, :] * np.ones((iscov.sum(), 1))
        f = (a / bl.L * nf) % 1.0
        line = ((f < 0.08) | (f > 0.94)) & ~iscov
        c[line] = c[line] * 0.78
        # barring on the coverts
        if seg == 'i':
            row = ((u * 5.0 + np.sin(a * 40.0) * 0.1) % 1.0) < 0.16
            m = iscov & row
            c[m] = c[m] * 0.88
        if tip is not None and seg == 'o':
            tp = t > tip_t + 0.05 * np.sin(b * 30.0)
            c[tp] = tip[None, :]
            if spot is not None:
                sp = (np.abs(t - (tip_t - 0.10)) < 0.055) & (u > 0.25) & (u < 0.75)
                c[sp] = spot[None, :]
        c *= (0.93 + 0.14 * fbm(p, 30.0, 2))[:, None]
        under = (n @ bl.n) < 0
        c[under] = c[under] * 0.35 + np.array(GUANO)[None, :] * 0.65 * np.array([0.92, 0.94, 1.0])[None, :]
        return np.clip(c, 0, 1)
    return fn


# ------------------------------------------------------------------ bird species

def _sp(**kw):
    d = dict(
        k=1.2,                       # overall scale
        body=(0.165, 0.150, 0.40), # half sizes x, y, z
        neck=0.30, headr=(0.072, 0.068, 0.10), neck_th=0.07,
        beak_len=0.21, beak_d=0.040, hook=0.022, beak_mat='beak', tip_mat=None,
        L_in=0.43, L_out=0.46, ch_root=0.32, ch_wrist=0.23, ch_tip=0.05, lead=0.055, th=0.030,
        dihedral=0.30, amp_in=0.45, amp_out=0.55, sweep_in=0.10, sweep_out=0.42, bend=0.0, teeth=(9, 0.05, 0.45),
        tail_len=0.34, tail_w=(0.07, 0.20), tail_notch=0.0, tail_th=0.014,
        col=dict(mantle=SLATE, covert=mix(SLATE, GUANO, 0.15), flight=mix(SLATE, INK, 0.25), tip=INK, spot=GUANO),
        back=SLATE, belly=GUANO, head=GUANO, neckc=GUANO, tailc=GUANO,
        saddle=(0.20, -0.04), leg=(0.05, 0.34), eye_ring=False, pouch=None, ruff=None, bare_head=False,
        nf=9, cov=0.36, tip_t=0.62, neck_ext=0.0,
    )
    d.update(kw)
    return d


SPECIES = {
    'gull': _sp(),
    'blackback': _sp(k=1.18, body=(0.17, 0.155, 0.42), beak_len=0.24, hook=0.028, L_in=0.52, L_out=0.58, ch_root=0.36,
                     col=dict(mantle=mix(INK, SLATE, 0.18), covert=mix(INK, SLATE, 0.3), flight=INK, tip=INK, spot=GUANO),
                     back=mix(INK, SLATE, 0.2), tailc=GUANO, nf=10),
    'crow': _sp(k=0.70, body=(0.15, 0.14, 0.34), beak_len=0.32, beak_d=0.075, hook=0.020, beak_mat='beak_ink', gloss=True,
                headr=(0.092, 0.086, 0.115), neck=0.26, L_in=0.40, L_out=0.50, ch_root=0.36, ch_wrist=0.30, ch_tip=0.10,
                th=0.034, sweep_out=0.30, teeth=(7, 0.11, 0.30), tail_len=0.36, tail_w=(0.06, 0.16),
                col=dict(mantle=mix(INK, SLATE, 0.35), covert=mix(INK, SLATE, 0.45), flight=mix(INK, SLATE, 0.25),
                         tip=None, spot=None),
                back=mix(INK, SLATE, 0.32), belly=mix(INK, SLATE, 0.22), head=mix(INK, SLATE, 0.2),
                neckc=mix(INK, SLATE, 0.3), tailc=INK, eye_ring=True, nf=8, cov=0.34, tip_t=0.99),
    'skua': _sp(k=1.0, body=(0.17, 0.155, 0.40), beak_len=0.20, hook=0.030, beak_mat='beak_ink', neck=0.26,
                L_in=0.46, L_out=0.56, ch_root=0.32, ch_wrist=0.22, ch_tip=0.045, sweep_in=0.28, sweep_out=0.62,
                teeth=(9, 0.04, 0.5), tail_len=0.30, tail_w=(0.06, 0.15),
                col=dict(mantle=_hex('#6d5c4b'), covert=_hex('#7c6a57'), flight=_hex('#4d4238'), tip=_hex('#2f2924'),
                         spot=GUANO),
                back=_hex('#6d5c4b'), belly=_hex('#9a8b78'), head=_hex('#5f5043'), neckc=_hex('#8a7a66'),
                tailc=_hex('#4d4238'), tip_t=0.50),
    'pelican': _sp(k=1.25, body=(0.20, 0.17, 0.42), neck=0.18, neck_th=0.09, headr=(0.07, 0.07, 0.09),
                   beak_len=0.50, beak_d=0.05, hook=0.03, L_in=0.56, L_out=0.60, ch_root=0.44, ch_wrist=0.34,
                   ch_tip=0.10, th=0.036, sweep_in=0.06, sweep_out=0.22, teeth=(10, 0.08, 0.42), tail_len=0.26,
                   tail_w=(0.08, 0.16), pouch='pelican',
                   col=dict(mantle=mix(GUANO, SLATE, 0.12), covert=mix(GUANO, SLATE, 0.05),
                            flight=mix(SLATE, INK, 0.45), tip=INK, spot=None),
                   back=mix(GUANO, SLATE, 0.10), belly=GUANO, head=GUANO, neckc=GUANO, tailc=mix(GUANO, SLATE, 0.2),
                   tip_t=0.50, saddle=(0.21, 0.0), nf=11, cov=0.42),
    'shrike': _sp(k=0.95, body=(0.15, 0.14, 0.36), neck=0.20, headr=(0.080, 0.072, 0.095), beak_len=0.15,
                  beak_d=0.043, hook=0.040, beak_mat='beak_ink', L_in=0.40, L_out=0.46, ch_root=0.30, ch_wrist=0.25,
                  ch_tip=0.07, sweep_out=0.30, teeth=(8, 0.05, 0.45), tail_len=0.52, tail_w=(0.05, 0.13),
                  col=dict(mantle=mix(INK, SLATE, 0.3), covert=mix(INK, SLATE, 0.4), flight=INK, tip=INK, spot=GUANO),
                  back=SLATE, belly=GUANO, head=mix(SLATE, GUANO, 0.15), neckc=mix(SLATE, GUANO, 0.4), tailc=INK,
                  tip_t=0.45, nf=8),
    'frigate': _sp(k=1.1, body=(0.14, 0.13, 0.40), neck=0.22, headr=(0.060, 0.058, 0.085), beak_len=0.32,
                   beak_d=0.032, hook=0.045, beak_mat='beak_bone', tip_mat='beak', L_in=0.62, L_out=0.82,
                   ch_root=0.26, ch_wrist=0.18, ch_tip=0.03, th=0.026, dihedral=0.20, sweep_in=-0.05, sweep_out=0.50,
                   bend=0.30, teeth=(10, 0.03, 0.55), tail_len=0.62, tail_w=(0.05, 0.20), tail_notch=0.34,
                   col=dict(mantle=mix(INK, SLATE, 0.2), covert=mix(INK, SLATE, 0.3), flight=INK, tip=None, spot=None),
                   back=mix(INK, SLATE, 0.18), belly=mix(INK, SLATE, 0.12), head=INK, neckc=INK, tailc=INK,
                   pouch='frigate', tip_t=0.99, nf=10, cov=0.30),
    'albatross': _sp(k=1.55, body=(0.19, 0.17, 0.44), neck=0.24, headr=(0.080, 0.076, 0.105), beak_len=0.30,
                     beak_d=0.052, hook=0.045, beak_mat='beak', L_in=0.62, L_out=0.80, ch_root=0.26, ch_wrist=0.20,
                     ch_tip=0.045, th=0.030, dihedral=0.06, amp_in=0.30, amp_out=0.30, sweep_in=0.04, sweep_out=0.20,
                     teeth=(12, 0.025, 0.55), tail_len=0.30, tail_w=(0.07, 0.15),
                     col=dict(mantle=mix(SLATE, INK, 0.35), covert=mix(SLATE, INK, 0.2), flight=mix(SLATE, INK, 0.5),
                              tip=INK, spot=None),
                     back=mix(GUANO, SLATE, 0.2), belly=GUANO, head=GUANO, neckc=GUANO, tailc=GUANO,
                     tip_t=0.6, saddle=(0.21, -0.02), nf=12, cov=0.32),
    'vulture': _sp(k=1.45, body=(0.19, 0.17, 0.42), neck=0.24, neck_th=0.06, headr=(0.060, 0.062, 0.085),
                   beak_len=0.20, beak_d=0.045, hook=0.050, beak_mat='beak_bone', tip_mat='beak',
                   L_in=0.52, L_out=0.60, ch_root=0.42, ch_wrist=0.36, ch_tip=0.16, th=0.034, dihedral=0.20,
                   sweep_in=0.0, sweep_out=0.15, teeth=(7, 0.15, 0.30), tail_len=0.34, tail_w=(0.08, 0.17),
                   col=dict(mantle=mix(INK, SLATE, 0.62), covert=mix(INK, SLATE, 0.75), flight=mix(INK, SLATE, 0.45),
                            tip=None, spot=None),
                   back=mix(INK, SLATE, 0.6), belly=mix(INK, SLATE, 0.55), head=_hex('#b49a92'), neckc=_hex('#a89088'),
                   tailc=INK, ruff=mix(GUANO, SLATE, 0.25), bare_head=True, tip_t=0.99, nf=7, cov=0.34,
                   saddle=(0.21, -0.02)),
}


def species(name, half=None, **kw):
    """Species spec. `half` rescales the wing so (L_in + L_out) * k equals that many metres (frame fit)."""
    d = copy.deepcopy(SPECIES[name])
    d.update(kw)
    if half:
        f = half / ((d['L_in'] + d['L_out']) * d['k'])
        d['L_in'] *= f
        d['L_out'] *= f
    return d


# ------------------------------------------------------------------ flier pose channels

FLY = dict(fl=0.3, fl2=0.0, fold=0.0, bob=0.0, dx=0.0, dz=0.0, dy=0.0, pitch=0.0, roll=0.0, yaw=0.0,
           neckx=0.0, dip=0.0, openb=0.0, strike=0.0, legs=0.0, pouch=0.0, kick=0.0, tell=0.0, glow=1.0,
           cast_glow=0.0, fx=0.0, end=0.0, melt=0.0, rfall=0.0, scatter=0.0, swirl=0.0, lean=0.0, arm=0.0,
           look=0.0, snatch=0.0, sink=0.0, tailup=0.0, tailsp=0.0, ruffle=0.0)


def fly_pose(**kw):
    P = dict(FLY)
    P.update(kw)
    return P


def bird_frame(P, y0=0.52, z0=0.0, x0=0.0):
    R = rot_y(P['yaw']) @ rot_zx(P['roll'], P['pitch'])
    t = v3(x0 + P['dx'], y0 + P['bob'] + P['dy'], z0 + P['dz'])
    return Frame(R, t)


def _axis_rot(ax, a):
    ax = norm(ax)
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * (K @ K)


def wing_geom(S, side, P):
    """Inner and outer wing segments in bird-local (unscaled) coordinates: A, e, c, n, L."""
    s = side
    fold = P['fold']
    ph_in = S['dihedral'] + P['fl'] * S['amp_in'] - 0.35 * fold
    sw_in = S['sweep_in'] + 0.80 * fold
    ph_out = ph_in * 0.5 + S['bend'] + P['fl2'] * S['amp_out'] - 0.30 * fold
    sw_out = S['sweep_out'] + 0.75 * fold + 0.15 * P['ruffle']

    def frame(sweep, elev):
        Rs = rot_y(s * sweep)
        e0 = Rs @ v3(s, 0, 0)
        c0 = Rs @ v3(0, 0, -1)
        n0 = v3(0, 1, 0)
        e = e0 * np.cos(elev) + n0 * np.sin(elev)
        n = n0 * np.cos(elev) - e0 * np.sin(elev)
        return e, c0, n
    e1, c1, n1 = frame(sw_in, ph_in)
    A = v3(s * S['body'][0] * 0.55, S['body'][1] * 0.55, S['body'][2] * 0.30)
    W = A + e1 * S['L_in']
    e2, c2, n2 = frame(sw_out, ph_out)
    return dict(A=A, e=e1, c=c1, n=n1, L=S['L_in']), dict(A=W, e=e2, c=c2, n=n2, L=S['L_out'])


def bird(add, mats, F, S, P, tag='b'):
    """Sculpt one bird in flight into `add`. F: Frame (world <- bird-local). Returns a dict of key points
    in WORLD coordinates (head, beak_tip, saddle, back, wing tips, tail)."""
    k = S['k']
    L = Loc(add, F, k)
    bx, by, bz = S['body']
    # ---- wings (blades are built in world space from local geometry)
    tips = {}
    for side in (-1, 1):
        gi, go = wing_geom(S, side, P)
        for seg, g in (('i', gi), ('o', go)):
            A = L.p(g['A'])
            e, c, n = F.R @ g['e'], F.R @ g['c'], F.R @ g['n']
            Ls = g['L'] * k
            if seg == 'i':
                bl = Blade(A, e, c, n, Ls, lead=(S['lead'] * k, S['lead'] * 0.7 * k),
                           trail=(S['ch_root'] * k, S['ch_wrist'] * k), th=(S['th'] * 1.3 * k, S['th'] * 0.9 * k),
                           teeth=(5, 0.03 * k, 0.15))
            else:
                bl = Blade(A, e, c, n, Ls, lead=(S['lead'] * 0.7 * k, S['lead'] * 0.25 * k),
                           trail=(S['ch_wrist'] * k, S['ch_tip'] * k), th=(S['th'] * 0.9 * k, S['th'] * 0.35 * k),
                           teeth=(S['teeth'][0], S['teeth'][1] * k, S['teeth'][2]))
            name = '%s_w%s%s' % (tag, seg, 'L' if side > 0 else 'R')
            mats[name] = Material(wing_paint(bl, S['col'], seg, S['nf'], S['cov'], S['tip_t']), spec=0.05, brush=0.05)
            add(bl, name, 0.0)
            if seg == 'i':
                add(Capsule(A, A + e * Ls, 0.040 * k * S.get('spar', 1.0), 0.030 * k * S.get('spar', 1.0)), tag + '_cov', 0.02)
            else:
                tip = A + e * Ls
                add(Capsule(A, tip, 0.030 * k * S.get('spar', 1.0), 0.012 * k * S.get('spar', 1.0)), tag + '_cov', 0.0)
                tips[side] = tip
                nfing = S.get('fingers', 5)
                for j in range(nfing):
                    ang = (j - (nfing - 1) / 2) * 0.13 * side
                    Rf = _axis_rot(n, ang)
                    ef = Rf @ e
                    cf = norm(c - ef * (c @ ef))
                    Af = A + e * Ls * (0.50 + 0.05 * j / nfing)
                    fl_ = Ls * (0.46 + 0.04 * (1 - abs(j - (nfing - 1) / 2) / nfing))
                    fb = Blade(Af, ef, cf, n, fl_, lead=(0.012 * k, 0.006 * k), trail=(0.06 * k, 0.02 * k),
                               th=(0.012 * k, 0.007 * k), gs=1.3)
                    fm = '%s_f%d%s' % (tag, j, 'L' if side > 0 else 'R')
                    mats[fm] = Material(wing_paint(fb, S['col'], 'o', 3, 0.0, 0.0), spec=0.05, brush=0.05)
                    add(fb, fm, 0.0)
    # ---- tail
    spread = 1.0 + P['tailsp']
    tl = S['tail_len'] * k
    ta = L.p(0, 0.0, -bz * 0.85)
    tdir = F.R @ norm(v3(0, 0.05 + 0.25 * P['tailup'] - 0.04, -1))
    tc = F.R @ v3(1, 0, 0)
    tn = norm(np.cross(tc, tdir))
    tn = tn if tn[1] > 0 else -tn
    tail = Blade(ta, tdir, tc, tn, tl, lead=(S['tail_w'][0] * k, S['tail_w'][1] * k * spread),
                 trail=(S['tail_w'][0] * k, S['tail_w'][1] * k * spread), th=(0.016 * k, 0.010 * k),
                 teeth=(7, 0.03 * k, 0.5), notch=S['tail_notch'] * k, gs=1.4)
    mats[tag + '_tail'] = Material(tail_paint(tail, S), spec=0.05, brush=0.05)
    add(tail, tag + '_tail', 0.0)
    # ---- body
    Rb = rot_x(-0.07)
    L.ell((0, 0, 0), (bx, by, bz), tag + '_body', 0.0, Rb)
    L.ell((0, -0.01, bz * 0.45), (bx * 0.97, by * 1.0, bz * 0.55), tag + '_body', 0.10)
    L.ell((0, 0.0, -bz * 0.62), (bx * 0.62, by * 0.62, bz * 0.50), tag + '_body', 0.08, Rb)
    # ---- neck and head
    nx, dip = P['neckx'], P['dip']
    base = v3(0, by * 0.30, bz * 0.72)
    H = v3(0, by * 0.95 + 0.02 - 0.08 * dip + 0.0, bz * 0.72 + S['neck'] * (0.55 + 0.45 * nx) + S['neck_ext'] * nx)
    if S['pouch'] == 'pelican':
        H = v3(0, by * 0.95 + 0.04 - 0.10 * dip, bz * 0.70 + S['neck'] * (0.5 + 0.4 * nx))
    mid = (base + H) / 2 + v3(0, 0.05 * (1 - dip), -0.02)
    L.cap(base, mid, S['neck_th'] * 1.15, S['neck_th'], tag + '_neck', 0.04)
    L.cap(mid, H, S['neck_th'], S['neck_th'] * 0.85, tag + '_neck', 0.04)
    hr = S['headr']
    L.ell(H, hr, tag + '_head', 0.04)
    if S['ruff']:
        L.ell(base + v3(0, 0.0, -0.03), (0.13, 0.08, 0.10), tag + '_ruff', 0.05)
    # beak
    bd = norm(v3(0, -0.16 - 0.18 * dip - 0.08 * P['strike'], 1.0))
    b0 = H + v3(0, -0.005, hr[2] * 0.75)
    b1 = b0 + bd * S['beak_len']
    open_ = P['openb']
    bm = S['beak_mat']
    if S['pouch'] == 'pelican':
        L.cap(b0, b1, S['beak_d'] * 0.95, S['beak_d'] * 0.35, bm, 0.0)
        low = b0 + v3(0, -0.01, 0) + norm(bd + v3(0, -open_ * 0.5, 0)) * 0.0
        L.cap(b0 + v3(0, -0.035, 0), b0 + v3(0, -0.035, 0) + norm(bd + v3(0, -0.25 * open_, 0)) * S['beak_len'] * 0.97,
              S['beak_d'] * 0.55, S['beak_d'] * 0.22, bm, 0.0)
        L.cap(b1, b1 + bd * 0.03 + v3(0, -0.035, 0), 0.016, 0.007, 'beak', 0.0)
        pf = P['pouch']
        pc = b0 + bd * S['beak_len'] * 0.46 + v3(0, -0.075 - 0.05 * pf, 0)
        L.ell(pc, (0.050 + 0.030 * pf, 0.060 + 0.075 * pf, S['beak_len'] * 0.50), tag + '_pouch', 0.02)
        if P['kick'] > 0 or pf > 0.3:
            kk = max(P['kick'], pf)
            a = pc + v3(0.05, -0.02, 0.0)
            L.cap(a + v3(0, 0, 0.02), a + v3(0.04, -0.12 - 0.03 * kk, 0.14 + 0.06 * kk), 0.040, 0.034, 'oil_dk', 0.0)
            L.ell(a + v3(0.05, -0.15 - 0.03 * kk, 0.18 + 0.06 * kk), (0.04, 0.045, 0.075), 'boot', 0.0,
                  basis_from(v3(0, -0.2, 1), v3(0, 1, 0)))
    else:
        bw = S['beak_d']
        L.cap(b0, b1, bw, bw * 0.30, bm, 0.0)
        low_d = norm(bd + v3(0, -open_ * 0.55, 0))
        L.cap(b0 + v3(0, -bw * 0.55, 0), b0 + v3(0, -bw * 0.55, 0) + low_d * S['beak_len'] * 0.88, bw * 0.62, bw * 0.20,
              bm, 0.0)
        hk = S['hook']
        L.cap(b1 - bd * 0.012, b1 + bd * hk * 0.5 + v3(0, -hk * 1.5, 0), bw * 0.34, bw * 0.10, S['tip_mat'] or bm, 0.0)
        if S['eye_ring']:
            # notch in the beak where something fought back
            L.sph(b0 + bd * S['beak_len'] * 0.62 + v3(0, bw * 0.18, 0), 0.012, 'eye_ring', 0.0)
    for sx in (-1, 1):
        L.sph(H + v3(sx * hr[0] * 0.80, hr[1] * 0.25, hr[2] * 0.22), 0.016, 'eye_ring' if S['eye_ring'] else tag + '_head', 0.0)
        L.sph(H + v3(sx * hr[0] * 0.90, hr[1] * 0.27, hr[2] * 0.25), 0.012, 'eye', 0.0)
    if S['pouch'] == 'frigate':
        infl = 0.35 + 0.9 * P['pouch']
        L.ell(H + v3(0, -0.075 * infl - 0.02, hr[2] * 0.35), (0.062 * infl + 0.01, 0.085 * infl, 0.07 * infl + 0.01), 'red', 0.04)
    # ---- legs (tucked back, dangle when `legs`)
    lg = P['legs']
    for sx in (-1, 1):
        hip = v3(sx * bx * 0.45, -by * 0.7, bz * 0.05)
        knee = hip + v3(sx * 0.01, -0.06 - 0.06 * lg, -0.10 + 0.20 * lg)
        foot = hip + v3(sx * 0.015, -0.10 - 0.20 * lg, -0.30 + 0.40 * lg)
        L.cap(hip, knee, 0.026, 0.020, 'leg', 0.02)
        L.cap(knee, foot, 0.018, 0.014, 'leg', 0.0)
        fd = norm(v3(0, -0.4 * lg, 1.0))
        for j in (-1, 0, 1):
            L.cap(foot, foot + fd * 0.07 + v3(j * 0.025, 0, 0), 0.010, 0.006, 'leg', 0.0)
        if lg > 0.3:
            for j in (-1, 1):
                L.cap(foot + fd * 0.07 + v3(j * 0.025, 0, 0), foot + fd * 0.085 + v3(j * 0.03, -0.025, 0), 0.006, 0.002, 'beak_ink', 0.0)
    # ---- harness: girth rings, breast strap, saddle pad, trailing cords
    gz = bz * 0.12
    L.add(Torus(L.p(0, 0, gz), L.d(0, 0, 1), (bx * 1.0 + 0.012) * k, 0.014 * k), 'tar', 0.0)
    L.add(Torus(L.p(0, 0, gz - 0.07), L.d(0, 0, 1), (bx * 1.0 + 0.010) * k, 0.010 * k), 'cord', 0.0)
    L.cap((0, by * 0.7, bz * 0.55), (0, by * 0.55, gz), 0.016, 0.016, 'tar', 0.0)
    sy, sz = S['saddle']
    L.ell((0, by * 0.88, sz * 0.5), (bx * 0.85, 0.035, 0.17), 'leather', 0.02)
    for sx in (-1, 1):
        L.cap((sx * bx * 0.92, by * 0.12, gz), (sx * bx * 0.4, by * 0.88, gz), 0.012, 0.012, 'tar', 0.0)
        L.sph((sx * (bx + 0.014), -by * 0.10, gz + 0.0), 0.024, 'bone', 0.0)
    tcw = (P['tell'] * 6.283)
    for j, sx in enumerate((-1, 1)):
        a = v3(sx * 0.05, by * 0.2, -bz * 0.5)
        flut = np.sin(tcw + j * 2.0) * 0.03
        b_ = a + v3(sx * 0.07 + flut, -0.10, -0.20)
        c_ = b_ + v3(sx * 0.05 - flut, -0.04, -0.14)
        L.cap(a, b_, 0.008, 0.007, 'cord' if j else 'tar', 0.0)
        L.cap(b_, c_, 0.007, 0.005, 'cord' if j else 'tar', 0.0)
    # ---- materials for body zones
    mats.update(bird_mats(F, S, tag))
    out = dict(head=F.t + F.R @ (H * k), beak=F.t + F.R @ (b1 * k), saddle=F.t + F.R @ (v3(0, by + 0.0, sz) * k),
               tips=tips, tail=ta, H=H, bd=bd)
    return out


def tail_paint(tail, S):
    c0 = np.array(S['tailc'])
    c1 = np.array(S['col']['tip'] if S['col'].get('tip') is not None and S['tailc'] is INK else S['tailc'])

    def fn(p, n):
        a, b, w, t, ld, tr, th = tail.coords(p)
        c = _arr(c0, len(p)) * (0.92 + 0.16 * fbm(p, 30.0, 2))[:, None]
        f = (b / np.maximum(tr, 1e-3) * 3.5) % 1.0
        c[(f < 0.06) | (f > 0.95)] *= 0.82
        return np.clip(c, 0, 1)
    return fn


def bird_mats(F, S, tag):
    back, belly, head, neckc = (np.array(S[x]) for x in ('back', 'belly', 'head', 'neckc'))
    ruff = np.array(S['ruff']) if S['ruff'] is not None else None
    bz = S['body'][2]
    k = S['k']

    def body_fn(p, n):
        q = F.inv(p) / k
        N = len(p)
        c = _arr(belly, N)
        top = q[:, 1] > (0.015 + 0.02 * np.sin(q[:, 2] * 18))
        shade = 0.5 + 0.5 * np.clip((q[:, 1] + 0.06) / 0.18, 0, 1)
        c[top] = back[None, :]
        c = c * (0.94 + 0.12 * fbm(p, 26.0, 2))[:, None]
        # streaky wing-fold lines on the back
        st = ((q[:, 0] * 22.0 + np.sin(q[:, 2] * 7)) % 1.0) < 0.10
        c[top & st] *= 0.86
        nk = q[:, 2] > bz * 0.74
        c[nk] = neckc[None, :]
        return np.clip(c, 0, 1)

    def head_fn(p, n):
        q = F.inv(p) / k
        c = _arr(head, len(p)) * (0.96 + 0.08 * fbm(p, 30.0, 2))[:, None]
        if S['bare_head']:
            wr = fbm(p + 2.2, 50.0, 2) > 0.58
            c[wr] = c[wr] * 0.82
        return np.clip(c, 0, 1)

    def neck_fn(p, n):
        q = F.inv(p) / k
        c = _arr(neckc, len(p)) * (0.95 + 0.1 * fbm(p, 30.0, 2))[:, None]
        if S['col'] and S['back'] is not None and not S['bare_head']:
            top = q[:, 1] > bz * 0.36
            c[top & (q[:, 2] < bz * 0.9)] = back[None, :] * 1.0 if S['neckc'] is S['back'] else c[top & (q[:, 2] < bz * 0.9)]
        return np.clip(c, 0, 1)

    out = {
        tag + '_body': Material(body_fn, spec=0.45 if S.get('gloss') else 0.05, gloss=34, brush=0.05),
        tag + '_head': Material(head_fn, spec=0.45 if S.get('gloss') else 0.05, gloss=34, brush=0.05),
        tag + '_neck': Material(neck_fn, spec=0.05, brush=0.05),
        tag + '_cov': Material(tone(S['col']['covert'], 0.92), spec=0.05, brush=0.05),
        tag + '_ruff': Material(noisy(ruff if ruff is not None else GUANO, 0.10, 44.0), spec=0.03, brush=0.08),
        tag + '_pouch': Material(pouch_albedo(S), spec=0.2, gloss=20, sss=0.3, brush=0.04),
    }
    return out


def pouch_albedo(S):
    base = np.array(mix(ORANGE, GUANO, 0.55))

    def fn(p, n):
        c = _arr(base, len(p))
        v = np.abs(vnoise(p * np.array([1.0, 2.2, 1.0]) + 3.3, 14.0) - 0.5) < 0.04
        c[v] = c[v] * 0.70 + np.array(FRIGATE)[None, :] * 0.18
        return c
    return fn



# ------------------------------------------------------------------ rider

def bp(S, x, y, z):
    """Bird-local (scaled) point in true metres."""
    return v3(x, y, z) * S['k']


def rider_cfg(**kw):
    c = dict(h=0.80, b=0.92, girth=1.0, lean=0.62, head='mask', hair=None, skin=SKIN_W, sash=True, scarf=False,
             hands=None, tails=True, collar=True, coat='oil', mask_col='bone', goggles=False, tail_len=0.42)
    c.update(kw)
    return c


JOINTS = ('pelvis', 'chest', 'neck', 'head', 'sh_r', 'el_r', 'wr_r', 'sh_l', 'el_l', 'wr_l',
          'hip_r', 'kn_r', 'an_r', 'hip_l', 'kn_l', 'an_l')


def rider_joints(P, S, R):
    """Seated, hunched rider joints in bird-local coordinates (true metres)."""
    h, b = R['h'], R['b']
    k = S['k']
    Q = base_pose(h, b)
    sy, sz = S['saddle']
    bx, by, bz = S['body']
    pel_t = v3(R.get('x', 0.0), (by + 0.06) * k + 0.02, sz * k + R.get('z', 0.0))
    d = pel_t - Q['pelvis']
    rig.shift(Q, JOINTS, d)
    lean = R['lean'] + P['lean']
    rig.lean(Q, fwd=lean)
    Q['head_pitch'] = np.radians(-4) + 0.25 * lean + P['look'] * 0.0
    Q['head_yaw'] = np.radians(-14) + P['look']
    for s in ('r', 'l'):
        sx = -1 if s == 'r' else 1
        an = pel_t + v3(sx * (bx * k + 0.045), -0.27 * h - 0.0, 0.07)
        rig.place_leg(Q, s, an, l1=0.43 * h, l2=0.42 * h, pole=(sx * 0.5, 0.6, 1.0))
        Q['foot_%s_yaw' % s] = np.radians(sx * 5)
    # reins: both hands at the neck base, elbows tucked
    for s in ('r', 'l'):
        sx = -1 if s == 'r' else 1
        tgt = v3(sx * 0.07 * k, (by + 0.11) * k, bz * 0.62 * k)
        rig.place_arm(Q, s, tgt, (sx, -0.5, -0.2), l1=0.27 * h, l2=0.26 * h)
    Q['item_r'] = None
    Q['item_l'] = None
    if R['hands']:
        R['hands'](P, Q, S)
    return Q


def world_rider(P, S, F, R):
    Q = rider_joints(P, S, R)
    W = dict(Q)
    for key in JOINTS:
        W[key] = F.pt(Q[key])
    # head orientation: carry the bird's frame into yaw / pitch (roll cannot be represented)
    Rh = F.R @ rot_y(Q['head_yaw']) @ rot_x(-Q['head_pitch'])
    f = Rh @ v3(0, 0, 1)
    W['head_yaw'] = float(np.arctan2(f[0], f[2]))
    W['head_pitch'] = float(np.arcsin(np.clip(f[1], -1, 1)))
    W['breathe'] = 0.0
    W['tell'] = P['tell']
    W['_back'] = F.R @ v3(0, 0, -1)
    W['_side'] = F.R @ v3(1, 0, 0)
    rf = P['rfall']
    if rf > 0:
        pv = W['pelvis'].copy()
        tgt = v3(-0.10 * rf, 0.0, -0.12 * rf)
        Rz = rot_z(-1.45 * rf) @ rot_x(0.35 * rf)
        for key in JOINTS:
            W[key] = pv + Rz @ (W[key] - pv) + tgt * 1.0
        lift = pv[1] * (1 - rf) + 0.15 * rf - pv[1]
        for key in JOINTS:
            W[key] = W[key] + v3(0, lift, 0)
        W['head_pitch'] += 0.4 * rf
        # limbs flail
        for s in ('r', 'l'):
            sx = -1 if s == 'r' else 1
            W['wr_' + s] = W['wr_' + s] + v3(sx * 0.15, 0.25, 0.1) * rf * 0.6
    return W


def rider_body(W, add, R, S=None):
    """Seated rider from world-space joints W: legs, oriented torso, flight coat, arms, hands, head gear."""
    h, b, g = R['h'], R['b'], R['girth']
    coat = R['coat']
    SK = R.get('skin_mat', 'skin')
    pel, ch, nk, H = W['pelvis'], W['chest'], W['neck'], W['head']
    for s in ('r', 'l'):
        hip, kn, an = W['hip_' + s], W['kn_' + s], W['an_' + s]
        add(Capsule(hip, kn, 0.068 * b, 0.052 * b), 'oil_dk', 0.02)
        add(Capsule(kn, an, 0.050 * b, 0.040 * b), 'boot', 0.0)
        fd = rot_y(W['foot_%s_yaw' % s]) @ v3(0, 0, 1)
        add(Capsule(an + v3(0, -0.03, -0.02), an + fd * 0.13 * h + v3(0, -0.05, 0), 0.045 * b, 0.034 * b), 'boot', 0.03)
    ax = norm(nk - pel)
    Rt = basis_from(ax, v3(0, 0, 1))
    add(Ellipsoid(pel + ax * 0.12 * h, (0.14 * b * g ** 0.5, 0.15 * h, 0.10 * b * g), Rt), coat, 0.0)
    add(Ellipsoid(ch, (0.17 * b * g ** 0.5, 0.20 * h, 0.115 * b * g), Rt), coat, 0.06)
    # belt / harness
    add(Cylinder(pel + ax * 0.075 * h, pel + ax * 0.115 * h, 0.14 * b, 0.01), 'tar', 0.0)
    if R['sash']:
        a = ch + Rt @ v3(0.15 * b, 0.12 * h, 0.07) * 1.0
        c = pel + Rt @ v3(-0.14 * b, 0.02 * h, 0.06)
        add(Capsule(a, c, 0.017, 0.017), 'cord', 0.0)
    if R['collar']:
        add(Cylinder(nk + v3(0, -0.04, 0), nk + v3(0, 0.035, 0), 0.068 * b, 0.02), coat, 0.0)
    # bone cross-harness
    add(Capsule(ch + Rt @ v3(-0.12 * b, 0.12 * h, 0.08), ch + Rt @ v3(0.12 * b, -0.10 * h, 0.09), 0.012, 0.012), 'bone', 0.0)
    for s in ('r', 'l'):
        sh, el, wr = W['sh_' + s], W['el_' + s], W['wr_' + s]
        sx = -1 if s == 'r' else 1
        add(Capsule(sh + v3(-sx * 0.02, -0.03, 0), el, 0.056 * b, 0.048 * b), coat, 0.03)
        add(Capsule(el, wr, 0.048 * b, 0.040 * b), coat, 0.02)
        d = norm(wr - el)
        add(Ellipsoid(wr + d * 0.045, (0.034 * b, 0.045 * b, 0.030 * b), basis_from(d, (0, 0, 1))), 'glove', 0.01)
    # coat tails streaming back
    if R['tails']:
        tell = W.get('tell', 0.0)
        flut = np.sin(tell * 6.283) * 0.5
        back = W['_back']
        sidev = W['_side']
        up = norm(np.cross(sidev, back))
        up = up if up[1] > 0 else -up
        for sx, off in ((-1, 0.0), (1, 0.0)):
            A = pel + ax * 0.05 * h + sidev * sx * 0.07 * b + back * 0.04
            e = norm(back + v3(0, -0.28 - 0.15 * flut, 0) + sidev * sx * (0.12 + 0.10 * flut))
            c = norm(np.cross(up, e))
            c = c if c @ sidev * sx > 0 else -c
            n = norm(np.cross(e, c))
            n = n if n[1] > 0 else -n
            add(Blade(A, e, c, n, R['tail_len'] * h / 0.8, lead=(0.0, 0.0), trail=(0.085 * b, 0.13 * b),
                      th=(0.012, 0.009), teeth=(3, 0.04, 0.6), gs=1.6), coat, 0.0)
    # neck and head
    add(Capsule(nk + v3(0, -0.02, 0), H + v3(0, -0.07 * h, -0.01), 0.04 * b), SK, 0.0)
    Rh = head_R(W)
    add(Ellipsoid(H, (0.078 * h, 0.097 * h, 0.088 * h), Rh), SK, 0.0)
    add(Ellipsoid(H + Rh @ v3(0, -0.05, 0.022) * h, (0.056 * h, 0.05 * h, 0.062 * h), Rh), SK, 0.03)
    add(Capsule(H + Rh @ v3(0, 0.0, 0.078) * h, H + Rh @ v3(0, -0.028, 0.092) * h, 0.010, 0.013), SK, 0.01)
    hd = R['head']
    if hd == 'mask':
        # skull beak-mask, worn pushed up so the mouth shows: cranium, long bone beak with orange tip, cord brow band
        add(Ellipsoid(H + Rh @ v3(0, 0.040, -0.012) * h, (0.088 * h, 0.075 * h, 0.098 * h), Rh), 'oil_dk', 0.0)
        add(Ellipsoid(H + Rh @ v3(0, 0.022, 0.050) * h, (0.074 * h, 0.060 * h, 0.060 * h), Rh), 'bone', 0.02)
        a = H + Rh @ v3(0, 0.0, 0.085) * h
        bb = H + Rh @ v3(0, -0.020, 0.24) * h
        add(Capsule(a, bb, 0.034 * h, 0.009 * h), 'bone', 0.02)
        add(Capsule(bb - (bb - a) * 0.12, bb + Rh @ v3(0, -0.012, 0.03) * h, 0.011 * h, 0.006 * h), 'beak', 0.0)
        for sx in (-1, 1):
            add(Sphere(H + Rh @ v3(sx * 0.050, 0.020, 0.085) * h, 0.019 * h), 'beak_ink', 0.0)
        add(Torus(H + Rh @ v3(0, 0.02, -0.01) * h, Rh[:, 1], 0.085 * h, 0.006 * h), 'cord', 0.0)
    elif hd == 'hood':
        add(hood_shell(W, size=1.05), coat, 0.0)
    elif hd == 'scarf':
        hair(W, add, 'hair', 'short')
        add(Torus(nk + v3(0, 0.0, 0.0), v3(0, 1, 0.2), 0.058 * b, 0.026 * b), 'cord', 0.0)
        a = nk + v3(-0.04 * b, -0.01, -0.03)
        back = W['_back']
        add(Capsule(a, a + back * 0.20 + v3(0, 0.02, 0.0), 0.016, 0.010), 'cord', 0.0)
    elif hd == 'cap':
        add(Ellipsoid(H + Rh @ v3(0, 0.055, -0.01) * h, (0.088 * h, 0.05 * h, 0.094 * h), Rh), 'oil_dk', 0.01)
        add(Cylinder(H + Rh @ v3(0, 0.03, 0.05) * h, H + Rh @ v3(0, 0.038, 0.07) * h, 0.07 * h, 0.004), 'oil_dk', 0.0)
    elif hd == 'hair':
        hair(W, add, 'hair', R.get('hair_style', 'short'))
    if R['goggles']:
        for sx in (-1, 1):
            add(Torus(H + Rh @ v3(sx * 0.036, 0.012, 0.074) * h, Rh[:, 2], 0.018 * h, 0.005), 'brass', 0.0)


# ------------------------------------------------------------------ feathers, swirl, heap, finish

def _feather(add, c, yaw, tilt, size, mat, roll=0.0):
    R = rot_y(yaw) @ rot_z(tilt) @ rot_x(roll)
    add(Ellipsoid(c, (size, size * 0.07, size * 0.28), R), mat, 0.0)
    add(Capsule(c - R[:, 0] * size * 0.9, c + R[:, 0] * size * 0.9, size * 0.03, size * 0.015), mat, 0.0)


def drift_feathers(add, center, amount, S, seed=3, n=9, spread=0.9, phase=0.0):
    if amount <= 0:
        return
    rng = np.random.default_rng(seed)
    for i in range(n):
        ang = rng.uniform(0, 6.28) + phase * 0.8
        r = spread * rng.uniform(0.35, 1.0) * (0.4 + 0.6 * amount)
        y = rng.uniform(-0.2, 0.9) + 0.25 * amount * rng.uniform(-1, 1)
        c = center + v3(np.cos(ang) * r, y, np.sin(ang) * r * 0.8)
        m = ('feather_s', 'feather_g', 'feather_i')[int(rng.integers(0, 3))]
        _feather(add, c, rng.uniform(0, 6.28), rng.uniform(-0.8, 0.8), 0.045 * rng.uniform(0.7, 1.2), m, rng.uniform(-1, 1))


def swirl_feathers(add, center, amount, phase, n=10, r0=0.55, height=1.1, cord=True):
    """A helix of feathers wheeling around `center` (cast / cry)."""
    if amount <= 0:
        return
    for i in range(n):
        t = i / n
        th = phase * 6.283 + t * 6.283 * 1.4
        r = r0 * (0.75 + 0.5 * t) * (0.4 + 0.6 * amount)
        c = center + v3(np.cos(th) * r, -0.2 + height * t, np.sin(th) * r * 0.8)
        m = 'cord' if (i == 3 and cord) else ('feather_g', 'feather_s', 'feather_i')[i % 3]
        _feather(add, c, -th, 0.4, 0.05 + 0.02 * t, m, 0.5)


def feather_heap(add, mats, S, amount, seed=11):
    """End state: a heap of grey feathers on the ground with harness bones and one orange cord."""
    if amount <= 0:
        return
    rng = np.random.default_rng(seed)
    a = amount
    mats['h_a'] = Material(noisy(S['back'], 0.10, 40.0), spec=0.05, brush=0.06)
    mats['h_b'] = Material(noisy(S['belly'], 0.06, 40.0), spec=0.04, brush=0.06)
    mats['h_c'] = Material(noisy(S['col'].get('flight') or SLATE, 0.10, 40.0), spec=0.05, brush=0.06)
    k = S['k']
    rad = (0.20 + 0.26 * a) * (0.7 + 0.45 * k)
    add(Ellipsoid(v3(0, 0.02 * a, 0.02), (rad * 0.66, 0.11 * a * (0.8 + 0.3 * k), rad * 0.56)), 'h_a', 0.0)
    for i in range(int(10 + 30 * a)):
        ang = rng.uniform(0, 6.283)
        r = rad * (rng.uniform(0.05, 1.0) ** 0.7)
        y = max(0.02, 0.11 * a * (1 - (r / rad) ** 2) + rng.uniform(0, 0.03))
        c = v3(np.cos(ang) * r, y, np.sin(ang) * r * 0.78 + 0.02)
        m = ('h_b', 'h_a', 'h_c', 'h_b', 'h_a', 'h_b')[i % 6]
        sz = 0.10 * rng.uniform(0.7, 1.3) * (0.6 + 0.5 * k)
        R = rot_y(rng.uniform(0, 6.28)) @ rot_z(rng.uniform(-0.55, 0.55)) @ rot_x(rng.uniform(-0.3, 0.3))
        add(Ellipsoid(c, (sz, 0.020, sz * 0.34), R), m, 0.0)
    # a scrap of the rider's flight coat
    add(Ellipsoid(v3(0.32 * a, 0.02, 0.22 * a), (0.10, 0.018, 0.07), rot_y(0.6)), 'oil', 0.0)
    # harness: a loop of tar strap round the mound, bone toggles, loose buckle
    rr = rad * 0.74
    for j in range(10):
        a0, a1 = 0.5 + j * 0.55, 0.5 + (j + 1) * 0.55
        add(Capsule(v3(np.cos(a0) * rr, 0.025, np.sin(a0) * rr * 0.8 + 0.02), v3(np.cos(a1) * rr, 0.025, np.sin(a1) * rr * 0.8 + 0.02),
                    0.020, 0.020), 'tar', 0.0)
    for j in range(3):
        ang = 1.0 + j * 2.0
        c0 = v3(np.cos(ang) * rr, 0.045, np.sin(ang) * rr * 0.8 + 0.02)
        add(Capsule(c0, c0 + v3(0.07, 0.0, 0.03), 0.022, 0.022), 'bone', 0.0)
    # the one orange cord
    pts = [v3(-0.05, 0.10, 0.12), v3(-0.30, 0.04, 0.34), v3(-0.52, 0.025, 0.34), v3(-0.70, 0.022, 0.46)]
    for u, v in zip(pts[:-1], pts[1:]):
        add(Capsule(u * a, v * a, 0.022, 0.022), 'cord', 0.0)


def gyre_finish(P, parts, mats, lights=(), S=None, ground=True):
    """Apply the melt (collapse into the heap), the feather heap and drifting feathers, then kit finish."""
    melt = P.get('melt', 0.0)
    if melt > 0.01:
        parts[:] = squash_parts(parts, sy=1 - 0.88 * melt, sxz=1 + 0.30 * melt)
    if melt >= 0.97:
        parts.clear()
    if P.get('end', 0) > 0 and S is not None:
        hp = []
        feather_heap(lambda prim, mat, k=0.0: hp.append(Part(prim, mat, k)), mats, S, P['end'])
        parts.extend(transform_parts(hp, t=(0.0, 0.0, -0.22)))
    P2 = dict(P)
    P2['end'] = 0.0
    P2['sink'] = 1e-4 if (P.get('melt', 0) > 0 or P.get('rfall', 0) > 0.5) else 0.0     # ground clip while it lands
    return _kit_finish(P2, FACTION, parts, mats, lights, end_style='none')


def flier_build(P, S, R, extra=None, y0=0.52, tag='b', rider=True):
    """Standard flier: bird + seated rider + unit extras. extra(ctx) may add props and return lights."""
    parts, add = new_parts()
    F = bird_frame(P, y0=y0 + 0.15)
    W = world_rider(P, S, F, R) if (rider and R is not None) else None
    mats = gyre_mats(W if W is not None else P, **((R or {}).get('mats') or {}))
    if R is not None:
        mats['skin'] = Material(face_albedo(W, R['skin'], R.get('hair') or _hex('#3f3730'), eyes=_hex('#241c19'),
                                            lips=_hex('#9a5a4c'), beard=R.get('beard')),
                                spec=0.06, gloss=12, sss=0.5, brush=0.02) if W is not None else mats['skin']
        mats['hair'] = Material(R.get('hair') or _hex('#3f3730'), spec=0.2, gloss=16, brush=0.1)
    info = bird(add, mats, F, S, P, tag)
    if W is not None:
        rider_body(W, add, R, S)
    ctx = dict(add=add, mats=mats, F=F, S=S, P=P, W=W, info=info, R=R, parts=parts)
    lights = []
    if extra:
        lights = extra(ctx) or []
    cen = F.t
    if P['scatter'] > 0:
        drift_feathers(add, cen, P['scatter'], S, n=int(6 + 8 * P['scatter']), phase=P['tell'])
    if P['swirl'] > 0:
        swirl_feathers(add, cen + v3(0, 0.3, 0), P['swirl'], P['tell'])
    return gyre_finish(P, parts, mats, lights, S)


# ------------------------------------------------------------------ flier animation rows

def _flap(ph, a=0.45, c=0.30, lag=1.0, a2=None):
    fl = c + a * np.sin(ph)
    fl2 = (a2 if a2 is not None else a) * 0.9 * np.sin(ph - lag)
    return fl, fl2


def fly_rows(base, tweak=None, stoop=False, atk=None, idle_amp=0.60, strike_kind='beak'):
    """(ROWS, frames) for a flier. base() returns the neutral flight pose (fly_pose(...)). `tweak(rows)` may
    post-process the dict. Attack = anticipation (wings fold), dive + strike on frame 2, climb-out."""
    def frames():
        B = base
        rows = {}
        idle = []
        for i in range(4):
            P = B()
            ph = i / 4 * 2 * np.pi
            fl, fl2 = _flap(ph, idle_amp, P['fl'], 1.0)
            P['fl'], P['fl2'] = fl, fl2 + P['fl2']
            P['bob'] = 0.03 * np.sin(ph + 0.6)
            P['tell'] = i / 4
            P['ruffle'] = 1.0 if i == 2 else 0.0
            P['tailup'] = 0.25 * np.sin(ph)
            idle.append((P, {}))
        rows['idle'] = idle
        mv = []
        for i in range(4):
            P = B()
            ph = i / 4 * 2 * np.pi
            fl, fl2 = _flap(ph, 0.75, P['fl'], 1.2)
            P['fl'], P['fl2'] = fl, fl2
            P['bob'] = 0.045 * np.sin(ph + 1.0)
            P['pitch'] += 0.10
            P['dz'] = [0.0, 0.05, 0.1, 0.05][i]
            P['tell'] = i / 4
            P['tailup'] = 0.3 * np.sin(ph)
            P['legs'] = 0.0
            mv.append((P, {}))
        rows['move'] = mv
        a = atk or {}
        ak = []
        spec = [
            dict(fold=0.55, pitch=-0.20, fl=0.7, fl2=0.5, dz=-0.16, dy=0.20, strike=0.0, neckx=-0.3, dip=0.0),
            dict(fold=0.95, pitch=0.42, fl=-0.05, fl2=-0.2, dz=-0.05, dy=0.34, strike=0.3, neckx=0.6, dip=0.6),
            dict(fold=0.15, pitch=0.30, fl=0.7, fl2=0.2, dz=0.06, dy=0.30, strike=1.0, neckx=1.0, dip=0.9, openb=0.8,
                 legs=0.8, fx=1.0),
            dict(fold=0.2, pitch=-0.28, fl=0.8, fl2=0.7, dz=0.14, dy=0.24, strike=0.2, neckx=0.2, dip=0.0, legs=0.4),
        ]
        for i in range(4):
            P = B()
            sp = dict(spec[i])
            sp.update({kk: vv[i] for kk, vv in a.items() if isinstance(vv, (list, tuple))})
            for kk, vv in sp.items():
                P[kk] = P[kk] + vv if kk in ('dz', 'dy', 'pitch') else vv
            P['tell'] = i / 4
            P['lean'] = [0.0, 0.2, 0.35, 0.0][i] if not stoop else [0.0, 0.1, 0.25, 0.0][i]
            ak.append((P, {}))
        rows['attack'] = ak
        h0 = B()
        h0.update(fl=1.0, fl2=0.8, pitch=-0.32, dz=-0.14, dy=0.06, openb=0.9, scatter=0.9, ruffle=1.0, lean=-0.2,
                  neckx=-0.2, fold=0.0, tell=0.3)
        h1 = B()
        h1.update(fl=0.7, fl2=0.3, pitch=-0.12, dz=-0.05, scatter=0.5, tell=0.6, lean=-0.1)
        rows['hit'] = [(h0, dict(exposure=1.25, flash=0.22)), (h1, {})]
        d = []
        specs = [
            dict(fl=0.9, fl2=0.7, pitch=-0.25, dz=-0.10, dy=0.04, openb=1.0, scatter=0.5, lean=-0.3, fold=0.0),
            dict(fl=-0.7, fl2=-0.2, pitch=0.55, roll=0.85, dz=-0.06, dy=0.05, fold=0.45, scatter=0.9, rfall=0.45,
                 lean=0.2, legs=0.7),
            dict(fl=-0.9, fl2=-0.5, pitch=0.80, roll=0.9, dz=-0.15, dy=-0.12, fold=0.2, scatter=1.0, rfall=1.0,
                 melt=0.30, legs=0.2),
            dict(fl=-0.9, fl2=-0.5, roll=1.5, dy=-0.4, rfall=1.0, melt=1.0, end=1.0),
        ]
        for i in range(4):
            P = B()
            P.update(specs[i])
            P['tell'] = i / 4
            d.append((P, GROUND_OVER if i >= 2 else {}))
        rows['death'] = d
        cs = []
        for i in range(3):
            P = B()
            P['fl'] = [0.4, 1.0, 0.6][i]
            P['fl2'] = [0.2, 0.9, 0.4][i]
            P['pitch'] += [-0.05, -0.22, 0.0][i]
            P['openb'] = [0.4, 1.0, 0.5][i]
            P['neckx'] = [0.2, 1.0, 0.4][i]
            P['cast_glow'] = [0.5, 1.0, 0.4][i]
            P['glow'] = [1.2, 1.8, 1.2][i]
            P['swirl'] = [0.4, 1.0, 0.7][i]
            P['arm'] = [0.4, 1.0, 0.6][i]
            P['bob'] = [0.0, 0.05, 0.02][i]
            P['tell'] = [0.0, 0.3, 0.6][i]
            P['lean'] = [-0.05, -0.2, 0.0][i]
            cs.append((P, {}))
        rows['cast'] = cs
        if tweak:
            tweak(rows)
        return rows
    return KIT_ROWS, frames


# ------------------------------------------------------------------ ground roost-folk helpers

HEAP_S = dict(k=1.0, back=SLATE, belly=GUANO, col=dict(flight=mix(SLATE, INK, 0.3)))

GROUND_DEFAULTS = dict(melt=0.0, flock=0.0, orbit=0.0, flap=0.0, tellp=0.0)


def ground_pose(P):
    """Add the Gyre scalars to a kit pose (melt = collapse into the end heap, flock/orbit = birds in play)."""
    for k, v in GROUND_DEFAULTS.items():
        P.setdefault(k, v)
    return P


def mini_bird(add, c, yaw=0.0, flap=0.0, k=0.22, pitch=0.0, back='feather_s', belly='feather_g', beak='beak',
              span=1.0, spot=True):
    """A small gull/crow in flight (flocks, orbiting crows). Eight parts, world space, centre c."""
    R = rot_y(yaw) @ rot_x(pitch)
    p = lambda q: c + R @ (v3(*q) * k)
    add(Ellipsoid(p((0, 0, 0)), (0.17 * k, 0.16 * k, 0.42 * k), R @ rot_x(-0.08)), belly, 0.0)
    add(Ellipsoid(p((0, 0.04, -0.05)), (0.15 * k, 0.12 * k, 0.34 * k), R @ rot_x(-0.08)), back, 0.06)
    add(Sphere(p((0, 0.12, 0.50)), 0.115 * k), belly if back != 'feather_i' else back, 0.04)
    add(Capsule(p((0, 0.10, 0.58)), p((0, 0.05, 0.84)), 0.05 * k, 0.015 * k), beak, 0.0)
    add(Capsule(p((0, 0.01, -0.34)), p((0, 0.02, -0.80)), 0.07 * k, 0.12 * k), belly if back != 'feather_i' else back, 0.0)
    for s in (-1, 1):
        f = 0.35 + flap * 0.75
        e = norm(v3(s * np.cos(f), np.sin(f), -0.30))
        ch = R @ v3(0, 0, -1)
        e = R @ e
        cc = norm(ch - e * (ch @ e))
        n = norm(np.cross(e, cc))
        n = n if n[1] > 0 else -n
        A = p((s * 0.12, 0.10, 0.12))
        add(Blade(A, e, cc, n, 1.20 * span * k, lead=(0.05 * k, 0.02 * k), trail=(0.46 * k, 0.07 * k),
                  th=(0.03 * k, 0.012 * k), teeth=(5, 0.07 * k, 0.5), gs=1.8), back, 0.0)


def perched_crow(add, c, yaw=0.0, k=0.30, lean=0.0):
    """A crow sitting folded on a shoulder (grounded exception: perched with folded wings)."""
    R = rot_y(yaw) @ rot_x(lean)
    p = lambda q: c + R @ (v3(*q) * k)
    add(Ellipsoid(p((0, 0.12, 0)), (0.17 * k, 0.17 * k, 0.34 * k), R @ rot_x(-0.5)), 'feather_i', 0.0)
    add(Sphere(p((0, 0.38, 0.22)), 0.11 * k), 'feather_i', 0.04)
    add(Capsule(p((0, 0.36, 0.30)), p((0, 0.30, 0.54)), 0.05 * k, 0.014 * k), 'beak_ink', 0.0)
    add(Capsule(p((0, 0.05, -0.2)), p((0, -0.12, -0.62)), 0.07 * k, 0.10 * k), 'feather_i', 0.0)
    add(Sphere(p((-0.09, 0.40, 0.27)), 0.035 * k), 'eye_ring', 0.0)
    add(Sphere(p((-0.10, 0.40, 0.29)), 0.022 * k), 'eye', 0.0)
    add(Sphere(p((0.09, 0.40, 0.27)), 0.035 * k), 'eye_ring', 0.0)


def feather_mantle(P, add, mats=('feather_s', 'feather_g', 'feather_i'), rings=((0.17, 0.0, 0.10, 12), (0.235, -0.07, 0.12, 14)),
                   droop=0.55, scale=1.0, seed=2):
    """Shawl of hanging feathers around the shoulders (rows of overlapping feather blades)."""
    h, b = P['height'], P['build']
    nk = P['neck']
    rng = np.random.default_rng(seed)
    for ri, (rad, dy, ln, n) in enumerate(rings):
        for i in range(n):
            th = (i / n) * 6.283 + ri * 0.3
            ox, oz = np.sin(th), np.cos(th)
            c = nk + v3(ox * rad * b, (-0.04 + dy) * h, oz * rad * b * 0.8)
            d = norm(v3(ox * droop, -1.0, oz * droop * 0.8))
            R = basis_from(d, v3(0, 0, 1))
            m = mats[(i + ri) % len(mats)] if rng.random() > 0.15 else mats[(i + 1) % len(mats)]
            add(Ellipsoid(c + d * ln * 0.5 * h * scale, (0.036 * scale, ln * 0.55 * h * scale, 0.014), R), m, 0.0)


def ground_finish(P, parts, mats, lights=(), S=None):
    return gyre_finish(P, parts, mats, lights, S or HEAP_S)


def ground_rows(base, attack='swing', weapon_side='r', cast_side='l', tweak=None, melt=(0, 0, 0.35, 1.0)):
    rows_, fr = humanoid_rows(base, attack_style=attack, weapon_side=weapon_side, cast_side=cast_side)

    def frames():
        rows = fr()
        for i, (P, o) in enumerate(rows['death']):
            ground_pose(P)
            P['melt'] = melt[i]
            P['end'] = [0, 0, 0.5, 1.0][i]
            if melt[i] >= 0.97:
                P['glow'] = 0.0
        for nm in rows:
            for P, o in rows[nm]:
                ground_pose(P)
        if tweak:
            tweak(rows)
        return rows
    return rows_, frames

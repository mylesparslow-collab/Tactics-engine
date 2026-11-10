"""Prow Ram (Hermitage champion, melee charger). A horse-sized crab wearing the broken-off bow of a wrecked ship:
the pointed stem leads (the bow faces where the crab faces), grey timber in three broad strakes under a faded paint
band, a heavy dark keel line that sweeps up the cutwater to the stem head, a solid gunwale rail, a ragged smashed
stern at the back. A heavy iron-shod ram beak juts low off the forefoot; a small carved figurehead (a pale woman's
bust, arms crossed, blank eyes) rides the stem under the stem head. Legs come out from under the hull, the big claw
out under the ram, eyestalks up through the deck hatch. ~1.8 m, ppm 44.
Defining detail: the ram beak leading the pointed bow (and the figurehead's stare above it)."""
from _hermitage_common import *

UNIT_ID = 'hermitage_prow_ram'
SIZE = 'large'
CAMERA = Camera(ppm=44)

HL = 0.54          # half length of the bow section (stern cut at -z, stem at +z)
W0 = 0.30          # half beam at the cut stern
RAKE = 0.42        # the stem rakes forward going up
TIMBER = _hex('#d2c8b4')
TIMBER_DK = _hex('#6f665c')
PAINT = _hex('#5a8ea6')      # faded blue-grey paint strake
KEEL = _hex('#3a2e2a')       # tarred oak keel, stem and rail
DECK = _hex('#5a4c3e')
IRON_DK = _hex('#3a3436')
WALL = 0.032       # plank thickness of the open hold
ZFC = 0.02         # the forecastle deck starts here; aft of it the hold is open


def _deck_y(u):
    return 0.10 + 0.56 * u ** 2.2


def _bot_y(u):
    return -0.48 + 0.42 * u ** 2.2


def _half_w(u):
    return W0 * np.clip(1.0 - u ** 2.1, 0, 1) ** 0.62 + 0.012


def _uvt(q):
    """Hull coordinates of local points: u along (0 stern .. 1 stem), t down the side (0 sheer .. 1 keel)."""
    x, y, z = q[:, 0], q[:, 1], q[:, 2]
    ze = z - RAKE * y
    u = np.clip((ze + HL) / (2 * HL), 0, 1)
    yd, yb = _deck_y(u), _bot_y(u)
    t = np.clip((yd - y) / (yd - yb), 0, 1)
    return u, t, yd, yb, ze


def _hw(q):
    u, t, yd, yb, ze = _uvt(q)
    return _half_w(u) * np.clip(1.0 - t ** 4.0, 0, 1) ** 0.45 + 0.01


def _hull_sdf(q):
    x, y, z = q[:, 0], q[:, 1], q[:, 2]
    u, t, yd, yb, ze = _uvt(q)
    hw = _hw(q)
    e = 0.01
    gz = (_hw(q + v3(0, 0, e)) - _hw(q - v3(0, 0, e))) / (2 * e)
    gy = (_hw(q + v3(0, e, 0)) - _hw(q - v3(0, e, 0))) / (2 * e)
    side = (np.abs(x) - hw) / np.sqrt(1.0 + gz ** 2 + gy ** 2)       # normalised: no soft-shadow smudge
    d = side * 0.95
    d = np.maximum(d, (y - yd) * 0.9)
    d = np.maximum(d, (yb - y) * 0.9)
    d = np.maximum(d, (ze - HL) * 0.8)
    # ragged, smashed-off stern: a splintered cut that is not a straight saw line
    jag = 0.05 * np.sin(y * 17.0 + 0.7) + 0.035 * np.sin(x * 23.0 + y * 9.0) + 0.04 * (y - 0.1)
    d = np.maximum(d, (-(z + HL) + jag) * 0.8)
    # the aft half is an open, smashed hold: hollow it out behind the forecastle deck
    cav = np.maximum(side * 0.95 + WALL, (yb - y) * 0.9 + 0.07)
    cav = np.maximum(cav, (ze - ZFC + 0.04 * np.sin(x * 19.0)) * 0.8)
    return np.maximum(d, -cav)


def _cav_d(q):
    x, y, z = q[:, 0], q[:, 1], q[:, 2]
    u, t, yd, yb, ze = _uvt(q)
    hw = _half_w(u) * np.clip(1.0 - t ** 4.0, 0, 1) ** 0.45 + 0.01
    return np.abs(x) - hw, ze, y - yb


def _keel_pts():
    pts = []
    for u in np.linspace(0.0, 1.0, 9):
        y = _bot_y(u) - 0.01
        pts.append(v3(0, y, -HL + 2 * HL * u + RAKE * y))
    for f in np.linspace(0.2, 1.0, 4):          # up the cutwater to the stem head
        y = _bot_y(1.0) + (_deck_y(1.0) + 0.16 - _bot_y(1.0)) * f
        pts.append(v3(0, y, HL + RAKE * y + 0.015 + 0.03 * f ** 2))
    return pts


def prow_shell():
    def build(add, P, F):
        F.put(add, Func(_hull_sdf, (0, 0, 0.1), 1.3), 'timber')
        # keel + stem: one heavy dark line along the bottom that sweeps up the cutwater
        kp = _keel_pts()
        for i, (a, b) in enumerate(zip(kp[:-1], kp[1:])):
            r0 = 0.040 if i < 8 else 0.046
            F.put(add, Capsule(a, b, r0, r0), 'keel', 0.0 if i == 0 else 0.01)
        sh = kp[-1]
        F.sph(add, tuple(sh + v3(0, 0.02, 0.01)), 0.058, 'keel')            # stem head knob
        # solid gunwale rail band each side along the sheer, meeting at the stem
        for sx in (-1, 1):
            pts = []
            for u in np.linspace(0.0, 0.97, 7):
                y = _deck_y(u) + 0.005
                pts.append(v3(sx * (_half_w(u) + 0.004), y, -HL + 2 * HL * u + RAKE * y))
            for a, b in zip(pts[:-1], pts[1:]):
                F.put(add, Capsule(a, b, 0.030), 'keel', 0.006)
        # two ribs standing in the open hold (structure, not a comb)
        for uu in (0.16, 0.36):
            pts = []
            for tt in np.linspace(0.0, 0.92, 5):
                yd, yb = _deck_y(uu), _bot_y(uu)
                y = yd - (yd - yb) * tt
                hw = _half_w(uu) * (1.0 - tt ** 4.0) ** 0.45
                pts.append((hw - 0.045, y, -HL + 2 * HL * uu + RAKE * y))
            for sx in (-1, 1):
                for a, b in zip(pts[:-1], pts[1:]):
                    F.put(add, Capsule(v3(sx * a[0], a[1], a[2]), v3(sx * b[0], b[1], b[2]), 0.026), 'timberd', 0.004)
        # forecastle deck edge beam across the front of the hold
        yb0 = _deck_y(0.53)
        F.cap(add, (-_half_w(0.53), yb0 - 0.02, ZFC + RAKE * yb0 - 0.03), (_half_w(0.53), yb0 - 0.02, ZFC + RAKE * yb0 - 0.03),
              0.034, None, 'keel')
        # two splintered plank ends sticking out of the broken stern
        for sx, y, ln, ang in ((-1, 0.02, 0.12, 0.30), (1, -0.20, 0.10, -0.15)):
            u0 = 0.02
            c = v3(sx * (_half_w(u0) * 0.92), y, -HL - ln * 0.35 + RAKE * y)
            F.box(add, tuple(c), (0.016, 0.042, ln * 0.5), 0.008, 'timberd', R=rot_y(sx * 0.18) @ rot_x(ang))
        # iron-shod ram beak low off the forefoot
        y0 = _bot_y(1.0) + 0.12
        a = v3(0, y0 + 0.03, HL + RAKE * y0 - 0.30)
        b = v3(0, y0 - 0.07, HL + RAKE * y0 + 0.56)
        F.put(add, Capsule(a, b, 0.20, 0.036), 'ram', 0.0)
        F.put(add, Ellipsoid(lerp(a, b, 0.55), (0.19, 0.04, 0.25), rot_x(0.10)), 'ram', 0.03)   # flat beak blades
        F.sph(add, tuple(b + norm(b - a) * 0.02), 0.04, 'ramtip')
        ax = norm(b - a)
        for f, rr in ((0.28, 0.165), (0.50, 0.125)):
            F.put(add, Torus(lerp(a, b, f), ax, rr, 0.026), 'ramband')
        for sx, f, dy in ((-1, 0.38, 0.03), (1, 0.38, 0.03), (-1, 0.20, -0.06)):     # three bolt bosses
            c = lerp(a, b, f)
            rr = 0.20 + (0.036 - 0.20) * f
            F.sph(add, tuple(c + v3(sx * rr * 0.9, dy, 0)), 0.028, 'ramband')
        # figurehead: a small pale bust on the stem under the stem head, leaning out, arms crossed
        fy = _deck_y(1.0) - 0.03
        G = F.child((0, fy, HL + RAKE * fy + 0.10), rot_x(0.55), 1.0)
        G.ell(add, (0, 0.0, 0.0), (0.075, 0.10, 0.065), 'figure', 0.02)                 # bust
        G.cap(add, (-0.07, -0.01, 0.04), (0.06, 0.04, 0.06), 0.028, 0.026, 'figure', 0.015)   # crossed arms
        G.cap(add, (0.07, -0.01, 0.045), (-0.05, 0.04, 0.065), 0.028, 0.026, 'figure', 0.015)
        G.ell(add, (0, 0.15, 0.025), (0.052, 0.062, 0.055), 'figure', 0.02)              # head
        G.ell(add, (0, 0.165, -0.02), (0.058, 0.07, 0.05), 'hair', 0.015)
        G.ell(add, (0, 0.09, -0.04), (0.055, 0.10, 0.04), 'hair', 0.015)
        for sx in (-1, 1):
            G.ell(add, (sx * 0.022, 0.155, 0.072), (0.014, 0.010, 0.008), 'blank', 0.0)

        def alb(q, n):
            u, t, yd, yb, ze = _uvt(q)
            a = _arr(TIMBER, len(q))
            g = fbm(q * v3(1, 4, 0.6), 6.0, 2)[:, None]
            a = a * (0.86 + 0.24 * g)
            # three broad strakes under a faded paint band; seams follow the sheer and converge at the stem
            st = np.floor(np.clip((t - 0.22) / 0.26, 0, 2.999)).astype(int)
            a = np.where((st == 1)[:, None], a * 0.88, a)
            paint = (t > 0.04) & (t < 0.22)
            pc = _arr(PAINT, len(q)) * (0.88 + 0.2 * fbm(q, 9.0, 2)[:, None])
            flake = (vnoise(q * v3(1, 2, 1), 10.0) > 0.66)[:, None]
            a = np.where(paint[:, None], np.where(flake, a, pc), a)
            seam = (np.abs(t - 0.22) < 0.028) | (np.abs(t - 0.48) < 0.022) | (np.abs(t - 0.74) < 0.022)
            a = np.where(seam[:, None], np.array(TAR)[None, :] * 1.4, a)
            top = q[:, 1] > yd - 0.012
            deck = _arr(DECK, len(q)) * (0.85 + 0.3 * fbm(q * v3(6, 1, 1), 8.0, 2)[:, None])
            a = np.where(top[:, None], deck, a)
            # the smashed stern face is dark inside
            cut = (q[:, 2] + HL) < 0.05
            sd, ze2, hb = _cav_d(q)
            hold = (sd < -0.035) & (hb > 0.05) & (ze2 < ZFC + 0.03) & (q[:, 1] < yd - 0.01)
            a = np.where((cut | hold)[:, None] & ~top[:, None], np.array(TAR)[None, :] * 1.5, a)
            return a

        def rust(q, n):
            a = _arr(_hex('#8a4a2a'), len(q)) * (0.9 + 0.25 * fbm(q, 7.0, 2)[:, None])
            b = (vnoise(q * v3(1, 1, 0.5), 7.0) > 0.62)[:, None]
            a = np.where(b, np.array(IRON_DK)[None, :], a)
            b2 = (vnoise(q + 2.2, 11.0) > 0.70)[:, None]
            return np.where(b2, np.array(ORANGE)[None, :] * 0.9, a)
        return {'timber': Material(local_albedo(F, alb), spec=0.08, gloss=10, brush=0.10),
                'timberd': Material(TIMBER_DK, spec=0.08, gloss=10, brush=0.08),
                'keel': Material(KEEL, spec=0.15, gloss=14, brush=0.06),
                'ram': Material(local_albedo(F, rust), spec=0.55, gloss=28, metal=0.5),
                'ramtip': Material(_hex('#b86a36'), spec=0.6, gloss=30, metal=0.5),
                'ramband': Material(_hex('#1e1a1c'), spec=0.5, gloss=26, metal=0.5),
                'figure': Material(_hex('#d8ccb0'), spec=0.15, gloss=14, brush=0.05),
                'hair': Material(_hex('#3c3434'), spec=0.1, gloss=12),
                'blank': Material(_hex('#fbf6ea'), spec=0.3, gloss=20, rim=0.0)}
    return build


def _eyes():
    out = []
    for sx in (-1, 1):
        base = v3(sx * 0.07, 0.0, -0.10)
        d = norm(v3(sx * 0.25, 1.0, 0.30))
        out.append((tuple(base), tuple(d), 0.46))
    return tuple(out)


SHELL = Shell(
    build=prow_shell(),
    ride=0.98, tilt=0.0, crab_at=(0, -0.38, 0.22), crab_pitch=0.10, z0=-0.40, x0=0.04, yaw=0.62,
    feet=((-0.40, 0.36), (0.42, 0.34), (-0.42, -0.34), (0.46, -0.38)),
    leg_roots=((-0.14, -0.40, 0.20), (0.14, -0.40, 0.20), (-0.17, -0.40, -0.20), (0.17, -0.40, -0.20)),
    eyes=_eyes(), eye_bead=0.055, antennae=False,
    guard=((0.12, -0.20, 0.30), (-0.05, -0.30, 0.95)),
    big=0.85, small=0.5, side_r=0.40, tip_angle=1.15, leg_len=1.12, leg_r=1.15)


def neutral_pose():
    return hermit_pose(open=0.3, spread=0.3)


def build(P):
    return shelled(P, SIZE, SHELL)


def _rows(R):
    # attack: the prow dips and lunges, the claw snaps under the ram
    for i, (P, o) in enumerate(R['attack']):
        P['lean'] = [-0.10, -0.16, 0.12, 0.03][i]
        P['slide'] = [0.0, -0.04, 0.0, 0.0][i]
        P['snap'] *= 0.4
    for P, o in R['death']:
        P['yaw'] = 0.25 * P['tip']           # keels over turning side-on, so the long hull stays in frame
        k = min(1.0, 1.6 * P['tip'])
        P['slide'] = 0.42 * k
        P['recoil'] = 0.30 * k
    for row in ('hit', 'death', 'cast'):
        for P, o in R[row]:
            P['snap'] *= 0.6
            P['drum'] *= 0.6
    return R


ROWS, frames = hermit_rows(neutral_pose, 'shell', extra=_rows)

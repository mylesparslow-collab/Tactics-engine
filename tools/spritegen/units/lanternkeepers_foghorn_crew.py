"""Foghorn Crew (Lanternkeepers area control, one sculpt, two keepers). A great hand-cranked brass-dull fog horn
on a wooden trestle, the bell flaring toward the enemy, a big spoked flywheel on the camera side. A stocky keeper
in a sou'wester cranks the wheel; a tall hooded keeper stands by the throat with a lamp pole and fingers in her
ears. Both wear wool ear-muffs. Defining detail: the huge flared bell with its dark mouth and ribbed hoops; on the
attack the crank spins, B clamps her hands over her ears and pale rings of sound roll out of the mouth."""
import numpy as np
from _lanternkeepers_w2 import *
from kit import anim
from sdf import Prim

UNIT_ID = 'lanternkeepers_foghorn_crew'
FACTION = 'lanternkeepers'
LOOK = LOOKS[FACTION]
CAMERA = Camera(ppm=44, anchor=(55, 104))

UH = norm(v3(0.60, 0.0, 0.80))
U = norm(UH + v3(0, 0.26, 0))            # horn axis (toward the enemy, a little up)
SD = norm(np.cross(v3(0, 1, 0), UH))     # horizontal side axis, pointing away from the camera
YAW = float(np.arctan2(UH[0], UH[2]))
T0 = v3(0.0, 1.00, 0.0)              # throat of the horn
HORN_L = 0.86

CA = Costume(top='oilskin_dk', sleeve='oilskin', legs='slate', boot='boot', hand='glove', skirt='coat',
             skirt_mat='oilskin', hem=0.30, flare=0.8, head='none', belt='leather', girth=1.12, skin='skinA')
CB = Costume(top='coatgrey', sleeve='coatgrey', legs='slate', boot='boot', hand='glove', skirt='robe',
             skirt_mat='coatgrey', hem=0.08, flare=0.9, head='hood', head_mat='coatgrey', belt='leather', girth=0.9,
             skin='skinB')

VEC_KEYS = ('pelvis', 'chest', 'neck', 'head', 'sh_r', 'el_r', 'wr_r', 'sh_l', 'el_l', 'wr_l',
            'hip_r', 'kn_r', 'an_r', 'hip_l', 'kn_l', 'an_l')


def orient(P, yaw, pos):
    """Turn a canonical (facing +z) pose about the vertical through its feet-centre and move it to pos."""
    pivot = v3(0, 0, 0)
    rig.rotate(P, VEC_KEYS, pivot, rot_y(yaw))
    rig.shift(P, VEC_KEYS, pos)
    P['head_yaw'] = P['head_yaw'] + yaw
    P['foot_r_yaw'] += yaw
    P['foot_l_yaw'] += yaw
    for k in ('item_r', 'item_l'):
        if P[k] is not None:
            P[k] = rot_y(yaw) @ P[k]
    return P


def horn_pts(P):
    """Scene anchor points from the pose scalars: throat, mouth, wheel centre, crank handle."""
    th = P['horn_pitch']
    Ux = norm(UH + v3(0, 0.26 + th, 0))
    T = T0 + v3(0, 0.03 * P['horn_bob'], 0)
    mouth = T + Ux * HORN_L
    wc = T - SD * 0.34 + Ux * (-0.06) + v3(0, -0.10, 0)     # camera-side flywheel
    ang = P['crank'] * 2 * np.pi
    Uw = norm(UH)
    hnd = wc + (np.cos(ang) * v3(0, 1, 0) + np.sin(ang) * Uw) * 0.20 - SD * 0.07
    return Ux, T, mouth, wc, hnd, ang


class Bell(Prim):
    """Hollow flared horn shell along an axis (open mouth)."""
    def __init__(self, O, u, L, r0, r1, p=2.4, th=0.016):
        self.O, self.u, self.L, self.r0, self.r1, self.p, self.th = O, norm(u), L, r0, r1, p, th
        self.bc = O + self.u * L * 0.5
        self.br = L * 0.5 + r1 + 0.1

    def __call__(self, pts):
        q = pts - self.O
        t = q @ self.u
        rad = np.linalg.norm(q - t[:, None] * self.u[None, :], axis=1)
        tn = np.clip(t / self.L, 0, 1)
        r = self.r0 + (self.r1 - self.r0) * tn ** self.p
        d = np.abs(rad - r) - self.th
        return np.maximum(d, np.maximum(-t, t - self.L)) * 0.8


def horn(add, lights, P):
    Ux, T, mouth, wc, hnd, ang = horn_pts(P)
    add(Func(Bell(T, Ux, HORN_L, 0.06, 0.31, p=2.2).__call__, T + Ux * HORN_L * 0.5, HORN_L * 0.5 + 0.5), 'hornbrass', 0.0)
    # dark cavity inside the bell
    add(Cylinder(mouth - Ux * 0.14, mouth - Ux * 0.13, 0.27, 0.003), 'cavity', 0.0)
    # ribbed hoops, mouth rim
    for t, rr in ((0.30, 0.088), (0.52, 0.12), (0.72, 0.18), (0.88, 0.25), (1.0, 0.31)):
        add(Torus(T + Ux * HORN_L * t, Ux, rr + 0.012, 0.011 if t < 1 else 0.017), 'hoop', 0.0)
    # throat: wind-chest drum and mouthpiece
    add(Cylinder(T - Ux * 0.30, T + Ux * 0.04, 0.115, 0.012), 'hornbrass', 0.0)
    add(Torus(T - Ux * 0.12, Ux, 0.118, 0.012), 'hoop', 0.0)
    add(Torus(T - Ux * 0.28, Ux, 0.118, 0.012), 'hoop', 0.0)
    add(Capsule(T - Ux * 0.30, T - Ux * 0.46, 0.05, 0.03), 'hornbrass', 0.0)
    # trestle: two A-frame legs under the throat region and one under the bell
    for off, sp in ((-0.05, 0.30), (0.62, 0.30)):
        c = T + Ux * off
        for sg in (-1, 1):
            foot = v3(c[0], 0.0, c[2]) + SD * sg * sp + UH * 0.0
            add(Capsule(c + v3(0, -0.04, 0) + SD * sg * 0.05, foot, 0.030, 0.034), 'wood', 0.0)
        add(Capsule(c - SD * 0.16 + v3(0, -0.07, 0), c + SD * 0.16 + v3(0, -0.07, 0), 0.032, 0.032), 'wood', 0.0)
        add(Capsule(v3(c[0], 0.20, c[2]) - SD * 0.22, v3(c[0], 0.20, c[2]) + SD * 0.22, 0.016, 0.016), 'wood', 0.0)
    # flywheel on the camera side: rim, hub, spokes, handle
    ax = -SD
    add(Torus(wc, ax, 0.255, 0.020), 'iron', 0.0)
    add(Cylinder(wc - ax * 0.03, wc + ax * 0.03, 0.045, 0.006), 'hornbrass', 0.0)
    add(Capsule(wc, T - Ux * 0.12 - ax * 0.0 + v3(0, 0, 0), 0.012, 0.012), 'iron', 0.0)
    for k in range(6):
        a = ang + k * np.pi / 3
        d = np.cos(a) * v3(0, 1, 0) + np.sin(a) * norm(UH)
        add(Capsule(wc + ax * 0.0, wc + d * 0.245, 0.012, 0.010), 'iron', 0.0)
    add(Capsule(hnd, hnd + ax * 0.10, 0.017, 0.017), 'wood', 0.0)
    # sound rings leaving the mouth
    fx = P['fx']
    if fx > 0:
        for k in range(3):
            tt = (k + 0.4 + 0.9 * P['ringp']) % 3.0
            rc = mouth + Ux * (0.12 + 0.30 * tt)
            add(Torus(rc, Ux, 0.18 + 0.20 * tt, 0.012 * fx * (1.2 - tt / 3.5)), 'soundring', 0.0)
        light_at(lights, P, mouth + Ux * 0.2, 1.2 * fx, 0.5, color=_hex('#e9f2ff'))


def make_keeper(kind):
    if kind == 'A':
        P = base_pose(height=0.97, build=1.14)
    else:
        P = base_pose(height=1.07, build=0.88)
    return P


def keeper_pose(kind, row, i, P_main):
    """Canonical -> scene pose for keeper A or B in a given row/frame."""
    base = lambda: make_keeper(kind)
    if row == 'idle':
        P, _ = anim.idle(base, i)
    elif row == 'move':
        P, _ = anim.walk(base, i)
    elif row == 'death':
        P, _ = anim.death(base, i)
    elif row == 'hit':
        P, _ = anim.hit(base, i)
    else:
        P, _ = anim.idle(base, i % 4)
    return P


POS_A = T0 * v3(1, 0, 1) - UH * 0.62 - SD * 0.38
POS_B = T0 * v3(1, 0, 1) - UH * 0.22 + SD * 0.55


def _neutral():
    P = base_pose()
    P.update(dict(horn_pitch=0.0, horn_bob=0.0, crank=0.0, fx=0.0, ringp=0.0, wheel=0.0, ears=0.0, A=None, B=None))
    return P


def neutral_pose():
    return pose_frame('idle', 0, 0.0)


def pose_frame(row, i, crank, fx=0.0, ears=0.0, ringp=0.0, bob=0.0, pitch=0.0, lift=0.0):
    P = _neutral()
    P.update(crank=crank, fx=fx, ears=ears, ringp=ringp, horn_bob=bob, horn_pitch=pitch)
    PA = keeper_pose('A', row, i, P)
    PB = keeper_pose('B', row, i, P)
    orient(PA, YAW + 0.25, POS_A)
    orient(PB, YAW - 0.15, POS_B)
    PB['head_yaw'] += np.radians(-20)
    PA['head_yaw'] += np.radians(-18)
    Ux, T, mouth, wc, hnd, ang = horn_pts(P)
    hA, hB = PA['height'], PB['height']
    if row not in ('death', 'hit'):
        # A: right hand on the crank handle, left hand on the wheel rim opposite; leans with the turn
        sw = np.sin(ang)
        rig.lean(PA, fwd=np.radians(8 + 5 * fx))
        rig.place_arm(PA, 'r', hnd - SD * 0.06 + v3(0, 0.02, 0), (-1, -0.6, -0.3), l1=0.27 * hA, l2=0.26 * hA)
        rig.place_arm(PA, 'l', wc + SD * 0.0 + v3(0.04, 0.12, 0.0) + UH * 0.18 - v3(0, 0.33 * 0, 0), (1, -0.6, -0.3), l1=0.27 * hA, l2=0.26 * hA)
        # B: one hand on the lamp pole, the other on the horn throat; ears clamp when blasting
        e = ears
        hp = PB['head']
        rig.lean(PB, fwd=np.radians(-4 + 6 * e))
        for s, sx in (('r', -1), ('l', 1)):
            ear = hp + v3(sx * 0.10, 0.0, -0.01) + rot_y(YAW) @ v3(sx * 0.0, 0, 0)
            if s == 'l':
                tgt_pole = PB['pelvis'] + rot_y(YAW) @ v3(0.25, 0.26, 0.20)
                tgt = ear * e + tgt_pole * (1 - e)
                rig.place_arm(PB, 'l', tgt, (1, -0.4, -0.5), l1=0.27 * hB, l2=0.26 * hB)
                PB['item_l'] = norm(v3(0.04, 1.0, 0.0)) if e < 0.5 else None
            else:
                tgt_h = T - Ux * 0.22 + SD * 0.0 + v3(0, 0.02, 0.0) - SD * 0.14
                tgt = ear * e + tgt_h * (1 - e)
                rig.place_arm(PB, 'r', tgt, (-1, -0.4, -0.4), l1=0.27 * hB, l2=0.26 * hB)
    P['A'], P['B'] = PA, PB
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    PA, PB = P['A'], P['B']
    hA, hB = PA['height'], PB['height']
    horn(add, lights, P)
    body(PA, add, CA)
    body(PB, add, CB)
    # keeper A: sou'wester and a rope of knitted scarf; keeper B: hood peak
    sou_wester(add, PA, 'oilskin', brim=1.0, tilt=0.05)
    hair(PA, add, 'hairA', 'short')
    # ear muffs (both): padded cups joined by a band
    for Q in (PA, PB):
        H, R, h = Q['head'], head_R(Q), Q['height']
        for sx in (-1, 1):
            add(Cylinder(H + R @ v3(sx * 0.082, 0.0, -0.005) * h, H + R @ v3(sx * 0.112, 0.0, -0.005) * h, 0.042 * h, 0.008), 'muff', 0.01)
        add(Torus(H + R @ v3(0, 0.02, -0.005) * h, R[:, 2], 0.083 * h, 0.006), 'darkiron', 0.0)
    # B's lamp pole (left hand)
    if PB['item_l'] is not None:
        d = norm(PB['item_l'])
        g = hand_pos(PB, 'l')
        butt, top = g - d * 0.95, g + d * 0.78
        add(Capsule(butt, top, 0.016, 0.013), 'wood', 0.0)
        pole_lamp(add, lights, PB, butt + d * 0.0 if False else g - d * 0.0, top, 'hurricane', size=1.05, shaft='wood', frame='darkiron', arm=0.07, light=1.5) if False else None
        c = top + v3(0.05, -0.04, 0)
        add(Capsule(top, c, 0.008), 'darkiron', 0.0)
        hurricane(add, lights, PB, c - v3(0, 0.08, 0), size=1.05, frame='darkiron', light=1.5)
    # B and A: satchels / coil
    pel = PA['pelvis']
    add(Torus(pel + v3(-0.0, -0.02, 0.0) + rot_y(YAW) @ v3(0.19, 0.0, 0.0), rot_y(YAW) @ v3(1, 0, 0), 0.07, 0.012), 'rope', 0.0)
    mats = keeper_mats(PA, hair=_hex('#6b5a46'), skin=_hex('#c99877'), coat=_hex('#9a9772'))
    mats['skinA'] = Material(face_albedo(PA, _hex('#c99877'), _hex('#6b5a46'), lips=_hex('#a65a4a')), spec=0.06, gloss=12, sss=0.6, brush=0.02)
    mats['skinB'] = Material(face_albedo(PB, _hex('#a9795a'), _hex('#2c2420'), lips=_hex('#8f4f44')), spec=0.06, gloss=12, sss=0.6, brush=0.02)
    mats['hairA'] = Material(_hex('#6b5a46'), spec=0.2, gloss=16, brush=0.1)
    mats['hornbrass'] = Material(noisy(_hex('#6b6350'), 0.10, 18.0), spec=0.6, gloss=26, metal=0.7, brush=0.06)
    mats['hoop'] = Material(noisy(_hex('#4a4a46'), 0.10), spec=0.6, gloss=28, metal=0.7, brush=0.05)
    mats['cavity'] = Material(_hex('#1b1a18'), spec=0.0, brush=0.0)
    mats['muff'] = Material(noisy(_hex('#b9ae94'), 0.14, 60.0), spec=0.02, brush=0.1)
    mats['rope'] = Material(noisy(_hex('#8f8366'), 0.16, 60.0), spec=0.02, brush=0.1)
    mats['soundring'] = Material(_hex('#e8f1f6'), emissive=_hex('#9fb6c2'), rim=0.0)
    return finish(P, FACTION, parts, mats, lights=lights)


def frames():
    rows = {}
    rows['idle'] = [(pose_frame('idle', i, crank=[0.0, 0.07, 0.14, 0.21][i], bob=[0, 1, 0, -1][i]), {}) for i in range(4)]
    for i, (P, o) in enumerate(rows['idle']):
        P['glow'] = [1.0, 0.88, 1.08, 0.94][i]
    rows['move'] = [(pose_frame('move', i, crank=[0.0, 0.18, 0.36, 0.54][i], bob=[1, 0, 1, 0][i]), {}) for i in range(4)]
    rows['attack'] = [(pose_frame('idle', i, crank=[0.0, 0.2, 0.5, 0.8][i], fx=[0, 0.4, 1.0, 0.6][i],
                                  ears=[0.0, 0.6, 1.0, 0.8][i], ringp=[0, 0.1, 0.3, 0.8][i],
                                  bob=[0, -1, 1, 0.5][i], pitch=[0, -0.04, 0.03, 0.0][i]), {}) for i in range(4)]
    rows['hit'] = [(pose_frame('hit', 0, crank=0.1), dict(exposure=1.25, flash=0.22)), (pose_frame('hit', 1, crank=0.1), {})]
    rows['death'] = []
    for i in range(4):
        P = pose_frame('death', i, crank=0.1 * i, pitch=[0, -0.05, -0.12, -0.2][i])
        P['end'] = [0, 0.15, 0.5, 1.0][i]
        P['glow'] = [1, 0.6, 0.3, 0.0][i]
        for K in ('A', 'B'):
            P[K]['end'] = P['end']
        rows['death'].append((P, {}))
    rows['cast'] = [(pose_frame('idle', i, crank=[0.0, 0.2, 0.4][i], fx=[0.3, 0.8, 0.4][i], ears=[0.2, 0.7, 0.3][i],
                                ringp=[0, 0.3, 0.6][i]), {}) for i in range(3)]
    for i, (P, o) in enumerate(rows['cast']):
        P['cast_glow'] = [0.4, 1.0, 0.4][i]
        P['glow'] = [1.2, 1.8, 1.2][i]
    return rows


ROWS = anim.ROWS

"""Mother Harrow (Hermitage hero, shell healer; the faction's one human). A stout old ex-Compact ship's carpenter in
a patched canvas-grey smock, a leather apron stained with barnacle-bone salt, a faded headscarf over grey hair,
sleeves rolled to bare forearms. A wooden caulking mallet in her right hand, a coil of oakum over one shoulder, a
tar-black caulking iron through her belt, and a violet rag tied round her right arm (she is one of them). Alone: no
crab in the sprite. Defining detail: the mallet and the violet arm rag."""
import numpy as np
from kit.humanoid import *
from kit.anim import humanoid_rows
from _hermitage_common import LOOK, rag

UNIT_ID = 'hermitage_mother_harrow'
FACTION = 'hermitage'

SMOCK = _hex('#8f8d86')
SMOCK_DK = _hex('#6f6d68')
APRON = _hex('#855a38')
SCARF = _hex('#74879c')
BONE = _hex('#e3d9c6')
TARC = _hex('#1f1a1d')
RAGV = _hex('#7a3a9e')
OAKUM = _hex('#b79f68')
HAIR = _hex('#b9b4ae')

C = Costume(top='smock', sleeve='skin', legs='trousers', boot='boot', hand='skin', skirt='robe', skirt_mat='smock',
            hem=0.30, flare=0.8, head='bald', belt='leather', girth=1.28, boots_tall=False, neck_len=0.8)


def neutral_pose():
    P = base_pose(height=0.93, build=1.12)
    rig.lean(P, fwd=np.radians(5))
    P['head_pitch'] = np.radians(2)
    P['head_yaw'] = np.radians(-22)
    rig.place_arm(P, 'r', v3(-0.47, 1.22, 0.12), (-1.0, -0.6, -0.2))          # mallet raised, ready to tap
    P['item_r'] = norm(v3(-0.18, 1.0, 0.12))
    rig.place_arm(P, 'l', v3(0.27, 0.95, 0.10), (1, -0.1, -0.7))             # fist on the hip
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    h, b = P['height'], P['build']
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    H, R = P['head'], head_R(P)
    # rolled sleeves: short smock sleeve to mid upper arm with a fat rolled cuff
    for s in ('r', 'l'):
        sh, el = P['sh_' + s], P['el_' + s]
        a = sh + (el - sh) * 0.60
        add(Capsule(sh + v3(0, -0.04, 0), a, 0.064 * b, 0.060 * b), 'smock', 0.03)
        ax = norm(el - sh)
        add(Torus(a, ax, 0.060 * b, 0.022), 'smockdk', 0.01)
    # leather apron: bib to the knee, a pocket and a strap round the neck
    ap = ch + v3(0, -0.27 * h, 0.150 * b)
    Ra = rot_x(0.10)
    add(Ellipsoid(ap, (0.165 * b, 0.34 * h, 0.04), Ra), 'apron', 0.02)
    add(Ellipsoid(ap + v3(0, -0.17 * h, 0.03), (0.11 * b, 0.07 * h, 0.022), Ra), 'apron2', 0.01)       # pocket
    for sx in (-1, 1):
        add(Capsule(ch + v3(sx * 0.070 * b, 0.13 * h, 0.07), ch + v3(sx * 0.046 * b, 0.28 * h, 0.03), 0.014), 'apron2')
    # tar-black caulking iron through the belt on her left hip
    a = pel + v3(0.15 * b, 0.07 * h, 0.07)
    add(Capsule(a + v3(0.02, -0.17, -0.02), a + v3(-0.03, 0.12, 0.05), 0.014), 'tar')
    add(RoundBox(a + v3(-0.04, 0.14, 0.055), (0.012, 0.05, 0.026), 0.004, basis_from(v3(-0.5, 1, 0.4), (0, 0, 1))), 'iron')
    # a tar pail hanging off her belt on the left hip: a fat iron-banded bucket, handle loop and tar skin
    pc = pel + v3(0.24 * b, -0.12 * h, 0.04)
    add(Cylinder(pc + v3(0, -0.10, 0), pc + v3(0, 0.10, 0), 0.085, 0.01), 'pail', 0.0)
    add(Cylinder(pc + v3(0, 0.095, 0), pc + v3(0, 0.105, 0), 0.075, 0.005), 'tar')
    add(Torus(pc + v3(0, 0.0, 0), v3(0, 1, 0), 0.09, 0.012), 'iron')
    add(Torus(pc + v3(0, 0.13, 0), v3(0.2, 0, 1), 0.07, 0.008), 'iron')
    # oakum: two fat coils over the left shoulder and across the chest, a loose end hanging
    axis = norm(v3(1.0, 1.0, 0.2))
    add(Torus(ch + v3(0.0, -0.06 * h, -0.01), axis, 0.215 * b, 0.050), 'oakum', 0.0)
    add(Capsule(ch + v3(0.10, -0.12 * h, 0.15 * b), ch + v3(0.13, -0.30 * h, 0.17 * b), 0.030, 0.022), 'oakum', 0.01)
    # headscarf: cap over the crown, a band, and a knot with two tails at the back; a grey fringe at the temples
    add(Ellipsoid(H + R @ v3(0, 0.045, -0.015) * h, (0.088 * h, 0.075 * h, 0.092 * h), R), 'scarf', 0.01)
    add(Torus(H + R @ v3(0, 0.022, 0.0) * h, R[:, 1], 0.083 * h, 0.014), 'scarf', 0.01)
    kn = H + R @ v3(0.02, 0.03, -0.095) * h
    add(Sphere(kn, 0.03), 'scarf', 0.01)
    for sx, ln in ((-1, 0.10), (1, 0.13)):
        add(Ellipsoid(kn + R @ v3(sx * 0.03, -0.05, -0.03) * h, (0.018, ln * 0.5, 0.012), R), 'scarf', 0.01)
    for sx in (-1, 1):
        add(Ellipsoid(H + R @ v3(sx * 0.072, 0.02, 0.035) * h, (0.016 * h, 0.024 * h, 0.03 * h), R), 'hairg', 0.01)
    # caulking mallet in the right hand (a fat round head, two iron bands), follows item_r
    d = P['item_r']
    if d is not None:
        d = norm(d)
        g = hand_pos(P, 'r')
        butt, tip = g - d * 0.07, g + d * 0.36
        add(Capsule(butt, tip, 0.020, 0.018), 'wood', 0.0)
        sv = norm(np.cross(d, v3(0, 0, 1))) if abs(d[2]) < 0.9 else v3(1, 0, 0)
        hc = tip + d * 0.02
        add(Cylinder(hc - sv * 0.09, hc + sv * 0.09, 0.066, 0.014), 'mallet')
        for k in (-1, 1):
            add(Torus(hc + sv * k * 0.068, sv, 0.069, 0.010), 'iron')
    # the violet rag round her right upper arm
    sh, el = P['sh_r'], P['el_r']
    rag(add, sh + (el - sh) * 0.50, norm(el - sh), 0.056 * b, P, length=0.15, width=0.05)
    mats = {
        'smock': Material(_smock(SMOCK, 0.0), spec=0.04, brush=0.10),
        'smockdk': Material(SMOCK_DK, spec=0.04, brush=0.08),
        'trousers': Material(_hex('#5e5a56'), spec=0.04, brush=0.08),
        'apron': Material(_apron(), spec=0.14, gloss=16, brush=0.07),
        'apron2': Material(_hex('#503522'), spec=0.12, gloss=14, brush=0.06),
        'oakum': Material(_oak(), spec=0.03, brush=0.14),
        'scarf': Material(SCARF, spec=0.04, brush=0.08),
        'hairg': Material(HAIR, spec=0.2, brush=0.1),
        'tar': Material(TARC, spec=0.3, gloss=20),
        'pail': Material(_hex('#4a4e57'), spec=0.5, gloss=26, metal=0.4),
        'mallet': Material(_hex('#8a6440'), spec=0.1, gloss=12, brush=0.08),
        'rag': Material(RAGV, spec=0.08, gloss=8, brush=0.06),
        'skin': Material(_face(P), spec=0.06, gloss=12, sss=0.6, brush=0.02),
    }
    return finish(P, FACTION, parts, mats, end_style='gutter')


def _smock(col, _):
    def fn(p, n):
        a = np.array(col)[None, :].repeat(len(p), 0)
        a = a * (0.88 + 0.22 * fbm(p, 12.0, 2)[:, None])
        patch = (vnoise(p + 2.0, 7.0) > 0.72)[:, None]                       # a darker patch
        a = np.where(patch, a * 0.78, a)
        low = np.clip((0.55 - p[:, 1]) / 0.55, 0, 1)[:, None] * 0.35         # tar and salt at the hem
        return a * (1 - low) + np.array(_hex('#4b4440'))[None, :] * low
    return fn


def _apron():
    def fn(p, n):
        a = np.array(APRON)[None, :].repeat(len(p), 0)
        a = a * (0.85 + 0.3 * fbm(p, 10.0, 2)[:, None])
        st = (vnoise(p * 1.3, 8.0) > 0.66)[:, None]                          # barnacle-bone salt stains
        return np.where(st, a * 0.35 + np.array(BONE)[None, :] * 0.65, a)
    return fn


def _oak():
    def fn(p, n):
        a = np.array(OAKUM)[None, :].repeat(len(p), 0)
        return a * (0.75 + 0.5 * fbm(p * 2.0, 24.0, 2)[:, None])
    return fn


def _face(P):
    f0 = face_albedo(P, _hex('#dcb394'), HAIR, lips=_hex('#9a5a4e'), eyes=_hex('#2a2a2e'))

    def fn(p, n):
        a = f0(p, n)
        q = (p - P['head']) @ head_R(P) / P['height']
        front = q[:, 2] > 0.03
        for sx in (-1, 1):                                                   # laugh lines and crow's feet
            w = ((q[:, 0] - sx * 0.044) / 0.004) ** 2 + ((q[:, 1] + 0.020) / 0.026) ** 2 < 1
            w2 = ((q[:, 0] - sx * 0.056) / 0.010) ** 2 + ((q[:, 1] - 0.0) / 0.004) ** 2 < 1
            a = np.where(((w | w2) & front)[:, None], a * 0.78, a)
        return a
    return fn


ROWS, frames = humanoid_rows(neutral_pose, attack_style='swing', weapon_side='r', cast_side='l')

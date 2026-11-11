"""Shed Husk (Slough token: structure, decoy). An empty shed skin still standing in the shape of the Slough that
left it: coil, rising body, hood up, no arms (the empty sleeves collapsed and hanging), no weapon, eye-holes
empty. Translucent husk pale with ghost bands, no gloss, a slight sag. Idle: a slight flutter, edges lifting.
Death: collapses flat and blows away. Structures are drawn 150/112 larger by the engine, so ppm is 52 / 1.34."""
from _slough_common import *
from kit.xform import Xform

UNIT_ID = 'slough_husk'
N = Naga(height=2.05, tube=0.15, coil_r=0.48, loops=1.7, hood='cobra', accent=(), band_fade=0.25)
CAMERA = Camera(ppm=39.0)
EMPTY = _hex('#3a3428')


def neutral_pose():
    P = naga_pose(N, shake=0.0, gone=0.0)
    P['head_pitch'] = np.radians(10)
    return P


def sleeves(P, add, N, B):
    """Empty arm skins hanging limp from the shoulders, flattened."""
    s = P['s']
    for sd in SIDES:
        if 'sh_' + sd not in P:
            continue
        sx = -1 if sd[0] == 'r' else 1
        sh = P['sh_' + sd]
        sway = 0.04 * np.sin(2 * np.pi * P['tell'] + (0 if sx < 0 else 1.5))
        a = sh + v3(sx * 0.03, -0.04, 0.02) * s
        m = a + v3(sx * 0.05 + sway, -0.24, 0.05) * s
        b = m + v3(sx * 0.01 + sway, -0.20, 0.02) * s
        for p0, p1, w in ((a, m, 0.055), (m, b, 0.042)):
            R = R_from(p1 - p0, v3(-sx * 0.3, 0, 1.0))
            add(Ellipsoid((p0 + p1) / 2, (w * s, np.linalg.norm(p1 - p0) * 0.62, 0.018 * s), R), 'band_skin', 0.02)


def build(P):
    parts, add = new_parts()
    P = dict(P)
    sh = P['shake']
    P['hood'] = 1.0 + 0.07 * np.sin(2 * np.pi * P['tell'])
    bend(P, side=np.radians(1.2) * np.sin(2 * np.pi * P['tell']) + 0.06 * sh)
    B = naga_body(P, add, N, arms=False)
    sleeves(P, add, N, B)
    e_true = P['end']
    P['end'] = 1.0
    mats = {'eye': Material(EMPTY, spec=0.0, rim=0.0), 'pupil': Material(EMPTY, spec=0.0, rim=0.0),
            'band_skin': Material(HUSK, spec=0.0, sss=0.6), 'mouth': Material(EMPTY, spec=0.0, rim=0.0)}
    parts[:] = [Part(Squash(pt.prim, 0.95, 1.0, (0, 0, 0)), pt.mat, pt.k) for pt in parts]
    sc = naga_finish(P, N, parts, mats, B=B)
    for k in ('band_skin', 'eye', 'pupil', 'mouth'):
        sc.materials[k] = mats[k]
    # translucent: soft wrap light through the skin, greyer as it dies
    for m in sc.materials.values():
        m.sss = max(m.sss, 0.7)
        m.spec = 0.0
    g = P['gone']
    if g > 0:
        sc.parts = [Part(Xform(pt.prim, None, tuple(E1 * 0.5 * g + v3(0, 0.1 * g, 0)), 1 - 0.75 * g, (0, 0, 0)),
                         pt.mat, pt.k) for pt in sc.parts]
    return sc


ROWS, frames = token_rows(neutral_pose)

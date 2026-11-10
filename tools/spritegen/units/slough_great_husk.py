"""Great Husk (Slough token: structure, decoy). The lacquered outer coat of a four-armed giant left standing on
the field like a cast-off suit of armour: coil, rising body, a hood as big as a tent, four empty sleeves
hanging, amber lacquer patches still on it. ppm 44 / 1.34 (structures are drawn 150/112 larger)."""
from _slough_common import *
from kit.xform import Xform
from slough_husk import sleeves, EMPTY

UNIT_ID = 'slough_great_husk'
N = Naga(height=2.7, arms=4, girth=1.30, tube=0.21, coil_r=0.60, loops=1.75, coil_back=0.27, hood='broad',
         hood_w=1.2, hood_h=1.15, band_len=0.30, accent=(), body_r=0.19, head_len=1.15, band_fade=0.2)
CAMERA = Camera(ppm=33.0)


def neutral_pose():
    P = naga_pose(N, shake=0.0, gone=0.0)
    P['head_pitch'] = np.radians(10)
    return P


def build(P):
    parts, add = new_parts()
    P = dict(P)
    sh = P['shake']
    P['hood'] = 1.05 + 0.06 * np.sin(2 * np.pi * P['tell'])
    bend(P, side=np.radians(1.0) * np.sin(2 * np.pi * P['tell']) + 0.05 * sh)
    B = naga_body(P, add, N, arms=False)
    sleeves(P, add, N, B)
    lacquer_coat(add, P, B, N, rows=3, per_row=3, coil=False)   # a few patches left, not a full coat
    P['end'] = 1.0
    mats = {'eye': Material(EMPTY, spec=0.0, rim=0.0), 'pupil': Material(EMPTY, spec=0.0, rim=0.0),
            'band_skin': Material(HUSK, spec=0.0, sss=0.6), 'mouth': Material(EMPTY, spec=0.0, rim=0.0)}
    parts[:] = [Part(Squash(pt.prim, 0.95, 1.0, (0, 0, 0)), pt.mat, pt.k) for pt in parts]
    sc = naga_finish(P, N, parts, mats, B=B)
    for k in ('band_skin', 'eye', 'pupil', 'mouth'):
        sc.materials[k] = mats[k]
    for m in sc.materials.values():
        m.sss = max(m.sss, 0.7)
        m.spec = 0.0
    # the amber lacquer survives on the empty coat (dulled a little as it dies)
    lac = Material(lambda p, n: np.array(LACQUER)[None, :] * (0.85 + 0.3 * fbm(p, 9.0, 2)[:, None]),
                   spec=0.5, gloss=40, sss=0.3, brush=0.03)
    sc.materials['lacquer'] = husked({'l': lac}, 0.15 + 0.6 * P['flat'])['l']
    g = P['gone']
    if g > 0:
        sc.parts = [Part(Xform(pt.prim, None, tuple(E1 * 0.5 * g + v3(0, 0.1 * g, 0)), 1 - 0.75 * g, (0, 0, 0)),
                         pt.mat, pt.k) for pt in sc.parts]
    return sc


ROWS, frames = token_rows(neutral_pose)

"""Spitting Olive (Slough common, ranged). Lean olive-skinned krait with faint black bands, reared to 2.0 m, the
hood wide and flat, the throat swollen into a round pale sac that glows chartreuse inside. The right hand is
raised with a short fang sabre held out to the side; the left is on the throat. Spits a thin bright stream (never a cloud).
Defining detail: the inflated throat sac."""
from _slough_common import *

UNIT_ID = 'slough_spitting_olive'
DK_OLIVE = _hex('#2f3619')
N = Naga(**SKINS['olive'], height=2.0, girth=0.90, tube=0.14, coil_r=0.46, loops=1.7, hood='flat', hood_w=1.15,
         pattern='saddles', band_len=0.22, band_dark=0.45, accent=(), hood_mark='ocelli', hood_mark_col=_hex('#e8e07a'),
         tail_side=-1, bracer=_hex('#8a8550'), head_w=1.1)
CAMERA = naga_camera(N)


def neutral_pose():
    P = naga_pose(N, u_sac=v3(0, 0, 0))
    s = P['s']
    P['u_sac'] = P['neck'] + v3(0.0, 0.09, 0.13) * s
    reach(P, 'r', scr(-0.40, 1.42 * s, 0.30))
    reach(P, 'l', P['u_sac'] + v3(0.10, -0.08, 0.05) * s)
    P['item_r'] = sdir(-0.55, 0.85, 0.25)
    return P


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    blade(add, P, 'r', 'sabre', length=0.44, below=0.06)
    s = P['s']
    sp = max(P['spit'], P['venom'] * 0.6, P['cast_glow'])
    sac_r = 0.085 * s * (1 + 0.22 * sp) * (1 - 0.6 * P['flat'])
    add(Sphere(P['u_sac'], sac_r), 'sac', 0.04)
    lights = [Light(P['u_sac'] + v3(0, 0, 0.1), CHART, 0.35 + 0.9 * sp, 0.35)]

    def world(add2):
        if P['spit'] > 0.25:
            F = B['head']
            d = norm(F.d((0, -0.12, 1.0)) + v3(0, 0, 0.2))
            spit_stream(add2, P, B['mouth'] + d * 0.04, d, length=0.55 * P['spit'], n=6)
    mats = {'sac': Material(_hex('#efe4b0'), spec=0.6, gloss=50, sss=0.8,
                            emissive=tuple(np.array(CHART) * (0.30 + 0.7 * sp)))}
    return naga_finish(P, N, parts, mats, lights, world=world)


ROWS, frames = naga_rows(neutral_pose, attack='spit', cast='spit')

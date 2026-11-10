"""Spitting Olive (Slough common, ranged). Lean olive-skinned krait with faint black bands, reared to 2.0 m, the
hood wide and flat, the throat swollen into a round pale sac that glows chartreuse inside. No weapon: the right
hand raised palm-out as if aiming, the left on the throat. Spits a thin bright stream (never a cloud).
Defining detail: the inflated throat sac."""
from _slough_common import *

UNIT_ID = 'slough_spitting_olive'
DK_OLIVE = _hex('#2f3619')
N = Naga(height=2.0, girth=0.88, tube=0.135, coil_r=0.46, loops=1.7, hood='flat', hood_w=1.12,
         dark=DK_OLIVE, light=OLIVE, band_len=0.26, band_dark=0.38, accent=(), belly=GOLD,
         skin=_hex('#6d7a3a'), mantle=_hex('#3b4422'), hood_face=_hex('#4a5428'), hood_rim=_hex('#c9c48e'),
         lip=_hex('#e0c060'), tail_side=-1)
CAMERA = naga_camera(N)


def neutral_pose():
    P = naga_pose(N, u_sac=v3(0, 0, 0))
    s = P['s']
    P['u_sac'] = P['neck'] + v3(0.0, 0.09, 0.13) * s
    reach(P, 'r', v3(-0.20, 1.62 * s, 0.46))
    reach(P, 'l', P['u_sac'] + v3(0.10, -0.08, 0.05) * s)
    return P


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
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

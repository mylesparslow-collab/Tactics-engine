"""Old Sounding (Overcurrent hero). An ancient cloud-whale that fell once already and climbed back: a vast
scarred pearl-grey body with healed gashes, a nicked flipper, crusts of barnacles along the head and jaw, a deep
sunk eye ringed in pearl, a pleated throat that glows like a struck bell, a thunderhead of cloud heaped on its
back, and curtains of rain trailing off every edge. Defining detail: the scars and barnacles under the rain
curtains. Tell: slow body wave, throat-light breathing like a tolling bell, rain streaming off the flukes."""
from _overcurrent_w2 import *

UNIT_ID = 'overcurrent_old_sounding'
CAMERA = Camera(ppm=44)
LK = 0.57


def neutral_pose():
    return pose()


def build(P):
    parts, add = new_parts()
    st, op = P['strike'], P['open']
    pl = Placer(P, yaw=0.5, pitch=-0.25, hover=0.28, shift=0.24, back=0.1)
    info = whale(add, P, L=LK, head=1.2, y0=0.78, jaw_open=0.55 + 0.7 * op, flip=1.15, fluke=1.15, seed=7, tail_lift=0.3, barn=14, scars=True)
    clouds = cloud_mantle(add, P, LK, 0.78, n=11, big=1.35, info=info)
    # thunderhead: a tall heap on the shoulders
    for (z, dy, r) in [(0.1, 0.25, 0.22), (-0.1, 0.38, 0.19), (0.3, 0.20, 0.16), (-0.3, 0.30, 0.15)]:
        c = clouds[3] + v3(0.02, dy * LK, z * LK)
        add(Sphere(c, r * LK * 1.4), 'cloud', 0.12)
    # nicked flipper: notch cut by a little bite of sky on the left flipper tip (a few ragged spikes)
    for j in range(3):
        q = v3(-0.55 * LK * 1.15 + 0.04 * j, 0.78 - 0.52 * LK * 1.15 - 0.03 * j, 0.45 * LK - 0.30 * LK * 1.15)
        add(Capsule(q, q + v3(-0.04, -0.07, 0.0), 0.012, 0.004), 'bonef', 0.0)
    mats = std_mats(P, {
        'skin': whale_mats(P, pl, scars=True, old=True),
        'fin': skin(top=_hex('#a7bad4'), under=_hex('#f0eeff'), glow=0.85, mottle=0.08, spec=0.3, wet=40, local=pl.inv, veins=0.55, vein_col=_hex('#6f84ae'), vfreq=16.0),
        'cloud': skin(top=_hex('#aab6cc'), under=_hex('#e6eaf6'), glow=0.5, mottle=0.2, spec=0.0, wet=5, local=pl.inv),
        'pleat': Material(_hex('#aee9f0'), emissive=tuple(np.array(CYAN) * (0.7 + 0.4 * np.sin(2 * np.pi * P['tell']) + 0.8 * P['cast_glow']) * P['glow']), spec=0.5, gloss=50, rim=0.0),
        'baleen': Material(_hex('#f1d4dc'), spec=0.4, gloss=40, sss=0.5),
        'eyesock': Material(_hex('#8fa4c8'), spec=0.4, gloss=40),
        'eyeb': Material(_hex('#10162a'), spec=1.0, gloss=90),
        'maw': Material(_hex('#7c2c48'), spec=0.4, gloss=30, rim=0.1),
        'bonef': Material(_hex('#f4f2e8'), spec=0.4, gloss=40),
        'barn': Material(_hex('#ebe3cf'), spec=0.3, gloss=20, brush=0.1),
        'rain': Material(_hex('#d6f2ff'), spec=1.0, gloss=100, emissive=tuple(np.array(CYAN) * 0.6), rim=0.4)})
    anchors = [clouds[i] + v3(0, -0.2, 0) for i in (1, 3, 5, 7, 9)] + [info['tail'] + v3(0.2, 0, 0), info['tail'] + v3(-0.2, 0, 0)]
    wa = [pl.pt(a) for a in anchors]
    lights = [under_light(P, v3(0, 0.15, 0.2), 1.2, 2.2)]

    def world(add2):
        rain_curtain(add2, P, wa, L=0.75, n_each=2, seed=4)
        spray(add2, P, pl.pt(v3(0, 1.3, 0.5)), n=7, up=0.8)
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.3, 0.9, 1.0, 0.3), atk_strike=(0.0, 0.5, 1.0, 0.3), idle_amp=0.7)

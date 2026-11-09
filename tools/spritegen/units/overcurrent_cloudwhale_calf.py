"""Cloudwhale Calf (Overcurrent, tank). A young cloud-whale, slow and enormous: a big blunt head with a pearl
baleen fringe, a throat of glowing pleat ridges, long finned flippers, broad flukes, and a mantle of cloud
clinging to its back and shredding rain from its belly. Defining detail: the glowing pleated throat and the
rain-shedding cloud mantle. Tell: slow body wave, belly light breathing, drops rising and falling."""
from _overcurrent_w2 import *

UNIT_ID = 'overcurrent_cloudwhale_calf'
CAMERA = Camera(ppm=44)
LK = 0.50


def neutral_pose():
    return pose()


def build(P):
    parts, add = new_parts()
    st, op = P['strike'], P['open']
    pl = Placer(P, yaw=0.55, pitch=-0.12, hover=0.25, shift=0.28, back=0.1)
    info = whale(add, P, L=LK, head=1.12, y0=0.78, jaw_open=0.55 + 0.7 * op, flip=1.0, fluke=1.0, seed=2, tail_lift=0.35)
    clouds = cloud_mantle(add, P, LK, 0.78, n=8, big=1.0, info=info)
    mats = std_mats(P, {
        'skin': whale_mats(P, pl),
        'fin': skin(top=_hex('#b5cbe4'), under=_hex('#f4f2ff'), glow=0.8, mottle=0.05, spec=0.3, wet=40, local=pl.inv, veins=0.4, vein_col=_hex('#7a90b8'), vfreq=18.0),
        'cloud': skin(top=_hex('#c9d4e6'), under=_hex('#f0f2fc'), glow=0.5, mottle=0.16, spec=0.0, wet=5, local=pl.inv),
        'pleat': Material(_hex('#aee9f0'), emissive=tuple(np.array(CYAN) * (0.55 + 0.35 * np.sin(2 * np.pi * P['tell'])) * P['glow']), spec=0.5, gloss=50, rim=0.0),
        'baleen': Material(_hex('#f4dde4'), spec=0.4, gloss=40, sss=0.5),
        'eyesock': Material(_hex('#b9ccec'), spec=0.4, gloss=40),
        'maw': Material(_hex('#7c2c48'), spec=0.4, gloss=30, rim=0.1),
        'bonef': Material(_hex('#eef0fa'), spec=0.4, gloss=40),
        'barn': Material(_hex('#e8e2d4'), spec=0.3, gloss=20),
        'rain': Material(_hex('#d6f2ff'), spec=1.0, gloss=100, emissive=tuple(np.array(CYAN) * 0.6), rim=0.4)})
    anchors = [clouds[1] + v3(0, -0.25, 0), clouds[3] + v3(0.1, -0.4, 0), clouds[5] + v3(-0.1, -0.4, 0), clouds[7] + v3(0, -0.3, 0)]
    # rain falls in world space beneath the body: map through the placer
    wa = [pl.pt(a) for a in anchors]
    lights = [under_light(P, v3(0, 0.15, 0.2), 1.1, 2.0)]

    def world(add2):
        rain_curtain(add2, P, wa, L=0.55, n_each=2)
        spray(add2, P, pl.pt(v3(0, 1.2, 0.5)), n=6, up=0.7)
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.3, 0.8, 1.0, 0.3), atk_strike=(0.0, 0.5, 1.0, 0.3), idle_amp=0.8)

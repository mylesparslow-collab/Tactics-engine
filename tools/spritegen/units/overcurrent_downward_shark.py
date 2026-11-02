"""Downward Shark (Overcurrent burst). A frilled, goblin-jawed shark falling point-first: blade snout, jaw already
slung forward on its ligament with needle teeth open, red gill frills flared, water streaming upward off its pale
pink skin. It reaches the ground before its scream does.
Defining detail: the jaw is extended and the teeth are open before it arrives. Tell: the frills flutter, drops stream up."""
from _overcurrent_common import *

UNIT_ID = 'overcurrent_downward_shark'
CAMERA = Camera(ppm=46)


def neutral_pose():
    return pose(open=0.35)


def build(P):
    parts, add = new_parts()
    ph, st, op = P['ph'], P['strike'], P['open']
    F = Frame((0, 0, 0), rot_x(0.0), 1.0)
    ext = 0.55 + 0.45 * st
    J = goblin(F, add, ph=ph, ext=ext, gape=0.25 + 0.75 * op)
    pl = Placer(P, yaw=0.95, pitch=0.50 + 0.15 * st, hover=0.95 - 0.2 * st, shift=0.0, back=0.15, scale=0.72)
    organs = [Organ(pl.pt(v3(0, -0.02, -0.1)), (0.10, 0.10, 0.28), _hex('#e08aa0'), 0.0, 0.6),
              Organ(pl.pt(v3(0, 0.0, 0.15)), (0.06, 0.07, 0.07), _hex('#c4344a'), 0.0, 0.6)]
    mats = std_mats(P, {'skin': skin(top=_hex('#d6a8bc'), under=_hex('#f6dce6'), organs=organs, veins=0.3, glow=0.7,
                                     local=pl.inv, depth=0.4, spec=0.4, mottle=0.05)})
    lights = [under_light(P, v3(0, 0.2, 0), 1.0, 1.4)]
    streams = [pl.pt(v3(sx * 0.2, 0.2 + 0.1 * i, -0.4 - 0.25 * i)) for i, sx in enumerate((-1, 1, -1, 1))]

    def world(add2):
        # water rising off the falling body
        for i, q in enumerate(streams):
            if P['end'] > 0.3:
                break
            t = (P['tell'] + i * 0.27) % 1.0
            add2(Sphere(q + v3(0, 0.15 + 0.7 * t, 0), 0.026 * (1.2 - 0.6 * t)), 'water', 0.0)
            add2(Sphere(q + v3(0.05, 0.5 + 0.5 * t, -0.04), 0.018 * (1.2 - 0.6 * t)), 'water', 0.0)
        spray(add2, P, pl.pt(J.p((0, 0, 0.3))))
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.3, 0.8, 1.0, 0.4), atk_strike=(0.0, 0.5, 1.0, 0.3), idle_amp=0.7)

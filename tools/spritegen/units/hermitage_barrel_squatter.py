"""Barrel Squatter (Hermitage cheap body). A tarred hogshead with three iron hoops on four violet legs, tilted back,
mouth forward-down, one big orange-tipped claw and two eyestalks out of the mouth. Whole unit ~1.1 m (big dog).
Defining detail: the knocked-out bung-hole on top with a third eyestalk poking through it."""
from _hermitage_common import *

UNIT_ID = 'hermitage_barrel_squatter'
SIZE = 1.0             # 'small' class body, crab scaled up so its front fills the barrel mouth
CAMERA = size_camera('small')

SHELL = Shell(
    build=barrel_shell(length=0.80, r_mid=0.32, r_end=0.265),
    ride=0.31, tilt=-0.06, crab_at=(0, -0.10, 0.53), crab_upright=0.8, z0=-0.92, x0=0.30, yaw=0.15, shield=1.15,
    eye_len=0.32, span=0.46,
    extra_eyes=(((0.0, 0.25, -0.02), (0.05, 1.0, -0.05), 0.24),),       # the bung-hole eye
    big=1.35, small=0.70, side_r=0.30)


def neutral_pose():
    return hermit_pose(open=0.35)


def build(P):
    return shelled(P, SIZE, SHELL)


def _fit(R):
    for row in R.values():
        for P, o in row:
            P['snap'] *= 0.7       # keep the snap (and its strokes) inside the frame
    return R


ROWS, frames = hermit_rows(neutral_pose, 'shell', extra=_fit)

"""Barrel Squatter (Hermitage cheap body). A tarred hogshead with three iron hoops on four violet legs, tilted back,
mouth forward-down, one big orange-tipped claw and two eyestalks out of the mouth. Whole unit ~1.1 m (big dog).
Defining detail: the knocked-out bung-hole on top with a third eyestalk poking through it."""
from _hermitage_common import *

UNIT_ID = 'hermitage_barrel_squatter'
SIZE = 'small'
CAMERA = size_camera(SIZE)

SHELL = Shell(
    build=barrel_shell(length=0.88, r_mid=0.35, r_end=0.29),
    ride=0.56, tilt=0.24, crab_at=(0, -0.04, 0.30), crab_pitch=-0.40, z0=-0.36, x0=0.10,
    feet=((-0.40, 0.36), (0.42, 0.34), (-0.50, -0.20), (0.50, -0.22)),
    leg_roots=((-0.15, -0.17, 0.33), (0.15, -0.17, 0.33), (-0.24, -0.22, -0.04), (0.24, -0.22, -0.04)),
    eyes=(((-0.09, 0.12, 0.40), (-0.30, 1.0, 0.20), 0.44),
          ((0.09, 0.12, 0.40), (0.30, 1.0, 0.20), 0.44),
          ((0.0, 0.30, -0.02), (0.05, 1.0, -0.05), 0.24)),       # the bung-hole eye
    big=1.35, small=0.5, side_r=0.33)


def neutral_pose():
    return hermit_pose(open=0.35)


def build(P):
    return shelled(P, SIZE, SHELL)


ROWS, frames = hermit_rows(neutral_pose, 'shell')

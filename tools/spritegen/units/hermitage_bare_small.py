"""Bare Scuttler (hermitage_bare_small; also Hopeful). Big-dog-sized evicted crab, ~1.0-1.1 m to the top of the
raised claw: side-on crouch, big claw up, the pale tail curled in a fat spiral as big as the body."""
from _hermitage_common import *

UNIT_ID = 'hermitage_bare_small'
SIZE = 0.86            # a touch over the 'small' scale: dog-to-pony, never tiny
CAMERA = size_camera('small')
BARE = Bare(h=0.46, yaw=0.62, leg_len=1.05, z0=-0.36, x0=0.18, big=1.3, small=0.55, eye_len=0.36,
            tail=dict(size=1.32, center=(0, 0.20, -0.36), r0=0.25, r1=0.06, thick=(0.16, 0.04), turns=1.08))


def neutral_pose():
    return hermit_pose(raise_=1.0, rear=0.18, open=0.3)


def build(P):
    return bare(P, SIZE, BARE)


ROWS, frames = hermit_rows(neutral_pose, 'bare')

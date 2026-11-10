"""Bare Scuttler (hermitage_bare_small; also Hopeful). Big-dog-sized evicted crab, ~1.0-1.1 m to the top of the
raised claw: side-on crouch, big claw up, the pale tail curled in a fat spiral as big as the body."""
from _hermitage_common import *

UNIT_ID = 'hermitage_bare_small'
SIZE = 0.86            # a touch over the 'small' scale: dog-to-pony, never tiny
CAMERA = size_camera('small')
BARE = Bare(h=0.38, yaw=0.80, leg_len=0.95, z0=-0.36, x0=0.18, big=1.3, small=0.55, eye_len=0.36,
            tail=dict(size=1.45, center=(0, 0.20, -0.34), r0=0.25, r1=0.06, thick=(0.16, 0.04), turns=1.08))


def neutral_pose():
    return hermit_pose(raise_=0.85, rear=0.08, open=0.45, lean=0.06)


def build(P):
    return bare(P, SIZE, BARE)


def _fit(R):
    for row in R.values():
        for P, o in row:
            P['snap'] *= 0.7       # keep the lunge inside the 96 px frame
    for P, o in R['death']:
        P['raise_'] = max(P['raise_'], 0.0) * 0.5
    return R


ROWS, frames = hermit_rows(neutral_pose, 'bare', extra=_fit)

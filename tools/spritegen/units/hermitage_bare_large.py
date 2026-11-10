"""Bare Brute (hermitage_bare_large; also Old Knell, Bare). Horse-sized evicted crab, ~1.8 m: low and wide, both
claws spread, the pale tail dragging on the ground. Defining detail: barnacle clusters on the big claw (it has
been housed a long time)."""
from _hermitage_common import *

UNIT_ID = 'hermitage_bare_large'
SIZE = 1.12   # 'large' class, trimmed so both spread claws and the tail fit the frame
CAMERA = size_camera('large')
BARE = Bare(h=0.40, yaw=0.10, leg_len=1.05, z0=-0.52, x0=0.12, big=1.35, small=0.75, eye_len=0.30, barn=2,
            feet=((-0.52, 0.38), (0.62, 0.34), (-0.58, -0.26), (0.66, -0.24)),
            tail=dict(size=1.15, center=(0, 0.02, -0.46), r0=0.25, r1=0.06, thick=(0.16, 0.04), turns=0.95))


def neutral_pose():
    return hermit_pose(raise_=0.75, spread=1.0, rear=0.0, open=0.45, lean=0.05)


def build(P):
    return bare(P, SIZE, BARE)


def _fit(R):
    for row in R.values():
        for P, o in row:
            P['snap'] *= 0.6       # two spread claws at this size: keep the lunge inside the frame
            P['drum'] *= 0.7
    return R


ROWS, frames = hermit_rows(neutral_pose, 'bare', extra=_fit)

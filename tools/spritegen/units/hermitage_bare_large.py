"""Bare Brute (hermitage_bare_large; also Old Knell, Bare). Horse-sized evicted crab, ~1.8 m: low and wide, both
claws spread like a wrestler, the heavy pink abdomen sagging and dragging under it. Defining detail: barnacle
clusters on the big claw (it has been housed a long time)."""
from _hermitage_common import *

UNIT_ID = 'hermitage_bare_large'
SIZE = 1.15   # 'large' class
CAMERA = size_camera('large')
BARE = Bare(h=0.30, yaw=0.05, pitch=0.04, z0=-0.50, x0=0.32, big=1.40, small=1.0, eye_len=0.24, eye_bead=0.058,
            span=0.50, spread=1.3, leg_len=1.0, leg_r=1.25, shield=1.15, arm=1.2, fat=1.05, barn=2,
            tail=dict(size=1.10, thick=(0.17, 0.06), side=-0.5, drop=0.05, sag=0.6))


def neutral_pose():
    return hermit_pose(raise_=0.15, spread=1.0, open=0.45, lean=0.03)


def build(P):
    return bare(P, SIZE, BARE)


def _fit(R):
    for row in R.values():
        for P, o in row:
            P['snap'] *= 0.6       # two spread claws at this size: keep the lunge inside the frame
            P['drum'] *= 0.5
    return R


ROWS, frames = hermit_rows(neutral_pose, 'bare', extra=_fit)

"""Bare Snapper (hermitage_bare_medium; also Sixpence, Bare). Pony-sized evicted crab, ~1.4 m to the top of the
claw: reared up on its back legs, the big claw held over its head like a grievance, one claw clearly twice the size
of the other, the soft pink abdomen hanging and curled under it."""
from _hermitage_common import *

UNIT_ID = 'hermitage_bare_medium'
SIZE = 'medium'
CAMERA = size_camera(SIZE)
BARE = Bare(h=0.36, yaw=0.30, z0=-0.58, x0=0.40, big=1.55, small=0.70, eye_len=0.30, eye_bead=0.068,
            span=0.42, leg_len=1.0, leg_r=1.05,
            tail=dict(size=1.05, thick=(0.15, 0.05), side=-0.6, drop=0.02))


def neutral_pose():
    return hermit_pose(raise_=1.0, rear=0.32, open=0.35)


def build(P):
    return bare(P, SIZE, BARE)


def _fit(R):
    for row in R.values():
        for P, o in row:
            P['snap'] *= 0.75      # keep the lunge inside the 96 px frame
            P['drum'] *= 0.6
    for P, o in R['death']:
        P['raise_'] = max(P['raise_'], 0.0) * 0.4
    return R


ROWS, frames = hermit_rows(neutral_pose, 'bare', extra=_fit)

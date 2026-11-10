"""Bare Snapper (hermitage_bare_medium; also Sixpence, Bare). Pony-sized evicted crab, ~1.4 m to the top of
the claw: reared on its back legs, the big claw held over its head like a grievance, one claw clearly twice
the size of the other, pale tail curled tight behind."""
from _hermitage_common import *

UNIT_ID = 'hermitage_bare_medium'
SIZE = 'medium'
CAMERA = size_camera(SIZE)
BARE = Bare(h=0.50, yaw=0.65, leg_len=1.12, z0=-0.38, x0=0.20, big=1.4, small=0.55, eye_len=0.36,
            tail=dict(size=1.15, center=(0, 0.26, -0.40), r0=0.25, r1=0.06, thick=(0.15, 0.035), turns=1.05))


def neutral_pose():
    return hermit_pose(raise_=1.15, rear=0.45, open=0.25)


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

"""Bare Scuttler (hermitage_bare_small; also Hopeful). Big-dog-sized evicted crab, ~1.0 m to the top of the raised
claw. Nervous youngster: huge glossy eyes on tall stalks, a claw far too big for it held up in a jittery guard, legs
set high and wide, and the soft pink abdomen curled tight under itself and off to one side."""
from _hermitage_common import *

UNIT_ID = 'hermitage_bare_small'
SIZE = 1.0            # a touch over the 'small' scale: dog-to-pony, never tiny
CAMERA = size_camera('small')
BARE = Bare(h=0.34, yaw=0.10, pitch=-0.06, z0=-0.38, x0=0.20, big=1.75, small=0.72, eye_len=0.34, eye_bead=0.088,
            span=0.40, leg_len=1.0, leg_r=0.95, shield=0.95, arm=0.9,
            tail=dict(size=0.95, thick=(0.16, 0.05), side=-0.7))


def neutral_pose():
    return hermit_pose(raise_=0.35, open=0.45, rear=0.10, eye_l=0.15, eye_r=-0.15)


def build(P):
    return bare(P, SIZE, BARE)


def _fit(R):
    for i, (P, o) in enumerate(R['idle']):          # jittery: quick sidestep, eyes darting
        P['slide'] += [0, .06, -.02, .04][i]
        P['eye_l'] += [.2, -.3, .4, -.1][i]
        P['eye_r'] += [-.3, .2, -.1, .3][i]
    for row in R.values():
        for P, o in row:
            P['snap'] *= 0.6
            P['drum'] *= 0.5
    for i, (P, o) in enumerate(R['death']):         # the collapse spreads toward the viewer: keep it off the edge
        P['recoil'] += [0, 0.03, 0.07, 0.07][i]
    return R


ROWS, frames = hermit_rows(neutral_pose, 'bare', extra=_fit)

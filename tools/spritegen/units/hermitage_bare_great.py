"""Bare Giant (hermitage_bare_great; also Duchess Abaft, Bare). Hay-wagon-sized evicted crab, ~2.4 m: massive
forequarters (a broad barnacled head shield, arms like hawsers, a huge scarred orange-tipped claw), eyestalks
swivelled round at the viewer, and under all that armour a great soft pink abdomen sagging out to one side.
Something this big should never be this soft."""
from _hermitage_common import *

UNIT_ID = 'hermitage_bare_great'
SIZE = 1.42   # 'great' class at ppm 44: fills the frame
CAMERA = size_camera('great')
BARE = Bare(h=0.40, yaw=0.10, pitch=0.02, z0=-0.56, x0=0.42, big=1.70, small=0.90, eye_len=0.30, eye_bead=0.060,
            span=0.46, spread=1.2, leg_len=1.05, leg_r=1.45, shield=1.45, arm=1.6, fat=1.15, barn=2, scar=True,
            shield_barn=2, tail=dict(size=1.30, thick=(0.18, 0.06), side=-0.8, drop=0.02, sag=0.8))


def neutral_pose():
    return hermit_pose(raise_=0.0, spread=0.4, rear=0.12, open=0.30, eye_l=-0.5, eye_r=-0.7)


def build(P):
    return bare(P, SIZE, BARE)


def _eyes(R):
    """eyestalks stay swivelled round at the viewer in every row"""
    for row in R.values():
        for P, o in row:
            P['eye_l'] -= 0.5
            P['eye_r'] -= 0.6
            P['snap'] *= 0.55          # keep the lunge inside the frame at this size
            P['drum'] *= 0.45
    return R


ROWS, frames = hermit_rows(neutral_pose, 'bare', extra=_eyes)

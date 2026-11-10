"""Bare Giant (hermitage_bare_great; also Duchess Abaft, Bare). Hay-wagon-sized evicted crab, ~2.4 m: tall,
the tail a huge pale coil (the largest shape in the frame), the big claw scarred and orange-tipped,
eyestalks swivelled round at the viewer. Something this big should never be this soft."""
from _hermitage_common import *

UNIT_ID = 'hermitage_bare_great'
SIZE = 1.40   # 'great' class, trimmed so the coil and claw fit at ppm 44
CAMERA = size_camera('great')
BARE = Bare(h=0.50, yaw=0.35, leg_len=1.1, z0=-0.32, x0=0.18, big=1.3, small=0.6, eye_len=0.36,
            feet=((-0.42, 0.32), (0.52, 0.30), (-0.46, -0.24), (0.54, -0.22)),
            tail=dict(size=1.32, center=(0, 0.30, -0.30), r0=0.25, r1=0.06, thick=(0.165, 0.04), turns=1.1))


def scarred(p, n):
    a = chitin(VIOLET, amt=0.06)(p, n)
    sc = (np.abs(vnoise(p * v3(1, 3, 1), 6.0) - 0.5) < 0.03)[:, None]
    return np.where(sc, np.array(BONE)[None, :] * 0.85, a)


def neutral_pose():
    return hermit_pose(raise_=0.9, rear=0.25, open=0.2, eye_l=-0.6, eye_r=-0.9)


def build(P):
    return bare(P, SIZE, BARE, mats={'claw': Material(scarred, spec=0.55, gloss=34, brush=0.04)})


def _eyes(R):
    """eyestalks stay swivelled round at the viewer in every row"""
    for row in R.values():
        for P, o in row:
            P['eye_l'] -= 0.6
            P['eye_r'] -= 0.8
    return R


ROWS, frames = hermit_rows(neutral_pose, 'bare', extra=_eyes)

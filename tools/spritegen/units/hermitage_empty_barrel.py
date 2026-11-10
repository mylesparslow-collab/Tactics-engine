"""Empty Barrel (Hermitage structure). A tarred hogshead on its side, three hoops, bung out, the knocked-out head
toward the camera so the inside reads tar-black, a violet 'Vacant' rag tied round it. ~1.0 m long.
Rows: idle (the rag stirs), hit, death (cracks spread, staves split off)."""
from _hermitage_common import *

UNIT_ID = 'hermitage_empty_barrel'
CAMERA = Camera(ppm=56)
L, RM, RE = 0.98, 0.37, 0.31
SHELL = Shell(build=barrel_shell(length=L, r_mid=RM, r_end=RE), ride=RM, crab_at=(0, 0, 0))
PLACE = (v3(0.02, RM - 0.01, -0.30), rot_y(0.30) @ rot_z(0.5))


def neutral_pose():
    return hermit_pose()


def build(P):
    return empty(P, SHELL, PLACE, rag_at=((0, 0, -0.20), (0, 0, 1), RM))


ROWS, frames = structure_rows(neutral_pose)

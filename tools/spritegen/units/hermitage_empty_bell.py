"""Empty Bell (Hermitage structure). A cracked verdigris bronze chapel bell lying tipped on its lip, mouth toward
the camera and dark inside, the clapper hauled up and lashed with rope so it does not ring for nobody, a violet
'Vacant' rag on the crown loop. ~1.4 m."""
from _hermitage_common import *

UNIT_ID = 'hermitage_empty_bell'
CAMERA = Camera(ppm=54)
H = 0.95
SHELL = Shell(build=chapel_bell_shell(h=H, r_bot=0.50, r_top=0.27, rope=False), ride=H / 2, crab_at=(0, 0, 0))
PLACE = (v3(0.12, 0.43, -0.42), rot_y(-0.45) @ rot_x(-1.05))


def neutral_pose():
    return hermit_pose()


def build(P):
    return empty(P, SHELL, PLACE, rag_at=((0, 0.08, 0), (0, 1, 0), 0.31))


ROWS, frames = structure_rows(neutral_pose)

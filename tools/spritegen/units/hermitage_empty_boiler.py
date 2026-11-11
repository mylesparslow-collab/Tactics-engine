"""Empty Boiler (Hermitage structure). A rust-brown riveted ship's boiler rolled on its side, firebox door hanging
open toward the camera with a faint amber glow inside (still cooling), a violet 'Vacant' rag round the stub
funnel. ~1.6 m long."""
from _hermitage_common import *

UNIT_ID = 'hermitage_empty_boiler'
CAMERA = Camera(ppm=46)
R = 0.48
SHELL = Shell(build=boiler_shell(length=1.25, r=R, door=0.9, glow=0.22, funnel_h=0.34), ride=R, crab_at=(0, 0, 0))
PLACE = (v3(0.18, R, -0.52), rot_y(0.05) @ rot_z(0.30))


def neutral_pose():
    return hermit_pose()


def build(P):
    return empty(P, SHELL, PLACE, rag_at=((0, 0, -0.18), (0, 0, 1), R + 0.01),
                 lights=[Light(PLACE[0] + PLACE[1] @ v3(0, -0.06, 0.80), LAMP, 0.35 * (1 - P['crack']), 0.4)])


ROWS, frames = structure_rows(neutral_pose)

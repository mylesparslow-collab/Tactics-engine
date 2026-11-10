"""Empty Diving Bell (Hermitage structure). A brass diving bell standing open-mouthed on its rim, three dark
portholes, a coil of air-hose, a violet 'Vacant' rag tied to the lifting eye. ~1.4 m."""
from _hermitage_common import *

UNIT_ID = 'hermitage_empty_diving_bell'
CAMERA = Camera(ppm=54)
H = 0.98
SHELL = Shell(build=diving_bell_shell(h=H, r_bot=0.50, r_top=0.36, ports=((-0.62, 1.0), (0.42, 1.0), (2.7, 1.0)),
                                      port_y=0.06, hose=True, eyes_in=()), ride=H / 2, crab_at=(0, 0, 0))
PLACE = (v3(0.08, H / 2 - 0.02, -0.32), rot_y(0.15) @ rot_x(-0.05))


def neutral_pose():
    return hermit_pose()


def build(P):
    return empty(P, SHELL, PLACE, rag_at=((0, -0.30, 0), (0, 1, 0), 0.50))


ROWS, frames = structure_rows(neutral_pose)

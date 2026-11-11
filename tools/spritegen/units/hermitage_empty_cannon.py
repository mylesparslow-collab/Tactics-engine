"""Empty Cannon (Hermitage structure). A Concord long gun with its carriage gone, lying on the salt with the
breech knocked open toward the camera (dark inside), muzzle ring, trunnions, a violet 'Vacant' rag round the
chase. ~2.0 m. The biggest prize in the queue: kept to one clean silhouette."""
from _hermitage_common import *

UNIT_ID = 'hermitage_empty_cannon'
CAMERA = Camera(ppm=46)
GL, RBR, RMZ = 1.95, 0.25, 0.15
SHELL = Shell(build=long_gun_shell(length=GL, r_breech=RBR, r_muzzle=RMZ, open_breech=True, bore=0.075),
              ride=RBR, crab_at=(0, 0, 0))
_tilt = np.arctan2(RBR - RMZ - 0.035, GL)          # rests on breech and muzzle ring, so it slopes a touch
PLACE = (v3(0.42, RBR + 0.005 - 0.5 * (RBR - RMZ), -0.62), rot_y(1.95) @ rot_x(-_tilt))


def neutral_pose():
    return hermit_pose()


def build(P):
    return empty(P, SHELL, PLACE, rag_at=((0, 0, GL * 0.18), (0, 0, 1), RBR - (RBR - RMZ) * 0.68 + 0.005))


ROWS, frames = structure_rows(neutral_pose)

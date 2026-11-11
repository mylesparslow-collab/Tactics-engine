"""Gun-Deck Lodger (Hermitage long ranged). A horse-sized crab wearing a Concord naval long gun with no carriage:
the breech end rests on the salt behind it, the barrel rides on the crab's back and points forward and up over its
head, and the crab's face, eyestalks, claws and legs spill out from under the trunnions. ~1.8 m, ppm 48.
Defining detail: the muzzle ring and the recoil (the whole crab skids back a step on the hit frame)."""
from _hermitage_common import *

UNIT_ID = 'hermitage_gun_deck_lodger'
SIZE = 1.34            # 'large' class; crab scaled up so its face and claws read clearly under the muzzle
CAMERA = size_camera('large')
GUN_L = 1.16

SHELL = Shell(
    build=long_gun_shell(length=GUN_L, r_breech=0.27, r_muzzle=0.14, open_breech=True, bore=0.075),
    ride=0.52, tilt=-0.24, crab_at=(0, -0.30, 0.36), crab_upright=1.0, z0=-0.87, x0=0.30, yaw=0.32,
    eye_len=0.32, eye_bead=0.066, span=0.46, duck_dir=(0, 0.6, -1.0), duck_depth=0.22,
    big=1.40, small=0.82, guard=((0.25, -0.20, 0.17), (-0.42, 0.12, 0.90)), side_r=0.30, tip_angle=0.9, lie=-0.05, leg_r=1.1)


def neutral_pose():
    return hermit_pose(open=0.35, spread=0.3)


def build(P):
    F = shell_frame(P, SHELL)
    muzzle = F.p((0, 0, GUN_L / 2 + 0.06))

    def world(add):
        f = P['fire']
        if f > 0:
            add(Sphere(muzzle + F.v((0, 0, 0.10)), 0.07 + 0.09 * f), 'flash', 0.0)
            add(Ellipsoid(muzzle + F.v((0, 0, 0.22)), (0.07 * f, 0.07 * f, 0.16 * f), F.R), 'flame', 0.0)
        emit(add, muzzle + F.v((0, 0, 0.08)), 'smoke', 1.4 * f + 0.5 * P['fx'] * (f == 0))
    return shelled(P, SIZE, SHELL, world=world)


def _rows(R):
    # attack = Round Shot: brace, aim (muzzle lifts), FIRE (flash + skid back a step), settle
    for i, (P, o) in enumerate(R['attack']):
        P['cock'] = 0.0
        P['snap'] = 0.0
        P['open'] = [0.3, 0.2, 0.5, 0.3][i]
        P['lean'] = [-0.03, -0.07, -0.13, -0.05][i]
        P['recoil'] = [0.0, 0.0, 0.08, 0.06][i]
        P['fire'] = [0.0, 0.0, 1.0, 0.0][i]
        P['fx'] = [0.0, 0.0, 1.0, 0.4][i]
        P['lift_a'] = [0, 0, 0.6, 0][i]
        P['squash'] = [1.0, 0.97, 1.02, 1.0][i]
        P['slide'] += 0.05                     # room for the skid back
    for P, o in R['cast']:
        P['drum'] *= 0.6
    for row in R.values():
        for P, o in row:
            P['snap'] *= 0.7
    # death: the gun slumps level and rolls part-way onto its side, one claw lolling out from under it
    for i, (P, o) in enumerate(R['death']):
        P['tip'] = min(P['tip'], 0.75)
        P['limp'] *= 0.45
        k = [0, 0.3, 0.85, 1.0][i]  # topple forward onto the shadow, not behind it
        P['slide'] += -0.03 * k
        P['recoil'] += -0.10 * k
    fit_rows(R, stride=0.5)
    return R


ROWS, frames = hermit_rows(neutral_pose, 'shell', extra=_rows)

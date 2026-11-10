"""Gun-Deck Lodger (Hermitage long ranged). A horse-sized crab living in a Concord naval long gun with no carriage:
the crab braced on four legs under the breech end, the barrel pointing forward over its head, claws out under
the gun either side, eyestalks up either side of the barrel. ~1.8 m, ppm 48.
Defining detail: the muzzle ring and the recoil (the whole crab skids back a step on the hit frame)."""
from _hermitage_common import *

UNIT_ID = 'hermitage_gun_deck_lodger'
SIZE = 'large'
CAMERA = size_camera(SIZE)
GUN_L = 1.45

SHELL = Shell(
    build=long_gun_shell(length=GUN_L, r_breech=0.27, r_muzzle=0.14, open_breech=True, bore=0.075),
    ride=1.08, tilt=-0.10, crab_at=(0, -0.30, -0.22), crab_pitch=0.05, z0=-0.24, x0=0.18, yaw=0.62,
    feet=((-0.52, 0.30), (0.58, 0.26), (-0.60, -0.55), (0.64, -0.60)),
    eyes=(((-0.20, -0.18, 0.02), (-0.30, 1.0, 0.55), 0.44),
          ((0.20, -0.18, 0.02), (0.30, 1.0, 0.55), 0.44)),
    guard=((0.20, -0.04, 0.30), (-0.25, 0.70, 0.65)),
    big=1.25, small=0.6, side_r=0.26, tip_angle=0.0, lie=0.0, leg_len=1.15, leg_r=1.1)


def neutral_pose():
    return hermit_pose(open=0.3, spread=0.5)


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
        P['recoil'] = [0.0, 0.0, 0.16, 0.12][i]
        P['fire'] = [0.0, 0.0, 1.0, 0.0][i]
        P['fx'] = [0.0, 0.0, 1.0, 0.4][i]
        P['lift_a'] = [0, 0, 0.6, 0][i]
        P['squash'] = [1.0, 0.97, 1.02, 1.0][i]
    for P, o in R['cast']:
        P['drum'] *= 0.6
    # death: the gun is too long to roll; it slumps nose-down onto the salt
    for i, (P, o) in enumerate(R['death']):
        P['tip'] = 0.0
        P['fold'] = [0.0, 0.5, 0.9, 1.0][i]
        P['lean'] = [-0.10, 0.06, 0.16, 0.18][i]
        P['bob'] = [0.0, -0.25, -0.50, -0.55][i]
        P['sway'] = [0.04, 0.10, 0.20, 0.22][i]
    return R


ROWS, frames = hermit_rows(neutral_pose, 'shell', extra=_rows)

"""Diving-Bell Hermit (Hermitage tank). A tarnished brass diving bell with three big round portholes, worn tipped
back like a hood, its heavy rim resting on the salt behind; the crab's face, eyestalks and big guarding claw spill
out from under the front rim, legs planted wide. Pony-sized, ~1.4 m. Batten Down (hit): the crab pulls up into the
bell and lays its claw across the gap. Defining detail: the round portholes over the crab's head."""
from _hermitage_common import *

UNIT_ID = 'hermitage_diving_bell_hermit'
SIZE = 1.12            # 'medium' class; crab scaled so its front fills the gap under the rim
CAMERA = size_camera('medium')
H, RB, RT = 0.92, 0.50, 0.36
PORTS = ((-0.62, 1.0), (0.42, 1.0), (2.7, 1.0))
PORT_Y = 0.06


SHELL = Shell(
    build=diving_bell_shell(h=H, r_bot=RB, r_top=RT, ports=PORTS, port_y=PORT_Y, eyes_in=()),
    ride=0.60, tilt=-0.36, crab_at=(0, -0.50, 0.46), crab_upright=1.0, z0=-0.98, x0=0.36,
    eye_len=0.30, eye_bead=0.064, span=0.48, duck_dir=(0, 1.0, -0.25), duck_depth=0.24,
    big=1.40, small=0.70, side_r=0.50, tip_angle=1.25, tip_dir=-1.0)


def neutral_pose():
    return hermit_pose(open=0.3)


def build(P):
    return shelled(P, SIZE, SHELL)


def _fit(R):
    for row in R.values():
        for P, o in row:
            P['snap'] *= 0.6
    for i, (P, o) in enumerate(R['death']):      # the bell rolls to its right: slide it back into frame
        P['slide'] = [0, -0.08, -0.28, -0.32][i]
    return R


ROWS, frames = hermit_rows(neutral_pose, 'shell', extra=_fit)

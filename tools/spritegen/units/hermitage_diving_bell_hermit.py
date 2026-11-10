"""Diving-Bell Hermit (Hermitage tank). A tarnished brass diving bell with three big round portholes, planted wide
on four violet legs, the big claw guarding the open bottom. Pony-sized, ~1.4 m. Defining detail: the crab's
eyes pressed up behind two of the porthole glasses."""
from _hermitage_common import *

UNIT_ID = 'hermitage_diving_bell_hermit'
SIZE = 'medium'
CAMERA = size_camera(SIZE)
H, RB, RT = 0.92, 0.50, 0.36
PORTS = ((-0.62, 1.0), (0.42, 1.0), (2.7, 1.0))
PORT_Y = 0.06


def _eyes():
    out = []
    for az, sc in PORTS[:2]:
        c, nrm = bell_port(H, RB, RT, az, PORT_Y)
        base = c - nrm * 0.30 + v3(0, -0.26, 0)
        d = c + nrm * 0.005 - base
        out.append((tuple(base), tuple(norm(d)), float(np.linalg.norm(d)) - 0.03))
    return tuple(out)


SHELL = Shell(
    build=diving_bell_shell(h=H, r_bot=RB, r_top=RT, ports=PORTS, port_y=PORT_Y, eyes_in=(0, 1)),
    ride=0.80, tilt=-0.16, crab_at=(0, -0.42, 0.14), crab_pitch=0.16, z0=-0.50, x0=0.02,
    feet=((-0.50, 0.40), (0.56, 0.36), (-0.60, -0.22), (0.62, -0.26)),
    leg_roots=((-0.20, -0.46, 0.18), (0.20, -0.46, 0.18), (-0.30, -0.47, -0.10), (0.30, -0.47, -0.10)),
    eyes=_eyes(), eye_bead=0.05, antennae=True,
    guard=((0.12, -0.02, 0.44), (-0.6, 0.30, 0.75)),
    big=1.3, small=0.55, side_r=0.50, tip_angle=1.25, tip_dir=-1.0, leg_len=1.1)


def neutral_pose():
    return hermit_pose(open=0.3)


def build(P):
    return shelled(P, SIZE, SHELL)


ROWS, frames = hermit_rows(neutral_pose, 'shell')

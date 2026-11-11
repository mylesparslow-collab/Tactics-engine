"""Banded Lancer (Slough common). Standard build reared to 2.1 m on three tight loops pulled in under it like
a drawn bow; a long lance held low and forward in both hands, its tip one great curved pale fang lashed on
with chartreuse reed. Crisp black-and-bone banding. Defining detail: the fang lance tip."""
from _slough_common import *

UNIT_ID = 'slough_banded_lancer'
N = Naga(palette='yellow', height=2.1, tube=0.165, coil_r=0.48, loops=1.85, coil_lift=1.1, hood='cobra',
         hood_mark='bars', accent=(), band_len=0.34, band_dark=0.5, lean=0.10, shoulders=1.08, girth=1.05)
CAMERA = naga_camera(N)


def neutral_pose():
    P = naga_pose(N)
    hold_pole(P, 'r', 'l', grip=v3(-0.22, 1.18, 0.10), direction=v3(0.62, -0.30, 0.55), spacing=0.42)
    return P


def build(P):
    parts, add = new_parts()
    B = naga_body(P, add, N)
    pole(add, P, "r", "l", "lance", below=0.40, above=0.44)
    pauldron(add, P, B, N, 'l', plates=3)
    return naga_finish(P, N, parts)


ROWS, frames = naga_rows(neutral_pose, attack='thrust')

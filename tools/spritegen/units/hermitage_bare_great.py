"""Bare Giant (hermitage_bare_great; also Duchess Abaft, Bare). Hay-wagon-sized evicted crab, ~2.4 m: the biggest,
heaviest thing in the faction. It stands TALL where the Bare Brute crouches low: massive forequarters reared up, a
broad battered head shield crusted with fat barnacles, arms like hawsers, a huge gouged orange-tipped claw raised
high over its head, legs as thick as posts, eyestalks swivelled round at the viewer, and under all that armour a
great soft pink abdomen sagging out to one side. A century of housing has dulled its violet to a bruised,
greyer plum. Something this big should never be this soft."""
from _hermitage_common import *
from _hermitage_common import _arr

UNIT_ID = 'hermitage_bare_great'
SIZE = 1.46   # well over the 'great' class scale at ppm 44: clearly the biggest bare crab
CAMERA = size_camera('great')
BARE = Bare(h=0.46, yaw=0.08, pitch=0.02, z0=-0.42, x0=0.30, big=1.62, small=0.90, eye_len=0.34, eye_bead=0.062,
            span=0.40, spread=1.0, leg_len=1.08, leg_r=1.60, shield=1.40, arm=1.65, fat=1.18, barn=3, scar=True,
            shield_barn=2, tail=dict(size=1.30, thick=(0.19, 0.07), side=-0.75, drop=0.0, sag=0.8))

# battered colours: the claw a bruised, duller plum; the shield a greyer, chipped lilac
CLAW_OLD = _hex('#7c4c98')
CLAW_OLD_DK = _hex('#4e2b62')
SHIELD_OLD = _hex('#958aa8')


def _mats():
    return {
        'claw': Material(chitin(CLAW_OLD, dark=CLAW_OLD_DK, speck=_hex('#b49ac0'), amt=0.10, freq=5.0), spec=0.22,
                         gloss=22, brush=0.03),
        'carapace': Material(chitin(SHIELD_OLD, dark=SHIELD_DK, speck=_hex('#d8cfe2'), freq=6.0, amt=0.16),
                             spec=0.25, gloss=20, brush=0.05),
    }


def neutral_pose():
    return hermit_pose(raise_=0.0, spread=0.3, rear=0.12, open=0.35, eye_l=-0.5, eye_r=-0.7)


def build(P):
    return bare(P, SIZE, BARE, mats=_mats())


def _rows(R):
    """eyestalks stay swivelled round at the viewer in every row; the lunge is kept short so it stays in frame"""
    for row in R.values():
        for P, o in row:
            P['eye_l'] -= 0.5
            P['eye_r'] -= 0.6
            P['snap'] *= 0.40
            P['drum'] *= 0.45
            P['spread'] *= 0.6
            P['cock'] *= 0.72
    for P, o in R['hit']:
        P['recoil'] += 0.06
        P['slide'] -= 0.05
    for i, (P, o) in enumerate(R['death']):     # the collapse spreads toward the viewer: keep it off the edge
        P['recoil'] += [0, 0.16, 0.31, 0.31][i]
        P['slide'] += [0, 0.03, 0.06, 0.07][i]
    return R


ROWS, frames = hermit_rows(neutral_pose, 'bare', extra=_rows)

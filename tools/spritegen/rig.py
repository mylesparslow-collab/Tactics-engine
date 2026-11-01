"""Small posing helpers shared by unit files: copy poses, move the upper body, two-bone IK."""
import copy
import numpy as np
from sdf import v3, norm, rot_x, rot_z, rot_y

UPPER = ('chest', 'neck', 'head', 'sh_r', 'el_r', 'wr_r', 'sh_l', 'el_l', 'wr_l')


def clone(P):
    return copy.deepcopy(P)


def shift(P, keys, d):
    for k in keys:
        P[k] = P[k] + d


def rotate(P, keys, pivot, R):
    for k in keys:
        P[k] = pivot + R @ (P[k] - pivot)


def lean(P, fwd=0.0, side=0.0, keys=UPPER, extra=()):
    """Tilt the upper body about the pelvis. fwd>0 leans toward +z, side>0 toward +x (radians)."""
    R = rot_z(-side) @ rot_x(fwd)
    rotate(P, tuple(keys) + tuple(extra), P['pelvis'], R)


def two_bone(root, target, l1, l2, pole):
    """Return the middle joint for a two-bone chain reaching from root toward target."""
    d = target - root
    dist = np.clip(np.linalg.norm(d), 1e-4, l1 + l2 - 1e-4)
    dn = d / np.linalg.norm(d)
    a = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    h = np.sqrt(max(l1 * l1 - a * a, 0.0))
    pole = np.asarray(pole, dtype=np.float64)
    side = pole - dn * (pole @ dn)
    side = norm(side) if np.linalg.norm(side) > 1e-6 else norm(np.cross(dn, (1, 0, 0)))
    return root + dn * a + side * h


def place_arm(P, s, wrist, pole, l1=0.27, l2=0.26):
    P['wr_' + s] = v3(*wrist)
    P['el_' + s] = two_bone(P['sh_' + s], P['wr_' + s], l1, l2, pole)


def place_leg(P, s, ankle, hip=None, l1=0.43, l2=0.42, pole=(0, 0, 1)):
    if hip is not None:
        P['hip_' + s] = v3(*hip)
    P['an_' + s] = v3(*ankle)
    P['kn_' + s] = two_bone(P['hip_' + s], P['an_' + s], l1, l2, pole)


def staff_from_grips(P, low, high, below=0.75, length=2.06):
    """Set the staff so it runs through two grip points (low hand, high hand)."""
    low, high = v3(*low), v3(*high)
    d = norm(high - low)
    P['staff_base'] = low - d * below
    P['staff_top'] = P['staff_base'] + d * length

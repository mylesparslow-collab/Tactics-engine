"""Murk Diver (Hadal Court skirmisher). A lean pressure-born scout that runs on all fours: long jointed
limbs with hooked claws, a narrow armoured back of overlapping plates, a small domed diving-helm head
with one teal port, and a trailing air-hose. Murk smoke clings to its heels.
Defining detail: the low four-legged crouch and the single port light (the fastest thing in the Court).
"""
from _hadal_court_common import *

UNIT_ID = 'hadal_court_murk_diver'
CAMERA = Camera(ppm=52)


def neutral_pose():
    return creature_pose()


def build(P):
    parts, add = new_parts()
    e, st, sk = P['end'], P['stride'], P['strike']
    hip = v3(0, 0.62 - 0.3 * e, -0.32)
    sho = v3(0, 0.78 - 0.3 * e + 0.05 * sk, 0.18 + 0.08 * sk)
    sp = norm(sho - hip)
    Rb = basis_from(sp, v3(0, 1, 0))
    # back plates along the spine
    for k in range(5):
        t = k / 4
        q = hip + (sho - hip) * t + v3(0, 0.05, 0)
        add(Ellipsoid(q, (0.14 - 0.01 * k, 0.09, 0.13), Rb), 'plate', 0.02)
    add(Capsule(hip, sho, 0.12, 0.13), 'hide', 0.04)
    # head: small diving helm on a neck
    hd = sho + v3(0, 0.16, 0.22 + 0.10 * sk)
    add(Capsule(sho, hd, 0.06), 'hide', 0.03)
    Rh = rot_x(0.25 - 0.2 * sk) if True else np.eye(3)
    dome_helm(add, hd, Rh, r=0.15, mat='helm', ports=1, rim='iron')
    port = hd + Rh[:, 2] * 0.16
    # air hose from helm back to hip, trailing
    hose = [hd - v3(0, 0.02, 0.12), sho + v3(0, 0.14, -0.15), hip + v3(0, 0.16, -0.05), hip + v3(0.05, 0.05, -0.30)]
    seg_limb(add, hose, [0.022, 0.022, 0.02, 0.015], 'hose', joint=None)
    # limbs
    for sx in (-1, 1):
        for front in (True, False):
            g = (1 if front else -1) * sx * st
            root = (sho if front else hip) + v3(sx * 0.12, -0.04, 0)
            reach = sk if (front and sx == -1) else 0
            ft = v3(sx * (0.26 + 0.15 * e), 0.10 * max(g, 0) + 0.35 * reach,
                    (0.30 + 0.35 * reach if front else -0.40) + 0.18 * g)
            kn = root + (v3(sx * 0.13, -0.28, -0.06) if front else v3(sx * 0.12, -0.16, 0.24))
            seg_limb(add, [root, kn, ft + v3(0, 0.06, 0)], [0.05, 0.04, 0.03], 'hide', joint='plate', k=0.01)
            fd = norm(v3(0, -0.4, 1.0 if front else 0.6))
            for c in (-1, 0, 1):
                add(Capsule(ft + v3(0, 0.05, 0), ft + v3(c * 0.04, 0.0, 0) + fd * 0.09, 0.012, 0.004), 'claw', 0.0)
    # murk wisps
    for k in range(3):
        q = v3(0.14 * (k - 1), 0.03, -0.45 - 0.12 * k)
        add(Ellipsoid(q, (0.16, 0.03, 0.11)), 'murk', 0.03)
    parts[:] = transform_parts(creature_place(parts, P), t=(0, 0, 0.05))
    mats = hadal_mats(P, {
        'plate': Material(cracked_albedo(_hex('#4b5378'), crack=_hex('#1a1c30'), freq=9, width=0.012, seep=TEAL), spec=0.6, gloss=35, metal=0.3),
        'helm': bell_metal(hd, Rh, base=_hex('#58607f'), spacing=0.3, barn=0),
        'hose': Material(_hex('#2c2f42'), spec=0.4, gloss=25),
        'claw': Material(_hex('#b3b0a0'), spec=0.4),
        'murk': Material(_hex('#151726'), spec=0.0, brush=0.12, rim=0.3),
    }, lamp_gain=1.3)
    lights = [teal_light(port + v3(0, P['bob'], 0.08), P, 0.8, 0.6)]
    return hadal_finish(P, parts, mats, lights)


def _extra(rows):
    # cast = murk-step: crouch, vanish into smoke, reappear
    for i, (P, o) in enumerate(rows['cast']):
        P['squash'] = [0.9, 0.7, 1.0][i]
    return rows


ROWS, frames = creature_rows(neutral_pose, sink=(0, 0, 0.08, 0.25), extra=_extra)

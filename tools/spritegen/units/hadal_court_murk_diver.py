"""Murk Diver (Hadal Court skirmisher). A lean pressure-born scout that runs on all fours: long jointed
limbs with hooked claws, a narrow armoured back of overlapping plates, a small domed diving-helm head
with one teal port, and a trailing air-hose. Murk smoke clings to its heels.
Defining detail: the low four-legged crouch and the single port light (the fastest thing in the Court).
"""
from _hadal_court_common import *
from kit.fx import emit

UNIT_ID = 'hadal_court_murk_diver'
CAMERA = Camera(ppm=52)


def neutral_pose():
    return creature_pose()


def build(P):
    parts, add = new_parts()
    e, st, sk = P['end'], P['stride'], P['strike']
    # Knuckle-walking diver: a hunched, heavy front (shoulder hump and bell-iron mantle) tapering to
    # short hind legs, so it still reads bottom-heavy and Court-shaped while low and quick.
    hip = v3(0, 0.50 - 0.25 * e, -0.30)
    sho = v3(0, 0.80 - 0.32 * e + 0.05 * sk, 0.12 + 0.08 * sk)
    sp = norm(sho - hip)
    Rb = basis_from(sp, v3(0, 1, 0))
    add(Capsule(hip, sho, 0.15, 0.20), 'hide', 0.05)
    # shoulder hump and mantle: one big rounded mass over the forelimbs
    add(Ellipsoid(sho + v3(0, 0.06, -0.04), (0.30, 0.22, 0.24), Rb), 'helm', 0.06)
    add(Torus(sho + v3(0, -0.04, -0.02), Rb[:, 1], 0.27, 0.035), 'iron', 0.03)
    # overlapping back plates, shrinking toward the tail
    for k in range(4):
        t = 0.15 + k * 0.24
        q = sho + (hip - sho) * t + v3(0, 0.15 - 0.06 * t, 0)
        add(Ellipsoid(q, (0.20 - 0.03 * k, 0.08, 0.13), Rb), 'plate', 0.02)
    # head: a big domed helm slung low and forward between the shoulders
    hd = sho + v3(0, -0.02, 0.32 + 0.10 * sk)
    Rh = rot_x(0.20 - 0.2 * sk)
    dome_helm(add, hd, Rh, r=0.19, mat='helm', ports=1, rim='iron')
    port = hd + Rh[:, 2] * 0.20
    add(Capsule(sho + v3(0, 0.0, 0.10), hd, 0.10), 'hide', 0.04)
    # air hose from the helm back over the hump to the hip, trailing
    hose = [hd - v3(0, -0.06, 0.16), sho + v3(0, 0.30, -0.12), hip + v3(0, 0.20, -0.05), hip + v3(0.06, 0.05, -0.32)]
    seg_limb(add, hose, [0.028, 0.026, 0.022, 0.016], 'hose', joint=None)
    # limbs: thick forearms planted on the knuckles, short crouched hind legs
    for sx in (-1, 1):
        for front in (True, False):
            g = (1 if front else -1) * sx * st
            root = (sho if front else hip) + v3(sx * (0.22 if front else 0.13), -0.04, 0)
            reach = sk if (front and sx == -1) else 0
            ft = v3(sx * ((0.40 if front else 0.24) + 0.15 * e), 0.10 * max(g, 0) + 0.35 * reach,
                    (0.28 + 0.35 * reach if front else -0.40) + 0.16 * g)
            kn = root + (v3(sx * 0.20, -0.20, -0.04) if front else v3(sx * 0.10, -0.12, 0.20))
            rad = [0.085, 0.07, 0.055] if front else [0.07, 0.05, 0.035]
            seg_limb(add, [root, kn, ft + v3(0, 0.06, 0)], rad, 'hide', joint='plate', k=0.02)
            fd = norm(v3(0, -0.4, 1.0 if front else 0.6))
            for c in (-1, 0, 1):
                add(Capsule(ft + v3(0, 0.05, 0), ft + v3(c * 0.045, 0.0, 0) + fd * 0.10, 0.015, 0.005), 'claw', 0.0)
    # murk clinging to its heels: live emitters (kit/fx.py), thicker on the run and in the murk-step cast
    for k in range(2):
        emit(add, hip + v3(0.12 * (2 * k - 1), -0.42, -0.10), 'murk', 0.7 + 0.8 * abs(st) + 1.2 * P.get('vanish', 0.0))
    parts[:] = transform_parts(squash_parts(creature_place(parts, P), sy=1.15, sxz=1.15), t=(0.24, 0, -0.34))
    mats = hadal_mats(P, {
        'plate': Material(cracked_albedo(_hex('#363c5e'), crack=_hex('#14162a'), freq=9, width=0.012, seep=TEAL, barn=0.2), spec=0.35, gloss=24, metal=0.3),
        'helm': bell_metal(hd, Rh, base=_hex('#424862'), spacing=0.18, barn=0.25),
        'hose': Material(_hex('#2c2f42'), spec=0.4, gloss=25),
        'claw': Material(_hex('#b3b0a0'), spec=0.4),
    }, lamp_gain=1.3)
    lights = [teal_light((port + v3(0, P['bob'], 0.08)) * 1.15 + v3(0.24, 0, -0.34), P, 0.8, 0.6)]
    return hadal_finish(P, parts, mats, lights)


def _extra(rows):
    # cast = murk-step: crouch, vanish into smoke, reappear
    for i, (P, o) in enumerate(rows['cast']):
        P['squash'] = [0.9, 0.7, 1.0][i]
        P['vanish'] = [0.3, 1.0, 0.6][i]
    return rows


ROWS, frames = creature_rows(neutral_pose, sink=(0, 0, 0.08, 0.25), extra=_extra)

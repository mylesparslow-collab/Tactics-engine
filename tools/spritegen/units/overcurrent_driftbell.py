"""Driftbell (Overcurrent ranged / area). A cart-sized translucent jelly that hangs over the board like a slow
cold bruise: a glassy bell with its organs plainly visible and pulsing, frilled oral arms, and threads that
hang the length of a street, each stinging bead lit cyan. Defining detail: the see-through organs and the
threads, with a drip that rises up into the bell. Tell: the bell pulses and the stomach beats cyan."""
from _overcurrent_common import *

UNIT_ID = 'overcurrent_driftbell'
CAMERA = Camera(ppm=46)


def neutral_pose():
    return pose()


def build(P):
    parts, add = new_parts()
    ph, st, op = P['ph'], P['strike'], P['open']
    beat = 0.5 + 0.5 * np.sin(2 * np.pi * P['tell'])
    pulse = 1 + 0.07 * np.sin(ph) - 0.05 * st
    cy = 1.40
    R = 0.58 * pulse
    # bell: a dome clipped flat at the margin, with a thick scalloped rim of lappets
    def bell(p):
        q = p - v3(0, cy, 0)
        d = np.linalg.norm(q / v3(R, 0.50 * (2 - pulse), R), axis=1) - 1.0
        d = d * 0.45
        return smax(d, -q[:, 1] - 0.10, 0.04)
    add(Func(bell, v3(0, cy, 0), R + 0.5), 'bell', 0.0)
    for i in range(14):
        a = 2 * np.pi * i / 14
        q = v3(np.cos(a) * R * 0.97, cy - 0.10 + 0.012 * np.sin(ph + i), np.sin(a) * R * 0.97)
        add(Sphere(q, 0.055), 'bell', 0.03)
    # oral arms: four frilled ribbons from the centre
    for i in range(4):
        a = np.pi / 4 + i * np.pi / 2
        pts = [v3(0, cy - 0.05, 0), v3(np.cos(a) * 0.10, cy - 0.30, np.sin(a) * 0.10),
               v3(np.cos(a) * 0.16 + 0.05 * np.sin(ph + i), cy - 0.58, np.sin(a) * 0.16),
               v3(np.cos(a) * 0.12 + 0.08 * np.sin(ph + i + 1), cy - 0.84, np.sin(a) * 0.12 + 0.20 * st)]
        ribbon(add, pts, [0.05, 0.07, 0.05, 0.02], 0.012, 'frill', n=8, k=0.02, side=v3(np.cos(a), 0, np.sin(a)))
    # stinging threads from the rim
    beads = []
    nS = 11
    for k in range(nS):
        a = 2 * np.pi * (k + 0.5) / nS + 0.2
        rx, rz = np.cos(a) * R * 0.92, np.sin(a) * R * 0.92
        L = 1.2 + 0.25 * np.sin(k * 2.3)
        prev = v3(rx, cy - 0.10, rz)
        segs = 5
        for j in range(1, segs + 1):
            h = j / segs
            x = rx * (1 - 0.1 * h) + 0.07 * np.sin(ph + k * 1.7 + h * 4) * h
            z = rz * (1 - 0.1 * h) + 0.07 * np.cos(ph + k * 1.3 + h * 4) * h + 0.55 * st * h * h
            y = max(cy - 0.10 - L * h * (1.0 - 0.15 * st), 0.06 + 0.04 * (k % 3))
            cur = v3(x, y, z)
            add(Capsule(prev, cur, 0.016 * (1 - 0.5 * h), 0.016 * (1 - 0.5 * (h + 0.2))), 'thread', 0.0)
            if j in (2, 4):
                add(Sphere(cur, 0.027), 'bead', 0.0)
            prev = cur
        beads.append(prev)
    pl = Placer(P, yaw=0.0, hover=0.0, shift=-0.0)
    c0 = v3(0, cy, 0)
    organs = [Organ(pl.pt(c0 + v3(0, 0.0, 0)), (0.14, 0.17, 0.14), _hex('#7fe8ee'), 0.55 + 0.4 * beat, 0.9)]
    for i in range(4):
        a = np.pi / 4 + i * np.pi / 2
        organs.append(Organ(pl.pt(c0 + v3(np.cos(a) * 0.30, 0.10, np.sin(a) * 0.30)), (0.15, 0.06, 0.11), _hex('#d8506a'), 0.1, 0.85))
    for i in range(4):
        a = i * np.pi / 2
        organs.append(Organ(pl.pt(c0 + v3(np.cos(a) * 0.43, 0.02, np.sin(a) * 0.43)), (0.05, 0.05, 0.05), _hex('#f4f0ff'), 0.3, 0.7))
    mats = std_mats(P, {'bell': jelly(organs, glow=0.55, depth=0.9, local=pl.inv, striate=0.7),
                        'frill': skin(top=_hex('#e89aaa'), under=_hex('#f4c4d0'), glow=0.5, spec=0.4),
                        'thread': Material(_hex('#d8ecf8'), spec=0.7, gloss=60, emissive=tuple(np.array(CYAN) * 0.15), sss=0.5),
                        'bead': Material(CYAN, emissive=tuple(np.array(CYAN) * (0.8 + 0.8 * P['fx'] + 0.6 * P['cast_glow']) * P['glow']), rim=0.0)})
    lights = [under_light(P, v3(0, 0.3, 0), 0.9, 1.2), Light(v3(0, cy, 0.1), CYAN, 0.5 * (0.5 + beat) * P['glow'], 0.9)]
    dp = [pl.pt(beads[3] + v3(0, 0.2, 0)), pl.pt(beads[7] + v3(0, 0.2, 0))]

    def world(add2):
        drips(add2, P, dp, rise=0.5)
        spray(add2, P, v3(0.3, 0.2, 0.3))
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


def _extra(rows):
    for P, o in rows['idle']:
        P['squash'] = 1.0


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.2, 0.5, 1.0, 0.3), atk_strike=(0.0, 0.5, 1.0, 0.3), extra=_extra)

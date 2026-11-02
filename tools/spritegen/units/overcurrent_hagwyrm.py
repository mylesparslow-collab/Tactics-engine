"""Hagwyrm (Overcurrent tank). A hagfish the length of a wagon, heaped in a wet knot, ropes of clear slime
hanging off it in long glittering strings, a reared head with a round rasping mouth, whiskers and a blind eye.
It does not fight so much as fill the space where you were.
Defining detail: slime in strings from every pore, each pore a cyan dot. Tell: the coil heaves and slime drips."""
from _overcurrent_common import *

UNIT_ID = 'overcurrent_hagwyrm'
CAMERA = Camera(ppm=46)


def neutral_pose():
    return pose()


def build(P):
    parts, add = new_parts()
    ph, st, op = P['ph'], P['strike'], P['open']
    # coil path: a heaped spiral, then the neck rears up out of the top
    pts = []
    for t in np.linspace(0, 1, 9):
        th = -0.4 + t * 2 * np.pi * 1.45 + 0.10 * np.sin(ph + t * 4)
        r = 0.62 - 0.16 * t
        pts.append(v3(np.cos(th) * r, 0.17 + 0.46 * t + 0.015 * np.sin(ph * 2 + t * 6), np.sin(th) * r))
    last = pts[-1]
    out = norm(v3(last[0], 0, last[2]))
    nk = [last + v3(0, 0.34, 0) + out * 0.04, last + v3(0, 0.82, 0.04) + v3(0.0, 0, 0.10 + 0.1 * st),
          last + v3(0.0, 1.00 - 0.25 * st, 0.40 + 0.20 * st)]
    nk[1] = nk[1] + v3(0.1 * np.sin(ph), 0, 0)
    allp = pts + nk
    rad = [0.035, 0.09, 0.15, 0.19, 0.20, 0.20, 0.20, 0.19, 0.18, 0.17, 0.155, 0.15]
    s = tube(add, allp, rad, 'skin', n=44, k=0.05)
    # head
    hd = norm(s[-1] - s[-3])
    R = basis_from(v3(0, 1, 0), hd)
    # frame with z along hd: build from axes
    zax = hd
    xax = norm(np.cross(v3(0, 1, 0), zax))
    yax = np.cross(zax, xax)
    H = Frame(s[-1], np.stack([xax, yax, zax], axis=1), 1.25)
    H.ell(add, (0, 0, 0.06), (0.20, 0.19, 0.24), 'skin', 0.05)
    mr = 0.15 + 0.08 * op
    H.tor(add, (0, -0.01, 0.24), (0, 0, 1), mr, 0.045, 'gum', 0.03)
    H.ell(add, (0, -0.01, 0.22), (mr, mr, 0.03), 'throat')
    for ring, (rr, n_t, ln) in enumerate([(mr * 0.92, 18, 0.10), (mr * 0.60, 12, 0.09), (mr * 0.30, 6, 0.07)]):
        for i in range(n_t):
            a = 2 * np.pi * (i + 0.5 * ring) / n_t
            q = v3(np.cos(a) * rr, -0.01 + np.sin(a) * rr, 0.25)
            H.tooth(add, q, q + v3(-np.cos(a) * 0.03, -np.sin(a) * 0.03, 0.0) * 0 + v3(-np.cos(a) * 0.045, -np.sin(a) * 0.045, -0.055 + 0.0), 0.016, 'tooth')
    for sx in (-1, 1):
        for j in range(3):
            q = v3(sx * (0.07 + 0.02 * j), 0.04 - 0.05 * j, 0.27)
            H.cap(add, q, q + v3(sx * 0.12, -0.02 - 0.03 * j, 0.10 + 0.04 * np.sin(ph + j)), 0.012, 0.006, 'skin')
        H.sph(add, (sx * 0.12, 0.07, 0.15), 0.022, 'eyeb')
    # slime ropes hanging from the body, and glowing pores
    ends = []
    for i in range(3, 41, 4):
        q = s[i]
        r = rad[min(int(i / 44 * 11), 11)]
        o = norm(v3(q[0], 0, q[2])) if np.hypot(q[0], q[2]) > 0.1 else v3(0, 0, 1)
        top = q + o * r * 0.9 + v3(0, -r * 0.3, 0)
        ln = 0.28 + 0.12 * ((i * 7) % 5) / 4
        sway = 0.03 * np.sin(ph + i)
        end = v3(top[0] + o[0] * 0.05 + sway, max(top[1] - ln, 0.05), top[2] + o[2] * 0.05)
        add(Capsule(top, end, 0.012, 0.006), 'slime', 0.0)
        add(Sphere(end + v3(0, -0.01, 0), 0.02), 'slime', 0.0)
        add(Sphere(top + v3(0, 0.03, 0), 0.016), 'glow', 0.0)
        ends.append(end)
    pl = Placer(P, yaw=0.45, hover=0.0, shift=-0.22, back=0.2)
    organs = [Organ(pl.pt(s[22] + v3(0, 0.04, 0)), (0.14, 0.12, 0.14), _hex('#d27a92'), 0.0, 0.6),
              Organ(pl.pt(s[32] + v3(0, 0.04, 0)), (0.13, 0.12, 0.13), _hex('#c4344a'), 0.0, 0.5)]
    mats = std_mats(P, {'skin': skin(top=_hex('#a8a6c4'), under=_hex('#ecd4e0'), organs=organs, veins=0.35, glow=0.75, depth=0.5,
                                     local=pl.inv, spec=0.5, wet=60, mottle=0.06)})
    lights = [under_light(P, v3(0, 0.1, 0), 1.0, 1.3)]
    dp = [pl.pt(e) for e in ends[2:7:2]]

    def world(add2):
        drips(add2, P, dp, rise=0.12)
        spray(add2, P, pl.pt(H.p((0, 0.3, 0.3))))
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.4, 1.0, 0.0, 0.3), atk_strike=(0.0, 0.5, 1.0, 0.3))

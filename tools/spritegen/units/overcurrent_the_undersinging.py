"""The Undersinging, what feeds below the beam (Overcurrent hero). A siphonophore choir a hundred bodies long stood on
end like a drowned cathedral organ: a pink float crowning a wreath of great bells, a fan of hanging pipe-bodies
glowing at their open ends, a long cord of smaller bells below it, every one humming the pitch of the lamps.
A single thin gold thread runs up the central cord. Defining detail: the pipe fan over the bell wreath, wide at the
top. Tell: a pulse of light climbs the cord, bell by bell, and the pipes shimmer."""
from _overcurrent_common import *

LOOK = dataclasses.replace(LOOK, sky_int=0.20, key_int=0.7, exposure=0.95)
UNIT_ID = 'overcurrent_the_undersinging'
CAMERA = Camera(ppm=44)


def neutral_pose():
    return pose()


def build(P):
    parts, add = new_parts()
    ph, st, op = P['ph'], P['strike'], P['open']
    tl = P['tell']
    sway = lambda y: 0.07 * np.sin(ph - y * 2.4)
    lean = lambda y: 0.35 * st * max(y - 0.8, 0) / 1.4
    cord = [v3(sway(y), y, lean(y)) for y in (0.45, 0.85, 1.25, 1.7, 2.1)]
    s = tube(add, cord, [0.02, 0.04, 0.05, 0.06, 0.07], 'cord', n=14, k=0.02)
    gold = [c + v3(0.045, 0, 0.04) for c in cord]
    for a, b in zip(gold[:-1], gold[1:]):
        add(Capsule(a, b, 0.009, 0.009), 'gold', 0.0)
    top = cord[-1]
    add(Ellipsoid(top + v3(0, 0.20, 0), (0.17, 0.22, 0.17), None), 'float', 0.05)
    for i in range(6):
        a = i * 1.1
        add(Sphere(top + v3(np.cos(a) * 0.10, 0.34 + 0.03 * (i % 2), np.sin(a) * 0.10), 0.032), 'finred', 0.02)
    bells = []
    # crown: wreath of great bells around the stem top
    for i in range(5):
        a = 2 * np.pi * i / 5 + 0.4
        beat = 0.5 + 0.5 * np.sin(ph - i * 0.8 + 2 * np.pi * tl)
        c = top + v3(np.cos(a) * 0.44, -0.10 + 0.03 * np.sin(ph + i), np.sin(a) * 0.44)
        r = 0.15 * (1 + 0.06 * beat)
        add(Capsule(top + v3(0, -0.04, 0), c + v3(0, 0.16, 0), 0.02, 0.014), 'cord', 0.0)
        add(Ellipsoid(c, (r, r * 1.2, r), None), 'bell', 0.03)
        add(Torus(c + v3(0, -r * 1.05, 0), v3(0, 1, 0), r * 0.8, 0.022), 'bell', 0.02)
        bells.append((c, r, beat))
    # organ pipes fanned on the viewer's side
    pipes = []
    for i in range(6):
        a = -1.0 + i * 0.4
        L = 0.50 + 0.40 * (1 - abs(a) / 1.1)
        c = top + v3(np.sin(a) * 0.40, -0.38 - L * 0.5, np.cos(a) * 0.36 + 0.05)
        beat = 0.5 + 0.5 * np.sin(ph - i * 0.9 + 2 * np.pi * tl)
        add(Capsule(c + v3(0, L * 0.5, 0), c + v3(0, -L * 0.5, 0), 0.045, 0.060), 'bell', 0.0)
        add(Sphere(c + v3(0, -L * 0.5 - 0.01, 0), 0.050 + 0.01 * beat), 'lure', 0.0)
        bells.append((c, 0.06, beat))
        pipes.append(c + v3(0, -L * 0.5, 0))
    # lower cord of smaller bells, alternating sides, with stinging threads
    lows = []
    for i, y in enumerate((1.46, 1.24, 1.04, 0.86, 0.70, 0.56)):
        side = 1 if i % 2 == 0 else -1
        beat = 0.5 + 0.5 * np.sin(ph - (i + 3) * 0.9 + 2 * np.pi * tl)
        r = 0.15 - 0.012 * i
        c = v3(sway(y) + side * (r + 0.07), y - 0.03, lean(y) + 0.05)
        add(Capsule(v3(sway(y), y, lean(y)), c + v3(0, 0.08, 0), 0.018, 0.014), 'cord', 0.0)
        add(Ellipsoid(c, (r, r * 1.15, r), None), 'bell', 0.03)
        add(Torus(c + v3(0, -r * 1.05, 0), v3(0, 1, 0), r * 0.8, 0.018), 'bell', 0.02)
        bells.append((c, r, beat))
        lows.append(c)
        prev = c + v3(0, -r * 1.1, 0)
        for m in range(1, 4):
            h = m / 3
            cur = v3(c[0] + 0.05 * np.sin(ph + i + h * 4) * h, max(c[1] - r * 1.1 - 0.35 * h, 0.06), c[2] + 0.04 * h)
            add(Capsule(prev, cur, 0.010, 0.008), 'thread', 0.0)
            if m == 2:
                add(Sphere(cur, 0.022), 'bead', 0.0)
            prev = cur
    add(Sphere(cord[0] + v3(0, -0.06, 0), 0.05 + 0.01 * np.sin(ph)), 'lure', 0.0)
    pl = Placer(P, yaw=0.45, hover=0.10, shift=-0.0, back=0.0, scale=0.96)
    organs = [Organ(pl.pt(c), (r * 0.58, r * 0.7, r * 0.58), CYAN if k % 2 == 0 else _hex('#dff6ff'), 0.35 + 0.8 * beat, 0.95)
              for k, (c, r, beat) in enumerate(bells)]
    mats = std_mats(P, {'bell': jelly(organs, glow=0.5, depth=0.6, local=pl.inv, tint=tuple(np.array(CERU) * 0.5 + np.array(PEARL) * 0.5)),
                        'float': skin(top=_hex('#e4a4b8'), under=_hex('#f8d8e2'), organs=[], glow=0.4, spec=0.7, wet=70),
                        'cord': Material(_hex('#e8f0fa'), spec=0.6, gloss=50, emissive=tuple(np.array(CYAN) * 0.25), sss=0.5),
                        'thread': Material(_hex('#d8ecf8'), spec=0.7, gloss=60, emissive=tuple(np.array(CYAN) * 0.15)),
                        'bead': Material(CYAN, emissive=tuple(np.array(CYAN) * (0.8 + 0.8 * P['fx'] + 0.6 * P['cast_glow']) * P['glow']), rim=0.0)})
    lights = [under_light(P, v3(0, 0.3, 0), 0.9, 1.6)] + [Light(pl.pt(p), CYAN, 0.35 * P['glow'], 0.5) for p in pipes[1::2]]
    dp = [pl.pt(pipes[2] + v3(0, -0.05, 0)), pl.pt(pipes[4] + v3(0, -0.05, 0))]

    def world(add2):
        drips(add2, P, dp, rise=0.3)
        spray(add2, P, pl.pt(top))
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.2, 0.5, 1.0, 0.3), atk_strike=(0.0, 0.5, 1.0, 0.3))

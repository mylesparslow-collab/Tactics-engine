"""Siphon Chain (Overcurrent ranged). A siphonophore strung across the air: a hundred lantern-bodies sharing one
nerve, shown as an arc of linked glassy bells on a pearl cord under a pink float, each bell lit cyan from inside
with its own small mouth, stinging threads trailing from every link. It is not one animal and has never been alone.
Defining detail: the chain of lit bells. Tell: a pulse of light runs down the bells in order."""
from _overcurrent_common import *

UNIT_ID = 'overcurrent_siphon_chain'
CAMERA = Camera(ppm=46)
NB = 8


def neutral_pose():
    return pose()


def arc(t, P):
    st = P['strike']
    x = -0.78 + 1.56 * t
    y = 0.80 + 1.05 * np.sin(np.pi * t) ** 0.9 - 0.10 * t
    z = 0.55 * st * t ** 2
    return v3(x, y + 0.04 * np.sin(P['ph'] - t * 5), z)


def build(P):
    parts, add = new_parts()
    ph, st, op = P['ph'], P['strike'], P['open']
    ts = np.linspace(0.06, 0.94, NB)
    cord = [arc(t, P) for t in np.linspace(0.0, 1.0, 12)]
    tube(add, cord, [0.03] * 12, 'cord', n=24, k=0.02)
    # float at the crest of the arc
    top = arc(0.5, P)
    add(Ellipsoid(top + v3(0, 0.15, 0), (0.17, 0.20, 0.17)), 'float', 0.05)
    for i in range(5):
        a = i * 1.3
        add(Sphere(top + v3(np.cos(a) * 0.10, 0.28 + 0.03 * i % 2, np.sin(a) * 0.10), 0.034), 'finred', 0.02)
    bells, threads = [], []
    for k, t in enumerate(ts):
        c = arc(t, P)
        size = 0.10 + 0.06 * np.sin(np.pi * t) ** 0.7
        beat = 0.5 + 0.5 * np.sin(ph * 1.0 - k * 0.9 + 2 * np.pi * P['tell'])
        sz = size * (1 + 0.06 * beat)
        bc = c + v3(0, -sz * 0.95, 0)
        tan = norm(arc(min(t + 0.02, 1.0), P) - arc(max(t - 0.02, 0.0), P))
        R = basis_from(v3(0, 1, 0), v3(0, 0, 1))
        add(Ellipsoid(bc, (sz, sz * 1.15, sz), None), 'bell', 0.03)
        add(Torus(bc + v3(0, -sz * 0.95, 0), v3(0, 1, 0), sz * 0.82, 0.022), 'bell', 0.02)
        add(Sphere(bc + v3(0, -sz * 1.05, sz * 0.25), 0.03), 'finred', 0.0)       # tiny mouth
        bells.append((bc, sz, beat))
        n_th = 2 if sz > 0.15 else 1
        for j in range(n_th):
            ox = (j - 0.5 * (n_th - 1)) * 0.10
            prev = bc + v3(ox, -sz * 1.0, 0)
            L = 0.55 + 0.2 * np.sin(k * 1.9 + j)
            for m in range(1, 5):
                h = m / 4
                cur = prev * 0 + v3(bc[0] + ox + 0.06 * np.sin(ph + k + h * 4) * h + 0.2 * st * h * t,
                                    max(bc[1] - sz * 1.0 - L * h, 0.07), bc[2] + 0.4 * st * h * t * h)
                add(Capsule(prev, cur, 0.011, 0.009), 'thread', 0.0)
                if m == 3:
                    add(Sphere(cur, 0.024), 'bead', 0.0)
                prev = cur
            threads.append(prev)
    pl = Placer(P, yaw=-0.45, hover=0.0, shift=0.0, back=0.1)
    organs = [Organ(pl.pt(bc), (sz * 0.58, sz * 0.7, sz * 0.58), CYAN if k % 2 == 0 else _hex('#dff6ff'), 0.35 + 0.8 * beat, 0.95)
              for k, (bc, sz, beat) in enumerate(bells)]
    organs.append(Organ(pl.pt(top + v3(0, 0.15, 0)), (0.10, 0.13, 0.10), _hex('#f6c8d4'), 0.1, 0.8))
    mats = std_mats(P, {'bell': jelly(organs[:-1], glow=0.5, depth=0.6, local=pl.inv),
                        'float': skin(top=_hex('#e4a4b8'), under=_hex('#f8d8e2'), organs=[], glow=0.4, spec=0.7, wet=70),
                        'cord': Material(_hex('#e8f0fa'), spec=0.6, gloss=50, emissive=tuple(np.array(CYAN) * 0.2), sss=0.5),
                        'thread': Material(_hex('#d8ecf8'), spec=0.7, gloss=60, emissive=tuple(np.array(CYAN) * 0.15)),
                        'bead': Material(CYAN, emissive=tuple(np.array(CYAN) * (0.8 + 0.8 * P['fx'] + 0.6 * P['cast_glow']) * P['glow']), rim=0.0)})
    lights = [under_light(P, v3(0, 0.3, 0), 0.8, 1.5)] + [Light(pl.pt(bc), CYAN, 0.3 * (0.3 + beat) * P['glow'], 0.45) for bc, sz, beat in bells[::2]]
    dp = [pl.pt(bells[2][0] + v3(0, -0.2, 0)), pl.pt(bells[6][0] + v3(0, -0.2, 0))]

    def world(add2):
        drips(add2, P, dp, rise=0.3)
        spray(add2, P, pl.pt(top))
        ripple(add2, P)
    return finish(P, pl, parts, mats, lights, world)


ROWS, frames = oc_rows(neutral_pose, atk_open=(0.2, 0.5, 1.0, 0.3), atk_strike=(0.0, 0.5, 1.0, 0.3))

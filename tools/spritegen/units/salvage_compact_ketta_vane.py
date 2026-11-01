"""Ketta Vane, Sled-Queen of the Long Salt (Salvage Compact hero). Crouched low on a racing bone-sled
mid-drift (sled yawed and heeled over, a spray of salt off the runners), one hand on the rein, the
Cutwater blade swept back in the other. Brass goggles, long patchwork coat streaming, a flare belt.
The sled has a jawbone figurehead. Defining detail: the salt spray. Tell: a fuse flickers on the belt."""
import numpy as np
from _salvage_compact_common import *
from render import Camera
from kit.xform import transform_parts

UNIT_ID = 'salvage_compact_ketta_vane'
FACTION = 'salvage_compact'
CAMERA = Camera(ppm=46)
C = Costume(top='coat', sleeve='coat', legs='trousers', hand='glove', skirt=None, head='hair',
            hair='hair', hair_style='tail', belt='leather', girth=0.85)
DECK = 0.17


def neutral_pose():
    P = rider_pose(height=0.94, build=0.86, deck=DECK, crouch=0.55, lean_fwd=22)
    h = 0.94
    rig.place_leg(P, 'l', (0.10, DECK + 0.085, 0.16), l1=0.43 * h, l2=0.42 * h, pole=(0.1, 0.3, 1))
    rig.place_leg(P, 'r', (-0.12, DECK + 0.085, -0.20), l1=0.43 * h, l2=0.42 * h, pole=(-0.1, 0.3, 1))
    rig.lean(P, side=np.radians(8))
    rig.place_arm(P, 'r', P['sh_r'] + v3(-0.20, -0.14, -0.12), (-0.35, -0.3, -1), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(-0.5, 0.25, -0.8))          # Cutwater swept back
    rig.place_arm(P, 'l', P['sh_l'] + v3(0.02, -0.18, 0.34), (0.35, -0.5, -1), l1=0.27 * h, l2=0.26 * h)
    P['head_yaw'] = np.radians(-16)
    P['spray'] = 0.55
    P['spray_seed'] = 3
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    sled = []
    add_s = lambda prim, mat, k=0.0: sled.append(Part(prim, mat, k))
    bone_sled(add_s, P, length=1.4, width=0.46, deck=DECK, rich=True)
    # a short mast with a patched triangle of sail, raked back
    mb = v3(-0.05, DECK, 0.25)
    mt = mb + v3(-0.04, 0.95 - 0.5 * P['sled_break'], -0.18)
    def sail(p, a=mt, b=mb + v3(0, 0.25, 0), c=mb + v3(0.0, 0.3, -0.75)):
        # thin triangle: plane through a, b, c
        n = norm(np.cross(b - a, c - a))
        dpl = np.abs((p - a) @ n) - 0.006
        e = []
        for u, v in ((a, b), (b, c), (c, a)):
            en = norm(np.cross(n, v - u))
            e.append(-((p - u) @ en))
        inside = np.maximum(np.maximum(e[0], e[1]), e[2])
        return np.maximum(dpl, inside)
    if False:
        add_s(Func(sail, (mt + mb + mb + v3(0, 0.3, -0.75)) / 3, 0.7), 'sail', 0.0)
    for prt in sled:
        parts.append(prt)
    body(P, add, C)
    add(ragged_coat(P, hem_lo=0.50, hem_hi=0.66, slope=1, opening=0.6, flare=0.6), 'coat', 0.0)
    coat_tail(P, add, 'coat', length=0.5 + 0.2 * P['coat_fly'], width=0.14)
    goggles(P, add, up=False)
    scarf(P, add, 'canvas', tail=True, side=1)
    flare_belt(P, add, n=5)
    # Cutwater: a long curved single-edged blade
    d = P['item_r']
    if d is not None:
        d = norm(d)
        g = hand_pos(P, 'r')
        add(Capsule(g - d * 0.07, g + d * 0.06, 0.012), 'leather', 0.0)
        sv = norm(np.cross(d, v3(0, 1, 0.2)))
        add(Capsule(g + d * 0.06 - sv * 0.05, g + d * 0.06 + sv * 0.05, 0.01), 'brass', 0.0)
        prev = g + d * 0.07
        for k in range(1, 5):
            t = k / 4
            p = g + d * (0.07 + 0.62 * t) + sv * 0.06 * t * t
            add(Capsule(prev, p, 0.020 - 0.004 * k, 0.018 - 0.004 * k), 'steel', 0.0)
            prev = p
    # rein
    gl = hand_pos(P, 'l')
    if P['sled_break'] < 0.3:
        for sxx in (-1, 1):
            add(Capsule(gl, v3(sxx * 0.21, 0.27, 0.66), 0.006), 'rope', 0.0)
    # lit fuse on the flare belt (tell)
    pel = P['pelvis']
    fz = pel + v3(-0.15, 0.17, 0.07)
    add(Sphere(fz, 0.012 * (0.7 + 0.4 * P['glow'])), 'fuse', 0.0)
    lights.append(Light(pos=fz + v3(0, 0.03, 0.03), color=_hex('#ff9a40'), intensity=0.6 * P['glow'], radius=0.1))
    hand_flare(P, add, lights, 'l')
    # drift: yaw and heel the whole sled
    place_sled(parts, lights, P, dz=-0.30, yaw=np.radians(18), heel=np.radians(-5))
    mats = sv_materials(P, skin='light', hair=_hex('#3a2016'), coat_seed=41,
                        coat_colors=(MUTED_RUST, BONE, OCHRE, CANVAS, SAILCLOTH))
    mats.update(sled_materials())
    mats['sail'] = Material(patchwork(lambda: v3(0, 0, 0), (SAILCLOTH, BONE, CANVAS, MUTED_RUST), cell=0.16, seed=2, mute=0.3),
                            spec=0.02, brush=0.08)
    return finish(P, FACTION, parts, mats, lights=lights)


def _neutral():
    return neutral_pose()


_ROWS, _frames = sled_rows(neutral_pose, attack='swing', side='r')
ROWS = _ROWS


def frames():
    fr = _frames()
    for name in ('idle', 'hit'):
        for P, _ in fr[name]:
            P['spray'] = max(P['spray'], 0.4)
    return fr

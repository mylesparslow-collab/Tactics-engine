"""Bone-Sled Rider (Salvage Compact, mobile). A lean courier crouched on a sled of leviathan ribs:
bone runners curling up at the prow, rib arches, lashed hull planks, a keg and rope coil at the back.
A couched bone lance, goggles down, a tin lantern swinging from a pole at the prow (the idle tell),
coat tail streaming. Salt sprays off the runners when it moves."""
import numpy as np
from _salvage_compact_common import *
from render import Camera

UNIT_ID = 'salvage_compact_bone_sled_rider'
FACTION = 'salvage_compact'
CAMERA = Camera(ppm=46)
C = Costume(top='coat', sleeve='coat2', legs='trousers', hand='glove', skirt=None, head='bald',
            belt='leather', girth=0.9)
DECK = 0.17


def neutral_pose():
    P = rider_pose(height=0.95, build=0.9, deck=DECK, crouch=0.6, lean_fwd=16)
    h = 0.95
    rig.place_arm(P, 'r', P['sh_r'] + v3(-0.06, -0.30, 0.16), (-0.35, -0.3, -1), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(0.08, 0.12, 1.0))
    rig.place_arm(P, 'l', P['sh_l'] + v3(0.04, -0.22, 0.30), (0.35, -0.5, -1), l1=0.27 * h, l2=0.26 * h)
    P['head_yaw'] = np.radians(-8)
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    bone_sled(add, P, length=1.35, width=0.48, deck=DECK)
    body(P, add, C)
    add(ragged_coat(P, hem_lo=0.55, hem_hi=0.7, slope=1, opening=0.5, flare=0.6, top=1.02), 'coat', 0.0)
    coat_tail(P, add, 'coat', length=0.4 + 0.15 * P['coat_fly'])
    wrap_head(P, add, 'coat2', knot_side=-1)
    goggles(P, add, up=False)
    scarf(P, add, 'canvas', tail=False)
    d = P['item_r']
    if d is not None:
        bone_lance(add, hand_pos(P, 'r'), norm(d), below=0.35, above=1.0)
    # rein: a rope from the left hand to the prow curl
    gl = hand_pos(P, 'l')
    if P['sled_break'] < 0.3:
        for sxx in (-1, 1):
            add(Capsule(gl, v3(sxx * 0.22, 0.27, 0.64), 0.006), 'rope', 0.0)
    # lantern pole at the prow (left runner), lantern swinging
    base = v3(0.24, 0.12, 0.47)
    top = base + v3(0.04 + 0.3 * P['sled_break'], 0.75 - 0.3 * P['sled_break'], -0.06)
    add(Capsule(base, top, 0.014), 'wood', 0.0)
    lash(add, base, top, n=1, r=0.02, at=(0.1,))
    add(Capsule(top, top + v3(0.0, 0.0, 0.10), 0.008), 'wood', 0.0)
    lc = top + v3(0.0, -0.08, 0.10)
    add(Capsule(top + v3(0, 0, 0.1), lc + v3(0, 0.05, 0), 0.004), 'iron', 0.0)
    tin_lantern(add, lights, lc, P['glow'], size=0.85)
    hand_flare(P, add, lights, 'l')
    place_sled(parts, lights, P, dz=-0.28)
    mats = sv_materials(P, skin='light', hair=_hex('#2e2018'), coat_seed=31,
                        coat_colors=(CANVAS, MUTED_RUST, SAILCLOTH, OCHRE))
    mats.update(sled_materials())
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = sled_rows(neutral_pose, attack='thrust', side='r')

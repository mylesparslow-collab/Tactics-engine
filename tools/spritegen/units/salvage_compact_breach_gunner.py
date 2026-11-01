"""Breach-Gunner (Salvage Compact, ranged). Soot-faced gunner with a stubby flared hand cannon braced
at the hip, a powder keg strapped high on the back, a mortar fuse coiled on the shoulder. Goggles
down, oilskin. Defining detail: the bell-mouthed hand cannon with a smouldering match."""
import numpy as np
from _salvage_compact_common import *

UNIT_ID = 'salvage_compact_breach_gunner'
FACTION = 'salvage_compact'

C = Costume(top='coat2', sleeve='oilskin', legs='trousers', hand='glove', skirt=None, head='bald',
            belt='leather', girth=1.15)


def neutral_pose():
    P = base_pose(height=0.98, build=1.08)
    rig.lean(P, fwd=np.radians(-2), side=np.radians(-5))
    rig.place_leg(P, 'l', (0.17, 0.085, 0.16))
    rig.place_arm(P, 'r', v3(-0.22, 1.02, 0.10), (-0.35, -0.4, -1))
    P['item_r'] = norm(v3(0.1, 0.35, 1.0))
    rig.place_arm(P, 'l', P['wr_r'] + norm(v3(0.1, 0.35, 1.0)) * 0.30 + v3(0.02, -0.05, 0), (0.35, -0.6, -1))
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    add(ragged_coat(P, hem_lo=0.30, hem_hi=0.50, slope=1, opening=0.6, flare=0.85, girth=1.15), 'oilskin', 0.0)
    knit_cap(P, add, 'soot', slouch=0.5)
    goggles(P, add, up=False)
    pauldron(P, add, 'l', size=1.0, layers=2)
    ch, pel = P['chest'], P['pelvis']
    keg(add, ch + v3(0.05, 0.12, -0.21), up=(0.3, 1, -0.1), r=0.12, hh=0.15)
    add(Capsule(ch + v3(-0.15, 0.15, 0.08), pel + v3(0.15, 0.05, 0.1), 0.014), 'rope', 0.0)
    d = P['item_r']
    if d is not None:
        d = norm(d)
        g = hand_pos(P, 'r')
        add(Capsule(g - d * 0.18 - v3(0, 0.03, 0), g + d * 0.06, 0.035, 0.03), 'wood', 0.01)
        a, b = g + d * 0.04, g + d * 0.55
        add(Cylinder(a, b, 0.045, 0.01), 'iron', 0.0)
        add(Cylinder(b - d * 0.04, b + d * 0.08, 0.075, 0.012), 'iron', 0.0)    # bell mouth
        for t in (0.2, 0.55):
            add(Torus(a + (b - a) * t, d, 0.047, 0.01), 'rust', 0.0)
        # slow match
        m = g + d * 0.10 + v3(0, 0.06, 0)
        add(Capsule(m, m + v3(0.03, 0.06, -0.04), 0.006), 'rope', 0.0)
        add(Sphere(m + v3(0.03, 0.065, -0.04), 0.012), 'fuse', 0.0)
        lights.append(Light(pos=m + v3(0.03, 0.08, 0), color=_hex('#ff9a40'), intensity=0.7 * P['glow'], radius=0.1))
        if P['fx'] > 0:
            f = P['fx']
            mz = b + d * 0.14
            add(Ellipsoid(mz, (0.09 * f, 0.09 * f, 0.13 * f), basis_from(d)), 'flash', 0.0)
            lights.append(Light(pos=mz, color=_hex('#ffd08a'), intensity=2.5 * f, radius=0.35))
            smoke_puffs(add, mz + d * 0.05, f, n=5, seed=12, spread=0.12, size=0.06)
    mats = sv_materials(P, skin='mid', hair=_hex('#1a120e'), coat_seed=21,
                        coat_colors=(DRAB, MUTED_RUST, CANVAS, OCHRE))
    face = face_albedo(P, SKINS['mid'], _hex('#1a120e'))
    mats['skin'] = Material(lambda p, n: face(p, n) * (0.72 + 0.28 * fbm(p, 30, 2)[:, None]),
                            spec=0.06, gloss=12, sss=0.6, brush=0.04)
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = sv_rows(neutral_pose, attack_style='shoot', weapon_side='r', fidget='shoulder', cast_side='l')

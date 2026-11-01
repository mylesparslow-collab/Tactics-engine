"""Powder-Monk (Salvage Compact, fire caster). Keeper of the fat kilns: soot-black hooded robe with
a rust patch, tallow-stained apron, a powder cane with a smouldering fuse at its tip, a bone powder
horn on the belt and a small keg on the back. Tell: the fuse flickers and smokes."""
import numpy as np
from _salvage_compact_common import *

UNIT_ID = 'salvage_compact_powder_monk'
FACTION = 'salvage_compact'

C = Costume(top='robe', sleeve='robe', legs='trousers', hand='skin', skirt=None, head='bald',
            belt='rope', girth=1.05, boots_tall=False)


def neutral_pose():
    P = base_pose(height=0.98, build=0.95)
    rig.lean(P, fwd=np.radians(5), side=np.radians(-2))
    P['head_pitch'] = np.radians(-8)
    rig.place_arm(P, 'r', v3(-0.33, 1.08, 0.24), (-0.35, -0.5, -1))
    P['item_r'] = norm(v3(-0.12, 1.0, 0.22))
    rig.place_arm(P, 'l', v3(0.12, 1.05, 0.16), (0.35, -0.4, -1))
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    add(ragged_coat(P, hem_lo=0.08, hem_hi=0.22, slope=-1, opening=0.0, flare=0.9, notch=0.04), 'robe', 0.0)
    add(hood_shell(P, size=1.05, peak=0.06), 'robe', 0.0)
    pel, ch = P['pelvis'], P['chest']
    # apron (front panel, slightly askew)
    # bandolier of tin powder flasks across the chest, diagonal
    a0, a1 = P['sh_l'] + v3(-0.03, -0.02, 0.06), pel + v3(-0.13, 0.06, 0.1)
    add(Capsule(a0, a1, 0.016), 'apron', 0.0)
    for t in (0.25, 0.5, 0.75):
        c = a0 + (a1 - a0) * t + v3(0, 0, 0.03)
        tin_cylinder(add, c - v3(0, 0.035, 0), c + v3(0, 0.035, 0), 0.022, mat='tin', bands=False)
    # cane with fuse
    r = held(P, add, 'r', 'staff', shaft='wood', head='rust', below=0.95, above=0.72)
    if r:
        butt, tip = r
        d = norm(tip - butt)
        add(Cylinder(tip - d * 0.02, tip + d * 0.08, 0.03, 0.004), 'tin', 0.0)   # tin fuse holder
        g = P['glow'] * (1 + 1.2 * P['cast_glow'])
        f = tip + d * 0.10
        add(Capsule(tip + d * 0.08, f + v3(0.02, 0.03, 0), 0.006), 'soot', 0.0)
        add(Sphere(f + v3(0.02, 0.035, 0), 0.022 * (0.8 + 0.4 * g)), 'fuse', 0.0)
        lights.append(Light(pos=f + v3(0, 0.05, 0.03), color=_hex('#ff9a40'), intensity=1.4 * g, radius=0.2))
        smoke_puffs(add, f + v3(0.02, 0.06, 0), 0.5 + 0.5 * P['cast_glow'], n=3, seed=2, spread=0.03, size=0.028)
        lash(add, butt, tip, n=2, r=0.022, at=(0.6, 0.66))
    # bone powder horn and keg
    add(Capsule(pel + v3(0.14, 0.02, 0.07), pel + v3(0.17, -0.18, 0.12), 0.035, 0.012), 'bone', 0.0)
    add(Capsule(pel + v3(-0.1, 0.12, 0.1), ch + v3(0.12, 0.14, 0.06), 0.011), 'rope', 0.0)
    keg(add, ch + v3(-0.02, -0.02, -0.19), up=(0.15, 1, 0), r=0.09, hh=0.12)
    if P['cast_glow'] > 0.05:
        # the blessed fuse burst: flame cupped in the left hand
        g = hand_pos(P, 'l')
        a = P['cast_glow']
        add(Ellipsoid(g + v3(0, 0.07, 0.02), (0.04 * a + 0.01, 0.07 * a + 0.01, 0.04 * a + 0.01)), 'flame', 0.0)
        lights.append(Light(pos=g + v3(0, 0.1, 0.05), color=_hex('#ff9a40'), intensity=2.0 * a, radius=0.25))
        smoke_puffs(add, g + v3(0, 0.14, 0), a, n=4, seed=8, spread=0.06, size=0.04)
    mats = sv_materials(P, skin='weathered', hair=_hex('#2a2018'), beard=_hex('#3a2e24'))
    mats['robe'] = Material(patchwork(lambda: P['pelvis'], (_hex('#5a4a3c'), _hex('#3a332d'), MUTED_RUST, _hex('#6a5a48')),
                                      cell=0.11, seed=2, mute=0.4), spec=0.04, brush=0.1)
    mats['apron'] = Material(lambda p, n: np.where((fbm(p, 16, 3) > 0.72)[:, None], _arr(TALLOW, len(p)) * 0.7,
                                                   _arr(_hex('#6a4a32'), len(p))), spec=0.3, gloss=20, brush=0.08)
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = sv_rows(neutral_pose, attack_style='swing', weapon_side='r', fidget='shoulder', cast_side='l')

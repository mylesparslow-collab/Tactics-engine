"""Wrecker (Salvage Compact, skirmisher). Lean, mid-slip across the salt: wrecking axe in the right
hand, hooked gutting knife in the left, long patchwork coat with a diagonal ragged tail, bandana and
goggles pushed up. Defining detail: the hooked blade."""
import numpy as np
from _salvage_compact_common import *

UNIT_ID = 'salvage_compact_wrecker'
FACTION = 'salvage_compact'

C = Costume(top='coat2', sleeve='coat', legs='trousers', hand='glove', skirt=None, head='bald',
            belt='leather', girth=0.9)


def neutral_pose():
    P = base_pose(height=1.0, build=0.92)
    h = 1.0
    # low, sliding stance: wide feet, weight on the front leg
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + rig.UPPER, v3(0, -0.08, 0))
    rig.place_leg(P, 'l', (0.16, 0.085, 0.22))
    rig.place_leg(P, 'r', (-0.16, 0.085, -0.18))
    rig.lean(P, fwd=np.radians(12), side=np.radians(-6))
    P['head_yaw'] = np.radians(-14)
    rig.place_arm(P, 'r', v3(-0.32, 1.06, 0.30), (-0.35, -0.6, -1))
    P['item_r'] = norm(v3(-0.75, 0.6, 0.25))          # axe angled out
    rig.place_arm(P, 'l', v3(0.24, 0.95, 0.24), (0.35, -0.4, -1))
    P['item_l'] = norm(v3(0.3, -0.6, 0.6))             # knife reversed, low
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    add(ragged_coat(P, hem_lo=0.22, hem_hi=0.58, slope=1, opening=0.55, flare=1.0, notch=0.08), 'coat', 0.0)
    wrap_head(P, add, 'coat2', knot_side=1)
    goggles(P, add, up=True)
    scarf(P, add, 'canvas', tail=True, side=1)
    r = held(P, add, 'r', 'axe', shaft='wood', head='rust', above=0.62)
    if r:
        b, t = r
        d = norm(t - b)
        sv = norm(np.cross(d, v3(0, 1, 0.2)))
        # broad bearded wrecking blade, cut from hull plate
        def blade(p, c=t - d * 0.08 + sv * 0.11, R=basis_from(d, sv)):
            q = (p - c) @ R
            x, y, z = q[:, 0], q[:, 1], q[:, 2]
            dd = np.maximum(np.abs(y) - (0.07 + 0.07 * np.clip(z / 0.12, 0, 1)), np.abs(z) - 0.10)
            return np.maximum(dd, np.abs(x) - 0.007) - 0.003
        add(Func(blade, t, 0.2), 'steelrust', 0.0)
        lash(add, b, t, n=1, r=0.02, at=(0.85,))
    k = held(P, add, 'l', 'knife', head='iron', above=0.30)
    if k:
        b, t = k
        d = norm(t - b)
        sv = norm(np.cross(d, v3(0, 1, 0.2)))
        add(Torus(t + sv * 0.04, np.cross(d, sv), 0.04, 0.009), 'steel', 0.0)  # the hook
    # crowbar slung across the back
    ch = P['chest']
    add(Capsule(ch + v3(-0.2, -0.25, -0.13), ch + v3(0.22, 0.32, -0.14), 0.014), 'iron', 0.0)
    mats = sv_materials(P, skin='mid', hair=_hex('#1e1612'), coat_seed=7,
                        coat_colors=(MUTED_RUST, CANVAS, OCHRE, DRAB, BONE))
    mats['steelrust'] = Material(lambda p, n: np.where((fbm(p, 30, 2) > 0.55)[:, None], _arr(RUST, len(p)), _arr(_hex('#a9adab'), len(p))),
                                 spec=0.8, gloss=40, metal=0.5, brush=0.04)
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = sv_rows(neutral_pose, attack_style='swing', weapon_side='r', fidget='sway', flicker=False)

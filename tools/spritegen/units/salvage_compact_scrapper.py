"""Hull Scrapper (Salvage Compact, cheap body).

Hunched forward behind a cut hull-plate held out on the left arm, a boat hook in the right, a dented
tin cap worn askew. Defining detail: the shield is a scrap of ship with half a painted name visible.
"""
import numpy as np
from _salvage_compact_common import *

UNIT_ID = 'salvage_compact_scrapper'
FACTION = 'salvage_compact'

C = Costume(top='coat', sleeve='coat2', legs='trousers', hand='glove', skirt=None, head='bald',
            belt='rope', girth=1.0)


def neutral_pose():
    P = base_pose(height=0.93, build=1.0)
    rig.lean(P, fwd=np.radians(14), side=np.radians(-3))       # hunched forward, list to the right
    P['head_pitch'] = np.radians(-14)
    rig.place_arm(P, 'l', v3(0.12, 1.08, 0.36), (0.35, -0.6, -1))     # shield arm out front
    rig.place_arm(P, 'r', v3(-0.24, 1.0, 0.22), (-0.35, -0.5, -1))
    P['item_r'] = norm(v3(-0.55, 1.0, -0.30))   # boat hook slanted out and back, clear of the face (a Compact diagonal)
    return P


def shield_frame(P):
    el, wr = P['el_l'], P['wr_l']
    c = wr + v3(-0.02, 0.0, 0.07)
    out = norm(v3(-0.35, 0.05, 1.0))
    R = basis_from(v3(0.12, 1, 0.08), out)
    return c, R


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    pel, ch, h = P['pelvis'], P['chest'], P['height']
    # short ragged jerkin skirt, long on the right side
    add(ragged_coat(P, hem_lo=0.52, hem_hi=0.74, slope=-1, opening=0.35, flare=0.6), 'coat', 0.0)
    scarf(P, add, 'coat2', tail=False)
    tin_cap(P, add, 'tin', tilt=-0.3)
    # hook
    r = held(P, add, 'r', 'hook', shaft='wood', head='rust', below=0.75, above=0.75)
    if r:
        lash(add, r[0], r[1], n=2, r=0.02, at=(0.55, 0.62))
    # hull-plate shield: irregular bent slab with a diagonal cut corner and painted name
    c, R = shield_frame(P)

    def slab(p):
        q = (p - c) @ R
        x, y = q[:, 0], q[:, 1]
        z = q[:, 2] + 0.12 * x * x          # bent plate
        d = np.maximum(np.abs(x) - 0.19, np.abs(y) - 0.27)
        d = np.maximum(d, (x + y - 0.27) * 0.707)      # diagonal torch-cut corner
        d = np.maximum(d, (-x - y * 0.4 - 0.21) * 0.9)
        return np.maximum(d, np.abs(z) - 0.012) - 0.004
    add(Func(slab, c, 0.36), 'shield', 0.0)
    for (u, v) in ((-0.13, 0.2), (0.12, -0.21), (-0.13, -0.21), (0.0, 0.21)):
        add(Sphere(c + R @ v3(u, v, 0.016 - 0.12 * u * u), 0.013), 'tin', 0.0)
    # rope handle lashings on the forearm
    lash(add, P['el_l'], P['wr_l'], n=2, r=0.05, at=(0.35, 0.75))
    # tally of salvage on the belt: a rag and a small pry bar
    add(Capsule(pel + v3(0.13, 0.08, 0.06), pel + v3(0.2, -0.25, 0.04), 0.012), 'iron', 0.0)
    mats = sv_materials(P, skin='weathered', hair=_hex('#2e231c'), beard=None, coat_seed=1, coat_colors=(SAILCLOTH, CANVAS, MUTED_RUST, BONE, OCHRE))
    mats['shield'] = Material(painted_plate(lambda: c, lambda: R, letters_col=BONE, base=RUST, band=FLARE),
                              spec=0.35, gloss=18, metal=0.3, brush=0.08)
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = sv_rows(neutral_pose, attack_style='swing', weapon_side='r', fidget='look', flicker=False)

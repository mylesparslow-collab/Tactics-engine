"""Brother Ashmaw, Fat-Cook of the Burning Chapel (Salvage Compact hero). Head of the Powder-Monks:
huge, bald, soot-bearded, in a long scorched robe and a grease-stiff leather apron. A bone shoulder
plate on the left carries three lit tallow candles; a smoking tin censer on a chain swings from the
right hand. Defining detail: the candle-crowned shoulder. Tell: candle and censer flicker."""
import numpy as np
from _salvage_compact_common import *

UNIT_ID = 'salvage_compact_brother_ashmaw'
FACTION = 'salvage_compact'

C = Costume(top='robe', sleeve='robe', legs='trousers', hand='skin', skirt=None, head='bald',
            belt='rope', girth=1.7, boots_tall=False)


def neutral_pose():
    P = base_pose(height=1.06, build=1.28)
    rig.lean(P, fwd=np.radians(4), side=np.radians(-3))
    P['head_pitch'] = np.radians(-6)
    rig.place_arm(P, 'r', v3(-0.34, 1.06, 0.20), (-0.35, -0.3, -1), l1=0.29, l2=0.28)
    P['item_r'] = norm(v3(-0.05, -1.0, 0.12))    # censer hanging down
    rig.place_arm(P, 'l', v3(0.24, 1.16, 0.26), (0.35, -0.5, -1), l1=0.29, l2=0.28)
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    pel, ch, h = P['pelvis'], P['chest'], P['height']
    add(Ellipsoid(pel + v3(0, 0.2, 0.05), (0.27, 0.22, 0.2)), 'robe', 0.05)
    add(ragged_coat(P, hem_lo=0.03, hem_hi=0.16, slope=1, opening=0.0, flare=1.0, girth=1.7, notch=0.04), 'robe', 0.0)
    # apron
    def apron(p):
        q = p - (pel + v3(0, 0.12, 0.04))
        e = np.sqrt((q[:, 0] / 0.29) ** 2 + (q[:, 2] / 0.23) ** 2) - 1.0
        d = np.abs(e * 0.23) - 0.009
        d = np.maximum(d, np.maximum(q[:, 1] - 0.30, -0.62 - q[:, 1]))
        d = np.maximum(d, np.abs(q[:, 0] + 0.03 * q[:, 1]) - 0.15)
        return np.maximum(d, 0.03 - q[:, 2])
    # grease-stiff tallow stole hanging from the neck, plus a rope belt of fuse cord
    nk = P['neck']
    for sx in (-1, 1):
        a = nk + v3(sx * 0.07, -0.03, 0.08)
        b = pel + v3(sx * 0.10, -0.25, 0.24)
        add(Capsule(a, (a + b) / 2 + v3(0, 0, 0.1), 0.035, 0.035), 'apron', 0.01)
        add(Capsule((a + b) / 2 + v3(0, 0, 0.1), b, 0.035, 0.03), 'apron', 0.01)
    # soot beard and brows
    H, Rh = P['head'], head_R(P)
    add(Ellipsoid(H + Rh @ v3(0, -0.085, 0.04) * h, (0.072 * h, 0.08 * h, 0.055 * h), Rh), 'soot', 0.02)
    # candle shoulder: bone plate with three tallow candles
    pauldron(P, add, 'l', size=1.3, mat='bone', layers=1, rivets=False)
    sh = P['sh_l']
    P2 = dict(P)
    P2['glow'] = P['glow'] * (1 + 1.3 * P['cast_glow'])
    for k, (dx, dz, hh) in enumerate(((0.04, -0.04, 0.10), (0.11, 0.02, 0.07), (0.03, 0.06, 0.05))):
        candle(add, lights, sh + v3(dx, 0.07 - 0.03 * k, dz), P2, height=hh, r=0.018)
    # censer on a chain
    d = P['item_r']
    if d is not None:
        d = norm(d)
        g = hand_pos(P, 'r')
        for k in range(5):
            add(Torus(g + d * (0.04 + 0.06 * k), norm(np.cross(d, v3(1, 0, 0)) if k % 2 else np.cross(d, v3(0, 0, 1))), 0.02, 0.006), 'iron', 0.0)
        cc = g + d * 0.40
        add(Sphere(cc, 0.095), 'tin', 0.0)
        add(Cylinder(cc - v3(0, 0.0, 0), cc + v3(0, 0.035, 0), 0.098, 0.004), 'rust', 0.0)
        add(Capsule(cc + v3(0, 0.03, 0), cc + v3(0, 0.12, 0), 0.03, 0.012), 'tin', 0.0)
        for k in range(4):
            a = k * np.pi / 2 + 0.4
            add(Sphere(cc + v3(np.cos(a) * 0.088, -0.015, np.sin(a) * 0.088), 0.02), 'fuse', 0.0)
        gl = P['glow'] * (1 + P['cast_glow'] + P['fx'])
        lights.append(Light(pos=cc + v3(0, 0.05, 0.05), color=_hex('#ff9a40'), intensity=1.2 * gl, radius=0.2))
        smoke_puffs(add, cc + v3(0, 0.07, 0), 0.6 + 0.4 * P['fx'], n=4, seed=6, spread=0.05, size=0.04)
        if P['fx'] > 0:
            add(Ellipsoid(cc + d * 0.02, (0.11 * P['fx'], 0.09 * P['fx'], 0.11 * P['fx'])), 'flame', 0.0)
    if P['cast_glow'] > 0.05:
        gl = hand_pos(P, 'l')
        a = P['cast_glow']
        add(Ellipsoid(gl + v3(0, 0.08, 0.02), (0.05 * a + 0.01, 0.09 * a + 0.01, 0.05 * a + 0.01)), 'flame', 0.0)
        lights.append(Light(pos=gl + v3(0, 0.12, 0.05), color=_hex('#ff9a40'), intensity=2.2 * a, radius=0.3))
        smoke_puffs(add, gl + v3(0, 0.18, 0), a, n=5, seed=9, spread=0.08, size=0.05)
    mats = sv_materials(P, skin='mid', hair=SOOT, beard=None)
    mats['robe'] = Material(patchwork(lambda: P['pelvis'], (_hex('#4a3a30'), MUTED_RUST, SOOT, _hex('#5a4434')),
                                      cell=0.13, seed=3, mute=0.5), spec=0.04, brush=0.1)
    mats['apron'] = Material(lambda p, n: np.where((fbm(p, 12, 3) > 0.70)[:, None], _arr(TALLOW, len(p)) * 0.85,
                                                   _arr(_hex('#6e5038'), len(p))), spec=0.4, gloss=22, brush=0.08)
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = sv_rows(neutral_pose, attack_style='swing', weapon_side='r', fidget='shoulder', cast_side='l')

"""Fat-Renderer (Salvage Compact cheap fire).

Enormous, sweating leviathan-fat boiler: bald soot-streaked head with a rag over the mouth, bare thick
forearms, a long greasy leather apron over a bone-white undershirt, a bubbling tallow cauldron lashed to
his hip on a rope sling, and a huge iron ladle brimming with glowing fat. Defining detail: the steaming
ladle and the cauldron.
"""
import numpy as np
from _salvage_compact_common import *
from _salvage_compact_w2 import *

UNIT_ID = 'salvage_compact_fat_renderer'
FACTION = 'salvage_compact'

C = Costume(top='shirt', sleeve='skinarm', legs='trousers', hand='glove', skirt=None, head='none', belt=None,
            girth=2.0, boots_tall=False)


def neutral_pose():
    P = base_pose(height=0.90, build=1.42)
    rig.lean(P, fwd=np.radians(-5))
    P['head_yaw'] = np.radians(-12)
    rig.place_arm(P, 'r', v3(-0.42, 1.02, 0.24), (-1, -0.2, -0.5))
    P['item_r'] = norm(v3(-0.35, 1.0, 0.35))
    rig.place_arm(P, 'l', v3(0.40, 0.95, 0.12), (1, -0.4, -0.5))
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    H, R, h, b = P['head'], head_R(P), P['height'], P['build']
    # vast belly under a long apron
    add(Ellipsoid(pel + v3(0, 0.15, 0.07), (0.27 * b * 0.8, 0.24, 0.24)), 'shirt', 0.06)
    add(Ellipsoid(pel + v3(0, 0.12, 0.14), (0.25 * b * 0.78, 0.26, 0.17)), 'apron', 0.03)
    tabard_ap = [(0.0, 0.0)]
    top = ch + v3(0, 0.10, 0.115)
    bot = v3(pel[0], 0.30, pel[2] + 0.30)
    mid = (top + bot) / 2
    add(RoundBox(mid + v3(0, 0.0, 0.0), (0.22 * b * 0.9, np.linalg.norm(top - bot) / 2, 0.020), 0.014,
                 basis_from(top - bot, (0, 0, 1))), 'apron', 0.04)
    add(RoundBox(ch + v3(0, 0.12, 0.10), (0.13, 0.10, 0.012), 0.010, rot_x(0.2)), 'apron', 0.0)      # bib
    for sx in (-1, 1):
        add(Capsule(ch + v3(sx * 0.12, 0.20, 0.06), ch + v3(sx * 0.15, 0.27, -0.10), 0.012), 'apron', 0.0)  # straps
    add(Torus(pel + v3(0, 0.12, 0.0), v3(0, 1, 0), 0.30, 0.016), 'rope', 0.0)                  # rope belt
    # bald head with soot streaks, a rag over the mouth, thick neck, heavy brow
    add(Ellipsoid(H, (0.082 * h, 0.099 * h, 0.092 * h), R), 'skin', 0.0)
    add(Ellipsoid(H + R @ v3(0, -0.05, 0.022) * h, (0.075 * h, 0.06 * h, 0.07 * h), R), 'skin', 0.04)
    add(Ellipsoid(H + R @ v3(0, -0.075, 0.015) * h, (0.08 * h, 0.04 * h, 0.07 * h), R), 'skin', 0.03)   # jowl
    add(Capsule(H + R @ v3(0, 0.0, 0.078) * h, H + R @ v3(0, -0.028, 0.092) * h, 0.010, 0.013), 'skin', 0.01)
    add(RoundBox(H + R @ v3(0, -0.04, 0.074) * h, (0.060, 0.026, 0.026), 0.012, R), 'rag', 0.0)
    add(Capsule(H + R @ v3(-0.08, -0.04, 0.0) * h, H + R @ v3(-0.07, -0.01, -0.09) * h, 0.012), 'rag', 0.0)
    add(Capsule(H + R @ v3(-0.07, 0.015, -0.085) * h, H + R @ v3(-0.12, -0.08, -0.12) * h, 0.014, 0.008), 'rag', 0.0)
    add(Torus(nk + v3(0, 0.0, 0.0), v3(0, 1, 0), 0.09 * b, 0.03), 'skin', 0.02)
    # soot-black sleeves rolled to the elbow: bare forearms
    for s in ('r', 'l'):
        el, wr = P['el_' + s], P['wr_' + s]
        add(Capsule(el + (wr - el) * 0.05, wr - (wr - el) * 0.05, 0.062 * b, 0.050 * b), 'skin', 0.01)
        add(Torus(el, norm(wr - el), 0.06 * b, 0.016), 'shirt', 0.0)
    # cauldron on a rope sling at the left hip: iron, bubbling tallow with an ember glow
    cc = pel + v3(0.08, -0.12, 0.34)
    for k in range(2):
        add(Capsule(ch + v3(-0.10, 0.20, 0.07), cc + v3(-0.02 * k, 0.11, 0.0), 0.008), 'rope', 0.0)
    add(Ellipsoid(cc, (0.15, 0.12, 0.15)), 'cauldron', 0.0)
    add(Torus(cc + v3(0, 0.085, 0), v3(0, 1, 0), 0.135, 0.018), 'cauldron', 0.0)
    gl = P['glow']
    add(Cylinder(cc + v3(0, 0.085, 0), cc + v3(0, 0.098, 0), 0.128, 0.004), 'fat', 0.0)
    for k in range(3):
        a = P['tell'] * 6.283 + k * 2.1
        add(Sphere(cc + v3(0.06 * np.sin(a), 0.115 + 0.01 * np.sin(a * 2), 0.06 * np.cos(a)), 0.026), 'fat', 0.0)
    for sx in (-1, 1):
        add(Sphere(cc + v3(sx * 0.125, 0.0, 0.0), 0.014), 'rope', 0.0)
    lights.append(Light(pos=cc + v3(0, 0.12, 0.05), color=_hex('#ff9a40'), intensity=1.0 * gl, radius=0.20))
    smoke_puffs(add, cc + v3(0, 0.12, 0), 0.8 + 0.2 * np.sin(P['tell'] * 6.283), n=4, seed=5, spread=0.07, size=0.045)
    # the ladle: long iron handle, deep bowl heaped with glowing fat
    d = P['item_r']
    if d is not None:
        d = norm(d)
        g = hand_pos(P, 'r')
        tip = g + d * 0.50
        add(Capsule(g - d * 0.22, tip, 0.028, 0.024), 'iron', 0.0)
        for t in (-0.12, -0.02):
            add(Torus(g + d * t, d, 0.026, 0.008), 'rope', 0.0)
        bowl = tip + d * 0.07 + v3(0, 0.0, 0.0)
        add(Ellipsoid(bowl, (0.115, 0.070, 0.115), basis_from(v3(0, 1, 0), d)), 'iron', 0.0)
        add(Ellipsoid(bowl + v3(0, 0.035, 0), (0.106, 0.036, 0.106), basis_from(v3(0, 1, 0), d)), 'fatglow', 0.0)
        smoke_puffs(add, bowl + v3(0, 0.06, 0), 0.8, n=3, seed=9, spread=0.05, size=0.04)
        lights.append(Light(pos=bowl + v3(0, 0.1, 0.05), color=_hex('#ff9a40'), intensity=1.2 * gl, radius=0.22))
        if P['fx'] > 0.05:         # splash
            for k in range(5):
                a = k * 1.26
                add(Sphere(bowl + d * 0.18 * P['fx'] * (1 + k * 0.4) + v3(0.04 * np.sin(a), 0.03 * k, 0.04 * np.cos(a)), 0.020), 'fatglow', 0.0)
    mats = sv_materials(P, skin='light', hair=_hex('#4a3626'), coat_seed=31)
    mats['skin'] = Material(face_albedo(P, _hex('#d3a98d'), _hex('#4a3626'), lips=_hex('#9a4a40')), spec=0.18, gloss=18, sss=0.7, brush=0.02)
    mats.update({
        'shirt': Material(lambda p, n: np.array(_hex('#cfc4a6'))[None, :] * (0.88 + 0.18 * fbm(p, 14, 2)[:, None]), spec=0.04, brush=0.1),
        'skinarm': Material(_hex('#cfa588'), spec=0.12, gloss=14, sss=0.6, brush=0.03),
        'apron': Material(lambda p, n: np.array(_hex('#40362c'))[None, :] * (0.8 + 0.4 * (fbm(p, 12, 3) > 0.55)[:, None] * 1.0) + np.array(TALLOW)[None, :] * 0.18 * (fbm(p, 22, 2) > 0.6)[:, None],
                          spec=0.4, gloss=22, brush=0.08),
        'rag': Material(_hex('#8f866f'), spec=0.03, brush=0.1),
        'cauldron': Material(_hex('#3b3a38'), spec=0.5, gloss=26, metal=0.5, brush=0.06),
        'fat': Material(_hex('#ffd98a'), spec=0.4, gloss=30, emissive=tuple(np.array(_hex('#ffb347')) * 0.6 * gl), rim=0.0),
        'fatglow': Material(_hex('#ffb35a'), spec=0.4, gloss=30, emissive=tuple(np.array(_hex('#ff8a30')) * 1.1 * gl), rim=0.0),
        'iron': Material(_hex('#4a4a4c'), spec=0.7, gloss=30, metal=0.7, brush=0.05),
        'trousers': Material(lambda p, n: np.array(_hex('#4c453a'))[None, :] * (0.85 + 0.2 * fbm(p, 16, 2)[:, None]), spec=0.04, brush=0.09),
    })
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, _frames = sv_rows(neutral_pose, attack_style='swing', weapon_side='r', fidget='sway', cast_side='l')


def frames():
    f = _frames()
    return f

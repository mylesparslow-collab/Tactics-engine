"""Ballast Diver (Salvage Compact tank).

Wreck-diver sealed in a riveted copper suit gone green at the seams: a huge round brass-ringed helmet
with three portholes and a lamp, corrugated arms with heavy riveted gauntlets, a lead-block weight belt,
lead boots, a back tank and a coiled air hose lashed with rope, and a long crowbar. Defining detail:
the big riveted helmet and lead boots.
"""
import numpy as np
from _salvage_compact_common import *

UNIT_ID = 'salvage_compact_ballast_diver'
FACTION = 'salvage_compact'

COPPER = _hex('#8c6048')
VERDI = _hex('#5c8479')
LEAD = _hex('#4c4f56')

C = Costume(top='suit', sleeve='suit', legs='suit', boot='lead', hand='gaunt', skirt=None, head='none',
            belt=None, girth=1.7, boots_tall=False)


def neutral_pose():
    P = base_pose(height=0.95, build=1.30)
    rig.lean(P, fwd=np.radians(3))
    P['head_yaw'] = np.radians(-10)
    rig.place_arm(P, 'r', v3(-0.40, 0.98, 0.24), (-1, -0.3, -0.5))
    P['item_r'] = norm(v3(-0.05, 0.55, 0.85))
    rig.place_arm(P, 'l', v3(0.34, 0.95, 0.12), (1, -0.4, -0.5))
    return P


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    H, R, h, b = P['head'], head_R(P), P['height'], P['build']
    # corrugated limbs: copper rings on arms and legs
    for s in ('r', 'l'):
        sh, el, wr = P['sh_' + s], P['el_' + s], P['wr_' + s]
        for a_, b_, rr in ((sh, el, 0.075), (el, wr, 0.064)):
            dd = norm(b_ - a_)
            for t in (0.2, 0.5, 0.8):
                add(Torus(a_ + (b_ - a_) * t, dd, rr * b * 0.92, 0.011), 'ring', 0.0)
        add(Sphere(el, 0.072 * b), 'ring', 0.01)
        hp, kn, an = P['hip_' + s], P['kn_' + s], P['an_' + s]
        for a_, b_, rr in ((hp, kn, 0.088), (kn, an, 0.072)):
            dd = norm(b_ - a_)
            for t in (0.25, 0.55, 0.85):
                add(Torus(a_ + (b_ - a_) * t, dd, rr * b * 0.9, 0.011), 'ring', 0.0)
        add(Sphere(kn, 0.078 * b), 'ring', 0.01)
        # lead boot: huge block with a toe cap
        fd = rot_y(P['foot_%s_yaw' % s]) @ v3(0, 0, 1)
        add(RoundBox(an + fd * 0.10 + v3(0, -0.045, 0), (0.075 * b, 0.05, 0.16), 0.03, basis_from(v3(0, 1, 0), fd)), 'lead', 0.0)
        add(RoundBox(an + v3(0, 0.0, 0), (0.062 * b, 0.05, 0.062 * b), 0.02), 'ring', 0.0)
        # gauntlet: big riveted mitt
        d = norm(wr - el)
        add(Sphere(wr + d * 0.05, 0.062 * b), 'ring', 0.01)
        add(Cylinder(wr - d * 0.02, wr + d * 0.015, 0.066 * b, 0.008), 'brass', 0.0)
    # chest plate seams and a belt of lead weights
    add(Torus(ch + v3(0, -0.06, 0), v3(0, 1, 0), 0.17 * b, 0.014), 'ring', 0.0)
    add(Torus(pel + v3(0, 0.04, 0), v3(0, 1, 0), 0.15 * b * 1.25, 0.018), 'leather', 0.0)
    for k in range(6):
        a = np.radians(-70 + k * 28)
        add(RoundBox(pel + v3(np.sin(a) * 0.20 * b, 0.02, np.cos(a) * 0.16 * b), (0.032, 0.05, 0.020), 0.008, rot_y(a)), 'lead', 0.0)
    for k in range(5):     # rivets on the chest collar
        a = np.radians(-50 + k * 25)
        add(Sphere(ch + v3(np.sin(a) * 0.15 * b, 0.12, np.cos(a) * 0.11 * b), 0.012), 'brass', 0.0)
    # breastplate collar ring and the great helmet
    add(Torus(nk + v3(0, -0.03, 0.0), v3(0, 1, 0), 0.115, 0.024), 'brass', 0.0)
    hc = H + v3(0, 0.0, 0.0)
    rh = 0.185
    add(Sphere(hc, rh), 'copper', 0.0)
    add(Torus(hc + v3(0, -0.10, 0), v3(0, 1, 0), 0.165, 0.016), 'brass', 0.0)
    for k in range(10):
        a = k * 0.628
        add(Sphere(hc + v3(0.17 * np.cos(a), -0.10, 0.17 * np.sin(a)), 0.0095), 'ring', 0.0)
    # portholes: front and two sides, brass-ringed, dark teal glass
    for ang in (0.0, 0.95, -0.95):
        dv = R @ v3(np.sin(ang), 0.02, np.cos(ang))
        c = hc + dv * (rh - 0.004)
        add(Torus(c, dv, 0.060 if ang == 0.0 else 0.046, 0.011), 'brass', 0.0)
        add(Cylinder(c - dv * 0.008, c + dv * 0.004, 0.058 if ang == 0.0 else 0.044, 0.004), 'port', 0.0)
        if ang == 0.0:
            for k in range(6):
                a = k * 1.047
                add(Sphere(c + (R @ v3(np.cos(a), np.sin(a), 0)) * 0.066 + dv * 0.004, 0.007), 'ring', 0.0)
    # lamp on the crown, hose to the back tank
    lampc = hc + R @ v3(0.0, 0.17, 0.05)
    add(RoundBox(lampc, (0.035, 0.03, 0.04), 0.012, R), 'brass', 0.0)
    add(Cylinder(lampc + R @ v3(0, 0, 0.04), lampc + R @ v3(0, 0, 0.055), 0.028, 0.005), 'lamp', 0.0)
    lights.append(Light(pos=lampc + R @ v3(0, 0.0, 0.12), color=_hex('#ffcf7a'), intensity=1.0 * P['glow'], radius=0.16))
    # back tank pair and a rope-lashed hose
    for sx in (-1, 1):
        add(Capsule(ch + v3(sx * 0.09, -0.12, -0.20), ch + v3(sx * 0.09, 0.22, -0.20), 0.062, 0.062), 'tank', 0.0)
        add(Sphere(ch + v3(sx * 0.09, 0.24, -0.20), 0.062), 'tank', 0.0)
        for t in (-0.05, 0.12):
            add(Torus(ch + v3(sx * 0.09, t, -0.20), v3(0, 1, 0), 0.064, 0.010), 'rope', 0.0)
    hose = [hc + v3(-0.05, 0.02, -0.17), ch + v3(-0.16, 0.30, -0.28), ch + v3(-0.02, 0.38, -0.22),
            ch + v3(0.10, 0.28, -0.26), ch + v3(0.09, 0.26, -0.20)]
    for a_, b_ in zip(hose[:-1], hose[1:]):
        add(Capsule(a_, b_, 0.022), 'hose', 0.0)
    for a_ in hose[1:-1]:
        add(Sphere(a_, 0.026), 'hose', 0.0)
    # crowbar in the right hand (long, bent end with a claw), rope-wrapped grip
    d = P['item_r']
    if d is not None:
        d = norm(d)
        g = hand_pos(P, 'r')
        tip = g + d * 0.62
        add(Capsule(g - d * 0.30, tip, 0.023, 0.020), 'iron', 0.0)
        sv = norm(np.cross(d, v3(0, 0, 1)))
        add(Capsule(tip, tip + d * 0.06 + sv * 0.10, 0.021, 0.014), 'iron', 0.0)
        add(Capsule(tip + d * 0.06 + sv * 0.10, tip + d * 0.02 + sv * 0.15, 0.014, 0.006), 'iron', 0.0)
        for t in (-0.15, -0.05, 0.05):
            add(Torus(g + d * t, d, 0.026, 0.007), 'rope', 0.0)
    mats = sv_materials(P, skin='weathered')
    def verd(p, n):
        cu = np.array(COPPER)[None, :] * (0.92 + 0.14 * fbm(p, 10, 2)[:, None])
        low = np.clip((0.55 - p[:, 1]) / 0.55, 0, 1)
        m = np.clip((fbm(p, 16, 3) - 0.60 + 0.25 * low) * 5.0, 0, 1)[:, None]
        return cu * (1 - m) + np.array(VERDI)[None, :] * m
    mats.update({
        'suit': Material(verd, spec=0.5, gloss=26, metal=0.6, brush=0.07),
        'copper': Material(verd, spec=0.6, gloss=30, metal=0.7, brush=0.07),
        'ring': Material(lambda p, n: verd(p, n) * 0.85, spec=0.5, gloss=24, metal=0.6, brush=0.07),
        'gaunt': Material(verd, spec=0.5, gloss=24, metal=0.6, brush=0.07),
        'lead': Material(LEAD, spec=0.5, gloss=18, metal=0.5, brush=0.06),
        'tank': Material(lambda p, n: np.array(_hex('#7a8a8c'))[None, :] * (0.85 + 0.2 * fbm(p, 20, 2)[:, None]), spec=0.5, gloss=28, metal=0.5, brush=0.06),
        'hose': Material(_hex('#3c3a35'), spec=0.2, gloss=14, brush=0.05),
        'port': Material(_hex('#16363a'), spec=1.0, gloss=70, emissive=tuple(np.array(_hex('#2c7a74')) * 0.35), rim=0.0),
        'lamp': Material(_hex('#ffcf7a'), emissive=tuple(np.array(_hex('#ffc46a')) * min(P['glow'], 1.6)), rim=0.0),
        'iron': Material(_hex('#5a5f66'), spec=0.7, gloss=30, metal=0.7, brush=0.05),
    })
    return finish(P, FACTION, parts, mats, lights=lights)


ROWS, frames = sv_rows(neutral_pose, attack_style='swing', weapon_side='r', fidget='look', cast_side='l')

"""Verge Lancer (Salt Concord shock cavalry).

Heavy horse of the Verge forts: the Causeway Outrider's horse sculpt, now in salt-scaled steel-blue
barding (crinet, peytral, flanchards, croupiere, spiked chanfron) under a squared salt-bordered
caparison. The rider is plate-harnessed in a closed barbute with a steel-blue horsehair crest and
carries a long couched lance with a brass vamplate and a heavy pennant. Defining detail: the
armoured destrier and the lowered lance.
"""
import numpy as np
from kit.humanoid import *
from kit.looks import LOOKS
from kit.xform import transform_parts
from render import Camera
from _salt_concord_common import *
import salt_concord_causeway_outrider as O

UNIT_ID = 'salt_concord_verge_lancer'
FACTION = 'salt_concord'
LOOK = LOOKS[FACTION]
CAMERA = Camera(ppm=44)

C = Costume(top='plate', sleeve='plate', legs='plate', hand='gaunt', skirt=None, head='bald', belt='leather',
            girth=1.18, boots_tall=True)
SEAT = O.SEAT
ZS = O.ZS


_O_NEUTRAL = O.neutral_pose


def neutral_pose():
    P = _O_NEUTRAL()
    # heavier rider: re-seat with a lance couched low under the right arm
    P['build'] = 1.12
    rig.place_arm(P, 'r', v3(-0.27, SEAT + 0.10, 0.12), (-1, -0.3, -0.5))
    P['item_r'] = norm(v3(-0.10, 0.20, 1.0))
    return P


def barding(add, P):
    fold = P['fold']
    by = 0.88 - 0.46 * fold
    # peytral (chest) and croupiere (rump): squared scale plates over the horse
    add(RoundBox(v3(0, by - 0.02, 0.60), (0.20, 0.22, 0.04), 0.05, rot_x(-0.18)), 'scales', 0.0)
    add(Ellipsoid(v3(0, by + 0.12, -0.40), (0.275, 0.29, 0.30)), 'scales', 0.0)
    for sx in (-1, 1):
        # caparison skirt: squared salt-bordered cloth from the saddle to the hocks, plated flanchard low on the barrel
        add(RoundBox(v3(sx * 0.262, by - 0.20, 0.0), (0.012, 0.085, 0.30), 0.010), 'cloth_h', 0.0)
        add(RoundBox(v3(sx * 0.266, by - 0.30, 0.0), (0.010, 0.016, 0.30), 0.006), 'trim', 0.0)
        add(RoundBox(v3(sx * 0.268, by - 0.02, 0.10), (0.012, 0.07, 0.15), 0.012), 'scales', 0.0)
        add(Sphere(v3(sx * 0.274, by + 0.03, 0.25), 0.020), 'brass', 0.0)
    # crinet: overlapping plates along the neck
    na = v3(0, by + 0.12, 0.50)
    nd = norm(v3(0, 0.80 - 0.5 * P['hneck'] - 0.4 * fold, 0.60))
    for t in np.linspace(0.12, 0.88, 6):
        c = na + nd * 0.52 * t + v3(0, 0.0, 0.0)
        add(RoundBox(c + v3(0, 0.02, 0.0), (0.12 - 0.04 * t, 0.032, 0.14 - 0.03 * t), 0.014,
                     basis_from(nd, (0, 0, 1))), 'scales', 0.0)
    # chanfron with a brass spike (the existing faceplate is made bigger)
    nb = na + nd * 0.52
    hd = norm(v3(0, -0.75, 0.66) + v3(0, 0, 0.3 * P['hneck']))
    hb = nb + hd * 0.34
    add(Capsule(nb + hd * 0.05, hb + hd * 0.05, 0.07, 0.052), 'scales', 0.0)
    add(Capsule(nb + hd * 0.06 + v3(0, 0.07, 0.0), nb + hd * 0.06 + v3(0, 0.17, 0.0) + hd * 0.05, 0.016, 0.003), 'brass', 0.0)
    # saddle: tall squared cantle front and back
    add(RoundBox(v3(0, by + 0.34, 0.07), (0.16, 0.10, 0.025), 0.02), 'leather', 0.0)
    add(RoundBox(v3(0, by + 0.34, -0.20), (0.16, 0.12, 0.025), 0.02), 'leather', 0.0)


def build(P):
    parts, add = new_parts()
    O.horse(P, add)
    barding(add, P)
    hparts = list(parts)
    parts.clear()
    body(P, add, C)
    nk, ch, pel = P['neck'], P['chest'], P['pelvis']
    barbute(P, add, 'helm', trim='helm_dk', size=0.95)
    H, R, h = P['head'], head_R(P), P['height']
    # visor slit and breath holes, painted dark; steel-blue horsehair crest
    add(RoundBox(H + R @ v3(0, 0.012, 0.088) * h, (0.052, 0.008, 0.010), 0.004, R), 'ink', 0.0)
    add(RoundBox(H + R @ v3(0, -0.02, 0.090) * h, (0.006, 0.05, 0.008), 0.003, R), 'ink', 0.0)
    cr = H + R @ v3(0, 0.12, -0.01) * h
    add(RoundBox(cr, (0.012, 0.016, 0.075), 0.006, R), 'brass', 0.0)
    sw = np.sin(P['tell'] * 6.283) * 0.02
    add(Capsule(cr + v3(0, 0.0, 0.07), cr + v3(0, 0.04, -0.12 + sw), 0.026, 0.020), 'crest', 0.02)
    add(Capsule(cr + v3(0, 0.0, 0.0), cr + v3(0, 0.03, -0.24 + sw), 0.020, 0.008), 'crest', 0.02)
    square_pauldrons(P, add, 'plate', size=1.2, trim='steelcloth_dk')
    add(Cylinder(nk + v3(0, -0.04, -0.005), nk + v3(0, 0.03, -0.012), 0.082, 0.01), 'plate', 0.0)
    # steel-blue surcoat skirt over the saddle, salt-bordered
    add(RoundBox(pel + v3(0, -0.08, 0.10), (0.15, 0.13, 0.012), 0.008, rot_x(0.35)), 'cloth_h', 0.0)
    add(RoundBox(pel + v3(0, -0.20, 0.13), (0.15, 0.012, 0.012), 0.006, rot_x(0.35)), 'trim', 0.0)
    # breastplate ridge, tabard-bib, brass buckle
    add(Ellipsoid(ch + v3(0, 0.03, 0.065), (0.16, 0.17, 0.065)), 'plate', 0.04)
    add(RoundBox(ch + v3(0, -0.05, 0.115), (0.040, 0.15, 0.006), 0.004), 'salt', 0.0)
    for s in ('r', 'l'):
        el, wr = P['el_' + s], P['wr_' + s]
        add(Capsule(el + (wr - el) * 0.70, wr - (wr - el) * 0.02, 0.052), 'plate')
        add(Sphere(el, 0.052), 'plate', 0.01)
    # long couched lance with vamplate and pennant
    r = held(P, add, 'r', 'pike', shaft='wood', head='steel', below=0.75, above=P.get('lance', 1.22))
    if r is not None:
        butt, tip = r
        d = norm(tip - butt)
        g = hand_pos(P, 'r')
        add(Capsule(butt, tip - d * 0.15, 0.062, 0.040), 'lance', 0.0)          # fat shaft, reads at 1x
        add(Capsule(tip - d * 0.40, tip, 0.050, 0.004), 'steel', 0.0)
        add(Cylinder(g + d * 0.10, g + d * 0.17, 0.050, 0.01), 'brass', 0.0)      # vamplate
        add(Cylinder(g + d * 0.17, g + d * 0.30, 0.050, 0.01), 'brass', 0.0)
        add(Cylinder(tip - d * 0.40, tip - d * 0.36, 0.026, 0.004), 'brass', 0.0)
        pennant(add, tip - d * 0.30, length=0.62, height=0.24, sway=np.sin(P['tell'] * 6.28),
                direction=norm(v3(0.35, -0.1, -1.0) - d * 0.3), phase=P['tell'] * 6.28, swallow=True)
    rparts = list(parts)
    parts.clear()
    R_ = rot_x(-P['hpitch'])
    hp = transform_parts(hparts, R=R_, t=(0, P['hbob'], P.get('zs', ZS)), pivot=(0, 0.9, -0.3))
    rp = transform_parts(rparts, R=R_, t=(0, P['hbob'], P.get('zs', ZS)), pivot=(0, 0.9, -0.3))
    parts.extend(hp + rp)
    mats = base_mats(P)

    def scales(p, n):
        # staggered rows of scale plates, steel-blue with salt-white lips
        y = p[:, 1] * 24
        row = np.floor(y)
        x = (p[:, 0] + p[:, 2] * 0.6) * 24 + 0.5 * (row % 2)
        fx = x - np.floor(x)
        fy = y - row
        a = np.array(STEEL)[None, :].repeat(len(p), 0) * 0.78 * (0.9 + 0.22 * ((np.floor(x) + row) % 3 == 0)[:, None])
        lip = (fy < 0.20) | (fx < 0.10)
        a[lip] = np.array(STEEL_LT) * 1.05
        a[fy > 0.86] = np.array(INK) * 1.2
        return salt_seams(a, p, 0.28, 26, 0.0, 0.0)
    mats.update({
        'lance': Material(lambda p, n: np.where(((np.floor(p[:, 1] * 9) % 2) == 0)[:, None], np.array(SALT_HI), np.array(_hex('#4a3626')))[:len(p)] * 1.0,
                          spec=0.2, brush=0.04),
        'plate': salted_metal(_hex('#363d47'), amount=0.3, gloss=34),
        'helm': salted_metal(_hex('#a3adb8'), amount=0.3),
        'helm_dk': salted_metal(_hex('#6d7783'), amount=0.3),
        'scales': Material(scales, spec=0.35, gloss=26, metal=0.5, brush=0.05),
        'cloth': salted(STEEL, 0.3, ground=0.4, gamt=0.7),
        'trim': salted(SALT, 0.1, ground=0.0, gamt=0.0, spec=0.05),
        'cloth_h': salted(STEEL_DK, 0.35, ground=0.5, gamt=0.7, spec=0.04, brush=0.07),
        'crest': Material(_hex('#3f6a94'), spec=0.15, brush=0.12),
        'steelcloth_dk': salted(STEEL_DK, 0.3),
        'gaunt': salted_metal(_hex('#262b33'), amount=0.3),
        'coat_h': salted(_hex('#b3a68e'), 0.3, ground=0.55, gamt=1.0, vary=0.12, spec=0.12, gloss=16),
        'leg_h': salted(_hex('#8a7d68'), 0.5, ground=0.6, gamt=1.2),
        'mane': Material(_hex('#3a3029'), spec=0.15, brush=0.12),
        'hoof': Material(_hex('#2b2622'), spec=0.2),
        'faceplate': salted_metal(_hex('#8c939c'), amount=0.4),
        'skin': skin_mat(P, skin=W['skin_mid'], hair=_hex('#3b2a20')),
    })
    return finish(P, FACTION, parts, mats)


ROWS = O.ROWS


def frames():
    # reuse the outrider's riding rows with this unit's pose and a lowered, heavier lance
    keep = _O_NEUTRAL
    O.neutral_pose = neutral_pose
    try:
        f = O.frames()
    finally:
        O.neutral_pose = keep
    for P, lo in f['attack']:
        P['lance'] = 0.95
        P['zs'] = ZS - 0.22
    for P, lo in f['cast']:
        P['lance'] = 1.05
    return f

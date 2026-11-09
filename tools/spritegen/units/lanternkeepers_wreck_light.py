"""Wreck-Light (Lanternkeepers trickster). The keepers' oldest secret: a hunched figure in a black oilskin
cloak and deep hood, face lost in shadow, holding a long crook out over the water with a FALSE lamp hanging from
it, burning the wrong cold sea-green. Defining detail: the crook with the pale lure lamp swinging far out in front,
razor oysters bristling at his feet and a coil of wrecker's rope at the hip. Darker and ragged beside the line."""
import numpy as np
from _lanternkeepers_w2 import *

UNIT_ID = 'lanternkeepers_wreck_light'
FACTION = 'lanternkeepers'
LOOK = LOOKS[FACTION]

C = Costume(top='cloak_dk', sleeve='cloak_dk', legs='slate', boot='boot', hand='glove', skirt='robe',
            skirt_mat='cloak', hem=0.10, flare=1.15, head='hood', head_mat='cloak_dk', belt='rope', girth=1.08)


def neutral_pose():
    P = base_pose(height=1.02, build=1.0)
    h = P['height']
    rig.lean(P, fwd=np.radians(9))
    P['head_pitch'] = np.radians(10)
    P['head_yaw'] = np.radians(-22)
    # crook arm: out in front, high; free hand low and curled at the cloak
    rig.place_arm(P, 'r', v3(-0.40, 1.02, 0.10), (-1, -0.5, -0.2), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(-0.10, 1.0, 0.12))
    rig.place_arm(P, 'l', v3(0.16, 0.98, 0.16), (1, -0.4, -0.5), l1=0.27 * h, l2=0.26 * h)
    P['lamp_swing'] = 0.0
    return P


def crook(add, lights, P):
    d = P['item_r']
    if d is None:
        return
    d = norm(d)
    g = hand_pos(P, 'r')
    butt, top = g - d * 0.95, g + d * 0.78
    add(Capsule(butt, top, 0.019, 0.014), 'driftwood', 0.0)
    # crook: shaft curls over and down
    fwd = norm(v3(-1.0, 0, -0.35))
    p1 = top + fwd * 0.12 + d * 0.07
    p2 = top + fwd * 0.30 + d * 0.03
    p3 = top + fwd * 0.40 - d * 0.05
    add(Capsule(top, p1, 0.014, 0.012), 'driftwood', 0.0)
    add(Capsule(p1, p2, 0.012, 0.011), 'driftwood', 0.0)
    add(Capsule(p2, p3, 0.011, 0.010), 'driftwood', 0.0)
    # chain and lure lamp
    sw = P['lamp_swing']
    ch_end = p3 + v3(0.04 * sw, -0.14, 0.0)
    add(Capsule(p3, ch_end, 0.005, 0.005), 'darkiron', 0.0)
    lc = ch_end + v3(0.03 * sw, -0.10, 0.0)
    false_lamp(add, lights, P, lc, size=1.9, swing=0.25 * sw)
    # tarred ribbon streamers on the crook
    add(Capsule(top - d * 0.18, top - d * 0.18 + v3(0.05, -0.22, -0.06 + 0.04 * sw), 0.012, 0.004), 'cloak', 0.0)


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    h, b = P['height'], P['build']
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    # tattered round cape over the shoulders, ragged strips hanging
    add(capelet_shell(P, depth=0.20, width=0.20, sq=2.2), 'cloak', 0.0)
    for i in range(7):
        a = -1.1 + i * 0.37
        top = ch + v3(np.sin(a) * 0.19 * b, -0.14, np.cos(a) * -0.11 - 0.02)
        ln = 0.18 + 0.07 * ((i * 5) % 3)
        add(Capsule(top, top + v3(0.02 * np.sin(a) + 0.015 * P['skirt_sway'], -ln, -0.04), 0.022, 0.006), 'cloak_dk', 0.0)
    # rope coil at the hip
    rc = pel + v3(0.17 * b, -0.04, 0.02)
    for k in range(3):
        add(Torus(rc + v3(0, 0.014 * k, 0), v3(1, 0, 0.1), 0.065, 0.011), 'rope', 0.0)
    # hooded face is in shadow: dark void under the brow and a pale cold glint of the lamp on the cheek
    H, R = P['head'], head_R(P)
    # razor oysters at his feet (on the lit side)
    razor_oysters(add, v3(0.34, 0.0, 0.30), n=6, seed=2)
    razor_oysters(add, v3(-0.35, 0.0, -0.12), n=4, seed=9, scale=0.8)
    crook(add, lights, P)
    mats = keeper_mats(P, skin=_hex('#a98062'), hair=_hex('#2a2422'))
    mats['cloak'] = Material(oilskin_albedo(_hex('#3c454b'), wear=0.12), spec=0.28, gloss=22, brush=0.08)
    mats['cloak_dk'] = Material(oilskin_albedo(_hex('#272e33'), wear=0.10), spec=0.24, gloss=20, brush=0.08)
    mats['driftwood'] = Material(noisy(_hex('#6b5e4e'), 0.14, 14.0), spec=0.1, brush=0.1)
    mats['rope'] = Material(noisy(_hex('#8f8366'), 0.16, 60.0), spec=0.02, brush=0.1)
    mats['oyster'] = Material(noisy(_hex('#5f686a'), 0.2, 60.0), spec=0.25, gloss=24, brush=0.06)
    mats['oyster_edge'] = Material(_hex('#dfe6e4'), spec=0.4, gloss=30, brush=0.04)
    g = P['glow'] * (1 + 0.8 * P['cast_glow'])
    mats['falselamp'] = Material(FALSE_LIGHT, spec=0.3, gloss=30, emissive=tuple(np.array(FALSE_LIGHT) * g), rim=0.0)
    return finish(P, FACTION, parts, mats, lights=lights)


def _post(fr):
    for i, (P, o) in enumerate(fr['idle']):
        P['lamp_swing'] = [0.0, 0.5, 0.0, -0.5][i]
    for i, (P, o) in enumerate(fr['move']):
        P['lamp_swing'] = [0.5, 0.0, -0.5, 0.0][i]
    for i, (P, o) in enumerate(fr['attack']):
        # swing the lamp out and hold it: the lure
        P['item_r'] = norm(v3([-0.1, -0.1, -0.35, -0.25][i], [1.0, 1.0, 0.8, 0.9][i], [0.15, 0.1, 0.55, 0.4][i]))
        P['lamp_swing'] = [-0.4, -1.0, 1.0, 0.4][i]
        P['cast_glow'] = [0.2, 0.5, 1.0, 0.3][i]
    for i, (P, o) in enumerate(fr['cast']):
        P['item_r'] = norm(v3(-0.1, 1.0, [0.2, 0.0, 0.3][i]))
        P['lamp_swing'] = [0.3, -0.6, 0.6][i]
    for i, (P, o) in enumerate(fr['death']):
        if P['item_r'] is not None and i > 0:
            P['item_r'] = norm(v3(-0.6 * [0, 0.5, 0.8, 1][i], [1, 0.7, 0.5, 0.4][i], 0.2))
    return fr


ROWS, frames = keeper_rows(neutral_pose, attack_style='cast', weapon_side='l', cast_side='l', post=_post)

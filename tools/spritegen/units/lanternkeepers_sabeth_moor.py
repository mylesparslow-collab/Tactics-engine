"""Archivist Sabeth Moor (Lanternkeepers hero). Keeper of the Archive, who has read the true logbooks of the Long
Ebb. Tall and spare in a long ink-slate robe under a sea-grey archivist's mantle, white hair in a tight bun,
wire spectacles. Defining detail: a leaning stack of logbooks with ribbon bookmarks hugged on her left arm, a
ledger satchel at the hip with a ring of archive keys, and a brass-hooded reading lamp on a gooseneck rod arching
over the books so its light falls on the page. On the cast the top book falls open and the page-light flares."""
import numpy as np
from _lanternkeepers_w2 import *

UNIT_ID = 'lanternkeepers_sabeth_moor'
FACTION = 'lanternkeepers'
LOOK = LOOKS[FACTION]

C = Costume(top='robe_top', sleeve='robe_top', legs='slate', boot='boot', hand='skin', skirt='robe',
            skirt_mat='robe', hem=0.04, flare=0.78, head='hair', hair='hair', hair_style='bob', belt='ribbonbelt',
            girth=0.95)


def neutral_pose():
    P = base_pose(height=1.06, build=0.90)
    h = P['height']
    P['head_pitch'] = np.radians(6)
    P['head_yaw'] = np.radians(-16)
    # left forearm carries the book stack at the chest; right hand holds the lamp rod
    rig.place_arm(P, 'l', v3(0.16, 1.03, 0.30), (1, -0.6, -0.2), l1=0.27 * h, l2=0.26 * h)
    rig.place_arm(P, 'r', v3(-0.30, 1.13, 0.12), (-1, -0.4, -0.5), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(0.03, 1.0, -0.02))
    P['page_open'] = 0.0
    P['lamp_sw'] = 0.0
    return P


def lamp_rod(add, lights, P):
    d = P['item_r']
    if d is None:
        return
    d = norm(d)
    g = hand_pos(P, 'r')
    butt = g - d * 0.95
    top = g + d * 0.62
    add(Capsule(butt, top, 0.017, 0.014), 'wood', 0.0)
    add(Cylinder(g + d * 0.02, g + d * 0.06, 0.024, 0.005), 'brass', 0.0)
    add(Sphere(butt, 0.02), 'brass', 0.0)
    # gooseneck: arches up, over and down toward the books
    sw = P['lamp_sw']
    tgt = hand_pos(P, 'l') + v3(0.02 * sw, 0.66, 0.0)       # lamp hangs above the books
    pts = [top, top + v3(0.02, 0.12, 0.0), (top + tgt) / 2 + v3(0.0, 0.17, 0.02), tgt + v3(-0.03, 0.17, 0.0), tgt + v3(0, 0.09, 0)]
    for a, b in zip(pts[:-1], pts[1:]):
        add(Capsule(a, b, 0.012, 0.010), 'brass', 0.0)
    dome_lamp(add, lights, P, tgt + v3(0, -0.02, 0.0), size=1.0, light=1.3)


def build(P):
    parts, add = new_parts()
    lights = []
    body(P, add, C)
    h, b = P['height'], P['build']
    pel, ch, nk = P['pelvis'], P['chest'], P['neck']
    # archivist's mantle: round sea-grey shoulder cape with a darker collar band
    add(capelet_shell(P, depth=0.20, width=0.17, sq=3.0), 'mantle', 0.0)
    add(Torus(nk + v3(0, -0.035, 0.0), v3(0, 1, 0.1), 0.070, 0.020), 'mantle_dk', 0.01)
    # hair bun, spectacles
    H, R = P['head'], head_R(P)
    add(Sphere(H + R @ v3(0, 0.045, -0.095) * h, 0.050), 'hair', 0.02)
    add(Capsule(H + R @ v3(-0.07, 0.02, -0.06) * h, H + R @ v3(0, 0.05, -0.095) * h, 0.012), 'hair', 0.0)
    spectacles(add, P)
    # satchel at the right hip (camera side): flap, strap, ledger corners poking out
    sc = pel + v3(-0.19 * b, -0.12, 0.0)
    add(RoundBox(sc, (0.05, 0.075, 0.095), 0.012, rot_z(0.08)), 'leather', 0.0)
    add(RoundBox(sc + v3(-0.01, 0.07, 0.0), (0.048, 0.01, 0.100), 0.008, rot_z(0.08)), 'leather_dk', 0.0)
    add(Capsule(sc + v3(0.02, 0.07, 0.0), ch + v3(0.12, 0.10, -0.04), 0.011, 0.011), 'leather_dk', 0.0)
    add(RoundBox(sc + v3(-0.04, 0.10, -0.02), (0.012, 0.075, 0.07), 0.005, rot_z(0.2)), 'book_a', 0.0)
    add(RoundBox(sc + v3(-0.04, 0.095, 0.045), (0.012, 0.070, 0.06), 0.005, rot_z(0.15)), 'book_c', 0.0)
    # key ring on the belt with three long archive keys
    kc = pel + v3(0.17 * b, 0.0, 0.03)
    add(Torus(kc, v3(1, 0, 0), 0.020, 0.004), 'brass', 0.0)
    for k in range(3):
        a = kc + v3(0.01, -0.02, 0.0)
        e = a + v3(0.012 * (k - 1) + 0.01 * P['skirt_sway'], -0.10 - 0.02 * k, 0.012 * (k - 1))
        add(Capsule(a, e, 0.0045, 0.004), 'brass', 0.0)
        add(RoundBox(e, (0.012, 0.010, 0.004), 0.003), 'brass', 0.0)
    # the logbook stack, hugged on the left forearm; top book opens on the cast
    gl = hand_pos(P, 'l')
    top_c = book_stack(add, gl + v3(-0.01, 0.015, 0.01), yaw=0.0, n=4, seed=3, size=0.95)
    op = P['page_open']
    if op > 0.01:
        # a book falls open on the stack: two cover leaves, pages fan up, page-light
        for sx in (-1, 1):
            add(RoundBox(top_c + v3(sx * 0.05, 0.01 + 0.03 * op, 0.0), (0.05, 0.004, 0.065), 0.003, rot_z(sx * 0.35 * op)), 'book_b', 0.0)
            add(RoundBox(top_c + v3(sx * 0.045, 0.02 + 0.03 * op, 0.0), (0.045, 0.003, 0.06), 0.003, rot_z(sx * 0.25 * op)), 'wax', 0.0)
        add(Ellipsoid(top_c + v3(0, 0.04, 0.0), (0.05 * op, 0.03 * op, 0.05 * op)), 'flash', 0.0)
        light_at(lights, P, top_c + v3(0, 0.07, 0.04), 2.4 * op, 0.22, color=_hex('#fff1c8'))
    # rolled chart under the right arm... as a quill-tube at the belt (clear vertical read)
    lamp_rod(add, lights, P)
    mats = keeper_mats(P, hair=_hex('#aeab9f'), skin=_hex('#cfa584'))
    mats['robe'] = Material(oilskin_albedo(_hex('#34414b'), wear=0.08), spec=0.12, gloss=14, brush=0.08)
    mats['robe_top'] = Material(noisy(_hex('#3e4c57'), 0.10), spec=0.08, gloss=12, brush=0.08)
    mats['mantle'] = Material(noisy(_hex('#8e9ba3'), 0.10), spec=0.06, gloss=10, brush=0.09)
    mats['mantle_dk'] = Material(noisy(_hex('#59636b'), 0.1), spec=0.05, brush=0.09)
    mats['ribbonbelt'] = Material(noisy(_hex('#a3832f'), 0.1, 40.0), spec=0.1, brush=0.06)
    mats['leather'] = Material(noisy(_hex('#6a4e38'), 0.10), spec=0.2, gloss=20, brush=0.06)
    mats['leather_dk'] = Material(noisy(_hex('#42332a'), 0.10), spec=0.2, gloss=20, brush=0.06)
    mats['book_a'] = Material(noisy(_hex('#4d6657'), 0.08, 40.0), spec=0.08, brush=0.07)
    mats['book_b'] = Material(noisy(_hex('#7c4a3f'), 0.08, 40.0), spec=0.08, brush=0.07)
    mats['book_c'] = Material(noisy(_hex('#3b4f6a'), 0.08, 40.0), spec=0.08, brush=0.07)
    mats['book_d'] = Material(noisy(_hex('#8a7550'), 0.08, 40.0), spec=0.08, brush=0.07)
    mats['ribbon'] = Material(_hex('#b34a3a'), spec=0.1, brush=0.04)
    mats['lens'] = Material(_hex('#dfe9ea'), spec=1.0, gloss=60, emissive=tuple(np.array(LENS) * 0.18), rim=0.4, brush=0.0)
    return finish(P, FACTION, parts, mats, lights=lights)


def _post(fr):
    for i, (P, o) in enumerate(fr['idle']):
        P['lamp_sw'] = [0, 0.4, 0, -0.4][i]
    for i, (P, o) in enumerate(fr['attack']):
        # lamp rod swept forward and raised: the Recorded Truth flare
        P['item_r'] = norm(v3([0.0, -0.05, -0.15, -0.1][i], [1.0, 0.9, 0.55, 0.8][i], [0.0, 0.3, 0.8, 0.4][i]))
        P['page_open'] = [0, 0.4, 1.0, 0.5][i]
        P['cast_glow'] = [0.2, 0.5, 1.0, 0.3][i]
    for i, (P, o) in enumerate(fr['cast']):
        rig.place_arm(P, 'l', v3(0.14, [1.10, 1.20, 1.14][i], 0.32), (1, -0.6, -0.2), l1=0.27 * P['height'], l2=0.26 * P['height'])
        P['page_open'] = [0.5, 1.0, 0.7][i]
        P['lamp_sw'] = [0, 0.5, -0.3][i]
    for i, (P, o) in enumerate(fr['death']):
        P['page_open'] = 0.0
    return fr


ROWS, frames = keeper_rows(neutral_pose, attack_style='cast', weapon_side='r', cast_side='l', post=_post, pole='r')

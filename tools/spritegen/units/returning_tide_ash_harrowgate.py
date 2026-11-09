"""Deacon Ash Harrowgate (Returning Tide hero). Dunnock's enforcer, who wrings the doubters first. Tall,
square-shouldered and stern in a black soaked cassock with a drowned-green stole edged in bleached linen,
a bandolier of iron flensing hooks across the chest, S-hooks at the cord belt, a barnacle-mail pauldron.
The right fist holds the double-hooked wring-pole; the left twists a sodden linen cloth that pours brine.
Defining detail: the wrung linen cloth streaming water, and the bandolier of hooks.
"""
from _returning_tide_w2 import *
from render import Camera

UNIT_ID = 'returning_tide_ash_harrowgate'
CAMERA = Camera(ppm=50)

C = Costume(top='cassock', sleeve='cassock', legs='cassock', boot='boot', hand='skin', skin='skin',
            skirt=None, head='bald', belt=None, boots_tall=True, girth=1.18)
H_ = 1.10


def neutral_pose():
    P = base_pose(height=H_, build=1.14)
    h = H_
    rig.place_leg(P, 'l', (0.20, 0.085, 0.07), l1=0.43 * h, l2=0.42 * h)
    rig.place_leg(P, 'r', (-0.20, 0.085, -0.05), l1=0.43 * h, l2=0.42 * h)
    rig.lean(P, fwd=np.radians(-1))
    P['head_pitch'] = np.radians(-5)
    P['head_yaw'] = np.radians(-6)
    rig.place_arm(P, 'r', v3(-0.33, 1.02, 0.18), (-1, -0.4, -0.4), l1=0.27 * h, l2=0.26 * h)
    P['item_r'] = norm(v3(0.02, 1.0, 0.04))
    rig.place_arm(P, 'l', v3(0.22, 1.08, 0.34), (1, -0.6, -0.3), l1=0.27 * h, l2=0.26 * h)
    return P


def cloth(P, add, g, phase, wring=0.0, length=0.40):
    """Sodden linen twisted in the left fist, hanging in a heavy rope that sways and pours."""
    pts = []
    a = g + v3(0, -0.03, 0)
    n = 6
    for k in range(n + 1):
        t = k / n
        sway = 0.035 * np.sin(phase * 6.28 + t * 3.0) * t + P['skirt_sway'] * 0.03 * t
        pts.append(a + v3(sway + 0.05 * t, -length * t * (1 + 0.12 * wring), 0.07 * t * (1 - 0.5 * wring)))
    for k in range(n):
        r0 = 0.052 * (1 - 0.30 * k / n)
        add(Capsule(pts[k], pts[k + 1], r0, r0 * 0.88), 'cloth', 0.02)
        # twist ridges
        mid = (pts[k] + pts[k + 1]) / 2
        c = norm(np.cross(pts[k + 1] - pts[k], v3(0, 0, 1)))
        add(Capsule(mid - c * 0.03 + v3(0, 0.012, 0), mid + c * 0.03 - v3(0, 0.012, 0), 0.010), 'cloth', 0.0)
    add(Torus(a + v3(0, 0.02, 0), v3(0, 1, 0), 0.045, 0.014), 'cloth', 0.0)     # knuckle wrap
    tip = pts[-1]
    add(Ellipsoid(tip + v3(0, -0.03, 0), (0.026, 0.045, 0.026)), 'cloth', 0.02)
    return tip


def build(P):
    parts, add = new_parts()
    h, b = P['height'], P['build']
    body(P, add, C)
    R = frame_for(P)
    nk, ch, pel, H = P['neck'], P['chest'], P['pelvis'], P['head']
    Rh = head_R(P)
    tl, cg = P['tell'], P['cast_glow']
    # soaked cassock, high collar, drowned-green stole
    add(ragged_robe(P, hem=0.05, flare=0.85, top=1.04, rag=0.45, seed=1.2, droop=0.02, girth=1.2), 'cassock', 0.0)
    add(Cylinder(nk - R[:, 1] * 0.03, nk + R[:, 1] * 0.06, 0.082, 0.012), 'cassock', 0.0)
    add(Torus(nk + R[:, 1] * 0.03, R[:, 1], 0.075, 0.014), 'linen', 0.0)             # bleached bands
    for sx in (-1, 1):
        a = nk + R @ v3(sx * 0.07, -0.02, 0.08)
        bq = pel + R @ v3(sx * 0.07, -0.30 * h, 0.17)
        add(RoundBox((a + bq) / 2, (0.045, np.linalg.norm(bq - a) / 2, 0.008), 0.004, basis_from(norm(a - bq), (0, 0, 1))), 'stole', 0.0)
        add(RoundBox((a + bq) / 2 + v3(sx * 0.03, 0, 0.004), (0.008, np.linalg.norm(bq - a) / 2, 0.009), 0.003, basis_from(norm(a - bq), (0, 0, 1))), 'linen', 0.0)
        add(Sphere(bq - v3(0, 0.0, 0), 0.018), 'gold', 0.0)
    # the stole hangs forward over the cord belt, ending in a linen-tasselled hem
    # cord belt with hanging S-hooks and a knotted tail
    knotted_cord(add, P, y_off=0.07, mat='cord', girth=1.18)
    for k, sx in enumerate((-0.15, 0.13, 0.04)):
        a = pel + v3(sx * b, 0.05, 0.12)
        add(Capsule(a, a + v3(0, -0.06, 0.012), 0.006), 'iron', 0.0)
        add(Torus(a + v3(0, -0.095, 0.015), v3(1, 0, 0), 0.028, 0.007), 'iron', 0.0)
        add(Torus(a + v3(0, -0.145, 0.015), v3(0, 0, 1), 0.026, 0.007), 'iron', 0.0)
    # bandolier of flensing hooks across the chest
    sa = P['sh_r'] + v3(0.02, 0.01, 0.02)
    sbq = pel + R @ v3(0.14 * b, 0.06, 0.12)
    add(Capsule(sa + v3(0, 0, 0.03), sbq, 0.016), 'strap', 0.01)
    add(Capsule(sa + v3(0, 0, -0.07), sbq + v3(0, 0, -0.18), 0.016), 'strap', 0.01)
    for k in range(6):
        t = (k + 0.5) / 6
        q = sa + (sbq - sa) * t + v3(0, 0, 0.03 + 0.08 * t) + R @ v3(0, 0, 0.055 - 0.0 * t)
        add(Capsule(q, q + v3(0, -0.07, 0.015), 0.007), 'iron', 0.0)
        add(Torus(q + v3(0.008, -0.085, 0.02), v3(1, 0.3, 0), 0.020, 0.0065), 'iron', 0.0)
    # barnacle-mail pauldron on the left shoulder, plain wet wool on the right
    sl = P['sh_l']
    for j, (rad, dy) in enumerate(((0.13, 0.06), (0.15, 0.02), (0.165, -0.025))):
        add(Ellipsoid(sl + v3(0.03, dy, 0), (rad, 0.040, rad * 0.85), basis_from(norm(v3(0.5, 1, 0)), (0, 0, 1))), 'mail', 0.01)
    barnacles(add, sl + v3(0.05, 0.05, 0.02), v3(0.5, 1, 0.2), n=10, spread=0.09, size=0.018, seed=11)
    add(Ellipsoid(P['sh_r'] + v3(-0.02, 0.05, 0), (0.12, 0.045, 0.11), basis_from(norm(v3(-0.5, 1, 0)), (0, 0, 1))), 'cassock', 0.02)
    # cuffs
    for s in ('r', 'l'):
        el, wr = P['el_' + s], P['wr_' + s]
        add(Capsule(el + (wr - el) * 0.72, wr, 0.052), 'linen', 0.0)
    # head: shaved skull, stern; wet cowl rolled on the shoulders
    hood_down(P, add, 'cassock', size=1.05)
    # the wring-pole: dark pole, a double iron hook at the head
    bt = held(P, add, 'r', 'staff', shaft='pole', head='iron', below=1.0, above=0.8)
    if bt:
        butt, tip = bt
        d = norm(tip - butt)
        sd = norm(np.cross(d, v3(0, 0, 1)))
        add(Torus(tip + sd * 0.07, np.cross(d, sd), 0.065, 0.014), 'iron', 0.0)
        add(Torus(tip - sd * 0.07 - d * 0.05, np.cross(d, sd), 0.058, 0.013), 'iron', 0.0)
        add(Capsule(tip, tip + d * 0.09, 0.014, 0.004), 'iron', 0.0)
        add(Cylinder(tip - d * 0.18, tip - d * 0.14, 0.024, 0.006), 'iron', 0.0)
        drips(P, add, [tip + sd * 0.12 + v3(0, -0.08, 0)], fall=0.4)
    # the wrung cloth
    gl = hand_pos(P, 'l')
    wring = 0.5 + 0.5 * cg
    tipc = cloth(P, add, gl, tl, wring=wring)
    stream(add, tipc + v3(0, -0.06, 0), ground_y=0.0, phase=tl, r=0.012 * (1 + 1.5 * cg), out=(0.03, 0.04), n=6)
    drips(P, add, [pel + v3(0.22, -0.9, 0.06), pel + v3(-0.2, -0.92, -0.02), P['sh_l'] + v3(0.05, -0.12, 0.05)], fall=0.5)
    if cg > 0:
        for k in range(8):
            a = k * 0.78 + tl * 6.28
            add(Sphere(gl + v3(np.cos(a) * 0.12 * cg, 0.1 + 0.25 * ((k / 8 + tl) % 1.0) * cg, np.sin(a) * 0.12 * cg), 0.018), 'drip', 0.0)
    if P['fx'] > 0:
        add(Torus(v3(0, 0.03, 0.6), v3(0, 1, 0), 0.15 + 0.35 * P['fx'], 0.018), 'drip', 0.0)
    puddle(P, add, r=0.40, seed=4.0, grow=1.0 + 0.2 * cg)
    ripples(P, add, n=2, r0=0.34)
    mats = {
        'cassock': wet_cloth(_hex('#1d2824'), wet=0.9, low_dark=0.22, streak=0.12),
        'stole': wet_cloth(_hex('#3f7a5c'), wet=0.8, low_dark=0.15),
        'linen': wet_cloth(LINEN, wet=0.6, low_dark=0.2),
        'cloth': wet_cloth(_hex('#d3d5c6'), wet=0.9, low_dark=0.1, streak=0.2, top=1.2),
        'boot': Material(_hex('#1a1d1c'), spec=0.5, gloss=34, brush=0.06),
        'iron': Material(_hex('#4a4e50'), spec=0.7, gloss=34, metal=0.6, brush=0.06),
        'gold': Material(GOLD, spec=0.8, gloss=36, metal=0.8, brush=0.05),
        'strap': Material(_hex('#2d2a26'), spec=0.3, gloss=24, brush=0.06),
        'pole': Material(_hex('#2f2c28'), spec=0.4, gloss=26, brush=0.06),
        'mail': Material(lambda p, n: np.where((fbm(p, 40, 2) > 0.5)[:, None], np.array(_hex('#9c9d90'))[None, :], np.array(_hex('#5d6862'))[None, :]) * (0.85 + 0.2 * fbm(p, 14, 2)[:, None]), spec=0.35, gloss=24, metal=0.3, brush=0.08),
        'skin': wet_skin_h(P),
    }
    return tide_finish(P, parts, mats, add, pool_r=0.62)


def wet_skin_h(P):
    return Material(tide_face(P, _hex('#b3a898'), _hex('#35383a'), eyes=_hex('#1c2122'), lips=_hex('#6a5650'),
                              beard=_hex('#6d7270'), sunken=0.6), spec=0.30, gloss=26, sss=0.4, brush=0.03)


ROWS, _fr = tide_rows(neutral_pose, attack_style='swing', weapon_side='r', cast_side='l', sink=0.35)


def frames():
    fr = _fr()
    h = H_
    for i, (P, o) in enumerate(fr['cast']):
        P['item_l'] = None
        g = [v3(0.24, 1.2, 0.36), v3(0.20, 1.62, 0.34), v3(0.22, 1.34, 0.42)][i]
        rig.place_arm(P, 'l', g, (1, -0.6, -0.3), l1=0.27 * h, l2=0.26 * h)
    return fr

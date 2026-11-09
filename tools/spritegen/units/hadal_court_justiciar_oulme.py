"""Justiciar Oulme, the Second Bell (Hadal Court hero). The Court's judge: a tall, formal figure sealed in
layered brine-armour robes whose lames toll like a bell when he moves, a high flared judge's collar, a
domed helm with one vertical slit of teal and a small bell at each temple. In both arms he carries the
pressure-casket: the indictment of the surface, iron-banded, barnacled, a teal port glowing, strips of
pale indictment hanging from its seals. Defining detail: the casket and its trailing indictment strips.
"""
from _hadal_court_w2 import *

UNIT_ID = 'hadal_court_justiciar_oulme'
CAMERA = Camera(ppm=44)

C = Costume(top='plate', sleeve='plate', legs='hide', boot='iron', hand='iron', skin='hide', skirt='coat',
            skirt_mat='plate', hem=0.12, flare=1.1, head='none', belt='chain', boots_tall=False, girth=1.3)
H_ = 1.4


def carry(P, fwd=0.48, down=-0.06, tilt=0.0):
    """Casket centre cradled in front of the torso; both hands on its flanks."""
    R = frame_for(P)
    c = P['chest'] + R @ v3(0, down, fwd)
    c[1] = max(c[1], 0.22)
    P['cask'] = c
    P['cask_tilt'] = tilt
    h = H_
    rig.place_arm(P, 'r', c + v3(-0.19, -0.02, 0.02), (-1, -0.6, -0.3), l1=0.27 * h, l2=0.26 * h)
    rig.place_arm(P, 'l', c + v3(0.19, -0.02, 0.02), (1, -0.6, -0.3), l1=0.27 * h, l2=0.26 * h)


def neutral_pose():
    P = hpose(H_, 1.32)
    rig.lean(P, fwd=np.radians(3))
    P['head_pitch'] = np.radians(2)
    rig.shift(P, ('head',), v3(0, 0.09, 0.03))
    carry(P)
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    h, b = P['height'], P['build']
    R = frame_for(P)
    nk, ch, pel = P['neck'], P['chest'], P['pelvis']
    H = P['head']
    Rh = rot_y(P['head_yaw']) @ rot_x(-P['head_pitch'])
    tl = P['tell']
    # brine-armour robe: a long fluted bell of overlapping lames
    add(bell_hull(nk + R[:, 1] * 0.0, 0.36 * h, 0.17, 0.25, R=R, power=0.9, sz=0.80, lip=0.03, ribs=0.03, ribs_n=14), 'lames', 0.03)
    # hem band with hanging teal-seeping tassels of chain
    # broad layered spaulders (flat lames, not bells)
    for s in ('r', 'l'):
        sx = -1 if s == 'r' else 1
        sh = P['sh_' + s]
        Rs = basis_from(norm(v3(sx * 0.7, 1, 0)), (0, 0, 1))
        for j, (rad, dy) in enumerate(((0.20, 0.08), (0.24, 0.04), (0.27, -0.01))):
            add(Ellipsoid(sh + v3(sx * 0.02, dy, 0), (rad, 0.035, rad * 0.8), Rs), 'lames', 0.01)
        el, wr = P['el_' + s], P['wr_' + s]
        d = norm(wr - el)
        add(Capsule(el, wr, 0.072, 0.062), 'iron', 0.02)          # vambrace
        add(Torus(el + d * 0.02, d, 0.075, 0.016), 'bellg', 0.0)
        add(Sphere(wr + d * 0.06, 0.06), 'iron', 0.01)
    # judge's collar: a tall flared gorget
    add(bell_hull(nk + R[:, 1] * 0.09, 0.16, 0.185, 0.10, R=R, power=0.7, sz=0.85, lip=0.0, thick=0.02, open_bottom=False), 'collar', 0.02)
    add(Torus(nk + R[:, 1] * 0.09, R[:, 1], 0.178, 0.014), 'bellg', 0.0)
    # chain of the Second Bell: a small bell on the breast
    for i in range(7):
        t = i / 6
        q = nk + R @ v3(-0.16 + 0.32 * t, -0.07 - 0.20 * np.sin(np.pi * t), 0.19 + 0.04 * np.sin(np.pi * t))
        add(Torus(q, v3(1, 0, 0) if i % 2 else v3(0, 0, 1), 0.019, 0.0065), 'brass', 0.0)
    sb = nk + R @ v3(0, -0.38, 0.22)
    add(bell_hull(sb + v3(0, 0.07, 0), 0.12, 0.025, 0.065, power=1.0, lip=0.01), 'bellg', 0.0)
    add(Sphere(sb + v3(0, -0.07, 0), 0.014), 'lamp', 0.0)
    # helm: tall dome, a single vertical slit, side bells, a fin crest
    add(Ellipsoid(H + Rh[:, 1] * 0.03, (0.16, 0.21, 0.17), Rh), 'helm', 0.0)
    add(Cylinder(H - Rh[:, 1] * 0.10, H - Rh[:, 1] * 0.06, 0.135, 0.012), 'iron', 0.02)
    add(RoundBox(H + Rh @ v3(0, 0.02, 0.128), (0.020, 0.095, 0.016), 0.006, Rh), 'abyss', 0.0)
    add(RoundBox(H + Rh @ v3(0, 0.02, 0.132), (0.011, 0.085, 0.012), 0.004, Rh), 'speck', 0.0)
    add(Capsule(H + Rh @ v3(0, 0.16, 0.07), H + Rh @ v3(0, 0.16, -0.14), 0.016, 0.012), 'bellg', 0.01)
    add(Ellipsoid(H + Rh @ v3(0, 0.15, -0.03), (0.012, 0.045, 0.14), Rh), 'bellg', 0.01)
    for sx in (-1, 1):
        a = H + Rh @ v3(sx * 0.128, 0.0, 0.0)
        add(Capsule(a, a + Rh @ v3(sx * 0.03, -0.05, 0), 0.008), 'brass', 0.0)
        add(bell_hull(a + Rh @ v3(sx * 0.03, -0.04, 0), 0.075, 0.016, 0.05, power=1.0, lip=0.008), 'bellg', 0.0)
    # the pressure-casket
    cc = P['cask']
    Rc = rot_x(P['cask_tilt']) @ R @ rot_y(0.0)
    cw = (0.20, 0.135, 0.15)
    add(RoundBox(cc, cw, 0.03, Rc), 'cask', 0.0)
    for dz in (-0.09, 0.09):
        add(RoundBox(cc + Rc @ v3(0, 0, dz), (cw[0] + 0.012, cw[1] + 0.012, 0.018), 0.008, Rc), 'iron', 0.0)
    add(RoundBox(cc + Rc @ v3(0, cw[1] - 0.005, 0), (cw[0] + 0.01, 0.022, cw[2] + 0.01), 0.01, Rc), 'bellg', 0.0)   # lid
    pc = cc + Rc @ v3(0, 0.0, cw[2] + 0.002)
    add(Cylinder(pc - Rc[:, 2] * 0.012, pc + Rc[:, 2] * 0.014, 0.065, 0.008), 'port', 0.0)
    add(Torus(pc + Rc[:, 2] * 0.012, Rc[:, 2], 0.067, 0.014), 'iron', 0.0)
    for sx in (-1, 1):                                  # carry-rings and chains over the shoulders
        rg = cc + Rc @ v3(sx * (cw[0] + 0.01), 0.07, 0.0)
        add(Torus(rg, Rc[:, 0], 0.035, 0.009), 'iron', 0.0)
    for sx in (-1, 1):
        a = nk + R @ v3(sx * 0.12, -0.04, 0.12)
        chain_links(add, a, cc + Rc @ v3(sx * 0.14, cw[1], 0.06), n=6, r=0.016, sag=0.03)
    barnacles(add, cc + Rc @ v3(0.1, 0.1, -0.05), Rc, n=7, spread=0.14, size=0.022, seed=5)
    # indictment strips streaming from the seals under the casket
    for k, x in enumerate((-0.13, -0.045, 0.045, 0.13)):
        a = cc + Rc @ v3(x, -cw[1] + 0.01, cw[2] * 0.7)
        sw = 0.03 * np.sin(2 * np.pi * (tl + k * 0.27))
        L = 0.26 + 0.05 * (k % 2)
        b = a + v3(sw, -L, 0.03)
        add(RoundBox((a + b) / 2, (0.022, L / 2, 0.004), 0.002, basis_from(norm(b - a), (0, 0, 1))), 'paper', 0.0)
        add(Sphere(a, 0.014), 'wax', 0.0)
    if P['fx'] > 0:
        add(Torus(v3(0, 0.03, 0.62), v3(0, 1, 0), 0.15 + 0.35 * P['fx'], 0.02), 'speck', 0.0)
    # raised sentencing hand glow
    mats = hadal_mats(P, {
        'lames': bell_metal(nk, R, base=_hex('#6a729c'), band=_hex('#242843'), spacing=0.10, patina_amt=0.22, barn=0.1),
        'plate': Material(cracked_albedo(_hex('#444a6c'), crack=_hex('#15172c'), freq=6, width=0.012, seep=TEAL), spec=0.5, gloss=30, metal=0.4, brush=0.05),
        'collar': bell_metal(nk, R, base=_hex('#555c7c'), spacing=0.07, patina_amt=0.3, barn=0.0),
        'helm': bell_metal(H, Rh, base=_hex('#8890b4'), spacing=0.35, patina_amt=0.3, barn=0.0),
        'bellg': bell_metal(H, Rh, base=BRONZE, band=_hex('#36443c'), spacing=0.06, patina_amt=0.5, barn=0),
        'brass': Material(_hex('#7f8a6c'), spec=0.8, gloss=40, metal=0.8),
        'cask': Material(cracked_albedo(_hex('#3a3f5a'), crack=_hex('#101224'), freq=8, width=0.012, seep=TEAL, barn=0.35), spec=0.5, gloss=26, metal=0.4, brush=0.06),
        'paper': Material(lambda p, n: np.array(_hex('#cfcab2'))[None, :] * (0.8 + 0.25 * fbm(p, 40, 2)[:, None]), spec=0.2, brush=0.06),
        'wax': Material(_hex('#8a2e2e'), spec=0.6, gloss=40),
    })
    lights = [teal_light(H + Rh[:, 2] * 0.2, P, 0.4, 0.4), teal_light(pc + Rc[:, 2] * 0.12, P, 0.9, 0.55, phase=0.3)]
    return hadal_finish(P, parts, mats, lights)


ROWS, _fr = humanoid_rows(neutral_pose, attack_style='cast', weapon_side='r', sink_depth=0.7, cast_side='r')


def frames():
    fr = _fr()
    hh = H_
    for i, (P, o) in enumerate(fr['idle']):
        carry(P, fwd=0.48, down=-0.06 + 0.006 * P['breathe'])
    for i, (P, o) in enumerate(fr['move']):
        carry(P, fwd=0.48, down=-0.06 + 0.012 * [1, 0, 1, 0][i], tilt=0.04 * [1, 0, -1, 0][i])
    # attack: heaves the casket forward and down onto the target (Weight of the Verdict)
    for i, (P, o) in enumerate(fr['attack']):
        carry(P, fwd=[0.34, 0.42, 0.52, 0.48][i], down=[0.02, 0.10, -0.22, -0.14][i], tilt=[-0.2, -0.45, 0.35, 0.1][i])
    for i, (P, o) in enumerate(fr['hit']):
        carry(P, fwd=0.28, down=-0.06)
    # cast (Pass Sentence): casket on the left arm, right hand raised in judgement
    for i, (P, o) in enumerate(fr['cast']):
        carry(P, fwd=0.36, down=-0.12)
        rig.place_arm(P, 'r', P['sh_r'] + v3(-0.10, [0.20, 0.48, 0.30][i], [0.22, 0.30, 0.42][i]), (-1, -0.2, -0.4), l1=0.27 * hh, l2=0.26 * hh)
        P['glow'] *= 1.2
    for i, (P, o) in enumerate(fr['death']):
        carry(P, fwd=[0.34, 0.36, 0.40, 0.42][i], down=[-0.12, -0.35, -0.7, -0.9][i])
        P['deflate'] = [0, 0, 0.2, 0.5][i]
    return fr

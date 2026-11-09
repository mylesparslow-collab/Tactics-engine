"""Bell-Bearer (Hadal Court, transport). Two bowed pit-thralls carry a verdigris pressure-bell slung on
chains between two long poles across their shoulders. The bell swings as they walk and rings out on the
attack. Defining detail: the hanging bell on its chains, teal ports glowing round its lip.
One sculpt: both thralls, poles, chains and bell are built here and posed from the unit's scalars.
"""
from _hadal_court_w2 import *

UNIT_ID = 'hadal_court_bell_bearer'
CAMERA = Camera(ppm=44)

C = Costume(top='hide', sleeve='hide', legs='hide', boot='hide', hand='hide', skin='hide', skirt='robe',
            skirt_mat='robe', hem=0.55, flare=0.6, head='none', belt='chain', boots_tall=False, girth=1.25)
ZT = 0.64          # thrall distance from the bell
POLE_Y = 1.12


def neutral_pose():
    return creature_pose()


def thrall_pose(st, lean, front, collapse=0.0):
    P = base_pose(0.92, 1.25)
    h = 0.92
    dn = -0.10 - 0.18 * collapse
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + rig.UPPER, v3(0, dn, 0))
    xr, xl = P['an_r'][0], P['an_l'][0]
    rig.place_leg(P, 'l', (xl, 0.085 + 0.07 * max(st, 0), 0.04 + 0.16 * st), l1=0.43 * h, l2=0.42 * h)
    rig.place_leg(P, 'r', (xr, 0.085 + 0.07 * max(-st, 0), 0.0 - 0.16 * st), l1=0.43 * h, l2=0.42 * h)
    rig.lean(P, fwd=np.radians(24 + 40 * collapse) + lean)
    P['head_pitch'] = np.radians(-22)
    # both hands grip the poles just ahead of the shoulders
    for s, sx in (('r', -1), ('l', 1)):
        sh = P['sh_' + s]
        rig.place_arm(P, s, v3(sx * 0.27, sh[1] - 0.10, sh[2] + 0.22), (sx, -0.6, -0.3), l1=0.27 * h, l2=0.26 * h)
    return P


def thrall(P, z0, front, tag):
    st = P['stride'] * (1 if front else 1)
    tp = thrall_pose(st, P['lean'] * 0.8, front, collapse=P['end'])
    tp['skirt_sway'] = 0.0
    parts, add = new_parts()
    body(tp, add, C)
    brute_limbs(tp, add, 'hide', arm=(0.085, 0.07, 0.065), fist=0.07, leg=(0.095, 0.075))
    R = frame_for(tp)
    add(Ellipsoid(tp['chest'] + R @ v3(0, -0.02, -0.07), (0.29, 0.19, 0.19), R), 'hide', 0.06)
    # crude bell-helm with an eye slit and a dim lamp
    H = tp['head']
    Rh = rot_y(tp['head_yaw']) @ rot_x(-tp['head_pitch'])
    add(bell_hull(H + Rh[:, 1] * 0.17, 0.30, 0.12, 0.20, R=Rh, power=0.6, sz=0.95, lip=0.03), 'helm', 0.0)
    add(Ellipsoid(H + Rh[:, 1] * 0.16, (0.12, 0.06, 0.11), Rh), 'helm', 0.03)
    add(RoundBox(H + Rh @ v3(0, -0.01, 0.185), (0.095, 0.015, 0.03), 0.008, Rh), 'abyss', 0.0)
    specks(add, [H + Rh @ v3(sx * 0.04, -0.01, 0.2) for sx in (-1, 1)], 0.010)
    flick = [1.0, 0.5, 1.1, 0.7][int((P['tell'] + (0.0 if front else 0.4)) * 4) % 4]
    bulb = stalk_lamp(add, H + Rh[:, 1] * 0.20, Rh[:, 1] + Rh[:, 2] * 0.5, Rh[:, 2] + v3(0, -0.1, 0),
                      0.09, 0.08, bulb=0.038, mat='iron', r0=0.015, r1=0.009)
    # yoke saddle: a padded iron collar where the pole rests
    for s, sx in (('r', -1), ('l', 1)):
        add(Capsule(tp['sh_' + s] + v3(0, 0.07, -0.05), tp['sh_' + s] + v3(0, 0.07, 0.10), 0.05, 0.05), 'iron', 0.02)
    out = transform_parts(parts, t=(0, 0, z0))
    return out, [Light(bulb + v3(0, 0, z0), TEAL, 0.3 * flick * max(pulse(P), 0), 0.4)], tp


def build(P):
    parts, add = new_parts()
    e, st, sk, tl = P['end'], P['stride'], P['strike'], P['tell']
    # thralls (front one pulls, rear one pushes)
    pf, lf, tpf = thrall(P, +ZT, True, 'f')
    pb, lb, tpb = thrall(P, -ZT - 0.05, False, 'b')
    parts += pf + pb
    # twin carry-poles across the shoulders with iron caps
    for sx in (-1, 1):
        sfy = tpf['sh_' + ('r' if sx < 0 else 'l')][1] + 0.08
        sby = tpb['sh_' + ('r' if sx < 0 else 'l')][1] + 0.08
        a = v3(sx * 0.26, sby, -ZT - 0.30)
        b = v3(sx * 0.26, sfy, ZT + 0.30)
        add(Capsule(a, b, 0.032, 0.032), 'wood', 0.0)
        for q in (a, b):
            add(Sphere(q, 0.042), 'iron', 0.0)
        for zz in (-ZT - 0.05, ZT):
            t = (zz - a[2]) / (b[2] - a[2])
            add(Torus(a + (b - a) * t, norm(b - a), 0.04, 0.012), 'iron', 0.0)
    # cross-yoke over the bell
    hang = v3(0, 1.26, 0.0)
    add(Capsule(v3(-0.26, hang[1], 0.0), v3(0.26, hang[1], 0.0), 0.034), 'iron', 0.0)
    # the bell on chains, swinging about the yoke
    ang = 0.07 * np.sin(2 * np.pi * (tl + 0.25)) + 0.30 * sk - 0.12 * (1 if sk > 0 else 0) + 0.18 * st * 0.5
    bparts = []
    badd = lambda prim, mat, k=0.0: bparts.append(Part(prim, mat, k))
    top = v3(0, hang[1] - 0.14, 0.0)
    bh = 1.0
    badd(bell_hull(top, bh, 0.16, 0.46, power=1.5, sz=0.95, lip=0.05, ribs=0.02, ribs_n=12), 'bell', 0.03)
    badd(Torus(top + v3(0, -0.03, 0), v3(0, 1, 0), 0.17, 0.028), 'bellg', 0.0)       # crown ring
    badd(Torus(top + v3(0, -bh * 0.52, 0), v3(0, 1, 0), 0.33, 0.020), 'bellg', 0.0)   # waist band
    badd(Torus(top + v3(0, -bh * 0.93, 0), v3(0, 1, 0), 0.46, 0.024), 'bellg', 0.0)   # lip band
    for k in range(6):
        a = k * 1.047 + 0.3
        q = top + v3(np.sin(a) * 0.44, -bh * 0.86, np.cos(a) * 0.42)
        badd(Sphere(q, 0.028), 'port', 0.0)
    # barnacles crust on one flank
    bn = []
    barnacles(lambda pr, m, k=0.0: bparts.append(Part(pr, m, k)), top + v3(0.0, -0.45, 0), np.eye(3), n=12, spread=0.33, size=0.032, seed=9)
    # crown loop
    badd(Torus(top + v3(0, 0.07, 0), v3(1, 0, 0), 0.05, 0.016), 'iron', 0.0)
    # clapper swinging inside, peeking below the lip
    parts.extend(transform_parts(bparts, R=rot_x(ang), pivot=hang))
    # chains from the yoke to the bell crown and from the poles to the thrall harness
    vchain(add, hang + v3(0, -0.01, 0), hang + v3(0, -0.12, 0.0), n=2, r=0.03)
    for sx in (-1, 1):
        pass
    for q, tpp, zc in ((v3(0, 0, 0), tpf, ZT), (v3(0, 0, 0), tpb, -ZT - 0.05)):
        for sx, s in ((-1, 'r'), (1, 'l')):
            a = tpp['chest'] + v3(sx * 0.14, 0.02, zc + 0.2)
            b = v3(sx * 0.26, hang[1] - 0.02, zc * 0.45)
            chain_links(add, a, b, n=5, r=0.02, sag=0.05)
    if P['fx'] > 0:
        fx = P['fx']
        add(Torus(v3(0, 0.03, 0.62), v3(0, 1, 0), 0.30 + 0.5 * fx, 0.022), 'speck', 0.0)
        add(Torus(v3(0, 0.03, 0.62), v3(0, 1, 0), 0.15 + 0.3 * fx, 0.016), 'speck', 0.0)
    # global bob (everything bounces slightly with the gait) and death squash
    parts[:] = transform_parts(parts, t=(0, P['bob'], -0.30))
    mats = hadal_mats(P, {
        'bell': bell_metal(top, np.eye(3), base=_hex('#6f7c5c'), band=_hex('#2f3a30'), patina=VERDI, patina_amt=0.30, spacing=0.17, barn=0.25),
        'bellg': bell_metal(top, np.eye(3), base=BRONZE, band=_hex('#36443c'), spacing=0.9, patina_amt=0.4, barn=0),
        'helm': bell_metal(v3(0, 1, 0), np.eye(3), base=_hex('#5d6584'), spacing=0.4, patina_amt=0.4, barn=0.0),
        'hide': Material(cracked_albedo(_hex('#33385f'), crack=_hex('#0f121c'), freq=6, width=0.02, mottle=0.2), spec=0.5, gloss=34, brush=0.05),
        'wood': Material(_hex('#4a3d33'), spec=0.1, brush=0.12),
        'robe': Material(cracked_albedo(_hex('#2c3058'), crack=_hex('#14162b'), freq=5, width=0.008, mottle=0.2), spec=0.06, brush=0.1),
    })
    lights = [Light(L.pos + v3(0, 0, -0.30), L.color, L.intensity, L.radius) for L in lf + lb] + [Light(v3(0, 0.45 + P['bob'], -0.30), TEAL, 0.3 * max(pulse(P, 0.3), 0), 0.6)]
    return hadal_finish(P, parts, mats, lights)


def _extra(rows):
    for i, (P, o) in enumerate(rows['death']):
        P['lean'] = [0.0, 0.1, 0.12, 0.12][i]
    return rows


ROWS, frames = creature_rows(neutral_pose, sink=(0, 0, 0.14, 0.42), deflate=(0, 0, 0.12, 0.35), extra=_extra)

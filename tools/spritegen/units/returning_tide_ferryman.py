"""Ferryman (Returning Tide, reviver). He rows a DRY boat across the salt: a pale, bleached skiff on two
curved sled runners, the only dry thing in the whole faction, a shrouded passenger lying in the bottom and a
dim brine-lantern on the bow-post. He is hooded, soaked and green-black, standing in the stern and
punting with a long oar-pole. One sculpt: boat, runners, ferryman, pole and passenger.
Defining detail: the dry upturned boat on runners with the shrouded passenger.
"""
from _returning_tide_w2 import *
from render import Camera
from kit.xform import transform_parts

UNIT_ID = 'returning_tide_ferryman'
CAMERA = Camera(ppm=46)

C = Costume(top='robe', sleeve='robe', legs='robe', boot='skin', hand='skin', skin='skin',
            skirt=None, head='none', belt=None, boots_tall=False, girth=1.05)
BL = 0.80           # boat half length
BOAT_Z = 0.32       # boat centre ahead of the ferryman's feet
FLOOR = 0.27        # boat floor height (figure stands on it)
SHIFT = -0.30


def fpose(g1, g2, lean=8, plant=True, bob=0.0, pitch=0, z=0.0, roll=0.0, kneel=0.0, pole_d=None, lh=None):
    P = base_pose(height=1.02, build=1.0)
    h = 1.02
    P['plant'] = plant
    P['g1'], P['g2'] = v3(*g1), v3(*g2)
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + rig.UPPER, v3(0, -0.06 - 0.28 * kneel, z))
    rig.place_leg(P, 'l', (0.17, 0.085, 0.14 + z), l1=0.43 * h, l2=0.42 * h, pole=(0.3, 0, 1))
    rig.place_leg(P, 'r', (-0.17, 0.085, -0.16 + z), l1=0.43 * h, l2=0.42 * h, pole=(-0.3, 0, 1))
    rig.lean(P, fwd=np.radians(lean))
    P['head_pitch'] = np.radians(pitch)
    rig.place_arm(P, 'r', P['g1'], (-1, -0.5, -0.3), l1=0.27 * h, l2=0.26 * h)
    rig.place_arm(P, 'l', P['g2'] if lh is None else v3(*lh), (1, -0.5, -0.3), l1=0.27 * h, l2=0.26 * h)
    P['pole_d'] = pole_d
    P['bob'], P['roll'], P['rise'] = bob, roll, 0.0
    P['boat_sink'] = 0.0
    return P


def neutral_pose():
    return fpose((-0.22, 1.02, 0.16), (-0.14, 1.36, 0.26))


def hull(c, rad_w=0.30, L=BL):
    def f(p):
        x, y, z = p[:, 0] - c[0], p[:, 1] - c[1], p[:, 2] - c[2]
        s = np.clip(z / L, -1.2, 1.2)
        w = rad_w * np.clip(1 - np.abs(s) ** 1.7, 0.0, 1) ** 0.6 + 0.012
        top = 0.56 + 0.20 * s * s
        yc = 0.38 + 0.08 * s * s
        a = np.abs(x) / w
        b = (y - yc) / 0.20
        sec = (a ** 2.6 + np.abs(b) ** 2.6) ** (1 / 2.6)
        d = (sec - 1) * np.minimum(w, 0.2) * 0.8
        d = np.maximum(d, np.abs(z) - L)
        # hollow
        w2 = np.maximum(w - 0.035, 0.005)
        a2 = np.abs(x) / w2
        b2 = (y - (yc + 0.07)) / 0.22
        sec2 = (a2 ** 2.6 + np.abs(b2) ** 2.6) ** (1 / 2.6)
        d2 = (sec2 - 1) * np.minimum(w2, 0.2) * 0.8
        d = np.maximum(d, -d2)
        d = np.maximum(d, y - top)
        return d
    return Func(f, c + v3(0, 0.4, 0), L + 0.35)


def build(P):
    parts, add = new_parts()
    tl = P['tell']
    # ---------- the ferryman (feet at ground level in local coords)
    fparts, fadd = new_parts()
    body(P, fadd, C)
    h, b = P['height'], P['build']
    R = frame_for(P)
    fadd(ragged_robe(P, hem=0.07, flare=1.0, rag=1.0, seed=6.0, droop=0.05, girth=1.15), 'robe', 0.0)
    fadd(shawl(P, depth=0.22, width=0.20, rag=1.0, seed=2.2, front_drop=0.06), 'black', 0.0)
    deep_hood(P, fadd, 'black', size=1.12, peak=0.08, tail=0.28, droop=0.03)
    for s in ('r', 'l'):
        sleeve_flare(P, fadd, s, 'robe', length=0.08, width=0.065)
    # rope sash with a coil of mooring line
    knotted_cord(fadd, P, y_off=0.07, mat='cord')
    for k in range(3):
        fadd(Torus(P['pelvis'] + v3(-0.18, 0.02 + 0.02 * k, 0.04), v3(1, 0, 0), 0.07, 0.016), 'cord', 0.0)
    # the pole: butt in the salt behind him, crooked handle on top, flat oar-blade at the foot
    g1, g2 = P['g1'], P['g2']
    d = norm(g2 - g1) if P['pole_d'] is None else norm(v3(*P['pole_d']))
    Lb = (g1[1] / max(d[1], 0.3)) if P['plant'] else 1.25
    butt, top = g1 - d * Lb, g1 + d * 0.62
    fadd(Capsule(butt, top, 0.020, 0.017), 'pole', 0.0)
    side = norm(np.cross(d, v3(0, 0, 1)))
    fadd(RoundBox(butt + d * 0.16, (0.062, 0.20, 0.010), 0.006, basis_from(d, side)), 'pole', 0.0)   # oar blade
    fadd(Capsule(top, top + side * 0.09 + d * 0.01, 0.017, 0.017), 'pole', 0.01)
    fadd(Sphere(top + side * 0.10, 0.022), 'pole', 0.0)
    fparts_t = transform_parts(fparts, t=(0, FLOOR - 0.045 + P['bob'], 0))
    parts += fparts_t
    drips(P, add, [P['wr_l'] + v3(0, FLOOR - 0.12, 0), P['pelvis'] + v3(0.2, FLOOR - 0.7, 0.05), butt + v3(0, FLOOR + 0.3, 0)], fall=0.35)
    # ---------- the dry boat, shifted along z, rolled/sunk as scalars say
    bparts, badd = new_parts()
    bc = v3(0, 0.0, BOAT_Z)
    badd(hull(bc), 'plank', 0.0)
    # gunwale rail and stem posts (curl up at bow and stern)
    for zz, sg in ((BL * 0.97, 1), (-BL * 0.97, -1)):
        a = bc + v3(0, 0.50, zz)
        badd(Capsule(a, a + v3(0, 0.22, sg * 0.05), 0.030, 0.022), 'plank', 0.01)
        badd(Sphere(a + v3(0, 0.24, sg * 0.055), 0.034), 'plank', 0.0)
    for sx in (-1, 1):
        badd(Capsule(bc + v3(sx * 0.27, 0.57, -0.50), bc + v3(sx * 0.255, 0.56, 0.5), 0.018, 0.018), 'plank_dk', 0.0)
    # thwarts (cross planks)
    for zz in (-0.12, 0.30):
        badd(RoundBox(bc + v3(0, 0.46, zz), (0.28, 0.015, 0.05), 0.005), 'plank_dk', 0.0)
    # sled runners with iron shoes, curling up at the bow
    for sx in (-1, 1):
        pts = [bc + v3(sx * 0.17, 0.10, z_) for z_ in (-0.85, -0.5, 0.0, 0.5, 0.82)] + [bc + v3(sx * 0.17, 0.20, 0.97), bc + v3(sx * 0.17, 0.36, 1.03)]
        pts[0] = bc + v3(sx * 0.17, 0.14, -0.90)
        for i in range(len(pts) - 1):
            badd(Capsule(pts[i], pts[i + 1], 0.030, 0.030), 'runner', 0.01)
        for zz in (-0.45, 0.05, 0.55):
            badd(Capsule(bc + v3(sx * 0.17, 0.10, zz), bc + v3(sx * 0.11, 0.30, zz), 0.022), 'plank_dk', 0.0)
    # bow-post lantern with a brine-glint glass
    lp = bc + v3(0, 0.80, BL * 0.97 + 0.06)
    badd(Capsule(lp + v3(0, 0.0, -0.02), lp + v3(0, -0.10, 0.07), 0.009), 'cord', 0.0)
    lc = lp + v3(0, -0.15, 0.09)
    badd(Cylinder(lc - v3(0, 0.05, 0), lc + v3(0, 0.05, 0), 0.04, 0.008), 'glass', 0.0)
    badd(Sphere(lc, 0.026), 'lamp', 0.0)
    badd(Torus(lc + v3(0, 0.055, 0), v3(0, 1, 0), 0.038, 0.007), 'iron', 0.0)
    # the passenger: a long bundle in linen, lying in the bottom, hands crossed
    rise = P['rise']
    pc = bc + v3(0, 0.40 + 0.35 * rise, 0.34)
    pR = rot_x(np.pi / 2 - 0.0 * rise)
    badd(Capsule(pc + v3(0, 0, -0.30), pc + v3(0, 0, 0.30), 0.075, 0.062), 'linen', 0.05)
    badd(Sphere(pc + v3(0, 0.0, 0.34), 0.07), 'linen', 0.03)
    for zz in (-0.18, 0.0, 0.16):
        badd(Torus(pc + v3(0, 0, zz), v3(0, 0, 1), 0.07, 0.010), 'cord', 0.0)
    if rise > 0:
        for k in range(5):
            a = k * 1.25 + tl * 6.28
            badd(Sphere(pc + v3(np.cos(a) * 0.12, 0.10 + 0.2 * rise * (k / 4), np.sin(a) * 0.12), 0.014), 'drip', 0.0)
    # boat group transform: roll/sink for death, bob for the glide
    R_roll = rot_z(P['roll']) if P['roll'] else np.eye(3)
    parts += transform_parts(bparts, R=R_roll, t=(0, P['bob'] * 0.6 - P['boat_sink'], 0), pivot=(0, 0.2, 0))
    # a splash at the pole foot / blade slap
    if P['fx'] > 0:
        for k in range(8):
            a = k / 8 * 6.28
            add(Sphere(v3(0.35 + np.cos(a) * 0.3 * P['fx'], 0.12 + 0.08 * (k % 2), 0.55 + np.sin(a) * 0.3 * P['fx']), 0.03), 'drip', 0.0)
        add(Torus(v3(0.35, 0.02, 0.55), v3(0, 1, 0), 0.2 + 0.4 * P['fx'], 0.018), 'drip', 0.0)
    parts[:] = transform_parts(parts, t=(0, 0, SHIFT))
    # ---------- materials
    def plank_albedo(p, n):
        base = np.array(_hex('#cfc3a3'))[None, :] * (0.82 + 0.3 * fbm(p, 14, 3)[:, None])
        seam = np.abs(np.mod(p[:, 1] * 6.5, 1.0) - 0.5) > 0.47
        base[seam] = base[seam] * 0.55
        grain = fbm(p * np.array([1.0, 3.0, 0.2]), 40, 2) > 0.62
        base[grain] *= 0.88
        return base
    mats = {
        'robe': wet_cloth(_hex('#2c3a35'), wet=0.9, low_dark=0.2),
        'black': wet_cloth(_hex('#33493f'), wet=0.85, low_dark=0.1),
        'skin': wet_skin(P, SKIN_PALE, hair=BLACK, sunken=0.45),
        'plank': Material(plank_albedo, spec=0.08, gloss=10, brush=0.1),
        'plank_dk': Material(_hex('#8f836a'), spec=0.08, brush=0.1),
        'runner': Material(_hex('#4d4f4a'), spec=0.6, gloss=30, metal=0.5, brush=0.06),
        'pole': Material(_hex('#b9a88a'), spec=0.08, brush=0.1),
        'iron': Material(_hex('#3a3d3c'), spec=0.6, gloss=30, metal=0.5),
        'glass': Material(_hex('#9fc9c2'), spec=0.9, gloss=60, emissive=tuple(np.array(BRINE) * 0.35), rim=0.0),
        'lamp': Material(GLINT, emissive=tuple(np.array(GLINT) * 1.3 * P['glow']), rim=0.0),
    }
    lamp_pos = bc + v3(0, 0.65, BL * 0.97 + 0.15) + v3(0, 0, SHIFT)
    lights = [Light(lamp_pos, BRINE, 0.9 * P['glow'] * (1 + 0.8 * rise), 0.6)]
    puddle(P, add, r=0.34, center=(0.0, 0.0, -0.10 + SHIFT), seed=1.0)
    sc = tide_finish(P, parts, mats, add, lights=lights, pool_r=0.8)
    return sc


def row_frames():
    fr = {}
    h = 1.02
    fr['idle'] = []
    for i in range(4):
        b = [0, 1, 0, -1][i]
        P = fpose((-0.22, 1.02, 0.16 + 0.01 * b), (-0.14, 1.36, 0.26), bob=0.006 * b)
        P['tell'] = i / 4.0
        P['breathe'] = b
        P['skirt_sway'] = 0.1 * b
        P['glow'] = [1, 0.85, 1.1, 0.9][i]
        fr['idle'].append((P, {}))
    fr['move'] = []
    for i in range(4):
        ph = [0.0, 0.5, 1.0, 0.5][i]       # pole push: plant, lean in, shove, recover
        g1 = (-0.22, 1.02, 0.04 + 0.22 * ph)
        g2 = (-0.14, 1.36, 0.14 + 0.30 * ph)
        P = fpose(g1, g2, lean=6 + 8 * ph, bob=0.012 * [0, 1, 0, 1][i], z=0.03 * ph)
        P['tell'] = i / 4.0
        P['skirt_sway'] = [0.4, 0.0, -0.4, 0.0][i]
        fr['move'].append((P, {}))
    fr['attack'] = []
    A = [((-0.30, 1.20, -0.05), (-0.10, 1.55, -0.20), 4, False),         # wind up, blade drawn back and up
         ((-0.22, 1.20, 0.10), (0.05, 1.50, 0.05), 10, False),
         ((0.10, 1.00, 0.50), (0.36, 1.12, 0.78), 18, False),               # blade slaps the water forward-left
         ((0.00, 1.05, 0.30), (0.20, 1.22, 0.50), 10, False)]
    for i, (g1, g2, ln, pl) in enumerate(A):
        P = fpose(g1, g2, lean=ln, plant=pl, z=[-0.02, 0.0, 0.06, 0.03][i])
        P['fx'] = [0, 0, 1, 0.3][i]
        P['head_pitch'] = np.radians([-4, 0, 8, 2][i])
        fr['attack'].append((P, {}))
    fr['hit'] = []
    for i in range(2):
        P = fpose((-0.22, 1.02, 0.12 - 0.04 * (1 - i)), (-0.14, 1.36, 0.20), lean=[-10, -3][i], pitch=[10, 3][i])
        fr['hit'].append((P, dict(exposure=1.25, flash=0.22) if i == 0 else {}))
    fr['death'] = []
    for i in range(4):
        P = fpose([(-0.2, 1.0, 0.10), (-0.18, 0.80, 0.30), (-0.18, 0.60, 0.40), (-0.18, 0.5, 0.44)][i],
                  [(-0.1, 1.3, 0.22), (-0.10, 1.0, 0.36), (-0.1, 0.8, 0.46), (-0.1, 0.62, 0.5)][i],
                  lean=[-8, 14, 30, 38][i], plant=False, kneel=[0, 0.4, 0.8, 1.0][i], pitch=[10, 20, 30, 34][i],
                  roll=[0.0, 0.05, 0.12, 0.2][i])
        P['boat_sink'] = [0, 0.02, 0.10, 0.24][i]
        P['glow'] = [1, 0.6, 0.3, 0.0][i]
        P['end'] = [0, 0.15, 0.5, 1.0][i]
        P['sink'] = [0, 0, 0.12, 0.30][i]
        fr['death'].append((P, {}))
    fr['cast'] = []
    for i in range(3):
        P = fpose((-0.22, 1.02, 0.14), (-0.14, 1.36, 0.26), lean=[2, -4, 3][i], pitch=[-6, -14, -2][i], plant=True, pole_d=(0.12, 1.0, 0.25), lh=(0.12, [1.5, 1.85, 1.6][i], 0.26))
        P['rise'] = [0.3, 1.0, 0.5][i]
        P['glow'] = [1.3, 2.0, 1.3][i]
        P['cast_glow'] = [0.5, 1.0, 0.4][i]
        fr['cast'].append((P, {}))
    return fr


frames = row_frames
from kit.anim import ROWS

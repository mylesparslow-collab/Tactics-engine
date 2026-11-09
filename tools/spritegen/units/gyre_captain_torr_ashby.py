"""Captain Torr Ashby of the Black Wheel (Gyre hero, flying). A scarred mercenary on a vast bald vulture descending,
neck hunched, wings wide. Dark oilskin coat with a thin gold company badge, bone hook at the belt, beak-orange sash,
a half-eaten loaf of bread in his teeth. Grim and patient."""
from _gyre_common import *

UNIT_ID = 'gyre_captain_torr_ashby'
LOOK = LOOK_AIR
CAMERA = Camera(ppm=46)
S = species('vulture', half=0.78, body=(0.17, 0.14, 0.33), headr=(0.043, 0.045, 0.058), neck=0.20, neck_th=0.034, beak_len=0.105, beak_d=0.022,
            hook=0.035, tip_mat=None, head=hx('#b0605a'), neckc=mix(INK, SLATE, 0.35), ruff=hx('#e8e2d6'), fingers=7,
            col=dict(mantle=mix(INK, SLATE, 0.30), covert=mix(INK, SLATE, 0.22), flight=hx('#8b7f72'), tip=None, spot=None),
            back=mix(INK, SLATE, 0.30), belly=hx('#6b625b'), tailc=hx('#6e655c'))


def hands(P, Q, S):
    h = 0.90
    sh = Q['sh_r']
    rig.place_arm(Q, 'r', sh + v3(-0.12, -0.14, 0.22), (-1, -0.3, -0.2), l1=0.27 * h, l2=0.26 * h)


R = rider_cfg(h=1.0, b=1.06, girth=1.1, lean=0.50, head='bald', skin=hx('#b88562'), hands=hands, tail_len=0.6,
              beard=hx('#3a342f'), mats=dict(coat=hx('#72767e'), skin=hx('#b88562')))
R['hair'] = hx('#3a342f')


def neutral_pose():
    return fly_pose(fl=0.22, pitch=0.26, neckx=0.35, dip=-0.8, yaw=-0.35, legs=0.3)


def extra(c):
    W, add, F, P = c['W'], c['add'], c['F'], c['P']
    H = W['head']
    Rh = head_R(W)
    # fluffy pale neck ruff: ring of puffs around the lower neck, head pokes out above it
    k = S['k']
    bx_, by_, bz_ = S['body']
    nxx, dp = P['neckx'], P['dip']
    Hl = v3(0, by_ * 0.95 + 0.02 - 0.08 * dp, bz_ * 0.72 + S['neck'] * (0.55 + 0.45 * nxx))
    cen = Hl + v3(0, -0.035, -0.07)
    c['mats']['ruffw'] = Material(noisy(hx('#f0eadc'), 0.06, 40.0), spec=0.03, brush=0.08)
    for i in range(10):
        a = i / 10 * 6.283
        q = cen + v3(0.105 * np.sin(a), 0.03 * np.cos(a), 0.06 * np.cos(a))
        add(Sphere(F.pt(q * k), 0.062), 'ruffw', 0.05)
    add(Sphere(F.pt(cen * k), 0.07), 'ruffw', 0.05)
    # half-eaten loaf in his teeth
    m = H + Rh @ v3(0.0, -0.03, 0.085) * 0.9
    add(Ellipsoid(m + Rh @ v3(0.0, 0.0, 0.05), (0.075, 0.032, 0.038), Rh @ rot_z(0.2)), 'bread', 0.0)
    add(Sphere(m + Rh @ v3(0.07, -0.01, 0.08), 0.022), 'skin_in', 0.0)
    c['mats']['skin_in'] = Material(hx('#e6d2a8'), spec=0.02, brush=0.04)
    # gold company badge on the chest
    ch = W['chest']
    add(Cylinder(ch + F.R @ v3(-0.08, 0.06, 0.12), ch + F.R @ v3(-0.08, 0.06, 0.135), 0.024, 0.004), 'gold', 0.0)
    # beak-orange sash: thin diagonal stripe across the chest
    ax_ = norm(W['neck'] - W['pelvis'])
    Rt = basis_from(ax_, v3(0, 0, 1))
    a_ = ch + Rt @ v3(0.15, 0.14, 0.125)
    b_ = W['pelvis'] + Rt @ v3(-0.15, 0.03, 0.13)
    add(Capsule(a_, b_, 0.024, 0.024), 'cord', 0.0)
    # cool-lit lighter shoulders (pale oilskin pads) to separate rider from bird
    for s_ in ('sh_r', 'sh_l'):
        add(Sphere(W[s_] + v3(0, 0.025, 0), 0.062), 'oil_pale', 0.0)
    # bone hook at the belt
    pel = W['pelvis']
    side = F.R @ v3(-1, 0, 0)
    a = pel + side * 0.15 + F.R @ v3(0, 0.0, 0.0)
    b = a + F.R @ v3(-0.02, -0.12, 0.10)
    add(Capsule(a, b, 0.016, 0.012), 'bone', 0.0)
    add(Capsule(b, b + F.R @ v3(-0.03, -0.02, 0.07), 0.012, 0.004), 'bone', 0.0)
    add(Capsule(pel + side * 0.0, pel + side * 0.18, 0.02, 0.02), 'cord', 0.0)


def build(P):
    sc = flier_build(P, S, R, extra, y0=0.80)
    # drop stray trailing harness cords that fly out of frame during the fall / hit rows
    fwd, right, up = CAMERA.basis()
    keep = []
    for p in sc.parts:
        c = getattr(p.prim, 'bc', None)
        if c is None:
            c = getattr(p.prim, 'c', getattr(p.prim, 'a', None))
        if c is not None and p.mat in ('tar', 'cord'):
            c = np.array(c)
            sx = CAMERA.anchor[0] + CAMERA.ppm * (c @ right)
            sy = CAMERA.anchor[1] - CAMERA.ppm * (c @ up)
            if sx < 6 or sx > 90 or sy < 8 or sy > 104:
                continue
        keep.append(p)
    sc.parts[:] = keep
    mt = P.get('melt', 0.0)
    if mt > 0.01:
        sc.parts[:] = squash_parts(sc.parts, sy=1.0, sxz=1 - 0.30 * mt)
    rf = P.get('rfall', 0.0)
    if rf > 0.01:
        sc.parts[:] = transform_parts(sc.parts, t=(0.06 * rf, 0.30 * rf, 0.0))
    return sc


ROWS, frames = fly_rows(neutral_pose, idle_amp=0.60)

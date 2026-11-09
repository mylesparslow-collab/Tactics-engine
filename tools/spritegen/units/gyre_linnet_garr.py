"""Linnet Garr (Gyre hero, flying). The messenger who never breaks the Gyre's oldest bargain: a young rider flat
along a fast white tern, black-capped, forked tail, long needle wings swept back. Windblown hair under a beak-orange
scarf, grey-green flight coat, an oilcloth letter pouch (red wax seal) slung at the hip and a sealed letter held
out in the free hand. Defining detail: the glowing sealed letter (cast: it flares and a ring of feathers carries it)
against the fast, clean tern silhouette."""
from _gyre_w2 import *

UNIT_ID = 'gyre_linnet_garr'
LOOK = LOOK_AIR
CAMERA = Camera(ppm=48)
S = species('tern', k=1.2, half=0.92, tail_len=0.42, ch_root=0.28, ch_wrist=0.19, back=mix(GUANO, SLATE, 0.18),
            col=dict(mantle=mix(GUANO, SLATE, 0.16), covert=mix(GUANO, SLATE, 0.06), flight=mix(SLATE, GUANO, 0.30),
                     tip=INK, spot=None))


def hands(P, Q, S_):
    h = 0.78
    sh = Q['sh_r']
    # right hand holds the letter out beside the bird's neck; left on the reins
    rig.place_arm(Q, 'r', sh + v3(-0.10, -0.12, 0.30 + 0.12 * P['arm']), (-1, -0.3, -0.2), l1=0.27 * h, l2=0.26 * h)


R = rider_cfg(h=0.78, b=0.90, lean=0.80, head='scarf', hair=hx('#9a5f33'), skin=hx('#d6a582'), hands=hands,
              tail_len=0.42, goggles=True, mats=dict(coat=hx('#4f5f6b'), lips=hx('#b2564a')))
R['look'] = 0.0


def neutral_pose():
    return fly_pose(fl=0.22, pitch=0.06, roll=0.16, yaw=0.50, neckx=0.9, legs=0.0, look=-0.5, tailsp=0.3)


def extra(c):
    W, add, F, P, mats = c['W'], c['add'], c['F'], c['P'], c['mats']
    extra_mats(mats)
    lights = []
    pel = W['pelvis']
    side = F.R @ v3(-1, 0, 0)
    # oilcloth pouch at the camera-side hip, strap across the chest
    pc = pel + side * 0.17 + F.R @ v3(0, -0.12, -0.02)
    Rp = F.R @ rot_z(0.15)
    pouch(add, pc, Rp, size=1.25)
    ch = W['chest']
    add(Capsule(pc + F.R @ v3(0, 0.07, -0.01), ch + F.R @ v3(0.07, 0.10, 0.07), 0.011, 0.011), 'oilcloth_dk', 0.0)
    add(Capsule(ch + F.R @ v3(0.07, 0.10, 0.07), ch + F.R @ v3(-0.12, 0.13, 0.05), 0.011, 0.011), 'oilcloth_dk', 0.0)
    # the sealed letter in the right hand
    g = hand_pos(W, 'r')
    glow = 0.35 + 0.65 * P['cast_glow']
    Rl = F.R @ rot_x(-0.9) @ rot_z(-0.2)
    letter(add, g + F.R @ v3(-0.02, 0.03, 0.05), Rl, size=1.35, glow=glow, lights=lights)
    # scarf tails streaming
    H = W['head']
    back = W['_back']
    fl = np.sin(P['tell'] * 6.283)
    a = W['neck'] + v3(0, -0.01, 0.0)
    for j, off in enumerate((-0.03, 0.03)):
        b1 = a + back * 0.20 + v3(off, 0.02 + 0.03 * fl, 0)
        b2 = b1 + back * 0.18 + v3(off * 2, -0.02 - 0.03 * fl, 0)
        add(Capsule(a, b1, 0.018, 0.016), 'cord', 0.0)
        add(Capsule(b1, b2, 0.016, 0.008), 'cord', 0.0)
    return lights


def build(P):
    return flier_build(P, S, R, extra, y0=0.62)


def tweak(rows):
    for nm in rows:
        for i, (P, o) in enumerate(rows[nm]):
            P['tailsp'] = 0.3 + 0.2 * np.sin(i)
    for i, (P, o) in enumerate(rows['attack']):
        P['arm'] = [0, 0.3, 1.0, 0.4][i]
    for i, (P, o) in enumerate(rows['cast']):
        P['arm'] = [0.6, 1.0, 0.8][i]


ROWS, frames = fly_rows(neutral_pose, tweak=tweak, idle_amp=0.55)

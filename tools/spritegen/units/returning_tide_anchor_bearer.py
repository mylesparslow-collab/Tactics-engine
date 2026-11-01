"""Anchor-Bearer (Returning Tide, tank). A penitent who chose to drag a ship's anchor until the tide took them.

Hulking and bent forward in dark wet sackcloth, grey-green skin. Defining detail: a giant barnacled
anchor hauled over the right shoulder, its chain wound round the waist.
"""
from _returning_tide_common import *
from render import Camera

UNIT_ID = 'returning_tide_anchor_bearer'
CAMERA = Camera(ppm=46)

C = Costume(top='sack', sleeve='sack', legs='sack', boot='skin', hand='skin', skin='skin',
            skirt=None, head='bald', belt=None, boots_tall=False, girth=1.35)


def neutral_pose():
    P = base_pose(height=1.06, build=1.32)
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + rig.UPPER, v3(0, -0.05, 0))
    rig.place_leg(P, 'l', (0.20, 0.085, 0.14), l1=0.45, l2=0.44)
    rig.place_leg(P, 'r', (-0.20, 0.085, -0.10), l1=0.45, l2=0.44)
    rig.lean(P, fwd=np.radians(20))
    P['head_pitch'] = np.radians(-10)
    # both hands on the shank over the right shoulder
    rig.place_arm(P, 'r', P['sh_r'] + v3(-0.04, 0.04, 0.16), (-1, -0.6, 0.2), l1=0.29, l2=0.28)
    rig.place_arm(P, 'l', P['sh_r'] + v3(0.06, -0.10, 0.22), (1, -0.6, -0.2), l1=0.29, l2=0.28)
    P['item_r'] = norm(v3(-0.40, -0.80, -0.50))
    return P


def anchor(P, add, g, d):
    """Shank from the ring end (near the hands) down to the crown; two curved flukes."""
    side = norm(np.cross(d, v3(-0.53, 0.5, 0.68)))   # flukes spread across the view
    ring = g - d * 0.22
    crown = g + d * 0.95
    add(Capsule(ring, crown, 0.034, 0.042), 'anchor', 0.0)
    add(Torus(ring - d * 0.06, side, 0.06, 0.016), 'anchor', 0.0)
    add(Capsule(ring + d * 0.04 - side * 0.24, ring + d * 0.04 + side * 0.24, 0.022), 'anchor', 0.0)   # stock
    up = norm(np.cross(side, d))
    for sx in (-1, 1):
        a = crown + side * sx * 0.03
        m = crown + side * sx * 0.20 - d * 0.05
        t = crown + side * sx * 0.30 - d * 0.28
        add(Capsule(a, m, 0.036, 0.032), 'anchor', 0.02)
        add(Capsule(m, t, 0.032, 0.012), 'anchor', 0.02)
        add(Ellipsoid(m * 0.5 + t * 0.5 + side * sx * 0.02, (0.085, 0.06, 0.018), basis_from(t - m, up)), 'anchor', 0.01)
    add(Sphere(crown + d * 0.02, 0.05), 'anchor', 0.02)
    barnacles(add, crown + d * 0.0 + up * 0.04, up, n=6, spread=0.06, seed=11)
    barnacles(add, g + d * 0.4 + up * 0.03, up, n=4, spread=0.04, seed=12)
    return ring - d * 0.06


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    add(ragged_robe(P, hem=0.40, flare=0.7, top=1.0, rag=1.6, seed=7.7, droop=0.02, girth=1.25), 'sack', 0.0)
    add(shawl(P, depth=0.20, width=0.26, rag=1.6, seed=4.4, front_drop=0.02, thick=0.014), 'sack', 0.0)
    deep_hood(P, add, 'sack', size=1.0, peak=0.02, tail=0.0, droop=0.02)
    # wrapped forearms
    for s in ('r', 'l'):
        el, wr = P['el_' + s], P['wr_' + s]
        add(Capsule(el + (wr - el) * 0.45, wr, 0.05, 0.046), 'wrap', 0.01)
    d = P['item_r']
    pts = []
    if d is not None:
        g = (hand_pos(P, 'r') + hand_pos(P, 'l')) / 2 if P.get('two_hand', True) else hand_pos(P, 'r')
        ringp = anchor(P, add, g, norm(d))
        # chain from the ring, looping down to the waist
        w = P['pelvis'] + v3(-0.12, 0.10, 0.12)
        n = 9
        for k in range(n):
            t = (k + 0.5) / n
            c = ringp * (1 - t) + w * t - v3(0, 0.25 * 4 * t * (1 - t), 0)
            ax = v3(1, 0, 0) if k % 2 else v3(0, 0, 1)
            add(Torus(c, ax, 0.026, 0.008), 'chain', 0.0)
            pts.append(c)
    # chain round the waist

    def belt(p, c=P['pelvis'] + v3(0, 0.10, 0)):
        q = p - c
        e = np.sqrt((q[:, 0] / 0.21) ** 2 + (q[:, 2] / 0.16) ** 2) - 1.0
        return np.sqrt((e * 0.16) ** 2 + q[:, 1] ** 2) - 0.02
    add(Func(belt, P['pelvis'] + v3(0, 0.10, 0), 0.3), 'chain', 0.0)
    barnacles(add, P['sh_l'] + v3(0.03, 0.05, -0.03), v3(0.4, 1, -0.3), n=6, spread=0.05, seed=13)
    drips(P, add, pts[::4] + [P['pelvis'] + v3(0.2, -0.5, 0.08)])
    puddle(P, add, r=0.36)
    mats = {
        'sack': wet_cloth(_hex('#68726b'), wet=0.6, low_dark=0.3, streak=0.15),
        'wrap': wet_cloth(LINEN_DK, wet=0.6, low_dark=0.2),
        'anchor': Material(lambda p, n: np.where((fbm(p, 16, 3) > 0.58)[:, None], np.array(_hex('#6b4a38'))[None, :],
                                                 np.array(_hex('#3c4442'))[None, :]), spec=0.5, gloss=26, metal=0.5, brush=0.1),
        'chain': Material(_hex('#3e4644'), spec=0.6, gloss=30, metal=0.6, brush=0.06),
        'skin': wet_skin(P, SKIN_DROWNED, hair=BLACK, sunken=0.5),
    }
    return tide_finish(P, parts, mats, add, pool_r=0.55)


def _post(fr):
    for row in ('move', 'hit', 'idle'):
        for P, lk in fr[row]:
            rig.place_arm(P, 'r', P['sh_r'] + v3(-0.04, 0.04, 0.16), (-1, -0.6, 0.2), l1=0.29, l2=0.28)
            rig.place_arm(P, 'l', P['sh_r'] + v3(0.06, -0.10, 0.22), (1, -0.6, -0.2), l1=0.29, l2=0.28)
    # wind-up: keep the crown inside the frame (swing it back, not straight up)
    for i, (P, lk) in enumerate(fr['attack'][:2]):
        d = [v3(-0.1, 0.12, -1.0), v3(-0.1, 0.45, -0.7)][i]
        P['item_r'] = norm(d)
        for s in ('r', 'l'):
            rig.place_arm(P, s, P['wr_' + s] + v3(0, -0.22, 0), (-1 if s == 'r' else 1, -0.3, -0.5), l1=0.29, l2=0.28)
    for P, lk in fr['cast']:
        P['two_hand'] = False
    for P, lk in fr['death']:
        P['two_hand'] = False
    return fr


ROWS, frames = tide_rows(neutral_pose, attack_style='slam', weapon_side='r', sink=0.4, post=_post)

"""Bloat-Drowned (Returning Tide, bruiser). A corpse left to swell for a season until it carries a river inside.

Hugely swollen grey-green body on short stumpy legs, a small sunk head, heavy arms hanging, tattered
rags strapped across the belly. Barnacled, solemn, not gory. Defining detail: split seams across the
belly leaking thin streams of brine.
"""
from _returning_tide_common import *
from render import Camera

UNIT_ID = 'returning_tide_bloat_drowned'
CAMERA = Camera(ppm=46)

C = Costume(top='skin', sleeve='skin', legs='skin', boot='skin', hand='skin', skin='skin',
            skirt=None, head='bald', belt=None, boots_tall=False, girth=1.6)


def neutral_pose():
    P = base_pose(height=0.98, build=1.45)
    # short stumpy legs: drop the whole upper body
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + rig.UPPER, v3(0, -0.20, 0))
    rig.place_leg(P, 'l', (0.22, 0.085, 0.10), l1=0.36, l2=0.36)
    rig.place_leg(P, 'r', (-0.22, 0.085, -0.06), l1=0.36, l2=0.36)
    rig.lean(P, fwd=np.radians(12))
    rig.shift(P, ('neck', 'head'), v3(0, -0.02, 0.09))
    P['head_pitch'] = np.radians(6)
    rig.place_arm(P, 'r', P['sh_r'] + v3(-0.14, -0.50, 0.10), (-1, 0, -0.3), l1=0.30, l2=0.29)
    rig.place_arm(P, 'l', P['sh_l'] + v3(0.14, -0.48, 0.14), (1, 0, -0.3), l1=0.30, l2=0.29)
    return P


def build(P):
    parts, add = new_parts()
    pel, ch = P['pelvis'], P['chest']
    b = P['build']
    body(P, add, C)
    # the swollen belly and chest
    fwd = norm(ch - pel)
    bc = pel + fwd * 0.20 + v3(0, -0.02, 0.13)
    sq = 1.0 + 0.03 * P['breathe'] + 0.08 * P['fx']
    add(Ellipsoid(bc, (0.32 * sq, 0.31, 0.31 * sq), basis_from(fwd, (0, 0, 1))), 'skin', 0.08)
    add(Ellipsoid(ch + v3(0, 0.02, -0.02), (0.27, 0.20, 0.20)), 'skin', 0.08)
    # thick arms
    for s in ('r', 'l'):
        sh, el, wr = P['sh_' + s], P['el_' + s], P['wr_' + s]
        add(Capsule(sh, el, 0.085, 0.072), 'skin', 0.05)
        add(Capsule(el, wr, 0.072, 0.062), 'skin', 0.04)
        d = norm(wr - el)
        add(Ellipsoid(wr + d * 0.06, (0.06, 0.07, 0.055), basis_from(d, (0, 0, 1))), 'skin', 0.02)
    # thick legs
    for s in ('r', 'l'):
        add(Capsule(P['hip_' + s], P['kn_' + s], 0.11, 0.09), 'skin', 0.04)
        add(Capsule(P['kn_' + s], P['an_' + s], 0.09, 0.075), 'skin', 0.03)
    # tattered rags: a loincloth skirt and a strap across the belly
    add(ragged_robe(P, hem=0.56, flare=0.6, top=0.86, rag=2.0, seed=10.3, droop=0.0, girth=1.7, depth=1.3), 'rags', 0.0)
    add(Capsule(P['sh_l'] + v3(-0.03, 0.04, 0.10), pel + v3(-0.22, 0.08, 0.26), 0.035), 'rags', 0.02)
    add(Capsule(P['sh_l'] + v3(-0.03, 0.04, -0.10), pel + v3(-0.20, 0.10, -0.22), 0.035), 'rags', 0.02)
    barnacles(add, P['head'] + v3(0.02, 0.08, -0.03), v3(0.2, 1, -0.4), n=5, spread=0.04, size=0.012, seed=24)
    # split seams on the belly (painted dark) leaking streams of brine
    R = basis_from(fwd, (0, 0, 1))
    leaks = []
    for k, (ax, ay) in enumerate(((0.45, 0.15), (-0.35, -0.15), (0.05, 0.35))):
        n = R @ norm(v3(np.sin(ax), ay, np.cos(ax)))
        p0 = bc + n * v3(0.32, 0.31, 0.31) * sq * 1.0
        flow = 0.10 + 0.05 * np.sin(P['tell'] * 6.28 + k * 2)
        a = p0 + n * 0.01
        m = a + n * 0.05 + v3(0, -0.08, 0)
        add(Capsule(a, m, 0.014, 0.012), 'water', 0.01)
        add(Capsule(m, m + v3(0, -flow - 0.1 * P['fx'], 0.02), 0.012, 0.007), 'water', 0.0)
        leaks.append(m + v3(0, -flow, 0.02))
    barnacles(add, P['sh_r'] + v3(-0.04, 0.06, 0.0), v3(-0.5, 1, 0), n=9, spread=0.07, size=0.016, seed=21)
    barnacles(add, bc + R @ v3(0.15, 0.1, -0.25), R @ v3(0.4, 0.2, -1), n=7, spread=0.07, size=0.015, seed=22)
    barnacles(add, P['kn_l'] + v3(0.04, 0, 0.05), v3(0.5, 0.3, 1), n=4, spread=0.03, seed=23)
    # slam splash
    if P['fx'] > 0:
        for k in range(7):
            a = k / 7 * 2 * np.pi
            c = v3(np.cos(a) * 0.32, 0.06 + 0.10 * P['fx'] * (k % 2), np.sin(a) * 0.32 + 0.35)
            add(Ellipsoid(c, (0.03, 0.07 * P['fx'], 0.03)), 'water', 0.0)
    drips(P, add, leaks + [hand_pos(P, 'r') + v3(0, -0.06, 0), hand_pos(P, 'l') + v3(0, -0.06, 0)])
    puddle(P, add, r=0.42)
    seam_dirs = [R @ norm(v3(np.sin(ax), ay, np.cos(ax))) for ax, ay in ((0.45, 0.15), (-0.35, -0.15), (0.05, 0.35))]
    base_skin = _hex('#86968a')

    def bloat_skin(p, n):
        face = tide_face(P, base_skin, BLACK, milky=True, sunken=0.6, brows=False, lips=_hex('#6c7672'))(p, n)
        q = p - bc
        r = np.linalg.norm(q, axis=1) + 1e-6
        for sd in seam_dirs:
            cosang = (q @ sd) / r
            band = (cosang > 0.93) & (np.abs(q @ np.cross(sd, v3(0, 1, 0))) < 0.012)
            face[band] = _hex('#2c3a36')
        mott = fbm(p, 9, 2)[:, None]
        on_body = (p[:, 1] < P['neck'][1] - 0.05)[:, None]
        return np.where(on_body, face * (0.9 + 0.2 * mott) * np.array([0.97, 1.0, 1.0]), face)
    mats = {
        'skin': Material(bloat_skin, spec=0.45, gloss=36, sss=0.35, brush=0.05),
        'rags': wet_cloth(_hex('#3c5a4a'), wet=0.8, low_dark=0.2, streak=0.2, top=1.4),
    }
    return tide_finish(P, parts, mats, add, pool_r=0.62)


ROWS, frames = tide_rows(neutral_pose, attack_style='slam', weapon_side='r', sink=0.3)

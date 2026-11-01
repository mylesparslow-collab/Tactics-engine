"""Tide-Prophet (Returning Tide, exotic). The one who heard the sea above and told the faithful where it went.

A head taller than the crowd, arms spread, hood thrown back, layered black-green wet robes over barnacle
mail, a long hooked staff, a pool spreading at her feet. Defining detail: a sheet of water arcing
behind her shoulders and a halo of water drops hanging in the air, with rain falling only on her.
"""
from _returning_tide_common import *
from render import Camera

UNIT_ID = 'returning_tide_tide_prophet'
CAMERA = Camera(ppm=46)

C = Costume(top='mail', sleeve='robe', legs='robe', boot='skin', hand='skin', skin='skin',
            skirt=None, head='bald', belt=None, boots_tall=False, girth=1.0)


def neutral_pose():
    P = base_pose(height=1.13, build=0.98)
    rig.lean(P, fwd=np.radians(-4))
    P['head_pitch'] = np.radians(-14)
    h = 1.13
    rig.place_arm(P, 'r', v3(-0.52, 1.62, 0.10), (-0.3, -1, -0.3), l1=0.30, l2=0.29)
    rig.place_arm(P, 'l', v3(0.54, 1.66, 0.08), (0.3, -1, -0.3), l1=0.30, l2=0.29)
    P['item_r'] = norm(v3(-0.05, 1.0, 0.1))
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    wet_hair(P, add, 'hair', style='long')
    h = P['height']
    add(ragged_robe(P, hem=0.02, flare=1.0, top=1.02, rag=1.2, seed=11.4, droop=0.10), 'robe', 0.0)
    add(ragged_robe(P, hem=0.38, flare=0.8, top=1.04, rag=1.6, seed=3.4, droop=0.08, opening=0.4, girth=1.1), 'black', 0.0)
    add(shawl(P, depth=0.22, width=0.21, rag=1.2, seed=6.6, front_drop=0.04), 'black', 0.0)
    hood_down(P, add, 'robe', size=1.0)
    for s in ('r', 'l'):
        sleeve_flare(P, add, s, 'robe', length=0.16, width=0.075)
    # barnacle mail across the chest
    ch = P['chest']
    for i in range(4):
        for j in range(5):
            c = ch + v3(-0.10 + j * 0.05, 0.10 - i * 0.07, 0.10 - abs(j - 2) * 0.012)
            add(Sphere(c, 0.019), 'barnacle', 0.0)
    # long hooked staff
    r = held(P, add, 'r', 'hook', shaft='driftwood', head='driftwood', below=1.0 * 1.1, above=0.5)
    # the sheet of water arcing behind the shoulders, from hand to hand
    hr, hl = hand_pos(P, 'r'), hand_pos(P, 'l')
    cg = P['cast_glow']
    mid = (hr + hl) / 2 + v3(0, 0.18 + 0.06 * cg, -0.22)

    prev = None
    n = 16
    for k in range(n + 1):
        t = k / n
        c = (1 - t) ** 2 * hr + 2 * t * (1 - t) * mid + t * t * hl
        c = c + v3(0, 0.012 * np.sin(t * 18 + P['tell'] * 6.28), 0)
        if prev is not None:
            rr = 0.020 + 0.016 * np.sin(np.pi * t)
            add(Capsule(prev, c, rr), 'water', 0.02)
        prev = c
    # halo of drops around the head, slowly turning
    H = P['head']
    ph = P['tell'] + cg * 0.5
    for k in range(9):
        a = k / 9 * 2 * np.pi + ph * 2 * np.pi / 9
        c = H + v3(np.cos(a) * 0.19, 0.13 + 0.025 * np.sin(a * 2 + ph * 6.28), np.sin(a) * 0.19 - 0.03)
        add(Ellipsoid(c, (0.012, 0.018, 0.012)), 'drip', 0.0)
    rain(add, H + v3(0, 0.30, 0.05), w=0.30, n=10, length=0.10, phase=P['tell'], top=0.0, bottom=-1.9, seed=8)
    drips(P, add, [hr + v3(0, -0.08, 0), hl + v3(0, -0.08, 0)])
    puddle(P, add, r=0.46)
    ripples(P, add, n=2, r0=0.36)
    mats = {
        'robe': wet_cloth(_hex('#3f7a5c'), wet=0.8, low_dark=0.35),
        'black': wet_cloth(_hex('#1d2522'), wet=0.9, low_dark=0.0),
        'mail': wet_cloth(GREY_DK, wet=0.6),
        'hair': Material(_hex('#d8d6c8'), spec=0.7, gloss=40, brush=0.06),
        'driftwood': Material(_hex('#6e6252'), spec=0.2, gloss=18, brush=0.12),
        'skin': wet_skin(P, SKIN_PALE, hair=_hex('#b8b6a8'), mouth=0.3),
        'water': Material(GLINT, spec=1.2, gloss=70, emissive=tuple(np.array(BRINE) * (0.45 + 0.5 * cg)), brush=0.0),
    }
    return tide_finish(P, parts, mats, add, pool_r=0.6)


def _post(fr):
    # keep both arms spread while walking (the arc stays up)
    for i, (P, lk) in enumerate(fr['move']):
        rig.place_arm(P, 'l', P['sh_l'] + v3(0.36, 0.18 + 0.02 * (i % 2), 0.10), (0.3, -1, -0.3), l1=0.30, l2=0.29)
    return fr


ROWS, frames = tide_rows(neutral_pose, attack_style='swing', weapon_side='r', cast_side='l', post=_post)

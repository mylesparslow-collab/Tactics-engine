"""Sister Maren Ketch, Matron of the Dry Hands (Returning Tide hero).

Senior wringer: tall and stern, hood thrown back, hair in a tight bun, layered black and drowned-green
robes, black gloves with a gold cord at each wrist. Defining details: a taut rope of water twisting
between her hands at chest height, and a belt of stoppered flasks with gold stoppers.
"""
from _returning_tide_common import *

UNIT_ID = 'returning_tide_maren_ketch'

C = Costume(top='robe', sleeve='sleeve', legs='robe', boot='boot', hand='glove', skin='skin',
            skirt=None, head='bald', belt='leather', boots_tall=False, girth=0.95)


def neutral_pose():
    P = base_pose(height=1.08, build=0.95)
    rig.place_leg(P, 'l', (0.17, 0.085, 0.10))
    rig.place_leg(P, 'r', (-0.15, 0.085, -0.05))
    rig.lean(P, fwd=np.radians(2))
    P['head_pitch'] = np.radians(4)
    P['head_yaw'] = np.radians(-16)
    rig.place_arm(P, 'r', v3(-0.34, 1.26, 0.22), (-1, -0.6, -0.2), l1=0.29, l2=0.28)
    rig.place_arm(P, 'l', v3(0.30, 1.30, 0.26), (1, -0.6, -0.2), l1=0.29, l2=0.28)
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    wet_hair(P, add, 'hair', style='bun')
    add(ragged_robe(P, hem=0.02, flare=0.85, rag=0.9, seed=12.5, droop=0.08), 'black', 0.0)
    add(ragged_robe(P, hem=0.30, flare=0.75, top=1.04, rag=1.4, seed=2.5, droop=0.06, opening=0.45, girth=1.08), 'robe', 0.0)
    add(shawl(P, depth=0.18, width=0.20, rag=1.0, seed=7.1, front_drop=0.04), 'robe', 0.0)
    hood_down(P, add, 'black', size=0.95)
    for s in ('r', 'l'):
        sleeve_flare(P, add, s, 'sleeve', length=0.08, width=0.07)
    # gold cords at the wrists
    for s in ('r', 'l'):
        el, wr = P['el_' + s], P['wr_' + s]
        d = norm(wr - el)
        add(Torus(wr - d * 0.01, d, 0.044, 0.007), 'gold', 0.0)
    # belt of stoppered flasks
    pel = P['pelvis']
    for k, a in enumerate(np.radians([-110, -70, -35, 25, 60, 100])):
        c = pel + v3(np.sin(a) * 0.20, 0.04, np.cos(a) * 0.165)
        add(Ellipsoid(c + v3(0, -0.04, 0), (0.036, 0.052, 0.036)), 'flask', 0.0)
        add(Capsule(c, c + v3(0, 0.025, 0), 0.012), 'flask', 0.0)
        add(Sphere(c + v3(0, 0.032, 0), 0.013), 'gold', 0.0)
    # taut twisting rope of water between her hands
    a, b = hand_pos(P, 'r'), hand_pos(P, 'l')
    if np.linalg.norm(b - a) > 0.1:
        water_rope(add, a, b, phase=P['tell'] * 2 + P['cast_glow'], r=0.019, amp=0.026, twist=2.5, n=10, sag=0.02)
    drips(P, add, [(a + b) / 2 + v3(0, -0.03, 0), a + v3(0, -0.04, 0), pel + v3(0.2, -0.88, 0.04)])
    puddle(P, add, r=0.30)
    mats = {
        'robe': wet_cloth(_hex('#3f7a5c'), wet=0.8, low_dark=0.35),
        'black': wet_cloth(_hex('#1c2220'), wet=0.9, low_dark=0.0),
        'sleeve': wet_cloth(_hex('#2c4a3c'), wet=0.8, low_dark=0.0),
        'glove': Material(_hex('#16191a'), spec=0.6, gloss=40, brush=0.03),
        'hair': Material(_hex('#4a4a44'), spec=0.7, gloss=40, brush=0.06),
        'flask': Material(_hex('#5f7a6c'), spec=1.0, gloss=60, emissive=tuple(np.array(BRINE) * 0.2), brush=0.02),
        'skin': wet_skin(P, _hex('#cfb19a'), hair=_hex('#4a4a44'), lips=_hex('#7a5450')),
        'water': Material(GLINT, spec=1.2, gloss=70, emissive=tuple(np.array(BRINE) * (0.4 + 0.5 * P['cast_glow'])), brush=0.0),
    }
    return tide_finish(P, parts, mats, add)


ROWS, frames = tide_rows(neutral_pose, attack_style='cast', weapon_side='r', cast_side='l')

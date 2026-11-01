"""Drowned (Returning Tide, cheap body). One of the faithful dead, kept wet so it keeps walking.

Shambling forward lean, one hand reaching to grasp, a rusted blade held low. Tattered drowned-green
rags and a torn cowl, pale grey-green skin with milky eyes (solemn, not gory). Barnacles crust the
shoulder and the blade. Defining detail: kelp strands trailing from both arms.
"""
from _returning_tide_common import *

UNIT_ID = 'returning_tide_drowned'

C = Costume(top='rags', sleeve='skin', legs='skin', boot='skin', hand='skin', skin='skin',
            skirt=None, head='bald', belt=None, boots_tall=False, girth=0.95)


def neutral_pose():
    P = base_pose(height=0.98, build=0.98)
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + rig.UPPER, v3(0, -0.04, 0))
    rig.place_leg(P, 'l', (0.14, 0.085, 0.12), l1=0.43, l2=0.42)
    rig.place_leg(P, 'r', (-0.12, 0.085, -0.08), l1=0.43, l2=0.42)
    rig.lean(P, fwd=np.radians(16), side=np.radians(-4))
    P['head_pitch'] = np.radians(4)
    P['head_yaw'] = np.radians(-14)
    rig.place_arm(P, 'l', v3(0.20, 1.12, 0.40), (0.6, -0.5, -0.4))
    rig.place_arm(P, 'r', v3(-0.27, 0.86, 0.12), (-0.4, 0, -1))
    P['item_r'] = norm(v3(-0.15, -0.55, 0.8))
    return P


def build(P):
    parts, add = new_parts()
    body(P, add, C)
    add(ragged_robe(P, hem=0.36, flare=0.45, top=1.06, rag=2.0, seed=2.1, droop=0.06, girth=0.95), 'rags', 0.0)
    deep_hood(P, add, 'rags', size=1.06, peak=0.03, tail=0.12, droop=0.04)
    # tattered short sleeves
    for s in ('r', 'l'):
        sx = -1 if s == 'r' else 1
        sh, el = P['sh_' + s], P['el_' + s]
        add(Capsule(sh + v3(-sx * 0.02, -0.03, 0), sh + (el - sh) * 0.7, 0.068, 0.062), 'rags', 0.03)
    _, tip = held(P, add, 'r', 'blade', head='rust') or (None, None)
    # kelp strands hanging from both forearms
    sway = P['skirt_sway']
    ends = []
    for s, seed in (('r', 1), ('l', 2)):
        el, wr = P['el_' + s], P['wr_' + s]
        for k, t in enumerate((0.25, 0.6)):
            a = el + (wr - el) * t
            ends += rag_strips(add, a, 2, 0.30, 'kelp', spread=0.02, seed=seed * 7 + k, sway=sway, r=0.017)
    # barnacles: right shoulder, back of the cowl, along the blade
    barnacles(add, P['sh_r'] + v3(-0.02, 0.04, -0.02), v3(-0.6, 1, -0.2), n=7, spread=0.045, seed=4)
    barnacles(add, P['chest'] + v3(0.06, 0.10, -0.11), v3(0.2, 0.3, -1), n=5, spread=0.05, seed=5)
    if tip is not None:
        g = hand_pos(P, 'r')
        barnacles(add, g + (tip - g) * 0.6, v3(0, 1, 0), n=3, spread=0.02, size=0.010, seed=6)
    drips(P, add, ends[::2] + [P['wr_l'] + v3(0, -0.06, 0)])
    puddle(P, add, r=0.28)
    mats = {
        'rags': wet_cloth(_hex('#527a64'), wet=0.8, low_dark=0.32, streak=0.18),
        'steel': Material(_hex('#7a5a46'), spec=0.4, gloss=20, metal=0.3, brush=0.15),
        'skin': wet_skin(P, SKIN_DROWNED, hair=_hex('#3c4640'), milky=True, sunken=0.7, brows=False,
                         lips=_hex('#6c7672')),
    }
    return tide_finish(P, parts, mats, add)


ROWS, frames = tide_rows(neutral_pose, attack_style='swing', weapon_side='r', sink=0.4)

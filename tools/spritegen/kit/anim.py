"""Standard animation rows for kit humanoids (and a simple set for creatures).

    ROWS, frames = humanoid_rows(neutral_pose, attack='swing', weapon_side='r')

attack styles:
  swing   one-handed cut with the item in weapon_side hand (blade, club, axe, hammer, hook)
  thrust  two-handed spear/pike/long-weapon jab forward
  shoot   raise and aim the item (gun, sling, lens, thrown), recoil on the hit frame with P['fx'] = 1
  slam    two-handed overhead smash into the ground
  cast    raise the free hand, flare P['cast_glow']; use for healers/casters with no weapon
cast row is always a raise-glow-release on the free hand (or both hands when no item).
death rows: stagger, kneel, slump, end state (P['end'] 0 -> 1; P['sink'] for sinking factions).

Each frame is (pose dict, look overrides). Units can post-process: frames = tweak(frames) etc.
"""
import numpy as np
from sdf import v3, norm
import rig

ROWS = [
    ('idle', 4, True, {}),
    ('move', 8, True, {}),
    ('attack', 10, False, {'hitFrame': 2}),
    ('hit', 10, False, {}),
    ('death', 6, False, {'holdLast': True}),
    ('cast', 8, False, {}),
]

UPPER_ALL = rig.UPPER


def _scale(P, x, y, z):
    return v3(x * P['build'], y * P['height'], z)


def idle(base, i):
    P = base()
    b = [0.0, 1.0, 0.0, -1.0][i]
    P['breathe'] = b
    rig.shift(P, ('chest', 'neck', 'head', 'sh_r', 'sh_l', 'el_r', 'el_l'), v3(0, 0.006 * b, 0))
    P['tell'] = i / 4.0
    P['glow'] = P['glow'] * [1.0, 0.88, 1.08, 0.94][i]
    P['skirt_sway'] = 0.12 * b
    P['head_yaw'] = P['head_yaw'] + np.radians([0, 2, 3, 1][i])
    return P, {}


def walk(base, i, carry=True):
    P = base()
    h = P['height']
    stride = 0.17 * h
    xr, xl = P['an_r'][0], P['an_l'][0]
    keys = [
        dict(l=(xl, 0.085, 0.07 + stride), r=(xr, 0.085, -0.05 - stride * 0.6), dy=-0.025),
        dict(l=(xl, 0.085, 0.02), r=(xr, 0.17, 0.05), dy=0.01),
        dict(l=(xl, 0.085, 0.02 - stride * 0.8), r=(xr, 0.085, 0.05 + stride), dy=-0.025),
        dict(l=(xl, 0.17, 0.10), r=(xr, 0.085, 0.0), dy=0.01),
    ][i]
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + UPPER_ALL, v3(0, keys['dy'] * h, 0.03))
    rig.place_leg(P, 'l', keys['l'], l1=0.43 * h, l2=0.42 * h)
    rig.place_leg(P, 'r', keys['r'], l1=0.43 * h, l2=0.42 * h)
    rig.lean(P, fwd=np.radians(4))
    sw = [1, 0, -1, 0][i]
    # arms swing opposite the legs unless they hold something two-handed
    for s, sg in (('r', -1), ('l', 1)):
        if P['item_' + s] is None:
            sh = P['sh_' + s]
            rig.place_arm(P, s, sh + v3((-0.04 if s == 'r' else 0.04) * P['build'], -0.48 * h, 0.07 * sw * sg),
                          (-1 if s == 'r' else 1, 0, -1), l1=0.27 * h, l2=0.26 * h)
        else:
            rig.shift(P, ('el_' + s, 'wr_' + s), v3(0, 0.01 * abs(sw), 0.03 * sw * sg))
    P['skirt_sway'] = 0.7 * sw
    P['tell'] = i / 4.0
    return P, {}


def attack(base, i, style='swing', side='r'):
    P = base()
    h = P['height']
    o = 'l' if side == 'r' else 'r'
    sx = -1 if side == 'r' else 1
    step = [0.0, 0.05, 0.12, 0.06][i]
    lean_deg = [-5, 3, 12, 5][i]
    d = v3(0, -0.02 * (step > 0.1), step * 0.5)
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + UPPER_ALL, d)
    rig.place_leg(P, 'l', (P['an_l'][0], 0.085, P['an_l'][2] + step * 1.4), l1=0.43 * h, l2=0.42 * h)
    rig.place_leg(P, 'r', (P['an_r'][0], 0.085, P['an_r'][2] - 0.02), l1=0.43 * h, l2=0.42 * h)
    rig.lean(P, fwd=np.radians(lean_deg))
    S = lambda x, y, z: _scale(P, x, y, z) + d
    if style == 'swing':
        w = [S(sx * 0.20, 1.62, -0.10), S(sx * 0.12, 1.52, 0.18), S(sx * 0.02, 1.08, 0.40), S(sx * 0.14, 1.04, 0.24)][i]
        dirs = [v3(-sx * 0.15, 0.55, -0.8), v3(-sx * 0.25, 0.85, 0.45), v3(-sx * 0.35, -0.35, 0.85), v3(-sx * 0.15, -0.6, 0.75)][i]
        rig.place_arm(P, side, w, (sx, -0.3, -0.4), l1=0.27 * h, l2=0.26 * h)
        P['item_' + side] = dirs
    elif style == 'thrust':
        lo = [S(sx * 0.10, 1.05, -0.10), S(sx * 0.08, 1.10, 0.0), S(sx * 0.02, 1.12, 0.30), S(sx * 0.06, 1.08, 0.12)][i]
        fwd = norm(v3(-sx * 0.15, [0.25, 0.15, 0.02, 0.1][i], 1.0))
        hi = lo + fwd * 0.30
        rig.place_arm(P, side, lo, (sx, -0.5, -0.3), l1=0.27 * h, l2=0.26 * h)
        rig.place_arm(P, o, hi, (-sx, -0.6, -0.2), l1=0.27 * h, l2=0.26 * h)
        P['item_' + side] = fwd
        P['item_' + o] = None
    elif style == 'shoot':
        aim = norm(v3(-sx * 0.25, [0.10, 0.04, 0.10, -0.2][i], 1.0))
        g = [S(sx * 0.16, 1.25, 0.18), S(sx * 0.10, 1.32, 0.30), S(sx * 0.10, 1.36, 0.22), S(sx * 0.16, 1.15, 0.16)][i]
        rig.place_arm(P, side, g, (sx, -0.6, -0.2), l1=0.27 * h, l2=0.26 * h)
        if P['item_' + o] is None:
            rig.place_arm(P, o, g + aim * 0.22 + v3(0, -0.03, 0), (-sx, -0.6, -0.2), l1=0.27 * h, l2=0.26 * h)
        P['item_' + side] = aim
        P['fx'] = [0, 0, 1, 0.2][i]
        lean_extra = [0, 0, -6, -2][i]
        rig.lean(P, fwd=np.radians(lean_extra))
    elif style == 'slam':
        up = [S(sx * 0.05, 1.75, -0.12), S(sx * 0.02, 1.80, 0.05), S(sx * 0.02, 0.95, 0.42), S(sx * 0.05, 1.05, 0.30)][i]
        dirs = [v3(0, 0.5, -0.8), v3(0, 1, 0.3), v3(0, -0.5, 0.85), v3(0, -0.7, 0.6)][i]
        rig.place_arm(P, side, up, (sx, -0.2, -0.5), l1=0.27 * h, l2=0.26 * h)
        rig.place_arm(P, o, up + norm(dirs) * 0.12, (-sx, -0.2, -0.5), l1=0.27 * h, l2=0.26 * h)
        P['item_' + side] = dirs
        P['item_' + o] = None
        P['fx'] = [0, 0, 1, 0][i]
    elif style == 'cast':
        g = [S(sx * 0.22, 1.25, 0.12), S(sx * 0.18, 1.55, 0.22), S(sx * 0.10, 1.35, 0.42), S(sx * 0.2, 1.1, 0.2)][i]
        rig.place_arm(P, side, g, (sx, -0.5, -0.4), l1=0.27 * h, l2=0.26 * h)
        P['cast_glow'] = [0.3, 0.7, 1.0, 0.2][i]
    P['head_pitch'] = np.radians([-6, 0, 8, 2][i])
    P['skirt_sway'] = [0.2, 0.0, -0.4, -0.2][i]
    return P, {}


def hit(base, i):
    P = base()
    rig.lean(P, fwd=np.radians([-11, -4][i]))
    P['head_pitch'] = np.radians([10, 3][i])
    P['skirt_sway'] = [0.3, 0.1][i]
    return P, (dict(exposure=1.25, flash=0.22) if i == 0 else {})


def kneel(P, depth):
    h = P['height']
    py = (0.94 - 0.36 * depth) * h
    d = v3(0, py - P['pelvis'][1], -0.03 * depth)
    rig.shift(P, ('pelvis', 'hip_r', 'hip_l') + UPPER_ALL, d)
    rig.place_leg(P, 'l', (P['an_l'][0], 0.085, 0.07 + 0.25 * depth), l1=0.43 * h, l2=0.42 * h)
    rig.place_leg(P, 'r', (P['an_r'][0], 0.085, -0.02 - 0.32 * depth), l1=0.43 * h, l2=0.42 * h,
                  pole=(0, -0.2 * depth, 1))
    if depth > 0.7:
        P['kn_r'] = v3(P['an_r'][0], 0.075, 0.10)
        P['an_r'] = v3(P['an_r'][0], 0.08, -0.32 * h)


def death(base, i, sink_depth=0.0):
    """stagger / kneel / slump / end state. sink_depth > 0 sinks the body into the ground at the end."""
    P = base()
    h = P['height']
    if i == 0:
        rig.lean(P, fwd=np.radians(-12))
        P['head_pitch'] = np.radians(16)
        P['glow'] *= 0.8
        return P, {}
    depth = [0, 0.75, 1.0, 1.0][i]
    kneel(P, depth)
    rig.lean(P, fwd=np.radians([0, 14, 24, 24][i]))
    for s in ('r', 'l'):
        sx = -1 if s == 'r' else 1
        if P['item_' + s] is not None:
            P['item_' + s] = norm(v3(sx * 0.3, -0.6, 0.6))   # weapon droops toward the ground
        rig.place_arm(P, s, P['pelvis'] + v3(sx * 0.17 * P['build'], (0.0 if i == 1 else -0.08) * h, 0.16),
                      (sx, 0, -0.5), l1=0.27 * h, l2=0.26 * h)
    P['head_pitch'] = np.radians([0, 18, 34, 34][i])
    P['glow'] *= [1, 0.6, 0.3, 0.0][i]
    P['end'] = [0, 0.15, 0.5, 1.0][i]
    P['sink'] = [0, 0, 0.25, 1.0][i] * sink_depth
    return P, {}


def cast(base, i, side='l'):
    P = base()
    h = P['height']
    sx = -1 if side == 'r' else 1
    sides = [side] if P['item_' + side] is None else []
    if not sides:
        side = 'r' if side == 'l' else 'l'
        sx = -sx
        sides = [side] if P['item_' + side] is None else []
    for s in sides:
        g = [v3(sx * 0.24, 1.20, 0.14), v3(sx * 0.22, 1.62, 0.20), v3(sx * 0.15, 1.30, 0.40)][i]
        rig.place_arm(P, s, v3(g[0] * P['build'], g[1] * h, g[2]), (sx, -0.6, -0.3), l1=0.27 * h, l2=0.26 * h)
    rig.lean(P, fwd=np.radians([-3, -6, 4][i]))
    P['head_pitch'] = np.radians([-6, -12, 2][i])
    P['cast_glow'] = [0.5, 1.0, 0.4][i]
    P['glow'] *= [1.3, 2.0, 1.3][i]
    P['skirt_sway'] = [0.2, 0.4, -0.2][i]
    return P, {}


def humanoid_rows(base, attack_style='swing', weapon_side='r', sink_depth=0.0, cast_side='l'):
    """Return (ROWS, frames) for a kit humanoid. base() must return a fresh neutral pose."""
    def frames():
        return {
            'idle': [idle(base, i) for i in range(4)],
            'move': [walk(base, i) for i in range(4)],
            'attack': [attack(base, i, attack_style, weapon_side) for i in range(4)],
            'hit': [hit(base, i) for i in range(2)],
            'death': [death(base, i, sink_depth) for i in range(4)],
            'cast': [cast(base, i, cast_side) for i in range(3)],
        }
    return ROWS, frames


# ------------------------------------------------------------------ creatures
# For non-humanoids: the unit's pose is a dict of scalars its build() reads. These helpers give the
# standard timing; the unit maps them onto its own parts (legs, tentacles, tracks, bell, fronds...).

def creature_frames(base, overrides=None):
    """Generic scalar channels per row/frame:
       bob (vertical offset m), lean (rad, + = forward), squash (y scale), stride (-1..1 gait phase),
       strike (0..1 reach), glow, cast_glow, fx, end (0..1), sink (m), flash (look override)."""
    def mk(i, **kw):
        P = base()
        P.update(kw)
        return P
    rows = {
        'idle': [(mk(i, bob=[0, .01, 0, -.01][i], squash=[1, 1.02, 1, 0.98][i], tell=i / 4,
                     glow=[1, .88, 1.08, .94][i]), {}) for i in range(4)],
        'move': [(mk(i, bob=[0, .03, 0, .03][i], stride=[1, 0, -1, 0][i], lean=0.06, tell=i / 4), {}) for i in range(4)],
        'attack': [(mk(i, lean=[-.12, .05, .25, .08][i], strike=[0, .4, 1, .3][i], squash=[.94, 1.04, 1.0, 1][i],
                       fx=[0, 0, 1, .2][i]), {}) for i in range(4)],
        'hit': [(mk(0, lean=-.18, squash=.95), dict(exposure=1.25, flash=0.22)), (mk(1, lean=-.06), {})],
        'death': [(mk(i, lean=[-.15, .1, .25, .25][i], squash=[1, .9, .75, .7][i], glow=[.8, .5, .2, 0][i],
                      end=[0, .15, .5, 1][i]), {}) for i in range(4)],
        'cast': [(mk(i, cast_glow=[.5, 1, .4][i], glow=[1.3, 2, 1.3][i], bob=[.01, .03, 0][i],
                     squash=[1.02, 1.05, .98][i]), {}) for i in range(3)],
    }
    if overrides:
        rows = overrides(rows)
    return lambda: rows


CREATURE_DEFAULTS = dict(bob=0.0, lean=0.0, squash=1.0, stride=0.0, strike=0.0, tell=0.0, glow=1.0,
                         cast_glow=0.0, fx=0.0, end=0.0, sink=0.0)

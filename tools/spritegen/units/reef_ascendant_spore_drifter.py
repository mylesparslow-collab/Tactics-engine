"""Spore Drifter (Reef Ascendant, flier drone). A drifting coral jelly: a fluted pink-calcite bell with a small
branching coral crest on top, a ruffled flesh skirt, and a trailing curtain of tendrils tipped with spore beads.
Defining detail: the glowing spore pores and the hanging tendrils; it hovers. Tell: the bell pulses, spores rise."""
from _reef_ascendant_common import *

UNIT_ID = 'reef_ascendant_spore_drifter'
HOVER = 0.62


def neutral_pose():
    return base()


def build(P):
    parts, add = new_parts()
    st, tw = P['strike'], P['twitch']
    ph = 2 * np.pi * P['tell']
    pulse = 1.0 + 0.06 * np.sin(ph) - 0.07 * st
    cy = HOVER + 0.30
    R = 0.34 * pulse
    H = 0.26 * (2 - pulse)

    def bell(p):
        q = p - v3(0, cy, 0)
        th = np.arctan2(q[:, 0], q[:, 2])
        fl = 1.0 - 0.16 * (0.5 - 0.5 * np.cos(10 * th)) ** 1.2
        d = (np.linalg.norm(q / v3(R, H, R), axis=1) - fl) * 0.30
        return smax(d, -q[:, 1] - 0.02, 0.03)
    add(Func(bell, v3(0, cy, 0), R + 0.3), 'bell', 0.0)
    # scalloped rim of lappets
    for i in range(12):
        a = 2 * np.pi * i / 12
        add(Sphere(v3(np.cos(a) * R * 0.97, cy - 0.03 + 0.01 * np.sin(ph + i), np.sin(a) * R * 0.97), 0.045), 'flesh', 0.03)
    # calcite ribs running over the bell
    for i in range(6):
        a = 2 * np.pi * i / 6 + 0.3
        pts = [v3(np.cos(a) * R * 0.99, cy - 0.02, np.sin(a) * R * 0.99), v3(np.cos(a) * R * 0.85, cy + H * 0.55, np.sin(a) * R * 0.85),
               v3(np.cos(a) * R * 0.35, cy + H * 0.97, np.sin(a) * R * 0.35)]
        chain(add, bez(*pts, n=5), 0.03, 0.016, 'calcite_p', k=0.01)
    # little branching crest on top
    rng = np.random.default_rng(4)
    branches(add, v3(0, cy + H * 0.9, 0), (0, 1, 0), 0.14, 0.03, 3, 'coral', rng, spread=0.7, kids=(2, 3),
             sway=(0.05 * np.sin(ph), 0.03 * np.cos(ph)), tip=lambda a, e, d, r: a(Sphere(e, r * 1.3), 'glow', 0.0))
    # oral frills + inner glow
    for i in range(4):
        a = np.pi / 4 + i * np.pi / 2
        pts = [v3(0, cy - 0.02, 0), v3(np.cos(a) * 0.09, cy - 0.15, np.sin(a) * 0.09),
               v3(np.cos(a) * 0.12 + 0.03 * np.sin(ph + i), cy - 0.30, np.sin(a) * 0.12)]
        chain(add, pts, 0.034, 0.012, 'flesh', k=0.02)
    add(Sphere(v3(0, cy + 0.05, 0.0), 0.10), 'glow', 0.0) if False else None
    # tendrils: long, trailing, beaded
    tips = []
    for k in range(9):
        a = 2 * np.pi * k / 9 + 0.2
        rx, rz = np.cos(a) * R * 0.88, np.sin(a) * R * 0.88
        L = 0.62 + 0.18 * np.sin(k * 2.1) + (0.12 if k % 3 == 0 else 0)
        pts = []
        for j in range(5):
            h = j / 4
            sw = 0.09 * h * np.sin(ph - h * 3 + k * 1.3)
            pts.append(v3(rx * (1 - 0.35 * h) + sw, cy - 0.04 - L * h * (1 - 0.1 * st), rz * (1 - 0.35 * h) + sw * 0.5))
        chain(add, pts, 0.017, 0.005, 'flesh' if k % 2 else 'coral', k=0.004)
        for j in (2, 4):
            add(Sphere(pts[j], 0.024 if j == 4 else 0.017), 'glow', 0.0)
        tips.append(pts[-1])
    # drifting spores
    for i in range(5):
        t = (P['tell'] + i * 0.21) % 1.0
        a = i * 2.4
        add(Sphere(v3(np.cos(a) * 0.5 * (0.5 + t), cy - 0.1 + 0.9 * t, np.sin(a) * 0.5 * (0.5 + t)), 0.022 * (1 - 0.5 * t)), 'glow', 0.0)
    for k in range(len(parts)):
        pass
    parts = transform_parts(parts, t=(0, P['bob'] * 1.2, 0))
    parts = transform_parts(parts, R=rot_x(P['lean'] * 0.5) @ rot_z(P.get('topple', 0.0)), pivot=(0, cy, 0))
    m = reef_mats(P, glow=0.8)
    m['bell'] = pore_glow_mat(P, flesh_mat(col=_hex('#f6aa9c'), inner=CORAL).albedo, k=1.0, freq=48.0, thresh=0.7)
    b0 = m['bell'].albedo
    def stripe(p, n, b0=b0, cy=cy):
        a = b0(p, n)
        th = np.arctan2(p[:, 0], p[:, 2])
        t = (0.5 - 0.5 * np.cos(10 * th))[:, None] ** 2
        a = a * (1 - t * 0.55) + np.array(CORAL)[None, :] * t * 0.55
        return a
    m['bell'].albedo = stripe
    m['bell'].sss = 0.6
    m['flesh'] = flesh_mat(col=_hex('#f59a8c'), inner=CORAL, P=P, glow=0.7)
    return finish(P, FACTION, parts, m)


def _extra(rows):
    for P, o in rows['death']:
        P['bob'] = -P['sink'] * 0 - HOVER * P['end'] * 0.9


ROWS, frames = reef_rows(neutral_pose, sink=0.05, extra=_extra)

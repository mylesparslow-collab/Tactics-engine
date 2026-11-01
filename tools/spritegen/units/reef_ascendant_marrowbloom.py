"""Marrowbloom, the Slow Hunger of the Shelf (Reef Ascendant hero). A colony woken in a mass grave of
wrecks: an old ribcage of bone and a rusted hull plate, overgrown with coral, and rising out of it a
thick neck carrying a maw-flower of fleshy petals ringed with calcite teeth. The maw gapes and bites on
the attack; the petals breathe in idle."""
from _reef_ascendant_common import *
from render import Camera

UNIT_ID = 'reef_ascendant_marrowbloom'
CAMERA = Camera(ppm=48)


def neutral_pose():
    return base()


def build(P):
    parts, add = new_parts()
    rng = np.random.default_rng(61)
    st, op = P['strike'], P['open']
    sw = wave(P, 0.0, strike=0.0)
    # wreck: a keel/spine on the ground and arching ribs
    add(Capsule(v3(0, 0.05, -0.45), v3(0, 0.06, 0.35), 0.05, 0.04), 'bone', 0.0)
    for i, z in enumerate(np.linspace(-0.35, 0.25, 5)):
        h = 0.55 - 0.08 * abs(z + 0.05) * 3
        for s in (-1, 1):
            pts = bez(v3(0.03 * s, 0.07, z), v3(0.55 * s, 0.12 + h * 0.4, z), v3(0.3 * s, h + 0.05, z - 0.04), n=4)
            chain(add, pts, 0.032, 0.018, 'bone', k=0.01)
            # coral overgrowth lumps on the ribs
            add(ribbed(pts[2] + v3(0.02 * s, 0.0, 0), (0.06, 0.05, 0.06), n=8, depth=0.008), 'coral', 0.03)
    # rusted hull plate leaning on the ribs
    add(RoundBox(v3(-0.42, 0.25, -0.15), (0.03, 0.22, 0.2), 0.01, rot_z(0.45) @ rot_y(0.2)), 'scrap', 0.0)
    ground_root(add, v3(0, 0.05, 0), 8, 0.6, 0.04, 'coral', rng, k=0.02)
    # the neck: thick fluted flesh-coral rising from inside the ribs, arching forward
    a = v3(0, 0.08, -0.1)
    head = v3(0.03 * sw, 1.02 + 0.03 * np.sin(6.28 * P['tell']) - 0.25 * st, 0.12 + 0.45 * st)
    pts = bez(a, v3(0, 0.75, -0.25), head, n=6)
    chain(add, pts, 0.15, 0.1, 'neck', k=0.05)
    for i in (2, 3, 4):
        d = norm(pts[i + 1] - pts[i - 1])
        add(Torus(pts[i], d, 0.135 - 0.01 * i, 0.022), 'calcite_b', 0.02)
    # maw-flower: petal ring, teeth ring, dark throat; faces forward and down
    fwd = norm(pts[-1] - pts[-2] + v3(0, 0, 0.25))
    Rm = basis_from(fwd)
    gap = 0.4 + 0.6 * max(op, P['cast_glow'])
    add(crown(head, 9, 0.1, 0.27 + 0.06 * gap, 0.04 + 0.12 * gap, 0.065, 0.016, R=Rm, curl=0.02 + 0.06 * (1 - gap),
              sway=lambda i: (0.02 * np.sin(i * 1.3 + 6.28 * P['tell']), 0.0, 0.0), tangential=0.0), 'petal', 0.03)
    add(crown(head + fwd * 0.03, 12, 0.08, 0.04 + 0.03 * gap, 0.06, 0.013, 0.002, R=Rm, curl=-0.03), 'teeth', 0.0)
    add(Sphere(head + fwd * 0.03, 0.09 + 0.03 * gap), 'mouth', 0.0)
    add(Sphere(head - fwd * 0.06, 0.12), 'neck', 0.04)
    parts = body_pose(parts, P, lean_scale=0.4)
    m = reef_mats(P, glow=0.5)
    m['bone'] = Material(BONE, spec=0.08, gloss=12, brush=0.1)
    m['neck'] = coral_mat(deep=0.3, base_col=_hex('#dc7a6c'), hi_col=PINK)
    m['petal'] = flesh_mat(col=_hex('#f2a596'), inner=RED, P=P, glow=0.4)
    m['teeth'] = Material(_hex('#f7f1e6'), spec=0.4, gloss=30, brush=0.02)
    return finish(P, FACTION, parts, m)


ROWS, frames = reef_rows(neutral_pose, sink=0.2, tilt=0.1)

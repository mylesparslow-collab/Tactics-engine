"""Mother of the Wheel (Gyre exotic commander, flying giant). An albatross the size of a sail-barge gliding on
full wingspan with three small riders and lanterns strung along her back, cord-and-bone harness trailing.
Defining detail: the strung lanterns (the only warm light) and the sheer span."""
from _gyre_common import *

UNIT_ID = 'gyre_mother_of_the_wheel'
LOOK = LOOK_AIR
CAMERA = Camera(ppm=36)
S = species('albatross', k=1.9, half=1.10, ch_root=0.21, ch_wrist=0.135, ch_tip=0.05, tail_len=0.20, tail_w=(0.05, 0.11), th=0.020, sweep_in=0.0,
            sweep_out=0.10, dihedral=0.03, amp_in=0.22, amp_out=0.25, saddle=(0.21, 0.0), headr=(0.052, 0.050, 0.072),
            back=GUANO, beak_len=0.22, beak_d=0.036, hook=0.034, neck=0.20, tip_mat='beak_tip', fingers=0, spar=0.3, body=(0.16, 0.14, 0.42),
            col=dict(mantle=hx('#6a737e'), covert=hx('#3a424d'), flight=hx('#5a6470'), tip=hx('#1c1f26'), spot=None))
ROLL = 0.12
PITCH = 0.18
YAW = -0.28


def neutral_pose():
    return fly_pose(fl=0.10, pitch=PITCH, roll=ROLL, neckx=0.2, legs=0.0, yaw=YAW)


INKC = hx('#262930')


def extra(c):
    add, F, P, S_, mats = c['add'], c['F'], c['P'], c['S'], c['mats']
    mats['lamp'] = Material(hx('#ff9c3a'), spec=0.3, gloss=30, emissive=(1.0, 0.66, 0.26), rim=0.0)
    mats['beak_tip'] = Material(hx('#e8892f'), spec=0.25, gloss=26, brush=0.03)
    mats['beak'] = Material(hx('#eab59b'), spec=0.25, gloss=26, brush=0.03)
    mats['leather'] = Material(hx('#e4dfd2'), spec=0.05, brush=0.05)
    mats['figure'] = Material(INKC, spec=0.1, gloss=12, brush=0.04)
    mats['figure_hi'] = Material(hx('#3c424c'), spec=0.1, gloss=12, brush=0.04)
    mats['cordline'] = Material(hx('#d9d0b4'), spec=0.1, gloss=12, brush=0.03)
    mats['harness'] = Material(hx('#cfc6aa'), spec=0.1, gloss=12, brush=0.04)
    mats['b_cov'] = Material(hx('#3a424d'), spec=0.05, brush=0.05)
    k = S_['k']
    bx, by, bz = S_['body']
    top = by * k
    lights = []
    # three tiny hooded figures, clearly spaced along the spine
    for z, lean in ((0.42, 0.5), (0.0, 0.3), (-0.40, 0.4)):
        base = F.pt(v3(-0.04, top - 0.02, z))
        up = F.R @ v3(0, 1, 0)
        fw = F.R @ v3(0, 0, 1)
        mid = base + up * 0.09 + fw * 0.02 * lean
        hd = base + up * 0.19 + fw * 0.035 * lean
        add(Capsule(base, mid, 0.06, 0.050), 'figure', 0.0)
        add(Capsule(mid, hd - up * 0.03, 0.050, 0.038), 'figure', 0.04)
        add(Sphere(hd, 0.042), 'figure_hi', 0.02)
    # one thin cord with five tiny lanterns, running along the right side of the spine
    zs = (0.62, 0.22, -0.18, -0.48, -0.70)
    pts = [F.pt(v3(0.13, top + 0.02, z)) for z in zs]
    for a, b in zip(pts[:-1], pts[1:]):
        add(Capsule(a, b, 0.004, 0.004), 'cordline', 0.0)
    for q in pts:
        q2 = q + v3(0, 0.025, 0)
        add(Sphere(q2, 0.05), 'lamp', 0.0)
        lights.append(Light(q2, hx('#ffb35c'), 0.06 * P['glow'], 0.2))
    # cord-and-bone harness trailing under the belly
    for sx, z0 in ((-1, 0.25), (1, 0.05), (-1, -0.2)):
        pv = F.pt(v3(sx * bx * k * 0.8, -0.02, z0))
        for i in range(1, 5):
            q = F.pt(v3(sx * (bx * k * 0.8 + 0.05 * i), -0.10 * i - 0.04, z0 - 0.09 * i))
            add(Capsule(pv, q, 0.005, 0.005), 'harness', 0.0)
            if i >= 2:
                add(Sphere(q, 0.016), 'bone', 0.0)
            pv = q
    return lights


def build(P):
    return flier_build(P, S, None, extra, y0=0.58, rider=False)


def tweak(rows):
    # keep the collapsing bird inside the frame: lift the mid-fall poses
    for i, (P, over) in enumerate(rows['death']):
        if i == 1:
            P['dy'] += 0.40
        elif i == 2:
            P['dy'] += 0.58
        elif i == 3:
            P['dy'] += 0.22


ROWS, frames = fly_rows(neutral_pose, tweak=tweak, idle_amp=0.60)

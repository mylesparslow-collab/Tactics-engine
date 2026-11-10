"""The Landlord (Hermitage exotic big body). A wagon-sized crab wearing the lamp-room of a fallen lighthouse: glass
cylinder with four thick mullions, verdigris copper dome with a ball finial, a solid gallery band (four posts)
round the base, worn tipped back on the crab's shoulders, the iron lantern deck resting on the salt behind; the crab's face, eyestalks
and boxer's claws spill out from under the deck door, on four legs as thick as posts. ~2.5 m, ppm 44.
Defining detail: the lit lamp turning inside (a bright face sweeps round the glass), lighting the crab's head below."""
from _hermitage_common import *

UNIT_ID = 'hermitage_the_landlord'
SIZE = 1.30            # 'great' class, trimmed so lamp-room, claws and legs fit at ppm 44
CAMERA = size_camera('great')
GR, GH = 0.50, 0.78          # glass radius / height (shell-local y 0.10 .. 0.88)
G0 = 0.10
EYE_AZ = (-0.62, -0.22)


ROOM_S = 0.70                # the lamp-room's own scale inside the frame


def lamp_room(add, P, F):
    F = Frame(F.o, F.R, ROOM_S)
    ang0 = 2 * np.pi * P['tell'] + P['spin']
    # iron lantern deck under the gallery, with the door the crab lives behind
    deck = Subtract(Cylinder(v3(0, -0.40, 0), v3(0, 0.0, 0), 0.50, 0.03),
                    RoundBox(v3(0, -0.26, 0.48), (0.20, 0.17, 0.20), 0.03))
    F.put(add, deck, 'iron')
    F.box(add, (0, -0.26, 0.36), (0.19, 0.16, 0.02), 0.02, 'dark')
    # gallery: floor disk, solid band, four posts
    F.cyl(add, (0, -0.02, 0), (0, 0.05, 0), 0.74, 'copperd', 0.0, 0.015)
    band = Subtract(Cylinder(v3(0, 0.22, 0), v3(0, 0.34, 0), 0.74, 0.01), Cylinder(v3(0, 0.1, 0), v3(0, 0.5, 0), 0.70))
    F.put(add, band, 'copperd')
    for az in (0.30, 0.30 + np.pi / 2, 0.30 + np.pi, 0.30 + 1.5 * np.pi):
        c = v3(np.sin(az) * 0.72, 0, np.cos(az) * 0.72)
        F.cyl(add, c + v3(0, 0.04, 0), c + v3(0, 0.30, 0), 0.025, 'copperd')
    # glass drum and mullions
    F.cyl(add, (0, G0, 0), (0, G0 + GH, 0), GR, 'glass')
    for az in (0.75, 0.75 + np.pi / 2, 0.75 + np.pi, 0.75 + 1.5 * np.pi):
        c = v3(np.sin(az) * GR, 0, np.cos(az) * GR)
        F.box(add, c + v3(0, G0 + GH / 2, 0), (0.035, GH / 2, 0.035), 0.01, 'copper', 0.0, rot_y(az))
    F.put(add, Torus(v3(0, G0 + 0.01, 0), v3(0, 1, 0), GR + 0.01, 0.035), 'copper')
    F.put(add, Torus(v3(0, G0 + GH, 0), v3(0, 1, 0), GR + 0.03, 0.045), 'copper')
    # dome, vent cap and ball finial
    F.ell(add, (0, G0 + GH + 0.02, 0), (GR + 0.08, 0.40, GR + 0.08), 'dome', 0.0)
    F.cyl(add, (0, G0 + GH - 0.02, 0), (0, G0 + GH + 0.05, 0), GR + 0.10, 'copperd', 0.02, 0.02)
    F.cyl(add, (0, G0 + GH + 0.36, 0), (0, G0 + GH + 0.52, 0), 0.05, 'copperd', 0.0, 0.01)
    F.sph(add, (0, G0 + GH + 0.58, 0), 0.085, 'copperd')

    def glass_em(p, n):
        q = F.inv(p)
        a = np.arctan2(q[:, 0], q[:, 2])
        d = np.angle(np.exp(1j * (a - ang0)))
        beam = np.exp(-(d / 0.42) ** 2)
        hgt = np.exp(-((q[:, 1] - (G0 + GH * 0.5)) / 0.26) ** 2)
        e = 0.22 + 0.25 * hgt + 1.05 * beam * (0.4 + 0.6 * hgt)
        e = e * (1 + 0.4 * P['cast_glow']) * (1 - P['end'])
        return np.array(LAMP)[None, :] * np.clip(e, 0, 1.3)[:, None]

    def verd(base, amt):
        def fn(q, n):
            a = _arr(base, len(q))
            v = fbm(q, 4.0, 2)[:, None]
            pat = np.clip((v - 0.30) * 2.0, 0, 1) * amt
            return a * (1 - pat) + np.array(VERDI)[None, :] * pat
        return fn
    return {
        'glass': Material(_hex('#f2dfae'), spec=1.0, gloss=80, emissive=glass_em, rim=0.3),
        'dome': Material(local_albedo(F, verd(_hex('#9a6a44'), 0.9)), spec=0.25, gloss=60, metal=0.5),
        'copper': Material(local_albedo(F, verd(_hex('#8a5a3a'), 0.6)), spec=0.5, gloss=30, metal=0.5),
        'copperd': Material(local_albedo(F, verd(_hex('#5d4a3c'), 0.7)), spec=0.4, gloss=24, metal=0.4),
        'iron': Material(_hex('#3a3436'), spec=0.4, gloss=24, metal=0.5),
    }


def _eyes():
    out = []
    for az in EYE_AZ:
        c = v3(np.sin(az) * (GR - 0.02), G0 + GH * 0.50, np.cos(az) * (GR - 0.02)) * ROOM_S
        base = v3(np.sin(az) * 0.14, -0.10, np.cos(az) * 0.14)
        d = c - base
        out.append((tuple(base), tuple(norm(d)), float(np.linalg.norm(d))))
    return tuple(out)


SHELL = Shell(
    build=lamp_room, ride=0.44, tilt=-0.20, crab_at=(0, -0.26, 0.34), crab_upright=1.0, z0=-0.78, x0=0.36,
    eye_len=0.26, eye_bead=0.058, span=0.46, duck_dir=(0, 0.7, -1.0), duck_depth=0.16,
    big=1.30, small=0.70, side_r=0.62, tip_angle=0.60, tip_dir=-1.0, leg_r=1.30, shield=1.1)


def neutral_pose():
    return hermit_pose(open=0.3)


def build(P):
    F = shell_frame(P, SHELL)
    F = Frame(F.o, F.R, ROOM_S)
    lights = [Light(F.p((0, G0 + GH * 0.5, 0)), LAMP, 1.2 * (1 - P['end']) * (1 + 0.5 * P['cast_glow']), 0.9)]

    def world(add):
        if P['ring'] > 0:          # The Lamp Turns: one beam swings out of the glass
            a = 2 * np.pi * P['tell'] + P['spin']
            d = F.v((np.sin(a), 0, np.cos(a)))
            c = F.p((0, G0 + GH * 0.5, 0)) + d * (GR + 0.22)
            add(Ellipsoid(c, (0.06, 0.06, 0.26 * P['ring']), R_from(d)), 'beam', 0.0)
    return shelled(P, SIZE, SHELL, lights=lights, world=world,
                   mats={'beam': Material(LAMP, emissive=tuple(np.array(LAMP) * 1.1), rim=0.0)})


def _rows(R):
    for i, (P, o) in enumerate(R['idle']):
        P['spin'] = 0.0
    for i, (P, o) in enumerate(R['move']):
        P['spin'] = 0.4
    for row in ('attack', 'death', 'cast', 'hit'):     # the claw is huge at this scale: keep it in frame
        for P, o in R[row]:
            P['snap'] *= 0.55
            P['drum'] *= 0.5
            P['limp'] *= 0.4
    for i, (P, o) in enumerate(R['death']):
        P['slide'] = [0, 0.0, -0.02, -0.02][i]
        P['duck'] = [0.6, 0.5, 0.7, 0.75][i]
    for i, (P, o) in enumerate(R['cast']):
        P['ring'] = [0.6, 1.0, 1.0, 0.7][i]
        P['tell'] = [0.10, 0.22, 0.34, 0.46][i]
    return R


ROWS, frames = hermit_rows(neutral_pose, 'shell', extra=_rows)

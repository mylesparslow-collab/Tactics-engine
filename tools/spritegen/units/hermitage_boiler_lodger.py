"""Boiler Lodger (Hermitage short ranged / fire). A pony-ish crab living UNDER a riveted rust-iron ship's boiler like
legs under a stove: the boiler rides high, its round firebox door on the front glowing lamp amber, a stub funnel on
top, the crab's claw and eyestalks out below and beside the door. Scald: the door bangs open with a lick of flame.
Blow-Off Valve (cast): one thin straight steam jet from a valve on top, no clouds. ~1.5 m.
Defining detail: the glowing firebox door."""
import dataclasses
from _hermitage_common import *
from _hermitage_common import _claw_target, _arr

UNIT_ID = 'hermitage_boiler_lodger'
SIZE = 'medium'
CAMERA = size_camera(SIZE)
BL, BR = 1.04, 0.40            # boiler length / radius
HL_ = BL / 2 - BR * 0.5
FZ = HL_ + BR * 0.55           # front plate z in shell space
VALVE = (0.18, BR - 0.02, 0.10)

SHELL = Shell(
    build=None,
    ride=0.70, tilt=0.0, crab_at=(0, -0.42, 0.52), crab_upright=1.0, z0=-0.62, x0=0.30,
    eye_len=0.30, eye_bead=0.064, span=0.46, duck_dir=(0, 0.5, -1.0), duck_depth=0.22,
    big=1.35, small=0.70, side_r=0.46, tip_angle=1.30, tip_dir=1.0, leg_len=1.05, leg_r=1.10)


def neutral_pose():
    return hermit_pose(open=0.35, door=0.55, jet=0.0)


def _glow(P):
    return max(0.25, 1.25 + 0.12 * np.sin(2 * np.pi * P['tell'] * 2) + 0.5 * P['cast_glow'] + 0.9 * P['door'] - 0.85 * P['end'])


def build(P):
    glow = _glow(P)
    base = boiler_shell(length=BL, r=BR, door=P['door'], glow=glow, funnel=True, bosses=4, funnel_h=0.20)

    def shell_build(add, P_, F):
        m = base(add, P_, F)
        F.cyl(add, (VALVE[0], VALVE[1] - 0.04, VALVE[2]), (VALVE[0], VALVE[1] + 0.07, VALVE[2]), 0.034, 'boilband', 0.01)
        F.sph(add, (VALVE[0], VALVE[1] + 0.10, VALVE[2]), 0.05, 'valve')
        F.cyl(add, (VALVE[0] - 0.06, VALVE[1] + 0.10, VALVE[2]), (VALVE[0] + 0.06, VALVE[1] + 0.10, VALVE[2]), 0.016, 'boilband')
        m['valve'] = Material(_hex('#b08a45'), spec=0.7, gloss=40, metal=0.6)
        return m
    sh = dataclasses.replace(SHELL, build=shell_build)
    F = shell_frame(P, sh)
    door_c = F.p((0, -0.06, FZ + 0.05))
    lights = [Light(door_c + F.v((0, 0, 0.40)), LAMP, 0.9 * min(glow, 1.4) * (1 - P['end']), 0.9)]

    def world(add):
        if P['fx'] > 0.05:       # Scald: one short tongue of flame out of the opened door
            fl = P['fx']
            add(Ellipsoid(door_c + F.v((0.0, 0.0, 0.20 + 0.18 * fl)), (0.10 * fl, 0.10 * fl, 0.24 * fl), F.R), 'flame', 0.0)
            add(Sphere(door_c + F.v((0, 0, 0.08)), 0.09 * fl), 'flash', 0.0)
        j = P['jet']
        v0 = F.p((VALVE[0], VALVE[1] + 0.10, VALVE[2]))
        if j > 0.05:                                 # Blow-Off Valve: ONE thin straight jet, pointing forward-up
            d = norm(F.v((0.0, 0.18, 1.0)))
            add(Capsule(v0 + d * 0.04, v0 + d * (0.10 + 0.38 * j), 0.016, 0.011), 'steamjet', 0.0)
            emit(add, v0 + d * (0.14 + 0.38 * j), 'steam', 1.2 * j)
        else:
            emit(add, v0, 'steam', 0.18 + 0.0 * P['fx'])
        emit(add, door_c + F.v((0, 0.0, 0.05)), 'embers', 0.25 + 0.6 * P['fx'])
    return shelled(P, SIZE, sh, lights=lights, world=world,
                   mats={'steamjet': Material(_hex('#f4f7f6'), emissive=_hex('#bfc9c8'), rim=0.0)})


def _rows(R):
    # attack = Scald: claw cocks, firebox door bangs open with a flame lick on the hit frame
    for i, (P, o) in enumerate(R['attack']):
        P['door'] = [0.55, 0.7, 1.0, 0.75][i]
        P['fx'] = [0.0, 0.0, 1.0, 0.3][i]
        P['snap'] *= 0.7
    # cast = Blow-Off Valve: rear back, the valve spits one thin jet
    for i, (P, o) in enumerate(R['cast']):
        P['jet'] = [0.0, 0.6, 1.0, 0.7][i]
        P['drum'] *= 0.5
    # death: the fire dies down
    for i, (P, o) in enumerate(R['death']):
        P['door'] = 0.0
    for P, o in R['cast']:
        P['door'] = 0.55
    fit_rows(R, snap=0.6, drum=0.45, limp=0.5, death_back=0.40, death_slide=0.24, death_yaw=-0.5, cast_back=0.22)   # keep claws and the death topple inside the frame
    return R


ROWS, frames = hermit_rows(neutral_pose, 'shell', extra=_rows)

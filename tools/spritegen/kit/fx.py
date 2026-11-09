"""Animated effects: smoke, soot, ink, murk, mist, steam, salt plumes, rain clouds, spray.

These are NOT sculpted. A solid SDF puff renders as a flat painted blob that never moves, so instead a
unit drops an invisible *emitter* where the effect comes from, and the game spawns live particles there
(src/render/fx.ts): drifting, swirling, growing and fading puffs, re-emitted every frame.

    from kit.fx import emit
    emit(add, funnel_tip, 'ink', strength=0.6 + 0.6 * P['cast_glow'])

The emitter is a tiny marker part, so every whole-body transform the unit applies afterwards (lean, bob,
squash, sink) carries it along with the body. render() drops markers before tracing; sheet.py projects
them per frame and writes them into the manifest as `fx` tracks, which the engine reads.

strength 0..2 scales the emission rate (0 or less = off for that frame). Presets, defined in fx.ts:
  smoke   grey woodsmoke / gunsmoke that rises and curls         soot    dark greasy smoke
  ink     dark blue-black ink that blooms and curls, sinks a bit murk    Hadal murk that hugs the ground
  mist    pale low drifting mist                                   steam   fast white rising steam
  salt    white powdered-salt plume that billows up and settles    cloud   a churning rain cloud that rains
  spray   brine droplets thrown off with a fine mist               embers  sparks that rise and wink out
"""
import numpy as np
from sdf import Sphere

PRESETS = ('smoke', 'soot', 'ink', 'murk', 'mist', 'steam', 'salt', 'cloud', 'spray', 'embers')
PREFIX = 'fx:'


def emit(add, pos, preset, strength=1.0):
    """Mark an emitter at `pos` (unit space, metres) for this frame."""
    assert preset in PRESETS, preset
    if strength <= 0.01:
        return
    add(Sphere(np.asarray(pos, dtype=np.float64), 0.004), '%s%s:%.3f' % (PREFIX, preset, float(strength)), 0.0)


def is_fx(part):
    return isinstance(part.mat, str) and part.mat.startswith(PREFIX)


def split(parts):
    """(solid parts, [(preset, strength, centre)]) in emission order."""
    solid, em = [], []
    for p in parts:
        if is_fx(p):
            _, preset, s = p.mat.split(':')
            em.append((preset, float(s), np.asarray(p.prim.bc, dtype=np.float64)))
        else:
            solid.append(p)
    return solid, em


def project(cam, pos):
    """Unit-space point -> frame pixel (x, y) for the given render.Camera."""
    _, right, up = cam.basis()
    return cam.anchor[0] + float(pos @ right) * cam.ppm, cam.anchor[1] - float(pos @ up) * cam.ppm

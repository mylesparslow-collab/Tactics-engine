# spritegen: painted unit sprites from code

This tool renders EBB unit sprites as small 3D sculpts, lit and then painted down to the agreed
96×112 frame. It replaces the flat procedural vector placeholders. One sculpt drives every animation
row, so a unit is written once and posed per frame.

Reference unit: `units/salt_concord_tamsin_orrel.py` (Commander Tamsin Orrel). Copy it to start a new unit.

## Running it

```
cd tools/spritegen
python3 preview.py salt_concord_tamsin_orrel out/          # still, 4x enlargement, board mock-up (~35 s)
python3 closeup.py salt_concord_tamsin_orrel out/c.png 220 1.3   # big debug render of the head and torso
python3 sheet.py   salt_concord_tamsin_orrel out/          # full sheet + manifest + preview gif (~3 min on 4 cores)
```

Needs only Python 3, numpy and Pillow. `sheet.py` writes:

- `<unitId>.png`: palette-quantised sheet, one animation per row, 96×112 frames (the engine format)
- `<unitId>.json`: manifest (`frameWidth`, `frameHeight`, `anchor: [48,104]`, `facing: lower-right`, per-row frames/fps/loop/hitFrame/holdLast)
- `<unitId>_still.png`: idle frame 0, for cards and fallbacks
- `<unitId>_rgba.png`: the unquantised sheet
- `<unitId>_preview.gif`: every row played in turn at 3x, for review

## How a frame is made

1. **Sculpt** (`sdf.py`). The unit is a list of parts, each a signed-distance primitive (sphere,
   ellipsoid, capsule or round cone, rounded box, cylinder, torus, or a custom `Func`) with a material
   name and an optional smooth-blend radius `k`. Cloth is a custom shell: the coat skirt is a flared
   ellipse with sine folds, split at the front, and the capelet is a superellipse shell (squared shoulders,
   which is the Concord's shape language). Units are metres. y is up, the figure faces +z, and its
   left hand is +x.
2. **Camera** (`render.Camera`). Orthographic, 30° elevation, 38° azimuth toward the figure's right, so it
   faces lower-right on screen. 52 px per metre at 1x, rendered at 4x supersampling. Feet at (48,104).
3. **Light** (`render.Look`). The art bible's light: a warm key from the upper left with soft SDF shadows,
   dull wrong-sky ambient, warm salt-flat bounce from below, a cool rim from behind-right, AO, Blinn
   specular (brass is metallic), and point lights for lamps. Shadows get a cool hue shift.
4. **Paint**. The key light is pulled 35% toward three value bands. Albedo gets world-space brush noise.
   A Kuwahara filter at 4x flattens the result into brush-like patches. Materials can be functions of
   position, which is how the coat gets salt trim, salt bloom creeping up from the hem, the survey
   rod's bands, and the face (eyes, brows, lips and cheeks painted in head space, not modelled).
5. **Finish**. Emissive bloom (with an alpha halo, so the lamp glows over the board), box downsample to 1x,
   unsharp mask, a gentle S-curve, a soft ink darkening on silhouette pixels (not a hard outline), and a
   ground shadow (contact ellipse plus a short cast shadow toward the lower right).

## Making a new unit

1. Copy the reference unit file. Set `UNIT_ID` to the `units.json` id.
2. **Palette first.** Take the faction's hexes from `world/bible/art_direction.md`. Keep about 70% muted
   neutrals, 25% faction colour and 5% one saturated light source (lamp, bioluminescence).
3. **Pose dict.** `neutral_pose()` holds the joints (pelvis, chest, neck, head, shoulders, elbows, wrists,
   hips, knees, ankles) plus scalars such as `breathe`, `coat_sway`, `lamp_glow` and `crust`. `build(P)`
   turns a pose into parts, so the parts must hang off joints, never fixed world positions.
4. **Silhouette before detail.** Read the shape at 1x on the board mock-up (`preview.py`) before adding
   buttons. At 96×112 a head is about 10 px tall. Paint faces as albedo, give hands gloves or simple
   mitts, and make props a little oversized (the staff ring, the lamp).
5. **Animate** with `rig.py`: `shift`, `lean`, `place_arm` / `place_leg` (two-bone IK) and
   `staff_from_grips`. Write `frames()` returning `{row: [(pose, look_overrides), ...]}` and `ROWS`
   (name, fps, loop, extra manifest fields). The rows follow the animation spec: idle with a faction tell,
   a two-step move, attack with `hitFrame`, a hit with a flash (`flash` look override), death ending in
   the faction's end state, and cast.
6. **Faction end states and tells** go through materials. For example `salt_crusted()` wraps every
   material so white salt blooms over the body in the Concord death. A bell could deflate (scale the
   part), brine could pool (an ellipsoid on the ground), and a flame could gutter (emissive to 0).
7. Check the result in `closeup.py`, then in `preview.py`, then build the sheet.

Non-human units (crabs, polyps, engines) work the same way. Swap the humanoid joint set for whatever
the body needs and keep the camera, `Look` and paint pass, so every faction shares one look.

## Tuning knobs

| Knob | Where | Effect |
|---|---|---|
| `Camera.ppm` | render.py | figure size in the frame |
| `Look.bands` | render.py | 0 = smooth light, 1 = hard cel bands |
| `Look.kuwahara` | render.py | brush-patch radius at 4x (0 = off) |
| `Look.edge_dark` | render.py | strength of the soft silhouette darkening |
| `Look.sharpen`, `Look.contrast` | render.py | crispness at 1x |
| `Material.brush` | per material | strength of the paint texture |
| `Material.sss` | per material | soft warm wrap, for skin |
| `LOOK` in a unit file | unit | per-unit or per-faction overrides (e.g. darker ambient for the Hadal Court) |

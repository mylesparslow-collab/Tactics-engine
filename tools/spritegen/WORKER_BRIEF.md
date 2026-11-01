# Brief: sculpt one faction's unit sprites with spritegen

You are building painted, semi-realistic isometric unit sprites for EBB, an original tactics game
(PoxNora-like quality bar, but all designs original). The pipeline is code: each unit is a numpy
signed-distance-field sculpt, posed per frame, lit and painted down to 96x112.

## Read first (in this order)
1. tools/spritegen/README.md (how the renderer works, the kit, tuning knobs)
2. tools/spritegen/kit/humanoid.py, kit/anim.py, kit/xform.py, kit/endstates.py, kit/looks.py (docstrings)
3. tools/spritegen/units/salt_concord_salt_levy.py (short kit example) and
   units/salt_concord_tamsin_orrel.py (hand-built reference that set the quality bar). Look at
   tools/spritegen/examples/showcase.png and examples/salt_concord_tamsin_orrel.png to see the bar.
4. /mnt/project-files/world/bible/art_direction.md: section 1 (global look), YOUR faction's section
   (silhouette language, palette, materials, reference units, "Do not" list), sections 9 and 10
   (presentation and animation spec, including your faction's idle tell and death end state).
5. /mnt/project-files/world/factions/<faction>/README.md and the unit entries for your faction in
   /mnt/project-files/tactics-engine/content/units.json (name, role, description, abilities).
6. /mnt/project-files/world/sprites_v2_contact_sheet.png shows the old flat placeholders, which only
   show intended silhouette/props. Do not copy their flat style.

## For each unit
Write tools/spritegen/units/<unitId>.py exposing UNIT_ID, FACTION, LOOK (= LOOKS[FACTION] or a tweak),
neutral_pose(), build(P) -> Scene (end with kit finish()), ROWS and frames (from kit.anim.humanoid_rows,
or kit.anim.creature_frames for non-humanoids, or your own like the Tamsin file). Optional CAMERA for giants
(ppm >= 44). Shared faction helpers go in tools/spritegen/units/_<faction>_common.py.

Iterate visually, from tools/spritegen/:
- python3 preview.py <unitId> out/<faction>/wip   (still + 4x + board mock-up, about 5-12 s). Read the
  _x4.png and _board.png images and judge them like an art director.
- python3 closeup.py <unitId> out/<faction>/wip/c.png 220 1.3   (big render of head and torso)
- python3 sheet.py <unitId> out/<faction> --jobs 2   (all rows). Then Read <unitId>_review.png and check
  every frame: limbs attached, props held, nothing important cut off by the 96x112 frame (top edge is
  about 2.1 m above the feet at default scale), death ends in the faction end state, cast and attack readable.

Quality checklist: strong readable silhouette at 1x in your faction's shape language; faction palette
(70% muted neutrals, 25% faction colour, 5% one saturated light source); one defining detail per unit
from the brief; faces painted via face_albedo, not modelled; props a little oversized; units
distinguishable from each other at board scale (vary height/build/props/headgear); heroes richer than
commons. Non-humanoids (creatures, engines, polyps, bells) should be real sculpts too, not blobs: give
them structure (segments, plates, fronds, wheels), and make the animation rows move their parts.

## Rules
- Do NOT edit shared files: render.py, sdf.py, rig.py, kit/*, preview.py, sheet.py, contact.py, README.md,
  or other factions' units. If the kit lacks something, build it in your _<faction>_common.py. If a shared
  bug blocks you, work around it and mention it in your report.
- Do NOT run git and do not write into /mnt/project-files/ (the lead copies outputs). Output only to
  tools/spritegen/out/<faction>/.
- Use --jobs 2 for sheet.py. Five other workers share these 4 CPUs.
- Finish every unit with a complete sheet before polishing any one. Budget roughly 10-15 minutes per unit.
- At the end run: python3 contact.py out/<faction> out/<faction>_contact.png "<Faction name>", Read it,
  fix the weakest 2-3 units, then rerun it.

## Report (keep it short)
The list of unitIds with finished sheets. One line on anything weak or unfinished. Any shared-kit bug you hit.

# Sound credits

Every sound in Brinewake is a recording from a licensed pack. Nothing is synthesised. We trim, level-match, EQ,
loop-crossfade, pitch-shift (percussion only) and arrange them; the build scripts in `tools/sounds/` document exactly how,
and `python3 tools/sounds/build.py <packs-dir>` plus `python3 tools/sounds/compose.py <packs-dir>` regenerate `src/audio/assets/`.

## Packs

| Pack | Author | License | Used for |
|---|---|---|---|
| Interface Sounds | Kenney (kenney.nl) | CC0 1.0 | clicks, confirm/back/open/close, errors, selection, status glints |
| UI Audio | Kenney (kenney.nl) | CC0 1.0 | hover ticks, button clicks |
| RPG Audio | Kenney (kenney.nl) | CC0 1.0 | card draw and play, equip, coins, blade draws |
| Impact Sounds | Kenney (kenney.nl) | CC0 1.0 | footsteps on salt/stone/wood/coral, armor and metal hits, the lighthouse bell, Beacon hits, drum hits in the battle music |
| Meta Piano (Meta Open Sound) | Meta Creative Audio | CC0 1.0 | every piano note in the menu and battle music |
| Oculus Audio Pack 01 (Meta Open Sound) | Oculus VR, LLC | CC BY 4.0 | ambient beds (ocean, underwater, wind, rain, bubbles, chimes, drone), unit voices (human, ogre, troll, giant, creature, drowned), sword, whoosh, magic, metal, creaks, stingers, footsteps |

Credit line required by CC BY 4.0:

> "Oculus Audio Pack 01" by Oculus VR, LLC (https://developers.meta.com/vr/downloads/package/oculus-audio-pack-1/), licensed under CC BY 4.0. Files renamed to the UCS naming convention; OGG previews transcoded from the original WAVs.
> Here the files were additionally trimmed, level-matched, filtered, looped and transcoded to MP3.

Source repositories (all public): `Calinou/kenney-interface-sounds`, `Calinou/kenney-ui-audio`,
`Boyquotes/kenney-rpg-audio-for-godot`, `Boyquotes/kenney-impact-sounds-for-godot`, `facebookincubator/Meta-open-sound`.

## Music

`menu`, `battle_a` and `battle_b` are arrangements made for Brinewake: the notes are chosen and timed by `tools/sounds/compose.py`,
but every sound in them is a recording (Meta Piano notes, Kenney impact hits pitched down, an Oculus drone bed) with a room reverb applied.

## Layout

- `assets/sfx/<bank>_<n>.mp3`: one-shot banks (a random variant plays each time). Add or swap variants freely.
- `assets/accent/`: rare ambient one-shots (creaks, a distant bell) sprinkled over the beds by `scenes.ts`.
- `assets/amb/`: seamless ambient loops. `assets/music/`: music loops.

# Tidewatch: Brinewake's auto-battle mode

Status: design v1 (2026-11-09). Code: `src/engine/autobattle.ts`, `src/ui/autobattle.ts`.

## Pitch

You are a lamp-keeper hiring a crew to hold one stretch of the drained shelf through ten
**Watches**. Between watches you hire champions at the **Tideline**, a salvage market on the
wet edge of the sea. Then you set your crew on the shelf and step back: both crews fight on
their own, using the same tactics AI and rules as Skirmish. Your lamp has **Light**. Lose a
watch and the lamp dims. Hold all ten and the Long Ebb holds one more night.

What makes it Brinewake and not a generic auto-battler:

1. **It is a tactics board, not a bench of slots.** Fights run on cropped real maps with
   height, terrain, Tide Wells and drops. Formation and terrain matter (Reef on living reef,
   Hadal near vents, shooters on beam glass).
2. **The tide comes back.** From battle round 7 the sea floods the arena one ring at a time
   from the edges. Floodwater is wet (Returning Tide and wet-loving units like it) and drowns
   everyone else for 3 a turn. No stalemates, and wet factions get a real late-game identity.
3. **Tempering instead of merging.** There is no "buy three to upgrade". Champions grow by
   surviving watches and earn the tempering ranks already written in `content/relics.json`
   (stat bumps, then a rank-3 signature ability). Buying a champion you already own
   **feeds** it 3 XP instead of adding a body. Keeping veterans alive is the long game.
4. **The crew earns its own pay.** Tide your crew collects in battle (Wells held, drops picked
   up from the fallen) is kept as salvage. Aggressive crews that win the scramble get richer.
5. **A two-faction Charter.** You pick one or two factions at the start. The market only
   offers your Charter, so a run is a story about a pairing (Concord + Lanternkeepers,
   Hadal + Overcurrent, ...).

## Run structure

- Pick a **Charter**: 1 or 2 factions. Start with **Light 5** and **10 salvage**.
- Ten watches. Watch 5 and watch 10 are **Lamp-eater** watches: the enemy crew is led by a
  hero and has +1 tempering rank.
- Each watch: Tideline (market) -> Formation -> Battle -> Result.
- Lose a watch: -1 Light, or -2 if the enemy has 3+ champions still standing. Draw: no loss.
- Run ends at Light 0 (defeat) or after winning watch 10 (victory). Best result is kept in
  localStorage (`brinewake.tidewatch.best`). The run in progress is saved after every step
  (`brinewake.tidewatch.run`) so a reload resumes at the market.

## The Tideline (market)

- **Income** at the start of every watch after the first: 8 salvage, plus whatever the crew
  earned in battle (Tide gained during the battle / 5, rounded down, max 6).
- **Offer**: 5 cards. 4 champion slots from the Charter factions, 1 slot that is a spell or
  equipment from the Charter. Offers keep until rerolled or bought.
- **Tiers by watch** (by `cost`): watches 1-2 cost <= 35; 3-4 cost <= 55; 5+ everything.
  Heroes can appear from watch 4 (max one hero in the crew; heroes are unique).
- **Price** = `ceil(cost / 10)` salvage (champions 2-9; spells/equipment the same rule).
- **Dredge** (reroll): 2 salvage. **Mark** a card to keep it through a dredge (free).
- **Scrap** (sell): half the price paid, rounded down, minimum 1.
- **Berths** (crew size on the field): 3 at watch 1, +1 per watch to 8 at watch 6.
- **Hold** (bench): 3 slots. Held champions do not fight and do not earn XP.
- **Equipment**: buy, then attach to a crew champion. Permanent for the run, one per
  champion (engine rule; `restrictTo` respected). Replacing it scraps the old one.
- **Hymns** (spells): up to 2. In battle the team starts holding them with exactly enough Tide
  to cast each once; the AI casts them when it judges them good. They go on cooldown and can
  return as usual.

## Tempering (veterancy)

Per watch, each crew champion that fought gains XP: +2 if alive at the end, +1 if it fell,
+1 more if the crew won. Feeding (buying a duplicate) gives +3. Ranks come from the unit's
`relics.json` entry (`tempering[].xpRequired`, `statMods`, `addAbility`). In battle a
tempered champion is a synthesized unit def (`tw:<defId>:<rank>`) with the stat mods and added
abilities applied, registered into `content.units` before the mission starts. A champion with
no relic entry simply does not temper.

## Formation

- Each watch uses a **12x12 arena** cropped from one of the 14 maps (seeded per run and watch,
  window chosen to have the fewest void/impassable tiles). The player's deploy zone is the 3
  rows on their side, the enemy's the opposite 3 rows. No Beacons in Tidewatch.
- The player places crew champions on their deploy tiles (click a champion, click a tile;
  click a placed one to pick it up). Positions are remembered as offsets and reused next
  watch when valid; "Auto" fills the rest.
- The enemy crew is shown as a list (names, faction, rank), not positions.

## Battle

- Both teams `controller: 'ai'`. The player watches with the normal board renderer.
  Controls: speed 1x / 2x / 4x and **Skip** (resolves the same seeded battle headless and
  jumps to the result; the AI is deterministic so the outcome matches).
- Starting Tide: each team gets the sum of its Hymn costs, nothing else. Wells and drops work
  normally; the Tide gained is what pays out as salvage.
- **The Flood**: generated as mission events. At the start of round 7 the outer ring of the
  arena becomes `floodwater`, round 8 the next ring, and so on. `floodwater`: moveCost 2, wet,
  onTurnStart 3 damage (`drowning`), drawn with the brine pool tiles.
- **Hard cap**: if both crews still stand after round 12, the crew with the higher total
  remaining HP fraction wins; equal is a draw.

## Enemy crews

Generated per watch from the run seed: a random faction (not filtered by the Charter), a
crew size equal to the player's berths, and a salvage budget of `10 + 9 x (watch - 1)` spent
with the same tier and price rules (greedy for the strongest affordable picks, some
randomness). From watch 6 enemy champions get tempering rank 1, from watch 9 rank 2.
Lamp-eater watches add a hero and +1 rank. Names come from the faction, e.g. "Hadal Court
tithe-crew".

## Out of scope for v1

Online play, ghosts of other players' crews, a meta-progression shop, item combining, and
new art. All visuals reuse existing cards, sprites, tiles and the house UI (Cormorant SC +
Barlow Semi Condensed, no illuminated initials, no generic gradient-card look).

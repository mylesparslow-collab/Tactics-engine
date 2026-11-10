# Content schema (v0.1)

All game content is JSON in `content/`. The engine reads it at startup and validates every cross-reference
(unknown ability, status, terrain or unit ids are reported as errors). Ids are lowercase snake_case keys.
Example files ship in `content/` with placeholder names; replace them freely.

## content/units.json — `{ [unitId]: UnitDef }`
| field | type | notes |
|---|---|---|
| name | string | display name |
| role | string | flavour/UI label (Tank, Ranged...) |
| faction | string? | optional faction id, free text for now |
| cost | number | essence cost to deploy |
| structure | bool? | true = cannot move/act, not deployable (e.g. keystone) |
| stats.hp / ap / attack / defense / jump | number | jump = max height step when walking |
| abilities | string[] | ability ids; the first one is the unit's "basic attack" |
| sprite.shape | "square"\|"circle"\|"triangle"\|"diamond"\|"pillar" | placeholder art |
| sprite.glyph | string | 1-2 chars drawn on the placeholder |
| sprite.image | string? | optional URL to a real sprite (used instead of placeholder) |
| description | string? | lore text |
| resist | {damageType: number}? | flat damage reduction per damage type (negative = weakness) |
| hero | bool? | unique: max one copy per warband/roster; shown with a crown |
| revive | {hpFraction}? | returns once on death with that fraction of max HP |
| skyfall | {impact: number}? | besides the deploy zone, may be deployed on any empty passable tile not within 2 (Manhattan) of the enemy keystone. The cost is paid now and a landing marker (visible to both sides) sits on the tile; at the start of the owner's next turn the unit lands and can act. On landing every adjacent enemy takes `impact` flat physical damage (resist applies, defense does not). If the tile is occupied then, the occupant (any team) takes impact+3 and the unit lands on the nearest free passable tile. A pending landing counts as alive for `eliminate`. |
| dries | number? | at the start of its owner's turn (not the turn it lands) loses this many HP, unless it stands on a wet tile (`brine_pool`, `living_reef`, or terrain with `wet: true`), has a status with `wet: true`, or is inside a passive aura with `keepsWet: true`. Can kill (damageType `drying`). |
| flying | bool? | every passable tile costs 1 AP, height/jump ignored, impassable tiles can be crossed but not ended on (enemies and structures still block, allies can be passed), terrain `onEnter` never triggers, and the unit does not hold Wells (no income, no forward deploy). |
| ignoresEngagement | bool? | never pays the engagement cost (below). Flyers ignore it already. |
| token | bool? | never a card: excluded from warbands, campaign rosters/unlocks (validation error), default faction decks, the collection, the card gallery, Tidewatch offers and the proving ground. Use for evicted forms, empty shells, husks and tail segments. Units named as `shed.husk`, `shell.evicted`, `shell.leaves` or `tail.segment`, and every `decoy`/`emptyShell` unit, are treated as tokens even without the flag. Tokens may still be summoned, pre-placed or spawned. |
| decoy | bool? | (must also be `structure: true`) a decoy such as a Shed husk: does not count for `eliminate`, holds no Wells, drops no Tide, and vanishes at the start of its owner's 3rd turn after it appeared. The AI treats it as a low-value target. |
| shed | {husk: unitId, slide?: number}? | see **Shed** below. `husk` must be a structure unit (normally `{structure, decoy, token, cost 0, stats.hp 1, abilities []}`); `slide` defaults to 2. |
| coiled | {ability: abilityId}? | see **Coiled** below. |
| shell | {hp: number, evicted: unitId, leaves?: unitId}? | see **Shells** below. `evicted` must exist, have no `shell` and not be a structure; `leaves` must be an `emptyShell` unit. Not allowed on structures. |
| emptyShell | {becomes: unitId}? | (must also be `structure: true`, mark it `token: true`) an empty shell object; `becomes` must be a unit with a `shell`. |
| tail | {segment: unitId, length: 1\|2\|3}? | see **Long bodies** below. `segment` must be a structure unit (mark it `token: true`). |

## content/abilities.json — `{ [abilityId]: AbilityDef }`
| field | type | notes |
|---|---|---|
| name, description | string | |
| apCost | number | |
| cooldown | number? | turns before reuse |
| range | {min,max} | Manhattan distance; 0 = self |
| target | "enemy"\|"ally"\|"unit"\|"tile"\|"empty"\|"self" | what the player clicks |
| area | {shape:"radius"\|"line", size}? | radius: splash around the target tile. line: `size` tiles starting next to the caster, heading toward the target |
| affects | "enemies"\|"allies"\|"all"? | who the area hits (default: matches target) |
| effects | Effect[] | applied in order to each affected unit |

Effect types:
- `{type:"damage", amount, damageType, ignoreAttack?, pierce?}` — damage = attacker.attack + amount − target.defense − terrain defense + height bonus (min 1), then minus the target's `resist[damageType]` (min 0). `ignoreAttack` makes the base a flat `amount`; `pierce` ignores defense and terrain. `vsWounded: {below, bonus}` adds `bonus` to the amount (before defense/resist) when the target's current HP is below `below` × its max HP; works in abilities and spells.
- `{type:"heal", amount, target?: "caster"}` — `target:"caster"` heals the caster (life drain), once per unit hit
- `{type:"sacrifice"}` — kills the caster (no revive); put it last
- `{type:"status", status, duration, target?: "caster"}` — `target:"caster"` applies it to the caster once per use (not per unit hit); not allowed in spells
- **Engagement:** a unit that starts a walk orthogonally next to a living enemy (structures don't count) pays +2 AP (`ENGAGE_COST` in game.ts) on its first step, once per walk, even if it stays adjacent. Flyers, units with `ignoresEngagement`, and carriers of an `ignoresEngagement` status are exempt. Effect movement (charge, swap, push, teleport) never pays it.
- Any effect may carry `filter: {flying?, shelled?, faction?: [ids], notFaction?: [ids]}` (only matching units are affected; also on `aura`; `shelled: true` = target's shell is up (shellHp > 0), `false` = it has none), `ifTargetStatus: "<statusId>"` (only targets that had that status when the use began — a snapshot, so an earlier effect in the same use cannot enable it) and `ifTargetStacks: {status: "<statusId>", min: N}` (only targets that had at least N stacks of that status when the use began; same snapshot rule).
- An ability with `target:"empty"` and an `area` hits the units in that area (e.g. `line` + `affects:"enemies"`); cast-level effects such as `teleport` then run once.
- Passive `aura` effects may carry `keepsWet: true`: allies inside count as wet for `dries`.
- `{type:"push", distance, collisionDamage?}` — away from the caster
- `{type:"teleport"}` — caster moves to target tile (target "empty")
- `{type:"pull", distance}` — toward the caster, stops when adjacent or blocked
- `{type:"swap"}` — caster and target unit swap places (not structures)
- `{type:"summon", unit, count?}` — spawns units for the caster's team on/near the target tile; they act next turn
- `{type:"terrain", terrain, duration?}` — changes the target tile (and `area`) to a terrain; reverts after `duration` rounds
- `{type:"essence", amount, team?: "self"|"enemy"}` — gain (or drain, with negative amount)
- `{type:"aura", radius, affects?, statMods}` — only in `passive: true` abilities; continuous stat mods (radius 0 = self only)

- `{type:"aura", ..., perAdjacentAlly: true, maxStacks?}` — swarm bonus: statMods multiplied by the number of allies adjacent to the affected unit
- `{type:"reshed"}` — per unit hit: resets the target's Shed so it can trigger again. No effect on units without `shed`.
- `{type:"shell", amount}` — per unit hit: repairs the target's shell by `amount`, never above its `shell.hp`. No effect on units without `shell`.
- `{type:"rehouse"}` — cast-level, ability only (not spells), the ability must have `target:"tile"` (use range 1). See **Shells**.
- `{type:"moveOut"}` — cast-level, ability only (not spells), the ability must have `target:"empty"` (use range 1). See **Shells**.

Damage types (free text; these are the ones in use): `physical`, `fire`, `salt`, `pressure`, `light`, `brine`, `drowning`, `venom` (new, Slough), plus engine-made `impact` (push collisions), `drying` and `sacrifice`. `venom`, `drying` and `sacrifice` damage, and any `pierce` damage, bypass shells.

Passive abilities: `{name, description, passive: true, effects: [aura...]}`; apCost/range/target can be omitted.
Optional `requires: string[]` on abilities is ignored by the engine (author bookkeeping). Tags for engine features: `terrain`, `draw`, `convert_on_kill`, `untargetable`.

Effect additions:
- `{"type":"draw","count":N}` (requires `draw`): cast-level; the caster's team draws N cards from its deck into hand, stopping at the hand max (8) or an empty deck; emits a `draw` event per card. Allowed in abilities and spells.
- `convertOnKill: "<unitId>"` on a `damage` effect (requires `convert_on_kill`): if the damage kills the target (not a hero, not a structure/Beacon), one `<unitId>` is summoned for the caster's team on the target's tile after the death (acts next turn, like `summon`). Works in abilities and spells.

## Wave 3 mechanics (Slough and Hermitage)

### Venom
Canonical status (statuses.json):
```json
"sl_venom": { "name": "Venom", "stacks": true, "maxStacks": 5, "shedsWhenIdle": true,
  "onAct": [ { "type": "damage", "amount": 1, "damageType": "venom", "ignoreAttack": true, "pierce": true } ] }
```
Apply it with `{ "type": "status", "status": "sl_venom", "duration": 99 }`; several of these in one ability add several stacks
(capped at maxStacks). Each walk and each ability use by the carrier then costs it (stacks x 1) venom damage minus its
`resist.venom`. A carrier that does nothing for a whole turn loses one stack at the end of that turn. Venom damage bypasses
shells. Structures (husks, shells, segments, Beacons) are immune. Pair with `ifTargetStatus: "sl_venom"`,
`ifTargetStacks: {status: "sl_venom", min: N}` and `vsWounded` on other effects.

### Shed
`"shed": { "husk": "<unitId>", "slide": 2 }` on a UnitDef. The first time damage leaves the unit alive with HP below
50% of its base max HP (`stats.hp`): all its statuses are removed, it slides to the free passable tile within `slide`
steps (walking over free tiles only, jump respected) that is farthest from the nearest enemy, and a `husk` unit is
spawned for its team on the tile it left. If no tile is free it stays put, still drops its statuses, and no husk appears.
Once per battle per unit; `{ "type": "reshed" }` re-arms it. A unit that sheds loses its tail segments. The slide is
effect movement: no `onEnter`, no Coiled trigger. If it happens mid-walk the walk ends there (unspent AP refunded).
Husk shape: `{ "structure": true, "decoy": true, "token": true, "cost": 0, "stats": {"hp": 1, ...}, "abilities": [] }`.

### Coiled
`"coiled": { "ability": "<abilityId>" }` on a UnitDef. When its owner's turn ends and it used no ability that turn
(walking is fine; a unit deployed that turn counts), it is Coiled until its owner's next turn starts. During each enemy
turn, the first enemy that walks onto a tile orthogonally adjacent to it (by a move command; flyers included) is hit at once
with that ability's per-unit effects: no AP cost, range ignored, `area`/`affects` measured around the walker's tile, the
walker always hit. Cast-level effects (teleport, summon, terrain, draw, essence, swap, sacrifice, rehouse, moveOut) in the
coiled ability are ignored, so use a plain damage/status ability. Once per enemy turn per coiled unit. The walker stops on
that tile (and gets back the AP for the rest of the walk) if the strike kills it, moves it, roots it (`preventsMove`) or
newly stuns it (`preventsAction`). A coiled unit that is itself stunned does not strike. Tiles the walker only passes
through (occupied by an ally) do not trigger it. Push, pull, swap, teleport, skyfall landings and slides never trigger it.
The strike emits `react` then a normal `ability` event. It does not trigger the striker's Venom.

### Shells, eviction and rehousing
- `"shell": { "hp": N, "evicted": "<unitId>", "leaves": "<unitId>" }`. The unit enters play (deployed, summoned,
  pre-placed or rehoused) with `shellHp = N` (rehousing into an empty shell: that object's current HP). Every damage hit
  is reduced by defense/terrain/resist as normal and then lands on the shell first; when shellHp reaches 0 the rest of that
  hit is discarded and the unit is **Evicted**: it becomes `shell.evicted` (new stats, abilities, sprite, traits), body HP
  carries over capped to the new max, statuses and equipment stay, ability cooldowns are cleared, AP is capped to the new
  max. `pierce` damage and `venom`/`drying`/`sacrifice` damage skip the shell and hit the body. Healing heals the body only.
- `shell.onBreak?: Effect[]` — cast-level effects run for the owner at the unit's tile when the shell breaks (forced eviction
  only, not moveOut). Only `essence`, `summon`, `terrain` and `draw` are allowed, e.g. `[{"type":"essence","amount":4}]`.
- Evicted forms are ordinary UnitDefs, mark them `"token": true` (cost 0). A champion that dies after being evicted (or after
  rehousing into something else) still puts the card it was DEPLOYED as on cooldown and spills that card's Tide.
- Heroes: give the hero's evicted form its own token UnitDef without `hero: true`. The unit still counts and shows as a hero
  (crown, AI value, convertOnKill immunity, one-per-side) because the card it was deployed as is a hero (`Game.isHero`).
- Tidewatch Tempering: a tempered shelled champion's evicted form gets the same Tempering stat bonuses and rank abilities
  (as a synthesized `tw:<evicted>:<rank>:<card>` token). Rehousing into a different shelled unit does not carry Tempering.
- Several UnitDefs may share art through `sprite.image` / `sprite.sheet` / `sprite.manifest`; the renderer looks the art up
  from the unit's current definition every frame, so the sprite swaps on eviction/rehouse.
- Empty shells: `{ "structure": true, "token": true, "emptyShell": { "becomes": "<shelled unitId>" }, "stats": {"hp": N, ...}, "abilities": [] }`.
  They belong to a team, block movement (even for allies), can be attacked, never count for `eliminate`, hold no Wells,
  drop no Tide. A spell or ability drops one with the normal `summon` effect (full `stats.hp`).
- `{ "type": "rehouse" }` in an ability with `"target": "tile"`, range 1. The caster must have no `shell` in its current
  form (the ability is unusable otherwise). Valid target tiles (only these are offered): a tile holding a friendly empty
  shell, or an unoccupied tile whose terrain has `shellSource`. Empty shell: the shell object vanishes, the caster steps onto
  its tile and becomes `emptyShell.becomes` with shellHp = the object's current HP (capped at that unit's `shell.hp`).
  shellSource tile: the caster steps onto it, becomes that unit with a full shell, and the tile turns into `salt_flat`.
- `{ "type": "moveOut" }` in an ability with `"target": "empty"`, range 1. The caster must have a `shell` (unusable
  otherwise). It steps to the target tile as its `shell.evicted` form and leaves `shell.leaves` (an empty-shell unit of its
  team, HP = its shellHp at that moment) on the tile it left. No shell is left if `leaves` is absent or shellHp is 0.
- `{ "type": "shell", "amount": N }` repairs the target's shell by N (up to `shell.hp`). Allowed in abilities and spells.
- `filter: { "shelled": true|false }` on any effect, passive `aura` effects included: target's shell up (shellHp > 0) or not.
- Every definition change (eviction, rehouse, moveOut) clears ability cooldowns; abilities already used this turn stay used.
- Rehouse/moveOut steps are effect movement (no AP for the step, no `onEnter`, no Coiled trigger). They emit `move` + `rehouse`/`evict`.

### Long bodies
`"tail": { "segment": "<unitId>", "length": 1-3 }` on a UnitDef; the segment is a structure unit (`"token": true`, cost 0,
no abilities; its HP is irrelevant). After each walk the head lays its tail on the tiles it just walked (newest first),
then on the tiles its old tail covered, skipping occupied and impassable tiles, up to `length` segments. A unit has no
tail until its first walk; a 1-tile walk with no old tail gives 1 segment. Segments are structures of the head's team:
they block movement (the head itself may walk over its own tail but not stop on it), are never healed, take no statuses,
and hold no Wells. Damage that hits a segment is dealt to the head instead (computed against the head's defense and
resist), and an area that hits several segments and/or the head deals that effect to the head only once. Segments vanish
when the head dies, sheds, or changes into a form without `tail`. There is no line of sight in the engine, so segments
do not block sight. A long unit must still be a good unit without its tail. Non-damage effects (push, status...) on a
segment affect the segment (a structure), i.e. nothing.

### Events (for UI)
`damage` gains `shell?: true` (the hit landed on the shell). New: `shed {uid, from, to, husk?}`,
`evict {uid, from, to, at, voluntary?}` (voluntary = moveOut; `at` = where the unit stands after it), `rehouse {uid, from, to, at}`, `shell {uid, amount}` (repair),
`react {uid, target, ability}` (Coiled strike), `vanish {uid}` (removed without dying: expired husk, used empty shell,
old tail segment). A unit's `defId` can change mid-battle; its `deployedAs` keeps the id it entered play as.

## Cards: the warband is a deck
A warband / roster / unlock list may contain unit ids, spell ids and equipment ids. Ids must be unique across
units, spells and equipment. Everything is played from the hand by paying its `cost` in essence on your turn.

## content/spells.json — `{ [spellId]: SpellDef }`
`name, description, faction?, cost, castRange? (number: within N tiles of one of your units; {nearKeystone: N}: within N of your keystone; omit = anywhere),
target: "enemy"|"ally"|"unit"|"tile"|"empty", area?, affects?, effects, icon?`.
Spell damage is the flat `amount` minus defense/terrain (unless `pierce`) minus resist, min 1 before resist.
Allowed effects: damage, heal, status, push/pull (away from / toward the target tile), summon, terrain, essence.

## content/equipment.json — `{ [equipmentId]: EquipmentDef }`
`name, description, faction?, cost, statMods?, grantAbilities?: abilityId[], resist?, restrictTo?: (unitId|role)[], icon?`.
Attached to one of your units on the board; one item per unit; lasts until the unit dies.

## content/statuses.json — `{ [statusId]: StatusDef }`
`name, description, onTurnStart?: Effect[] (damage/heal only), preventsMove?, preventsAction?, statMods?: {attack?, defense?, ap?},
stacks?: bool, maxStacks?, wet?: bool (carrier does not dry out), ignoresEngagement?: bool (carrier never pays the engagement cost),
onAct?: Effect[] (damage only), shedsWhenIdle?: bool` — stacking statuses add a stack on re-application; statMods, onTurnStart and onAct amounts are multiplied by stacks.
- `onAct`: applied to the carrier right after each of its own actions resolves: one walk (any length; one per move command) or one ability use (including a `rehouse`/`moveOut`). Not after cards played from the hand, not after a Coiled reaction strike, not after effect movement. Amount x stacks, then defense/terrain (unless `pierce`) and the carrier's `resist[damageType]` exactly like spell damage (min 1 before resist, can reach 0 after resist).
- `shedsWhenIdle`: at the END of the owner's turn, a carrier that took no action that turn (no walk, no ability) loses one stack; at 0 stacks the status is removed.
- Structures never receive statuses.

## content/terrain.json — `{ [terrainId]: TerrainDef }`
`name, moveCost, defense, color (placeholder tile colour), impassable?, onEnter?: Effect, wet?: bool` — `wet` tiles (and always `brine_pool`, `living_reef`) stop `dries` units losing HP.
Extra optional fields:
- `void: true` — a chasm: empty space. The renderer draws no tile at all (neighbours show their cliff faces down into it), and nothing can stand, deploy, land, spawn or be pushed there. Always also set `impassable: true`. Flyers may cross it but not end on it.
- `description` — one line shown when hovering the tile.
- `onTurnStart: Effect[]` — applied to each unit that starts its turn standing here (after drying, before status effects). Only `damage`, `heal` and `status` are allowed; each effect's `filter` is respected; heals cap at max HP. Flyers are skipped (like `onEnter`), as are units that landed this turn.
- `rangeBonus: number` — added to the max range of abilities with `range.max > 1` used from this tile (stacks with the +1 high-ground bonus). Melee is unaffected.
- `factionMoveCost: { [factionId]: number }` — move cost (>= 1) replacing `moveCost` for non-flying units whose `UnitDef.faction` matches. Faction ids must exist in `factions` when it is defined.
- `underlay: terrainId` — renderer hint: terrain drawn beneath this tile's art.
- Negative `defense` is allowed (the tile makes its occupant easier to hurt).
- `onEnter` effects honour `filter` too, e.g. `{ "filter": { "notFaction": ["reef_ascendant"] } }`.
- `shellSource: unitId` — a `rehouse` aimed at this tile (when nothing stands on it) turns the caster into this unit with a full shell, and the tile becomes `salt_flat` (which must exist). The unit must have a `shell`.

`EffectFilter` (the `filter` on damage/heal/status/aura effects): `flying?: bool`, `shelled?: bool`, `faction?: string[]` (only units whose faction is listed), `notFaction?: string[]` (units whose faction is not listed; units with no faction always pass). All present keys must match. Faction ids must exist in `factions` when it is defined.

## content/maps/<id>.json
`id, name, description, legend {char: terrainId}, tiles: string[] (rows), heights: string[] (digit rows, 0-9),
keystones: [{team, x, y}], deployZones: {"0": [[x,y]...], "1": [...]}, wells?: [{x, y, amount}]`.
A well grants `amount` (default 10) essence at the start of a team's turn if one of its units stands on it. Row strings must all be the same width.

## content/missions/<id>.json — MissionDef
| field | type | notes |
|---|---|---|
| id, name, description | string | |
| map | string | map id |
| briefing | string[]? | shown before the mission, one paragraph per entry |
| victoryText / defeatText | string? | shown at the end |
| startingEssence / essencePerTurn / maxEssence | number? | defaults 100 / 25 / 200 |
| teams | MissionTeam[] | index 0 = player, 1 = opponent |
| objectives | {victory?: Condition[], defeat?: Condition[]} | ANY condition met ends the mission. Default: destroy the other side's keystone or eliminate them |
| events | MissionEvent[]? | scripted triggers |

MissionTeam: `name, color, controller ("human"|"ai"), warband?: unitId[] (deployable with essence),
useCampaignRoster?: bool (player warband comes from the campaign roster), units?: [{unit, x, y, tag?}] (pre-placed),
keystone?: bool (default true if the map has one for this team), startingEssence?, essencePerTurn?` (per-team overrides).

Conditions:
`{type:"destroy_keystone", team}`, `{type:"eliminate", team}`, `{type:"defeat_unit", tag}` (every unit with the tag dead),
`{type:"unit_lost", tag}` (any unit with the tag dead), `{type:"survive", turns}`, `{type:"turn_limit", turns}`,
`{type:"reach_tile", team, tiles:[[x,y]...], tag?}`, `{type:"unit_hp_above", tag, fraction}`.
Every condition also takes `not: true` (invert) and `label` (objective text shown to the player).
"turns" counts full rounds (both sides have moved).

MissionEvent: `{when: {turn: N, team?} | {unitDefeated: tag}, do: Action[], once?: bool (default true)}`.
Actions: `{type:"message", text, speaker?}`, `{type:"spawn", team, unit, x, y, tag?}`, `{type:"grant_essence", team, amount}`,
`{type:"terrain", x, y, terrain, radius?, duration?}`, `{type:"status", tag, status, duration}`.

Teams: a mission can have 3+ teams (e.g. a neutral monster team at index 2). All teams are hostile to each other;
turns go 0, 1, 2, ... and a round ends after the last team.

## content/campaigns.json — `{ [campaignId]: CampaignDef }`
`name, description, startingRoster: unitId[], missions: [{mission: missionId, unlocks?: unitId[]}]`.
Missions are played in order; winning one adds its `unlocks` to the roster and opens the next. Progress is saved in the browser.

## content/config.json
`{ "labels": { "title": "...", "subtitle": "...", "essence": "Tide", "keystone": "Beacon", "warband": "..." } }` — game title and player-facing names for engine terms.

## content/factions.json
`{ [factionId]: { name, color, accent?, tagline? } }` — used by Quick battle (faction vs faction on any map). A faction's
default deck is its hero, its champions, then its spells and equipment.

## Sprites
`sprite.image: "sprites/<file>"` resolves to `content/sprites/<file>` and is bundled. Missing files fall back to the placeholder shape.

## Rules summary (for designers)
- Cooldown N: after use, the ability is unavailable for your next N−1 turns.
- Side-based turns. Each unit has AP: walking costs terrain moveCost per tile, abilities cost apCost.
- Essence: spend to deploy warband units onto your deploy zone. Units deployed this turn cannot act until next turn.
- Win by destroying the enemy Keystone or every enemy unit.
- Height: +1 damage per level the attacker stands above the target (max +3); −1 per level below (min −2).

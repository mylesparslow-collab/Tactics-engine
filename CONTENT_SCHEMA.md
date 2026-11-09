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
- Any effect may carry `filter: {flying?, faction?: [ids], notFaction?: [ids]}` (only matching units are affected; also on `aura`) and `ifTargetStatus: "<statusId>"` (only targets that had that status when the use began — a snapshot, so an earlier effect in the same use cannot enable it).
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

Passive abilities: `{name, description, passive: true, effects: [aura...]}`; apCost/range/target can be omitted.
Optional `requires: string[]` on abilities is ignored by the engine (author bookkeeping).

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
stacks?: bool, maxStacks?, wet?: bool (carrier does not dry out), ignoresEngagement?: bool (carrier never pays the engagement cost)` — stacking statuses add a stack on re-application; statMods and onTurnStart amounts are multiplied by stacks.

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

`EffectFilter` (the `filter` on damage/heal/status/aura effects): `flying?: bool`, `faction?: string[]` (only units whose faction is listed), `notFaction?: string[]` (units whose faction is not listed; units with no faction always pass). All present keys must match. Faction ids must exist in `factions` when it is defined.

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

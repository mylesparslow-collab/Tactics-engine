// ---------- Content definitions (loaded from JSON) ----------
export type Pos = { x: number; y: number };
export type StatBlock = { hp: number; ap: number; attack: number; defense: number; jump: number };
export type StatKey = keyof StatBlock;

/** Only units whose flags match are affected. Currently just `flying`. */
/** Restricts who an effect touches. All present keys must match; `faction` / `notFaction` compare UnitDef.faction. */
export interface EffectFilter { flying?: boolean; faction?: string[]; notFaction?: string[] }

/** Any effect may also carry `ifTargetStatus`: it only applies to targets that had that status when the use began. */
export type Effect = EffectBody & { ifTargetStatus?: string };
type EffectBody =
  | { type: 'damage'; amount: number; damageType?: string; ignoreAttack?: boolean; pierce?: boolean;
      /** +`bonus` to the amount (before defense/resist) when the target's current HP is below `below` x its max HP. */
      vsWounded?: { below: number; bonus: number }; filter?: EffectFilter;
      /** If this kills the target (not a hero, not a Beacon/keystone), summon one of this unit for the caster's team on its tile. */
      convertOnKill?: string }
  | { type: 'heal'; amount: number; target?: 'caster'; filter?: EffectFilter }
  | { type: 'sacrifice' }
  /** status target 'caster': applied to the caster once per use instead of to each unit hit. */
  | { type: 'status'; status: string; duration: number; target?: 'caster'; filter?: EffectFilter }
  | { type: 'push'; distance: number; collisionDamage?: number }
  | { type: 'teleport' }
  | { type: 'pull'; distance: number }
  | { type: 'swap' }
  | { type: 'summon'; unit: string; count?: number }
  /** The caster's team draws `count` cards into hand (respecting the hand limit). */
  | { type: 'draw'; count: number }
  | { type: 'terrain'; terrain: string; duration?: number }
  | { type: 'essence'; amount: number; team?: 'self' | 'enemy' }
  | { type: 'aura'; radius: number; affects?: Affects; statMods?: Partial<Record<StatKey, number>>; resist?: Record<string, number>;
      /** Multiply statMods by the number of allies adjacent to the affected unit (swarm bonus), capped at maxStacks. */
      perAdjacentAlly?: boolean; maxStacks?: number; filter?: EffectFilter;
      /** Units inside this aura count as wet for the `dries` rule. */
      keepsWet?: boolean };

/** Effects applied once per cast (at the target tile) rather than once per affected unit. */
export const CAST_LEVEL_EFFECTS = ['teleport', 'summon', 'terrain', 'essence', 'swap', 'sacrifice', 'draw'] as const;

export type TargetKind = 'enemy' | 'ally' | 'unit' | 'tile' | 'empty' | 'self';
export type Affects = 'enemies' | 'allies' | 'all';

export interface AbilityDef {
  name: string;
  description?: string;
  apCost: number;
  cooldown?: number;
  range: { min: number; max: number };
  target: TargetKind;
  /** radius: diamond around the target. line: `size` tiles from the caster through the target. */
  area?: { shape: 'radius' | 'line'; size: number };
  affects?: Affects;
  effects: Effect[];
  /** Passive abilities are never cast; their 'aura' effects apply continuously. */
  passive?: boolean;
  requires?: string[];
  /** Live visual effect at the target (src/render/fx.ts preset: smoke, ink, murk, mist, salt, ...). */
  vfx?: string;
}

/** A card cast straight from the hand for essence (no unit needed). */
export interface SpellDef {
  name: string;
  description?: string;
  faction?: string;
  cost: number;
  /** Must target within this many tiles of a friendly unit; omit for anywhere on the map. */
  castRange?: number | { nearKeystone: number };
  target: Exclude<TargetKind, 'self'>;
  area?: { shape: 'radius'; size: number };
  affects?: Affects;
  effects: Effect[];
  icon?: string;
  /** How the spell animates (src/render/spellfx.ts: beam, hail, fall, glyph, summon, geyser, crush, vortex,
   *  blast, cloud, drain, heal, growth, feathers, hex); defaults from its effects. */
  anim?: string;
  /** The particle preset the animation uses (src/render/fx.ts: smoke, ink, salt, water, coral, ...). */
  vfx?: string;
}

/** A card attached to a friendly unit from the hand; lasts until the unit dies. One per unit. */
export interface EquipmentDef {
  name: string;
  description?: string;
  faction?: string;
  cost: number;
  statMods?: Partial<Record<StatKey, number>>;
  grantAbilities?: string[];
  resist?: Record<string, number>;
  /** Only units whose role or id is listed may equip it; omit for any. */
  restrictTo?: string[];
  icon?: string;
}

export type CardKind = 'unit' | 'spell' | 'equipment';

export interface StatusDef {
  name: string;
  description?: string;
  onTurnStart?: Effect[];
  preventsMove?: boolean;
  preventsAction?: boolean;
  statMods?: Partial<Record<StatKey, number>>;
  /** Re-applying adds a stack (up to maxStacks); statMods and onTurnStart amounts scale with stacks. */
  stacks?: boolean;
  maxStacks?: number;
  /** A unit carrying this status walks away from adjacent enemies without paying the engagement cost. */
  ignoresEngagement?: boolean;
  /** A unit carrying this status counts as standing in water (it does not dry out). */
  wet?: boolean;
  /** A unit carrying this status cannot be directly targeted by enemy abilities or spells (area effects not centred on it still hit). */
  untargetable?: boolean;
  /** Live visual effect clinging to the unit while it has the status (src/render/fx.ts preset). */
  vfx?: string;
}

export interface TerrainDef {
  name: string;
  moveCost: number;
  defense: number;
  color: string;
  impassable?: boolean;
  /** Empty space: nothing is drawn, nothing can stand, land, spawn or be pushed here (flyers may cross). Implies impassable. */
  void?: boolean;
  onEnter?: Effect;
  /** Units standing here do not dry out (see UnitDef.dries). `brine_pool` and `living_reef` are always wet. */
  wet?: boolean;
  description?: string;
  /** Applied to each unit that starts its turn standing here (damage / heal / status only; filters respected; flyers skip). */
  onTurnStart?: Effect[];
  /** Added to the max range of ranged abilities (range.max > 1) used by a unit standing here. */
  rangeBonus?: number;
  /** Per-faction move cost override for non-flyers, e.g. { "reef_ascendant": 1 }. */
  factionMoveCost?: Record<string, number>;
  /** Terrain drawn beneath this tile's art (renderer hint). */
  underlay?: string;
}

export interface UnitDef {
  name: string;
  role?: string;
  faction?: string;
  description?: string;
  cost: number;
  structure?: boolean;
  stats: StatBlock;
  abilities: string[];
  sprite: { shape: string; glyph: string; image?: string; color?: string };
  /** Flat damage reduction per damageType (negative = weakness). */
  resist?: Record<string, number>;
  /** Heroes are unique: at most one copy per warband, shown with a crown. */
  hero?: boolean;
  /** Comes back once on death with this fraction of max HP. */
  revive?: { hpFraction: number };
  /** May also be deployed on any empty passable tile beyond 2 of the enemy keystone; lands at the start of the owner's next turn. */
  skyfall?: { impact: number };
  /** Loses this many HP at the start of its owner's turn unless on a wet tile or carrying a wet status. */
  dries?: number;
  /** Never pays the extra AP to leave an adjacent enemy (flyers already don't). */
  ignoresEngagement?: boolean;
  /** Every passable tile costs 1 AP, no jump limit, may cross (not end on) impassable tiles, ignores onEnter, holds no Wells. */
  flying?: boolean;
}

export interface MapDef {
  id: string;
  name: string;
  description?: string;
  legend: Record<string, string>;
  tiles: string[];
  heights: string[];
  keystones?: { team: number; x: number; y: number }[];
  deployZones: Record<string, [number, number][]>;
  /** Tiles that grant essence at turn start to the team holding them with a unit. */
  wells?: { x: number; y: number; amount: number }[];
}

// ---- Missions & campaigns ----
/** `not` inverts the condition; `label` overrides the objective text shown to the player. */
export type Condition = ConditionBody & { not?: boolean; label?: string };
type ConditionBody =
  | { type: 'destroy_keystone'; team: number }
  | { type: 'eliminate'; team: number }
  | { type: 'defeat_unit'; tag: string }
  | { type: 'unit_lost'; tag: string }
  | { type: 'survive'; turns: number }
  | { type: 'turn_limit'; turns: number }
  | { type: 'reach_tile'; team: number; tiles: [number, number][]; tag?: string }
  | { type: 'unit_hp_above'; tag: string; fraction: number };

export type MissionAction =
  | { type: 'message'; text: string; speaker?: string }
  | { type: 'spawn'; team: number; unit: string; x: number; y: number; tag?: string }
  | { type: 'grant_essence'; team: number; amount: number }
  | { type: 'terrain'; x: number; y: number; terrain: string; radius?: number; duration?: number }
  | { type: 'status'; tag: string; status: string; duration: number };

export type Trigger =
  | { turn: number; team?: number }
  | { unitDefeated: string };

export interface MissionEvent { when: Trigger; do: MissionAction[]; once?: boolean }

export interface PlacedUnit { unit: string; x: number; y: number; tag?: string; /** Equipment id attached at the start of the battle. */ equipment?: string }

export interface MissionTeam {
  name: string;
  color: string;
  controller: 'human' | 'ai';
  warband?: string[];
  useCampaignRoster?: boolean;
  units?: PlacedUnit[];
  keystone?: boolean; // default true when the map defines one for this team
  startingEssence?: number;
  essencePerTurn?: number;
}

export interface MissionDef {
  id: string;
  name: string;
  description?: string;
  map: string;
  briefing?: string[];
  victoryText?: string;
  defeatText?: string;
  startingEssence?: number;
  essencePerTurn?: number;
  maxEssence?: number;
  /** Holding a Tide Well lets a team deploy next to it (default true). */
  wellDeploy?: boolean;
  teams: MissionTeam[];
  objectives?: { victory?: Condition[]; defeat?: Condition[] };
  events?: MissionEvent[];
}

export interface CampaignDef {
  name: string;
  description?: string;
  /** The faction whose story this is; names the campaign's tab and colours it. */
  faction?: string;
  startingRoster: string[];
  missions: { mission: string; unlocks?: string[] }[];
}

export interface GameConfig {
  /** Player-facing names for engine terms, e.g. { essence: "Tide", keystone: "Beacon" }. */
  labels?: Record<string, string>;
}

export interface FactionDef { name: string; color: string; accent?: string; tagline?: string }

export interface Content {
  config?: GameConfig;
  factions?: Record<string, FactionDef>;
  units: Record<string, UnitDef>;
  abilities: Record<string, AbilityDef>;
  spells: Record<string, SpellDef>;
  equipment: Record<string, EquipmentDef>;
  statuses: Record<string, StatusDef>;
  terrain: Record<string, TerrainDef>;
  maps: Record<string, MapDef>;
  missions: Record<string, MissionDef>;
  campaigns: Record<string, CampaignDef>;
}

// ---------- Runtime state ----------
export interface Tile { terrain: string; height: number }

export interface StatusInstance { id: string; remaining: number; stacks?: number }

export interface Unit {
  uid: number;
  defId: string;
  team: number;
  x: number;
  y: number;
  hp: number;
  ap: number;
  statuses: StatusInstance[];
  cooldowns: Record<string, number>;
  summonedThisTurn: boolean;
  /** Abilities already used this turn (each ability once per turn). */
  usedAbilities?: string[];
  tag?: string;
  alive: boolean;
  revived?: boolean;
  equipment?: string;
  /** Deployed from the hand (or landed by skyfall): goes on cooldown and returns to the hand when it dies. */
  fromCard?: boolean;
}

/** Tide spilled where a unit died; the first unit to step on the tile collects it for its team. */
export interface TideDrop { x: number; y: number; amount: number }

/** A played spell/equipment or a fallen champion resting before it returns to the hand. */
export interface CardCooldown { card: string; turns: number }

/** A skyfall unit that has been paid for and is on its way down; it lands at the start of its owner's next turn. */
export interface Landing { uid: number; defId: string; team: number; x: number; y: number }

export interface TeamState {
  name: string;
  color: string;
  controller: 'human' | 'ai';
  essence: number;
  hand: string[]; // cards you can play now: unit, spell or equipment ids
  /** Shuffled draw pile (rest of the Chart). One card is drawn at the start of each of your turns. */
  deck: string[];
  /** Cards on cooldown: each ticks down at the start of the owner's turn and returns to the hand at 0. */
  cooldown: CardCooldown[];
}

export type Phase = 'playing' | 'victory' | 'defeat';

export type GameEvent =
  | { kind: 'move'; uid: number; path: Pos[] }
  | { kind: 'ability'; uid: number; ability: string; target: Pos }
  | { kind: 'damage'; uid: number; amount: number; damageType?: string }
  | { kind: 'heal'; uid: number; amount: number }
  | { kind: 'status'; uid: number; status: string }
  | { kind: 'push'; uid: number; from: Pos; to: Pos }
  | { kind: 'death'; uid: number }
  | { kind: 'revive'; uid: number; hp: number }
  | { kind: 'essence'; team: number; amount: number; at?: Pos }
  | { kind: 'terrain'; x: number; y: number; terrain: string }
  | { kind: 'deploy'; uid: number }
  | { kind: 'skyfall'; uid: number; team: number; defId: string; x: number; y: number }
  | { kind: 'land'; uid: number; from: Pos; to: Pos }
  | { kind: 'spell'; team: number; spell: string; target: Pos }
  | { kind: 'equip'; uid: number; equipment: string }
  | { kind: 'turn'; team: number; turn: number }
  | { kind: 'draw'; team: number; card: string }
  | { kind: 'cooldown'; team: number; card: string; turns: number }
  | { kind: 'ready'; team: number; card: string; toHand: boolean }
  | { kind: 'drop'; x: number; y: number; amount: number }
  | { kind: 'pickup'; uid: number; team: number; x: number; y: number; amount: number }
  | { kind: 'message'; text: string; speaker?: string }
  | { kind: 'end'; phase: Phase };

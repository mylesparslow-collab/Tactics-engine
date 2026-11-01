// ---------- Content definitions (loaded from JSON) ----------
export type Pos = { x: number; y: number };
export type StatBlock = { hp: number; ap: number; attack: number; defense: number; jump: number };
export type StatKey = keyof StatBlock;

export type Effect =
  | { type: 'damage'; amount: number; damageType?: string; ignoreAttack?: boolean; pierce?: boolean }
  | { type: 'heal'; amount: number; target?: 'caster' }
  | { type: 'sacrifice' }
  | { type: 'status'; status: string; duration: number }
  | { type: 'push'; distance: number; collisionDamage?: number }
  | { type: 'teleport' }
  | { type: 'pull'; distance: number }
  | { type: 'swap' }
  | { type: 'summon'; unit: string; count?: number }
  | { type: 'terrain'; terrain: string; duration?: number }
  | { type: 'essence'; amount: number; team?: 'self' | 'enemy' }
  | { type: 'aura'; radius: number; affects?: Affects; statMods?: Partial<Record<StatKey, number>>; resist?: Record<string, number>;
      /** Multiply statMods by the number of allies adjacent to the affected unit (swarm bonus), capped at maxStacks. */
      perAdjacentAlly?: boolean; maxStacks?: number };

/** Effects applied once per cast (at the target tile) rather than once per affected unit. */
export const CAST_LEVEL_EFFECTS = ['teleport', 'summon', 'terrain', 'essence', 'swap', 'sacrifice'] as const;

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
}

export interface TerrainDef {
  name: string;
  moveCost: number;
  defense: number;
  color: string;
  impassable?: boolean;
  onEnter?: Effect;
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

export interface PlacedUnit { unit: string; x: number; y: number; tag?: string }

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
  teams: MissionTeam[];
  objectives?: { victory?: Condition[]; defeat?: Condition[] };
  events?: MissionEvent[];
}

export interface CampaignDef {
  name: string;
  description?: string;
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
  tag?: string;
  alive: boolean;
  revived?: boolean;
  equipment?: string;
}

export interface TeamState {
  name: string;
  color: string;
  controller: 'human' | 'ai';
  essence: number;
  hand: string[]; // undeployed warband cards: unit, spell or equipment ids
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
  | { kind: 'essence'; team: number; amount: number }
  | { kind: 'terrain'; x: number; y: number; terrain: string }
  | { kind: 'deploy'; uid: number }
  | { kind: 'spell'; team: number; spell: string; target: Pos }
  | { kind: 'equip'; uid: number; equipment: string }
  | { kind: 'turn'; team: number; turn: number }
  | { kind: 'message'; text: string; speaker?: string }
  | { kind: 'end'; phase: Phase };

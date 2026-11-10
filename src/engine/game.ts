import { CAST_LEVEL_EFFECTS } from './types';
import type {
  EffectFilter,
  AbilityDef, Affects, CardKind, EquipmentDef, SpellDef, Condition, Content, Effect, GameEvent, MapDef, MissionAction, MissionDef,
  Landing, Phase, Pos, StatKey, TeamState, TideDrop, Tile, Unit, UnitDef,
} from './types';

export const DEFAULTS = { startingEssence: 100, essencePerTurn: 25, maxEssence: 200 };
/** Card draw: opening hand size, cards drawn per turn, hand limit (a full hand skips the draw; the card stays on top). */
export const DRAW = { opening: 5, perTurn: 2, maxHand: 8, minOpeningUnits: 2 };
/**
 * Card cooldowns (PoxNora-style rune rest): a cast spell, an attached equipment, or a champion that dies rests for
 * max(min, ceil(cost / tidePerTurn)) of its owner's turns, then returns to the hand (or the top of the draw pile if the hand is full).
 */
export const COOLDOWN = { tidePerTurn: 15, min: 2 };
export const cooldownFor = (cost: number) => Math.max(COOLDOWN.min, Math.ceil(cost / COOLDOWN.tidePerTurn));
/** Tide a dying champion spills on its tile: max(min, cost × fraction) rounded to 5. Free summons and structures drop nothing. */
/** Extra AP to walk away from an adjacent enemy (see Game.disengageCost). */
export const ENGAGE_COST = 2;

export const TIDE_DROP = { fraction: 0.25, min: 5 };
/** Damage types that skip a shell and hit the body (pierce damage does too). */
export const SHELL_BYPASS = ['venom', 'drying', 'sacrifice'];
export const tideDropFor = (cost: number) => cost > 0 ? Math.max(TIDE_DROP.min, Math.round(cost * TIDE_DROP.fraction / 5) * 5) : 0;

/** Small seeded PRNG (mulberry32) so a game can be replayed from its seed. */
export function rng(seed: number) {
  let a = seed >>> 0;
  return () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
const key = (x: number, y: number) => `${x},${y}`;
export const manhattan = (a: Pos, b: Pos) => Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
const DIRS: Pos[] = [{ x: 1, y: 0 }, { x: -1, y: 0 }, { x: 0, y: 1 }, { x: 0, y: -1 }];

export interface ReachNode { cost: number; prev: string | null }
export interface GameOptions { roster?: string[]; /** Shuffle seed; random when omitted. */ seed?: number }

/**
 * Rules engine. Pure game logic, no rendering. All mutations go through the public action methods
 * (move, useAbility, deploy, endTurn), which validate and return false when illegal.
 */
export class Game {
  readonly content: Content;
  readonly mission: MissionDef;
  readonly map: MapDef;
  readonly width: number;
  readonly height: number;
  readonly tiles: Tile[][];
  units: Unit[] = [];
  /** Skyfall units in flight: paid for, shown as a marker, landing at the start of their owner's next turn. */
  landings: Landing[] = [];
  /** Tide lying on the board where units fell. */
  drops: TideDrop[] = [];
  teams: TeamState[];
  current = 0;
  round = 1;
  phase: Phase = 'playing';
  log: GameEvent[] = [];
  private listeners: ((e: GameEvent) => void)[] = [];
  private nextUid = 1;
  /** Counts every turn start (any team); Coiled strikes are once per enemy turn. */
  private turnNo = 0;
  private firedEvents = new Set<number>();
  readonly seed: number;
  /** Seeded randomness for shuffles. */
  readonly random: () => number;
  private shuffle<T>(xs: T[]): T[] {
    const a = [...xs];
    for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(this.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
    return a;
  }
  /** Temporary terrain changes, reverted when `remaining` rounds have passed. */
  private terrainTimers: { x: number; y: number; prev: string; remaining: number }[] = [];

  constructor(content: Content, missionId: string, opts: GameOptions = {}) {
    this.content = content;
    const mission = content.missions[missionId];
    if (!mission) throw new Error(`Unknown mission ${missionId}`);
    this.mission = mission;
    this.map = content.maps[mission.map];
    this.height = this.map.tiles.length;
    this.width = this.map.tiles[0].length;
    this.tiles = this.map.tiles.map((row, y) =>
      [...row].map((ch, x) => ({ terrain: this.map.legend[ch], height: Number(this.map.heights[y][x]) })));

    const start = mission.startingEssence ?? DEFAULTS.startingEssence;
    this.teams = mission.teams.map(t => ({
      name: t.name, color: t.color, controller: t.controller, essence: t.startingEssence ?? start,
      hand: [...((t.useCampaignRoster && opts.roster) ? opts.roster : (t.warband ?? []))], deck: [], cooldown: [],
    }));
    this.seed = opts.seed ?? Math.floor(Math.random() * 2 ** 31);
    this.random = rng(this.seed);
    mission.teams.forEach((t, team) => {
      const ks = this.map.keystones?.find(k => k.team === team);
      if (ks && t.keystone !== false) this.spawn('keystone', team, ks.x, ks.y, `keystone_${team}`);
      t.units?.forEach(u => { const s = this.spawn(u.unit, team, u.x, u.y, u.tag); if (u.equipment && this.content.equipment[u.equipment]) s.equipment = u.equipment; });
    });
    // Heroes are unique: a hero already on the field is not also in the hand (campaign rosters list the commander).
    this.teams.forEach((t, team) => {
      const seen = new Set(this.units.filter(u => u.team === team && this.isHero(u)).map(u => u.deployedAs ?? u.defId));
      t.hand = t.hand.filter(id => { if (!this.content.units[id]?.hero) return true; if (seen.has(id)) return false; seen.add(id); return true; });
    });
    // Shuffle each Chart and draw the opening hand. Short warbands (scripted fights, tests) stay fully in hand.
    for (const t of this.teams) {
      if (t.hand.length <= DRAW.opening) continue;
      const pile = this.shuffle(t.hand);
      const hand = pile.splice(0, DRAW.opening);
      // No hopeless openers: make sure there are a couple of champions to deploy.
      const isUnit = (id: string) => this.cardKind(id) === 'unit';
      while (hand.filter(isUnit).length < DRAW.minOpeningUnits) {
        const ui = pile.findIndex(isUnit), ni = hand.findIndex(id => !isUnit(id));
        if (ui < 0 || ni < 0) break;
        [hand[ni], pile[ui]] = [pile[ui], hand[ni]];
      }
      t.hand = hand; t.deck = pile;
    }
    // Pre-placed units can act on turn 1.
    for (const u of this.units) { u.summonedThisTurn = false; u.ap = this.stat(u, 'ap'); }
    this.beginTurn();
  }

  // ---------- events ----------
  on(fn: (e: GameEvent) => void) { this.listeners.push(fn); return () => { this.listeners = this.listeners.filter(l => l !== fn); }; }
  private emit(e: GameEvent) { this.log.push(e); for (const l of this.listeners) l(e); }

  // ---------- queries ----------
  def(u: Unit): UnitDef { return this.content.units[u.defId]; }
  ability(id: string): AbilityDef { return this.content.abilities[id]; }
  inBounds(x: number, y: number) { return x >= 0 && y >= 0 && x < this.width && y < this.height; }
  tile(x: number, y: number): Tile | undefined { return this.inBounds(x, y) ? this.tiles[y][x] : undefined; }
  terrainAt(x: number, y: number) { return this.content.terrain[this.tiles[y][x].terrain]; }
  unitAt(x: number, y: number) { return this.units.find(u => u.alive && u.x === x && u.y === y); }
  unit(uid: number) { return this.units.find(u => u.uid === uid); }
  aliveUnits(team?: number) { return this.units.filter(u => u.alive && (team === undefined || u.team === team)); }

  /** Innate abilities plus any granted by equipment. */
  abilitiesOf(u: Unit): string[] {
    const eq = this.equipmentOf(u);
    return eq?.grantAbilities ? [...this.def(u).abilities, ...eq.grantAbilities] : this.def(u).abilities;
  }
  equipmentOf(u: Unit): EquipmentDef | undefined { return u.equipment ? this.content.equipment[u.equipment] : undefined; }
  resistOf(u: Unit, damageType: string): number {
    return (this.def(u).resist?.[damageType] ?? 0) + (this.equipmentOf(u)?.resist?.[damageType] ?? 0) +
      this.aurasOn(u).reduce((v, { e, mult }) => v + (e.resist?.[damageType] ?? 0) * mult, 0);
  }

  stat(u: Unit, k: StatKey): number {
    let v = this.def(u).stats[k] + (this.equipmentOf(u)?.statMods?.[k] ?? 0);
    for (const s of u.statuses) v += (this.content.statuses[s.id]?.statMods?.[k] ?? 0) * (s.stacks ?? 1);
    v += this.auraMod(u, k);
    return Math.max(0, v);
  }

  /** Passive aura effects covering `u`, with their multiplier (swarm stacks). Radius 0 = self only; radius > 0 excludes the source. */
  aurasOn(u: Unit): { e: Extract<Effect, { type: 'aura' }>; mult: number }[] {
    const out: { e: Extract<Effect, { type: 'aura' }>; mult: number }[] = [];
    for (const src of this.units) {
      if (!src.alive) continue;
      for (const abId of this.abilitiesOf(src)) {
        const a = this.ability(abId);
        if (!a?.passive) continue;
        for (const e of a.effects) {
          if (e.type !== 'aura' || manhattan(src, u) > e.radius || !this.passesFilter(u, e.filter)) continue;
          const affects = e.affects ?? 'allies';
          const ok = e.radius === 0 ? src.uid === u.uid
            : src.uid !== u.uid && (affects === 'all' || (affects === 'enemies' ? src.team !== u.team : src.team === u.team));
          if (!ok) continue;
          let mult = 1;
          if (e.perAdjacentAlly) {
            const n = this.units.filter(o => o.alive && o.uid !== u.uid && o.team === u.team && !this.def(o).structure && manhattan(o, u) === 1).length;
            mult = Math.min(n, e.maxStacks ?? Infinity);
          }
          out.push({ e, mult });
        }
      }
    }
    return out;
  }

  /** Sum of passive aura stat mods on `u`. */
  auraMod(u: Unit, k: StatKey): number {
    return this.aurasOn(u).reduce((v, { e, mult }) => v + (e.statMods?.[k] ?? 0) * mult, 0);
  }

  /** Terrain ids that always count as wet, plus any TerrainDef with `wet: true`. */
  isWetTile(x: number, y: number): boolean {
    const id = this.tiles[y]?.[x]?.terrain;
    return !!id && (id === 'brine_pool' || id === 'living_reef' || !!this.content.terrain[id]?.wet);
  }
  /** True if `u` would not dry out standing at `at` (default: where it is): wet tile or a wet status. */
  isWetFor(u: Unit, at: Pos = u): boolean {
    return this.isWetTile(at.x, at.y) || u.statuses.some(s => this.content.statuses[s.id]?.wet) ||
      this.aurasOn(u).some(({ e }) => e.keepsWet);
  }
  /** HP `u` would lose to drying at the start of its next turn if it stood at `at`. */
  dryingLoss(u: Unit, at: Pos = u): number {
    const n = this.def(u).dries ?? 0;
    return n > 0 && !this.isWetFor(u, at) ? n : 0;
  }

  /** Effect filters compare unit flags; absent filter matches everyone. */
  passesFilter(u: Unit, f?: EffectFilter): boolean {
    if (!f) return true;
    const d = this.def(u);
    if (f.flying !== undefined && !!d.flying !== f.flying) return false;
    if (f.faction && !(d.faction !== undefined && f.faction.includes(d.faction))) return false;
    if (f.notFaction && d.faction !== undefined && f.notFaction.includes(d.faction)) return false;
    if (f.shelled !== undefined && this.shelled(u) !== f.shelled) return false;
    return true;
  }

  /** True while the unit's shell is up. */
  shelled(u: Unit): boolean { return (u.shellHp ?? 0) > 0; }
  /** True for units that are not real fighters: decoys, empty shells and tail segments (AI and UI treat them as props). */
  /** Heroes stay heroes after an eviction or rehouse: the card it was deployed as counts. */
  isHero(u: Unit): boolean { return !!this.def(u).hero || !!this.content.units[u.deployedAs ?? '']?.hero; }
  isProp(u: Unit): boolean { const d = this.def(u); return !!d.decoy || !!d.emptyShell || u.tailOf !== undefined; }
  /** A tail segment stands in for its head; anything else is itself. */
  proxyOf(u: Unit): Unit { if (u.tailOf === undefined) return u; const h = this.unit(u.tailOf); return h && h.alive ? h : u; }

  hasFlag(u: Unit, flag: 'preventsMove' | 'preventsAction') {
    return u.statuses.some(s => this.content.statuses[s.id]?.[flag]);
  }
  isActive(u: Unit) { return u.alive && u.team === this.current && this.phase === 'playing'; }

  canMove(u: Unit) {
    return this.isActive(u) && !this.def(u).structure && !u.summonedThisTurn && !this.hasFlag(u, 'preventsMove');
  }

  /** Engagement: a unit that starts a move next to a living enemy (not a structure) pays ENGAGE_COST extra AP
   *  on the first step, once per move, even if that step keeps it adjacent. Flyers and units with an
   *  `ignoresEngagement` trait or status slip away for free. Ability movement (charge, swap, push) ignores it. */
  engagedBy(u: Unit): Unit[] {
    if (u.alive === false) return [];
    return this.units.filter(o => o.alive && o.team !== u.team && !this.def(o).structure && manhattan(o, u) === 1);
  }
  ignoresEngagement(u: Unit) {
    const d = this.def(u);
    return !!d.flying || !!d.ignoresEngagement || u.statuses.some(s => this.content.statuses[s.id]?.ignoresEngagement);
  }
  /** Extra AP this unit pays to step away from where it stands now. */
  disengageCost(u: Unit) { return !this.ignoresEngagement(u) && this.engagedBy(u).length ? ENGAGE_COST : 0; }

  /** Dijkstra over AP. Units may pass through allies but not stop on them; enemies block. Flyers pay 1 AP per tile, ignore height, and may cross (not end on) impassable tiles. */
  reachable(u: Unit, apBudget = u.ap): Map<string, ReachNode> {
    const out = this.reachRaw(u, apBudget);
    // Allies can be walked through but not stopped on.
    for (const k of [...out.keys()]) {
      const [x, y] = k.split(',').map(Number);
      const occ = this.unitAt(x, y);
      if ((occ && occ.uid !== u.uid) || this.terrainAt(x, y).impassable) out.delete(k);
    }
    return out;
  }

  /** Where a unit could walk on its next turn with a full AP bar, regardless of whose turn it is (AI threat maps). */
  moveRange(u: Unit, apBudget = this.stat(u, 'ap')): Map<string, ReachNode> {
    if (this.def(u).structure || this.hasFlag(u, 'preventsMove')) return new Map([[key(u.x, u.y), { cost: 0, prev: null }]]);
    const out = this.reachRaw(u, apBudget, true);
    for (const k of [...out.keys()]) {
      const [x, y] = k.split(',').map(Number);
      const occ = this.unitAt(x, y);
      if ((occ && occ.uid !== u.uid) || this.terrainAt(x, y).impassable) out.delete(k);
    }
    return out;
  }

  private reachRaw(u: Unit, apBudget: number, anyTurn = false): Map<string, ReachNode> {
    const out = new Map<string, ReachNode>();
    out.set(key(u.x, u.y), { cost: 0, prev: null });
    if (!anyTurn && !this.canMove(u)) return out;
    const jump = this.stat(u, 'jump');
    const flying = !!this.def(u).flying;
    const faction = this.def(u).faction;
    const leave = this.disengageCost(u);
    const frontier: { x: number; y: number; cost: number }[] = [{ x: u.x, y: u.y, cost: 0 }];
    while (frontier.length) {
      frontier.sort((a, b) => a.cost - b.cost);
      const cur = frontier.shift()!;
      if (cur.cost > (out.get(key(cur.x, cur.y))?.cost ?? Infinity)) continue;
      for (const d of DIRS) {
        const nx = cur.x + d.x, ny = cur.y + d.y;
        const t = this.tile(nx, ny);
        if (!t) continue;
        const terr = this.content.terrain[t.terrain];
        if (terr.impassable && !flying) continue;
        if (!flying && Math.abs(t.height - this.tiles[cur.y][cur.x].height) > jump) continue;
        const occ = this.unitAt(nx, ny);
        if (occ && occ.team !== u.team) continue;
        if (occ && this.def(occ).structure && occ.tailOf !== u.uid) continue; // a long body may slither over its own tail
        const cost = cur.cost + (cur.x === u.x && cur.y === u.y ? leave : 0) + (flying ? 1 : (faction !== undefined ? terr.factionMoveCost?.[faction] : undefined) ?? terr.moveCost);
        if (cost > apBudget) continue;
        const k = key(nx, ny);
        if (cost < (out.get(k)?.cost ?? Infinity)) {
          out.set(k, { cost, prev: key(cur.x, cur.y) });
          frontier.push({ x: nx, y: ny, cost });
        }
      }
    }
    return out;
  }

  /** Walking path the unit would take to (x, y), start tile included. */
  pathTo(u: Unit, x: number, y: number): Pos[] { return this.pathFrom(this.reachRaw(u, u.ap), x, y); }

  private pathFrom(reach: Map<string, ReachNode>, x: number, y: number): Pos[] {
    const path: Pos[] = [];
    let k: string | null = key(x, y);
    while (k) {
      const [px, py] = k.split(',').map(Number);
      path.unshift({ x: px, y: py });
      k = reach.get(k)?.prev ?? null;
    }
    return path;
  }

  canUse(u: Unit, abilityId: string) {
    const a = this.ability(abilityId);
    return !!a && !a.passive && this.isActive(u) && !this.def(u).structure && !u.summonedThisTurn &&
      !this.hasFlag(u, 'preventsAction') && u.ap >= a.apCost && (u.cooldowns[abilityId] ?? 0) <= 0 &&
      !this.usedThisTurn(u, abilityId) && this.abilitiesOf(u).includes(abilityId) && this.shellUseOk(u, a);
  }

  /** `rehouse` needs a caster without a shell; `moveOut` needs a shelled caster. */
  private shellUseOk(u: Unit, a: AbilityDef): boolean {
    if (a.effects.some(e => e.type === 'rehouse') && this.def(u).shell) return false;
    if (a.effects.some(e => e.type === 'moveOut') && !this.def(u).shell) return false;
    return true;
  }

  /** Where a `rehouse` by `u` would succeed: a friendly empty shell, or an unoccupied tile whose terrain is a shellSource. */
  rehouseOk(u: Unit, x: number, y: number, from: Pos = u): boolean {
    const occ = (x === from.x && y === from.y) ? u : this.units.find(o => o.alive && o.uid !== u.uid && o.x === x && o.y === y);
    if (occ) return occ.uid !== u.uid && occ.team === u.team && !!this.def(occ).emptyShell;
    return !!this.terrainAt(x, y).shellSource;
  }

  /** Each ability fires at most once per turn: the basic attack can't be spammed, so specials and positioning matter. */
  usedThisTurn(u: Unit, abilityId: string) { return !!u.usedAbilities?.includes(abilityId);
  }

  /** Max range including the high-ground bonus (+1 when 2+ levels above the target tile). */
  private inRange(a: AbilityDef, from: Pos, to: Pos) {
    const d = manhattan(from, to);
    return d >= a.range.min && d <= a.range.max + this.rangeBonusAt(a, from, to);
  }

  /** Extra reach for a ranged ability fired from `from` at `to`: +1 from 2+ levels of high ground, plus the tile's own `rangeBonus`. */
  rangeBonusAt(a: AbilityDef, from: Pos, to?: Pos): number {
    if (a.range.max <= 1) return 0;
    const high = to && this.tiles[from.y][from.x].height - this.tiles[to.y][to.x].height >= 2 ? 1 : 0;
    return high + Math.max(0, this.terrainAt(from.x, from.y).rangeBonus ?? 0);
  }

  /** Every tile an ability can reach from the unit (its range zone), whether or not anything is there to hit. */
  rangeTiles(u: Unit, abilityId: string): Pos[] {
    const a = this.ability(abilityId); if (!a || a.passive) return [];
    if (a.target === 'self') return [{ x: u.x, y: u.y }];
    const out: Pos[] = [], r = a.range.max + 1 + Math.max(0, this.terrainAt(u.x, u.y).rangeBonus ?? 0);
    for (let y = u.y - r; y <= u.y + r; y++) for (let x = u.x - r; x <= u.x + r; x++)
      if (this.inBounds(x, y) && this.inRange(a, u, { x, y })) out.push({ x, y });
    return out;
  }

  /** Valid target tiles for an ability if the caster stood at `from`. */
  targetsFrom(u: Unit, abilityId: string, from: Pos = u): Pos[] {
    const a = this.ability(abilityId);
    const out: Pos[] = [];
    if (a.target === 'self') return [{ x: from.x, y: from.y }];
    const r = a.range.max + 1 + Math.max(0, this.terrainAt(from.x, from.y).rangeBonus ?? 0);
    const rehouse = a.effects.some(e => e.type === 'rehouse');
    for (let y = from.y - r; y <= from.y + r; y++) for (let x = from.x - r; x <= from.x + r; x++) {
      if (!this.inBounds(x, y) || !this.inRange(a, from, { x, y })) continue;
      if (rehouse && !this.rehouseOk(u, x, y, from)) continue;
      const occ = this.unitAt(x, y);
      const occIsSelf = occ?.uid === u.uid;
      const atSelfTile = x === from.x && y === from.y;
      const target = atSelfTile ? u : (occIsSelf ? undefined : occ);
      if (target && target.team !== u.team && this.untargetable(target)) continue;
      switch (a.target) {
        case 'enemy': if (target && target.team !== u.team) out.push({ x, y }); break;
        case 'ally': if (target && target.team === u.team && !this.def(target).structure) out.push({ x, y }); break;
        case 'unit': if (target) out.push({ x, y }); break;
        case 'tile': out.push({ x, y }); break;
        case 'empty': if ((!occ || occIsSelf) && !atSelfTile && !this.terrainAt(x, y).impassable) out.push({ x, y }); break;
      }
    }
    return out;
  }

  /** True while the unit carries a status with `untargetable`: enemies cannot pick it as a target. */
  untargetable(u: Unit): boolean {
    return u.statuses.some(s => this.content.statuses[s.id]?.untargetable);
  }

  validTargets(u: Unit, abilityId: string): Pos[] {
    return this.canUse(u, abilityId) ? this.targetsFrom(u, abilityId) : [];
  }

  /** Units hit by an ability aimed at `target` from `from`. */
  affected(u: Unit, abilityId: string, target: Pos, from: Pos = u): Unit[] {
    const a = this.ability(abilityId);
    if (a.target === 'empty' && !a.area) return [];
    const affects: Affects = a.affects ?? (a.target === 'enemy' ? 'enemies' : a.target === 'ally' || a.target === 'self' ? 'allies' : 'all');
    const match = (o: Unit) => affects === 'all' || (affects === 'enemies' ? o.team !== u.team : o.team === u.team);
    // Position-aware lookup so the AI can evaluate hypothetical caster positions.
    const at = (x: number, y: number) => (x === from.x && y === from.y) ? u : this.units.find(o => o.alive && o.uid !== u.uid && o.x === x && o.y === y);
    if (!a.area) { const o = at(target.x, target.y); return o && match(o) ? [o] : []; }
    const out: Unit[] = [];
    if (a.area.shape === 'line') {
      for (const p of this.lineTiles(from, target, a.area.size)) { const o = at(p.x, p.y); if (o && match(o)) out.push(o); }
      return out;
    }
    for (let y = target.y - a.area.size; y <= target.y + a.area.size; y++)
      for (let x = target.x - a.area.size; x <= target.x + a.area.size; x++) {
        if (manhattan({ x, y }, target) > a.area.size) continue;
        const o = at(x, y);
        if (o && match(o)) out.push(o);
      }
    return out;
  }

  /** `length` tiles starting next to `from`, heading toward `target` along its dominant axis. */
  lineTiles(from: Pos, target: Pos, length: number): Pos[] {
    const dx = target.x - from.x, dy = target.y - from.y;
    const dir = Math.abs(dx) >= Math.abs(dy) ? { x: Math.sign(dx), y: 0 } : { x: 0, y: Math.sign(dy) };
    const out: Pos[] = [];
    if (!dir.x && !dir.y) return out;
    for (let i = 1; i <= length; i++) {
      const p = { x: from.x + dir.x * i, y: from.y + dir.y * i };
      if (!this.inBounds(p.x, p.y)) break;
      out.push(p);
    }
    return out;
  }

  /** Tiles covered by an ability's area (for previews and terrain effects). */
  areaTiles(u: Unit, abilityId: string, target: Pos, from: Pos = u): Pos[] {
    const a = this.ability(abilityId);
    if (!a.area) return [target];
    if (a.area.shape === 'line') return this.lineTiles(from, target, a.area.size);
    return this.radiusTiles(target, a.area.size);
  }

  radiusTiles(c: Pos, size: number): Pos[] {
    const out: Pos[] = [];
    for (let y = c.y - size; y <= c.y + size; y++) for (let x = c.x - size; x <= c.x + size; x++)
      if (this.inBounds(x, y) && manhattan({ x, y }, c) <= size) out.push({ x, y });
    return out;
  }

  heightBonus(from: Pos, to: Pos) {
    const d = this.tiles[from.y][from.x].height - this.tiles[to.y][to.x].height;
    return Math.max(-2, Math.min(3, d));
  }

  /** Damage a single damage effect would deal. `from` is the attacker's (possibly hypothetical) position. */
  previewDamage(attacker: Unit, target: Unit, e: Extract<Effect, { type: 'damage' }>, from: Pos = attacker): number {
    const base = (e.ignoreAttack ? e.amount : this.stat(attacker, 'attack') + e.amount) + this.woundedBonus(target, e);
    const def = e.pierce ? 0 : this.stat(target, 'defense') + (this.def(target).structure ? 0 : this.terrainAt(target.x, target.y).defense);
    const resist = e.damageType ? this.resistOf(target, e.damageType) : 0;
    return Math.max(0, Math.max(1, base - def + this.heightBonus(from, target)) - resist);
  }

  /** vsWounded: extra damage when the target's current HP is below the given fraction of its max HP. */
  woundedBonus(target: Unit, e: Extract<Effect, { type: 'damage' }>): number {
    return e.vsWounded && target.hp < e.vsWounded.below * this.def(target).stats.hp ? e.vsWounded.bonus : 0;
  }

  /** Spell damage: flat amount, reduced by defense/terrain unless pierce, then resist. */
  previewSpellDamage(target: Unit, e: Extract<Effect, { type: 'damage' }>): number {
    const def = e.pierce ? 0 : this.stat(target, 'defense') + (this.def(target).structure ? 0 : this.terrainAt(target.x, target.y).defense);
    const resist = e.damageType ? this.resistOf(target, e.damageType) : 0;
    return Math.max(0, Math.max(1, e.amount + this.woundedBonus(target, e) - def) - resist);
  }

  // ---------- cards (warband hand) ----------
  cardKind(id: string): CardKind | undefined {
    if (this.content.units[id]) return 'unit';
    if (this.content.spells[id]) return 'spell';
    if (this.content.equipment[id]) return 'equipment';
    return undefined;
  }
  cardCost(id: string): number {
    return (this.content.units[id] ?? this.content.spells[id] ?? this.content.equipment[id])?.cost ?? Infinity;
  }
  cardName(id: string): string {
    return (this.content.units[id] ?? this.content.spells[id] ?? this.content.equipment[id])?.name ?? id;
  }

  /** Tiles where the card at handIndex can be played right now (empty if unaffordable/not your turn). */
  cardTargets(team: number, handIndex: number): Pos[] {
    const id = this.teams[team]?.hand[handIndex];
    if (!id || this.phase !== 'playing' || team !== this.current || this.cardCost(id) > this.teams[team].essence) return [];
    switch (this.cardKind(id)) {
      case 'unit': return this.unitDeployTiles(team, id);
      case 'spell': return this.spellTargets(team, this.content.spells[id]);
      case 'equipment': {
        const eq = this.content.equipment[id];
        return this.aliveUnits(team).filter(u => !this.def(u).structure && !u.equipment &&
          (!eq.restrictTo || eq.restrictTo.includes(u.defId) || eq.restrictTo.includes(this.def(u).role ?? ''))).map(u => ({ x: u.x, y: u.y }));
      }
      default: return [];
    }
  }

  /** Play any card from the hand: deploy a unit, cast a spell, or equip a unit. */
  playCard(team: number, handIndex: number, x: number, y: number): boolean {
    const id = this.teams[team]?.hand[handIndex];
    if (!id || !this.cardTargets(team, handIndex).some(p => p.x === x && p.y === y)) return false;
    const kind = this.cardKind(id);
    if (kind === 'unit') return this.deploy(team, handIndex, x, y);
    this.teams[team].essence -= this.cardCost(id);
    this.teams[team].hand.splice(handIndex, 1);
    this.startCooldown(team, id);
    if (kind === 'equipment') {
      const u = this.unitAt(x, y)!;
      u.equipment = id;
      // Raising max AP/HP via equipment takes effect immediately.
      const eq = this.content.equipment[id];
      if (eq.statMods?.hp) u.hp += eq.statMods.hp;
      this.emit({ kind: 'equip', uid: u.uid, equipment: id });
    } else {
      const sp = this.content.spells[id];
      this.emit({ kind: 'spell', team, spell: id, target: { x, y } });
      const targets = this.spellAffected(team, sp, { x, y });
      const had = this.statusSnapshot(sp.effects, targets);
      for (const e of sp.effects) {
        if ((CAST_LEVEL_EFFECTS as readonly string[]).includes(e.type)) { if (this.snapOk(e, had)) this.applyCastEffect(e, team, undefined, this.radiusTiles({ x, y }, sp.area?.size ?? 0), { x, y }); }
        else for (const t of this.proxied(e, targets)) if (t.alive && this.snapOk(e, had, t)) this.applyEffect(e, t, undefined, { x, y }, team);
      }
    }
    this.afterAction();
    return true;
  }

  /** For ifTargetStatus / ifTargetStacks: each unit's status stacks when the use began (tail segments add their head). */
  private statusSnapshot(effects: Effect[], units: Unit[]): Map<number, Record<string, number>> {
    const out = new Map<number, Record<string, number>>();
    if (!effects.some(e => e.ifTargetStatus || e.ifTargetStacks)) return out;
    for (const t of [...units, ...units.map(o => this.proxyOf(o))]) {
      if (out.has(t.uid)) continue;
      const rec: Record<string, number> = {};
      for (const s of t.statuses) rec[s.id] = s.stacks ?? 1;
      out.set(t.uid, rec);
    }
    return out;
  }
  /** Per-target check against the snapshot; without a target (cast-level effects) any snapshot unit passing is enough. */
  private snapOk(e: Effect, had: Map<number, Record<string, number>>, t?: Unit): boolean {
    if (!e.ifTargetStatus && !e.ifTargetStacks) return true;
    const ok = (rec: Record<string, number> | undefined) => !!rec && (!e.ifTargetStatus || (rec[e.ifTargetStatus] ?? 0) > 0) &&
      (!e.ifTargetStacks || (rec[e.ifTargetStacks.status] ?? 0) >= e.ifTargetStacks.min);
    return t ? ok(had.get(t.uid)) : [...had.values()].some(ok);
  }
  /** Damage aimed at tail segments lands on the head instead, once per effect however many segments were hit. */
  private proxied(e: Effect, targets: Unit[]): Unit[] {
    if (e.type !== 'damage' || !targets.some(t => t.tailOf !== undefined)) return targets;
    const out: Unit[] = [];
    for (const t of targets) { const p = this.proxyOf(t); if (!out.includes(p)) out.push(p); }
    return out;
  }

  spellTargets(team: number, sp: SpellDef): Pos[] {
    const cr = sp.castRange;
    const anchors = cr === undefined ? [] : typeof cr === 'number' ? this.aliveUnits(team)
      : this.aliveUnits(team).filter(u => u.tag === `keystone_${team}`);
    const reach = cr === undefined ? Infinity : typeof cr === 'number' ? cr : cr.nearKeystone;
    const out: Pos[] = [];
    for (let y = 0; y < this.height; y++) for (let x = 0; x < this.width; x++) {
      if (cr !== undefined && !anchors.some(f => manhattan(f, { x, y }) <= reach)) continue;
      const occ = this.unitAt(x, y);
      if (occ && occ.team !== team && this.untargetable(occ)) continue;
      switch (sp.target) {
        case 'enemy': if (occ && occ.team !== team) out.push({ x, y }); break;
        case 'ally': if (occ && occ.team === team && !this.def(occ).structure) out.push({ x, y }); break;
        case 'unit': if (occ) out.push({ x, y }); break;
        case 'tile': out.push({ x, y }); break;
        case 'empty': if (!occ && !this.terrainAt(x, y).impassable) out.push({ x, y }); break;
      }
    }
    return out;
  }

  spellAffected(team: number, sp: SpellDef, target: Pos): Unit[] {
    const affects: Affects = sp.affects ?? (sp.target === 'enemy' ? 'enemies' : sp.target === 'ally' ? 'allies' : 'all');
    const match = (o: Unit) => affects === 'all' || (affects === 'enemies' ? o.team !== team : o.team === team);
    const size = sp.area?.size ?? 0;
    return this.aliveUnits().filter(o => manhattan(o, target) <= size && match(o));
  }

  deployTiles(team: number): Pos[] {
    const zone = (this.map.deployZones[String(team)] ?? []).map(([x, y]) => ({ x, y }));
    // Forward deployment: a Tide Well held by one of your champions lets you deploy next to it.
    // Wells become the map's front line: worth fighting for, and reinforcements don't spend two turns walking.
    for (const w of this.heldWells(team)) for (const d of DIRS) zone.push({ x: w.x + d.x, y: w.y + d.y });
    const seen = new Set<string>();
    return zone.filter(p => {
      const k = key(p.x, p.y);
      if (seen.has(k) || !this.inBounds(p.x, p.y)) return false;
      seen.add(k);
      return !this.unitAt(p.x, p.y) && !this.terrainAt(p.x, p.y).impassable;
    });
  }

  /** Wells with one of the team's (non-structure, non-flying) units standing on them. */
  heldWells(team: number): Pos[] {
    if (this.mission.wellDeploy === false) return [];
    return (this.map.wells ?? []).filter(w => { const o = this.unitAt(w.x, w.y); return !!o && o.team === team && this.holdsWell(o); });
  }
  /** Flyers hover over a Well without holding it. */
  private holdsWell(o: Unit) { return !this.def(o).structure && !this.def(o).flying; }

  /** Extra deploy tiles for a skyfall card: any empty passable tile not within 2 of an enemy keystone (and not already claimed by a landing). */
  skyfallTiles(team: number): Pos[] {
    const keystones = this.units.filter(u => u.alive && u.team !== team && u.tag?.startsWith('keystone_'));
    const out: Pos[] = [];
    for (let y = 0; y < this.height; y++) for (let x = 0; x < this.width; x++) {
      if (this.unitAt(x, y) || this.terrainAt(x, y).impassable || this.landings.some(l => l.x === x && l.y === y)) continue;
      if (keystones.some(k => manhattan(k, { x, y }) <= 2)) continue;
      out.push({ x, y });
    }
    return out;
  }

  /** Where the unit card `id` can be deployed: the normal deploy zone (instant), plus skyfall tiles (pending landing) for skyfall units. */
  unitDeployTiles(team: number, id: string): Pos[] {
    const zone = this.deployTiles(team);
    if (!this.content.units[id]?.skyfall) return zone;
    const seen = new Set(zone.map(p => key(p.x, p.y)));
    return zone.concat(this.skyfallTiles(team).filter(p => !seen.has(key(p.x, p.y))));
  }

  canDeploy(team: number, handIndex: number) {
    const id = this.teams[team].hand[handIndex];
    return this.phase === 'playing' && team === this.current && !!id && this.cardKind(id) === 'unit' &&
      this.content.units[id].cost <= this.teams[team].essence && this.unitDeployTiles(team, id).length > 0;
  }

  // ---------- actions ----------
  move(uid: number, x: number, y: number): boolean {
    const u = this.unit(uid);
    if (!u || !this.canMove(u) || (u.x === x && u.y === y)) return false;
    const node = this.reachable(u).get(key(x, y));
    if (!node) return false;
    const raw = this.reachRaw(u, u.ap);
    const path = this.pathFrom(raw, x, y);
    u.ap -= node.cost;
    this.emit({ kind: 'move', uid, path });
    const walked: Pos[] = [path[0]];
    for (const step of path.slice(1)) {
      u.x = step.x; u.y = step.y;
      walked.push(step);
      this.enterTile(u);
      if (!u.alive || u.x !== step.x || u.y !== step.y) break; // died, or shed away
      this.collectAt(u);
      // Coiled enemies strike the first walker that comes next to them; it stops if killed, moved, rooted or stunned.
      // (Not checked on a tile it is only passing through, where it could not stop.)
      const stunned = this.hasFlag(u, 'preventsAction');
      if (!this.units.some(o => o.alive && o !== u && o.x === step.x && o.y === step.y) && this.coiledStrike(u) && (!u.alive || u.x !== step.x || u.y !== step.y || this.hasFlag(u, 'preventsMove') || (!stunned && this.hasFlag(u, 'preventsAction')))) break;
    }
    // A walk cut short refunds the AP for the tiles not walked.
    const last = walked[walked.length - 1];
    if (u.alive && (last.x !== x || last.y !== y)) u.ap += Math.max(0, node.cost - (raw.get(key(last.x, last.y))?.cost ?? node.cost));
    if (u.alive && u.x === last.x && u.y === last.y) this.layTail(u, walked);
    this.afterUnitAct(u);
    this.afterAction();
    return true;
  }

  useAbility(uid: number, abilityId: string, x: number, y: number): boolean {
    const u = this.unit(uid);
    if (!u || !this.canUse(u, abilityId)) return false;
    if (!this.targetsFrom(u, abilityId).some(p => p.x === x && p.y === y)) return false;
    const a = this.ability(abilityId);
    u.ap -= a.apCost;
    if (a.cooldown) u.cooldowns[abilityId] = a.cooldown;
    (u.usedAbilities ??= []).push(abilityId);
    this.emit({ kind: 'ability', uid, ability: abilityId, target: { x, y } });
    this.resolveAbility(u, abilityId, { x, y });
    this.afterUnitAct(u);
    this.afterAction();
    return true;
  }

  /** Apply an ability's effects from `u` at `target`. `reaction`: a Coiled strike (cast-level effects are skipped, `must` is always hit). */
  private resolveAbility(u: Unit, abilityId: string, target: Pos, reaction?: { must: Unit }) {
    const a = this.ability(abilityId);
    const targets = this.affected(u, abilityId, target);
    if (reaction && !targets.includes(reaction.must)) targets.unshift(reaction.must);
    const had = this.statusSnapshot(a.effects, [...targets, u]);
    for (const e of a.effects) {
      if (!u.alive) break;
      if ((CAST_LEVEL_EFFECTS as readonly string[]).includes(e.type)) { if (!reaction && this.snapOk(e, had)) this.applyCastEffect(e, u.team, u, this.areaTiles(u, abilityId, target), target); }
      else if (e.type === 'status' && e.target === 'caster') { if (this.snapOk(e, had, u)) this.applyEffect(e, u, u); } // once per use
      else for (const t of this.proxied(e, targets)) if (t.alive && this.snapOk(e, had, t)) this.applyEffect(e, t, u);
    }
  }

  /** Coiled: enemies of `walker` that are armed and orthogonally adjacent strike it once this turn. Returns true if any struck. */
  private coiledStrike(walker: Unit): boolean {
    if (this.def(walker).structure) return false;
    let struck = false;
    for (const c of this.units) {
      if (!walker.alive) break;
      const cd = this.def(c).coiled;
      if (!cd || !c.alive || !c.coiled || c.team === walker.team || c.coilSpent === this.turnNo || manhattan(c, walker) !== 1) continue;
      if (this.hasFlag(c, 'preventsAction') || !this.ability(cd.ability)) continue;
      c.coilSpent = this.turnNo;
      struck = true;
      const at = { x: walker.x, y: walker.y };
      this.emit({ kind: 'react', uid: c.uid, target: walker.uid, ability: cd.ability });
      this.emit({ kind: 'ability', uid: c.uid, ability: cd.ability, target: at });
      this.resolveAbility(c, cd.ability, at, { must: walker });
    }
    return struck;
  }

  /** After a unit's own action (one walk or one ability use): mark it as having acted, then Venom-like onAct effects bite. */
  private afterUnitAct(u: Unit) {
    u.acted = true;
    for (const s of [...u.statuses]) {
      const sd = this.content.statuses[s.id];
      for (const e of sd?.onAct ?? []) {
        if (!u.alive || !u.statuses.includes(s) || e.type !== 'damage') continue;
        const amt = this.previewSpellDamage(u, { ...e, amount: e.amount * (s.stacks ?? 1) });
        if (amt > 0) this.damage(u, amt, e.damageType, e.pierce);
      }
    }
  }

  deploy(team: number, handIndex: number, x: number, y: number): boolean {
    if (!this.canDeploy(team, handIndex)) return false;
    const id = this.teams[team].hand[handIndex];
    const instant = this.deployTiles(team).some(p => p.x === x && p.y === y);
    if (!instant && !this.unitDeployTiles(team, id).some(p => p.x === x && p.y === y)) return false;
    this.teams[team].essence -= this.content.units[id].cost;
    this.teams[team].hand.splice(handIndex, 1);
    if (!instant) {
      // Skyfall: the cost is paid now; a marker holds the tile until the unit lands next turn.
      const uid = this.nextUid++;
      this.landings.push({ uid, defId: id, team, x, y });
      this.emit({ kind: 'skyfall', uid, team, defId: id, x, y });
      this.afterAction();
      return true;
    }
    const u = this.spawn(id, team, x, y);
    u.fromCard = true;
    this.emit({ kind: 'deploy', uid: u.uid });
    this.afterAction();
    return true;
  }

  endTurn() {
    if (this.phase !== 'playing') return;
    // Statuses on the team that just acted tick down.
    for (const u of this.aliveUnits(this.current)) {
      // Venom-like statuses lose a stack on a turn the carrier stayed idle.
      if (!u.acted) for (const s of u.statuses) if (this.content.statuses[s.id]?.shedsWhenIdle) {
        s.stacks = (s.stacks ?? 1) - 1;
        if (s.stacks <= 0) s.remaining = 0;
      }
      // Coiled for the enemy turns ahead if it used no ability this turn.
      u.coiled = !!this.def(u).coiled && !u.usedAbilities?.length;
      for (const s of u.statuses) s.remaining--;
      u.statuses = u.statuses.filter(s => s.remaining > 0);
    }
    if (this.current === this.teams.length - 1) {
      this.checkRoundConditions();
      if (this.phase !== 'playing') return;
      this.round++;
      for (const t of this.terrainTimers) if (--t.remaining <= 0) this.setTerrain(t.x, t.y, t.prev);
      this.terrainTimers = this.terrainTimers.filter(t => t.remaining > 0);
    }
    this.current = (this.current + 1) % this.teams.length;
    this.beginTurn();
  }

  // ---------- internals ----------
  private spawn(defId: string, team: number, x: number, y: number, tag?: string, uid?: number): Unit {
    const d = this.content.units[defId];
    const u: Unit = {
      uid: uid ?? this.nextUid++, defId, team, x, y, hp: d.stats.hp, ap: 0, statuses: [], cooldowns: {},
      summonedThisTurn: true, tag, alive: true, deployedAs: defId,
    };
    if (d.shell) u.shellHp = d.shell.hp;
    if (d.decoy) u.decoyTurns = 3;
    this.units.push(u);
    return u;
  }

  /** Remove a unit from the board without a death (no Tide, no card cooldown, no mission trigger). */
  private vanish(u: Unit) {
    if (!u.alive) return;
    u.alive = false;
    this.emit({ kind: 'vanish', uid: u.uid });
    this.dropTail(u);
  }
  private dropTail(u: Unit) {
    const segs = u.tail ?? [];
    u.tail = undefined;
    for (const id of segs) { const s = this.unit(id); if (s) this.vanish(s); }
  }

  /** Long body: put the tail on the tiles just walked (newest first), then where the old tail lay. */
  private layTail(u: Unit, walked: Pos[]) {
    const t = this.def(u).tail;
    if (!t) return;
    const old = (u.tail ?? []).map(id => this.unit(id)).filter((s): s is Unit => !!s && s.alive);
    const trail = [...walked.slice(0, -1).reverse(), ...old.map(s => ({ x: s.x, y: s.y }))];
    const used = new Set([key(u.x, u.y)]);
    const spots: Pos[] = [];
    for (const p of trail) {
      if (spots.length >= t.length) break;
      const k = key(p.x, p.y);
      if (used.has(k)) continue;
      used.add(k);
      const occ = this.unitAt(p.x, p.y);
      if ((occ && occ.tailOf !== u.uid) || this.terrainAt(p.x, p.y).impassable) continue;
      spots.push(p);
    }
    // Reuse the old segments in order (they snap to their new tiles), add or remove the difference.
    u.tail = [];
    spots.forEach((p, i) => {
      const s = old[i];
      if (s) { s.x = p.x; s.y = p.y; u.tail!.push(s.uid); return; }
      const n = this.spawn(t.segment, u.team, p.x, p.y);
      n.tailOf = u.uid;
      u.tail!.push(n.uid);
      this.emit({ kind: 'deploy', uid: n.uid });
    });
    for (const s of old.slice(spots.length)) this.vanish(s);
  }

  /** Change what a unit is (eviction, rehouse, moveOut): new stats, abilities and art; body HP carries over (capped),
   *  statuses and equipment stay, ability cooldowns reset. */
  private morph(u: Unit, defId: string, shellHp?: number) {
    u.defId = defId;
    const d = this.def(u);
    u.shellHp = d.shell ? Math.max(0, Math.min(d.shell.hp, shellHp ?? d.shell.hp)) : undefined;
    u.hp = Math.min(u.hp, Math.max(1, this.stat(u, 'hp')));
    u.ap = Math.min(u.ap, this.stat(u, 'ap'));
    u.cooldowns = {};
    if (!d.tail) this.dropTail(u);
  }

  /** Shell broke: the unit becomes its `shell.evicted` form. */
  private evict(u: Unit) {
    const sh = this.def(u).shell;
    if (!sh || !this.content.units[sh.evicted]) { u.shellHp = 0; return; }
    const from = u.defId, at = { x: u.x, y: u.y };
    this.morph(u, sh.evicted);
    this.emit({ kind: 'evict', uid: u.uid, from, to: u.defId, at });
    for (const e of sh.onBreak ?? []) if ((CAST_LEVEL_EFFECTS as readonly string[]).includes(e.type)) this.applyCastEffect(e, u.team, u, [at], at);
  }

  /** Shed: drop every status, leave a husk on this tile and slide away from the nearest enemy. */
  private shedSkin(u: Unit) {
    const sd = this.def(u).shed!;
    u.shedUsed = true;
    u.statuses = [];
    this.dropTail(u);
    const from = { x: u.x, y: u.y };
    const to = this.slideTile(u, sd.slide ?? 2);
    let husk: Unit | undefined;
    if (to) {
      u.x = to.x; u.y = to.y;
      if (this.content.units[sd.husk]) husk = this.spawn(sd.husk, u.team, from.x, from.y);
    }
    this.emit({ kind: 'shed', uid: u.uid, from, to: to ?? from, ...(husk ? { husk: husk.uid } : {}) });
    if (husk) this.emit({ kind: 'deploy', uid: husk.uid });
  }

  /** The free passable tile within `steps` (walking over free tiles, jump respected) farthest from the nearest enemy. */
  private slideTile(u: Unit, steps: number): Pos | undefined {
    const foes = this.units.filter(o => o.alive && o.team !== u.team && !this.isProp(o));
    const far = (p: Pos) => foes.length ? Math.min(...foes.map(o => manhattan(o, p))) : 0;
    const jump = this.stat(u, 'jump'), flying = !!this.def(u).flying;
    const seen = new Set([key(u.x, u.y)]);
    let frontier: Pos[] = [{ x: u.x, y: u.y }];
    let best: { p: Pos; d: number } | undefined;
    for (let i = 0; i < steps; i++) {
      const next: Pos[] = [];
      for (const c of frontier) for (const d of DIRS) {
        const n = { x: c.x + d.x, y: c.y + d.y };
        const k = key(n.x, n.y);
        if (!this.inBounds(n.x, n.y) || seen.has(k)) continue;
        seen.add(k);
        if (this.terrainAt(n.x, n.y).impassable || this.unitAt(n.x, n.y)) continue;
        if (!flying && Math.abs(this.tiles[n.y][n.x].height - this.tiles[c.y][c.x].height) > jump) continue;
        next.push(n);
        const dd = far(n);
        if (!best || dd > best.d) best = { p: n, d: dd };
      }
      frontier = next;
    }
    return best?.p;
  }

  private beginTurn() {
    const team = this.teams[this.current];
    if (this.round > 1)
      team.essence = Math.min(this.mission.maxEssence ?? DEFAULTS.maxEssence, team.essence + (this.mission.teams[this.current]?.essencePerTurn ?? this.mission.essencePerTurn ?? DEFAULTS.essencePerTurn));
    this.emit({ kind: 'turn', team: this.current, turn: this.round });
    // Rested cards come back first: into the hand, or onto the top of the draw pile when the hand is full.
    for (const c of team.cooldown) c.turns--;
    for (const c of team.cooldown.filter(c => c.turns <= 0)) {
      const toHand = team.hand.length < DRAW.maxHand;
      if (toHand) team.hand.push(c.card); else team.deck.unshift(c.card);
      this.emit({ kind: 'ready', team: this.current, card: c.card, toHand });
    }
    team.cooldown = team.cooldown.filter(c => c.turns > 0);
    // Draw (not on the very first turn of the game: going first is already an edge).
    if (this.round > 1 || this.current > 0) for (let i = 0; i < DRAW.perTurn; i++) {
      if (!team.deck.length || team.hand.length >= DRAW.maxHand) break;
      const card = team.deck.shift()!;
      team.hand.push(card);
      this.emit({ kind: 'draw', team: this.current, card });
    }
    for (const w of this.map.wells ?? []) {
      const holder = this.unitAt(w.x, w.y);
      if (holder && holder.team === this.current && this.holdsWell(holder)) this.gainEssence(this.current, w.amount, { x: w.x, y: w.y });
    }
    this.turnNo++;
    // Decoys (husks) last until the start of their owner's 3rd turn after they appeared.
    for (const u of this.aliveUnits(this.current)) if (u.decoyTurns !== undefined && --u.decoyTurns <= 0) this.vanish(u);
    const landed = this.resolveLandings();
    this.collectDrops();
    for (const u of this.aliveUnits(this.current)) {
      u.summonedThisTurn = false;
      u.usedAbilities = [];
      u.acted = false;
      u.coiled = false;
      // Drying: a dry unit off wet ground loses HP (not on the turn it lands). Can kill.
      const dry = landed.has(u.uid) ? 0 : this.dryingLoss(u);
      if (dry > 0) { this.damage(u, dry, 'drying'); if (!u.alive) continue; }
      // Terrain under the unit's feet (flyers skip it, like onEnter; not on the turn a unit lands).
      if (!landed.has(u.uid) && !this.def(u).flying)
        for (const e of this.terrainAt(u.x, u.y).onTurnStart ?? []) if (u.alive) this.applyEffect(e, u);
      if (!u.alive) continue;
      for (const k of Object.keys(u.cooldowns)) u.cooldowns[k] = Math.max(0, u.cooldowns[k] - 1);
      for (const s of [...u.statuses]) for (const e of this.content.statuses[s.id]?.onTurnStart ?? [])
        if (u.alive && (e.type === 'damage' || e.type === 'heal')) this.applyEffect({ ...e, amount: e.amount * (s.stacks ?? 1) }, u);
      u.ap = this.stat(u, 'ap');
    }
    this.runEvents(ev => 'turn' in ev.when && ev.when.turn === this.round && (ev.when.team ?? 0) === this.current);
    this.checkConditions();
  }

  /** Land this team's pending skyfall units. Returns the uids that landed. */
  private resolveLandings(): Set<number> {
    const landed = new Set<number>();
    const mine = this.landings.filter(l => l.team === this.current);
    this.landings = this.landings.filter(l => l.team !== this.current);
    for (const l of mine) {
      const impact = this.content.units[l.defId].skyfall?.impact ?? 0;
      const hit = (o: Unit, amount: number) => { const n = Math.max(0, amount - this.resistOf(o, 'physical')); if (n > 0) this.damage(o, n, 'physical'); };
      let at: Pos | undefined = { x: l.x, y: l.y };
      const occ = this.unitAt(l.x, l.y);
      if (occ) {
        hit(occ, impact + 3);
        at = this.nearestFree({ x: l.x, y: l.y }, Math.max(this.width, this.height));
      }
      if (!at) continue; // nowhere to land: the unit is lost
      const u = this.spawn(l.defId, l.team, at.x, at.y, undefined, l.uid);
      u.fromCard = true;
      landed.add(u.uid);
      this.emit({ kind: 'deploy', uid: u.uid });
      this.emit({ kind: 'land', uid: u.uid, from: { x: l.x, y: l.y }, to: at });
      for (const o of this.units) if (o.alive && o.team !== l.team && manhattan(o, at) === 1) hit(o, impact);
    }
    return landed;
  }

  private enterTile(u: Unit) {
    if (this.def(u).flying) return; // flyers skip terrain onEnter effects
    const e = this.terrainAt(u.x, u.y).onEnter;
    if (e) this.applyEffect(e, u);
  }

  /** `source` = casting unit (ability); `origin` = spell target tile used for push/pull direction. */
  private applyEffect(e: Effect, target: Unit, source?: Unit, origin?: Pos, team = source?.team) {
    const center: Pos | undefined = source ?? origin;
    if ('filter' in e && !this.passesFilter(target, e.filter)) return;
    switch (e.type) {
      case 'damage': {
        target = this.proxyOf(target);
        if (!target.alive) break;
        const amt = source ? this.previewDamage(source, target, e) : origin ? this.previewSpellDamage(target, e) : Math.max(1, e.amount);
        this.damage(target, amt, e.damageType, e.pierce);
        const d = this.def(target);
        if (e.convertOnKill && !target.alive && team !== undefined && !d.hero && !this.isHero(target) && !d.structure && !target.tag?.startsWith('keystone_'))
          this.summonAt(e.convertOnKill, team, target, 1);
        break;
      }
      case 'heal': {
        if (e.target === 'caster') { if (!source) break; target = source; }
        if (target.tailOf !== undefined) break; // tail segments are not healed
        const max = this.def(target).stats.hp;
        const amt = Math.min(e.amount, max - target.hp);
        if (amt > 0) { target.hp += amt; this.emit({ kind: 'heal', uid: target.uid, amount: amt }); }
        break;
      }
      case 'status': {
        if (e.target === 'caster') { if (!source) break; target = source; }
        if (this.def(target).structure) break;
        const existing = target.statuses.find(s => s.id === e.status);
        const sd = this.content.statuses[e.status];
        if (existing && sd?.stacks) existing.stacks = Math.min((existing.stacks ?? 1) + 1, sd.maxStacks ?? Infinity);
        if (existing) existing.remaining = Math.max(existing.remaining, e.duration);
        else target.statuses.push({ id: e.status, remaining: e.duration });
        this.emit({ kind: 'status', uid: target.uid, status: e.status });
        break;
      }
      case 'push': {
        if (!center || this.def(target).structure) break;
        const dx = target.x - center.x, dy = target.y - center.y;
        const dir = Math.abs(dx) >= Math.abs(dy) ? { x: Math.sign(dx), y: 0 } : { x: 0, y: Math.sign(dy) };
        if (!dir.x && !dir.y) break;
        const from = { x: target.x, y: target.y };
        for (let i = 0; i < e.distance; i++) {
          const nx = target.x + dir.x, ny = target.y + dir.y;
          const t = this.tile(nx, ny);
          const blocked = !t || this.content.terrain[t.terrain].impassable || !!this.unitAt(nx, ny) ||
            t.height - this.tiles[target.y][target.x].height > 1;
          if (blocked) { if (e.collisionDamage) this.damage(target, e.collisionDamage, 'impact'); break; }
          target.x = nx; target.y = ny;
          this.enterTile(target);
          if (!target.alive) break;
        }
        if (target.x !== from.x || target.y !== from.y) this.emit({ kind: 'push', uid: target.uid, from, to: { x: target.x, y: target.y } });
        break;
      }
      case 'pull': {
        if (!center || this.def(target).structure) break;
        const from = { x: target.x, y: target.y };
        for (let i = 0; i < e.distance; i++) {
          if (manhattan(target, center) <= (source ? 1 : 0)) break;
          const dx = center.x - target.x, dy = center.y - target.y;
          const dir = Math.abs(dx) >= Math.abs(dy) ? { x: Math.sign(dx), y: 0 } : { x: 0, y: Math.sign(dy) };
          const nx = target.x + dir.x, ny = target.y + dir.y;
          const t = this.tile(nx, ny);
          if (!t || this.content.terrain[t.terrain].impassable || this.unitAt(nx, ny) ||
            t.height - this.tiles[target.y][target.x].height > 1) break;
          target.x = nx; target.y = ny;
          this.enterTile(target);
          if (!target.alive) break;
        }
        if (target.x !== from.x || target.y !== from.y) this.emit({ kind: 'push', uid: target.uid, from, to: { x: target.x, y: target.y } });
        break;
      }
      case 'reshed': {
        if (this.def(target).shed && target.shedUsed) { target.shedUsed = false; this.emit({ kind: 'status', uid: target.uid, status: 'reshed' }); }
        break;
      }
      case 'shell': {
        const sh = this.def(target).shell;
        if (!sh || !target.alive) break;
        const amt = Math.min(e.amount, sh.hp - (target.shellHp ?? 0));
        if (amt > 0) { target.shellHp = (target.shellHp ?? 0) + amt; this.emit({ kind: 'shell', uid: target.uid, amount: amt }); }
        break;
      }
      default: break; // cast-level effects are handled in applyCastEffect; auras are passive
    }
  }

  /** Effect movement for rehouse / moveOut: one step onto `to` (no engagement, no onEnter, no Coiled trigger). */
  private stepTo(u: Unit, to: Pos) {
    this.emit({ kind: 'move', uid: u.uid, path: [{ x: u.x, y: u.y }, { x: to.x, y: to.y }] });
    u.x = to.x; u.y = to.y;
  }

  private applyCastEffect(e: Effect, team: number, u: Unit | undefined, area: Pos[], target: Pos) {
    switch (e.type) {
      case 'teleport': {
        if (!u || this.unitAt(target.x, target.y)) return;
        this.emit({ kind: 'move', uid: u.uid, path: [{ x: u.x, y: u.y }, { x: target.x, y: target.y }] });
        u.x = target.x; u.y = target.y; this.enterTile(u);
        return;
      }
      case 'swap': {
        const o = this.unitAt(target.x, target.y);
        if (!u || !o || o.uid === u.uid || this.def(o).structure) return;
        const a0 = { x: u.x, y: u.y }, b0 = { x: o.x, y: o.y };
        u.x = b0.x; u.y = b0.y; o.x = a0.x; o.y = a0.y;
        this.emit({ kind: 'push', uid: u.uid, from: a0, to: b0 });
        this.emit({ kind: 'push', uid: o.uid, from: b0, to: a0 });
        this.enterTile(u); if (o.alive) this.enterTile(o);
        return;
      }
      case 'summon': this.summonAt(e.unit, team, target, e.count ?? 1); return;
      case 'draw': {
        const t = this.teams[team];
        for (let i = 0; i < e.count; i++) {
          if (!t.deck.length || t.hand.length >= DRAW.maxHand) break;
          const card = t.deck.shift()!;
          t.hand.push(card);
          this.emit({ kind: 'draw', team, card });
        }
        return;
      }
      case 'terrain': {
        for (const { x, y } of area) {
          const occ = this.unitAt(x, y);
          if (occ && (this.def(occ).structure || this.content.terrain[e.terrain].impassable)) continue;
          const prev = this.tiles[y][x].terrain;
          if (prev === e.terrain) continue;
          this.setTerrain(x, y, e.terrain);
          if (e.duration) this.terrainTimers.push({ x, y, prev, remaining: e.duration });
        }
        return;
      }
      case 'sacrifice': {
        if (u?.alive) { u.revived = true; u.shedUsed = true; this.damage(u, u.hp, 'sacrifice', true); }
        return;
      }
      case 'essence': {
        this.gainEssence(e.team === 'enemy' ? (team === 0 ? 1 : 0) : team, e.amount);
        return;
      }
      case 'rehouse': {
        if (!u?.alive || this.def(u).shell || !this.rehouseOk(u, target.x, target.y)) return;
        const from = u.defId;
        const occ = this.unitAt(target.x, target.y);
        if (occ) {
          const becomes = this.def(occ).emptyShell!.becomes;
          const hp = occ.hp;
          this.vanish(occ);
          this.stepTo(u, target);
          this.morph(u, becomes, hp);
        } else {
          const src = this.terrainAt(target.x, target.y).shellSource!;
          this.stepTo(u, target);
          this.morph(u, src);
          if (this.content.terrain.salt_flat) this.setTerrain(target.x, target.y, 'salt_flat');
        }
        this.emit({ kind: 'rehouse', uid: u.uid, from, to: u.defId, at: { x: target.x, y: target.y } });
        return;
      }
      case 'moveOut': {
        const sh = u?.alive ? this.def(u).shell : undefined;
        if (!u || !sh || this.unitAt(target.x, target.y) || this.terrainAt(target.x, target.y).impassable || !this.content.units[sh.evicted]) return;
        const at = { x: u.x, y: u.y }, left = u.shellHp ?? 0, from = u.defId;
        this.stepTo(u, target);
        this.morph(u, sh.evicted);
        this.emit({ kind: 'evict', uid: u.uid, from, to: u.defId, voluntary: true, at: { x: u.x, y: u.y } });
        if (sh.leaves && left > 0 && this.content.units[sh.leaves]) {
          const s = this.spawn(sh.leaves, u.team, at.x, at.y);
          s.hp = left;
          this.emit({ kind: 'deploy', uid: s.uid });
        }
        return;
      }
    }
  }

  /** Summon `count` of a unit for `team` on (or next to) a tile; they act next turn. */
  private summonAt(unit: string, team: number, target: Pos, count: number) {
    for (let i = 0; i < count; i++) {
      const p = !this.unitAt(target.x, target.y) && !this.terrainAt(target.x, target.y).impassable ? target : this.nearestFree(target);
      if (!p) return;
      const s = this.spawn(unit, team, p.x, p.y);
      this.emit({ kind: 'deploy', uid: s.uid });
    }
  }

  private setTerrain(x: number, y: number, terrain: string) {
    if (this.content.terrain[this.tiles[y][x].terrain]?.void) return; // chasm stays empty
    this.tiles[y][x].terrain = terrain;
    this.emit({ kind: 'terrain', x, y, terrain });
  }

  private gainEssence(team: number, amount: number, at?: Pos) {
    const t = this.teams[team];
    const before = t.essence;
    t.essence = Math.max(0, Math.min(this.mission.maxEssence ?? DEFAULTS.maxEssence, t.essence + amount));
    if (t.essence !== before) this.emit({ kind: 'essence', team, amount: t.essence - before, ...(at ? { at } : {}) });
  }

  /** Deal `amount` to `u`. A shell soaks it first unless `pierce` or the type is venom/drying/sacrifice. */
  private damage(u: Unit, amount: number, damageType?: string, pierce = false) {
    u = this.proxyOf(u);
    if (!u.alive) return;
    if (this.shelled(u) && !pierce && !SHELL_BYPASS.includes(damageType ?? '')) {
      // The shell takes the hit; whatever is left over when it breaks is lost.
      const dealt = Math.min(amount, u.shellHp!);
      u.shellHp! -= amount;
      this.emit({ kind: 'damage', uid: u.uid, amount: dealt, damageType, shell: true });
      if (u.shellHp! <= 0) { u.shellHp = 0; this.evict(u); }
      return;
    }
    u.hp -= amount;
    this.emit({ kind: 'damage', uid: u.uid, amount, damageType });
    const sd = this.def(u).shed;
    if (u.hp > 0 && sd && !u.shedUsed && !this.def(u).structure && u.hp < this.def(u).stats.hp * 0.5) this.shedSkin(u);
    if (u.hp <= 0) {
      const rv = this.def(u).revive;
      if (rv && !u.revived) {
        u.revived = true;
        u.statuses = [];
        u.hp = Math.max(1, Math.ceil(this.def(u).stats.hp * rv.hpFraction));
        this.emit({ kind: 'revive', uid: u.uid, hp: u.hp });
        return;
      }
      u.hp = 0; u.alive = false;
      this.emit({ kind: 'death', uid: u.uid });
      this.dropTail(u);
      const d = this.def(u);
      if (!d.structure) {
        // Tide and the card cooldown go by what the unit was deployed as (an evicted crab is still its card).
        const amount = tideDropFor(this.content.units[u.deployedAs ?? u.defId]?.cost ?? d.cost ?? 0);
        if (amount > 0) {
          const at = this.drops.find(p => p.x === u.x && p.y === u.y);
          if (at) at.amount += amount; else this.drops.push({ x: u.x, y: u.y, amount });
          this.emit({ kind: 'drop', x: u.x, y: u.y, amount });
        }
        if (u.fromCard) this.startCooldown(u.team, u.deployedAs ?? u.defId);
      }
      if (u.tag) this.runEvents(ev => 'unitDefeated' in ev.when && ev.when.unitDefeated === u.tag);
    }
  }

  private runEvents(pred: (ev: NonNullable<MissionDef['events']>[number]) => boolean) {
    (this.mission.events ?? []).forEach((ev, i) => {
      if (this.firedEvents.has(i) || !pred(ev)) return;
      if (ev.once !== false) this.firedEvents.add(i);
      ev.do.forEach(a => this.runAction(a));
    });
  }

  private runAction(a: MissionAction) {
    switch (a.type) {
      case 'message': this.emit({ kind: 'message', text: a.text, speaker: a.speaker }); break;
      case 'grant_essence': this.gainEssence(a.team, a.amount); break;
      case 'terrain': {
        for (const { x, y } of this.radiusTiles({ x: a.x, y: a.y }, a.radius ?? 0)) {
          const occ = this.unitAt(x, y);
          if (occ && (this.def(occ).structure || this.content.terrain[a.terrain]?.impassable)) continue;
          const prev = this.tiles[y][x].terrain;
          if (prev === a.terrain) continue;
          this.setTerrain(x, y, a.terrain);
          if (a.duration) this.terrainTimers.push({ x, y, prev, remaining: a.duration });
        }
        break;
      }
      case 'status':
        for (const u of this.units) if (u.alive && u.tag === a.tag) this.applyEffect({ type: 'status', status: a.status, duration: a.duration }, u);
        break;
      case 'spawn': {
        let p: Pos | undefined = !this.unitAt(a.x, a.y) && !this.terrainAt(a.x, a.y).impassable ? { x: a.x, y: a.y } : undefined;
        if (!p) p = this.nearestFree({ x: a.x, y: a.y });
        if (!p) break;
        const u = this.spawn(a.unit, a.team, p.x, p.y, a.tag);
        if (a.team !== this.current) u.summonedThisTurn = false;
        this.emit({ kind: 'deploy', uid: u.uid });
        break;
      }
    }
  }

  private nearestFree(c: Pos, maxR = 4): Pos | undefined {
    for (let r = 1; r < maxR; r++) for (let y = c.y - r; y <= c.y + r; y++) for (let x = c.x - r; x <= c.x + r; x++)
      if (this.inBounds(x, y) && manhattan({ x, y }, c) === r && !this.unitAt(x, y) && !this.terrainAt(x, y).impassable) return { x, y };
    return undefined;
  }

  private afterAction() { this.collectDrops(); this.checkConditions(); }

  private startCooldown(team: number, card: string) {
    const turns = cooldownFor(this.cardCost(card));
    this.teams[team].cooldown.push({ card, turns });
    this.emit({ kind: 'cooldown', team, card, turns });
  }

  /** Any non-structure unit standing on spilled Tide picks it up (pushes, teleports and deploys included). */
  private collectDrops() {
    if (!this.drops.length) return;
    for (const u of this.aliveUnits()) this.collectAt(u);
  }
  private collectAt(u: Unit) {
    if (this.def(u).structure) return;
    const i = this.drops.findIndex(d => d.x === u.x && d.y === u.y);
    if (i < 0) return;
    const [d] = this.drops.splice(i, 1);
    this.emit({ kind: 'pickup', uid: u.uid, team: u.team, x: d.x, y: d.y, amount: d.amount });
    this.gainEssence(u.team, d.amount, { x: d.x, y: d.y });
  }

  private defaultConditions(enemyOf: number): Condition[] {
    const other = enemyOf === 0 ? 1 : 0;
    const out: Condition[] = [{ type: 'eliminate', team: other }];
    if (this.units.some(u => u.team === other && u.tag === `keystone_${other}`)) out.unshift({ type: 'destroy_keystone', team: other });
    return out;
  }

  /**
   * Evaluate a condition right now. For salvage bonuses call it at the moment of victory with endOfRound = true,
   * so survive/turn_limit compare against the current round ("not turn_limit 8" = won before round 8).
   */
  conditionMet(c: Condition, endOfRound = false): boolean {
    return this.met(c, endOfRound);
  }

  private met(c: Condition, endOfRound: boolean): boolean {
    const r = this.metRaw(c, endOfRound);
    return c.not ? !r : r;
  }

  private metRaw(c: Condition, endOfRound: boolean): boolean {
    switch (c.type) {
      case 'destroy_keystone': return this.units.some(u => u.tag === `keystone_${c.team}` && !u.alive);
      case 'eliminate': return ![...this.teams[c.team].hand, ...this.teams[c.team].deck].some(id => this.cardKind(id) === 'unit') &&
        !this.landings.some(l => l.team === c.team) &&
        !this.aliveUnits(c.team).some(u => !this.def(u).structure);
      case 'defeat_unit': { const tagged = this.units.filter(u => u.tag === c.tag); return tagged.length > 0 && tagged.every(u => !u.alive); }
      case 'unit_lost': return this.units.some(u => u.tag === c.tag && !u.alive);
      case 'unit_hp_above': return this.units.some(u => u.tag === c.tag && u.alive && u.hp > this.def(u).stats.hp * c.fraction);
      case 'reach_tile': return this.aliveUnits(c.team).some(u => (!c.tag || u.tag === c.tag) && c.tiles.some(([x, y]) => u.x === x && u.y === y));
      case 'survive': return endOfRound && this.round >= c.turns;
      case 'turn_limit': return endOfRound && this.round >= c.turns;
    }
  }

  private evaluate(endOfRound: boolean) {
    if (this.phase !== 'playing') return;
    const victory = this.mission.objectives?.victory ?? this.defaultConditions(0);
    const defeat = this.mission.objectives?.defeat ?? this.defaultConditions(1);
    // Defeat is checked first: losing your keystone on the same blow you win still counts as a loss.
    if (defeat.some(c => this.met(c, endOfRound))) this.finish('defeat');
    else if (victory.some(c => this.met(c, endOfRound))) this.finish('victory');
  }

  private checkConditions() { this.evaluate(false); }
  private checkRoundConditions() { this.evaluate(true); }

  private finish(p: Phase) {
    this.phase = p;
    this.emit({ kind: 'end', phase: p });
  }
}

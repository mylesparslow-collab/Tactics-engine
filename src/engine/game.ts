import { CAST_LEVEL_EFFECTS } from './types';
import type {
  AbilityDef, Affects, CardKind, EquipmentDef, SpellDef, Condition, Content, Effect, GameEvent, MapDef, MissionAction, MissionDef,
  Phase, Pos, StatKey, TeamState, Tile, Unit, UnitDef,
} from './types';

export const DEFAULTS = { startingEssence: 100, essencePerTurn: 25, maxEssence: 200 };
const key = (x: number, y: number) => `${x},${y}`;
export const manhattan = (a: Pos, b: Pos) => Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
const DIRS: Pos[] = [{ x: 1, y: 0 }, { x: -1, y: 0 }, { x: 0, y: 1 }, { x: 0, y: -1 }];

export interface ReachNode { cost: number; prev: string | null }
export interface GameOptions { roster?: string[] }

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
  teams: TeamState[];
  current = 0;
  round = 1;
  phase: Phase = 'playing';
  log: GameEvent[] = [];
  private listeners: ((e: GameEvent) => void)[] = [];
  private nextUid = 1;
  private firedEvents = new Set<number>();
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
      hand: [...((t.useCampaignRoster && opts.roster) ? opts.roster : (t.warband ?? []))],
    }));
    mission.teams.forEach((t, team) => {
      const ks = this.map.keystones?.find(k => k.team === team);
      if (ks && t.keystone !== false) this.spawn('keystone', team, ks.x, ks.y, `keystone_${team}`);
      t.units?.forEach(u => this.spawn(u.unit, team, u.x, u.y, u.tag));
    });
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
          if (e.type !== 'aura' || manhattan(src, u) > e.radius) continue;
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

  hasFlag(u: Unit, flag: 'preventsMove' | 'preventsAction') {
    return u.statuses.some(s => this.content.statuses[s.id]?.[flag]);
  }
  isActive(u: Unit) { return u.alive && u.team === this.current && this.phase === 'playing'; }

  canMove(u: Unit) {
    return this.isActive(u) && !this.def(u).structure && !u.summonedThisTurn && !this.hasFlag(u, 'preventsMove');
  }

  /** Dijkstra over AP. Units may pass through allies but not stop on them; enemies block. */
  reachable(u: Unit, apBudget = u.ap): Map<string, ReachNode> {
    const out = this.reachRaw(u, apBudget);
    // Allies can be walked through but not stopped on.
    for (const k of [...out.keys()]) {
      const [x, y] = k.split(',').map(Number);
      const occ = this.unitAt(x, y);
      if (occ && occ.uid !== u.uid) out.delete(k);
    }
    return out;
  }

  private reachRaw(u: Unit, apBudget: number): Map<string, ReachNode> {
    const out = new Map<string, ReachNode>();
    out.set(key(u.x, u.y), { cost: 0, prev: null });
    if (!this.canMove(u)) return out;
    const jump = this.stat(u, 'jump');
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
        if (terr.impassable) continue;
        if (Math.abs(t.height - this.tiles[cur.y][cur.x].height) > jump) continue;
        const occ = this.unitAt(nx, ny);
        if (occ && occ.team !== u.team) continue;
        if (occ && this.def(occ).structure) continue;
        const cost = cur.cost + terr.moveCost;
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
      this.abilitiesOf(u).includes(abilityId);
  }

  /** Max range including the high-ground bonus (+1 when 2+ levels above the target tile). */
  private inRange(a: AbilityDef, from: Pos, to: Pos) {
    const d = manhattan(from, to);
    const bonus = a.range.max > 1 && this.tiles[from.y][from.x].height - this.tiles[to.y][to.x].height >= 2 ? 1 : 0;
    return d >= a.range.min && d <= a.range.max + bonus;
  }

  /** Valid target tiles for an ability if the caster stood at `from`. */
  targetsFrom(u: Unit, abilityId: string, from: Pos = u): Pos[] {
    const a = this.ability(abilityId);
    const out: Pos[] = [];
    if (a.target === 'self') return [{ x: from.x, y: from.y }];
    const r = a.range.max + 1;
    for (let y = from.y - r; y <= from.y + r; y++) for (let x = from.x - r; x <= from.x + r; x++) {
      if (!this.inBounds(x, y) || !this.inRange(a, from, { x, y })) continue;
      const occ = this.unitAt(x, y);
      const occIsSelf = occ?.uid === u.uid;
      const atSelfTile = x === from.x && y === from.y;
      const target = atSelfTile ? u : (occIsSelf ? undefined : occ);
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

  validTargets(u: Unit, abilityId: string): Pos[] {
    return this.canUse(u, abilityId) ? this.targetsFrom(u, abilityId) : [];
  }

  /** Units hit by an ability aimed at `target` from `from`. */
  affected(u: Unit, abilityId: string, target: Pos, from: Pos = u): Unit[] {
    const a = this.ability(abilityId);
    if (a.target === 'empty') return [];
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
    const base = e.ignoreAttack ? e.amount : this.stat(attacker, 'attack') + e.amount;
    const def = e.pierce ? 0 : this.stat(target, 'defense') + (this.def(target).structure ? 0 : this.terrainAt(target.x, target.y).defense);
    const resist = e.damageType ? this.resistOf(target, e.damageType) : 0;
    return Math.max(0, Math.max(1, base - def + this.heightBonus(from, target)) - resist);
  }

  /** Spell damage: flat amount, reduced by defense/terrain unless pierce, then resist. */
  previewSpellDamage(target: Unit, e: Extract<Effect, { type: 'damage' }>): number {
    const def = e.pierce ? 0 : this.stat(target, 'defense') + (this.def(target).structure ? 0 : this.terrainAt(target.x, target.y).defense);
    const resist = e.damageType ? this.resistOf(target, e.damageType) : 0;
    return Math.max(0, Math.max(1, e.amount - def) - resist);
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
      case 'unit': return this.deployTiles(team);
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
      for (const e of sp.effects) {
        if ((CAST_LEVEL_EFFECTS as readonly string[]).includes(e.type)) this.applyCastEffect(e, team, undefined, this.radiusTiles({ x, y }, sp.area?.size ?? 0), { x, y });
        else for (const t of targets) if (t.alive) this.applyEffect(e, t, undefined, { x, y });
      }
    }
    this.afterAction();
    return true;
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
    const zone = this.map.deployZones[String(team)] ?? [];
    return zone.map(([x, y]) => ({ x, y })).filter(p => !this.unitAt(p.x, p.y) && !this.terrainAt(p.x, p.y).impassable);
  }

  canDeploy(team: number, handIndex: number) {
    const id = this.teams[team].hand[handIndex];
    return this.phase === 'playing' && team === this.current && !!id && this.cardKind(id) === 'unit' &&
      this.content.units[id].cost <= this.teams[team].essence && this.deployTiles(team).length > 0;
  }

  // ---------- actions ----------
  move(uid: number, x: number, y: number): boolean {
    const u = this.unit(uid);
    if (!u || !this.canMove(u) || (u.x === x && u.y === y)) return false;
    const node = this.reachable(u).get(key(x, y));
    if (!node) return false;
    const path = this.pathFrom(this.reachRaw(u, u.ap), x, y);
    u.ap -= node.cost;
    this.emit({ kind: 'move', uid, path });
    for (const step of path.slice(1)) {
      u.x = step.x; u.y = step.y;
      this.enterTile(u);
      if (!u.alive) break;
    }
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
    this.emit({ kind: 'ability', uid, ability: abilityId, target: { x, y } });
    const targets = this.affected(u, abilityId, { x, y });
    for (const e of a.effects) {
      if (!u.alive) break;
      if ((CAST_LEVEL_EFFECTS as readonly string[]).includes(e.type)) this.applyCastEffect(e, u.team, u, this.areaTiles(u, abilityId, { x, y }), { x, y });
      else for (const t of targets) if (t.alive) this.applyEffect(e, t, u);
    }
    this.afterAction();
    return true;
  }

  deploy(team: number, handIndex: number, x: number, y: number): boolean {
    if (!this.canDeploy(team, handIndex)) return false;
    if (!this.deployTiles(team).some(p => p.x === x && p.y === y)) return false;
    const id = this.teams[team].hand[handIndex];
    this.teams[team].essence -= this.content.units[id].cost;
    this.teams[team].hand.splice(handIndex, 1);
    const u = this.spawn(id, team, x, y);
    this.emit({ kind: 'deploy', uid: u.uid });
    this.afterAction();
    return true;
  }

  endTurn() {
    if (this.phase !== 'playing') return;
    // Statuses on the team that just acted tick down.
    for (const u of this.aliveUnits(this.current)) {
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
  private spawn(defId: string, team: number, x: number, y: number, tag?: string): Unit {
    const d = this.content.units[defId];
    const u: Unit = {
      uid: this.nextUid++, defId, team, x, y, hp: d.stats.hp, ap: 0, statuses: [], cooldowns: {},
      summonedThisTurn: true, tag, alive: true,
    };
    this.units.push(u);
    return u;
  }

  private beginTurn() {
    const team = this.teams[this.current];
    if (this.round > 1)
      team.essence = Math.min(this.mission.maxEssence ?? DEFAULTS.maxEssence, team.essence + (this.mission.teams[this.current]?.essencePerTurn ?? this.mission.essencePerTurn ?? DEFAULTS.essencePerTurn));
    this.emit({ kind: 'turn', team: this.current, turn: this.round });
    for (const w of this.map.wells ?? []) {
      const holder = this.unitAt(w.x, w.y);
      if (holder && holder.team === this.current && !this.def(holder).structure) this.gainEssence(this.current, w.amount, { x: w.x, y: w.y });
    }
    for (const u of this.aliveUnits(this.current)) {
      u.summonedThisTurn = false;
      for (const k of Object.keys(u.cooldowns)) u.cooldowns[k] = Math.max(0, u.cooldowns[k] - 1);
      for (const s of [...u.statuses]) for (const e of this.content.statuses[s.id]?.onTurnStart ?? [])
        if (u.alive && (e.type === 'damage' || e.type === 'heal')) this.applyEffect({ ...e, amount: e.amount * (s.stacks ?? 1) }, u);
      u.ap = this.stat(u, 'ap');
    }
    this.runEvents(ev => 'turn' in ev.when && ev.when.turn === this.round && (ev.when.team ?? 0) === this.current);
    this.checkConditions();
  }

  private enterTile(u: Unit) {
    const e = this.terrainAt(u.x, u.y).onEnter;
    if (e) this.applyEffect(e, u);
  }

  /** `source` = casting unit (ability); `origin` = spell target tile used for push/pull direction. */
  private applyEffect(e: Effect, target: Unit, source?: Unit, origin?: Pos) {
    const center: Pos | undefined = source ?? origin;
    switch (e.type) {
      case 'damage': {
        const amt = source ? this.previewDamage(source, target, e) : origin ? this.previewSpellDamage(target, e) : Math.max(1, e.amount);
        this.damage(target, amt, e.damageType);
        break;
      }
      case 'heal': {
        if (e.target === 'caster') { if (!source) break; target = source; }
        const max = this.def(target).stats.hp;
        const amt = Math.min(e.amount, max - target.hp);
        if (amt > 0) { target.hp += amt; this.emit({ kind: 'heal', uid: target.uid, amount: amt }); }
        break;
      }
      case 'status': {
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
      default: break; // cast-level effects are handled in applyCastEffect; auras are passive
    }
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
      case 'summon': {
        for (let i = 0; i < (e.count ?? 1); i++) {
          const p = !this.unitAt(target.x, target.y) && !this.terrainAt(target.x, target.y).impassable ? target : this.nearestFree(target);
          if (!p) return;
          const s = this.spawn(e.unit, team, p.x, p.y);
          this.emit({ kind: 'deploy', uid: s.uid });
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
        if (u?.alive) { u.revived = true; this.damage(u, u.hp, 'sacrifice'); }
        return;
      }
      case 'essence': {
        this.gainEssence(e.team === 'enemy' ? (team === 0 ? 1 : 0) : team, e.amount);
        return;
      }
    }
  }

  private setTerrain(x: number, y: number, terrain: string) {
    this.tiles[y][x].terrain = terrain;
    this.emit({ kind: 'terrain', x, y, terrain });
  }

  private gainEssence(team: number, amount: number, at?: Pos) {
    const t = this.teams[team];
    const before = t.essence;
    t.essence = Math.max(0, Math.min(this.mission.maxEssence ?? DEFAULTS.maxEssence, t.essence + amount));
    if (t.essence !== before) this.emit({ kind: 'essence', team, amount: t.essence - before, ...(at ? { at } : {}) });
  }

  private damage(u: Unit, amount: number, damageType?: string) {
    if (!u.alive) return;
    u.hp -= amount;
    this.emit({ kind: 'damage', uid: u.uid, amount, damageType });
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
        let p: Pos | undefined = !this.unitAt(a.x, a.y) ? { x: a.x, y: a.y } : undefined;
        if (!p) p = this.nearestFree({ x: a.x, y: a.y });
        if (!p) break;
        const u = this.spawn(a.unit, a.team, p.x, p.y, a.tag);
        if (a.team !== this.current) u.summonedThisTurn = false;
        this.emit({ kind: 'deploy', uid: u.uid });
        break;
      }
    }
  }

  private nearestFree(c: Pos): Pos | undefined {
    for (let r = 1; r < 4; r++) for (let y = c.y - r; y <= c.y + r; y++) for (let x = c.x - r; x <= c.x + r; x++)
      if (this.inBounds(x, y) && manhattan({ x, y }, c) === r && !this.unitAt(x, y) && !this.terrainAt(x, y).impassable) return { x, y };
    return undefined;
  }

  private afterAction() { this.checkConditions(); }

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
      case 'eliminate': return !this.teams[c.team].hand.some(id => this.cardKind(id) === 'unit') &&
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

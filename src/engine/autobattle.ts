// Tidewatch: Brinewake's auto-battle mode. Pure run logic, no DOM. See docs/autobattler/DESIGN.md.
// A run is plain JSON (Run). Battles reuse the tactics engine: both crews are AI-controlled units placed on a
// cropped 12x12 arena, and the same Game + aiStep decide the outcome headless (resolveBattle) or on screen.
import { Game, rng } from './game';
import { playAiTurn } from './ai';
import { playableFactions } from './skirmish';
import { isCardUnit } from './content';
import type { Content, MapDef, MissionDef, MissionEvent, Pos, UnitDef } from './types';
import relicsJson from '../../content/relics.json';

// ---------------------------------------------------------------- constants

export const TW = {
  watches: 10,
  startLight: 5,
  startSalvage: 10,
  baseIncome: 8,
  incomePerTide: 5, // 1 salvage per this much Tide gained in battle
  maxTideIncome: 6,
  offerUnits: 4,
  dredgeCost: 2,
  holdSlots: 3,
  maxHymns: 2,
  maxGear: 3,
  maxBerths: 8,
  feedXp: 3,
  arena: 12,
  zoneRows: 3,
  roundCap: 12,
  floodStart: 7,
  lampEaterWatches: [5, 10],
  heroFromWatch: 4,
  heroChance: 0.14,
  enemyBase: 10,
  enemyStep: 9,
  storageKey: 'brinewake.tidewatch.run',
  bestKey: 'brinewake.tidewatch.best',
} as const;

// ---------------------------------------------------------------- types

export interface Crewman { id: number; def: string; xp: number; paid: number; equip?: string; equipPaid?: number; pos?: { x: number; r: number } }
export interface Owned { id: string; paid: number }
export interface Offer { kind: 'unit' | 'spell' | 'equipment'; id: string; marked: boolean; sold: boolean }
export type Outcome = 'win' | 'loss' | 'draw';

export interface BattleResult {
  outcome: Outcome;
  rounds: number;
  capped: boolean;
  /** Tide the crew gained during the battle (wells, drops). */
  tideGained: number;
  survivors: number[];
  fell: number[];
  /** Enemy champions still standing at the end. */
  enemyStanding: number;
  enemyTotal: number;
}

export interface WatchSummary extends BattleResult {
  watch: number;
  enemyName: string;
  lightLost: number;
  /** Salvage that will arrive at the next Tideline. */
  income: number;
  xp: { id: number; def: string; gain: number; rankBefore: number; rankAfter: number; alive: boolean }[];
}

export interface Run {
  v: 1;
  seed: number;
  charter: string[];
  watch: number;
  light: number;
  salvage: number;
  crew: Crewman[];
  hold: Crewman[];
  hymns: Owned[];
  gear: Owned[];
  offers: Offer[];
  rolls: number;
  nextId: number;
  held: number;
  status: 'active' | 'victory' | 'defeat';
  last?: WatchSummary;
}

export interface EnemyMember { def: string; rank: number }
export interface EnemyCrew { faction: string; name: string; lampEater: boolean; members: EnemyMember[]; budget: number }

export type Res = { ok: true; msg: string } | { ok: false; msg: string };
const ok = (msg: string): Res => ({ ok: true, msg });
const no = (msg: string): Res => ({ ok: false, msg });

// ---------------------------------------------------------------- helpers

const mixSeed = (...n: number[]) => { let a = 0x9e3779b9; for (const x of n) a = Math.imul(a ^ (x | 0), 0x85ebca6b) + 0x7f4a7c15 | 0; return a >>> 0; };
const pick = <T>(r: () => number, xs: T[]): T => xs[Math.floor(r() * xs.length)];
function shuffled<T>(r: () => number, xs: T[]): T[] {
  const a = [...xs];
  for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
  return a;
}

/** Salvage price of any card: ceil(cost / 10). */
export const priceOf = (cost: number) => Math.ceil(cost / 10);
export const cardCost = (c: Content, id: string) => (c.units[id] ?? c.spells[id] ?? c.equipment[id])?.cost ?? 0;
export const cardPrice = (c: Content, id: string) => priceOf(cardCost(c, id));
/** Scrap value: half the price paid, rounded down, at least 1. */
export const scrapValue = (paid: number) => Math.max(1, Math.floor(paid / 2));
/** Crew size on the field at a watch: 3 at watch 1, +1 per watch up to 8. */
export const berthsAt = (watch: number) => Math.min(TW.maxBerths, 2 + Math.max(1, watch));
/** Highest card cost offered at a watch. Heroes are exempt from watch 4 on. */
export const tierCap = (watch: number) => watch <= 2 ? 35 : watch <= 4 ? 55 : Infinity;
export const isLampEater = (watch: number) => (TW.lampEaterWatches as readonly number[]).includes(watch);
/** Salvage that arrives at the start of a watch after the first. */
export const incomeFor = (tideGained: number) => TW.baseIncome + Math.min(TW.maxTideIncome, Math.floor(tideGained / TW.incomePerTide));

export const factionName = (c: Content, id: string) => (c.factions?.[id]?.name ?? id).replace(/^The /, '');

// ---------------------------------------------------------------- tempering

interface TemperRank { xpRequired: number; statMods?: Partial<Record<'hp' | 'ap' | 'attack' | 'defense' | 'jump', number>>; addAbility?: string; label: string }
interface RelicEntry { tempering?: TemperRank[] }
const RELICS = relicsJson as unknown as Record<string, RelicEntry>;

export const temperingOf = (def: string): TemperRank[] => RELICS[def]?.tempering ?? [];
export const maxRank = (def: string) => temperingOf(def).length;
/** Tempering rank (0-3) a champion with `xp` has earned. */
export const rankOf = (def: string, xp: number) => temperingOf(def).filter(r => xp >= r.xpRequired).length;
export const rankLabel = (def: string, rank: number) => (rank > 0 ? temperingOf(def)[rank - 1]?.label : undefined);
/** XP still needed for the next rank, or null at the top. */
export function nextRankXp(def: string, xp: number): number | null {
  const t = temperingOf(def)[rankOf(def, xp)];
  return t ? t.xpRequired : null;
}

export const temperedId = (def: string, rank: number) => (rank > 0 ? `tw:${def}:${Math.min(rank, maxRank(def))}` : def);
export const isTempered = (id: string) => id.startsWith('tw:');
export const baseId = (id: string) => (isTempered(id) ? id.split(':')[1] : id);

/** Register the tempered variant `tw:<def>:<rank>` in content.units (idempotent) and return its id. */
export function ensureTempered(c: Content, def: string, rank: number): string {
  const r = Math.min(rank, maxRank(def));
  if (r <= 0 || !c.units[def]) return def;
  const id = `tw:${def}:${r}`;
  if (c.units[id]) return id;
  const base = c.units[def];
  const u: UnitDef = structuredClone(base);
  for (const t of temperingOf(def).slice(0, r)) {
    for (const [k, v] of Object.entries(t.statMods ?? {})) u.stats[k as 'hp'] += v ?? 0;
    if (t.addAbility && c.abilities[t.addAbility] && !u.abilities.includes(t.addAbility)) u.abilities.push(t.addAbility);
  }
  c.units[id] = u;
  return id;
}

/** Remove every synthesized `tw:` unit (they must not leak into Skirmish decks or the collection). */
export function clearTempered(c: Content) {
  for (const id of Object.keys(c.units)) if (isTempered(id)) delete c.units[id];
}

// ---------------------------------------------------------------- run lifecycle

/** Factions that can be chartered: those with at least one champion. */
export const charterFactions = (c: Content) => playableFactions(c);

export function newRun(c: Content, charter: string[], seed: number): Run {
  const fs = [...new Set(charter)].filter(f => c.factions?.[f] || playableFactions(c).includes(f)).slice(0, 2);
  if (!fs.length) throw new Error('A charter needs one or two factions');
  const run: Run = {
    v: 1, seed: seed >>> 0, charter: fs, watch: 1, light: TW.startLight, salvage: TW.startSalvage,
    crew: [], hold: [], hymns: [], gear: [], offers: [], rolls: 0, nextId: 1, held: 0, status: 'active',
  };
  rollOffers(c, run);
  return run;
}

const allMembers = (run: Run) => [...run.crew, ...run.hold];
const memberOf = (run: Run, id: number) => allMembers(run).find(m => m.id === id);
const heroOwned = (c: Content, run: Run) => allMembers(run).some(m => c.units[m.def]?.hero);

// ---------------------------------------------------------------- market

interface Pool { units: string[]; heroes: string[]; spells: string[]; equipment: string[] }

export function poolFor(c: Content, charter: string[], watch: number): Pool {
  const cap = tierCap(watch);
  const inCharter = (f?: string) => !!f && charter.includes(f);
  const units = Object.entries(c.units).filter(([id, u]) => !isTempered(id) && inCharter(u.faction) && isCardUnit(c, id) && u.cost > 0);
  return {
    units: units.filter(([, u]) => !u.hero && u.cost <= cap).map(([id]) => id),
    heroes: watch >= TW.heroFromWatch ? units.filter(([, u]) => u.hero).map(([id]) => id) : [],
    spells: Object.entries(c.spells).filter(([, s]) => inCharter(s.faction) && s.cost <= cap).map(([id]) => id),
    equipment: Object.entries(c.equipment).filter(([, e]) => inCharter(e.faction) && e.cost <= cap).map(([id]) => id),
  };
}

/** Refill every offer slot that is not marked (all of them when called for a new watch or a dredge). Marked cards stay. */
export function rollOffers(c: Content, run: Run) {
  const r = rng(mixSeed(run.seed, run.watch, run.rolls++));
  const pool = poolFor(c, run.charter, run.watch);
  const kept = run.offers.filter(o => o.marked && !o.sold);
  const taken = new Set(kept.map(o => o.id));
  const keptUnits = kept.filter(o => o.kind === 'unit').length;
  const keptExtra = kept.filter(o => o.kind !== 'unit').length;
  let heroPending = !heroOwned(c, run) && !kept.some(o => c.units[o.id]?.hero);
  const out: Offer[] = [...kept];
  for (let i = keptUnits; i < TW.offerUnits; i++) {
    let id: string | undefined;
    if (heroPending && r() < TW.heroChance) { const hs = pool.heroes.filter(h => !taken.has(h)); if (hs.length) { id = pick(r, hs); heroPending = false; } }
    if (!id) { const opts = pool.units.filter(u => !taken.has(u)); if (opts.length) id = pick(r, opts); }
    if (id) { taken.add(id); out.push({ kind: 'unit', id, marked: false, sold: false }); }
  }
  if (!keptExtra) {
    const spell = r() < 0.5;
    const list = (spell ? pool.spells : pool.equipment).filter(x => !taken.has(x));
    const alt = (spell ? pool.equipment : pool.spells).filter(x => !taken.has(x));
    const use = list.length ? list : alt;
    if (use.length) { const id = pick(r, use); out.push({ kind: c.spells[id] ? 'spell' : 'equipment', id, marked: false, sold: false }); }
  }
  // Stable order: champions first, then the spell/equipment slot.
  run.offers = [...out.filter(o => o.kind === 'unit'), ...out.filter(o => o.kind !== 'unit')];
}

export function dredge(c: Content, run: Run): Res {
  if (run.salvage < TW.dredgeCost) return no(`Dredging costs ${TW.dredgeCost} salvage.`);
  run.salvage -= TW.dredgeCost;
  rollOffers(c, run);
  return ok('The Tideline turns over fresh salvage.');
}

export function toggleMark(run: Run, slot: number): Res {
  const o = run.offers[slot];
  if (!o || o.sold) return no('Nothing to mark.');
  o.marked = !o.marked;
  return ok(o.marked ? 'Marked: it stays through a dredge.' : 'Mark removed.');
}

/** Feed XP to a champion (crew or hold). */
export function feedMember(run: Run, id: number, xp: number = TW.feedXp): boolean {
  const m = memberOf(run, id);
  if (!m) return false;
  m.xp += xp;
  return true;
}

export function buy(c: Content, run: Run, slot: number): Res {
  const o = run.offers[slot];
  if (!o || o.sold) return no('That card is gone.');
  const price = cardPrice(c, o.id);
  if (run.salvage < price) return no(`Needs ${price} salvage.`);
  const name = (c.units[o.id] ?? c.spells[o.id] ?? c.equipment[o.id]).name;
  if (o.kind === 'unit') {
    const own = allMembers(run).filter(m => m.def === o.id).sort((a, b) => (run.crew.includes(b) ? 1 : 0) - (run.crew.includes(a) ? 1 : 0) || b.xp - a.xp)[0];
    if (own) {
      run.salvage -= price; o.sold = true; own.xp += TW.feedXp;
      return ok(`${name} is fed ${TW.feedXp} XP.`);
    }
    if (c.units[o.id].hero && heroOwned(c, run)) return no('Your crew already has a hero.');
    const m: Crewman = { id: run.nextId++, def: o.id, xp: 0, paid: price };
    if (run.crew.length < berthsAt(run.watch)) run.crew.push(m);
    else if (run.hold.length < TW.holdSlots) run.hold.push(m);
    else return no('No berth and no hold space. Scrap someone first.');
    run.salvage -= price; o.sold = true;
    return ok(`${name} joins the ${run.crew.includes(m) ? 'crew' : 'hold'}.`);
  }
  if (o.kind === 'spell') {
    if (run.hymns.length >= TW.maxHymns) return no(`Only ${TW.maxHymns} hymns. Scrap one first.`);
    if (run.hymns.some(h => h.id === o.id)) return no('You already know that hymn.');
    run.salvage -= price; o.sold = true; run.hymns.push({ id: o.id, paid: price });
    return ok(`${name} is added to your hymns.`);
  }
  if (run.gear.length >= TW.maxGear) return no('Gear store is full. Equip or scrap something.');
  run.salvage -= price; o.sold = true; run.gear.push({ id: o.id, paid: price });
  return ok(`${name} goes into the gear store.`);
}

export const canEquip = (c: Content, equipId: string, def: string) => {
  const e = c.equipment[equipId], u = c.units[def];
  return !!e && !!u && (!e.restrictTo || e.restrictTo.includes(def) || (!!u.role && e.restrictTo.includes(u.role)));
};

/** Attach stored gear to a champion. An existing item is scrapped. */
export function equip(c: Content, run: Run, gearIndex: number, crewId: number): Res {
  const g = run.gear[gearIndex], m = memberOf(run, crewId);
  if (!g || !m) return no('Nothing to equip.');
  if (!canEquip(c, g.id, m.def)) return no(`${c.units[m.def].name} cannot carry that.`);
  let msg = `${c.equipment[g.id].name} is fitted to ${c.units[m.def].name}.`;
  if (m.equip) { run.salvage += scrapValue(m.equipPaid ?? 1); msg += ` The old ${c.equipment[m.equip]?.name ?? 'gear'} is scrapped.`; }
  m.equip = g.id; m.equipPaid = g.paid;
  run.gear.splice(gearIndex, 1);
  return ok(msg);
}

export function unequip(run: Run, crewId: number): Res {
  const m = memberOf(run, crewId);
  if (!m?.equip) return no('Nothing to remove.');
  if (run.gear.length >= TW.maxGear) return no('Gear store is full.');
  run.gear.push({ id: m.equip, paid: m.equipPaid ?? 1 });
  delete m.equip; delete m.equipPaid;
  return ok('Gear returned to the store.');
}

export type ScrapTarget = { kind: 'crew' | 'hold'; id: number } | { kind: 'hymn' | 'gear'; index: number } | { kind: 'equip'; id: number };
export function scrap(run: Run, t: ScrapTarget): Res {
  if (t.kind === 'crew' || t.kind === 'hold') {
    const list = t.kind === 'crew' ? run.crew : run.hold;
    const i = list.findIndex(m => m.id === t.id);
    if (i < 0) return no('No such champion.');
    const [m] = list.splice(i, 1);
    run.salvage += scrapValue(m.paid) + (m.equip ? scrapValue(m.equipPaid ?? 1) : 0);
    return ok('Scrapped.');
  }
  if (t.kind === 'equip') {
    const m = memberOf(run, t.id);
    if (!m?.equip) return no('Nothing to scrap.');
    run.salvage += scrapValue(m.equipPaid ?? 1); delete m.equip; delete m.equipPaid;
    return ok('Scrapped.');
  }
  const list = t.kind === 'hymn' ? run.hymns : run.gear;
  const idx = (t as { index: number }).index, o = list[idx];
  if (!o) return no('Nothing to scrap.');
  run.salvage += scrapValue(o.paid); list.splice(idx, 1);
  return ok('Scrapped.');
}

export function toCrew(run: Run, id: number): Res {
  const i = run.hold.findIndex(m => m.id === id);
  if (i < 0) return no('Not in the hold.');
  if (run.crew.length >= berthsAt(run.watch)) return no('Every berth is taken.');
  run.crew.push(...run.hold.splice(i, 1));
  return ok('Moved to the crew.');
}
export function toHold(run: Run, id: number): Res {
  const i = run.crew.findIndex(m => m.id === id);
  if (i < 0) return no('Not in the crew.');
  if (run.hold.length >= TW.holdSlots) return no('The hold is full.');
  const [m] = run.crew.splice(i, 1);
  delete m.pos;
  run.hold.push(m);
  return ok('Moved to the hold.');
}

// ---------------------------------------------------------------- enemy crews

export function enemyCrew(c: Content, run: Run, watch = run.watch): EnemyCrew {
  const r = rng(mixSeed(run.seed, watch, 777));
  const fs = playableFactions(c).sort();
  const faction = pick(r, fs);
  const lampEater = isLampEater(watch);
  const budget = TW.enemyBase + TW.enemyStep * (watch - 1);
  const size = berthsAt(watch);
  const rank = (watch >= 9 ? 2 : watch >= 6 ? 1 : 0) + (lampEater ? 1 : 0);
  const cap = tierCap(watch);
  const units = Object.entries(c.units).filter(([id, u]) => !isTempered(id) && u.faction === faction && isCardUnit(c, id) && u.cost > 0);
  const regular = units.filter(([, u]) => !u.hero && u.cost <= cap);
  const minPrice = Math.min(...regular.map(([, u]) => priceOf(u.cost)));
  const members: EnemyMember[] = [];
  let left = budget;
  if (lampEater) {
    const heroes = units.filter(([, u]) => u.hero);
    if (heroes.length) { const [id, u] = pick(r, heroes); members.push({ def: id, rank }); left -= priceOf(u.cost); }
  }
  while (members.length < size) {
    const slotsAfter = size - members.length - 1;
    const opts = regular.filter(([, u]) => priceOf(u.cost) <= left - minPrice * slotsAfter);
    if (!opts.length) break;
    // Greedy for the strongest affordable picks, with a good measure of luck.
    const weights = opts.map(([, u]) => Math.pow(u.cost, 3) * (0.5 + r()));
    let t = r() * weights.reduce((a, b) => a + b, 0), k = 0;
    while (k < opts.length - 1 && (t -= weights[k]) > 0) k++;
    members.push({ def: opts[k][0], rank });
    left -= priceOf(opts[k][1].cost);
  }
  return { faction, name: `${factionName(c, faction)} tithe-crew`, lampEater, members, budget };
}

// ---------------------------------------------------------------- arena

const isBlocked = (c: Content, m: Pick<MapDef, 'legend'>, ch: string) => { const t = c.terrain[m.legend[ch]]; return !t || !!t.void || !!t.impassable; };

/** A 12x12 window of one of the 14 maps with the fewest void / impassable tiles, picked from the run seed and watch. */
export function cropArena(c: Content, seed: number, watch: number): MapDef {
  const n = TW.arena, z = TW.zoneRows;
  const ids = Object.keys(c.maps).filter(id => !id.startsWith('tw:') && c.maps[id].tiles.length >= n && c.maps[id].tiles[0].length >= n).sort();
  const r = rng(mixSeed(seed, 4242));
  const order = shuffled(r, ids);
  const mapId = order[(watch - 1) % order.length];
  const m = c.maps[mapId];
  const wr = rng(mixSeed(seed, watch, 99));
  const cands: { ox: number; oy: number; bad: number; k: number }[] = [];
  for (let oy = 0; oy + n <= m.tiles.length; oy++) for (let ox = 0; ox + n <= m.tiles[0].length; ox++) {
    let bad = 0, top = 0, bot = 0;
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
      const blocked = isBlocked(c, m, m.tiles[oy + y][ox + x]);
      if (blocked) bad++;
      else if (y < z) top++;
      else if (y >= n - z) bot++;
    }
    if (top >= 12 && bot >= 12) cands.push({ ox, oy, bad, k: wr() });
  }
  if (!cands.length) throw new Error(`No usable 12x12 window on ${mapId}`);
  cands.sort((a, b) => a.bad - b.bad || a.k - b.k);
  const best = cands[0].bad;
  const near = cands.filter(w => w.bad <= best + 2).slice(0, 6);
  const w = pick(wr, near);
  const tiles = Array.from({ length: n }, (_, y) => m.tiles[w.oy + y].slice(w.ox, w.ox + n));
  const heights = Array.from({ length: n }, (_, y) => m.heights[w.oy + y].slice(w.ox, w.ox + n));
  const zone = (rows: number[]) => rows.flatMap(y => Array.from({ length: n }, (_, x) => [x, y] as [number, number]).filter(([x, yy]) => !isBlocked(c, m, tiles[yy][x])));
  const wells = (m.wells ?? []).filter(p => p.x >= w.ox && p.x < w.ox + n && p.y >= w.oy && p.y < w.oy + n && !isBlocked(c, m, tiles[p.y - w.oy][p.x - w.ox]))
    .map(p => ({ x: p.x - w.ox, y: p.y - w.oy, amount: p.amount }));
  return {
    id: `tw:${mapId}:${watch}`, name: m.name, description: m.description, legend: m.legend, tiles, heights,
    deployZones: { '0': zone(Array.from({ length: z }, (_, i) => n - 1 - i)), '1': zone(Array.from({ length: z }, (_, i) => i)) },
    wells,
  };
}

/** Mission events for the Flood: round 7 the outer ring, round 8 the next ring in, and so on. */
export function floodEvents(c: Content, arena: MapDef): MissionEvent[] {
  const n = arena.tiles.length, rings = Math.ceil(n / 2);
  const out: MissionEvent[] = [];
  for (let k = 0; k < rings; k++) {
    const turn = TW.floodStart + k;
    if (turn > TW.roundCap) break;
    const ev: MissionEvent = { when: { turn }, do: [] };
    if (k === 0) ev.do.push({ type: 'message', speaker: 'Tidewatch', text: 'The tide is coming back. The shelf floods from the edges inward.' });
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
      if (Math.min(x, y, n - 1 - x, n - 1 - y) !== k) continue;
      if (isBlocked(c, arena, arena.tiles[y][x])) continue;
      ev.do.push({ type: 'terrain', x, y, terrain: 'floodwater', radius: 0 });
    }
    out.push(ev);
  }
  return out;
}

// ---------------------------------------------------------------- formation

const maxReach = (c: Content, u: UnitDef) => Math.max(1, ...u.abilities.map(a => c.abilities[a]).filter(a => a && !a.passive && a.effects.some(e => e.type === 'damage')).map(a => a.range.max));

/** Tile (x, y) for a crew offset: x column, r rows in from the crew's back edge. */
export const tileFor = (arena: MapDef, p: { x: number; r: number }): Pos => ({ x: p.x, y: arena.tiles.length - 1 - p.r });

/** Where each crew champion stands: remembered offsets when still valid, the rest placed automatically (shooters at the back). */
export function layoutCrew(c: Content, run: Run, arena: MapDef, fresh = false): Map<number, Pos> {
  const zone = new Set(arena.deployZones['0'].map(([x, y]) => `${x},${y}`));
  const out = new Map<number, Pos>(), used = new Set<string>();
  if (!fresh) for (const m of run.crew) {
    if (!m.pos) continue;
    const t = tileFor(arena, m.pos), k = `${t.x},${t.y}`;
    if (zone.has(k) && !used.has(k)) { out.set(m.id, t); used.add(k); }
  }
  const free = arena.deployZones['0'].map(([x, y]) => ({ x, y })).filter(p => !used.has(`${p.x},${p.y}`));
  const mid = (arena.tiles.length - 1) / 2;
  const rest = run.crew.filter(m => !out.has(m.id)).sort((a, b) => maxReach(c, c.units[b.def]) - maxReach(c, c.units[a.def]));
  for (const m of rest) {
    // Long reach prefers the back row, short reach the front row; both prefer the middle columns.
    const back = maxReach(c, c.units[m.def]) >= 2;
    free.sort((a, b) => {
      const ra = arena.tiles.length - 1 - a.y, rb = arena.tiles.length - 1 - b.y;
      const sa = (back ? -ra : ra) * 3 + Math.abs(a.x - mid), sb = (back ? -rb : rb) * 3 + Math.abs(b.x - mid);
      return sa - sb;
    });
    const t = free.shift();
    if (t) out.set(m.id, t);
  }
  return out;
}

/** Write a layout back into the crew as remembered offsets. */
export function rememberLayout(run: Run, arena: MapDef, layout: Map<number, Pos>) {
  for (const m of run.crew) {
    const t = layout.get(m.id);
    m.pos = t ? { x: t.x, r: arena.tiles.length - 1 - t.y } : undefined;
    if (!m.pos) delete m.pos;
  }
}

function enemyLayout(c: Content, arena: MapDef, crew: EnemyCrew): Pos[] {
  const free = arena.deployZones['1'].map(([x, y]) => ({ x, y }));
  const mid = (arena.tiles.length - 1) / 2;
  const out: Pos[] = [];
  crew.members.forEach(mem => {
    const back = maxReach(c, c.units[mem.def]) >= 2;
    free.sort((a, b) => ((back ? -a.y : a.y) * 3 + Math.abs(a.x - mid)) - ((back ? -b.y : b.y) * 3 + Math.abs(b.x - mid)));
    const t = free.shift();
    if (t) out.push(t);
  });
  return out;
}

// ---------------------------------------------------------------- battle

export const battleSeed = (run: Run) => mixSeed(run.seed, run.watch, 31337) % 2147483647;

export interface Battle { missionId: string; mission: MissionDef; arena: MapDef; enemy: EnemyCrew; seed: number; crewTags: Map<number, string> }

/** Build the battle mission for the current watch, register its arena and tempered units in `content`, and return it. */
export function buildBattleMission(c: Content, run: Run, opts: { preview?: boolean } = {}): Battle {
  const arena = cropArena(c, run.seed, run.watch);
  c.maps[arena.id] = arena;
  const enemy = enemyCrew(c, run);
  const layout = layoutCrew(c, run, arena);
  const tags = new Map<number, string>();
  const mine = run.crew.filter(m => layout.has(m.id)).map(m => {
    const tag = `c${m.id}`; tags.set(m.id, tag);
    const p = layout.get(m.id)!;
    return { unit: ensureTempered(c, m.def, rankOf(m.def, m.xp)), x: p.x, y: p.y, tag, ...(m.equip ? { equipment: m.equip } : {}) };
  });
  const epos = enemyLayout(c, arena, enemy);
  const theirs = opts.preview ? [] : enemy.members.map((mem, i) => ({ unit: ensureTempered(c, mem.def, mem.rank), x: epos[i].x, y: epos[i].y, tag: `e${i}` })).filter((_, i) => epos[i]);
  const hymns = run.hymns.map(h => h.id);
  const tide = hymns.reduce((n, id) => n + cardCost(c, id), 0);
  const f0 = run.charter[0];
  const mission: MissionDef = {
    id: opts.preview ? 'tw:preview' : 'tw:battle', name: `Watch ${run.watch}${isLampEater(run.watch) ? ': Lamp-eater' : ''}`, description: arena.description, map: arena.id,
    teams: [
      { name: run.charter.map(f => factionName(c, f)).join(' and ') + ' crew', color: c.factions?.[f0]?.color ?? '#e0b84d', controller: 'ai', warband: hymns, units: mine, startingEssence: tide, essencePerTurn: 0 },
      { name: enemy.name, color: c.factions?.[enemy.faction]?.color ?? '#3d8fe0', controller: 'ai', warband: [], units: theirs, startingEssence: 0, essencePerTurn: 0 },
    ],
    startingEssence: 0, essencePerTurn: 0,
    events: floodEvents(c, arena),
  };
  c.missions[mission.id] = mission;
  return { missionId: mission.id, mission, arena, enemy, seed: battleSeed(run), crewTags: tags };
}

const hpFraction = (g: Game, team: number) => {
  let now = 0, max = 0;
  for (const u of g.units) { if (u.team !== team || g.def(u).structure) continue; const m = g.stat(u, 'hp'); max += m; if (u.alive) now += Math.min(u.hp, m); }
  return max > 0 ? now / max : 0;
};

/** Read the result off a finished (or round-capped) game. */
export function resultOf(g: Game, battle: Battle): BattleResult {
  const standing = (team: number) => g.aliveUnits(team).filter(u => !g.def(u).structure);
  const capped = g.phase === 'playing';
  let outcome: Outcome;
  if (g.phase === 'victory') outcome = 'win';
  else if (g.phase === 'defeat') outcome = standing(1).length === 0 ? 'draw' : 'loss';
  else {
    const a = hpFraction(g, 0), b = hpFraction(g, 1);
    outcome = Math.abs(a - b) < 1e-9 ? 'draw' : a > b ? 'win' : 'loss';
  }
  let tide = 0;
  for (const e of g.log) if (e.kind === 'essence' && e.team === 0 && e.amount > 0) tide += e.amount;
  const alive = (tag: string) => g.units.some(u => u.tag === tag && u.alive);
  const mine = [...battle.crewTags.entries()];
  return {
    outcome, rounds: Math.min(g.round, TW.roundCap), capped, tideGained: tide,
    survivors: mine.filter(([, t]) => alive(t)).map(([id]) => id), fell: mine.filter(([, t]) => !alive(t)).map(([id]) => id),
    enemyStanding: standing(1).length, enemyTotal: battle.enemy.members.length,
  };
}

/** Watches a game and captures its result the moment it is decided, or when round 13 would begin (the cap), before the next round's drowning can skew it. */
export function trackBattle(g: Game, battle: Battle): { result: BattleResult | null } {
  const t: { result: BattleResult | null } = { result: null };
  g.on(e => {
    if (t.result) return;
    if (e.kind === 'end' || (e.kind === 'turn' && e.turn > TW.roundCap)) t.result = resultOf(g, battle);
  });
  return t;
}

/** Fight the watch headless with the same seed and AI the on-screen battle uses. */
export function resolveBattle(c: Content, run: Run): BattleResult {
  const battle = buildBattleMission(c, run);
  try {
    const g = new Game(c, battle.missionId, { seed: battle.seed });
    const t = trackBattle(g, battle);
    let guard = 0;
    while (!t.result && guard++ < 200) playAiTurn(g);
    return t.result ?? resultOf(g, battle);
  } finally { clearTempered(c); }
}

/** Apply a battle result to the run: XP, Light, salvage income, next watch (or the end of the run). Returns the summary. */
export function applyBattleResult(c: Content, run: Run, res: BattleResult): WatchSummary {
  const enemy = enemyCrew(c, run);
  const xp = run.crew.filter(m => res.survivors.includes(m.id) || res.fell.includes(m.id)).map(m => {
    const alive = res.survivors.includes(m.id);
    const gain = (alive ? 2 : 1) + (res.outcome === 'win' ? 1 : 0);
    const before = rankOf(m.def, m.xp);
    m.xp += gain;
    return { id: m.id, def: m.def, gain, rankBefore: before, rankAfter: rankOf(m.def, m.xp), alive };
  });
  const lightLost = res.outcome === 'loss' ? (res.enemyStanding >= 3 ? 2 : 1) : 0;
  run.light = Math.max(0, run.light - lightLost);
  if (res.outcome !== 'loss') run.held++;
  const income = incomeFor(res.tideGained);
  const summary: WatchSummary = { ...res, watch: run.watch, enemyName: enemy.name, lightLost, income, xp };
  run.last = summary;
  if (run.light <= 0) run.status = 'defeat';
  else if (run.watch >= TW.watches && res.outcome !== 'loss') run.status = 'victory';
  else {
    // A loss on the final watch with Light left replays that watch instead of running past the last one.
    run.watch = Math.min(run.watch + 1, TW.watches);
    run.salvage += income;
    rollOffers(c, run);
    // Berths grew: promote held champions into open berths automatically.
    while (run.crew.length < berthsAt(run.watch) && run.hold.length) run.crew.push(run.hold.shift()!);
  }
  return summary;
}

// ---------------------------------------------------------------- persistence

const store = (): Storage | null => { try { return typeof localStorage === 'undefined' ? null : localStorage; } catch { return null; } };

export function saveRun(run: Run | null) {
  try {
    const s = store(); if (!s) return;
    if (!run || run.status !== 'active') s.removeItem(TW.storageKey); else s.setItem(TW.storageKey, JSON.stringify(run));
  } catch { /* storage unavailable */ }
}
export function loadRun(): Run | null {
  try {
    const s = store(); const raw = s?.getItem(TW.storageKey);
    if (!raw) return null;
    const r = JSON.parse(raw) as Run;
    return r && r.v === 1 && r.status === 'active' ? r : null;
  } catch { return null; }
}

export interface Best { watch: number; won: boolean }
export function loadBest(): Best | null {
  try { const raw = store()?.getItem(TW.bestKey); return raw ? JSON.parse(raw) as Best : null; } catch { return null; }
}
/** Record a finished run as the best if it beat the old one. */
export function recordBest(run: Run): Best | null {
  const cur: Best = { watch: run.status === 'victory' ? TW.watches : run.watch, won: run.status === 'victory' };
  const old = loadBest();
  const better = !old || (cur.won && !old.won) || (cur.won === old.won && cur.watch > old.watch);
  if (better) { try { store()?.setItem(TW.bestKey, JSON.stringify(cur)); } catch { /* ignore */ } }
  return better ? cur : old;
}

/** Spend a Run's turn through the market with a simple greedy policy. Used by the simulation tests and demo runs. */
export function greedyShop(c: Content, run: Run) {
  const bestSlot = () => {
    let best = -1, score = -1;
    run.offers.forEach((o, i) => {
      if (o.sold) return;
      const price = cardPrice(c, o.id);
      if (price > run.salvage) return;
      let s = cardCost(c, o.id);
      if (o.kind !== 'unit') s = run.crew.length >= berthsAt(run.watch) ? s * 1.2 : s * 0.3;
      if (o.kind === 'unit' && run.crew.length < berthsAt(run.watch) && !allMembers(run).some(m => m.def === o.id)) s += 100;
      if (s > score) { score = s; best = i; }
    });
    return best;
  };
  for (let guard = 0; guard < 40; guard++) {
    const i = bestSlot();
    if (i >= 0) {
      const res = buy(c, run, i);
      if (!res.ok) run.offers[i].sold = true; // cannot use it: skip it
      const o = run.offers[i];
      if (res.ok && o.kind === 'equipment') {
        const gi = run.gear.length - 1;
        const target = [...run.crew].filter(m => canEquip(c, run.gear[gi].id, m.def)).sort((a, b) => c.units[b.def].cost - c.units[a.def].cost)[0];
        if (target) equip(c, run, gi, target.id);
      }
      continue;
    }
    const needBody = run.crew.length < berthsAt(run.watch);
    if (needBody && run.salvage >= TW.dredgeCost + 2 && run.rolls < 400 && guard < 6) { dredge(c, run); continue; }
    break;
  }
}

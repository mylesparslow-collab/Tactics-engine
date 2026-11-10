import type { Game } from './game';
import { manhattan } from './game';
import type { Condition, Effect, Pos, SpellDef, StatusDef, Unit } from './types';

/**
 * Greedy one-ply AI with a threat map and mission awareness. Call aiStep repeatedly; each call performs one
 * decision (a deploy, a card, or a move-and/or-ability for one unit) for game.current and returns false when
 * the team is done.
 *
 * What it knows beyond "hit the nearest thing":
 * - Threat: where the enemy can strike next turn and for how much. It avoids ending moves where it would die
 *   for nothing, and prefers attacking from safer tiles.
 * - Mission objectives: it hunts the units the player must protect (escorts, commanders, garrisons), guards its
 *   own must-survive units (bosses stay behind their line), and walks objective carriers to their goal tiles.
 */
interface TurnMemo { round: number; team: number; done: Set<number> }
const memo = new WeakMap<Game, TurnMemo>();

/**
 * Optional decision noise, per game and team. Without it the AI is fully deterministic, so a matchup on a map
 * always plays out the same way; simulations add a little jitter to sample a spread of games instead.
 */
const noiseOf = new WeakMap<Game, number[]>();
/** Per-team jitter in score points, drawn from the game's seeded RNG (so a seed replays the same game). */
export function setAiNoise(g: Game, amount: number | number[]) {
  noiseOf.set(g, Array.isArray(amount) ? amount : [amount, amount]);
}
const jitter = (g: Game) => {
  const amt = noiseOf.get(g)?.[g.current] ?? 0;
  return amt ? (g.random() - 0.5) * 2 * amt : 0;
};

function turnMemo(g: Game): TurnMemo {
  let m = memo.get(g);
  if (!m || m.round !== g.round || m.team !== g.current) {
    m = { round: g.round, team: g.current, done: new Set() };
    memo.set(g, m);
  }
  return m;
}

const isHarmful = (s?: StatusDef) => !!s && (!!s.preventsMove || !!s.preventsAction ||
  (s.onTurnStart ?? []).some(e => e.type === 'damage') || (s.onAct ?? []).some(e => e.type === 'damage') ||
  Object.values(s.statMods ?? {}).some(v => (v ?? 0) < 0));

/** HP `u` loses after each of its own actions (Venom-like onAct statuses). */
function actTick(g: Game, u: Unit): number {
  let n = 0;
  for (const s of u.statuses) for (const e of g.content.statuses[s.id]?.onAct ?? [])
    if (e.type === 'damage') n += g.previewSpellDamage(u, { ...e, amount: e.amount * (s.stacks ?? 1) });
  return n;
}

/** Decoys and empty shells: not worth chasing or spending a big hit on. Tail segments are proxies, not decoys. */
const isDecoy = (g: Game, o: Unit) => !!g.def(o).decoy || !!g.def(o).emptyShell;

const key = (x: number, y: number) => `${x},${y}`;

// ---------- mission awareness ----------
interface Intel {
  /** Enemy units whose death wins (or helps win) the mission for us. */
  hunt: Set<string>;
  /** Our units whose death loses the mission. */
  guard: Set<string>;
  /** Tiles our tagged units (or any unit, tag '*') must reach. */
  goals: { tag: string; tiles: Pos[] }[];
}

function intel(g: Game, team: number): Intel {
  const obj = g.mission.objectives ?? {};
  // Objectives are written from team 0's point of view.
  const ours: Condition[] = team === 0 ? (obj.victory ?? []) : (obj.defeat ?? []);
  const theirs: Condition[] = team === 0 ? (obj.defeat ?? []) : (obj.victory ?? []);
  const out: Intel = { hunt: new Set(), guard: new Set(), goals: [] };
  for (const c of ours) {
    if (c.not) continue;
    // Things that win for us: the enemy losing a tagged unit.
    if ((c.type === 'unit_lost' || c.type === 'defeat_unit') && c.tag) out.hunt.add(c.tag);
    if (c.type === 'reach_tile' && c.team === team) out.goals.push({ tag: c.tag ?? '*', tiles: c.tiles.map(([x, y]) => ({ x, y })) });
  }
  for (const c of theirs) {
    if (c.not) continue;
    if ((c.type === 'unit_lost' || c.type === 'defeat_unit' || c.type === 'unit_hp_above') && c.tag) out.guard.add(c.tag);
    // The enemy must reach a tile with a unit: hunt that carrier.
    if (c.type === 'reach_tile' && c.team !== team && c.tag) out.hunt.add(c.tag);
  }
  // Tags only count for units of the right side.
  const tagsOf = (t: number) => new Set(g.units.filter(u => u.team === t && u.tag).map(u => u.tag!));
  const mine = tagsOf(team);
  for (const t of [...out.hunt]) if (mine.has(t) && !g.units.some(u => u.team !== team && u.tag === t)) out.hunt.delete(t);
  for (const t of [...out.guard]) if (!mine.has(t)) out.guard.delete(t);
  return out;
}

const isVip = (u: Unit, tags: Set<string>) => !!u.tag && tags.has(u.tag);

// ---------- threat ----------
/** Per tile: the summed raw strike power (attack + bonus) enemies can bring there next turn, and whether it pierces. */
type Threat = Map<string, number>;

function threatMap(g: Game, team: number): Threat {
  const out: Threat = new Map();
  for (const e of g.aliveUnits()) {
    if (e.team === team || g.def(e).structure || g.hasFlag(e, 'preventsAction')) continue;
    const best = new Map<string, number>(); // strongest single hit this enemy can land on each tile
    const ap = g.stat(e, 'ap');
    for (const abId of g.abilitiesOf(e)) {
      const a = g.ability(abId);
      if (!a || a.passive || a.apCost > ap) continue;
      const dmg = a.effects.find((x): x is Extract<Effect, { type: 'damage' }> => x.type === 'damage');
      if (!dmg) continue;
      const power = dmg.ignoreAttack ? dmg.amount : g.stat(e, 'attack') + dmg.amount;
      const reach = g.moveRange(e, ap - a.apCost);
      for (const k of reach.keys()) {
        const [cx, cy] = k.split(',').map(Number);
        const r = a.range.max + (a.area?.size ?? 0) + (a.range.max > 1 ? Math.max(0, g.terrainAt(cx, cy).rangeBonus ?? 0) : 0);
        for (let y = cy - r; y <= cy + r; y++) for (let x = cx - r; x <= cx + r; x++) {
          const d = Math.abs(x - cx) + Math.abs(y - cy);
          if (d > r || d < Math.min(a.range.min, 1) || !g.inBounds(x, y)) continue;
          const kk = key(x, y);
          if ((best.get(kk) ?? 0) < power) best.set(kk, power);
        }
      }
    }
    for (const [k, p] of best) out.set(k, (out.get(k) ?? 0) + p);
  }
  return out;
}

/** Expected damage `u` takes standing on `p` next enemy turn, and how bad that is in score points. */
function danger(g: Game, th: Threat, u: Unit, p: Pos, vip: boolean): number {
  const raw = th.get(key(p.x, p.y)) ?? 0;
  if (!raw) return 0;
  const def = g.stat(u, 'defense') + g.terrainAt(p.x, p.y).defense;
  // Roughly one hit per threatening enemy; defense applies to each, so subtract it about twice.
  const expected = Math.max(0, raw - def * 2);
  const worth = g.def(u).cost / 6 + (g.isHero(u) ? 6 : 0);
  let pen = expected * 0.25;
  // A shell soaks hits before the body (and loses the overflow when it breaks), so it counts toward staying alive.
  if (expected >= u.hp + (u.shellHp ?? 0)) pen += worth;
  return vip ? pen * 3 + (expected > 0 ? 4 : 0) : pen;
}

/** True when a status would hurt its carrier (blocks moving/acting, saps stats, or burns). */
function harmfulStatus(g: Game, id: string): boolean {
  const s = g.content.statuses[id];
  if (!s) return false;
  const mods = Object.values(s.statMods ?? {}).reduce((a: number, b) => a + (b ?? 0), 0);
  return !!s.preventsMove || !!s.preventsAction || mods < 0 || !!s.onTurnStart?.some(e => e.type === 'damage');
}

/** Score cost of walking onto `p` now: only onEnter effects that would really hurt this unit count, scaled by damage. */
function enterPenalty(g: Game, u: Unit, p: Pos): number {
  if (g.def(u).flying) return 0;
  const e = g.terrainAt(p.x, p.y).onEnter;
  if (!e || !g.passesFilter(u, 'filter' in e ? e.filter : undefined)) return 0;
  if (e.type === 'damage') return 1 + e.amount * 0.8;
  if (e.type === 'status' && harmfulStatus(g, e.status)) return 2.5;
  return 0;
}

/** Score value (positive good, negative bad) of ending a move on `p` given its start-of-turn terrain effects. */
function turnStartValue(g: Game, u: Unit, p: Pos): number {
  if (g.def(u).flying) return 0;
  let v = 0;
  const hp = u.hp, max = g.def(u).stats.hp;
  for (const e of g.terrainAt(p.x, p.y).onTurnStart ?? []) {
    if (!g.passesFilter(u, 'filter' in e ? e.filter : undefined)) continue;
    if (e.type === 'heal') v += 0.1 + Math.min(e.amount, Math.max(0, max - hp)) * 0.7;
    else if (e.type === 'damage') {
      const amt = Math.max(1, e.amount - (e.damageType ? g.resistOf(u, e.damageType) : 0));
      v -= amt * 1.2;
      if (hp <= amt) v -= 20 + g.def(u).cost / 6; // it would die
    } else if (e.type === 'status' && harmfulStatus(g, e.status)) v -= 2.5;
  }
  return v;
}

/** Ranged units like ground that extends their reach. */
function rangeTileBonus(g: Game, u: Unit, p: Pos): number {
  return desiredRange(g, u) > 1 ? Math.max(0, g.terrainAt(p.x, p.y).rangeBonus ?? 0) : 0;
}

/** Standing on a Tide Well: Tide every turn plus a forward deploy point. Worth a detour. */
function wellBonus(g: Game, u: Unit, p: Pos): number {
  if (g.def(u).flying) return 0; // flyers hold no Wells
  const w = (g.map.wells ?? []).find(w => w.x === p.x && w.y === p.y);
  if (!w) return 0;
  const occ = g.unitAt(w.x, w.y);
  if (occ && occ.uid !== u.uid) return 0;
  return occ?.uid === u.uid ? 2 : 6; // holding is good, taking is better
}

/** Spilled Tide on the tile: collected by walking onto it. */
function dropBonus(g: Game, p: Pos): number {
  const d = g.drops.find(d => d.x === p.x && d.y === p.y);
  return d ? d.amount / 3 : 0;
}

// ---------- scoring ----------
interface Plan { score: number; to: Pos; ability?: string; target?: Pos }

function scoreAbility(g: Game, u: Unit, abilityId: string, target: Pos, from: Pos, it: Intel): number {
  const a = g.ability(abilityId);
  let s = scoreEffects(g, u.team, a.effects, g.affected(u, abilityId, target, from),
    (o, e) => g.previewDamage(u, o, e, from), it, target);
  // Rehouse: a crab out of its shell badly wants a new one (unless climbing in would cost it more than it gains).
  if (a.effects.some(e => e.type === 'rehouse')) {
    const occ = g.unitAt(target.x, target.y);
    const becomes = occ ? g.def(occ).emptyShell?.becomes : g.terrainAt(target.x, target.y).shellSource;
    const v = becomes ? rehouseValue(g, u, becomes, occ ? occ.hp : undefined) : 0;
    s += v > 0 ? v : -100;
  }
  // moveOut: only to trade a nearly broken shell for a fresh one next to the tile it steps to; otherwise never.
  if (a.effects.some(e => e.type === 'moveOut')) {
    const sh = g.def(u).shell, left = u.shellHp ?? 0;
    const fresh = !!sh && left <= sh.hp * 0.25 && [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => {
      const x = target.x + dx, y = target.y + dy;
      if (!g.inBounds(x, y) || (x === from.x && y === from.y)) return false;
      const o = g.unitAt(x, y);
      if (o) return o.uid !== u.uid && o.team === u.team && !!g.def(o).emptyShell && o.hp > left + 2;
      return !!g.terrainAt(x, y).shellSource;
    });
    s += fresh ? 1.5 : -100;
  }
  // Terrain effects: hazards dropped under enemies are worth something, under friends they hurt.
  const terr = a.effects.find((e): e is Extract<Effect, { type: 'terrain' }> => e.type === 'terrain');
  if (terr) {
    const td = g.content.terrain[terr.terrain];
    const hostile = !!td?.onEnter && td.onEnter.type === 'damage';
    for (const p of g.areaTiles(u, abilityId, target, from)) {
      const o = g.unitAt(p.x, p.y);
      if (!o || g.def(o).structure) continue;
      if (hostile) s += o.team !== u.team ? 2 : -3;
      else if ((td?.defense ?? 0) > 0) s += o.team === u.team ? 1 : 0;
    }
  }
  return s;
}

/** Score of `u` (a crab with no shell) climbing into a shell that turns it into `becomes` with `shellHp` (default: full). */
function rehouseValue(g: Game, u: Unit, becomes: string, shellHp?: number): number {
  const nd = g.content.units[becomes], cur = g.def(u);
  if (!nd?.shell) return 0;
  // A real champion without a shell (not an evicted crab) only trades its own kit up, never down.
  if (!cur.token && nd.cost < cur.cost) return 0;
  const sh = Math.min(nd.shell.hp, shellHp ?? nd.shell.hp);
  const lost = Math.max(0, u.hp - nd.stats.hp); // body HP is capped to the new form's max
  return 6 + sh * 0.6 - lost * 1.2;
}

/** Value of summoning `count` of `unitId` at `at` for `team`. An empty shell is clutter that blocks our own units
 *  unless a crab without a shell can still walk next to it and climb in this turn (it would likely die before the next). */
function summonValue(g: Game, team: number, unitId: string, at: Pos | undefined, count: number): number {
  const d = g.content.units[unitId];
  if (!d?.emptyShell) return 4 * count;
  if (!at) return 0.5;
  let best = 0;
  for (const o of g.aliveUnits(team)) {
    const od = g.def(o);
    if (od.structure || od.shell || o.summonedThisTurn || g.hasFlag(o, 'preventsAction')) continue;
    const rh = g.abilitiesOf(o).find(id => g.ability(id)?.effects.some(e => e.type === 'rehouse'));
    if (!rh || (o.cooldowns[rh] ?? 0) > 0 || manhattan(o, at) > o.ap - g.ability(rh).apCost + 1) continue;
    best = Math.max(best, rehouseValue(g, o, d.emptyShell.becomes, d.stats.hp));
  }
  return best > 0 ? best * 0.8 : 0.5;
}

function scoreEffects(g: Game, team: number, effects: Effect[], hit: Unit[],
  dmg: (o: Unit, e: Extract<Effect, { type: 'damage' }>) => number, it?: Intel, at?: Pos): number {
  let score = 0;
  // Tail segments stand in for their head (damage lands on the head once).
  const seen = new Set<number>();
  hit = hit.map(o => g.proxyOf(o)).filter(o => !seen.has(o.uid) && !!seen.add(o.uid));
  for (const o of hit) {
    const enemy = o.team !== team;
    effects = effects.filter(e => !('filter' in e) || g.passesFilter(o, e.filter));
    const vip = enemy && !!it && isVip(o, it.hunt);
    const decoy = isDecoy(g, o);
    const objective = decoy ? 0.15 : g.def(o).structure ? 1.6 : vip ? 2.5 : 1;
    let hp = o.hp, shell = o.shellHp ?? 0;
    for (const e of effects) {
      if (e.type === 'damage') {
        // A shell soaks the hit (overflow is lost) unless it pierces or is venom.
        if (shell > 0 && !e.pierce && e.damageType !== 'venom') {
          const d = Math.min(dmg(o, e), shell);
          shell -= d;
          score += enemy ? d * 0.8 * objective + (shell <= 0 ? 4 : 0) : -d;
          continue;
        }
        const d = Math.min(dmg(o, e), hp);
        hp -= d;
        score += enemy ? d * objective : -d * 1.5;
        // Kills are what swing a tactics game: worth more for expensive targets, a mission win for VIPs. Husks are worth nothing.
        if (hp <= 0) score += enemy ? (decoy ? 0.5 : (8 + g.def(o).cost / 10) * objective + (vip ? 40 : 0)) : -15;
      } else if (e.type === 'heal') {
        const missing = g.def(o).stats.hp - o.hp;
        const guardBonus = !enemy && it && isVip(o, it.guard) ? 2 : 1;
        if (!enemy) score += Math.min(e.amount, missing) * (missing > 4 ? 1.2 : 0.3) * guardBonus;
      } else if (e.type === 'shell') {
        const sh = g.def(o).shell;
        if (!enemy && sh) score += Math.min(e.amount, sh.hp - (o.shellHp ?? 0)) * 0.8;
      } else if (e.type === 'status') {
        const sd = g.content.statuses[e.status];
        const had = o.statuses.find(s => s.id === e.status);
        // Another stack of a stacking poison is still worth something.
        if (had && sd?.stacks && !g.def(o).structure && (had.stacks ?? 1) < (sd.maxStacks ?? Infinity)) { score += isHarmful(sd) === enemy ? 2 : -2; continue; }
        if (g.def(o).structure || had) continue;
        const harmful = isHarmful(sd);
        const heavy = sd?.preventsAction ? 2 : sd?.preventsMove ? 1.4 : 1;
        if (harmful === enemy) score += 3 * heavy * Math.min(2, e.duration) / 1.5;
        else score -= 3;
      } else if (e.type === 'push' || e.type === 'pull') {
        if (enemy) score += 1;
      }
    }
  }
  for (const e of effects) {
    if (e.type === 'summon') score += summonValue(g, team, e.unit, at, e.count ?? 1);
    if (e.type === 'essence') score += Math.abs(e.amount) / 5;
  }
  return score;
}

function bestPlan(g: Game, u: Unit, th: Threat, it: Intel): Plan | undefined {
  const reach = g.reachable(u);
  const tick = actTick(g, u);
  const vip = isVip(u, it.guard);
  let best: Plan | undefined;
  for (const [k, node] of reach) {
    const [x, y] = k.split(',').map(Number);
    const from = { x, y };
    const left = u.ap - node.cost;
    const hazard = enterPenalty(g, u, from) - turnStartValue(g, u, from) * 0.6 - rangeTileBonus(g, u, from) * 0.4;
    // A drying unit left off wet ground loses HP next turn.
    const risk = danger(g, th, u, from, vip) + g.dryingLoss(u, from) * 1.3;
    // Venom bites after every action: a walk and an ability are two bites. Never act into a Venom death.
    const bites = tick * ((x !== u.x || y !== u.y) ? 2 : 1);
    if (tick > 0 && bites >= u.hp) continue;
    for (const ab of g.abilitiesOf(u)) {
      const a = g.ability(ab);
      if (!a || a.apCost > left || (u.cooldowns[ab] ?? 0) > 0 || g.usedThisTurn(u, ab) || g.hasFlag(u, 'preventsAction') || u.summonedThisTurn) continue;
      if (a.passive || a.effects.some(e => e.type === 'teleport' || e.type === 'swap' || e.type === 'sacrifice')) continue;
      for (const t of g.targetsFrom(u, ab, from)) {
        // Risk is discounted when the action is a kill: trading into danger for a kill is often right.
        const s = scoreAbility(g, u, ab, t, from, it) - node.cost * 0.05 - hazard - a.apCost * 0.1 - risk * 0.6 - bites * 1.2 + wellBonus(g, u, from) * 0.5 + dropBonus(g, from) * 0.5 + jitter(g);
        if (!best || s > best.score) best = { score: s, to: from, ability: ab, target: t };
      }
    }
  }
  return best && best.score > 0.5 ? best : undefined;
}

function desiredRange(g: Game, u: Unit) {
  let r = 1;
  for (const id of g.abilitiesOf(u)) {
    const a = g.ability(id);
    if (a && !a.passive && a.effects.some(e => e.type === 'damage')) r = Math.max(r, a.range.max);
  }
  return r;
}

/** Where to walk when there is nothing worth doing from here: toward goals, enemies, or safety. */
function approach(g: Game, u: Unit, th: Threat, it: Intel): Pos | undefined {
  const reach = g.reachable(u);
  const vip = isVip(u, it.guard);
  const goal = it.goals.find(gl => gl.tag === '*' || gl.tag === u.tag);
  const enemies = g.aliveUnits().filter(o => o.team !== u.team && !isDecoy(g, o));
  // Walking under Venom costs HP: never walk into a Venom death, and only walk when it is worth the bite.
  const tick = actTick(g, u);
  if (tick > 0 && tick >= u.hp) return;
  if (!enemies.length && !goal) return;
  const want = desiredRange(g, u);
  const value = (p: Pos) => {
    if (goal) return Math.min(...goal.tiles.map(t => manhattan(p, t))) * 2;
    // Hunted units pull harder; Beacons pull a little less than live units.
    return Math.min(...enemies.map(o => Math.abs(manhattan(p, o) - want) - (isVip(o, it.hunt) ? 4 : 0) + (g.def(o).structure ? 1 : 0)));
  };
  const cost = (p: Pos, steps: number) => {
    let c = value(p) + steps * 0.01 + (enterPenalty(g, u, p) * 1.3 - turnStartValue(g, u, p) - rangeTileBonus(g, u, p) * 0.6) - (vip ? 0 : wellBonus(g, u, p) + dropBonus(g, p)) + g.dryingLoss(u, p) * 3;
    // An open well within a turn's walk pulls a unit off its march.
    if (!vip && !goal && !g.def(u).flying) {
      const open = (g.map.wells ?? []).filter(w => { const o = g.unitAt(w.x, w.y); return !o || o.uid === u.uid; });
      const near = open.length ? Math.min(...open.map(w => manhattan(p, w))) : 99;
      if (near <= 6) c += near * 0.3 - 1.8;
    }
    // Only lethal danger slows the advance, or the line would never close; VIPs hang back from any danger.
    const d = danger(g, th, u, p, vip);
    c += vip ? d : d > u.hp * 0.25 + g.def(u).cost / 6 ? d * 0.5 : 0;
    // A guarded VIP stays near its friends rather than leading the charge.
    if (vip) {
      const friends = g.aliveUnits(u.team).filter(o => o.uid !== u.uid && !g.def(o).structure);
      if (friends.length) c += Math.max(0, Math.min(...friends.map(o => manhattan(p, o))) - 2);
    }
    return c;
  };
  const here = cost(u, 0);
  let best: { p: Pos; d: number } | undefined;
  for (const [k, node] of reach) {
    const [x, y] = k.split(',').map(Number);
    const d = cost({ x, y }, node.cost) + tick * 1.5 + jitter(g) * 0.5;
    if (!best || d < best.d) best = { p: { x, y }, d };
  }
  return best && best.d < here - 0.5 ? best.p : undefined;
}

function tryDeploy(g: Game): boolean {
  const team = g.teams[g.current];
  // Most expensive affordable unit first.
  const order = team.hand.map((id, i) => ({ i, id, cost: g.cardCost(id) }))
    .filter(h => g.cardKind(h.id) === 'unit' && h.cost <= team.essence).sort((a, b) => b.cost - a.cost);
  if (!order.length) return false;
  const pick = order[0];
  const tiles = g.unitDeployTiles(g.current, pick.id);
  if (!tiles.length) return false;
  const enemies = g.aliveUnits().filter(o => o.team !== g.current);
  const instant = new Set(g.deployTiles(g.current).map(p => key(p.x, p.y)));
  const impact = g.content.units[pick.id].skyfall?.impact ?? 0;
  const ghost = { uid: -1, defId: pick.id, team: g.current, x: 0, y: 0, hp: g.content.units[pick.id].stats.hp, ap: 0, statuses: [], cooldowns: {}, summonedThisTurn: true, alive: true } as Unit;
  const keystones = enemies.filter(o => o.tag?.startsWith('keystone_'));
  // Lower is better. Normal deploys go as close to the enemy as the zone allows; a skyfall drop (only taken when worth something) is scored on the
  // damage its landing would do (kills count extra), with a pull toward the enemy keystone. Tiles are never occupied.
  const score = (p: Pos) => {
    const near = enemies.length ? Math.min(...enemies.map(o => manhattan(p, o))) : 0;
    // Don't land on a damaging vent (unless it heals this unit there); a healing tile is a mild plus.
    const terr = enterPenalty(g, ghost, p) - turnStartValue(g, ghost, p) * 0.5;
    if (instant.has(key(p.x, p.y))) return near + 4 + terr;
    let v = 0, adj = 0;
    for (const o of enemies) {
      if (manhattan(p, o) !== 1) continue;
      adj++;
      const d = Math.max(0, impact - g.resistOf(o, 'physical'));
      v += Math.min(d, o.hp) * (g.def(o).structure ? 1.6 : 1) + (d >= o.hp ? 6 + g.def(o).cost / 10 : 0);
    }
    const ks = keystones.length ? Math.min(...keystones.map(o => manhattan(p, o))) : 99;
    v += Math.max(0, 8 - ks) * 0.6;
    if (adj > 2) v -= (adj - 2) * 2; // do not land in the middle of a crowd
    if (g.content.units[pick.id].dries && g.isWetTile(p.x, p.y)) v += 2; // a drying unit likes to land in water
    return v > 0 ? 4 - v + terr : 100; // a drop that hits nothing and threatens nothing is not worth it
  };
  const tile = tiles.map(p => ({ p, s: score(p) + Math.abs(jitter(g)) })).sort((a, b) => a.s - b.s)[0].p;
  return g.deploy(g.current, pick.i, tile.x, tile.y);
}

/** A spell that turns ground into a shell source: worth what the best bare ally in reach would gain by climbing in. */
function shellSourceValue(g: Game, team: number, sp: SpellDef, p: Pos): number {
  const terr = sp.effects.find((e): e is Extract<Effect, { type: 'terrain' }> => e.type === 'terrain');
  const src = terr && g.content.terrain[terr.terrain]?.shellSource;
  if (!src) return 0;
  const size = sp.area?.size ?? 0;
  let best = 0;
  for (const o of g.aliveUnits(team)) {
    const od = g.def(o);
    if (od.structure || od.shell || manhattan(o, p) > g.stat(o, 'ap') + size) continue;
    if (!g.abilitiesOf(o).some(id => g.ability(id)?.effects.some(e => e.type === 'rehouse'))) continue;
    best = Math.max(best, rehouseValue(g, o, src));
  }
  return best;
}

function tryCards(g: Game, it: Intel): boolean {
  const team = g.current;
  const hand = g.teams[team].hand;
  for (let i = 0; i < hand.length; i++) {
    const kind = g.cardKind(hand[i]);
    if (kind === 'unit') continue;
    const targets = g.cardTargets(team, i);
    if (!targets.length) continue;
    if (kind === 'equipment') {
      // Equip the strongest unit.
      const best = targets.map(p => g.unitAt(p.x, p.y)!).sort((a, b) => (b.hp + g.stat(b, 'attack') * 3) - (a.hp + g.stat(a, 'attack') * 3))[0];
      return g.playCard(team, i, best.x, best.y);
    }
    const sp: SpellDef = g.content.spells[hand[i]];
    let best: { p: Pos; s: number } | undefined;
    for (const p of targets) {
      const s = scoreEffects(g, team, sp.effects, g.spellAffected(team, sp, p), (o, e) => g.previewSpellDamage(o, e), it, p) + shellSourceValue(g, team, sp, p);
      if (!best || s > best.s) best = { p, s };
    }
    // Only cast when worth roughly its cost.
    // Terrain spells are skipped (hard to judge), except ground that bare crabs can climb into.
    if (best && best.s >= sp.cost / 6 && !sp.effects.some(e => e.type === 'terrain' && !g.content.terrain[e.terrain]?.shellSource)) return g.playCard(team, i, best.p.x, best.p.y);
  }
  return false;
}

export function aiStep(g: Game): boolean {
  if (g.phase !== 'playing') return false;
  if (tryDeploy(g)) return true;
  const it = intel(g, g.current);
  if (tryCards(g, it)) return true;
  const m = turnMemo(g);
  const th = threatMap(g, g.current);
  // Act with the units that have the best opportunity first, so kills land before units wander off.
  const ready = g.aliveUnits(g.current).filter(u => !m.done.has(u.uid) && !g.def(u).structure);
  const plans = ready.map(u => ({ u, plan: bestPlan(g, u, th, it) })).sort((a, b) => (b.plan?.score ?? -1) - (a.plan?.score ?? -1));
  for (const { u, plan } of plans) {
    if (plan) {
      if (plan.to.x !== u.x || plan.to.y !== u.y) g.move(u.uid, plan.to.x, plan.to.y);
      if (u.alive && plan.ability && plan.target && g.useAbility(u.uid, plan.ability, plan.target.x, plan.target.y)) return true;
      m.done.add(u.uid);
      return true;
    }
    const step = approach(g, u, th, it);
    m.done.add(u.uid); // one repositioning per unit per turn; it gets re-planned only through bestPlan above
    if (step && g.move(u.uid, step.x, step.y)) return true;
  }
  return false;
}

/** Convenience for tests/simulations: play the whole current turn and end it. */
export function playAiTurn(g: Game, maxSteps = 200) {
  for (let i = 0; i < maxSteps && aiStep(g); i++) { /* keep going */ }
  if (g.phase === 'playing') g.endTurn();
}

import type { Game } from './game';
import { manhattan } from './game';
import type { Effect, Pos, SpellDef, StatusDef, Unit } from './types';

/**
 * Greedy one-ply AI. Call aiStep repeatedly; each call performs one decision (a deploy, or a
 * move-and/or-ability for one unit) for game.current and returns false when the team is done.
 */
interface TurnMemo { round: number; team: number; done: Set<number> }
const memo = new WeakMap<Game, TurnMemo>();

function turnMemo(g: Game): TurnMemo {
  let m = memo.get(g);
  if (!m || m.round !== g.round || m.team !== g.current) {
    m = { round: g.round, team: g.current, done: new Set() };
    memo.set(g, m);
  }
  return m;
}

const isHarmful = (s?: StatusDef) => !!s && (!!s.preventsMove || !!s.preventsAction ||
  (s.onTurnStart ?? []).some(e => e.type === 'damage') || Object.values(s.statMods ?? {}).some(v => (v ?? 0) < 0));

interface Plan { score: number; to: Pos; ability?: string; target?: Pos }

function scoreAbility(g: Game, u: Unit, abilityId: string, target: Pos, from: Pos): number {
  return scoreEffects(g, u.team, g.ability(abilityId).effects, g.affected(u, abilityId, target, from),
    (o, e) => g.previewDamage(u, o, e, from));
}

function scoreEffects(g: Game, team: number, effects: Effect[], hit: Unit[],
  dmg: (o: Unit, e: Extract<Effect, { type: 'damage' }>) => number): number {
  let score = 0;
  for (const o of hit) {
    const enemy = o.team !== team;
    const objective = g.def(o).structure ? 1.5 : 1;
    let hp = o.hp;
    for (const e of effects) {
      if (e.type === 'damage') {
        const d = Math.min(dmg(o, e), hp);
        hp -= d;
        score += enemy ? d * objective : -d * 1.5;
        if (hp <= 0) score += enemy ? 8 * objective : -15;
      } else if (e.type === 'heal') {
        const missing = g.def(o).stats.hp - o.hp;
        if (!enemy) score += Math.min(e.amount, missing) * (missing > 4 ? 1.2 : 0.3);
      } else if (e.type === 'status') {
        if (g.def(o).structure || o.statuses.some(s => s.id === e.status)) continue;
        const harmful = isHarmful(g.content.statuses[e.status]);
        if (harmful === enemy) score += 3;
        else score -= 3;
      } else if (e.type === 'push' || e.type === 'pull') {
        if (enemy) score += 1;
      }
    }
  }
  for (const e of effects) {
    if (e.type === 'summon') score += 4 * (e.count ?? 1);
    if (e.type === 'essence') score += Math.abs(e.amount) / 5;
  }
  return score;
}

function bestPlan(g: Game, u: Unit): Plan | undefined {
  const reach = g.reachable(u);
  let best: Plan | undefined;
  for (const [k, node] of reach) {
    const [x, y] = k.split(',').map(Number);
    const from = { x, y };
    const left = u.ap - node.cost;
    const hazard = g.terrainAt(x, y).onEnter ? 3 : 0;
    for (const ab of g.abilitiesOf(u)) {
      const a = g.ability(ab);
      if (a.apCost > left || (u.cooldowns[ab] ?? 0) > 0 || g.hasFlag(u, 'preventsAction') || u.summonedThisTurn) continue;
      if (a.passive || a.effects.some(e => e.type === 'teleport' || e.type === 'swap' || e.type === 'terrain' || e.type === 'sacrifice')) continue; // AI skips mobility/terrain skills for now
      for (const t of g.targetsFrom(u, ab, from)) {
        const s = scoreAbility(g, u, ab, t, from) - node.cost * 0.05 - hazard - a.apCost * 0.1;
        if (!best || s > best.score) best = { score: s, to: from, ability: ab, target: t };
      }
    }
  }
  return best && best.score > 0.5 ? best : undefined;
}

function desiredRange(g: Game, u: Unit) {
  const first = g.abilitiesOf(u).find(id => !g.ability(id).passive);
  return first ? g.ability(first).range.max : 1;
}

function approach(g: Game, u: Unit): Pos | undefined {
  const enemies = g.aliveUnits().filter(o => o.team !== u.team);
  if (!enemies.length) return;
  const want = desiredRange(g, u);
  const distTo = (p: Pos) => Math.min(...enemies.map(o => Math.abs(manhattan(p, o) - want) + (g.def(o).structure ? 1 : 0)));
  const here = distTo(u);
  let best: { p: Pos; d: number } | undefined;
  for (const [k, node] of g.reachable(u)) {
    const [x, y] = k.split(',').map(Number);
    const d = distTo({ x, y }) + node.cost * 0.01 + (g.terrainAt(x, y).onEnter ? 4 : 0);
    if (!best || d < best.d) best = { p: { x, y }, d };
  }
  return best && best.d < here - 0.5 ? best.p : undefined;
}

function tryDeploy(g: Game): boolean {
  const team = g.teams[g.current];
  const tiles = g.deployTiles(g.current);
  if (!tiles.length) return false;
  // Most expensive affordable unit first.
  const order = team.hand.map((id, i) => ({ i, id, cost: g.cardCost(id) }))
    .filter(h => g.cardKind(h.id) === 'unit' && h.cost <= team.essence).sort((a, b) => b.cost - a.cost);
  if (!order.length) return false;
  const enemies = g.aliveUnits().filter(o => o.team !== g.current);
  const score = (p: Pos) => enemies.length ? Math.min(...enemies.map(o => manhattan(p, o))) : 0;
  const tile = tiles.sort((a, b) => score(a) - score(b))[0];
  return g.deploy(g.current, order[0].i, tile.x, tile.y);
}

function tryCards(g: Game): boolean {
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
      const s = scoreEffects(g, team, sp.effects, g.spellAffected(team, sp, p), (o, e) => g.previewSpellDamage(o, e));
      if (!best || s > best.s) best = { p, s };
    }
    // Only cast when worth roughly its cost.
    if (best && best.s >= sp.cost / 6 && !sp.effects.some(e => e.type === 'terrain')) return g.playCard(team, i, best.p.x, best.p.y);
  }
  return false;
}

export function aiStep(g: Game): boolean {
  if (g.phase !== 'playing') return false;
  if (tryDeploy(g)) return true;
  if (tryCards(g)) return true;
  const m = turnMemo(g);
  for (const u of g.aliveUnits(g.current)) {
    if (m.done.has(u.uid) || g.def(u).structure) continue;
    const plan = bestPlan(g, u);
    if (plan) {
      if (plan.to.x !== u.x || plan.to.y !== u.y) g.move(u.uid, plan.to.x, plan.to.y);
      if (u.alive && plan.ability && plan.target && g.useAbility(u.uid, plan.ability, plan.target.x, plan.target.y)) return true;
      m.done.add(u.uid);
      return true;
    }
    const step = approach(g, u);
    if (step && g.move(u.uid, step.x, step.y)) {
      return true;
    }
    m.done.add(u.uid);
  }
  return false;
}

/** Convenience for tests/simulations: play the whole current turn and end it. */
export function playAiTurn(g: Game, maxSteps = 200) {
  for (let i = 0; i < maxSteps && aiStep(g); i++) { /* keep going */ }
  if (g.phase === 'playing') g.endTurn();
}

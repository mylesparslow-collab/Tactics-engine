// TEMPORARY hermitage balance diagnostics (gated by HMSIM=1). Delete when done.
//   HMSIM=1 HM_OPP=a,b HM_SEEDS=1 HM_SHARD=i/n HM_OUT=file HM_PATCH=patch.json  -> focused sim rows with diagnostics
//   HMSIM=1 HM_LOG=1 HM_OPP=x HM_MAP=m HM_SEAT=0  -> verbose log of one game to stdout
import { it } from 'vitest';
// @ts-expect-error node builtin
import { appendFileSync, readFileSync } from 'node:fs';
import { loadBundledContent } from '../src/engine/bundled';
import { Game } from '../src/engine/game';
import { playAiTurn, setAiNoise } from '../src/engine/ai';
import { buildSkirmish } from '../src/engine/skirmish';
import type { Content } from '../src/engine/types';

declare const process: { env: Record<string, string | undefined> };
const env = process.env;
const F = 'hermitage';

function deepMerge(target: any, patch: any) {
  for (const [k, v] of Object.entries(patch)) {
    if (v && typeof v === 'object' && !Array.isArray(v) && target[k] && typeof target[k] === 'object') deepMerge(target[k], v);
    else target[k] = v;
  }
}

function diag(g: Game, hm: number, log: boolean) {
  const d: any = { deploys: {}, spells: {}, oppSpells: 0, evict: 0, rehouse: 0, moveOut: 0, emptySpawn: 0, emptyUsed: 0,
    dmgBy: [0, 0], shellDmgTaken: 0, bodyDmgTaken: 0, bareDeaths: 0, bareLife: [] as number[], shelledDeaths: 0,
    firstHit: [0, 0], tideSpent: [0, 0], hero: '', bareDmg: 0, shelledDmg: 0 };
  const evictedAt = new Map<number, number>();
  let src: number | undefined;
  const name = (uid: number) => { const u = g.unit(uid); return u ? `${u.defId.replace(/^[a-z]+_/, '')}#${uid}(t${u.team} ${u.hp}${u.shellHp ? '+' + u.shellHp : ''})` : '?' + uid; };
  g.on(e => {
    if (log && e.kind !== 'draw' && e.kind !== 'ready' && e.kind !== 'cooldown' && e.kind !== 'essence') {
      const s = JSON.stringify(e).replace(/"uid":(\d+)/g, (_, n) => `"u":"${name(+n)}"`);
      appendFileSync(env.HM_LOGFILE ?? '/dev/stdout', `r${g.round} t${g.current} ${s}\n`);
    }
    if (e.kind === 'deploy') {
      const u = g.unit(e.uid)!;
      if (u.team === hm) {
        if (g.def(u).emptyShell) d.emptySpawn++;
        else { d.deploys[u.defId] = (d.deploys[u.defId] ?? 0) + 1; if (g.def(u).hero) d.hero = u.defId; }
      }
    } else if (e.kind === 'spell') {
      if (e.team === hm) d.spells[e.spell] = (d.spells[e.spell] ?? 0) + 1; else d.oppSpells++;
      src = -1;
    } else if (e.kind === 'ability') src = e.uid;
    else if (e.kind === 'evict') {
      const u = g.unit(e.uid)!;
      if (u.team === hm) { if (e.voluntary) d.moveOut++; else d.evict++; evictedAt.set(u.uid, g.round); }
    } else if (e.kind === 'rehouse') {
      const u = g.unit(e.uid)!; if (u.team === hm) { d.rehouse++; evictedAt.delete(u.uid); }
    } else if (e.kind === 'vanish') {
      const u = g.unit(e.uid)!; if (u.team === hm && g.def(u).emptyShell) d.emptyUsed++;
    } else if (e.kind === 'damage') {
      const v = g.unit(e.uid)!;
      if (g.def(v).structure && g.def(v).emptyShell) return;
      const atk = src !== undefined && src >= 0 ? g.unit(src) : undefined;
      const team = v.team === 0 ? 1 : 0;
      d.dmgBy[team === hm ? 0 : 1] += e.amount;
      if (!d.firstHit[team === hm ? 0 : 1]) d.firstHit[team === hm ? 0 : 1] = g.round;
      if (atk && atk.team === hm) { if (g.def(atk).shell) d.shelledDmg += e.amount; else d.bareDmg += e.amount; }
      if (v.team === hm) { if (e.shell) d.shellDmgTaken += e.amount; else d.bodyDmgTaken += e.amount; }
    } else if (e.kind === 'death') {
      const u = g.unit(e.uid)!;
      if (u.team === hm && !g.def(u).structure) {
        if (evictedAt.has(u.uid)) { d.bareDeaths++; d.bareLife.push(g.round - evictedAt.get(u.uid)!); }
        else if (g.def(u).shell) d.shelledDeaths++;
      }
    } else if (e.kind === 'turn') src = undefined;
  });
  return d;
}

it.skipIf(!env.HMSIM)('hermitage sim', () => {
  const c: Content = loadBundledContent();
  if (env.HM_PATCH) deepMerge(c, JSON.parse(readFileSync(env.HM_PATCH, 'utf8')));
  const opps = (env.HM_OPP ?? 'salt_concord,gyre').split(',');
  const maps = env.HM_MAP ? env.HM_MAP.split(',') : Object.keys(c.maps);
  const seeds = Number(env.HM_SEEDS ?? 1);
  const [si, sn] = (env.HM_SHARD ?? '0/1').split('/').map(Number);
  const log = !!env.HM_LOG;
  const seats = env.HM_SEAT ? [Number(env.HM_SEAT)] : [0, 1];
  let job = 0;
  for (const o of opps) for (const seat of seats) for (const map of maps) for (let s = 0; s < seeds; s++) {
    if (job++ % sn !== si) continue;
    const pair: [string, string] = seat === 0 ? [F, o] : [o, F];
    const m = buildSkirmish(c, map, pair, ['ai', 'ai']);
    c.missions[m.id] = m;
    const seed = s + 1000 * job + Number(env.HM_SEEDOFF ?? 0);
    const g = new Game(c, m.id, { seed });
    setAiNoise(g, [1.5, 1.5]);
    const d = diag(g, seat, log);
    // Tide spent: track essence before each turn end roughly via deploy costs
    let t = 0;
    while (g.phase === 'playing' && t < 160) { playAiTurn(g); t++; }
    const result = g.phase === 'victory' ? 'p0' : g.phase === 'defeat' ? 'p1' : 'timeout';
    const hp = (team: number) => g.aliveUnits(team).filter(u => !g.def(u).structure).reduce((s, u) => s + u.hp + (u.shellHp ?? 0), 0);
    const row = { mode: 'skirmish', p0: pair[0], p1: pair[1], map, seed, result, rounds: g.round, hmWin: result === (seat === 0 ? 'p0' : 'p1'),
      opp: o, seat, hpHm: hp(seat), hpOpp: hp(1 - seat), ...d };
    if (env.HM_OUT) appendFileSync(env.HM_OUT, JSON.stringify(row) + '\n'); else console.log(JSON.stringify(row));
  }
}, 3_600_000);

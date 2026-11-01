// AI-vs-AI simulation harness for balance work. Gated by SIM=1; run it through tools/sim/run.sh, summarise with tools/sim/report.py.
//   SIM_MODE   skirmish | missions            (default skirmish)
//   SIM_SEEDS  games per pairing/map or per mission (default 4)
//   SIM_NOISE  AI decision jitter in score points (default 1.5); SIM_NOISE_P0 overrides team 0 (the "player" in missions)
//   SIM_SHARD  "i/n": run only every n-th job starting at i (for parallel processes)
//   SIM_PATCH  path to a JSON content patch, deep-merged over content (for trying tuning without editing files)
//   SIM_OUT    path to append JSONL results (default: print to stdout)
//   SIM_CARDS  1 to add per-card tallies (deploys/casts, damage dealt and taken, kills, deaths)
//   SIM_FACTIONS / SIM_MAPS / SIM_MISSIONS  comma lists to restrict the run
import { it } from 'vitest';
// @ts-expect-error node builtin; the project has no @types/node
import { appendFileSync, readFileSync } from 'node:fs';
import { loadBundledContent } from '../src/engine/bundled';
import { Game } from '../src/engine/game';
import { playAiTurn, setAiNoise } from '../src/engine/ai';
import { buildSkirmish, playableFactions } from '../src/engine/skirmish';
import { rosterFor } from '../src/engine/campaign';
import type { Content } from '../src/engine/types';

declare const process: { env: Record<string, string | undefined> };
const env = process.env;

function deepMerge(target: any, patch: any) {
  for (const [k, v] of Object.entries(patch)) {
    if (v && typeof v === 'object' && !Array.isArray(v) && target[k] && typeof target[k] === 'object') deepMerge(target[k], v);
    else target[k] = v;
  }
}

const list = (s?: string) => (s ? s.split(',').map(x => x.trim()).filter(Boolean) : undefined);

/** Per-card tallies: damage is credited to the unit (or spell) whose action caused it. */
function cardStats(g: Game) {
  const out: Record<string, { team: number; n: number; dmg: number; kills: number; taken: number; died: number }> = {};
  const byUid = new Map<number, string>();
  const rec = (id: string, team: number) => (out[`${team}:${id}`] ??= { team, n: 0, dmg: 0, kills: 0, taken: 0, died: 0 });
  let src: string | undefined; let srcTeam = 0;
  g.on(e => {
    if (e.kind === 'deploy') { const u = g.unit(e.uid)!; byUid.set(u.uid, u.defId); rec(u.defId, u.team).n++; }
    else if (e.kind === 'ability') { const u = g.unit(e.uid); src = u?.defId; srcTeam = u?.team ?? 0; }
    else if (e.kind === 'spell') { src = e.spell; srcTeam = e.team; rec(e.spell, e.team).n++; }
    else if (e.kind === 'equip') { const u = g.unit(e.uid); if (u) rec(e.equipment, u.team).n++; }
    else if (e.kind === 'turn') src = undefined;
    else if (e.kind === 'damage' || e.kind === 'death') {
      const v = g.unit(e.uid); if (!v || g.def(v).structure && e.kind === 'death') return;
      if (!byUid.has(v.uid)) { byUid.set(v.uid, v.defId); if (!g.def(v).structure) rec(v.defId, v.team).n++; }
      const mine = !g.def(v).structure ? rec(v.defId, v.team) : undefined;
      const theirs = src && srcTeam !== v.team ? rec(src, srcTeam) : undefined;
      if (e.kind === 'damage') { if (mine) mine.taken += e.amount; if (theirs) theirs.dmg += e.amount; }
      else { if (mine) mine.died++; if (theirs) theirs.kills++; }
    }
  });
  return out;
}

function play(g: Game, noise: number, noiseP0: number) {
  setAiNoise(g, [noiseP0, noise]);
  const cards = env.SIM_CARDS ? cardStats(g) : undefined;
  let t = 0;
  while (g.phase === 'playing' && t < 160) { playAiTurn(g); t++; }
  const obj = g.mission.objectives;
  const why = g.phase === 'defeat' && obj?.defeat ? obj.defeat.filter(c => g.conditionMet(c, true)).map(c => c.label ?? c.type).join(' / ') : undefined;
  const hp = (team: number) => g.aliveUnits(team).filter(u => !g.def(u).structure).reduce((s, u) => s + u.hp, 0);
  return { result: g.phase === 'victory' ? 'p0' : g.phase === 'defeat' ? 'p1' : 'timeout', rounds: g.round, hp0: hp(0), hp1: hp(1), ...(why ? { why } : {}), ...(cards ? { cards } : {}) };
}

it.skipIf(!env.SIM)('simulate', () => {
  const c: Content = loadBundledContent();
  if (env.SIM_PATCH) deepMerge(c, JSON.parse(readFileSync(env.SIM_PATCH, 'utf8')));
  const seeds = Number(env.SIM_SEEDS ?? 4);
  const noise = Number(env.SIM_NOISE ?? 1.5);
  const noiseP0 = Number(env.SIM_NOISE_P0 ?? noise);
  const [si, sn] = (env.SIM_SHARD ?? '0/1').split('/').map(Number);
  const out = (row: object) => {
    const line = JSON.stringify(row);
    if (env.SIM_OUT) appendFileSync(env.SIM_OUT, line + '\n'); else console.log(line);
  };
  let job = 0;
  const mine = () => job++ % sn === si;

  if ((env.SIM_MODE ?? 'skirmish') === 'skirmish') {
    const fs = list(env.SIM_FACTIONS) ?? playableFactions(c);
    const maps = list(env.SIM_MAPS) ?? Object.keys(c.maps);
    for (const a of fs) for (const b of fs) {
      if (a === b) continue;
      for (const map of maps) for (let s = 0; s < seeds; s++) {
        if (!mine()) continue;
        const m = buildSkirmish(c, map, [a, b], ['ai', 'ai']);
        c.missions[m.id] = m;
        const seed = s + 1000 * job;
        const g = new Game(c, m.id, { seed });
        out({ mode: 'skirmish', p0: a, p1: b, map, seed, ...play(g, noise, noiseP0) });
      }
    }
  } else {
    const only = list(env.SIM_MISSIONS);
    for (const [cid, camp] of Object.entries(c.campaigns)) {
      camp.missions.forEach((step, i) => {
        if (only && !only.includes(step.mission)) return;
        for (let s = 0; s < seeds; s++) {
          if (!mine()) continue;
          const roster = rosterFor(c, cid, { completed: i });
          const seed = s + 1000 * job;
          const g = new Game(c, step.mission, { roster, seed });
          out({ mode: 'mission', campaign: cid, index: i, mission: step.mission, seed, ...play(g, noise, noiseP0) });
        }
      });
    }
  }
}, 3_600_000);

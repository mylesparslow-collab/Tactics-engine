// TEMPORARY scratch logger for balance work (deleted afterwards). LOG=1 LOG_A=fac LOG_B=fac LOG_MAP=map LOG_SEED=n
import { it } from 'vitest';
// @ts-expect-error node builtin
import { writeFileSync, readFileSync } from 'node:fs';
import { loadBundledContent } from '../src/engine/bundled';
import { Game } from '../src/engine/game';
import { playAiTurn, setAiNoise } from '../src/engine/ai';
import { buildSkirmish } from '../src/engine/skirmish';
declare const process: { env: Record<string, string | undefined> };
const env = process.env;
function deepMerge(target: any, patch: any) {
  for (const [k, v] of Object.entries(patch)) {
    if (v && typeof v === 'object' && !Array.isArray(v) && target[k] && typeof target[k] === 'object') deepMerge(target[k], v);
    else target[k] = v;
  }
}
it.skipIf(!env.LOG)('log', () => {
  const c = loadBundledContent();
  if (env.SIM_PATCH) deepMerge(c, JSON.parse(readFileSync(env.SIM_PATCH, 'utf8')));
  const m = buildSkirmish(c, env.LOG_MAP!, [env.LOG_A!, env.LOG_B!], ['ai', 'ai']);
  c.missions[m.id] = m;
  const g = new Game(c, m.id, { seed: Number(env.LOG_SEED ?? 1) });
  setAiNoise(g, [1.5, 1.5]);
  const out: string[] = [];
  const nm = (uid: number) => { const u = g.unit(uid); return u ? `${u.team}:${u.defId.replace(/^[a-z]+_/, '')}#${uid}(${u.hp}${u.shellHp ? '+s' + u.shellHp : ''})` : `?${uid}`; };
  g.on((e: any) => {
    switch (e.kind) {
      case 'turn': out.push(`== round ${g.round} team ${e.team} ess ${g.teams[e.team].essence}`); break;
      case 'move': out.push(`  move ${nm(e.uid)} ${e.path.length - 1} steps -> ${e.path[e.path.length - 1].x},${e.path[e.path.length - 1].y}`); break;
      case 'ability': out.push(`  ${nm(e.uid)} uses ${e.ability} @${e.target.x},${e.target.y}`); break;
      case 'react': out.push(`  COIL ${nm(e.uid)} strikes ${nm(e.target)}`); break;
      case 'damage': out.push(`    dmg ${nm(e.uid)} -${e.amount} ${e.damageType ?? ''}${e.shell ? ' [shell]' : ''}`); break;
      case 'death': out.push(`    DEATH ${nm(e.uid)}`); break;
      case 'deploy': out.push(`  deploy ${nm(e.uid)} at ${g.unit(e.uid)?.x},${g.unit(e.uid)?.y}`); break;
      case 'skyfall': out.push(`  skyfall ${e.defId} marker ${e.x},${e.y}`); break;
      case 'spell': out.push(`  SPELL ${e.spell} @${e.target.x},${e.target.y}`); break;
      case 'evict': out.push(`    EVICT ${nm(e.uid)} ${e.from}->${e.to}${e.voluntary ? ' (moveOut)' : ''}`); break;
      case 'rehouse': out.push(`    REHOUSE ${nm(e.uid)} ${e.from}->${e.to}`); break;
      case 'shed': out.push(`    SHED ${nm(e.uid)}`); break;
      case 'status': out.push(`    status ${nm(e.uid)} ${e.status}`); break;
      case 'heal': out.push(`    heal ${nm(e.uid)} +${e.amount}`); break;
      case 'end': out.push(`END ${e.phase}`); break;
    }
  });
  let t = 0;
  while (g.phase === 'playing' && t < 160) { playAiTurn(g); t++; }
  writeFileSync(env.LOG_OUT!, out.join('\n') + `\nRESULT ${g.phase} round ${g.round}\n`);
}, 600_000);

// TEMPORARY scratch diagnostics for balance work (deleted afterwards).
// DIAG=1 DIAG_A=fac DIAG_B=fac DIAG_OUT=file [SIM_PATCH] [SIM_SHARD]
import { it } from 'vitest';
// @ts-expect-error node builtin
import { appendFileSync, readFileSync } from 'node:fs';
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
it.skipIf(!env.DIAG)('diag', () => {
  const c = loadBundledContent();
  if (env.SIM_PATCH) deepMerge(c, JSON.parse(readFileSync(env.SIM_PATCH, 'utf8')));
  const A = env.DIAG_A!, B = env.DIAG_B!;
  const [si, sn] = (env.SIM_SHARD ?? '0/1').split('/').map(Number);
  let job = 0;
  for (const [a, b] of [[A, B], [B, A]]) for (const map of Object.keys(c.maps)) {
    if (job++ % sn !== si) continue;
    const m = buildSkirmish(c, map, [a, b], ['ai', 'ai']);
    c.missions[m.id] = m;
    const g = new Game(c, m.id, { seed: 1000 * job });
    setAiNoise(g, [1.5, 1.5]);
    // tallies keyed by `${team}:${bucket}` : damage taken by that team's units by category
    const t: Record<string, number> = {};
    const add = (k: string, v: number) => { t[k] = (t[k] ?? 0) + v; };
    let src: string | undefined; let srcTeam = -1; let react = false;
    g.on((e: any) => {
      if (e.kind === 'ability') { const u = g.unit(e.uid); if (!react) { src = u?.defId; srcTeam = u?.team ?? -1; } }
      else if (e.kind === 'react') { const u = g.unit(e.uid); src = 'COIL:' + u?.defId; srcTeam = u?.team ?? -1; react = true; add(`${u?.team}:coil_strikes`, 1); }
      else if (e.kind === 'spell') { src = 'SPELL:' + e.spell; srcTeam = e.team; react = false; }
      else if (e.kind === 'move') { react = false; src = undefined; }
      else if (e.kind === 'turn') { src = undefined; react = false; }
      else if (e.kind === 'land') { src = 'LAND'; srcTeam = g.unit(e.uid)?.team ?? -1; }
      else if (e.kind === 'evict' && !e.voluntary) add(`${g.unit(e.uid)?.team}:evictions`, 1);
      else if (e.kind === 'shed') add(`${g.unit(e.uid)?.team}:sheds`, 1);
      else if (e.kind === 'damage') {
        const v = g.unit(e.uid); if (!v) return;
        const d = g.def(v);
        const cat = e.damageType === 'venom' && (src === v.defId || src === undefined) ? 'venom_tick' : e.damageType === 'drying' ? 'drying'
          : d.structure ? (v.tag?.startsWith('keystone') ? 'keystone' : 'structure') : e.shell ? 'shell' : 'body';
        add(`${v.team}:taken_${cat}`, e.amount);
        if (src && srcTeam !== v.team && (cat === 'body' || cat === 'shell')) add(`${v.team}:by:${src.startsWith('COIL') ? 'COIL' : src.startsWith('SPELL') ? 'SPELL' : src === 'LAND' ? 'LAND' : g.content.units[src]?.token ? 'TOKEN:' + src : 'unit'}`, e.amount);
      } else if (e.kind === 'death') {
        const v = g.unit(e.uid); if (!v || g.def(v).structure) return;
        add(`${v.team}:deaths`, 1);
      }
    });
    let n = 0;
    while (g.phase === 'playing' && n < 160) { playAiTurn(g); n++; }
    // normalise to faction names
    const out: Record<string, number> = {};
    for (const [k, v] of Object.entries(t)) { const [tm, ...rest] = k.split(':'); out[`${tm === '0' ? a : b}|${rest.join(':')}`] = v; }
    appendFileSync(env.DIAG_OUT!, JSON.stringify({ p0: a, p1: b, map, result: g.phase === 'victory' ? 'p0' : g.phase === 'defeat' ? 'p1' : 'timeout', rounds: g.round, t: out }) + '\n');
  }
}, 3_600_000);

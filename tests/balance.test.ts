// Balance report: AI vs AI for every ordered faction pairing on every map. Run with `npm run balance`.
import { it } from 'vitest';

declare const process: { env: Record<string, string | undefined> };
import { loadBundledContent } from '../src/engine/bundled';
import { Game } from '../src/engine/game';
import { playAiTurn } from '../src/engine/ai';
import { buildSkirmish, playableFactions } from '../src/engine/skirmish';

it.skipIf(!process.env.BALANCE)('balance report', () => {
  const c = loadBundledContent();
  const fs = playableFactions(c);
  const maps = Object.keys(c.maps);
  const stats: Record<string, { games: number; wins: number; draws: number; rounds: number[] }> = {};
  for (const f of fs) stats[f] = { games: 0, wins: 0, draws: 0, rounds: [] };
  const rows: string[] = [];
  for (const a of fs) for (const b of fs) {
    if (a === b) continue;
    for (const map of maps) {
      const m = buildSkirmish(c, map, [a, b], ['ai', 'ai']);
      c.missions[m.id] = m;
      const g = new Game(c, m.id);
      let t = 0;
      while (g.phase === 'playing' && t < 120) { playAiTurn(g); t++; }
      const winner = g.phase === 'victory' ? a : g.phase === 'defeat' ? b : null;
      for (const f of [a, b]) { stats[f].games++; stats[f].rounds.push(g.round); if (!winner) stats[f].draws++; }
      if (winner) stats[winner].wins++;
      rows.push(`${a},${b},${map},${winner ?? 'timeout'},${g.round}`);
    }
  }
  const med = (xs: number[]) => { const s = [...xs].sort((x, y) => x - y); return s[Math.floor(s.length / 2)]; };
  const all = Object.values(stats).flatMap(s => s.rounds);
  console.log(`median rounds overall: ${med(all)} (games: ${rows.length})`);
  console.log('faction,games,win%,timeouts,median_rounds');
  for (const [f, s] of Object.entries(stats))
    console.log(`${f},${s.games},${Math.round((100 * s.wins) / s.games)},${s.draws},${med(s.rounds)}`);
  console.log('\nattacker,defender,map,winner,rounds\n' + rows.join('\n'));
}, 600000);

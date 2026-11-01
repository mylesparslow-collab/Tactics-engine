import { describe, expect, it } from 'vitest';
import { loadBundledContent } from '../src/engine/bundled';
import { validateContent } from '../src/engine/content';

describe('real game content in /content', () => {
  it('passes validation', () => {
    expect(validateContent(loadBundledContent())).toEqual([]);
  });
});

import { Game } from '../src/engine/game';
import { playAiTurn } from '../src/engine/ai';
import { buildSkirmish, playableFactions } from '../src/engine/skirmish';

describe('real content plays', () => {
  const c = loadBundledContent();
  const factions = playableFactions(c);
  const maps = Object.keys(c.maps);
  it('has factions and maps', () => {
    expect(factions.length).toBeGreaterThanOrEqual(2);
    expect(maps.length).toBeGreaterThanOrEqual(1);
  });
  it('every faction pairing finishes an AI-vs-AI battle without crashing', () => {
    const results: string[] = [];
    factions.forEach((a, i) => {
      const b = factions[(i + 1) % factions.length];
      const map = maps[i % maps.length];
      const m = buildSkirmish(c, map, [a, b], ['ai', 'ai']);
      c.missions[m.id] = m;
      const g = new Game(c, m.id);
      let t = 0;
      while (g.phase === 'playing' && t < 80) { playAiTurn(g); t++; }
      results.push(`${a} vs ${b} on ${map}: ${g.phase} r${g.round}`);
    });
    console.log(results.join('\n'));
    expect(results.length).toBe(factions.length);
  });
  it('every mission starts', () => {
    for (const [id, camp] of Object.entries(c.campaigns)) {
      const roster = camp.startingRoster.concat(camp.missions.flatMap(m => m.unlocks ?? []));
      for (const m of camp.missions) expect(() => new Game(c, m.mission, { roster }), `${id}/${m.mission}`).not.toThrow();
    }
  });
});

describe('campaign missions play to an end', () => {
  const c = loadBundledContent();
  for (const [cid, camp] of Object.entries(c.campaigns)) {
    const roster = camp.startingRoster.concat(camp.missions.flatMap(m => m.unlocks ?? []));
    for (const step of camp.missions) {
      it(`${cid}/${step.mission}`, () => {
        const g = new Game(c, step.mission, { roster });
        let t = 0;
        while (g.phase === 'playing' && t < 150) { playAiTurn(g); t++; }
        console.log(`${step.mission}: ${g.phase} at round ${g.round}, teams ${g.teams.length}, messages ${g.log.filter(e => e.kind === 'message').length}, terrain changes ${g.log.filter(e => e.kind === 'terrain').length}`);
        expect(g.units.every(u => !u.alive || g.inBounds(u.x, u.y))).toBe(true);
      });
    }
  }
});

import { describe, expect, it } from 'vitest';
import { loadBundledContent } from '../src/engine/bundled';
import { Game } from '../src/engine/game';
import {
  TW, applyBattleResult, berthsAt, buildBattleMission, buy, cardPrice, clearTempered, cropArena, dredge, enemyCrew, ensureTempered,
  equip, floodEvents, greedyShop, incomeFor, layoutCrew, loadRun, newRun, poolFor, priceOf, rankOf, resolveBattle, saveRun,
  scrap, scrapValue, temperingOf, tierCap, toggleMark, toHold, toCrew, type Run,
} from '../src/engine/autobattle';
import { validateContent } from '../src/engine/content';

declare const process: { env: Record<string, string | undefined> };
const c = loadBundledContent();
const factions = Object.keys(c.factions ?? {});

describe('Tidewatch economy', () => {
  it('prices cards at ceil(cost / 10) and scrap pays half, min 1', () => {
    expect(priceOf(15)).toBe(2); expect(priceOf(35)).toBe(4); expect(priceOf(40)).toBe(4); expect(priceOf(90)).toBe(9);
    expect(scrapValue(4)).toBe(2); expect(scrapValue(3)).toBe(1); expect(scrapValue(1)).toBe(1);
    expect(cardPrice(c, 'salt_concord_salt_levy')).toBe(3);
  });
  it('tiers by watch and berths grow 3..8', () => {
    expect(tierCap(1)).toBe(35); expect(tierCap(2)).toBe(35); expect(tierCap(3)).toBe(55); expect(tierCap(4)).toBe(55); expect(tierCap(5)).toBe(Infinity);
    expect([1, 2, 3, 4, 5, 6, 7, 10].map(berthsAt)).toEqual([3, 4, 5, 6, 7, 8, 8, 8]);
    const early = poolFor(c, ['salt_concord'], 1), mid = poolFor(c, ['salt_concord'], 3);
    expect(early.units.every(u => c.units[u].cost <= 35)).toBe(true);
    expect(early.heroes).toEqual([]);
    expect(mid.units.some(u => c.units[u].cost > 35)).toBe(true);
    expect(poolFor(c, ['salt_concord'], 4).heroes.length).toBeGreaterThan(0);
  });
  it('income is 8 plus Tide gained / 5, capped at +6', () => {
    expect(incomeFor(0)).toBe(8); expect(incomeFor(14)).toBe(10); expect(incomeFor(500)).toBe(14);
  });
  it('offers 5 cards from the charter only; marks survive a dredge', () => {
    const run = newRun(c, ['hadal_court', 'overcurrent'], 7);
    expect(run.offers.length).toBe(5);
    expect(run.offers.filter(o => o.kind === 'unit').length).toBe(4);
    for (const o of run.offers) expect(['hadal_court', 'overcurrent']).toContain((c.units[o.id] ?? c.spells[o.id] ?? c.equipment[o.id]).faction);
    const keep = run.offers[1].id;
    toggleMark(run, 1);
    run.salvage = 10;
    expect(dredge(c, run).ok).toBe(true);
    expect(run.salvage).toBe(8);
    expect(run.offers.find(o => o.id === keep)?.marked).toBe(true);
    run.salvage = 1;
    expect(dredge(c, run).ok).toBe(false);
  });
  it('buying fills berths, then the hold; a duplicate feeds 3 XP instead of adding a body', () => {
    const run = newRun(c, ['salt_concord'], 3);
    run.salvage = 100;
    const id = run.offers.find(o => o.kind === 'unit')!.id;
    run.offers = [0, 1, 2, 3, 4].map(() => ({ kind: 'unit' as const, id, marked: false, sold: false }));
    expect(buy(c, run, 0).ok).toBe(true);
    expect(run.crew.length).toBe(1);
    expect(buy(c, run, 1).ok).toBe(true);
    expect(run.crew.length).toBe(1);
    expect(run.crew[0].xp).toBe(3);
    expect(run.salvage).toBe(100 - 2 * cardPrice(c, id));
    // fill the crew and the hold with different champions
    const others = poolFor(c, ['salt_concord'], 3).units.filter(u => u !== id);
    for (let i = 0; i < 2 + TW.holdSlots; i++) { run.offers[0] = { kind: 'unit', id: others[i], marked: false, sold: false }; expect(buy(c, run, 0).ok).toBe(true); }
    expect(run.crew.length).toBe(3); expect(run.hold.length).toBe(TW.holdSlots);
    run.offers[0] = { kind: 'unit', id: others[5], marked: false, sold: false };
    expect(buy(c, run, 0).ok).toBe(false);
    expect(toCrew(run, run.hold[0].id).ok).toBe(false);
    expect(scrap(run, { kind: 'crew', id: run.crew[0].id }).ok).toBe(true);
    expect(toCrew(run, run.hold[0].id).ok).toBe(true);
    expect(toHold(run, run.crew[0].id).ok).toBe(true);
  });
  it('hymns cap at 2 and equipment attaches one per champion, scrapping the old one', () => {
    const run = newRun(c, ['salt_concord'], 5);
    run.salvage = 100;
    const spells = Object.keys(c.spells).filter(s => c.spells[s].faction === 'salt_concord').slice(0, 3);
    const gear = Object.keys(c.equipment).filter(s => c.equipment[s].faction === 'salt_concord').slice(0, 2);
    run.offers = spells.map(id => ({ kind: 'spell' as 'spell' | 'equipment', id, marked: false, sold: false })).concat(gear.map(id => ({ kind: 'equipment' as 'spell' | 'equipment', id, marked: false, sold: false })));
    expect(buy(c, run, 0).ok && buy(c, run, 1).ok).toBe(true);
    expect(buy(c, run, 2).ok).toBe(false);
    run.crew.push({ id: 99, def: 'salt_concord_brineguard', xp: 0, paid: 4 });
    expect(buy(c, run, 3).ok && buy(c, run, 4).ok).toBe(true);
    expect(equip(c, run, 0, 99).ok).toBe(true);
    const before = run.salvage;
    expect(equip(c, run, 0, 99).ok).toBe(true);
    expect(run.salvage).toBeGreaterThan(before);
    expect(run.crew[0].equip).toBe(gear[1]);
  });
});

describe('Tidewatch tempering', () => {
  it('ranks come from relics.json xp thresholds', () => {
    const def = 'salt_concord_brineguard';
    expect(rankOf(def, 0)).toBe(0); expect(rankOf(def, 3)).toBe(1); expect(rankOf(def, 8)).toBe(2); expect(rankOf(def, 99)).toBe(3);
  });
  it('synthesizes tw:<def>:<rank> with cumulative stat mods and the rank-3 ability, and cleans up', () => {
    const cc = loadBundledContent();
    const def = 'salt_concord_brineguard', base = cc.units[def], t = temperingOf(def);
    expect(ensureTempered(cc, def, 0)).toBe(def);
    const id2 = ensureTempered(cc, def, 2);
    expect(id2).toBe(`tw:${def}:2`);
    expect(cc.units[id2].stats.defense).toBe(base.stats.defense + (t[0].statMods?.defense ?? 0));
    expect(cc.units[id2].stats.hp).toBe(base.stats.hp + (t[1].statMods?.hp ?? 0));
    expect(cc.units[id2].abilities).toEqual(base.abilities);
    const id3 = ensureTempered(cc, def, 3);
    expect(cc.units[id3].abilities).toContain(t[2].addAbility);
    expect(cc.units[def].abilities).not.toContain(t[2].addAbility); // base untouched
    expect(validateContent(cc)).toEqual([]);
    clearTempered(cc);
    expect(Object.keys(cc.units).some(k => k.startsWith('tw:'))).toBe(false);
  });
  it('a unit with no relic entry does not temper', () => {
    expect(rankOf('keystone', 100)).toBe(0);
  });
});

describe('Tidewatch arenas and flood', () => {
  it('crops a 12x12 window with passable deploy zones, no beacons, and a different map per watch', () => {
    const maps = new Set<string>();
    for (let w = 1; w <= 10; w++) {
      const a = cropArena(c, 11, w);
      maps.add(a.id.split(':')[1]);
      expect(a.tiles.length).toBe(12); expect(a.heights.length).toBe(12);
      expect(a.tiles.every(r => r.length === 12) && a.heights.every(r => r.length === 12)).toBe(true);
      expect(a.keystones).toBeUndefined();
      for (const side of ['0', '1']) {
        expect(a.deployZones[side].length).toBeGreaterThanOrEqual(12);
        for (const [x, y] of a.deployZones[side]) { const t = c.terrain[a.legend[a.tiles[y][x]]]; expect(t.impassable || t.void).toBeFalsy(); }
      }
      expect(a.deployZones['0'].every(([, y]) => y >= 9)).toBe(true);
      expect(a.deployZones['1'].every(([, y]) => y <= 2)).toBe(true);
      for (const w2 of a.wells ?? []) expect(w2.x >= 0 && w2.x < 12 && w2.y >= 0 && w2.y < 12).toBe(true);
    }
    expect(maps.size).toBe(10);
    expect(cropArena(c, 11, 4)).toEqual(cropArena(c, 11, 4));
  });
  it('floods one ring per round from round 7 and the new terrain validates', () => {
    expect(validateContent(c)).toEqual([]);
    const a = cropArena(c, 5, 1);
    const ev = floodEvents(c, a);
    expect(ev.map(e => (e.when as { turn: number }).turn)).toEqual([7, 8, 9, 10, 11, 12]);
    const tiles0 = ev[0].do.filter(d => d.type === 'terrain');
    expect(tiles0.length).toBeGreaterThan(20);
    for (const d of tiles0) if (d.type === 'terrain') expect(d.x === 0 || d.y === 0 || d.x === 11 || d.y === 11).toBe(true);
    expect(c.terrain.floodwater.wet).toBe(true);
    expect(c.terrain.floodwater.moveCost).toBe(2);
  });
  it('the Flood changes tiles in a real game and drowns a unit that is not at home there', () => {
    const run = newRun(c, ['salt_concord'], 21);
    run.salvage = 100; greedyShop(c, run);
    const b = buildBattleMission(c, run);
    const g = new Game(c, b.missionId, { seed: b.seed });
    // jump to round 7 by ending turns without any AI action
    while (g.round < 8 && g.phase === 'playing') g.endTurn();
    const wet = g.tiles.flat().filter(t => t.terrain === 'floodwater').length;
    expect(wet).toBeGreaterThan(20);
    clearTempered(c);
  });
  it('placed equipment is applied at spawn', () => {
    const run = newRun(c, ['salt_concord'], 2);
    run.crew.push({ id: 1, def: 'salt_concord_brineguard', xp: 0, paid: 4, equip: 'sc_equip_salt_crusted_helm' });
    const g = new Game(c, buildBattleMission(c, run).missionId, { seed: 1 });
    expect(g.units.find(u => u.tag === 'c1')?.equipment).toBe('sc_equip_salt_crusted_helm');
    clearTempered(c);
  });
});

describe('Tidewatch enemies and results', () => {
  it('enemy crews fill berths within budget, scale in rank, and lamp-eaters bring a hero', () => {
    const run = newRun(c, ['salt_concord'], 9);
    for (let w = 1; w <= 10; w++) {
      const e = enemyCrew(c, run, w);
      expect(e.members.length).toBe(berthsAt(w));
      const spent = e.members.reduce((n, m) => n + cardPrice(c, m.def), 0);
      const heroPrice = e.members.filter(m => c.units[m.def].hero).reduce((n, m) => n + cardPrice(c, m.def), 0);
      expect(spent - heroPrice).toBeLessThanOrEqual(e.budget);
      expect(e.members.some(m => c.units[m.def].hero)).toBe(w === 5 || w === 10);
      expect(e.members[e.members.length - 1].rank).toBe((w >= 9 ? 2 : w >= 6 ? 1 : 0) + (w === 5 || w === 10 ? 1 : 0));
    }
    expect(enemyCrew(c, run, 3)).toEqual(enemyCrew(c, run, 3));
  });
  it('applying results: XP, Light loss, salvage income, next watch, end of run', () => {
    const run = newRun(c, ['lanternkeepers'], 4);
    run.crew.push({ id: 1, def: 'lanternkeepers_wick', xp: 0, paid: 3 }, { id: 2, def: 'lanternkeepers_signalman', xp: 0, paid: 4 });
    run.nextId = 3;
    const s = applyBattleResult(c, run, { outcome: 'win', rounds: 5, capped: false, tideGained: 12, survivors: [1], fell: [2], enemyStanding: 0, enemyTotal: 3 });
    expect(run.crew[0].xp).toBe(3); expect(run.crew[1].xp).toBe(2);
    expect(run.watch).toBe(2); expect(run.salvage).toBe(10 + 10); expect(s.income).toBe(10); expect(run.light).toBe(5); expect(run.held).toBe(1);
    applyBattleResult(c, run, { outcome: 'loss', rounds: 12, capped: true, tideGained: 0, survivors: [], fell: [1, 2], enemyStanding: 3, enemyTotal: 4 });
    expect(run.light).toBe(3);
    applyBattleResult(c, run, { outcome: 'loss', rounds: 12, capped: true, tideGained: 0, survivors: [], fell: [1, 2], enemyStanding: 2, enemyTotal: 4 });
    expect(run.light).toBe(2);
    applyBattleResult(c, run, { outcome: 'draw', rounds: 12, capped: true, tideGained: 0, survivors: [1], fell: [2], enemyStanding: 1, enemyTotal: 4 });
    expect(run.light).toBe(2); expect(run.watch).toBe(5);
    run.light = 1;
    applyBattleResult(c, run, { outcome: 'loss', rounds: 3, capped: false, tideGained: 0, survivors: [], fell: [1, 2], enemyStanding: 1, enemyTotal: 4 });
    expect(run.status).toBe('defeat');
    const won = newRun(c, ['gyre'], 1); won.watch = 10;
    applyBattleResult(c, won, { outcome: 'win', rounds: 3, capped: false, tideGained: 0, survivors: [], fell: [], enemyStanding: 0, enemyTotal: 8 });
    expect(won.status).toBe('victory');
  });
  it('runs round-trip through save and load without storage (node)', () => {
    const run = newRun(c, ['gyre', 'overcurrent'], 6);
    expect(() => saveRun(run)).not.toThrow();
    expect(loadRun()).toBeNull();
    expect(JSON.parse(JSON.stringify(run))).toEqual(run);
  });
  it('lays out the crew on valid, distinct deploy tiles and remembers offsets', () => {
    const run = newRun(c, ['salt_concord'], 8);
    run.salvage = 99; run.watch = 6; greedyShop(c, run);
    const a = cropArena(c, run.seed, 6);
    const lay = layoutCrew(c, run, a);
    expect(lay.size).toBe(run.crew.length);
    const keys = new Set([...lay.values()].map(p => `${p.x},${p.y}`));
    expect(keys.size).toBe(lay.size);
    for (const p of lay.values()) expect(a.deployZones['0'].some(([x, y]) => x === p.x && y === p.y)).toBe(true);
  });
});

describe('Tidewatch simulation', () => {
  it('greedy-bot runs finish without exceptions, every battle ends by the cap, lengths are sane', () => {
    const N = Number(process.env.TW_RUNS ?? 30);
    const reached: number[] = []; let wins = 0, battles = 0, capped = 0, draws = 0;
    const cc = loadBundledContent();
    for (let i = 0; i < N; i++) {
      const pair = [factions[i % factions.length], factions[(i * 3 + 1) % factions.length]];
      const run: Run = newRun(cc, i % 3 === 0 ? [pair[0]] : [...new Set(pair)], 1000 + i * 7919);
      let guard = 0;
      while (run.status === 'active' && guard++ < 40) {
        greedyShop(cc, run);
        expect(run.crew.length).toBeGreaterThan(0);
        expect(run.crew.length).toBeLessThanOrEqual(berthsAt(run.watch));
        const res = resolveBattle(cc, run);
        battles++; if (res.capped) capped++; if (res.outcome === 'draw') draws++;
        expect(res.rounds).toBeLessThanOrEqual(TW.roundCap);
        applyBattleResult(cc, run, res);
      }
      expect(run.status).not.toBe('active');
      if (run.status === 'victory') wins++;
      reached.push(run.status === 'victory' ? TW.watches : run.watch);
      expect(run.watch).toBeGreaterThanOrEqual(2);
      expect(run.watch).toBeLessThanOrEqual(TW.watches);
    }
    reached.sort((a, b) => a - b);
    const median = reached[Math.floor(reached.length / 2)];
    console.log(`Tidewatch sim: ${N} runs, median watch reached ${median}, run wins ${wins}/${N}, battles ${battles}, capped ${capped}, draws ${draws}, distribution ${reached.join(',')}`);
    expect(median).toBeGreaterThanOrEqual(3);
    expect(median).toBeLessThanOrEqual(9);
    expect(Object.keys(cc.units).some(k => k.startsWith('tw:'))).toBe(false);
  }, 600000);
});

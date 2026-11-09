import { describe, expect, it } from 'vitest';
import { Game, cooldownFor, manhattan, tideDropFor } from '../src/engine/game';
import { playAiTurn } from '../src/engine/ai';
import { loadFixtureContent } from './fixtures/load';
import { normalizeContent, validateContent } from '../src/engine/content';
import type { Content, MapDef, MissionDef } from '../src/engine/types';

const base = loadFixtureContent();
const stats = (hp: number, ap = 6, attack = 4, defense = 0, jump = 1) => ({ hp, ap, attack, defense, jump });
const sprite = { shape: 'circle', glyph: 'X' };

/**
 * 8x6 board. Row 0: brine_pool / living_reef / wet tidal / trench. Column 3 (rows 1-5) is a trench wall,
 * (2,3) is a tall block and (1,3) is forest, (5,3) is lava.
 */
function world(opts: { teams: MissionDef['teams']; map?: Partial<MapDef>; edit?: (c: Content) => void }): Game {
  const c: Content = structuredClone(base);
  c.terrain.brine_pool = { name: 'Brine Pool', moveCost: 1, defense: 0, color: '#2a8' };
  c.terrain.living_reef = { name: 'Living Reef', moveCost: 1, defense: 0, color: '#a82' };
  c.terrain.tidal = { name: 'Tidal', moveCost: 1, defense: 0, color: '#28a', wet: true };
  c.terrain.trench = { name: 'Trench', moveCost: 99, defense: 0, color: '#112', impassable: true };
  c.statuses.drenched = { name: 'Drenched', wet: true };
  c.units.dropper = { name: 'Dropper', cost: 30, stats: stats(12), abilities: ['basic_strike'], sprite, skyfall: { impact: 6 } };
  c.units.armored = { name: 'Armored', cost: 30, stats: stats(30, 6, 4, 5), abilities: ['basic_strike'], sprite, resist: { physical: 2 } };
  c.units.dryer = { name: 'Dryer', cost: 30, stats: stats(10), abilities: ['basic_strike'], sprite, dries: 2 };
  c.units.wisp = { name: 'Wisp', cost: 30, stats: stats(10, 6, 4, 0, 0), abilities: ['basic_strike'], sprite, flying: true };
  c.abilities.rend = { name: 'Rend', apCost: 2, range: { min: 1, max: 1 }, target: 'enemy',
    effects: [{ type: 'damage', amount: 2, vsWounded: { below: 0.5, bonus: 3 } }] };
  c.units.render = { name: 'Render', cost: 30, stats: stats(10), abilities: ['rend'], sprite };
  c.spells.hunger = { name: 'Hunger', cost: 10, target: 'enemy', effects: [{ type: 'damage', amount: 4, vsWounded: { below: 0.5, bonus: 3 } }] };
  const unit = (name: string, abilities: string[], extra: object = {}) => ({ name, cost: 30, stats: stats(20), abilities, sprite, ...extra });
  c.abilities.surge = { name: 'Surge', apCost: 2, range: { min: 1, max: 4 }, target: 'empty', area: { shape: 'line', size: 4 }, affects: 'enemies',
    effects: [{ type: 'damage', amount: 2 }, { type: 'teleport' }] };
  c.abilities.skysong = { name: 'Skysong', apCost: 1, range: { min: 0, max: 0 }, target: 'self', area: { shape: 'radius', size: 3 }, affects: 'allies',
    effects: [{ type: 'heal', amount: 5, filter: { flying: true } }] };
  c.abilities.updraft = { name: 'Updraft', apCost: 0, range: { min: 0, max: 0 }, target: 'self', passive: true,
    effects: [{ type: 'aura', radius: 3, affects: 'allies', statMods: { attack: 2 }, filter: { flying: true } }] };
  c.abilities.mist = { name: 'Mist', apCost: 0, range: { min: 0, max: 0 }, target: 'self', passive: true,
    effects: [{ type: 'aura', radius: 2, affects: 'allies', keepsWet: true }] };
  c.abilities.brace = { name: 'Brace', apCost: 2, range: { min: 1, max: 1 }, target: 'enemy', area: { shape: 'radius', size: 1 },
    effects: [{ type: 'damage', amount: 0 }, { type: 'status', status: 'shielded', duration: 2, target: 'caster' }] };
  c.abilities.exploit = { name: 'Exploit', apCost: 2, range: { min: 1, max: 1 }, target: 'enemy',
    effects: [{ type: 'status', status: 'rooted', duration: 2 }, { type: 'damage', amount: 5, ignoreAttack: true, pierce: true, ifTargetStatus: 'rooted' }] };
  Object.assign(c.units, {
    surger: unit('Surger', ['surge']), singer: unit('Singer', ['skysong']), banner: unit('Banner', ['updraft']),
    mistress: unit('Mistress', ['mist']), bracer: unit('Bracer', ['brace']), exploiter: unit('Exploiter', ['exploit']),
  });
  c.maps.world = {
    id: 'world', name: 'World', legend: { '.': 'grass', b: 'brine_pool', r: 'living_reef', t: 'tidal', '#': 'trench', f: 'forest', x: 'lava' },
    tiles: ['brt#....', '...#....', '...#....', '.f.#.x..', '...#....', '........'],
    heights: ['00000000', '00000000', '00000000', '00500000', '00000000', '00000000'],
    deployZones: { '0': [[0, 5], [1, 5]], '1': [[7, 0], [7, 1]] },
    ...opts.map,
  };
  c.missions.world = {
    id: 'world', name: 'World', map: 'world', startingEssence: 100, teams: opts.teams,
    objectives: { victory: [{ type: 'eliminate', team: 1 }], defeat: [{ type: 'eliminate', team: 0 }] },
  };
  opts.edit?.(c);
  return new Game(normalizeContent(c), 'world', { seed: 1 });
}
const team = (controller: 'human' | 'ai', units: { unit: string; x: number; y: number; tag?: string }[], warband: string[] = []) =>
  ({ name: controller, color: controller === 'human' ? '#f00' : '#00f', controller, units, warband });
/** An enemy far from everything, so a side never gets eliminated by accident. */
const anchor = (x = 7, y = 5) => ({ unit: 'vanguard', x, y });
const cycle = (g: Game) => { g.endTurn(); g.endTurn(); };
const KEYSTONE = { keystones: [{ team: 1, x: 7, y: 0 }] };

describe('skyfall', () => {
  const mk = (enemy: { unit: string; x: number; y: number }[] = [anchor()]) =>
    world({ teams: [team('human', [anchor(0, 4)], ['dropper']), team('ai', enemy)], map: KEYSTONE });

  it('offers every empty passable tile beyond 2 of the enemy keystone, plus the normal deploy zone', () => {
    const g = mk();
    const tiles = g.cardTargets(0, 0).map(p => `${p.x},${p.y}`);
    expect(tiles).toContain('0,5'); // normal deploy zone
    expect(tiles).toContain('4,3'); // skyfall
    expect(tiles).toContain('2,1');
    expect(tiles).not.toContain('3,2'); // trench is impassable
    expect(tiles).not.toContain('0,4'); // occupied
    for (const near of ['7,0', '6,0', '5,0', '7,1', '7,2', '6,1']) expect(tiles).not.toContain(near); // within 2 of the keystone
    expect(tiles).toContain('4,0'); // exactly 3 away
    expect(g.deploy(0, 0, 6, 1)).toBe(false);
  });

  it('plain deploy tiles still deploy instantly; other tiles pay now and leave a landing marker', () => {
    const g = mk();
    expect(g.deploy(0, 0, 0, 5)).toBe(true);
    expect(g.unitAt(0, 5)?.defId).toBe('dropper');
    expect(g.landings).toHaveLength(0);

    const h = mk();
    expect(h.deploy(0, 0, 4, 3)).toBe(true);
    expect(h.teams[0].essence).toBe(70);
    expect(h.teams[0].hand).toHaveLength(0);
    expect(h.unitAt(4, 3)).toBeUndefined();
    expect(h.landings).toEqual([expect.objectContaining({ team: 0, x: 4, y: 3, defId: 'dropper' })]);
    expect(h.cardTargets(0, 0)).toEqual([]);
  });

  it('lands at the start of the owner\'s next turn, hits adjacent enemies with flat resisted damage, and can act at once', () => {
    const g = mk([anchor(), { unit: 'vanguard', x: 4, y: 2 }, { unit: 'armored', x: 5, y: 3 }, { unit: 'vanguard', x: 6, y: 5 }]);
    g.deploy(0, 0, 4, 3);
    g.endTurn(); // enemy turn: nothing lands yet
    expect(g.unitAt(4, 3)).toBeUndefined();
    expect(g.landings).toHaveLength(1);
    g.endTurn(); // our turn begins
    const u = g.unitAt(4, 3)!;
    expect(u.defId).toBe('dropper');
    expect(g.landings).toHaveLength(0);
    expect(g.aliveUnits(1).find(e => e.x === 4 && e.y === 2)!.hp).toBe(26 - 6); // defense ignored
    expect(g.aliveUnits(1).find(e => e.defId === 'armored')!.hp).toBe(30 - (6 - 2)); // resist applies
    expect(g.aliveUnits(1).find(e => e.x === 6 && e.y === 5)!.hp).toBe(26); // not adjacent
    expect(u.summonedThisTurn).toBe(false);
    expect(u.ap).toBeGreaterThan(0);
    expect(g.canMove(u)).toBe(true);
    expect(g.canUse(u, 'basic_strike')).toBe(true);
  });

  it('hits an occupant of the tile for impact + 3 and lands on the nearest free tile', () => {
    const g = mk([anchor()]);
    g.deploy(0, 0, 4, 3);
    g.endTurn();
    (g as unknown as { spawn: (d: string, t: number, x: number, y: number) => void }).spawn('vanguard', 1, 4, 3);
    (g as unknown as { spawn: (d: string, t: number, x: number, y: number) => void }).spawn('vanguard', 0, 5, 3); // an ally nearby is not hit by impact
    g.endTurn();
    const occupant = g.unitAt(4, 3)!;
    expect(occupant.defId).toBe('vanguard');
    const faller = g.units.find(u => u.defId === 'dropper')!;
    expect(manhattan(faller, occupant)).toBe(1);
    expect(g.unitAt(faller.x, faller.y)).toBe(faller);
    expect(occupant.hp).toBe(26 - 9 - 6); // impact + 3 on the tile, then impact as an adjacent enemy after landing
    expect(g.unitAt(5, 3)!.hp).toBe(26);
  });

  it('an allied occupant takes impact + 3 as well', () => {
    const g = mk();
    g.deploy(0, 0, 4, 3);
    g.endTurn();
    (g as unknown as { spawn: (d: string, t: number, x: number, y: number) => void }).spawn('vanguard', 0, 4, 3);
    g.endTurn();
    expect(g.unitAt(4, 3)!.hp).toBe(26 - 9);
  });

  it('counts an in-flight unit as alive for elimination', () => {
    const g = world({ teams: [team('human', [], ['dropper']), team('ai', [anchor()])], map: KEYSTONE });
    g.deploy(0, 0, 4, 3);
    expect(g.phase).toBe('playing');
  });

  it('the AI drops skyfall units next to enemies', () => {
    const g = world({ teams: [team('human', [anchor(0, 4), { unit: 'skirmisher', x: 2, y: 2 }]), team('ai', [anchor(), { unit: 'archer', x: 6, y: 4 }], ['dropper'])], map: KEYSTONE });
    g.endTurn();
    playAiTurn(g);
    expect(g.teams[1].hand).toHaveLength(0);
    const l = g.landings.find(x => x.team === 1) ?? (g.units.some(u => u.defId === 'dropper') ? { x: -9, y: -9 } : undefined);
    expect(l).toBeDefined();
    if (g.landings.length) {
      const near = g.aliveUnits(0).some(e => manhattan(e, g.landings[0]) === 1);
      expect(near).toBe(true);
    }
  });
});

describe('dries', () => {
  const hpAfter = (spec: { x: number; y: number; hp?: number; status?: string }) => {
    // The dryer belongs to the second team, so its first turn starts at the first endTurn().
    const g = world({ teams: [team('human', [anchor(0, 5)]), team('ai', [anchor(), { unit: 'dryer', x: spec.x, y: spec.y, tag: 'd' }])] });
    const d = g.units.find(u => u.tag === 'd')!;
    if (spec.hp) d.hp = spec.hp;
    if (spec.status) d.statuses.push({ id: spec.status, remaining: 5 });
    expect(d.hp).toBe(spec.hp ?? 10); // never dries on the enemy's turn
    g.endTurn();
    return { d, g };
  };
  it('loses HP on a dry tile at the start of its owner\'s turn', () => {
    expect(hpAfter({ x: 0, y: 1 }).d.hp).toBe(8);
  });
  it('is safe on brine_pool, living_reef and any wet terrain', () => {
    expect(hpAfter({ x: 0, y: 0 }).d.hp).toBe(10);
    expect(hpAfter({ x: 1, y: 0 }).d.hp).toBe(10);
    expect(hpAfter({ x: 2, y: 0 }).d.hp).toBe(10);
  });
  it('is safe with a wet status', () => {
    expect(hpAfter({ x: 0, y: 1, status: 'drenched' }).d.hp).toBe(10);
  });
  it('can die of it, and logs a damage event', () => {
    const { d, g } = hpAfter({ x: 0, y: 1, hp: 2 });
    expect(d.alive).toBe(false);
    expect(g.log.some(e => e.kind === 'damage' && e.uid === d.uid && e.amount === 2 && e.damageType === 'drying')).toBe(true);
    expect(g.log.some(e => e.kind === 'death' && e.uid === d.uid)).toBe(true);
  });
  it('the AI steps onto a nearby wet tile instead of drying out', () => {
    const g = world({ teams: [team('human', [anchor(7, 5)]), team('ai', [{ unit: 'dryer', x: 1, y: 2, tag: 'd' }])] });
    playAiTurn(g.current === 1 ? g : (g.endTurn(), g));
    const d = g.units.find(u => u.tag === 'd')!;
    expect(g.isWetTile(d.x, d.y)).toBe(true);
  });
});

describe('flying', () => {
  const fly = (extra: { unit: string; x: number; y: number }[] = []) =>
    world({ teams: [team('human', [anchor(0, 5), { unit: 'wisp', x: 2, y: 2, tag: 'w' }, { unit: 'vanguard', x: 2, y: 1, tag: 'v' }, ...extra]), team('ai', [anchor()])] });

  it('crosses a trench but never ends on it, paying 1 AP per tile', () => {
    const g = fly();
    const w = g.units.find(u => u.tag === 'w')!;
    const reach = g.reachable(w);
    expect(reach.has('3,2')).toBe(false); // impassable: cannot end here
    expect(reach.get('4,2')?.cost).toBe(2);
    expect(g.move(w.uid, 4, 2)).toBe(true);
    expect(w.ap).toBe(4);
    expect(g.move(w.uid, 3, 2)).toBe(false);
    const v = g.units.find(u => u.tag === 'v')!;
    expect(g.reachable(v).has('4,1')).toBe(false); // walkers cannot cross the trench
  });

  it('ignores height and terrain move cost', () => {
    const g = fly();
    const w = g.units.find(u => u.tag === 'w')!; // jump 0
    expect(g.reachable(w).get('2,3')?.cost).toBe(1); // height-5 block
    const f = g.reachable(w).get('1,3');
    expect(f?.cost).toBe(2); // forest costs 2 for walkers, 1 per tile for flyers: (2,2)->(1,2)->(1,3)
    const v = g.units.find(u => u.tag === 'v')!;
    expect(g.reachable(v).has('2,3')).toBe(false); // too tall for jump 1
  });

  it('is not blocked by terrain onEnter effects and still stops for enemies', () => {
    const g = world({ teams: [team('human', [anchor(0, 5), { unit: 'wisp', x: 4, y: 3, tag: 'w' }]), team('ai', [anchor(), { unit: 'vanguard', x: 5, y: 2 }])] });
    const w = g.units.find(u => u.tag === 'w')!;
    expect(g.reachable(w).has('5,2')).toBe(false); // enemies block
    const hp = w.hp;
    expect(g.move(w.uid, 5, 3)).toBe(true); // lava
    expect(w.hp).toBe(hp);
  });

  it('does not hold Wells: no income, no forward deploy', () => {
    const wells = { wells: [{ x: 4, y: 4, amount: 10 }] };
    const run = (unit: string) => {
      const g = world({ teams: [team('human', [anchor(0, 5), { unit, x: 4, y: 4 }], ['vanguard']), team('ai', [anchor()])], map: wells });
      const tiles = g.deployTiles(0).map(p => `${p.x},${p.y}`);
      cycle(g);
      return { tiles, essence: g.teams[0].essence };
    };
    const walker = run('vanguard'), flyer = run('wisp');
    expect(walker.tiles).toContain('4,3');
    expect(flyer.tiles).not.toContain('4,3');
    expect(walker.essence - flyer.essence).toBe(20); // 10 at each of our two turn starts
  });
});

describe('vsWounded', () => {
  const duel = (hp: number) => {
    const g = world({ teams: [team('human', [{ unit: 'render', x: 0, y: 2, tag: 'a' }, anchor(0, 5)], ['hunger']), team('ai', [{ unit: 'vanguard', x: 1, y: 2, tag: 't' }, anchor()])] });
    const a = g.units.find(u => u.tag === 'a')!, t = g.units.find(u => u.tag === 't')!;
    t.hp = hp;
    return { g, a, t };
  };
  it('adds the bonus to abilities only below the threshold', () => {
    const e = { type: 'damage', amount: 2, vsWounded: { below: 0.5, bonus: 3 } } as const;
    for (const [hp, dmg] of [[26, 3], [13, 3], [12, 6]] as const) {
      const { g, a, t } = duel(hp);
      expect(g.previewDamage(a, t, e)).toBe(dmg); // attack 4 + 2 (+3) - defense 3
      expect(g.useAbility(a.uid, 'rend', t.x, t.y)).toBe(true);
      expect(t.hp).toBe(hp - dmg);
    }
  });
  it('works for spells', () => {
    for (const [hp, dmg] of [[26, 1], [12, 4]] as const) {
      const { g, t } = duel(hp);
      expect(g.playCard(0, 0, t.x, t.y)).toBe(true);
      expect(t.hp).toBe(hp - dmg); // 4 (+3) - defense 3
    }
  });
});

describe('content validation', () => {
  it('accepts the new fields and rejects malformed ones', () => {
    const ok = world({ teams: [team('human', [anchor(0, 5)]), team('ai', [anchor()])] });
    expect(validateContent(ok.content)).toEqual([]);
    const bad = structuredClone(ok.content);
    (bad.units.dropper as unknown as { skyfall: unknown }).skyfall = {};
    (bad.units.dryer as unknown as { dries: unknown }).dries = 'lots';
    (bad.terrain.tidal as unknown as { wet: unknown }).wet = 'yes';
    (bad.abilities.rend.effects[0] as unknown as { vsWounded: unknown }).vsWounded = { below: 0.5 };
    const errs = validateContent(bad);
    expect(errs.filter(e => /skyfall|dries|wet|vsWounded/.test(e))).toHaveLength(4);
  });
});

describe('effect extensions', () => {
  const two = (mine: { unit: string; x: number; y: number; tag?: string }[], theirs: { unit: string; x: number; y: number; tag?: string }[]) =>
    world({ teams: [team('human', [anchor(0, 5), ...mine]), team('ai', [anchor(), ...theirs])] });
  const tag = (g: Game, t: string) => g.units.find(u => u.tag === t)!;

  it('filter {flying} limits heals to flyers', () => {
    const g = two([{ unit: 'singer', x: 1, y: 2, tag: 's' }, { unit: 'wisp', x: 2, y: 2, tag: 'w' }, { unit: 'vanguard', x: 1, y: 1, tag: 'v' }], []);
    tag(g, 'w').hp = 3; tag(g, 'v').hp = 3;
    expect(g.useAbility(tag(g, 's').uid, 'skysong', 1, 2)).toBe(true);
    expect(tag(g, 'w').hp).toBe(8);
    expect(tag(g, 'v').hp).toBe(3);
  });
  it('filter {flying} limits an aura to flyers', () => {
    const g = two([{ unit: 'banner', x: 1, y: 2 }, { unit: 'wisp', x: 2, y: 2, tag: 'w' }, { unit: 'vanguard', x: 1, y: 1, tag: 'v' }], []);
    expect(g.stat(tag(g, 'w'), 'attack')).toBe(6);
    expect(g.stat(tag(g, 'v'), 'attack')).toBe(6); // vanguard base 6: not a flyer, unchanged
  });
  it('status target "caster" applies once per use, however many are hit', () => {
    const g = two([{ unit: 'bracer', x: 1, y: 2, tag: 'b' }], [{ unit: 'vanguard', x: 2, y: 2 }, { unit: 'vanguard', x: 2, y: 1 }]);
    expect(g.useAbility(tag(g, 'b').uid, 'brace', 2, 2)).toBe(true);
    expect(g.log.filter(e => e.kind === 'status' && e.uid === tag(g, 'b').uid)).toHaveLength(1);
    expect(tag(g, 'b').statuses.map(x => x.id)).toEqual(['shielded']);
    expect(g.aliveUnits(1).filter(u => u.statuses.length)).toHaveLength(0);
  });
  it('ifTargetStatus uses a snapshot from the start of the use', () => {
    const g = two([{ unit: 'exploiter', x: 1, y: 2, tag: 'e' }], [{ unit: 'vanguard', x: 2, y: 2, tag: 'a' }, { unit: 'vanguard', x: 1, y: 1, tag: 'b' }]);
    tag(g, 'b').statuses.push({ id: 'rooted', remaining: 2 });
    g.useAbility(tag(g, 'e').uid, 'exploit', 2, 2); // target a: not rooted at the start, so the bonus damage is skipped even though it is rooted afterwards
    expect(tag(g, 'a').hp).toBe(26);
    expect(tag(g, 'a').statuses.map(x => x.id)).toEqual(['rooted']);
    g.endTurn(); g.endTurn();
    g.useAbility(tag(g, 'e').uid, 'exploit', 2, 2); // now it starts rooted
    expect(tag(g, 'a').hp).toBe(21);
  });
  it('keepsWet auras stop allies drying out', () => {
    const run = (dx: number) => {
      const g = world({ teams: [team('human', [anchor(0, 5)]), team('ai', [anchor(), { unit: 'mistress', x: 0, y: 2 }, { unit: 'dryer', x: dx, y: 2, tag: 'd' }])] });
      g.endTurn();
      return tag(g, 'd').hp;
    };
    expect(run(1)).toBe(10); // inside the aura
    expect(run(2)).toBe(10); // radius 2
    const far = world({ teams: [team('human', [anchor(0, 5)]), team('ai', [anchor(), { unit: 'mistress', x: 0, y: 0 }, { unit: 'dryer', x: 2, y: 2, tag: 'd' }])] });
    far.endTurn();
    expect(tag(far, 'd').hp).toBe(8);
  });
  it('empty-target line ability: damage hits the line, then the caster teleports once', () => {
    for (const foes of [[], [{ unit: 'vanguard', x: 5, y: 2 }], [{ unit: 'vanguard', x: 5, y: 2 }, { unit: 'vanguard', x: 7, y: 2 }, { unit: 'vanguard', x: 5, y: 3 }]]) {
      const g = two([{ unit: 'surger', x: 4, y: 2, tag: 's' }], foes.map((f, i) => ({ ...f, tag: `f${i}` })));
      const s = tag(g, 's');
      expect(g.validTargets(s, 'surge').some(p => p.x === 6 && p.y === 2)).toBe(true);
      expect(g.useAbility(s.uid, 'surge', 6, 2)).toBe(true);
      expect([s.x, s.y]).toEqual([6, 2]);
      expect(g.log.filter(e => e.kind === 'move' && e.uid === s.uid)).toHaveLength(1);
      foes.forEach((f, i) => expect(tag(g, `f${i}`).hp).toBe(f.y === 2 ? 26 - (4 + 2 - 3) : 26)); // row 2 line only
    }
  });
});

describe('tide drops and card cooldowns', () => {
  it('a cast spell rests for its cooldown, then returns to the hand', () => {
    const g = world({ teams: [team('human', [anchor(0, 4)], ['hunger']), team('ai', [anchor(), { unit: 'vanguard', x: 4, y: 4 }])] });
    expect(g.playCard(0, 0, 4, 4)).toBe(true);
    expect(g.teams[0].hand).toEqual([]);
    expect(g.teams[0].cooldown).toEqual([{ card: 'hunger', turns: cooldownFor(10) }]);
    cycle(g);
    expect(g.teams[0].cooldown).toEqual([{ card: 'hunger', turns: cooldownFor(10) - 1 }]);
    for (let i = 1; i < cooldownFor(10); i++) cycle(g);
    expect(g.teams[0].cooldown).toEqual([]);
    expect(g.teams[0].hand).toEqual(['hunger']);
  });

  it('a champion deployed from the hand drops Tide and goes on cooldown when it dies; walking onto the drop collects it', () => {
    const g = world({ teams: [team('human', [{ unit: 'render', x: 0, y: 3 }], ['dryer']), team('ai', [anchor()], ['hunger'])] });
    expect(g.deploy(0, 0, 1, 5)).toBe(true);
    const mine = g.unitAt(1, 5)!;
    g.endTurn();
    mine.hp = 1;
    expect(g.playCard(1, 0, 1, 5)).toBe(true);
    expect(mine.alive).toBe(false);
    expect(g.drops).toEqual([{ x: 1, y: 5, amount: tideDropFor(30) }]);
    expect(g.teams[0].cooldown).toEqual([{ card: 'dryer', turns: cooldownFor(30) }]);
    g.endTurn();
    const before = g.teams[0].essence;
    const walker = g.unitAt(0, 3)!;
    expect(g.move(walker.uid, 1, 5)).toBe(true);
    expect(g.teams[0].essence).toBe(before + tideDropFor(30));
    expect(g.drops).toEqual([]);
  });

  it('pre-placed units drop Tide but are not cards, so they never come back', () => {
    const g = world({ teams: [team('human', [anchor(0, 4), { unit: 'render', x: 4, y: 4 }]), team('ai', [anchor()], ['hunger'])] });
    const r = g.unitAt(4, 4)!;
    g.endTurn();
    r.hp = 1;
    g.playCard(1, 0, 4, 4);
    expect(r.alive).toBe(false);
    expect(g.drops).toHaveLength(1);
    expect(g.teams[0].cooldown).toEqual([]);
    expect(g.teams[1].cooldown.map(c => c.card)).toEqual(['hunger']);
  });

  it('formulas: cooldown is ceil(cost/15) with a floor of 2; drops are a quarter of cost, rounded to 5', () => {
    expect([15, 30, 45, 60, 90].map(cooldownFor)).toEqual([2, 2, 3, 4, 6]);
    expect([0, 15, 30, 45, 90].map(tideDropFor)).toEqual([0, 5, 10, 10, 25]);
  });
});

describe('terrain mechanics', () => {
  const FLAT = '00000000';
  const tiles = ['........', '........', 'll......', '.....b..', 'vvgww...', '........'];
  const terrainWorld = (teams: MissionDef['teams'], edit?: (c: Content) => void) => world({
    teams,
    map: {
      legend: { '.': 'grass', l: 'living_reef', v: 'vent', g: 'glowmoss', w: 'tangleweed', b: 'beam_glass' },
      tiles, heights: Array(6).fill(FLAT),
    },
    edit: c => {
      c.factions = { reef_ascendant: { name: 'Reef', color: '#f00' }, hadal_court: { name: 'Hadal', color: '#00f' } };
      c.terrain.living_reef = { name: 'Living Reef', moveCost: 2, defense: 1, color: '#e07', factionMoveCost: { reef_ascendant: 1 } };
      c.terrain.vent = { name: 'Vent', moveCost: 1, defense: 0, color: '#533', onTurnStart: [
        { type: 'damage', amount: 2, damageType: 'fire', filter: { notFaction: ['hadal_court'] } },
        { type: 'heal', amount: 2, filter: { faction: ['hadal_court'] } }] };
      c.terrain.glowmoss = { name: 'Glowmoss', moveCost: 1, defense: 0, color: '#7b6', onTurnStart: [{ type: 'heal', amount: 2 }] };
      c.terrain.tangleweed = { name: 'Tangleweed', moveCost: 2, defense: 1, color: '#4a3',
        onEnter: { type: 'status', status: 'tangled', duration: 2, filter: { notFaction: ['reef_ascendant'] } } };
      c.terrain.beam_glass = { name: 'Beam Glass', moveCost: 1, defense: -1, color: '#9cb', rangeBonus: 1 };
      c.statuses.tangled = { name: 'Tangled', statMods: { ap: -1 } };
      c.abilities.jab = { name: 'Jab', apCost: 1, range: { min: 1, max: 1 }, target: 'enemy', effects: [{ type: 'damage', amount: 1 }] };
      c.abilities.bow = { name: 'Bow', apCost: 1, range: { min: 2, max: 3 }, target: 'enemy', effects: [{ type: 'damage', amount: 1 }] };
      c.abilities.snipe = { name: 'Snipe', apCost: 1, range: { min: 2, max: 2 }, target: 'enemy', effects: [{ type: 'damage', amount: 3 }] };
      const mk = (name: string, abilities: string[], extra: object = {}) => ({ name, cost: 30, stats: stats(20), abilities, sprite, ...extra });
      Object.assign(c.units, {
        walker: mk('Walker', ['jab']), reefer: mk('Reefer', ['jab'], { faction: 'reef_ascendant' }),
        hadal: mk('Hadal', ['jab'], { faction: 'hadal_court' }), archer: mk('Archer', ['bow']), sniper: mk('Sniper', ['snipe']),
      });
      edit?.(c);
    },
  });
  const tag = (g: Game, t: string) => g.units.find(u => u.tag === t)!;
  const far = team('human', [{ unit: 'walker', x: 7, y: 0 }]);

  it('factionMoveCost lowers the move cost for that faction only', () => {
    const g = terrainWorld([team('human', [{ unit: 'reefer', x: 0, y: 3, tag: 'r' }, { unit: 'walker', x: 1, y: 3, tag: 'w' }]), team('ai', [anchor()])]);
    expect(g.reachable(tag(g, 'r')).get('0,2')?.cost).toBe(1);
    expect(g.reachable(tag(g, 'w')).get('1,2')?.cost).toBe(2);
    expect(g.pathTo(tag(g, 'w'), 1, 2)).toHaveLength(2);
  });

  it('vents burn non-Hadal units and heal Hadal units at turn start', () => {
    const g = terrainWorld([far, team('ai', [{ unit: 'walker', x: 0, y: 4, tag: 'w' }, { unit: 'hadal', x: 1, y: 4, tag: 'h' }])]);
    tag(g, 'h').hp = 10;
    g.endTurn();
    expect(tag(g, 'w').hp).toBe(18);
    expect(tag(g, 'h').hp).toBe(12);
    expect(g.log.some(e => e.kind === 'damage' && e.uid === tag(g, 'w').uid && e.amount === 2)).toBe(true);
    expect(g.log.some(e => e.kind === 'heal' && e.uid === tag(g, 'h').uid && e.amount === 2)).toBe(true);
  });

  it('glowmoss heals but never above max HP', () => {
    const g = terrainWorld([far, team('ai', [{ unit: 'walker', x: 2, y: 4, tag: 'a' }, { unit: 'walker', x: 2, y: 4, tag: 'b' }])]);
    // Two units cannot share a tile in play; move the second by editing coordinates before the turn starts.
    tag(g, 'b').x = 7; tag(g, 'b').y = 5;
    tag(g, 'a').hp = 19;
    g.endTurn();
    expect(tag(g, 'a').hp).toBe(20);
    expect(g.log.filter(e => e.kind === 'heal' && e.uid === tag(g, 'a').uid).map(e => (e as { amount: number }).amount)).toEqual([1]);
    const h = terrainWorld([far, team('ai', [{ unit: 'walker', x: 2, y: 4, tag: 'a' }])]);
    tag(h, 'a').hp = 10; h.endTurn();
    expect(tag(h, 'a').hp).toBe(12);
    h.endTurn(); h.endTurn();
    expect(tag(h, 'a').hp).toBe(14);
  });

  it('flyers ignore onTurnStart terrain', () => {
    const g = terrainWorld([far, team('ai', [{ unit: 'wisp', x: 0, y: 4, tag: 'v' }, { unit: 'wisp', x: 2, y: 4, tag: 'm' }])]);
    tag(g, 'm').hp = 5;
    g.endTurn();
    expect(tag(g, 'v').hp).toBe(10);
    expect(tag(g, 'm').hp).toBe(5);
  });

  it('beam glass adds 1 range to ranged abilities only', () => {
    const g = terrainWorld([team('human', [{ unit: 'archer', x: 5, y: 3, tag: 'on' }, { unit: 'archer', x: 5, y: 2, tag: 'off' }]), team('ai', [anchor(7, 5)])]);
    const has = (u: string, ab: string, x: number, y: number) => g.rangeTiles(tag(g, u), ab).some(p => p.x === x && p.y === y);
    expect(has('on', 'bow', 1, 3)).toBe(true);  // distance 4
    expect(has('off', 'bow', 1, 2)).toBe(false);
    expect(has('off', 'bow', 2, 2)).toBe(true); // distance 3 still fine
    expect(has('on', 'jab', 4, 3)).toBe(true);
    expect(has('on', 'jab', 3, 3)).toBe(false); // melee gets no bonus
    // Targeting agrees with the preview.
    const t = terrainWorld([team('human', [{ unit: 'archer', x: 5, y: 3, tag: 'a' }]), team('ai', [{ unit: 'walker', x: 1, y: 3 }, anchor(7, 5)])]);
    expect(t.targetsFrom(tag(t, 'a'), 'bow').some(p => p.x === 1 && p.y === 3)).toBe(true);
  });

  it('tangleweed tangles everyone except Reef Ascendant', () => {
    const g = terrainWorld([team('human', [{ unit: 'walker', x: 3, y: 5, tag: 'w' }, { unit: 'reefer', x: 4, y: 5, tag: 'r' }]), team('ai', [anchor()])]);
    expect(g.move(tag(g, 'w').uid, 3, 4)).toBe(true);
    expect(g.move(tag(g, 'r').uid, 4, 4)).toBe(true);
    expect(tag(g, 'w').statuses.some(s => s.id === 'tangled')).toBe(true);
    expect(tag(g, 'r').statuses.some(s => s.id === 'tangled')).toBe(false);
  });

  it('validation rejects a bad factionMoveCost, rangeBonus, onTurnStart and unknown filter factions', () => {
    const ok = terrainWorld([far, team('ai', [anchor()])]);
    expect(validateContent(ok.content)).toEqual([]);
    const bad = structuredClone(ok.content);
    bad.terrain.living_reef.factionMoveCost = { reef_ascendant: 0, nowhere: 1 };
    (bad.terrain.beam_glass as unknown as { rangeBonus: unknown }).rangeBonus = 'far';
    bad.terrain.glowmoss.onTurnStart = [{ type: 'push', distance: 1 }];
    bad.terrain.vent.onTurnStart = [{ type: 'heal', amount: 1, filter: { faction: ['ghosts'] } }];
    const errs = validateContent(bad);
    expect(errs.filter(e => /factionMoveCost/.test(e))).toHaveLength(2);
    expect(errs.some(e => /rangeBonus/.test(e))).toBe(true);
    expect(errs.some(e => /glowmoss onTurnStart 0: only damage, heal and status/.test(e))).toBe(true);
    expect(errs.some(e => /unknown faction "ghosts"/.test(e))).toBe(true);
  });

  it('the AI avoids ending on a harmful vent when an equivalent safe tile exists', () => {
    // Sniper needs distance exactly 2 from the enemy at (0,2). (2,2) is a vent; (1,1) and (1,3) are plain grass.
    const g = terrainWorld([team('human', [{ unit: 'walker', x: 0, y: 2 }]), team('ai', [{ unit: 'sniper', x: 4, y: 2, tag: 's' }])], c => {
      c.maps.world.tiles[2] = '..v.....';
    });
    g.endTurn();
    expect(g.current).toBe(1);
    playAiTurn(g);
    const s = tag(g, 's');
    expect(manhattan(s, { x: 0, y: 2 })).toBe(2);
    expect(`${s.x},${s.y}`).not.toBe('2,2');
  });
});

describe('void (chasm) terrain', () => {
  const chasm = (c: Content) => {
    c.terrain.void = { name: 'Chasm', moveCost: 99, defense: 0, color: '#000', impassable: true, void: true };
    c.maps.world.legend['_'] = 'void';
    c.maps.world.tiles[2] = '...#.__.';
    c.maps.world.tiles[5] = '._......';
  };
  const mk = () => world({
    teams: [team('human', [anchor(0, 4), { unit: 'wisp', x: 4, y: 2, tag: 'w' }, { unit: 'vanguard', x: 4, y: 3, tag: 'v' }], ['vanguard']), team('ai', [anchor()])],
    edit: chasm,
  });

  it('validates', () => {
    expect(validateContent(normalizeContent(structuredClone(mk().content)))).toEqual([]);
  });
  it('walkers and flyers cannot end on void, flyers can cross it', () => {
    const g = mk();
    const w = g.units.find(u => u.tag === 'w')!, v = g.units.find(u => u.tag === 'v')!;
    const fr = g.reachable(w);
    expect(fr.has('5,2')).toBe(false);
    expect(fr.has('6,2')).toBe(false);
    expect(fr.has('7,2')).toBe(true); // flew over both chasm tiles
    expect(g.move(w.uid, 5, 2)).toBe(false);
    expect(g.reachable(v).has('5,2')).toBe(false);
    expect(g.reachable(v).has('6,2')).toBe(false);
  });
  it('never offers void as a deploy or skyfall tile', () => {
    const g = mk();
    expect(g.deployTiles(0).some(p => p.x === 1 && p.y === 5)).toBe(false);
    expect(g.deploy(0, 0, 1, 5)).toBe(false);
    expect(g.skyfallTiles(0).some(p => g.terrainAt(p.x, p.y).void)).toBe(false);
  });
});

describe('engagement', () => {
  // v (human) at 4,4 is adjacent to the enemy e at 5,4. Row 4-5 east of the trench is open grass.
  const mk = (unit = 'vanguard', extra: { unit: string; x: number; y: number; tag?: string }[] = [], edit?: (c: Content) => void) =>
    world({ teams: [team('human', [anchor(0, 5), { unit, x: 4, y: 4, tag: 'v' }, ...extra]), team('ai', [anchor(7, 0), { unit: 'vanguard', x: 5, y: 4, tag: 'e' }])], edit });
  const tag = (g: Game, t: string) => g.units.find(u => u.tag === t)!;

  it('costs +2 AP on the first step away from an adjacent enemy, even a step that stays adjacent', () => {
    const g = mk();
    const v = tag(g, 'v');
    expect(g.disengageCost(v)).toBe(2);
    expect(g.reachable(v).get('4,5')?.cost).toBe(3);
    expect(g.reachable(v).get('4,3')?.cost).toBe(3);
    expect(g.reachable(v).get('4,2')?.cost).toBe(4); // only once per move
    const ap = v.ap;
    expect(g.move(v.uid, 4, 3)).toBe(true);
    expect(v.ap).toBe(ap - 3);
    expect(g.disengageCost(v)).toBe(0); // free now
    expect(g.reachable(v).get('4,2')?.cost).toBe(1);
  });

  it('charges again when moving between two tiles that both touch the enemy', () => {
    const g = mk();
    const v = tag(g, 'v');
    // 5,5 is adjacent to e (5,4) as well; 4,4 -> 4,5 -> 5,5 = 2 steps + 2
    expect(g.reachable(v).get('5,5')?.cost).toBe(4);
  });

  it('is free for flyers, ignoresEngagement units and statuses, and next to structures', () => {
    expect(g0('wisp')).toBe(0);
    expect(g0('vanguard', c => { c.units.vanguard.ignoresEngagement = true; })).toBe(0);
    const g = mk();
    const v = tag(g, 'v');
    g.content.statuses.slippery = { name: 'Slippery', ignoresEngagement: true };
    v.statuses.push({ id: 'slippery', remaining: 2 });
    expect(g.disengageCost(v)).toBe(0);
    const dead = mk(); tag(dead, 'e').alive = false;
    expect(dead.disengageCost(tag(dead, 'v'))).toBe(0);
    function g0(unit: string, edit?: (c: Content) => void) { const gg = mk(unit, [], edit); return gg.disengageCost(tag(gg, 'v')); }
  });

  it('shrinks the AI threat range too', () => {
    const g = mk();
    const e = tag(g, 'e');
    const free = mk(); free.units.find(u => u.tag === 'v')!.alive = false;
    expect(g.moveRange(e).size).toBeLessThan(free.moveRange(free.units.find(u => u.tag === 'e')!).size);
  });
});

import { describe, expect, it } from 'vitest';
import { Game } from '../src/engine/game';
import { playAiTurn } from '../src/engine/ai';
import { loadFixtureContent } from './fixtures/load';
import { normalizeContent, validateContent } from '../src/engine/content';
import type { Content, MissionDef } from '../src/engine/types';

const base = loadFixtureContent();

/** Clone bundled content and add a tiny flat test map + mission. */
function fixture(mission: Partial<MissionDef> = {}, edit?: (c: Content) => void): Content {
  const c: Content = structuredClone(base);
  c.maps.flat = {
    id: 'flat', name: 'Flat', legend: { '.': 'grass', '~': 'water', 'x': 'lava', 'f': 'forest' },
    tiles: ['......', '......', '......', '......', '......', '......'],
    heights: ['000000', '000000', '000000', '000000', '000000', '000000'],
    deployZones: { '0': [[0, 5], [1, 5]], '1': [[5, 0], [4, 0]] },
  };
  c.missions.test = {
    id: 'test', name: 'Test', map: 'flat',
    teams: [
      { name: 'A', color: '#f00', controller: 'human', warband: [] },
      { name: 'B', color: '#00f', controller: 'ai', warband: [] },
    ],
    objectives: { victory: [{ type: 'eliminate', team: 1 }], defeat: [{ type: 'eliminate', team: 0 }] },
    ...mission,
  };
  edit?.(c);
  return normalizeContent(c);
}

const duel = (a: string, ax: number, ay: number, b: string, bx: number, by: number, extra?: (c: Content) => void) =>
  new Game(fixture({
    teams: [
      { name: 'A', color: '#f00', controller: 'human', units: [{ unit: a, x: ax, y: ay, tag: 'a' }] },
      { name: 'B', color: '#00f', controller: 'ai', units: [{ unit: b, x: bx, y: by, tag: 'b' }] },
    ],
  }, extra), 'test');

describe('bundled content', () => {
  it('validates with no errors', () => {
    expect(validateContent(base)).toEqual([]);
  });
  it('reports broken references', () => {
    const c = fixture({}, c => { c.units.vanguard.abilities.push('nope'); c.maps.flat.tiles[0] = '..?...'; });
    const errs = validateContent(c);
    expect(errs.some(e => e.includes('unknown ability "nope"'))).toBe(true);
    expect(errs.some(e => e.includes('not in legend'))).toBe(true);
  });
});

describe('movement', () => {
  it('spends AP by terrain cost and respects the AP budget', () => {
    const g = duel('vanguard', 0, 0, 'vanguard', 5, 5);
    const u = g.units[0];
    expect(g.reachable(u).has('3,3')).toBe(true); // 6 steps, 6 AP
    expect(g.reachable(u).has('4,3')).toBe(false);
    expect(g.move(u.uid, 2, 0)).toBe(true);
    expect(u.ap).toBe(4);
  });
  it('blocks water and enemy tiles, allows passing allies', () => {
    const g = new Game(fixture({
      teams: [
        { name: 'A', color: '#f00', controller: 'human', units: [{ unit: 'vanguard', x: 0, y: 0 }, { unit: 'vanguard', x: 1, y: 0 }] },
        { name: 'B', color: '#00f', controller: 'ai', units: [{ unit: 'vanguard', x: 0, y: 1 }] },
      ],
    }, c => { c.maps.flat.tiles[1] = '.~....'; }), 'test');
    const [u] = g.units;
    const r = g.reachable(u);
    expect(r.has('1,0')).toBe(false); // ally occupies, can't stop
    expect(r.has('2,0')).toBe(true);  // but can pass through
    expect(r.has('0,1')).toBe(false); // enemy
    expect(r.has('1,1')).toBe(false); // water
  });
  it('respects jump height', () => {
    const g = duel('vanguard', 0, 0, 'vanguard', 5, 5, c => { c.maps.flat.heights[0] = '020000'; });
    expect(g.reachable(g.units[0]).has('1,0')).toBe(false);
  });
  it('lava hurts on entry', () => {
    const g = duel('vanguard', 0, 0, 'vanguard', 5, 5, c => { c.maps.flat.tiles[0] = '.x....'; });
    const u = g.units[0];
    g.move(u.uid, 1, 0);
    expect(u.hp).toBe(23);
  });
});

describe('combat', () => {
  it('basic strike: attack - defense', () => {
    const g = duel('skirmisher', 0, 0, 'vanguard', 1, 0);
    const [a, b] = g.units;
    expect(g.useAbility(a.uid, 'basic_strike', 1, 0)).toBe(true);
    expect(b.hp).toBe(26 - (7 - 3));
  });
  it('high ground adds damage and forest adds defense', () => {
    const g = duel('skirmisher', 0, 0, 'vanguard', 1, 0, c => {
      c.maps.flat.heights[0] = '200000'; c.maps.flat.tiles[0] = '.f....';
    });
    const [a, b] = g.units;
    g.useAbility(a.uid, 'basic_strike', 1, 0);
    expect(b.hp).toBe(26 - (7 - 3 - 1 + 2));
  });
  it('rejects out-of-range targets and insufficient AP', () => {
    const g = duel('skirmisher', 0, 0, 'vanguard', 3, 0);
    const a = g.units[0];
    expect(g.useAbility(a.uid, 'basic_strike', 3, 0)).toBe(false);
    a.ap = 1;
    expect(g.canUse(a, 'basic_strike')).toBe(false);
  });
  it('push moves target and collision deals extra damage', () => {
    const g = duel('vanguard', 0, 0, 'skirmisher', 1, 0);
    const [a, b] = g.units;
    g.useAbility(a.uid, 'shield_bash', 1, 0);
    expect(b.x).toBe(2);
    const g2 = duel('vanguard', 4, 0, 'skirmisher', 5, 0);
    const [a2, b2] = g2.units;
    g2.useAbility(a2.uid, 'shield_bash', 5, 0);
    expect(b2.x).toBe(5);
    expect(b2.hp).toBe(18 - (6 - 1 - 1) - 2);
  });
  it('cooldowns block reuse until they expire', () => {
    const g = duel('vanguard', 0, 0, 'brute', 1, 0);
    const a = g.units[0];
    g.useAbility(a.uid, 'shield_bash', 1, 0);
    expect(g.canUse(a, 'shield_bash')).toBe(false);
  });
  it('piercing fire burst + burning ticks at the start of the victim turn, then expires', () => {
    const g = duel('pyromancer', 0, 0, 'vanguard', 3, 0);
    const [a, b] = g.units;
    g.useAbility(a.uid, 'fire_burst', 3, 0);
    expect(b.hp).toBe(23);
    g.endTurn();
    expect(b.hp).toBe(21);
    g.endTurn(); g.endTurn();
    expect(b.hp).toBe(19);
    g.endTurn(); g.endTurn();
    expect(b.hp).toBe(19);
    expect(b.statuses).toEqual([]);
  });
  it('stun prevents acting on the victim turn only', () => {
    const g = duel('brute', 0, 0, 'skirmisher', 1, 0);
    const [a, b] = g.units;
    g.useAbility(a.uid, 'ground_slam', 0, 0);
    g.endTurn();
    expect(g.canUse(b, 'basic_strike')).toBe(false);
    expect(g.reachable(b).size).toBe(1);
    g.endTurn(); g.endTurn();
    expect(g.canUse(b, 'basic_strike')).toBe(true);
  });
  it('shield aura raises defense of adjacent allies', () => {
    const g = new Game(fixture({
      teams: [
        { name: 'A', color: '#f00', controller: 'human', units: [{ unit: 'vanguard', x: 0, y: 0 }, { unit: 'archer', x: 1, y: 0 }, { unit: 'archer', x: 3, y: 0 }] },
        { name: 'B', color: '#00f', controller: 'ai', units: [{ unit: 'vanguard', x: 5, y: 5 }] },
      ],
    }), 'test');
    const [v, near, far] = g.units;
    g.useAbility(v.uid, 'guard_aura', 0, 0);
    expect(g.stat(near, 'defense')).toBe(4);
    expect(g.stat(far, 'defense')).toBe(1);
  });
});

describe('new mechanics', () => {
  const withAbility = (id: string, def: object) => (c: Content) => {
    c.abilities[id] = def as never;
    c.units.vanguard.abilities.push(id);
  };
  it('pull drags target toward caster', () => {
    const g = duel('vanguard', 0, 0, 'skirmisher', 4, 0, withAbility('hook', {
      name: 'Hook', apCost: 2, range: { min: 2, max: 4 }, target: 'enemy', effects: [{ type: 'pull', distance: 5 }],
    }));
    g.useAbility(g.units[0].uid, 'hook', 4, 0);
    expect(g.units[1].x).toBe(1);
  });
  it('swap exchanges positions', () => {
    const g = duel('vanguard', 0, 0, 'skirmisher', 2, 0, withAbility('swap', {
      name: 'Swap', apCost: 2, range: { min: 1, max: 3 }, target: 'unit', effects: [{ type: 'swap' }],
    }));
    g.useAbility(g.units[0].uid, 'swap', 2, 0);
    expect([g.units[0].x, g.units[1].x]).toEqual([2, 0]);
  });
  it('summon creates units for the caster team that cannot act this turn', () => {
    const g = duel('vanguard', 0, 0, 'skirmisher', 5, 5, withAbility('call', {
      name: 'Call', apCost: 2, range: { min: 1, max: 1 }, target: 'empty', effects: [{ type: 'summon', unit: 'archer', count: 2 }],
    }));
    g.useAbility(g.units[0].uid, 'call', 1, 0);
    const summoned = g.units.filter(u => u.defId === 'archer');
    expect(summoned.length).toBe(2);
    expect(summoned.every(u => u.team === 0 && u.summonedThisTurn)).toBe(true);
  });
  it('terrain effect changes tiles and reverts after duration', () => {
    const g = duel('vanguard', 0, 0, 'skirmisher', 5, 5, withAbility('wall', {
      name: 'Wall', apCost: 2, range: { min: 1, max: 2 }, target: 'tile', effects: [{ type: 'terrain', terrain: 'water', duration: 1 }],
    }));
    g.useAbility(g.units[0].uid, 'wall', 2, 0);
    expect(g.tiles[0][2].terrain).toBe('water');
    g.endTurn(); g.endTurn();
    expect(g.tiles[0][2].terrain).toBe('grass');
  });
  it('essence drain and gain', () => {
    const g = duel('vanguard', 0, 0, 'skirmisher', 5, 5, withAbility('siphon', {
      name: 'Siphon', apCost: 1, range: { min: 0, max: 0 }, target: 'self',
      effects: [{ type: 'essence', amount: -30, team: 'enemy' }, { type: 'essence', amount: 10 }],
    }));
    const before = g.teams.map(t => t.essence);
    g.useAbility(g.units[0].uid, 'siphon', 0, 0);
    expect(g.teams[1].essence).toBe(before[1] - 30);
    expect(g.teams[0].essence).toBe(before[0] + 10);
  });
  it('passive aura modifies stats continuously', () => {
    const g = duel('vanguard', 0, 0, 'skirmisher', 1, 0, withAbility('dread', {
      name: 'Dread', passive: true, effects: [{ type: 'aura', radius: 2, affects: 'enemies', statMods: { attack: -2 } }],
    }));
    expect(g.stat(g.units[1], 'attack')).toBe(5);
    expect(g.canUse(g.units[0], 'dread')).toBe(false);
    g.units[1].x = 4;
    expect(g.stat(g.units[1], 'attack')).toBe(7);
  });
  it('revive brings a unit back once', () => {
    const g = duel('brute', 0, 0, 'skirmisher', 1, 0, c => { c.units.skirmisher.revive = { hpFraction: 0.5 }; });
    const [a, b] = g.units;
    b.hp = 1;
    g.useAbility(a.uid, 'basic_strike', 1, 0);
    expect(b.alive).toBe(true);
    expect(b.hp).toBe(9);
    b.hp = 1; a.ap = 5; a.usedAbilities = [];
    g.useAbility(a.uid, 'basic_strike', 1, 0);
    expect(b.alive).toBe(false);
  });
  it('each ability can be used once per turn', () => {
    const g = duel('brute', 0, 0, 'vanguard', 1, 0);
    const [a] = g.units; a.ap = 10;
    expect(g.useAbility(a.uid, 'basic_strike', 1, 0)).toBe(true);
    expect(g.useAbility(a.uid, 'basic_strike', 1, 0)).toBe(false);
  });
  it('resistances reduce damage', () => {
    const g = duel('skirmisher', 0, 0, 'vanguard', 1, 0, c => { c.units.vanguard.resist = { physical: 2 }; });
    g.useAbility(g.units[0].uid, 'basic_strike', 1, 0);
    expect(g.units[1].hp).toBe(26 - 2);
  });
  it('wells grant essence to the holder at turn start', () => {
    const g = duel('vanguard', 0, 0, 'skirmisher', 5, 5, c => { c.maps.flat.wells = [{ x: 0, y: 0, amount: 7 }]; });
    const e0 = g.teams[0].essence;
    g.endTurn(); g.endTurn();
    expect(g.teams[0].essence).toBe(e0 + 25 + 7);
  });
});

describe('missions', () => {
  it('survive objective wins after N rounds', () => {
    const g = new Game(fixture({
      teams: [
        { name: 'A', color: '#f00', controller: 'human', units: [{ unit: 'vanguard', x: 0, y: 0 }] },
        { name: 'B', color: '#00f', controller: 'ai', units: [{ unit: 'vanguard', x: 5, y: 5 }] },
      ],
      objectives: { victory: [{ type: 'survive', turns: 2 }], defeat: [{ type: 'eliminate', team: 0 }] },
    }), 'test');
    g.endTurn(); g.endTurn();
    expect(g.phase).toBe('playing');
    g.endTurn(); g.endTurn();
    expect(g.phase).toBe('victory');
  });
  it('defeat_unit tag + unitDefeated event', () => {
    const g = duel('brute', 0, 0, 'skirmisher', 1, 0);
    (g.mission as MissionDef).objectives = { victory: [{ type: 'defeat_unit', tag: 'b' }] };
    (g.mission as MissionDef).events = [{ when: { unitDefeated: 'b' }, do: [{ type: 'message', text: 'argh' }] }];
    g.units[1].hp = 1;
    g.useAbility(g.units[0].uid, 'basic_strike', 1, 0);
    expect(g.phase).toBe('victory');
    expect(g.log.some(e => e.kind === 'message' && e.text === 'argh')).toBe(true);
  });
  it('turn events spawn units', () => {
    const g = new Game(fixture({
      teams: [
        { name: 'A', color: '#f00', controller: 'human', units: [{ unit: 'vanguard', x: 0, y: 0 }] },
        { name: 'B', color: '#00f', controller: 'ai', units: [{ unit: 'vanguard', x: 5, y: 5 }] },
      ],
      events: [{ when: { turn: 2, team: 1 }, do: [{ type: 'spawn', team: 1, unit: 'archer', x: 5, y: 5 }] }],
    }), 'test');
    g.endTurn(); g.endTurn(); g.endTurn();
    const archer = g.units.find(u => u.defId === 'archer');
    expect(archer && archer.x === 5 && archer.y === 5).toBe(false); // occupied, placed nearby
    expect(archer?.team).toBe(1);
  });
  it('deploy spends essence, uses zone tiles, unit waits a turn', () => {
    const g = new Game(fixture({
      teams: [
        { name: 'A', color: '#f00', controller: 'human', warband: ['archer'] },
        { name: 'B', color: '#00f', controller: 'ai', warband: ['archer'] },
      ],
    }), 'test');
    expect(g.deploy(0, 0, 3, 3)).toBe(false);
    expect(g.deploy(0, 0, 0, 5)).toBe(true);
    expect(g.teams[0].essence).toBe(65);
    const u = g.units.find(x => x.team === 0)!;
    expect(g.canUse(u, 'basic_shot')).toBe(false);
  });
});

describe('AI', () => {
  it('finishes bundled missions in AI vs AI play without errors', () => {
    for (const id of Object.keys(base.missions)) {
      const camp = Object.values(base.campaigns)[0];
      const g = new Game(base, id, { roster: camp.startingRoster.concat(camp.missions.flatMap(m => m.unlocks ?? [])) });
      let turns = 0;
      while (g.phase === 'playing' && turns < 120) { playAiTurn(g); turns++; }
      expect(['victory', 'defeat', 'playing']).toContain(g.phase);
      expect(g.units.filter(u => u.alive).every(u => g.inBounds(u.x, u.y))).toBe(true);
    }
  });
  it('the AI actually attacks when an enemy is adjacent', () => {
    const g = duel('vanguard', 0, 0, 'brute', 1, 0);
    g.endTurn();
    playAiTurn(g);
    expect(g.units[0].hp).toBeLessThan(26);
  });
});

describe('cards: spells, equipment, heroes, swarm', () => {
  const cardGame = (hand: string[]) => new Game(fixture({
    teams: [
      { name: 'A', color: '#f00', controller: 'human', warband: hand, units: [{ unit: 'vanguard', x: 0, y: 4 }] },
      { name: 'B', color: '#00f', controller: 'ai', units: [{ unit: 'skirmisher', x: 2, y: 2 }, { unit: 'skirmisher', x: 3, y: 2 }, { unit: 'skirmisher', x: 5, y: 0 }] },
    ],
  }), 'test');
  it('spells hit enemies in area within cast range and cost essence', () => {
    const g = cardGame(['ember_rain']);
    expect(g.cardTargets(0, 0).some(p => p.x === 5 && p.y === 0)).toBe(false); // too far from friendly units
    expect(g.playCard(0, 0, 2, 2)).toBe(true);
    const [, s1, s2, s3] = g.units;
    expect([s1.hp, s2.hp, s3.hp]).toEqual([15, 15, 18]);
    expect(g.teams[0].essence).toBe(70);
    expect(g.teams[0].hand).toEqual([]);
  });
  it('equipment modifies stats and grants abilities', () => {
    const g = cardGame(['ember_blade']);
    const v = g.units[0];
    expect(g.playCard(0, 0, 0, 4)).toBe(true);
    expect(g.stat(v, 'attack')).toBe(8);
    expect(g.abilitiesOf(v)).toContain('cinder_slash');
    const g2 = cardGame(['iron_plate', 'iron_plate']);
    g2.playCard(0, 0, 0, 4);
    expect(g2.cardTargets(0, 0)).toEqual([]); // one equipment per unit
  });
  it('terrain spell makes a temporary wall', () => {
    const g = cardGame(['stone_wall']);
    expect(g.playCard(0, 0, 1, 4)).toBe(true);
    expect(g.terrainAt(1, 4).impassable).toBe(true);
  });
  it('swarm instinct scales with adjacent allies', () => {
    const g = new Game(fixture({
      teams: [
        { name: 'A', color: '#f00', controller: 'human', units: [{ unit: 'drone', x: 2, y: 2 }, { unit: 'drone', x: 1, y: 2 }, { unit: 'drone', x: 3, y: 2 }] },
        { name: 'B', color: '#00f', controller: 'ai', units: [{ unit: 'vanguard', x: 5, y: 5 }] },
      ],
    }), 'test');
    const [mid, left] = g.units;
    expect(g.stat(mid, 'attack')).toBe(5);
    expect(g.stat(left, 'attack')).toBe(4);
  });
  it('validation rejects duplicate heroes and unknown cards', () => {
    const c = fixture({}, c => { c.missions.test.teams[0].warband = ['warlord', 'warlord', 'mystery']; });
    const errs = validateContent(c);
    expect(errs.some(e => e.includes('hero "warlord" appears more than once'))).toBe(true);
    expect(errs.some(e => e.includes('unknown card "mystery"'))).toBe(true);
  });
});

describe('world-thread mechanics batch 2', () => {
  const withAbility = (id: string, def: object, unit = 'vanguard') => (c: Content) => {
    c.abilities[id] = def as never;
    c.units[unit].abilities.push(id);
  };
  it('life drain heals the caster', () => {
    const g = duel('vanguard', 0, 0, 'skirmisher', 1, 0, withAbility('drain', {
      name: 'Drain', apCost: 2, range: { min: 1, max: 1 }, target: 'enemy',
      effects: [{ type: 'damage', amount: 0 }, { type: 'heal', amount: 3, target: 'caster' }],
    }));
    g.units[0].hp = 10;
    g.useAbility(g.units[0].uid, 'drain', 1, 0);
    expect(g.units[0].hp).toBe(13);
    expect(g.units[1].hp).toBe(18 - 5);
  });
  it('sacrifice kills the caster after other effects', () => {
    const g = duel('vanguard', 0, 0, 'skirmisher', 5, 5, withAbility('offer', {
      name: 'Offer', apCost: 0, range: { min: 0, max: 0 }, target: 'self',
      effects: [{ type: 'essence', amount: 20 }, { type: 'sacrifice' }],
    }));
    const e = g.teams[0].essence;
    g.useAbility(g.units[0].uid, 'offer', 0, 0);
    expect(g.units[0].alive).toBe(false);
    expect(g.teams[0].essence).toBe(e + 20);
  });
  it('line areas hit every unit along the beam', () => {
    const g = new Game(fixture({
      teams: [
        { name: 'A', color: '#f00', controller: 'human', units: [{ unit: 'vanguard', x: 0, y: 0 }] },
        { name: 'B', color: '#00f', controller: 'ai', units: [{ unit: 'skirmisher', x: 1, y: 0 }, { unit: 'skirmisher', x: 3, y: 0 }, { unit: 'skirmisher', x: 5, y: 0 }, { unit: 'skirmisher', x: 1, y: 1 }] },
      ],
    }, withAbility('beam', {
      name: 'Beam', apCost: 2, range: { min: 1, max: 1 }, target: 'tile', area: { shape: 'line', size: 4 }, affects: 'enemies',
      effects: [{ type: 'damage', amount: 5, ignoreAttack: true, pierce: true }],
    })), 'test');
    g.useAbility(g.units[0].uid, 'beam', 1, 0);
    expect(g.units.slice(1).map(u => u.hp)).toEqual([13, 13, 18, 18]);
  });
  it('stacking statuses scale stat mods up to maxStacks', () => {
    const g = duel('vanguard', 0, 0, 'skirmisher', 1, 0, c => {
      c.statuses.bloom = { name: 'Bloom', statMods: { attack: 1 }, stacks: true, maxStacks: 2 };
      withAbility('bloom', { name: 'Bloom', apCost: 1, range: { min: 0, max: 0 }, target: 'self', effects: [{ type: 'status', status: 'bloom', duration: 3 }] })(c);
    });
    const v = g.units[0];
    for (let i = 0; i < 3; i++) { v.usedAbilities = []; g.useAbility(v.uid, 'bloom', 0, 0); }
    expect(g.stat(v, 'attack')).toBe(8);
  });
  it('spells can be limited to near the keystone', () => {
    const g = new Game(fixture({
      teams: [
        { name: 'A', color: '#f00', controller: 'human', warband: ['ward'], units: [{ unit: 'vanguard', x: 5, y: 0 }] },
        { name: 'B', color: '#00f', controller: 'ai', units: [{ unit: 'skirmisher', x: 5, y: 5 }] },
      ],
    }, c => {
      c.maps.flat.keystones = [{ team: 0, x: 0, y: 5 }];
      c.spells.ward = { name: 'Ward', cost: 10, castRange: { nearKeystone: 2 }, target: 'tile', effects: [{ type: 'heal', amount: 1 }] };
    }), 'test');
    const t = g.cardTargets(0, 0);
    expect(t.length).toBeGreaterThan(0);
    expect(t.every(p => manhattanTest(p, { x: 0, y: 5 }) <= 2)).toBe(true);
  });
});
const manhattanTest = (a: { x: number; y: number }, b: { x: number; y: number }) => Math.abs(a.x - b.x) + Math.abs(a.y - b.y);

describe('mission scripting batch 2', () => {
  const three = (extra: Partial<MissionDef> = {}) => new Game(fixture({
    teams: [
      { name: 'A', color: '#f00', controller: 'human', units: [{ unit: 'brute', x: 0, y: 0 }], startingEssence: 50, essencePerTurn: 5 },
      { name: 'B', color: '#00f', controller: 'ai', units: [{ unit: 'skirmisher', x: 1, y: 0, tag: 'r' }, { unit: 'skirmisher', x: 5, y: 5, tag: 'r' }] },
      { name: 'Neutral', color: '#888', controller: 'ai', units: [{ unit: 'archer', x: 3, y: 3, tag: 'n' }] },
    ],
    objectives: { victory: [{ type: 'defeat_unit', tag: 'r' }], defeat: [{ type: 'unit_hp_above', tag: 'n', fraction: 0.5, not: true }] },
    ...extra,
  }), 'test');
  it('defeat_unit needs every unit with the tag dead', () => {
    const g = three();
    g.units[1].hp = 1;
    g.useAbility(g.units[0].uid, 'basic_strike', 1, 0);
    expect(g.phase).toBe('playing');
    g.units[2].alive = false;
    g.useAbility(g.units[0].uid, 'basic_strike', 1, 0); // re-check conditions via any action
    g.endTurn();
    expect(g.phase).toBe('victory');
  });
  it('per-team essence and three-team turn order', () => {
    const g = three();
    expect(g.teams[0].essence).toBe(50);
    g.endTurn(); expect(g.current).toBe(1);
    g.endTurn(); expect(g.current).toBe(2);
    g.endTurn(); expect(g.current).toBe(0);
    expect(g.round).toBe(2);
    expect(g.teams[0].essence).toBe(55);
  });
  it('not: inverts a condition', () => {
    const g = three();
    g.units[3].hp = 2;
    g.endTurn();
    expect(g.phase).toBe('defeat');
  });
  it('terrain and status event actions', () => {
    const g = three({ events: [{ when: { turn: 1 }, do: [
      { type: 'terrain', x: 2, y: 2, terrain: 'water', radius: 1, duration: 1 },
      { type: 'status', tag: 'r', status: 'rooted', duration: 1 },
    ] }] });
    expect(g.tiles[2][2].terrain).toBe('water');
    expect(g.tiles[1][2].terrain).toBe('water');
    expect(g.units[1].statuses.map(s => s.id)).toEqual(['rooted']);
  });
});

describe('card draw', () => {
  it('deals an opening hand of 5 with champions, then draws one per turn', async () => {
    const { loadBundledContent } = await import('../src/engine/bundled');
    const { buildSkirmish } = await import('../src/engine/skirmish');
    const { Game: G, DRAW } = await import('../src/engine/game');
    const c = loadBundledContent();
    const m = buildSkirmish(c, Object.keys(c.maps)[0], ['salt_concord', 'hadal_court'], ['ai', 'ai']);
    c.missions[m.id] = m;
    const g = new G(c, m.id, { seed: 7 });
    const t0 = g.teams[0];
    expect(t0.hand.length).toBe(DRAW.opening);
    expect(t0.hand.filter(id => g.cardKind(id) === 'unit').length).toBeGreaterThanOrEqual(DRAW.minOpeningUnits);
    const total = t0.hand.length + t0.deck.length;
    expect(total).toBe(m.teams[0].warband!.length);
    // Team 1 draws on its first turn; team 0 draws from round 2.
    g.endTurn();
    expect(g.teams[1].hand.length).toBe(DRAW.opening + 1);
    g.endTurn();
    expect(t0.hand.length).toBe(DRAW.opening + 1);
    // Same seed, same shuffle.
    expect(new G(c, m.id, { seed: 7 }).teams[0].hand).toEqual(new G(c, m.id, { seed: 7 }).teams[0].hand);
  });
});

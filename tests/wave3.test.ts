// Wave 3 mechanics: Venom (onAct / shedsWhenIdle / ifTargetStacks), Shed + husks, Coiled reaction strikes,
// Shell / Eviction / Rehouse / moveOut / shell repair / filter.shelled, and Long-body tails.
import { describe, expect, it } from 'vitest';
import { Game } from '../src/engine/game';
import { aiStep, playAiTurn } from '../src/engine/ai';
import { loadFixtureContent } from './fixtures/load';
import { isCardUnit, nonCardUnits, normalizeContent, validateContent } from '../src/engine/content';
import { factionDeck, playableFactions } from '../src/engine/skirmish';
import { allRelics } from '../src/engine/collection';
import type { Content, GameEvent, MapDef, MissionDef, Unit } from '../src/engine/types';

const base = loadFixtureContent();
const stats = (hp: number, ap = 6, attack = 4, defense = 0, jump = 1) => ({ hp, ap, attack, defense, jump });
const sprite = { shape: 'circle', glyph: 'X' };
const melee = (effects: object[], extra: object = {}) => ({ name: 'A', apCost: 2, range: { min: 1, max: 1 }, target: 'enemy', effects, ...extra });

function wave3Content(): Content {
  const c: Content = structuredClone(base);
  c.factions = { slough: { name: 'Slough', color: '#b5c934' }, hermitage: { name: 'Hermitage', color: '#7b4f8f' } };
  c.terrain.salt_flat = { name: 'Salt Flat', moveCost: 1, defense: 0, color: '#ddd' };
  c.terrain.wreck_t = { name: 'Wreck', moveCost: 1, defense: 0, color: '#654', shellSource: 'crab' };
  c.statuses.sl_venom = { name: 'Venom', stacks: true, maxStacks: 5, shedsWhenIdle: true,
    onAct: [{ type: 'damage', amount: 1, damageType: 'venom', ignoreAttack: true, pierce: true }] };
  Object.assign(c.abilities, {
    poke: melee([{ type: 'damage', amount: 0, damageType: 'physical' }], { apCost: 1 }),
    bite: melee([{ type: 'damage', amount: 0, damageType: 'physical' }, { type: 'status', status: 'sl_venom', duration: 99 }, { type: 'status', status: 'sl_venom', duration: 99 }]),
    envenom: melee([{ type: 'damage', amount: 5, ignoreAttack: true, pierce: true, ifTargetStacks: { status: 'sl_venom', min: 2 } }]),
    snap: melee([{ type: 'damage', amount: 3, ignoreAttack: true }, { type: 'status', status: 'rooted', duration: 1 }]),
    nip: melee([{ type: 'damage', amount: 1, ignoreAttack: true }]),
    pierce_hit: melee([{ type: 'damage', amount: 2, ignoreAttack: true, pierce: true }]),
    venom_hit: melee([{ type: 'damage', amount: 2, ignoreAttack: true, damageType: 'venom' }]),
    crack: melee([{ type: 'damage', amount: 4, ignoreAttack: true, pierce: true, filter: { shelled: true } }]),
    slam: { name: 'Slam', apCost: 2, range: { min: 1, max: 2 }, target: 'tile', area: { shape: 'radius', size: 1 }, affects: 'enemies',
      effects: [{ type: 'damage', amount: 3, ignoreAttack: true, pierce: true }] },
    rehouse: { name: 'Rehouse', apCost: 2, range: { min: 1, max: 1 }, target: 'tile', effects: [{ type: 'rehouse' }] },
    move_out: { name: 'Move Out', apCost: 1, range: { min: 1, max: 1 }, target: 'empty', effects: [{ type: 'moveOut' }] },
    patch: { name: 'Patch', apCost: 1, range: { min: 0, max: 1 }, target: 'ally', effects: [{ type: 'shell', amount: 3 }] },
    reshed_ab: { name: 'Reshed', apCost: 1, range: { min: 0, max: 0 }, target: 'self', effects: [{ type: 'reshed' }] },
  });
  const unit = (name: string, hp: number, abilities: string[], extra: object = {}) => ({ name, cost: 40, stats: stats(hp), abilities, sprite, ...extra });
  Object.assign(c.units, {
    snake: unit('Snake', 20, ['poke', 'bite', 'envenom', 'reshed_ab'], { faction: 'slough', shed: { husk: 'husk' }, resist: { venom: 0 } }),
    tough_snake: unit('Tough Snake', 20, ['poke'], { faction: 'slough', resist: { venom: 1 } }),
    husk: { name: 'Husk', cost: 0, structure: true, decoy: true, token: true, stats: stats(1, 0, 0), abilities: [], sprite, faction: 'slough' },
    coiler: unit('Coiler', 20, ['poke'], { faction: 'slough', coiled: { ability: 'snap' } }),
    nipper: unit('Nipper', 20, ['poke'], { faction: 'slough', coiled: { ability: 'nip' } }),
    crab: unit('Crab', 20, ['poke', 'move_out', 'patch'], { faction: 'hermitage', shell: { hp: 8, evicted: 'crab_bare', leaves: 'crab_empty' } }),
    crab_bare: { ...unit('Bare Crab', 12, ['poke', 'rehouse']), faction: 'hermitage', cost: 0, token: true },
    crab_empty: { name: 'Empty Shell', cost: 0, structure: true, token: true, emptyShell: { becomes: 'crab' }, stats: stats(8, 0, 0), abilities: [], sprite, faction: 'hermitage' },
    eel: unit('Eel', 20, ['poke'], { faction: 'slough', tail: { segment: 'eel_seg', length: 2 } }),
    eel_seg: { name: 'Eel Tail', cost: 0, structure: true, token: true, stats: stats(99, 0, 0), abilities: [], sprite },
    hitter: unit('Hitter', 30, ['poke', 'pierce_hit', 'venom_hit', 'crack', 'slam', 'bite']),
    dummy: unit('Dummy', 30, ['poke']),
  });
  return c;
}

function world(opts: { teams: MissionDef['teams']; map?: Partial<MapDef>; edit?: (c: Content) => void }): Game {
  const c = wave3Content();
  c.maps.w3 = {
    id: 'w3', name: 'W3', legend: { '.': 'grass', w: 'wreck_t', '#': 'wall' },
    tiles: ['........', '........', '........', '........', '........', '........'],
    heights: ['00000000', '00000000', '00000000', '00000000', '00000000', '00000000'],
    deployZones: { '0': [[0, 5], [1, 5]], '1': [[7, 0], [7, 1]] }, ...opts.map,
  };
  c.missions.w3 = { id: 'w3', name: 'W3', map: 'w3', startingEssence: 100, teams: opts.teams,
    objectives: { victory: [{ type: 'eliminate', team: 1 }], defeat: [{ type: 'eliminate', team: 0 }] } };
  opts.edit?.(c);
  return new Game(normalizeContent(c), 'w3', { seed: 1 });
}
type P = { unit: string; x: number; y: number; tag?: string };
const team = (controller: 'human' | 'ai', units: P[], warband: string[] = []) =>
  ({ name: controller, color: controller === 'human' ? '#f00' : '#00f', controller, units, warband });
const anchor = (x = 7, y = 5): P => ({ unit: 'dummy', x, y });
const at = (g: Game, x: number, y: number) => g.unitAt(x, y)!;
const byTag = (g: Game, tag: string) => g.units.find(u => u.tag === tag)!;
const cycle = (g: Game) => { g.endTurn(); g.endTurn(); };
const events = (g: Game) => { const out: GameEvent[] = []; g.on(e => out.push(e)); return out; };
/** Walk `u` to the cheapest free tile orthogonally next to `t`. */
function nextTo(g: Game, u: Unit, t: Unit) {
  const reach = g.reachable(u);
  const tile = [[1, 0], [-1, 0], [0, 1], [0, -1]].map(([dx, dy]) => ({ x: t.x + dx, y: t.y + dy }))
    .filter(p => reach.has(`${p.x},${p.y}`)).sort((a, b) => reach.get(`${a.x},${a.y}`)!.cost - reach.get(`${b.x},${b.y}`)!.cost)[0];
  expect(g.move(u.uid, tile.x, tile.y)).toBe(true);
}
const stacks = (u: Unit, id = 'sl_venom') => { const s = u.statuses.find(x => x.id === id); return s ? (s.stacks ?? 1) : 0; };

describe('content validation for wave 3 fields', () => {
  it('accepts the test content', () => {
    const c = wave3Content();
    expect(validateContent(normalizeContent(c))).toEqual([]);
  });
  it('reports every bad cross-reference', () => {
    const c = wave3Content();
    c.units.snake.shed = { husk: 'nope' };
    c.units.coiler.coiled = { ability: 'nope' };
    c.units.crab.shell = { hp: 8, evicted: 'nope', leaves: 'dummy' };
    c.units.crab_empty.emptyShell = { becomes: 'dummy' };
    c.units.eel.tail = { segment: 'nope', length: 5 };
    c.terrain.wreck_t.shellSource = 'dummy';
    c.statuses.sl_venom.onAct = [{ type: 'heal', amount: 1 }];
    c.abilities.envenom.effects[0].ifTargetStacks = { status: 'nope', min: 1 };
    c.abilities.crack.effects[0] = { type: 'damage', amount: 1, filter: { shelled: 'yes' as unknown as boolean } };
    c.spells.bad = { name: 'Bad', cost: 1, target: 'tile', effects: [{ type: 'rehouse' }] };
    const errs = validateContent(normalizeContent(c)).join('\n');
    for (const bit of ['shed.husk names unknown unit "nope"', 'coiled.ability names unknown ability', 'shell.evicted names unknown unit "nope"',
      'shell.leaves "dummy" must be an emptyShell unit', 'emptyShell.becomes "dummy" must be a unit with a shell', 'tail.segment names unknown unit',
      'tail.length must be 1, 2 or 3', 'shellSource "dummy" must be a unit with a shell', 'onAct 0: only damage', 'ifTargetStacks names unknown status',
      'filter.shelled must be true or false', '"rehouse" needs a caster unit']) expect(errs).toContain(bit);
  });
  it('rejects tokens in warbands and keeps them out of decks, factions and the collection', () => {
    const c = wave3Content();
    c.campaigns = { camp: { name: 'C', startingRoster: ['crab', 'crab_bare'], missions: [] } };
    expect(validateContent(normalizeContent(c)).join('\n')).toContain('"crab_bare" is a token unit');
    const tokens = nonCardUnits(c);
    for (const id of ['husk', 'crab_bare', 'crab_empty', 'eel_seg']) expect(tokens.has(id)).toBe(true);
    expect(isCardUnit(c, 'crab')).toBe(true);
    expect(isCardUnit(c, 'crab_bare')).toBe(false);
    const deck = factionDeck(c, 'hermitage');
    expect(deck).toContain('crab');
    expect(deck).not.toContain('crab_bare');
    expect(deck).not.toContain('crab_empty');
    expect(factionDeck(c, 'slough')).not.toContain('husk');
    const relics = allRelics(c);
    expect(relics).not.toContain('crab_bare');
    expect(relics).not.toContain('husk');
    expect(playableFactions(c)).toContain('hermitage');
  });
});

describe('venom', () => {
  it('stacks, bites once per walk and once per ability use, resist and pierce applied', () => {
    const g = world({ teams: [team('human', [{ unit: 'snake', x: 1, y: 1, tag: 's' }, anchor(0, 5)]), team('ai', [{ unit: 'dummy', x: 2, y: 1, tag: 'd' }, anchor()])] });
    const s = byTag(g, 's'), d = byTag(g, 'd');
    expect(g.useAbility(s.uid, 'bite', 2, 1)).toBe(true);
    expect(stacks(d)).toBe(2);
    g.endTurn();
    const hp = d.hp;
    expect(g.move(d.uid, 5, 1)).toBe(true); // a 3-tile walk is one bite of 2
    expect(d.hp).toBe(hp - 2);
    expect(g.useAbility(d.uid, 'poke', 6, 1)).toBe(false); // nothing there; no bite for a refused action
    expect(d.hp).toBe(hp - 2);
  });

  it('venom resist reduces the bite', () => {
    const g = world({ teams: [team('human', [{ unit: 'hitter', x: 1, y: 1, tag: 'h' }, anchor(0, 5)]), team('ai', [{ unit: 'tough_snake', x: 2, y: 1, tag: 't' }, anchor()])] });
    g.useAbility(byTag(g, 'h').uid, 'bite', 2, 1);
    g.endTurn();
    const t = byTag(g, 't'), hp = t.hp;
    g.move(t.uid, 2, 3);
    expect(t.hp).toBe(hp - 1); // 2 stacks x 1, minus resist 1
  });

  it('loses a stack at the end of an idle turn, not after an active one', () => {
    const g = world({ teams: [team('human', [{ unit: 'snake', x: 1, y: 1, tag: 's' }, anchor(0, 5)]), team('ai', [{ unit: 'dummy', x: 2, y: 1, tag: 'd' }, anchor()])] });
    const s = byTag(g, 's'), d = byTag(g, 'd');
    g.useAbility(s.uid, 'bite', 2, 1);
    g.endTurn();
    g.move(d.uid, 2, 3); // active turn: keeps both stacks
    g.endTurn();
    expect(stacks(d)).toBe(2);
    g.endTurn(); g.endTurn(); // idle
    expect(stacks(d)).toBe(1);
    g.endTurn(); g.endTurn(); // idle again: gone
    expect(d.statuses.some(x => x.id === 'sl_venom')).toBe(false);
  });

  it('ifTargetStacks only fires with enough stacks at use start', () => {
    const g = world({ teams: [team('human', [{ unit: 'snake', x: 1, y: 1, tag: 's' }, anchor(0, 5)]), team('ai', [{ unit: 'dummy', x: 2, y: 1, tag: 'd' }, anchor()])] });
    const s = byTag(g, 's'), d = byTag(g, 'd');
    g.useAbility(s.uid, 'envenom', 2, 1);
    expect(d.hp).toBe(30); // no stacks yet
    cycle(g);
    g.useAbility(s.uid, 'bite', 2, 1);
    const hp = d.hp;
    g.useAbility(s.uid, 'envenom', 2, 1);
    expect(d.hp).toBe(hp - 5);
  });

  it('structures are immune', () => {
    const g = world({ teams: [team('human', [{ unit: 'snake', x: 1, y: 1, tag: 's' }, anchor(0, 5)]), team('ai', [{ unit: 'crab_empty', x: 2, y: 1, tag: 'e' }, anchor()])] });
    g.useAbility(byTag(g, 's').uid, 'bite', 2, 1);
    expect(byTag(g, 'e').statuses).toEqual([]);
  });

  it('the AI does not walk a unit into a Venom death when it can stand still', () => {
    const g = world({ teams: [team('human', [{ unit: 'dummy', x: 0, y: 5, tag: 'p' }]), team('ai', [{ unit: 'dummy', x: 7, y: 0, tag: 'v' }, anchor(7, 3)])] });
    const v = byTag(g, 'v');
    v.statuses.push({ id: 'sl_venom', remaining: 99, stacks: 3 });
    v.hp = 3;
    g.endTurn();
    playAiTurn(g);
    expect(v.alive).toBe(true);
    expect([v.x, v.y]).toEqual([7, 0]);
  });
});

describe('shed', () => {
  it('drops statuses, leaves a husk and slides away from the nearest enemy, once', () => {
    const g = world({ teams: [team('human', [{ unit: 'hitter', x: 3, y: 2, tag: 'h' }, anchor(0, 5)]), team('ai', [{ unit: 'snake', x: 4, y: 2, tag: 's' }, anchor()])] });
    const h = byTag(g, 'h'), s = byTag(g, 's');
    const ev = events(g);
    s.statuses.push({ id: 'rooted', remaining: 2 });
    s.hp = 11;
    g.useAbility(h.uid, 'pierce_hit', 4, 2); // 11 -> 9, below half of 20
    expect(s.hp).toBe(9);
    expect(s.statuses).toEqual([]);
    const husk = at(g, 4, 2);
    expect(husk.defId).toBe('husk');
    expect(husk.team).toBe(1);
    expect(s.x === 4 && s.y === 2).toBe(false);
    expect(Math.abs(s.x - 4) + Math.abs(s.y - 2)).toBeLessThanOrEqual(2);
    expect(Math.abs(s.x - h.x) + Math.abs(s.y - h.y)).toBe(3); // as far from the hitter as 2 steps allow
    expect(ev.some(e => e.kind === 'shed' && e.uid === s.uid && e.husk === husk.uid)).toBe(true);
    // Once per battle...
    cycle(g);
    const pos = { x: s.x, y: s.y }, hp = s.hp;
    nextTo(g, h, s);
    expect(g.useAbility(h.uid, 'pierce_hit', s.x, s.y)).toBe(true);
    expect(s.hp).toBe(hp - 2);
    expect({ x: s.x, y: s.y }).toEqual(pos);
    // ...unless reshed.
    g.endTurn();
    g.useAbility(s.uid, 'reshed_ab', s.x, s.y);
    expect(s.shedUsed).toBe(false);
  });

  it('husks do not count for elimination and vanish at the start of the owner\'s 3rd turn', () => {
    const g = world({ teams: [team('human', [{ unit: 'hitter', x: 3, y: 2, tag: 'h' }, anchor(0, 5)]), team('ai', [{ unit: 'snake', x: 4, y: 2, tag: 's' }])] });
    const s = byTag(g, 's');
    s.hp = 11;
    g.useAbility(byTag(g, 'h').uid, 'pierce_hit', 4, 2);
    const husk = at(g, 4, 2);
    g.endTurn(); expect(husk.alive).toBe(true); // owner's 1st turn
    cycle(g); expect(husk.alive).toBe(true); // 2nd
    cycle(g); expect(husk.alive).toBe(false); // 3rd
    // Kill the snake: the side is eliminated even with a husk standing.
    const g2 = world({ teams: [team('human', [{ unit: 'hitter', x: 3, y: 2, tag: 'h' }, anchor(0, 5)]), team('ai', [{ unit: 'snake', x: 4, y: 2, tag: 's' }])] });
    const s2 = byTag(g2, 's');
    s2.hp = 11;
    g2.useAbility(byTag(g2, 'h').uid, 'pierce_hit', 4, 2);
    s2.hp = 1;
    cycle(g2);
    const h2 = byTag(g2, 'h');
    nextTo(g2, h2, s2);
    g2.useAbility(h2.uid, 'pierce_hit', s2.x, s2.y);
    expect(s2.alive).toBe(false);
    expect(g2.phase).toBe('victory');
  });

  it('the AI prefers a real target over a husk', () => {
    const g = world({ teams: [team('human', [{ unit: 'husk', x: 3, y: 2 }, { unit: 'dummy', x: 5, y: 2, tag: 'real' }, anchor(0, 5)]), team('ai', [{ unit: 'hitter', x: 4, y: 2, tag: 'h' }])] });
    g.endTurn();
    aiStep(g);
    expect(byTag(g, 'real').hp).toBeLessThan(30);
    expect(at(g, 3, 2)?.defId).toBe('husk');
  });
});

describe('coiled', () => {
  it('strikes the first enemy that walks next to it, which stops there; once per enemy turn', () => {
    const g = world({ teams: [team('human', [{ unit: 'coiler', x: 4, y: 2, tag: 'c' }, anchor(0, 5)]),
      team('ai', [{ unit: 'dummy', x: 7, y: 1, tag: 'a' }, { unit: 'dummy', x: 7, y: 3, tag: 'b' }, anchor(7, 5)])] });
    const ev = events(g);
    g.endTurn(); // coiler used no ability: coiled
    const c = byTag(g, 'c'), a = byTag(g, 'a'), b = byTag(g, 'b');
    expect(c.coiled).toBe(true);
    const ap = a.ap;
    expect(g.move(a.uid, 2, 1)).toBe(true); // path along row 1 passes (4,1), adjacent to the coiler
    expect(ev.some(e => e.kind === 'react' && e.uid === c.uid && e.target === a.uid)).toBe(true);
    expect(a.hp).toBe(27);
    expect(g.hasFlag(a, 'preventsMove')).toBe(true);
    expect([a.x, a.y]).toEqual([4, 1]);
    expect(a.ap).toBe(ap - 3); // only the tiles walked are paid for
    g.move(b.uid, 4, 3); // second walker this turn: no strike
    expect(b.hp).toBe(30);
  });

  it('a strike that does not stop the walker lets it finish the walk', () => {
    const g = world({ teams: [team('human', [{ unit: 'nipper', x: 4, y: 2, tag: 'c' }, anchor(0, 5)]), team('ai', [{ unit: 'dummy', x: 7, y: 1, tag: 'a' }, anchor(7, 5)])] });
    g.endTurn();
    const a = byTag(g, 'a');
    g.move(a.uid, 2, 1);
    expect(a.hp).toBe(29);
    expect([a.x, a.y]).toEqual([2, 1]);
  });

  it('is not coiled after using an ability, and push movement never triggers it', () => {
    const g = world({ teams: [team('human', [{ unit: 'coiler', x: 4, y: 2, tag: 'c' }, anchor(0, 5)]), team('ai', [{ unit: 'dummy', x: 5, y: 2, tag: 'a' }, anchor(7, 5)])] });
    const c = byTag(g, 'c'), a = byTag(g, 'a');
    g.useAbility(c.uid, 'poke', 5, 2);
    g.endTurn();
    expect(c.coiled).toBe(false);
    const hp = a.hp;
    g.move(a.uid, 5, 3);
    expect(a.hp).toBe(hp);
  });
});

describe('shells', () => {
  it('soaks damage first, discards the overflow, then evicts into the token form', () => {
    const g = world({ teams: [team('human', [{ unit: 'hitter', x: 3, y: 2, tag: 'h' }, anchor(0, 5)]), team('ai', [{ unit: 'crab', x: 4, y: 2, tag: 'c' }, anchor()])] });
    const ev = events(g);
    const h = byTag(g, 'h'), c = byTag(g, 'c');
    expect(c.shellHp).toBe(8);
    g.useAbility(h.uid, 'poke', 4, 2); // attack 4 + 0
    expect(c.shellHp).toBe(4);
    expect(c.hp).toBe(20);
    cycle(g);
    c.cooldowns.poke = 1;
    c.hp = 15;
    g.useAbility(h.uid, 'slam', 4, 2); // 3 pierce: bypasses the shell
    expect(c.shellHp).toBe(4);
    expect(c.hp).toBe(12);
    cycle(g);
    g.useAbility(h.uid, 'venom_hit', 4, 2); // venom bypasses the shell
    expect(c.hp).toBe(10);
    cycle(g);
    g.useAbility(h.uid, 'poke', 4, 2); // 4 into a 4 shell: breaks, overflow 0
    expect(c.defId).toBe('crab_bare');
    expect(c.shellHp).toBeUndefined();
    expect(c.hp).toBe(10);
    expect(c.cooldowns).toEqual({});
    expect(ev.some(e => e.kind === 'evict' && e.uid === c.uid && e.from === 'crab' && e.to === 'crab_bare')).toBe(true);
    expect(ev.some(e => e.kind === 'damage' && e.uid === c.uid && e.shell)).toBe(true);
  });

  it('caps body HP to the evicted form and keeps statuses and equipment', () => {
    const g = world({ teams: [team('human', [{ unit: 'hitter', x: 3, y: 2, tag: 'h' }, anchor(0, 5)]), team('ai', [{ unit: 'crab', x: 4, y: 2, tag: 'c' }, anchor()])] });
    const c = byTag(g, 'c');
    c.shellHp = 1;
    c.statuses.push({ id: 'weakened', remaining: 3 });
    g.useAbility(byTag(g, 'h').uid, 'poke', 4, 2);
    expect(c.defId).toBe('crab_bare');
    expect(c.hp).toBe(12);
    expect(c.statuses.map(s => s.id)).toEqual(['weakened']);
  });

  it('a fallen evicted crab puts the card it was deployed as on cooldown', () => {
    const g = world({ teams: [team('human', [anchor(0, 4)], ['crab']), team('ai', [{ unit: 'hitter', x: 2, y: 5, tag: 'h' }, anchor()])] });
    expect(g.playCard(0, 0, 1, 5)).toBe(true);
    const c = at(g, 1, 5);
    g.endTurn();
    c.shellHp = 1;
    c.hp = 2;
    const h = byTag(g, 'h');
    g.useAbility(h.uid, 'poke', 1, 5);
    expect(c.defId).toBe('crab_bare');
    cycle(g);
    g.useAbility(h.uid, 'poke', 1, 5);
    expect(c.alive).toBe(false);
    expect(g.teams[0].cooldown.map(x => x.card)).toEqual(['crab']);
  });

  it('moveOut steps out as the evicted form and leaves an empty shell with the remaining shell HP', () => {
    const g = world({ teams: [team('human', [{ unit: 'crab', x: 3, y: 2, tag: 'c' }, anchor(0, 5)]), team('ai', [anchor()])] });
    const c = byTag(g, 'c');
    c.shellHp = 5;
    expect(g.validTargets(c, 'move_out').length).toBeGreaterThan(0);
    expect(g.canUse(c, 'rehouse')).toBe(false); // not one of the shelled form's abilities
    expect(g.useAbility(c.uid, 'move_out', 3, 3)).toBe(true);
    expect(c.defId).toBe('crab_bare');
    expect([c.x, c.y]).toEqual([3, 3]);
    const shell = at(g, 3, 2);
    expect(shell.defId).toBe('crab_empty');
    expect(shell.hp).toBe(5);
    expect(shell.team).toBe(0);
    // ...and rehouse climbs back in with that much shell.
    cycle(g);
    expect(g.canUse(c, 'rehouse')).toBe(true);
    expect(g.validTargets(c, 'rehouse')).toEqual([{ x: 3, y: 2 }]);
    expect(g.useAbility(c.uid, 'rehouse', 3, 2)).toBe(true);
    expect(c.defId).toBe('crab');
    expect(c.shellHp).toBe(5);
    expect([c.x, c.y]).toEqual([3, 2]);
    expect(shell.alive).toBe(false);
  });

  it('rehouse onto a shellSource tile gives a full shell and turns the tile to salt_flat', () => {
    const g = world({ teams: [team('human', [{ unit: 'crab_bare', x: 3, y: 2, tag: 'c' }, anchor(0, 5)]), team('ai', [anchor()])],
      map: { tiles: ['........', '........', '....w...', '........', '........', '........'] } });
    const c = byTag(g, 'c');
    const ev = events(g);
    expect(g.validTargets(c, 'rehouse')).toEqual([{ x: 4, y: 2 }]);
    expect(g.useAbility(c.uid, 'rehouse', 4, 2)).toBe(true);
    expect(c.defId).toBe('crab');
    expect(c.shellHp).toBe(8);
    expect(c.hp).toBe(12); // body HP carries over
    expect(g.tiles[2][4].terrain).toBe('salt_flat');
    expect(ev.some(e => e.kind === 'rehouse' && e.uid === c.uid)).toBe(true);
    expect(g.canUse(c, 'rehouse')).toBe(false); // abilities follow the new form
  });

  it('shell repair caps at shell.hp and does nothing to unshelled units; filter.shelled picks targets', () => {
    const g = world({ teams: [team('human', [{ unit: 'crab', x: 3, y: 2, tag: 'c' }, { unit: 'crab', x: 3, y: 3, tag: 'c2' }, anchor(0, 5)]),
      team('ai', [{ unit: 'hitter', x: 4, y: 2, tag: 'h' }, anchor()])] });
    const c = byTag(g, 'c'), c2 = byTag(g, 'c2');
    c2.shellHp = 6;
    g.useAbility(c.uid, 'patch', 3, 3);
    expect(c2.shellHp).toBe(8);
    g.endTurn();
    const h = byTag(g, 'h');
    g.useAbility(h.uid, 'crack', 3, 2); // shelled: pierces for 4
    expect(c.hp).toBe(16);
    c.shellHp = 0;
    cycle(g);
    g.useAbility(h.uid, 'crack', 3, 2);
    expect(c.hp).toBe(16); // filter.shelled: true skips an unshelled target
  });

  it('the AI rehouses an evicted crab standing next to an empty shell', () => {
    const g = world({ teams: [team('human', [{ unit: 'dummy', x: 0, y: 5 }]),
      team('ai', [{ unit: 'crab_bare', x: 6, y: 0, tag: 'c' }, { unit: 'crab_empty', x: 6, y: 1 }, anchor(7, 4)])] });
    g.endTurn();
    playAiTurn(g);
    const c = byTag(g, 'c');
    expect(c.defId).toBe('crab');
    expect(c.shellHp).toBe(8);
  });
});

describe('long bodies', () => {
  it('walking lays the tail on the tiles behind; damage to segments hits the head once; segments go with the head', () => {
    const g = world({ teams: [team('human', [{ unit: 'eel', x: 1, y: 2, tag: 'e' }, anchor(0, 5)]), team('ai', [{ unit: 'hitter', x: 7, y: 2, tag: 'h' }, anchor()])] });
    const e = byTag(g, 'e');
    expect(g.move(e.uid, 4, 2)).toBe(true);
    const segs = e.tail!.map(id => g.unit(id)!);
    expect(segs.map(s => [s.x, s.y])).toEqual([[3, 2], [2, 2]]);
    expect(segs.every(s => s.tailOf === e.uid && g.def(s).structure)).toBe(true);
    // Walk again: the tail follows.
    cycle(g);
    g.move(e.uid, 4, 4);
    expect(e.tail!.map(id => [g.unit(id)!.x, g.unit(id)!.y])).toEqual([[4, 3], [4, 2]]);
    g.endTurn();
    const h = byTag(g, 'h');
    g.move(h.uid, 5, 2);
    const hp = e.hp;
    g.useAbility(h.uid, 'pierce_hit', 4, 2); // hits a segment
    expect(e.hp).toBe(hp - 2);
    cycle(g);
    g.useAbility(h.uid, 'slam', 4, 3); // area covers the head and both segments: one hit of 3
    expect(e.hp).toBe(hp - 5);
    e.hp = 1;
    cycle(g);
    g.useAbility(h.uid, 'pierce_hit', 4, 2);
    expect(e.alive).toBe(false);
    expect(segs.every(s => !s.alive)).toBe(true);
  });

  it('the AI attacks a tail segment as a proxy for its head without crashing', () => {
    const g = world({ teams: [team('human', [{ unit: 'eel', x: 1, y: 2, tag: 'e' }, anchor(0, 5)]), team('ai', [{ unit: 'hitter', x: 4, y: 0, tag: 'h' }])] });
    const e = byTag(g, 'e');
    g.move(e.uid, 1, 4); // tail at (1,3),(1,2)
    g.endTurn();
    const hp = e.hp;
    playAiTurn(g);
    expect(e.hp).toBeLessThan(hp);
  });
});

describe('AI stays stable with every new mechanic on the board', () => {
  it('plays AI vs AI for several rounds without throwing', () => {
    for (let seed = 1; seed <= 4; seed++) {
      const g = world({
        teams: [
          team('ai', [{ unit: 'snake', x: 1, y: 4 }, { unit: 'coiler', x: 2, y: 4 }, { unit: 'eel', x: 3, y: 5 }, { unit: 'crab', x: 0, y: 3 }]),
          team('ai', [{ unit: 'crab', x: 6, y: 1 }, { unit: 'crab_empty', x: 5, y: 0 }, { unit: 'hitter', x: 7, y: 2 }, { unit: 'nipper', x: 6, y: 0 }]),
        ],
        map: { tiles: ['........', '...w....', '........', '........', '....w...', '........'] },
      });
      for (let i = 0; i < 24 && g.phase === 'playing'; i++) playAiTurn(g);
      expect(['playing', 'victory', 'defeat']).toContain(g.phase);
    }
  });
});

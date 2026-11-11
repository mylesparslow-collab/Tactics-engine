// The proving ground: a tiny live battle board in the collection's card detail. It runs the real Game and
// Renderer, so a champion swings its real abilities and a spell or piece of equipment plays its real effect,
// on a looping stage with a rival training dummy.
import type { AbilityDef, Content, MapDef, MissionDef, PlacedUnit, Pos } from '../engine/types';
import { Game } from '../engine/game';
import { Renderer } from '../render/renderer';
import { playCue } from '../audio/sfx';
import { isCardUnit, label } from '../engine/content';
import { h } from './dom';

const W = 7, H = 5, MID = 2;
const MAP_ID = 'collection:proving';
const MISSION_ID = 'collection:proving';

interface Step { caption: string; act: (g: Game) => boolean }
interface Scene { ally: PlacedUnit[]; foe: PlacedUnit[]; hand: string[]; wounded?: string[]; focus: Pos; steps: Step[] }

function provingMap(): MapDef {
  // salt flat with silt drifts, a deterministic scatter so every visit looks the same
  const tiles: string[] = [], heights: string[] = [];
  for (let y = 0; y < H; y++) {
    let row = '';
    for (let x = 0; x < W; x++) row += ((x * 7 + y * 13) % 5 === 0) ? 's' : '.';
    tiles.push(row); heights.push('0'.repeat(W));
  }
  return { id: MAP_ID, name: 'Proving ground', legend: { '.': 'salt_flat', s: 'silt' }, tiles, heights, keystones: [], deployZones: { 0: [], 1: [] } };
}

/** A cheap non-hero champion of the faction after this one: the training dummy. */
function rivalDummy(c: Content, faction: string | undefined): string {
  const fids = Object.keys(c.factions ?? {});
  const rival = fids[(Math.max(0, fids.indexOf(faction ?? '')) + 1) % Math.max(1, fids.length)];
  const pool = Object.entries(c.units).filter(([k, u]) => isCardUnit(c, k) && !u.hero && u.faction === rival).sort((a, b) => a[1].cost - b[1].cost);
  return pool[0]?.[0] ?? Object.keys(c.units).find(k => isCardUnit(c, k))!;
}

/** A face for spells and a wearer for equipment: the faction's first hero (or cheapest champion). */
function factionUnit(c: Content, faction: string | undefined, restrict?: string[]): string {
  const all = Object.entries(c.units).filter(([k, u]) => isCardUnit(c, k) && u.faction === faction);
  const ok = restrict?.length ? all.filter(([k, u]) => restrict.includes(k) || restrict.includes(u.role ?? '')) : all;
  const pool = ok.length ? ok : all;
  return (pool.find(([, u]) => u.hero && !restrict?.length) ?? [...pool].sort((a, b) => a[1].cost - b[1].cost)[0])?.[0] ?? rivalDummy(c, undefined);
}

function abilityMeta(c: Content, a: AbilityDef) {
  const r = a.range.min === a.range.max ? `${a.range.max}` : `${a.range.min}-${a.range.max}`;
  return `${a.name} · ${a.apCost} AP · range ${r}`;
}

/** Desired target distance for an ability, kept inside the stage. */
const reach = (a: { range: { min: number; max: number } }) => Math.max(1, Math.min(a.range.max, Math.max(a.range.min, 2), W - 2));

/** Pick the tile closest to `want` from a list of legal targets. */
function nearest(list: Pos[], want: Pos): Pos | undefined {
  let best: Pos | undefined, bd = Infinity;
  for (const p of list) { const d = Math.abs(p.x - want.x) + Math.abs(p.y - want.y); if (d < bd) { bd = d; best = p; } }
  return best;
}

/** Put enemies on the target tile and, for area effects, around it, so splash damage has something to hit. */
function crowd(dummy: string, at: Pos, area: number, skipCentre = false): PlacedUnit[] {
  const out: PlacedUnit[] = skipCentre ? [] : [{ unit: dummy, ...at }];
  if (area > 0) for (const d of [{ x: 0, y: -1 }, { x: 0, y: 1 }, { x: 1, y: 0 }]) {
    const p = { x: at.x + d.x, y: at.y + d.y };
    if (p.x < W && p.y >= 0 && p.y < H) out.push({ unit: dummy, ...p });
  }
  return out;
}

function unitScenes(c: Content, id: string): Scene[] {
  const u = c.units[id], dummy = rivalDummy(c, u.faction);
  const active = u.abilities.filter(a => c.abilities[a] && !c.abilities[a].passive);
  const me: Pos = { x: 1, y: MID };
  if (!active.length) return [{ ally: [{ unit: id, ...me }], foe: [{ unit: dummy, x: 4, y: MID }], hand: [], focus: { x: 2.5, y: MID }, steps: [] }];
  return active.map(aid => {
    const a = c.abilities[aid], d = reach(a), at = { x: me.x + d, y: MID };
    const ally: PlacedUnit[] = [{ unit: id, ...me, tag: 'subject' }], foe: PlacedUnit[] = [];
    let want: Pos = at; const wounded: string[] = [];
    switch (a.target) {
      case 'ally': ally.push({ unit: factionUnit(c, u.faction), ...at, tag: 'patient' }); wounded.push('patient'); break;
      case 'self': want = me; foe.push(...crowd(dummy, { x: me.x + 1, y: MID }, a.area?.size ?? 0)); wounded.push('subject'); break;
      case 'empty': foe.push(...crowd(dummy, { x: Math.min(W - 1, at.x + 1), y: MID }, 0)); break;
      default: foe.push(...crowd(dummy, at, a.area?.size ?? 0, false));
    }
    if (a.area?.shape === 'line') for (let k = 1; k < a.area.size && at.x + k < W; k++) foe.push({ unit: dummy, x: at.x + k, y: MID });
    if (!foe.length) foe.push({ unit: dummy, x: W - 1, y: 0 });
    return {
      ally, foe, hand: [], wounded, focus: { x: (me.x + Math.max(at.x, me.x + 1)) / 2, y: MID },
      steps: [{ caption: abilityMeta(c, a), act: (g: Game) => {
        const s = g.units.find(x => x.tag === 'subject'); if (!s) return false;
        s.ap = 99;
        const t = nearest(g.targetsFrom(s, aid), want);
        return !!t && g.useAbility(s.uid, aid, t.x, t.y);
      } }],
    };
  });
}

function spellScene(c: Content, id: string): Scene {
  const sp = c.spells[id], dummy = rivalDummy(c, sp.faction), caster = factionUnit(c, sp.faction);
  const cr = sp.castRange;
  const nearBeacon = typeof cr === 'object';
  const me: Pos = { x: 1, y: MID };
  const d = Math.max(1, Math.min(3, typeof cr === 'number' ? cr : nearBeacon ? cr.nearKeystone : 3));
  const at = { x: me.x + d, y: MID };
  const ally: PlacedUnit[] = [{ unit: caster, ...me, tag: 'caster' }], foe: PlacedUnit[] = [];
  if (nearBeacon) ally.push({ unit: 'keystone', x: 0, y: 0, tag: 'keystone_0' });
  const wounded: string[] = [];
  const area = sp.area?.size ?? 0;
  switch (sp.target) {
    case 'ally': {
      const patient = Object.entries(c.units).find(([k, u]) => u.faction === sp.faction && isCardUnit(c, k) && !u.hero && k !== caster)?.[0] ?? caster;
      ally.push({ unit: patient, ...at, tag: 'patient' }); wounded.push('patient', 'caster');
      foe.push({ unit: dummy, x: Math.min(W - 1, at.x + 2), y: MID }); break;
    }
    case 'empty': foe.push(...crowd(dummy, at, Math.max(1, area), true)); break;
    default: foe.push(...crowd(dummy, at, area));
  }
  const heals = sp.effects.some(e => e.type === 'heal');
  if (heals && sp.target !== 'ally') wounded.push('caster');
  return {
    ally, foe, hand: [id], wounded, focus: { x: (me.x + at.x) / 2 + 0.3, y: MID + (area ? 0.6 : 0) },
    steps: [{ caption: `${sp.name} · ${sp.cost} ${label(c, 'essence')}`, act: (g: Game) => {
      const t = nearest(g.cardTargets(0, 0), at);
      return !!t && g.playCard(0, 0, t.x, t.y);
    } }],
  };
}

function equipScene(c: Content, id: string): Scene {
  const eq = c.equipment[id], dummy = rivalDummy(c, eq.faction), wearer = factionUnit(c, eq.faction, eq.restrictTo);
  const me: Pos = { x: 2, y: MID };
  const granted = (eq.grantAbilities ?? []).find(a => c.abilities[a] && !c.abilities[a].passive);
  const shown = granted ?? c.units[wearer].abilities.find(a => c.abilities[a] && !c.abilities[a].passive);
  const d = shown ? reach(c.abilities[shown]) : 1;
  const at = { x: Math.min(W - 1, me.x + d), y: MID };
  const steps: Step[] = [{ caption: `${eq.name} · ${eq.cost} ${label(c, 'essence')}`, act: (g: Game) => {
    const w = g.units.find(x => x.tag === 'wearer'); return !!w && g.playCard(0, 0, w.x, w.y);
  } }];
  if (shown) steps.push({ caption: `${granted ? 'Grants ' : 'Wearer: '}${abilityMeta(c, c.abilities[shown])}`, act: (g: Game) => {
    const w = g.units.find(x => x.tag === 'wearer'); if (!w) return false;
    w.ap = 99; const t = nearest(g.targetsFrom(w, shown), at);
    return !!t && g.useAbility(w.uid, shown, t.x, t.y);
  } });
  return { ally: [{ unit: wearer, ...me, tag: 'wearer' }], foe: [{ unit: dummy, ...at }], hand: [id], focus: { x: (me.x + at.x) / 2, y: MID }, steps };
}

export class ProvingGround {
  readonly el: HTMLElement;
  private cv: HTMLCanvasElement;
  private cap: HTMLElement;
  private r: Renderer;
  private ro: ResizeObserver;
  private content: Content;
  private scenes: Scene[] = [];
  private sceneIdx = 0;
  private game: Game | null = null;
  private timers: number[] = [];
  private sound = false;
  private dead = false;
  private running = false;

  constructor(base: Content) {
    // A private copy of the tables, so the stage map never shows up in the skirmish map list.
    this.content = { ...base, maps: { ...base.maps, [MAP_ID]: provingMap() }, missions: { ...base.missions } };
    this.cv = h('canvas', { class: 'pg-canvas' });
    this.cap = h('div', { class: 'pg-cap' });
    const replay = h('button', { class: 'pg-replay', title: 'Play again', onclick: () => { this.sound = true; this.sceneIdx = Math.max(0, this.sceneIdx - 1); this.next(); } }, '↻');
    this.el = h('div', { class: 'pg' }, h('div', { class: 'pg-stage' }, this.cv), h('div', { class: 'pg-foot' }, this.cap, replay));
    this.r = new Renderer(this.cv);
    this.r.onCue = cue => { if (this.sound && this.game) playCue(cue, this.game); };
    this.ro = new ResizeObserver(() => { if (!this.game) return; this.r.resize(); this.frame(); });
    this.ro.observe(this.cv.parentElement ?? this.el);
  }

  /** Show a card. Sound plays for the first run (the player just clicked), then the loop goes quiet. */
  show(id: string) {
    const c = this.content;
    this.scenes = c.units[id] ? unitScenes(c, id) : c.spells[id] ? [spellScene(c, id)] : c.equipment[id] ? [equipScene(c, id)] : [];
    this.sceneIdx = 0; this.sound = true;
    requestAnimationFrame(() => this.next());
  }

  private clearTimers() { this.timers.forEach(t => clearTimeout(t)); this.timers = []; }
  private later(ms: number, fn: () => void) { this.timers.push(window.setTimeout(() => { if (!this.dead) fn(); }, ms)); }
  private zoom() { const w = this.cv.parentElement?.clientWidth ?? 400; return w < 420 ? 2.1 : 2.0; }
  private frame() { const s = this.scenes[(this.sceneIdx + this.scenes.length - 1) % this.scenes.length]; if (s) this.r.frameTile(s.focus, this.zoom(), 72); }

  private next() {
    if (this.dead || !this.scenes.length) return;
    this.clearTimers();
    const s = this.scenes[this.sceneIdx % this.scenes.length];
    this.sceneIdx = (this.sceneIdx + 1) % this.scenes.length;
    const mission: MissionDef = {
      id: MISSION_ID, name: 'Proving ground', map: MAP_ID, startingEssence: 999, maxEssence: 999,
      teams: [
        { name: 'You', color: '#e8c57a', controller: 'human', keystone: false, warband: s.hand, units: s.ally },
        { name: 'Rival', color: '#c0503a', controller: 'ai', keystone: false, warband: [], units: s.foe },
      ],
      objectives: { victory: [], defeat: [] },
    };
    this.content.missions[MISSION_ID] = mission;
    let g: Game;
    try { g = new Game(this.content, MISSION_ID, { seed: 7 }); } catch (e) { console.warn('proving ground', e); this.cap.textContent = ''; return; }
    for (const tag of s.wounded ?? []) { const u = g.units.find(x => x.tag === tag); if (u) u.hp = Math.max(1, Math.ceil(g.def(u).stats.hp * 0.45)); }
    this.game = g;
    this.r.setGame(g);
    if (!this.running) { this.running = true; this.r.start(); }
    this.frame();
    g.on(e => this.r.handleEvent(e));
    this.cap.textContent = s.steps[0]?.caption ?? 'Passive abilities only';
    const run = (i: number) => {
      if (i >= s.steps.length) { this.later(1500, () => { this.sound = false; this.next(); }); return; }
      this.cap.textContent = s.steps[i].caption;
      let ok = false;
      try { ok = s.steps[i].act(g); } catch (e) { console.warn('proving ground step', e); }
      const wait = () => this.r.busy() ? this.later(120, wait) : this.later(ok ? 650 : 200, () => run(i + 1));
      wait();
    };
    if (s.steps.length) this.later(750, () => run(0));
  }

  destroy() {
    this.dead = true; this.clearTimers(); this.r.stop(); this.ro.disconnect(); this.r.onCue = null;
  }
}

// Spell animations. Each spell picks an `anim` (content/spells.json), so spells read by what they do and
// whose they are instead of all being the same shaft of light: salt hail, pressure that crushes inward,
// geysers of brine, ink and veil clouds, undertow vortices, powder blasts, coral bursting from the ground,
// feather squalls. The Lanternkeepers keep the light beam: it is their thing.
import type { Pos, SpellDef } from '../engine/types';
import { isFxPreset, type Fx, type FxPreset } from './fx';
import { TW } from './iso';

export type SpellAnim = 'beam' | 'hail' | 'fall' | 'glyph' | 'summon' | 'geyser' | 'crush' | 'vortex' | 'blast' | 'cloud'
  | 'drain' | 'heal' | 'growth' | 'feathers' | 'hex';

export interface SpellHost {
  fx: Fx;
  at(t: number, fn: () => void): void;
  project(p: Pos): { sx: number; sy: number };
  ring(p: Pos, start: number, dur: number, color: string, rune?: boolean): void;
  column(p: Pos, start: number, dur: number, color: string, width: number): void;
  shake(t: number, mag: number, ms: number): void;
  tiles(c: Pos, size: number): Pos[];
  /** The legacy flash of sparks at the target. */
  sparks(p: Pos, n: number, color: string, opts: { up?: number; spread?: number; life?: number; size?: number; g?: number; rise?: boolean }): void;
}

/** What a spell does when no `anim` is set, from its effects. */
export function defaultAnim(sp: SpellDef): SpellAnim {
  const ty = sp.effects.map(e => e.type);
  if (ty.includes('summon')) return 'summon';
  if (ty.includes('pull') || ty.includes('push')) return 'vortex';
  if (ty.includes('damage')) return (sp.area?.size ?? 0) > 0 ? 'blast' : 'hail';
  if (ty.includes('heal')) return 'heal';
  if (ty.includes('essence')) return 'drain';
  if (ty.includes('terrain')) return 'growth';
  return sp.target === 'ally' ? 'glyph' : 'hex';
}

const pick = <T,>(a: T[]) => a[(Math.random() * a.length) | 0];

/** Plays the spell's animation from time `t`. Returns when its damage should land and when it's over (ms after t). */
export function playSpell(h: SpellHost, sp: SpellDef, target: Pos, t: number, col: string): { impact: number; dur: number } {
  const anim = (sp.anim as SpellAnim | undefined) ?? defaultAnim(sp);
  const vfx = isFxPreset(sp.vfx) ? sp.vfx : undefined;
  const area = Math.min(3, sp.area?.size ?? 0);            // whole-map spells animate around the target only
  const rx = (area + 0.5) * TW * 0.5;
  // Spell particles read at board zoom: bigger, denser and longer-lived than a unit's idle wisps.
  const S = 1.9, N = 1.6, base = h.fx;
  const fx = {
    burst: (pr: FxPreset, x: number, y: number, n: number, o: { radius?: number; scale?: number; push?: { vx: number; vy: number } } = {}) => base.burst(pr, x, y, Math.round(n * N), { ...o, scale: (o.scale ?? 1) * S }),
    fountain: (pr: FxPreset, x: number, y: number, n: number, radius = 0, up = 1, scale = 1) => base.fountain(pr, x, y, Math.round(n * N), radius, up, scale * S),
    vortex: (pr: FxPreset, x: number, y: number, n: number, r: number, o: { w?: number; dr?: number; dl?: number; scale?: number; ms?: number } = {}) => base.vortex(pr, x, y, Math.round(n * N), r, { ...o, scale: (o.scale ?? 1) * S, ms: o.ms ? o.ms * 1.35 : undefined }),
    area: (pr: FxPreset, x: number, y: number, r: number, ms: number, now: number) => base.area(pr, x, y, r, ms, now),
    comet: (x0: number, y0: number, x1: number, y1: number, ms: number, color: string, size = 2.4) => base.comet(x0, y0, x1, y1, ms, color, size * 1.6),
  };
  const tiles = area ? h.tiles(target, area) : [target];
  const dmg = sp.effects.some(e => e.type === 'damage');
  const at = (ms: number, fn: (c: { sx: number; sy: number }) => void, p: Pos = target) => h.at(t + ms, () => fn(h.project(p)));
  const dist = (p: Pos) => Math.abs(p.x - target.x) + Math.abs(p.y - target.y);
  const ripple = (delay: number, dur = 520) => { for (const p of tiles) if (dist(p)) h.ring(p, t + delay + 50 * dist(p), dur, col); };
  switch (anim) {
    case 'beam': { // the Lanternkeepers' lamp: a shaft of light and a rune on the ground
      h.column(target, t, 760, col, 26 + area * 14);
      h.ring(target, t, 820, col, true); ripple(180);
      at(260, () => { h.sparks(target, 22 + area * 10, '#fff2c4', { up: 90, spread: 60 + area * 30, life: 800, size: 3.2 }); });
      at(260, c => fx.burst('gold', c.sx, c.sy - 10, 14 + area * 6, { radius: rx * 0.6 }));
      if (dmg) h.shake(t + 260, 3 + area * 1.5, 260);
      return { impact: 420, dur: 900 };
    }
    case 'hail': { // projectiles streak down out of the sky onto the target tiles
      const n = area ? Math.min(12, 3 + tiles.length) : 3, hit = vfx ?? 'shards';
      for (let i = 0; i < n; i++) {
        const p = i < tiles.length ? tiles[i] : pick(tiles), d = 90 * i / n + Math.random() * 40;
        at(d, c => { const ox = (Math.random() - 0.5) * 30; fx.comet(c.sx - 170 + ox, c.sy - 330, c.sx + ox * 0.3, c.sy - 6, 360, col, 2.6); }, p);
        at(d + 360, c => { fx.burst(hit, c.sx, c.sy - 6, 9, { radius: 6 }); fx.burst('dust', c.sx, c.sy - 4, 3, { radius: 8 }); h.ring(p, t + d + 360, 360, col); }, p);
      }
      if (dmg) h.shake(t + 380, 2.5 + area, 220);
      return { impact: 420, dur: 900 };
    }
    case 'fall': { // something heavy: a long whistle down, then the ground jumps
      at(0, c => fx.comet(c.sx - 40, c.sy - 460, c.sx, c.sy - 10, 520, '#cfd8e0', 7));
      h.ring(target, t + 80, 460, '#1a1d2b');
      at(520, c => { fx.burst('dust', c.sx, c.sy - 6, 22, { radius: 30, scale: 1.8, push: { vx: 0, vy: -10 } }); fx.fountain('shards', c.sx, c.sy - 4, 14, 10); fx.fountain(vfx ?? 'water', c.sx, c.sy - 4, 16, 8); h.ring(target, t + 520, 520, '#e8dcc2'); });
      h.shake(t + 520, 9, 360);
      return { impact: 540, dur: 1100 };
    }
    case 'glyph': { // a rite: the rune lights the ground and motes rise off it over every ally in reach
      const m = vfx ?? 'gold';
      h.ring(target, t, 1000, col, true); ripple(140, 700);
      for (const p of tiles) at(120 + 60 * dist(p), c => fx.fountain(m, c.sx, c.sy - 6, 8, 20, 0.7), p);
      at(60, c => fx.vortex(m, c.sx, c.sy - 6, 18, 46, { w: 3, dr: -16, dl: 30, ms: 900 }));
      return { impact: 380, dur: 1000 };
    }
    case 'summon': { // a rift: matter spirals in, then bursts up out of the ground
      const m = vfx ?? 'motes';
      h.ring(target, t, 1000, col, true);
      at(0, c => fx.vortex(m, c.sx, c.sy - 6, 26, 60, { w: 5, dr: -70, dl: 10, ms: 650 }));
      at(560, c => { fx.fountain(m, c.sx, c.sy - 6, 22, 16, 1.2, 1.3); fx.burst('dust', c.sx, c.sy - 4, 8, { radius: 18 }); h.ring(target, t + 560, 500, col); });
      return { impact: 600, dur: 1100 };
    }
    case 'geyser': { // water (or steam, or oil) bursts up from under each tile in a rolling wave
      const m = vfx ?? 'water';
      for (const p of tiles) at(60 * dist(p), c => {
        fx.fountain(m, c.sx, c.sy - 6, 22, 10, 1.3, 1.2);
        if (m !== 'steam') fx.burst('steam', c.sx, c.sy - 10, 5, { radius: 10 });
        if (m === 'water') fx.burst('bubbles', c.sx, c.sy - 6, 4, { radius: 12 });
        h.ring(p, t + 60 * dist(p), 520, col);
      }, p);
      if (dmg) h.shake(t + 120, 2 + area, 200);
      return { impact: 300, dur: 900 + area * 120 };
    }
    case 'crush': { // the weight of the deep: dark pressure rings close in, then everything flattens
      at(0, c => fx.vortex('current', c.sx, c.sy - 6, 20 + area * 8, rx * 1.4, { w: 3, dr: -rx * 2.6, ms: 420 }));
      for (let i = 0; i < 3; i++) at(i * 90, c => fx.vortex('murk', c.sx, c.sy - 4, 10 + area * 6, rx * 1.3, { w: 2.5, dr: -rx * 2.2, ms: 480, scale: 1.4 }));
      at(440, c => { fx.burst('dust', c.sx, c.sy - 4, 14 + area * 8, { radius: rx * 0.8, scale: 1.5 }); fx.fountain('shards', c.sx, c.sy - 4, 8 + area * 4, rx * 0.5, 0.5); });
      at(440, () => ripple(0, 400)); h.ring(target, t + 440, 420, '#6fb6ff');
      h.shake(t + 440, 6 + area * 2, 320);
      return { impact: 460, dur: 1000 };
    }
    case 'vortex': { // undertow and gales: a whirl that drags in (pull), throws out (push) or lifts (neither)
      const pull = sp.effects.some(e => e.type === 'pull'), push = sp.effects.some(e => e.type === 'push');
      const m = vfx ?? (pull ? 'bubbles' : 'dust');
      at(0, c => {
        fx.vortex(m, c.sx, c.sy - 6, 30 + area * 12, rx * (pull ? 1.3 : 0.5), { w: pull ? 5 : 6, dr: pull ? -rx * 1.4 : push ? rx * 1.6 : 4, dl: push || pull ? 6 : 60, ms: 1100, scale: 1.2 });
        fx.vortex(pull ? 'current' : 'wind', c.sx, c.sy - 6, 24 + area * 8, rx * (pull ? 1.2 : 0.4), { w: 5, dr: pull ? -rx : push ? rx * 1.2 : 10, dl: pull || push ? 4 : 70, ms: 800 });
        if (pull) { fx.vortex('spray', c.sx, c.sy - 6, 20, rx, { w: 6, dr: -rx, ms: 900 }); fx.vortex('mist', c.sx, c.sy - 6, 10, rx, { w: 3, dr: -rx * 0.8, ms: 900 }); }
        else fx.vortex('dust', c.sx, c.sy - 6, 12, rx * 0.7, { w: 5, dr: rx, dl: push ? 0 : 40, ms: 900, scale: 1.6 });
      });
      h.ring(target, t, 900, col, true);
      return { impact: 500, dur: 1100 };
    }
    case 'blast': { // powder and fire: staggered explosions across the area, embers and a pall of smoke
      const n = Math.max(1, Math.min(6, 1 + area * 2));
      for (let i = 0; i < n; i++) {
        const p = i === 0 ? target : pick(tiles), d = i * 110;
        at(d, c => {
          fx.burst('fire', c.sx, c.sy - 10, 16, { radius: 12, scale: 1.6 }); fx.fountain('embers', c.sx, c.sy - 8, 14, 6, 1.4);
          fx.burst('smoke', c.sx, c.sy - 16, 8, { radius: 14, scale: 1.6 }); h.ring(p, t + d, 420, '#ffb347');
        }, p);
        h.shake(t + d, 3 + area, 180);
      }
      if (vfx && vfx !== 'embers') at(200, c => fx.area(vfx, c.sx, c.sy - 6, rx, 2400, performance.now()));
      return { impact: 200, dur: 900 + n * 110 };
    }
    case 'cloud': { // ink, veil, mist, salt: a cloud rolls out over the area and lingers
      h.ring(target, t, 700, col, true);
      at(120, c => fx.area(vfx ?? 'mist', c.sx, c.sy - 6, rx, 3000, performance.now()));
      if (vfx !== 'cloud') at(120, c => fx.vortex(vfx ?? 'mist', c.sx, c.sy - 8, 10 + area * 6, 10, { w: 2, dr: rx * 1.4, ms: 900, scale: 1.8 }));
      if (dmg) h.shake(t + 200, 2, 200);
      return { impact: 320, dur: 1000 };
    }
    case 'drain': { // tithes: Tide is torn out of the target in a spiral and carried up and away
      const m = vfx ?? 'tide';
      if (dmg) at(0, c => fx.burst('dust', c.sx, c.sy - 10, 6, { radius: 10 }));
      at(0, c => { fx.vortex(m, c.sx, c.sy - 30, 26, 34, { w: 6, dr: -24, dl: 110, ms: 1000 }); fx.vortex(m === 'gold' ? 'gold' : 'current', c.sx, c.sy - 20, 18, 40, { w: 7, dr: -30, dl: 130, ms: 800 }); fx.fountain(m, c.sx, c.sy - 20, 10, 8, 1.6); });
      h.ring(target, t, 700, col);
      return { impact: 240, dur: 1000 };
    }
    case 'heal': { // mending: a soft ring, then light lifts gently off the target
      const m = vfx ?? 'heal';
      h.ring(target, t, 800, col); ripple(120, 600);
      for (const p of tiles) at(80 + 60 * dist(p), c => { fx.fountain(m, c.sx, c.sy - 10, 14, 18, 0.8); fx.vortex('heal', c.sx, c.sy - 20, 8, 22, { w: 4, dl: 50, ms: 900 }); }, p);
      return { impact: 300, dur: 1000 };
    }
    case 'growth': { // ground that changes: coral, salt walls, reef spikes erupt tile by tile
      const m = vfx ?? 'coral';
      for (const p of tiles) at(70 * dist(p), c => { fx.fountain(m, c.sx, c.sy - 4, 14, 14, 1.1); fx.burst('dust', c.sx, c.sy - 4, 4, { radius: 14 }); h.ring(p, t + 70 * dist(p), 460, col); }, p);
      h.shake(t + 80, 2, 200);
      return { impact: 300, dur: 900 + area * 140 };
    }
    case 'feathers': { // the Gyre: a squall of feathers, the sky darkened by wings
      at(0, c => { fx.vortex('feathers', c.sx, c.sy - 30, 22 + area * 12, rx * 0.9, { w: 4, dr: -10, dl: -10, ms: 1400 }); fx.burst('feathers', c.sx, c.sy - 80, 12 + area * 6, { radius: rx }); });
      if (vfx) at(100, c => fx.area(vfx, c.sx, c.sy - 6, rx, 2200, performance.now()));
      ripple(160);
      if (dmg) { for (const p of tiles.slice(0, 6)) at(300 + Math.random() * 200, c => fx.comet(c.sx + 120, c.sy - 260, c.sx, c.sy - 12, 220, '#2a2d34', 3.2), p); h.shake(t + 520, 2.5, 200); }
      return { impact: dmg ? 520 : 300, dur: 1400 };
    }
    case 'hex': { // curses and tricks: a ring snaps tight, a puff of the faction's stuff
      const m = vfx ?? 'soot';
      h.ring(target, t, 700, col, true); ripple(100, 420);
      at(80, c => { fx.vortex(m, c.sx, c.sy - 10, 16 + area * 8, rx, { w: 7, dr: -rx * 1.4, ms: 500, scale: 1.2 }); });
      at(520, c => fx.burst(m, c.sx, c.sy - 10, 10 + area * 6, { radius: rx * 0.5, scale: 1.3 }));
      return { impact: 520, dur: 1000 };
    }
  }
}

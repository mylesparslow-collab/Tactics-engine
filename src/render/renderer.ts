import type { Game } from '../engine/game';
import type { GameEvent, Pos, Unit } from '../engine/types';
import { GROUND, LV, TH, TW, View, key, rgba, shade } from './iso';
import { drawUnitSprite } from './sprites';

export interface Preview { text: string; color: string }
export interface Overlay {
  reach: Set<string>;
  targets: Set<string>;
  area: Set<string>;
  deploy: Set<string>;
  path: Pos[];
  pathCost: number | null;
  selected: Pos | null;
  hover: Pos | null;
  previews: Map<number, Preview>;
}
export const emptyOverlay = (): Overlay => ({
  reach: new Set(), targets: new Set(), area: new Set(), deploy: new Set(), path: [], pathCost: null,
  selected: null, hover: null, previews: new Map(),
});

const MS_PER_TILE = 80;
const DEATH_MS = 450;
const POP_MS = 260;

interface Seg { start: number; dur: number; path: Pos[]; arc: boolean }
interface Float { x: number; y: number; text: string; color: string; born: number; life: number }
interface Ring { pos: Pos; start: number; dur: number; color: string }
interface Item { start: number; fn: () => void }
type Drawable = { d: number; kind: 'tile'; x: number; y: number } | { d: number; kind: 'unit'; u: Unit; px: number; py: number; pz: number };

export class Renderer {
  private ctx: CanvasRenderingContext2D;
  private game!: Game;
  private view!: View;
  overlay: Overlay = emptyOverlay();
  private scale = 1; private ox = 0; private oy = 0; private dpr = 1;
  private cssW = 0; private cssH = 0;
  private raf = 0;
  // animation state
  private cursor = 0; private endAt = 0;
  private segs = new Map<number, Seg[]>();
  private bumps = new Map<number, { start: number; dur: number; dx: number; dy: number }>();
  private hpShown = new Map<number, number>();
  private flashUntil = new Map<number, number>();
  private pendingDeath = new Set<number>();
  private dying = new Map<number, number>();
  private pendingDeploy = new Set<number>();
  private popStart = new Map<number, number>();
  private floats: Float[] = [];
  private rings: Ring[] = [];
  private items: Item[] = [];
  private cachedDraw: Drawable[] = [];

  constructor(private canvas: HTMLCanvasElement) {
    this.ctx = canvas.getContext('2d')!;
  }

  setGame(game: Game) {
    this.game = game;
    this.view = new View(game.width, game.height);
    this.overlay = emptyOverlay();
    this.segs.clear(); this.bumps.clear(); this.hpShown.clear(); this.flashUntil.clear();
    this.pendingDeath.clear(); this.dying.clear(); this.pendingDeploy.clear(); this.popStart.clear();
    this.floats = []; this.rings = []; this.items = []; this.cursor = 0; this.endAt = 0;
    for (const u of game.units) this.hpShown.set(u.uid, u.hp);
    this.resize();
  }

  start() { const loop = () => { this.raf = requestAnimationFrame(loop); this.frame(performance.now()); }; this.raf = requestAnimationFrame(loop); }
  stop() { cancelAnimationFrame(this.raf); }

  get rotation() { return this.view.rot; }
  rotate(dir: 1 | -1) { this.view.rot = (this.view.rot + dir + 4) % 4; this.fit(); }

  resize() {
    const r = this.canvas.parentElement!.getBoundingClientRect();
    this.dpr = window.devicePixelRatio || 1;
    this.cssW = Math.max(100, r.width); this.cssH = Math.max(100, r.height);
    this.canvas.width = Math.round(this.cssW * this.dpr);
    this.canvas.height = Math.round(this.cssH * this.dpr);
    this.canvas.style.width = this.cssW + 'px'; this.canvas.style.height = this.cssH + 'px';
    if (this.game) this.fit();
  }

  private fit() {
    const v = this.view;
    let maxL = 0;
    for (const row of this.game.tiles) for (const t of row) maxL = Math.max(maxL, t.height);
    const minX = -(v.rh - 1) * TW / 2 - TW / 2, maxX = (v.rw - 1) * TW / 2 + TW / 2;
    const minY = -TH / 2 - maxL * LV - 56, maxY = (v.rw + v.rh - 2) * TH / 2 + TH / 2 + GROUND + 8;
    const bw = maxX - minX, bh = maxY - minY;
    this.scale = Math.max(0.35, Math.min(this.cssW / bw, this.cssH / bh, 1.8)) * 0.96;
    this.ox = this.cssW / 2 - (minX + bw / 2) * this.scale;
    this.oy = this.cssH / 2 - (minY + bh / 2) * this.scale;
  }

  // ---------- animation scheduling ----------
  busy() { return performance.now() < this.endAt; }

  private at(start: number, fn: () => void) { this.items.push({ start, fn }); this.endAt = Math.max(this.endAt, start); }
  private uname(uid: number) { return this.game.unit(uid); }
  private floatAt(p: Pos, text: string, color: string, born: number) {
    const s = this.view.project(p.x, p.y, this.game.tiles[p.y]?.[p.x]?.height ?? 0);
    const n = this.floats.filter(f => Math.abs(f.born - born) < 300 && Math.abs(f.x - s.sx) < 4 && Math.abs(f.y - s.sy) < 40).length;
    this.floats.push({ x: s.sx, y: s.sy - 46 - n * 14, text, color, born, life: 1100 });
  }
  /** Where a unit is displayed at time `t` (honouring queued movement segments). */
  private unitPos(u: Unit, t: number) {
    const segs = this.segs.get(u.uid);
    const hz = (p: Pos) => this.game.tiles[Math.round(p.y)]?.[Math.round(p.x)]?.height ?? 0;
    if (segs) for (const s of segs) {
      if (t < s.start + s.dur) {
        const p = s.dur > 0 ? Math.max(0, Math.min(1, (t - s.start) / s.dur)) : 1;
        const n = s.path.length - 1;
        const f = p * n, i = Math.min(n - 1, Math.floor(f)), k = f - i;
        const a = s.path[i], b = s.path[i + 1];
        let z = hz(a) + (hz(b) - hz(a)) * k;
        if (s.arc) z += Math.sin(Math.PI * p) * 1.2;
        return { x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k, z };
      }
    }
    return { x: u.x, y: u.y, z: hz(u) };
  }

  handleEvent(e: GameEvent) {
    const now = performance.now();
    this.cursor = Math.max(this.cursor, now);
    const g = this.game;
    const push = (uid: number, seg: Seg) => { const l = this.segs.get(uid) ?? []; l.push(seg); this.segs.set(uid, l); this.endAt = Math.max(this.endAt, seg.start + seg.dur); };
    switch (e.kind) {
      case 'move': {
        const dur = Math.max(e.path.length - 1, 1) * MS_PER_TILE;
        push(e.uid, { start: this.cursor, dur, path: e.path, arc: e.path.length === 2 && Math.abs(e.path[0].x - e.path[1].x) + Math.abs(e.path[0].y - e.path[1].y) > 1 });
        this.cursor += dur; break;
      }
      case 'push': {
        push(e.uid, { start: this.cursor, dur: 200, path: [e.from, e.to], arc: false });
        this.cursor += 200; break;
      }
      case 'ability': {
        const u = g.unit(e.uid);
        if (u) {
          const a = this.view.project(u.x, u.y), b = this.view.project(e.target.x, e.target.y);
          const dx = b.sx - a.sx, dy = b.sy - a.sy, len = Math.hypot(dx, dy) || 1;
          this.bumps.set(e.uid, { start: this.cursor, dur: 200, dx: dx / len * 10, dy: dy / len * 5 });
        }
        this.rings.push({ pos: e.target, start: this.cursor, dur: 450, color: '#ffb347' });
        this.endAt = Math.max(this.endAt, this.cursor + 450);
        this.cursor += 220; break;
      }
      case 'damage': {
        const t = this.cursor;
        this.at(t, () => {
          const u = this.uname(e.uid); if (!u) return;
          this.hpShown.set(e.uid, Math.max(0, (this.hpShown.get(e.uid) ?? u.hp) - e.amount));
          this.flashUntil.set(e.uid, t + 220);
          const p = this.unitPos(u, t);
          this.floatAt(p, `-${e.amount}`, '#ff5d4d', performance.now());
        });
        break;
      }
      case 'heal': {
        const t = this.cursor;
        this.at(t, () => {
          const u = this.uname(e.uid); if (!u) return;
          this.hpShown.set(e.uid, (this.hpShown.get(e.uid) ?? u.hp) + e.amount);
          this.floatAt(this.unitPos(u, t), `+${e.amount}`, '#6fe08a', performance.now());
        });
        break;
      }
      case 'revive': {
        const t = this.cursor + 200;
        this.at(t, () => {
          const u = this.uname(e.uid); if (!u) return;
          this.hpShown.set(e.uid, e.hp);
          this.popStart.set(e.uid, t);
          this.floatAt(this.unitPos(u, t), 'Revived!', '#ffe27a', performance.now());
        });
        this.cursor = t + 200; this.endAt = Math.max(this.endAt, this.cursor); break;
      }
      case 'status': {
        const t = this.cursor;
        const name = g.content.statuses[e.status]?.name ?? e.status;
        this.at(t, () => { const u = this.uname(e.uid); if (u) this.floatAt(this.unitPos(u, t), name, '#c79bff', performance.now()); });
        break;
      }
      case 'death': {
        const t = this.cursor + 220;
        this.pendingDeath.add(e.uid);
        this.at(t, () => { this.pendingDeath.delete(e.uid); this.dying.set(e.uid, t); });
        this.endAt = Math.max(this.endAt, t + DEATH_MS);
        this.cursor = t; break;
      }
      case 'deploy': {
        const u = g.unit(e.uid);
        if (u) this.hpShown.set(e.uid, u.hp);
        this.pendingDeploy.add(e.uid);
        const t = this.cursor;
        this.at(t, () => { this.pendingDeploy.delete(e.uid); this.popStart.set(e.uid, t); });
        this.endAt = Math.max(this.endAt, t + POP_MS);
        break;
      }
      case 'spell': {
        this.rings.push({ pos: e.target, start: this.cursor, dur: 550, color: '#c79bff' });
        this.endAt = Math.max(this.endAt, this.cursor + 550);
        this.cursor += 300; break;
      }
      case 'equip': {
        const t = this.cursor;
        this.at(t, () => { const u = this.uname(e.uid); if (u) this.floatAt(this.unitPos(u, t), 'Equipped', '#ffe27a', performance.now()); });
        break;
      }
      case 'essence': {
        break; // handled by HUD
      }
      default: break;
    }
  }

  // ---------- drawing ----------
  private buildDrawables(now: number): Drawable[] {
    const g = this.game, v = this.view, out: Drawable[] = [];
    for (let y = 0; y < g.height; y++) for (let x = 0; x < g.width; x++) out.push({ d: v.depth(x, y), kind: 'tile', x, y });
    for (const u of g.units) {
      const visible = (u.alive || this.dying.has(u.uid) || this.pendingDeath.has(u.uid)) && !this.pendingDeploy.has(u.uid);
      if (!visible) continue;
      const p = this.unitPos(u, now);
      out.push({ d: v.depth(p.x, p.y) + 0.5, kind: 'unit', u, px: p.x, py: p.y, pz: p.z });
    }
    out.sort((a, b) => a.d - b.d);
    return out;
  }

  private frame(now: number) {
    // run due items, expire segments
    if (this.items.length) {
      const due = this.items.filter(i => i.start <= now);
      if (due.length) { this.items = this.items.filter(i => i.start > now); due.sort((a, b) => a.start - b.start).forEach(i => i.fn()); }
    }
    for (const [uid, l] of this.segs) {
      const rest = l.filter(s => s.start + s.dur > now);
      if (rest.length) this.segs.set(uid, rest); else this.segs.delete(uid);
    }
    for (const [uid, t] of this.dying) if (now - t > DEATH_MS) this.dying.delete(uid);
    this.floats = this.floats.filter(f => now - f.born < f.life);
    this.rings = this.rings.filter(r => now < r.start + r.dur);

    const ctx = this.ctx, g = this.game;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    ctx.setTransform(this.dpr * this.scale, 0, 0, this.dpr * this.scale, this.dpr * this.ox, this.dpr * this.oy);

    this.cachedDraw = this.buildDrawables(now);
    for (const dr of this.cachedDraw) {
      if (dr.kind === 'tile') this.drawTile(dr.x, dr.y, now);
      else this.drawUnit(dr, now);
    }
    // rings
    for (const r of this.rings) {
      if (now < r.start) continue;
      const p = (now - r.start) / r.dur;
      const t = g.tiles[r.pos.y]?.[r.pos.x]; if (!t) continue;
      const s = this.view.project(r.pos.x, r.pos.y, t.height);
      ctx.strokeStyle = rgba(r.color, 1 - p); ctx.lineWidth = 3;
      ctx.beginPath(); ctx.ellipse(s.sx, s.sy, 8 + p * 30, 4 + p * 15, 0, 0, Math.PI * 2); ctx.stroke();
    }
    // previews + floats on top
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    for (const [uid, pv] of this.overlay.previews) {
      const u = g.unit(uid); if (!u || !u.alive) continue;
      const p = this.unitPos(u, now), s = this.view.project(p.x, p.y, p.z);
      ctx.font = 'bold 13px system-ui, sans-serif';
      const w = ctx.measureText(pv.text).width + 12;
      const y = s.sy - 74;
      ctx.fillStyle = 'rgba(10,10,16,0.88)'; ctx.beginPath(); ctx.roundRect(s.sx - w / 2, y - 9, w, 18, 5); ctx.fill();
      ctx.strokeStyle = pv.color; ctx.lineWidth = 1.5; ctx.stroke();
      ctx.fillStyle = pv.color; ctx.fillText(pv.text, s.sx, y + 0.5);
    }
    for (const f of this.floats) {
      const k = (now - f.born) / f.life;
      ctx.globalAlpha = k < 0.7 ? 1 : 1 - (k - 0.7) / 0.3;
      ctx.font = 'bold 18px system-ui, sans-serif';
      ctx.lineWidth = 4; ctx.strokeStyle = 'rgba(0,0,0,0.85)';
      const y = f.y - k * 34;
      ctx.strokeText(f.text, f.x, y); ctx.fillStyle = f.color; ctx.fillText(f.text, f.x, y);
      ctx.globalAlpha = 1;
    }
  }

  private diamond(sx: number, sy: number, inset = 0) {
    const ctx = this.ctx, w = TW / 2 - inset * 2, h = TH / 2 - inset;
    ctx.beginPath(); ctx.moveTo(sx, sy - h); ctx.lineTo(sx + w, sy); ctx.lineTo(sx, sy + h); ctx.lineTo(sx - w, sy); ctx.closePath();
  }

  private drawTile(x: number, y: number, now: number) {
    const g = this.game, ctx = this.ctx, ov = this.overlay;
    const t = g.tiles[y][x], terr = g.content.terrain[t.terrain];
    const { sx, sy } = this.view.project(x, y, t.height);
    const th = t.height * LV + GROUND, hw = TW / 2, hh = TH / 2;
    const base = terr?.color ?? '#777';
    // sides
    ctx.fillStyle = shade(base, 0.68);
    ctx.beginPath(); ctx.moveTo(sx - hw, sy); ctx.lineTo(sx, sy + hh); ctx.lineTo(sx, sy + hh + th); ctx.lineTo(sx - hw, sy + th); ctx.closePath(); ctx.fill();
    ctx.fillStyle = shade(base, 0.48);
    ctx.beginPath(); ctx.moveTo(sx, sy + hh); ctx.lineTo(sx + hw, sy); ctx.lineTo(sx + hw, sy + th); ctx.lineTo(sx, sy + hh + th); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.35)'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(sx - hw, sy + th); ctx.lineTo(sx, sy + hh + th); ctx.lineTo(sx + hw, sy + th); ctx.moveTo(sx, sy + hh); ctx.lineTo(sx, sy + hh + th); ctx.stroke();
    // top
    this.diamond(sx, sy);
    ctx.fillStyle = base; ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.28)'; ctx.stroke();
    this.decorate(x, y, t.terrain, sx, sy, now);
    // well marker
    const well = g.map.wells?.find(w => w.x === x && w.y === y);
    if (well) {
      ctx.strokeStyle = '#8ee6ff'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.ellipse(sx, sy, 13, 6.5, 0, 0, Math.PI * 2); ctx.stroke();
      ctx.fillStyle = `rgba(142,230,255,${0.35 + 0.2 * Math.sin(now / 400)})`; ctx.fill();
      ctx.fillStyle = '#d8f6ff'; ctx.beginPath(); ctx.arc(sx, sy, 2.5, 0, Math.PI * 2); ctx.fill();
    }
    // highlights
    const k = key(x, y);
    const fillTop = (color: string, a: number, stroke?: string) => {
      this.diamond(sx, sy, 1); ctx.fillStyle = rgba(color, a); ctx.fill();
      if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = 1.5; ctx.stroke(); }
    };
    const pulse = 0.5 + 0.12 * Math.sin(now / 300);
    if (ov.deploy.has(k)) fillTop('#4cd964', pulse, 'rgba(160,255,170,0.9)');
    if (ov.reach.has(k)) fillTop('#3d8bff', 0.38, 'rgba(120,180,255,0.8)');
    if (ov.targets.has(k)) fillTop('#ff6a3d', pulse + 0.1, 'rgba(255,170,120,0.95)');
    if (ov.area.has(k)) fillTop('#ffe14d', 0.55, 'rgba(255,240,140,1)');
    const pi = ov.path.findIndex(p => p.x === x && p.y === y);
    if (pi >= 0) {
      fillTop('#9fd0ff', 0.45);
      ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(sx, sy, 3, 0, Math.PI * 2); ctx.fill();
      if (pi === ov.path.length - 1 && ov.pathCost !== null) {
        ctx.font = 'bold 12px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(0,0,0,0.8)';
        const txt = `${ov.pathCost} AP`; ctx.strokeText(txt, sx, sy - 14); ctx.fillStyle = '#fff'; ctx.fillText(txt, sx, sy - 14);
      }
    }
    if (ov.selected && ov.selected.x === x && ov.selected.y === y) { this.diamond(sx, sy, 1); ctx.strokeStyle = '#ffd86b'; ctx.lineWidth = 2.5; ctx.stroke(); }
    if (ov.hover && ov.hover.x === x && ov.hover.y === y) { this.diamond(sx, sy, 1); ctx.strokeStyle = 'rgba(255,255,255,0.95)'; ctx.lineWidth = 2; ctx.stroke(); }
  }

  private decorate(x: number, y: number, terrain: string, sx: number, sy: number, now: number) {
    const ctx = this.ctx, r = ((x * 73856093) ^ (y * 19349663)) >>> 0;
    if (terrain === 'forest') {
      for (let i = 0; i < 2; i++) {
        const ox = (i ? 11 : -10) + ((r >> i) & 3), oy = (i ? 2 : -2);
        ctx.fillStyle = '#2b4d2a'; ctx.beginPath(); ctx.moveTo(sx + ox, sy + oy - 16); ctx.lineTo(sx + ox + 7, sy + oy); ctx.lineTo(sx + ox - 7, sy + oy); ctx.closePath(); ctx.fill();
        ctx.fillStyle = '#4e8a45'; ctx.beginPath(); ctx.moveTo(sx + ox, sy + oy - 16); ctx.lineTo(sx + ox + 7, sy + oy); ctx.lineTo(sx + ox, sy + oy); ctx.closePath(); ctx.fill();
      }
    } else if (terrain === 'water') {
      ctx.strokeStyle = 'rgba(255,255,255,0.22)'; ctx.lineWidth = 1;
      const o = Math.sin(now / 700 + x + y) * 3;
      ctx.beginPath(); ctx.moveTo(sx - 12 + o, sy - 2); ctx.lineTo(sx - 2 + o, sy - 2); ctx.moveTo(sx + 2 - o, sy + 4); ctx.lineTo(sx + 12 - o, sy + 4); ctx.stroke();
    } else if (terrain === 'lava') {
      this.diamond(sx, sy, 6); ctx.fillStyle = `rgba(255,190,60,${0.35 + 0.25 * Math.sin(now / 350 + x)})`; ctx.fill();
    } else if (terrain === 'stone' && (r & 3) === 0) {
      ctx.fillStyle = 'rgba(0,0,0,0.12)'; ctx.fillRect(sx - 6, sy - 1, 8, 3);
    }
  }

  private drawUnit(d: Extract<Drawable, { kind: 'unit' }>, now: number) {
    const g = this.game, u = d.u, ov = this.overlay;
    const def = g.def(u);
    let { sx, sy } = this.view.project(d.px, d.py, d.pz);
    const bump = this.bumps.get(u.uid);
    if (bump) {
      if (now > bump.start + bump.dur) this.bumps.delete(u.uid);
      else if (now >= bump.start) { const k = Math.sin(Math.PI * (now - bump.start) / bump.dur); sx += bump.dx * k; sy += bump.dy * k; }
    }
    let alpha = 1;
    const dt = this.dying.get(u.uid);
    if (dt !== undefined) alpha = Math.max(0, 1 - (now - dt) / DEATH_MS);
    const ps = this.popStart.get(u.uid);
    let scale = 1;
    if (ps !== undefined) {
      const k = (now - ps) / POP_MS;
      if (k >= 1) this.popStart.delete(u.uid); else if (k >= 0) scale = 0.2 + 0.8 * (1 - Math.pow(1 - k, 3)) ;
    }
    const mine = u.team === g.current && g.phase === 'playing';
    const dim = mine && !def.structure && (u.ap <= 0 || u.summonedThisTurn);
    const fl = (this.flashUntil.get(u.uid) ?? 0) - now;
    drawUnitSprite(this.ctx, {
      def, hero: !!def.hero, teamColor: g.teams[u.team].color, x: sx, y: sy - (dt !== undefined ? (now - dt) / DEATH_MS * 6 : 0), alpha, dim,
      flash: Math.max(0, Math.min(1, fl / 220)),
      hp: this.hpShown.get(u.uid) ?? u.hp, maxHp: def.stats.hp,
      statuses: u.statuses.map(s => ({ id: s.id, name: g.content.statuses[s.id]?.name ?? s.id })),
      selected: !!ov.selected && ov.selected.x === u.x && ov.selected.y === u.y && !this.segs.has(u.uid),
      hovered: !!ov.hover && ov.hover.x === u.x && ov.hover.y === u.y,
      scale, time: now,
    });
  }

  // ---------- picking ----------
  /** Front-most tile under a CSS-pixel point (units first, then top faces, then cliff sides). */
  pick(cx: number, cy: number): Pos | null {
    const wx = (cx - this.ox) / this.scale, wy = (cy - this.oy) / this.scale;
    const g = this.game, now = performance.now();
    const list = this.cachedDraw.length ? this.cachedDraw : this.buildDrawables(now);
    for (let i = list.length - 1; i >= 0; i--) {
      const d = list[i];
      if (d.kind === 'unit') {
        if (!d.u.alive) continue;
        const s = this.view.project(d.px, d.py, d.pz);
        if (Math.abs(wx - s.sx) <= 14 && wy >= s.sy - 46 && wy <= s.sy + 4) return { x: d.u.x, y: d.u.y };
      } else {
        const t = g.tiles[d.y][d.x];
        const s = this.view.project(d.x, d.y, t.height);
        const dx = wx - s.sx, dy = wy - s.sy;
        if (Math.abs(dx) / (TW / 2) + Math.abs(dy) / (TH / 2) <= 1) return { x: d.x, y: d.y };
        const th = t.height * LV + GROUND;
        if (Math.abs(dx) <= TW / 2) {
          const edge = dx < 0 ? (TH / 2) * (dx + TW / 2) / (TW / 2) : (TH / 2) * (1 - dx / (TW / 2));
          if (dy >= edge && dy <= edge + th) return { x: d.x, y: d.y };
        }
      }
    }
    return null;
  }
}

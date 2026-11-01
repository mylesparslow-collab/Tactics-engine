import type { Game } from '../engine/game';
import { label } from '../engine/content';
import type { GameEvent, Pos, Tile, Unit } from '../engine/types';
import { GROUND, LV, TH, TW, View, key, mix, rgba } from './iso';
import { drawUnitSprite, figureHeight } from './sprites';
import { backdropFor, diamondPath, glowSprite } from './terrain';
import { BoardPainter, onTileArtReady, visualTiles, type AnimTile } from './board';
import { clipDuration, clipHitTime, frameFor, unitArt, type AnimState } from './anim';

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

const MS_PER_TILE = 150;
const DEATH_MS = 650;
const POP_MS = 420;
const HIT_MS = 280;

interface Seg { start: number; dur: number; path: Pos[]; arc: boolean }
interface Float { x: number; y: number; text: string; color: string; born: number; life: number; icon?: string }
interface Ring { pos: Pos; start: number; dur: number; color: string; rune?: boolean }
interface Bolt { from: Pos; to: Pos; start: number; dur: number; color: string }
interface Particle { x: number; y: number; vx: number; vy: number; born: number; life: number; color: string; size: number; g: number }
interface Item { start: number; fn: () => void }
interface Anim { state: AnimState; start: number; dur: number; impact: number; target?: Pos; ranged?: boolean }
type Drawable = { d: number; kind: 'tile'; x: number; y: number } | { d: number; kind: 'unit'; u: Unit; px: number; py: number; pz: number; facing: 1 | -1; hop: number };

export class Renderer {
  private ctx: CanvasRenderingContext2D;
  private game!: Game;
  private view!: View;
  overlay: Overlay = emptyOverlay();
  private scale = 1; private ox = 0; private oy = 0; private dpr = 1;
  private fitScale = 1; zoom = 1; private panX = 0; private panY = 0;
  /** CSS px of the stage covered by overlays at the bottom; the board is centred in what remains. */
  bottomInset = 0;
  private cssW = 0; private cssH = 0;
  private raf = 0;
  reduced = typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
  // board cache
  private board: HTMLCanvasElement | null = null;
  private boardK = 1; private boardX0 = 0; private boardY0 = 0; private boardDirty = true; private vt: Tile[][] = []; private artTimer: ReturnType<typeof setTimeout> | undefined;
  private animTiles: AnimTile[] = [];
  private painter!: BoardPainter;
  private seeds: Uint32Array = new Uint32Array(0);
  // animation state
  private cursor = 0; private endAt = 0;
  private segs = new Map<number, Seg[]>();
  private anims = new Map<number, Anim>();
  private facing = new Map<number, 1 | -1>();
  private hpShown = new Map<number, number>();
  private flashUntil = new Map<number, number>();
  private shake = new Map<number, number>();
  private pendingDeath = new Set<number>();
  private dying = new Map<number, number>();
  private pendingDeploy = new Set<number>();
  private popStart = new Map<number, number>();
  private floats: Float[] = [];
  private rings: Ring[] = [];
  private bolts: Bolt[] = [];
  private particles: Particle[] = [];
  private items: Item[] = [];
  private cachedDraw: Drawable[] = [];
  private lastFrame = 0;

  constructor(private canvas: HTMLCanvasElement) {
    this.ctx = canvas.getContext('2d')!;
  }

  setGame(game: Game) {
    this.game = game;
    this.view = new View(game.width, game.height);
    this.overlay = emptyOverlay();
    this.segs.clear(); this.anims.clear(); this.hpShown.clear(); this.flashUntil.clear(); this.shake.clear();
    this.pendingDeath.clear(); this.dying.clear(); this.pendingDeploy.clear(); this.popStart.clear(); this.facing.clear();
    this.floats = []; this.rings = []; this.bolts = []; this.particles = []; this.items = []; this.cursor = 0; this.endAt = 0;
    for (const u of game.units) this.hpShown.set(u.uid, u.hp);
    this.seeds = new Uint32Array(game.width * game.height);
    for (let y = 0; y < game.height; y++) for (let x = 0; x < game.width; x++) this.seeds[y * game.width + x] = (((x * 73856093) ^ (y * 19349663) ^ 0x5bd1e995) >>> 0);
    this.zoom = 1; this.panX = 0; this.panY = 0; this.userMoved = false;
    this.vt = visualTiles(game); this.painter = new BoardPainter(game, this.view, this.seeds, this.vt);
    onTileArtReady(() => { clearTimeout(this.artTimer); this.artTimer = setTimeout(() => { this.boardDirty = true; }, 120); });
    this.boardDirty = true;
    this.resize();
  }

  start() { const loop = () => { this.raf = requestAnimationFrame(loop); this.frame(performance.now()); }; this.raf = requestAnimationFrame(loop); }
  stop() { cancelAnimationFrame(this.raf); }

  get rotation() { return this.view.rot; }
  rotate(dir: 1 | -1) { this.view.rot = (this.view.rot + dir + 4) % 4; this.boardDirty = true; this.fit(); }
  /** Terrain changed under us: rebuild the static board layer. */
  invalidateBoard() { this.boardDirty = true; }

  resize() {
    const r = this.canvas.parentElement!.getBoundingClientRect();
    this.dpr = Math.min(window.devicePixelRatio || 1, 3);
    this.cssW = Math.max(100, r.width); this.cssH = Math.max(100, r.height);
    this.canvas.width = Math.round(this.cssW * this.dpr);
    this.canvas.height = Math.round(this.cssH * this.dpr);
    this.canvas.style.width = this.cssW + 'px'; this.canvas.style.height = this.cssH + 'px';
    if (this.game) { this.boardDirty = true; this.fit(); }
  }

  private bounds() {
    const v = this.view;
    let maxL = 0;
    for (const row of this.vt) for (const t of row) maxL = Math.max(maxL, t.height);
    const minX = -(v.rh - 1) * TW / 2 - TW / 2, maxX = (v.rw - 1) * TW / 2 + TW / 2;
    const minY = -TH / 2 - maxL * LV - 120, maxY = (v.rw + v.rh - 2) * TH / 2 + TH / 2 + GROUND + 10;
    return { minX, maxX, minY, maxY };
  }

  private fit() {
    const { minX, maxX, minY, maxY } = this.bounds();
    const bw = maxX - minX, bh = maxY - minY;
    this.fitScale = Math.max(0.12, Math.min(this.cssW / bw, this.cssH / bh, 1.6)) * 0.97;
    if (this.userMoved) this.applyView(); else this.defaultView();
  }
  /** Start view: close enough that about 14 tiles span the screen width, centred on the player's Beacon. */
  private defaultView() {
    const target = Math.min(1.1, this.cssW / ((this.cssW > 1000 ? 18 : 12) * TW));
    this.zoom = Math.max(1, Math.min(4, target / this.fitScale));
    this.panX = 0; this.panY = 0; this.applyView();
    const g = this.game, human = g.teams.findIndex(t => t.controller === 'human');
    const ks = g.units.find(u => u.alive && u.team === Math.max(0, human) && g.def(u).structure)
      ?? g.units.find(u => u.alive && u.team === Math.max(0, human));
    if (!ks) return;
    const p = this.view.project(ks.x, ks.y, this.vt[ks.y][ks.x].height);
    const sx = p.sx * this.scale + this.ox, sy = (p.sy - 40) * this.scale + this.oy;
    this.panX = this.cssW / 2 - sx; this.panY = (this.cssH - this.bottomInset) / 2 - sy;
    this.clampPan(); this.applyView();
  }
  private clampPan() {
    const lim = Math.max(this.cssW, this.cssH) * 0.9 * this.zoom;
    this.panX = Math.max(-lim, Math.min(lim, this.panX)); this.panY = Math.max(-lim, Math.min(lim, this.panY));
  }
  private userMoved = false;
  private applyView() {
    const { minX, maxX, minY, maxY } = this.bounds();
    const bw = maxX - minX, bh = maxY - minY;
    this.scale = this.fitScale * this.zoom;
    this.ox = this.cssW / 2 - (minX + bw / 2) * this.scale + this.panX;
    this.oy = (this.cssH - this.bottomInset) / 2 - (minY + bh / 2) * this.scale + this.panY;
    const need = Math.min(2.5, this.scale * this.dpr);
    if (this.board && need > this.boardK * 1.3) { clearTimeout(this.zoomTimer); this.zoomTimer = setTimeout(() => { this.boardDirty = true; }, 150); }
  }
  private zoomTimer: ReturnType<typeof setTimeout> | undefined;
  /** Pan by CSS pixels. */
  pan(dx: number, dy: number) {
    this.panX += dx; this.panY += dy; this.userMoved = true;
    this.clampPan(); this.applyView();
  }
  /** Multiply zoom, keeping the CSS point (cx,cy) fixed. */
  zoomBy(f: number, cx = this.cssW / 2, cy = this.cssH / 2) {
    const z0 = this.zoom; this.userMoved = true;
    this.zoom = Math.max(0.5, Math.min(Math.max(4, 2.6 / this.fitScale), this.zoom * f));
    const k = this.zoom / z0;
    const wx = (cx - this.ox), wy = (cy - this.oy);
    this.panX += (wx - wx * k) ; this.panY += (wy - wy * k);
    this.applyView();
  }
  resetView() { this.userMoved = false; this.defaultView(); }
  setBottomInset(px: number) { if (px !== this.bottomInset) { this.bottomInset = px; this.applyView(); } }

  // ---------- animation scheduling ----------
  busy() { return performance.now() < this.endAt; }

  private at(start: number, fn: () => void) { this.items.push({ start, fn }); this.endAt = Math.max(this.endAt, start); }
  private uname(uid: number) { return this.game.unit(uid); }
  private tileZ(p: Pos) { return this.game.tiles[Math.round(p.y)]?.[Math.round(p.x)]?.height ?? 0; }
  private floatAt(p: Pos, text: string, color: string, born: number, icon?: string) {
    const s = this.view.project(p.x, p.y, this.tileZ(p));
    const n = this.floats.filter(f => Math.abs(f.born - born) < 300 && Math.abs(f.x - s.sx) < 4 && Math.abs(f.y - s.sy) < 80).length;
    this.floats.push({ x: s.sx, y: s.sy - 96 - n * 18, text, color, born, life: 1200, icon });
  }
  private burst(p: Pos, n: number, color: string, opts: { up?: number; spread?: number; life?: number; size?: number; g?: number; rise?: boolean } = {}) {
    const s = this.view.project(p.x, p.y, this.tileZ(p)), now = performance.now();
    for (let i = 0; i < n; i++) {
      const a = Math.random() * Math.PI * 2, sp = (opts.spread ?? 40) * (0.4 + Math.random() * 0.6);
      this.particles.push({ x: s.sx + (Math.random() - 0.5) * 20, y: s.sy - (opts.rise ? Math.random() * 40 : 0), vx: Math.cos(a) * sp, vy: Math.sin(a) * sp * 0.5 - (opts.up ?? 40) * (0.5 + Math.random()),
        born: now, life: (opts.life ?? 700) * (0.6 + Math.random() * 0.6), color, size: (opts.size ?? 3) * (0.5 + Math.random()), g: opts.g ?? 80 });
    }
  }
  /** Where a unit is displayed at time `t` (honouring queued movement segments), with hop and facing. */
  private unitPos(u: Unit, t: number) {
    const segs = this.segs.get(u.uid);
    const hz = (p: Pos) => this.tileZ(p);
    let facing = this.facing.get(u.uid) ?? 1;
    if (segs) for (const s of segs) {
      if (t < s.start + s.dur) {
        const p = s.dur > 0 ? Math.max(0, Math.min(1, (t - s.start) / s.dur)) : 1;
        const n = s.path.length - 1;
        const f = p * n, i = Math.min(n - 1, Math.floor(f)), k = f - i;
        const a = s.path[i], b = s.path[i + 1];
        let z = hz(a) + (hz(b) - hz(a)) * k;
        if (s.arc) z += Math.sin(Math.PI * p) * 1.2;
        const sa = this.view.project(a.x, a.y), sb = this.view.project(b.x, b.y);
        if (Math.abs(sb.sx - sa.sx) > 1) { facing = sb.sx > sa.sx ? 1 : -1; this.facing.set(u.uid, facing); }
        const hop = this.reduced ? 0 : Math.abs(Math.sin(Math.PI * k)) * 7;
        return { x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k, z, facing, hop, moving: true };
      }
    }
    return { x: u.x, y: u.y, z: hz(u), facing, hop: 0, moving: false };
  }
  private faceToward(uid: number, from: Pos, to: Pos) {
    const a = this.view.project(from.x, from.y), b = this.view.project(to.x, to.y);
    if (Math.abs(b.sx - a.sx) > 1) this.facing.set(uid, b.sx > a.sx ? 1 : -1);
  }
  private setAnim(uid: number, state: AnimState, start: number, dur: number, extra: Partial<Anim> = {}) {
    this.anims.set(uid, { state, start, dur, impact: extra.impact ?? 0, ...extra });
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
        this.setAnim(e.uid, 'move', this.cursor, dur);
        this.cursor += dur; break;
      }
      case 'push': {
        push(e.uid, { start: this.cursor, dur: 220, path: [e.from, e.to], arc: false });
        const t = this.cursor;
        this.at(t, () => { this.shake.set(e.uid, t + 200); });
        this.cursor += 220; break;
      }
      case 'ability': {
        const u = g.unit(e.uid);
        const a = g.ability(e.ability);
        const t = this.cursor;
        const ranged = (a?.range.max ?? 1) > 1;
        const harmful = a?.effects.some(x => x.type === 'damage' || x.type === 'push' || x.type === 'pull') ?? true;
        const state: AnimState = harmful && a?.target !== 'ally' && a?.target !== 'self' ? 'attack' : 'cast';
        if (u) {
          const art = unitArt(u.defId, g.def(u));
          const clipDur = clipDuration(art, state);
          const hit = clipHitTime(art, state) ?? (state === 'cast' ? 380 : ranged ? 320 : 230);
          const dur = clipDur ?? (state === 'cast' ? 700 : 520);
          this.at(t, () => {
            this.faceToward(e.uid, u, e.target);
            this.setAnim(e.uid, state, t, dur, { impact: hit, target: e.target, ranged });
            if (ranged && state === 'attack') this.bolts.push({ from: { x: u.x, y: u.y }, to: e.target, start: t + hit * 0.35, dur: hit * 0.65, color: '#ffd37a' });
          });
          this.at(t + hit, () => {
            if (a?.area) { this.rings.push({ pos: e.target, start: t + hit, dur: 520, color: state === 'cast' ? '#9fe3ff' : '#ffb347' }); this.burst(e.target, 14, state === 'cast' ? '#bfeeff' : '#ffb347', { up: 60, spread: 70, life: 600 }); }
            else this.rings.push({ pos: e.target, start: t + hit, dur: 380, color: state === 'cast' ? '#9fe3ff' : '#ffb347' });
          });
          this.endAt = Math.max(this.endAt, t + dur);
          this.cursor = t + hit;
        } else {
          this.rings.push({ pos: e.target, start: t, dur: 450, color: '#ffb347' });
          this.cursor += 220;
        }
        break;
      }
      case 'damage': {
        const t = this.cursor;
        this.at(t, () => {
          const u = this.uname(e.uid); if (!u) return;
          this.hpShown.set(e.uid, Math.max(0, (this.hpShown.get(e.uid) ?? u.hp) - e.amount));
          this.flashUntil.set(e.uid, t + 220);
          this.shake.set(e.uid, t + 260);
          const art = unitArt(u.defId, g.def(u));
          this.setAnim(e.uid, 'hit', t, clipDuration(art, 'hit') ?? HIT_MS);
          const p = this.unitPos(u, t);
          this.floatAt(p, `-${e.amount}`, '#ff5d4d', performance.now());
          this.burst(p, 6, '#ff8a6a', { up: 50, spread: 50, life: 450, size: 2.5 });
        });
        this.endAt = Math.max(this.endAt, t + HIT_MS);
        break;
      }
      case 'heal': {
        const t = this.cursor;
        this.at(t, () => {
          const u = this.uname(e.uid); if (!u) return;
          this.hpShown.set(e.uid, (this.hpShown.get(e.uid) ?? u.hp) + e.amount);
          this.floatAt(this.unitPos(u, t), `+${e.amount}`, '#6fe08a', performance.now());
          this.burst(u, 12, '#8ff0a0', { up: 70, spread: 18, life: 900, size: 2.5, g: -20, rise: true });
        });
        break;
      }
      case 'revive': {
        const t = this.cursor + 200;
        this.at(t, () => {
          const u = this.uname(e.uid); if (!u) return;
          this.hpShown.set(e.uid, e.hp);
          this.popStart.set(e.uid, t);
          this.anims.delete(e.uid);
          this.floatAt(this.unitPos(u, t), 'Revived!', '#ffe27a', performance.now());
          this.burst(u, 16, '#ffe9a0', { up: 60, spread: 40, life: 800, size: 3 });
        });
        this.cursor = t + 200; this.endAt = Math.max(this.endAt, this.cursor); break;
      }
      case 'status': {
        const t = this.cursor;
        const name = g.content.statuses[e.status]?.name ?? e.status;
        this.at(t, () => { const u = this.uname(e.uid); if (u) this.floatAt(this.unitPos(u, t), name, '#c79bff', performance.now(), e.status); });
        break;
      }
      case 'death': {
        const t = this.cursor + 180;
        this.pendingDeath.add(e.uid);
        this.at(t, () => {
          this.pendingDeath.delete(e.uid); this.dying.set(e.uid, t);
          const u = this.uname(e.uid);
          if (u) {
            const art = unitArt(u.defId, g.def(u));
            this.setAnim(e.uid, 'death', t, clipDuration(art, 'death') ?? DEATH_MS);
            this.burst(u, 14, mix(g.teams[u.team].color, '#ffffff', 0.5), { up: 30, spread: 45, life: 900, size: 3, g: 30 });
            this.burst(u, 10, '#c9c2b0', { up: 20, spread: 30, life: 1100, size: 4, g: 10 });
          }
        });
        this.endAt = Math.max(this.endAt, t + DEATH_MS);
        this.cursor = t; break;
      }
      case 'deploy': {
        const u = g.unit(e.uid);
        if (u) this.hpShown.set(e.uid, u.hp);
        this.pendingDeploy.add(e.uid);
        const t = this.cursor;
        this.at(t, () => {
          this.pendingDeploy.delete(e.uid); this.popStart.set(e.uid, t);
          if (u) { this.burst(u, 18, '#7fe0dc', { up: 90, spread: 55, life: 700, size: 3 }); this.rings.push({ pos: u, start: t, dur: 500, color: '#9fe8e4' }); }
        });
        this.endAt = Math.max(this.endAt, t + POP_MS);
        break;
      }
      case 'spell': {
        const t = this.cursor;
        this.rings.push({ pos: e.target, start: t, dur: 700, color: '#c79bff', rune: true });
        this.at(t + 300, () => this.burst(e.target, 16, '#d8b8ff', { up: 70, spread: 60, life: 700, size: 3 }));
        this.endAt = Math.max(this.endAt, t + 700);
        this.cursor += 360; break;
      }
      case 'equip': {
        const t = this.cursor;
        this.at(t, () => { const u = this.uname(e.uid); if (u) { this.floatAt(this.unitPos(u, t), 'Equipped', '#ffe27a', performance.now()); this.burst(u, 8, '#ffe9a0', { up: 50, spread: 20, life: 700, size: 2.5, g: -10, rise: true }); } });
        break;
      }
      case 'terrain': { this.boardDirty = true; break; }
      case 'essence': { // HUD shows totals; a well payout also pops over the well
        if (e.at) { const at = e.at, t = this.cursor; this.at(t, () => { this.floatAt(at, `+${e.amount} ${label(this.game.content, 'essence')}`, '#7fe0ff', performance.now()); this.burst(at, 12, '#9fe8ff', { up: 70, spread: 18, life: 900, size: 2.5, g: -20, rise: true }); }); this.cursor += 250; }
        break;
      }
      default: break;
    }
  }

  // ---------- board cache ----------
  private buildBoard() {
    visualTiles(this.game, this.vt);
    const { minX, maxX, minY, maxY } = this.bounds();
    const want = Math.min(2.5, Math.max(0.5, this.scale * this.dpr));
    const k = Math.min(want, Math.sqrt(12_000_000 / Math.max(1, (maxX - minX) * (maxY - minY)))); // stay under ~12 MP (mobile canvas limits)
    const W = Math.ceil((maxX - minX) * k), H = Math.ceil((maxY - minY) * k);
    if (!this.board || this.board.width !== W || this.board.height !== H) { this.board = document.createElement('canvas'); this.board.width = W; this.board.height = H; }
    const ctx = this.board.getContext('2d')!;
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, W, H);
    ctx.setTransform(k, 0, 0, k, -minX * k, -minY * k);
    this.boardK = k; this.boardX0 = minX; this.boardY0 = minY;
    this.animTiles = this.painter.paint(ctx, minY, maxY);
    this.boardDirty = false;
  }

  // ---------- drawing ----------
  private buildDrawables(now: number): Drawable[] {
    const g = this.game, v = this.view, out: Drawable[] = [];
    for (let y = 0; y < g.height; y++) for (let x = 0; x < g.width; x++) out.push({ d: v.depth(x, y), kind: 'tile', x, y });
    for (const u of g.units) {
      const visible = (u.alive || this.dying.has(u.uid) || this.pendingDeath.has(u.uid)) && !this.pendingDeploy.has(u.uid);
      if (!visible) continue;
      const p = this.unitPos(u, now);
      out.push({ d: v.depth(p.x, p.y) + 0.5, kind: 'unit', u, px: p.x, py: p.y, pz: p.z, facing: p.facing, hop: p.hop });
    }
    out.sort((a, b) => a.d - b.d);
    return out;
  }

  private frame(now: number) {
    const dt = Math.min(50, now - (this.lastFrame || now)); this.lastFrame = now;
    // run due items, expire segments
    if (this.items.length) {
      const due = this.items.filter(i => i.start <= now);
      if (due.length) { this.items = this.items.filter(i => i.start > now); due.sort((a, b) => a.start - b.start).forEach(i => i.fn()); }
    }
    for (const [uid, l] of this.segs) {
      const rest = l.filter(s => s.start + s.dur > now);
      if (rest.length) this.segs.set(uid, rest); else this.segs.delete(uid);
    }
    for (const [uid, a] of this.anims) if (a.state !== 'death' && now > a.start + a.dur) this.anims.delete(uid);
    for (const [uid, t] of this.dying) if (now - t > DEATH_MS + 400) { this.dying.delete(uid); this.anims.delete(uid); }
    this.floats = this.floats.filter(f => now - f.born < f.life);
    this.rings = this.rings.filter(r => now < r.start + r.dur);
    this.bolts = this.bolts.filter(b => now < b.start + b.dur);
    if (this.particles.length) {
      const s = dt / 1000;
      this.particles = this.particles.filter(p => now - p.born < p.life);
      for (const p of this.particles) { p.x += p.vx * s; p.y += p.vy * s; p.vy += p.g * s; p.vx *= 0.98; }
    }
    if (this.boardDirty) this.buildBoard();

    const ctx = this.ctx, g = this.game;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.drawImage(backdropFor(this.canvas.width, this.canvas.height), 0, 0);
    this.drawBeam(ctx, now);
    ctx.setTransform(this.dpr * this.scale, 0, 0, this.dpr * this.scale, this.dpr * this.ox, this.dpr * this.oy);
    // board shadow + cached static layer
    const b = this.board!;
    ctx.drawImage(b, this.boardX0, this.boardY0, b.width / this.boardK, b.height / this.boardK);
    for (const t of this.animTiles) this.animateTile(t, now);
    this.drawOverlays(now);

    this.cachedDraw = this.buildDrawables(now);
    const units = this.cachedDraw.filter((d): d is Extract<Drawable, { kind: 'unit' }> => d.kind === 'unit');
    for (const dr of units) {
      this.drawUnit(dr, now);
      this.reoccludeAround(dr);
    }
    // bolts
    for (const bt of this.bolts) {
      if (now < bt.start) continue;
      const p = Math.min(1, (now - bt.start) / bt.dur);
      const a = this.view.project(bt.from.x, bt.from.y, this.tileZ(bt.from)), c = this.view.project(bt.to.x, bt.to.y, this.tileZ(bt.to));
      const x = a.sx + (c.sx - a.sx) * p, y = a.sy - 50 + (c.sy - 40 - (a.sy - 50)) * p - Math.sin(Math.PI * p) * 40;
      ctx.save(); ctx.shadowColor = bt.color; ctx.shadowBlur = 12; ctx.fillStyle = bt.color;
      ctx.beginPath(); ctx.ellipse(x, y, 7, 3.5, Math.atan2(c.sy - a.sy, c.sx - a.sx), 0, Math.PI * 2); ctx.fill();
      ctx.restore();
    }
    // rings
    for (const r of this.rings) {
      if (now < r.start) continue;
      const p = (now - r.start) / r.dur;
      const t = this.vt[r.pos.y]?.[r.pos.x]; if (!t) continue;
      const s = this.view.project(r.pos.x, r.pos.y, t.height);
      ctx.save(); ctx.translate(s.sx, s.sy); ctx.scale(1, 0.5);
      if (r.rune) {
        ctx.globalAlpha = p < 0.7 ? 1 : 1 - (p - 0.7) / 0.3;
        ctx.strokeStyle = r.color; ctx.lineWidth = 2.5; ctx.shadowColor = r.color; ctx.shadowBlur = 14;
        ctx.beginPath(); ctx.arc(0, 0, 50, 0, Math.PI * 2); ctx.stroke();
        ctx.setLineDash([5, 7]); ctx.lineDashOffset = -now / 12; ctx.beginPath(); ctx.arc(0, 0, 40, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]);
        ctx.rotate(now / 900); ctx.beginPath(); for (let i = 0; i < 4; i++) { const a = i * Math.PI / 2; ctx.moveTo(Math.cos(a) * 50, Math.sin(a) * 50); ctx.lineTo(Math.cos(a + Math.PI / 2) * 50, Math.sin(a + Math.PI / 2) * 50); } ctx.stroke();
        const fg = ctx.createRadialGradient(0, 0, 0, 0, 0, 50); fg.addColorStop(0, rgba(r.color, 0.4 * (1 - p))); fg.addColorStop(1, rgba(r.color, 0));
        ctx.fillStyle = fg; ctx.beginPath(); ctx.arc(0, 0, 50, 0, Math.PI * 2); ctx.fill();
      } else {
        ctx.strokeStyle = rgba(r.color, 1 - p); ctx.lineWidth = 3; ctx.shadowColor = r.color; ctx.shadowBlur = 10;
        ctx.beginPath(); ctx.arc(0, 0, 14 + p * 54, 0, Math.PI * 2); ctx.stroke();
        const fg = ctx.createRadialGradient(0, 0, 0, 0, 0, 60); fg.addColorStop(0, rgba(r.color, 0.35 * (1 - p))); fg.addColorStop(1, rgba(r.color, 0));
        ctx.fillStyle = fg; ctx.beginPath(); ctx.arc(0, 0, 60, 0, Math.PI * 2); ctx.fill();
      }
      ctx.restore();
    }
    // particles
    for (const p of this.particles) {
      const k = (now - p.born) / p.life;
      ctx.globalAlpha = 1 - k * k; ctx.fillStyle = p.color;
      ctx.beginPath(); ctx.arc(p.x, p.y, p.size * (1 - k * 0.5), 0, Math.PI * 2); ctx.fill();
    }
    ctx.globalAlpha = 1;
    // previews + floats on top
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    for (const [uid, pv] of this.overlay.previews) {
      const u = g.unit(uid); if (!u || !u.alive) continue;
      const p = this.unitPos(u, now), s = this.view.project(p.x, p.y, p.z);
      ctx.font = 'bold 15px Cinzel, Georgia, serif';
      const w = ctx.measureText(pv.text).width + 16;
      const y = s.sy - 128;
      ctx.fillStyle = 'rgba(10,10,16,0.88)'; ctx.beginPath(); ctx.roundRect(s.sx - w / 2, y - 11, w, 22, 6); ctx.fill();
      ctx.strokeStyle = pv.color; ctx.lineWidth = 1.5; ctx.stroke();
      ctx.fillStyle = pv.color; ctx.fillText(pv.text, s.sx, y + 1);
    }
    for (const f of this.floats) {
      const k = (now - f.born) / f.life;
      ctx.globalAlpha = k < 0.7 ? 1 : 1 - (k - 0.7) / 0.3;
      const sc = k < 0.15 ? 0.6 + k / 0.15 * 0.5 : 1.1 - Math.min(0.1, (k - 0.15));
      ctx.font = `bold ${Math.round(22 * sc)}px Cinzel, Georgia, serif`;
      ctx.lineWidth = 4; ctx.strokeStyle = 'rgba(0,0,0,0.85)';
      const y = f.y - k * 40;
      ctx.strokeText(f.text, f.x, y); ctx.fillStyle = f.color; ctx.fillText(f.text, f.x, y);
      ctx.globalAlpha = 1;
    }
    this.drawWellHint(ctx);
  }

  /** Hovering a well explains it: who holds it and what it pays. */
  private drawWellHint(ctx: CanvasRenderingContext2D) {
    const h = this.overlay.hover, g = this.game; if (!h) return;
    const w = g.map.wells?.find(q => q.x === h.x && q.y === h.y); if (!w) return;
    const tide = label(g.content, 'essence'), holder = g.unitAt(w.x, w.y);
    const owner = holder && !g.def(holder).structure ? g.teams[holder.team] : undefined;
    const l1 = `${tide} Well  +${w.amount ?? 10} ${tide} per turn`;
    const l2 = owner ? `Held by ${owner.name}` : 'Stand a unit here at the start of your turn';
    const wp = this.view.project(w.x, w.y, this.vt[w.y][w.x].height);
    const s = { sx: wp.sx * this.scale + this.ox, sy: wp.sy * this.scale + this.oy + 118 - 56 - 30 * this.scale }; // CSS px, sits above the tile
    ctx.save(); ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0); ctx.font = '600 15px Alegreya, Georgia, serif';
    const tw = Math.max(ctx.measureText(l1).width, ctx.measureText(l2).width) + 24, th = 48, x = s.sx - tw / 2, y = s.sy - 118;
    ctx.fillStyle = 'rgba(12,14,22,0.92)'; ctx.strokeStyle = '#b8913e'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.roundRect(x, y, tw, th, 6); ctx.fill(); ctx.stroke();
    ctx.textAlign = 'center'; ctx.fillStyle = '#9fe8ff'; ctx.fillText(l1, s.sx, y + 20);
    ctx.font = 'italic 13px Alegreya, Georgia, serif'; ctx.fillStyle = owner ? owner.color : '#cbbfa6'; ctx.fillText(l2, s.sx, y + 39);
    ctx.restore();
  }

  /** A slow lighthouse beam sweeping the backdrop. */
  private drawBeam(ctx: CanvasRenderingContext2D, now: number) {
    if (this.reduced) return;
    const W = this.canvas.width, H = this.canvas.height;
    const a = -0.9 + Math.sin(now / 9000) * 0.5;
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.translate(W * 0.15, -H * 0.1); ctx.rotate(a);
    const g = ctx.createLinearGradient(0, 0, 0, H * 2);
    g.addColorStop(0, 'rgba(255,225,160,0.10)'); g.addColorStop(1, 'rgba(255,225,160,0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(-10, 0); ctx.lineTo(10, 0); ctx.lineTo(W * 0.35, H * 2); ctx.lineTo(-W * 0.25, H * 2); ctx.closePath(); ctx.fill();
    ctx.restore();
  }

  private animateTile(at: AnimTile, now: number) {
    const { x, y, kind } = at;
    const ctx = this.ctx, g = this.game, t = this.vt[y][x];
    if (at.frames?.length) {
      const img = at.frames[Math.floor(now / 400) % at.frames.length];
      const { sx, sy } = this.view.project(x, y, t.height);
      const s = TW / img.naturalWidth;
      ctx.drawImage(img, sx - TW / 2, sy + TH / 2 - img.naturalHeight * s, TW, img.naturalHeight * s);
    }
    const { sx, sy } = this.view.project(x, y, t.height);
    const well = g.map.wells?.find(w => w.x === x && w.y === y);
    const ph = (x * 1.7 + y * 2.3);
    if (!this.reduced && !at.frames) {
      if (kind === 'water' || kind === 'deepwater') {
        ctx.save(); diamondPath(ctx, sx, sy, 2); ctx.clip();
        const k = kind === 'water' ? 0.5 : 0.22;
        ctx.strokeStyle = `rgba(255,255,255,${0.28 * k + 0.1 * k * Math.sin(now / 500 + ph)})`; ctx.lineWidth = 1.5;
        for (let i = 0; i < 3; i++) {
          const o = Math.sin(now / 900 + ph + i * 2) * 10, yy = sy - 14 + i * 12;
          ctx.beginPath(); ctx.moveTo(sx - 30 + o, yy); ctx.quadraticCurveTo(sx - 10 + o, yy - 3, sx + 10 + o, yy); ctx.quadraticCurveTo(sx + 20 + o, yy + 2, sx + 32 + o, yy - 1); ctx.stroke();
        }
        const gx = sx - 18 + Math.sin(now / 1500 + ph) * 14, gy = sy - 6 + Math.cos(now / 1900 + ph) * 6;
        const gr = ctx.createRadialGradient(gx, gy, 0, gx, gy, 26);
        gr.addColorStop(0, `rgba(255,255,255,${0.22 * k + 0.12 * k * Math.sin(now / 400 + ph)})`); gr.addColorStop(1, 'rgba(255,255,255,0)');
        ctx.fillStyle = gr; ctx.fillRect(sx - 64, sy - 32, 128, 64);
        ctx.restore();
      } else if (kind === 'glow') {
        ctx.save(); diamondPath(ctx, sx, sy, 3); ctx.clip();
        const gr = ctx.createRadialGradient(sx, sy, 2, sx, sy, 60);
        const a = 0.28 + 0.18 * Math.sin(now / 350 + ph);
        gr.addColorStop(0, `rgba(255,200,90,${a})`); gr.addColorStop(1, 'rgba(255,120,30,0)');
        ctx.fillStyle = gr; ctx.fillRect(sx - 64, sy - 32, 128, 64); ctx.restore();
        ctx.save(); ctx.globalCompositeOperation = 'lighter';
        const hg = ctx.createRadialGradient(sx, sy, 10, sx, sy, 80); hg.addColorStop(0, `rgba(255,150,50,${0.12 + 0.06 * Math.sin(now / 420 + ph)})`); hg.addColorStop(1, 'rgba(255,150,50,0)');
        ctx.fillStyle = hg; ctx.fillRect(sx - 80, sy - 60, 160, 120); ctx.restore();
      } else if (kind === 'coral') {
        ctx.save(); diamondPath(ctx, sx, sy, 3); ctx.clip();
        const a = 0.10 + 0.08 * Math.sin(now / 1200 + ph);
        const gr = ctx.createRadialGradient(sx + 8, sy - 4, 0, sx + 8, sy - 4, 40);
        gr.addColorStop(0, `rgba(255,190,200,${a})`); gr.addColorStop(1, 'rgba(255,190,200,0)');
        ctx.fillStyle = gr; ctx.fillRect(sx - 64, sy - 32, 128, 64); ctx.restore();
      } else if (kind === 'trench') {
        const a = 0.25 + 0.2 * Math.sin(now / 1400 + ph);
        ctx.fillStyle = `rgba(63,209,196,${a})`; ctx.beginPath(); ctx.arc(sx + Math.sin(ph) * 10, sy + 4, 1.5, 0, Math.PI * 2); ctx.fill();
      }
    }
    if (well) {
      ctx.save(); ctx.translate(sx, sy); ctx.scale(1, 0.5);
      const pulse = this.reduced ? 0.5 : 0.5 + 0.2 * Math.sin(now / 400 + ph);
      const gr = ctx.createRadialGradient(0, 0, 2, 0, 0, 34);
      gr.addColorStop(0, `rgba(160,240,255,${0.55 * pulse + 0.2})`); gr.addColorStop(0.6, `rgba(100,210,230,${0.25 * pulse})`); gr.addColorStop(1, 'rgba(100,210,230,0)');
      ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(0, 0, 34, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = 'rgba(190,245,255,0.9)'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.arc(0, 0, 22, 0, Math.PI * 2); ctx.stroke();
      ctx.strokeStyle = 'rgba(190,245,255,0.5)'; ctx.lineWidth = 1; ctx.setLineDash([4, 6]); ctx.lineDashOffset = this.reduced ? 0 : -now / 30; ctx.beginPath(); ctx.arc(0, 0, 30, 0, Math.PI * 2); ctx.stroke();
      ctx.restore();
      ctx.fillStyle = '#e8fbff'; ctx.beginPath(); ctx.arc(sx, sy - 2, 3, 0, Math.PI * 2); ctx.fill();
    }
  }

  private drawOverlays(now: number) {
    const ov = this.overlay, ctx = this.ctx;
    const pulse = this.reduced ? 0.8 : 0.72 + 0.18 * Math.sin(now / 300);
    const glow = (k: string, color: string, strength: number) => {
      const [x, y] = k.split(',').map(Number);
      const t = this.vt[y]?.[x]; if (!t) return;
      const { sx, sy } = this.view.project(x, y, t.height);
      const s = glowSprite(color, strength);
      ctx.drawImage(s, sx - s.width / 4, sy - s.height / 4, s.width / 2, s.height / 2);
    };
    for (const k of ov.deploy) glow(k, '#4cd964', pulse);
    for (const k of ov.reach) glow(k, '#4aa3ff', 0.8);
    for (const k of ov.targets) glow(k, '#ff6a3d', pulse + 0.1);
    for (const k of ov.area) glow(k, '#ffe14d', 0.9);
    ov.path.forEach((p, pi) => {
      const t = this.vt[p.y]?.[p.x]; if (!t) return;
      const { sx, sy } = this.view.project(p.x, p.y, t.height);
      if (pi > 0) {
        const q = ov.path[pi - 1], tq = this.vt[q.y][q.x], a = this.view.project(q.x, q.y, tq.height);
        ctx.strokeStyle = 'rgba(220,240,255,0.85)'; ctx.lineWidth = 3; ctx.setLineDash([8, 6]); ctx.lineDashOffset = this.reduced ? 0 : -now / 40;
        ctx.beginPath(); ctx.moveTo(a.sx, a.sy); ctx.lineTo(sx, sy); ctx.stroke(); ctx.setLineDash([]);
      }
      ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(sx, sy, 4, 0, Math.PI * 2); ctx.fill();
      if (pi === ov.path.length - 1 && ov.pathCost !== null) {
        ctx.font = 'bold 15px Cinzel, Georgia, serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.lineWidth = 4; ctx.strokeStyle = 'rgba(0,0,0,0.85)';
        const txt = `${ov.pathCost} AP`; ctx.strokeText(txt, sx, sy - 22); ctx.fillStyle = '#fff'; ctx.fillText(txt, sx, sy - 22);
      }
    });
    const outline = (p: Pos, color: string, lw: number) => {
      const t = this.vt[p.y]?.[p.x]; if (!t) return;
      const { sx, sy } = this.view.project(p.x, p.y, t.height);
      ctx.save(); ctx.shadowColor = color; ctx.shadowBlur = 10; ctx.strokeStyle = color; ctx.lineWidth = lw; diamondPath(ctx, sx, sy, 2); ctx.stroke(); ctx.restore();
    };
    if (ov.selected) outline(ov.selected, '#ffd86b', 3);
    if (ov.hover) outline(ov.hover, 'rgba(255,255,255,0.95)', 2);
  }

  /** Redraw taller tiles in front of a unit so cliffs occlude it correctly (the board layer is static). */
  private reoccludeAround(d: Extract<Drawable, { kind: 'unit' }>) {
    const g = this.game, v = this.view, ctx = this.ctx;
    const ux = Math.round(d.px), uy = Math.round(d.py), depth = v.depth(d.px, d.py);
    const s = v.project(d.px, d.py, d.pz);
    const top = s.sy - 130, left = s.sx - 50, right = s.sx + 50;
    for (let dy = -3; dy <= 3; dy++) for (let dx = -3; dx <= 3; dx++) {
      const x = ux + dx, y = uy + dy;
      if (!g.inBounds(x, y) || (dx === 0 && dy === 0)) continue;
      const t = this.vt[y][x];
      if (v.depth(x, y) <= depth || t.height <= Math.floor(d.pz + 0.01)) continue;
      const ts = v.project(x, y, t.height);
      const th = t.height * LV + GROUND;
      if (ts.sx + TW / 2 < left || ts.sx - TW / 2 > right || ts.sy - TH / 2 > s.sy + 10 || ts.sy + TH / 2 + th < top) continue;
      this.painter.drawTile(ctx, x, y);
    }
  }

  private drawUnit(d: Extract<Drawable, { kind: 'unit' }>, now: number) {
    const g = this.game, u = d.u, ov = this.overlay;
    const def = g.def(u);
    let { sx, sy } = this.view.project(d.px, d.py, d.pz);
    const art = unitArt(u.defId, def);
    const an = this.anims.get(u.uid);
    const state: AnimState = an?.state ?? 'idle';
    const el = an ? now - an.start : now + u.uid * 173;
    let squash = 1, tilt = 0, lift = d.hop, glow = 0, alpha = 1, scale = 1;
    // procedural layer
    if (!this.reduced && !def.structure) {
      if (state === 'idle') { squash = 1 + Math.sin(now / 700 + u.uid * 1.3) * 0.018; sx += Math.sin(now / 1100 + u.uid) * 0.8; }
      else if (state === 'move') squash = 1 + Math.sin(now / 90) * 0.04;
    }
    if (an && (state === 'attack' || state === 'cast')) {
      const k = Math.min(1, el / Math.max(1, an.impact));
      if (state === 'attack' && an.target) {
        const b = this.view.project(an.target.x, an.target.y, this.tileZ(an.target));
        const dx = b.sx - sx, dy = b.sy - sy, len = Math.hypot(dx, dy) || 1;
        const m = an.ranged ? -8 : 22;
        // wind-up back, then lunge to impact, then settle
        const f = el <= an.impact ? (k < 0.45 ? -0.35 * (k / 0.45) : -0.35 + 1.35 * ((k - 0.45) / 0.55)) : Math.max(0, 1 - (el - an.impact) / (an.dur - an.impact || 1));
        sx += dx / len * m * f; sy += dy / len * m * 0.5 * f;
        squash *= 1 + 0.08 * Math.max(0, f);
      } else {
        glow = el < an.impact ? k : Math.max(0, 1 - (el - an.impact) / 300);
        lift += glow * 4;
      }
    }
    if (an && state === 'hit' && !this.reduced) {
      const k = el / an.dur;
      squash *= 1 - 0.12 * Math.sin(Math.PI * Math.min(1, k));
    }
    const sh = this.shake.get(u.uid);
    if (sh !== undefined) { if (now > sh) this.shake.delete(u.uid); else if (!this.reduced) { const r = (sh - now) / 260; sx += Math.sin(now / 18) * 5 * r; } }
    const dt = this.dying.get(u.uid);
    if (dt !== undefined) {
      const k = Math.min(1, (now - dt) / DEATH_MS);
      const frames = art.clips.death;
      alpha = frames ? Math.max(0, 1 - Math.max(0, (now - dt - (clipDuration(art, 'death') ?? 0))) / 400) : Math.max(0, 1 - k);
      if (!frames) { tilt = (u.uid % 2 ? 1 : -1) * 0.55 * k * k; sy += 10 * k; }
    }
    const ps = this.popStart.get(u.uid);
    if (ps !== undefined) {
      const k = (now - ps) / POP_MS;
      if (k >= 1) this.popStart.delete(u.uid); else if (k >= 0) { const e = 1 - Math.pow(1 - k, 3); scale = 0.3 + 0.7 * e; lift += (1 - e) * 30; alpha *= Math.min(1, k * 2); }
    }
    const mine = u.team === g.current && g.phase === 'playing';
    const dim = mine && !def.structure && (u.ap <= 0 || u.summonedThisTurn);
    const fl = (this.flashUntil.get(u.uid) ?? 0) - now;
    const frame = frameFor(art, state, el, !!def.structure);
    const hpNow = this.hpShown.get(u.uid) ?? u.hp;
    drawUnitSprite(this.ctx, {
      def, hero: !!def.hero, teamColor: g.teams[u.team].color, factionColor: def.faction ? g.content.factions?.[def.faction]?.color : undefined,
      x: sx, y: sy, alpha, dim,
      flash: Math.max(0, Math.min(1, fl / 220)),
      hp: hpNow, maxHp: def.stats.hp,
      statuses: u.statuses.map(s => ({ id: s.id, name: g.content.statuses[s.id]?.name ?? s.id })),
      selected: !!ov.selected && ov.selected.x === u.x && ov.selected.y === u.y && !this.segs.has(u.uid),
      hovered: !!ov.hover && ov.hover.x === u.x && ov.hover.y === u.y,
      scale, time: now, frame, facing: d.facing, squash, tilt, lift, glow,
      lampGlow: def.structure ? Math.max(0.08, hpNow / def.stats.hp) : undefined,
      reduced: this.reduced,
    });
  }

  // ---------- picking ----------
  /** Tile under a CSS-pixel point. Order: the clear middle of a tile's top face (so tiles behind a sprite stay
   *  clickable), then a unit's body, then the rest of a top face, then cliff sides. */
  pick(cx: number, cy: number): Pos | null {
    const wx = (cx - this.ox) / this.scale, wy = (cy - this.oy) / this.scale;
    const g = this.game, now = performance.now();
    const list = this.cachedDraw.length ? this.cachedDraw : this.buildDrawables(now);
    const topDist = (x: number, y: number) => {
      const s = this.view.project(x, y, this.vt[y][x].height);
      return Math.abs(wx - s.sx) / (TW / 2) + Math.abs(wy - s.sy) / (TH / 2);
    };
    // 1) clear middle of a top face, front-most first
    for (let i = list.length - 1; i >= 0; i--) { const d = list[i]; if (d.kind === 'tile' && topDist(d.x, d.y) <= 0.72) return { x: d.x, y: d.y }; }
    // 2) unit bodies (generous box)
    for (let i = list.length - 1; i >= 0; i--) {
      const d = list[i]; if (d.kind !== 'unit' || !d.u.alive) continue;
      const s = this.view.project(d.px, d.py, d.pz);
      const fh = figureHeight({ frame: frameFor(unitArt(d.u.defId, g.def(d.u)), 'idle', 0, !!g.def(d.u).structure), def: g.def(d.u) });
      if (Math.abs(wx - s.sx) <= 32 && wy >= s.sy - fh - 6 && wy <= s.sy + 10) return { x: d.u.x, y: d.u.y };
    }
    // 3) rest of a top face, then cliff sides
    for (let i = list.length - 1; i >= 0; i--) {
      const d = list[i]; if (d.kind !== 'tile') continue;
      if (topDist(d.x, d.y) <= 1) return { x: d.x, y: d.y };
      const t = this.vt[d.y][d.x], s = this.view.project(d.x, d.y, t.height);
      const dx = wx - s.sx, dy = wy - s.sy, th = t.height * LV + GROUND;
      if (Math.abs(dx) <= TW / 2) {
        const edge = dx < 0 ? (TH / 2) * (dx + TW / 2) / (TW / 2) : (TH / 2) * (1 - dx / (TW / 2));
        if (dy >= edge && dy <= edge + th) return { x: d.x, y: d.y };
      }
    }
    return null;
  }
}
export { key };

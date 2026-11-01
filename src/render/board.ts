// Board painter: draws the static terrain layer (cliff sides, tops, decals, edges, fog) in depth order.
// Uses painted tile art from content when present (terrain[id].tiles), else the procedural painterly fallback.
import type { Game } from '../engine/game';
import type { TerrainDef } from '../engine/types';
import { GROUND, LV, TH, TW, View, mix, rgba, rng, shade } from './iso';
import { diamondPath, sidePattern, terrainKind, terrainPattern } from './terrain';

/** Content-side extension of TerrainDef for painted tiles. */
export type TerrainExt = TerrainDef & {
  tiles?: { top?: string[]; side?: string; props?: string[]; animatedTop?: boolean; underlay?: string };
  underlay?: string;
};

const tileUrls = import.meta.glob('../../content/tiles/**/*.{png,webp,svg,jpg,jpeg,gif}', { eager: true, query: '?url', import: 'default' }) as Record<string, string>;
const images = new Map<string, HTMLImageElement>();
let onReady: (() => void) | null = null;
/** Called whenever a tile image finishes loading (so the cached board can be rebuilt). */
export function onTileArtReady(fn: () => void) { onReady = fn; }
function tileImage(p: string | undefined): HTMLImageElement | null {
  if (!p) return null;
  const url = /^(https?:|data:|\/|blob:)/.test(p) ? p : tileUrls[`../../content/${p}`];
  if (!url) return null;
  let img = images.get(url);
  if (!img) { img = new Image(); img.src = url; img.onload = () => onReady?.(); images.set(url, img); }
  return img.complete && img.naturalWidth > 0 ? img : null;
}
const sidePats = new Map<string, CanvasPattern>();

export interface AnimTile { x: number; y: number; kind: ReturnType<typeof terrainKind>; frames?: HTMLImageElement[] }

export class BoardPainter {
  constructor(private game: Game, private view: View, private seeds: Uint32Array) {}
  private art(id: string) { return (this.game.content.terrain[id] as TerrainExt | undefined)?.tiles; }
  private seed(x: number, y: number) { return this.seeds[y * this.game.width + x]; }

  /** Paint every tile. Returns the tiles that need per-frame animation. */
  paint(ctx: CanvasRenderingContext2D, minY: number, maxY: number): AnimTile[] {
    const g = this.game, v = this.view;
    const order: { d: number; x: number; y: number }[] = [];
    for (let y = 0; y < g.height; y++) for (let x = 0; x < g.width; x++) order.push({ d: v.depth(x, y), x, y });
    order.sort((a, b) => a.d - b.d);
    const anim: AnimTile[] = [];
    for (const o of order) {
      const t = g.tiles[o.y][o.x], def = g.content.terrain[t.terrain] as TerrainExt | undefined;
      const kind = terrainKind(t.terrain, def);
      this.sides(ctx, o.x, o.y);
      this.top(ctx, o.x, o.y, t.terrain, def, kind);
      this.edges(ctx, o.x, o.y);
      const art = this.art(t.terrain);
      if (art?.animatedTop && art.top && art.top.length > 1) anim.push({ x: o.x, y: o.y, kind, frames: art.top.map(p => tileImage(p)).filter((i): i is HTMLImageElement => !!i) });
      else if (!art?.top && (kind === 'water' || kind === 'deepwater' || kind === 'glow' || kind === 'coral' || kind === 'trench')) anim.push({ x: o.x, y: o.y, kind });
      else if (g.map.wells?.some(w => w.x === o.x && w.y === o.y)) anim.push({ x: o.x, y: o.y, kind });
    }
    const { minX, maxX } = this.xBounds();
    ctx.save(); ctx.globalCompositeOperation = 'source-atop'; // tint tiles only, not the empty corners
    // global key light from the upper left: warm toward it, cool blue-violet away from it
    const lg = ctx.createLinearGradient(minX, minY, maxX, maxY);
    lg.addColorStop(0, 'rgba(255,240,210,0.16)'); lg.addColorStop(0.5, 'rgba(255,255,255,0)'); lg.addColorStop(1, 'rgba(40,30,70,0.2)');
    ctx.fillStyle = lg; ctx.fillRect(minX, minY, maxX - minX, maxY - minY);
    // depth fog: far rows fade toward the dusk haze
    const fog = ctx.createLinearGradient(0, minY, 0, maxY);
    fog.addColorStop(0, 'rgba(110,100,120,0.34)'); fog.addColorStop(0.45, 'rgba(110,100,120,0.08)'); fog.addColorStop(1, 'rgba(60,40,70,0)');
    ctx.fillStyle = fog;
    ctx.fillRect(minX, minY, maxX - minX, maxY - minY);
    ctx.restore();
    return anim;
  }
  private xBounds() { const v = this.view; return { minX: -(v.rh) * TW / 2 - TW, maxX: (v.rw) * TW / 2 + TW }; }

  /** Both cliff faces of a tile, with strata texture, per-level shading and bottom darkening. */
  private sides(ctx: CanvasRenderingContext2D, x: number, y: number) {
    const g = this.game, t = g.tiles[y][x], def = g.content.terrain[t.terrain] as TerrainExt | undefined;
    const kind = terrainKind(t.terrain, def);
    if (kind === 'trench') return;
    const { sx, sy } = this.view.project(x, y, t.height);
    const th = t.height * LV + GROUND, hw = TW / 2, hh = TH / 2;
    const sideArt = tileImage(def?.tiles?.side);
    for (const right of [false, true]) {
      ctx.save();
      ctx.beginPath();
      if (right) { ctx.moveTo(sx, sy + hh); ctx.lineTo(sx + hw, sy); ctx.lineTo(sx + hw, sy + th); ctx.lineTo(sx, sy + hh + th); }
      else { ctx.moveTo(sx - hw, sy); ctx.lineTo(sx, sy + hh); ctx.lineTo(sx, sy + hh + th); ctx.lineTo(sx - hw, sy + th); }
      ctx.closePath(); ctx.clip();
      if (sideArt) {
        const k = `${def?.tiles?.side}`; let p = sidePats.get(k);
        if (!p) { p = ctx.createPattern(sideArt, 'repeat')!; sidePats.set(k, p); }
        ctx.save(); ctx.translate(right ? sx : sx - hw, right ? sy : sy); ctx.transform(1, right ? -0.5 : 0.5, 0, 1, 0, right ? hh : 0);
        ctx.fillStyle = p; ctx.fillRect(0, -hh, hw, th + TH); ctx.restore();
        ctx.fillStyle = right ? 'rgba(10,8,14,0.45)' : 'rgba(10,8,14,0.22)'; ctx.fillRect(sx - hw, sy - hh, TW, th + TH);
      } else {
        ctx.save(); ctx.translate(right ? sx : sx - hw, right ? sy : sy); ctx.transform(1, right ? -0.5 : 0.5, 0, 1, 0, right ? hh : 0);
        ctx.fillStyle = sidePattern(ctx, t.terrain, def, right); ctx.fillRect(0, -hh, hw, th + TH); ctx.restore();
      }
      // per-level shading bands + bottom darkening
      for (let l = 0; l < t.height; l++) {
        const yy = sy + l * LV;
        ctx.fillStyle = 'rgba(0,0,0,0.14)'; ctx.save(); ctx.transform(1, right ? -0.5 : 0.5, 0, 1, 0, 0);
        ctx.fillRect(right ? sx : sx - hw, right ? yy + hh + LV - 3 : yy + hh / 2 + LV - 3 - (hh / 2), hw, 3); ctx.restore();
      }
      const gr = ctx.createLinearGradient(0, sy, 0, sy + hh + th);
      gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(0.5, 'rgba(0,0,0,0.12)'); gr.addColorStop(1, 'rgba(0,0,0,0.5)');
      ctx.fillStyle = gr; ctx.fillRect(sx - hw, sy, TW, th + TH);
      // rim light along the top edge of the lit (left) face
      ctx.strokeStyle = right ? 'rgba(0,0,0,0.35)' : 'rgba(255,245,220,0.18)'; ctx.lineWidth = 1.5;
      ctx.beginPath(); if (right) { ctx.moveTo(sx, sy + hh); ctx.lineTo(sx + hw, sy); } else { ctx.moveTo(sx - hw, sy); ctx.lineTo(sx, sy + hh); } ctx.stroke();
      ctx.restore();
    }
    // vertical corner line
    ctx.strokeStyle = 'rgba(0,0,0,0.45)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(sx, sy + hh); ctx.lineTo(sx, sy + hh + th); ctx.stroke();
  }

  private topArt(ctx: CanvasRenderingContext2D, id: string, sx: number, sy: number, seed: number, alpha = 1): boolean {
    const art = this.art(id); if (!art?.top?.length) return false;
    const idx = art.animatedTop ? 0 : seed % art.top.length;
    const img = tileImage(art.top[idx]) ?? tileImage(art.top[0]); if (!img) return false;
    const w = img.naturalWidth, h = img.naturalHeight, s = TW / w;
    ctx.save(); ctx.globalAlpha = alpha; ctx.drawImage(img, sx - TW / 2, sy + TH / 2 - h * s, TW, h * s); ctx.restore();
    return true;
  }

  private top(ctx: CanvasRenderingContext2D, x: number, y: number, id: string, def: TerrainExt | undefined, kind: ReturnType<typeof terrainKind>) {
    const { sx, sy } = this.view.project(x, y, this.game.tiles[y][x].height);
    const seed = this.seed(x, y);
    const under = def?.tiles?.underlay ?? def?.underlay;
    ctx.save(); diamondPath(ctx, sx, sy, -0.5); ctx.clip();
    if (under && this.game.content.terrain[under]) {
      if (!this.topArt(ctx, under, sx, sy, seed)) this.proceduralTop(ctx, sx, sy, under, this.game.content.terrain[under], terrainKind(under, this.game.content.terrain[under]), seed);
    }
    if (!this.topArt(ctx, id, sx, sy, seed, under ? 0.82 : 1)) this.proceduralTop(ctx, sx, sy, id, def, kind, seed);
    ctx.restore();
    // props from content art
    const props = def?.tiles?.props;
    if (props?.length) {
      const r = rng(seed ^ 0x51ed);
      const n = r() < 0.34 ? 1 : 0; // story props stay rare (~1 in 3 eligible tiles)
      for (let i = 0; i < n; i++) {
        const img = tileImage(props[Math.floor(r() * props.length)]); if (!img) continue;
        const u = (r() - 0.5) * 0.9, v = (r() - 0.5) * 0.9;
        const px = sx + (u - v) * TW / 2 * 0.7, py = sy + (u + v) * TH / 2 * 0.7;
        ctx.drawImage(img, px - img.naturalWidth / 2, py - img.naturalHeight, img.naturalWidth, img.naturalHeight);
      }
    }
  }

  /** Procedural fallback: continuous world-space texture, organic tone variation and scattered decals. */
  private proceduralTop(ctx: CanvasRenderingContext2D, sx: number, sy: number, id: string, def: TerrainDef | undefined, kind: ReturnType<typeof terrainKind>, seed: number) {
    const base = def?.color ?? '#777';
    ctx.fillStyle = terrainPattern(ctx, id, def); ctx.fillRect(sx - TW / 2, sy - TH / 2, TW, TH);
    const r = rng(seed);
    // organic colour variation: a soft blotch per tile (not aligned to the grid)
    const tone = (r() - 0.5) * 0.2, bx = sx + (r() - 0.5) * 60, by = sy + (r() - 0.5) * 30;
    const bg = ctx.createRadialGradient(bx, by, 4, bx, by, 50 + r() * 40);
    bg.addColorStop(0, tone > 0 ? `rgba(255,250,235,${tone})` : `rgba(30,25,40,${-tone})`); bg.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = bg; ctx.fillRect(sx - TW, sy - TH, TW * 2, TH * 2);
    if (kind === 'trench') {
      const pg = ctx.createRadialGradient(sx, sy, 2, sx, sy, TW / 2);
      pg.addColorStop(0, 'rgba(0,0,0,0.95)'); pg.addColorStop(0.6, 'rgba(2,4,8,0.7)'); pg.addColorStop(1, 'rgba(20,30,40,0.2)');
      ctx.fillStyle = pg; ctx.fillRect(sx - TW / 2, sy - TH / 2, TW, TH);
      ctx.strokeStyle = 'rgba(0,0,0,0.9)'; ctx.lineWidth = 14; diamondPath(ctx, sx, sy); ctx.stroke();
      return;
    }
    if (kind === 'water' || kind === 'deepwater' || kind === 'glow') {
      const sg = ctx.createRadialGradient(sx - 22, sy - 10, 2, sx - 22, sy - 10, 56);
      sg.addColorStop(0, 'rgba(255,255,255,0.25)'); sg.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.fillStyle = sg; ctx.fillRect(sx - TW / 2, sy - TH / 2, TW, TH);
      // wet rim
      ctx.strokeStyle = rgba(mix(base, '#ffffff', 0.5), 0.35); ctx.lineWidth = 3; diamondPath(ctx, sx, sy, 2); ctx.stroke();
    }
    this.decals(ctx, sx, sy, base, kind, r);
  }

  /** Small painted props scattered on the top face (clipped to the diamond). */
  private decals(ctx: CanvasRenderingContext2D, sx: number, sy: number, base: string, kind: ReturnType<typeof terrainKind>, r: () => number) {
    const count = kind === 'coral' || kind === 'kelp' ? 2 + Math.floor(r() * 3) : kind === 'wall' ? 2 + Math.floor(r() * 2) : r() < 0.6 ? 0 : 1 + Math.floor(r() * 2);
    const dark = shade(base, 0.45), light = mix(base, '#fffaf0', 0.5);
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (let i = 0; i < count; i++) {
      const u = (r() - 0.5) * 0.8, v = (r() - 0.5) * 0.8;
      const px = sx + (u - v) * TW / 2, py = sy + (u + v) * TH / 2, s = 0.7 + r() * 0.7;
      ctx.save(); ctx.translate(px, py); ctx.scale(s, s);
      switch (kind) {
        case 'salt': case 'wall': { // salt crystal cluster with blue shadow
          ctx.fillStyle = 'rgba(70,90,120,0.25)'; ctx.beginPath(); ctx.ellipse(3, 3, 12, 5, 0, 0, 7); ctx.fill();
          for (let k = 0; k < 3 + Math.floor(r() * 3); k++) {
            const ox = (r() - 0.5) * 14, h = (kind === 'wall' ? 14 : 5) + r() * (kind === 'wall' ? 16 : 9), w = 3 + r() * 3;
            ctx.fillStyle = r() < 0.5 ? '#fbfaf5' : '#e4e8ee'; ctx.beginPath(); ctx.moveTo(ox - w, 2); ctx.lineTo(ox + (r() - 0.5) * 3, 2 - h); ctx.lineTo(ox + w, 2); ctx.closePath(); ctx.fill();
            ctx.strokeStyle = 'rgba(80,100,130,0.5)'; ctx.lineWidth = 0.8; ctx.stroke();
          }
          break;
        }
        case 'silt': case 'plain': case 'chalk': {
          if (r() < 0.4 && kind === 'silt') { // puddle
            const pg = ctx.createRadialGradient(-3, -2, 1, 0, 0, 16); pg.addColorStop(0, 'rgba(180,220,230,0.55)'); pg.addColorStop(1, rgba(shade(base, 0.6), 0.6));
            ctx.fillStyle = pg; ctx.beginPath(); ctx.ellipse(0, 0, 16, 7, 0.2, 0, 7); ctx.fill();
            ctx.strokeStyle = 'rgba(255,255,255,0.4)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.ellipse(-4, -2, 6, 2, 0.2, 0, 7); ctx.stroke();
          } else if (kind === 'chalk') { // bone shards
            ctx.strokeStyle = '#f3eee2'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(-8, 2); ctx.lineTo(8, -3); ctx.stroke();
            ctx.strokeStyle = 'rgba(90,80,70,0.5)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(-8, 3); ctx.lineTo(8, -2); ctx.stroke();
          } else { // pebbles
            for (let k = 0; k < 3; k++) { const ox = (r() - 0.5) * 16, oy = (r() - 0.5) * 8, rr = 1.5 + r() * 2.5;
              ctx.fillStyle = 'rgba(0,0,0,0.25)'; ctx.beginPath(); ctx.ellipse(ox + 1, oy + 1, rr, rr * 0.6, 0, 0, 7); ctx.fill();
              ctx.fillStyle = r() < 0.5 ? light : dark; ctx.beginPath(); ctx.ellipse(ox, oy, rr, rr * 0.6, 0, 0, 7); ctx.fill(); }
          }
          break;
        }
        case 'coral': { // coral clump: branching strokes with knobs
          ctx.fillStyle = 'rgba(0,0,0,0.25)'; ctx.beginPath(); ctx.ellipse(1, 2, 10, 4, 0, 0, 7); ctx.fill();
          const col = r() < 0.5 ? mix(base, '#ffd6c8', 0.3) : mix(base, '#6a3050', 0.3);
          ctx.strokeStyle = col; ctx.lineWidth = 2.5;
          for (let k = 0; k < 4; k++) { const a = -Math.PI / 2 + (k - 1.5) * 0.5, l = 8 + r() * 8; ctx.beginPath(); ctx.moveTo(0, 0); ctx.quadraticCurveTo(Math.cos(a) * l * 0.5 + (r() - 0.5) * 4, Math.sin(a) * l * 0.6, Math.cos(a) * l, Math.sin(a) * l); ctx.stroke();
            ctx.fillStyle = mix(col, '#ffffff', 0.4); ctx.beginPath(); ctx.arc(Math.cos(a) * l, Math.sin(a) * l, 1.8, 0, 7); ctx.fill(); }
          break;
        }
        case 'wood': { // broken plank + rivets
          ctx.rotate(r() * 0.6 - 0.3);
          ctx.fillStyle = 'rgba(0,0,0,0.3)'; ctx.fillRect(-13, -2, 26, 7);
          ctx.fillStyle = mix(base, '#c47a3a', 0.3); ctx.fillRect(-13, -4, 26, 6);
          ctx.strokeStyle = 'rgba(20,10,5,0.6)'; ctx.lineWidth = 1; ctx.strokeRect(-13, -4, 26, 6);
          ctx.fillStyle = '#3a2a20'; for (let k = -1; k <= 1; k++) { ctx.beginPath(); ctx.arc(k * 9, -1, 1.3, 0, 7); ctx.fill(); }
          break;
        }
        case 'road': { // rib curve / vertebrae
          ctx.strokeStyle = '#efe8d4'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(0, 8, 14, Math.PI * 1.15, Math.PI * 1.85); ctx.stroke();
          ctx.strokeStyle = 'rgba(80,70,50,0.6)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(0, 9, 14, Math.PI * 1.15, Math.PI * 1.85); ctx.stroke();
          break;
        }
        case 'kelp': { // dry tuft
          ctx.lineWidth = 2;
          for (let k = 0; k < 5; k++) { const a = -Math.PI / 2 + (k - 2) * 0.35, l = 10 + r() * 10; ctx.strokeStyle = r() < 0.5 ? shade(base, 0.5) : mix(base, '#c8c27a', 0.4); ctx.beginPath(); ctx.moveTo(0, 0); ctx.quadraticCurveTo(Math.cos(a) * l * 0.4, Math.sin(a) * l * 0.7, Math.cos(a) * l * 1.1, Math.sin(a) * l); ctx.stroke(); }
          break;
        }
        case 'stone': { // crack
          ctx.strokeStyle = 'rgba(0,0,0,0.45)'; ctx.lineWidth = 1.2; ctx.beginPath(); ctx.moveTo(-10, 4); ctx.lineTo(-3, -2); ctx.lineTo(4, 1); ctx.lineTo(11, -5); ctx.stroke();
          ctx.strokeStyle = 'rgba(255,255,255,0.2)'; ctx.beginPath(); ctx.moveTo(-10, 5); ctx.lineTo(-3, -1); ctx.lineTo(4, 2); ctx.lineTo(11, -4); ctx.stroke();
          break;
        }
        case 'glow': { // bubbles
          for (let k = 0; k < 3; k++) { ctx.strokeStyle = 'rgba(255,240,200,0.6)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.ellipse((r() - 0.5) * 20, (r() - 0.5) * 10, 2 + r() * 3, 1.5 + r() * 2, 0, 0, 7); ctx.stroke(); }
          break;
        }
        case 'water': { // foam arc
          ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(0, 0, 8 + r() * 6, Math.PI * 1.1, Math.PI * 1.9); ctx.stroke();
          break;
        }
        default: break;
      }
      ctx.restore();
    }
  }

  /** Paint a fading band of another terrain's top into the tile at (tx,ty), along edge A-B. Texture is anchored at (ox,oy). */
  private blendBand(ctx: CanvasRenderingContext2D, tx: number, ty: number, ax: number, ay: number, bx: number, by: number, id: string, def: TerrainExt | undefined, ox: number, oy: number, seed: number) {
    const mx = (ax + bx) / 2, my = (ay + by) / 2;
    let ix = tx - mx, iy = ty - my; const L = Math.hypot(ix, iy) || 1; ix /= L; iy /= L;
    for (const [w, a] of [[5, 0.13], [3, 0.17], [1.5, 0.22]] as const) {
      ctx.save(); diamondPath(ctx, tx, ty); ctx.clip();
      ctx.beginPath(); ctx.moveTo(ax - ix, ay - iy); ctx.lineTo(bx - ix, by - iy); ctx.lineTo(bx + ix * w, by + iy * w); ctx.lineTo(ax + ix * w, ay + iy * w); ctx.closePath(); ctx.clip();
      ctx.globalAlpha = a;
      if (!this.topArt(ctx, id, ox, oy, seed, a)) this.proceduralTop(ctx, ox, oy, id, def, terrainKind(id, def), seed);
      ctx.restore();
    }
  }

  /** Soft boundary lines where terrain changes, AO under cliffs behind this tile, faint grid elsewhere. */
  private edges(ctx: CanvasRenderingContext2D, x: number, y: number) {
    const g = this.game, v = this.view, t = g.tiles[y][x];
    const { sx, sy } = v.project(x, y, t.height);
    const myDepth = v.depth(x, y);
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]] as const) {
      const nx = x + dx, ny = y + dy;
      if (!g.inBounds(nx, ny)) continue;
      if (v.depth(nx, ny) > myDepth) continue; // neighbour in front draws this edge later
      const n = g.tiles[ny][nx];
      const c = v.project(nx, ny, t.height);
      const mx = (sx + c.sx) / 2, my = (sy + c.sy) / 2, ex = (c.sx - sx) / 2, ey = (c.sy - sy) / 2;
      const ax = mx + ex, ay = my - ey, bx = mx - ex, by = my + ey; // shared edge endpoints at this tile's height
      const diffT = n.terrain !== t.terrain, higher = n.height > t.height;
      if (higher) {
        // ambient occlusion band on this (lower) tile along the cliff foot
        ctx.save(); diamondPath(ctx, sx, sy); ctx.clip();
        const gr = ctx.createLinearGradient(mx, my, sx, sy);
        gr.addColorStop(0, 'rgba(0,0,0,0.5)'); gr.addColorStop(0.5, 'rgba(0,0,0,0.0)');
        ctx.fillStyle = gr; ctx.fillRect(sx - TW / 2, sy - TH / 2, TW, TH);
        ctx.restore();
      } else if (diffT) {
        if (n.height === t.height) {
          // soft texture blend across the shared edge, both directions (no seam line)
          const ndef = g.content.terrain[n.terrain] as TerrainExt | undefined;
          this.blendBand(ctx, sx, sy, ax, ay, bx, by, n.terrain, ndef, c.sx, c.sy, this.seed(nx, ny));
          this.blendBand(ctx, c.sx, c.sy, ax, ay, bx, by, t.terrain, g.content.terrain[t.terrain] as TerrainExt | undefined, sx, sy, this.seed(x, y));
        }
      } else if (n.height === t.height) {
        ctx.strokeStyle = 'rgba(20,16,24,0.055)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(bx, by); ctx.stroke();
      }
    }
  }
  /** Redraw one tile (sides + top + edges), used to re-occlude units behind cliffs. */
  drawTile(ctx: CanvasRenderingContext2D, x: number, y: number) {
    const t = this.game.tiles[y][x], def = this.game.content.terrain[t.terrain] as TerrainExt | undefined;
    this.sides(ctx, x, y); this.top(ctx, x, y, t.terrain, def, terrainKind(t.terrain, def)); this.edges(ctx, x, y);
  }
}

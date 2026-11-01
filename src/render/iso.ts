import type { Pos } from '../engine/types';

export const TW = 64;   // tile width (diamond)
export const TH = 32;   // tile height (diamond)
export const LV = 12;   // pixels per height level
export const GROUND = 8; // extra thickness under every tile

/** Isometric projection with 90-degree camera rotation. Works with fractional coordinates. */
export class View {
  rot = 0;
  constructor(public w: number, public h: number) {}
  get rw() { return this.rot % 2 ? this.h : this.w; }
  get rh() { return this.rot % 2 ? this.w : this.h; }
  rotate(x: number, y: number): Pos {
    switch (this.rot) {
      case 1: return { x: this.h - 1 - y, y: x };
      case 2: return { x: this.w - 1 - x, y: this.h - 1 - y };
      case 3: return { x: y, y: this.w - 1 - x };
      default: return { x, y };
    }
  }
  /** Centre of a tile's top face at height `z` (in levels). */
  project(x: number, y: number, z = 0) {
    const r = this.rotate(x, y);
    return { sx: (r.x - r.y) * TW / 2, sy: (r.x + r.y) * TH / 2 - z * LV };
  }
  depth(x: number, y: number) { const r = this.rotate(x, y); return r.x + r.y; }
}

export const key = (x: number, y: number) => `${x},${y}`;

// ---- colour helpers ----
export function parseHex(c: string): [number, number, number] {
  let s = c.replace('#', '');
  if (s.length === 3) s = [...s].map(ch => ch + ch).join('');
  const n = parseInt(s, 16);
  if (Number.isNaN(n)) return [128, 128, 128];
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
export function shade(c: string, f: number) {
  const [r, g, b] = parseHex(c);
  const cl = (v: number) => Math.max(0, Math.min(255, Math.round(v)));
  return `rgb(${cl(r * f)},${cl(g * f)},${cl(b * f)})`;
}
export function rgba(c: string, a: number) {
  const [r, g, b] = parseHex(c);
  return `rgba(${r},${g},${b},${a})`;
}

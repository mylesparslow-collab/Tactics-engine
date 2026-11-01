import type { Pos } from '../engine/types';

export const TW = 128;  // tile width (diamond) at 1x
export const TH = 64;   // tile height (diamond) at 1x
export const LV = 24;   // pixels per height level
export const GROUND = 14; // extra thickness under every tile

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
const cl = (v: number) => Math.max(0, Math.min(255, Math.round(v)));
export function shade(c: string, f: number) {
  const [r, g, b] = parseHex(c);
  return `rgb(${cl(r * f)},${cl(g * f)},${cl(b * f)})`;
}
export function rgba(c: string, a: number) {
  const [r, g, b] = parseHex(c);
  return `rgba(${r},${g},${b},${a})`;
}
/** Linear mix of two hex colours; t=0 gives a. */
export function mix(a: string, b: string, t: number) {
  const [r1, g1, b1] = parseHex(a), [r2, g2, b2] = parseHex(b);
  return `rgb(${cl(r1 + (r2 - r1) * t)},${cl(g1 + (g2 - g1) * t)},${cl(b1 + (b2 - b1) * t)})`;
}
export function luminance(c: string) {
  const [r, g, b] = parseHex(c);
  return (0.299 * r + 0.587 * g + 0.114 * b) / 255;
}

/** Small deterministic PRNG (mulberry32). */
export function rng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export function hashStr(s: string) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  return h >>> 0;
}

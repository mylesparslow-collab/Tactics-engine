// Painterly procedural terrain: per-terrain textures, pre-rendered tile blocks, glow highlights and the backdrop.
import type { TerrainDef } from '../engine/types';
import { LV, TH, TW, hashStr, luminance, mix, parseHex, rgba, rng, shade } from './iso';

export const RES = 2;            // offscreen render resolution multiplier
const TEX = 256;                 // texture size at 1x (world px)
export const VARIANTS = 4;

type Kind = 'water' | 'deepwater' | 'coral' | 'wood' | 'salt' | 'wall' | 'road' | 'glow' | 'kelp' | 'stone' | 'silt' | 'chalk' | 'trench' | 'plain';

export function terrainKind(id: string, def: TerrainDef | undefined): Kind {
  const s = `${id} ${def?.name ?? ''}`.toLowerCase();
  const has = (...k: string[]) => k.some(w => s.includes(w));
  if (has('trench', 'abyss', 'chasm', 'pit')) return 'trench';
  if (has('lake', 'deep')) return 'deepwater';
  if (has('water', 'brine', 'pool', 'tide', 'sea')) return 'water';
  if (has('lava', 'ember', 'oil', 'fire', 'magma')) return 'glow';
  if (has('coral', 'reef')) return 'coral';
  if (has('wreck', 'wood', 'hull', 'plank', 'deck')) return 'wood';
  if (has('road', 'path', 'bone')) return 'road';
  if (has('kelp', 'husk', 'forest', 'thicket', 'weed')) return 'kelp';
  if (has('stone', 'rock', 'masonry', 'ruin')) return 'stone';
  if (has('salt', 'crust')) return 'salt';
  if (has('wall')) return 'wall';
  if (has('calcite', 'chalk', 'ash')) return 'chalk';
  if (has('silt', 'mud', 'sand')) return 'silt';
  return 'plain';
}

export const isAnimated = (k: Kind) => k === 'water' || k === 'deepwater' || k === 'glow' || k === 'coral' || k === 'trench';

function canvas(w: number, h: number) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; return c;
}

/** Periodic value noise in [0,1], period `p` cells over size `n`. */
function noiseField(n: number, p: number, seed: number, octaves = 3) {
  const out = new Float32Array(n * n);
  const lat = new Float32Array(p * p * 8);
  const r = rng(seed);
  for (let i = 0; i < lat.length; i++) lat[i] = r();
  const sm = (t: number) => t * t * (3 - 2 * t);
  let amp = 1, total = 0;
  for (let o = 0; o < octaves; o++) {
    const cells = p << o, off = o * p * p;
    const idx = (x: number, y: number) => lat[(off + ((y % cells + cells) % cells) * p + ((x % cells + cells) % cells)) % lat.length];
    const cs = n / cells;
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
      const fx = x / cs, fy = y / cs, ix = Math.floor(fx), iy = Math.floor(fy);
      const tx = sm(fx - ix), ty = sm(fy - iy);
      const a = idx(ix, iy), b = idx(ix + 1, iy), c = idx(ix, iy + 1), d = idx(ix + 1, iy + 1);
      out[y * n + x] += ((a + (b - a) * tx) + ((c + (d - c) * tx) - (a + (b - a) * tx)) * ty) * amp;
    }
    total += amp; amp *= 0.5;
  }
  for (let i = 0; i < out.length; i++) out[i] /= total;
  return out;
}

const texCache = new Map<string, HTMLCanvasElement>();
const sideCache = new Map<string, HTMLCanvasElement>();

/** A square painterly texture for a terrain (world px TEX at RES). */
export function terrainTexture(id: string, def: TerrainDef | undefined): HTMLCanvasElement {
  const hit = texCache.get(id); if (hit) return hit;
  const base = def?.color ?? '#777', kind = terrainKind(id, def), seed = hashStr(id);
  const n = TEX * RES, c = canvas(n, n), ctx = c.getContext('2d')!;
  const [br, bg, bb] = parseHex(base);
  const lum = luminance(base);
  const f = noiseField(n, 8, seed, 4), g = noiseField(n, 32, seed + 7, 2);
  const img = ctx.createImageData(n, n), d = img.data;
  // warm/cool tint drift so the colour is not flat
  const warm = [br * 1.06 + 8, bg * 1.0, bb * 0.9], cool = [br * 0.92, bg * 0.97, bb * 1.08 + 6];
  const amp = kind === 'water' || kind === 'deepwater' ? 0.10 : kind === 'trench' ? 0.06 : 0.18;
  for (let i = 0; i < n * n; i++) {
    const v = f[i] - 0.5, gr = (g[i] - 0.5) * (kind === 'water' ? 0.05 : 0.11);
    const t = f[i];
    const r = warm[0] * (1 - t) + cool[0] * t, gg = warm[1] * (1 - t) + cool[1] * t, b = warm[2] * (1 - t) + cool[2] * t;
    const k = 1 + v * amp * 2 + gr;
    d[i * 4] = Math.max(0, Math.min(255, r * k)); d[i * 4 + 1] = Math.max(0, Math.min(255, gg * k)); d[i * 4 + 2] = Math.max(0, Math.min(255, b * k)); d[i * 4 + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
  ctx.scale(RES, RES);
  const r = rng(seed ^ 0x9e37);
  const dark = shade(base, 0.55), light = mix(base, '#ffffff', 0.35);
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  switch (kind) {
    case 'salt': case 'wall': case 'chalk': case 'plain': {
      // cracked crust: random polyline cracks + sparkle specks
      ctx.strokeStyle = rgba(shade(base, 0.5), kind === 'chalk' ? 0.3 : 0.7); ctx.lineWidth = 1.3;
      for (let i = 0; i < 46; i++) {
        let x = r() * TEX, y = r() * TEX; ctx.beginPath(); ctx.moveTo(x, y);
        const steps = 3 + Math.floor(r() * 5), ang0 = r() * Math.PI * 2;
        for (let s = 0; s < steps; s++) { const a = ang0 + (r() - 0.5) * 1.6; x += Math.cos(a) * (6 + r() * 14); y += Math.sin(a) * (6 + r() * 14); ctx.lineTo(x, y); }
        ctx.stroke();
      }
      ctx.strokeStyle = rgba('#8fb0c8', 0.18); ctx.lineWidth = 2.5;
      for (let i = 0; i < 14; i++) { const x = r() * TEX, y = r() * TEX; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + (r() - 0.5) * 30, y + (r() - 0.5) * 30); ctx.stroke(); }
      for (let i = 0; i < (kind === 'chalk' ? 260 : 150); i++) {
        ctx.fillStyle = r() < 0.75 ? rgba('#ffffff', 0.35 + r() * 0.5) : rgba(dark, 0.4);
        ctx.beginPath(); ctx.arc(r() * TEX, r() * TEX, 0.5 + r() * (kind === 'chalk' ? 1.6 : 1.1), 0, 7); ctx.fill();
      }
      break;
    }
    case 'silt': {
      ctx.strokeStyle = rgba(dark, 0.28); ctx.lineWidth = 1.4;
      for (let i = 0; i < 40; i++) {
        const y0 = r() * TEX, x0 = r() * TEX, len = 20 + r() * 40;
        ctx.beginPath(); for (let x = 0; x <= len; x += 4) ctx.lineTo(x0 + x, y0 + Math.sin(x / 6 + i) * 2.2); ctx.stroke();
      }
      ctx.fillStyle = rgba(light, 0.25);
      for (let i = 0; i < 60; i++) { ctx.beginPath(); ctx.ellipse(r() * TEX, r() * TEX, 1.5 + r() * 2, 0.8, 0, 0, 7); ctx.fill(); }
      break;
    }
    case 'stone': {
      const bw = 22, bh = 11;
      for (let row = 0; row * bh < TEX + bh; row++) for (let col = -1; col * bw < TEX + bw; col++) {
        const x = col * bw + (row % 2 ? bw / 2 : 0) + (r() - 0.5) * 2, y = row * bh + (r() - 0.5) * 2;
        ctx.fillStyle = rgba(r() < 0.5 ? light : dark, 0.1 + r() * 0.12);
        ctx.fillRect(x + 1, y + 1, bw - 2, bh - 2);
        ctx.strokeStyle = rgba(dark, 0.55); ctx.lineWidth = 1.3; ctx.strokeRect(x + 0.5, y + 0.5, bw - 1, bh - 1);
        ctx.strokeStyle = rgba(light, 0.25); ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(x + 1.5, y + bh - 1.5); ctx.lineTo(x + 1.5, y + 1.5); ctx.lineTo(x + bw - 1.5, y + 1.5); ctx.stroke();
      }
      break;
    }
    case 'road': {
      // worn flagstones / laid vertebrae: rounded polygons with dark grout
      const cell = 26;
      for (let row = 0; row * cell < TEX + cell; row++) for (let col = -1; col * cell < TEX + cell; col++) {
        const cx = col * cell + (row % 2 ? cell / 2 : 0) + cell / 2, cy = row * cell + cell / 2;
        const pts = 6 + Math.floor(r() * 3), rad = cell * 0.52;
        ctx.beginPath();
        for (let k = 0; k < pts; k++) { const a = k / pts * Math.PI * 2; const rr = rad * (0.82 + r() * 0.2); ctx.lineTo(cx + Math.cos(a) * rr, cy + Math.sin(a) * rr * 0.85); }
        ctx.closePath();
        ctx.fillStyle = rgba(r() < 0.5 ? light : base, 0.22); ctx.fill();
        ctx.strokeStyle = rgba(dark, 0.6); ctx.lineWidth = 2.2; ctx.stroke();
        ctx.strokeStyle = rgba(light, 0.3); ctx.lineWidth = 0.8; ctx.stroke();
      }
      break;
    }
    case 'wood': {
      // planks along a diagonal with grain, rust and rivets
      ctx.save(); ctx.translate(TEX / 2, TEX / 2); ctx.rotate(0.46); ctx.translate(-TEX, -TEX);
      const pw = 17;
      for (let i = 0; i * pw < TEX * 2; i++) {
        const y = i * pw;
        ctx.fillStyle = rgba(r() < 0.5 ? dark : light, 0.1 + r() * 0.12); ctx.fillRect(0, y, TEX * 2, pw - 1.5);
        ctx.strokeStyle = rgba('#1a0f08', 0.6); ctx.lineWidth = 1.6; ctx.beginPath(); ctx.moveTo(0, y + pw - 1); ctx.lineTo(TEX * 2, y + pw - 1); ctx.stroke();
        ctx.strokeStyle = rgba(dark, 0.3); ctx.lineWidth = 0.7;
        for (let gI = 0; gI < 4; gI++) { const gy = y + 2 + r() * (pw - 5); ctx.beginPath(); ctx.moveTo(0, gy); for (let x = 0; x < TEX * 2; x += 10) ctx.lineTo(x, gy + Math.sin(x / 17 + gI) * 1.2); ctx.stroke(); }
        for (let k = 0; k < 6; k++) { const x = r() * TEX * 2; ctx.fillStyle = rgba('#2a1a10', 0.8); ctx.beginPath(); ctx.arc(x, y + pw / 2, 1.4, 0, 7); ctx.fill(); ctx.fillStyle = rgba('#c47a3a', 0.35); ctx.beginPath(); ctx.arc(x + 1, y + pw / 2 + 2, 3, 0, 7); ctx.fill(); }
      }
      ctx.restore();
      break;
    }
    case 'coral': {
      // knobbly polyps: shaded bumps + branching twigs
      for (let i = 0; i < 230; i++) {
        const x = r() * TEX, y = r() * TEX, rad = 1.5 + r() * 4.5;
        const gr = ctx.createRadialGradient(x - rad * 0.4, y - rad * 0.4, 0, x, y, rad);
        gr.addColorStop(0, rgba(mix(base, '#fff5ee', 0.5), 0.9)); gr.addColorStop(1, rgba(shade(base, 0.5), 0.75));
        ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(x, y, rad, 0, 7); ctx.fill();
      }
      ctx.strokeStyle = rgba(shade(base, 0.45), 0.7); ctx.lineWidth = 1.6;
      for (let i = 0; i < 28; i++) {
        let x = r() * TEX, y = r() * TEX; const a0 = r() * 6.3;
        for (let b = 0; b < 3; b++) { ctx.beginPath(); ctx.moveTo(x, y); const a = a0 + (b - 1) * 0.7; ctx.lineTo(x + Math.cos(a) * 12, y + Math.sin(a) * 12); ctx.stroke(); }
        x += 0; y += 0;
      }
      break;
    }
    case 'kelp': {
      ctx.lineWidth = 2.2;
      for (let i = 0; i < 140; i++) {
        const x = r() * TEX, y = r() * TEX, len = 8 + r() * 18;
        ctx.strokeStyle = rgba(r() < 0.5 ? shade(base, 0.45) : mix(base, '#b8c27a', 0.35), 0.75);
        ctx.beginPath(); ctx.moveTo(x, y); ctx.quadraticCurveTo(x + (r() - 0.5) * 10, y - len / 2, x + (r() - 0.5) * 14, y - len); ctx.stroke();
      }
      break;
    }
    case 'water': case 'deepwater': {
      // glossy: broad soft lightness bands and thin ripple highlights
      for (let i = 0; i < 14; i++) {
        const y = r() * TEX, x = r() * TEX;
        const gr = ctx.createRadialGradient(x, y, 0, x, y, 40 + r() * 40);
        gr.addColorStop(0, rgba(mix(base, '#ffffff', 0.35), kind === 'water' ? 0.22 : 0.08)); gr.addColorStop(1, rgba(base, 0));
        ctx.fillStyle = gr; ctx.fillRect(0, 0, TEX, TEX);
      }
      if (kind === 'water') {
        ctx.strokeStyle = rgba('#ffffff', 0.35); ctx.lineWidth = 1.2;
        for (let i = 0; i < 26; i++) { const x = r() * TEX, y = r() * TEX, w = 8 + r() * 18; ctx.beginPath(); ctx.moveTo(x, y); ctx.quadraticCurveTo(x + w / 2, y - 2.5, x + w, y); ctx.stroke(); }
      }
      break;
    }
    case 'glow': {
      // hot cracks of brighter amber under a glossy skin
      ctx.strokeStyle = rgba(mix(base, '#fff2a0', 0.6), 0.75); ctx.lineWidth = 2.4;
      for (let i = 0; i < 30; i++) {
        let x = r() * TEX, y = r() * TEX; ctx.beginPath(); ctx.moveTo(x, y);
        for (let s = 0; s < 5; s++) { x += (r() - 0.5) * 30; y += (r() - 0.5) * 30; ctx.lineTo(x, y); }
        ctx.stroke();
      }
      const gr = ctx.createLinearGradient(0, 0, TEX, TEX);
      gr.addColorStop(0, rgba('#ffffff', 0.18)); gr.addColorStop(0.5, rgba('#000000', 0)); gr.addColorStop(1, rgba('#000000', 0.2));
      ctx.fillStyle = gr; ctx.fillRect(0, 0, TEX, TEX);
      break;
    }
    case 'trench': {
      ctx.fillStyle = 'rgba(0,0,0,0.5)'; ctx.fillRect(0, 0, TEX, TEX);
      for (let i = 0; i < 20; i++) { ctx.fillStyle = rgba('#3fd1c4', 0.1 + r() * 0.2); ctx.beginPath(); ctx.arc(r() * TEX, r() * TEX, 0.6 + r(), 0, 7); ctx.fill(); }
      break;
    }
  }
  // paper grain over everything (very low alpha specks)
  for (let i = 0; i < 500; i++) { ctx.fillStyle = r() < 0.5 ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'; ctx.fillRect(r() * TEX, r() * TEX, 1, 1); }
  if (lum < 0.2 && kind !== 'trench') { ctx.fillStyle = 'rgba(255,255,255,0.04)'; ctx.fillRect(0, 0, TEX, TEX); }
  texCache.set(id, c);
  return c;
}

/** Strata texture used for cliff sides, tinted from the terrain colour. */
function sideTexture(id: string, def: TerrainDef | undefined, right: boolean): HTMLCanvasElement {
  const k = `${id}|${right}`; const hit = sideCache.get(k); if (hit) return hit;
  const base = def?.color ?? '#777', kind = terrainKind(id, def);
  const rock = mix(shade(base, right ? 0.42 : 0.6), '#2a2622', kind === 'wall' ? 0.15 : 0.45);
  const n = TEX * RES, c = canvas(n, n), ctx = c.getContext('2d')!;
  ctx.fillStyle = rock; ctx.fillRect(0, 0, n, n);
  ctx.scale(RES, RES);
  const r = rng(hashStr(k));
  const f = noiseField(64, 8, hashStr(id) + 3, 2);
  for (let y = 0; y < 64; y++) for (let x = 0; x < 64; x++) { ctx.fillStyle = `rgba(${f[y * 64 + x] > 0.5 ? '255,255,255' : '0,0,0'},${Math.abs(f[y * 64 + x] - 0.5) * 0.28})`; ctx.fillRect(x * 4, y * 4, 4, 4); }
  // strata bands at height-level spacing
  for (let y = 0; y < TEX; y += LV) {
    const off = (r() - 0.5) * 4;
    ctx.fillStyle = rgba('#000000', 0.22); ctx.fillRect(0, y + off, TEX, 2.5);
    ctx.fillStyle = rgba(mix(base, '#ffffff', 0.4), 0.14); ctx.fillRect(0, y + off + 2.5, TEX, 1.5);
    ctx.fillStyle = rgba(r() < 0.5 ? '#000000' : '#ffffff', 0.06); ctx.fillRect(0, y + off + 4, TEX, LV / 2);
  }
  ctx.strokeStyle = 'rgba(0,0,0,0.3)'; ctx.lineWidth = 1;
  for (let i = 0; i < 40; i++) { const x = r() * TEX, y = r() * TEX; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + (r() - 0.5) * 6, y + 6 + r() * 14); ctx.stroke(); }
  sideCache.set(k, c);
  return c;
}

export function diamondPath(ctx: CanvasRenderingContext2D, sx: number, sy: number, inset = 0) {
  const w = TW / 2 - inset * 2, h = TH / 2 - inset;
  ctx.beginPath(); ctx.moveTo(sx, sy - h); ctx.lineTo(sx + w, sy); ctx.lineTo(sx, sy + h); ctx.lineTo(sx - w, sy); ctx.closePath();
}
/** Seamless canvas pattern of a terrain texture in world scale (1 px = 1 world px). */
const patCache = new Map<string, CanvasPattern>();
export function terrainPattern(ctx: CanvasRenderingContext2D, id: string, def: TerrainDef | undefined): CanvasPattern {
  const hit = patCache.get(id); if (hit) return hit;
  const p = ctx.createPattern(terrainTexture(id, def), 'repeat')!;
  p.setTransform(new DOMMatrix().scale(1 / RES));
  patCache.set(id, p); return p;
}
export function sidePattern(ctx: CanvasRenderingContext2D, id: string, def: TerrainDef | undefined, right: boolean): CanvasPattern {
  const k = `side|${id}|${right}`; const hit = patCache.get(k); if (hit) return hit;
  const p = ctx.createPattern(sideTexture(id, def, right), 'repeat')!;
  p.setTransform(new DOMMatrix().scale(1 / RES));
  patCache.set(k, p); return p;
}
export { TEX };

// ---- highlight glow sprites ----
const glowCache = new Map<string, HTMLCanvasElement>();
/** Soft glowing diamond inset for move/attack/area/deploy highlights. */
export function glowSprite(color: string, strength: number): HTMLCanvasElement {
  const k = `${color}|${strength}`; const hit = glowCache.get(k); if (hit) return hit;
  const pad = 14, W = TW + pad * 2, H = TH + pad * 2;
  const c = canvas(W * RES, H * RES), ctx = c.getContext('2d')!;
  ctx.scale(RES, RES);
  const sx = W / 2, sy = H / 2;
  if ('filter' in ctx) ctx.filter = 'blur(5px)';
  diamondPath(ctx, sx, sy, 3); ctx.fillStyle = rgba(color, 0.55 * strength); ctx.fill();
  ctx.filter = 'none';
  const g = ctx.createRadialGradient(sx, sy, 2, sx, sy, TW / 2);
  g.addColorStop(0, rgba(color, 0.08 * strength)); g.addColorStop(1, rgba(color, 0.42 * strength));
  diamondPath(ctx, sx, sy, 5); ctx.fillStyle = g; ctx.fill();
  ctx.strokeStyle = rgba(mix(color, '#ffffff', 0.5), 0.9 * strength); ctx.lineWidth = 1.6; diamondPath(ctx, sx, sy, 5); ctx.stroke();
  ctx.strokeStyle = rgba(color, 0.5 * strength); ctx.lineWidth = 3; diamondPath(ctx, sx, sy, 9); ctx.stroke();
  glowCache.set(k, c);
  return c;
}

// ---- backdrop ----
let backdrop: HTMLCanvasElement | null = null; let bdW = 0, bdH = 0;
/** Deep-sea dusk backdrop with light rays and vignette, cached per canvas size (device px). */
export function backdropFor(w: number, h: number): HTMLCanvasElement {
  if (backdrop && bdW === w && bdH === h) return backdrop;
  const c = canvas(w, h), ctx = c.getContext('2d')!;
  const sky = ctx.createLinearGradient(0, 0, 0, h);
  sky.addColorStop(0, '#7d7a78'); sky.addColorStop(0.2, '#5e5566'); sky.addColorStop(0.5, '#3b2f44'); sky.addColorStop(0.8, '#201a2a'); sky.addColorStop(1, '#0e0b14');
  ctx.fillStyle = sky; ctx.fillRect(0, 0, w, h);
  // luminous haze band (the lifted sea, never shown outright)
  const haze = ctx.createRadialGradient(w * 0.55, h * 0.1, 10, w * 0.55, h * 0.1, h * 0.9);
  haze.addColorStop(0, 'rgba(196,186,170,0.28)'); haze.addColorStop(0.5, 'rgba(120,130,120,0.08)'); haze.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = haze; ctx.fillRect(0, 0, w, h);
  // light rays from top-left
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const r = rng(77);
  for (let i = 0; i < 9; i++) {
    const x0 = w * (0.05 + r() * 0.5), ang = 0.9 + r() * 0.5, len = h * 1.6, wid = 30 + r() * 110;
    ctx.save(); ctx.translate(x0, -20); ctx.rotate(-Math.PI / 2 + ang);
    const g = ctx.createLinearGradient(0, 0, len, 0);
    g.addColorStop(0, `rgba(235,220,180,${0.05 + r() * 0.05})`); g.addColorStop(1, 'rgba(235,220,180,0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(0, -wid / 4); ctx.lineTo(len, -wid); ctx.lineTo(len, wid); ctx.lineTo(0, wid / 4); ctx.closePath(); ctx.fill();
    ctx.restore();
  }
  ctx.restore();
  // deep teal glow low down
  const deep = ctx.createRadialGradient(w * 0.5, h * 0.95, 10, w * 0.5, h * 0.95, w * 0.7);
  deep.addColorStop(0, 'rgba(60,40,90,0.35)'); deep.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = deep; ctx.fillRect(0, 0, w, h);
  // vignette
  const v = ctx.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.35, w / 2, h / 2, Math.max(w, h) * 0.75);
  v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,0.55)');
  ctx.fillStyle = v; ctx.fillRect(0, 0, w, h);
  // grain
  const rr = rng(5);
  for (let i = 0; i < (w * h) / 900; i++) { ctx.fillStyle = rr() < 0.5 ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.05)'; ctx.fillRect(rr() * w, rr() * h, 2, 2); }
  backdrop = c; bdW = w; bdH = h;
  return c;
}

// Live particle effects for anything gaseous or liquid: smoke, soot, ink, murk, mist, steam, salt plumes,
// rain clouds, spray and embers. Nothing here is a flat blob: every puff is a noise-shaped soft texture that
// drifts through a swirling flow field, spins, grows and fades, and emitters keep re-spawning them.
//
// Three ways in:
//  - stream(): a continuous emitter, called every frame (sprite emitters from the sheet manifest's `fx`
//    tracks, written by tools/spritegen/kit/fx.py, and status effects such as Inked or Sooted).
//  - area():   a lingering cloud over a patch of ground (spells and area abilities with a `vfx`).
//  - burst():  a one-shot puff (muzzle smoke, a murk-step vanish, a death).
// Textures are generated at load, so this adds no files to the build.

export type FxPreset = 'smoke' | 'soot' | 'ink' | 'murk' | 'mist' | 'steam' | 'salt' | 'cloud' | 'spray' | 'embers' | 'veil' | 'dust'
  | 'fire' | 'water' | 'bubbles' | 'motes' | 'gold' | 'heal' | 'tide' | 'shards' | 'coral' | 'feathers' | 'oil' | 'wind' | 'current';
export const FX_PRESETS: FxPreset[] = ['smoke', 'soot', 'ink', 'murk', 'mist', 'steam', 'salt', 'cloud', 'spray', 'embers', 'veil', 'dust',
  'fire', 'water', 'bubbles', 'motes', 'gold', 'heal', 'tide', 'shards', 'coral', 'feathers', 'oil', 'wind', 'current'];
export const isFxPreset = (s: unknown): s is FxPreset => typeof s === 'string' && (FX_PRESETS as string[]).includes(s);

type Kind = 'puff' | 'drop' | 'streak' | 'spark' | 'shard' | 'flake' | 'bubble';
type Layer = 'ground' | 'air';
interface Spec {
  kind: Kind; layer: Layer;
  colors: string[];            // picked per particle, for a little variation
  rate: number;                // particles per second at strength 1 (stream / area)
  life: [number, number];      // ms
  size: [number, number];      // radius px at birth -> at death (puffs); radius for drops/sparks
  alpha: number;
  vx: number; vy: number;      // initial velocity spread (vx: +-) and bias (vy: negative is up), px/s
  jitter: number;              // spawn position scatter, px
  swirl: number;               // flow-field strength, px/s^2
  spin: number;                // max rotation speed, rad/s
  flat: number;                // vertical squash (1 = round, 0.5 = lying on the ground)
  stretch?: number;            // elongate puffs along their motion (ink tendrils)
  g?: number;                  // gravity px/s^2
  drag?: number;               // velocity kept per second (0..1)
  blend?: GlobalCompositeOperation;
  extra?: { preset: FxPreset; share: number }; // also spawn some of another preset (rain under a cloud)
  trail?: number;              // streaks: trail length in seconds of travel
}

const SPECS: Record<FxPreset, Spec> = {
  smoke: { kind: 'puff', layer: 'air', colors: ['#8d877f', '#7a756f', '#a19a90'], rate: 14, life: [1300, 2100], size: [4, 17], alpha: 0.5, vx: 6, vy: -22, jitter: 2, swirl: 26, spin: 1.2, flat: 1, drag: 0.6 },
  soot: { kind: 'puff', layer: 'air', colors: ['#3b3632', '#2e2a27', '#4a433d'], rate: 14, life: [1200, 1900], size: [4, 15], alpha: 0.6, vx: 6, vy: -18, jitter: 2, swirl: 24, spin: 1.2, flat: 1, drag: 0.6 },
  ink: { kind: 'puff', layer: 'air', colors: ['#101a3c', '#0b1230', '#1b2a5a'], rate: 13, life: [1500, 2400], size: [3, 16], alpha: 0.8, vx: 12, vy: 5, jitter: 2, swirl: 34, spin: 1.6, flat: 0.9, stretch: 1.6, drag: 0.45 },
  murk: { kind: 'puff', layer: 'ground', colors: ['#171a2b', '#1f2438', '#122030'], rate: 12, life: [1400, 2200], size: [5, 18], alpha: 0.7, vx: 14, vy: -4, jitter: 3, swirl: 20, spin: 0.8, flat: 0.6, drag: 0.5 },
  mist: { kind: 'puff', layer: 'ground', colors: ['#c8dcb6', '#b7cfa3', '#d6e4c6'], rate: 10, life: [1800, 2800], size: [10, 30], alpha: 0.42, vx: 10, vy: -3, jitter: 6, swirl: 14, spin: 0.5, flat: 0.55, drag: 0.6 },
  steam: { kind: 'puff', layer: 'air', colors: ['#e9eef0', '#dfe6e8'], rate: 16, life: [800, 1300], size: [3, 14], alpha: 0.42, vx: 8, vy: -40, jitter: 2, swirl: 30, spin: 1.5, flat: 1, drag: 0.7 },
  salt: { kind: 'puff', layer: 'air', colors: ['#f4f1e8', '#e9e3d4', '#fffdf6'], rate: 18, life: [1100, 1700], size: [4, 16], alpha: 0.62, vx: 10, vy: -30, jitter: 3, swirl: 28, spin: 1.3, flat: 1, g: 9, drag: 0.55 },
  cloud: { kind: 'puff', layer: 'air', colors: ['#8e999f', '#a9b3b8', '#6f7a81'], rate: 16, life: [900, 1500], size: [7, 13], alpha: 0.8, vx: 7, vy: -2, jitter: 7, swirl: 16, spin: 0.8, flat: 0.75, drag: 0.4 },
  spray: { kind: 'drop', layer: 'air', colors: ['#dff4f2', '#bfe6e4', '#ffffff'], rate: 22, life: [350, 650], size: [1.1, 1.8], alpha: 0.85, vx: 40, vy: -45, jitter: 3, swirl: 0, spin: 0, flat: 1, g: 260, drag: 0.8, extra: { preset: 'steam', share: 0.2 } },
  embers: { kind: 'spark', layer: 'air', colors: ['#ffb347', '#ffd27a', '#ff7a33'], rate: 9, life: [600, 1200], size: [0.9, 1.6], alpha: 1, vx: 10, vy: -38, jitter: 5, swirl: 40, spin: 0, flat: 1, drag: 0.7, blend: 'lighter', extra: { preset: 'smoke', share: 0.5 } },
  veil: { kind: 'puff', layer: 'air', colors: ['#0a0c16', '#10142a', '#070912'], rate: 14, life: [1600, 2600], size: [8, 26], alpha: 0.65, vx: 12, vy: -6, jitter: 6, swirl: 22, spin: 0.7, flat: 0.75, drag: 0.5 },
  fire: { kind: 'puff', layer: 'air', colors: ['#ff9a3c', '#ffcf6b', '#ff6a2a'], rate: 22, life: [380, 700], size: [5, 13], alpha: 0.85, vx: 12, vy: -55, jitter: 4, swirl: 40, spin: 2, flat: 1, drag: 0.5, blend: 'lighter', extra: { preset: 'smoke', share: 0.25 } },
  water: { kind: 'drop', layer: 'air', colors: ['#7fc6d8', '#b6e4ee', '#e8fbff'], rate: 30, life: [500, 900], size: [1.6, 2.6], alpha: 0.9, vx: 30, vy: -120, jitter: 5, swirl: 0, spin: 0, flat: 1, g: 340, drag: 0.85, extra: { preset: 'spray', share: 0.25 } },
  bubbles: { kind: 'bubble', layer: 'air', colors: ['#a8e8f0', '#d8fbff', '#7fd8e0'], rate: 10, life: [900, 1600], size: [1.6, 3.6], alpha: 0.8, vx: 6, vy: -34, jitter: 8, swirl: 30, spin: 0, flat: 1, drag: 0.8 },
  motes: { kind: 'spark', layer: 'air', colors: ['#9fe8ff', '#d4f6ff', '#6fd0ff'], rate: 14, life: [900, 1600], size: [1.2, 2.2], alpha: 1, vx: 10, vy: -30, jitter: 10, swirl: 30, spin: 0, flat: 1, drag: 0.8, blend: 'lighter' },
  gold: { kind: 'spark', layer: 'air', colors: ['#ffe08a', '#fff2c4', '#ffc24d'], rate: 14, life: [900, 1600], size: [1.3, 2.4], alpha: 1, vx: 10, vy: -30, jitter: 10, swirl: 26, spin: 0, flat: 1, drag: 0.8, blend: 'lighter' },
  heal: { kind: 'spark', layer: 'air', colors: ['#8ff0a0', '#c8ffd0', '#5fd88a'], rate: 14, life: [900, 1500], size: [1.3, 2.4], alpha: 1, vx: 8, vy: -40, jitter: 12, swirl: 22, spin: 0, flat: 1, drag: 0.8, blend: 'lighter' },
  tide: { kind: 'spark', layer: 'air', colors: ['#7fe0ff', '#bff4ff', '#4fc8e8'], rate: 14, life: [700, 1200], size: [1.4, 2.6], alpha: 1, vx: 12, vy: -60, jitter: 10, swirl: 50, spin: 0, flat: 1, drag: 0.9, blend: 'lighter' },
  shards: { kind: 'shard', layer: 'air', colors: ['#f4f1e8', '#dfe8ee', '#ffffff'], rate: 20, life: [500, 900], size: [2.4, 4.2], alpha: 1, vx: 50, vy: -110, jitter: 6, swirl: 0, spin: 9, flat: 1, g: 380, drag: 0.85 },
  coral: { kind: 'shard', layer: 'air', colors: ['#e07a6a', '#f2a08c', '#d9d0c2'], rate: 20, life: [600, 1000], size: [2.6, 4.6], alpha: 1, vx: 30, vy: -130, jitter: 8, swirl: 0, spin: 7, flat: 1, g: 360, drag: 0.85, extra: { preset: 'mist', share: 0.15 } },
  feathers: { kind: 'flake', layer: 'air', colors: ['#3a3f4a', '#5d6470', '#e8e2d6', '#2a2d34'], rate: 12, life: [1400, 2400], size: [3, 4.5], alpha: 1, vx: 40, vy: -20, jitter: 10, swirl: 70, spin: 4, flat: 1, g: 30, drag: 0.55 },
  oil: { kind: 'drop', layer: 'air', colors: ['#3a2a14', '#5c3d16', '#d98a2b'], rate: 24, life: [500, 800], size: [1.8, 2.8], alpha: 0.95, vx: 45, vy: -90, jitter: 6, swirl: 0, spin: 0, flat: 1, g: 360, drag: 0.85 },
  wind: { kind: 'streak', layer: 'air', colors: ['#ffffff', '#e8f0f4'], rate: 10, life: [500, 900], size: [1.1, 1.1], alpha: 0.75, vx: 0, vy: 0, jitter: 0, swirl: 0, spin: 0, flat: 1, trail: 0.12 },
  current: { kind: 'streak', layer: 'air', colors: ['#7fe0ff', '#bff4ff', '#4fb8d8'], rate: 10, life: [500, 900], size: [1.3, 1.3], alpha: 0.85, vx: 0, vy: 0, jitter: 0, swirl: 0, spin: 0, flat: 1, trail: 0.12, blend: 'lighter' },
  dust: { kind: 'puff', layer: 'air', colors: ['#c9c2b0', '#b5ad99', '#d8d1bf'], rate: 12, life: [700, 1200], size: [3, 12], alpha: 0.45, vx: 26, vy: -14, jitter: 6, swirl: 18, spin: 1, flat: 0.8, drag: 0.35 },
};
// rain falls out of the cloud as streaks
const RAIN: Spec = { kind: 'streak', layer: 'air', colors: ['#cfe3ee', '#a9c8d8'], rate: 0, life: [260, 380], size: [5, 5], alpha: 0.6, vx: 4, vy: 150, jitter: 7, swirl: 0, spin: 0, flat: 1, g: 300, drag: 1 };

interface Particle {
  spec: Spec; x: number; y: number; vx: number; vy: number; born: number; life: number;
  r0: number; r1: number; rot: number; vr: number; a: number; tex: CanvasImageSource | null; color: string; seed: number;
  orbit?: { cx: number; cy: number; r: number; w: number; dr: number; lift: number; dl: number };
}
/** A projectile: a glowing head with a trail, flying from one point to another. */
const COMET: Spec = { kind: 'streak', layer: 'air', colors: ['#ffffff'], rate: 0, life: [0, 0], size: [2.4, 2.4], alpha: 1, vx: 0, vy: 0, jitter: 0, swirl: 0, spin: 0, flat: 1, drag: 1, blend: 'lighter', trail: 0.09 };
interface Area { preset: FxPreset; x: number; y: number; rx: number; start: number; end: number; strength: number; acc: number; scale: number }

const MAX = 900;

// ---------------------------------------------------------------- textures

const VARIANTS = 6, TEX = 64;
let base: HTMLCanvasElement[] | null = null;
const tinted = new Map<string, HTMLCanvasElement>();

function hash(x: number, y: number, s: number) { let h = (x * 374761393 + y * 668265263 + s * 2147483647) | 0; h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
function vnoise(x: number, y: number, s: number) {
  const ix = Math.floor(x), iy = Math.floor(y), fx = x - ix, fy = y - iy;
  const u = fx * fx * (3 - 2 * fx), v = fy * fy * (3 - 2 * fy);
  const a = hash(ix, iy, s), b = hash(ix + 1, iy, s), c = hash(ix, iy + 1, s), d = hash(ix + 1, iy + 1, s);
  return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
}
function fbm(x: number, y: number, s: number) { return vnoise(x, y, s) * 0.55 + vnoise(x * 2.1, y * 2.1, s + 7) * 0.3 + vnoise(x * 4.3, y * 4.3, s + 13) * 0.15; }

/** Soft, lumpy puffs: a radial falloff whose edge is eaten by noise, with billowy density inside. */
function baseTextures(): HTMLCanvasElement[] {
  if (base) return base;
  base = [];
  for (let v = 0; v < VARIANTS; v++) {
    const c = document.createElement('canvas'); c.width = c.height = TEX;
    const x = c.getContext('2d')!, img = x.createImageData(TEX, TEX), h = TEX / 2;
    for (let j = 0; j < TEX; j++) for (let i = 0; i < TEX; i++) {
      const dx = (i + 0.5 - h) / h, dy = (j + 0.5 - h) / h, r = Math.hypot(dx, dy);
      const n = fbm(i / 11 + v * 3.1, j / 11 + v * 1.7, v * 17 + 1);
      const edge = 0.62 + 0.38 * n;                       // ragged outline
      let a = Math.max(0, 1 - r / edge); a = a * a * (3 - 2 * a);
      a *= 0.45 + 0.75 * fbm(i / 6 + v, j / 6 - v, v * 31 + 5); // billows inside
      // lit from the upper left: lighter there, a touch darker underneath
      const lit = 0.82 + 0.3 * (-dx * 0.55 - dy * 0.8) * 0.5 + 0.12 * (n - 0.5);
      const k = (j * TEX + i) * 4, l = Math.max(0, Math.min(255, 255 * lit));
      img.data[k] = l; img.data[k + 1] = l; img.data[k + 2] = l; img.data[k + 3] = Math.min(255, 255 * a);
    }
    x.putImageData(img, 0, 0);
    base.push(c);
  }
  return base;
}
function texture(v: number, color: string): HTMLCanvasElement {
  const key = v + color;
  let t = tinted.get(key);
  if (!t) {
    const b = baseTextures()[v];
    t = document.createElement('canvas'); t.width = t.height = TEX;
    const x = t.getContext('2d')!;
    x.drawImage(b, 0, 0);
    x.globalCompositeOperation = 'multiply'; x.fillStyle = color; x.fillRect(0, 0, TEX, TEX); // shade x tint
    x.globalCompositeOperation = 'destination-in'; x.drawImage(b, 0, 0);                         // keep the puff's alpha
    tinted.set(key, t);
  }
  return t;
}

// ---------------------------------------------------------------- system

export class Fx {
  private ps: Particle[] = [];
  private areas: Area[] = [];
  private acc = new Map<string, { a: number; seen: number }>();
  reduced = false;

  clear() { this.ps = []; this.areas = []; this.acc.clear(); }
  get count() { return this.ps.length; }

  private spawn(spec: Spec, x: number, y: number, now: number, strength = 1, push?: { vx: number; vy: number }, scale = 1) {
    if (this.ps.length >= MAX) this.ps.shift();
    const rnd = Math.random, j = spec.jitter * (0.6 + 0.4 * strength);
    const life = (spec.life[0] + rnd() * (spec.life[1] - spec.life[0])) * (1 + (scale - 1) * 0.35);
    const sizeK = (0.75 + 0.25 * Math.min(2, strength)) * scale;
    const color = spec.colors[(rnd() * spec.colors.length) | 0];
    const p: Particle = {
      spec, x: x + (rnd() - 0.5) * 2 * j, y: y + (rnd() - 0.5) * 2 * j * spec.flat, born: now, life,
      vx: (rnd() - 0.5) * 2 * spec.vx + (push?.vx ?? 0), vy: spec.vy * (0.6 + 0.6 * rnd()) + (push?.vy ?? 0),
      r0: spec.size[0] * sizeK * (0.8 + 0.4 * rnd()), r1: spec.size[1] * sizeK * (0.8 + 0.4 * rnd()),
      rot: rnd() * Math.PI * 2, vr: (rnd() - 0.5) * 2 * spec.spin, a: spec.alpha * (0.75 + 0.25 * rnd()),
      tex: spec.kind === 'puff' ? texture((rnd() * VARIANTS) | 0, color) : null, color, seed: rnd() * 100,
    };
    this.ps.push(p);
    if (spec.extra && spec.extra.share > 0 && rnd() < spec.extra.share) this.spawn(SPECS[spec.extra.preset], x, y, now, strength * 0.6, undefined, scale);
    if (spec === SPECS.cloud && rnd() < 0.9) this.spawn(RAIN, x + (rnd() - 0.5) * 14 * scale, y + 4, now, 1); // it rains
  }

  /** Continuous emitter: call every frame with the frame's dt. `key` keeps its fractional spawn budget. */
  stream(key: string, preset: FxPreset, x: number, y: number, strength: number, dt: number, now: number, scale = 1) {
    const spec = SPECS[preset]; if (!spec || strength <= 0) return;
    const e = this.acc.get(key) ?? { a: Math.random(), seen: now };
    e.a += spec.rate * strength * (this.reduced ? 0.4 : 1) * dt / 1000; e.seen = now;
    while (e.a >= 1) { e.a -= 1; this.spawn(spec, x, y, now, strength, undefined, scale); }
    this.acc.set(key, e);
  }

  /** A lingering cloud over an elliptical patch of ground (rx px wide, half as tall), for `ms`. */
  area(preset: FxPreset, x: number, y: number, rx: number, ms: number, now: number, strength = 1) {
    const scale = 1.6 + rx / 90; // a patch of ground wants billows, not wisps
    if (preset === 'cloud') y -= 70; // rain clouds hang over the area and rain onto it
    this.areas.push({ preset, x, y, rx, start: now, end: now + ms, strength, acc: 0, scale });
    this.burst(preset, x, y, Math.round(10 + rx / 5), { radius: rx * 0.8, strength, scale });
  }

  /** One-shot puff of `n` particles, optionally scattered over `radius` and thrown along `push`. */
  burst(preset: FxPreset, x: number, y: number, n: number, o: { radius?: number; strength?: number; push?: { vx: number; vy: number }; scale?: number } = {}) {
    const spec = SPECS[preset]; if (!spec) return;
    const now = performance.now(), r = o.radius ?? 0;
    for (let i = 0; i < (this.reduced ? Math.ceil(n / 2) : n); i++) {
      const a = Math.random() * Math.PI * 2, d = Math.sqrt(Math.random()) * r;
      this.spawn(spec, x + Math.cos(a) * d, y + Math.sin(a) * d * 0.5, now, o.strength ?? 1, o.push, o.scale ?? 1);
    }
  }

  /** A glowing projectile from (x0,y0) to (x1,y1) arriving in `ms`; `color` tints its trail. */
  comet(x0: number, y0: number, x1: number, y1: number, ms: number, color: string, size = 2.4) {
    const now = performance.now(), s = ms / 1000;
    this.ps.push({ spec: { ...COMET, colors: [color] }, x: x0, y: y0, vx: (x1 - x0) / s, vy: (y1 - y0) / s, born: now, life: ms,
      r0: size, r1: size, rot: 0, vr: 0, a: 1, tex: null, color, seed: 0 });
  }

  /** `n` particles circling (cx,cy): radius r, spiralling by dr px/s (negative pulls in), rising dl px/s. */
  vortex(preset: FxPreset, cx: number, cy: number, n: number, r: number, o: { w?: number; dr?: number; dl?: number; scale?: number; ms?: number } = {}) {
    const spec = SPECS[preset]; if (!spec) return;
    const now = performance.now();
    for (let i = 0; i < (this.reduced ? Math.ceil(n / 2) : n); i++) {
      this.spawn(spec, cx, cy, now, 1, undefined, o.scale ?? 1);
      const p = this.ps[this.ps.length - 1];
      p.seed = Math.random() * Math.PI * 2; p.born = now - Math.random() * 120;
      if (o.ms) p.life = o.ms * (0.7 + 0.3 * Math.random());
      p.orbit = { cx, cy, r: r * (0.6 + 0.5 * Math.random()), w: (o.w ?? 4) * (0.8 + 0.4 * Math.random()), dr: o.dr ?? 0, lift: Math.random() * 6, dl: o.dl ?? 0 };
    }
  }

  /** A fountain: `n` particles thrown upward from (x,y) over a ring of `radius`. */
  fountain(preset: FxPreset, x: number, y: number, n: number, radius = 0, up = 1, scale = 1) {
    const spec = SPECS[preset]; if (!spec) return;
    const now = performance.now();
    for (let i = 0; i < (this.reduced ? Math.ceil(n / 2) : n); i++) {
      const a = Math.random() * Math.PI * 2, d = Math.sqrt(Math.random()) * radius;
      this.spawn(spec, x + Math.cos(a) * d, y + Math.sin(a) * d * 0.5, now, 1, { vx: Math.cos(a) * 20, vy: spec.vy * (up - 1) }, scale);
    }
  }

  update(now: number, dt: number) {
    const s = dt / 1000;
    // area clouds: dense at first, thinning as they lift
    for (const ar of this.areas) {
      const spec = SPECS[ar.preset], k = (now - ar.start) / (ar.end - ar.start);
      ar.acc += spec.rate * (0.6 + ar.rx / 60) * ar.strength * (1 - k) * (this.reduced ? 0.4 : 1) * s;
      while (ar.acc >= 1) { ar.acc -= 1; const a = Math.random() * Math.PI * 2, d = Math.sqrt(Math.random()) * ar.rx; this.spawn(spec, ar.x + Math.cos(a) * d, ar.y + Math.sin(a) * d * 0.5, now, ar.strength, undefined, ar.scale); }
    }
    this.areas = this.areas.filter(a => now < a.end);
    for (const [k, e] of this.acc) if (now - e.seen > 1000) this.acc.delete(k);
    if (!this.ps.length) return;
    this.ps = this.ps.filter(p => now - p.born < p.life);
    const t = now / 1000;
    for (const p of this.ps) {
      const sp = p.spec;
      const o = p.orbit;
      if (o) { // vortex: circle the centre, spiralling in or out, rising
        o.r = Math.max(2, o.r + o.dr * s); o.lift += o.dl * s; p.rot += o.w * s;
        const a = p.seed + (now - p.born) / 1000 * o.w;
        p.vx = (o.cx + Math.cos(a) * o.r - p.x) / Math.max(s, 0.001); p.vy = (o.cy + Math.sin(a) * o.r * 0.5 - o.lift - p.y) / Math.max(s, 0.001);
        p.x = o.cx + Math.cos(a) * o.r; p.y = o.cy + Math.sin(a) * o.r * 0.5 - o.lift;
        continue;
      }
      if (sp.swirl && !this.reduced) { // cheap curl-ish flow: two crossed sine fields that drift over time
        p.vx += sp.swirl * Math.sin(p.y * 0.06 + t * 1.3 + p.seed) * s;
        p.vy += sp.swirl * 0.6 * Math.cos(p.x * 0.07 - t * 1.1 + p.seed * 1.7) * s;
      }
      if (sp.g) p.vy += sp.g * s;
      if (sp.drag !== undefined && sp.drag < 1) { const d = Math.pow(sp.drag, s); p.vx *= d; p.vy *= d; }
      p.x += p.vx * s; p.y += p.vy * s; p.rot += p.vr * s;
    }
  }

  /** Draw one layer ('ground' sits under the units, 'air' over them) in the board's world transform. */
  draw(ctx: CanvasRenderingContext2D, layer: Layer, now: number) {
    if (!this.ps.length) return;
    const m = ctx.getTransform();
    ctx.save();
    for (const p of this.ps) {
      const sp = p.spec; if (sp.layer !== layer) continue;
      const k = (now - p.born) / p.life; if (k < 0) continue;
      const fade = sp === COMET || sp.rate === 0 && sp.trail ? Math.min(1, (1 - k) / 0.1) : Math.min(1, k / 0.14) * Math.pow(1 - k, 1.4);
      ctx.globalAlpha = Math.max(0, p.a * fade);
      ctx.globalCompositeOperation = sp.blend ?? 'source-over';
      if (sp.kind === 'puff') {
        const r = p.r0 + (p.r1 - p.r0) * (1 - (1 - k) * (1 - k));
        const v = Math.hypot(p.vx, p.vy), st = sp.stretch ? 1 + (sp.stretch - 1) * Math.min(1, v / 25) : 1;
        const ang = sp.stretch ? Math.atan2(p.vy, p.vx) : p.rot;
        ctx.setTransform(m);
        ctx.translate(p.x, p.y); ctx.scale(1, sp.flat); ctx.rotate(ang);
        if (sp.stretch) ctx.rotate(p.rot * 0.25);
        ctx.drawImage(p.tex!, -r * st, -r, 2 * r * st, 2 * r);
      } else {
        ctx.setTransform(m);
        ctx.fillStyle = p.color; ctx.strokeStyle = p.color;
        if (sp.kind === 'streak') {
          const tl = sp.trail ?? 0.03;
          ctx.lineWidth = sp.trail ? p.r0 * 1.4 : 1; ctx.lineCap = 'round';
          if (sp.trail) { const gr = ctx.createLinearGradient(p.x, p.y, p.x - p.vx * tl, p.y - p.vy * tl); gr.addColorStop(0, p.color); gr.addColorStop(1, 'rgba(255,255,255,0)'); ctx.strokeStyle = gr; }
          ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p.x - p.vx * tl, p.y - p.vy * tl); ctx.stroke();
          if (sp.trail && sp.rate === 0) { ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.arc(p.x, p.y, p.r0 * 1.2, 0, Math.PI * 2); ctx.fill(); }
        } else if (sp.kind === 'shard') {
          ctx.translate(p.x, p.y); ctx.rotate(p.rot); const r = p.r0;
          ctx.beginPath(); ctx.moveTo(0, -r * 1.6); ctx.lineTo(r * 0.7, 0); ctx.lineTo(0, r * 1.2); ctx.lineTo(-r * 0.6, 0); ctx.closePath(); ctx.fill();
          ctx.globalAlpha *= 0.5; ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.moveTo(0, -r * 1.6); ctx.lineTo(r * 0.7, 0); ctx.lineTo(0, 0); ctx.closePath(); ctx.fill();
        } else if (sp.kind === 'flake') {
          ctx.translate(p.x, p.y); ctx.rotate(p.rot); const r = p.r0, w = Math.abs(Math.sin(p.seed + now / 160)) * 0.7 + 0.3; // tumbling
          ctx.beginPath(); ctx.ellipse(0, 0, r * 2, r * 0.75 * w, 0, 0, Math.PI * 2); ctx.fill();
          ctx.strokeStyle = 'rgba(0,0,0,0.35)'; ctx.lineWidth = 0.6; ctx.beginPath(); ctx.moveTo(-r * 2.2, 0); ctx.lineTo(r * 2, 0); ctx.stroke();
        } else if (sp.kind === 'bubble') {
          const r = p.r0 + (p.r1 - p.r0) * k; ctx.lineWidth = 0.9;
          ctx.beginPath(); ctx.arc(p.x + Math.sin(now / 140 + p.seed) * 1.5, p.y, r, 0, Math.PI * 2); ctx.stroke();
          ctx.fillStyle = 'rgba(255,255,255,0.8)'; ctx.beginPath(); ctx.arc(p.x - r * 0.35, p.y - r * 0.35, r * 0.25, 0, Math.PI * 2); ctx.fill();
        } else {
          const r = sp.kind === 'spark' ? p.r0 * (1 - k * 0.6) : p.r0;
          ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, Math.PI * 2); ctx.fill();
        }
      }
    }
    ctx.restore();
  }
}

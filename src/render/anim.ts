// Unit art + frame-animation adapter. The renderer only asks: "frame image + source rect for state S at time t".
// Supports (1) sprite sheets: sprite.sheet (png) + sprite.manifest (json), (2) per-frame lists in sprite.animations,
// (3) the still sprite.image. All paths are "sprites/..." relative to content/ and resolved by a UI-side glob.
import type { UnitDef } from '../engine/types';

export type AnimState = 'idle' | 'move' | 'attack' | 'cast' | 'hit' | 'death';

interface SheetAnim { row: number; frames: number; fps: number; loop?: boolean; hitFrame?: number; holdLast?: boolean }
export interface Manifest {
  frameWidth: number; frameHeight: number; anchor?: [number, number]; facing?: string;
  animations: Partial<Record<AnimState, SheetAnim>>;
}
interface FrameAnim { frames: string[]; fps?: number; loop?: boolean; hitFrame?: number; holdLast?: boolean }
/** Content-side extensions of UnitDef.sprite that the engine types do not know about. */
export type SpriteExt = UnitDef['sprite'] & {
  sheet?: string; manifest?: string;
  animations?: Partial<Record<AnimState | 'walk', FrameAnim>>;
};

const urls = import.meta.glob('../../content/sprites/**/*.{svg,png,webp,jpg,jpeg,gif}', { eager: true, query: '?url', import: 'default' }) as Record<string, string>;
const manifests = import.meta.glob('../../content/sprites/**/*.json', { eager: true, import: 'default' }) as Record<string, unknown>;

/** Resolve a content-relative asset path ("sprites/x.svg") to a built URL; absolute/data URLs pass through. */
export function assetUrl(p: string | undefined): string | undefined {
  if (!p) return undefined;
  if (/^(https?:|data:|\/|blob:)/.test(p)) return p;
  return urls[`../../content/${p}`];
}
function manifestFor(p: string | undefined): Manifest | undefined {
  if (!p) return undefined;
  return manifests[`../../content/${p}`] as Manifest | undefined;
}

const images = new Map<string, HTMLImageElement>();
export function getImage(src: string): HTMLImageElement | null {
  let img = images.get(src);
  if (!img) { img = new Image(); img.src = src; images.set(src, img); }
  return img.complete && img.naturalWidth > 0 ? img : null;
}

export interface Frame {
  img: HTMLImageElement;
  sx: number; sy: number; sw: number; sh: number;   // source rect
  ax: number; ay: number;                           // anchor (feet) inside the source rect
  scale: number;                                    // world px per source px
  done: boolean;                                    // non-looping animation has finished
  index: number;
}

type Clip = { kind: 'sheet'; img: string; a: SheetAnim; m: Manifest } | { kind: 'frames'; a: FrameAnim; srcs: string[] };
interface UnitArt { still?: string; clips: Partial<Record<AnimState, Clip>>; animated: boolean }

const artCache = new Map<string, UnitArt>();
export function unitArt(defId: string, def: UnitDef): UnitArt {
  const hit = artCache.get(defId); if (hit) return hit;
  const sp = def.sprite as SpriteExt;
  const art: UnitArt = { still: sp.image, clips: {}, animated: false };
  const sheet = assetUrl(sp.sheet), man = manifestFor(sp.manifest);
  if (sheet && man?.animations) {
    for (const [k, a] of Object.entries(man.animations)) if (a) art.clips[k as AnimState] = { kind: 'sheet', img: sheet, a, m: man };
  }
  if (sp.animations) {
    for (const [k0, a] of Object.entries(sp.animations)) {
      const k = (k0 === 'walk' ? 'move' : k0) as AnimState;
      if (!a?.frames?.length || art.clips[k]) continue;
      const srcs = a.frames.map(f => assetUrl(f)).filter((u): u is string => !!u);
      if (srcs.length) art.clips[k] = { kind: 'frames', a, srcs };
    }
  }
  if (!art.clips.cast && art.clips.attack) art.clips.cast = art.clips.attack;
  art.animated = Object.keys(art.clips).length > 0;
  artCache.set(defId, art);
  return art;
}

/** Natural target height of a still image in world px, and its foot anchor. */
function stillLayout(img: HTMLImageElement, structure: boolean) {
  const w = img.naturalWidth, h = img.naturalHeight;
  const spec = Math.abs(w / h - 96 / 112) < 0.02; // the 96x112 spec with feet at (48,104)
  const ax = w / 2, ay = spec ? h * (104 / 112) : h * 0.92;
  const target = structure ? 150 : spec ? 112 : 96;
  return { ax, ay, scale: target / h };
}

/** Duration in ms of a non-looping clip, or undefined when procedural. */
export function clipDuration(art: UnitArt, state: AnimState): number | undefined {
  const c = art.clips[state]; if (!c) return undefined;
  const n = c.kind === 'sheet' ? c.a.frames : c.srcs.length, fps = c.a.fps || 8;
  return n / fps * 1000;
}
/** Time (ms from clip start) of the hit frame of an attack/cast clip, if any. */
export function clipHitTime(art: UnitArt, state: AnimState): number | undefined {
  const c = art.clips[state]; if (!c || c.a.hitFrame === undefined) return undefined;
  return c.a.hitFrame / (c.a.fps || 8) * 1000;
}

/**
 * The frame to draw for a unit in `state`, `elapsed` ms after the state began. Returns null when no image is
 * ready yet (the caller draws a placeholder figure).
 */
export function frameFor(art: UnitArt, state: AnimState, elapsed: number, structure: boolean): Frame | null {
  const clip = art.clips[state] ?? (state !== 'idle' ? art.clips.idle : undefined);
  if (clip) {
    const n = clip.kind === 'sheet' ? clip.a.frames : clip.srcs.length;
    const fps = clip.a.fps || 8;
    const loop = clip.a.loop ?? (state === 'idle' || state === 'move');
    let i = Math.floor(elapsed / 1000 * fps);
    let done = false;
    if (loop) i = ((i % n) + n) % n; else if (i >= n) { i = n - 1; done = true; }
    if (clip.kind === 'sheet') {
      const img = getImage(clip.img);
      if (img) {
        const fw = clip.m.frameWidth || 96, fh = clip.m.frameHeight || 112;
        const [ax, ay] = clip.m.anchor ?? [fw / 2, fh * 104 / 112];
        return { img, sx: i * fw, sy: clip.a.row * fh, sw: fw, sh: fh, ax, ay, scale: structure ? 150 / fh : 1, done, index: i };
      }
    } else {
      const img = getImage(clip.srcs[i]) ?? getImage(clip.srcs[0]);
      if (img) { const l = stillLayout(img, structure); return { img, sx: 0, sy: 0, sw: img.naturalWidth, sh: img.naturalHeight, ...l, done, index: i }; }
    }
  }
  if (art.still) {
    const img = getImage(art.still);
    if (img) { const l = stillLayout(img, structure); return { img, sx: 0, sy: 0, sw: img.naturalWidth, sh: img.naturalHeight, ...l, done: false, index: 0 }; }
  }
  return null;
}

/** Card art resolver: "cards/<id>.svg" via the `art` field, or by id convention. */
const cardUrls = import.meta.glob('../../content/cards/*', { eager: true, query: '?url', import: 'default' }) as Record<string, string>;
export function cardArtUrl(id: string, def: { art?: string } | undefined): string | undefined {
  const a = def?.art;
  if (a) { if (/^(https?:|data:|\/)/.test(a)) return a; const u = cardUrls[`../../content/${a}`]; if (u) return u; }
  return cardUrls[`../../content/cards/${id}.svg`] ?? cardUrls[`../../content/cards/${id}.png`];
}

// Web Audio core: one AudioContext, a master bus with music / sfx / ambience sub-buses, persisted volume
// settings, lazy buffer loading with a small preload queue, and one-shot + looping players.
// All sample files come from licensed packs (see CREDITS.md); nothing in here synthesises sound.

export type Channel = 'master' | 'music' | 'sfx' | 'ambience';
export interface AudioSettings { master: number; music: number; sfx: number; ambience: number; muted: boolean }

const KEY = 'brinewake.audio';
const OLD_MUTE_KEY = 'brinewake.muted';
const DEFAULTS: AudioSettings = { master: 0.8, music: 0.55, sfx: 0.8, ambience: 0.7, muted: false };

const sfxFiles = import.meta.glob('./assets/sfx/*.mp3', { eager: true, query: '?url', import: 'default' }) as Record<string, string>;
const accentFiles = import.meta.glob('./assets/accent/*.mp3', { eager: true, query: '?url', import: 'default' }) as Record<string, string>;
const bedFiles = import.meta.glob('./assets/amb/*.mp3', { eager: true, query: '?url', import: 'default' }) as Record<string, string>;
const musicFiles = import.meta.glob('./assets/music/*.mp3', { eager: true, query: '?url', import: 'default' }) as Record<string, string>;

function bank(files: Record<string, string>): Record<string, string[]> {
  const out: Record<string, string[]> = {};
  for (const [path, url] of Object.entries(files).sort(([a], [b]) => a.localeCompare(b, undefined, { numeric: true }))) {
    const m = /\/([a-z_]+?)_\d+\.mp3$/.exec(path);
    if (m) (out[m[1]] ??= []).push(url);
  }
  return out;
}
function named(files: Record<string, string>): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [path, url] of Object.entries(files)) { const m = /\/([a-z_]+)\.mp3$/.exec(path); if (m) out[m[1]] = url; }
  return out;
}

export const banks = bank(sfxFiles);
export const accents = bank(accentFiles);
export const beds = named(bedFiles);
export const tracks = named(musicFiles);

let settings: AudioSettings = readSettings();
const listeners = new Set<(s: AudioSettings) => void>();

function readSettings(): AudioSettings {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return { ...DEFAULTS, ...JSON.parse(raw) };
    if (localStorage.getItem(OLD_MUTE_KEY) === '1') return { ...DEFAULTS, muted: true };
  } catch { /* storage unavailable */ }
  return { ...DEFAULTS };
}

export function getSettings(): AudioSettings { return { ...settings }; }
export function onSettingsChange(fn: (s: AudioSettings) => void): () => void { listeners.add(fn); return () => listeners.delete(fn); }
export function isMuted() { return settings.muted; }
export function setMuted(m: boolean) { patch({ muted: m }); }
export function setVolume(ch: Channel, v: number) { patch({ [ch]: Math.min(1, Math.max(0, v)) } as Partial<AudioSettings>); }

function patch(p: Partial<AudioSettings>) {
  settings = { ...settings, ...p };
  try { localStorage.setItem(KEY, JSON.stringify(settings)); } catch { /* storage unavailable */ }
  applyGains();
  for (const fn of listeners) fn(getSettings());
}

// ---------- graph ----------
let ctx: AudioContext | null = null;
let masterGain: GainNode, musicBus: GainNode, sfxBus: GainNode, ambBus: GainNode;
let sfxComp: DynamicsCompressorNode;
// Per-channel scene gains (ducking, fades) multiply the user's slider.
const scene = { music: 1, ambience: 1 };

export function audio(): AudioContext | null {
  if (ctx) return ctx;
  const AC = (globalThis as { AudioContext?: typeof AudioContext }).AudioContext
    ?? (globalThis as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AC) return null;
  ctx = new AC();
  masterGain = ctx.createGain();
  musicBus = ctx.createGain(); sfxBus = ctx.createGain(); ambBus = ctx.createGain();
  // A gentle limiter on the sfx bus keeps a 6-unit spell or a big volley from clipping.
  sfxComp = ctx.createDynamicsCompressor();
  sfxComp.threshold.value = -14; sfxComp.knee.value = 10; sfxComp.ratio.value = 4; sfxComp.attack.value = 0.004; sfxComp.release.value = 0.2;
  sfxBus.connect(sfxComp).connect(masterGain);
  musicBus.connect(masterGain); ambBus.connect(masterGain);
  masterGain.connect(ctx.destination);
  applyGains(true);
  return ctx;
}

function curve(v: number) { return v * v; } // slider position -> perceptual gain

function applyGains(immediate = false) {
  if (!ctx) return;
  const t = ctx.currentTime, k = immediate ? 0.001 : 0.04;
  const m = settings.muted ? 0 : curve(settings.master);
  masterGain.gain.setTargetAtTime(m, t, k);
  musicBus.gain.setTargetAtTime(curve(settings.music) * scene.music, t, immediate ? 0.001 : 0.25);
  sfxBus.gain.setTargetAtTime(curve(settings.sfx), t, k);
  ambBus.gain.setTargetAtTime(curve(settings.ambience) * scene.ambience, t, immediate ? 0.001 : 0.4);
}

/** Duck or restore a scene channel (e.g. music under a victory stinger). */
export function setSceneGain(ch: 'music' | 'ambience', v: number) { scene[ch] = v; applyGains(); }

// ---------- loading ----------
const buffers = new Map<string, AudioBuffer>();
const loading = new Map<string, Promise<AudioBuffer | null>>();

export function load(url: string): Promise<AudioBuffer | null> {
  const ac = audio();
  if (!ac) return Promise.resolve(null);
  const hit = buffers.get(url);
  if (hit) return Promise.resolve(hit);
  let p = loading.get(url);
  if (!p) {
    p = fetch(url).then(r => r.arrayBuffer()).then(b => ac.decodeAudioData(b)).then(buf => { buffers.set(url, buf); return buf; }).catch(() => { loading.delete(url); return null; });
    loading.set(url, p);
  }
  return p;
}

/** Preload in the background, a few at a time, so first use is instant without blocking the page. */
export function preload(urls: string[], concurrency = 3): Promise<void> {
  const queue = urls.filter(u => !buffers.has(u));
  return new Promise(resolve => {
    let active = 0;
    const next = () => {
      if (!queue.length && active === 0) { resolve(); return; }
      while (active < concurrency && queue.length) {
        const u = queue.shift()!; active++;
        void load(u).then(() => { active--; next(); });
      }
    };
    next();
  });
}

export function running(): boolean { return !!ctx && ctx.state === 'running'; }

// ---------- one-shots ----------
export interface PlayOpts { volume?: number; rate?: number; jitter?: number; minGap?: number; pan?: number; delay?: number; bus?: 'sfx' | 'ambience' | 'music' }
const lastPlayed = new Map<string, number>();

/** Play a random variant from a bank, with pitch/volume jitter so repeats don't sound mechanical. */
export function play(name: string, opts: PlayOpts = {}, source: Record<string, string[]> = banks): boolean {
  const urls = source[name];
  const ac = audio();
  if (settings.muted || !urls?.length || !ac || ac.state !== 'running') return false;
  const now = performance.now();
  if (now - (lastPlayed.get(name) ?? -1e9) < (opts.minGap ?? 35)) return false;
  lastPlayed.set(name, now);
  const url = urls[Math.floor(Math.random() * urls.length)];
  void load(url).then(buf => {
    if (!buf) return;
    const src = ac.createBufferSource();
    src.buffer = buf;
    const j = opts.jitter ?? 0.05;
    src.playbackRate.value = (opts.rate ?? 1) * (1 + (Math.random() * 2 - 1) * j);
    const g = ac.createGain();
    g.gain.value = (opts.volume ?? 1) * (0.88 + Math.random() * 0.12);
    let node: AudioNode = src.connect(g);
    if (opts.pan && ac.createStereoPanner) { const p = ac.createStereoPanner(); p.pan.value = Math.max(-1, Math.min(1, opts.pan)); node = node.connect(p); }
    node.connect(opts.bus === 'ambience' ? ambBus : opts.bus === 'music' ? musicBus : sfxBus);
    src.start(ac.currentTime + (opts.delay ?? 0));
  });
  return true;
}

// ---------- loops ----------
export interface Loop { stop(fade?: number): void; setGain(v: number, time?: number): void }

/** Start a looping buffer on a bus, fading in. Resolves once playback has been scheduled. */
export async function loop(url: string, busName: 'music' | 'ambience', gain: number, fadeIn = 2, pan = 0): Promise<Loop | null> {
  const ac = audio();
  if (!ac) return null;
  const buf = await load(url);
  if (!buf) return null;
  const src = ac.createBufferSource();
  src.buffer = buf; src.loop = true;
  const g = ac.createGain();
  g.gain.value = 0.0001;
  let node: AudioNode = src.connect(g);
  if (pan && ac.createStereoPanner) { const p = ac.createStereoPanner(); p.pan.value = pan; node = node.connect(p); }
  node.connect(busName === 'music' ? musicBus : ambBus);
  // random start offset so repeated scenes don't always begin at the same point
  src.start(0, busName === 'ambience' ? Math.random() * buf.duration : 0);
  const t = ac.currentTime;
  g.gain.setValueAtTime(0.0001, t);
  g.gain.linearRampToValueAtTime(gain, t + fadeIn);
  let stopped = false;
  return {
    stop(fade = 2) {
      if (stopped) return; stopped = true;
      const n = ac.currentTime;
      g.gain.cancelScheduledValues(n);
      g.gain.setValueAtTime(g.gain.value, n);
      g.gain.linearRampToValueAtTime(0.0001, n + fade);
      src.stop(n + fade + 0.05);
      setTimeout(() => { try { src.disconnect(); g.disconnect(); } catch { /* already gone */ } }, (fade + 0.2) * 1000);
    },
    setGain(v, time = 4) { if (stopped) return; const n = ac.currentTime; g.gain.cancelScheduledValues(n); g.gain.setValueAtTime(g.gain.value, n); g.gain.linearRampToValueAtTime(v, n + time); },
  };
}

// ---------- lifecycle ----------
let unlocked = false;
const unlockHooks: (() => void)[] = [];
export function whenUnlocked(fn: () => void) { if (unlocked) fn(); else unlockHooks.push(fn); }

/** Browsers only allow audio after a user gesture: unlock on the first one. */
export function installAudioUnlock() {
  const unlock = () => {
    const ac = audio();
    if (!ac) return;
    const done = () => {
      if (unlocked) return;
      unlocked = true;
      window.removeEventListener('pointerdown', unlock, true);
      window.removeEventListener('keydown', unlock, true);
      for (const fn of unlockHooks.splice(0)) fn();
    };
    if (ac.state === 'suspended') void ac.resume().then(done); else done();
  };
  window.addEventListener('pointerdown', unlock, true);
  window.addEventListener('keydown', unlock, true);
  // Don't burn CPU or battery in a background tab.
  document.addEventListener('visibilitychange', () => {
    if (!ctx || !unlocked) return;
    if (document.hidden) void ctx.suspend(); else void ctx.resume();
  });
}

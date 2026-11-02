// Game sound effects. All samples are from Kenney's CC0 packs (RPG Audio, Impact Sounds, Music Jingles),
// converted to mono MP3 in src/audio/sfx/. See src/audio/sfx/CREDITS.md for which file maps to which source.
import type { Cue } from '../render/renderer';
import type { Game } from '../engine/game';

const files = import.meta.glob('./sfx/*.mp3', { eager: true, query: '?url', import: 'default' }) as Record<string, string>;

/** Sample banks: name -> variant URLs (hit_0.mp3, hit_1.mp3 ... -> 'hit'). */
const banks: Record<string, string[]> = {};
for (const [path, url] of Object.entries(files)) {
  const m = /\/([a-z]+)_\d+\.mp3$/.exec(path);
  if (m) (banks[m[1]] ??= []).push(url);
}

const MUTE_KEY = 'brinewake.muted';
let ctx: AudioContext | null = null;
let master: GainNode | null = null;
const buffers = new Map<string, AudioBuffer>();
const loading = new Map<string, Promise<AudioBuffer | null>>();
let muted = (() => { try { return localStorage.getItem(MUTE_KEY) === '1'; } catch { return false; } })();
const lastPlayed = new Map<string, number>();

function audio(): AudioContext | null {
  if (ctx) return ctx;
  const AC = (globalThis as { AudioContext?: typeof AudioContext; webkitAudioContext?: typeof AudioContext }).AudioContext
    ?? (globalThis as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AC) return null;
  ctx = new AC();
  master = ctx.createGain();
  master.gain.value = muted ? 0 : 0.8;
  master.connect(ctx.destination);
  return ctx;
}

function load(url: string): Promise<AudioBuffer | null> {
  const ac = audio();
  if (!ac) return Promise.resolve(null);
  const hit = buffers.get(url);
  if (hit) return Promise.resolve(hit);
  let p = loading.get(url);
  if (!p) {
    p = fetch(url).then(r => r.arrayBuffer()).then(b => ac.decodeAudioData(b)).then(buf => { buffers.set(url, buf); return buf; }).catch(() => null);
    loading.set(url, p);
  }
  return p;
}

/** Browsers only allow audio after a user gesture: unlock on the first one and warm up the banks. */
export function installAudioUnlock() {
  const unlock = () => {
    const ac = audio();
    if (ac?.state === 'suspended') void ac.resume();
    for (const urls of Object.values(banks)) for (const u of urls) void load(u);
    window.removeEventListener('pointerdown', unlock);
    window.removeEventListener('keydown', unlock);
  };
  window.addEventListener('pointerdown', unlock);
  window.addEventListener('keydown', unlock);
}

export function isMuted() { return muted; }
export function setMuted(m: boolean) {
  muted = m;
  try { localStorage.setItem(MUTE_KEY, m ? '1' : '0'); } catch { /* storage unavailable */ }
  if (master && ctx) master.gain.setTargetAtTime(m ? 0 : 0.8, ctx.currentTime, 0.02);
}

/** Play a random variant from a bank, with slight pitch/volume jitter so repeats don't sound mechanical. */
export function play(bank: string, opts: { volume?: number; rate?: number; jitter?: number; minGap?: number } = {}) {
  if (muted) return;
  const urls = banks[bank];
  const ac = audio();
  if (!urls?.length || !ac || ac.state !== 'running') return;
  const now = performance.now();
  // Footsteps from several units, or a 6-target spell, shouldn't stack into a wall of noise.
  if (now - (lastPlayed.get(bank) ?? -1e9) < (opts.minGap ?? 35)) return;
  lastPlayed.set(bank, now);
  const url = urls[Math.floor(Math.random() * urls.length)];
  void load(url).then(buf => {
    if (!buf || !master) return;
    const src = ac.createBufferSource();
    src.buffer = buf;
    const j = opts.jitter ?? 0.06;
    src.playbackRate.value = (opts.rate ?? 1) * (1 + (Math.random() * 2 - 1) * j);
    const g = ac.createGain();
    g.gain.value = (opts.volume ?? 1) * (0.9 + Math.random() * 0.1);
    src.connect(g).connect(master);
    src.start();
  });
}

const SALT = new Set(['salt', 'caustic', 'light']);
const CRUSH = new Set(['pressure', 'brine', 'impact']);

/** Map a renderer cue to sounds. */
export function playCue(c: Cue, g: Game) {
  switch (c.kind) {
    case 'swing': play('swing', { volume: 0.55 }); break;
    case 'release': play('release', { volume: 0.6, rate: 1.3 }); break;
    case 'cast': play('cast', { volume: 0.45, rate: 0.85 }); break;
    case 'hit': {
      const u = g.unit(c.uid);
      const armored = !!u && (g.def(u).structure || g.stat(u, 'defense') >= 3);
      const type = c.damageType ?? '';
      const bank = SALT.has(type) ? 'salt' : CRUSH.has(type) ? 'crush' : c.heavy || c.lethal ? 'heavy' : armored ? 'armor' : 'hit';
      play(bank, { volume: c.lethal ? 1 : 0.8, rate: c.lethal ? 0.85 : 1, minGap: 20 });
      if (armored && bank !== 'armor') play('armor', { volume: 0.35 });
      break;
    }
    case 'death': play('death', { volume: 0.9, rate: 0.9 }); break;
    case 'revive': play('bell', { volume: 0.45, rate: 1.5 }); break;
    case 'deploy': play('deploy', { volume: 0.55 }); break;
    case 'step': play(/silt|reef|coral|mud|kelp|grass/.test(c.terrain) ? 'stepsoft' : 'step', { volume: 0.18, minGap: 60, jitter: 0.1 }); break;
    case 'push': play('push', { volume: 0.6 }); break;
    case 'spell': play('spell', { volume: 0.6, rate: 0.9 }); break;
    case 'heal': play('cast', { volume: 0.35, rate: 1.35, minGap: 80 }); break;
    case 'status': play('cast', { volume: 0.22, rate: 0.7, minGap: 120 }); break;
    case 'equip': play('equip', { volume: 0.7 }); break;
    case 'essence': play('coins', { volume: 0.55 }); break;
  }
}

/** The lighthouse bell: your turn. */
export function playTurnBell(mine: boolean) { play('bell', { volume: mine ? 0.55 : 0.25, rate: mine ? 1 : 0.8, jitter: 0 }); }
export function playCard() { play('card', { volume: 0.5 }); }
export function playEnd(victory: boolean) { play(victory ? 'victory' : 'defeat', { volume: 0.8, jitter: 0 }); }

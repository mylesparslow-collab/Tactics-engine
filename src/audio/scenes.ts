// Scenes: which music track and which ambient bed mix is playing, and the one-off accents that get
// sprinkled over it. The menu and briefing share one music scene; each battle map has its own bed mix.
import { accents, audio, beds, load, loop, play, preload, running, setSceneGain, tracks, whenUnlocked, type Loop } from './engine';

interface Layer { bed: string; gain: number; pan?: number }
interface Accent { name: string; every: [number, number]; volume: number; pan?: boolean }
interface Recipe { layers: Layer[]; accents: Accent[] }

/** Every map hears the drained sea hanging overhead (muffled surf), plus its own weather and sounds. */
const RECIPES: Record<string, Recipe> = {
  lantern_shoal: {
    layers: [{ bed: 'overhead', gain: 0.35 }, { bed: 'wind_light', gain: 0.5 }, { bed: 'surf', gain: 0.2 }, { bed: 'flag', gain: 0.1, pan: 0.3 }],
    accents: [{ name: 'bell_far', every: [35, 70], volume: 0.5, pan: true }, { name: 'gull', every: [25, 55], volume: 0.4, pan: true }],
  },
  greywater_stair: {
    layers: [{ bed: 'overhead', gain: 0.4 }, { bed: 'wind', gain: 0.5 }, { bed: 'lap', gain: 0.18 }],
    accents: [{ name: 'metal_groan', every: [25, 50], volume: 0.4, pan: true }, { name: 'chains', every: [45, 90], volume: 0.35, pan: true }],
  },
  mother_hull: {
    layers: [{ bed: 'overhead', gain: 0.35 }, { bed: 'wind', gain: 0.3 }, { bed: 'drone', gain: 0.3 }],
    accents: [{ name: 'creak', every: [8, 20], volume: 0.55, pan: true }, { name: 'whisper', every: [50, 90], volume: 0.35, pan: true }, { name: 'metal_groan', every: [30, 60], volume: 0.35, pan: true }],
  },
  the_kettle: {
    layers: [{ bed: 'overhead', gain: 0.4 }, { bed: 'wind_light', gain: 0.35 }, { bed: 'chimes', gain: 0.2, pan: -0.3 }],
    accents: [{ name: 'creak', every: [20, 40], volume: 0.45, pan: true }, { name: 'metal_groan', every: [30, 60], volume: 0.35, pan: true }],
  },
  trench_deeplight: {
    layers: [{ bed: 'overhead', gain: 0.6 }, { bed: 'drone', gain: 0.4 }, { bed: 'bubbles', gain: 0.3 }],
    accents: [{ name: 'drip', every: [10, 25], volume: 0.4, pan: true }, { name: 'whisper', every: [30, 60], volume: 0.4, pan: true }, { name: 'chains', every: [50, 90], volume: 0.3, pan: true }],
  },
  weeping_shelf: {
    layers: [{ bed: 'overhead', gain: 0.3 }, { bed: 'rain', gain: 0.5 }, { bed: 'lap', gain: 0.22 }, { bed: 'wind', gain: 0.2 }],
    accents: [{ name: 'bell_far', every: [40, 80], volume: 0.4, pan: true }],
  },
};
const FALLBACK: Recipe = { layers: [{ bed: 'overhead', gain: 0.4 }, { bed: 'wind', gain: 0.4 }, { bed: 'surf', gain: 0.2 }], accents: [{ name: 'creak', every: [30, 60], volume: 0.35, pan: true }] };

const MENU_BED: Recipe = {
  layers: [{ bed: 'overhead', gain: 0.4 }, { bed: 'surf', gain: 0.22 }, { bed: 'wind_light', gain: 0.18 }],
  accents: [{ name: 'bell_far', every: [30, 60], volume: 0.4, pan: true }],
};

let music: { name: string; loop: Loop } | null = null;
let musicToken = 0;
let ambLoops: Loop[] = [];
let ambToken = 0;
let accentTimers: number[] = [];
let wanted: { music: string | null; recipe: Recipe | null } = { music: null, recipe: null };

function musicGain(name: string) { return name === 'menu' ? 0.9 : 0.8; }

function switchMusic(name: string | null, fade = 2.5) {
  const token = ++musicToken;
  const old = music; music = null;
  old?.loop.stop(fade);
  if (!name || !tracks[name]) return;
  whenUnlocked(() => {
    if (token !== musicToken) return;
    void loop(tracks[name], 'music', musicGain(name), fade).then(l => {
      if (!l) return;
      if (token !== musicToken) { l.stop(0.1); return; }
      music = { name, loop: l };
    });
  });
}

function startBed(r: Recipe | null, fade = 3) {
  const token = ++ambToken;
  for (const l of ambLoops.splice(0)) l.stop(fade);
  for (const t of accentTimers.splice(0)) clearTimeout(t);
  if (!r) return;
  whenUnlocked(() => {
    if (token !== ambToken) return;
    for (const layer of r.layers) {
      const url = beds[layer.bed];
      if (!url) continue;
      void loop(url, 'ambience', layer.gain, fade, layer.pan ?? 0).then(l => {
        if (!l) return;
        if (token !== ambToken) { l.stop(0.1); return; }
        ambLoops.push(l);
        // let the bed breathe: drift each layer's level so the wind swells and settles
        const drift = () => {
          if (token !== ambToken) return;
          l.setGain(layer.gain * (0.65 + Math.random() * 0.7), 6 + Math.random() * 8);
          accentTimers.push(window.setTimeout(drift, 9000 + Math.random() * 9000));
        };
        accentTimers.push(window.setTimeout(drift, 4000 + Math.random() * 6000));
      });
    }
    for (const a of r.accents) {
      const arm = () => {
        const wait = (a.every[0] + Math.random() * (a.every[1] - a.every[0])) * 1000;
        accentTimers.push(window.setTimeout(() => {
          if (token !== ambToken) return;
          if (running() && !document.hidden) play(a.name, { volume: a.volume, pan: a.pan ? (Math.random() * 2 - 1) * 0.8 : 0, jitter: 0.04, minGap: 1000, bus: 'ambience' }, accents);
          arm();
        }, wait));
      };
      arm();
    }
  });
}

/** Warm the decode cache for what a scene will need, without blocking anything. */
function warm(urls: (string | undefined)[]) { whenUnlocked(() => { void preload(urls.filter((u): u is string => !!u), 2); }); }

export function enterMenu() {
  setSceneGain('music', 1); setSceneGain('ambience', 1);
  if (music?.name === 'menu' && wanted.music === 'menu') return;
  wanted = { music: 'menu', recipe: MENU_BED };
  switchMusic('menu');
  startBed(MENU_BED);
}

export function enterBattle(mapId: string, seed = 0) {
  setSceneGain('music', 1); setSceneGain('ambience', 1);
  const r = RECIPES[mapId] ?? FALLBACK;
  const track = seed % 2 === 0 ? 'battle_a' : 'battle_b';
  wanted = { music: track, recipe: r };
  switchMusic(track, 3);
  startBed(r, 4);
  warm(r.layers.map(l => beds[l.bed]));
}

export function leaveAll() { wanted = { music: null, recipe: null }; switchMusic(null, 1.5); startBed(null, 1.5); }

/** Victory/defeat: pull the music and weather back under the stinger, then let the music fade away. */
export function duckForEnd() {
  setSceneGain('music', 0.18); setSceneGain('ambience', 0.5);
  window.setTimeout(() => { setSceneGain('music', 1); if (wanted.music?.startsWith('battle')) switchMusic(null, 4); }, 6500);
}

/** Cheap hash so the same mission always gets the same battle track. */
export function seedOf(id: string): number { let h = 0; for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) | 0; return Math.abs(h); }

export function preloadCore(urls: string[]) { whenUnlocked(() => { void preload(urls, 3); }); }
export { audio, load };

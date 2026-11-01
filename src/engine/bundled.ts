// Loads every JSON file under /content at build time (Vite). Drop new files in and they are picked up.
import type { Content, MapDef, MissionDef } from './types';
import { normalizeContent } from './content';

const top = import.meta.glob('../../content/*.json', { eager: true, import: 'default' }) as Record<string, unknown>;
const mapFiles = import.meta.glob('../../content/maps/*.json', { eager: true, import: 'default' });
const missionFiles = import.meta.glob('../../content/missions/*.json', { eager: true, import: 'default' });
// Sprite images referenced as "sprites/<file>" in units.json are bundled and rewritten to their built URL.
const spriteFiles = import.meta.glob('../../content/sprites/*', { eager: true, query: '?url', import: 'default' }) as Record<string, string>;

export function byId<T extends { id: string }>(files: Record<string, unknown>): Record<string, T> {
  const out: Record<string, T> = {};
  for (const v of Object.values(files)) { const d = v as T; out[d.id] = d; }
  return out;
}

const file = (name: string) => structuredClone(top[`../../content/${name}.json`] ?? {}) as never;

export function loadBundledContent(): Content {
  const c = normalizeContent({
    config: file('config'), units: file('units'), abilities: file('abilities'), spells: file('spells'),
    equipment: file('equipment'), statuses: file('statuses'), terrain: file('terrain'), campaigns: file('campaigns'),
    factions: file('factions'),
    maps: byId<MapDef>(mapFiles),
    missions: byId<MissionDef>(missionFiles),
  });
  for (const u of Object.values(c.units)) {
    const img = u.sprite?.image;
    if (img && !/^(https?:|data:|\/)/.test(img)) {
      const url = spriteFiles[`../../content/${img}`];
      if (url) u.sprite.image = url; else delete u.sprite.image; // missing art falls back to placeholder
    }
  }
  return c;
}

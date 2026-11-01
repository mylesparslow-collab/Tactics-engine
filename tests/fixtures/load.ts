// Placeholder content used by the rules tests, independent of the real game content in /content.
import type { Content, MapDef, MissionDef } from '../../src/engine/types';
import { normalizeContent } from '../../src/engine/content';
import { byId } from '../../src/engine/bundled';
import units from './content/units.json';
import abilities from './content/abilities.json';
import spells from './content/spells.json';
import equipment from './content/equipment.json';
import statuses from './content/statuses.json';
import terrain from './content/terrain.json';
import campaigns from './content/campaigns.json';
import config from './content/config.json';

const maps = import.meta.glob('./content/maps/*.json', { eager: true, import: 'default' });
const missions = import.meta.glob('./content/missions/*.json', { eager: true, import: 'default' });

export function loadFixtureContent(): Content {
  return normalizeContent(structuredClone({
    config, units, abilities, spells, equipment, statuses, terrain, campaigns,
    maps: byId<MapDef>(maps), missions: byId<MissionDef>(missions),
  }) as unknown as Content);
}

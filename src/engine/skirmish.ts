import type { Content, MissionDef } from './types';

declare const process: { env: Record<string, string | undefined> } | undefined;
const env = (k: string, d: number) => { try { const v = typeof process !== 'undefined' ? process.env[k] : undefined; return v ? Number(v) : d; } catch { return d; } };
/** Skirmish economy. Tuned with AI-vs-AI sims (tests/balance.test.ts); env overrides are for tuning runs only. */
export const SKIRMISH = { startingEssence: env('SK_START', 120), essencePerTurn: env('SK_INC', 30), secondPlayerBonus: env('SK_P2', 20) };

/** Faction ids that have at least one deployable unit. */
export function playableFactions(c: Content): string[] {
  const ids = new Set<string>();
  for (const u of Object.values(c.units)) if (u.faction && !u.structure) ids.add(u.faction);
  return [...ids];
}

/**
 * Default deck for a faction: every non-hero champion, one hero, then spells and equipment
 * (cheapest first) up to `size` cards. `hero` picks a specific hero id.
 */
export function factionDeck(c: Content, faction: string, opts: { size?: number; hero?: string } = {}): string[] {
  const size = opts.size ?? 22;
  const byCost = <T extends { cost: number }>(rec: Record<string, T & { faction?: string }>) =>
    Object.entries(rec).filter(([, v]) => v.faction === faction).sort((a, b) => a[1].cost - b[1].cost).map(([k]) => k);
  const units = Object.entries(c.units).filter(([, u]) => u.faction === faction && !u.structure);
  const heroes = units.filter(([, u]) => u.hero).map(([k]) => k);
  const champions = units.filter(([, u]) => !u.hero).sort((a, b) => a[1].cost - b[1].cost).map(([k]) => k);
  const hero = opts.hero && heroes.includes(opts.hero) ? opts.hero : heroes[0];
  const deck = [...(hero ? [hero] : []), ...champions];
  const spells = byCost(c.spells), equipment = byCost(c.equipment);
  while (deck.length < size && (spells.length || equipment.length)) {
    if (spells.length) deck.push(spells.shift()!);
    if (deck.length < size && equipment.length && deck.length % 3 === 0) deck.push(equipment.shift()!);
  }
  return deck.slice(0, Math.max(size, hero ? 1 : 0));
}

/** Build a one-off battle mission: faction vs faction on a map. Register it in content.missions before starting. */
export function buildSkirmish(c: Content, mapId: string, factions: [string, string], playerControllers: ['human' | 'ai', 'human' | 'ai'] = ['human', 'ai']): MissionDef {
  const f = (id: string) => c.factions?.[id];
  const map = c.maps[mapId];
  return {
    id: `skirmish:${mapId}:${factions[0]}:${factions[1]}`,
    name: `${f(factions[0])?.name ?? factions[0]} vs ${f(factions[1])?.name ?? factions[1]}`,
    description: map.description,
    map: mapId,
    briefing: [map.description ?? '', f(factions[0])?.tagline ?? ''].filter(Boolean),
    teams: factions.map((fid, i) => ({
      name: f(fid)?.name ?? fid,
      color: f(fid)?.color ?? (i === 0 ? '#e0573d' : '#3d8fe0'),
      controller: playerControllers[i],
      warband: factionDeck(c, fid),
      // Going second is a real handicap (the first mover reaches the wells first): compensate with extra Tide.
      ...(i === 1 ? { startingEssence: (SKIRMISH.startingEssence + SKIRMISH.secondPlayerBonus) } : {}),
    })),
    startingEssence: SKIRMISH.startingEssence,
    essencePerTurn: SKIRMISH.essencePerTurn,
  };
}

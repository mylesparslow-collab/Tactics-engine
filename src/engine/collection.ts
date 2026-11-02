// The Relic collection: which cards the player owns, and where the rest are earned.
// Ownership comes from campaign progress (starting rosters + mission unlocks), plus a persistent record of
// everything ever earned, so resetting a campaign does not take relics away. Pearls and Tempering come later.
import type { Content } from './types';
import { loadProgress } from './campaign';

export type RelicType = 'champion' | 'hero' | 'spell' | 'equipment';
export interface RelicSource { campaign: string; campaignName: string; mission?: number; missionName?: string }

/** Every relic counts as owned while this is on (playtesting, before Pearls and other campaigns exist).
 * Turn it off to go back to earning relics through campaigns. */
export const UNLOCK_ALL = true;

const OWNED_KEY = 'tactics.collection.owned';
const SEEN_KEY = 'tactics.collection.seen';

function readSet(k: string): Set<string> {
  try { const raw = localStorage.getItem(k); if (raw) return new Set(JSON.parse(raw) as string[]); } catch { /* storage unavailable */ }
  return new Set();
}
function writeSet(k: string, s: Set<string>) {
  try { localStorage.setItem(k, JSON.stringify([...s])); } catch { /* storage unavailable */ }
}

/** Remember relics as earned for good (called when a mission is won). */
export function grantRelics(ids: string[]) {
  if (!ids.length) return;
  const s = readSet(OWNED_KEY); ids.forEach(i => s.add(i)); writeSet(OWNED_KEY, s);
}

/** Every collectable card id: faction champions, heroes, spells and equipment (not Beacons or other structures). */
export function allRelics(c: Content): string[] {
  const units = Object.entries(c.units).filter(([, u]) => u.faction && !u.structure).map(([k]) => k);
  return [...units, ...Object.keys(c.spells), ...Object.keys(c.equipment)];
}

export function relicType(c: Content, id: string): RelicType {
  const u = c.units[id];
  if (u) return u.hero ? 'hero' : 'champion';
  return c.spells[id] ? 'spell' : 'equipment';
}

export function relicFaction(c: Content, id: string): string | undefined {
  return (c.units[id] ?? c.spells[id] ?? c.equipment[id])?.faction;
}

/** Where a card is earned: a campaign's starting company, or the mission that unlocks it. First source wins. */
export function relicSources(c: Content): Map<string, RelicSource> {
  const out = new Map<string, RelicSource>();
  for (const [cid, camp] of Object.entries(c.campaigns)) {
    for (const id of camp.startingRoster) if (!out.has(id)) out.set(id, { campaign: cid, campaignName: camp.name });
    camp.missions.forEach((m, i) => {
      for (const id of m.unlocks ?? []) if (!out.has(id)) out.set(id, { campaign: cid, campaignName: camp.name, mission: i, missionName: c.missions[m.mission]?.name ?? m.mission });
    });
  }
  return out;
}

/** Cards the player owns right now. Relics that no campaign awards yet start unlocked, so every faction is
 * available until its own campaign arrives to earn them through. */
export function ownedRelics(c: Content, unlockAll = UNLOCK_ALL): Set<string> {
  if (unlockAll) return new Set(allRelics(c));
  const owned = readSet(OWNED_KEY);
  const sources = relicSources(c);
  for (const id of allRelics(c)) if (!sources.has(id)) owned.add(id);
  for (const [cid, camp] of Object.entries(c.campaigns)) {
    camp.startingRoster.forEach(id => owned.add(id));
    const done = loadProgress(cid).completed;
    camp.missions.slice(0, done).forEach(m => (m.unlocks ?? []).forEach(id => owned.add(id)));
  }
  return owned;
}

/** Owned cards earned from missions that the player has not opened in the collection yet. */
export function unseenRelics(c: Content, owned = ownedRelics(c)): Set<string> {
  const seen = readSet(SEEN_KEY);
  const sources = relicSources(c);
  return new Set([...owned].filter(id => !seen.has(id) && sources.get(id)?.mission !== undefined));
}
export function markSeen(ids: string[]) {
  const s = readSet(SEEN_KEY); let changed = false;
  for (const i of ids) if (!s.has(i)) { s.add(i); changed = true; }
  if (changed) writeSet(SEEN_KEY, s);
}

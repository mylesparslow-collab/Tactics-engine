import { beforeEach, describe, expect, it } from 'vitest';
import { loadBundledContent } from '../src/engine/bundled';
import { allRelics, markSeen, ownedRelics, relicSources, unseenRelics } from '../src/engine/collection';
import { recordVictory, saveProgress } from '../src/engine/campaign';

// minimal in-memory localStorage for the node test environment
const store = new Map<string, string>();
(globalThis as unknown as { localStorage: Storage }).localStorage = {
  getItem: k => store.get(k) ?? null, setItem: (k, v) => { store.set(k, String(v)); }, removeItem: k => { store.delete(k); },
  clear: () => store.clear(), key: i => [...store.keys()][i] ?? null, get length() { return store.size; },
};

const c = loadBundledContent();
const cid = Object.keys(c.campaigns)[0];
const camp = c.campaigns[cid];

describe('relic collection', () => {
  beforeEach(() => store.clear());

  it('lists every faction card once, without Beacons', () => {
    const ids = allRelics(c);
    expect(new Set(ids).size).toBe(ids.length);
    expect(ids).not.toContain('keystone');
    expect(ids.length).toBe(Object.values(c.units).filter(u => u.faction && !u.structure).length + Object.keys(c.spells).length + Object.keys(c.equipment).length);
  });

  it('owns the starting company and mission unlocks already won', () => {
    const sources = relicSources(c);
    const free = allRelics(c).filter(id => !sources.has(id));
    expect(free.length).toBeGreaterThan(0);
    expect([...ownedRelics(c)].sort()).toEqual([...new Set([...camp.startingRoster, ...free])].sort());
    for (const id of camp.missions[0].unlocks ?? []) expect(ownedRelics(c).has(id)).toBe(false);
    saveProgress(cid, { completed: 2 });
    const owned = ownedRelics(c);
    for (const m of camp.missions.slice(0, 2)) for (const id of m.unlocks ?? []) expect(owned.has(id)).toBe(true);
    for (const id of camp.missions[2].unlocks ?? []) expect(owned.has(id)).toBe(false);
  });

  it('keeps earned relics after a campaign reset, and flags them as new until seen', () => {
    recordVictory(c, cid, 0);
    saveProgress(cid, { completed: 0 });
    const won = camp.missions[0].unlocks ?? [];
    expect(won.length).toBeGreaterThan(0);
    for (const id of won) expect(ownedRelics(c).has(id)).toBe(true);
    expect([...unseenRelics(c)].sort()).toEqual([...won].sort());
    markSeen(won);
    expect(unseenRelics(c).size).toBe(0);
  });

  it('knows which mission earns a relic', () => {
    const id = camp.missions[3].unlocks![0];
    expect(relicSources(c).get(id)).toMatchObject({ campaign: cid, mission: 3 });
  });
});

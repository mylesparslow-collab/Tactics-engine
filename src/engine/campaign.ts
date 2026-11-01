import type { Content } from './types';

export interface CampaignProgress { completed: number } // number of missions won, in order

const storeKey = (id: string) => `tactics.campaign.${id}`;

export function loadProgress(campaignId: string): CampaignProgress {
  try {
    const raw = localStorage.getItem(storeKey(campaignId));
    if (raw) return JSON.parse(raw) as CampaignProgress;
  } catch { /* storage unavailable */ }
  return { completed: 0 };
}

export function saveProgress(campaignId: string, p: CampaignProgress) {
  try { localStorage.setItem(storeKey(campaignId), JSON.stringify(p)); } catch { /* storage unavailable */ }
}

/** Starting roster plus every unlock from missions already won. */
export function rosterFor(content: Content, campaignId: string, p: CampaignProgress): string[] {
  const c = content.campaigns[campaignId];
  const roster = [...c.startingRoster];
  c.missions.slice(0, p.completed).forEach(m => roster.push(...(m.unlocks ?? [])));
  return roster;
}

/** Mark mission index `i` as won. Returns the units unlocked by it. */
export function recordVictory(content: Content, campaignId: string, i: number): string[] {
  const p = loadProgress(campaignId);
  if (i === p.completed) { p.completed++; saveProgress(campaignId, p); }
  return content.campaigns[campaignId].missions[i]?.unlocks ?? [];
}

export function isUnlocked(p: CampaignProgress, i: number) { return i <= p.completed; }

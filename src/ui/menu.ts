import type { Content } from '../engine/types';
import { isUnlocked, loadProgress, saveProgress } from '../engine/campaign';
import { label } from '../engine/content';
import { clear, h } from './dom';
import { describeObjectives } from './text';
import { buildSkirmish, playableFactions } from '../engine/skirmish';

export interface MissionChoice { missionId: string; campaign?: { id: string; index: number } }

export function showMenu(root: HTMLElement, content: Content, errors: string[], onPick: (c: MissionChoice) => void) {
  clear(root); root.className = 'screen';
  const wrap = h('div', { class: 'menu' }, h('h1', null, content.config?.labels?.title ?? 'Tactics'),
    h('div', { class: 'tag' }, content.config?.labels?.subtitle ?? 'A turn-based tactics prototype'));
  if (errors.length) {
    wrap.append(h('div', { class: 'errbox' }, h('b', null, `Content validation found ${errors.length} problem${errors.length === 1 ? '' : 's'}:`),
      h('ul', null, ...errors.slice(0, 30).map(e => h('li', null, e))), errors.length > 30 ? h('div', null, `...and ${errors.length - 30} more`) : null));
  }
  const cols = h('div', { class: 'menucols' });
  const camps = h('section', null, h('h2', null, 'Campaign'));
  for (const [id, c] of Object.entries(content.campaigns)) {
    const p = loadProgress(id);
    const card = h('div', { class: 'mcard' }, h('h3', null, c.name), c.description ? h('p', { class: 'muted' }, c.description) : null,
      h('div', { class: 'muted small' }, `Progress: ${Math.min(p.completed, c.missions.length)}/${c.missions.length} missions`));
    const list = h('ol', { class: 'mlist' });
    c.missions.forEach((m, i) => {
      const md = content.missions[m.mission];
      const ok = isUnlocked(p, i) && !!md;
      list.append(h('li', null, h('button', { disabled: !ok, onclick: () => onPick({ missionId: m.mission, campaign: { id, index: i } }) },
        h('span', null, md?.name ?? m.mission), h('span', { class: 'badge' }, !ok ? 'Locked' : i < p.completed ? 'Won' : 'Ready'))));
    });
    card.append(list, h('button', { class: 'quiet small', onclick: () => { saveProgress(id, { completed: 0 }); showMenu(root, content, errors, onPick); } }, 'Reset progress'));
    camps.append(card);
  }
  const sk = h('section', null, h('h2', null, 'Skirmish'));
  const factions = playableFactions(content);
  const maps = Object.keys(content.maps);
  if (factions.length >= 2 && maps.length) {
    const fname = (id: string) => content.factions?.[id]?.name ?? id;
    const sel = (opts: string[], name: (id: string) => string, initial: string) => {
      const s = h('select', null, ...opts.map(o => h('option', { value: o }, name(o))));
      s.value = initial; return s;
    };
    const mine = sel(factions, fname, factions[0]);
    const theirs = sel(factions, fname, factions[1]);
    const mapSel = sel(maps, id => content.maps[id].name, maps[0]);
    sk.append(h('div', { class: 'mcard quick' }, h('h3', null, 'Quick battle'),
      h('label', null, 'Your faction', mine), h('label', null, 'Opponent', theirs), h('label', null, 'Map', mapSel),
      h('button', { class: 'primary', onclick: () => {
        const m = buildSkirmish(content, mapSel.value, [mine.value, theirs.value]);
        content.missions[m.id] = m;
        onPick({ missionId: m.id });
      } }, 'Fight')));
  }
  const sl = h('div', { class: 'mcard' });
  for (const [id, m] of Object.entries(content.missions)) if (!id.startsWith('skirmish:'))
    sl.append(h('button', { class: 'skirm', onclick: () => onPick({ missionId: id }) }, h('b', null, m.name), h('small', null, m.description ?? '')));
  sk.append(sl);
  cols.append(camps, sk);
  wrap.append(cols);
  root.append(wrap);
}

export function showBriefing(root: HTMLElement, content: Content, choice: MissionChoice, onStart: () => void, onBack: () => void) {
  const m = content.missions[choice.missionId];
  const obj = describeObjectives(content, m);
  const map = content.maps[m.map];
  clear(root); root.className = 'screen';
  root.append(h('div', { class: 'menu' },
    h('div', { class: 'briefing' },
      h('div', { class: 'tag' }, choice.campaign ? content.campaigns[choice.campaign.id].name : 'Skirmish'),
      h('h1', null, m.name),
      m.description ? h('p', { class: 'lead' }, m.description) : null,
      ...(m.briefing ?? []).map(t => h('p', null, t)),
      h('div', { class: 'objs' },
        h('div', null, h('h3', null, obj.winAny ? 'Victory (any of)' : 'Victory'), h('ul', null, ...obj.win.map(t => h('li', null, t)))),
        h('div', null, h('h3', null, 'Defeat'), h('ul', null, ...obj.lose.map(t => h('li', null, t))))),
      h('div', { class: 'muted small' }, `Map: ${map?.name ?? m.map} - ${label(content, 'essence')} start: ${m.startingEssence ?? 100}`),
      h('div', { class: 'btnrow' }, h('button', { class: 'primary', onclick: onStart }, 'Start'), h('button', { onclick: onBack }, 'Back')))));
}

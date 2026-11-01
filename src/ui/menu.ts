import type { Content } from '../engine/types';
import { isUnlocked, loadProgress, saveProgress } from '../engine/campaign';
import { label } from '../engine/content';
import { clear, h } from './dom';
import { describeObjectives } from './text';
import { buildSkirmish, playableFactions } from '../engine/skirmish';
import { emblemSvg } from './cards';

export interface MissionChoice { missionId: string; campaign?: { id: string; index: number } }

function factionTile(content: Content, id: string, selected: boolean, onPick: () => void) {
  const f = content.factions?.[id];
  const color = f?.color ?? '#777', accent = f?.accent && f.accent !== '#101314' ? f.accent : '#e8e0cc';
  const em = h('span', { class: 'femblem' }); em.innerHTML = emblemSvg(id, 'unit', color, accent);
  const n = Object.values(content.units).filter(u => u.faction === id && !u.structure).length;
  return h('button', { class: 'ftile' + (selected ? ' selected' : ''), style: `--fc:${color};--fa:${accent}`, onclick: onPick, type: 'button' },
    em, h('span', { class: 'fname' }, f?.name ?? id), h('span', { class: 'ftag' }, f?.tagline ?? ''), h('span', { class: 'fcount' }, `${n} relics`));
}

export function showMenu(root: HTMLElement, content: Content, errors: string[], onPick: (c: MissionChoice) => void) {
  clear(root); root.className = 'screen';
  const wrap = h('div', { class: 'menu' },
    h('div', { class: 'title' }, h('h1', null, content.config?.labels?.title ?? 'Tactics'),
      h('div', { class: 'tag' }, content.config?.labels?.subtitle ?? 'A turn-based tactics prototype')));
  if (errors.length) {
    wrap.append(h('div', { class: 'errbox' }, h('b', null, `Content validation found ${errors.length} problem${errors.length === 1 ? '' : 's'}:`),
      h('ul', null, ...errors.slice(0, 30).map(e => h('li', null, e))), errors.length > 30 ? h('div', null, `...and ${errors.length - 30} more`) : null));
  }
  const cols = h('div', { class: 'menucols' });
  const sk = h('section', { class: 'chart' }, h('h2', null, 'Quick battle'));
  const factions = playableFactions(content);
  const maps = Object.keys(content.maps);
  if (factions.length >= 2 && maps.length) {
    let mine = factions[0], theirs = factions[1];
    const mapSel = h('select', null, ...maps.map(o => h('option', { value: o }, content.maps[o].name)));
    const rows = h('div', { class: 'fpick' });
    const draw = () => {
      clear(rows);
      rows.append(h('h3', null, 'Your faction'), h('div', { class: 'ftiles' }, ...factions.map(id => factionTile(content, id, id === mine, () => { mine = id; draw(); }))),
        h('h3', null, 'Opponent'), h('div', { class: 'ftiles' }, ...factions.map(id => factionTile(content, id, id === theirs, () => { theirs = id; draw(); }))));
    };
    draw();
    const mapDesc = h('div', { class: 'muted small mapdesc' }, content.maps[maps[0]].description ?? '');
    mapSel.onchange = () => { mapDesc.textContent = content.maps[mapSel.value].description ?? ''; };
    sk.append(h('div', { class: 'mcard quick' }, rows,
      h('label', null, h('span', null, 'Map'), mapSel), mapDesc,
      h('button', { class: 'brass big', onclick: () => {
        const m = buildSkirmish(content, mapSel.value, [mine, theirs]);
        content.missions[m.id] = m;
        onPick({ missionId: m.id });
      } }, h('span', null, 'Fight'))));
  }
  const camps = h('section', { class: 'chart' }, h('h2', null, 'Campaign'));
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
  const sl = h('div', { class: 'mcard' }, h('h3', null, 'Scenarios'));
  for (const [id, m] of Object.entries(content.missions)) if (!id.startsWith('skirmish:'))
    sl.append(h('button', { class: 'skirm', onclick: () => onPick({ missionId: id }) }, h('b', null, m.name), h('small', null, m.description ?? '')));
  camps.append(sl);
  cols.append(sk, camps);
  wrap.append(cols);
  root.append(wrap);
}

export function showBriefing(root: HTMLElement, content: Content, choice: MissionChoice, onStart: () => void, onBack: () => void) {
  const m = content.missions[choice.missionId];
  const obj = describeObjectives(content, m);
  const map = content.maps[m.map];
  clear(root); root.className = 'screen';
  root.append(h('div', { class: 'menu' },
    h('div', { class: 'briefing chart' },
      h('div', { class: 'tag' }, choice.campaign ? content.campaigns[choice.campaign.id].name : 'Skirmish'),
      h('h1', null, m.name),
      m.description ? h('p', { class: 'lead' }, m.description) : null,
      ...(m.briefing ?? []).map(t => h('p', null, t)),
      h('div', { class: 'teams' }, ...m.teams.map(t => h('span', { class: 'teamchip', style: `--tc:${t.color}` }, h('i', { class: 'dot' }), t.name))),
      h('div', { class: 'objs' },
        h('div', null, h('h3', null, obj.winAny ? 'Victory (any of)' : 'Victory'), h('ul', null, ...obj.win.map(t => h('li', null, t)))),
        h('div', null, h('h3', null, 'Defeat'), h('ul', null, ...obj.lose.map(t => h('li', null, t))))),
      h('div', { class: 'muted small' }, `Map: ${map?.name ?? m.map} - ${label(content, 'essence')} start: ${m.startingEssence ?? 100}`),
      h('div', { class: 'btnrow' }, h('button', { class: 'brass big', onclick: onStart }, h('span', null, 'Start')), h('button', { onclick: onBack }, 'Back')))));
}

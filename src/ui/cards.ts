// Relic cards: an ornate original frame tinted by faction, with art window, cost gem, name banner, type line and stats.
import type { Game } from '../engine/game';
import type { Content, Unit } from '../engine/types';
import { assetUrl, cardArtUrl } from '../render/anim';
import { hashStr, mix, rgba, shade } from '../render/iso';
import { h } from './dom';
import { effectText } from './text';

export type CardSize = 'hand' | 'mini' | 'full' | 'portrait';
export interface CardOpts { size: CardSize; live?: { game: Game; unit: Unit }; content: Content }

const KIND_COLORS: Record<string, { color: string; accent: string }> = {
  unit: { color: '#5a6f7a', accent: '#d8d0bf' }, spell: { color: '#5b3b9a', accent: '#d9c8ff' }, equipment: { color: '#8a6a2a', accent: '#f0dca8' },
};

function kindOf(c: Content, id: string): 'unit' | 'spell' | 'equipment' | undefined {
  if (c.units[id]) return 'unit'; if (c.spells[id]) return 'spell'; if (c.equipment[id]) return 'equipment'; return undefined;
}

/** Procedural heraldic emblem for cards without art (spells, equipment, units without sprites). */
let emblemSeq = 0;
export function emblemSvg(id: string, kind: string, color: string, accent: string): string {
  const r = hashStr(id);
  const gid = `em${++emblemSeq}`;
  const pick = (n: number, k: number) => (r >>> (k * 4)) % n;
  const c2 = mix(color, '#ffffff', 0.35), dark = shade(color, 0.5);
  let body = '';
  if (kind === 'spell') {
    const rays = 6 + pick(5, 1);
    let pts = '';
    for (let i = 0; i < rays * 2; i++) { const a = i / (rays * 2) * Math.PI * 2 - Math.PI / 2, rr = i % 2 ? 22 : 46; pts += `${50 + Math.cos(a) * rr},${50 + Math.sin(a) * rr} `; }
    body = `<circle cx="50" cy="50" r="40" fill="none" stroke="${accent}" stroke-width="1.5" stroke-dasharray="${3 + pick(5, 2)} ${4 + pick(4, 3)}" opacity=".8"/>
      <polygon points="${pts}" fill="url(#${gid})" stroke="${accent}" stroke-width="1.2"/>
      <circle cx="50" cy="50" r="${8 + pick(5, 4)}" fill="${accent}" opacity=".9"/><circle cx="50" cy="50" r="3" fill="${dark}"/>`;
  } else if (kind === 'equipment') {
    const shape = pick(3, 1);
    if (shape === 0) body = `<path d="M50 12 L82 24 L80 56 Q76 78 50 90 Q24 78 20 56 L18 24 Z" fill="url(#${gid})" stroke="${accent}" stroke-width="2"/><path d="M50 26 L50 76 M30 44 L70 44" stroke="${accent}" stroke-width="4" stroke-linecap="round"/>`;
    else if (shape === 1) body = `<rect x="22" y="40" width="56" height="26" rx="4" fill="url(#${gid})" stroke="${accent}" stroke-width="2"/><rect x="44" y="18" width="12" height="64" rx="3" fill="${c2}" stroke="${accent}" stroke-width="1.5"/><circle cx="50" cy="53" r="6" fill="${accent}"/>`;
    else body = `<path d="M30 80 L50 18 L70 80 Z" fill="url(#${gid})" stroke="${accent}" stroke-width="2"/><path d="M38 66 H62" stroke="${accent}" stroke-width="3"/><circle cx="50" cy="48" r="5" fill="${accent}"/>`;
  } else {
    const inner = [`<circle cx="50" cy="50" r="16" fill="none" stroke="${accent}" stroke-width="2"/><circle cx="50" cy="50" r="6" fill="${accent}"/>`,
      `<path d="M50 28 L50 72 M36 42 L64 42 M40 60 L60 60" stroke="${accent}" stroke-width="3" stroke-linecap="round"/>`,
      `<path d="M34 64 Q50 30 66 64" fill="none" stroke="${accent}" stroke-width="3"/><circle cx="50" cy="40" r="5" fill="${accent}"/>`,
      `<path d="M50 30 L62 50 L50 70 L38 50 Z" fill="${accent}" opacity=".9"/>`][pick(4, 2)];
    body = `<path d="M50 10 L84 24 L80 60 Q74 82 50 92 Q26 82 20 60 L16 24 Z" fill="url(#${gid})" stroke="${accent}" stroke-width="2"/>${inner}`;
  }
  return `<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><defs><radialGradient id="${gid}" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="${c2}"/><stop offset="1" stop-color="${dark}"/></radialGradient></defs>${body}</svg>`;
}

function statChip(cls: string, label: string, v: number, base?: number) {
  const mod = base === undefined ? '' : v > base ? ' up' : v < base ? ' down' : '';
  return h('span', { class: `st ${cls}${mod}`, title: label }, h('i', null, label), h('b', null, String(v)));
}

/** Ability text block for full cards and panels. */
export function abilityLines(c: Content, ids: string[]): HTMLElement[] {
  const out: HTMLElement[] = [];
  for (const id of ids) {
    const a = c.abilities[id]; if (!a) continue;
    const range = a.passive ? 'Passive' : `${a.apCost} AP · range ${a.range.min === a.range.max ? a.range.max : a.range.min + '-' + a.range.max}${a.area ? ` · area ${a.area.size}` : ''}${a.cooldown ? ` · cd ${a.cooldown}` : ''}`;
    out.push(h('div', { class: 'abl' + (a.passive ? ' passive' : '') }, h('b', null, a.name), h('span', { class: 'meta' }, range),
      h('div', { class: 'adesc' }, a.description ?? a.effects.map(e => effectText(c, e)).join('. '))));
  }
  return out;
}

export function cardColors(c: Content, id: string) {
  const kind = kindOf(c, id) ?? 'unit';
  const def = (c.units[id] ?? c.spells[id] ?? c.equipment[id]) as { faction?: string } | undefined;
  const f = def?.faction ? c.factions?.[def.faction] : undefined;
  const color = f?.color ?? KIND_COLORS[kind].color;
  const accent = f?.accent && f.accent !== '#101314' ? f.accent : KIND_COLORS[kind].accent;
  return { color, accent, kind, factionName: f?.name };
}

/** The art window for a relic: painted card art, else the unit's sprite still on a faction wash, else a heraldic emblem. */
export function artNode(id: string, c: Content): HTMLElement {
  const { color, accent, kind } = cardColors(c, id);
  const ud = c.units[id];
  const def = (ud ?? c.spells[id] ?? c.equipment[id]) as { art?: string } | undefined;
  const art = h('div', { class: 'rc-art', style: `--fc:${color};--fcd:${shade(color, 0.55)};--fcl:${mix(color, '#ffffff', 0.3)}` });
  const artUrl = cardArtUrl(id, def);
  const painted = ud ? assetUrl(`sprites/${id}_still.png`) : undefined;
  const still = ud ? assetUrl(ud.sprite.image) : undefined;
  // generated placeholder cards (content/cards/*.svg) carry their own frame, cost and name: crop to the picture area
  const ph = !!artUrl && (/cards\/[^/]*\.svg/.test(artUrl) || artUrl.startsWith('data:image/svg'));
  if (artUrl && !ph) art.append(h('img', { src: artUrl, alt: '', draggable: 'false' }));
  else if (painted) {
    art.classList.add('painted');
    art.append(h('div', { class: 'rc-ground' }), h('img', { class: 'figure', src: painted, alt: '', draggable: 'false' }));
  } else if (artUrl) {
    art.append(h('img', { class: 'cardart', src: artUrl, alt: '', draggable: 'false' }));
  } else if (still) {
    art.classList.add('painted');
    art.append(h('div', { class: 'rc-ground' }), h('img', { class: 'figure', src: still, alt: '', draggable: 'false' }));
  } else {
    art.classList.add('painted', 'emblem');
    const em = h('div', { class: 'rc-emblem' }); em.innerHTML = emblemSvg(id, kind, color, accent); art.append(em);
  }
  return art;
}

export function buildCard(id: string, o: CardOpts): HTMLElement {
  const c = o.content;
  const { color, accent, kind, factionName } = cardColors(c, id);
  const ud = c.units[id], sd = c.spells[id], ed = c.equipment[id];
  const def = (ud ?? sd ?? ed) as { name: string; description?: string; cost: number; art?: string } | undefined;
  const name = def?.name ?? id;
  const el = h('div', { class: `rcard ${kind} ${o.size}${ud?.hero ? ' hero' : ''}`, style: `--fc:${color};--fa:${accent};--fcd:${shade(color, 0.55)};--fcl:${mix(color, '#ffffff', 0.3)}` });
  const art = artNode(id, c);
  const typeLine = kind === 'unit' ? `${ud?.hero ? 'Hero' : ud?.structure ? 'Structure' : 'Champion'}${ud?.role ? ' · ' + ud.role : ''}` : kind === 'spell' ? 'Spell' : 'Equipment';
  el.append(
    h('div', { class: 'rc-frame' }, h('i', { class: 'c1' }), h('i', { class: 'c2' }), h('i', { class: 'c3' }), h('i', { class: 'c4' })),
    art,
    h('div', { class: 'rc-cost' }, h('span', null, String(def?.cost ?? '?'))),
    ud?.hero ? h('div', { class: 'rc-crown', title: 'Hero' }, '\u2655') : '',
    h('div', { class: 'rc-name' }, h('span', null, name)),
    h('div', { class: 'rc-type' }, typeLine),
  );
  if (ud) {
    const live = o.live, g = live?.game, u = live?.unit;
    const stat = (k: 'attack' | 'defense' | 'ap') => g && u ? g.stat(u, k) : ud.stats[k];
    el.append(h('div', { class: 'rc-stats' },
      statChip('hp', 'HP', u ? u.hp : ud.stats.hp), ud.structure ? null : statChip('ap', 'AP', u ? u.ap : stat('ap'), u ? stat('ap') : undefined),
      statChip('atk', 'ATK', stat('attack'), u ? ud.stats.attack : undefined), statChip('def', 'DEF', stat('defense'), u ? ud.stats.defense : undefined)));
  } else if (ed) {
    const mods = Object.entries(ed.statMods ?? {}).map(([k, v]) => `${(v ?? 0) >= 0 ? '+' : ''}${v} ${k}`).join(' ');
    el.append(h('div', { class: 'rc-stats text' }, mods || (ed.grantAbilities?.length ? 'Grants ability' : 'Relic')));
  } else if (sd) {
    el.append(h('div', { class: 'rc-stats text' }, `${sd.target}${sd.area ? ` · area ${sd.area.size}` : ''}${sd.castRange !== undefined ? ` · ${typeof sd.castRange === 'number' ? 'range ' + sd.castRange : 'near ' + (c.config?.labels?.keystone ?? 'Beacon')}` : ''}`));
  }
  if (o.size === 'full') {
    const text = h('div', { class: 'rc-text' });
    if (factionName) text.append(h('div', { class: 'rc-faction' }, factionName));
    if (def?.description) text.append(h('p', null, def.description));
    if (ud) text.append(...abilityLines(c, ud.abilities));
    if (ud?.resist && Object.keys(ud.resist).length) text.append(h('div', { class: 'rc-line' }, 'Resist: ' + Object.entries(ud.resist).map(([k, v]) => `${k} ${v > 0 ? '+' : ''}${v}`).join(', ')));
    if (ud?.revive) text.append(h('div', { class: 'rc-line' }, `Rises once on death (${Math.round(ud.revive.hpFraction * 100)}% HP).`));
    if (sd) text.append(h('div', { class: 'abl' }, h('b', null, 'Effect'), h('div', { class: 'adesc' }, sd.effects.map(e => effectText(c, e)).join('. '))));
    if (ed) {
      if (ed.grantAbilities?.length) text.append(...abilityLines(c, ed.grantAbilities));
      if (ed.resist && Object.keys(ed.resist).length) text.append(h('div', { class: 'rc-line' }, 'Resist: ' + Object.entries(ed.resist).map(([k, v]) => `${k} ${v > 0 ? '+' : ''}${v}`).join(', ')));
      if (ed.restrictTo?.length) text.append(h('div', { class: 'rc-line' }, 'Only: ' + ed.restrictTo.join(', ')));
    }
    el.append(text);
  }
  el.style.setProperty('--fcl-a', rgba(color, 0.35));
  return el;
}

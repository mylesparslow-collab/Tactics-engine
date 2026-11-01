// Collection screen: every Relic, filterable by faction, type and ownership. Owned cards open a detail sheet with
// the card, its stats, abilities, Tempering path and a live proving ground; sealed cards show as silhouettes with
// where they are earned.
import './collection.css';
import type { Content } from '../engine/types';
import { allRelics, markSeen, ownedRelics, relicFaction, relicSources, relicType, unseenRelics, type RelicType } from '../engine/collection';
import { label } from '../engine/content';
import { assetUrl } from '../render/anim';
import { mix, shade } from '../render/iso';
import { abilityLines, buildCard, cardColors } from './cards';
import { crestSvg, glyph } from './art';
import { clear, h } from './dom';
import { effectText } from './text';
import { ProvingGround } from './proving';

interface TemperRank { xpRequired: number; statMods?: Record<string, number>; addAbility?: string; label: string }
interface RelicDef { type: string; faction?: string; rarity?: string; pearlCost?: number; card?: string; unit?: string; tempering?: TemperRank[] }
const RELIC_FILES = import.meta.glob('../../content/relics.json', { eager: true, import: 'default' }) as Record<string, Record<string, RelicDef>>;
const RELICS: Map<string, RelicDef> = new Map(Object.entries(Object.values(RELIC_FILES)[0] ?? {}).map(([k, r]) => [r.card ?? r.unit ?? k, r]));

type TypeFilter = 'all' | RelicType;
type OwnFilter = 'all' | 'owned' | 'sealed';
const TYPES: [TypeFilter, string][] = [['all', 'All'], ['hero', 'Heroes'], ['champion', 'Champions'], ['spell', 'Spells'], ['equipment', 'Equipment']];
const OWNS: [OwnFilter, string][] = [['all', 'All'], ['owned', 'Owned'], ['sealed', 'Sealed']];
const TYPE_ORDER: Record<RelicType, number> = { hero: 0, champion: 1, spell: 2, equipment: 3 };
const RARITY: Record<string, string> = { common: 'Common', uncommon: 'Uncommon', rare: 'Rare', exotic: 'Exotic', hero: 'Hero' };
const ROMAN = ['I', 'II', 'III', 'IV'];

// remembered between visits (not persisted)
const memo: { faction: string; type: TypeFilter; own: OwnFilter } = { faction: 'all', type: 'all', own: 'all' };

const nameOf = (c: Content, id: string) => (c.units[id] ?? c.spells[id] ?? c.equipment[id])?.name ?? id;
const costOf = (c: Content, id: string) => (c.units[id] ?? c.spells[id] ?? c.equipment[id])?.cost ?? 0;
function svgSpan(markup: string, cls: string) { const s = h('span', { class: cls }); s.innerHTML = markup; return s; }

/** A card face for a relic not yet earned: frame and name, art as a black silhouette, numbers hidden. */
function sealedCard(c: Content, id: string, size: 'hand' | 'full'): HTMLElement {
  const card = buildCard(id, { size, content: c });
  card.classList.add('sealed');
  const { color, accent } = cardColors(c, id);
  const art = h('div', { class: 'rc-art painted sil', style: `--fc:${shade(color, 0.5)};--fcd:${shade(color, 0.2)};--fcl:${shade(color, 0.8)};--fa:${mix(accent, color, 0.3)}` });
  const still = c.units[id] ? assetUrl(`sprites/${id}_still.png`) : undefined;
  if (still) art.append(h('div', { class: 'rc-ground' }), h('img', { class: 'figure', src: still, alt: '', draggable: 'false' }));
  else art.append(svgSpan(crestSvg(relicFaction(c, id), shade(color, 0.35)), 'sil-crest'));
  card.querySelector('.rc-art')?.replaceWith(art);
  card.querySelectorAll('.rc-stat b, .rc-rail b, .rc-cost span').forEach(b => { b.textContent = '?'; });
  const rail = card.querySelector('.rc-rail.text'); if (rail) rail.textContent = 'Sealed';
  const text = card.querySelector('.rc-text');
  if (text) { clear(text as HTMLElement); text.append(h('p', { class: 'r fl' }, 'Sealed relic')); }
  card.append(h('div', { class: 'sil-lock' }, glyph('lock')));
  return card;
}

function sourceText(c: Content, id: string, src = relicSources(c).get(id)) {
  if (!src) return 'Not yet earnable. Future campaigns and the Pearl exchange will raise this relic.';
  if (src.mission === undefined) return `Part of the starting company in ${src.campaignName}.`;
  return `Earned in ${src.campaignName}, mission ${src.mission + 1}: ${src.missionName}.`;
}

export function showCollection(host: HTMLElement, content: Content, onBack: () => void) {
  const c = content;
  const ids = allRelics(c);
  const owned = ownedRelics(c);
  const unseen = unseenRelics(c, owned);
  const fids = Object.keys(c.factions ?? {}).filter(f => ids.some(i => relicFaction(c, i) === f));
  if (memo.faction !== 'all' && !fids.includes(memo.faction)) memo.faction = 'all';
  const sorted = [...ids].sort((a, b) =>
    fids.indexOf(relicFaction(c, a) ?? '') - fids.indexOf(relicFaction(c, b) ?? '') ||
    TYPE_ORDER[relicType(c, a)] - TYPE_ORDER[relicType(c, b)] || costOf(c, a) - costOf(c, b) || nameOf(c, a).localeCompare(nameOf(c, b)));

  const ownedIn = (f: string) => ids.filter(i => relicFaction(c, i) === f && owned.has(i)).length;
  const totalIn = (f: string) => ids.filter(i => relicFaction(c, i) === f).length;

  const factionRail = h('div', { class: 'cl-factions' });
  const typeSeg = h('div', { class: 'cl-seg' });
  const ownSeg = h('div', { class: 'cl-seg' });
  const grid = h('div', { class: 'cl-body' });
  const count = h('div', { class: 'cl-count' });

  const visible = () => sorted.filter(i =>
    (memo.faction === 'all' || relicFaction(c, i) === memo.faction) &&
    (memo.type === 'all' || relicType(c, i) === memo.type) &&
    (memo.own === 'all' || (memo.own === 'owned') === owned.has(i)));

  const drawBar = () => {
    clear(factionRail); clear(typeSeg); clear(ownSeg);
    factionRail.append(h('button', { class: 'cl-fac all' + (memo.faction === 'all' ? ' on' : ''), onclick: () => { memo.faction = 'all'; redraw(); } },
      h('span', { class: 'cl-fac-ic' }, glyph('collection')), h('span', { class: 'cl-fac-t' }, h('b', null, 'All factions'), h('small', null, `${owned.size} / ${ids.length}`))));
    for (const f of fids) {
      const fd = c.factions?.[f];
      factionRail.append(h('button', { class: 'cl-fac' + (memo.faction === f ? ' on' : ''), style: `--fc:${fd?.color ?? '#777'}`, title: fd?.name ?? f, onclick: () => { memo.faction = f; redraw(); } },
        svgSpan(crestSvg(f), 'crest'), h('span', { class: 'cl-fac-t' }, h('b', null, (fd?.name ?? f).replace(/^The /, '')), h('small', null, `${ownedIn(f)} / ${totalIn(f)}`))));
    }
    for (const [k, t] of TYPES) typeSeg.append(h('button', { class: memo.type === k ? 'on' : '', onclick: () => { memo.type = k; redraw(); } }, t));
    for (const [k, t] of OWNS) ownSeg.append(h('button', { class: memo.own === k ? 'on' : '', onclick: () => { memo.own = k; redraw(); } }, t));
  };

  const tile = (id: string, list: string[]) => {
    const has = owned.has(id);
    const card = has ? buildCard(id, { size: 'hand', content: c }) : sealedCard(c, id, 'hand');
    const b = h('button', { class: 'cl-tile' + (has ? '' : ' locked'), title: has ? nameOf(c, id) : `${nameOf(c, id)} (sealed)`, onclick: () => openDetail(id, list) }, card);
    if (unseen.has(id)) b.append(h('span', { class: 'cl-new' }, 'New'));
    return b;
  };

  const drawGrid = () => {
    clear(grid);
    const list = visible();
    count.textContent = `${list.filter(i => owned.has(i)).length} of ${list.length} owned`;
    if (!list.length) { grid.append(h('p', { class: 'cl-empty muted' }, memo.own === 'owned' ? 'No relics of this kind earned yet.' : 'Nothing matches these filters.')); return; }
    const groups = memo.faction === 'all' ? fids.map(f => [f, list.filter(i => relicFaction(c, i) === f)] as const).filter(([, l]) => l.length) : [[memo.faction, list] as const];
    for (const [f, l] of groups) {
      const fd = c.factions?.[f];
      grid.append(h('section', { class: 'cl-group', style: `--fc:${fd?.color ?? '#777'}` },
        h('header', { class: 'cl-gh' }, svgSpan(crestSvg(f), 'crest'), h('h2', null, fd?.name ?? f), h('i'), h('span', { class: 'cl-gc' }, `${l.filter(i => owned.has(i)).length} / ${l.length}`)),
        h('div', { class: 'cl-grid' }, ...l.map(i => tile(i, list)))));
    }
  };

  const redraw = () => { drawBar(); drawGrid(); };

  // ---------------------------------------------------------------- detail sheet
  let sheet: HTMLElement | null = null, pg: ProvingGround | null = null;
  const closeDetail = () => { pg?.destroy(); pg = null; sheet?.remove(); sheet = null; document.removeEventListener('keydown', onKey); };
  const onKey = (e: KeyboardEvent) => {
    if (!sheet) return;
    if (e.key === 'Escape') { e.preventDefault(); closeDetail(); }
    else if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') { e.preventDefault(); sheet.dispatchEvent(new CustomEvent('step', { detail: e.key === 'ArrowLeft' ? -1 : 1 })); }
  };

  const openDetail = (id: string, list: string[]) => {
    if (!sheet) {
      sheet = h('div', { class: 'cl-sheet', onclick: (e: Event) => { if (e.target === sheet) closeDetail(); } });
      host.append(sheet);
      document.addEventListener('keydown', onKey);
      sheet.addEventListener('step', (e: Event) => {
        const cur = sheet?.dataset.id ?? id, l = JSON.parse(sheet?.dataset.list ?? '[]') as string[];
        const i = l.indexOf(cur), d = (e as CustomEvent<number>).detail;
        if (i >= 0 && l.length > 1) openDetail(l[(i + d + l.length) % l.length], l);
      });
    }
    sheet.dataset.id = id; sheet.dataset.list = JSON.stringify(list);
    pg?.destroy(); pg = null;
    clear(sheet);
    const has = owned.has(id);
    if (has && unseen.delete(id)) { markSeen([id]); drawGrid(); }
    const t = relicType(c, id), r = RELICS.get(id), f = relicFaction(c, id), fd = f ? c.factions?.[f] : undefined;
    const typeName = { hero: 'Hero', champion: 'Champion', spell: 'Spell', equipment: 'Equipment' }[t];
    const step = (d: number) => sheet?.dispatchEvent(new CustomEvent('step', { detail: d }));

    const info = h('div', { class: 'cl-info' },
      h('div', { class: 'kicker' }, [typeName, r?.rarity && r.rarity !== 'hero' ? RARITY[r.rarity] : null, fd?.name].filter(Boolean).join(' · ')),
      h('h2', null, nameOf(c, id)));
    const panel = h('div', { class: 'cl-detail framed' + (has ? '' : ' sealed'), style: `--fc:${fd?.color ?? '#777'}` },
      h('button', { class: 'iconbtn cl-close', title: 'Close (Esc)', onclick: closeDetail }, glyph('close')),
      h('div', { class: 'cl-cardcol' }, has ? buildCard(id, { size: 'full', content: c }) : sealedCard(c, id, 'full'),
        list.length > 1 ? h('div', { class: 'cl-nav' },
          h('button', { class: 'iconbtn', title: 'Previous (←)', onclick: () => step(-1) }, glyph('back')),
          h('span', null, `${list.indexOf(id) + 1} / ${list.length}`),
          h('button', { class: 'iconbtn flip', title: 'Next (→)', onclick: () => step(1) }, glyph('back'))) : null),
      info);
    sheet.append(panel);

    if (!has) {
      info.append(h('div', { class: 'cl-sealed' }, glyph('lock'), h('div', null, h('b', null, 'Sealed relic'), h('p', null, sourceText(c, id)))));
      return;
    }
    pg = new ProvingGround(c);
    info.append(pg.el);
    info.append(...detailBody(c, id, r));
    const src = relicSources(c).get(id);
    info.append(h('p', { class: 'cl-src muted' }, sourceText(c, id, src)));
    pg.show(id);
  };

  host.append(h('div', { class: 'scr coll-scr' },
    h('header', { class: 'scr-head' },
      h('button', { class: 'iconbtn back', title: 'Back', onclick: () => { closeDetail(); onBack(); } }, glyph('back')),
      h('div', { class: 'scr-title' }, h('div', { class: 'kicker' }, 'Collection'), h('h1', null, 'Relics')),
      h('div', { class: 'scr-head-sp' })),
    h('div', { class: 'cl-bar' }, factionRail, h('div', { class: 'cl-row' }, typeSeg, ownSeg, count)),
    grid));
  redraw();
}

/** Stats, abilities, effects and the Tempering path for an owned relic. */
function detailBody(c: Content, id: string, r: RelicDef | undefined): HTMLElement[] {
  const out: HTMLElement[] = [];
  const tide = label(c, 'essence');
  const ud = c.units[id], sd = c.spells[id], ed = c.equipment[id];
  const stat = (k: string, v: string | number, cls = '') => h('div', { class: 'cl-st ' + cls }, h('b', null, String(v)), h('span', null, k));
  if (ud) {
    out.push(h('div', { class: 'cl-stats' }, stat(tide, ud.cost, 'tide'), stat('Health', ud.stats.hp, 'hp'), stat('Attack', ud.stats.attack, 'atk'),
      stat('Defense', ud.stats.defense), stat('AP', ud.stats.ap), stat('Jump', ud.stats.jump)));
    const extra: string[] = [];
    if (ud.role && !['hero', 'champion'].includes(ud.role.toLowerCase())) extra.push(ud.role);
    if (ud.resist && Object.keys(ud.resist).length) extra.push('Resist ' + Object.entries(ud.resist).map(([k, v]) => `${k} ${v > 0 ? '+' : ''}${v}`).join(', '));
    if (ud.revive) extra.push(`Rises once on death at ${Math.round(ud.revive.hpFraction * 100)}% health`);
    if (extra.length) out.push(h('p', { class: 'cl-tags' }, extra.join(' · ')));
    out.push(h('div', { class: 'cl-sec' }, h('h3', null, 'Abilities'), h('div', { class: 'cl-abl' }, ...abilityLines(c, ud.abilities))));
    if (ud.description) out.push(h('p', { class: 'cl-flavor' }, ud.description));
  } else if (sd) {
    const range = sd.castRange === undefined ? 'Anywhere' : typeof sd.castRange === 'number' ? `Within ${sd.castRange} of an ally` : `Within ${sd.castRange.nearKeystone} of your ${label(c, 'keystone')}`;
    out.push(h('div', { class: 'cl-stats' }, stat(tide, sd.cost, 'tide'), stat('Target', sd.target), stat('Range', range, 'wide'), ...(sd.area ? [stat('Area', sd.area.size)] : [])));
    if (sd.description) out.push(h('p', { class: 'cl-lead' }, sd.description));
    out.push(h('div', { class: 'cl-sec' }, h('h3', null, 'Effects'), h('ul', { class: 'cl-fx' }, ...sd.effects.map(e => h('li', null, effectText(c, e))))));
  } else if (ed) {
    const mods = Object.entries(ed.statMods ?? {}).map(([k, v]) => stat(k, `${(v ?? 0) >= 0 ? '+' : ''}${v}`, 'mod'));
    out.push(h('div', { class: 'cl-stats' }, stat(tide, ed.cost, 'tide'), ...mods));
    if (ed.description) out.push(h('p', { class: 'cl-lead' }, ed.description));
    if (ed.resist && Object.keys(ed.resist).length) out.push(h('p', { class: 'cl-tags' }, 'Resist ' + Object.entries(ed.resist).map(([k, v]) => `${k} ${v > 0 ? '+' : ''}${v}`).join(', ')));
    if (ed.grantAbilities?.length) out.push(h('div', { class: 'cl-sec' }, h('h3', null, 'Grants'), h('div', { class: 'cl-abl' }, ...abilityLines(c, ed.grantAbilities))));
    if (ed.restrictTo?.length) out.push(h('p', { class: 'cl-tags' }, 'Only for: ' + ed.restrictTo.map(x => c.units[x]?.name ?? x).join(', ')));
  }
  if (r?.tempering?.length) {
    out.push(h('div', { class: 'cl-sec' }, h('h3', null, 'Tempering'),
      h('ol', { class: 'cl-temper' }, ...r.tempering.map((t, i) => {
        const mods = Object.entries(t.statMods ?? {}).map(([k, v]) => `${v >= 0 ? '+' : ''}${v} ${k}`);
        const ab = t.addAbility ? c.abilities[t.addAbility] : undefined;
        return h('li', null, h('span', { class: 'cl-rank' }, ROMAN[i] ?? String(i + 1)),
          h('div', null, h('b', null, t.label), h('span', { class: 'muted' }, ` · ${t.xpRequired} xp`),
            h('div', { class: 'cl-tdesc' }, [...mods, ab ? `learns ${ab.name}${ab.description ? ': ' + ab.description : ''}` : ''].filter(Boolean).join(', '))));
      }))));
  }
  return out;
}

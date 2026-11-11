import type { Content, MissionDef } from '../engine/types';
import { isUnlocked, loadProgress, saveProgress } from '../engine/campaign';
import { label } from '../engine/content';
import { clear, h } from './dom';
import { describeObjectives } from './text';
import { buildSkirmish, playableFactions } from '../engine/skirmish';
import { artNode, paintedArtUrl } from './cards';
import { crestSvg, glyph, illuminated, installArt, kit, teamFaction } from './art';
import { Game } from '../engine/game';
import { Renderer } from '../render/renderer';
import { showCollection } from './collection';
import { allRelics, ownedRelics } from '../engine/collection';
import { loadBest, loadRun, TW } from '../engine/autobattle';

export interface MissionChoice { missionId: string; campaign?: { id: string; index: number } }

type Pick = (c: MissionChoice) => void;
interface Ctx { root: HTMLElement; content: Content; errors: string[]; onPick: Pick; tw?: TidewatchMenu }

// remembered between visits to the menu (not persisted)
const memo = { mine: '', theirs: '', map: '', campaign: '', node: -1 };

function svgEl(markup: string, cls: string) {
  const s = h('span', { class: cls }); s.innerHTML = markup; return s;
}
export function crest(fid: string | undefined, cls = 'crest', color?: string) { return svgEl(crestSvg(fid, color), cls); }

let backdrop: { r: Renderer; ro: ResizeObserver } | null = null;
/** Stop the live board behind the menus (called when a battle starts). */
export function stopBackdrop() { if (backdrop) { backdrop.r.stop(); backdrop.ro.disconnect(); backdrop = null; } }

/** The real game board, idling under the menus: painted tiles and units instead of illustrated key art. */
function liveBoard(content: Content): HTMLElement {
  const wrap = h('div', { class: 'bg' });
  const cv = h('canvas', { class: 'bg-board' });
  wrap.append(h('div', { class: 'bg-drift' }, cv), h('div', { class: 'bg-shade' }));
  stopBackdrop();
  try {
    const camp = Object.values(content.campaigns)[0];
    const mid = camp?.missions[0]?.mission ?? Object.keys(content.missions)[0];
    const game = new Game(content, mid, { roster: camp?.startingRoster });
    // put the player's opening hand on the field so the backdrop shows a company, not an empty board
    for (let i = game.teams[game.current].hand.length - 1, n = 0; i >= 0 && n < 6; i--) {
      const id = game.teams[game.current].hand[i];
      if (game.cardKind(id) !== 'unit') continue;
      const t = game.cardTargets(game.current, i);
      if (t.length) { game.teams[game.current].essence = 999; game.playCard(game.current, i, t[(n * 3) % t.length].x, t[(n * 3) % t.length].y); n++; }
    }
    const r = new Renderer(cv);
    requestAnimationFrame(() => { r.setGame(game); r.zoomBy(1.35); r.pan(wrap.clientWidth * 0.2, wrap.clientHeight * 0.05); r.start(); });
    const ro = new ResizeObserver(() => r.resize()); ro.observe(wrap);
    backdrop = { r, ro };
  } catch (e) { console.warn('menu backdrop unavailable', e); }
  return wrap;
}

/** Persistent menu backdrop; screens swap inside its host. */
export function shell(root: HTMLElement, content: Content): HTMLElement {
  installArt();
  let host = root.querySelector<HTMLElement>(':scope > .shell > .host');
  if (!host || !root.classList.contains('screen')) {
    clear(root); root.className = 'screen';
    host = h('div', { class: 'host' });
    root.append(h('div', { class: 'shell' }, liveBoard(content), host));
  }
  clear(host);
  root.scrollTop = 0;
  return host;
}

export function screenHeader(title: string, kicker: string | null, onBack: () => void) {
  return h('header', { class: 'scr-head' },
    h('button', { class: 'iconbtn back', title: 'Back', onclick: onBack }, glyph('back')),
    h('div', { class: 'scr-title' }, kicker ? h('div', { class: 'kicker' }, kicker) : null, h('h1', null, title)),
    h('div', { class: 'scr-head-sp' }));
}

export function ornament(cls = 'orn') {
  return h('div', { class: cls }, h('i'), svgEl('<svg viewBox="0 0 40 16"><path d="M20 1 L27 8 L20 15 L13 8 Z" fill="currentColor"/><circle cx="4" cy="8" r="2" fill="currentColor"/><circle cx="36" cy="8" r="2" fill="currentColor"/></svg>', 'orn-gem'), h('i'));
}

// ---------------------------------------------------------------- title

/** Tidewatch entry points wired by main.ts. */
export interface TidewatchMenu { onStart: () => void; onResume: () => void; onAbandon: () => void }

export function showMenu(root: HTMLElement, content: Content, errors: string[], onPick: Pick, tw?: TidewatchMenu) {
  const ctx: Ctx = { root, content, errors, onPick, tw };
  const host = shell(root, content);
  const L = content.config?.labels ?? {};
  const camps = Object.entries(content.campaigns);
  const campDone = camps.reduce((n, [id, c]) => n + Math.min(loadProgress(id).completed, c.missions.length), 0);
  const campTotal = camps.reduce((n, [, c]) => n + c.missions.length, 0);
  const scen = Object.keys(content.missions).filter(id => !id.startsWith('skirmish:')).length;
  const item = (title: string, sub: string, on: (() => void) | null, extra = '') =>
    h('button', { class: 'mitem' + extra, disabled: !on, onclick: on ?? undefined }, h('span', { class: 'mi-title' }, title), h('span', { class: 'mi-sub' }, sub));
  const scr = h('div', { class: 'scr title-scr' },
    h('div', { class: 'logo-block' },
      h('img', { class: 'logo-img', src: '', alt: L.title ?? 'Brinewake', draggable: 'false' }),
      h('div', { class: 'logo-sub' }, L.subtitle ?? 'A tactics game')),
    h('nav', { class: 'mainnav' },
      item('Campaign', campTotal ? `${campDone} / ${campTotal}` : '', camps.length ? () => showCampaign(ctx) : null, ' primary'),
      item('Skirmish', '', playableFactions(content).length >= 2 ? () => showSkirmish(ctx) : null),
      ...tidewatchItems(item, tw),
      item('Scenarios', String(scen), scen ? () => showScenarios(ctx) : null),
      item('Collection', `${ownedRelics(content).size} / ${allRelics(content).length}`, () => showCollection(shell(root, content), content, () => showMenu(root, content, errors, onPick, tw)))),
    errors.length ? h('details', { class: 'errbox' }, h('summary', null, `Content check: ${errors.length} problem${errors.length === 1 ? '' : 's'}`),
      h('ul', null, ...errors.slice(0, 30).map(e => h('li', null, e)))) : null,
    h('footer', { class: 'ver' }, 'Early access'));
  (scr.querySelector('.logo-img') as HTMLImageElement).src = kit('logo');
  host.append(scr);
}

/** Tidewatch nav entries: a plain entry with the best result, or Resume / Abandon when a run is saved. */
function tidewatchItems(item: (title: string, sub: string, on: (() => void) | null, extra?: string) => HTMLElement, tw?: TidewatchMenu): HTMLElement[] {
  if (!tw) return [];
  const saved = loadRun(), best = loadBest();
  if (saved) return [
    item('Resume Tidewatch', `Watch ${saved.watch} / ${TW.watches} \u00B7 Light ${saved.light}`, tw.onResume),
    item('Abandon run', '', () => { if (confirm('Abandon your Tidewatch run? It cannot be resumed.')) tw.onAbandon(); }, ' minor'),
  ];
  return [item('Tidewatch', best ? (best.won ? 'Held all ten' : `Best: watch ${best.watch}`) : '', tw.onStart)];
}

// ---------------------------------------------------------------- campaign

function showCampaign(ctx: Ctx) {
  const { content } = ctx;
  const host = shell(ctx.root, ctx.content);
  const ids = Object.keys(content.campaigns);
  const cid = ids.includes(memo.campaign) ? memo.campaign : ids[0];
  memo.campaign = cid;
  const camp = content.campaigns[cid];
  const prog = loadProgress(cid);
  const n = camp.missions.length;
  const firstOpen = Math.min(prog.completed, n - 1);
  let sel = memo.node >= 0 && memo.node < n && isUnlocked(prog, memo.node) ? memo.node : firstOpen;

  // node layout: a winding survey route across the chart
  const pts = camp.missions.map((_, i) => {
    const t = n === 1 ? 0.5 : i / (n - 1);
    return { x: 9 + t * 82, y: 52 + Math.sin(i * 1.25 + 0.4) * 26 };
  });
  let d = `M${pts[0].x} ${pts[0].y}`;
  for (let i = 1; i < pts.length; i++) { const a = pts[i - 1], b = pts[i]; d += ` C${(a.x + b.x) / 2} ${a.y} ${(a.x + b.x) / 2} ${b.y} ${b.x} ${b.y}`; }
  const done = Math.min(prog.completed, n - 1);
  let dDone = `M${pts[0].x} ${pts[0].y}`;
  for (let i = 1; i <= done; i++) { const a = pts[i - 1], b = pts[i]; dDone += ` C${(a.x + b.x) / 2} ${a.y} ${(a.x + b.x) / 2} ${b.y} ${b.x} ${b.y}`; }

  const chart = h('div', { class: 'chartmap' });
  chart.append(svgEl(`<svg viewBox="0 0 100 100" preserveAspectRatio="none">
      <g fill="none" stroke="#6b5838" stroke-opacity=".35" vector-effect="non-scaling-stroke">
        <path d="M0 18 C14 22 20 10 34 14 S52 4 66 10 S88 2 100 8" vector-effect="non-scaling-stroke"/>
        <path d="M0 24 C14 28 22 16 36 20 S54 10 68 16 S88 8 100 14" stroke-dasharray="1 2" vector-effect="non-scaling-stroke"/>
        <path d="M0 92 C20 86 30 96 50 90 S80 84 100 92" vector-effect="non-scaling-stroke"/>
      </g>
      <path d="${d}" fill="none" stroke="#5a4426" stroke-opacity=".55" stroke-width="2.4" stroke-dasharray="6 6" vector-effect="non-scaling-stroke"/>
      ${prog.completed ? `<path d="${dDone}" fill="none" stroke="#9b3d2e" stroke-width="3" vector-effect="non-scaling-stroke"/>` : ''}
    </svg>`, 'chart-lines'),
    svgEl(`<svg viewBox="0 0 100 100"><g fill="none" stroke="#5a4426" stroke-opacity=".6"><circle cx="50" cy="50" r="30"/><circle cx="50" cy="50" r="22" stroke-dasharray="2 2"/></g>
      <path d="M50 8 L56 50 L50 92 L44 50 Z" fill="#5a4426" fill-opacity=".7"/><path d="M8 50 L50 44 L92 50 L50 56 Z" fill="#5a4426" fill-opacity=".45"/>
      <text x="50" y="7" text-anchor="middle" font-size="9" fill="#5a4426" font-family="Cinzel,serif">N</text></svg>`, 'compass'),
    h('div', { class: 'chart-label' }, camp.name));

  const detail = h('aside', { class: 'mdetail framed' });
  const nodes: HTMLButtonElement[] = [];
  const drawDetail = () => {
    clear(detail);
    const step = camp.missions[sel], md = content.missions[step.mission];
    const won = sel < prog.completed;
    const unlocks = (step.unlocks ?? []).map(u => ({ id: u, name: content.units[u]?.name ?? content.spells[u]?.name ?? content.equipment[u]?.name ?? u }));
    detail.append(h('div', null,
      camp.faction ? h('figure', { class: 'md-art' }, heroImg(content, camp.faction)) : null,
      h('div', { class: 'kicker' }, `Mission ${sel + 1} of ${n}`),
      h('h2', null, md?.name ?? step.mission),
      ornament(),
      md?.description ? h('p', { class: 'lead' }, md.description) : null,
      unlocks.length ? h('div', { class: 'rewards' }, h('div', { class: 'rw-h' }, won ? 'Earned' : 'Reward'), h('div', { class: 'rw-list' }, ...unlocks.map(u => h('div', { class: 'rw', title: u.name }, h('div', { class: 'rw-art' }, artNode(u.id, content)), h('span', null, u.name))))) : null,
      h('div', { class: 'mstate' + (won ? ' won' : '') }, won ? 'Victory recorded' : 'Not yet won'),
      h('button', { class: 'btn-gold big', disabled: !md, onclick: () => { memo.node = sel; ctx.onPick({ missionId: step.mission, campaign: { id: cid, index: sel } }); } }, won ? 'Replay' : 'Begin')));
  };
  camp.missions.forEach((m, i) => {
    const ok = isUnlocked(prog, i) && !!content.missions[m.mission];
    const won = i < prog.completed;
    const b = h('button', {
      class: `node${won ? ' won' : ''}${ok ? '' : ' locked'}${i === firstOpen && !won ? ' next' : ''}${i === sel ? ' sel' : ''}`,
      style: `left:${pts[i].x}%;top:${pts[i].y}%`, disabled: !ok, title: content.missions[m.mission]?.name ?? m.mission,
      onclick: () => { sel = i; nodes.forEach((x, j) => x.classList.toggle('sel', j === i)); drawDetail(); },
    }, h('span', { class: 'seal' }, ok ? (won ? glyph('check') : String(i + 1)) : glyph('lock')), h('span', { class: 'nlabel' }, content.missions[m.mission]?.name ?? m.mission));
    nodes.push(b); chart.append(b);
  });
  drawDetail();

  const tabs = ids.length > 1 ? h('div', { class: 'tabs camp-tabs' }, ...ids.map(id => {
    const c = content.campaigns[id], f = c.faction ? content.factions?.[c.faction] : undefined;
    const won = Math.min(loadProgress(id).completed, c.missions.length);
    return h('button', {
      class: 'tab' + (id === cid ? ' on' : ''), title: c.name, style: f?.color ? `--tab-c:${f.color}` : undefined,
      onclick: () => { memo.campaign = id; memo.node = -1; showCampaign(ctx); },
    }, (f?.name ?? c.name).replace(/^The /, ''), h('span', { class: 'tab-prog' }, `${won}/${c.missions.length}`));
  })) : null;
  host.append(h('div', { class: 'scr camp-scr' },
    screenHeader(camp.name, 'Campaign', () => showMenu(ctx.root, content, ctx.errors, ctx.onPick, ctx.tw)),
    tabs,
    h('div', { class: 'camp-body' }, h('div', { class: 'chartwrap framed' }, chart), detail),
    h('div', { class: 'camp-foot' },
      camp.description ? h('p', { class: 'muted' }, camp.description) : null,
      h('button', { class: 'linkbtn', onclick: () => { if (confirm('Reset campaign progress?')) { saveProgress(cid, { completed: 0 }); memo.node = -1; showCampaign(ctx); } } }, 'Reset progress'))));
}

// ---------------------------------------------------------------- skirmish

/** Small isometric preview of a map, coloured by terrain. */
function mapPreview(content: Content, mapId: string) {
  const m = content.maps[mapId];
  const H = m.tiles.length, W = m.tiles[0]?.length ?? 0;
  const tw = 10, th = 5;
  let s = '';
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const ch = m.tiles[y][x], terr = content.terrain[m.legend[ch]];
    if ((terr as { void?: boolean } | undefined)?.void) continue;
    const hgt = Number(m.heights?.[y]?.[x] ?? 0) || 0;
    const cx = (x - y) * tw / 2 + H * tw / 2, cy = (x + y) * th / 2 - hgt * 2 + 8;
    const col = terr?.color ?? '#888';
    s += `<path d="M${cx} ${cy} l${tw / 2} ${th / 2} l${-tw / 2} ${th / 2} l${-tw / 2} ${-th / 2} Z" fill="${col}" stroke="#000" stroke-opacity=".12" stroke-width=".3"/>`;
    if (hgt > 0) s += `<path d="M${cx - tw / 2} ${cy + th / 2} l${tw / 2} ${th / 2} v${hgt * 2} l${-tw / 2} ${-th / 2} Z" fill="#000" fill-opacity=".25"/>`;
  }
  for (const k of m.keystones ?? []) {
    const cx = (k.x - k.y) * tw / 2 + H * tw / 2, cy = (k.x + k.y) * th / 2 + 8 + th / 2;
    s += `<circle cx="${cx}" cy="${cy}" r="3.2" fill="#ffd86b" stroke="#5a3f10" stroke-width=".8"/>`;
  }
  const vw = (W + H) * tw / 2, vh = (W + H) * th / 2 + 20;
  return svgEl(`<svg viewBox="0 0 ${vw} ${vh}" preserveAspectRatio="xMidYMid meet">${s}</svg>`, 'mapprev');
}

function showSkirmish(ctx: Ctx) {
  const { content } = ctx;
  const host = shell(ctx.root, ctx.content);
  const factions = playableFactions(content);
  const maps = Object.keys(content.maps);
  if (!factions.includes(memo.mine)) memo.mine = factions[0];
  if (!factions.includes(memo.theirs)) memo.theirs = factions.find(f => f !== memo.mine) ?? factions[1];
  if (!maps.includes(memo.map)) memo.map = maps[0];

  const side = (key: 'mine' | 'theirs', title: string) => {
    const box = h('section', { class: 'fside framed ' + key });
    const draw = () => {
      clear(box);
      const fid = memo[key], f = content.factions?.[fid];
      box.style.setProperty('--fc', f?.color ?? '#777');
      box.append(
        h('figure', { class: 'fs-art' }, heroImg(content, fid)),
        h('div', { class: 'kicker' }, title),
        h('div', { class: 'fhero' }, crest(fid, 'crest big'), h('div', { class: 'fhero-t' }, h('h2', null, f?.name ?? fid), h('p', null, f?.tagline ?? ''))),
        h('div', { class: 'fgrid' }, ...factions.map(id => h('button', {
          class: 'fpick' + (id === fid ? ' on' : ''), title: content.factions?.[id]?.name ?? id, style: `--fc:${content.factions?.[id]?.color ?? '#777'}`,
          onclick: () => { memo[key] = id; draw(); },
        }, crest(id, 'crest'), h('span', null, (content.factions?.[id]?.name ?? id).replace(/^The /, ''))))));
    };
    draw();
    return box;
  };

  const mapBox = h('div', { class: 'mappick' });
  const drawMap = () => {
    clear(mapBox);
    const i = maps.indexOf(memo.map), m = content.maps[memo.map];
    const go = (d: number) => { memo.map = maps[(i + d + maps.length) % maps.length]; drawMap(); };
    mapBox.append(
      h('div', { class: 'kicker' }, 'Battlefield'),
      h('div', { class: 'mp-row' }, h('button', { class: 'iconbtn', title: 'Previous map', onclick: () => go(-1) }, glyph('back')),
        h('div', { class: 'mp-name' }, m.name), h('button', { class: 'iconbtn flip', title: 'Next map', onclick: () => go(1) }, glyph('back'))),
      mapPreview(content, memo.map),
      h('p', { class: 'mp-desc' }, m.description ?? ''));
  };
  drawMap();

  host.append(h('div', { class: 'scr skirm-scr' },
    screenHeader('Skirmish', 'Battle', () => showMenu(ctx.root, content, ctx.errors, ctx.onPick, ctx.tw)),
    h('div', { class: 'skirm-body' },
      side('mine', 'Your faction'),
      h('div', { class: 'vs-col' }, h('div', { class: 'vs' }, 'VS'), mapBox,
        h('button', { class: 'btn-gold big', onclick: () => {
          const m = buildSkirmish(content, memo.map, [memo.mine, memo.theirs]);
          content.missions[m.id] = m;
          ctx.onPick({ missionId: m.id });
        } }, 'To Battle')),
      side('theirs', 'Opponent'))));
}

// ---------------------------------------------------------------- scenarios

function showScenarios(ctx: Ctx) {
  const { content } = ctx;
  const host = shell(ctx.root, ctx.content);
  const list = Object.entries(content.missions).filter(([id]) => !id.startsWith('skirmish:'));
  host.append(h('div', { class: 'scr scen-scr' },
    screenHeader('Scenarios', 'Standalone battles', () => showMenu(ctx.root, content, ctx.errors, ctx.onPick, ctx.tw)),
    h('div', { class: 'scen-grid' }, ...list.map(([id, m]) => {
      const fids = m.teams.map(t => missionTeamFaction(content, m, t));
      return h('button', { class: 'scen framed', onclick: () => ctx.onPick({ missionId: id }) },
        h('div', { class: 'scen-crests' }, ...fids.slice(0, 2).map((f, i) => crest(f, 'crest', m.teams[i].color))),
        h('div', { class: 'scen-t' }, h('h3', null, m.name), h('p', null, m.description ?? '')),
        h('span', { class: 'pl-arrow' }, '›'));
    }))));
}

function missionTeamFaction(content: Content, m: MissionDef, t: MissionDef['teams'][number]) {
  const ids = [...(t.warband ?? []), ...(t.units ?? []).map(u => u.unit)];
  if (t.useCampaignRoster) for (const c of Object.values(content.campaigns)) if (c.missions.some(x => x.mission === m.id)) ids.push(...c.startingRoster);
  return teamFaction(content, ids);
}

// ---------------------------------------------------------------- briefing

export function showBriefing(root: HTMLElement, content: Content, choice: MissionChoice, onStart: () => void, onBack: () => void) {
  const m = content.missions[choice.missionId];
  const obj = describeObjectives(content, m);
  const map = content.maps[m.map];
  const host = shell(root, content);
  const kicker = choice.campaign ? `${content.campaigns[choice.campaign.id].name} · Mission ${choice.campaign.index + 1}` : 'Skirmish';
  const teams = m.teams.map(t => ({ t, f: missionTeamFaction(content, m, t) }));
  const story = (m.briefing ?? []).filter(t => t.trim() !== m.description?.trim());
  const objRow = (kind: 'win' | 'lose', t: string) => h('li', { class: 'bo-row ' + kind }, h('i', { class: 'bo-mark' }), h('span', null, t));
  const side = h('aside', { class: 'brief-side framed' },
    h('div', { class: 'bs-map' }, mapPreview(content, m.map),
      h('div', { class: 'bs-mapname' }, h('span', { class: 'kicker' }, 'Battlefield'), h('b', null, map?.name ?? m.map),
        h('small', null, `${m.startingEssence ?? 100} ${label(content, 'essence')} to start`))),
    h('div', { class: 'bs-forces' }, ...teams.map(({ t, f }) =>
      h('div', { class: 'bs-force', style: `--tc:${t.color}` }, crest(f, 'crest', t.color),
        h('b', null, t.name), h('small', null, t.controller === 'human' ? 'You' : 'Enemy')))),
    h('div', { class: 'bs-objs' },
      h('div', { class: 'kicker' }, obj.winAny ? 'Victory, any of' : 'Victory'),
      h('ul', null, ...obj.win.map(t => objRow('win', t))),
      h('div', { class: 'kicker lose' }, 'Defeat'),
      h('ul', null, ...obj.lose.map(t => objRow('lose', t)))),
    h('button', { class: 'btn-gold big bs-deploy', onclick: onStart }, 'Deploy'));
  const me = teams.find(x => x.t.controller === 'human') ?? teams[0];
  const foe = teams.find(x => x !== me) ?? teams[1];
  if (!choice.campaign && me && foe) {
    // Skirmish: the two sides face each other as painted heroes; the order of battle sits between them.
    const fig = (x: typeof me, who: string, cls: string) => {
      const fd = x.f ? content.factions?.[x.f] : undefined;
      return h('figure', { class: 'bf-art ' + cls, style: `--tc:${fd?.color ?? x.t.color}` }, heroImg(content, x.f),
        h('figcaption', null, crest(x.f, 'crest', x.t.color), h('span', { class: 'kicker' }, who), h('b', null, (fd?.name ?? x.t.name)), fd?.tagline ? h('i', null, fd.tagline) : null));
    };
    host.append(h('div', { class: 'scr brief-scr vs-brief' },
      h('header', { class: 'brief-top' }, h('button', { class: 'iconbtn back', title: 'Back', onclick: onBack }, glyph('back'))),
      h('div', { class: 'vsb-grid' }, fig(me, 'You', 'mine'),
        h('div', { class: 'vsb-mid' }, h('div', { class: 'kicker' }, 'Skirmish'), h('div', { class: 'vsb-vs' }, 'vs'), side),
        fig(foe, 'Opponent', 'theirs'))));
    return;
  }
  host.append(h('div', { class: 'scr brief-scr' + (me?.f && paintedArtUrl(heroOf(content, me.f) ?? '') ? ' has-art' : '') },
    me?.f ? h('figure', { class: 'brief-bg', style: `--tc:${me.t.color}` }, heroImg(content, me.f)) : null,
    h('header', { class: 'brief-top' }, h('button', { class: 'iconbtn back', title: 'Back', onclick: onBack }, glyph('back'))),
    h('div', { class: 'brief-grid' },
      h('section', { class: 'brief-story' },
        h('div', { class: 'kicker' }, kicker),
        h('h1', { class: 'brief-title' }, m.name),
        m.description ? h('p', { class: 'lead' }, m.description) : null,
        story.length ? h('div', { class: 'brief-text' }, ...story.map((t, i) => i || t.length < 160 ? h('p', null, t) : h('p', { class: 'dropcap' }, ...illuminated(t)))) : null),
      side)));
}

/** Each faction's face: the campaign lead where there is one, else the first hero. */
const LEADS: Record<string, string> = { salt_concord: 'salt_concord_tamsin_orrel', hadal_court: 'hadal_court_herald_vhaal', returning_tide: 'returning_tide_maren_ketch',
  salvage_compact: 'salvage_compact_ketta_vane', reef_ascendant: 'reef_ascendant_coralspire', lanternkeepers: 'lanternkeepers_captain_hollis_drenn',
  overcurrent: 'overcurrent_the_undersinging', gyre: 'gyre_wren_halloway', hermitage: 'hermitage_mother_harrow', slough: 'slough_eldest_skin' };
function heroOf(content: Content, fid: string): string | undefined {
  if (LEADS[fid] && content.units[LEADS[fid]]) return LEADS[fid];
  return Object.keys(content.units).find(id => content.units[id].faction === fid && content.units[id].hero);
}
function heroImg(content: Content, fid: string | undefined): HTMLElement | null {
  const id = fid ? heroOf(content, fid) : undefined; const url = id ? paintedArtUrl(id) : undefined;
  return url ? h('img', { src: url, alt: '', draggable: 'false' }) : null;
}

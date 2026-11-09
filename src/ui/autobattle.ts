// Tidewatch screens: Charter -> Tideline (market) -> Formation -> Battle -> Result, plus the run-over screen.
// All rules live in src/engine/autobattle.ts; this file only draws them. House look: same shell, kicker/ornament
// headers, .framed panels and gold buttons as Skirmish and Collection.
import './autobattle.css';
import type { Content, MapDef, Pos } from '../engine/types';
import { Game } from '../engine/game';
import { label } from '../engine/content';
import { Renderer } from '../render/renderer';
import {
  TW, applyBattleResult, berthsAt, buildBattleMission, buy, cardCost, cardPrice, charterFactions, clearTempered, cropArena,
  dredge, enemyCrew, equip, factionName, greedyShop, isLampEater, layoutCrew, loadBest, loadRun, newRun, nextRankXp, rankLabel, rankOf, recordBest,
  rememberLayout, resolveBattle, resultOf, saveRun, scrap, scrapValue, temperingOf, tierCap, toCrew, toHold, toggleMark, trackBattle,
  unequip, canEquip, type BattleResult, type Run, type WatchSummary,
} from '../engine/autobattle';
import { clear, h } from './dom';
import { artNode, buildCard } from './cards';
import { crestSvg, glyph, installArt } from './art';
import { crest, ornament, screenHeader, shell } from './menu';
import { stopBackdrop } from './menu';
import { GameSession } from './session';
import { enterBattle } from '../audio/scenes';
import { playBattleStart, preloadBattleBanks } from '../audio/sfx';

export interface TidewatchHost { root: HTMLElement; content: Content; onExit: () => void }
export type DemoStage = 'charter' | 'market' | 'formation' | 'battle' | 'result';

const svgSpan = (markup: string, cls: string) => { const s = h('span', { class: cls }); s.innerHTML = markup; return s; };

export function createTidewatch(host: TidewatchHost) {
  const { root, content } = host;
  let run: Run | null = null;
  let session: GameSession | null = null;
  let formation: { renderer: Renderer; ro: ResizeObserver } | null = null;
  let marketMsg = '';
  let equipSel: number | null = null;
  const charterPick: string[] = [];

  const L = (t: string) => label(content, t);
  const uname = (id: string) => (content.units[id] ?? content.spells[id] ?? content.equipment[id])?.name ?? id;
  const fcolor = (id: string) => { const f = (content.units[id] ?? content.spells[id] ?? content.equipment[id])?.faction; return (f && content.factions?.[f]?.color) || '#777'; };

  function teardown() {
    session?.destroy(); session = null;
    if (formation) { formation.renderer.stop(); formation.ro.disconnect(); formation = null; }
    clearTempered(content);
  }
  const save = () => saveRun(run);
  const leave = () => { teardown(); host.onExit(); };

  // ---------------------------------------------------------------- small widgets

  const portrait = (id: string, cls = '') => h('div', { class: 'tw-port ' + cls, style: `--pc:${fcolor(id)}` }, artNode(id, content));

  function lamps(n: number) {
    return h('span', { class: 'tw-lamps', title: `Light ${n} of ${TW.startLight}`, 'aria-label': `Light ${n}` },
      ...Array.from({ length: TW.startLight }, (_, i) => h('i', { class: 'lamp' + (i < n ? ' lit' : '') })));
  }

  function rankPips(def: string, xp: number) {
    const r = rankOf(def, xp), m = temperingOf(def).length;
    return h('span', { class: 'tw-pips', title: r ? `${rankLabel(def, r)} (rank ${r} of ${m})` : 'Untempered' },
      ...Array.from({ length: m }, (_, i) => h('i', { class: i < r ? 'on' : '' })));
  }

  function xpBar(def: string, xp: number) {
    const ts = temperingOf(def), r = rankOf(def, xp);
    const next = nextRankXp(def, xp), prev = r ? ts[r - 1].xpRequired : 0;
    const pct = next === null ? 100 : Math.round(((xp - prev) / (next - prev)) * 100);
    return h('div', { class: 'tw-xp', title: next === null ? `${xp} XP, fully tempered` : `${xp} / ${next} XP to ${ts[r]?.label ?? 'the next rank'}` },
      h('i', { style: `width:${pct}%` }), h('span', null, next === null ? `${xp} XP` : `${xp}/${next}`));
  }

  function statline(id: string) {
    const d = content.units[id];
    return h('span', { class: 'tw-stats' }, `${d.stats.attack} atk · ${d.stats.hp} hp · ${d.stats.defense} def`);
  }

  function resource(title: string, value: Node | string, sub?: string) {
    return h('div', { class: 'tw-res' }, h('div', { class: 'kicker' }, title), h('div', { class: 'tw-res-v num' }, value), sub ? h('small', null, sub) : null);
  }

  function header(title: string, kicker: string, back: () => void) {
    return screenHeader(title, kicker, back);
  }

  function resourceBar(r: Run) {
    return h('div', { class: 'tw-bar' },
      resource('Light', lamps(r.light)),
      resource('Salvage', String(r.salvage), 'to spend'),
      resource('Berths', `${r.crew.length} / ${berthsAt(r.watch)}`, 'on the field'),
      resource('Watch', `${r.watch}`, `of ${TW.watches}`));
  }

  // ---------------------------------------------------------------- charter

  function showCharter() {
    teardown(); run = null; marketMsg = '';
    const host_ = shell(root, content);
    const factions = charterFactions(content);
    const render = () => {
      clear(box);
      const picked = charterPick;
      box.append(...factions.map(id => {
        const f = content.factions?.[id];
        return h('button', {
          class: 'fpick tw-fpick' + (picked.includes(id) ? ' on' : ''), style: `--fc:${f?.color ?? '#777'}`, title: f?.tagline ?? '',
          onclick: () => {
            const i = picked.indexOf(id);
            if (i >= 0) picked.splice(i, 1); else { if (picked.length >= 2) picked.shift(); picked.push(id); }
            render(); renderSummary();
          },
        }, crest(id, 'crest'), h('span', null, factionName(content, id)));
      }));
    };
    const box = h('div', { class: 'fgrid tw-fgrid' });
    const summary = h('div', { class: 'tw-charter-sum' });
    const go = h('button', { class: 'btn-gold big', onclick: () => { if (picked().length) beginRun(picked()); } }, 'Take the Lamp');
    const picked = () => charterPick;
    const renderSummary = () => {
      clear(summary);
      const ps = picked();
      go.disabled = ps.length === 0;
      if (!ps.length) { summary.append(h('p', { class: 'tw-hint' }, 'Choose one faction, or two to pair them. The Tideline sells only your Charter.')); return; }
      summary.append(...ps.map(id => {
        const f = content.factions?.[id];
        return h('div', { class: 'tw-chosen', style: `--fc:${f?.color ?? '#777'}` }, crest(id, 'crest big'),
          h('div', null, h('h3', null, factionName(content, id)), h('p', null, f?.tagline ?? '')));
      }));
    };
    render(); renderSummary();
    host_.append(h('div', { class: 'scr tw-scr tw-charter' },
      header('Tidewatch', 'Hold the shelf', leave),
      h('div', { class: 'tw-charter-body' },
        h('section', { class: 'tw-intro framed' },
          h('div', { class: 'kicker' }, 'The Long Ebb'),
          h('h2', null, 'Ten Watches'),
          ornament(),
          h('p', { class: 'lead' }, 'You keep a lamp on the drained shelf. Between watches you hire champions at the Tideline; then you set them on the shelf and step back. Both crews fight on their own.'),
          h('ul', { class: 'tw-rules' },
            h('li', null, h('b', null, 'Light 5. '), 'Lose a watch and the lamp dims. At 0 the run is over.'),
            h('li', null, h('b', null, 'The tide comes back. '), `From round ${TW.floodStart} the sea floods the arena from the edges: it drowns anyone not at home in it.`),
            h('li', null, h('b', null, 'Tempering. '), 'Champions that survive watches earn ranks. A duplicate feeds a veteran instead of adding a body.'),
            h('li', null, h('b', null, 'Lamp-eaters. '), `Watches ${TW.lampEaterWatches.join(' and ')} are led by a hero.`))),
        h('section', { class: 'tw-charter-pick framed' },
          h('div', { class: 'kicker' }, 'Your Charter'),
          box, summary,
          h('div', { class: 'btnrow' }, go)))));
  }

  function beginRun(charter: string[]) {
    run = newRun(content, charter, Math.floor(Math.random() * 2 ** 31));
    marketMsg = ''; equipSel = null;
    save();
    showMarket();
  }

  // ---------------------------------------------------------------- tideline


  function showMarket() {
    teardown();
    if (!run) return showCharter();
    if (run.status !== 'active') return showOver();
    const r = run;
    const host_ = shell(root, content);
    const act = (res: { ok: boolean; msg: string }) => { marketMsg = res.msg; if (res.ok) save(); showMarket(); };

    const offers = h('div', { class: 'tw-offers' }, ...r.offers.map((o, i) => {
      const price = cardPrice(content, o.id), afford = r.salvage >= price && !o.sold;
      const own = o.kind === 'unit' && [...r.crew, ...r.hold].some(m => m.def === o.id);
      const el = h('div', { class: 'tw-offer' + (o.sold ? ' sold' : '') + (o.marked ? ' marked' : '') },
        h('div', { class: 'tw-offer-card' }, buildCard(o.id, { size: 'hand', content }),
          o.marked ? h('span', { class: 'tw-markflag', title: 'Marked: stays through a dredge' }, glyph('check')) : null,
          o.sold ? h('span', { class: 'tw-soldflag' }, 'Taken') : null),
        h('div', { class: 'tw-offer-ctl' },
          h('button', { class: 'tw-buy' + (afford ? '' : ' poor'), disabled: o.sold, title: own ? `Feeds ${uname(o.id)} ${TW.feedXp} XP` : afford ? 'Buy' : `Needs ${price} salvage`, onclick: () => act(buy(content, r, i)) },
            own ? 'Feed' : 'Buy', h('b', { class: 'num' }, String(price))),
          h('button', { class: 'iconbtn tw-mark' + (o.marked ? ' on' : ''), disabled: o.sold, title: o.marked ? 'Unmark' : 'Mark: keep through a dredge', 'aria-pressed': String(o.marked),
            onclick: () => act(toggleMark(r, i)) }, glyph('lock'))));
      return el;
    }));

    // enemy preview
    const enemy = enemyCrew(content, r);
    const arenaPrev = cropArena(content, r.seed, r.watch);
    const enemyBox = h('section', { class: 'tw-enemy framed' },
      h('div', { class: 'tw-enemy-h' }, crest(enemy.faction, 'crest', content.factions?.[enemy.faction]?.color),
        h('div', null, h('div', { class: 'kicker' }, isLampEater(r.watch) ? 'Lamp-eater watch' : `Watch ${r.watch} opposes`), h('h3', null, enemy.name)),
        h('div', { class: 'tw-arena-name', title: arenaPrev.description ?? '' }, h('small', null, 'Arena'), arenaPrev.name)),
      h('ul', { class: 'tw-enemy-list' }, ...enemy.members.map(m => h('li', { class: content.units[m.def].hero ? 'hero' : '' },
        h('span', { class: 'n' }, content.units[m.def].name), content.units[m.def].hero ? h('em', null, 'Hero') : null,
        m.rank ? h('span', { class: 'tw-pips', title: `Tempering rank ${m.rank}` }, ...Array.from({ length: m.rank }, () => h('i', { class: 'on' }))) : null))));

    // crew panels
    const rows = (list: typeof r.crew, kind: 'crew' | 'hold') => list.map(m => {
      const d = content.units[m.def];
      return h('li', { class: 'tw-row' + (equipSel !== null && kind === 'crew' ? ' pickable' : ''), style: `--pc:${fcolor(m.def)}` },
        portrait(m.def),
        h('div', { class: 'tw-row-main' },
          h('div', { class: 'tw-row-name' }, h('b', null, d.name), rankPips(m.def, m.xp)),
          h('div', { class: 'tw-row-sub' }, statline(m.def), m.equip ? h('button', { class: 'tw-eq', title: `Remove ${uname(m.equip)}`, onclick: () => act(unequip(r, m.id)) }, uname(m.equip), h('i', null, '×')) : null),
          xpBar(m.def, m.xp)),
        h('div', { class: 'tw-row-act' },
          equipSel !== null && kind === 'crew' && r.gear[equipSel] && canEquip(content, r.gear[equipSel].id, m.def)
            ? h('button', { class: 'btn-plain tiny', onclick: () => { const gi = equipSel!; equipSel = null; act(equip(content, r, gi, m.id)); } }, 'Fit') : null,
          h('button', { class: 'iconbtn sm', title: kind === 'crew' ? 'Send to the hold' : 'Send to the crew', onclick: () => act(kind === 'crew' ? toHold(r, m.id) : toCrew(r, m.id)) },
            h('span', { class: 'arr' + (kind === 'crew' ? ' down' : ' up') }, '›')),
          h('button', { class: 'iconbtn sm scrap', title: `Scrap for ${scrapValue(m.paid) + (m.equip ? scrapValue(m.equipPaid ?? 1) : 0)}`, onclick: () => { equipSel = null; act(scrap(r, { kind, id: m.id })); } }, glyph('close'))));
    });
    const empty = (n: number, what: string) => Array.from({ length: Math.max(0, n) }, () => h('li', { class: 'tw-row empty' }, h('span', null, what)));
    const berths = berthsAt(r.watch);

    const hymnRows = r.hymns.map((hy, i) => h('li', { class: 'tw-row slim' },
      h('span', { class: 'tw-glyph', style: `--pc:${fcolor(hy.id)}` }, glyph('magic')),
      h('div', { class: 'tw-row-main' }, h('div', { class: 'tw-row-name' }, h('b', null, uname(hy.id)), h('span', { class: 'tw-cost' }, `${cardCost(content, hy.id)} ${L('essence')}`))),
      h('div', { class: 'tw-row-act' }, h('button', { class: 'iconbtn sm scrap', title: `Scrap for ${scrapValue(hy.paid)}`, onclick: () => act(scrap(r, { kind: 'hymn', index: i })) }, glyph('close')))));
    const gearRows = r.gear.map((g, i) => h('li', { class: 'tw-row slim' + (equipSel === i ? ' sel' : '') },
      h('span', { class: 'tw-glyph', style: `--pc:${fcolor(g.id)}` }, glyph('buff')),
      h('div', { class: 'tw-row-main' }, h('div', { class: 'tw-row-name' }, h('b', null, uname(g.id)), h('small', null, content.equipment[g.id].description ?? ''))),
      h('div', { class: 'tw-row-act' },
        h('button', { class: 'btn-plain tiny', onclick: () => { equipSel = equipSel === i ? null : i; showMarket(); } }, equipSel === i ? 'Cancel' : 'Equip'),
        h('button', { class: 'iconbtn sm scrap', title: `Scrap for ${scrapValue(g.paid)}`, onclick: () => { equipSel = null; act(scrap(r, { kind: 'gear', index: i })); } }, glyph('close')))));

    const side = h('aside', { class: 'tw-crew framed' },
      h('div', { class: 'tw-sec' }, h('h3', null, 'Crew'), h('span', { class: 'num' }, `${r.crew.length} / ${berths}`)),
      h('ul', { class: 'tw-list' }, ...rows(r.crew, 'crew'), ...empty(berths - r.crew.length, 'Open berth')),
      h('div', { class: 'tw-sec' }, h('h3', null, 'Hold'), h('span', { class: 'num' }, `${r.hold.length} / ${TW.holdSlots}`), h('small', null, 'do not fight or earn XP')),
      h('ul', { class: 'tw-list' }, ...rows(r.hold, 'hold'), ...empty(TW.holdSlots - r.hold.length, 'Empty')),
      h('div', { class: 'tw-sec' }, h('h3', null, 'Hymns'), h('span', { class: 'num' }, `${r.hymns.length} / ${TW.maxHymns}`), h('small', null, 'cast once, from the first round')),
      h('ul', { class: 'tw-list' }, ...hymnRows, ...empty(TW.maxHymns - r.hymns.length, 'No hymn')),
      r.gear.length ? h('div', { class: 'tw-sec' }, h('h3', null, 'Gear'), h('span', { class: 'num' }, `${r.gear.length} / ${TW.maxGear}`)) : null,
      r.gear.length ? h('ul', { class: 'tw-list' }, ...gearRows) : null);

    const cap = tierCap(r.watch);
    const tierNote = cap === Infinity ? 'Everything is for sale.' : `Watch ${r.watch}: cards up to ${cap} ${L('essence')}.${r.watch < TW.heroFromWatch ? ' Heroes from watch 4.' : ''}`;
    const dredgeBtn = h('button', { class: 'btn-plain', disabled: r.salvage < TW.dredgeCost, title: 'Replace every card that is not marked', onclick: () => act(dredge(content, r)) }, 'Dredge', h('b', { class: 'num tw-btn-n' }, String(TW.dredgeCost)));
    const go = h('button', { class: 'btn-gold big', disabled: r.crew.length === 0, title: r.crew.length === 0 ? 'Hire at least one champion' : '', onclick: () => { save(); showFormation(); } }, 'To Formation');

    host_.append(h('div', { class: 'scr tw-scr tw-market' },
      header('The Tideline', `Watch ${r.watch} of ${TW.watches} · ${r.charter.map(f => factionName(content, f)).join(' + ')}`, () => { save(); leave(); }),
      resourceBar(r),
      h('div', { class: 'tw-body' },
        h('div', { class: 'tw-main' },
          h('section', { class: 'tw-shop framed' },
            h('div', { class: 'tw-shop-h' }, h('div', { class: 'kicker' }, 'Salvage on the Tideline'), h('small', null, tierNote)),
            offers,
            h('div', { class: 'tw-shop-f' }, dredgeBtn, h('p', { class: 'tw-msg', role: 'status' }, marketMsg || 'Buy a champion you already own to feed it XP. Mark a card to keep it through a dredge.'))),
          enemyBox,
          h('div', { class: 'tw-go' }, go)),
        side)));
  }

  // ---------------------------------------------------------------- formation

  function showFormation() {
    teardown();
    if (!run) return showCharter();
    const r = run;
    stopBackdrop(); installArt();
    clear(root); root.className = 'screen tw-form-root';
    const battle = buildBattleMission(content, r, { preview: true });
    const arena: MapDef = battle.arena;
    const layout = layoutCrew(content, r, arena);
    const game = new Game(content, battle.missionId, { seed: 1 });
    const unitOf = (id: number) => game.units.find(u => u.tag === `c${id}`);
    const zoneKeys = new Set(arena.deployZones['0'].map(([x, y]) => `${x},${y}`));
    let selected: number | null = null;
    const placed = new Map(layout); // crew id -> tile; picked-up champions are removed from here

    const canvas = h('canvas', { id: 'canvas', class: 'tw-canvas' });
    const stage = h('div', { class: 'tw-field framed' }, canvas, h('div', { class: 'tw-field-tip' }, 'Click a champion, then a lit tile. Click a placed champion to pick it up.'));
    const renderer = new Renderer(canvas);
    const list = h('ul', { class: 'tw-list' });
    const go = h('button', { class: 'btn-gold big', onclick: () => { commit(); startBattle(); } }, 'Begin the Watch');

    const sync = () => {
      for (const m of r.crew) {
        const u = unitOf(m.id); if (!u) continue;
        const t = placed.get(m.id);
        u.alive = !!t;
        if (t) { u.x = t.x; u.y = t.y; }
      }
      renderer.overlay.deploy = new Set([...zoneKeys].filter(k => ![...placed.values()].some(p => `${p.x},${p.y}` === k)));
      renderer.overlay.selected = null;
      const sel = selected !== null ? placed.get(selected) : undefined;
      if (sel) renderer.overlay.selected = { x: sel.x, y: sel.y };
      clear(list);
      for (const m of r.crew) {
        const d = content.units[m.def], on = placed.has(m.id);
        list.append(h('li', { class: 'tw-row pickrow' + (selected === m.id ? ' sel' : '') + (on ? ' placed' : ' loose'), style: `--pc:${fcolor(m.def)}` },
          h('button', { class: 'tw-row-btn', onclick: () => { selected = selected === m.id ? null : m.id; sync(); } },
            portrait(m.def),
            h('div', { class: 'tw-row-main' },
              h('div', { class: 'tw-row-name' }, h('b', null, d.name), rankPips(m.def, m.xp)),
              h('div', { class: 'tw-row-sub' }, statline(m.def), m.equip ? h('span', { class: 'tw-eq static' }, uname(m.equip)) : null)),
            h('span', { class: 'tw-place-state' }, on ? 'Placed' : 'Choose a tile'))));
      }
    };
    const commit = () => {
      // Anyone still unplaced is put somewhere sensible.
      const tmp = new Map(placed);
      r.crew.forEach(m => { if (!tmp.has(m.id)) delete m.pos; });
      rememberLayout(r, arena, tmp);
      save();
    };
    const clickTile = (p: Pos | null) => {
      if (!p) return;
      const k = `${p.x},${p.y}`;
      const here = [...placed.entries()].find(([, t]) => t.x === p.x && t.y === p.y)?.[0];
      if (selected === null) {
        if (here !== undefined) { selected = here; placed.delete(here); sync(); }
        return;
      }
      if (!zoneKeys.has(k)) return;
      if (here !== undefined && here !== selected) {
        const old = placed.get(selected);
        if (old) placed.set(here, old); else placed.delete(here);
      }
      placed.set(selected, { x: p.x, y: p.y });
      selected = null; sync();
    };
    // pointer: tap to pick, drag to pan
    let down: { x: number; y: number; t: number } | null = null;
    const local = (e: PointerEvent) => { const b = canvas.getBoundingClientRect(); return { x: e.clientX - b.left, y: e.clientY - b.top }; };
    canvas.addEventListener('pointerdown', e => { down = { ...local(e), t: performance.now() }; canvas.setPointerCapture(e.pointerId); });
    canvas.addEventListener('pointermove', e => {
      const p = local(e);
      if (down && Math.hypot(p.x - down.x, p.y - down.y) > 8 && down.t) { renderer.pan(p.x - down.x, p.y - down.y); down = { ...p, t: 0 }; return; }
      if (down && !down.t) { renderer.pan(p.x - down.x, p.y - down.y); down = { ...p, t: 0 }; return; }
      if (e.pointerType === 'mouse') renderer.overlay.hover = renderer.pick(p.x, p.y);
    });
    canvas.addEventListener('pointerup', e => { const d = down; down = null; if (d && d.t && performance.now() - d.t < 600) clickTile(renderer.pick(local(e).x, local(e).y)); });
    canvas.addEventListener('pointerleave', () => { renderer.overlay.hover = null; });
    canvas.addEventListener('wheel', e => { e.preventDefault(); const p = local(e as unknown as PointerEvent); renderer.zoomBy(e.deltaY < 0 ? 1.12 : 0.9, p.x, p.y); }, { passive: false });

    const enemy = enemyCrew(content, r);
    const autoBtn = h('button', { class: 'btn-plain', onclick: () => { placed.clear(); for (const [id, t] of layoutCrew(content, r, arena, true)) placed.set(id, t); selected = null; sync(); } }, 'Auto');
    const rows = h('aside', { class: 'tw-form-side framed' },
      h('div', { class: 'tw-sec' }, h('h3', null, 'Your crew'), h('span', { class: 'num' }, `${r.crew.length}`), autoBtn),
      list,
      h('div', { class: 'tw-sec' }, h('h3', null, 'Opposing crew'), h('small', null, 'positions unknown')),
      h('div', { class: 'tw-enemy-h compact' }, crest(enemy.faction, 'crest', content.factions?.[enemy.faction]?.color), h('b', null, enemy.name)),
      h('ul', { class: 'tw-enemy-list' }, ...enemy.members.map(m => h('li', { class: content.units[m.def].hero ? 'hero' : '' },
        h('span', { class: 'n' }, content.units[m.def].name), content.units[m.def].hero ? h('em', null, 'Hero') : null,
        m.rank ? h('span', { class: 'tw-pips' }, ...Array.from({ length: m.rank }, () => h('i', { class: 'on' }))) : null))));

    root.append(h('div', { class: 'scr tw-scr tw-form' },
      header(`Formation · ${arena.name}`, `Watch ${r.watch} of ${TW.watches}`, () => { commit(); showMarket(); }),
      h('div', { class: 'tw-form-body' }, stage, rows),
      h('div', { class: 'tw-go' },
        h('p', { class: 'tw-flood', title: 'Floodwater drowns anyone not at home in it' }, glyph('tide'), `The sea floods the arena from round ${TW.floodStart}. Hard stop after round ${TW.roundCap}.`),
        go)));
    renderer.setGame(game);
    sync();
    renderer.start();
    const ro = new ResizeObserver(() => renderer.resize());
    ro.observe(stage);
    formation = { renderer, ro };
    requestAnimationFrame(() => renderer.resize());
  }

  // ---------------------------------------------------------------- battle

  function startBattle() {
    if (!run) return;
    teardown();
    const r = run;
    const battle = buildBattleMission(content, r);
    preloadBattleBanks();
    enterBattle(battle.arena.id.split(':')[1], battle.seed);
    playBattleStart();
    session = new GameSession(root, {
      content, missionId: battle.missionId, seed: battle.seed, spectator: true, roundCap: TW.roundCap,
      onExit: () => { leave(); }, onRetry: () => undefined,
      onSkip: () => { teardown(); finish(resolveBattle(content, r)); },
      onBattleEnd: () => { const g = session!.game; finish(track.result ?? resultOf(g, battle)); },
    });
    const track = trackBattle(session.game, battle);
  }

  function finish(res: BattleResult) {
    if (!run) return;
    teardown();
    const summary = applyBattleResult(content, run, res);
    if (run.status !== 'active') recordBest(run);
    save();
    showResult(summary);
  }

  // ---------------------------------------------------------------- result

  function showResult(s: WatchSummary) {
    teardown();
    if (!run) return;
    const r = run;
    const host_ = shell(root, content);
    const win = s.outcome === 'win', draw = s.outcome === 'draw';
    const title = win ? 'Watch Held' : draw ? 'Stalemate' : 'Watch Lost';
    const why = s.capped ? `Both crews still stood after round ${TW.roundCap}; the stronger crew took it.` : win ? `The shelf is yours after ${s.rounds} round${s.rounds === 1 ? '' : 's'}.` : draw ? 'Both crews fell together.' : `Your crew was broken in round ${s.rounds}.`;
    const last = r.status !== 'active';
    const rows = s.xp.map(x => {
      const m = [...r.crew, ...r.hold].find(c => c.id === x.id);
      const d = content.units[x.def];
      return h('li', { class: 'tw-row res' + (x.alive ? '' : ' fell'), style: `--pc:${fcolor(x.def)}` },
        portrait(x.def),
        h('div', { class: 'tw-row-main' },
          h('div', { class: 'tw-row-name' }, h('b', null, d.name), rankPips(x.def, m?.xp ?? 0), x.rankAfter > x.rankBefore ? h('em', { class: 'tw-rankup' }, `Tempered: ${rankLabel(x.def, x.rankAfter)}`) : null),
          xpBar(x.def, m?.xp ?? 0)),
        h('div', { class: 'tw-row-act' }, h('span', { class: 'tw-xpgain num' }, `+${x.gain} XP`), h('small', null, x.alive ? 'Stood' : 'Fell')));
    });
    const card = h('div', { class: `tw-result framed ${win ? 'win' : draw ? 'draw' : 'lose'}` },
      h('div', { class: 'kicker' }, `Watch ${s.watch} of ${TW.watches} · vs ${s.enemyName}`),
      h('h2', null, title),
      ornament(),
      h('p', { class: 'lead' }, why),
      h('div', { class: 'tw-sumrow' },
        resource('Light', lamps(r.light), s.lightLost ? `−${s.lightLost} this watch` : 'unchanged'),
        resource(L('essence'), `+${s.tideGained}`, 'gained on the shelf'),
        resource('Next income', last ? '—' : `+${s.income}`, last ? '' : `${TW.baseIncome} pay + ${s.income - TW.baseIncome} salvage`)),
      h('ul', { class: 'tw-list res' }, ...rows),
      h('div', { class: 'btnrow' },
        h('button', { class: 'btn-gold big', onclick: () => (last ? showOver() : showMarket()) }, last ? (r.status === 'victory' ? 'See the Dawn' : 'Close the Lamp') : 'Return to the Tideline')));
    host_.append(h('div', { class: 'scr tw-scr tw-result-scr' }, card));
  }

  // ---------------------------------------------------------------- run over

  function showOver() {
    teardown();
    if (!run) return showCharter();
    const r = run;
    const won = r.status === 'victory';
    const best = loadBest();
    const host_ = shell(root, content);
    saveRun(null);
    const cr = svgSpan(crestSvg(r.charter[0], content.factions?.[r.charter[0]]?.color), 'end-crest');
    host_.append(h('div', { class: 'scr tw-scr tw-over' },
      h('div', { class: `tw-result framed ${won ? 'win' : 'lose'}` },
        cr,
        h('div', { class: 'kicker' }, r.charter.map(f => factionName(content, f)).join(' + ')),
        h('h2', null, won ? 'The Long Ebb Holds' : 'The Lamp Goes Out'),
        ornament(),
        h('p', { class: 'lead' }, won ? 'Ten watches held. The lamp burns one more night.' : `The lamp dimmed to nothing on watch ${r.watch}.`),
        h('div', { class: 'tw-sumrow' },
          resource('Watches held', String(r.held), `of ${TW.watches}`),
          resource('Reached', `${won ? TW.watches : r.watch}`, 'watch'),
          resource('Best', best ? (best.won ? 'Victory' : `Watch ${best.watch}`) : '—')),
        h('div', { class: 'btnrow' },
          h('button', { class: 'btn-gold big', onclick: () => { run = null; charterPick.length = 0; showCharter(); } }, 'New Run'),
          h('button', { class: 'btn-plain', onclick: leave }, 'Main Menu')))));
  }

  // ---------------------------------------------------------------- entry points

  function resume(): boolean {
    const r = loadRun();
    if (!r) return false;
    run = r; marketMsg = ''; equipSel = null;
    showMarket();
    return true;
  }

  /** Seeded demo run for screenshots and playtests: a few watches in, with a hymn, gear and some veterans. */
  function demoRun(): Run {
    const r = newRun(content, ['salt_concord', 'lanternkeepers'], 4242);
    let guard = 0;
    while (r.watch < 4 && r.status === 'active' && guard++ < 8) {
      r.salvage += 6;
      greedyShop(content, r);
      applyBattleResult(content, r, resolveBattle(content, r));
    }
    if (r.status !== 'active') { r.status = 'active'; r.light = 3; if (r.watch > 4) r.watch = 4; }
    r.salvage = Math.max(r.salvage, 9);
    return r;
  }

  function demo(stage: DemoStage) {
    teardown();
    run = demoRun();
    marketMsg = '';
    switch (stage) {
      case 'charter': charterPick.splice(0, charterPick.length, 'salt_concord', 'lanternkeepers'); showCharter(); break;
      case 'market': showMarket(); break;
      case 'formation': showFormation(); break;
      case 'battle': startBattle(); break;
      case 'result': showResult(applyBattleResult(content, run, resolveBattle(content, run))); break;
    }
  }

  return {
    start: () => { charterPick.length = 0; showCharter(); },
    resume,
    abandon: () => { saveRun(null); run = null; },
    demo,
    state: () => run,
    session: () => session,
    destroy: teardown,
  };
}

export type Tidewatch = ReturnType<typeof createTidewatch>;

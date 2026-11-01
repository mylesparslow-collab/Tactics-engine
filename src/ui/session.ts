import { Game } from '../engine/game';
import { aiStep } from '../engine/ai';
import { label } from '../engine/content';
import { loadProgress, recordVictory } from '../engine/campaign';
import type { Content, Effect, GameEvent, Pos, Unit } from '../engine/types';
import { Renderer } from '../render/renderer';
import { key } from '../render/iso';
import { statusColor } from '../render/sprites';
import { clear, h } from './dom';
import { effectText } from './text';

export interface SessionOpts {
  content: Content;
  missionId: string;
  roster?: string[];
  campaign?: { id: string; index: number };
  onExit: () => void;
  onRetry: () => void;
  onNext?: () => void;
}

type Mode = { kind: 'idle' } | { kind: 'move' } | { kind: 'ability'; ability: string } | { kind: 'card'; index: number };

export class GameSession {
  readonly game: Game;
  private renderer: Renderer;
  private content: Content;
  private root: HTMLElement;
  private top!: HTMLElement; private left!: HTMLElement; private right!: HTMLElement; private hoverBox!: HTMLElement;
  private logBox!: HTMLElement; private banner!: HTMLElement; private toast!: HTMLElement; private canvas!: HTMLCanvasElement;
  private selected: number | null = null;
  private mode: Mode = { kind: 'idle' };
  private hover: Pos | null = null;
  private aiRunning = false;
  private aiTimer = 0;
  private destroyed = false;
  private ended = false;
  private bannerQueue: { text: string; speaker?: string }[] = [];
  private bannerBusy = false;
  private cleanup: (() => void)[] = [];

  constructor(container: HTMLElement, private opts: SessionOpts) {
    this.content = opts.content;
    this.game = new Game(opts.content, opts.missionId, { roster: opts.roster });
    this.root = container;
    this.build();
    this.renderer = new Renderer(this.canvas);
    this.renderer.setGame(this.game);
    this.renderer.start();
    this.game.on(e => this.onEvent(e));
    const ro = new ResizeObserver(() => this.renderer.resize());
    ro.observe(this.canvas.parentElement!);
    this.cleanup.push(() => ro.disconnect());
    const kd = (e: KeyboardEvent) => this.onKey(e);
    window.addEventListener('keydown', kd);
    this.cleanup.push(() => window.removeEventListener('keydown', kd));
    this.logLine(`${this.game.mission.name} begins.`, 'sys');
    this.logLine(`Round 1 - ${this.game.teams[this.game.current].name}`, 'turn');
    this.refresh();
    this.toastMsg(`Round 1 - ${this.game.teams[this.game.current].name}`);
    // Debug/test hook: lets automated tests and the console drive the current session.
    (window as unknown as { __tactics?: GameSession }).__tactics = this;
    this.scheduleAi();
  }

  destroy() {
    this.destroyed = true;
    clearTimeout(this.aiTimer);
    this.renderer.stop();
    this.cleanup.forEach(f => f());
    clear(this.root);
  }

  // ---------- helpers ----------
  private L(term: string) { return label(this.content, term); }
  private get g() { return this.game; }
  private humanTeam() {
    const g = this.g;
    return g.teams[g.current].controller === 'human' ? g.current : Math.max(0, g.teams.findIndex(t => t.controller === 'human'));
  }
  private canAct() {
    const g = this.g;
    return !this.ended && !this.destroyed && !this.aiRunning && !this.renderer.busy() && g.phase === 'playing' && g.teams[g.current].controller === 'human';
  }
  private sel(): Unit | undefined { return this.selected === null ? undefined : this.g.unit(this.selected); }
  private uname(uid: number) { const u = this.g.unit(uid); return u ? this.g.def(u).name : '?'; }

  // ---------- DOM ----------
  private build() {
    clear(this.root); this.root.className = 'game';
    this.top = h('div', { id: 'topbar' });
    this.left = h('aside', { id: 'left', class: 'panel' });
    this.right = h('aside', { id: 'right', class: 'panel' });
    this.hoverBox = h('div', { class: 'hoverbox' });
    this.canvas = h('canvas', { id: 'canvas' });
    this.banner = h('div', { id: 'banner', class: 'hidden' });
    this.toast = h('div', { id: 'toast', class: 'hidden' });
    this.logBox = h('div', { id: 'log' });
    const rot = h('div', { id: 'rotbtns' },
      h('button', { title: 'Rotate view (Q)', onclick: () => this.renderer.rotate(-1) }, '⟲'),
      h('button', { title: 'Rotate view (R)', onclick: () => this.renderer.rotate(1) }, '⟳'));
    const stage = h('main', { id: 'stage' }, this.canvas, this.banner, this.toast, rot);
    this.root.append(this.top, this.left, stage, this.right, this.logBox);
    this.canvas.addEventListener('mousemove', e => {
      const r = this.canvas.getBoundingClientRect();
      const p = this.renderer.pick(e.clientX - r.left, e.clientY - r.top);
      if (p?.x !== this.hover?.x || p?.y !== this.hover?.y) { this.hover = p; this.updateOverlay(); this.renderHover(); }
    });
    this.canvas.addEventListener('mouseleave', () => { this.hover = null; this.updateOverlay(); this.renderHover(); });
    this.canvas.addEventListener('click', e => {
      const r = this.canvas.getBoundingClientRect();
      this.click(this.renderer.pick(e.clientX - r.left, e.clientY - r.top));
    });
    this.canvas.addEventListener('contextmenu', e => { e.preventDefault(); this.cancel(); });
  }

  // ---------- events ----------
  private onEvent(e: GameEvent) {
    this.renderer.handleEvent(e);
    const g = this.g;
    switch (e.kind) {
      case 'move': this.logLine(`${this.uname(e.uid)} moves ${e.path.length - 1} tile${e.path.length === 2 ? '' : 's'}.`, 'move'); break;
      case 'ability': this.logLine(`${this.uname(e.uid)} uses ${g.ability(e.ability)?.name ?? e.ability}.`, 'ability'); break;
      case 'damage': this.logLine(`${this.uname(e.uid)} takes ${e.amount} ${e.damageType ?? ''} damage.`.replace('  ', ' '), 'dmg'); break;
      case 'heal': this.logLine(`${this.uname(e.uid)} recovers ${e.amount} HP.`, 'heal'); break;
      case 'status': this.logLine(`${this.uname(e.uid)} is ${g.content.statuses[e.status]?.name ?? e.status}.`, 'status'); break;
      case 'push': this.logLine(`${this.uname(e.uid)} is moved.`, 'move'); break;
      case 'death': this.logLine(`${this.uname(e.uid)} is defeated.`, 'death'); break;
      case 'revive': this.logLine(`${this.uname(e.uid)} rises again with ${e.hp} HP.`, 'heal'); break;
      case 'spell': this.logLine(`${g.teams[e.team].name} casts ${g.content.spells[e.spell]?.name ?? e.spell}.`, 'ability'); break;
      case 'equip': this.logLine(`${this.uname(e.uid)} is equipped with ${g.content.equipment[e.equipment]?.name ?? e.equipment}.`, 'status'); break;
      case 'deploy': this.logLine(`${this.uname(e.uid)} enters the field.`, 'move'); break;
      case 'essence': this.logLine(`${g.teams[e.team].name} ${e.amount >= 0 ? 'gains' : 'loses'} ${Math.abs(e.amount)} ${this.L('essence')}.`, 'sys'); break;
      case 'terrain': this.logLine(`The ground at ${e.x},${e.y} becomes ${g.content.terrain[e.terrain]?.name ?? e.terrain}.`, 'sys'); break;
      case 'turn': this.logLine(`Round ${e.turn} - ${g.teams[e.team].name}`, 'turn'); this.toastMsg(`Round ${e.turn} - ${g.teams[e.team].name}`, g.teams[e.team].color); break;
      case 'message': this.logLine(`${e.speaker ? e.speaker + ': ' : ''}${e.text}`, 'msg'); this.bannerQueue.push({ text: e.text, speaker: e.speaker }); this.pumpBanner(); break;
      case 'end': this.ended = true; this.logLine(e.phase === 'victory' ? 'Victory!' : 'Defeat.', 'turn'); this.waitForEnd(e.phase); break;
    }
  }

  private logLine(text: string, cls: string) {
    this.logBox.append(h('div', { class: 'logline ' + cls }, text));
    while (this.logBox.childElementCount > 200) this.logBox.firstElementChild!.remove();
    this.logBox.scrollTop = this.logBox.scrollHeight;
  }

  private toastMsg(text: string, color?: string) {
    this.toast.textContent = text; this.toast.style.borderColor = color ?? ''; this.toast.classList.remove('hidden');
    this.toast.classList.remove('show'); void this.toast.offsetWidth; this.toast.classList.add('show');
  }

  private pumpBanner() {
    if (this.bannerBusy) return;
    const m = this.bannerQueue.shift();
    if (!m) { this.banner.classList.add('hidden'); return; }
    this.bannerBusy = true;
    clear(this.banner);
    if (m.speaker) this.banner.append(h('div', { class: 'speaker' }, m.speaker));
    this.banner.append(h('div', { class: 'speech' }, m.text));
    this.banner.classList.remove('hidden');
    setTimeout(() => { this.bannerBusy = false; if (this.destroyed) return; this.pumpBanner(); }, 4500);
  }

  // ---------- end of game ----------
  private waitForEnd(phase: 'playing' | 'victory' | 'defeat') {
    const poll = () => {
      if (this.destroyed) return;
      if (this.renderer.busy()) { setTimeout(poll, 150); return; }
      setTimeout(() => !this.destroyed && this.showEnd(phase), 500);
    };
    poll();
  }

  private showEnd(phase: string) {
    const m = this.g.mission, win = phase === 'victory';
    let unlockedNames: string[] = [];
    const c = this.opts.campaign;
    if (win && c) {
      const before = loadProgress(c.id).completed;
      const unlocked = recordVictory(this.content, c.id, c.index);
      if (before === c.index) unlockedNames = unlocked.map(u => this.content.units[u]?.name ?? u);
    }
    const text = win ? (m.victoryText ?? 'The field is yours.') : (m.defeatText ?? 'Your force has been broken.');
    const modal = h('div', { class: 'modal-back' },
      h('div', { class: 'modal ' + (win ? 'win' : 'lose') },
        h('h2', null, win ? 'Victory' : 'Defeat'),
        h('div', { class: 'mname' }, m.name),
        h('p', null, text),
        unlockedNames.length ? h('div', { class: 'unlocks' }, h('b', null, 'Unlocked: '), unlockedNames.join(', ')) : null,
        h('div', { class: 'btnrow' },
          win && this.opts.onNext ? h('button', { class: 'primary', onclick: () => this.opts.onNext!() }, 'Next mission') : null,
          h('button', { class: win && this.opts.onNext ? '' : 'primary', onclick: () => this.opts.onRetry() }, 'Retry'),
          h('button', { onclick: () => this.opts.onExit() }, 'Back to menu'))));
    this.root.append(modal);
  }

  // ---------- AI ----------
  private scheduleAi() {
    const g = this.g;
    if (this.aiRunning || this.destroyed || g.phase !== 'playing' || g.teams[g.current].controller !== 'ai') return;
    this.aiRunning = true;
    this.refresh();
    let steps = 0;
    const tick = () => {
      if (this.destroyed) return;
      if (g.phase !== 'playing') { this.aiRunning = false; this.refresh(); return; }
      if (this.renderer.busy()) { this.aiTimer = window.setTimeout(tick, 80); return; }
      let more = false;
      try { more = steps++ < 80 && aiStep(g); } catch (err) { console.error('AI error', err); }
      if (!more && g.phase === 'playing') g.endTurn();
      this.refresh();
      if (g.phase === 'playing' && g.teams[g.current].controller === 'ai') { steps = more ? steps : 0; this.aiTimer = window.setTimeout(tick, 350); }
      else { this.aiRunning = false; this.refresh(); }
    };
    this.aiTimer = window.setTimeout(tick, 600);
  }

  // ---------- input ----------
  private endTurn() {
    if (this.canActSoft() && this.renderer.busy()) { setTimeout(() => this.endTurn(), 120); return; }
    if (!this.canAct()) return;
    this.selected = null; this.mode = { kind: 'idle' };
    this.g.endTurn();
    this.refresh();
    this.scheduleAi();
  }

  private cancel() {
    if (this.mode.kind === 'ability') this.mode = { kind: 'move' };
    else if (this.mode.kind === 'card') this.mode = { kind: 'idle' };
    else { this.selected = null; this.mode = { kind: 'idle' }; }
    this.refresh();
  }

  private onKey(e: KeyboardEvent) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const k = e.key.toLowerCase();
    if (k === 'escape') this.cancel();
    else if (k === 'enter' || k === 'e') { e.preventDefault(); this.endTurn(); }
    else if (k === 'q') this.renderer.rotate(-1);
    else if (k === 'r') this.renderer.rotate(1);
    else if (/^[1-9]$/.test(k)) {
      const btn = this.right.querySelectorAll<HTMLButtonElement>('button.ability:not(:disabled)')[Number(k) - 1];
      btn?.click();
    }
  }

  private setSelected(u: Unit | null) {
    this.selected = u ? u.uid : null;
    this.mode = u && u.team === this.g.current ? { kind: 'move' } : { kind: 'idle' };
  }

  private click(p: Pos | null) {
    if (!this.canAct()) return;
    const g = this.g;
    const occ = p ? g.unitAt(p.x, p.y) : undefined;
    const u = this.sel();
    const mine = u && u.team === g.current;
    if (p && this.mode.kind === 'card') {
      const m = this.mode;
      if (g.cardTargets(g.current, m.index).some(t => t.x === p.x && t.y === p.y)) g.playCard(g.current, m.index, p.x, p.y);
      this.mode = { kind: 'idle' };
      this.refresh(); return;
    }
    if (p && u && mine && this.mode.kind === 'ability') {
      const ab = this.mode.ability;
      if (g.validTargets(u, ab).some(t => t.x === p.x && t.y === p.y)) {
        g.useAbility(u.uid, ab, p.x, p.y);
        this.mode = { kind: 'move' }; this.refresh(); return;
      }
      if (!(occ && occ.team === g.current)) { this.mode = { kind: 'move' }; this.refresh(); return; }
    }
    if (occ) {
      if (occ.team === g.current || !mine || !g.reachable(u!).has(key(p!.x, p!.y))) { this.setSelected(occ); this.refresh(); return; }
    }
    if (p && u && mine && !occ) {
      const reach = g.reachable(u);
      if (reach.has(key(p.x, p.y)) && !(u.x === p.x && u.y === p.y)) { g.move(u.uid, p.x, p.y); this.refresh(); return; }
    }
    this.selected = null; this.mode = { kind: 'idle' }; this.refresh();
  }

  // ---------- state -> UI ----------
  private refresh() {
    const u = this.sel();
    if (u && !u.alive) { this.selected = null; this.mode = { kind: 'idle' }; }
    if (this.mode.kind === 'ability') {
      const s = this.sel();
      if (!s || !this.g.canUse(s, this.mode.ability)) this.mode = s ? { kind: 'move' } : { kind: 'idle' };
    }
    if (this.mode.kind === 'card' && !this.g.cardTargets(this.g.current, this.mode.index).length) this.mode = { kind: 'idle' };
    this.updateOverlay();
    this.renderTop(); this.renderLeft(); this.renderRight(); this.renderHover();
  }

  private previewOf(units: Unit[], effects: Effect[], dmgFn: (o: Unit, e: Extract<Effect, { type: 'damage' }>) => number) {
    const g = this.g, out = new Map<number, { text: string; color: string }>();
    for (const o of units) {
      let dmg = 0, heal = 0;
      for (const e of effects) {
        if (e.type === 'damage') dmg += dmgFn(o, e);
        else if (e.type === 'heal') heal += Math.min(e.amount, g.def(o).stats.hp - o.hp);
      }
      const parts: string[] = [];
      if (dmg > 0) parts.push(`-${dmg}${dmg >= o.hp ? ' KO' : ''}`);
      if (heal > 0) parts.push(`+${heal}`);
      if (parts.length) out.set(o.uid, { text: parts.join(' '), color: dmg > 0 ? (dmg >= o.hp ? '#ff7766' : '#ffb347') : '#6fe08a' });
    }
    return out;
  }

  private computePreview(u: Unit, ab: string, target: Pos) {
    const g = this.g;
    return this.previewOf(g.affected(u, ab, target), g.ability(ab).effects, (o, e) => g.previewDamage(u, o, e));
  }

  private updateOverlay() {
    const g = this.g, ov = this.renderer.overlay;
    ov.reach.clear(); ov.targets.clear(); ov.area.clear(); ov.deploy.clear(); ov.path = []; ov.pathCost = null; ov.previews = new Map();
    ov.hover = this.hover;
    const u = this.sel();
    ov.selected = u ? { x: u.x, y: u.y } : null;
    if (!this.canActSoft()) return;
    const hv = this.hover;
    if (this.mode.kind === 'card') {
      const id = g.teams[g.current].hand[this.mode.index];
      const targets = g.cardTargets(g.current, this.mode.index);
      for (const t of targets) ov.deploy.add(key(t.x, t.y));
      const sp = g.content.spells[id];
      if (sp && hv && targets.some(t => t.x === hv.x && t.y === hv.y)) {
        const size = sp.area?.size ?? 0;
        for (let y = hv.y - size; y <= hv.y + size; y++) for (let x = hv.x - size; x <= hv.x + size; x++)
          if (g.inBounds(x, y) && Math.abs(x - hv.x) + Math.abs(y - hv.y) <= size) ov.area.add(key(x, y));
        ov.previews = this.previewOf(g.spellAffected(g.current, sp, hv), sp.effects, (o, e) => g.previewSpellDamage(o, e));
      }
      return;
    }
    if (!u || u.team !== g.current) return;
    if (this.mode.kind === 'move') {
      const reach = g.reachable(u);
      for (const k of reach.keys()) if (k !== key(u.x, u.y)) ov.reach.add(k);
      if (hv && reach.has(key(hv.x, hv.y)) && !(hv.x === u.x && hv.y === u.y)) {
        ov.path = g.pathTo(u, hv.x, hv.y); ov.pathCost = reach.get(key(hv.x, hv.y))!.cost;
      }
    } else if (this.mode.kind === 'ability') {
      const ab = this.mode.ability, a = g.ability(ab);
      const targets = g.validTargets(u, ab);
      for (const t of targets) ov.targets.add(key(t.x, t.y));
      if (hv && targets.some(t => t.x === hv.x && t.y === hv.y)) {
        const size = a.area?.size ?? 0;
        for (let y = hv.y - size; y <= hv.y + size; y++) for (let x = hv.x - size; x <= hv.x + size; x++)
          if (g.inBounds(x, y) && Math.abs(x - hv.x) + Math.abs(y - hv.y) <= size) ov.area.add(key(x, y));
        ov.previews = this.computePreview(u, ab, hv);
      }
    }
  }
  /** Highlights are shown while the player could act soon (also during animations, but not during AI turns). */
  private canActSoft() { const g = this.g; return !this.ended && !this.aiRunning && g.phase === 'playing' && g.teams[g.current].controller === 'human'; }

  private renderTop() {
    const g = this.g;
    clear(this.top);
    const cur = g.teams[g.current];
    this.top.append(
      h('div', { class: 'brand' }, g.mission.name),
      h('div', { class: 'tb round' }, `Round ${g.round}`),
      h('div', { class: 'tb turn', style: `color:${cur.color}` }, `${cur.name}${this.aiRunning ? ' (thinking...)' : "'s turn"}`),
      h('div', { class: 'spacer' }),
      ...g.teams.map((t, i) => h('div', { class: 'tb essence' + (i === g.current ? ' active' : ''), style: `border-color:${t.color}` },
        h('span', { class: 'dot', style: `background:${t.color}` }), `${t.name}: `, h('b', null, String(t.essence)), ` ${this.L('essence')}`)),
      h('button', { id: 'endturn', class: 'primary', disabled: !this.canActSoft(), title: 'End turn (E / Enter)', onclick: () => this.endTurn() }, 'End Turn'),
      h('button', { class: 'quiet', onclick: () => { if (this.ended || confirm('Abandon this battle and return to the menu?')) this.opts.onExit(); } }, 'Menu'));
  }

  private renderLeft() {
    const g = this.g, t = this.humanTeam(), team = g.teams[t];
    clear(this.left);
    this.left.append(h('h3', null, this.L('warband')), h('div', { class: 'sub' }, `${this.L('essence')}: ${team.essence}`));
    const list = h('div', { class: 'hand' });
    team.hand.forEach((id, i) => {
      const kind = g.cardKind(id) ?? 'unit';
      const ud = this.content.units[id];
      const desc = (ud ?? this.content.spells[id] ?? this.content.equipment[id])?.description ?? '';
      const cost = g.cardCost(id);
      const ok = this.canActSoft() && t === g.current && g.cardTargets(t, i).length > 0;
      const active = this.mode.kind === 'card' && this.mode.index === i;
      const glyph = ud ? h('span', { class: 'glyph', style: `background:${ud.sprite.color ?? team.color}` }, ud.sprite.glyph)
        : h('span', { class: 'glyph ' + kind }, kind === 'spell' ? '\u2736' : '\u2692');
      list.append(h('button', {
        class: 'card ' + kind + (active ? ' active' : ''), disabled: !ok,
        title: `${g.cardName(id)} (${kind}, ${cost} ${this.L('essence')})${desc ? '\n' + desc : ''}${ok ? '' : (cost > team.essence ? `\nNot enough ${this.L('essence')}` : '\nCannot be played now')}`,
        onclick: () => { if (!this.canAct()) return; this.mode = active ? { kind: 'idle' } : { kind: 'card', index: i }; this.selected = null; this.refresh(); },
      }, glyph,
        h('span', { class: 'cn' }, h('span', null, ud?.hero ? '\u2655 ' : '', g.cardName(id)), h('small', null, kind === 'unit' ? (ud?.role ?? 'Unit') : kind === 'spell' ? 'Spell' : 'Equipment')),
        h('span', { class: 'cost' }, String(cost))));
    });
    if (!team.hand.length) list.append(h('div', { class: 'muted' }, 'No cards in reserve.'));
    const hintFor = () => {
      if (this.mode.kind !== 'card') return 'Click a card, then a highlighted target.';
      const k = g.cardKind(team.hand[this.mode.index] ?? '');
      return k === 'spell' ? 'Click a target tile to cast. Esc cancels.' : k === 'equipment' ? 'Click a friendly unit to equip. Esc cancels.' : 'Click a green tile to deploy. Esc cancels.';
    };
    this.left.append(list, h('div', { class: 'hint' }, hintFor()));
    this.left.append(h('div', { class: 'help' },
      h('b', null, 'Controls'), h('div', null, 'Click a unit to select, blue tile to move.'),
      h('div', null, '1-9: ability  Esc: cancel'), h('div', null, 'E / Enter: end turn'), h('div', null, 'Q / R: rotate view')));
  }

  private unitCard(u: Unit, full: boolean) {
    const g = this.g, d = g.def(u), team = g.teams[u.team];
    const stat = (k: 'attack' | 'defense' | 'jump') => {
      const v = g.stat(u, k), b = d.stats[k];
      return h('span', { class: 'stat' + (v > b ? ' up' : v < b ? ' down' : '') }, `${v}`);
    };
    const maxAp = g.stat(u, 'ap');
    const box = h('div', { class: 'ucard' },
      h('div', { class: 'uname', style: `border-color:${team.color}` },
        h('span', { class: 'glyph', style: `background:${d.sprite.color ?? team.color}` }, d.sprite.glyph),
        h('div', null, h('b', null, d.hero ? '\u2655 ' : '', d.name), h('div', { class: 'role' }, `${d.role ?? ''}${d.role ? ' - ' : ''}${team.name}`))),
      h('div', { class: 'bar' }, h('div', { class: 'fill hp', style: `width:${Math.max(0, u.hp / d.stats.hp * 100)}%` }), h('span', null, `HP ${u.hp}/${d.stats.hp}`)),
      d.structure ? null : h('div', { class: 'bar' }, h('div', { class: 'fill ap', style: `width:${maxAp ? Math.min(100, u.ap / maxAp * 100) : 0}%` }), h('span', null, `AP ${u.ap}/${maxAp}`)),
      h('div', { class: 'stats' }, h('span', null, 'ATK ', stat('attack')), h('span', null, 'DEF ', stat('defense')), h('span', null, 'JUMP ', stat('jump'))),
      d.resist && Object.keys(d.resist).length ? h('div', { class: 'resist' }, 'Resist: ' + Object.entries(d.resist).map(([k, v]) => `${k} ${v > 0 ? '+' : ''}${v}`).join(', ')) : null,
      g.equipmentOf(u) ? h('div', { class: 'resist', title: g.equipmentOf(u)!.description ?? '' }, 'Equipped: ' + g.equipmentOf(u)!.name + (g.equipmentOf(u)!.description ? ' - ' + g.equipmentOf(u)!.description : '')) : null,
      d.revive ? h('div', { class: 'resist' }, u.revived ? 'Has risen once already.' : `Rises once on death (${Math.round(d.revive.hpFraction * 100)}% HP).`) : null);
    if (u.statuses.length) {
      box.append(h('div', { class: 'statuses' }, ...u.statuses.map(s => {
        const sd = g.content.statuses[s.id];
        return h('div', { class: 'status' }, h('span', { class: 'sdot', style: `background:${statusColor(s.id)}` }), h('b', null, `${sd?.name ?? s.id} `), `(${s.remaining}) `, h('span', { class: 'muted' }, sd?.description ?? ''));
      })));
    }
    if (full && d.description) box.append(h('div', { class: 'desc' }, d.description));
    return box;
  }

  private renderRight() {
    const g = this.g;
    clear(this.right);
    const u = this.sel();
    this.right.append(h('h3', null, u ? 'Selected' : 'No selection'));
    if (!u) {
      this.right.append(h('div', { class: 'muted' }, 'Click one of your units to select it.'));
    } else {
      this.right.append(this.unitCard(u, true));
      const abs = g.abilitiesOf(u);
      if (abs.length) {
        const list = h('div', { class: 'abilities' });
        abs.forEach(id => {
          const a = g.ability(id);
          if (!a) return;
          const tip = [a.description ?? '', `Range ${a.range.min === a.range.max ? a.range.max : a.range.min + '-' + a.range.max}${a.area ? `, area ${a.area.size}` : ''}`,
            ...a.effects.map(e => effectText(this.content, e)), a.cooldown ? `Cooldown ${a.cooldown} turns` : ''].filter(Boolean).join('\n');
          if (a.passive) {
            list.append(h('div', { class: 'ability passive', title: tip }, h('span', { class: 'an' }, a.name), h('span', { class: 'meta' }, 'Passive'), h('div', { class: 'adesc' }, a.description ?? '')));
            return;
          }
          const cd = u.cooldowns[id] ?? 0;
          const usable = u.team === g.current && this.canActSoft() && g.canUse(u, id);
          const active = this.mode.kind === 'ability' && this.mode.ability === id;
          const idx = list.querySelectorAll('button.ability').length + 1;
          list.append(h('button', {
            class: 'ability' + (active ? ' active' : ''), disabled: !usable, title: tip,
            onclick: () => { if (!this.canAct()) return; this.mode = active ? { kind: 'move' } : { kind: 'ability', ability: id }; this.refresh(); },
          }, h('span', { class: 'an' }, `${idx}. ${a.name}`),
            h('span', { class: 'meta' }, `${a.apCost} AP${cd > 0 ? ` - cd ${cd}` : a.cooldown ? ` - cd ${a.cooldown}` : ''}`)));
        });
        this.right.append(h('h3', null, 'Abilities'), list);
      }
    }
    this.right.append(this.hoverBox);
  }

  private renderHover() {
    const g = this.g;
    clear(this.hoverBox);
    const hv = this.hover;
    if (!hv || !g.inBounds(hv.x, hv.y)) return;
    const occ = g.unitAt(hv.x, hv.y);
    this.hoverBox.append(h('h3', null, 'Hover'));
    const t = g.tiles[hv.y][hv.x], terr = g.content.terrain[t.terrain];
    if (occ && occ.uid !== this.selected) this.hoverBox.append(this.unitCard(occ, false));
    const pv = this.renderer.overlay.previews;
    if (pv.size) {
      const box = h('div', { class: 'preview' }, h('b', null, 'Predicted'));
      for (const [uid, p] of pv) box.append(h('div', { style: `color:${p.color}` }, `${this.uname(uid)}: ${p.text}`));
      this.hoverBox.append(box);
    }
    this.hoverBox.append(h('div', { class: 'tileinfo' },
      `${terr?.name ?? t.terrain} - height ${t.height} - move ${terr?.moveCost} - def +${terr?.defense ?? 0}`,
      g.map.wells?.some(w => w.x === hv.x && w.y === hv.y) ? ` - ${this.L('essence')} well` : ''));
  }
}

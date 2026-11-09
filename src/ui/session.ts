import { Game, DEFAULTS } from '../engine/game';
import { aiStep } from '../engine/ai';
import { label } from '../engine/content';
import { loadProgress, recordVictory } from '../engine/campaign';
import type { Content, Effect, GameEvent, Pos, Unit } from '../engine/types';
import { Renderer } from '../render/renderer';
import { key } from '../render/iso';
import { statusColor } from '../render/sprites';
import { clear, h } from './dom';
import { artNode, buildCard } from './cards';
import { abilityGlyph, crestSvg, glyph, installArt, teamFaction } from './art';
import { stopBackdrop } from './menu';
import { isMuted, playCard, playCardPlay, playCue, playEnd, playTurnBell, playTurnEnd, setMuted } from '../audio/sfx';
import { onSettingsChange } from '../audio/engine';
import { playError } from '../audio/ui';
import { openSoundPanel } from './soundpanel';
import { effectText, traitLine } from './text';

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
  private top!: HTMLElement; private hand!: HTMLElement; private right!: HTMLElement; private hoverBox!: HTMLElement;
  private logBox!: HTMLElement; private logList!: HTMLElement; private ticker!: HTMLElement;
  private banner!: HTMLElement; private toast!: HTMLElement; private canvas!: HTMLCanvasElement; private stage!: HTMLElement;
  private preview!: HTMLElement;
  private selected: number | null = null;
  private mode: Mode = { kind: 'idle' };
  private hover: Pos | null = null;
  private aiRunning = false;
  private aiTimer = 0;
  private destroyed = false;
  private ended = false;
  private bannerQueue: { text: string; speaker?: string }[] = [];
  private bannerBusy = false;
  private enterArmed = 0;
  private hoverAbility: string | null = null;
  private cleanup: (() => void)[] = [];
  private logOpen = false;
  private handOpen = typeof window === 'undefined' || window.innerHeight >= 500;
  private touch = typeof matchMedia === 'function' && matchMedia('(hover: none)').matches;
  private previewId: string | null = null;
  private handFilter: 'all' | 'unit' | 'spell' | 'equipment' = 'all';
  private hudTop!: HTMLElement;
  private factions: (string | undefined)[] = [];

  constructor(container: HTMLElement, private opts: SessionOpts) {
    this.content = opts.content;
    this.game = new Game(opts.content, opts.missionId, { roster: opts.roster });
    this.root = container;
    this.build();
    this.renderer = new Renderer(this.canvas);
    this.renderer.setGame(this.game);
    this.renderer.start();
    this.renderer.onCue = c => playCue(c, this.game);
    this.game.on(e => this.onEvent(e));
    this.cleanup.push(onSettingsChange(() => this.renderTop()));
    let roRaf = 0; // coalesce bursts of resize events into one pass per frame
    const ro = new ResizeObserver(() => { if (roRaf) return; roRaf = requestAnimationFrame(() => { roRaf = 0; this.renderer.resize(); this.layoutHand(); }); });
    ro.observe(this.canvas.parentElement!);
    this.cleanup.push(() => { ro.disconnect(); cancelAnimationFrame(roRaf); });
    const kd = (e: KeyboardEvent) => this.onKey(e);
    // WASD / arrow keys pan the camera while held
    const held = new Set<string>();
    const PAN: Record<string, [number, number]> = { w: [0, 1], arrowup: [0, 1], s: [0, -1], arrowdown: [0, -1], a: [1, 0], arrowleft: [1, 0], d: [-1, 0], arrowright: [-1, 0] };
    const syncPan = () => { let x = 0, y = 0; for (const k of held) { x += PAN[k][0]; y += PAN[k][1]; } this.renderer.setPanVelocity(x, y); };
    const typing = (e: KeyboardEvent) => e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement;
    const pd = (e: KeyboardEvent) => { const k = e.key.toLowerCase(); if (PAN[k] && !typing(e) && !e.ctrlKey && !e.metaKey && !e.altKey) { e.preventDefault(); held.add(k); syncPan(); } };
    const pu = (e: KeyboardEvent) => { const k = e.key.toLowerCase(); if (held.delete(k)) syncPan(); };
    const blur = () => { held.clear(); syncPan(); };
    window.addEventListener('keydown', kd); window.addEventListener('keydown', pd); window.addEventListener('keyup', pu); window.addEventListener('blur', blur);
    this.cleanup.push(() => { window.removeEventListener('keydown', kd); window.removeEventListener('keydown', pd); window.removeEventListener('keyup', pu); window.removeEventListener('blur', blur); });
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
    installArt(); stopBackdrop();
    clear(this.root); this.root.className = 'game';
    const g = this.g;
    this.factions = g.teams.map((t, i) => teamFaction(this.content, [...t.hand, ...t.deck, ...g.units.filter(u => u.team === i).map(u => u.defId)]));
    this.hudTop = h('header', { id: 'hudtop' });
    this.top = this.hudTop;
    this.hand = h('div', { id: 'hand' });
    this.right = h('aside', { id: 'right', class: 'hudpanel' });
    this.hoverBox = h('div', { class: 'hoverbox' });
    this.canvas = h('canvas', { id: 'canvas' });
    this.banner = h('div', { id: 'banner', class: 'hidden' });
    this.toast = h('div', { id: 'turnflash', class: 'hidden' });
    this.logList = h('div', { class: 'loglist' });
    this.ticker = h('div', { class: 'ticker' });
    this.logBox = h('div', { id: 'log', class: 'hudpanel' },
      h('button', { class: 'logtoggle', title: 'Battle log', onclick: () => { this.logOpen = !this.logOpen; this.logBox.classList.toggle('open', this.logOpen); this.logList.scrollTop = this.logList.scrollHeight; } },
        glyph('log'), this.ticker), this.logList);
    this.preview = h('div', { id: 'cardpreview', class: 'hidden' });
    const vb = (icon: string, title: string, f: () => void) => h('button', { class: 'iconbtn', title, onclick: f }, glyph(icon));
    const ctl = h('div', { id: 'viewctl' },
      vb('rotl', 'Rotate view (Q)', () => this.renderer.rotate(-1)), vb('rotr', 'Rotate view (R)', () => this.renderer.rotate(1)),
      vb('plus', 'Zoom in', () => this.renderer.zoomBy(1.25)), vb('minus', 'Zoom out', () => this.renderer.zoomBy(0.8)),
      vb('center', 'Reset view', () => this.renderer.resetView()));
    const fade = h('div', { class: 'fadein' });
    this.stage = h('main', { id: 'stage' }, this.canvas, this.hudTop, this.logBox, this.banner, this.toast, ctl, this.preview, this.right, fade);
    this.root.append(this.stage, this.hand);
    this.bindPointer();
  }

  /** Pointer handling: hover (mouse), tap vs drag-to-pan, pinch/wheel zoom. */
  private bindPointer() {
    const cv = this.canvas;
    const pts = new Map<number, { x: number; y: number }>();
    let start: { x: number; y: number; t: number } | null = null, dragging = false, pinchD = 0, lastMid: { x: number; y: number } | null = null;
    const local = (e: PointerEvent) => { const r = cv.getBoundingClientRect(); return { x: e.clientX - r.left, y: e.clientY - r.top }; };
    cv.addEventListener('pointerdown', e => {
      cv.setPointerCapture(e.pointerId);
      pts.set(e.pointerId, local(e));
      if (pts.size === 1) { start = { ...local(e), t: performance.now() }; dragging = false; lastMid = null; }
      else if (pts.size === 2) { const [a, b] = [...pts.values()]; pinchD = Math.hypot(a.x - b.x, a.y - b.y); lastMid = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }; dragging = true; }
      e.preventDefault();
    });
    cv.addEventListener('pointermove', e => {
      const p = local(e);
      if (pts.has(e.pointerId)) {
        pts.set(e.pointerId, p);
        if (pts.size === 2) {
          const [a, b] = [...pts.values()]; const d = Math.hypot(a.x - b.x, a.y - b.y), mid = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
          if (pinchD > 0) this.renderer.zoomBy(d / pinchD, mid.x, mid.y);
          if (lastMid) this.renderer.pan(mid.x - lastMid.x, mid.y - lastMid.y);
          pinchD = d; lastMid = mid; return;
        }
        if (start) {
          const prev = lastMid ?? start;
          if (!dragging && Math.hypot(p.x - start.x, p.y - start.y) > 8) dragging = true;
          if (dragging) { this.renderer.pan(p.x - prev.x, p.y - prev.y); lastMid = p; this.setHover(null); return; }
        }
      }
      if (e.pointerType === 'mouse' && !dragging) this.setHover(this.renderer.pick(p.x, p.y));
    });
    const up = (e: PointerEvent) => {
      const p = local(e);
      const was = pts.size;
      pts.delete(e.pointerId);
      if (was === 1 && start && !dragging && performance.now() - start.t < 600) {
        this.hidePreview();
        this.click(this.renderer.pick(p.x, p.y));
      }
      if (pts.size === 0) { start = null; dragging = false; lastMid = null; }
      else if (pts.size === 1) { const [a] = [...pts.values()]; start = { ...a, t: 0 }; lastMid = a; dragging = true; }
    };
    cv.addEventListener('pointerup', up);
    cv.addEventListener('pointercancel', up);
    cv.addEventListener('mouseleave', () => this.setHover(null));
    cv.addEventListener('wheel', e => { e.preventDefault(); const p = local(e as unknown as PointerEvent); this.renderer.zoomBy(e.deltaY < 0 ? 1.12 : 0.9, p.x, p.y); }, { passive: false });
    cv.addEventListener('contextmenu', e => { e.preventDefault(); this.cancel(); });
  }
  private setHover(p: Pos | null) {
    if (p?.x !== this.hover?.x || p?.y !== this.hover?.y) { this.hover = p; this.updateOverlay(); this.renderHover(); }
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
      case 'skyfall': this.logLine(`${g.content.units[e.defId]?.name ?? e.defId} is falling toward ${e.x},${e.y}.`, 'move'); break;
      case 'land': this.logLine(`${this.uname(e.uid)} crashes down at ${e.to.x},${e.to.y}.`, 'move'); break;
      case 'essence': this.logLine(`${g.teams[e.team].name} ${e.amount >= 0 ? 'gains' : 'loses'} ${Math.abs(e.amount)} ${this.L('essence')}.`, 'sys'); break;
      case 'cooldown': if (g.teams[e.team].controller === 'human') this.logLine(`${g.cardName(e.card)} rests for ${e.turns} turn${e.turns === 1 ? '' : 's'}.`, 'sys'); break;
      case 'ready': if (g.teams[e.team].controller === 'human') this.logLine(`${g.cardName(e.card)} returns to ${e.toHand ? 'your hand' : 'the top of your draw pile'}.`, 'sys'); break;
      case 'drop': this.logLine(`${e.amount} ${this.L('essence')} spills on the seabed.`, 'sys'); break;
      case 'pickup': this.logLine(`${this.uname(e.uid)} collects ${e.amount} ${this.L('essence')}.`, 'sys'); break;
      case 'terrain': this.logLine(`The ground at ${e.x},${e.y} becomes ${g.content.terrain[e.terrain]?.name ?? e.terrain}.`, 'sys'); break;
      case 'turn': this.logLine(`Round ${e.turn} - ${g.teams[e.team].name}`, 'turn'); this.toastMsg(`Round ${e.turn} - ${g.teams[e.team].name}`, g.teams[e.team].color, e.team); playTurnBell(g.teams[e.team].controller === 'human'); break;
      case 'message': this.logLine(`${e.speaker ? e.speaker + ': ' : ''}${e.text}`, 'msg'); this.bannerQueue.push({ text: e.text, speaker: e.speaker }); this.pumpBanner(); break;
      case 'draw': if (g.teams[e.team].controller === 'human') { this.logLine(`You draw ${g.cardName(e.card)}.`, 'sys'); playCard(); } break;
      case 'end': this.ended = true; this.logLine(e.phase === 'victory' ? 'Victory!' : 'Defeat.', 'turn'); this.waitForEnd(e.phase); break;
    }
  }

  private logLine(text: string, cls: string) {
    this.logList.append(h('div', { class: 'logline ' + cls }, text));
    while (this.logList.childElementCount > 200) this.logList.firstElementChild!.remove();
    this.logList.scrollTop = this.logList.scrollHeight;
    this.ticker.className = 'ticker ' + cls; this.ticker.textContent = text;
  }

  private toastMsg(text: string, color?: string, team?: number) {
    const f = this.toast;
    clear(f);
    const m = /^Round (\d+) - (.*)$/.exec(text);
    f.classList.toggle('hint', !m);
    if (!m) { f.append(h('div', { class: 'tf-hint' }, text)); f.classList.remove('hidden', 'show'); void f.offsetWidth; f.classList.add('show'); return; }
    const ti = team ?? this.g.current;
    const mine = this.g.teams[ti]?.controller === 'human';
    f.style.setProperty('--tc', color ?? this.g.teams[ti]?.color ?? '#e8c57a');
    const cr = h('span', { class: 'tf-crest' }); cr.innerHTML = crestSvg(this.factions[ti], this.g.teams[ti]?.color);
    f.append(h('div', { class: 'tf-band' }, cr, h('div', { class: 'tf-text' },
      h('div', { class: 'tf-kick' }, m ? `Round ${m[1]}` : ''), h('div', { class: 'tf-main' }, m ? (mine ? 'Your Turn' : m[2]) : text))));
    f.classList.remove('hidden', 'show'); void f.offsetWidth; f.classList.add('show');
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
      setTimeout(() => { if (this.destroyed) return; playEnd(phase === 'victory'); this.showEnd(phase); }, 500);
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
    const ht = this.humanTeam();
    const cr = h('span', { class: 'end-crest' }); cr.innerHTML = crestSvg(this.factions[ht], this.g.teams[ht]?.color);
    const unlockIds = unlockedNames.length && c ? (this.content.campaigns[c.id].missions[c.index].unlocks ?? []) : [];
    const modal = h('div', { class: 'endscreen ' + (win ? 'win' : 'lose') },
      h('div', { class: 'end-inner' },
        cr,
        h('h2', { class: 'end-title' }, win ? 'Victory' : 'Defeat'),
        h('div', { class: 'end-mission' }, m.name),
        h('p', { class: 'end-text' }, text),
        unlockIds.length ? h('div', { class: 'end-unlocks' }, h('div', { class: 'kicker' }, 'New relics join your Chart'),
          h('div', { class: 'end-cards' }, ...unlockIds.map(id => buildCard(id, { size: 'hand', content: this.content })))) : null,
        h('div', { class: 'btnrow' },
          win && this.opts.onNext ? h('button', { class: 'btn-gold big', onclick: () => this.opts.onNext!() }, 'Next Mission') : null,
          h('button', { class: win && this.opts.onNext ? 'btn-plain' : 'btn-gold big', onclick: () => this.opts.onRetry() }, win ? 'Replay' : 'Try Again'),
          h('button', { class: 'btn-plain', onclick: () => this.opts.onExit() }, 'Main Menu'))));
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
      if (g.phase === 'playing' && g.teams[g.current].controller === 'ai') { steps = more ? steps : 0; this.aiTimer = window.setTimeout(tick, 200); }
      else { this.aiRunning = false; this.refresh(); }
    };
    this.aiTimer = window.setTimeout(tick, 350);
  }

  // ---------- input ----------
  private endTurn() {
    if (this.canActSoft() && this.renderer.busy()) { setTimeout(() => this.endTurn(), 120); return; }
    if (!this.canAct()) return;
    this.selected = null; this.mode = { kind: 'idle' };
    this.hidePreview();
    playTurnEnd();
    this.g.endTurn();
    this.refresh();
    this.scheduleAi();
  }

  private cancel() {
    if (this.mode.kind === 'ability') this.mode = { kind: 'move' };
    else if (this.mode.kind === 'card') this.mode = { kind: 'idle' };
    else { this.selected = null; this.mode = { kind: 'idle' }; }
    this.hidePreview();
    this.refresh();
  }

  private onKey(e: KeyboardEvent) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const k = e.key.toLowerCase();
    if (k === 'escape') this.cancel();
    else if (k === 'm') { setMuted(!isMuted()); this.renderTop(); this.toastMsg(isMuted() ? 'Sound off (M)' : 'Sound on (M)', '#b8913e', this.g.current); }
    else if (k === 'enter') { // press twice to end the turn (not 'e': it sits next to WASD)
      e.preventDefault();
      if (performance.now() < this.enterArmed) { this.enterArmed = 0; this.endTurn(); }
      else if (this.canActSoft()) { this.enterArmed = performance.now() + 2500; this.toastMsg('Press Enter again to end turn'); }
    }
    else if (k === 'q') this.renderer.rotate(-1);
    else if (k === 'r') this.renderer.rotate(1);
    else if (k === '+' || k === '=') this.renderer.zoomBy(1.2);
    else if (k === '-') this.renderer.zoomBy(0.83);
    else if (/^[1-9]$/.test(k)) {
      const btn = this.right.querySelectorAll<HTMLButtonElement>('button.abtn:not(:disabled)')[Number(k) - 1];
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
      if (g.cardTargets(g.current, m.index).some(t => t.x === p.x && t.y === p.y)) { if (g.playCard(g.current, m.index, p.x, p.y)) playCardPlay(); } else playError();
      this.mode = { kind: 'idle' };
      this.refresh(); return;
    }
    if (p && u && mine && this.mode.kind === 'ability') {
      const ab = this.mode.ability;
      if (g.validTargets(u, ab).some(t => t.x === p.x && t.y === p.y)) {
        g.useAbility(u.uid, ab, p.x, p.y);
        this.mode = { kind: 'move' }; this.refresh(); return;
      }
      // inside the range zone: keep the attack armed; outside it: cancel
      if (g.rangeTiles(u, ab).some(t => t.x === p.x && t.y === p.y) && !(occ && occ.team === g.current)) return;
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
    this.hoverAbility = null; // the unit panel is rebuilt below, so a stale hover can't linger
    const u = this.sel();
    if (u && !u.alive) { this.selected = null; this.mode = { kind: 'idle' }; }
    if (this.mode.kind === 'ability') {
      const s = this.sel();
      if (!s || !this.g.canUse(s, this.mode.ability)) this.mode = s ? { kind: 'move' } : { kind: 'idle' };
    }
    if (this.mode.kind === 'card' && !this.g.cardTargets(this.g.current, this.mode.index).length) this.mode = { kind: 'idle' };
    this.updateOverlay();
    this.renderTop(); this.renderHand(); this.renderRight(); this.renderHover();
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
    ov.reach.clear(); ov.range.clear(); ov.targets.clear(); ov.area.clear(); ov.deploy.clear(); ov.skyfall.clear(); ov.path = []; ov.pathCost = null; ov.previews = new Map();
    ov.hover = this.hover;
    const u = this.sel();
    ov.selected = u ? { x: u.x, y: u.y } : null;
    if (!this.canActSoft()) return;
    const hv = this.hover;
    if (this.mode.kind === 'card') {
      const id = g.teams[g.current].hand[this.mode.index];
      const targets = g.cardTargets(g.current, this.mode.index);
      const instant = new Set(g.deployTiles(g.current).map(p => key(p.x, p.y)));
      for (const t of targets) (g.content.units[id]?.skyfall && !instant.has(key(t.x, t.y)) ? ov.skyfall : ov.deploy).add(key(t.x, t.y));
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
    // ability range in yellow: the armed ability, or the one under the mouse in the unit panel
    const rangeAb = this.mode.kind === 'ability' ? this.mode.ability : this.hoverAbility;
    if (rangeAb && g.ability(rangeAb)) for (const t of g.rangeTiles(u, rangeAb)) ov.range.add(key(t.x, t.y));
    if (this.mode.kind === 'move' && !this.hoverAbility) {
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

  /** Player plate: crest, name, Tide gauge and Beacon lamp. */
  private teamGauge(i: number, side: 'left' | 'right') {
    const g = this.g, t = g.teams[i];
    const max = g.mission.maxEssence ?? DEFAULTS.maxEssence;
    const fill = Math.max(0, Math.min(1, t.essence / max));
    const ks = g.units.find(u => u.team === i && g.def(u).structure && u.tag?.startsWith('keystone'));
    const kf = ks ? (ks.alive ? ks.hp / g.def(ks).stats.hp : 0) : -1;
    const cr = h('span', { class: 'pp-crest' }); cr.innerHTML = crestSvg(this.factions[i], t.color);
    return h('div', { class: `pplate ${side}${i === g.current ? ' active' : ''}`, style: `--tc:${t.color}`, title: `${t.name}: ${t.essence} ${this.L('essence')}${ks ? ` \u00B7 ${this.L('keystone')} ${ks.hp}/${g.def(ks).stats.hp}` : ''}` },
      cr,
      h('div', { class: 'pp-body' },
        h('div', { class: 'pp-name' }, t.name.replace(/^The /, '')),
        h('div', { class: 'pp-row' },
          h('span', { class: 'pp-tide num' }, String(t.essence), h('small', null, this.L('essence'))),
          h('div', { class: 'tidebar', title: `${this.L('essence')} ${t.essence}/${max}` }, h('i', { class: 'water', style: `width:${Math.round(fill * 100)}%` })),
          kf >= 0 ? h('span', { class: 'lamp', style: `--lk:${kf.toFixed(2)}`, title: `${this.L('keystone')} ${ks!.hp}/${g.def(ks!).stats.hp}` }, h('i', { class: 'flame' }), h('i', { class: 'tower' })) : null)));
  }

  private renderTop() {
    const g = this.g;
    clear(this.top);
    const cur = g.teams[g.current], me = this.humanTeam();
    const myTurn = cur.controller === 'human';
    const others = g.teams.map((_, i) => i).filter(i => i !== me);
    const endBtn = h('button', { class: 'endturn-pill btn-gold', disabled: !this.canActSoft(), title: 'End turn (Enter twice)', onclick: () => this.endTurn() }, 'End Turn');
    this.top.append(
      h('div', { class: 'hud-l' }, this.teamGauge(me, 'left')),
      h('div', { class: 'roundmed', style: `--tc:${cur.color}` },
        h('div', { class: 'rm-round' }, 'Round ', h('b', { class: 'num' }, String(g.round))),
        h('div', { class: 'rm-turn' }, myTurn ? 'Your turn' : this.aiRunning ? `${cur.name.replace(/^The /, '')} acting` : `${cur.name.replace(/^The /, '')}`)),
      h('div', { class: 'hud-r' }, ...others.map(i => this.teamGauge(i, 'right')), endBtn,
        h('button', { class: 'iconbtn menubtn soundbtn', title: isMuted() ? 'Sound off (M)' : 'Sound settings (M mutes)', 'data-snd': 'open', onclick: (e: Event) => openSoundPanel(e.currentTarget as HTMLElement) }, glyph(isMuted() ? 'mute' : 'sound')),
        h('button', { class: 'iconbtn menubtn', title: 'Menu', onclick: () => { if (this.ended || confirm('Abandon this battle and return to the menu?')) this.opts.onExit(); } }, glyph('gear'))));
  }

  // ---------- hand ----------
  /** Show/hide the hand instantly: flip a class, no DOM rebuild and no animation. */
  private setHandOpen(open: boolean, btn?: HTMLElement) {
    this.handOpen = open; this.hand.classList.toggle('closed', !open);
    btn?.querySelector('.chev')?.classList.toggle('up', !open); btn?.setAttribute('title', open ? 'Hide hand' : 'Show hand');
    this.renderer.resize(); this.layoutHand();
  }
  private renderHand() {
    const g = this.g, t = this.humanTeam(), team = g.teams[t];
    const scroll = this.hand.querySelector('.handrow')?.scrollLeft ?? 0;
    clear(this.hand);
    this.hand.classList.toggle('closed', !this.handOpen);
    const row = h('div', { class: 'handrow' });
    const counts = { all: team.hand.length, unit: 0, spell: 0, equipment: 0 } as Record<string, number>;
    team.hand.forEach(id => { counts[g.cardKind(id) ?? 'unit']++; });
    if (this.handFilter !== 'all' && !counts[this.handFilter]) this.handFilter = 'all';
    team.hand.forEach((id, i) => {
      const kind = g.cardKind(id) ?? 'unit';
      if (this.handFilter !== 'all' && kind !== this.handFilter) return;
      const cost = g.cardCost(id);
      const ok = this.canActSoft() && t === g.current && g.cardTargets(t, i).length > 0;
      const active = this.mode.kind === 'card' && this.mode.index === i;
      const card = this.runeTile(id, cost);
      const why = ok ? '' : cost > team.essence ? `Not enough ${this.L('essence')}` : 'Cannot be played now';
      const slot = h('div', { class: `slot ${kind}${active ? ' active' : ''}${ok ? ' ok' : ' off'}`, title: why,
        onclick: () => {
          if (this.touch && this.previewId !== id) this.showPreview(id, slot); else this.hidePreview();
          if (!ok || !this.canAct()) return;
          this.mode = active ? { kind: 'idle' } : { kind: 'card', index: i }; this.selected = null; this.refresh();
        },
        onmouseenter: () => { if (!this.touch) this.showPreview(id, slot); },
        onmouseleave: () => { if (!this.touch) this.hidePreview(); },
      }, card, h('button', { class: 'info', title: 'Details', onclick: (e: Event) => { e.stopPropagation(); if (this.previewId === id) this.hidePreview(); else this.showPreview(id, slot); } }, 'i'));
      row.append(slot);
    });
    for (const cd of team.cooldown) { // resting cards: dimmed, not playable, badge = turns left
      const kind = g.cardKind(cd.card) ?? 'unit', tip = `Returns in ${cd.turns} turn${cd.turns === 1 ? '' : 's'}`;
      const slot = h('div', { class: `slot cd ${kind}`, title: tip,
        onclick: () => { if (this.touch && this.previewId !== cd.card) this.showPreview(cd.card, slot); else this.hidePreview(); },
        onmouseenter: () => { if (!this.touch) this.showPreview(cd.card, slot); }, onmouseleave: () => { if (!this.touch) this.hidePreview(); },
      }, this.runeTile(cd.card, g.cardCost(cd.card)), h('span', { class: 'cd-badge', title: tip }, String(cd.turns)));
      row.append(slot);
    }
    if (!team.hand.length && !team.cooldown.length) row.append(h('div', { class: 'empty' }, team.deck.length ? 'Your hand is empty. You draw 2 cards each turn.' : 'Every relic is on the field.'));
    else if (!team.hand.length) row.prepend(h('div', { class: 'empty' }, 'Hand empty. You draw 2 cards each turn; resting relics return soon.'));
    const hintFor = () => {
      if (this.mode.kind === 'ability') { const a = g.ability(this.mode.ability); return `${a?.name ?? ''}: choose a target \u00B7 Esc cancels`; }
      if (this.mode.kind !== 'card') {
        if (!(t === g.current && this.canActSoft())) return 'Waiting for the enemy';
        const su = this.sel();
        if (su && su.team === t && !g.def(su).structure) return su.ap > 0 ? 'Blue tiles: move \u00B7 Number keys: abilities \u00B7 Esc deselects' : `${g.def(su).name} is out of AP \u00B7 select another unit or end the turn`;
        return 'Play a relic, or select a unit on the board';
      }
      const k = g.cardKind(team.hand[this.mode.index] ?? '');
      return k === 'spell' ? 'Choose a target to cast \u00B7 Esc cancels' : k === 'equipment' ? 'Choose a friendly unit to equip \u00B7 Esc cancels' : g.content.units[team.hand[this.mode.index] ?? '']?.skyfall ? 'Green: deploy now \u00B7 Violet: drops in next turn \u00B7 Esc cancels' : 'Choose a glowing tile to deploy \u00B7 Esc cancels';
    };
    const tabs = h('div', { class: 'htabs' }, ...([['all', 'All'], ['unit', 'Champions'], ['spell', 'Spells'], ['equipment', 'Gear']] as const).map(([k, n]) =>
      h('button', { class: 'htab' + (this.handFilter === k ? ' on' : ''), disabled: !counts[k], onclick: (e: Event) => { e.stopPropagation(); this.handFilter = k; if (!this.handOpen) this.handOpen = true; this.renderHand(); this.renderer.resize(); } },
        n, h('small', null, String(counts[k])))));
    const strip = h('div', { class: 'hstrip' },
      h('button', { class: 'htoggle', title: this.handOpen ? 'Hide hand' : 'Show hand', onclick: (e: Event) => this.setHandOpen(!this.handOpen, e.currentTarget as HTMLElement) },
        h('span', { class: 'chev' + (this.handOpen ? '' : ' up') }, '\u25BE'), h('span', null, this.L('warband')), h('b', null, String(team.hand.length)), team.deck.length ? h('span', { class: 'hdeck', title: `${team.deck.length} cards left to draw` }, `+${team.deck.length}`) : null),
      tabs);
    const targeting = this.mode.kind === 'card' || this.mode.kind === 'ability';
    const end = h('button', { id: 'endturn', class: 'endturn-big', disabled: !this.canActSoft(), title: 'End turn (Enter twice)', onclick: () => this.endTurn() },
      h('span', { class: 'et-text' }, 'End Turn'), h('span', { class: 'et-key' }, 'Enter \u00D7 2'));
    this.hand.append(h('div', { class: 'hprompt' + (targeting ? ' act' : '') }, hintFor()), strip, h('div', { class: 'hmain' }, row, end));
    this.layoutHand();
    row.scrollLeft = scroll;
  }
  /** Compact rune tile for the hand bar: art, cost coin, kind pip. The full card shows on hover / tap. */
  private runeTile(id: string, cost: number) {
    const c = this.content, kind = this.g.cardKind(id) ?? 'unit';
    const def = (c.units[id] ?? c.spells[id] ?? c.equipment[id]) as { name: string; faction?: string } | undefined;
    const fc = def?.faction ? c.factions?.[def.faction]?.color : undefined;
    return h('div', { class: `rtile ${kind}${c.units[id]?.hero ? ' hero' : ''}`, style: `--fc:${fc ?? '#5a6f7a'}`, title: def?.name ?? id },
      artNode(id, c), h('span', { class: 'rt-cost hc-num' }, String(cost)), h('span', { class: 'rt-name' }, def?.name ?? id));
  }
  /** Fan the hand so every card fits in the available width (cards overlap when there are many). */
  private layoutHand() {
    const row = this.hand.querySelector<HTMLElement>('.handrow'); if (!row) return;
    row.classList.toggle('scroll', row.scrollWidth > row.clientWidth + 2);
  }

  private showPreview(id: string, anchor: HTMLElement) {
    this.previewId = id;
    clear(this.preview);
    this.preview.append(buildCard(id, { size: 'full', content: this.content }));
    this.preview.classList.remove('hidden');
    const sr = this.stage.getBoundingClientRect(), ar = anchor.getBoundingClientRect();
    const pw = this.preview.offsetWidth;
    const x = Math.max(8, Math.min(sr.width - pw - 8, ar.left + ar.width / 2 - sr.left - pw / 2));
    this.preview.style.left = `${x}px`;
  }
  private hidePreview() { this.previewId = null; this.preview.classList.add('hidden'); }

  private unitPanel(u: Unit, full: boolean) {
    const g = this.g, d = g.def(u), team = g.teams[u.team];
    const maxAp = g.stat(u, 'ap');
    const fc = d.faction ? this.content.factions?.[d.faction]?.color : undefined;
    const stat = (cls: string, lab: string, v: number, base: number) => h('span', { class: `ustat ${cls}${v > base ? ' up' : v < base ? ' down' : ''}`, title: lab }, h('small', null, lab), h('b', null, String(v)));
    const box = h('div', { class: 'upanel' + (full ? ' full' : ' mini'), style: `--tc:${team.color};--fc:${fc ?? team.color}` },
      h('div', { class: 'u-portrait' }, artNode(u.defId, this.content)),
      h('div', { class: 'u-body' },
        h('div', { class: 'u-name' }, d.name, d.hero ? h('span', { class: 'u-hero', title: 'Hero' }, '\u2655') : null),
        h('div', { class: 'u-line' },
          h('span', { class: 'u-hp' }, h('i', { class: 'hcoin' }), h('div', { class: 'ubar hp' }, h('div', { class: 'fill', style: `width:${Math.max(0, u.hp / d.stats.hp * 100)}%` }), h('span', null, `${u.hp}/${d.stats.hp}`))),
          stat('atk', 'ATK', g.stat(u, 'attack'), d.stats.attack), stat('def', 'DEF', g.stat(u, 'defense'), d.stats.defense)),
        d.structure ? null : h('div', { class: 'pips', title: `Action points ${u.ap}/${maxAp}` }, h('small', null, 'AP'), ...Array.from({ length: Math.min(maxAp, 14) }, (_, i) => h('i', { class: i < u.ap ? 'on' : '' })), h('b', { class: 'num' }, `${u.ap}/${maxAp}`)),
        u.statuses.length ? h('div', { class: 'statuses' }, ...u.statuses.map(s => {
          const sd = g.content.statuses[s.id];
          return h('span', { class: 'schip', style: `--sc:${statusColor(s.id)}`, title: sd?.description ?? '' }, sd?.name ?? s.id, h('small', null, `${s.remaining}${s.stacks && s.stacks > 1 ? ` \u00D7${s.stacks}` : ''}`));
        })) : null,
        traitLine(d) ? h('div', { class: 'line' }, traitLine(d)) : null,
        g.equipmentOf(u) ? h('div', { class: 'line equip', title: g.equipmentOf(u)!.description ?? '' }, h('b', null, g.equipmentOf(u)!.name)) : null));
    return box;
  }

  private renderRight() {
    const g = this.g;
    clear(this.right);
    const u = this.sel();
    this.right.classList.toggle('open', !!u || (!this.touch && !!this.hover && !!g.unitAt(this.hover.x, this.hover.y)));
    if (u) {
      const card = h('div', { class: 'ucard' });
      card.append(h('button', { class: 'iconbtn close', title: 'Close (Esc)', onclick: () => this.cancel() }, glyph('close')), this.unitPanel(u, true));
      const abs = g.abilitiesOf(u);
      if (abs.length) {
        const list = h('div', { class: 'abar' });
        let n = 0;
        abs.forEach(id => {
          const a = g.ability(id);
          if (!a) return;
          const range = a.range.min === a.range.max ? `${a.range.max}` : `${a.range.min}-${a.range.max}`;
          const tipEl = h('div', { class: 'abtip' }, h('b', null, a.name), h('span', { class: 'abmeta' }, a.passive ? 'Passive' : `${a.apCost} AP \u00B7 range ${range}${a.area ? ` \u00B7 area ${a.area.size}` : ''}${a.cooldown ? ` \u00B7 cooldown ${a.cooldown}` : ''}`),
            h('p', null, a.description ?? a.effects.map(e => effectText(this.content, e)).join('. ')));
          const meta = a.passive ? 'Passive' : `${range === '0' ? 'Self' : `Range ${range}`}${a.area ? ` \u00B7 area ${a.area.size}` : ''}`;
          if (a.passive) { list.append(h('div', { class: 'abtn passive', tabindex: '0' }, h('span', { class: 'ab-ic' }, glyph(abilityGlyph(a))), h('span', { class: 'ab-txt' }, h('span', { class: 'ab-name' }, a.name), h('span', { class: 'ab-meta' }, meta)), tipEl)); return; }
          const cd = u.cooldowns[id] ?? 0;
          const usable = u.team === g.current && this.canActSoft() && g.canUse(u, id);
          const active = this.mode.kind === 'ability' && this.mode.ability === id;
          const idx = ++n;
          list.append(h('button', {
            class: 'abtn' + (active ? ' active' : ''), disabled: !usable,
            onclick: () => { if (!this.canAct()) return; this.mode = active ? { kind: 'move' } : { kind: 'ability', ability: id }; this.hoverAbility = null; this.refresh(); },
            onmouseenter: () => { this.hoverAbility = id; this.updateOverlay(); },
            onmouseleave: () => { if (this.hoverAbility === id) { this.hoverAbility = null; this.updateOverlay(); } },
          }, h('span', { class: 'ab-key' }, String(idx)), h('span', { class: 'ab-ic' }, glyph(abilityGlyph(a))),
            h('span', { class: 'ab-txt' }, h('span', { class: 'ab-name' }, a.name), h('span', { class: 'ab-meta' }, cd > 0 ? `Ready in ${cd}` : meta)),
            h('span', { class: 'ab-ap hc-num', title: `${a.apCost} AP` }, String(a.apCost), h('small', null, 'AP')), tipEl));
        });
        card.append(list);
      }
      this.right.append(card);
    }
    this.right.append(this.hoverBox);
    this.updateInset();
  }
  /** On portrait phones the unit drawer covers the bottom of the stage; keep the board centred above it. */
  private updateInset() {
    const portraitPhone = this.touch && window.innerHeight > window.innerWidth && window.innerWidth <= 900;
    this.renderer.setBottomInset(portraitPhone && this.right.classList.contains('open') ? this.right.offsetHeight : 0);
  }

  private renderHover() {
    const g = this.g;
    clear(this.hoverBox);
    const hv = this.hover;
    if (!hv || !g.inBounds(hv.x, hv.y)) { if (!this.touch) this.right.classList.toggle('open', !!this.sel()); return; }
    const occ = g.unitAt(hv.x, hv.y);
    if (!this.touch) this.right.classList.toggle('open', !!this.sel() || !!occ);
    const t = g.tiles[hv.y][hv.x], terr = g.content.terrain[t.terrain];
    if (occ && occ.uid !== this.selected) { this.hoverBox.append(this.unitPanel(occ, false)); }
    const pv = this.renderer.overlay.previews;
    if (pv.size) {
      const box = h('div', { class: 'preview' }, h('div', { class: 'pv-h' }, 'Forecast'));
      for (const [uid, p] of pv) box.append(h('div', { class: 'pv-row' }, h('span', null, this.uname(uid)), h('b', { style: `color:${p.color}` }, p.text)));
      this.hoverBox.append(box);
    }
    const drop = g.drops.find(d => d.x === hv.x && d.y === hv.y);
    if (drop) this.hoverBox.append(h('div', { class: 'tileinfo dropinfo' }, h('b', null, `${drop.amount} ${this.L('essence')}`), h('span', null, 'Step here to collect')));
    this.hoverBox.append(h('div', { class: 'tileinfo' },
      h('b', null, terr?.name ?? t.terrain), h('span', null, `Height ${t.height}`), h('span', null, `Move ${terr?.moveCost}`), terr?.defense ? h('span', null, `DEF ${terr.defense > 0 ? '+' : ''}${terr.defense}`) : null, terr?.description ? h('span', { class: 'terr-desc' }, terr.description) : null,
      g.map.wells?.some(w => w.x === hv.x && w.y === hv.y) ? h('span', { class: 'well' }, `${this.L('essence')} well`) : null));
  }
}

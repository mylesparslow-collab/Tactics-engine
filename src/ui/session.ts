import { Game, DEFAULTS } from '../engine/game';
import { aiStep } from '../engine/ai';
import { label } from '../engine/content';
import { loadProgress, recordVictory } from '../engine/campaign';
import type { Content, Effect, GameEvent, Pos, Unit } from '../engine/types';
import { Renderer } from '../render/renderer';
import { key } from '../render/iso';
import { statusColor } from '../render/sprites';
import { clear, h } from './dom';
import { buildCard } from './cards';
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
  private cleanup: (() => void)[] = [];
  private logOpen = false;
  private handOpen = typeof window === 'undefined' || window.innerHeight >= 500;
  private touch = typeof matchMedia === 'function' && matchMedia('(hover: none)').matches;
  private previewId: string | null = null;

  constructor(container: HTMLElement, private opts: SessionOpts) {
    this.content = opts.content;
    this.game = new Game(opts.content, opts.missionId, { roster: opts.roster });
    this.root = container;
    this.build();
    this.renderer = new Renderer(this.canvas);
    this.renderer.setGame(this.game);
    this.renderer.start();
    this.game.on(e => this.onEvent(e));
    const ro = new ResizeObserver(() => { this.renderer.resize(); this.layoutHand(); });
    ro.observe(this.canvas.parentElement!);
    this.cleanup.push(() => ro.disconnect());
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
    clear(this.root); this.root.className = 'game';
    this.top = h('header', { id: 'topbar' });
    this.hand = h('div', { id: 'hand' });
    this.right = h('aside', { id: 'right', class: 'panel' });
    this.hoverBox = h('div', { class: 'hoverbox' });
    this.canvas = h('canvas', { id: 'canvas' });
    this.banner = h('div', { id: 'banner', class: 'hidden' });
    this.toast = h('div', { id: 'toast', class: 'hidden' });
    this.logList = h('div', { class: 'loglist' });
    this.ticker = h('div', { class: 'ticker' });
    this.logBox = h('div', { id: 'log', onclick: () => { this.logOpen = !this.logOpen; this.logBox.classList.toggle('open', this.logOpen); this.logList.scrollTop = this.logList.scrollHeight; } },
      h('div', { class: 'logtitle' }, h('span', null, 'Log'), h('span', { class: 'chev' }, '▴')), this.ticker, this.logList);
    this.preview = h('div', { id: 'cardpreview', class: 'hidden' });
    const ctl = h('div', { id: 'viewctl' },
      h('button', { title: 'Rotate view (Q)', onclick: () => this.renderer.rotate(-1) }, '⟲'),
      h('button', { title: 'Rotate view (R)', onclick: () => this.renderer.rotate(1) }, '⟳'),
      h('button', { title: 'Zoom in', onclick: () => this.renderer.zoomBy(1.25) }, '+'),
      h('button', { title: 'Zoom out', onclick: () => this.renderer.zoomBy(0.8) }, '−'),
      h('button', { title: 'Reset view', onclick: () => this.renderer.resetView() }, '⌖'));
    this.stage = h('main', { id: 'stage' }, this.canvas, this.logBox, this.banner, this.toast, ctl, this.preview, this.right);
    this.root.append(this.top, this.stage, this.hand);
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
      case 'essence': this.logLine(`${g.teams[e.team].name} ${e.amount >= 0 ? 'gains' : 'loses'} ${Math.abs(e.amount)} ${this.L('essence')}.`, 'sys'); break;
      case 'terrain': this.logLine(`The ground at ${e.x},${e.y} becomes ${g.content.terrain[e.terrain]?.name ?? e.terrain}.`, 'sys'); break;
      case 'turn': this.logLine(`Round ${e.turn} - ${g.teams[e.team].name}`, 'turn'); this.toastMsg(`Round ${e.turn} - ${g.teams[e.team].name}`, g.teams[e.team].color); break;
      case 'message': this.logLine(`${e.speaker ? e.speaker + ': ' : ''}${e.text}`, 'msg'); this.bannerQueue.push({ text: e.text, speaker: e.speaker }); this.pumpBanner(); break;
      case 'end': this.ended = true; this.logLine(e.phase === 'victory' ? 'Victory!' : 'Defeat.', 'turn'); this.waitForEnd(e.phase); break;
    }
  }

  private logLine(text: string, cls: string) {
    this.logList.append(h('div', { class: 'logline ' + cls }, text));
    while (this.logList.childElementCount > 200) this.logList.firstElementChild!.remove();
    this.logList.scrollTop = this.logList.scrollHeight;
    this.ticker.className = 'ticker ' + cls; this.ticker.textContent = text;
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
    this.hidePreview();
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
    else if (k === 'enter') { e.preventDefault(); this.endTurn(); } // not 'e': it sits next to WASD
    else if (k === 'q') this.renderer.rotate(-1);
    else if (k === 'r') this.renderer.rotate(1);
    else if (k === '+' || k === '=') this.renderer.zoomBy(1.2);
    else if (k === '-') this.renderer.zoomBy(0.83);
    else if (/^[1-9]$/.test(k)) {
      const btn = this.right.querySelectorAll<HTMLButtonElement>('button.rune:not(:disabled)')[Number(k) - 1];
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

  /** Tide vessel + Beacon lamp for a team. */
  private teamGauge(i: number) {
    const g = this.g, t = g.teams[i];
    const max = g.mission.maxEssence ?? DEFAULTS.maxEssence;
    const fill = Math.max(0, Math.min(1, t.essence / max));
    const ks = g.units.find(u => u.team === i && g.def(u).structure && u.tag?.startsWith('keystone'));
    const kf = ks ? (ks.alive ? ks.hp / g.def(ks).stats.hp : 0) : -1;
    const el = h('div', { class: 'tg' + (i === g.current ? ' active' : ''), style: `--tc:${t.color}`, title: `${t.name}: ${t.essence} ${this.L('essence')}${ks ? ` · ${this.L('keystone')} ${ks.hp}/${g.def(ks).stats.hp}` : ''}` },
      h('span', { class: 'tgname' }, t.name),
      h('span', { class: 'vessel', title: `${this.L('essence')} ${t.essence}/${max}` }, h('i', { class: 'water', style: `height:${Math.round(fill * 100)}%` }), h('i', { class: 'glass' })),
      h('b', { class: 'tide' }, String(t.essence)),
      kf >= 0 ? h('span', { class: 'lamp', style: `--lk:${kf.toFixed(2)}`, title: `${this.L('keystone')} ${ks!.hp}/${g.def(ks!).stats.hp}` }, h('i', { class: 'flame' }), h('i', { class: 'tower' })) : null);
    return el;
  }

  private renderTop() {
    const g = this.g;
    clear(this.top);
    const cur = g.teams[g.current];
    this.top.append(
      h('div', { class: 'brand' }, h('span', { class: 'ebb' }, this.content.config?.labels?.title ?? 'EBB'), h('span', { class: 'mission' }, g.mission.name)),
      h('div', { class: 'turnbox', style: `--tc:${cur.color}` }, h('span', { class: 'round' }, `Round ${g.round}`), h('span', { class: 'who' }, `${cur.name}${this.aiRunning ? ' is thinking' : "'s turn"}`)),
      h('div', { class: 'spacer' }),
      ...g.teams.map((_, i) => this.teamGauge(i)),
      h('button', { id: 'endturn', class: 'brass', disabled: !this.canActSoft(), title: 'End turn (Enter)', onclick: () => this.endTurn() }, h('span', null, 'End Turn')),
      h('button', { class: 'quiet menu', title: 'Menu', onclick: () => { if (this.ended || confirm('Abandon this battle and return to the menu?')) this.opts.onExit(); } }, 'Menu'));
  }

  // ---------- hand ----------
  private renderHand() {
    const g = this.g, t = this.humanTeam(), team = g.teams[t];
    clear(this.hand);
    this.hand.classList.toggle('closed', !this.handOpen);
    const row = h('div', { class: 'handrow' });
    team.hand.forEach((id, i) => {
      const kind = g.cardKind(id) ?? 'unit';
      const cost = g.cardCost(id);
      const ok = this.canActSoft() && t === g.current && g.cardTargets(t, i).length > 0;
      const active = this.mode.kind === 'card' && this.mode.index === i;
      const card = buildCard(id, { size: 'hand', content: this.content });
      const why = ok ? '' : cost > team.essence ? `Not enough ${this.L('essence')}` : 'Cannot be played now';
      const slot = h('div', { class: `slot ${kind}${active ? ' active' : ''}${ok ? '' : ' off'}`, title: why,
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
    if (!team.hand.length) row.append(h('div', { class: 'muted empty' }, 'No cards in reserve.'));
    const hintFor = () => {
      if (this.mode.kind !== 'card') return `${this.L('warband')} · tap a card, then a highlighted tile`;
      const k = g.cardKind(team.hand[this.mode.index] ?? '');
      return k === 'spell' ? 'Choose a target tile to cast. Esc cancels.' : k === 'equipment' ? 'Choose a friendly unit to equip. Esc cancels.' : 'Choose a green tile to deploy. Esc cancels.';
    };
    const tab = h('div', { class: 'handtab', onclick: () => { this.handOpen = !this.handOpen; this.hand.classList.toggle('closed', !this.handOpen); this.renderer.resize(); } },
      h('span', { class: 'chev' }, this.handOpen ? '▾' : '▴'), h('span', { class: 'hint' }, hintFor()), h('span', { class: 'count' }, `${team.hand.length}`));
    this.hand.append(tab, row);
    this.layoutHand();
  }
  /** Fan the hand so every card fits in the available width (cards overlap when there are many). */
  private layoutHand() {
    const row = this.hand.querySelector<HTMLElement>('.handrow'); if (!row) return;
    const slots = row.querySelectorAll<HTMLElement>('.slot'); if (!slots.length) return;
    const avail = row.clientWidth - 24, cw = slots[0].offsetWidth || 120, n = slots.length;
    const overlap = n > 1 ? Math.min(0, (avail - n * cw) / (n - 1)) : 0;
    const narrow = window.innerWidth < 900 || window.innerHeight < 520;
    row.classList.toggle('scroll', narrow);
    slots.forEach((s, i) => { s.style.marginLeft = narrow || i === 0 ? '' : `${Math.max(overlap, -cw * 0.7)}px`; s.style.zIndex = String(i + 1); });
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
    const box = h('div', { class: 'upanel', style: `--tc:${team.color}` },
      buildCard(u.defId, { size: 'portrait', content: this.content, live: { game: g, unit: u } }),
      h('div', { class: 'bars' },
        h('div', { class: 'bar' }, h('div', { class: 'fill hp', style: `width:${Math.max(0, u.hp / d.stats.hp * 100)}%` }), h('span', null, `HP ${u.hp}/${d.stats.hp}`)),
        d.structure ? null : h('div', { class: 'bar' }, h('div', { class: 'fill ap', style: `width:${maxAp ? Math.min(100, u.ap / maxAp * 100) : 0}%` }), h('span', null, `AP ${u.ap}/${maxAp}`))),
      h('div', { class: 'teamline' }, h('i', { class: 'dot' }), team.name, d.hero ? ' · Hero' : ''),
      d.resist && Object.keys(d.resist).length ? h('div', { class: 'line' }, 'Resist: ' + Object.entries(d.resist).map(([k, v]) => `${k} ${v > 0 ? '+' : ''}${v}`).join(', ')) : null,
      g.equipmentOf(u) ? h('div', { class: 'line equip', title: g.equipmentOf(u)!.description ?? '' }, h('b', null, g.equipmentOf(u)!.name), g.equipmentOf(u)!.description ? ' - ' + g.equipmentOf(u)!.description : '') : null,
      d.revive ? h('div', { class: 'line' }, u.revived ? 'Has risen once already.' : `Rises once on death (${Math.round(d.revive.hpFraction * 100)}% HP).`) : null);
    if (u.statuses.length) {
      box.append(h('div', { class: 'statuses' }, ...u.statuses.map(s => {
        const sd = g.content.statuses[s.id];
        return h('div', { class: 'status', title: sd?.description ?? '' }, h('span', { class: 'sdot', style: `background:${statusColor(s.id)}` }), h('b', null, `${sd?.name ?? s.id}`), h('span', { class: 'muted' }, ` ${s.remaining}${s.stacks && s.stacks > 1 ? ` ×${s.stacks}` : ''}`));
      })));
    }
    if (full && d.description) box.append(h('div', { class: 'desc' }, d.description));
    return box;
  }

  private renderRight() {
    const g = this.g;
    clear(this.right);
    const u = this.sel();
    this.right.classList.toggle('open', !!u || (!this.touch && !!this.hover && !!g.unitAt(this.hover.x, this.hover.y)));
    if (!u) {
      this.right.append(h('div', { class: 'ptitle' }, 'No selection'), h('div', { class: 'muted small' }, 'Select one of your units to see its relic, statuses and abilities.'));
    } else {
      this.right.append(h('div', { class: 'ptitle' }, h('span', null, 'Selected'), h('button', { class: 'close', title: 'Close (Esc)', onclick: () => this.cancel() }, '×')));
      this.right.append(this.unitPanel(u, true));
      const abs = g.abilitiesOf(u);
      if (abs.length) {
        const list = h('div', { class: 'runes' });
        let n = 0;
        abs.forEach(id => {
          const a = g.ability(id);
          if (!a) return;
          const tip = [a.description ?? '', `Range ${a.range.min === a.range.max ? a.range.max : a.range.min + '-' + a.range.max}${a.area ? `, area ${a.area.size}` : ''}`,
            ...a.effects.map(e => effectText(this.content, e)), a.cooldown ? `Cooldown ${a.cooldown} turns` : ''].filter(Boolean).join('\n');
          if (a.passive) {
            list.append(h('div', { class: 'rune passive', title: tip }, h('span', { class: 'slotno' }, '◇'), h('span', { class: 'an' }, a.name, h('small', null, a.description ?? '')), h('span', { class: 'meta' }, 'Passive')));
            return;
          }
          const cd = u.cooldowns[id] ?? 0;
          const usable = u.team === g.current && this.canActSoft() && g.canUse(u, id);
          const active = this.mode.kind === 'ability' && this.mode.ability === id;
          const idx = ++n;
          list.append(h('button', {
            class: 'rune' + (active ? ' active' : ''), disabled: !usable, title: tip,
            onclick: () => { if (!this.canAct()) return; this.mode = active ? { kind: 'move' } : { kind: 'ability', ability: id }; this.refresh(); },
          }, h('span', { class: 'slotno' }, String(idx)), h('span', { class: 'an' }, a.name, h('small', null, a.description ?? '')),
            h('span', { class: 'meta' }, `${a.apCost} AP${cd > 0 ? ` · cd ${cd}` : a.cooldown ? ` · cd ${a.cooldown}` : ''}`)));
        });
        this.right.append(h('div', { class: 'ptitle sub' }, 'Abilities'), list);
      }
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
    if (occ && occ.uid !== this.selected) { this.hoverBox.append(h('div', { class: 'ptitle sub' }, 'Under cursor'), this.unitPanel(occ, false)); }
    const pv = this.renderer.overlay.previews;
    if (pv.size) {
      const box = h('div', { class: 'preview' }, h('b', null, 'Predicted'));
      for (const [uid, p] of pv) box.append(h('div', { style: `color:${p.color}` }, `${this.uname(uid)}: ${p.text}`));
      this.hoverBox.append(box);
    }
    this.hoverBox.append(h('div', { class: 'tileinfo' },
      h('b', null, terr?.name ?? t.terrain), ` · height ${t.height} · move ${terr?.moveCost} · def +${terr?.defense ?? 0}`,
      g.map.wells?.some(w => w.x === hv.x && w.y === hv.y) ? ` · ${this.L('essence')} well` : ''));
  }
}

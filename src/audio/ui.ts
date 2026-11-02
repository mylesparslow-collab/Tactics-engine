// Interface sounds, delegated at document level so no screen needs to wire its own handlers.
// Opt a control out with data-nosound; give it data-snd="confirm|back|close|open|select|toggle|none" to override the guess.
import { play, running } from './engine';

const INTERACTIVE = 'button, [role="button"], a[href], .mitem, .card-tile, .cl-tile, .scen, .htab, summary, input[type="range"], select';
let lastHover: Element | null = null;

function kindOf(el: HTMLElement): string {
  const d = el.dataset.snd;
  if (d) return d;
  const cls = el.className?.toString() ?? '';
  const title = (el.getAttribute('title') ?? '').toLowerCase();
  if (/\bback\b/.test(cls) || title.startsWith('back') || title.startsWith('previous') || title.startsWith('next map')) return 'back';
  if (/close/.test(cls) || title.startsWith('close')) return 'close';
  if (/endturn/.test(cls) || el.id === 'endturn') return 'none'; // the turn-end cue is played by the game
  if (/btn-gold|bs-deploy/.test(cls)) return 'confirm';
  if (/htab|tab\b|cl-fac|toggle|seg/.test(cls) || el.closest('.seg')) return 'select';
  if (/info|menubtn|iconbtn|logtoggle|htoggle/.test(cls)) return 'open';
  return 'click';
}

function target(e: Event): HTMLElement | null {
  const el = (e.target as Element | null)?.closest?.(INTERACTIVE) as HTMLElement | null;
  if (!el || el.hasAttribute('data-nosound') || (el as HTMLButtonElement).disabled) return null;
  return el;
}

export function installUiSounds() {
  const canHover = typeof matchMedia === 'function' && matchMedia('(hover: hover)').matches;
  if (canHover) {
    document.addEventListener('pointerover', e => {
      if ((e as PointerEvent).pointerType !== 'mouse') return;
      const el = target(e);
      if (!el || el === lastHover || (e.relatedTarget && el.contains(e.relatedTarget as Node))) return;
      lastHover = el;
      if (running()) play('ui_hover', { volume: 0.35, minGap: 55, jitter: 0.08 });
    }, true);
    document.addEventListener('pointerout', e => { if (lastHover && !lastHover.contains((e as PointerEvent).relatedTarget as Node)) lastHover = null; }, true);
  }
  document.addEventListener('click', e => {
    const el = target(e);
    if (!el || el.tagName === 'INPUT' || el.tagName === 'SELECT') return;
    const k = kindOf(el);
    if (k === 'none') return;
    play(`ui_${k}`, { volume: k === 'confirm' ? 0.65 : 0.55, minGap: 40, jitter: 0.05 });
  }, true);
}

/** Error/refusal blip for actions the game rejects (e.g. an illegal move). */
export function playError() { play('ui_error', { volume: 0.5, minGap: 150 }); }
export function playSelect() { play('ui_select', { volume: 0.5, minGap: 60 }); }

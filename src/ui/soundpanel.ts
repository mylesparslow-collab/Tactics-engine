// Volume panel: master / music / sfx / ambience sliders and a mute switch, anchored to a button.
import './soundpanel.css';
import { getSettings, isMuted, onSettingsChange, setMuted, setVolume, type Channel } from '../audio/engine';
import { play } from '../audio/engine';
import { glyph } from './art';
import { h } from './dom';

const ROWS: [Channel, string][] = [['master', 'Master'], ['music', 'Music'], ['sfx', 'Effects'], ['ambience', 'Ambience']];
let open: { el: HTMLElement; close: () => void } | null = null;

export function openSoundPanel(anchor: HTMLElement) {
  if (open) { const wasSame = open.el.dataset.anchor === (anchor.id || 'a'); open.close(); if (wasSame) return; }
  const el = h('div', { class: 'sndpanel', role: 'dialog', 'aria-label': 'Sound settings', 'data-anchor': anchor.id || 'a' });
  const s = getSettings();
  const outs = new Map<Channel, HTMLOutputElement>();
  const sliders = new Map<Channel, HTMLInputElement>();
  el.append(h('h3', null, 'Sound'));
  for (const [ch, label] of ROWS) {
    const input = h('input', { type: 'range', min: '0', max: '100', step: '1', value: String(Math.round(s[ch] * 100)), id: `snd-${ch}`, 'aria-label': `${label} volume`, 'data-nosound': '' });
    const out = h('output', { for: `snd-${ch}` }, String(Math.round(s[ch] * 100)));
    const paint = () => input.style.setProperty('--p', `${input.value}%`);
    paint();
    input.oninput = () => { paint(); out.textContent = input.value; setVolume(ch, Number(input.value) / 100); };
    // a short sample on release so the level can be judged
    input.onchange = () => { if (ch === 'sfx' || ch === 'master') play('hit_flesh', { volume: 0.7, minGap: 0 }); };
    outs.set(ch, out); sliders.set(ch, input);
    el.append(h('div', { class: 'snd-row' + (ch === 'master' ? ' master' : '') }, h('label', { for: `snd-${ch}` }, label), input, out));
  }
  const mute = h('input', { type: 'checkbox', id: 'snd-mute', 'data-nosound': '' }) as HTMLInputElement;
  mute.checked = isMuted();
  mute.onchange = () => setMuted(mute.checked);
  el.append(h('label', { class: 'snd-mute', for: 'snd-mute' }, mute, 'Mute all'), h('div', { class: 'snd-hint' }, 'Press M to mute or unmute.'),
    h('details', { class: 'snd-credits' }, h('summary', null, 'Credits'), h('p', null, 'Sounds by Kenney (CC0), Meta Open Sound (CC0 piano) and the "Oculus Audio Pack 01" by Oculus VR, LLC (CC BY 4.0, developers.meta.com/vr/downloads/package/oculus-audio-pack-1). Edited and arranged for Brinewake; no synthesised sounds.')));
  const sync = (st = getSettings()) => { el.classList.toggle('muted', st.muted); mute.checked = st.muted; for (const [ch] of ROWS) { const i = sliders.get(ch)!; const v = String(Math.round(st[ch] * 100)); if (i.value !== v) { i.value = v; i.style.setProperty('--p', `${v}%`); outs.get(ch)!.textContent = v; } } };
  sync();
  const off = onSettingsChange(sync);

  document.body.append(el);
  const place = () => {
    const r = anchor.getBoundingClientRect(), w = el.offsetWidth, hh = el.offsetHeight;
    const left = Math.max(8, Math.min(innerWidth - w - 8, r.right - w));
    const below = r.bottom + 8 + hh < innerHeight;
    el.style.left = `${left}px`;
    el.style.top = `${below ? r.bottom + 8 : Math.max(8, r.top - 8 - hh)}px`;
  };
  place();
  const onDown = (e: PointerEvent) => { if (!el.contains(e.target as Node) && !anchor.contains(e.target as Node)) close(); };
  const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') { e.stopPropagation(); close(); } };
  const close = () => { off(); el.remove(); document.removeEventListener('pointerdown', onDown, true); document.removeEventListener('keydown', onKey, true); removeEventListener('resize', place); open = null; };
  document.addEventListener('pointerdown', onDown, true);
  document.addEventListener('keydown', onKey, true);
  addEventListener('resize', place);
  open = { el, close };
}

/** A small speaker button for screens without a HUD (the title screen). */
export function soundButton(cls = 'menu-sound'): HTMLButtonElement {
  const b = h('button', { class: `iconbtn ${cls} soundbtn`, title: 'Sound settings', 'data-snd': 'open' }) as HTMLButtonElement;
  const draw = () => { b.replaceChildren(glyph(isMuted() ? 'mute' : 'sound')); };
  draw();
  b.onclick = () => openSoundPanel(b);
  const off = onSettingsChange(() => { if (!b.isConnected) { off(); return; } draw(); });
  return b;
}

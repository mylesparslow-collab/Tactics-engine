// Dev page (cards.html): every relic card in each size, for reviewing the card face. ?ids=a,b&size=full
import './style.css';
import { loadBundledContent } from './engine/bundled';
import { installArt } from './ui/art';
import { buildCard, type CardSize } from './ui/cards';
import { h } from './ui/dom';

const content = loadBundledContent();
installArt();
const q = new URLSearchParams(location.search);
const ids = q.get('ids')?.split(',') ?? [...Object.keys(content.units).filter(id => id !== 'keystone'), ...Object.keys(content.spells), ...Object.keys(content.equipment)];
const sizes = (q.get('size')?.split(',') ?? ['full']) as CardSize[];
const root = document.getElementById('app')!;
root.style.cssText = 'display:flex;flex-wrap:wrap;gap:24px;padding:24px;align-items:flex-start;--cw:' + (q.get('w') ?? '300') + 'px';
for (const size of sizes) for (const id of ids) root.append(h('div', { class: 'gallery-cell', 'data-id': id }, buildCard(id, { size, content })));

// Original UI art for EBB, drawn as inline SVG: brass frames (9-slice), faction crests, title key art, and UI glyphs.
// Everything here is static vector art; nothing uses filters on animated layers (keeps mobile fast).

let uid = 0;
const nid = (p: string) => `${p}${++uid}`;

const enc = (svg: string) => `url("data:image/svg+xml,${encodeURIComponent(svg.replace(/\s+/g, ' '))}")`;

// ---------------------------------------------------------------- frames

/** Brass corner plate with rivet and salt bloom, drawn for the top-left corner of a `s`-sized frame. */
function corner(s: number, big: boolean) {
  const k = big ? 1 : 0.62;
  const a = 40 * k, b = 12 * k;
  return `<path d="M3 3 H${a} L${a - 7 * k} ${10 * k} H${b + 6} Q${b} ${b} ${b} ${b + 6} V${a - 7 * k} L3 ${a} Z" fill="url(#bz)" stroke="#120b04" stroke-width="1.2"/>
    <path d="M6 6 H${a - 4 * k} M6 6 V${a - 4 * k}" stroke="#fff3c8" stroke-opacity=".55" stroke-width="1"/>
    <circle cx="${15 * k}" cy="${15 * k}" r="${4.2 * k}" fill="url(#rv)" stroke="#2a1a06" stroke-width=".8"/>
    <circle cx="${13.8 * k}" cy="${13.8 * k}" r="${1.3 * k}" fill="#fff8dc"/>
    <g fill="#f4f1e8" opacity=".75"><path d="M${4 * k} ${a + 3} l2 -4 l2 4 z"/><path d="M${a + 2} ${4 * k} l3 -1 l-1 4 z"/><circle cx="${a - 1}" cy="${13 * k}" r=".9"/><circle cx="${12 * k}" cy="${a + 6 * k}" r=".8"/></g>`;
}

function frameSvg(s: number, big: boolean) {
  const c = corner(s, big);
  const band = big ? 6 : 4;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${s}" height="${s}" viewBox="0 0 ${s} ${s}">
  <defs>
    <linearGradient id="bz" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f6e1a3"/><stop offset=".35" stop-color="#c99a4b"/><stop offset=".6" stop-color="#7a5620"/><stop offset="1" stop-color="#d3ac5e"/></linearGradient>
    <linearGradient id="bv" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e9cc84"/><stop offset=".5" stop-color="#a77a2d"/><stop offset="1" stop-color="#5e4213"/></linearGradient>
    <radialGradient id="rv" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#fff2c0"/><stop offset=".5" stop-color="#c99a4b"/><stop offset="1" stop-color="#4a3310"/></radialGradient>
  </defs>
  <rect x="1" y="1" width="${s - 2}" height="${s - 2}" rx="5" fill="none" stroke="#0a0603" stroke-width="2"/>
  <rect x="${2 + band / 2}" y="${2 + band / 2}" width="${s - 4 - band}" height="${s - 4 - band}" rx="4" fill="none" stroke="url(#bv)" stroke-width="${band}"/>
  <rect x="${2.5 + band}" y="${2.5 + band}" width="${s - 5 - band * 2}" height="${s - 5 - band * 2}" rx="2" fill="none" stroke="#120b04" stroke-width="1.4"/>
  <rect x="${4.5 + band}" y="${4.5 + band}" width="${s - 9 - band * 2}" height="${s - 9 - band * 2}" rx="1.5" fill="none" stroke="#e8c57a" stroke-opacity=".28" stroke-width="1"/>
  <g>${c}</g>
  <g transform="translate(${s} 0) scale(-1 1)">${c}</g>
  <g transform="translate(0 ${s}) scale(1 -1)">${c}</g>
  <g transform="translate(${s} ${s}) scale(-1 -1)">${c}</g>
</svg>`;
}

/** Thin plate frame for buttons and small chips. */
function plateSvg() {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
  <defs><linearGradient id="p" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f0d690"/><stop offset=".45" stop-color="#b48838"/><stop offset=".55" stop-color="#83601f"/><stop offset="1" stop-color="#d8b25f"/></linearGradient></defs>
  <rect x=".5" y=".5" width="47" height="47" rx="6" fill="none" stroke="#0a0603"/>
  <rect x="2" y="2" width="44" height="44" rx="5" fill="none" stroke="url(#p)" stroke-width="3"/>
  <rect x="4.5" y="4.5" width="39" height="39" rx="3" fill="none" stroke="#120b04"/>
  <rect x="5.5" y="5.5" width="37" height="37" rx="2.5" fill="none" stroke="#ffe7a6" stroke-opacity=".18"/>
</svg>`;
}

/** Paper grain (static) used under chart panels. */
function grainSvg(light: boolean) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="220" height="220"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 ${light ? '.35 0 0 0 0 .25 0 0 0 0 .1' : '.8 0 0 0 0 .75 0 0 0 0 .6'} 0 0 0 ${light ? '.16' : '.07'} 0"/></filter><rect width="220" height="220" filter="url(#n)"/></svg>`;
}

/** Sea-chart grid with depth soundings, for dark panels. */
function chartSvg() {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="160" height="160"><g stroke="#7fb3c8" stroke-opacity=".07" fill="none"><path d="M0 .5 H160 M.5 0 V160"/><path d="M0 80.5 H160 M80.5 0 V160" stroke-dasharray="2 4"/></g><g fill="#9fc4d0" fill-opacity=".07" font-family="serif" font-size="8" font-style="italic"><text x="22" y="40">14</text><text x="110" y="122">9</text><text x="120" y="30">22</text></g></svg>`;
}

export function installArt() {
  if (document.getElementById('ebb-art')) return;
  if (!document.getElementById('ebb-fonts')) {
    const ln = document.createElement('link');
    ln.id = 'ebb-fonts'; ln.rel = 'stylesheet';
    ln.href = 'https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700;900&family=Cinzel+Decorative:wght@700;900&family=Alegreya:ital,wght@1,400;1,500&family=Alegreya+Sans:wght@400;500;700&display=swap';
    document.head.append(ln);
  }
  const st = document.createElement('style');
  st.id = 'ebb-art';
  st.textContent = `:root{--frame-lg:${enc(frameSvg(120, true))};--frame-sm:${enc(frameSvg(72, false))};--plate:${enc(plateSvg())};--grain:${enc(grainSvg(false))};--grain-paper:${enc(grainSvg(true))};--chart:${enc(chartSvg())};}`;
  document.head.append(st);
}

// ---------------------------------------------------------------- faction crests

const SHIELD = 'M12 10 H108 V62 C108 100 84 122 60 134 C36 122 12 100 12 62 Z';

interface CrestStyle { field: [string, string]; ink: string; hi: string; glow?: string }
const CREST: Record<string, CrestStyle> = {
  salt_concord: { field: ['#5f88b4', '#1d2a3a'], ink: '#efe9dc', hi: '#ffffff' },
  hadal_court: { field: ['#3c4290', '#0c0e1e'], ink: '#9aa3c8', hi: '#3fd6c4', glow: '#3fd6c4' },
  returning_tide: { field: ['#4f8f6d', '#0f1d17'], ink: '#0d1411', hi: '#b9dcc6' },
  salvage_compact: { field: ['#bf6a3e', '#3a1a0c'], ink: '#efe6d6', hi: '#fff6e6' },
  reef_ascendant: { field: ['#ec8f7f', '#5a2420'], ink: '#f6efe6', hi: '#ffffff', glow: '#ffd2c6' },
  lanternkeepers: { field: ['#7d8791', '#22272c'], ink: '#f2c766', hi: '#fff3c4', glow: '#ffd86b' },
};

function charge(fid: string, s: CrestStyle, g: string): string {
  const ink = s.ink;
  switch (fid) {
    case 'salt_concord': {
      const links = Array.from({ length: 7 }, (_, i) => { const a = Math.PI * (1.12 + i * 0.127); return `<ellipse cx="${60 + Math.cos(a) * 38}" cy="${70 + Math.sin(a) * 38}" rx="4.2" ry="2.6" transform="rotate(${a * 180 / Math.PI + 90} ${60 + Math.cos(a) * 38} ${70 + Math.sin(a) * 38})" fill="none" stroke="${ink}" stroke-width="2"/>`; }).join('');
      return `${links}<path d="M60 30 L70 44 L70 74 L60 86 L50 74 L50 44 Z" fill="${ink}"/><path d="M60 30 L60 86 M50 44 L60 50 L70 44" stroke="#5f7d9a" stroke-width="1.6" fill="none"/>
        <path d="M30 112 V104 H42 V96 H54 V90 H66 V96 H78 V104 H90 V112" fill="none" stroke="${ink}" stroke-width="4" stroke-linejoin="miter"/>`;
    }
    case 'hadal_court':
      return `<circle cx="60" cy="86" r="22" fill="url(#${g}gl)"/>
        <path d="M60 28 C42 28 38 46 38 62 C38 76 32 84 28 92 H92 C88 84 82 76 82 62 C82 46 78 28 60 28 Z" fill="${ink}" stroke="#14172e" stroke-width="2"/>
        <path d="M60 30 L64 44 L57 54 L63 66 L58 78" fill="none" stroke="#14172e" stroke-width="2.6"/>
        <rect x="55" y="20" width="10" height="9" rx="2" fill="${ink}"/><circle cx="60" cy="96" r="5.5" fill="${s.hi}"/><circle cx="60" cy="96" r="2.2" fill="#e8fffb"/>`;
    case 'returning_tide':
      return `<path d="M60 22 C60 22 47 40 47 50 A13 13 0 0 0 73 50 C73 40 60 22 60 22 Z" fill="${ink}" stroke="${s.hi}" stroke-width="1.6"/>
        <path d="M54 34 Q52 42 53 48" stroke="${s.hi}" stroke-width="1.5" fill="none" opacity=".7"/>
        <path d="M50 118 L54 80 H66 L70 118 Z" fill="${ink}" stroke="${s.hi}" stroke-width="1.6"/><rect x="51" y="70" width="18" height="10" fill="${ink}" stroke="${s.hi}" stroke-width="1.6"/>
        <path d="M48 70 L60 62 L72 70 Z" fill="${ink}" stroke="${s.hi}" stroke-width="1.6"/><path d="M52 92 H68 M51 104 H69" stroke="${s.hi}" stroke-width="1.2" opacity=".6"/>`;
    case 'salvage_compact': {
      const ring = Array.from({ length: 12 }, (_, i) => { const a = i / 12 * Math.PI * 2; return `<circle cx="${60 + Math.cos(a) * 34}" cy="${68 + Math.sin(a) * 34}" r="3.4" fill="${ink}"/>`; }).join('');
      return `<circle cx="60" cy="68" r="34" fill="none" stroke="${ink}" stroke-width="2" opacity=".55"/>${ring}
        <path d="M36 102 L82 38" stroke="${ink}" stroke-width="5" stroke-linecap="round"/><path d="M82 38 C92 30 98 44 88 50" fill="none" stroke="${ink}" stroke-width="5" stroke-linecap="round"/>
        <path d="M84 102 L40 42" stroke="${ink}" stroke-width="3.5" stroke-linecap="round"/>
        <g transform="translate(40 42) rotate(-36)"><rect x="-8" y="-12" width="16" height="20" rx="3" fill="${ink}" stroke="#3a1a0c" stroke-width="1.5"/><rect x="-4" y="-7" width="8" height="10" fill="#ffcf6b"/><path d="M-6 -12 Q0 -20 6 -12" fill="none" stroke="${ink}" stroke-width="2"/></g>`;
    }
    case 'reef_ascendant': {
      const polyps = Array.from({ length: 10 }, (_, i) => { const a = i / 10 * Math.PI * 2 - Math.PI / 2, x = 60 + Math.cos(a) * 36, y = 70 + Math.sin(a) * 36;
        return `<circle cx="${x}" cy="${y}" r="5.5" fill="${ink}"/><circle cx="${x}" cy="${y}" r="2.2" fill="#c45a4c"/><path d="M${x + Math.cos(a) * 5} ${y + Math.sin(a) * 5} l${Math.cos(a - .5) * 5} ${Math.sin(a - .5) * 5} M${x + Math.cos(a) * 5} ${y + Math.sin(a) * 5} l${Math.cos(a + .5) * 5} ${Math.sin(a + .5) * 5}" stroke="${ink}" stroke-width="1.6"/>`; }).join('');
      return `${polyps}<path d="M60 26 C66 50 70 80 72 108 H48 C50 80 54 50 60 26 Z" fill="${ink}" stroke="#7a2e26" stroke-width="1.5"/>
        <path d="M60 34 V106 M55 60 C54 78 52 92 52 106 M65 60 C66 78 68 92 68 106" stroke="#c45a4c" stroke-width="1.4" fill="none"/>`;
    }
    case 'lanternkeepers': {
      const lenses = Array.from({ length: 7 }, (_, i) => { const a = i / 7 * Math.PI * 2 - Math.PI / 2, x = 60 + Math.cos(a) * 36, y = 70 + Math.sin(a) * 36;
        return `<circle cx="${x}" cy="${y}" r="7" fill="#2b3036" stroke="${ink}" stroke-width="2"/><circle cx="${x - 2}" cy="${y - 2}" r="2.2" fill="${s.hi}" opacity=".85"/>`; }).join('');
      return `<circle cx="60" cy="70" r="26" fill="url(#${g}gl)"/>${lenses}
        <path d="M50 58 H70 L72 86 H48 Z" fill="none" stroke="${ink}" stroke-width="3"/><path d="M48 58 Q60 44 72 58" fill="${ink}"/><rect x="46" y="86" width="28" height="6" rx="1.5" fill="${ink}"/>
        <path d="M60 64 C55 70 56 78 60 82 C64 78 65 70 60 64 Z" fill="${s.hi}"/><circle cx="60" cy="40" r="3" fill="${ink}"/>`;
    }
  }
  return `<path d="M60 40 L76 70 L60 100 L44 70 Z" fill="${ink}"/>`;
}

/** A faction crest on a brass-rimmed heater shield. Falls back to a neutral crest for unknown ids. */
export function crestSvg(fid: string | undefined, color?: string): string {
  const s = (fid && CREST[fid]) || { field: [color ?? '#5a6f7a', '#151b22'] as [string, string], ink: '#e8e0cc', hi: '#ffffff' };
  const g = nid('cr');
  return `<svg viewBox="0 0 120 140" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <defs>
    <linearGradient id="${g}rim" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f6e1a3"/><stop offset=".4" stop-color="#c99a4b"/><stop offset=".7" stop-color="#6e4c18"/><stop offset="1" stop-color="#d9b46a"/></linearGradient>
    <radialGradient id="${g}f" cx=".4" cy=".3" r=".85"><stop offset="0" stop-color="${s.field[0]}"/><stop offset="1" stop-color="${s.field[1]}"/></radialGradient>
    <radialGradient id="${g}gl"><stop offset="0" stop-color="${s.glow ?? s.hi}" stop-opacity=".85"/><stop offset="1" stop-color="${s.glow ?? s.hi}" stop-opacity="0"/></radialGradient>
    <linearGradient id="${g}sh" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".22"/><stop offset=".45" stop-color="#fff" stop-opacity="0"/></linearGradient>
    <clipPath id="${g}c"><path d="${SHIELD}"/></clipPath>
  </defs>
  <path d="${SHIELD}" transform="translate(0 3)" fill="#000" opacity=".45"/>
  <path d="${SHIELD}" fill="url(#${g}f)"/>
  <g clip-path="url(#${g}c)">
    <g transform="translate(1.5 2)" opacity=".5" style="mix-blend-mode:multiply">${charge(fid ?? '', { ...s, ink: '#000', hi: '#000' }, g + 'x')}</g>
    ${charge(fid ?? '', s, g)}
    <path d="M12 10 H108 V70 C80 60 40 60 12 70 Z" fill="url(#${g}sh)"/>
  </g>
  <path d="${SHIELD}" fill="none" stroke="#0a0603" stroke-width="9"/>
  <path d="${SHIELD}" fill="none" stroke="url(#${g}rim)" stroke-width="6"/>
  <path d="${SHIELD}" fill="none" stroke="#fff3c8" stroke-opacity=".35" stroke-width="1" transform="translate(60 72) scale(.93) translate(-60 -72)"/>
  <circle cx="16" cy="14" r="3" fill="#f0d58e" stroke="#3a2808"/><circle cx="104" cy="14" r="3" fill="#f0d58e" stroke="#3a2808"/>
</svg>`;
}

/** Best guess at which faction a team fields (most common faction among its units and cards). */
export function teamFaction(content: { units: Record<string, { faction?: string }>; spells: Record<string, { faction?: string }>; equipment: Record<string, { faction?: string }> }, ids: string[]): string | undefined {
  const n = new Map<string, number>();
  for (const id of ids) { const f = (content.units[id] ?? content.spells[id] ?? content.equipment[id])?.faction; if (f) n.set(f, (n.get(f) ?? 0) + 1); }
  let best: string | undefined, bn = 0;
  for (const [f, c] of n) if (c > bn) { best = f; bn = c; }
  return best;
}

// ---------------------------------------------------------------- title key art

/** The drained seabed under the lifted sea, with a working lighthouse. Animated with SMIL/CSS transforms only. */
export function keyArtSvg(): string {
  const waves = Array.from({ length: 7 }, (_, i) => {
    const y = 30 + i * 22, a = 6 + (i % 3) * 3, w = 140 + i * 20;
    let d = `M-200 ${y}`;
    for (let x = -200; x <= 1900; x += w) d += ` q${w / 4} ${-a} ${w / 2} 0 t${w / 2} 0`;
    return `<path d="${d}" stroke="#bfe9e2" stroke-opacity="${(0.16 - i * 0.018).toFixed(3)}" stroke-width="${2 - i * 0.18}" fill="none"/>`;
  }).join('');
  const ribs = (x: number, y: number, s: number, n: number) => Array.from({ length: n }, (_, i) =>
    `<path d="M${x + i * 16 * s} ${y} q${-10 * s} ${-60 * s} ${8 * s} ${-90 * s + i * 6 * s}" stroke="#2a2428" stroke-width="${5 * s}" fill="none" stroke-linecap="round"/>`).join('');
  const coral = (x: number, y: number, s: number, flip = 1) => `<g transform="translate(${x} ${y}) scale(${s * flip} ${s})" stroke="#120f16" stroke-linecap="round" fill="none">
    <path d="M0 0 C-4 -40 -20 -60 -36 -90 M-10 -36 C4 -60 12 -70 18 -96 M-22 -64 C-40 -74 -50 -80 -58 -98 M8 -70 C24 -80 30 -90 40 -100" stroke-width="7"/>
    <path d="M-36 -90 l-6 -14 M18 -96 l2 -12 M-58 -98 l-8 -8 M40 -100 l8 -8" stroke-width="4"/></g>`;
  return `<svg class="keyart" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <defs>
    <linearGradient id="ka-sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#14202a"/><stop offset=".16" stop-color="#2a3a44"/><stop offset=".3" stop-color="#3e3a52"/>
      <stop offset=".5" stop-color="#6a5c72"/><stop offset=".62" stop-color="#8f8a7c"/><stop offset=".7" stop-color="#9aa182"/></linearGradient>
    <linearGradient id="ka-sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b2a33" stop-opacity=".95"/><stop offset=".7" stop-color="#1e4650" stop-opacity=".35"/><stop offset="1" stop-color="#3f6d70" stop-opacity="0"/></linearGradient>
    <radialGradient id="ka-haze" cx=".62" cy=".62" r=".5"><stop offset="0" stop-color="#f1edcf" stop-opacity=".55"/><stop offset="1" stop-color="#f1edcf" stop-opacity="0"/></radialGradient>
    <linearGradient id="ka-floor" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8d887a"/><stop offset=".3" stop-color="#6b665e"/><stop offset="1" stop-color="#2a2629"/></linearGradient>
    <linearGradient id="ka-rim" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5b5466"/><stop offset="1" stop-color="#3d3846"/></linearGradient>
    <linearGradient id="ka-rim2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3f3848"/><stop offset="1" stop-color="#29232f"/></linearGradient>
    <linearGradient id="ka-beam" x1="1" y1="0" x2="0" y2="0"><stop offset="0" stop-color="#ffe7a0" stop-opacity=".55"/><stop offset=".5" stop-color="#ffe7a0" stop-opacity=".14"/><stop offset="1" stop-color="#ffe7a0" stop-opacity="0"/></linearGradient>
    <radialGradient id="ka-lamp"><stop offset="0" stop-color="#fff8dc"/><stop offset=".2" stop-color="#ffd86b" stop-opacity=".9"/><stop offset="1" stop-color="#ffb84a" stop-opacity="0"/></radialGradient>
    <radialGradient id="ka-mist" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#d9d6c8" stop-opacity=".32"/><stop offset="1" stop-color="#d9d6c8" stop-opacity="0"/></radialGradient>
    <linearGradient id="ka-tower" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#e9e4d4"/><stop offset=".55" stop-color="#b9b2a0"/><stop offset="1" stop-color="#6d6758"/></linearGradient>
    <linearGradient id="ka-shaft" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#d8fff6" stop-opacity=".22"/><stop offset=".6" stop-color="#d8fff6" stop-opacity=".07"/><stop offset="1" stop-color="#d8fff6" stop-opacity="0"/></linearGradient>
    <radialGradient id="ka-salt"><stop offset="0" stop-color="#efeadb" stop-opacity=".38"/><stop offset=".6" stop-color="#efeadb" stop-opacity=".12"/><stop offset="1" stop-color="#efeadb" stop-opacity="0"/></radialGradient>
    <linearGradient id="ka-rock" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#4a4352"/><stop offset=".5" stop-color="#2e2833"/><stop offset="1" stop-color="#1c1820"/></linearGradient>
    <radialGradient id="ka-vig" cx=".5" cy=".45" r=".75"><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#05040a" stop-opacity=".85"/></radialGradient>
  </defs>
  <rect width="1600" height="900" fill="url(#ka-sky)"/>
  <rect width="1600" height="260" fill="url(#ka-sea)"/>
  <g class="ka-waves">${waves}</g>
  <g fill="url(#ka-shaft)"><polygon points="300,0 360,0 560,620 420,620"/><polygon points="960,0 990,0 1080,560 1020,560"/><polygon points="1330,0 1360,0 1450,600 1400,600"/></g>
  <rect width="1600" height="900" fill="url(#ka-haze)"/>
  <path d="M0 520 L80 500 L140 512 L230 488 L300 500 L380 476 L470 498 L520 490 L560 530 L1600 530 L1600 470 L1530 480 L1460 458 L1400 474 L1330 452 L1260 476 L1200 470 L1150 500 L1100 530 L0 560 Z" fill="url(#ka-rim)" opacity=".85"/>
  <g stroke="#7a7186" stroke-opacity=".35" fill="none"><path d="M0 532 L540 512 M1110 512 L1600 496 M0 546 L520 530 M1130 522 L1600 512"/></g>
  <path d="M0 560 L60 548 L130 556 L220 540 L320 556 L420 548 L520 566 L620 560 L760 572 L900 566 L1040 574 L1180 560 L1320 566 L1440 552 L1600 560 L1600 900 L0 900 Z" fill="url(#ka-floor)"/>
  <g fill="url(#ka-salt)"><ellipse cx="420" cy="640" rx="320" ry="34"/><ellipse cx="900" cy="606" rx="240" ry="16"/><ellipse cx="760" cy="730" rx="420" ry="54"/><ellipse cx="1350" cy="690" rx="260" ry="30"/></g>
  <g stroke="#3a3530" stroke-opacity=".5" fill="none" stroke-width="1.4"><path d="M200 660 l60 -10 l40 18 l70 -6 M610 700 l50 14 l40 -12 l80 10 M980 640 l40 10 l60 -8 M340 760 l90 -14 l60 22"/></g>
  <g transform="translate(780 604) rotate(-6)" opacity=".85">
    <path d="M0 0 C40 -6 150 -8 230 -2 L250 -22 L262 -20 L244 4 C160 14 50 12 0 0 Z" fill="#2e282c"/>
    ${ribs(18, 2, 0.42, 9)}
    <path d="M60 -40 L64 -2 M62 -40 L40 -26" stroke="#2e282c" stroke-width="3"/>
  </g>
  <g opacity=".55">${ribs(330, 606, 0.5, 5)}</g>
  <g class="ka-mist"><ellipse cx="500" cy="590" rx="520" ry="46" fill="url(#ka-mist)"/><ellipse cx="1200" cy="610" rx="460" ry="40" fill="url(#ka-mist)"/></g>
  <g transform="translate(1188 0)">
    <path d="M-130 660 C-120 620 -90 604 -60 600 L-44 560 C-30 548 30 546 46 562 L64 600 C96 606 124 626 136 660 Z" fill="url(#ka-rock)"/>
    <path d="M-60 600 L-44 560 M46 562 L64 600 M-100 630 C-80 618 -60 616 -40 618" stroke="#5a5262" stroke-width="2" fill="none" opacity=".7"/>
    <path d="M-26 560 L-18 360 H18 L26 560 Z" fill="url(#ka-tower)"/>
    <g stroke="#6d6758" stroke-opacity=".5" stroke-width="1.2"><path d="M-25 530 H25 M-24 500 H24 M-23 470 H23 M-22 440 H22 M-21 410 H21 M-20 384 H20"/></g>
    <rect x="-5" y="450" width="10" height="16" rx="5" fill="#2b2622"/><rect x="-4" y="398" width="8" height="12" rx="4" fill="#ffd86b" opacity=".8"/>
    <rect x="-28" y="348" width="56" height="12" fill="#3b3430"/><rect x="-32" y="344" width="64" height="5" fill="#8a6a2a"/>
    <path d="M-30 344 V334 M-20 344 V334 M-10 344 V334 M10 344 V334 M20 344 V334 M30 344 V334 M-31 334 H31" stroke="#3b3430" stroke-width="1.6"/>
    <rect x="-15" y="312" width="30" height="34" fill="#2b2622"/><rect x="-11" y="316" width="22" height="26" fill="#ffe08a"/>
    <path d="M-19 312 L0 292 L19 312 Z" fill="#3b3430"/><circle cx="0" cy="288" r="3" fill="#3b3430"/>
    <g><animateTransform attributeName="transform" type="rotate" values="-9 0 329; 7 0 329; -9 0 329" dur="9s" repeatCount="indefinite"/>
      <polygon points="0,322 -1250,180 -1250,470 0,336" fill="url(#ka-beam)"/></g>
    <circle cx="0" cy="329" r="70" fill="url(#ka-lamp)"><animate attributeName="r" values="62;74;62" dur="3.2s" repeatCount="indefinite"/></circle>
  </g>
  <g transform="translate(742 676)"><circle r="18" fill="url(#ka-lamp)" opacity=".8"/><path d="M-3 0 L-4 -18 Q0 -24 4 -18 L3 0 Z M-2 -24 a3.4 3.4 0 1 1 4 0" fill="#1a1618"/><path d="M4 -16 L9 -10" stroke="#1a1618" stroke-width="1.6"/><circle cx="9.5" cy="-8" r="2.4" fill="#ffd86b"/></g>
  <path d="M0 900 L0 760 C60 740 120 760 170 790 C240 760 300 800 340 840 L380 900 Z" fill="#141017"/>
  <path d="M1600 900 L1600 740 C1540 720 1460 750 1420 780 C1360 770 1290 820 1260 860 L1240 900 Z" fill="#141017"/>
  ${coral(180, 820, 1.1)}${coral(1450, 800, 1.25, -1)}${coral(1330, 870, 0.7)}
  <rect width="1600" height="900" fill="url(#ka-vig)"/>
</svg>`;
}

// ---------------------------------------------------------------- glyphs

const GLYPH: Record<string, string> = {
  campaign: '<path d="M6 5 L14 3 L22 5 L30 3 V27 L22 29 L14 27 L6 29 Z" fill="none" stroke="currentColor" stroke-width="2"/><path d="M14 3 V27 M22 5 V29" stroke="currentColor" stroke-width="1.4" opacity=".6"/><path d="M10 20 L13 16 L17 18 L20 12 L25 10" stroke="currentColor" stroke-width="1.6" fill="none" stroke-dasharray="2 2"/><circle cx="25" cy="10" r="2" fill="currentColor"/>',
  skirmish: '<path d="M6 6 L22 22 M6 6 L6 11 M6 6 L11 6 M20 24 L24 20 M26 26 L22 22" stroke="currentColor" stroke-width="2.4" fill="none" stroke-linecap="round"/><path d="M26 6 L10 22 M26 6 L26 11 M26 6 L21 6 M12 24 L8 20 M6 26 L10 22" stroke="currentColor" stroke-width="2.4" fill="none" stroke-linecap="round"/>',
  scenarios: '<path d="M8 4 H22 L26 8 V28 H8 Z" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 12 H22 M12 17 H22 M12 22 H18" stroke="currentColor" stroke-width="1.6"/>',
  collection: '<rect x="5" y="8" width="14" height="20" rx="2" fill="none" stroke="currentColor" stroke-width="2" transform="rotate(-10 12 18)"/><rect x="13" y="5" width="14" height="20" rx="2" fill="currentColor" fill-opacity=".25" stroke="currentColor" stroke-width="2" transform="rotate(8 20 15)"/>',
  gear: '<path d="M16 4 l2.4 3.4 4-1.2 .6 4.1 4 1.3 -1.6 3.8 2.6 3.2 -3.6 2 .4 4.2 -4.2 .1 -1.8 3.8 -3.4-2.4 -3.4 2.4 -1.8-3.8 -4.2-.1 .4-4.2 -3.6-2 2.6-3.2 -1.6-3.8 4-1.3 .6-4.1 4 1.2 Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><circle cx="16" cy="16" r="4.5" fill="none" stroke="currentColor" stroke-width="2"/>',
  back: '<path d="M20 6 L10 16 L20 26" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>',
  log: '<path d="M8 5 H24 V27 H8 Z" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 11 H20 M12 16 H20 M12 21 H17" stroke="currentColor" stroke-width="1.8"/>',
  rotl: '<path d="M9 13 A9 9 0 1 1 10 22" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><path d="M4 9 L9 14 L14 9" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
  rotr: '<path d="M23 13 A9 9 0 1 0 22 22" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><path d="M28 9 L23 14 L18 9" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
  plus: '<path d="M16 7 V25 M7 16 H25" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>',
  minus: '<path d="M7 16 H25" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>',
  center: '<circle cx="16" cy="16" r="8" fill="none" stroke="currentColor" stroke-width="2.2"/><path d="M16 3 V9 M16 23 V29 M3 16 H9 M23 16 H29" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>',
  close: '<path d="M9 9 L23 23 M23 9 L9 23" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>',
  lock: '<rect x="8" y="14" width="16" height="13" rx="2" fill="currentColor"/><path d="M11 14 V10 a5 5 0 0 1 10 0 V14" fill="none" stroke="currentColor" stroke-width="2.4"/>',
  check: '<path d="M7 17 L13 23 L25 9" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/>',
  // ability glyphs
  melee: '<path d="M24 4 L28 4 L28 8 L12 24 L8 20 Z" fill="currentColor"/><path d="M6 18 L14 26 M4 28 L9 23" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/>',
  ranged: '<path d="M5 27 L25 7" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><path d="M27 5 L19 7 L25 13 Z" fill="currentColor"/><path d="M5 27 L5 21 M5 27 L11 27 M9 23 L9 18 M9 23 L14 23" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
  heal: '<path d="M13 5 H19 V13 H27 V19 H19 V27 H13 V19 H5 V13 H13 Z" fill="currentColor"/>',
  buff: '<path d="M16 4 L26 14 H20 V27 H12 V14 H6 Z" fill="currentColor"/>',
  debuff: '<circle cx="16" cy="16" r="10" fill="none" stroke="currentColor" stroke-width="2.4"/><path d="M10 13 Q16 22 22 13" fill="none" stroke="currentColor" stroke-width="2.4"/><circle cx="12" cy="11" r="1.6" fill="currentColor"/><circle cx="20" cy="11" r="1.6" fill="currentColor"/>',
  push: '<path d="M4 16 H20" stroke="currentColor" stroke-width="3" stroke-linecap="round"/><path d="M16 8 L26 16 L16 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linejoin="round"/><path d="M28 6 V26" stroke="currentColor" stroke-width="2"/>',
  move: '<path d="M8 26 C8 18 14 18 14 12 M18 24 C18 16 24 16 24 8" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="3 3"/><path d="M20 8 L24 4 L28 8" fill="none" stroke="currentColor" stroke-width="2.4"/>',
  summon: '<circle cx="16" cy="16" r="11" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="4 3"/><circle cx="16" cy="12" r="3.4" fill="currentColor"/><path d="M10 23 Q16 14 22 23 Z" fill="currentColor"/>',
  terrain: '<path d="M3 24 L11 12 L16 18 L21 10 L29 24 Z" fill="currentColor"/>',
  tide: '<path d="M16 4 C16 4 7 15 7 20 a9 9 0 0 0 18 0 C25 15 16 4 16 4 Z" fill="currentColor"/>',
  aura: '<circle cx="16" cy="16" r="4" fill="currentColor"/><circle cx="16" cy="16" r="9" fill="none" stroke="currentColor" stroke-width="1.6" opacity=".7"/><circle cx="16" cy="16" r="13.5" fill="none" stroke="currentColor" stroke-width="1.2" opacity=".4"/>',
  magic: '<path d="M16 3 L19 13 L29 16 L19 19 L16 29 L13 19 L3 16 L13 13 Z" fill="currentColor"/>',
};

export function glyph(name: string, cls = 'glyph'): SVGSVGElement {
  const t = document.createElement('template');
  t.innerHTML = `<svg class="${cls}" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">${GLYPH[name] ?? GLYPH.magic}</svg>`;
  return t.content.firstChild as SVGSVGElement;
}

/** Pick a glyph that reads as what an ability mainly does. */
export function abilityGlyph(a: { passive?: boolean; range: { max: number }; target: string; effects: { type: string; damageType?: string }[] }): string {
  if (a.passive) return 'aura';
  const t = a.effects.map(e => e.type);
  if (t.includes('damage')) return a.range.max > 1 ? (a.effects.some(e => e.damageType && !['physical', 'pierce', 'crush', 'slash'].includes(e.damageType)) ? 'magic' : 'ranged') : 'melee';
  if (t.includes('heal')) return 'heal';
  if (t.includes('push') || t.includes('pull')) return 'push';
  if (t.includes('teleport') || t.includes('swap')) return 'move';
  if (t.includes('summon')) return 'summon';
  if (t.includes('terrain')) return 'terrain';
  if (t.includes('essence')) return 'tide';
  if (t.includes('status')) return a.target === 'enemy' ? 'debuff' : 'buff';
  return 'magic';
}

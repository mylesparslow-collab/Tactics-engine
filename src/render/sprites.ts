// Unit figure drawing: frame/still art or a painted placeholder figure, plus cast shadow, rings, crown, HP bar, status pips.
import type { UnitDef } from '../engine/types';
import type { Frame } from './anim';
import { mix, rgba, shade } from './iso';

export interface SpriteOpts {
  def: UnitDef;
  hero: boolean;
  teamColor: string;
  factionColor?: string;
  x: number; y: number;          // screen position of the tile-top centre (feet)
  alpha: number;
  dim: boolean;
  flash: number;                  // 0..1 white hit flash
  hp: number; maxHp: number;
  ap?: number; maxAp?: number;   // undefined for structures
  statuses: { id: string; name: string }[];
  selected: boolean;
  hovered: boolean;
  scale: number;                  // pop-in scale
  time: number;
  frame: Frame | null;
  facing: 1 | -1;                 // 1 = lower-right (native), -1 = mirrored
  flying?: boolean;               // hovering: its cast shadow detaches from the feet to show height
  squash: number;                 // vertical stretch factor (breathing / landing)
  tilt: number;                   // radians, death tilt
  lift: number;                   // px raised above the feet (hops)
  glow: number;                   // 0..1 caster glow
  lampGlow?: number;              // structures: 0..1 lamp intensity
  reduced: boolean;
}

export function statusColor(id: string) {
  let h = 0;
  for (const ch of id) h = (h * 31 + ch.charCodeAt(0)) % 360;
  return `hsl(${h},70%,55%)`;
}

/** Height of the drawn figure in world px (for bars, picking and crown placement). */
export function figureHeight(o: { frame: Frame | null; def: UnitDef }) {
  if (o.frame) return o.frame.sh * o.frame.scale * (o.frame.ay / o.frame.sh);
  return o.def.structure ? 120 : 92;
}

function placeholderFigure(ctx: CanvasRenderingContext2D, o: SpriteOpts) {
  const def = o.def, base = def.sprite.color ?? o.factionColor ?? o.teamColor;
  const fill = o.dim ? shade(base, 0.6) : base;
  const H = def.structure ? 120 : 92;
  const light = mix(fill, '#fff6e0', 0.35), dark = shade(fill, 0.55);
  if (def.structure) {
    // a stranded lighthouse: tapered tower, gallery, lamp
    const g = ctx.createLinearGradient(-18, 0, 18, 0);
    g.addColorStop(0, light); g.addColorStop(0.45, fill); g.addColorStop(1, dark);
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.moveTo(-16, 0); ctx.lineTo(-11, -H + 26); ctx.lineTo(11, -H + 26); ctx.lineTo(16, 0); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = 'rgba(10,10,14,0.8)'; ctx.lineWidth = 1.5; ctx.stroke();
    for (let i = 1; i < 4; i++) { ctx.fillStyle = 'rgba(0,0,0,0.18)'; ctx.fillRect(-14 + i * 1.2, -i * 22, 28 - i * 2.4, 3); }
    ctx.fillStyle = shade('#7d8791', 0.9); ctx.fillRect(-15, -H + 22, 30, 6);
    ctx.fillStyle = `rgba(255,230,150,${0.5 + 0.5 * (o.lampGlow ?? 1)})`; ctx.fillRect(-8, -H + 8, 16, 14);
    ctx.fillStyle = '#2b3239'; ctx.beginPath(); ctx.moveTo(-11, -H + 8); ctx.lineTo(0, -H - 4); ctx.lineTo(11, -H + 8); ctx.closePath(); ctx.fill();
    return;
  }
  // pawn-like silhouette: base plinth, tapered body, shoulders, head, with a cloak sweep
  const g = ctx.createLinearGradient(-20, -H, 16, 0);
  g.addColorStop(0, light); g.addColorStop(0.55, fill); g.addColorStop(1, dark);
  ctx.fillStyle = g;
  ctx.beginPath();
  ctx.moveTo(-17, 0); ctx.quadraticCurveTo(-19, -14, -11, -34); ctx.lineTo(-13, -52); ctx.quadraticCurveTo(-14, -62, -6, -64);
  ctx.quadraticCurveTo(-9, -72, -3, -78); ctx.arc(0, -78, 9, Math.PI, 0, false);
  ctx.quadraticCurveTo(9, -72, 6, -64); ctx.quadraticCurveTo(14, -62, 13, -52); ctx.lineTo(11, -34); ctx.quadraticCurveTo(19, -14, 17, 0); ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = o.dim ? 'rgba(20,20,26,0.6)' : 'rgba(12,12,18,0.85)'; ctx.lineWidth = 1.6; ctx.stroke();
  // face shadow / hood
  ctx.fillStyle = 'rgba(0,0,0,0.28)'; ctx.beginPath(); ctx.ellipse(2, -76, 6, 7, 0, 0, Math.PI * 2); ctx.fill();
  // belt + emblem
  ctx.fillStyle = rgba(o.teamColor, 0.9); ctx.fillRect(-12, -40, 24, 3.5);
  ctx.fillStyle = 'rgba(255,255,255,0.1)'; ctx.beginPath(); ctx.ellipse(-6, -50, 5, 14, 0.2, 0, Math.PI * 2); ctx.fill();
  ctx.font = 'bold 13px Cinzel, Georgia, serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(0,0,0,0.6)'; ctx.strokeText(def.sprite.glyph, 0, -52);
  ctx.fillStyle = o.dim ? '#cfcfd6' : '#fff7e6'; ctx.fillText(def.sprite.glyph, 0, -52);
}

// ---------- shadows ----------
// The sprites are lit by a warm key from the upper left, so shadows fall back and to the right. A figure-local
// point (fx, fy) (fy < 0 is up) lands on the ground at (fx - SHEAR * fy, FLAT * fy).
const SHEAR = 0.62, FLAT = 0.3, SHADOW_ALPHA = 0.5;
// Flyers are drawn as if seen from below the sun: the silhouette is squashed flat onto their own tile (so the
// shadow stays tied to the tile they hold) and slides right with their hover height, so height reads at a glance.
const FLY_FLAT = 0.36, FLY_SLIDE = 0.9, FLY_ALPHA = 0.4;

/** Black silhouettes of sprite images, built once per image (cheap: one composite, no filters). */
const silhouettes = new WeakMap<object, HTMLCanvasElement>();
function silhouette(src: CanvasImageSource): HTMLCanvasElement | null {
  const hit = silhouettes.get(src as object); if (hit) return hit;
  const w = (src as HTMLImageElement).naturalWidth || (src as HTMLCanvasElement).width;
  const h = (src as HTMLImageElement).naturalHeight || (src as HTMLCanvasElement).height;
  if (!w || !h) return null;
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const x = c.getContext('2d')!;
  x.drawImage(src, 0, 0); x.globalCompositeOperation = 'source-in'; x.fillStyle = '#000'; x.fillRect(0, 0, w, h);
  silhouettes.set(src as object, c);
  return c;
}
/** A soft round contact blob, pre-rendered once instead of building a gradient per unit per frame. */
let blob: HTMLCanvasElement | null = null;
function contactBlob() {
  if (blob) return blob;
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const x = c.getContext('2d')!, g = x.createRadialGradient(32, 32, 2, 32, 32, 32);
  g.addColorStop(0, 'rgba(0,0,0,0.6)'); g.addColorStop(0.55, 'rgba(0,0,0,0.3)'); g.addColorStop(1, 'rgba(0,0,0,0)');
  x.fillStyle = g; x.fillRect(0, 0, 64, 64);
  return (blob = c);
}

/** Ground shadow for a unit. Call for every unit before drawing any figures, so shadows never darken bodies. */
export function drawUnitShadow(ctx: CanvasRenderingContext2D, o: SpriteOpts) {
  if (o.alpha <= 0.02) return;
  const { x, y } = o;
  const f = o.frame;
  // how high the figure is off its tile (flyers hover; hops and pop-ins lift briefly)
  const fade = o.flying ? Math.max(0.6, 1 - o.lift / 90) : Math.max(0.4, 1 - o.lift / 60);
  ctx.save();
  ctx.globalAlpha = o.alpha * fade;
  if (o.flying) {
    // centre the squashed body (not the empty space under it) on the tile
    ctx.translate(x + o.lift * FLY_SLIDE, y + 2);
    ctx.scale(1, FLY_FLAT);
    ctx.translate(0, figureHeight(o) * o.scale * 0.6);
    ctx.globalAlpha = o.alpha * fade * FLY_ALPHA;
  } else {
    // ambient occlusion right under the feet
    const r = (o.def.structure ? 30 : 24) * o.scale;
    ctx.drawImage(contactBlob(), x - r, y - r * 0.5, r * 2, r);
    ctx.translate(x, y);
    ctx.transform(1, 0, -SHEAR, FLAT, 0, 0);
    ctx.translate(0, -o.lift);
    ctx.globalAlpha = o.alpha * fade * SHADOW_ALPHA;
  }
  if (f) {
    const sil = silhouette(f.img.src);
    if (sil) {
      ctx.rotate(o.tilt);
      ctx.scale(o.scale * o.facing / o.squash, o.scale * o.squash);
      const kx = f.img.src instanceof HTMLImageElement ? 1 : (f.img.src as HTMLCanvasElement).width / f.img.naturalWidth;
      ctx.drawImage(sil, f.sx * kx, f.sy * kx, f.sw * kx, f.sh * kx, -f.ax * f.scale, -f.ay * f.scale, f.sw * f.scale, f.sh * f.scale);
    }
  } else { // placeholder figure: a tall soft column
    const fh = figureHeight(o);
    ctx.fillStyle = '#000';
    ctx.beginPath(); ctx.ellipse(0, -fh / 2, (o.def.structure ? 16 : 15) * o.scale, fh / 2 * o.scale, 0, 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
}

export function drawUnitSprite(ctx: CanvasRenderingContext2D, o: SpriteOpts) {
  const { x, y, def } = o;
  const fh = figureHeight(o);
  ctx.save();
  ctx.globalAlpha = o.alpha;
  // team base ring
  ctx.lineWidth = 3; ctx.strokeStyle = rgba(o.teamColor, 0.95);
  ctx.beginPath(); ctx.ellipse(x, y, 30 * o.scale, 15 * o.scale, 0, 0, Math.PI * 2); ctx.stroke();
  ctx.lineWidth = 1; ctx.strokeStyle = rgba(mix(o.teamColor, '#ffffff', 0.6), 0.6);
  ctx.beginPath(); ctx.ellipse(x, y, 26 * o.scale, 13 * o.scale, 0, 0, Math.PI * 2); ctx.stroke();
  if (o.selected || o.hovered) {
    const pulse = o.selected && !o.reduced ? 1 + Math.sin(o.time / 180) * 0.05 : 1;
    ctx.save();
    ctx.shadowColor = o.selected ? '#ffd86b' : '#ffffff'; ctx.shadowBlur = 14;
    ctx.strokeStyle = o.selected ? '#ffe08a' : 'rgba(255,255,255,0.85)'; ctx.lineWidth = o.selected ? 3 : 2;
    ctx.beginPath(); ctx.ellipse(x, y, 38 * pulse, 19 * pulse, 0, 0, Math.PI * 2); ctx.stroke();
    ctx.restore();
  }
  if (o.glow > 0) {
    const g = ctx.createRadialGradient(x, y - 30, 4, x, y - 30, 60);
    g.addColorStop(0, `rgba(190,230,255,${0.45 * o.glow})`); g.addColorStop(1, 'rgba(190,230,255,0)');
    ctx.fillStyle = g; ctx.fillRect(x - 60, y - 100, 120, 120);
    ctx.save(); ctx.translate(x, y); ctx.scale(1, 0.5); ctx.strokeStyle = `rgba(200,240,255,${0.9 * o.glow})`; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(0, 0, 44, 0, Math.PI * 2); ctx.stroke();
    ctx.setLineDash([6, 8]); ctx.lineDashOffset = -o.time / 20; ctx.beginPath(); ctx.arc(0, 0, 52, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
  }

  // figure
  ctx.translate(x, y - o.lift);
  ctx.rotate(o.tilt);
  ctx.scale(o.scale * o.facing / o.squash, o.scale * o.squash);
  const f = o.frame;
  if (f) {
    if (o.dim) ctx.globalAlpha = o.alpha * 0.6;
    const w = f.sw * f.scale, h = f.sh * f.scale;
    const kx = f.img.src instanceof HTMLImageElement ? 1 : (f.img.src as HTMLCanvasElement).width / f.img.naturalWidth;
    ctx.drawImage(f.img.src, f.sx * kx, f.sy * kx, f.sw * kx, f.sh * kx, -f.ax * f.scale, -f.ay * f.scale, w, h);
    if (o.flash > 0) {
      ctx.save(); ctx.globalCompositeOperation = 'source-atop'; ctx.fillStyle = `rgba(255,255,255,${0.85 * o.flash})`;
      ctx.fillRect(-f.ax * f.scale, -f.ay * f.scale, w, h); ctx.restore();
    }
  } else {
    placeholderFigure(ctx, o);
    if (o.flash > 0) { ctx.fillStyle = `rgba(255,255,255,${0.8 * o.flash})`; ctx.beginPath(); ctx.ellipse(0, -fh / 2, 18, fh / 2, 0, 0, Math.PI * 2); ctx.fill(); }
  }
  ctx.restore();

  // structures: lamp glow tied to HP
  if (def.structure) {
    const k = o.lampGlow ?? 1;
    const ly = y - o.lift - fh + 10;
    const g = ctx.createRadialGradient(x, ly, 2, x, ly, 40 + 30 * k);
    g.addColorStop(0, `rgba(255,228,150,${0.55 * k + 0.05})`); g.addColorStop(0.4, `rgba(255,200,100,${0.22 * k})`); g.addColorStop(1, 'rgba(255,200,100,0)');
    ctx.save(); ctx.globalAlpha = o.alpha; ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = g; ctx.fillRect(x - 80, ly - 80, 160, 160); ctx.restore();
  }

  if (o.hero) { // crown marker above the figure
    ctx.save(); ctx.globalAlpha = o.alpha;
    const cy = y - o.lift - fh - 22 + (o.reduced ? 0 : Math.sin(o.time / 500) * 1.5), cx = x;
    ctx.shadowColor = 'rgba(255,210,80,0.8)'; ctx.shadowBlur = 8;
    ctx.fillStyle = '#ffd24d'; ctx.strokeStyle = '#6b4c00'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(cx - 9, cy + 6); ctx.lineTo(cx - 10, cy - 4); ctx.lineTo(cx - 4.5, cy + 1); ctx.lineTo(cx, cy - 6); ctx.lineTo(cx + 4.5, cy + 1); ctx.lineTo(cx + 10, cy - 4); ctx.lineTo(cx + 9, cy + 6); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.restore();
  }
  // HP bar + status pips (unscaled)
  if (o.alpha > 0.05) {
    ctx.save();
    ctx.globalAlpha = o.alpha;
    const by = y - o.lift - fh - 12, bw = 44, bh = 5;
    const ratio = Math.max(0, Math.min(1, o.hp / o.maxHp));
    ctx.fillStyle = 'rgba(8,8,12,0.85)'; ctx.beginPath(); ctx.roundRect(x - bw / 2 - 1.5, by - 1.5, bw + 3, bh + 3, 2); ctx.fill();
    const hg = ctx.createLinearGradient(0, by, 0, by + bh);
    const hc = ratio > 0.5 ? '#78d96f' : ratio > 0.25 ? '#e5c24a' : '#e5584a';
    hg.addColorStop(0, mix(hc, '#ffffff', 0.3)); hg.addColorStop(1, shade(hc, 0.75));
    ctx.fillStyle = hg; ctx.fillRect(x - bw / 2, by, bw * ratio, bh);
    ctx.strokeStyle = rgba(o.teamColor, 0.9); ctx.lineWidth = 1;
    ctx.beginPath(); ctx.roundRect(x - bw / 2 - 1, by - 1, bw + 2, bh + 2, 2); ctx.stroke();
    if (o.maxAp && o.ap !== undefined) { // AP ticks under the HP bar
      const n = Math.min(Math.max(o.maxAp, o.ap), 10), gap = 1.5, ay = by + bh + 3, ah = 3;
      const tw = (bw - gap * (n - 1)) / n;
      ctx.fillStyle = 'rgba(8,8,12,0.85)'; ctx.fillRect(x - bw / 2 - 1.5, ay - 1.5, bw + 3, ah + 3);
      for (let i = 0; i < n; i++) {
        ctx.fillStyle = i < o.ap ? '#6fa2ff' : 'rgba(111,162,255,0.18)';
        ctx.fillRect(x - bw / 2 + i * (tw + gap), ay, tw, ah);
      }
    }
    const st = o.statuses.slice(0, 5);
    st.forEach((s, i) => {
      const sx = x - (st.length - 1) * 6 + i * 12, sy = by - 9;
      ctx.fillStyle = statusColor(s.id);
      ctx.beginPath(); ctx.arc(sx, sy, 5, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = 'rgba(0,0,0,0.75)'; ctx.lineWidth = 1; ctx.stroke();
      ctx.fillStyle = '#fff'; ctx.font = 'bold 7px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(s.name.charAt(0).toUpperCase(), sx, sy + 0.5);
    });
    ctx.restore();
  }
}

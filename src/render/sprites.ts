// All placeholder unit art lives here. Replace drawUnitSprite (or set sprite.image in unit defs) for real art.
import type { UnitDef } from '../engine/types';
import { rgba, shade } from './iso';

export interface SpriteOpts {
  def: UnitDef;
  hero: boolean;
  teamColor: string;
  x: number; y: number;          // screen position of the tile-top centre
  alpha: number;
  dim: boolean;
  flash: number;                  // 0..1 white hit flash
  hp: number; maxHp: number;
  statuses: { id: string; name: string }[];
  selected: boolean;
  hovered: boolean;
  scale: number;                  // pop-in scale
  time: number;
}

const images = new Map<string, HTMLImageElement>();
function getImage(src: string): HTMLImageElement | null {
  let img = images.get(src);
  if (!img) { img = new Image(); img.src = src; images.set(src, img); }
  return img.complete && img.naturalWidth > 0 ? img : null;
}

export function statusColor(id: string) {
  let h = 0;
  for (const ch of id) h = (h * 31 + ch.charCodeAt(0)) % 360;
  return `hsl(${h},70%,55%)`;
}

export const SPRITE_HEIGHT = 40;

function bodyPath(ctx: CanvasRenderingContext2D, shape: string) {
  ctx.beginPath();
  switch (shape) {
    case 'circle': ctx.arc(0, -16, 13, 0, Math.PI * 2); break;
    case 'triangle': ctx.moveTo(0, -32); ctx.lineTo(14, -2); ctx.lineTo(-14, -2); ctx.closePath(); break;
    case 'diamond': ctx.moveTo(0, -34); ctx.lineTo(13, -18); ctx.lineTo(0, -2); ctx.lineTo(-13, -18); ctx.closePath(); break;
    case 'pillar': ctx.moveTo(-8, -2); ctx.lineTo(-8, -38); ctx.lineTo(0, -44); ctx.lineTo(8, -38); ctx.lineTo(8, -2); ctx.closePath(); break;
    default: ctx.roundRect(-11, -30, 22, 28, 4); break; // square
  }
}

export function drawUnitSprite(ctx: CanvasRenderingContext2D, o: SpriteOpts) {
  const { def, x, y } = o;
  const shape = def.sprite.shape;
  const bodyH = shape === 'pillar' ? 46 : 34;
  ctx.save();
  ctx.globalAlpha = o.alpha;
  // shadow + team ring
  ctx.fillStyle = 'rgba(0,0,0,0.35)';
  ctx.beginPath(); ctx.ellipse(x, y, 17 * o.scale, 8 * o.scale, 0, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = rgba(o.teamColor, 0.95); ctx.lineWidth = 2.5;
  ctx.beginPath(); ctx.ellipse(x, y, 15 * o.scale, 7 * o.scale, 0, 0, Math.PI * 2); ctx.stroke();
  if (o.selected || o.hovered) {
    ctx.strokeStyle = o.selected ? '#ffd86b' : 'rgba(255,255,255,0.8)'; ctx.lineWidth = 2;
    const pulse = o.selected ? 1 + Math.sin(o.time / 180) * 0.06 : 1;
    ctx.beginPath(); ctx.ellipse(x, y, 22 * pulse, 11 * pulse, 0, 0, Math.PI * 2); ctx.stroke();
  }

  const img = def.sprite.image ? getImage(def.sprite.image) : null;
  ctx.translate(x, y); ctx.scale(o.scale, o.scale);
  if (img) {
    const h = 52, w = img.naturalWidth / img.naturalHeight * h;
    if (o.dim) ctx.globalAlpha = o.alpha * 0.55;
    ctx.drawImage(img, -w / 2, -h + 4, w, h);
  } else {
    const base = def.sprite.color ?? o.teamColor;
    const fill = o.dim ? shade(base, 0.5) : base;
    const g = ctx.createLinearGradient(-14, -40, 14, 0);
    g.addColorStop(0, shade(fill, 1.25)); g.addColorStop(1, shade(fill, 0.7));
    bodyPath(ctx, shape);
    ctx.fillStyle = g; ctx.fill();
    ctx.lineWidth = 2; ctx.strokeStyle = o.dim ? '#222' : '#10101a'; ctx.stroke();
    // team trim
    ctx.lineWidth = 1.5; ctx.strokeStyle = rgba(o.teamColor, 0.9);
    bodyPath(ctx, shape); ctx.stroke();
    if (o.flash > 0) { bodyPath(ctx, shape); ctx.fillStyle = `rgba(255,255,255,${0.8 * o.flash})`; ctx.fill(); }
    // glyph
    ctx.font = 'bold 14px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(0,0,0,0.7)';
    const gy = shape === 'pillar' ? -22 : shape === 'triangle' ? -12 : -16;
    ctx.strokeText(def.sprite.glyph, 0, gy);
    ctx.fillStyle = o.dim ? '#bbb' : '#fff'; ctx.fillText(def.sprite.glyph, 0, gy);
  }
  ctx.restore();

  if (o.hero) { // crown
    ctx.save(); ctx.globalAlpha = o.alpha; const cy = y - bodyH - 10;const cx = x - 24;
    ctx.fillStyle = '#ffd24d'; ctx.strokeStyle = '#6b4c00'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(cx - 8, cy + 6); ctx.lineTo(cx - 9, cy - 3); ctx.lineTo(cx - 4, cy + 1); ctx.lineTo(cx, cy - 5); ctx.lineTo(cx + 4, cy + 1); ctx.lineTo(cx + 9, cy - 3); ctx.lineTo(cx + 8, cy + 6); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.restore();
  }
  // HP bar + statuses (unscaled)
  ctx.save();
  ctx.globalAlpha = o.alpha;
  const by = y - bodyH - 12, bw = 30, bh = 5;
  const ratio = Math.max(0, Math.min(1, o.hp / o.maxHp));
  ctx.fillStyle = 'rgba(8,8,12,0.85)'; ctx.fillRect(x - bw / 2 - 1, by - 1, bw + 2, bh + 2);
  ctx.fillStyle = ratio > 0.5 ? '#6fd36f' : ratio > 0.25 ? '#e5c24a' : '#e5584a';
  ctx.fillRect(x - bw / 2, by, bw * ratio, bh);
  ctx.strokeStyle = rgba(o.teamColor, 0.9); ctx.lineWidth = 1;
  ctx.strokeRect(x - bw / 2 - 0.5, by - 0.5, bw + 1, bh + 1);
  const st = o.statuses.slice(0, 5);
  st.forEach((s, i) => {
    const sx = x - (st.length - 1) * 5.5 + i * 11, sy = by - 8;
    ctx.fillStyle = statusColor(s.id);
    ctx.beginPath(); ctx.arc(sx, sy, 4.6, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.7)'; ctx.lineWidth = 1; ctx.stroke();
    ctx.fillStyle = '#fff'; ctx.font = 'bold 7px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(s.name.charAt(0).toUpperCase(), sx, sy + 0.5);
  });
  ctx.restore();
}

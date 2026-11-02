// Unit figure drawing: frame/still art or a painted placeholder figure, plus shadow, rings, crown, HP bar, status pips.
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
  statuses: { id: string; name: string }[];
  selected: boolean;
  hovered: boolean;
  scale: number;                  // pop-in scale
  time: number;
  frame: Frame | null;
  facing: 1 | -1;                 // 1 = lower-right (native), -1 = mirrored
  flying?: boolean;               // hovering: drawn with a tighter ground shadow
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

export function drawUnitSprite(ctx: CanvasRenderingContext2D, o: SpriteOpts) {
  const { x, y, def } = o;
  const fh = figureHeight(o);
  ctx.save();
  ctx.globalAlpha = o.alpha;
  // contact shadow (soft ellipse)
  const sg = ctx.createRadialGradient(x, y, 2, x, y, 34);
  sg.addColorStop(0, 'rgba(0,0,0,0.5)'); sg.addColorStop(0.6, 'rgba(0,0,0,0.25)'); sg.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = sg; ctx.save(); ctx.translate(x, y); ctx.scale(1, 0.5); ctx.beginPath(); ctx.arc(0, 0, 34 * o.scale, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  if (o.flying) { // crisp shadow on the ground under the hovering figure; it shrinks as the figure bobs up
    const k = Math.max(0.6, 1 - Math.max(0, o.lift - 18) / 40);
    ctx.fillStyle = 'rgba(0,0,0,0.38)'; ctx.beginPath(); ctx.ellipse(x, y + 1, 19 * k * o.scale, 8.5 * k * o.scale, 0, 0, Math.PI * 2); ctx.fill();
  }
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

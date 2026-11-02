// Game sound effects: maps renderer cues and game events to banks of recorded samples.
// Units get a "body type" from their faction and role, which picks their voice, footfalls and weapon sounds.
import type { Cue } from '../render/renderer';
import type { Game } from '../engine/game';
import type { Unit } from '../engine/types';
import { banks, play, preload, whenUnlocked } from './engine';
import { duckForEnd } from './scenes';

export { installAudioUnlock, isMuted, setMuted } from './engine';

/** h human, l large (ogre/troll voices), g giant (heroes of the deep), d drowned, c creature, m machine. */
type Body = 'h' | 'l' | 'g' | 'd' | 'c' | 'm';
type Style = 'blade' | 'blunt' | 'claw' | 'siege';

const BIG_ROLE = /tank|heavy|big|bruiser|juggernaut|spiked/i;
const MACHINE_ROLE = /engine|siege|juggernaut/i;
const BLADE_ROLE = /infantry|skirmisher|commander|scout|hero|line|mobile/i;

const bodyCache = new Map<string, { body: Body; style: Style; big: boolean }>();

function profile(g: Game, u: Unit) {
  const hit = bodyCache.get(u.defId);
  if (hit) return hit;
  const d = g.def(u);
  const role = d.role ?? '';
  const fac = d.faction ?? '';
  const big = BIG_ROLE.test(role);
  let body: Body;
  if (MACHINE_ROLE.test(role)) body = 'm';
  else if (fac === 'reef_ascendant') body = 'c';
  else if (fac === 'returning_tide') body = 'd';
  else if (fac === 'hadal_court') body = d.hero ? 'g' : 'l';
  else body = big ? 'l' : 'h';
  let style: Style = body === 'm' ? 'siege' : body === 'c' ? 'claw' : body === 'l' || body === 'g' ? 'blunt' : BLADE_ROLE.test(role) ? 'blade' : 'blade';
  if (body === 'd') style = 'claw';
  const p = { body, style, big: big || body === 'l' || body === 'g' };
  bodyCache.set(u.defId, p);
  return p;
}

/** Stereo position from where the unit stands on the board (iso: left/right of the screen is x - y). */
function panOf(g: Game, u?: Unit) {
  if (!u) return 0;
  const span = (g.width + g.height) / 2;
  return Math.max(-0.7, Math.min(0.7, ((u.x - u.y) / span) * 0.9));
}

const GROUND: Record<string, string> = {
  salt_flat: 'step_salt', silt: 'step_silt', brine_pool: 'step_silt', trench: 'step_silt', kelp_husk: 'step_silt', lamp_oil: 'step_silt', brine_lake: 'step_silt',
  dead_coral: 'step_reef', living_reef: 'step_reef', calcite: 'step_reef',
  wreck: 'step_metal', bone_road: 'step_wood', salt_wall: 'step_stone', lighthouse_stone: 'step_stone',
};

const SALT = new Set(['salt', 'caustic', 'light']);
const CRUSH = new Set(['pressure', 'brine', 'impact']);

const lastVoice = { t: 0 };
function voice(kind: 'hurt' | 'die' | 'effort', body: Body, o: { volume?: number; rate?: number; pan?: number; chance?: number; minGap?: number } = {}) {
  if (Math.random() > (o.chance ?? 1)) return;
  const now = performance.now();
  if (kind !== 'die' && now - lastVoice.t < (o.minGap ?? 280)) return; // a whole squad's yelps shouldn't pile up
  const big = body === 'g' ? 0.9 : body === 'l' ? 0.95 : 1;
  if (play(`v${body}_${kind}`, { volume: (o.volume ?? 0.8), rate: (o.rate ?? 1) * big, pan: o.pan, minGap: 0, jitter: 0.07 })) lastVoice.t = now;
}

/** Map a renderer cue to sounds. */
export function playCue(c: Cue, g: Game) {
  const u = 'uid' in c ? g.unit(c.uid) : undefined;
  const pan = panOf(g, u);
  const pr = u ? profile(g, u) : null;
  switch (c.kind) {
    case 'swing': {
      const style = pr?.style ?? 'blade';
      if (style === 'siege') play('atk_siege', { volume: 0.7, pan });
      else play(style === 'blade' ? 'atk_blade' : style === 'claw' ? 'atk_claw' : 'atk_blunt', { volume: 0.55, pan, minGap: 60 });
      if (pr && pr.body !== 'm') voice('effort', pr.body, { volume: 0.5, pan, chance: pr.big ? 0.6 : 0.35, minGap: 500 });
      break;
    }
    case 'release': {
      if (pr?.body === 'm') play('atk_siege', { volume: 0.6, pan });
      else play('atk_shoot', { volume: 0.6, rate: 1.1, pan });
      break;
    }
    case 'cast': play('atk_magic', { volume: 0.45, pan, rate: 1, minGap: 120 }); break;
    case 'hit': {
      if (!u) break;
      const d = g.def(u);
      const type = c.damageType ?? '';
      if (d.structure) {
        play('hit_beacon', { volume: 0.9, pan, minGap: 60 });
        if (c.heavy || c.lethal) play('bell', { volume: 0.35, rate: 0.7, jitter: 0.02 });
        break;
      }
      const armored = g.stat(u, 'defense') >= 3;
      const body = pr!.body;
      const bank = c.lethal ? (body === 'm' ? 'hit_metal' : body === 'c' ? 'hit_squish' : 'hit_crit')
        : SALT.has(type) ? 'hit_salt' : CRUSH.has(type) ? 'hit_crush'
        : body === 'm' ? 'hit_metal' : body === 'c' ? 'hit_squish'
        : c.heavy ? 'hit_heavy' : armored ? 'hit_armor' : 'hit_flesh';
      play(bank, { volume: c.lethal ? 1 : 0.8, rate: c.lethal ? 0.9 : 1, minGap: 20, pan });
      if (armored && bank !== 'hit_armor' && body !== 'm') play('hit_armor', { volume: 0.3, pan });
      // wound voice; lethal hits get the death cry from the death cue instead
      if (!c.lethal && c.amount > 0) voice('hurt', body, { volume: 0.7, pan, chance: c.heavy ? 0.9 : 0.55 });
      break;
    }
    case 'death': {
      if (!u) break;
      if (g.def(u).structure) { play('beacon_fall', { volume: 1, jitter: 0.02, minGap: 0 }); play('bell', { volume: 0.5, rate: 0.6, jitter: 0, minGap: 0 }); break; }
      const body = pr!.body;
      voice('die', body, { volume: 0.85, pan });
      if (body !== 'm') play('hit_crush', { volume: 0.4, rate: 0.85, pan, minGap: 100 });
      break;
    }
    case 'revive': play('revive', { volume: 0.7, pan, jitter: 0.02 }); break;
    case 'deploy': {
      play('deploy', { volume: 0.6, pan });
      if (pr?.big) play('hit_crush', { volume: 0.3, rate: 0.7, pan, delay: 0.05 });
      break;
    }
    case 'step': {
      const bank = GROUND[c.terrain] ?? 'step_stone';
      const body = pr?.body ?? 'h';
      play(bank, { volume: pr?.big ? 0.3 : 0.2, rate: pr?.big ? 0.8 : 1, minGap: 70, jitter: 0.1, pan });
      if (body === 'c' || body === 'd') play('mv_squelch', { volume: 0.12, minGap: 110, pan });
      else if (body === 'm') play('mv_servo', { volume: 0.16, minGap: 240, pan });
      else if (pr?.big) play('mv_clank', { volume: 0.12, minGap: 140, pan });
      else if (Math.random() < 0.4) play('mv_gear', { volume: 0.1, minGap: 160, pan });
      break;
    }
    case 'push': play('push', { volume: 0.6, pan }); break;
    case 'spell': play('spell', { volume: 0.65, rate: 0.95 }); play('atk_magic', { volume: 0.3, rate: 0.85, minGap: 200 }); break;
    case 'heal': play('chime', { volume: 0.35, rate: 1.2, minGap: 120, pan }); break;
    case 'status': play('status', { volume: 0.3, rate: 0.85, minGap: 140, pan }); break;
    case 'equip': play('equip', { volume: 0.7, pan }); break;
    case 'essence': play('essence', { volume: 0.5 }); break;
  }
}

/** The lighthouse bell: your turn. */
export function playTurnBell(mine: boolean) { play('bell', { volume: mine ? 0.6 : 0.25, rate: mine ? 1 : 0.8, jitter: 0, minGap: 0 }); }
/** A card arrives in your hand. */
export function playCard() { play('card_draw', { volume: 0.55, minGap: 120 }); }
/** A card is played from the hand (before its effect resolves). */
export function playCardPlay() { play('card_play', { volume: 0.6, minGap: 100 }); }
export function playTurnEnd() { play('turn_end', { volume: 0.5, minGap: 300 }); }
export function playBattleStart() { play('battle_start', { volume: 0.55, minGap: 0, jitter: 0 }); }
export function playEnd(victory: boolean) {
  duckForEnd();
  play(victory ? 'victory' : 'defeat', { volume: 0.85, jitter: 0, minGap: 0 });
}

/** After the first gesture, decode the small, frequently used banks so the first click and first turn aren't silent. */
const CORE = ['ui_hover', 'ui_click', 'ui_confirm', 'ui_back', 'ui_open', 'ui_close', 'ui_select', 'ui_error', 'card_draw', 'card_play', 'bell', 'turn_end',
  'step_salt', 'step_stone', 'atk_blade', 'hit_flesh', 'hit_heavy', 'hit_armor', 'vh_hurt', 'vh_die', 'atk_shoot', 'atk_magic', 'spell', 'deploy', 'chime'];
const REST = Object.keys(banks).filter(k => !CORE.includes(k));
export function preloadBanks() { whenUnlocked(() => { void preload(CORE.flatMap(k => banks[k] ?? []), 4); }); }
/** Voices, impacts and the rest are only needed in a fight: decode them when one starts (or is about to). */
export function preloadBattleBanks() { whenUnlocked(() => { void preload(REST.flatMap(k => banks[k] ?? []), 2); }); }

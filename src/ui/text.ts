import type { Condition, Content, Effect, MissionDef, UnitDef } from '../engine/types';
import { label } from '../engine/content';

/** Short badge text for the movement/survival flags a unit def carries, e.g. "Flying · Skyfall (impact 6) · Dries 2". */
export function traitLine(d: UnitDef): string {
  return [d.flying ? 'Flying' : '', d.skyfall ? `Skyfall (impact ${d.skyfall.impact})` : '', d.dries ? `Dries ${d.dries}` : '',
    d.shell ? `Shell ${d.shell.hp}` : '', d.shed ? 'Shed' : '', d.coiled ? 'Coiled' : '', d.tail ? `Long body (${d.tail.length})` : ''].filter(Boolean).join(' \u00B7 ');
}

export function effectText(c: Content, e: Effect): string {
  switch (e.type) {
    case 'damage': return (e.ignoreAttack ? `${e.amount} ${e.damageType ?? ''} damage (ignores attack)`.replace('  ', ' ')
      : `Damage: attack ${e.amount >= 0 ? '+' : ''}${e.amount}${e.damageType ? ` (${e.damageType})` : ''}`) +
      (e.vsWounded ? `, +${e.vsWounded.bonus} vs targets below ${Math.round(e.vsWounded.below * 100)}% health` : '');
    case 'heal': return `Heals ${e.amount}`;
    case 'status': return `Applies ${c.statuses[e.status]?.name ?? e.status} for ${e.duration} turn${e.duration === 1 ? '' : 's'}`;
    case 'push': return `Pushes ${e.distance} tile${e.distance === 1 ? '' : 's'}${e.collisionDamage ? ` (${e.collisionDamage} collision damage)` : ''}`;
    case 'pull': return `Pulls ${e.distance} tile${e.distance === 1 ? '' : 's'}`;
    case 'teleport': return 'Teleports the caster';
    case 'swap': return 'Swaps places with the target';
    case 'summon': return `Summons ${e.count ?? 1} ${c.units[e.unit]?.name ?? e.unit}`;
    case 'terrain': return `Changes terrain to ${c.terrain[e.terrain]?.name ?? e.terrain}${e.duration ? ` for ${e.duration} turns` : ''}`;
    case 'essence': return `${e.amount >= 0 ? 'Grants' : 'Drains'} ${Math.abs(e.amount)} ${label(c, 'essence')}`;
    case 'aura': {
      const parts = Object.entries(e.statMods ?? {}).map(([k, v]) => `${(v ?? 0) >= 0 ? '+' : ''}${v} ${k}`)
        .concat(Object.entries(e.resist ?? {}).map(([k, v]) => `resist ${k} ${v}`));
      const who = e.radius === 0 ? 'Self' : `${e.affects ?? 'allies'} within ${e.radius}`;
      return `${who}: ${parts.join(', ')}${e.perAdjacentAlly ? ' per adjacent ally' : ''}`;
    }
    case 'sacrifice': return 'Sacrifices the caster';
    case 'reshed': return 'Can Shed again';
    case 'shell': return `Repairs ${e.amount} shell`;
    case 'rehouse': return 'Moves into an adjacent empty shell or wreck';
    case 'moveOut': return 'Steps out of its shell, leaving it behind';
    default: return (e as { type: string }).type;
  }
}

function cond(c: Content, m: MissionDef, cd: Condition): string {
  if (cd.label) return cd.label;
  const base = condBase(c, m, cd);
  return cd.not ? `NOT: ${base}` : base;
}

function condBase(c: Content, m: MissionDef, cd: Condition): string {
  const tn = (t: number) => m.teams[t]?.name ?? `team ${t}`;
  const ks = label(c, 'keystone');
  const tagName = (tag: string) => {
    const placed = m.teams.flatMap(t => t.units ?? []).find(u => u.tag === tag)
      ?? (m.events ?? []).flatMap(e => e.do).find((a): a is Extract<typeof a, { type: 'spawn' }> => a.type === 'spawn' && a.tag === tag);
    return placed ? c.units[placed.unit]?.name ?? tag : tag;
  };
  switch (cd.type) {
    case 'destroy_keystone': return cd.team === 0 ? `Your ${ks} is destroyed` : `Destroy the ${tn(cd.team)} ${ks}`;
    case 'eliminate': return cd.team === 0 ? 'Your whole force is wiped out' : `Eliminate the ${tn(cd.team)} force`;
    case 'defeat_unit': return `Defeat ${tagName(cd.tag)}`;
    case 'unit_lost': return `${tagName(cd.tag)} falls`;
    case 'unit_hp_above': return `${tagName(cd.tag)} stays above ${Math.round(cd.fraction * 100)}% health`;
    case 'survive': return `Survive ${cd.turns} rounds`;
    case 'turn_limit': return `The ${cd.turns}-round limit passes`;
    case 'reach_tile': return `${cd.team === 0 ? 'Reach' : 'The enemy reaches'} the marked ground${cd.tag ? ` with ${cd.tag}` : ''}`;
  }
}

export function describeObjectives(c: Content, m: MissionDef) {
  const ks = label(c, 'keystone');
  const win = m.objectives?.victory?.map(x => cond(c, m, x)) ??
    [`Destroy the enemy ${ks} or eliminate their ${label(c, 'warband').toLowerCase()}`];
  const lose = m.objectives?.defeat?.map(x => cond(c, m, x)) ??
    [`Your ${ks} is destroyed or your ${label(c, 'warband').toLowerCase()} is wiped out`];
  return { win, lose, winAny: (m.objectives?.victory?.length ?? 0) > 1 };
}

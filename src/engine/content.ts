import type { AbilityDef, Content, Condition, Effect, MissionAction, StatKey, UnitDef } from './types';

const EFFECT_TYPES = ['damage', 'heal', 'status', 'push', 'pull', 'swap', 'teleport', 'summon', 'terrain', 'essence', 'aura', 'sacrifice', 'draw',
  'reshed', 'shell', 'rehouse', 'moveOut'];
/** Effects that need a caster unit (not allowed in spells, terrain or statuses). */
const CASTER_ONLY = ['teleport', 'swap', 'aura', 'sacrifice', 'rehouse', 'moveOut'];

/** Unit ids that are never cards: `token`, `decoy` and `emptyShell` units, plus anything named as a husk, evicted form,
 *  left-behind shell or tail segment by another unit. */
export function nonCardUnits(c: Pick<Content, 'units'>): Set<string> {
  const out = new Set<string>();
  for (const [id, u] of Object.entries(c.units)) {
    if (u.token || u.decoy || u.emptyShell) out.add(id);
    if (u.shed?.husk) out.add(u.shed.husk);
    if (u.shell?.evicted) out.add(u.shell.evicted);
    if (u.shell?.leaves) out.add(u.shell.leaves);
    if (u.tail?.segment) out.add(u.tail.segment);
  }
  return out;
}
/** True for a unit that can be a card in a deck, roster, collection or gallery: not a structure, not a token. */
export function isCardUnit(c: Pick<Content, 'units'>, id: string): boolean {
  const u: UnitDef | undefined = c.units[id];
  return !!u && !u.structure && !nonCardUnits(c).has(id);
}

/** Fill in defaults so content authors can omit fields (e.g. passives need no range/target/apCost). */
export function normalizeContent(c: Content): Content {
  for (const a of Object.values(c.abilities)) {
    // Shorthand passives: { passive, area?, affects?, statMods } or effects [{type:"resist", damageType, amount}].
    if (a.passive) {
      const raw = a as AbilityDef & { statMods?: Partial<Record<StatKey, number>> };
      const effects = (a.effects ?? []).map(e => {
        const r = e as unknown as { type: string; damageType?: string; amount?: number };
        return r.type === 'resist' && r.damageType
          ? { type: 'aura', radius: a.area?.size ?? 0, affects: a.affects, resist: { [r.damageType]: r.amount ?? 0 } } as Effect
          : e;
      });
      if (raw.statMods) effects.push({ type: 'aura', radius: a.area?.size ?? 0, affects: a.affects, statMods: raw.statMods });
      a.effects = effects;
    }
    a.apCost ??= 0;
    a.range ??= { min: 0, max: 0 };
    a.target ??= 'self';
    a.effects ??= [];
  }
  for (const u of Object.values(c.units)) u.abilities ??= [];
  for (const m of Object.values(c.maps ?? {})) for (const w of m.wells ?? []) w.amount ??= 10;
  c.spells ??= {};
  c.equipment ??= {};
  return c;
}

/** Player-facing name for an engine term ("essence", "keystone", ...), configurable in content/config.json. */
export function label(c: Content, term: string, fallback?: string): string {
  return c.config?.labels?.[term] ?? fallback ?? term.charAt(0).toUpperCase() + term.slice(1);
}

/** Validate every cross-reference in a content bundle. Returns a list of human-readable problems. */
export function validateContent(c: Content): string[] {
  const errs: string[] = [];
  const has = (rec: Record<string, unknown>, id: string) => Object.prototype.hasOwnProperty.call(rec, id);

  const checkEffect = (e: Effect, where: string) => {
    if (e.type === 'status' && !has(c.statuses, e.status)) errs.push(`${where}: unknown status "${e.status}"`);
    if (!EFFECT_TYPES.includes(e.type)) errs.push(`${where}: unknown effect type "${(e as Effect).type}"`);
    if (e.type === 'summon' && !has(c.units, e.unit)) errs.push(`${where}: unknown summon unit "${e.unit}"`);
    if (e.type === 'draw' && (!Number.isInteger(e.count) || e.count < 1)) errs.push(`${where}: draw needs an integer count >= 1`);
    if (e.type === 'damage' && e.convertOnKill !== undefined && (typeof e.convertOnKill !== 'string' || !has(c.units, e.convertOnKill))) errs.push(`${where}: unknown convertOnKill unit "${e.convertOnKill}"`);
    if (e.type === 'terrain' && !has(c.terrain, e.terrain)) errs.push(`${where}: unknown terrain "${e.terrain}"`);
    if (e.type === 'damage' && e.vsWounded && (typeof e.vsWounded.below !== 'number' || typeof e.vsWounded.bonus !== 'number')) errs.push(`${where}: vsWounded needs numeric below and bonus`);
    if (e.ifTargetStatus !== undefined && !has(c.statuses, e.ifTargetStatus)) errs.push(`${where}: ifTargetStatus names unknown status "${e.ifTargetStatus}"`);
    if (e.ifTargetStacks !== undefined) {
      const st = e.ifTargetStacks;
      if (typeof st !== 'object' || st === null || typeof st.status !== 'string' || typeof st.min !== 'number') errs.push(`${where}: ifTargetStacks needs {status, min}`);
      else if (!has(c.statuses, st.status)) errs.push(`${where}: ifTargetStacks names unknown status "${st.status}"`);
    }
    if (e.type === 'shell' && (typeof e.amount !== 'number' || e.amount < 0)) errs.push(`${where}: shell needs a number amount >= 0`);
    if (e.type === 'aura' && e.keepsWet !== undefined && typeof e.keepsWet !== 'boolean') errs.push(`${where}: keepsWet must be true or false`);
    const f = (e as { filter?: Record<string, unknown> }).filter;
    if (f) {
      if (typeof f !== 'object') errs.push(`${where}: filter must be an object`);
      else for (const [k, v] of Object.entries(f)) {
        if (k === 'flying' || k === 'shelled') { if (typeof v !== 'boolean') errs.push(`${where}: filter.${k} must be true or false`); }
        else if (k === 'faction' || k === 'notFaction') {
          if (!Array.isArray(v) || v.some(x => typeof x !== 'string')) errs.push(`${where}: filter.${k} must be a list of faction ids`);
          else if (c.factions) for (const x of v as string[]) if (!has(c.factions, x)) errs.push(`${where}: filter.${k} names unknown faction "${x}"`);
        } else errs.push(`${where}: filter only supports flying, shelled, faction and notFaction`);
      }
    }
    if (e.type === 'status' && e.target !== undefined && e.target !== 'caster') errs.push(`${where}: status target must be "caster"`);
    if (e.type === 'aura' && typeof e.radius !== 'number') errs.push(`${where}: aura needs a numeric radius`);
  };

  for (const [id, a] of Object.entries(c.abilities)) {
    if (!a.effects?.length) errs.push(`ability ${id}: has no effects`);
    a.effects?.forEach((e, i) => checkEffect(e, `ability ${id} effect ${i}`));
    if (a.passive && a.effects?.some(e => e.type !== 'aura')) errs.push(`ability ${id}: passive abilities only support "aura" effects`);
    if (a.range.min > a.range.max) errs.push(`ability ${id}: range.min > range.max`);
    if (a.effects?.some(e => e.type === 'rehouse') && a.target !== 'tile') errs.push(`ability ${id}: rehouse needs target "tile"`);
    if (a.effects?.some(e => e.type === 'moveOut') && a.target !== 'empty') errs.push(`ability ${id}: moveOut needs target "empty"`);
  }
  for (const [id, s] of Object.entries(c.statuses)) {
    if (s.wet !== undefined && typeof s.wet !== 'boolean') errs.push(`status ${id}: wet must be true or false`);
    if (s.untargetable !== undefined && typeof s.untargetable !== 'boolean') errs.push(`status ${id}: untargetable must be true or false`);
    s.onTurnStart?.forEach((e, i) => {
      if (e.type !== 'damage' && e.type !== 'heal') errs.push(`status ${id} onTurnStart ${i}: only damage/heal supported`);
    });
    if (s.onAct !== undefined && !Array.isArray(s.onAct)) errs.push(`status ${id}: onAct must be a list of effects`);
    else s.onAct?.forEach((e, i) => {
      checkEffect(e, `status ${id} onAct ${i}`);
      if (e.type !== 'damage') errs.push(`status ${id} onAct ${i}: only damage is supported`);
    });
    if (s.shedsWhenIdle !== undefined && typeof s.shedsWhenIdle !== 'boolean') errs.push(`status ${id}: shedsWhenIdle must be true or false`);
  }
  for (const [id, u] of Object.entries(c.units)) {
    for (const ab of u.abilities) if (!has(c.abilities, ab)) errs.push(`unit ${id}: unknown ability "${ab}"`);
    for (const k of ['hp', 'ap', 'attack', 'defense', 'jump'] as const)
      if (typeof u.stats?.[k] !== 'number') errs.push(`unit ${id}: stats.${k} missing`);
    if (u.skyfall !== undefined && typeof u.skyfall?.impact !== 'number') errs.push(`unit ${id}: skyfall needs a numeric impact`);
    if (u.dries !== undefined && (typeof u.dries !== 'number' || u.dries < 0)) errs.push(`unit ${id}: dries must be a number >= 0`);
    if (u.flying !== undefined && typeof u.flying !== 'boolean') errs.push(`unit ${id}: flying must be true or false`);
    for (const k of ['token', 'decoy'] as const) if (u[k] !== undefined && typeof u[k] !== 'boolean') errs.push(`unit ${id}: ${k} must be true or false`);
    if (u.decoy && !u.structure) errs.push(`unit ${id}: decoy units must also be structures`);
    const ref = (field: string, v: unknown, need?: (d: UnitDef) => string | undefined) => {
      if (typeof v !== 'string' || !has(c.units, v)) { errs.push(`unit ${id}: ${field} names unknown unit "${String(v)}"`); return; }
      const why = need?.(c.units[v]);
      if (why) errs.push(`unit ${id}: ${field} "${v}" ${why}`);
    };
    if (u.shed !== undefined) {
      ref('shed.husk', u.shed?.husk, d => d.structure ? undefined : 'must be a structure (decoy) unit');
      if (u.shed?.slide !== undefined && (!Number.isInteger(u.shed.slide) || u.shed.slide < 0)) errs.push(`unit ${id}: shed.slide must be an integer >= 0`);
    }
    if (u.coiled !== undefined && (typeof u.coiled?.ability !== 'string' || !has(c.abilities, u.coiled.ability))) errs.push(`unit ${id}: coiled.ability names unknown ability "${u.coiled?.ability}"`);
    if (u.shell !== undefined) {
      if (typeof u.shell?.hp !== 'number' || !(u.shell.hp > 0)) errs.push(`unit ${id}: shell.hp must be a number > 0`);
      ref('shell.evicted', u.shell?.evicted, d => d.shell ? 'must not have a shell itself' : d.structure ? 'must not be a structure' : undefined);
      if (u.shell?.leaves !== undefined) ref('shell.leaves', u.shell.leaves, d => d.emptyShell ? undefined : 'must be an emptyShell unit');
      if (u.structure) errs.push(`unit ${id}: a structure cannot have a shell`);
    }
    if (u.emptyShell !== undefined) {
      ref('emptyShell.becomes', u.emptyShell?.becomes, d => d.shell ? undefined : 'must be a unit with a shell');
      if (!u.structure) errs.push(`unit ${id}: emptyShell units must also be structures`);
    }
    if (u.tail !== undefined) {
      ref('tail.segment', u.tail?.segment, d => d.structure ? undefined : 'must be a structure unit');
      if (!Number.isInteger(u.tail?.length) || u.tail.length < 1 || u.tail.length > 3) errs.push(`unit ${id}: tail.length must be 1, 2 or 3`);
    }
  }
  for (const [id, sp] of Object.entries(c.spells ?? {})) {
    if (!sp.effects?.length) errs.push(`spell ${id}: has no effects`);
    if ((sp.area?.shape as string) === 'line') errs.push(`spell ${id}: line areas need a caster; use radius`);
    sp.effects?.forEach((e, i) => {
      checkEffect(e, `spell ${id} effect ${i}`);
      if (CASTER_ONLY.includes(e.type) || ((e.type === 'heal' || e.type === 'status') && e.target === 'caster')) errs.push(`spell ${id} effect ${i}: "${e.type}" needs a caster unit; not allowed in spells`);
    });
  }
  for (const [id, eq] of Object.entries(c.equipment ?? {}))
    for (const ab of eq.grantAbilities ?? []) if (!has(c.abilities, ab)) errs.push(`equipment ${id}: unknown ability "${ab}"`);
  const cardIds = [Object.keys(c.units), Object.keys(c.spells ?? {}), Object.keys(c.equipment ?? {})];
  const seen = new Map<string, number>();
  cardIds.forEach((ids, kind) => ids.forEach(i => {
    if (seen.has(i) && seen.get(i) !== kind) errs.push(`id "${i}" is used by more than one of units/spells/equipment`);
    seen.set(i, kind);
  }));
  const isCard = (i: string) => seen.has(i);
  const tokens = nonCardUnits(c);
  const checkWarband = (list: string[], where: string) => {
    list.forEach(i => { if (!isCard(i)) errs.push(`${where}: unknown card "${i}"`); else if (tokens.has(i)) errs.push(`${where}: "${i}" is a token unit and can never be a card`); });
    const heroes = list.filter(i => c.units[i]?.hero);
    const dup = heroes.find((h, i) => heroes.indexOf(h) !== i);
    if (dup) errs.push(`${where}: hero "${dup}" appears more than once`);
  };

  for (const [id, t] of Object.entries(c.terrain)) {
    if (t.onEnter) checkEffect(t.onEnter, `terrain ${id} onEnter`);
    t.onTurnStart?.forEach((e, i) => {
      checkEffect(e, `terrain ${id} onTurnStart ${i}`);
      if (!['damage', 'heal', 'status'].includes(e.type)) errs.push(`terrain ${id} onTurnStart ${i}: only damage, heal and status effects are allowed`);
    });
    if (t.void !== undefined && typeof t.void !== 'boolean') errs.push(`terrain ${id}: void must be true or false`);
    if (t.void && !t.impassable) errs.push(`terrain ${id}: void terrain must also be impassable`);
    if (t.rangeBonus !== undefined && typeof t.rangeBonus !== 'number') errs.push(`terrain ${id}: rangeBonus must be a number`);
    if (t.factionMoveCost !== undefined) {
      if (typeof t.factionMoveCost !== 'object' || t.factionMoveCost === null) errs.push(`terrain ${id}: factionMoveCost must be an object`);
      else for (const [f, v] of Object.entries(t.factionMoveCost)) {
        if (typeof v !== 'number' || !(v >= 1)) errs.push(`terrain ${id}: factionMoveCost.${f} must be a number >= 1`);
        if (c.factions && !has(c.factions, f)) errs.push(`terrain ${id}: factionMoveCost names unknown faction "${f}"`);
      }
    }
    if (t.wet !== undefined && typeof t.wet !== 'boolean') errs.push(`terrain ${id}: wet must be true or false`);
    if (t.shellSource !== undefined) {
      if (typeof t.shellSource !== 'string' || !has(c.units, t.shellSource)) errs.push(`terrain ${id}: shellSource names unknown unit "${String(t.shellSource)}"`);
      else if (!c.units[t.shellSource].shell) errs.push(`terrain ${id}: shellSource "${t.shellSource}" must be a unit with a shell`);
      if (!has(c.terrain, 'salt_flat')) errs.push(`terrain ${id}: shellSource needs a "salt_flat" terrain to leave behind`);
    }
  }

  for (const [id, m] of Object.entries(c.maps)) {
    const h = m.tiles.length;
    const w = m.tiles[0]?.length ?? 0;
    if (!h || !w) errs.push(`map ${id}: empty tiles`);
    if (m.heights.length !== h) errs.push(`map ${id}: heights has ${m.heights.length} rows, tiles has ${h}`);
    m.tiles.forEach((row, y) => {
      if (row.length !== w) errs.push(`map ${id}: tiles row ${y} width ${row.length} != ${w}`);
      for (const ch of row) {
        const t = m.legend[ch];
        if (!t) errs.push(`map ${id}: row ${y} char "${ch}" not in legend`);
        else if (!has(c.terrain, t)) errs.push(`map ${id}: legend "${ch}" -> unknown terrain "${t}"`);
      }
    });
    m.heights.forEach((row, y) => {
      if (row.length !== w) errs.push(`map ${id}: heights row ${y} width ${row.length} != ${w}`);
      if (!/^[0-9]*$/.test(row)) errs.push(`map ${id}: heights row ${y} must be digits`);
    });
    const inside = (x: number, y: number) => x >= 0 && y >= 0 && x < w && y < h;
    for (const wl of m.wells ?? []) if (!inside(wl.x, wl.y)) errs.push(`map ${id}: well out of bounds`);
    for (const k of m.keystones ?? []) if (!inside(k.x, k.y)) errs.push(`map ${id}: keystone out of bounds`);
    for (const [team, zone] of Object.entries(m.deployZones))
      for (const [x, y] of zone) if (!inside(x, y)) errs.push(`map ${id}: deploy zone ${team} tile ${x},${y} out of bounds`);
  }

  const unitRef = (id: string, where: string) => { if (!has(c.units, id)) errs.push(`${where}: unknown unit "${id}"`); };
  for (const [id, m] of Object.entries(c.missions)) {
    const map = c.maps[m.map];
    if (!map) { errs.push(`mission ${id}: unknown map "${m.map}"`); continue; }
    if (m.teams.length < 2) errs.push(`mission ${id}: needs at least 2 teams`);
    m.teams.forEach((t, ti) => {
      if (t.warband) checkWarband(t.warband, `mission ${id} team ${ti} warband`);
      t.units?.forEach(u => {
        unitRef(u.unit, `mission ${id} team ${ti} units`);
        if (u.x < 0 || u.y < 0 || u.y >= map.tiles.length || u.x >= map.tiles[0].length) errs.push(`mission ${id}: unit ${u.unit} out of bounds`);
      });
    });
    const checkCond = (cd: Condition, where: string) => {
      const known = ['destroy_keystone', 'eliminate', 'defeat_unit', 'unit_lost', 'survive', 'turn_limit', 'reach_tile', 'unit_hp_above'];
      if (!known.includes(cd.type)) errs.push(`${where}: unknown condition "${cd.type}"`);
    };
    m.objectives?.victory?.forEach((cd, i) => checkCond(cd, `mission ${id} victory ${i}`));
    m.objectives?.defeat?.forEach((cd, i) => checkCond(cd, `mission ${id} defeat ${i}`));
    m.events?.forEach((ev, i) => ev.do.forEach((a: MissionAction) => {
      if (a.type === 'spawn') {
        unitRef(a.unit, `mission ${id} event ${i}`);
        if (!m.teams[a.team]) errs.push(`mission ${id} event ${i}: spawn for team ${a.team}, but the mission has ${m.teams.length} teams`);
      }
      if (a.type === 'terrain' && !has(c.terrain, a.terrain)) errs.push(`mission ${id} event ${i}: unknown terrain "${a.terrain}"`);
      if (a.type === 'status' && !has(c.statuses, a.status)) errs.push(`mission ${id} event ${i}: unknown status "${a.status}"`);
    }));
  }
  for (const [id, camp] of Object.entries(c.campaigns)) {
    checkWarband(camp.startingRoster.concat(camp.missions.flatMap(m => m.unlocks ?? [])), `campaign ${id} roster+unlocks`);
    camp.missions.forEach((m, i) => {
      if (!has(c.missions, m.mission)) errs.push(`campaign ${id} step ${i}: unknown mission "${m.mission}"`);
    });
  }
  return errs;
}

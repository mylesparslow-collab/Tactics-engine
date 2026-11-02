import type { AbilityDef, Content, Condition, Effect, MissionAction, StatKey } from './types';

const EFFECT_TYPES = ['damage', 'heal', 'status', 'push', 'pull', 'swap', 'teleport', 'summon', 'terrain', 'essence', 'aura', 'sacrifice'];

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
    if (e.type === 'terrain' && !has(c.terrain, e.terrain)) errs.push(`${where}: unknown terrain "${e.terrain}"`);
    if (e.type === 'damage' && e.vsWounded && (typeof e.vsWounded.below !== 'number' || typeof e.vsWounded.bonus !== 'number')) errs.push(`${where}: vsWounded needs numeric below and bonus`);
    if (e.ifTargetStatus !== undefined && !has(c.statuses, e.ifTargetStatus)) errs.push(`${where}: ifTargetStatus names unknown status "${e.ifTargetStatus}"`);
    if (e.type === 'aura' && e.keepsWet !== undefined && typeof e.keepsWet !== 'boolean') errs.push(`${where}: keepsWet must be true or false`);
    const f = (e as { filter?: Record<string, unknown> }).filter;
    if (f && (typeof f !== 'object' || Object.entries(f).some(([k, v]) => k !== 'flying' || typeof v !== 'boolean'))) errs.push(`${where}: filter only supports { flying: boolean }`);
    if (e.type === 'status' && e.target !== undefined && e.target !== 'caster') errs.push(`${where}: status target must be "caster"`);
    if (e.type === 'aura' && typeof e.radius !== 'number') errs.push(`${where}: aura needs a numeric radius`);
  };

  for (const [id, a] of Object.entries(c.abilities)) {
    if (!a.effects?.length) errs.push(`ability ${id}: has no effects`);
    a.effects?.forEach((e, i) => checkEffect(e, `ability ${id} effect ${i}`));
    if (a.passive && a.effects?.some(e => e.type !== 'aura')) errs.push(`ability ${id}: passive abilities only support "aura" effects`);
    if (a.range.min > a.range.max) errs.push(`ability ${id}: range.min > range.max`);
  }
  for (const [id, s] of Object.entries(c.statuses)) {
    if (s.wet !== undefined && typeof s.wet !== 'boolean') errs.push(`status ${id}: wet must be true or false`);
    s.onTurnStart?.forEach((e, i) => {
      if (e.type !== 'damage' && e.type !== 'heal') errs.push(`status ${id} onTurnStart ${i}: only damage/heal supported`);
    });
  }
  for (const [id, u] of Object.entries(c.units)) {
    for (const ab of u.abilities) if (!has(c.abilities, ab)) errs.push(`unit ${id}: unknown ability "${ab}"`);
    for (const k of ['hp', 'ap', 'attack', 'defense', 'jump'] as const)
      if (typeof u.stats?.[k] !== 'number') errs.push(`unit ${id}: stats.${k} missing`);
    if (u.skyfall !== undefined && typeof u.skyfall?.impact !== 'number') errs.push(`unit ${id}: skyfall needs a numeric impact`);
    if (u.dries !== undefined && (typeof u.dries !== 'number' || u.dries < 0)) errs.push(`unit ${id}: dries must be a number >= 0`);
    if (u.flying !== undefined && typeof u.flying !== 'boolean') errs.push(`unit ${id}: flying must be true or false`);
  }
  for (const [id, sp] of Object.entries(c.spells ?? {})) {
    if (!sp.effects?.length) errs.push(`spell ${id}: has no effects`);
    if ((sp.area?.shape as string) === 'line') errs.push(`spell ${id}: line areas need a caster; use radius`);
    sp.effects?.forEach((e, i) => {
      checkEffect(e, `spell ${id} effect ${i}`);
      if (e.type === 'teleport' || e.type === 'swap' || e.type === 'aura' || e.type === 'sacrifice' || ((e.type === 'heal' || e.type === 'status') && e.target === 'caster')) errs.push(`spell ${id} effect ${i}: "${e.type}" needs a caster unit; not allowed in spells`);
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
  const checkWarband = (list: string[], where: string) => {
    list.forEach(i => { if (!isCard(i)) errs.push(`${where}: unknown card "${i}"`); });
    const heroes = list.filter(i => c.units[i]?.hero);
    const dup = heroes.find((h, i) => heroes.indexOf(h) !== i);
    if (dup) errs.push(`${where}: hero "${dup}" appears more than once`);
  };

  for (const [id, t] of Object.entries(c.terrain)) {
    if (t.onEnter) checkEffect(t.onEnter, `terrain ${id} onEnter`);
    if (t.wet !== undefined && typeof t.wet !== 'boolean') errs.push(`terrain ${id}: wet must be true or false`);
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

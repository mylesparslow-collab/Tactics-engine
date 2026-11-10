#!/usr/bin/env python3
"""Merge a faction's engine-ready fragments into content/*.json.

Usage: python3 tools/content/merge_faction.py <faction_folder> [--dry-run]

Folder layout: units.json abilities.json statuses.json spells.json equipment.json relics.json
faction.json (optional files are skipped), terrain_patch.json (optional). Each fragment is an object keyed by id.
faction.json is {factionId: {...}} (or a bare faction body, then the folder name is the id).

Rules
- new id: appended at the end of the target file (existing entries are never reordered).
- same id, same content: no-op (idempotent).
- same id, different content: updated IN PLACE if the entry belongs to this faction (its `faction` field equals the
  faction id, or the id is recorded in tools/content/merged/<faction>.json by an earlier run); otherwise the run
  aborts with a collision error and nothing is written.
- terrain_patch.json: {terrainId: {field: value}} merged into content/terrain.json; the terrain must exist, and an
  existing different value for a field is only overwritten if this faction patched it before.
- Formatting of each target file (indent, trailing newline) is detected and preserved.
"""
import json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CONTENT = os.path.join(ROOT, 'content')
MANIFESTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'merged')
TARGETS = ['units', 'abilities', 'statuses', 'spells', 'equipment', 'relics']


def load(path):
    with open(path, encoding='utf-8') as f:
        text = f.read()
    return json.loads(text), text


def detect_style(text, data):
    """Find (indent, ensure_ascii, trailing newline) that reproduces the file byte for byte."""
    for indent in (1, 2, 4, 3):
        for ea in (False, True):
            out = json.dumps(data, indent=indent, ensure_ascii=ea)
            for tail in ('', '\n'):
                if out + tail == text:
                    return indent, ea, tail
    raise SystemExit('cannot reproduce existing formatting; refusing to rewrite it')


def dump(data, style):
    indent, ea, tail = style
    return json.dumps(data, indent=indent, ensure_ascii=ea) + tail


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    if len(args) != 1:
        raise SystemExit(__doc__)
    folder = os.path.abspath(args[0])
    fid = os.path.basename(folder.rstrip('/'))
    mpath = os.path.join(MANIFESTS, fid + '.json')
    manifest = json.load(open(mpath)) if os.path.exists(mpath) else {}
    new_manifest = {}
    writes, errors, report = {}, [], []

    def merge_into(kind, frag):
        path = os.path.join(CONTENT, kind + '.json')
        data, text = load(path)
        style = detect_style(text, data)
        owned = set(manifest.get(kind, []))
        added = updated = same = 0
        for k, v in frag.items():
            if k not in data:
                data[k] = v; added += 1
            elif data[k] == v:
                same += 1
            elif k in owned or (isinstance(data[k], dict) and data[k].get('faction') == fid):
                data[k] = v; updated += 1
            else:
                errors.append(f'{kind}.json: id "{k}" already exists with different content and does not belong to {fid}')
        new_manifest[kind] = sorted(set(owned) | set(frag))
        report.append(f'{kind}: +{added} ~{updated} ={same}')
        if added or updated:
            writes[path] = dump(data, style)

    for kind in TARGETS:
        p = os.path.join(folder, kind + '.json')
        if os.path.exists(p):
            merge_into(kind, load(p)[0])

    p = os.path.join(folder, 'faction.json')
    if os.path.exists(p):
        frag = load(p)[0]
        if 'name' in frag:  # bare body
            frag = {fid: frag}
        merge_into('factions', frag)

    p = os.path.join(folder, 'terrain_patch.json')
    if os.path.exists(p):
        patch = load(p)[0]
        path = os.path.join(CONTENT, 'terrain.json')
        data, text = load(path)
        style = detect_style(text, data)
        owned = manifest.get('terrain', {})
        changed = 0
        for tid, fields in patch.items():
            if tid not in data:
                errors.append(f'terrain.json: unknown terrain "{tid}" in terrain_patch'); continue
            for fk, fv in fields.items():
                cur = data[tid].get(fk)
                if cur == fv:
                    continue
                if cur is not None and fk not in owned.get(tid, []):
                    errors.append(f'terrain.json: {tid}.{fk} is already {cur!r}, patch wants {fv!r}')
                    continue
                data[tid][fk] = fv; changed += 1
        tm = {t: list(v) for t, v in owned.items()}
        for t, f in patch.items():
            tm[t] = sorted(set(tm.get(t, [])) | set(f))
        new_manifest['terrain'] = tm
        report.append(f'terrain: {changed} field(s) set')
        if changed:
            writes[path] = dump(data, style)

    if errors:
        print('REFUSED, nothing written:\n  ' + '\n  '.join(errors)); sys.exit(1)
    print(f'faction {fid}: ' + '; '.join(report))
    if dry:
        print('dry run, nothing written'); return
    for path, out in writes.items():
        with open(path, 'w', encoding='utf-8') as f:
            f.write(out)
    os.makedirs(MANIFESTS, exist_ok=True)
    with open(mpath, 'w', encoding='utf-8') as f:
        f.write(json.dumps(new_manifest, indent=1) + '\n')
    print('wrote ' + ', '.join(os.path.relpath(p, ROOT) for p in writes) or 'nothing')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Balance changes as data. `tune.py patch OUT.json [SPEC.json]` writes a SIM_PATCH for trying them in sims;
`tune.py apply [SPEC.json]` writes them into content/*.json. A spec maps "file/id/path.to.field" to a value;
list indexes are numbers in the path (e.g. "spells/sc_spell_salt_volley/effects.0.amount": 5)."""
import json, sys, copy

def load_spec(p): return json.load(open(p))

def setp(obj, path, val):
    parts = [int(x) if x.isdigit() else x for x in path.split('.')]
    for k in parts[:-1]: obj = obj[k]
    obj[parts[-1]] = val

def main():
    cmd = sys.argv[1]
    spec = load_spec(sys.argv[3] if cmd == 'patch' else sys.argv[2])
    files = {}
    for key, val in spec.items():
        if key.startswith('#'): continue  # comments
        f, cid, path = key.split('/', 2)
        if f not in files: files[f] = json.load(open(f'content/{f}.json'))
        setp(files[f][cid], path, val)
    if cmd == 'apply':
        for f, d in files.items():
            json.dump(d, open(f'content/{f}.json', 'w'), indent=1, ensure_ascii=False)
    else:
        patch = {}
        for key in spec:
            if key.startswith('#'): continue
            f, cid, path = key.split('/', 2)
            top = path.split('.')[0]
            patch.setdefault(f, {}).setdefault(cid, {})[top] = copy.deepcopy(files[f][cid][top])
        json.dump(patch, open(sys.argv[2], 'w'))

main()

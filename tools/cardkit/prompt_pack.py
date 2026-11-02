"""Build the ChatGPT card-art pack: one folder per card with prompt.txt and the reference image(s) to upload.
Run: python3 tools/cardkit/prompt_pack.py <art_prompts.md> <ref_render_dir> <contact_dir> <out_dir>"""
import os, re, sys, json, shutil
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
SRC, REF, CONTACT, OUT = sys.argv[1:5]
units = json.load(open(os.path.join(ROOT, 'content', 'units.json')))
spells = json.load(open(os.path.join(ROOT, 'content', 'spells.json')))
equip = json.load(open(os.path.join(ROOT, 'content', 'equipment.json')))
factions = json.load(open(os.path.join(ROOT, 'content', 'factions.json')))
factions = factions if isinstance(factions, dict) else {f['id']: f for f in factions}

text = open(SRC).read()
sections = re.split(r'\n## ', text)
palette, scene = {}, {}
for sec in sections:
    m = re.search(r'\(`([a-z_]+)`\)', sec.split('\n')[0])
    if not m: continue
    fid = m.group(1)
    pm = re.search(r'\*\*Palette and silhouette reminder\.\*\*\s*(.+)', sec)
    palette[fid] = pm.group(1).strip() if pm else ''
    for row in sec.split('\n'):
        cells = [c.strip() for c in row.strip().strip('|').split('|')]
        if len(cells) >= 3 and cells[0].startswith('`'):
            cid = cells[0].strip('`')
            p = cells[2]
            p = re.sub(r'\s*\[CARD\]\s*$', '', p).strip()
            p = re.sub(r'^HERO\.\s*', '', p)
            scene[cid] = p

STYLE = ("STYLE: Hand-painted digital fantasy card illustration in the tradition of classic collectible card games. Painterly brushwork, "
         "semi-realistic proportions, strong value contrast, a clear light source with a rim light, atmospheric depth behind the subject. "
         "World: Brinewake, a drained seabed beneath a sea held up in the sky by lighthouses. Bleak, strange, salt-stained, warm at human scale: "
         "white salt flats, black trench shadow, rust, bone, bioluminescence, lighthouse beams in a subtly wrong-coloured sky.")
FORMAT = ("FORMAT: Vertical 2:3 portrait, 1024x1536. Full-bleed painting to every edge. The card's text panel will cover the bottom 40% "
          "of the image, so keep the face, hands and key props in the top 60%; the lower part can be legs, ground and shadow. "
          "No text, letters, numbers, runes that read as text, logos, borders, frames, card UI or watermark.")

def write(folder, prompt, refs):
    os.makedirs(folder, exist_ok=True)
    open(os.path.join(folder, 'prompt.txt'), 'w').write(prompt.strip() + '\n')
    for src, name in refs:
        if os.path.exists(src): shutil.copy(src, os.path.join(folder, name))

index = {}
missing = []
for fid, f in factions.items():
    fname = f.get('name', fid)
    ofname = fname if fname.startswith('The ') else 'the ' + fname
    pal = palette.get(fid, '')
    contact = os.path.join(CONTACT, fid, '_contact.png')
    cards = [(k, 'unit', u) for k, u in units.items() if u.get('faction') == fid and k != 'keystone']
    cards += [(k, 'spell', s) for k, s in spells.items() if s.get('faction') == fid]
    cards += [(k, 'equipment', e) for k, e in equip.items() if e.get('faction') == fid]
    for n, (cid, kind, d) in enumerate(cards, 1):
        sc = scene.get(cid)
        if not sc: missing.append(cid); sc = d.get('description', '')
        folder = os.path.join(OUT, fid, f'{n:02d}_{cid}')
        name = d.get('name', cid)
        if kind == 'unit':
            role = 'hero' if d.get('hero') else 'champion'
            prompt = f"""Paint the card art for "{name}", a {role} of {ofname}.

REFERENCE IMAGE (attached, model.png): this character's in-game 3D model. Match it exactly: the same costume, colours, materials, props, headgear, body shape and silhouette. Do not add, remove or redesign gear. Paint it as a finished illustration, not as a 3D render, and give it more detail and texture than the model has.

SCENE: {sc}

If the scene text and the reference image disagree about the outfit, props or body, follow the image.

{"HERO: this is a hero card, so make it feel grand: a more dramatic pose and light, and a thin gold accent on the gear." if d.get('hero') else ''}

PALETTE: {pal}

{STYLE}

{FORMAT}
"""
            refs = [(os.path.join(REF, f'{cid}.png'), 'model.png')]
        else:
            what = 'spell' if kind == 'spell' else 'piece of equipment'
            prompt = f"""Paint the card art for "{name}", a {what} of {ofname}.

REFERENCE IMAGE (attached, faction_models.png): {ofname}'s in-game unit models. Use it only for palette, materials and costume language so this card matches the faction's units. Do not copy the lineup.
If you have already made {fname} champion cards in this chat, match their painting style exactly.

SUBJECT: {sc}

{"The spell effect is the focal point; any figures are secondary, small or seen from behind." if kind == 'spell' else "The object is the focal point, shown large and close, with a little of the world behind it."}

PALETTE: {pal}

{STYLE}

{FORMAT}
"""
            refs = [(contact, 'faction_models.png')]
        prompt = re.sub(r'\n{3,}', '\n\n', prompt)
        write(folder, prompt, refs)
        index.setdefault(fid, []).append((n, cid, name, kind))

with open(os.path.join(OUT, 'INDEX.md'), 'w') as fp:
    for fid, rows in index.items():
        fp.write(f"\n## {factions[fid].get('name', fid)}\n\n")
        for n, cid, name, kind in rows: fp.write(f"- {n:02d} {name} ({kind}) `{cid}`\n")
print('cards', sum(len(v) for v in index.values()), 'missing scene', missing)

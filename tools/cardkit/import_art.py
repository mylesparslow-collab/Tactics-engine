"""Import finished card paintings: python3 tools/cardkit/import_art.py <dir>
Finds <cardId>.png/.jpg/.webp anywhere under <dir>, crops to 2:3, writes content/cards/<cardId>.webp at 512x768."""
import os, sys, json
from PIL import Image
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
ids = set()
for f in ('units.json', 'spells.json', 'equipment.json'):
    ids |= set(json.load(open(os.path.join(ROOT, 'content', f))))
n = 0
for dp, _, files in os.walk(sys.argv[1]):
    for fn in files:
        stem, ext = os.path.splitext(fn)
        if ext.lower() not in ('.png', '.jpg', '.jpeg', '.webp') or stem not in ids: continue
        im = Image.open(os.path.join(dp, fn)).convert('RGB')
        w, h = im.size; tw = min(w, int(h * 2 / 3)); th = int(tw * 3 / 2)
        im = im.crop(((w - tw) // 2, (h - th) // 2, (w - tw) // 2 + tw, (h - th) // 2 + th)).resize((512, 768), Image.LANCZOS)
        im.save(os.path.join(ROOT, 'content', 'cards', f'{stem}.webp'), quality=86, method=6); n += 1
print('imported', n)

"""Contact sheet of finished units: python contact.py <dir_with_sheets> <out.png> [title]
Shows each unit's idle frame at 2x plus 1x, labelled, on board-dark background."""
import sys, os, glob
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]
title = sys.argv[3] if len(sys.argv) > 3 else os.path.basename(d.rstrip('/'))
stills = sorted(glob.glob(os.path.join(d, '*_still.png')))
cols = 6
cw, ch = 96 * 2 + 70, 112 * 2 + 26
rows = (len(stills) + cols - 1) // cols
img = Image.new('RGBA', (cols * cw + 10, rows * ch + 34), (32, 35, 42, 255))
dr = ImageDraw.Draw(img)
dr.text((8, 8), title, fill=(230, 230, 230, 255))
for k, f in enumerate(stills):
    s = Image.open(f).convert('RGBA')
    x, y = 8 + (k % cols) * cw, 30 + (k // cols) * ch
    tile = Image.new('RGBA', (96 * 2, 112 * 2), (92, 94, 100, 255)); tile.alpha_composite(s.resize((192, 224), Image.NEAREST))
    img.paste(tile, (x, y))
    t1 = Image.new('RGBA', (96, 112), (92, 94, 100, 255)); t1.alpha_composite(s)
    img.paste(t1.crop((16, 0, 80, 112)), (x + 194, y + 112))
    name = os.path.basename(f).replace('_still.png', '').split('_', 2)[-1]
    dr.text((x, y + 226), name[:30], fill=(220, 220, 220, 255))
img.save(out)
print(out, len(stills))

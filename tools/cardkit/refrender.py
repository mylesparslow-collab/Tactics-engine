"""Large clean reference render of a unit's 3D model, for card-art prompts and interim card art.
Needs the spritegen tool (branch claude/project-thread-d65e9y, tools/spritegen): set SPRITEGEN to its path.
SPRITEGEN=../sg/tools/spritegen SS=1 python3 tools/cardkit/refrender.py <unitId> <out.png> [scale]
Writes <out.png> on grey (the ChatGPT reference) and <out>_rgba.png (transparent, for interim_art.py)."""
import sys, os, importlib
SG = os.environ['SPRITEGEN']
sys.path.insert(0, SG)
sys.path.insert(0, os.path.join(SG, 'units'))
from PIL import Image
from render import render, Camera, Look
mod = importlib.import_module(sys.argv[1])
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
base = getattr(mod, 'CAMERA', Camera())
W, H = int(96 * scale), int(112 * scale)
cam = Camera(width=W, height=H, anchor=(W // 2, int(104 * scale)), ppm=base.ppm * scale, ss=int(os.environ.get("SS", "2")))
look = getattr(mod, 'LOOK', Look())
img = render(mod.build(mod.neutral_pose()), cam, look)
fg = Image.fromarray(img)
bb = fg.getbbox()
bg = Image.new('RGBA', (W, H), (128, 128, 128, 255)); bg.alpha_composite(fg)
if bb:
    pad = int(12 * scale / 5)
    bg = bg.crop((max(0, bb[0]-pad), max(0, bb[1]-pad), min(W, bb[2]+pad), min(H, bb[3]+pad)))
bg.convert('RGB').save(sys.argv[2])
fg.save(sys.argv[2].replace('.png', '_rgba.png'))

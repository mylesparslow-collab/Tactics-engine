"""Debug close-up render: python closeup.py <unit> <out.png> [ppm] [focus_y_m]"""
import sys, os, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'units'))
from PIL import Image
from render import render, Camera, Look
mod = importlib.import_module(sys.argv[1])
ppm = float(sys.argv[3]) if len(sys.argv) > 3 else 200
fy = float(sys.argv[4]) if len(sys.argv) > 4 else 1.45
size = 200
cam = Camera(width=size, height=size, anchor=(size // 2, size // 2 + fy * 0.866 * ppm), ppm=ppm, ss=2)
look = getattr(mod, 'LOOK', Look())
img = render(mod.build(mod.neutral_pose()), cam, look)
bg = Image.new('RGBA', (size, size), (128, 128, 128, 255)); bg.alpha_composite(Image.fromarray(img))
bg.resize((size * 2, size * 2), Image.NEAREST).save(sys.argv[2])

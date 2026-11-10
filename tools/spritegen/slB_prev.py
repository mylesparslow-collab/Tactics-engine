"""usage: python3 slB_prev.py <unit> out.png [row:i ...]  (cel render of frames, 3x, in a strip)"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
import sys, importlib
from multiprocessing import Pool
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'units'))
from styles import styled

def job(a):
    name, row, i = a
    mod = importlib.import_module(name)
    P, over = mod.frames()[row][i]
    return styled(mod, P, 'cel', over)

if __name__ == '__main__':
    name, out = sys.argv[1], sys.argv[2]
    reqs = sys.argv[3:] or ['idle:0', 'attack:2', 'death:3', 'cast:1']
    jobs = [(name, r.split(':')[0], int(r.split(':')[1])) for r in reqs]
    with Pool(2) as p:
        ims = p.map(job, jobs)
    ims = [Image.fromarray(np.asarray(i)).convert('RGBA') for i in ims]
    W, H = ims[0].size
    sheet = Image.new('RGBA', (W * len(ims), H), (100, 104, 112, 255))
    for k, im in enumerate(ims):
        sheet.alpha_composite(im, (k * W, 0))
    sheet = sheet.resize((sheet.width * 3 // 2 * 1, sheet.height * 3 // 2), Image.NEAREST) if len(ims) > 4 else sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
    sheet.save(out)
